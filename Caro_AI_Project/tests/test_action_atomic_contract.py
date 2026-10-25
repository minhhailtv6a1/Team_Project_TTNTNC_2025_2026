
"""Contract test C2-ACTION và C2-ATOMIC cho ``CaroEnv`` (caro-v2).

C2-ACTION: step() phân loại đúng lý do lỗi theo thứ tự chuẩn của contract
(mục 4.4): GAME_OVER -> MALFORMED -> OUT_OF_BOUNDS -> OCCUPIED.
C2-ATOMIC: mọi lỗi phải giữ nguyên board, lượt, metadata, terminal state và
history (mục 4.4 và 5.2).

Chỉ dùng public API của ``GameEnv``. "History" được quan sát gián tiếp bằng
số lần ``undo()`` thành công trên một bản ``clone_env()``.

Trước khi PR engine của M2 merge (contract mục 11.2), có thể chạy với
``CARO_C2_XFAIL=1`` để đánh dấu cả file là xfail (không strict, vì engine hiện
tại đã pass một phần test). Test đã đúng sẽ hiện là XPASS. Khi M2 merge, bỏ biến
môi trường này để mọi test trở thành bắt buộc.
"""
from __future__ import annotations

import copy
import os

import pytest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import (
    GameState,
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

# ---------------------------------------------------------------------------
# Fixture dữ liệu
# ---------------------------------------------------------------------------
# X thắng ở nước thứ 9 bằng chuỗi 5 ngang giữa bàn, hai đầu trống (không dính
# luật biên). O chỉ có 4 quân ở hàng 0.
X_WIN_MOVES = [
    (5, 3), (0, 0), (5, 4), (0, 1), (5, 5), (0, 2), (5, 6), (0, 3), (5, 7),
]

# Bốn nước đầu của một ván đang chơi: X(5,5) O(5,6) X(6,5) O(6,6) -> tới lượt X.
MID_GAME_MOVES = [(5, 5), (5, 6), (6, 5), (6, 6)]


def _draw_moves() -> list[tuple[int, int]]:
    """121 nước tạo bàn đầy không có chuỗi 5 nào (X 61 ô, O 60 ô).

    Tô màu theo ``((r + 2c) // 2) % 2 == 0`` -> X. Mọi bàn con của bàn cuối
    cũng không có chuỗi 5 nên không nước nào kết thúc ván sớm.
    """
    x_cells = [(r, c) for r in range(N) for c in range(N) if ((r + 2 * c) // 2) % 2 == 0]
    o_cells = [(r, c) for r in range(N) for c in range(N) if ((r + 2 * c) // 2) % 2 == 1]
    assert (len(x_cells), len(o_cells)) == (61, 60)
    return [x_cells[i // 2] if i % 2 == 0 else o_cells[i // 2] for i in range(N * N)]


DRAW_MOVES = _draw_moves()


class _Weird:
    """Action độc hại: truy cập len/iter đều ném lỗi."""

    def __len__(self):
        raise RuntimeError("len should not be called")

    def __iter__(self):
        raise RuntimeError("iter should not be called")


def _params(prefix: str, values: list) -> list:
    return [pytest.param(v, id=f"{prefix}{i}-{type(v).__name__}") for i, v in enumerate(values)]


MALFORMED_ACTIONS = _params(
    "mal",
    [
        40, 0, 5.5, None, "ab", "", b"ab", (), (1,), (1, 2, 3), [5, 5],
        (1.0, 2), (1, 2.0), (True, 0), (0, False), (True, True),
        ("1", "2"), (None, None), ((1, 2), 3), {1, 2}, {}, object(), _Weird(),
    ],
)
OUT_OF_BOUNDS_ACTIONS = _params(
    "oob",
    [(-1, 0), (0, -1), (11, 0), (0, 11), (-1, -1), (11, 11), (100, 3), (3, 100), (-11, 5), (10**9, 0)],
)
# Tuple có kiểu sai và tọa độ ngoài biên cùng lúc -> MALFORMED thắng OUT_OF_BOUNDS.
MALFORMED_BEATS_BOUNDS = _params("prec", [(True, 99), (1.5, 99), (-1, "x"), (99, 1.5), (None, -5)])
CORNER_AND_EDGE_ACTIONS = [
    (0, 0), (0, 10), (10, 0), (10, 10), (0, 5), (5, 0), (10, 5), (5, 10),
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def new_env() -> CaroEnv:
    env = CaroEnv()
    env.reset()
    return env


def play(env, moves) -> None:
    for move in moves:
        env.step(move)


def undo_depth(env) -> int:
    """Số lần undo() thành công trên bản clone (= độ sâu history quan sát được)."""
    probe = env.clone_env()
    depth = 0
    while depth <= N * N:
        try:
            probe.undo()
        except UndoError:
            return depth
        depth += 1
    raise AssertionError("undo history is longer than the board")


def snapshot(env) -> dict:
    return {
        "state": env.state,
        "legal": env.legal_actions(),
        "terminal": env.is_terminal(),
        "render": env.render(),
        "undo_depth": undo_depth(env),
    }


def assert_rejected(env, action, reason: InvalidActionReason | None = None) -> InvalidActionError:
    """step(action) phải ném InvalidActionError và không đổi gì quan sát được."""
    before = snapshot(env)
    with pytest.raises(InvalidActionError) as info:
        env.step(action)
    assert snapshot(env) == before, "failed step() changed the environment"
    check_state_invariants(env.state)
    if reason is not None:
        assert info.value.reason is reason
    assert info.value.action == action
    assert str(info.value), "error message must not be empty"
    return info.value


@pytest.fixture
def env() -> CaroEnv:
    return new_env()


@pytest.fixture
def mid_env() -> CaroEnv:
    e = new_env()
    play(e, MID_GAME_MOVES)
    return e


@pytest.fixture(params=["x_win", "draw"])
def terminal_env(request) -> CaroEnv:
    e = new_env()
    play(e, X_WIN_MOVES if request.param == "x_win" else DRAW_MOVES)
    return e


@pytest.fixture(params=["fresh", "mid_game", "x_win", "draw"])
def any_env(request) -> CaroEnv:
    e = new_env()
    moves = {"fresh": [], "mid_game": MID_GAME_MOVES, "x_win": X_WIN_MOVES, "draw": DRAW_MOVES}
    play(e, moves[request.param])
    return e


# ---------------------------------------------------------------------------
# Kiểm tra bản thân fixture (lỗi ở đây = lỗi luật, không phải lỗi action)
# ---------------------------------------------------------------------------
class TestFixtures:
    def test_x_win_sequence_ends_with_x_win(self):
        e = new_env()
        play(e, X_WIN_MOVES)
        assert e.state.terminated is True
        assert e.state.winner == Player.X
        assert e.state.move_count == len(X_WIN_MOVES) == 9

    def test_draw_sequence_fills_board_without_winner(self):
        assert len(DRAW_MOVES) == len(set(DRAW_MOVES)) == N * N
        e = new_env()
        play(e, DRAW_MOVES)
        assert e.state.terminated is True
        assert e.state.winner is None
        assert e.state.move_count == N * N

    def test_mid_game_is_not_terminal_and_x_to_move(self, mid_env):
        assert mid_env.state.terminated is False
        assert mid_env.state.current_player == Player.X


# ---------------------------------------------------------------------------
# C2-ACTION
# ---------------------------------------------------------------------------
class TestActionValidation:
    @pytest.mark.parametrize("action", MALFORMED_ACTIONS)
    def test_malformed_action(self, env, action):
        assert_rejected(env, action, InvalidActionReason.MALFORMED)

    @pytest.mark.parametrize("action", OUT_OF_BOUNDS_ACTIONS)
    def test_out_of_bounds_action(self, env, action):
        assert_rejected(env, action, InvalidActionReason.OUT_OF_BOUNDS)

    @pytest.mark.parametrize("action", MALFORMED_BEATS_BOUNDS)
    def test_malformed_takes_precedence_over_out_of_bounds(self, env, action):
        assert_rejected(env, action, InvalidActionReason.MALFORMED)

    @pytest.mark.parametrize("action", CORNER_AND_EDGE_ACTIONS)
    def test_corner_and_edge_cells_are_valid(self, env, action):
        result = env.step(action)
        assert isinstance(result, StepResult)
        state = result.next_state
        assert state.last_action == action
        assert state.move_count == 1
        assert state.board[action[0]][action[1]] == Player.X
        assert state.current_player == Player.O
        check_state_invariants(state)

    @pytest.mark.parametrize("action", [(5, 5), (6, 5)], ids=["own_stone", "own_stone_2"])
    def test_occupied_by_current_player(self, mid_env, action):
        # Đang tới lượt X; (5,5) và (6,5) là quân của X.
        assert_rejected(mid_env, action, InvalidActionReason.OCCUPIED)

    @pytest.mark.parametrize("action", [(5, 6), (6, 6)], ids=["opp_stone", "opp_stone_2"])
    def test_occupied_by_opponent(self, mid_env, action):
        assert_rejected(mid_env, action, InvalidActionReason.OCCUPIED)

    def test_occupied_on_first_move_repeat(self, env):
        env.step((5, 5))
        assert_rejected(env, (5, 5), InvalidActionReason.OCCUPIED)

    @pytest.mark.parametrize(
        "action",
        _params(
            "go",
            [(10, 10), (5, 3), (0, 0), (-1, 0), 40, None, (True, 0), [5, 5], object()],
        ),
    )
    def test_game_over_takes_precedence_over_every_other_reason(self, terminal_env, action):
        # Trong cả hai ván terminal: ô trống / ô đã chiếm / ngoài biên / sai kiểu
        # đều phải báo GAME_OVER (kiểm tra terminal đứng đầu).
        assert_rejected(terminal_env, action, InvalidActionReason.GAME_OVER)

    def test_error_is_value_error_with_reason_enum(self, env):
        error = assert_rejected(env, 40)
        assert isinstance(error, ValueError)
        assert isinstance(error.reason, InvalidActionReason)


# ---------------------------------------------------------------------------
# C2-ATOMIC
# ---------------------------------------------------------------------------
ATOMIC_BAD_ACTIONS = _params(
    "bad",
    [40, None, (1,), (1, 2, 3), [5, 5], (True, 0), (1.0, 2), (-1, 0), (0, 11), (11, 11), _Weird()],
)


class TestAtomicity:
    @pytest.mark.parametrize("action", ATOMIC_BAD_ACTIONS)
    def test_failed_step_changes_nothing_in_any_scenario(self, any_env, action):
        assert_rejected(any_env, action)

    def test_occupied_failure_changes_nothing(self, mid_env):
        for action in MID_GAME_MOVES:
            assert_rejected(mid_env, action, InvalidActionReason.OCCUPIED)

    def test_repeated_failures_are_idempotent(self, mid_env):
        before = snapshot(mid_env)
        for _ in range(5):
            for action in (40, (11, 0), (5, 5), None):
                with pytest.raises(InvalidActionError):
                    mid_env.step(action)
        assert snapshot(mid_env) == before

    def test_terminal_metadata_survives_failed_step(self, terminal_env):
        before = terminal_env.state
        with pytest.raises(InvalidActionError):
            terminal_env.step((10, 10))
        after = terminal_env.state
        assert after.terminated is True
        assert after.winner == before.winner
        assert after.move_count == before.move_count
        assert after.last_action == before.last_action
        assert terminal_env.is_terminal() is True
        assert terminal_env.legal_actions() == []

    def test_previously_returned_state_is_not_modified_by_failed_step(self, mid_env):
        held = mid_env.state
        held_copy = copy.deepcopy(held)
        with pytest.raises(InvalidActionError):
            mid_env.step((5, 5))
        assert held == held_copy
        assert mid_env.state == held
        assert mid_env.state.board is not held.board

    def test_failed_step_does_not_create_undo_history(self, env):
        for action in (40, (11, 0), None, [1, 2]):
            with pytest.raises(InvalidActionError):
                env.step(action)
        with pytest.raises(UndoError):
            env.undo()

    def test_failed_steps_do_not_disturb_existing_undo_history(self, env):
        initial = env.state
        moves = [(5, 5), (5, 6), (6, 5)]
        play(env, moves)
        for action in (40, (11, 0), (5, 5), None):
            with pytest.raises(InvalidActionError):
                env.step(action)
        for _ in moves:
            env.undo()
        assert env.state == initial
        with pytest.raises(UndoError):
            env.undo()

    def test_valid_step_after_failures_behaves_normally(self, mid_env):
        before = mid_env.state
        for action in (40, (11, 0), (5, 5)):
            with pytest.raises(InvalidActionError):
                mid_env.step(action)
        result = mid_env.step((0, 0))
        assert result.next_state.move_count == before.move_count + 1
        assert result.next_state.last_action == (0, 0)
        assert result.next_state.current_player == Player.O
        assert result.done is False
        check_state_invariants(result.next_state)

    def test_step_after_failed_terminal_step_still_rejected(self, terminal_env):
        for _ in range(3):
            assert_rejected(terminal_env, (10, 10), InvalidActionReason.GAME_OVER)


# ---------------------------------------------------------------------------
# Step thành công: đúng một nước và snapshot độc lập (nền cho C2-ATOMIC)
# ---------------------------------------------------------------------------
class TestSuccessfulStepBaseline:
    def test_each_successful_step_advances_exactly_one_ply(self, env):
        expected_player = Player.X
        for index, action in enumerate([(5, 5), (5, 6), (6, 5), (6, 6), (7, 7)], start=1):
            result = env.step(action)
            state = result.next_state
            assert state.move_count == index
            assert state.last_action == action
            assert state.board[action[0]][action[1]] == int(expected_player)
            expected_player = Player.O if expected_player == Player.X else Player.X
            assert state.current_player == expected_player
            assert state == env.state
            assert result.done is False and result.winner is None
            check_state_invariants(state)

    def test_next_state_is_independent_snapshot(self, env):
        result = env.step((5, 5))
        result.next_state.board[0][0] = 1  # consumer vi phạm quy ước read-only
        assert env.state.board[0][0] == 0
        assert env.state.board[5][5] == Player.X

    def test_earlier_results_are_not_changed_by_later_steps(self, env):
        first = env.step((5, 5))
        first_copy = copy.deepcopy(first)
        env.step((5, 6))
        env.step((6, 5))
        assert first == first_copy

    def test_state_property_returns_independent_snapshots(self, env):
        snapshot_a = env.state
        snapshot_a.board[3][3] = 1
        assert env.state.board[3][3] == 0
        assert env.state.board is not env.state.board

    def test_legal_actions_is_fresh_row_major_list(self, env):
        actions = env.legal_actions()
        assert actions == [(r, c) for r in range(N) for c in range(N)]
        actions.clear()
        assert len(env.legal_actions()) == N * N
        assert env.legal_actions() is not env.legal_actions()
        env.step((0, 0))
        assert env.legal_actions() == [(r, c) for r in range(N) for c in range(N)][1:]

    def test_win_step_reports_reward_and_terminal(self, env):
        play(env, X_WIN_MOVES[:-1])
        result = env.step(X_WIN_MOVES[-1])
        assert result.done is True and result.winner == Player.X
        assert result.reward == 1.0
        assert result.next_state.terminated is True
        assert result.next_state.winner == Player.X
        # Lượt vẫn đổi sang O sau nước thắng (contract mục 4.2).
        assert result.next_state.current_player == Player.O
        check_state_invariants(result.next_state)
