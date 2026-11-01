# File: core/agents/minimax_ai.py
"""MinimaxAgent theo contract ``caro-v2`` (W34-M2-01, commit 2 và 3).

Một codebase duy nhất cho Minimax thuần và Alpha-Beta; Alpha-Beta và move
ordering bật/tắt bằng tham số constructor (phục vụ ablation sau này).

Quy ước:
  * ``score`` theo góc nhìn player đang đi tại root: lớn hơn là tốt hơn cho
    root, bất kể root là X hay O. ``None`` chỉ khi budget chạm giới hạn trước
    khi hoàn tất depth 1 (xem "Budget" bên dưới).
  * Leaf terminal: root thắng ``WIN_VALUE - ply``, thua ``-(WIN_VALUE - ply)``,
    hòa ``0.0``. Leaf chạm depth: ``evaluate_board`` (pattern + vị trí).
  * ``max_depth = d``: nhìn trước đúng ``d`` ply, nước của root là ply 1.
  * ``nodes`` = số lần gọi ``step`` trong lúc tìm kiếm, cộng dồn qua mọi
    iteration (root không tính). Cùng định nghĩa cho pruning bật và tắt.
  * Candidate: ô legal trong bán kính ``neighbor_radius`` quanh các quân đã đặt
    (bàn trống: ô trung tâm). Lọc nội bộ trong tập legal nên action trả về
    luôn thuộc ``env.legal_actions()``.

Iterative deepening:
  Tìm lần lượt depth 1, 2, ... ``max_depth``. Kết quả của depth *hoàn chỉnh*
  gần nhất luôn là đáp án; iteration bị cắt giữa chừng bị bỏ.
  Dừng sớm khi đã chứng minh được nước thắng (không depth sâu hơn nào tìm được
  nước thắng nhanh hơn).

Budget (dừng khi chạm giới hạn đầu tiên):
  * ``max_depth``: số ply tối đa (mặc định ``default_depth``).
  * ``max_nodes``: tổng node tối đa; không bao giờ bị vượt.
  * ``time_limit_ms``: wall-clock cho một lần ``choose_action``, kiểm tra trước
    mỗi node nên sai số chỉ cỡ một lần ordering/evaluation.
  Nếu giới hạn chạm trước khi xong depth 1, agent trả nước có ưu tiên
  heuristic cao nhất (win > block > threat > center) với ``score=None``.

Move ordering:
  Mỗi node sắp candidate theo ``action_priority`` của người đi tại node đó (win
  trước, rồi block, rồi điểm threat/center cao); hòa điểm thì row-major. Riêng
  root, nước tốt nhất của iteration trước được đưa lên đầu. Thứ tự chỉ phụ
  thuộc vào state, không phụ thuộc Alpha-Beta bật/tắt, nên hai chế độ cho cùng
  action và cùng score; chỉ ``nodes`` khác nhau.

Tie-break ở root: nước đứng trước trong thứ tự duyệt thắng khi điểm bằng nhau
(chỉ thay khi điểm lớn hơn hẳn).

Chỉ dùng public API của ``GameEnv``; mô phỏng chạy trên ``clone_env()`` bằng
``step()``/``undo()`` nên env nhận vào không bị mutation, kể cả khi dừng vì
budget.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from core.agents.heuristic_ai import action_priority, center_bonus, pattern_score
from core.engine.interfaces import (
    Action,
    AgentDecision,
    BoardMatrix,
    GameEnv,
    GameState,
    Player,
    SearchBudget,
    StepResult,
)

__all__ = ["MinimaxAgent", "WIN_VALUE", "evaluate_board", "candidate_actions"]

WIN_VALUE = 1_000_000.0
# Giới hạn điểm heuristic để không bao giờ vượt giá trị thắng/thua thật.
_EVAL_CLAMP = 500_000.0
# Điểm vị trí mỗi quân (center_bonus < 1) nhỏ hơn nhiều so với pattern.
POSITION_WEIGHT = 0.1

_DIRECTIONS: tuple[tuple[int, int], ...] = ((0, 1), (1, 0), (1, 1), (1, -1))
_INF = float("inf")


# --- Evaluation (dùng chung bảng điểm pattern với HeuristicAgent) ------------
def evaluate_board(board: BoardMatrix, root_player: Player, win_length: int) -> float:
    """Điểm tĩnh của board theo góc nhìn ``root_player`` (dương = tốt cho root).

    Gồm: tổng điểm pattern các chuỗi liên tiếp (theo số đầu trống) của root
    trừ của đối thủ, cộng chênh lệch điểm vị trí trung tâm. Mỗi chuỗi cực đại
    chỉ được tính một lần. Chỉ đọc ``board``.
    """
    size = len(board)
    empty = int(Player.EMPTY)
    me = int(root_player)
    mine = 0.0
    theirs = 0.0

    for r in range(size):
        row = board[r]
        for c in range(size):
            p = row[c]
            if p == empty:
                continue
            score = center_bonus((r, c), size) * POSITION_WEIGHT
            for dr, dc in _DIRECTIONS:
                pr, pc = r - dr, c - dc
                if 0 <= pr < size and 0 <= pc < size and board[pr][pc] == p:
                    continue  # chuỗi này đã được tính từ quân đầu chuỗi
                run = 1
                nr, nc = r + dr, c + dc
                while 0 <= nr < size and 0 <= nc < size and board[nr][nc] == p:
                    run += 1
                    nr += dr
                    nc += dc
                if run >= win_length:
                    score += _EVAL_CLAMP  # state thắng thật được xử lý ở terminal
                    continue
                open_ends = 0
                if 0 <= pr < size and 0 <= pc < size and board[pr][pc] == empty:
                    open_ends += 1
                if 0 <= nr < size and 0 <= nc < size and board[nr][nc] == empty:
                    open_ends += 1
                score += pattern_score(win_length - run, open_ends)
            if p == me:
                mine += score
            else:
                theirs += score

    return max(-_EVAL_CLAMP, min(_EVAL_CLAMP, mine - theirs))


def candidate_actions(
    board: BoardMatrix,
    legal: list[Action] | None = None,
    radius: int = 2,
) -> list[Action]:
    """Các ô trống trong bán kính ``radius`` (Chebyshev) quanh quân đã đặt, row-major.

    Bàn trống: trả về ô trung tâm. Nếu ``legal`` được truyền, chỉ giữ ô thuộc
    ``legal``.
    """
    size = len(board)
    empty = int(Player.EMPTY)
    near = [[False] * size for _ in range(size)]
    has_stone = False
    for r in range(size):
        for c in range(size):
            if board[r][c] != empty:
                has_stone = True
                for rr in range(max(0, r - radius), min(size, r + radius + 1)):
                    for cc in range(max(0, c - radius), min(size, c + radius + 1)):
                        near[rr][cc] = True

    if not has_stone:
        mid = size // 2
        return [(mid, mid)]

    legal_set = None if legal is None else set(legal)
    result: list[Action] = []
    for r in range(size):
        for c in range(size):
            if near[r][c] and board[r][c] == empty:
                if legal_set is None or (r, c) in legal_set:
                    result.append((r, c))
    return result


# --- Hạ tầng tìm kiếm --------------------------------------------------------
class _SearchStop(Exception):
    """Nội bộ: budget chạm giới hạn, bỏ iteration đang chạy."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class _Context:
    root_player: Player
    win_length: int
    max_nodes: int | None
    deadline: float | None  # mốc perf_counter, None nếu không giới hạn thời gian
    nodes: int = 0

    def check_limits(self) -> None:
        """Gọi TRƯỚC mỗi ``step``; ném ``_SearchStop`` nếu chạm giới hạn."""
        if self.max_nodes is not None and self.nodes >= self.max_nodes:
            raise _SearchStop("max_nodes")
        if self.deadline is not None and time.perf_counter() >= self.deadline:
            raise _SearchStop("time_limit")


