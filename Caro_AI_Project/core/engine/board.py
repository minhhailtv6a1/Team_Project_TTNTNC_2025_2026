import numpy as np
from typing import Tuple, List, Optional


class Board:
    """
    Quản lý mảng bàn cờ Caro 11x11 và các thao tác chuyển đổi tọa độ, đặt quân cờ.
    """

    BOARD_SIZE = 11
    TOTAL_CELLS = 121
    EMPTY_VALUE = 0
    PLAYER_X = 1
    PLAYER_O = -1

    def __init__(self, size: int = BOARD_SIZE) -> None:
        """
        Khởi tạo bàn cờ rỗng kích thước size x size (mặc định 11x11).
        """
        self.size = size
        self.total_cells = size * size
        self.grid = np.zeros((self.size, self.size), dtype=np.int8)

    @staticmethod
    def action_to_coord(action: int, size: int = BOARD_SIZE) -> Tuple[int, int]:
        """
        Chuyển đổi action (0..120) sang tọa độ (row, col).
        """
        if not (0 <= action < size * size):
            raise ValueError(f"Action {action} nằm ngoài phạm vi 0..{size * size - 1}")
        return action // size, action % size

    @staticmethod
    def coord_to_action(row: int, col: int, size: int = BOARD_SIZE) -> int:
        """
        Chuyển đổi tọa độ (row, col) sang action (0..120).
        """
        if not (0 <= row < size and 0 <= col < size):
            raise ValueError(f"Tọa độ ({row}, {col}) nằm ngoài bàn cờ {size}x{size}")
        return row * size + col

    def is_valid_action(self, action: int) -> bool:
        """
        Kiểm tra action có hợp lệ hay không (trong biên và ô còn trống).
        """
        if not (0 <= action < self.total_cells):
            return False
        row, col = self.action_to_coord(action, self.size)
        return bool(self.grid[row, col] == self.EMPTY_VALUE)

    def is_valid_coord(self, row: int, col: int) -> bool:
        """
        Kiểm tra tọa độ (row, col) có nằm trong bàn cờ hay không.
        """
        return 0 <= row < self.size and 0 <= col < self.size

    def place_stone(self, action: int, player: int) -> bool:
        """
        Đặt quân cờ của player (1 hoặc -1) vào vị trí action.
        Trả về True nếu đặt thành công, False nếu không hợp lệ.
        """
        if not self.is_valid_action(action):
            return False
        
        row, col = self.action_to_coord(action, self.size)
        self.grid[row, col] = player
        return True

    def get_legal_actions(self) -> List[int]:
        """
        Trả về danh sách tất cả các action hợp lệ (ô còn trống).
        """
        legal_actions = []
        for action in range(self.total_cells):
            row, col = self.action_to_coord(action, self.size)
            if self.grid[row, col] == self.EMPTY_VALUE:
                legal_actions.append(action)
        return legal_actions

    def get_board_state(self) -> np.ndarray:
        """
        Trả về bản sao độc lập của mảng bàn cờ (tránh sửa trực tiếp state nội bộ).
        """
        return self.grid.copy()

    def reset(self) -> None:
        """
        Đặt lại toàn bộ bàn cờ về trạng thái rỗng.
        """
        self.grid.fill(self.EMPTY_VALUE)

    def copy(self) -> 'Board':
        """
        Tạo bản sao độc lập (deep clone) của đối tượng Board.
        """
        new_board = Board(size=self.size)
        new_board.grid = self.grid.copy()
        return new_board

    def is_full(self) -> bool:
        """
        Kiểm tra bàn cờ đã đầy chưa.
        """
        return bool(not np.any(self.grid == self.EMPTY_VALUE))