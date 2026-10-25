# File: core/engine/game_env.py
from typing import List, Tuple
import copy
from core.engine.rules import RuleEngine
from core.engine.interfaces import GameConfig, GameState, Player, StepResult, InvalidActionError

class CaroEnv:
    def __init__(self, config: GameConfig = GameConfig()):
        self.config = config
        self.state = self.reset()

    def reset(self) -> GameState:
        """Khởi tạo lại bàn cờ trống."""
        board = [[Player.EMPTY for _ in range(self.config.board_size)] for _ in range(self.config.board_size)]
        self.state = GameState(board=board, current_player=Player.X)
        return self.clone_state()

    def legal_actions(self) -> List[Tuple[int, int]]:
        """Trả về danh sách tọa độ (row, col) các ô còn trống."""
        actions = []
        for r in range(self.config.board_size):
            for c in range(self.config.board_size):
                if self.state.board[r][c] == Player.EMPTY:
                    actions.append((r, c))
        return actions

    def step(self, action: Tuple[int, int]) -> StepResult:
        """Thực hiện một nước đi. Ném lỗi nếu không hợp lệ."""
        r, c = action
        
        # 1. Kiểm tra ngoài biên
        if r < 0 or r >= self.config.board_size or c < 0 or c >= self.config.board_size:
            raise InvalidActionError(f"Action {action} is out of bounds.")
            
        # 2. Kiểm tra ô đã đánh
        if self.state.board[r][c] != Player.EMPTY:
            raise InvalidActionError(f"Cell {action} is already occupied.")

        # Thực hiện nước đi (State thay đổi ở đây)
        self.state.board[r][c] = self.state.current_player
        
        # Đảo lượt
        self.state.current_player = Player.O if self.state.current_player == Player.X else Player.X

        # TODO: Khi M2 xong PR luật thắng (chặn 2 đầu), sẽ gọi check_winner của M2 tại đây.
        # Tạm thời mock chưa ai thắng để pass test tuần 1.
        # is_done = len(self.legal_actions()) == 0
        
        # return StepResult(
        #     next_state=self.clone_state(),
        #     reward=0.0, 
        #     done=is_done,
        #     winner=None
        # )

        done, winner = RuleEngine.is_terminal(self.state.board, self.config)

        # Người vừa thực hiện nước đi (người vừa đi xong)
        last_player = Player.O if self.state.current_player == Player.X else Player.X

        # Tính reward theo góc nhìn người vừa đi
        if done:
            if winner == last_player:
                reward = 1.0
            elif winner is not None:
                reward = -1.0
            else:
                reward = 0.0  # Hòa
        else:
            reward = 0.0

        return StepResult(
            next_state=self.clone_state(),
            reward=reward,
            done=done,
            winner=winner
        )

    def is_terminal(self) -> bool:
        # return len(self.legal_actions()) == 0 # Mock
        done, _ = RuleEngine.is_terminal(self.state.board, self.config)
        return done

    def result(self) -> StepResult:
        pass # Mock cho M2 điền logic

    def clone_state(self) -> GameState:
        """Trả về bản sao độc lập của state hiện tại."""
        return GameState(
            board=copy.deepcopy(self.state.board),
            current_player=self.state.current_player
        )
        
    def clone_env(self): # Không bắt buộc type hint nhưng nên có
        """Tạo ra một env hoàn toàn mới để AI (như MCTS) chạy simulation."""
        new_env = CaroEnv(self.config)
        new_env.state = self.clone_state()
        return new_env

    def render(self):
        """In bàn cờ ra terminal (hỗ trợ debug)."""
        symbols = {Player.X: 'X', Player.O: 'O', Player.EMPTY: '.'}
        for row in self.state.board:
            print(" ".join(symbols[cell] for cell in row))
        print(f"Current Player: {self.state.current_player.name}")