# File: tests/test_term_result_contract.py
"""Contract test C2-TERM và C2-RESULT cho ``CaroEnv`` (caro-v2, mục 5.2).

C2-TERM   : khi ván kết thúc (thắng hoặc hòa) ``legal_actions() == []``,
            ``step()`` tiếp theo ném GAME_OVER, ``is_terminal()`` luôn khớp
            ``state.terminated`` và không có side effect, ``reset()`` xóa sạch.
C2-RESULT : ``result(player)`` trả ``None`` (chưa xong), ``0.0`` (hòa), ``1.0``
            (player thắng), ``-1.0`` (đối thủ thắng); ``Player.EMPTY`` hoặc sai
            kiểu ném ``ValueError``.

Ba ván kết thúc dùng chung: X thắng (9 nước), O thắng (10 nước), hòa (121 nước).
Chỉ dùng public API. Trước khi PR engine của M2 merge, chạy với
``CARO_C2_XFAIL=1`` để đánh dấu cả file là xfail (không strict).
"""
from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import (
    InvalidActionError,
    InvalidActionReason,
    Player,
    StepResult,
    UndoError,
)
from helpers.helpers_contract import check_state_invariants

pytestmark = pytest.mark.xfail(
    os.environ.get("CARO_C2_XFAIL") == "1",
    reason="Chờ PR engine của M2 (contract mục 11.2)",
    strict=False,
)

N = 11
Cell = tuple[int, int]


# ---------------------------------------------------------------------------
# Ba ván kết thúc dùng chung
# ---------------------------------------------------------------------------
def _interleave(x_cells: list[Cell], o_cells: list[Cell]) -> list[Cell]:
    assert len(x_cells) - len(o_cells) in (0, 1)
    return [
        x_cells[i // 2] if i % 2 == 0 else o_cells[i // 2]
        for i in range(len(x_cells) + len(o_cells))
    ]


# X thắng ở nước 9: chuỗi ngang (5,3)-(5,7), hai đầu trống; O có 4 quân rời ở hàng 0.
X_WIN_MOVES: list[Cell] = [(5, 3), (0, 0), (5, 4), (0, 1), (5, 5), (0, 2), (5, 6), (0, 3), (5, 7)]

# O thắng ở nước 10: chuỗi dọc (1,0)-(5,0), hai đầu trống; X có 5 quân phụ rải rác.
O_WIN_MOVES: list[Cell] = _interleave(
    [(8, 2), (8, 8), (10, 5), (6, 10), (10, 10)],
    [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)],
)


