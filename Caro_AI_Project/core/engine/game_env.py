from __future__ import annotations

from numbers import Integral
from typing import List, Optional, Tuple

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
from core.engine.rules import RuleEngine


class CaroEnv:
    """
    Trạng thái nội bộ được giữ ở các field riêng (`_board`, `_current_player`, ...);
    mọi state trả ra ngoài (`state`, `reset`, `step`) đều là defensive snapshot,
    nên consumer không thể làm hỏng môi trường qua object đã nhận.
 
    Lựa chọn copy và độ phức tạp (n = board_size = 11, m = số nước đã đi):
      * History: 
            - Là stack các bản ghi nhỏ bất biến `(row, col, prev_last_action)`, không lưu cả board mỗi nước
            - Mọi thứ còn lại suy ra được khi undo():
                + current_player = quân đang nằm ở (row, col); 
                + Trước một step hợp lệ ván luôn chưa kết thúc (terminated=False, winner=None); 
                + move_count -= 1
      * Validation & History Safety:
            Action được validate hoàn tất trước khi mutate board và push history.
            Action lỗi hoặc action sau khi game over bị từ chối và tuyệt đối không đổi history.

      * `step()`: validate O(1) + kiểm tra thắng quanh nước vừa đi O(4n) + push history O(1).
      * `undo()`: O(1), không đụng tới phần còn lại của board.
      * `clone_env()`: O(n^2) copy board + O(m) copy list history (shallow, an toàn vì
        phần tử là tuple bất biến). Không dùng deepcopy => rẻ cho Minimax/MCTS.
      * `state` / `reset()` / `step()` / `undo()` trả snapshot: O(n^2) (copy từng hàng,
        nhanh hơn `copy.deepcopy` nhiều lần mà vẫn độc lập vì ô là int).
    """

    def __init__(self, config: GameConfig = GameConfig()):
        self._config = config
        self.reset()

    #  properties
    @property
    def config(self) -> GameConfig:
        return self._config

    @property
    def state(self) -> GameState:
        """Snapshot độc lập của state hiện tại."""
        return self._snapshot()

    #  lifecycle
    def reset(self, seed: Optional[int] = None) -> GameState:
        """
        Khởi tạo lại ván: bàn trống, X đi trước
        """
        size = self._config.board_size
        self._board: List[List[int]] = [[int(Player.EMPTY)] * size for _ in range(size)]
        self._current_player: Player = Player.X
        self._last_action: Optional[Action] = None
        self._move_count: int = 0
        self._terminated: bool = False
        self._winner: Optional[Player] = None
        # Xóa history cũ, nhưng vẫn giữ snapshot trước khi reset để AI có thể mô phỏng
        self._history: List[Tuple[int, int, Optional[Action]]] = []
        return self._snapshot()

    #  queries
    def legal_actions(self) -> List[Action]:
        if self._terminated:
            return []
        size = self._config.board_size
        empty = int(Player.EMPTY)
        actions = []
        for r in range(size):          
            for c in range(size):      
                if self._board[r][c] == empty:
                    actions.append((r, c))
        return actions

    def is_terminal(self) -> bool:
        return self._terminated

    def result(self, player: Player) -> Optional[float]:
        """
        None : ván chưa kết thúc
        0.0 : hòa
        1.0 : player thắng
        -1.0 : đối thủ của player thắng
        """
        if not isinstance(player, Player) or player == Player.EMPTY:
            raise ValueError(f"result() requires Player.X or Player.O, got {player!r}.")
        if not self._terminated:
            return None
        if self._winner is None:
            return 0.0
        return 1.0 if self._winner == player else -1.0

    #  transition
    def step(self, action: Action) -> StepResult:
        """
        Thực hiện một nước đi. Mọi validation hoàn tất TRƯỚC khi thay đổi state,
        nên nếu raise `InvalidActionError` thì state giữ nguyên hoàn toàn.
        """
        row, col = self._validate_action(action)

        acting_player = self._current_player
        size = self._config.board_size

        # --- từ đây trở đi không còn đường nào raise: cập nhật state nguyên tử ---
        self._history.append((row, col, self._last_action))
        self._board[row][col] = int(acting_player)
        self._last_action = (row, col)
        self._move_count += 1

        # Kiểm tra terminal đúng một lần: thắng trước, hòa sau.
        # Chỉ chuỗi đi qua nước vừa đặt mới có thể thắng (ván dừng ngay khi có người thắng).
        winner = RuleEngine.check_winner_from_action(self._board, (row, col), self._config)
        if winner is not None:
            self._terminated, self._winner = True, winner
        elif self._move_count == size * size:
            self._terminated, self._winner = True, None  # hòa: bàn đầy, chưa có winner

        # current_player luôn là người dự kiến đi tiếp, kể cả khi vừa terminal.
        self._current_player = Player.O if acting_player == Player.X else Player.X

        # Reward theo góc nhìn người vừa đi: thắng 1.0; hòa/chưa xong 0.0.
        reward = 1.0 if self._winner == acting_player else 0.0

        return StepResult(
            next_state=self._snapshot(),
            reward=reward,
            done=self._terminated,
            winner=self._winner,
        )

    #  clone / undo
    def clone_env(self) -> "CaroEnv":
        """
        Env mới, độc lập hoàn toàn (board, metadata, history) để AI mô phỏng.
        Step/undo/reset trên clone không ảnh hưởng env gốc và ngược lại.
        Clone giữ cả history nên có thể undo các nước đã đi trước khi clone.
        """
        new_env = CaroEnv.__new__(CaroEnv)  # bỏ qua __init__/reset để không tạo board + snapshot thừa
        new_env._config = self._config
        new_env._board = [row[:] for row in self._board]
        new_env._current_player = self._current_player
        new_env._last_action = self._last_action
        new_env._move_count = self._move_count
        new_env._terminated = self._terminated
        new_env._winner = self._winner
        new_env._history = self._history[:]  # phần tử là tuple bất biến => shallow copy là đủ
        return new_env

    def undo(self) -> GameState:
        """
        Hoàn tác đúng một `step()` thành công gần nhất; trả snapshot sau undo.

        Khôi phục board, current_player, last_action, move_count, terminated, winner.
        Được phép sau state thắng/hòa để mở lại ván. Raise `UndoError` (state giữ
        nguyên) khi history rỗng.
        """
        if not self._history:
            raise UndoError("Nothing to undo: move history is empty.")

        row, col, previous_last_action = self._history.pop()
        # Người vừa đi chính là chủ quân ở (row, col); sau undo họ lại là người đi tiếp.
        self._current_player = Player(self._board[row][col])
        self._board[row][col] = int(Player.EMPTY)
        self._move_count -= 1
        self._last_action = previous_last_action
        # Step chỉ được chấp nhận khi ván đang chạy => trước nước đó luôn chưa terminal.
        self._terminated = False
        self._winner = None
        return self._snapshot()

    #  render
    def render(self) -> str:
        """Biểu diễn text của board và lượt hiện tại; không mutation."""
        symbols = {int(Player.X): "X", int(Player.O): "O", int(Player.EMPTY): "."}
        lines = [" ".join(symbols[cell] for cell in row) for row in self._board]
        if self._terminated:
            outcome = "Draw" if self._winner is None else f"Winner: {self._winner.name}"
            lines.append(f"Game over. {outcome}")
        else:
            lines.append(f"Current Player: {self._current_player.name}")
        return "\n".join(lines)

    #  internals
    def _snapshot(self) -> GameState:
        return GameState(
            board=[row[:] for row in self._board],  # hàng chứa int bất biến => copy hàng là đủ độc lập
            current_player=self._current_player,
            last_action=self._last_action,
            move_count=self._move_count,
            terminated=self._terminated,
            winner=self._winner,
        )

    @staticmethod
    def _is_int(value: object) -> bool:
        return isinstance(value, Integral) and not isinstance(value, bool)

    def _validate_action(self, action: object) -> Action:
        """Thứ tự chuẩn: GAME_OVER -> MALFORMED -> OUT_OF_BOUNDS -> OCCUPIED."""
        if self._terminated:
            raise InvalidActionError(
                InvalidActionReason.GAME_OVER, action,
                f"Game is over; action {action!r} is not allowed.",
            )
        if not (isinstance(action, tuple) and len(action) == 2
                and self._is_int(action[0]) and self._is_int(action[1])):
            raise InvalidActionError(
                InvalidActionReason.MALFORMED, action,
                f"Action {action!r} must be a tuple (row, col) of two integers.",
            )
        row, col = int(action[0]), int(action[1])
        size = self._config.board_size
        if not (0 <= row < size and 0 <= col < size):
            raise InvalidActionError(
                InvalidActionReason.OUT_OF_BOUNDS, action,
                f"Action {action!r} is out of bounds for a {size}x{size} board.",
            )
        if self._board[row][col] != int(Player.EMPTY):
            raise InvalidActionError(
                InvalidActionReason.OCCUPIED, action,
                f"Cell {action!r} is already occupied.",
            )
        return row, col