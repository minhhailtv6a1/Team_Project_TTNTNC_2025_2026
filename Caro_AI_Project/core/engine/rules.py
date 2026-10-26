from typing import Tuple, Optional, List
from core.engine.interfaces import GameConfig, Player

DIRECTIONS: Tuple[Tuple[int, int], ...] = ((0, 1), (1, 0), (1, 1), (1, -1))


class RuleEngine:
    """
    Module xử lý luật chơi chuẩn theo contract (caro-v2):
      - Chuỗi liên tiếp >= win_length là ứng viên thắng (overline được tính).
      - Một đầu bị chặn khi gặp quân đối phương HOẶC biên bàn cờ.
      - Bị chặn CẢ HAI đầu -> không thắng.
      - Hòa: bàn đầy mà chưa có người thắng (thắng được xét trước hòa).

    Hàm không sửa board, không có side effect.
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
        win_length: int = 5,
    ) -> bool:
        """
        Kiểm tra chuỗi liên tiếp của `player` đi qua ô (row, col) theo trục (dr, dc)
        có phải chuỗi thắng hợp lệ hay không.

        (row, col) có thể nằm ở BẤT KỲ vị trí nào trong chuỗi (đầu, giữa hay cuối):
        hàm tự lùi về quân đầu tiên rồi đếm toàn bộ chuỗi cực đại, nên kết quả
        không phụ thuộc vào ô được truyền vào.

        - dr, dc: (0,1) Ngang, (1,0) Dọc, (1,1) Chéo chính, (1,-1) Chéo phụ.
        - Trả True khi độ dài >= win_length và KHÔNG bị chặn cả hai đầu.
        """
        player = int(player)
        if player == Player.EMPTY:
            return False
        if not RuleEngine._is_valid_coord(row, col, board_size) or board[row][col] != player:
            return False

        # 1. Lùi về quân đầu tiên của chuỗi.
        sr, sc = row, col
        while (
            RuleEngine._is_valid_coord(sr - dr, sc - dc, board_size)
            and board[sr - dr][sc - dc] == player
        ):
            sr -= dr
            sc -= dc

        # 2. Đếm toàn bộ chuỗi cực đại từ quân đầu tiên.
        count = 0
        r, c = sr, sc
        while RuleEngine._is_valid_coord(r, c, board_size) and board[r][c] == player:
            count += 1
            r += dr
            c += dc

        if count < win_length:
            return False

        # 3. Kiểm tra hai đầu: ô ngay trước quân đầu (sr-dr, sc-dc) và ô ngay sau quân cuối (r, c).
        h1r, h1c = sr - dr, sc - dc
        blocked_head1 = (
            not RuleEngine._is_valid_coord(h1r, h1c, board_size)
            or board[h1r][h1c] == -player
        )
        blocked_head2 = (
            not RuleEngine._is_valid_coord(r, c, board_size)
            or board[r][c] == -player
        )

        # Chỉ không thắng khi bị chặn cả hai đầu (quân địch hoặc biên).
        return not (blocked_head1 and blocked_head2)

    @staticmethod
    def check_winner(board: List[List[int]], config: GameConfig = GameConfig()) -> Optional[Player]:
        """
        Quét toàn bộ bàn cờ, trả về người thắng hoặc None.
        Mỗi chuỗi cực đại chỉ được đánh giá ĐỘC LẬP (hai chuỗi rời nhau không cộng dồn).
            Player.X: X thắng | Player.O: O thắng | None: chưa có người thắng
        """
        size = config.board_size
        win_len = config.win_length

        for r in range(size):
            for c in range(size):
                player = board[r][c]
                if player == Player.EMPTY:
                    continue

                for dr, dc in DIRECTIONS:
                    # Chỉ xét tại quân đầu chuỗi (ô phía trước không cùng màu) để tránh quét lặp.
                    pr, pc = r - dr, c - dc
                    if RuleEngine._is_valid_coord(pr, pc, size) and board[pr][pc] == player:
                        continue

                    if RuleEngine.check_line(board, r, c, dr, dc, player, size, win_len):
                        return Player(player)

        return None

    @staticmethod
    def check_winner_from_action(
        board: List[List[int]],
        last_action: Tuple[int, int],
        config: GameConfig = GameConfig(),
    ) -> Optional[Player]:
        """
        Điều kiện đúng đắn: trước nước đi này ván chưa có người thắng (luôn đúng vì
        ván dừng ngay khi có người thắng). Khi đó chỉ chuỗi chứa quân vừa đặt mới có
        thể trở thành chuỗi thắng mới. Hàm bổ sung, không thay đổi public interface.
        """
        row, col = last_action
        size = config.board_size
        if not RuleEngine._is_valid_coord(row, col, size):
            return None

        player = board[row][col]
        if player == Player.EMPTY:
            return None

        for dr, dc in DIRECTIONS:
            if RuleEngine.check_line(board, row, col, dr, dc, player, size, config.win_length):
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
        Trả về (done, winner):
            (True, Player.X) / (True, Player.O): có người thắng
            (True, None): hòa (bàn đầy, không ai thắng)
            (False, None): chưa kết thúc
        Thắng được xét TRƯỚC hòa.
        """
        winner = RuleEngine.check_winner(board, config)
        if winner is not None:
            return True, winner

        if RuleEngine.is_board_full(board, config.board_size):
            return True, None

        return False, None