# File: tests/test_integration_smoke.py
"""Integration smoke (W2-M3-03): chơi trọn vẹn nhiều ván ngẫu nhiên có seed qua
public API và kiểm tra các phần ghép lại với nhau: reset, step, terminal, result,
clone_env, undo, tái lập nước đi và bản ghi GameRecord (JSON).

Không dùng xfail: file này là cổng cuối trước khi gắn tag freeze.
"""
from __future__ import annotations

import json
import random

import pytest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import (
    CONTRACT_VERSION,
    GameConfig,
    GameRecord,
    MoveRecord,
    Player,
    UndoError,
)
from helpers.helpers_contract import (
    check_record_invariants,
    check_state_invariants,
    record_from_json,
    record_to_json,
)

N = 11
SEEDS = list(range(8))


def new_env(seed: int | None = None) -> CaroEnv:
    env = CaroEnv()
    env.reset(seed=seed)
    return env


def play_random_game(seed: int):
    """Chơi một ván ngẫu nhiên (có seed) đến khi kết thúc; trả về env, nước đi, state, reward."""
    rng = random.Random(seed)
    env = new_env(seed)
    states = [env.state]
    moves, rewards = [], []
    while not env.is_terminal():
        assert len(moves) < N * N, "game did not terminate"
        action = rng.choice(env.legal_actions())
        result = env.step(action)
        check_state_invariants(result.next_state)
        moves.append(action)
        rewards.append(result.reward)
        states.append(result.next_state)
    return env, moves, states, rewards


@pytest.fixture(params=SEEDS, ids=lambda s: f"seed{s}")
def game(request):
    seed = request.param
    env, moves, states, rewards = play_random_game(seed)
    return seed, env, moves, states, rewards


class TestFullGame:
    def test_game_ends_in_a_consistent_terminal_state(self, game):
        _, env, moves, states, rewards = game
        final = env.state
        assert final.terminated is True
        assert final.move_count == len(moves) <= N * N
        assert env.legal_actions() == []
        winner = final.winner
        assert winner in (Player.X, Player.O, None)
        if winner is None:
            assert len(moves) == N * N
            assert env.result(Player.X) == env.result(Player.O) == 0.0
        else:
            assert env.result(winner) == 1.0
            other = Player.O if winner == Player.X else Player.X
            assert env.result(other) == -1.0
        # reward: chỉ nước cuối có thể khác 0; thắng thì 1.0
        assert all(r == 0.0 for r in rewards[:-1])
        assert rewards[-1] == (0.0 if winner is None else 1.0)

    def test_only_the_last_move_ends_the_game(self, game):
        _, _, moves, states, _ = game
        assert all(not s.terminated for s in states[:-1])
        assert states[-1].terminated is True

    def test_same_seed_gives_the_same_game(self, game):
        seed, env, moves, _, _ = game
        env2, moves2, _, _ = play_random_game(seed)
        assert moves2 == moves
        assert env2.state == env.state

    def test_replaying_the_moves_on_a_fresh_env_reproduces_the_state(self, game):
        _, env, moves, states, _ = game
        replay = new_env()
        for index, move in enumerate(moves, start=1):
            replay.step(move)
            assert replay.state == states[index]
        assert replay.state == env.state


class TestCloneAndUndoTogether:
    def test_simulating_on_a_clone_does_not_disturb_the_real_game(self, game):
        seed, _, moves, states, _ = game
        cut = len(moves) // 2
        env = new_env()
        for move in moves[:cut]:
            env.step(move)
        before = env.state

        probe = env.clone_env()
        rng = random.Random(seed + 1000)
        while not probe.is_terminal():
            probe.step(rng.choice(probe.legal_actions()))
        assert probe.is_terminal() is True
        assert env.state == before and env.is_terminal() is False

        for move in moves[cut:]:  # ván thật tiếp tục như cũ
            env.step(move)
        assert env.state == states[-1]

    def test_undo_walks_back_through_every_state_of_the_game(self, game):
        _, env, moves, states, _ = game
        for index in range(len(moves), 0, -1):
            restored = env.undo()
            assert restored == states[index - 1]
            check_state_invariants(restored)
        with pytest.raises(UndoError):
            env.undo()
        assert env.state == states[0]

    def test_undo_the_last_move_and_play_it_again(self, game):
        _, env, moves, states, _ = game
        env.undo()
        assert env.is_terminal() is False
        result = env.step(moves[-1])
        assert result.next_state == states[-1]
        assert env.state == states[-1]

    def test_reset_after_a_full_game_starts_a_clean_game(self, game):
        _, env, _, _, _ = game
        env.reset()
        assert env.state == new_env().state
        assert env.is_terminal() is False
        with pytest.raises(UndoError):
            env.undo()
        env.step((5, 5))
        assert env.state.move_count == 1


class TestGameRecordIntegration:
    def test_a_finished_game_becomes_a_valid_record_and_survives_json(self, game, tmp_path):
        seed, env, moves, _, rewards = game
        record = GameRecord(
            contract_version=CONTRACT_VERSION,
            game_id=f"smoke-{seed}",
            config=GameConfig(),
            seed=seed,
            x_agent="Random-Thiện",
            o_agent="Random",
            moves=[
                MoveRecord(
                    ply=i + 1,
                    player=Player.X if i % 2 == 0 else Player.O,
                    action=action,
                    reward=rewards[i],
                )
                for i, action in enumerate(moves)
            ],
            terminated=env.state.terminated,
            winner=env.state.winner,
        )
        check_record_invariants(record)

        path = tmp_path / "games.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(record_to_json(record), ensure_ascii=False) + "\n")
        with path.open(encoding="utf-8") as handle:
            loaded = record_from_json(json.loads(handle.readline()))
        assert loaded == record

        # Bản ghi đủ để tái hiện đúng ván đã chơi.
        replay = new_env()
        for move in loaded.moves:
            replay.step(move.action)
        assert replay.state == env.state
