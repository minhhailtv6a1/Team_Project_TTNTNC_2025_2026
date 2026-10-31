"""Thin controller for human moves at the UI boundary.

The controller only forwards a public ``Action`` to ``GameEnv.step`` and
returns the player who submitted it.  Game rules and terminal detection stay
inside the engine, as required by the ``caro-v2`` contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.engine.interfaces import Action, GameEnv, Player, StepResult


@dataclass(frozen=True, slots=True)
class HumanMove:
    """A successful human action together with its engine result."""

    action: Action
    player: Player
    result: StepResult


def submit_human_action(env: GameEnv, action: Action) -> HumanMove:
    """Submit one click to the engine without reimplementing game rules."""

    player = env.state.current_player
    result = env.step(action)
    return HumanMove(action=action, player=player, result=result)


__all__ = ["HumanMove", "submit_human_action"]