def _draw_moves() -> list[Cell]:
    """121 nước tạo bàn đầy không có chuỗi 5 (X 61 ô, O 60 ô)."""
    x_cells = [(r, c) for r in range(N) for c in range(N) if ((r + 2 * c) // 2) % 2 == 0]
    o_cells = [(r, c) for r in range(N) for c in range(N) if ((r + 2 * c) // 2) % 2 == 1]
    return _interleave(x_cells, o_cells)


DRAW_MOVES: list[Cell] = _draw_moves()

# tên ván -> (danh sách nước đi, người thắng hoặc None nếu hòa)
GAMES: dict[str, tuple[list[Cell], Player | None]] = {
    "x_win": (X_WIN_MOVES, Player.X),
    "o_win": (O_WIN_MOVES, Player.O),
    "draw": (DRAW_MOVES, None),
}
GAME_NAMES = list(GAMES)


def opponent(player: Player) -> Player:
    return Player.O if player == Player.X else Player.X


def mover_of_last_move(moves: list[Cell]) -> Player:
    return Player.X if len(moves) % 2 == 1 else Player.O


def expected_result(player: Player, winner: Player | None) -> float:
    if winner is None:
        return 0.0
    return 1.0 if player == winner else -1.0


def new_env() -> CaroEnv:
    env = CaroEnv()
    env.reset()
    return env


@dataclass
class Finished:
    env: CaroEnv
    last_result: StepResult
    moves: list[Cell]
    winner: Player | None

    @property
    def last_mover(self) -> Player:
        return mover_of_last_move(self.moves)


def play_game(name: str) -> Finished:
    moves, winner = GAMES[name]
    env = new_env()
    result = None
    for index, move in enumerate(moves, start=1):
        result = env.step(move)
        if index < len(moves):
            assert not result.done, f"{name}: fixture ended early at ply {index}"
    assert result is not None
    return Finished(env, result, moves, winner)


@pytest.fixture(params=GAME_NAMES)
def finished(request) -> Finished:
    return play_game(request.param)


def snapshot(env) -> tuple:
    return (env.state, env.legal_actions(), env.is_terminal(), env.render())


# ---------------------------------------------------------------------------
# Kiểm tra bản thân fixture (lỗi ở đây là lỗi luật, không phải lỗi terminal)
# ---------------------------------------------------------------------------
class TestFixtures:
    def test_games_have_expected_length_and_outcome(self):
        assert [len(GAMES[n][0]) for n in GAME_NAMES] == [9, 10, 121]
        for name in GAME_NAMES:
            finished = play_game(name)
            state = finished.env.state
            assert state.terminated is True, name
            assert state.winner == finished.winner, name
            assert state.move_count == len(finished.moves), name


# ---------------------------------------------------------------------------
# C2-TERM
# ---------------------------------------------------------------------------
class TestTerminalState:
    def test_metadata_after_the_final_move(self, finished):
        state = finished.env.state
        assert state.terminated is True
        assert state.winner == finished.winner
        assert state.winner is not Player.EMPTY
        assert state.move_count == len(finished.moves)
        assert state.last_action == finished.moves[-1]
        # Lượt vẫn đổi sang đối thủ của người vừa đi, kể cả khi terminal (mục 4.2).
        assert state.current_player == opponent(finished.last_mover)
        check_state_invariants(state)

    def test_step_result_of_the_final_move(self, finished):
        result = finished.last_result
        assert result.done is True
        assert result.winner == finished.winner
        assert result.next_state == finished.env.state
        assert result.next_state.terminated is True

    def test_is_terminal_true(self, finished):
        assert finished.env.is_terminal() is True

    def test_legal_actions_is_empty(self, finished):
        assert finished.env.legal_actions() == []

    def test_legal_actions_is_empty_even_with_empty_cells_left(self):
        # Ván thắng vẫn còn nhiều ô trống: [] là do terminal guard, không phải do bàn đầy.
        for name in ("x_win", "o_win"):
            env = play_game(name).env
            assert any(0 in row for row in env.state.board)
            assert env.legal_actions() == []

    def test_draw_board_is_completely_full(self):
        env = play_game("draw").env
        assert all(cell != Player.EMPTY for row in env.state.board for cell in row)
        assert env.state.winner is None

    def test_legal_actions_returns_a_fresh_list_when_terminal(self, finished):
        actions = finished.env.legal_actions()
        actions.append((0, 0))
        assert finished.env.legal_actions() == []

    def test_every_cell_is_rejected_with_game_over(self, finished):
        env = finished.env
        before = snapshot(env)
        for row in range(N):
            for col in range(N):
                with pytest.raises(InvalidActionError) as info:
                    env.step((row, col))
                assert info.value.reason is InvalidActionReason.GAME_OVER
                assert info.value.action == (row, col)
        assert snapshot(env) == before

    def test_game_over_error_does_not_create_history_or_unlock_the_game(self, finished):
        env = finished.env
        for _ in range(3):
            with pytest.raises(InvalidActionError):
                env.step((10, 10))
        assert env.is_terminal() is True
        assert env.legal_actions() == []
        # Mọi lần undo thành công chỉ hoàn tác các nước đã đi, không có mục history thừa.
        undone = 0
        exhausted = False
        probe = env.clone_env()
        for _ in range(N * N + 1):  # có giới hạn: engine sai không được làm test treo
            try:
                probe.undo()
            except UndoError:
                exhausted = True
                break
            undone += 1
        assert exhausted, "undo() never raised UndoError on an empty history"
        assert undone == len(finished.moves)


class TestTerminalFlagConsistency:
    @pytest.mark.parametrize("name", GAME_NAMES)
    def test_flags_agree_after_every_ply_of_a_whole_game(self, name):
        moves, winner = GAMES[name]
        env = new_env()
        assert env.is_terminal() is False
        assert env.state.terminated is False
        for ply, move in enumerate(moves, start=1):
            result = env.step(move)
            final = ply == len(moves)
            assert result.done is final, f"ply {ply}"
            assert result.next_state.terminated is final
            assert env.state.terminated is final
            assert env.is_terminal() is final
            assert result.winner == (winner if final else None)
            assert env.state.winner == (winner if final else None)
            if final:
                assert env.legal_actions() == []
            else:
                assert len(env.legal_actions()) == N * N - ply

    def test_is_terminal_has_no_side_effects(self, finished):
        before = snapshot(finished.env)
        for _ in range(5):
            assert finished.env.is_terminal() is True
        assert snapshot(finished.env) == before

    def test_is_terminal_has_no_side_effects_mid_game(self):
        env = new_env()
        for move in X_WIN_MOVES[:4]:
            env.step(move)
        before = snapshot(env)
        for _ in range(5):
            assert env.is_terminal() is False
        assert snapshot(env) == before

    def test_winner_is_never_empty_and_terminated_false_implies_no_winner(self):
        for name in GAME_NAMES:
            moves, _ = GAMES[name]
            env = new_env()
            for move in moves:
                env.step(move)
                state = env.state
                assert state.winner in (Player.X, Player.O, None)
                if not state.terminated:
                    assert state.winner is None


class TestTerminalReset:
    def test_reset_returns_to_a_fresh_playable_game(self, finished):
        env = finished.env
        initial = new_env().state
        returned = env.reset()
        assert returned == initial
        assert env.state == initial
        assert env.is_terminal() is False
        assert env.state.terminated is False and env.state.winner is None
        assert env.state.last_action is None and env.state.move_count == 0
        assert env.state.current_player == Player.X
        assert env.legal_actions() == [(r, c) for r in range(N) for c in range(N)]
        assert env.result(Player.X) is None and env.result(Player.O) is None
        check_state_invariants(env.state)

    def test_reset_clears_undo_history(self, finished):
        finished.env.reset()
        with pytest.raises(UndoError):
            finished.env.undo()

    def test_game_is_playable_again_after_reset(self, finished):
        env = finished.env
        env.reset()
        result = env.step((5, 5))
        assert result.next_state.move_count == 1
        assert result.next_state.last_action == (5, 5)
        assert result.done is False

    def test_reset_accepts_seed_and_is_deterministic(self, finished):
        env = finished.env
        first = env.reset(seed=7)
        second = env.reset(seed=7)
        third = env.reset()
        assert first == second == third == new_env().state

    def test_reset_returns_independent_snapshot(self, finished):
        env = finished.env
        returned = env.reset()
        returned.board[0][0] = 1
        assert env.state.board[0][0] == 0

    @pytest.mark.parametrize("name", GAME_NAMES)
    def test_same_game_can_be_replayed_after_reset(self, name):
        moves, winner = GAMES[name]
        env = new_env()
        for _ in range(2):
            for move in moves:
                env.step(move)
            assert env.is_terminal() is True
            assert env.state.winner == winner
            env.reset()
            assert env.is_terminal() is False


class TestTerminalClone:
    def test_clone_of_a_finished_game_is_also_finished(self, finished):
        clone = finished.env.clone_env()
        assert clone.is_terminal() is True
        assert clone.state == finished.env.state
        assert clone.state.winner == finished.winner
        assert clone.legal_actions() == []

    def test_clone_of_a_finished_game_rejects_further_moves(self, finished):
        clone = finished.env.clone_env()
        before = finished.env.state
        with pytest.raises(InvalidActionError) as info:
            clone.step((10, 10))
        assert info.value.reason is InvalidActionReason.GAME_OVER
        assert finished.env.state == before

    def test_resetting_a_clone_does_not_reopen_the_original(self, finished):
        clone = finished.env.clone_env()
        clone.reset()
        assert clone.is_terminal() is False
        assert finished.env.is_terminal() is True
        assert finished.env.legal_actions() == []


# ---------------------------------------------------------------------------
# C2-RESULT
# ---------------------------------------------------------------------------
INVALID_PLAYERS = [
    pytest.param(Player.EMPTY, id="Player.EMPTY"),
    pytest.param(0, id="int0"),
    pytest.param(2, id="int2"),
    pytest.param(-2, id="int-2"),
    pytest.param(3, id="int3"),
    pytest.param("X", id="str-X"),
    pytest.param("O", id="str-O"),
    pytest.param(None, id="None"),
    pytest.param(2.5, id="float"),
    pytest.param((1,), id="tuple"),
    pytest.param([], id="list"),
    pytest.param(object(), id="object"),
]


class TestResultNonTerminal:
    @pytest.mark.parametrize("player", [Player.X, Player.O], ids=["X", "O"])
    def test_fresh_game_has_no_result(self, player):
        assert new_env().result(player) is None

    @pytest.mark.parametrize("player", [Player.X, Player.O], ids=["X", "O"])
    @pytest.mark.parametrize("plies", [1, 2, 5, 8])
    def test_game_in_progress_has_no_result(self, player, plies):
        env = new_env()
        for move in X_WIN_MOVES[:plies]:
            env.step(move)
        assert env.is_terminal() is False
        assert env.result(player) is None

    @pytest.mark.parametrize("name", GAME_NAMES)
    def test_no_result_on_any_ply_before_the_final_one(self, name):
        moves, _ = GAMES[name]
        env = new_env()
        for ply, move in enumerate(moves, start=1):
            if ply == len(moves):
                break
            env.step(move)
            assert env.result(Player.X) is None, f"ply {ply}"
            assert env.result(Player.O) is None, f"ply {ply}"

    def test_one_empty_cell_left_is_still_unfinished(self):
        env = new_env()
        for move in DRAW_MOVES[:-1]:
            env.step(move)
        assert env.result(Player.X) is None
        assert env.result(Player.O) is None


class TestResultTerminal:
    @pytest.mark.parametrize("player", [Player.X, Player.O], ids=["X", "O"])
    def test_result_is_from_the_players_point_of_view(self, finished, player):
        assert finished.env.result(player) == expected_result(player, finished.winner)

    def test_x_win_scores(self):
        env = play_game("x_win").env
        assert env.result(Player.X) == 1.0
        assert env.result(Player.O) == -1.0

    def test_o_win_scores(self):
        env = play_game("o_win").env
        assert env.result(Player.O) == 1.0
        assert env.result(Player.X) == -1.0

    def test_draw_scores_zero_for_both(self):
        env = play_game("draw").env
        assert env.result(Player.X) == 0.0
        assert env.result(Player.O) == 0.0

    def test_results_are_zero_sum(self, finished):
        env = finished.env
        assert env.result(Player.X) == -env.result(Player.O)

    def test_result_is_a_plain_float_not_a_step_result(self, finished):
        for player in (Player.X, Player.O):
            value = finished.env.result(player)
            assert type(value) is float
            assert not isinstance(value, StepResult)

    def test_result_agrees_with_state_winner(self, finished):
        state = finished.env.state
        for player in (Player.X, Player.O):
            value = finished.env.result(player)
            if state.winner is None:
                assert value == 0.0
            elif state.winner == player:
                assert value == 1.0
            else:
                assert value == -1.0

    def test_final_step_reward_equals_result_for_the_player_who_moved(self, finished):
        # Reward theo góc nhìn người vừa đi (mục 4.3) phải khớp result() của chính người đó.
        reward = finished.last_result.reward
        assert reward == finished.env.result(finished.last_mover)
        assert reward in (0.0, 1.0)  # CaroEnv chuẩn không tạo -1.0

    def test_result_is_stable_and_has_no_side_effects(self, finished):
        env = finished.env
        before = snapshot(env)
        first = [env.result(Player.X), env.result(Player.O)]
        for _ in range(3):
            assert [env.result(Player.X), env.result(Player.O)] == first
        assert snapshot(env) == before

    def test_result_has_no_side_effects_mid_game(self):
        env = new_env()
        for move in X_WIN_MOVES[:5]:
            env.step(move)
        before = snapshot(env)
        for _ in range(3):
            assert env.result(Player.X) is None
            assert env.result(Player.O) is None
        assert snapshot(env) == before

    def test_result_reverts_to_none_after_reset(self, finished):
        finished.env.reset()
        assert finished.env.result(Player.X) is None
        assert finished.env.result(Player.O) is None

    def test_clone_reports_the_same_result(self, finished):
        clone = finished.env.clone_env()
        for player in (Player.X, Player.O):
            assert clone.result(player) == finished.env.result(player)


class TestResultInvalidPlayer:
    @pytest.mark.parametrize("player", INVALID_PLAYERS)
    def test_invalid_player_raises_value_error_mid_game(self, player):
        env = new_env()
        env.step((5, 5))
        before = snapshot(env)
        with pytest.raises(ValueError):
            env.result(player)
        assert snapshot(env) == before

    @pytest.mark.parametrize("player", INVALID_PLAYERS)
    def test_invalid_player_raises_value_error_on_fresh_game(self, player):
        with pytest.raises(ValueError):
            new_env().result(player)

    @pytest.mark.parametrize("player", INVALID_PLAYERS)
    def test_invalid_player_raises_value_error_when_terminal(self, finished, player):
        before = snapshot(finished.env)
        with pytest.raises(ValueError):
            finished.env.result(player)
        assert snapshot(finished.env) == before

    def test_value_error_is_not_an_invalid_action_error(self):
        # InvalidActionError cũng là ValueError; result() không phải là một action.
        with pytest.raises(ValueError) as info:
            new_env().result(Player.EMPTY)
        assert not isinstance(info.value, InvalidActionError)
