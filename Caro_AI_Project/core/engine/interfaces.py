# File: core/engine/interfaces.py
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import IntEnum

class Player(IntEnum):
    X = 1       # Người chơi đi trước
    O = -1      # Người chơi đi sau
    EMPTY = 0   # Ô trống

class InvalidActionError(Exception):
    """Exception ném ra khi người chơi thực hiện nước đi không hợp lệ."""
    pass

@dataclass
class GameConfig:
    board_size: int = 11  # Kích thước mặc định 11x11
    win_length: int = 5  # Số quân liên tiếp để thắng

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