# File: core/engine/interfaces.py
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import IntEnum


# Cấu hình kích thước bàn cờ tập trung cho toàn dự án. Hiện tại chỉ 11x11 là
# module được phát triển và kiểm thử chính thức. Khi cần mở rộng, thêm kích
# thước mới vào SUPPORTED_BOARD_SIZES thay vì rải literal ở engine/UI/agents.
DEFAULT_BOARD_SIZE = 11
SUPPORTED_BOARD_SIZES = (DEFAULT_BOARD_SIZE,)
# 9x9 được chủ động tạm ngưng; có thể thêm lại ở đây trong một phiên bản sau.
DEFAULT_WIN_LENGTH = 5

class Player(IntEnum):
    X = 1       # Người chơi đi trước
    O = -1      # Người chơi đi sau
    EMPTY = 0   # Ô trống

class InvalidActionError(Exception):
    """Exception ném ra khi người chơi thực hiện nước đi không hợp lệ."""
    pass


class InvalidConfigError(ValueError):
    """Cấu hình nằm ngoài phạm vi phiên bản Caro hiện tại."""


@dataclass
class GameConfig:
    board_size: int = DEFAULT_BOARD_SIZE
    win_length: int = DEFAULT_WIN_LENGTH

    def __post_init__(self) -> None:
        if (
            isinstance(self.board_size, bool)
            or not isinstance(self.board_size, int)
            or self.board_size not in SUPPORTED_BOARD_SIZES
        ):
            supported = ", ".join(map(str, SUPPORTED_BOARD_SIZES))
            raise InvalidConfigError(f"board_size must be one of: {supported}")
        if (
            isinstance(self.win_length, bool)
            or not isinstance(self.win_length, int)
            or self.win_length != DEFAULT_WIN_LENGTH
        ):
            raise InvalidConfigError(
                f"win_length must be {DEFAULT_WIN_LENGTH} for the current ruleset"
            )

@dataclass
class GameState:
    # Ma trận 2 chiều lưu trạng thái bàn cờ
    board: List[List[int]] 
    current_player: Player

@dataclass
class StepResult:
    next_state: GameState
    reward: float        # Góc nhìn của người vừa đi (ví dụ: 1.0 thắng, -1.0 thua, 0.0 hòa/chưa xong)
    done: bool           # True nếu game kết thúc
    winner: Optional[Player] = None # None nếu hòa hoặc chưa kết thúc
