import numpy as np
import pytest

from core.engine.board import Board


def test_board_initialization():
    board = Board().get_board_state()
    assert board.shape == (11, 11)
    assert board.dtype == np.int8
    assert np.all(board == 0)


@pytest.mark.parametrize(("action", "expected"), [
    (0, (0, 0)),
    (10, (0, 10)),
    (11, (1, 0)),
    (50, (4, 6)),
    (120, (10, 10)),
])
def test_action_to_coord(action, expected):
    assert Board.action_to_coord(action) == expected


@pytest.mark.parametrize("action", range(121))
def test_action_coord_round_trip(action):
    row, col = Board.action_to_coord(action)
    assert Board.coord_to_action(row, col) == action


@pytest.mark.parametrize(("row", "col", "expected"), [
    (0, 0, 0),
    (0, 10, 10),
    (1, 0, 11),
    (4, 6, 50),
    (10, 10, 120),
])
def test_coord_to_action(row, col, expected):
    assert Board.coord_to_action(row, col) == expected


@pytest.mark.parametrize("action", [-1, 121, 150])
def test_action_to_coord_rejects_invalid(action):
    with pytest.raises(ValueError):
        Board.action_to_coord(action)


@pytest.mark.parametrize("row,col", [
    (-1, 0), (11, 0), (0, -1), (0, 11),
])
def test_coord_to_action_rejects_invalid(row, col):
    with pytest.raises(ValueError):
        Board.coord_to_action(row, col)


def test_valid_action_on_empty_cell():
    assert Board().is_valid_action(50) is True


@pytest.mark.parametrize("action", [-1, 121])
def test_is_valid_action_false_for_invalid(action):
    assert Board().is_valid_action(action) is False


def test_place_stone_x_and_o():
    board = Board()
    assert board.place_stone(50, Board.PLAYER_X) is True
    assert board.place_stone(51, Board.PLAYER_O) is True
    assert board.get_board_state()[4, 6] == 1
    assert board.get_board_state()[4, 7] == -1


def test_occupied_cell_rejected_without_mutation():
    board = Board()
    board.place_stone(50, Board.PLAYER_X)
    before = board.get_board_state()
    success = board.place_stone(50, Board.PLAYER_O)
    assert success is False
    np.testing.assert_array_equal(board.get_board_state(), before)


@pytest.mark.parametrize("action", [-1, 121])
def test_invalid_action_rejected_without_mutation(action):
    board = Board()
    before = board.get_board_state()
    success = board.place_stone(action, Board.PLAYER_X)
    assert success is False
    np.testing.assert_array_equal(board.get_board_state(), before)


def test_get_board_returns_independent_copy():
    board = Board()
    external = board.get_board_state()
    external[0, 0] = Board.PLAYER_X
    assert board.get_board_state()[0, 0] == Board.EMPTY_VALUE


def test_reset_clears_board():
    board = Board()
    board.place_stone(0, Board.PLAYER_X)
    board.place_stone(120, Board.PLAYER_O)
    board.reset()
    assert np.all(board.get_board_state() == 0)


def test_get_legal_actions():
    board = Board()
    assert len(board.get_legal_actions()) == 121
    board.place_stone(0, Board.PLAYER_X)
    assert len(board.get_legal_actions()) == 120
    assert 0 not in board.get_legal_actions()