"""Smoke and contract tests for Hải's W1-M1-02 mock environment."""

from __future__ import annotations

import numpy as np
import pytest

from core.engine.interfaces import GameConfig, InvalidActionError, Player
from ui.mock_game_env import MockGameEnv


def test_default_mock_is_an_11x11_int8_board() -> None:
    env = MockGameEnv()
    state = env.reset()

    assert env.board_array.shape == (11, 11)
    assert env.board_array.dtype == np.int8
    assert len(state.board) == 11
    assert all(len(row) == 11 for row in state.board)
    assert state.current_player == Player.X
    assert len(env.legal_actions()) == 121


def test_empty_cell_click_updates_board_and_changes_turn() -> None:
    env = MockGameEnv()

    result = env.step((4, 4))

    assert result.next_state.board[4][4] == Player.X
    assert result.next_state.current_player == Player.O
    assert result.reward == 0.0
    assert result.done is False
    assert result.winner is None
    assert env.move_count == 1
    assert env.last_action == (4, 4)
    assert len(env.legal_actions()) == 120


def test_occupied_cell_raises_clear_error_without_mutating_state() -> None:
    env = MockGameEnv()
    env.step((4, 4))
    state_before_error = env.state

    with pytest.raises(InvalidActionError, match="already occupied"):
        env.step((4, 4))

    assert env.state == state_before_error
    assert env.move_count == 1
    assert env.state.current_player == Player.O


@pytest.mark.parametrize("action", [(-1, 0), (0, -1), (11, 0), (0, 11)])
def test_out_of_bounds_action_does_not_mutate_state(action: tuple[int, int]) -> None:
    env = MockGameEnv()
    state_before_error = env.state

    with pytest.raises(InvalidActionError, match="out of bounds"):
        env.step(action)

    assert env.state == state_before_error
    assert env.move_count == 0


@pytest.mark.parametrize("action", [40, [4, 4], (4,), (4, "4")])
def test_action_must_follow_tuple_contract(action: object) -> None:
    env = MockGameEnv()

    with pytest.raises(InvalidActionError):
        env.step(action)  # type: ignore[arg-type]


def test_reset_restores_the_initial_state() -> None:
    env = MockGameEnv()
    env.step((0, 0))
    env.step((0, 1))

    state = env.reset()

    assert env.move_count == 0
    assert env.last_action is None
    assert state.current_player == Player.X
    assert np.count_nonzero(env.board_array) == 0
    assert len(env.legal_actions()) == 121


def test_default_11x11_mode_and_clone_are_independent() -> None:
    env = MockGameEnv()
    clone = env.clone_env()

    clone.step((5, 5))

    assert env.board_array.shape == (11, 11)
    assert len(env.legal_actions()) == 121
    assert env.state.board[5][5] == Player.EMPTY
    assert clone.state.board[5][5] == Player.X


def test_step_result_state_is_a_defensive_copy() -> None:
    env = MockGameEnv()
    result = env.step((2, 3))

    result.next_state.board[2][3] = Player.O

    assert env.state.board[2][3] == Player.X


def test_full_board_is_reported_as_draw_without_win_logic() -> None:
    env = MockGameEnv()
    final_action = (10, 10)

    for row in range(11):
        for col in range(11):
            if (row, col) != final_action:
                env.step((row, col))

    result = env.step(final_action)

    assert result.done is True
    assert result.winner is None
    assert result.reward == 0.0
    assert env.is_terminal() is True
    assert env.legal_actions() == []
    assert env.result() == result

    with pytest.raises(InvalidActionError, match="already finished"):
        env.step((0, 0))

