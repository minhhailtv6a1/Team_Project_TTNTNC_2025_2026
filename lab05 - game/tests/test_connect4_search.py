"""Hand-crafted regression tests for the Connect 4 search module."""

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from connect4_search import (
    AlphaBetaAgent,
    HeuristicAlphaBetaAgent,
    alpha_beta_search,
    evaluate,
    heuristic_alpha_beta_search,
)


def board_with_bottom_row(values, shape=(6, 7)):
    board = np.zeros(shape, dtype=int)
    board[-1, : len(values)] = values
    return board


def test_search_takes_an_immediate_horizontal_win():
    board = board_with_bottom_row([1, 1, 1, 0])
    found = heuristic_alpha_beta_search(board, player=1, cutoff=2)
    assert found["move"] == 3
    assert found["value"] == pytest.approx(1.0)


def test_search_blocks_an_immediate_loss():
    board = board_with_bottom_row([-1, -1, -1, 0])
    assert heuristic_alpha_beta_search(board, player=1, cutoff=2)["move"] == 3


def test_horizontal_and_vertical_wins_are_found():
    horizontal = board_with_bottom_row([1, 1, 1, 0], shape=(4, 4))
    vertical = np.zeros((4, 4), dtype=int)
    vertical[1:, 2] = 1
    # Exact minimax may return another eventual winning move because it does
    # not encode a preference for the shortest win.  The shallow heuristic
    # search must nevertheless spot each immediate winning column.
    assert alpha_beta_search(horizontal, player=1)["value"] == pytest.approx(1.0)
    assert alpha_beta_search(vertical, player=1)["value"] == pytest.approx(1.0)
    assert heuristic_alpha_beta_search(horizontal, player=1, cutoff=1)["move"] == 3
    assert heuristic_alpha_beta_search(vertical, player=1, cutoff=1)["move"] == 2


def test_search_finds_a_supported_diagonal_win():
    board = np.zeros((6, 7), dtype=int)
    board[5, 0] = 1
    board[5, 1], board[4, 1] = -1, 1
    board[5, 2], board[4, 2], board[3, 2] = -1, -1, 1
    board[5, 3], board[4, 3], board[3, 3] = -1, -1, -1
    assert heuristic_alpha_beta_search(board, player=1, cutoff=2)["move"] == 3


def test_heuristic_is_bounded_and_prefers_central_control():
    empty = np.zeros((6, 7), dtype=int)
    assert -1.0 <= evaluate(empty) <= 1.0
    assert heuristic_alpha_beta_search(empty, cutoff=1)["move"] == 3
    assert evaluate(board_with_bottom_row([1]), 1) > evaluate(board_with_bottom_row([1]), -1)


def test_search_reports_metrics_and_does_not_mutate_input():
    board = np.zeros((4, 4), dtype=int)
    original = board.copy()
    found = heuristic_alpha_beta_search(board, cutoff=4, move_ordering=True)
    assert np.array_equal(board, original)
    assert found["move"] in range(4)
    assert found["nodes"] > 0 and found["elapsed_s"] >= 0
    assert set(found) >= {"move", "value", "nodes", "elapsed_s"}


def test_agents_follow_the_shared_callable_contract():
    # Keep the exact-search agent on the documented small-board use case.
    board = board_with_bottom_row([1, 1, 1, 0], shape=(4, 4))
    assert AlphaBetaAgent()(board, 1) in range(4)
    assert HeuristicAlphaBetaAgent(cutoff=2)(board, 1) == 3
