"""Alpha--beta players for Connect 4.

The public API deliberately mirrors the contract in ``PHAN_CONG_LAB05.md``.
Boards contain ``0`` (empty), ``1`` and ``-1``; row zero is the top row.
When available, game-rule operations are delegated to ``connect4_core``.
"""

from __future__ import annotations

import math
import time
from typing import Callable, Iterable

import numpy as np

try:  # The search module can still be unit-tested before the core is merged.
    import connect4_core as _core
except ImportError:  # pragma: no cover - exercised only during isolated development
    _core = None


def _other(player: int) -> int:
    return _core.other(player) if _core is not None else -player


def _actions(board: np.ndarray) -> list[int]:
    if _core is not None:
        return list(_core.actions(board))
    return [col for col in range(board.shape[1]) if board[0, col] == 0]


def _result(board: np.ndarray, player: int, action: int) -> np.ndarray:
    if _core is not None:
        return _core.result(board, player, action)
    if action not in _actions(board):
        raise ValueError(f"Illegal Connect 4 column: {action}")
    child = np.array(board, copy=True)
    row = np.where(child[:, action] == 0)[0][-1]
    child[row, action] = player
    return child


def _has_four(board: np.ndarray, player: int) -> bool:
    rows, cols = board.shape
    for row in range(rows):
        for col in range(cols):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                end_row, end_col = row + 3 * dr, col + 3 * dc
                if 0 <= end_row < rows and 0 <= end_col < cols:
                    if all(board[row + k * dr, col + k * dc] == player for k in range(4)):
                        return True
    return False


def _utility(board: np.ndarray, player: int) -> int | None:
    if _core is not None:
        value = _core.utility(board, player)
        return None if value is None else int(value)
    if _has_four(board, player):
        return 1
    if _has_four(board, _other(player)):
        return -1
    return 0 if not _actions(board) else None


def _windows(board: np.ndarray) -> Iterable[np.ndarray]:
    """Yield every length-four horizontal, vertical and diagonal window."""
    rows, cols = board.shape
    for row in range(rows):
        for col in range(cols - 3):
            yield board[row, col : col + 4]
    for row in range(rows - 3):
        for col in range(cols):
            yield board[row : row + 4, col]
    for row in range(rows - 3):
        for col in range(cols - 3):
            yield np.array([board[row + k, col + k] for k in range(4)])
            yield np.array([board[row + 3 - k, col + k] for k in range(4)])


def evaluate(board: np.ndarray, player: int = 1) -> float:
    """Return a bounded positional estimate from ``player``'s perspective.

    Every four-cell window rewards an uncontested own chain and penalizes an
    uncontested opponent chain.  Central columns receive a small bonus because
    they participate in more potential four-in-a-row windows.  A ``tanh``
    normalization ensures non-terminal estimates stay strictly inside [-1, 1].
    """
    board = np.asarray(board)
    if player not in (1, -1):
        raise ValueError("player must be 1 or -1")

    terminal_value = _utility(board, player)
    if terminal_value is not None:
        return float(terminal_value)

    weights = (0.0, 0.015, 0.09, 0.42, 0.0)
    score = 0.0
    opponent = _other(player)
    for window in _windows(board):
        own = int(np.count_nonzero(window == player))
        opp = int(np.count_nonzero(window == opponent))
        if own == 0:
            score -= weights[opp]
        elif opp == 0:
            score += weights[own]

    # This also works for even-width boards: the two central columns tie.
    centre = (board.shape[1] - 1) / 2.0
    for col in range(board.shape[1]):
        centrality = 1.0 - abs(col - centre) / max(centre, 1.0)
        score += 0.035 * centrality * (
            int(np.count_nonzero(board[:, col] == player))
            - int(np.count_nonzero(board[:, col] == opponent))
        )
    return float(np.clip(math.tanh(score), -0.99, 0.99))


def _ordered_actions(board: np.ndarray, move_ordering: bool) -> list[int]:
    legal = _actions(board)
    if not move_ordering:
        return legal
    centre = (board.shape[1] - 1) / 2.0
    return sorted(legal, key=lambda col: (abs(col - centre), col))


def _search(
    board: np.ndarray,
    root_player: int,
    to_move: int,
    alpha: float,
    beta: float,
    depth: int,
    cutoff: int | None,
    move_ordering: bool,
    counter: list[int],
) -> tuple[float, int | None]:
    counter[0] += 1
    terminal_value = _utility(board, root_player)
    if terminal_value is not None:
        return float(terminal_value), None
    if cutoff is not None and depth >= cutoff:
        return evaluate(board, root_player), None

    maximizing = to_move == root_player
    best_value = -math.inf if maximizing else math.inf
    best_move: int | None = None
    for move in _ordered_actions(board, move_ordering):
        value, _ = _search(
            _result(board, to_move, move),
            root_player,
            _other(to_move),
            alpha,
            beta,
            depth + 1,
            cutoff,
            move_ordering,
            counter,
        )
        if maximizing:
            if value > best_value:
                best_value, best_move = value, move
            alpha = max(alpha, best_value)
        else:
            if value < best_value:
                best_value, best_move = value, move
            beta = min(beta, best_value)
        if alpha >= beta:
            break
    return best_value, best_move


def _run_search(
    board: np.ndarray,
    player: int,
    cutoff: int | None,
    move_ordering: bool,
) -> dict:
    if player not in (1, -1):
        raise ValueError("player must be 1 or -1")
    if cutoff is not None and (not isinstance(cutoff, int) or cutoff < 1):
        raise ValueError("cutoff must be a positive integer or None")
    started = time.perf_counter()
    counter = [0]
    value, move = _search(
        np.asarray(board), player, player, -math.inf, math.inf, 0, cutoff,
        move_ordering, counter,
    )
    return {
        "move": move,
        "value": float(value),
        "nodes": counter[0],
        "elapsed_s": time.perf_counter() - started,
    }


def alpha_beta_search(
    board: np.ndarray, player: int = 1, move_ordering: bool = True
) -> dict:
    """Solve a small Connect 4 position exactly with alpha--beta pruning.

    Full-width search is intentionally for small boards only (for example 4x4).
    Use :func:`heuristic_alpha_beta_search` for standard 6x7 positions.
    """
    return _run_search(board, player, cutoff=None, move_ordering=move_ordering)


def heuristic_alpha_beta_search(
    board: np.ndarray,
    player: int = 1,
    cutoff: int = 4,
    move_ordering: bool = True,
) -> dict:
    """Run depth-limited alpha--beta search using :func:`evaluate` at leaves."""
    return _run_search(board, player, cutoff=cutoff, move_ordering=move_ordering)


class AlphaBetaAgent:
    """Callable exact-search agent compatible with ``core.play``."""

    def __init__(self, move_ordering: bool = True) -> None:
        self.move_ordering = move_ordering

    def __call__(self, board: np.ndarray, player: int = 1) -> int | None:
        return alpha_beta_search(board, player, self.move_ordering)["move"]


class HeuristicAlphaBetaAgent:
    """Callable depth-limited alpha--beta agent compatible with ``core.play``."""

    def __init__(self, cutoff: int = 4, move_ordering: bool = True) -> None:
        self.cutoff = cutoff
        self.move_ordering = move_ordering

    def __call__(self, board: np.ndarray, player: int = 1) -> int | None:
        return heuristic_alpha_beta_search(
            board, player, self.cutoff, self.move_ordering
        )["move"]
