"""
Thứ tự ưu tiên công bố (cao -> thấp):

    1. WIN     : nước đi thắng ngay cho người đang đi.
    2. BLOCK   : nước đi chặn nước thắng ngay của đối thủ.
    3. THREAT  : tạo threat cho mình và/hoặc chặn threat của đối thủ.
    4. CENTER  : ưu tiên ô gần trung tâm bàn.

Các tầng được tách bằng khoảng cách điểm số đủ lớn (``WIN_SCORE`` >
``BLOCK_SCORE`` > mọi threat score > center bonus, vì center bonus luôn < 1
còn threat score nhỏ nhất là 10), nên thứ tự ưu tiên luôn đúng.

Tie-break deterministic: khi score bằng nhau, chọn action đứng trước theo
row-major (hàng nhỏ trước, rồi cột nhỏ).

Chỉ dùng public API của ``GameEnv`` (``state``, ``legal_actions``, ``config``).
Agent không mutation env và không dùng RNG nên luôn tái lập.

Các hàm ``cell_potential`` và ``center_bonus`` được để public
(Minimax) dùng lại làm evaluation chung, tránh hai implementation lệch nhau.
"""
from __future__ import annotations

import time

from core.engine.interfaces import (
    Action,
    AgentDecision,
    BoardMatrix,
    GameEnv,
    Player,
    SearchBudget,
)

__all__ = [
    "HeuristicAgent",
    "WIN_SCORE",
    "BLOCK_SCORE",
    "DEFENSE_FACTOR",
    "cell_potential",
    "center_bonus",
]

# --- Hằng số điểm ------------------------------------------------------------
WIN_SCORE = 1_000_000.0
BLOCK_SCORE = 100_000.0
# Chặn threat của đối thủ được tính hơi thấp hơn tự tạo threat cùng loại.
DEFENSE_FACTOR = 0.9

# 4 hướng: ngang, dọc, chéo xuống, chéo lên.
_DIRECTIONS: tuple[tuple[int, int], ...] = ((0, 1), (1, 0), (1, 1), (1, -1))

# Điểm theo (số quân còn thiếu để thắng, số đầu còn trống).
#   thiếu 1 = "bốn", thiếu 2 = "ba", thiếu 3 = "hai".
# Chuỗi một quân (thiếu 4) và chuỗi bị chặn cả hai đầu cho điểm 0:
# chuỗi chưa đủ độ dài mà cả hai đầu đều bị chặn thì không thể thắng.
_PATTERN_SCORES: dict[tuple[int, int], float] = {
    (1, 2): 10_000.0,  # open four: đối thủ không chặn được
    (1, 1): 2_000.0,   # closed four: ép đối thủ phải chặn
    (2, 2): 1_500.0,   # open three
    (2, 1): 150.0,     # closed three
    (3, 2): 100.0,     # open two
    (3, 1): 10.0,      # closed two
}


def _scan_direction(
    board: BoardMatrix,
    row: int,
    col: int,
    dr: int,
    dc: int,
    player: int,
) -> tuple[int, int]:
    """Giả sử ``player`` đặt quân tại ``(row, col)``.

    Trả về ``(run, open_ends)``: độ dài chuỗi liên tiếp đi qua ô đó theo
    hướng ``(dr, dc)`` (đã tính cả ô đặt) và số đầu chuỗi còn là ô trống.
    """
    size = len(board)
    empty = int(Player.EMPTY)
    run = 1
    open_ends = 0
    for sign in (1, -1):
        r, c = row + sign * dr, col + sign * dc
        while 0 <= r < size and 0 <= c < size and board[r][c] == player:
            run += 1
            r += sign * dr
            c += sign * dc
        if 0 <= r < size and 0 <= c < size and board[r][c] == empty:
            open_ends += 1
    return run, open_ends


def cell_potential(
    board: BoardMatrix,
    action: Action,
    player: Player,
    win_length: int,
) -> tuple[float, bool]:
    """Đánh giá nếu ``player`` đặt quân tại ``action`` (ô phải đang trống).

    Trả về ``(threat_score, wins)``:
      * ``wins``: nước đặt này tạo chuỗi >= ``win_length`` (thắng ngay). Kể cả
        thế có khoảng trống như ``X X _ X X`` vì đếm từ chính ô được đặt.
      * ``threat_score``: tổng điểm pattern của 4 hướng (0 nếu không có gì).

    Chỉ đọc ``board``, không sửa.
    """
    row, col = action
    value = int(player)
    total = 0.0
    wins = False
    for dr, dc in _DIRECTIONS:
        run, open_ends = _scan_direction(board, row, col, dr, dc, value)
        if run >= win_length:
            wins = True
            continue
        total += _PATTERN_SCORES.get((win_length - run, open_ends), 0.0)
    return total, wins


def center_bonus(action: Action, board_size: int) -> float:
    """Điểm ưu tiên trung tâm, luôn trong ``[0, 1)``.

    Ô gần tâm bàn có bonus lớn hơn. Giá trị < 1 đảm bảo bonus chỉ dùng để
    phân định khi các tầng trên bằng nhau.
    """
    center = (board_size - 1) / 2
    max_d2 = 2 * center * center
    d2 = (action[0] - center) ** 2 + (action[1] - center) ** 2
    return (max_d2 - d2) / (max_d2 + 1)


class HeuristicAgent:
    """Agent chọn nước theo thứ tự: thắng ngay -> chặn thua -> threat -> trung tâm.

    ``budget`` được nhận để thỏa ``Agent`` protocol nhưng không dùng: agent
    chỉ duyệt đúng một lượt các legal action (<= 121 ô trên bàn 11x11), nên
    không có vòng lặp nào cần giới hạn depth, nodes hay thời gian.
    """

    def __init__(self, name: str = "heuristic") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def choose_action(
        self,
        env: GameEnv,
        budget: SearchBudget | None = None,
    ) -> AgentDecision:
        started = time.perf_counter()

        state = env.state  # snapshot độc lập, không chạm vào env thật
        if state.terminated:
            raise RuntimeError(f"{self._name}: cannot choose an action in a terminal state.")
        legal = env.legal_actions()
        if not legal:
            raise RuntimeError(f"{self._name}: no legal actions available.")

        board = state.board
        win_length = env.config.win_length
        size = env.config.board_size
        me = state.current_player
        opponent = Player.O if me == Player.X else Player.X

        best_action: Action | None = None
        best_score = float("-inf")
        # Duyệt row-major + chỉ thay khi điểm lớn hơn hẳn => tie-break row-major.
        for action in sorted(legal):
            attack, wins = cell_potential(board, action, me, win_length)
            if wins:
                score = WIN_SCORE
            else:
                defend, blocks = cell_potential(board, action, opponent, win_length)
                if blocks:
                    score = BLOCK_SCORE
                else:
                    score = attack + DEFENSE_FACTOR * defend
            score += center_bonus(action, size)

            if score > best_score:
                best_action, best_score = action, score

        assert best_action is not None  # legal không rỗng nên luôn có action
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return AgentDecision(
            action=best_action,
            score=best_score,
            nodes=len(legal),  # số candidate đã đánh giá
            simulations=0,
            elapsed_ms=elapsed_ms,
        )