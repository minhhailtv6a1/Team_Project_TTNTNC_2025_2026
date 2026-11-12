from __future__ import annotations

from numbers import Integral
from time import perf_counter

import numpy as np

try:
    import connect4_core as _core
except ModuleNotFoundError as exc:
    if exc.name != "connect4_core":
        raise
    from connect4_search import _actions as actions, _result as result, _utility as utility
    RULES_BACKEND = "connect4_search fallback (core integration pending)"
else:
    actions, result, utility = _core.actions, _core.result, _core.utility
    RULES_BACKEND = "connect4_core"


def _validate(board, player):
    board = np.asarray(board)
    if board.ndim != 2 or min(board.shape) < 1 or not np.isin(board, (0, 1, -1)).all():
        raise ValueError("board must be a nonempty 2D array containing 0, 1, -1")
    if isinstance(player, (bool, np.bool_)) or player not in (1, -1):
        raise ValueError("player must be 1 or -1")
    # In each column, occupied cells must form a stack at the bottom.
    if np.any((board[:-1] != 0) & (board[1:] == 0)):
        raise ValueError("board contains unsupported pieces")
    return board


def _budget(n_playouts):
    if isinstance(n_playouts, (bool, np.bool_)) or not isinstance(n_playouts, Integral) or n_playouts < 1:
        raise ValueError("n_playouts must be a positive integer")
    return int(n_playouts)


def _rollout(board, action, player, rng):
    state = result(board, player, action)
    current = -player
    while True:
        value = utility(state, player)
        if value is not None:
            return int(value)
        move = int(rng.choice(actions(state)))
        state = result(state, current, move)
        current = -current


def playout(board, action, player=1, rng=None):
    """Play action then random legal moves; return utility for the root player."""
    board = _validate(board, player)
    if utility(board, player) is not None:
        raise ValueError("cannot start a playout from a terminal board")
    if isinstance(action, (bool, np.bool_)) or not isinstance(action, Integral) or action not in actions(board):
        raise ValueError("action must be a legal column index")
    rng = np.random.default_rng() if rng is None else rng
    return _rollout(board, int(action), player, rng)


def pmcs(board, player=1, n_playouts=100, seed=42):
    """Distribute exactly N rollouts over legal moves, counts differ by at most 1.

    Remainder allocation and tied estimates use a seeded random ordering. When
    N is smaller than the action count, unvisited moves have value None and are
    excluded from the empirical comparison. An immediate proven win takes
    precedence over noisy estimates; it does not consume rollout budget.
    A terminal root returns move=None and performs zero rollouts.
    """
    started = perf_counter()
    board = _validate(board, player)
    n_playouts = _budget(n_playouts)
    terminal_value = utility(board, player)
    if terminal_value is not None:
        return dict(move=None, value=int(terminal_value), playouts=0,
                    elapsed_s=perf_counter() - started, visits={}, action_values={})
    rng = np.random.default_rng(seed)
    legal = [int(a) for a in actions(board)]
    order = [int(a) for a in rng.permutation(legal)]
    quotient, remainder = divmod(n_playouts, len(legal))
    visits = {a: quotient + int(i < remainder) for i, a in enumerate(order)}
    values = {}
    for action, count in visits.items():
        values[action] = (sum(_rollout(board, action, player, rng) for _ in range(count)) / count
                          if count else None)
    wins = [a for a in order if utility(result(board, player, a), player) == 1]
    move = wins[0] if wins else max((a for a in order if visits[a]), key=values.get)
    return dict(move=move, value=1.0 if wins else float(values[move]),
                playouts=sum(visits.values()), elapsed_s=perf_counter() - started,
                visits=visits, action_values=values)


class PureMonteCarloAgent:
    """A persistent local RNG supplies fresh reproducible seeds across moves."""

    def __init__(self, n_playouts=100, seed=42):
        self.n_playouts = _budget(n_playouts)
        self.rng = np.random.default_rng(seed)

    def __call__(self, board, player=1):
        found = pmcs(board, player, self.n_playouts, int(self.rng.integers(2**63)))
        if found["move"] is None:
            raise ValueError("agent cannot move on a terminal board")
        return found["move"]
