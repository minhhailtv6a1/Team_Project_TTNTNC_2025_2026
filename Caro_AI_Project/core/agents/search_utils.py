"""Pure tactical and candidate-ordering helpers for search agents.

The functions in this module never mutate the caller's board.  They implement
rule-level win/block detection and lightweight locality/threat ranking without
delegating the final policy decision to :class:`HeuristicAgent`.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random

from core.engine.interfaces import Action, BoardMatrix, GameConfig, Player
from core.engine.rules import DIRECTIONS, RuleEngine

__all__ = [
    "TacticalSummary",
    "immediate_winning_actions",
    "tactical_summary",
    "rank_candidate_actions",
    "choose_tactical_local_action",
    "normalized_line_value",
]


@dataclass(frozen=True, slots=True)
class TacticalSummary:
    """Immediate tactical facts for the player to move."""

    winning_actions: tuple[Action, ...]
    opponent_winning_actions: tuple[Action, ...]

    @property
    def unique_forced_block(self) -> Action | None:
        if not self.winning_actions and len(self.opponent_winning_actions) == 1:
            return self.opponent_winning_actions[0]
        return None

    @property
    def has_unanswerable_threats(self) -> bool:
        return not self.winning_actions and len(self.opponent_winning_actions) > 1


def _opponent(player: Player) -> Player:
    return Player.O if player == Player.X else Player.X


def immediate_winning_actions(
    board: BoardMatrix,
    legal_actions: list[Action],
    player: Player,
    config: GameConfig,
) -> list[Action]:
    """Return sorted legal actions that immediately win for ``player``.

    A private board copy is reused across probes, so the input board remains
    unchanged and the exact Caro blocked-end rule stays delegated to RuleEngine.
    """

    work = [row[:] for row in board]
    value = int(player)
    empty = int(Player.EMPTY)
    wins: list[Action] = []
    for action in sorted(legal_actions):
        row, col = action
        if work[row][col] != empty:
            continue
        work[row][col] = value
        if RuleEngine.check_winner_from_action(work, action, config) == player:
            wins.append(action)
        work[row][col] = empty
    return wins


def tactical_summary(
    board: BoardMatrix,
    legal_actions: list[Action],
    player: Player,
    config: GameConfig,
) -> TacticalSummary:
    """Return immediate wins and opponent wins without mutating ``board``."""

    return TacticalSummary(
        winning_actions=tuple(
            immediate_winning_actions(board, legal_actions, player, config)
        ),
        opponent_winning_actions=tuple(
            immediate_winning_actions(board, legal_actions, _opponent(player), config)
        ),
    )


def _is_local(board: BoardMatrix, action: Action, radius: int) -> bool:
    size = len(board)
    row, col = action
    empty = int(Player.EMPTY)
    for r in range(max(0, row - radius), min(size, row + radius + 1)):
        for c in range(max(0, col - radius), min(size, col + radius + 1)):
            if board[r][c] != empty:
                return True
    return False


def _local_actions(
    board: BoardMatrix,
    legal_actions: list[Action],
    radius: int,
) -> list[Action]:
    return [action for action in legal_actions if _is_local(board, action, radius)]


def _line_strength(
    board: BoardMatrix,
    action: Action,
    player: Player,
) -> int:
    """Longest contiguous line created by a hypothetical placement."""

    size = len(board)
    row, col = action
    value = int(player)
    best = 1
    for dr, dc in DIRECTIONS:
        run = 1
        for sign in (1, -1):
            r, c = row + sign * dr, col + sign * dc
            while 0 <= r < size and 0 <= c < size and board[r][c] == value:
                run += 1
                r += sign * dr
                c += sign * dc
        best = max(best, run)
    return best


def rank_candidate_actions(
    board: BoardMatrix,
    legal_actions: list[Action],
    player: Player,
    config: GameConfig,
    *,
    neighbor_radius: int,
    rng: random.Random,
) -> list[Action]:
    """Rank the full legal set by tactical urgency and locality.

    The returned list always contains every legal action exactly once.  Urgent
    actions are deterministic; equally ranked local actions and all remote
    remainder actions use only the supplied local RNG.
    """

    if not legal_actions:
        return []
    # A winning or blocking placement must touch an existing stone. Restricting
    # exact tactical probes to radius 1 avoids scanning the whole empty board at
    # every tree node while preserving immediate-win/block completeness.
    tactical_probes = _local_actions(board, legal_actions, 1)
    summary = tactical_summary(board, tactical_probes, player, config)
    urgent = list(summary.winning_actions)
    urgent.extend(a for a in summary.opponent_winning_actions if a not in urgent)
    urgent_set = set(urgent)
    opponent = _opponent(player)

    local: list[tuple[int, int, float, Action]] = []
    remainder: list[Action] = []
    center = (len(board) - 1) / 2.0
    for action in legal_actions:
        if action in urgent_set:
            continue
        if _is_local(board, action, neighbor_radius):
            own_run = _line_strength(board, action, player)
            opp_run = _line_strength(board, action, opponent)
            distance = (action[0] - center) ** 2 + (action[1] - center) ** 2
            ranked = (-own_run, -opp_run, distance, action)
            local.append(ranked)
        else:
            # A contiguous threat necessarily touches an existing stone, so a
            # remote action cannot belong to the threat tier.
            remainder.append(action)

    # Seeded shuffles make exact-score ties explore reproducibly without adding
    # a permanent row-major policy bias. Python's stable sort preserves them.
    rng.shuffle(local)
    local.sort(key=lambda item: item[:3])
    rng.shuffle(remainder)
    return (
        urgent
        + [item[3] for item in local]
        + remainder
    )


def choose_tactical_local_action(
    board: BoardMatrix,
    legal_actions: list[Action],
    player: Player,
    config: GameConfig,
    *,
    neighbor_radius: int,
    epsilon: float,
    rng: random.Random,
) -> Action:
    """Choose one seeded epsilon-greedy tactical-local rollout action."""

    if not legal_actions:
        raise ValueError("cannot choose a rollout action from an empty legal set")
    tactical_probes = _local_actions(board, legal_actions, 1)
    summary = tactical_summary(board, tactical_probes, player, config)
    if summary.winning_actions:
        return summary.winning_actions[0]
    if summary.unique_forced_block is not None:
        return summary.unique_forced_block
    if rng.random() < epsilon:
        return rng.choice(legal_actions)

    candidates = _local_actions(board, legal_actions, neighbor_radius) or legal_actions
    opponent = _opponent(player)
    scored: list[tuple[int, int, float, Action]] = []
    center = (len(board) - 1) / 2.0
    for action in candidates:
        own_run = _line_strength(board, action, player)
        opp_run = _line_strength(board, action, opponent)
        distance = (action[0] - center) ** 2 + (action[1] - center) ** 2
        scored.append((-own_run, -opp_run, distance, action))
    rng.shuffle(scored)
    scored.sort(key=lambda item: item[:3])
    return scored[0][3]


def normalized_line_value(
    board: BoardMatrix,
    root_player: Player,
    win_length: int,
) -> float:
    """Cheap non-terminal rollout value in ``[-1, 1]``.

    This evaluator is intentionally independent of Minimax's pattern table. It
    scores maximal contiguous lines, their open ends, and returns a bounded
    root-perspective difference through ``tanh``.
    """

    size = len(board)
    empty = int(Player.EMPTY)

    def score_for(player: Player) -> float:
        value = int(player)
        score = 0.0
        for row in range(size):
            for col in range(size):
                if board[row][col] != value:
                    continue
                for dr, dc in DIRECTIONS:
                    pr, pc = row - dr, col - dc
                    if 0 <= pr < size and 0 <= pc < size and board[pr][pc] == value:
                        continue
                    run = 1
                    r, c = row + dr, col + dc
                    while 0 <= r < size and 0 <= c < size and board[r][c] == value:
                        run += 1
                        r += dr
                        c += dc
                    open_ends = 0
                    if 0 <= pr < size and 0 <= pc < size and board[pr][pc] == empty:
                        open_ends += 1
                    if 0 <= r < size and 0 <= c < size and board[r][c] == empty:
                        open_ends += 1
                    capped = min(run, win_length - 1)
                    score += (capped * capped) * (1.0 + 0.25 * open_ends)
        return score

    opponent = _opponent(root_player)
    difference = score_for(root_player) - score_for(opponent)
    return math.tanh(difference / 25.0)
