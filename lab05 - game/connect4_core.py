"""Core environment, rules, and baseline agent for Connect 4.

Implements the frozen contract defined in ``PHAN_CONG_LAB05.md``:
- Board cells use ``0`` (empty), ``1`` (first player) and ``-1`` (second player).
- Row ``0`` is the top row; pieces fall to the lowest empty row (largest row index).
- ``result`` returns a new board without mutating the input board.
- ``utility`` returns ``+1`` (win), ``0`` (draw), ``-1`` (loss), or ``None`` (non-terminal)
  from the perspective of ``player``.
"""

from __future__ import annotations

from numbers import Integral
import time
from typing import Callable

import numpy as np


def _validate_player(player: int) -> int:
    if isinstance(player, (bool, np.bool_)) or not isinstance(player, Integral) or int(player) not in (1, -1):
        raise ValueError("player must be 1 or -1")
    return int(player)


def _validate_board(board: np.ndarray) -> np.ndarray:
    arr = np.asarray(board)
    if arr.ndim != 2 or arr.shape[0] < 1 or arr.shape[1] < 1:
        raise ValueError("board must be a non-empty 2D array")
    if arr.dtype == bool or not np.isin(arr, (0, 1, -1)).all():
        raise ValueError("board values must be in {0, 1, -1}")
    return arr


def empty_board(shape: tuple[int, int] = (6, 7)) -> np.ndarray:
    """Create a new empty Connect 4 board with the given ``(rows, cols)`` shape."""
    if (
        not isinstance(shape, (tuple, list))
        or len(shape) != 2
        or any(isinstance(dim, (bool, np.bool_)) or not isinstance(dim, Integral) or dim < 1 for dim in shape)
    ):
        raise ValueError("shape must be a pair of positive integers (rows, cols)")
    return np.zeros((int(shape[0]), int(shape[1])), dtype=int)


def other(player: int) -> int:
    """Return the opposing player (``-1`` for ``1``, ``1`` for ``-1``)."""
    return -_validate_player(player)


def actions(board: np.ndarray) -> list[int]:
    """Return all non-full column indices (0-based) for ``board``."""
    arr = _validate_board(board)
    return [int(col) for col in range(arr.shape[1]) if arr[0, col] == 0]


def result(board: np.ndarray, player: int, action: int) -> np.ndarray:
    """Drop ``player``'s piece into column ``action`` and return a new board."""
    arr = _validate_board(board)
    p = _validate_player(player)
    if isinstance(action, (bool, np.bool_)) or not isinstance(action, Integral):
        raise ValueError(f"Illegal Connect 4 column: {action}")
    col = int(action)
    if col < 0 or col >= arr.shape[1]:
        raise ValueError(f"Column index out of range: {col}")
    if arr[0, col] != 0:
        raise ValueError(f"Column {col} is already full")

    empty_rows = np.where(arr[:, col] == 0)[0]
    if len(empty_rows) == 0:
        raise ValueError(f"Column {col} is already full")

    next_board = np.array(arr, dtype=int, copy=True)
    lowest_row = int(empty_rows[-1])
    next_board[lowest_row, col] = p
    return next_board


def _has_four(board: np.ndarray, player: int) -> bool:
    """Check whether ``player`` has four connected pieces horizontally, vertically, or diagonally."""
    rows, cols = board.shape
    # Horizontal (0, 1)
    if cols >= 4:
        for r in range(rows):
            for c in range(cols - 3):
                if (
                    board[r, c] == player
                    and board[r, c + 1] == player
                    and board[r, c + 2] == player
                    and board[r, c + 3] == player
                ):
                    return True
    # Vertical (1, 0)
    if rows >= 4:
        for r in range(rows - 3):
            for c in range(cols):
                if (
                    board[r, c] == player
                    and board[r + 1, c] == player
                    and board[r + 2, c] == player
                    and board[r + 3, c] == player
                ):
                    return True
    # Diagonals (1, 1) and (1, -1)
    if rows >= 4 and cols >= 4:
        for r in range(rows - 3):
            for c in range(cols - 3):
                if (
                    board[r, c] == player
                    and board[r + 1, c + 1] == player
                    and board[r + 2, c + 2] == player
                    and board[r + 3, c + 3] == player
                ):
                    return True
                if (
                    board[r + 3, c] == player
                    and board[r + 2, c + 1] == player
                    and board[r + 1, c + 2] == player
                    and board[r, c + 3] == player
                ):
                    return True
    return False


def utility(board: np.ndarray, player: int = 1) -> int | None:
    """Return ``+1`` if ``player`` won, ``-1`` if opponent won, ``0`` on draw, or ``None`` if ongoing."""
    arr = _validate_board(board)
    p = _validate_player(player)
    opp = -p
    if _has_four(arr, p):
        return 1
    if _has_four(arr, opp):
        return -1
    if not np.any(arr[0, :] == 0):
        return 0
    return None


def terminal(board: np.ndarray) -> bool:
    """Return ``True`` if ``board`` is a terminal state (win, loss, or draw)."""
    return utility(board, 1) is not None


def random_player(board: np.ndarray, player: int = 1, rng: np.random.Generator | None = None) -> int:
    """Choose a legal column uniformly at random."""
    _validate_player(player)
    legal = actions(board)
    if not legal:
        raise ValueError("No legal actions available on a terminal/full board")
    if rng is not None:
        return int(rng.choice(legal))
    return int(np.random.choice(legal))


def play(
    player1: Callable[[np.ndarray, int], int],
    player2: Callable[[np.ndarray, int], int],
    n_games: int = 100,
    shape: tuple[int, int] = (6, 7),
    seed: int | None = 42,
) -> dict:
    """Play ``n_games`` of Connect 4 between ``player1`` (+1, moves first) and ``player2`` (-1).

    Returns a dictionary containing outcome counts (both by player key ``1``, ``-1``, ``0``
    and descriptive keys ``p1_wins``, ``p2_wins``, ``draws``) and per-player timing/move stats.
    """
    if isinstance(n_games, (bool, np.bool_)) or not isinstance(n_games, Integral) or n_games < 1:
        raise ValueError("n_games must be a positive integer")

    rng = np.random.default_rng(seed) if seed is not None else np.random.default_rng()
    if seed is not None:
        np.random.seed(seed)

    counts = {1: 0, -1: 0, 0: 0}
    moves = {1: 0, -1: 0}
    elapsed = {1: 0.0, -1: 0.0}

    for _ in range(int(n_games)):
        board = empty_board(shape)
        current = 1
        while True:
            u = utility(board, 1)
            if u is not None:
                counts[u] += 1
                break

            agent = player1 if current == 1 else player2
            snapshot = np.array(board, copy=True)
            t0 = time.perf_counter()
            if agent is random_player:
                action = random_player(board, current, rng=rng)
            else:
                action = agent(board, current)
            elapsed[current] += time.perf_counter() - t0
            moves[current] += 1

            if not np.array_equal(board, snapshot):
                raise ValueError("Agent mutated input board")
            board = result(board, current, action)
            current = -current

    return {
        1: counts[1],
        -1: counts[-1],
        0: counts[0],
        "p1_wins": counts[1],
        "p2_wins": counts[-1],
        "draws": counts[0],
        "n_games": int(n_games),
        "p1_moves": moves[1],
        "p2_moves": moves[-1],
        "p1_total_s": elapsed[1],
        "p2_total_s": elapsed[-1],
        "p1_mean_ms": 1000.0 * elapsed[1] / moves[1] if moves[1] else 0.0,
        "p2_mean_ms": 1000.0 * elapsed[-1] / moves[-1] if moves[-1] else 0.0,
    }
