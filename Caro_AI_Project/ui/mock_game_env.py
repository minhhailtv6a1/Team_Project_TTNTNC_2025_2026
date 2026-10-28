"""Isolated test double that follows the public ``caro-v2`` protocol.

The mock deliberately implements only the interaction needed by the UI:
resetting a game, listing legal cells, placing stones, changing turns, cloning,
and reporting a draw when the board is full.  Win detection belongs to the
engine and must not be duplicated here.

``GameState.board`` remains a defensive ``list[list[int]]`` snapshot.  The
``board_array`` property exposes an independent ``numpy.int8`` view for UI or
test code that needs shape and dtype checks; production UI does not use it.
"""

from __future__ import annotations

import copy
from numbers import Integral

import numpy as np

from core.engine.interfaces import (
    Action,
    GameConfig,
    GameState,
    InvalidActionError,
    InvalidActionReason,
    Player,
    StepResult,
    UndoError,
)


class MockGameEnv:
    """Small isolated-test stand-in for :class:`core.engine.game_env.CaroEnv`.

    It follows ``GameConfig`` so the UI, mock, and real engine share the same
    11x11 default while retaining a configurable boundary for future sizes.
    """

    def __init__(self, config: GameConfig | None = None) -> None:
        self._config = copy.deepcopy(config or GameConfig())
        self._validate_config()
        self._board = np.empty((0, 0), dtype=np.int8)
        self._current_player = Player.X
        self._done = False
        self._winner: Player | None = None
        self._last_action: Action | None = None
        self._move_count = 0
        self._history: list[tuple[int, int, Action | None]] = []
        self.reset()

    @property
    def config(self) -> GameConfig:
        return self._config

    @property
    def state(self) -> GameState:
        """Return a defensive state snapshot that follows the merged contract."""

        return self.clone_state()

    @property
    def board_array(self) -> np.ndarray:
        """Return an independent int8 board for rendering and shape checks."""

        return self._board.copy()

    @property
    def move_count(self) -> int:
        return self._move_count

    @property
    def last_action(self) -> Action | None:
        return self._last_action

    @property
    def winner(self) -> Player | None:
        return self._winner

    def reset(self, seed: int | None = None) -> GameState:
        """Start a fresh game and return an independent state snapshot."""

        size = self.config.board_size
        self._board = np.zeros((size, size), dtype=np.int8)
        self._current_player = Player.X
        self._done = False
        self._winner = None
        self._last_action = None
        self._move_count = 0
        self._history = []
        return self.clone_state()

    def legal_actions(self) -> list[Action]:
        """Return empty-cell coordinates in deterministic row-major order."""

        if self._done:
            return []

        rows, cols = np.where(self._board == int(Player.EMPTY))
        return [(int(row), int(col)) for row, col in zip(rows, cols)]

    def step(self, action: Action) -> StepResult:
        """Place one stone, change turns, and return a contract ``StepResult``.

        Invalid actions are validated before mutation, so both the board and
        current player remain unchanged when ``InvalidActionError`` is raised.
        """

        row, col = self._validate_action(action)
        player_who_moved = self._current_player

        self._history.append((row, col, self._last_action))
        self._board[row, col] = int(player_who_moved)
        self._move_count += 1
        self._last_action = (row, col)

        # W1-M1-02 intentionally has no win detection.  A full board is the
        # only terminal state the mock can identify, and it is treated as draw.
        self._done = self._move_count == self.config.board_size**2
        self._winner = None
        self._current_player = (
            Player.O if player_who_moved == Player.X else Player.X
        )

        return StepResult(
            next_state=self.clone_state(),
            reward=0.0,
            done=self._done,
            winner=self._winner,
        )

    def is_terminal(self) -> bool:
        return self._done

    def result(self, player: Player) -> float | None:
        """Return the terminal result from one player's perspective."""

        if not isinstance(player, Player) or player == Player.EMPTY:
            raise ValueError(f"result() requires Player.X or Player.O, got {player!r}.")
        if not self._done:
            return None
        if self._winner is None:
            return 0.0
        return 1.0 if self._winner == player else -1.0

    def clone_state(self) -> GameState:
        """Create a state with no mutable board reference shared with the mock."""

        return GameState(
            board=self._board.astype(np.int8, copy=True).tolist(),
            current_player=self._current_player,
            last_action=self._last_action,
            move_count=self._move_count,
            terminated=self._done,
            winner=self._winner,
        )

    def clone_env(self) -> "MockGameEnv":
        """Create an independent environment snapshot for UI experiments."""

        clone = MockGameEnv(copy.deepcopy(self.config))
        clone._board = self._board.copy()
        clone._current_player = self._current_player
        clone._done = self._done
        clone._winner = self._winner
        clone._last_action = self._last_action
        clone._move_count = self._move_count
        clone._history = self._history[:]
        return clone

    def undo(self) -> GameState:
        """Undo one successful mock step and restore all public metadata."""

        if not self._history:
            raise UndoError("Nothing to undo: move history is empty.")

        row, col, previous_last_action = self._history.pop()
        self._current_player = Player(int(self._board[row, col]))
        self._board[row, col] = int(Player.EMPTY)
        self._move_count -= 1
        self._last_action = previous_last_action
        self._done = False
        self._winner = None
        return self.clone_state()

    def render(self) -> str:
        """Print and return a compact console representation for smoke tests."""

        symbols = {
            int(Player.X): "X",
            int(Player.O): "O",
            int(Player.EMPTY): ".",
        }
        lines = [" ".join(symbols[int(cell)] for cell in row) for row in self._board]
        lines.append(f"Current Player: {self._current_player.name}")
        rendered = "\n".join(lines)
        print(rendered)
        return rendered

    def _validate_config(self) -> None:
        if isinstance(self.config.board_size, bool) or not isinstance(
            self.config.board_size, Integral
        ):
            raise TypeError("board_size must be an integer")
        if self.config.board_size <= 0:
            raise ValueError("board_size must be greater than zero")

    def _validate_action(self, action: object) -> Action:
        if self._done:
            raise InvalidActionError(
                InvalidActionReason.GAME_OVER,
                action,
                "The game is already finished.",
            )

        if not isinstance(action, tuple) or len(action) != 2:
            raise InvalidActionError(
                InvalidActionReason.MALFORMED,
                action,
                "Action must be a (row, col) tuple following the caro-v2 contract.",
            )

        row, col = action
        if (
            isinstance(row, bool)
            or isinstance(col, bool)
            or not isinstance(row, Integral)
            or not isinstance(col, Integral)
        ):
            raise InvalidActionError(
                InvalidActionReason.MALFORMED,
                action,
                "Action coordinates must be integers.",
            )

        row, col = int(row), int(col)
        size = self.config.board_size
        if not (0 <= row < size and 0 <= col < size):
            raise InvalidActionError(
                InvalidActionReason.OUT_OF_BOUNDS,
                action,
                f"Action ({row}, {col}) is out of bounds for a {size}x{size} board.",
            )

        if self._board[row, col] != int(Player.EMPTY):
            raise InvalidActionError(
                InvalidActionReason.OCCUPIED,
                action,
                f"Cell ({row}, {col}) is already occupied.",
            )

        return row, col

