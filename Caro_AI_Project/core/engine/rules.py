from typing import Tuple, Optional, List
import numpy as np
from core.engine.interfaces import GameConfig, Player


class RuleEngine:
    """
    Module xử lý luật chơi chuẩn theo Hợp đồng caro-v1 (chặn 2 đầu, overline, hòa).
    """

    @staticmethod
    def _is_valid_coord(row: int, col: int, board_size: int) -> bool:
        """Kiểm tra tọa độ (row, col) có nằm trong bàn cờ hay không."""
        return 0 <= row < board_size and 0 <= col < board_size

    @staticmethod
    def check_line(
        board: List[List[int]], 
        row: int, 
        col: int, 
        dr: int, 
        dc: int, 
        player: int, 
        board_size: int, 
        win_length: int = 5
    ) -> bool:
        """
        Kiểm tra từ vị trí (row, col) theo hướng (dr, dc) xem có tạo thành chuỗi thắng hợp lệ không.
        - dr, dc: Hướng duyệt ((0,1) Ngang, (1,0) Dọc, (1,1) Chéo chính, (1,-1) Chéo phụ).
        """
        count = 0
        r, c = row, col

        # 1. Đếm số quân liên tiếp của player theo hướng (dr, dc)
        while RuleEngine._is_valid_coord(r, c, board_size) and board[r][c] == player:
            count += 1
            r += dr
            c += dc

        # Nếu không đủ số quân tối thiểu (mặc định 5) thì không thắng
        if count < win_length:
            return False

        # 2. Kiểm tra chặn 2 đầu
        # Đầu 1: Ngay trước quân đầu tiên (row - dr, col - dc)
        r_head1, c_head1 = row - dr, col - dc
        blocked_head1 = (
            not RuleEngine._is_valid_coord(r_head1, c_head1, board_size) 
            or board[r_head1][c_head1] == -player
        )

        # Đầu 2: Ngay sau quân cuối cùng (r, c)
        r_head2, c_head2 = r, c
        blocked_head2 = (
            not RuleEngine._is_valid_coord(r_head2, c_head2, board_size) 
            or board[r_head2][c_head2] == -player
        )

        # Nếu bị chặn CẢ 2 ĐẦU (bởi quân địch hoặc biên bàn cờ) -> KHÔNG THẮNG
        if blocked_head1 and blocked_head2:
            return False

        # Chỉ bị chặn 1 đầu hoặc không bị chặn đầu nào -> THẮNG
        return True

    @staticmethod
    def check_winner(board: List[List[int]], config: GameConfig = GameConfig()) -> Optional[Player]:
        """
        Kiểm tra toàn bộ bàn cờ xem đã có người thắng hay chưa.
        Trả về:
            Player.X: X thắng (1)
            Player.O: O thắng (-1)
            None: Chưa có người thắng
        """
        size = config.board_size
        win_len = config.win_length
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

        for r in range(size):
            for c in range(size):
                player = board[r][c]
                if player == Player.EMPTY:
                    continue

                for dr, dc in directions:
                    # Tối ưu: Chỉ kiểm tra bắt đầu chuỗi từ ô đầu tiên (ô trước đó không cùng màu)
                    prev_r, prev_c = r - dr, c - dc
                    if RuleEngine._is_valid_coord(prev_r, prev_c, size) and board[prev_r][prev_c] == player:
                        continue

                    if RuleEngine.check_line(board, r, c, dr, dc, player, size, win_len):
                        return Player(player)

        return None

    @staticmethod
    def is_board_full(board: List[List[int]], board_size: int) -> bool:
        """Kiểm tra bàn cờ đã đầy hoàn toàn hay chưa."""
        for r in range(board_size):
            for c in range(board_size):
                if board[r][c] == Player.EMPTY:
                    return False
        return True

    @staticmethod
    def is_terminal(board: List[List[int]], config: GameConfig = GameConfig()) -> Tuple[bool, Optional[Player]]:
        """
        Kiểm tra ván đấu đã kết thúc hay chưa theo đúng Contract.
        Trả về: (done: bool, winner: Optional[Player])
            - (True, Player.X): X thắng
            - (True, Player.O): O thắng
            - (True, None): Hòa (bàn cờ đầy mà không ai thắng)
            - (False, None): Chưa kết thúc
        """
        winner = RuleEngine.check_winner(board, config)
        if winner is not None:
            return True, winner

        if RuleEngine.is_board_full(board, config.board_size):
            return True, None  # Hòa (done = True, winner = None theo contract)

        return False, None