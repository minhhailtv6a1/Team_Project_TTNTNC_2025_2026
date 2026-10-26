import ast
import inspect
import json
import random
from pathlib import Path

import pytest

import core.engine.game_env as game_env_module
from core.engine.game_env import CaroEnv
from core.engine.interfaces import (
    GameEnv, GameConfig, InvalidActionError, InvalidActionReason, Player,
)
from core.engine.rules import RuleEngine

N = 11

# ------------------------------------------------------------------ helpers
def play(env, actions):
    last = None
    for a in actions:
        last = env.step(a)
    return last


def x_wins_row0():
    seq = []
    for i in range(5):
        seq.append((0, i))
        if i < 4:
            seq.append((1, i))
    return seq


def draw_sequence():
    xs = [(r, c) for r in range(N) for c in range(N) if (r // 2 + c) % 2 == 0]
    os_ = [(r, c) for r in range(N) for c in range(N) if (r // 2 + c) % 2 == 1]
    assert len(xs) == 61 and len(os_) == 60
    seq = []
    for i in range(61):
        seq.append(xs[i])
        if i < 60:
            seq.append(os_[i])
    return seq


def full_snapshot(env):
    return (env.state, env.legal_actions(), env.render(), env.is_terminal())


# ------------------------------------------------------------------ reset / legal_actions
def test_reset_initial_state():
    env = CaroEnv()
    s = env.reset()
    assert all(v == 0 for row in s.board for v in row)
    assert (s.current_player, s.last_action, s.move_count, s.terminated, s.winner) == (Player.X, None, 0, False, None)
    la = env.legal_actions()
    assert len(la) == 121 and la == sorted(la) and la[0] == (0, 0) and la[-1] == (10, 10)
    assert env.result(Player.X) is None and env.is_terminal() is False


def test_reset_accepts_seed_and_is_deterministic():
    env = CaroEnv()
    assert env.reset(seed=1) == env.reset(seed=999) == env.reset()


def test_reset_clears_terminal_state_after_win():
    env = CaroEnv()
    play(env, x_wins_row0())
    assert env.is_terminal()
    s = env.reset()
    assert (s.terminated, s.winner, s.last_action, s.move_count, s.current_player) == (False, None, None, 0, Player.X)
    assert len(env.legal_actions()) == 121
    env.step((5, 5))  # chơi lại được


def test_legal_actions_returns_fresh_list():
    env = CaroEnv()
    la = env.legal_actions()
    la.clear()
    assert len(env.legal_actions()) == 121


def test_legal_actions_shrinks_and_excludes_played_cells():
    env = CaroEnv()
    env.step((3, 3))
    la = env.legal_actions()
    assert len(la) == 120 and (3, 3) not in la


# ------------------------------------------------------------------ step: non-terminal
def test_step_non_terminal_metadata_and_reward():
    env = CaroEnv()
    r = env.step((4, 5))
    s = r.next_state
    assert r.reward == 0.0 and r.done is False and r.winner is None
    assert s.board[4][5] == 1
    assert (s.current_player, s.last_action, s.move_count, s.terminated, s.winner) == (Player.O, (4, 5), 1, False, None)
    r2 = env.step((4, 6))
    assert r2.next_state.board[4][6] == -1 and r2.next_state.current_player == Player.X
    assert r2.next_state.move_count == 2 and r2.next_state.last_action == (4, 6)


def test_step_result_invariants_hold_each_move():
    env = CaroEnv()
    rng = random.Random(1)
    for _ in range(30):
        r = env.step(rng.choice(env.legal_actions()))
        assert r.done == r.next_state.terminated and r.winner == r.next_state.winner
        assert r.next_state == env.state


# ------------------------------------------------------------------ step: win
def test_x_win_reward_winner_and_state():
    env = CaroEnv()
    r = play(env, x_wins_row0())
    assert r.done is True and r.winner == Player.X and r.reward == 1.0
    s = r.next_state
    assert s.terminated and s.winner == Player.X and s.last_action == (0, 4) and s.move_count == 9
    assert s.current_player == Player.O  # người dự kiến đi tiếp, kể cả khi terminal
    assert env.is_terminal()


def test_o_win_reward_is_from_last_mover_perspective():
    env = CaroEnv()
    seq = [(5, 10), (0, 0), (6, 10), (0, 1), (7, 10), (0, 2), (8, 10), (0, 3), (5, 0), (0, 4)]
    r = play(env, seq)
    assert r.done and r.winner == Player.O and r.reward == 1.0  # O vừa đi và thắng
    assert r.next_state.current_player == Player.X


def test_non_winning_move_after_blocked_five_is_not_terminal():
    env = CaroEnv()
    seq = [(1, 1), (1, 0), (1, 2), (1, 6), (1, 3), (9, 9), (1, 4), (9, 8), (1, 5), (9, 7)]
    # X: (1,1)..(1,5) ; O chặn (1,0) và (1,6)
    r = play(env, seq)
    assert r.done is False and r.winner is None and r.reward == 0.0


# ------------------------------------------------------------------ draw
def test_draw_full_board():
    env = CaroEnv()
    seq = draw_sequence()
    r = play(env, seq[:-1])
    assert r.done is False
    r = env.step(seq[-1])
    assert r.done is True and r.winner is None and r.reward == 0.0
    s = r.next_state
    assert s.terminated and s.winner is None and s.move_count == 121
    assert env.result(Player.X) == 0.0 and env.result(Player.O) == 0.0
    assert env.legal_actions() == []


# ------------------------------------------------------------------ result()
def test_result_all_cases():
    env = CaroEnv()
    assert env.result(Player.X) is None and env.result(Player.O) is None
    play(env, x_wins_row0())
    assert env.result(Player.X) == 1.0 and env.result(Player.O) == -1.0

    env2 = CaroEnv()
    play(env2, [(5, 10), (0, 0), (6, 10), (0, 1), (7, 10), (0, 2), (8, 10), (0, 3), (5, 0), (0, 4)])
    assert env2.result(Player.O) == 1.0 and env2.result(Player.X) == -1.0


@pytest.mark.parametrize("bad", [Player.EMPTY, 1, -1, 0, None, "X", True])
def test_result_rejects_invalid_player(bad):
    env = CaroEnv()
    with pytest.raises(ValueError):
        env.result(bad)


def test_result_is_pure():
    env = CaroEnv()
    before = full_snapshot(env)
    env.result(Player.X)
    env.is_terminal()
    assert full_snapshot(env) == before


# ------------------------------------------------------------------ terminal guard
def test_step_after_terminal_raises_game_over_and_keeps_state():
    env = CaroEnv()
    play(env, x_wins_row0())
    before = full_snapshot(env)
    for action in [(9, 9), (0, 0), (-1, 0), "garbage", None]:  # GAME_OVER được xét trước mọi validation khác
        with pytest.raises(InvalidActionError) as ei:
            env.step(action)
        assert ei.value.reason == InvalidActionReason.GAME_OVER and ei.value.action == action
        assert full_snapshot(env) == before


def test_step_after_draw_raises_game_over():
    env = CaroEnv()
    play(env, draw_sequence())
    with pytest.raises(InvalidActionError) as ei:
        env.step((0, 0))
    assert ei.value.reason == InvalidActionReason.GAME_OVER


# ------------------------------------------------------------------ invalid actions (atomic)
@pytest.mark.parametrize("action", [
    [3, 3], (3,), (3, 3, 3), (3.0, 3), (3, 3.5), (True, 3), (3, False), ("3", 3), None, 33, "ab", (), ((1,), 2),
])
def test_malformed_actions(action):
    env = CaroEnv()
    env.step((5, 5))
    before = full_snapshot(env)
    with pytest.raises(InvalidActionError) as ei:
        env.step(action)
    assert ei.value.reason == InvalidActionReason.MALFORMED
    assert ei.value.action == action or ei.value.action is action
    assert full_snapshot(env) == before


@pytest.mark.parametrize("action", [(-1, 0), (0, -1), (11, 0), (0, 11), (100, 100), (-5, -5)])
def test_out_of_bounds_actions(action):
    env = CaroEnv()
    before = full_snapshot(env)
    with pytest.raises(InvalidActionError) as ei:
        env.step(action)
    assert ei.value.reason == InvalidActionReason.OUT_OF_BOUNDS
    assert full_snapshot(env) == before


def test_occupied_action():
    env = CaroEnv()
    env.step((2, 2))
    before = full_snapshot(env)
    with pytest.raises(InvalidActionError) as ei:
        env.step((2, 2))
    assert ei.value.reason == InvalidActionReason.OCCUPIED and ei.value.action == (2, 2)
    assert full_snapshot(env) == before
    env.step((2, 3))  # vẫn chơi tiếp được, lượt không bị lệch
    assert env.state.current_player == Player.X


def test_error_messages_are_nonempty_and_consistent():
    env = CaroEnv()
    env.step((0, 0))
    msgs = []
    for a in [(0, 0), (99, 0), "x"]:
        with pytest.raises(InvalidActionError) as ei:
            env.step(a)
        msgs.append(str(ei.value))
    assert all(m for m in msgs) and isinstance(msgs[0], str)


def test_integer_subclasses_are_accepted():
    class Idx(int):  # int subclass (không phải bool) thể hiện số nguyên thực
        pass

    env = CaroEnv()
    r = env.step((Idx(1), Idx(2)))
    assert r.next_state.last_action == (1, 2)
    assert isinstance(r.next_state.last_action[0], int)


# ------------------------------------------------------------------ defensive snapshots
def test_returned_states_are_defensive_copies():
    env = CaroEnv()
    s0 = env.reset()
    s0.board[0][0] = 99
    assert env.state.board[0][0] == 0
    r = env.step((1, 1))
    r.next_state.board[1][1] = 0
    r.next_state.board[2][2] = 1
    assert env.state.board[1][1] == 1 and env.state.board[2][2] == 0
    st = env.state
    st.board[3][3] = -1
    assert env.state.board[3][3] == 0
    assert env.state is not env.state


def test_state_is_frozen():
    env = CaroEnv()
    with pytest.raises(Exception):
        env.state.move_count = 5


# ------------------------------------------------------------------ render
def test_render_returns_str_without_mutation():
    env = CaroEnv()
    env.step((0, 0))
    before = env.state
    text = env.render()
    assert isinstance(text, str) and "Current Player: O" in text and text.splitlines()[0].startswith("X")
    assert len(text.splitlines()) == N + 1 and env.state == before


def test_render_reports_outcome_when_terminal():
    env = CaroEnv()
    play(env, x_wins_row0())
    assert "Winner: X" in env.render()
    env2 = CaroEnv()
    play(env2, draw_sequence())
    assert "Draw" in env2.render()


# ------------------------------------------------------------------ property: engine nhất quán với RuleEngine quét toàn bàn
def test_random_games_stay_consistent_with_full_scan_and_invariants():
    rng = random.Random(2026)
    wins = draws = 0
    for _ in range(150):
        env = CaroEnv()
        while not env.is_terminal():
            before_count = env.state.move_count
            actor = env.state.current_player
            r = env.step(rng.choice(env.legal_actions()))
            s = r.next_state
            assert s.move_count == before_count + 1
            assert s.move_count == sum(v != 0 for row in s.board for v in row)
            assert s.current_player == (Player.X if s.move_count % 2 == 0 else Player.O)
            done, winner = RuleEngine.is_terminal(s.board, env.config)
            assert (r.done, r.winner) == (done, winner)
            assert r.reward == (1.0 if winner == actor else 0.0)
        assert env.legal_actions() == []
        if env.state.winner is not None:
            wins += 1
            assert env.result(env.state.winner) == 1.0
        else:
            draws += 1
            assert env.result(Player.X) == 0.0
    assert wins > 0


# ------------------------------------------------------------------ tuân thủ GameEnv protocol (interfaces.py của M3)
def test_caro_env_satisfies_game_env_protocol():
    from core.engine.interfaces import GameEnv
    assert isinstance(CaroEnv(), GameEnv)


def test_env_never_mutates_frozen_state_objects():
    env = CaroEnv()
    s1 = env.state
    env.step((0, 0))
    s2 = env.state
    assert s1 is not s2 and s1.move_count == 0 and s2.move_count == 1
    assert s1.board is not s2.board


# ------------------------------------------------------------------ replay fixture nhóm qua CaroEnv
_FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "test_vectors.json").read_text(encoding="utf-8"))
_TEAM_CASES = _FIXTURE["test_cases"]


@pytest.mark.parametrize("tc", _TEAM_CASES, ids=[t["id"] for t in _TEAM_CASES])
def test_team_fixture_replayed_through_env(tc):
    env = CaroEnv()
    moves = tc["board_moves"]
    for i, m in enumerate(moves):
        assert env.state.current_player == Player(m["player"]), f"nước {i} sai lượt"
        r = env.step(tuple(m["action"]))
        if i < len(moves) - 1:
            assert r.done is False, f"ván kết thúc sớm ở nước {i}"
    expected = None if tc["expected_winner"] is None else Player(tc["expected_winner"])
    s = env.state
    assert s.terminated == tc["terminated"] and s.winner == expected
    assert (r.done, r.winner) == (tc["terminated"], expected)
    assert s.move_count == len(moves)

    if tc["terminated"]:
        assert env.legal_actions() == []
        assert r.reward == (1.0 if expected is not None else 0.0)
        if expected is None:  # hòa
            assert env.result(Player.X) == 0.0 and env.result(Player.O) == 0.0 and s.move_count == 121
        else:
            assert env.result(expected) == 1.0 and env.result(Player(-int(expected))) == -1.0
            assert expected == Player(moves[-1]["player"])  # người đi nước cuối thắng
        with pytest.raises(InvalidActionError) as ei:
            env.step((0, 0))
        assert ei.value.reason == InvalidActionReason.GAME_OVER
    else:
        assert r.reward == 0.0 and env.result(Player.X) is None
        assert len(env.legal_actions()) == 121 - len(moves)

    # undo toàn bộ về bàn rỗng, và clone cuối ván độc lập
    clone = env.clone_env()
    assert clone.state == env.state
    for _ in moves:
        env.undo()
    assert env.state == CaroEnv().state
    assert clone.state.move_count == len(moves)


# ================================================================== bổ sung theo tiêu chí
def test_hoa_chi_khi_ban_day_va_chua_co_winner():
    env = CaroEnv()
    seq = draw_sequence()
    for a in seq[:-1]:
        r = env.step(a)
        assert r.done is False and r.winner is None  # 120 nước đầu: chưa hòa dù gần đầy
    r = env.step(seq[-1])
    assert r.done and r.winner is None and env.state.move_count == N * N
    assert RuleEngine.is_board_full(env.state.board, N) and RuleEngine.check_winner(env.state.board, env.config) is None


def test_legal_actions_empty_when_terminal():
    env = CaroEnv()
    play(env, x_wins_row0())
    assert env.legal_actions() == []
    env2 = CaroEnv()
    play(env2, draw_sequence())
    assert env2.legal_actions() == []


def test_terminal_is_evaluated_exactly_once_per_step(monkeypatch):
    calls = {"from_action": 0, "full_scan": 0, "is_terminal": 0}
    orig_from = RuleEngine.check_winner_from_action
    orig_full = RuleEngine.check_winner
    orig_term = RuleEngine.is_terminal

    def from_action(*a, **k):
        calls["from_action"] += 1
        return orig_from(*a, **k)

    def full(*a, **k):
        calls["full_scan"] += 1
        return orig_full(*a, **k)

    def term(*a, **k):
        calls["is_terminal"] += 1
        return orig_term(*a, **k)

    monkeypatch.setattr(RuleEngine, "check_winner_from_action", staticmethod(from_action))
    monkeypatch.setattr(RuleEngine, "check_winner", staticmethod(full))
    monkeypatch.setattr(RuleEngine, "is_terminal", staticmethod(term))
    env = CaroEnv()
    for a in [(0, 0), (1, 1), (0, 1)]:
        env.step(a)
    assert calls == {"from_action": 3, "full_scan": 0, "is_terminal": 0}
    # query/undo/clone không kiểm tra luật lại
    env.is_terminal(); env.result(Player.X); env.legal_actions(); env.undo(); env.clone_env(); env.render()
    assert calls["from_action"] == 3 and calls["full_scan"] == 0


def test_game_env_has_no_mock_todo_or_stub_code():
    src = inspect.getsource(game_env_module)
    lowered = src.lower()
    assert "todo" not in lowered and "mock" not in lowered and "notimplemented" not in lowered
    tree = ast.parse(src)
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.Pass)]
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        body = [b for b in fn.body if not (isinstance(b, ast.Expr) and isinstance(getattr(b, "value", None), ast.Constant))]
        assert body, f"hàm {fn.name} chỉ có docstring (stub)"