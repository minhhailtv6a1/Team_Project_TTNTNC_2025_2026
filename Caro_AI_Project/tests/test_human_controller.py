"""Tests for the thin caro-v2 human input controller."""

import pytest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import InvalidActionError, Player
from ui.human_controller import submit_human_action


def test_controller_forwards_tuple_action_and_returns_engine_result() -> None:
    env = CaroEnv()

    move = submit_human_action(env, (5, 5))

    assert move.action == (5, 5)
    assert move.player == Player.X
    assert move.result.next_state == env.state
    assert move.result.next_state.board[5][5] == Player.X
    assert move.result.next_state.move_count == 1
    assert move.result.done is False


def test_controller_does_not_hide_engine_validation_errors() -> None:
    env = CaroEnv()
    submit_human_action(env, (5, 5))
    state_before_error = env.state

    with pytest.raises(InvalidActionError):
        submit_human_action(env, (5, 5))

    assert env.state == state_before_error