class MinimaxAgent:
    """Minimax / Alpha-Beta giới hạn độ sâu, dùng iterative deepening.

    Args:
        name: tên agent trong log/runner.
        default_depth: độ sâu tối đa khi ``budget.max_depth`` là ``None``.
        alpha_beta: bật/tắt Alpha-Beta. Không đổi action/score, chỉ đổi ``nodes``.
        move_ordering: bật/tắt sắp xếp nước đi theo ``action_priority``.
        neighbor_radius: bán kính lọc candidate quanh các quân đã đặt.
        max_candidates: nếu đặt, mỗi node chỉ xét top-K candidate theo thứ tự
            ordering. ``None`` (mặc định) giữ minimax chính xác trên toàn bộ
            candidate; đặt K nhỏ để chạy depth cao trong thời gian ngắn (đánh
            đổi độ chính xác). Cần ``move_ordering=True``.

    Sau mỗi ``choose_action``, ``last_depth_completed`` và ``last_stop_reason``
    (``"depth_limit"``, ``"forced_win"``, ``"max_nodes"`` hoặc ``"time_limit"``)
    mô tả lần tìm kiếm vừa rồi, phục vụ benchmark.
    """

    def __init__(
        self,
        name: str = "minimax",
        default_depth: int = 2,
        alpha_beta: bool = True,
        move_ordering: bool = True,
        neighbor_radius: int = 2,
        max_candidates: int | None = None,
    ) -> None:
        if default_depth <= 0:
            raise ValueError("default_depth must be a positive integer")
        if neighbor_radius <= 0:
            raise ValueError("neighbor_radius must be a positive integer")
        if max_candidates is not None:
            if max_candidates <= 0:
                raise ValueError("max_candidates must be a positive integer or None")
            if not move_ordering:
                raise ValueError("max_candidates requires move_ordering=True")
        self._name = name
        self._default_depth = default_depth
        self._alpha_beta = alpha_beta
        self._ordering = move_ordering
        self._radius = neighbor_radius
        self._max_candidates = max_candidates
        self.last_depth_completed = 0
        self.last_stop_reason = ""

    @property
    def name(self) -> str:
        return self._name

    # -- API công khai --------------------------------------------------------
    def choose_action(
        self,
        env: GameEnv,
        budget: SearchBudget | None = None,
    ) -> AgentDecision:
        started = time.perf_counter()

        root_state = env.state
        if root_state.terminated:
            raise RuntimeError(f"{self._name}: cannot choose an action in a terminal state.")
        legal = env.legal_actions()
        if not legal:
            raise RuntimeError(f"{self._name}: no legal actions available.")

        max_depth = self._default_depth
        max_nodes = None
        deadline = None
        if budget is not None:
            if budget.max_depth is not None:
                max_depth = budget.max_depth
            max_nodes = budget.max_nodes
            if budget.time_limit_ms is not None:
                deadline = started + budget.time_limit_ms / 1000.0

        ctx = _Context(
            root_player=root_state.current_player,
            win_length=env.config.win_length,
            max_nodes=max_nodes,
            deadline=deadline,
        )
        sim = env.clone_env()  # mọi mô phỏng chạy trên clone
        root_candidates = candidate_actions(root_state.board, legal, self._radius) or sorted(legal)

        completed: tuple[Action, float] | None = None
        previous_best: Action | None = None
        reason = "depth_limit"
        depth_done = 0
        for depth in range(1, max_depth + 1):
            try:
                action, value = self._root_iteration(
                    sim, root_state, root_candidates, depth, previous_best, ctx
                )
            except _SearchStop as stop:
                reason = stop.reason
                break
            completed = (action, value)
            previous_best = action
            depth_done = depth
            if value > _EVAL_CLAMP:  # đã chứng minh thắng; depth sâu hơn không nhanh hơn
                if depth < max_depth:
                    reason = "forced_win"
                break

        if completed is None:
            # Chạm budget trước khi xong depth 1: trả nước ưu tiên heuristic cao nhất.
            action = self._order(root_state, root_candidates, None, ctx.win_length)[0]
            best_score = None
        else:
            action, best_score = completed

        self.last_depth_completed = depth_done
        self.last_stop_reason = reason
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return AgentDecision(
            action=action,
            score=best_score,
            nodes=ctx.nodes,
            simulations=0,
            elapsed_ms=elapsed_ms,
        )

    # -- ordering -------------------------------------------------------------
    def _order(
        self,
        state: GameState,
        candidates: list[Action],
        first: Action | None,
        win_length: int,
    ) -> list[Action]:
        """Thứ tự duyệt candidate; ``first`` (nếu có) được đưa lên đầu."""
        if not self._ordering:
            ordered = candidates
        else:
            mover = state.current_player
            scored = [
                (-action_priority(state.board, a, mover, win_length), a) for a in candidates
            ]
            scored.sort()  # hòa điểm => row-major
            ordered = [a for _, a in scored]
            if self._max_candidates is not None:
                ordered = ordered[: self._max_candidates]
        if first is not None and first in ordered and ordered[0] != first:
            ordered = [first] + [a for a in ordered if a != first]
        return ordered

    # -- search ---------------------------------------------------------------
    def _root_iteration(
        self,
        sim: GameEnv,
        root_state: GameState,
        candidates: list[Action],
        depth: int,
        previous_best: Action | None,
        ctx: _Context,
    ) -> tuple[Action, float]:
        """Một iteration depth cố định; trả (action, value) chính xác của root."""
        best_action: Action | None = None
        best_value = -_INF
        alpha = -_INF
        for action in self._order(root_state, candidates, previous_best, ctx.win_length):
            ctx.check_limits()
            result = sim.step(action)
            ctx.nodes += 1
            if result.done:
                value = self._terminal_value(result, ctx.root_player, 1)
            else:
                value = self._search(
                    sim, result.next_state, depth - 1, False, 1, alpha, _INF, ctx
                )
            sim.undo()
            if value > best_value:  # strict: hòa điểm giữ nước đứng trước
                best_action, best_value = action, value
                if self._alpha_beta:
                    alpha = best_value
        assert best_action is not None
        return best_action, best_value

    def _search(
        self,
        sim: GameEnv,
        state: GameState,
        depth: int,
        maximizing: bool,
        ply: int,
        alpha: float,
        beta: float,
        ctx: _Context,
    ) -> float:
        """Giá trị minimax của ``state`` (chưa terminal) theo góc nhìn root.

        ``depth``: số ply còn được phép đi; ``ply``: số ply đã đi từ root.
        ``alpha``/``beta`` chỉ có tác dụng khi Alpha-Beta bật.
        """
        if depth == 0:
            return evaluate_board(state.board, ctx.root_player, ctx.win_length)

        candidates = candidate_actions(state.board, sim.legal_actions(), self._radius)
        if not candidates:
            candidates = sim.legal_actions()
        best = -_INF if maximizing else _INF
        for action in self._order(state, candidates, None, ctx.win_length):
            ctx.check_limits()
            result = sim.step(action)
            ctx.nodes += 1
            if result.done:
                value = self._terminal_value(result, ctx.root_player, ply + 1)
            else:
                value = self._search(
                    sim, result.next_state, depth - 1, not maximizing, ply + 1,
                    alpha, beta, ctx,
                )
            sim.undo()
            if maximizing:
                if value > best:
                    best = value
                if self._alpha_beta:
                    alpha = max(alpha, best)
                    if alpha >= beta:
                        break
            else:
                if value < best:
                    best = value
                if self._alpha_beta:
                    beta = min(beta, best)
                    if alpha >= beta:
                        break
        return best

    @staticmethod
    def _terminal_value(result: StepResult, root_player: Player, ply: int) -> float:
        if result.winner is None:
            return 0.0  # hòa
        if result.winner == root_player:
            return WIN_VALUE - ply
        return -(WIN_VALUE - ply)