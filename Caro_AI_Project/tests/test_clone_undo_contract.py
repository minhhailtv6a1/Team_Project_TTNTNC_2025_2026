# File: tests/test_clone_undo_contract.py
"""Contract test C2-CLONE và C2-UNDO cho ``CaroEnv`` (caro-v2, mục 5.2).

C2-CLONE: ``clone_env()`` mang cùng config/state/terminal metadata/undo history;
          board và history độc lập HAI CHIỀU: step/undo/reset trên clone không
          ảnh hưởng bản gốc và ngược lại (Minimax/MCTS mô phỏng trên clone).
C2-UNDO : ``undo()`` hoàn tác đúng một ``step()`` thành công, khôi phục board,
          lượt, last_action, move_count, terminated, winner; dùng được sau thắng
          hoặc hòa; history rỗng ném ``UndoError`` và giữ nguyên state.

Chỉ dùng public API. Trước khi PR engine của M2 merge, chạy với
``CARO_C2_XFAIL=1`` để đánh dấu cả file là xfail (không strict).
"""
from __future__ import annotations

import os

import pytest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import (
    GameEnv,
    InvalidActionError,
    InvalidActionReason,
    Player,
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
# Dữ liệu ván chơi dùng chung
# ---------------------------------------------------------------------------
def _interleave(x_cells: list[Cell], o_cells: list[Cell]) -> list[Cell]:
    assert len(x_cells) - len(o_cells) in (0, 1)
    return [
        x_cells[i // 2] if i % 2 == 0 else o_cells[i // 2]
        for i in range(len(x_cells) + len(o_cells))
    ]


# Bốn nước đầu: X(5,5) O(5,6) X(6,5) O(6,6) -> tới lượt X, chưa kết thúc.
MID_MOVES: list[Cell] = [(5, 5), (5, 6), (6, 5), (6, 6)]
# X thắng ở nước 9 (chuỗi ngang (5,3)-(5,7), hai đầu trống).
X_WIN_MOVES: list[Cell] = [(5, 3), (0, 0), (5, 4), (0, 1), (5, 5), (0, 2), (5, 6), (0, 3), (5, 7)]
# O thắng ở nước 10 (chuỗi dọc (1,0)-(5,0), hai đầu trống).
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

SCENARIOS: dict[str, list[Cell]] = {
    "fresh": [],
    "mid": MID_MOVES,
    "x_win": X_WIN_MOVES,
    "o_win": O_WIN_MOVES,
    "draw": DRAW_MOVES,
}
ALL = list(SCENARIOS)
HISTORIC = [name for name in ALL if name != "fresh"]   # có ít nhất một nước để undo
OPEN = ["fresh", "mid"]                                 # còn nước để đi
FINISHED = ["x_win", "o_win", "draw"]
HARMLESS_CELL: Cell = (0, 6)  # ô trống, không tạo chuỗi nào trong x_win / o_win


def mover_of_last_move(moves: list[Cell]) -> Player:
    return Player.X if len(moves) % 2 == 1 else Player.O


def new_env() -> CaroEnv:
    env = CaroEnv()
    env.reset()
    return env


def play(env, moves: list[Cell]) -> None:
    for move in moves:
        env.step(move)


def build(name: str) -> CaroEnv:
    env = new_env()
    play(env, SCENARIOS[name])
    return env


def snapshot(env) -> tuple:
    return (env.state, env.legal_actions(), env.is_terminal(), env.render())


def drain(env) -> int:
    """Undo đến khi hết history; trả về số lần undo thành công."""
    count = 0
    while count <= N * N:
        try:
            env.undo()
        except UndoError:
            return count
        count += 1
    raise AssertionError("undo history is longer than the board")


def first_legal(env) -> Cell:
    return env.legal_actions()[0]


# ---------------------------------------------------------------------------
# Kiểm tra bản thân fixture
# ---------------------------------------------------------------------------
class TestFixtures:
    def test_scenarios_end_as_described(self):
        assert [len(SCENARIOS[n]) for n in ALL] == [0, 4, 9, 10, 121]
        assert build("mid").is_terminal() is False
        assert build("x_win").state.winner == Player.X
        assert build("o_win").state.winner == Player.O
        draw = build("draw").state
        assert draw.terminated is True and draw.winner is None

    def test_harmless_cell_is_empty_and_safe_in_both_wins(self):
        for name in ("x_win", "o_win"):
            env = build(name)
            assert env.state.board[HARMLESS_CELL[0]][HARMLESS_CELL[1]] == 0


# ---------------------------------------------------------------------------
# C2-CLONE: độ trung thực
# ---------------------------------------------------------------------------
class TestCloneFidelity:
    @pytest.mark.parametrize("name", ALL)
    def test_clone_matches_the_original(self, name):
        env = build(name)
        clone = env.clone_env()
        assert clone is not env
        assert isinstance(clone, GameEnv)
        assert clone.config == env.config
        assert clone.state == env.state
        assert clone.legal_actions() == env.legal_actions()
        assert clone.is_terminal() == env.is_terminal()
        assert clone.render() == env.render()
        for player in (Player.X, Player.O):
            assert clone.result(player) == env.result(player)

    @pytest.mark.parametrize("name", ALL)
    def test_clone_carries_the_same_undo_history(self, name):
        env = build(name)
        clone = env.clone_env()
        undone = 0
        exhausted = False
        for _ in range(N * N + 1):  # có giới hạn: engine sai không được làm test treo
            try:
                expected = env.undo()
            except UndoError:
                with pytest.raises(UndoError):
                    clone.undo()
                exhausted = True
                break
            assert clone.undo() == expected
            undone += 1
        assert exhausted, "undo() never raised UndoError on an empty history"
        assert undone == len(SCENARIOS[name])

    def test_clone_of_a_fresh_env_has_nothing_to_undo(self):
        clone = new_env().clone_env()
        with pytest.raises(UndoError):
            clone.undo()

    def test_clone_keeps_terminal_metadata(self):
        for name in FINISHED:
            env = build(name)
            clone = env.clone_env()
            assert clone.state.terminated is True
            assert clone.state.winner == env.state.winner
            assert clone.legal_actions() == []

    @pytest.mark.parametrize("name", ALL)
    def test_cloning_does_not_change_the_original(self, name):
        env = build(name)
        before = snapshot(env)
        env.clone_env()
        env.clone_env()
        assert snapshot(env) == before


# ---------------------------------------------------------------------------
# C2-CLONE: độc lập hai chiều
# ---------------------------------------------------------------------------
class TestCloneIndependence:
    @pytest.mark.parametrize("name", OPEN)
    def test_step_on_clone_does_not_touch_the_original(self, name):
        env = build(name)
        state_before_clone_move = env.state
        before = snapshot(env)
        clone = env.clone_env()
        clone.step(first_legal(clone))
        assert env.state != clone.state          # property của contract mục 10
        assert env.state == state_before_clone_move
        assert snapshot(env) == before
        assert clone.state.move_count == len(SCENARIOS[name]) + 1

    @pytest.mark.parametrize("name", OPEN)
    def test_step_on_original_does_not_touch_the_clone(self, name):
        env = build(name)
        clone = env.clone_env()
        before = snapshot(clone)
        env.step(first_legal(env))
        assert snapshot(clone) == before
        assert clone.state != env.state

    @pytest.mark.parametrize("name", OPEN)
    def test_clone_can_play_to_the_end_without_touching_the_original(self, name):
        env = build(name)
        before = snapshot(env)
        clone = env.clone_env()
        for _ in range(N * N):
            if clone.is_terminal():
                break
            clone.step(first_legal(clone))
        assert clone.is_terminal() is True
        assert env.is_terminal() is False
        assert snapshot(env) == before

    @pytest.mark.parametrize("name", HISTORIC)
    def test_undo_on_clone_does_not_touch_the_original(self, name):
        env = build(name)
        before = snapshot(env)
        clone = env.clone_env()
        clone.undo()
        assert snapshot(env) == before
        assert clone.state.move_count == len(SCENARIOS[name]) - 1

    @pytest.mark.parametrize("name", HISTORIC)
    def test_undo_on_original_does_not_touch_the_clone(self, name):
        env = build(name)
        clone = env.clone_env()
        before = snapshot(clone)
        env.undo()
        assert snapshot(clone) == before
        assert env.state.move_count == len(SCENARIOS[name]) - 1

    @pytest.mark.parametrize("name", ALL)
    def test_reset_on_clone_does_not_touch_the_original(self, name):
        env = build(name)
        before = snapshot(env)
        clone = env.clone_env()
        clone.reset()
        assert snapshot(env) == before
        assert clone.state.move_count == 0

    @pytest.mark.parametrize("name", ALL)
    def test_reset_on_original_does_not_touch_the_clone(self, name):
        env = build(name)
        clone = env.clone_env()
        before = snapshot(clone)
        env.reset()
        assert snapshot(clone) == before
        assert drain(clone) == len(SCENARIOS[name])  # history của clone còn nguyên

    def test_clone_history_grows_independently(self):
        env = build("mid")
        clone = env.clone_env()
        play(clone, [(0, 0), (0, 10), (10, 0)])
        assert drain(env) == len(MID_MOVES)
        assert drain(clone) == len(MID_MOVES) + 3

    def test_original_history_grows_independently(self):
        env = build("mid")
        clone = env.clone_env()
        play(env, [(0, 0), (0, 10)])
        assert drain(clone) == len(MID_MOVES)
        assert drain(env) == len(MID_MOVES) + 2

    def test_clone_can_undo_more_than_it_stepped_without_hurting_the_original(self):
        env = build("mid")
        clone = env.clone_env()
        clone.step((0, 0))
        assert drain(clone) == len(MID_MOVES) + 1
        assert env.state.move_count == len(MID_MOVES)
        assert drain(env) == len(MID_MOVES)

    def test_clone_of_a_clone_is_independent_all_the_way_down(self):
        env = build("mid")
        child = env.clone_env()
        grandchild = child.clone_env()
        before_env, before_child = snapshot(env), snapshot(child)
        grandchild.step(first_legal(grandchild))
        assert snapshot(env) == before_env
        assert snapshot(child) == before_child
        assert grandchild.state.move_count == len(MID_MOVES) + 1

    def test_sibling_clones_do_not_share_state(self):
        env = build("mid")
        a, b = env.clone_env(), env.clone_env()
        a.step((0, 0))
        b.step((10, 10))
        assert a.state.last_action == (0, 0)
        assert b.state.last_action == (10, 10)
        assert a.state != b.state
        assert env.state.move_count == len(MID_MOVES)

    def test_snapshots_of_a_clone_are_independent_of_the_original(self):
        env = build("mid")
        clone = env.clone_env()
        snapshot_of_clone = clone.state
        snapshot_of_clone.board[0][0] = 1  # consumer vi phạm quy ước read-only
        assert clone.state.board[0][0] == 0
        assert env.state.board[0][0] == 0

    def test_failed_step_on_clone_changes_neither_environment(self):
        env = build("mid")
        clone = env.clone_env()
        before_env, before_clone = snapshot(env), snapshot(clone)
        with pytest.raises(InvalidActionError):
            clone.step((5, 5))  # ô đã có quân
        assert snapshot(env) == before_env
        assert snapshot(clone) == before_clone

    def test_one_ply_search_over_clones_leaves_the_real_env_untouched(self):
        env = build("mid")
        before = snapshot(env)
        for action in env.legal_actions()[:30]:
            probe = env.clone_env()
            result = probe.step(action)
            assert result.next_state.last_action == action
        assert snapshot(env) == before

    def test_undoing_the_clones_own_moves_returns_it_to_the_original_state(self):
        env = build("mid")
        clone = env.clone_env()
        play(clone, [(0, 0), (0, 10), (10, 0)])
        for _ in range(3):
            clone.undo()
        assert clone.state == env.state


# ---------------------------------------------------------------------------
# C2-UNDO: round-trip
# ---------------------------------------------------------------------------
class TestUndoRoundTrip:
    @pytest.mark.parametrize("name", OPEN)
    @pytest.mark.parametrize("action", [(0, 0), (0, 10), (10, 0), (10, 10), (3, 7)])
    def test_step_then_undo_is_the_identity(self, name, action):
        env = build(name)
        before = env.state
        snap = snapshot(env)
        result = env.step(action)
        after_undo = env.undo()
        assert after_undo == before                       # property của contract mục 10
        assert result.next_state.move_count == before.move_count + 1
        assert env.state == before
        assert snapshot(env) == snap

    def test_undo_restores_every_field_individually(self):
        env = build("mid")
        before = env.state
        env.step((0, 0))
        restored = env.undo()
        assert restored.board == before.board
        assert restored.current_player == before.current_player == Player.X
        assert restored.last_action == before.last_action == (6, 6)
        assert restored.move_count == before.move_count == 4
        assert restored.terminated is before.terminated is False
        assert restored.winner is before.winner is None
        check_state_invariants(restored)

    def test_undoing_the_first_move_restores_the_empty_board(self):
        env = new_env()
        initial = env.state
        env.step((5, 5))
        restored = env.undo()
        assert restored == initial
        assert restored.last_action is None and restored.move_count == 0
        assert restored.current_player == Player.X
        assert env.legal_actions() == [(r, c) for r in range(N) for c in range(N)]

    def test_n_undos_walk_back_through_every_state(self):
        env = new_env()
        states = [env.state]
        for move in MID_MOVES + [(0, 0), (10, 10), (0, 10)]:
            env.step(move)
            states.append(env.state)
        for index in range(len(states) - 1, 0, -1):
            restored = env.undo()
            assert restored == states[index - 1], f"undo back to ply {index - 1}"
            assert env.state == states[index - 1]
            check_state_invariants(restored)

    def test_undo_reverts_exactly_one_ply(self):
        env = build("mid")
        state = env.undo()
        assert state.move_count == 3
        assert state.last_action == MID_MOVES[2]
        assert state.current_player == Player.O
        assert state.board[6][6] == 0 and state.board[6][5] == Player.X

    def test_undo_makes_the_cell_legal_again_in_row_major_order(self):
        env = build("mid")
        before = env.legal_actions()
        env.step((3, 3))
        assert (3, 3) not in env.legal_actions()
        env.undo()
        assert env.legal_actions() == before

    def test_undo_restores_render_output(self):
        env = build("mid")
        text = env.render()
        env.step((0, 0))
        assert env.render() != text
        env.undo()
        assert env.render() == text

    def test_undo_returns_an_independent_snapshot(self):
        env = build("mid")
        env.step((0, 0))
        returned = env.undo()
        returned.board[0][0] = 1  # consumer vi phạm quy ước read-only
        assert env.state.board[0][0] == 0
        assert env.state.board is not returned.board

    def test_undo_then_a_different_move_leaves_no_stale_history(self):
        env = new_env()
        env.step((0, 0))
        env.undo()
        env.step((0, 1))
        assert env.state.last_action == (0, 1)
        env.undo()
        with pytest.raises(UndoError):
            env.undo()

    def test_step_undo_step_gives_the_same_result_as_stepping_once(self):
        env = build("mid")
        first = env.step((0, 0))
        env.undo()
        second = env.step((0, 0))
        assert first == second

    def test_undo_inside_a_game_does_not_change_later_play(self):
        env = new_env()
        play(env, X_WIN_MOVES[:5])
        env.undo()
        env.undo()
        play(env, X_WIN_MOVES[3:])
        assert env.state.terminated is True
        assert env.state.winner == Player.X
        assert env.state.move_count == len(X_WIN_MOVES)

    def test_depth_first_search_with_step_and_undo_restores_the_root(self):
        env = build("mid")
        root = env.state

        def dfs(e, depth: int) -> int:
            if depth == 0:
                return 0
            visited = 0
            for action in e.legal_actions()[:4]:
                before = e.state
                e.step(action)
                visited += 1 + dfs(e, depth - 1)
                assert e.undo() == before
                assert e.state == before
            return visited

        assert dfs(env, 3) == 4 + 16 + 64
        assert env.state == root
        assert drain(env) == len(MID_MOVES)

    def test_depth_first_search_on_a_clone_leaves_the_real_env_untouched(self):
        env = build("mid")
        before = snapshot(env)
        probe = env.clone_env()
        for action in probe.legal_actions()[:6]:
            probe.step(action)
            probe.step(probe.legal_actions()[0])
            probe.undo()
            probe.undo()
        assert probe.state == env.state
        assert snapshot(env) == before


# ---------------------------------------------------------------------------
# C2-UNDO: sau thắng / hòa
# ---------------------------------------------------------------------------
class TestUndoFromTerminal:
    @pytest.mark.parametrize("name", FINISHED)
    def test_undo_returns_to_a_playing_state(self, name):
        moves = SCENARIOS[name]
        env = build(name)
        state = env.undo()
        assert state == env.state
        assert state.terminated is False
        assert state.winner is None
        assert state.move_count == len(moves) - 1
        assert state.last_action == moves[-2]
        assert state.current_player == mover_of_last_move(moves)
        assert env.is_terminal() is False
        assert state.board[moves[-1][0]][moves[-1][1]] == 0
        assert env.result(Player.X) is None and env.result(Player.O) is None
        check_state_invariants(state)

    @pytest.mark.parametrize("name", FINISHED)
    def test_legal_actions_come_back_after_undo(self, name):
        moves = SCENARIOS[name]
        env = build(name)
        env.undo()
        legal = env.legal_actions()
        assert moves[-1] in legal
        assert legal == sorted(legal)  # row-major
        assert len(legal) == N * N - (len(moves) - 1)

    def test_undo_from_a_draw_leaves_exactly_the_last_cell(self):
        env = build("draw")
        env.undo()
        assert env.legal_actions() == [DRAW_MOVES[-1]]

    @pytest.mark.parametrize("name", FINISHED)
    def test_replaying_the_last_move_reproduces_the_final_state(self, name):
        moves = SCENARIOS[name]
        env = build(name)
        final = env.state
        env.undo()
        result = env.step(moves[-1])
        assert env.state == final
        assert result.next_state == final
        assert result.done is True
        assert result.winner == final.winner

    @pytest.mark.parametrize("name", ["x_win", "o_win"])
    def test_a_different_move_after_undoing_a_win_continues_the_game(self, name):
        moves = SCENARIOS[name]
        env = build(name)
        env.undo()
        result = env.step(HARMLESS_CELL)
        assert result.done is False
        assert result.winner is None
        assert env.is_terminal() is False
        assert env.state.move_count == len(moves)
        assert env.state.last_action == HARMLESS_CELL
        assert env.legal_actions() != []
        check_state_invariants(env.state)

    @pytest.mark.parametrize("name", FINISHED)
    def test_every_move_of_a_finished_game_can_be_undone(self, name):
        env = build(name)
        initial = new_env().state
        assert drain(env) == len(SCENARIOS[name])
        assert env.state == initial
        assert env.legal_actions() == [(r, c) for r in range(N) for c in range(N)]

    @pytest.mark.parametrize("name", FINISHED)
    def test_failed_step_on_a_finished_game_does_not_consume_history(self, name):
        moves = SCENARIOS[name]
        env = build(name)
        with pytest.raises(InvalidActionError) as info:
            env.step((10, 10))
        assert info.value.reason is InvalidActionReason.GAME_OVER
        state = env.undo()
        assert state.move_count == len(moves) - 1  # chỉ lùi một nước, không lùi hai

    @pytest.mark.parametrize("name", FINISHED)
    def test_undo_on_a_clone_of_a_finished_game_leaves_the_original_finished(self, name):
        env = build(name)
        before = snapshot(env)
        clone = env.clone_env()
        clone.undo()
        assert clone.is_terminal() is False
        assert env.is_terminal() is True
        assert env.legal_actions() == []
        assert snapshot(env) == before


# ---------------------------------------------------------------------------
# C2-UNDO: history rỗng
# ---------------------------------------------------------------------------
class TestUndoEmptyHistory:
    def test_fresh_env_raises_undo_error_and_keeps_state(self):
        env = new_env()
        before = snapshot(env)
        with pytest.raises(UndoError):
            env.undo()
        assert snapshot(env) == before

    def test_repeated_undo_errors_change_nothing(self):
        env = new_env()
        before = snapshot(env)
        for _ in range(3):
            with pytest.raises(UndoError):
                env.undo()
        assert snapshot(env) == before

    @pytest.mark.parametrize("name", HISTORIC)
    def test_one_undo_more_than_the_number_of_steps_raises(self, name):
        env = build(name)
        initial = new_env().state
        assert drain(env) == len(SCENARIOS[name])
        before = snapshot(env)
        with pytest.raises(UndoError):
            env.undo()
        assert env.state == initial
        assert snapshot(env) == before

    @pytest.mark.parametrize("name", HISTORIC)
    def test_reset_clears_the_history(self, name):
        env = build(name)
        env.reset()
        with pytest.raises(UndoError):
            env.undo()

    def test_undo_error_is_a_runtime_error_and_not_an_invalid_action(self):
        with pytest.raises(UndoError) as info:
            new_env().undo()
        assert isinstance(info.value, RuntimeError)
        assert not isinstance(info.value, ValueError)
        assert not isinstance(info.value, InvalidActionError)

    def test_a_rejected_step_leaves_nothing_to_undo(self):
        env = new_env()
        for action in (40, (11, 0), None):
            with pytest.raises(InvalidActionError):
                env.step(action)
        with pytest.raises(UndoError):
            env.undo()

    def test_empty_history_on_a_clone_does_not_affect_the_original(self):
        env = new_env()
        clone = env.clone_env()
        with pytest.raises(UndoError):
            clone.undo()
        env.step((5, 5))
        assert env.undo().move_count == 0
        with pytest.raises(UndoError):
            clone.undo()
