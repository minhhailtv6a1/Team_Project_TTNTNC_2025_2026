"""Unit tests for ``connect4_core.py`` covering board representation, gravity,
terminal/utility detection, non-mutation guarantees, and match loop reproducibility.
"""

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import connect4_core as core


def test_empty_board_and_variable_shapes():
    b_default = core.empty_board()
    assert b_default.shape == (6, 7)
    assert b_default.dtype == int
    assert np.all(b_default == 0)

    b_small = core.empty_board((4, 4))
    assert b_small.shape == (4, 4)
    assert core.actions(b_small) == [0, 1, 2, 3]

    with pytest.raises(ValueError):
        core.empty_board((0, 7))


def test_other_player_validation():
    assert core.other(1) == -1
    assert core.other(-1) == 1
    for invalid in (0, 2, True, "x", None):
        with pytest.raises(ValueError):
            core.other(invalid)


def test_gravity_falls_to_lowest_row_and_does_not_mutate_input():
    board = core.empty_board((6, 7))
    original = board.copy()

    b1 = core.result(board, 1, 3)
    np.testing.assert_array_equal(board, original)
    assert b1[5, 3] == 1
    assert np.count_nonzero(b1) == 1

    b2 = core.result(b1, -1, 3)
    assert b1[4, 3] == 0  # b1 not mutated
    assert b2[5, 3] == 1
    assert b2[4, 3] == -1


def test_legal_actions_and_full_column_handling():
    board = core.empty_board((4, 4))
    for p in (1, -1, 1, -1):
        board = core.result(board, p, 2)

    assert core.actions(board) == [0, 1, 3]
    with pytest.raises(ValueError):
        core.result(board, 1, 2)
    with pytest.raises(ValueError):
        core.result(board, 1, -1)
    with pytest.raises(ValueError):
        core.result(board, 1, 4)


def test_horizontal_win_utility_and_terminal():
    board = core.empty_board((6, 7))
    for col in (1, 2, 3, 4):
        board = core.result(board, 1, col)
    assert core.terminal(board) is True
    assert core.utility(board, 1) == 1
    assert core.utility(board, -1) == -1


def test_vertical_win_utility_and_terminal():
    board = core.empty_board((6, 7))
    for _ in range(4):
        board = core.result(board, -1, 5)
    assert core.terminal(board) is True
    assert core.utility(board, -1) == 1
    assert core.utility(board, 1) == -1


def test_both_diagonal_wins():
    # Main diagonal (\): rows (2,1), (3,2), (4,3), (5,4)
    b_main = core.empty_board((6, 7))
    b_main[2, 1] = b_main[3, 2] = b_main[4, 3] = b_main[5, 4] = 1
    assert core.terminal(b_main) is True
    assert core.utility(b_main, 1) == 1
    assert core.utility(b_main, -1) == -1

    # Anti-diagonal (/): rows (5,1), (4,2), (3,3), (2,4)
    b_anti = core.empty_board((6, 7))
    b_anti[5, 1] = b_anti[4, 2] = b_anti[3, 3] = b_anti[2, 4] = -1
    assert core.terminal(b_anti) is True
    assert core.utility(b_anti, -1) == 1
    assert core.utility(b_anti, 1) == -1


def test_draw_and_non_terminal_states():
    board = core.empty_board((4, 4))
    assert core.terminal(board) is False
    assert core.utility(board, 1) is None
    assert core.utility(board, -1) is None

    # Construct a full 4x4 board with no 4-in-a-row for either player
    draw_board = np.array(
        [
            [1, 1, -1, -1],
            [-1, -1, 1, 1],
            [1, 1, -1, -1],
            [-1, -1, 1, 1],
        ],
        dtype=int,
    )
    assert core.actions(draw_board) == []
    assert core.terminal(draw_board) is True
    assert core.utility(draw_board, 1) == 0
    assert core.utility(draw_board, -1) == 0


def test_random_player_and_play_reproducibility():
    board = core.empty_board((6, 7))
    before = board.copy()
    move = core.random_player(board, 1, rng=np.random.default_rng(42))
    assert move in range(7)
    np.testing.assert_array_equal(board, before)

    res1 = core.play(core.random_player, core.random_player, n_games=50, shape=(6, 7), seed=42)
    res2 = core.play(core.random_player, core.random_player, n_games=50, shape=(6, 7), seed=42)
    assert res1["p1_wins"] == res2["p1_wins"] == res1[1]
    assert res1["p2_wins"] == res2["p2_wins"] == res1[-1]
    assert res1["draws"] == res2["draws"] == res1[0]
    assert res1["p1_wins"] + res1["p2_wins"] + res1["draws"] == 50
    assert res1["p1_moves"] >= res1["p2_moves"] > 0
