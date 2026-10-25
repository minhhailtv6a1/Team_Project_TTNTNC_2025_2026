# File: core/engine/interfaces.py
"""Public interface của Caro AI theo contract ``caro-v2``.

Tài liệu tham chiếu: ``docs_contracts_caro_v2.md``.
Mọi thay đổi public ở file này phải đi qua quy trình ở mục 12 của contract
(M1 duyệt UI/API, M2 duyệt luật/engine, M3 duyệt test/data/integration).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Protocol, TypeAlias, runtime_checkable

CONTRACT_VERSION = "caro-v2"

# Cấu hình kích thước bàn cờ tập trung cho toàn dự án. Hiện tại chỉ 11x11
# module được phát triển và kiểm thử chính thức. Khi cần mở rộng, thêm kích
# thước mới vào SUPPORTED_BOARD_SIZES thay vì rải literal ở engine/UI/agents,
# sau đó chạy lại toàn bộ contract test.
DEFAULT_BOARD_SIZE = 11
SUPPORTED_BOARD_SIZES = (DEFAULT_BOARD_SIZE,)
# 9x9 được chủ động tạm ngưng; có thể thêm lại ở đây trong một phiên bản sau.
DEFAULT_WIN_LENGTH = 5

# Public action luôn là (row, col), gốc ở góc trên trái, đánh số từ 0.
Action: TypeAlias = tuple[int, int]
# Defensive snapshot: consumer xem là read-only.
BoardMatrix: TypeAlias = list[list[int]]


class Player(IntEnum):
    """Mã ô / người chơi: ``X=1``, ``O=-1``, ``EMPTY=0``."""
    X = 1       # Người chơi đi trước
    O = -1      # Người chơi đi sau
    EMPTY = 0   # Ô trống


# ---------------------------------------------------------------------------
# Action <-> index (index phẳng chỉ dùng nội bộ / policy của neural agent)
# ---------------------------------------------------------------------------
def action_to_index(action: Action, board_size: int) -> int:
    """Đổi ``(row, col)`` sang index row-major. Không dùng ở public boundary."""
    row, col = action
    return row * board_size + col


def index_to_action(index: int, board_size: int) -> Action:
    """Đổi index row-major về ``(row, col)``."""
    return divmod(index, board_size)


def legal_action_mask(
    legal_actions: list[Action],
    board_size: int,
) -> list[bool]:
    """Mask độ dài ``board_size ** 2``; ``True`` tại ô hợp lệ."""
    mask = [False] * (board_size * board_size)
    for action in legal_actions:
        mask[action_to_index(action, board_size)] = True
    return mask


# ---------------------------------------------------------------------------
# Lỗi public
# ---------------------------------------------------------------------------
class InvalidConfigError(ValueError):
    """Cấu hình không thuộc miền được caro-v2 hỗ trợ."""


class InvalidActionReason(str, Enum):
    """Mã lý do chuẩn hóa cho ``InvalidActionError``."""

    MALFORMED = "malformed"
    OUT_OF_BOUNDS = "out_of_bounds"
    OCCUPIED = "occupied"
    GAME_OVER = "game_over"


class InvalidActionError(ValueError):
    """Nước đi không hợp lệ. Khi ném lỗi này, state và history phải giữ nguyên."""

    def __init__(
        self,
        reason: InvalidActionReason,
        action: object,
        message: str,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.action = action


class UndoError(RuntimeError):
    """Không thể undo vì history của environment đang rỗng."""

# ---------------------------------------------------------------------------
# Thực thể public
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class GameConfig:
    """Cấu hình bất biến của ván đấu (có thể chia sẻ giữa env và clone)."""

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


@dataclass(frozen=True, slots=True)
class GameState:
    """Snapshot trạng thái ván đấu.

    ``frozen=True`` không đóng băng list lồng nhau, nên engine phải deep-copy
    ``board`` trước khi trả state; consumer không được sửa ``board``.

    Invariant (xem contract mục 4.2):
      * ``move_count`` bằng số ô khác ``EMPTY``.
      * ``last_action is None`` khi và chỉ khi ``move_count == 0``.
      * ``current_player`` là X khi ``move_count`` chẵn, O khi lẻ (kể cả khi
        state vừa terminal).
      * ``terminated=False`` kéo theo ``winner=None``;
        ``terminated=True, winner=None`` là hòa.
      * ``winner`` chỉ là ``Player.X``, ``Player.O`` hoặc ``None``.
    """

    board: BoardMatrix
    current_player: Player
    last_action: Action | None = None
    move_count: int = 0
    terminated: bool = False
    winner: Player | None = None


@dataclass(frozen=True, slots=True)
class StepResult:
    """Kết quả một ``step()`` hợp lệ.

    Invariant: ``done == next_state.terminated`` và
    ``winner == next_state.winner``.

    ``reward`` theo góc nhìn người vừa đi: chưa kết thúc ``0.0``, hòa ``0.0``,
    người vừa đi thắng ``1.0``. ``-1.0`` dành cho adapter/môi trường mở rộng;
    ``CaroEnv`` chuẩn không tạo ra giá trị này.
    """

    next_state: GameState
    reward: float
    done: bool
    winner: Player | None = None


# ---------------------------------------------------------------------------
# GameEnv protocol
# ---------------------------------------------------------------------------
@runtime_checkable
class GameEnv(Protocol):
    """Interface chuẩn của môi trường; ``CaroEnv`` và mock cùng phải thỏa.

    UI/agent chỉ type-hint theo ``GameEnv``, không phụ thuộc ``Board``,
    ``_history`` hay hàm private của ``RuleEngine``.
    """

    @property
    def config(self) -> GameConfig: ...

    @property
    def state(self) -> GameState:
        """Defensive snapshot của state hiện tại."""
        ...

    def reset(self, seed: int | None = None) -> GameState:
        """Board rỗng, X đi trước, xóa metadata terminal và history undo."""
        ...

    def legal_actions(self) -> list[Action]:
        """Ô trống theo thứ tự row-major; ``[]`` khi terminal. Trả list mới."""
        ...

    def step(self, action: Action) -> StepResult:
        """Thực hiện một nước đi nguyên tử.

        Raises:
            InvalidActionError: theo thứ tự GAME_OVER, MALFORMED,
                OUT_OF_BOUNDS, OCCUPIED. State và history giữ nguyên.
        """
        ...

    def is_terminal(self) -> bool:
        """Tương đương ``state.terminated``; không side effect."""
        ...

    def result(self, player: Player) -> float | None:
        """``None`` nếu chưa xong, ``0.0`` hòa, ``1.0`` player thắng,
        ``-1.0`` đối thủ thắng.

        Raises:
            ValueError: ``player`` không phải ``Player.X`` / ``Player.O``.
        """
        ...

    def clone_env(self) -> GameEnv:
        """Bản sao độc lập (board, metadata, history) cho Minimax/MCTS."""
        ...

    def undo(self) -> GameState:
        """Hoàn tác đúng một ``step()`` thành công gần nhất.

        Raises:
            UndoError: history rỗng; state giữ nguyên.
        """
        ...

    def render(self) -> str:
        """Biểu diễn text của board và lượt hiện tại; không mutation."""
        ...


# ---------------------------------------------------------------------------
# Agent contract
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class SearchBudget:
    """Giới hạn tìm kiếm. Field không áp dụng với agent được để ``None``."""

    time_limit_ms: int | None = None
    max_depth: int | None = None
    max_nodes: int | None = None
    simulations: int | None = None
    seed: int | None = None

    def __post_init__(self) -> None:
        for name in ("time_limit_ms", "seed"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ValueError(f"{name} must be a non-negative integer or None")
        for name in ("max_depth", "max_nodes", "simulations"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value <= 0
            ):
                raise ValueError(f"{name} must be a positive integer or None")


@dataclass(frozen=True, slots=True)
class AgentDecision:
    """Quyết định của agent; ``action`` phải thuộc ``env.legal_actions()``."""

    action: Action
    score: float | None = None
    nodes: int = 0
    simulations: int = 0
    elapsed_ms: float = 0.0


@runtime_checkable
class Agent(Protocol):
    """Interface chung cho Random, Heuristic, Minimax, MCTS và Neural.

    ``choose_action`` ném ``RuntimeError`` nếu env đã terminal hoặc không còn
    legal action, không được mutation ``env`` (dùng ``clone_env()``), và phải
    tái lập được với cùng state, config, budget và seed.
    """

    @property
    def name(self) -> str: ...

    def choose_action(
        self,
        env: GameEnv,
        budget: SearchBudget | None = None,
    ) -> AgentDecision: ...


# ---------------------------------------------------------------------------
# Dữ liệu self-play / tournament
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class MoveRecord:
    """Một nước đi trong ván; ``ply`` bắt đầu từ 1."""

    ply: int
    player: Player
    action: Action
    reward: float
    elapsed_ms: float = 0.0
    nodes: int = 0
    simulations: int = 0


@dataclass(frozen=True, slots=True)
class GameRecord:
    """Bản ghi một ván. Record hoàn chỉnh phải có ``terminated=True``;
    ``winner=None`` khi hoàn chỉnh nghĩa là hòa.

    ``contract_version`` bắt buộc là ``"caro-v2"`` để data pipeline từ chối
    dữ liệu khác version.
    """

    contract_version: str
    game_id: str
    config: GameConfig
    seed: int | None
    x_agent: str
    o_agent: str
    moves: list[MoveRecord] = field(default_factory=list)
    terminated: bool = False
    winner: Player | None = None


# ---------------------------------------------------------------------------
# JSON encoding (UTF-8; action là [row, col], không dùng index phẳng)
# ---------------------------------------------------------------------------
def action_to_json(action: Action) -> list[int]:
    """``(row, col)`` -> ``[row, col]``."""
    return [action[0], action[1]]


def player_to_json(player: Player | None) -> int | None:
    """``Player`` -> ``1`` / ``-1`` / ``0``; ``None`` -> ``null``."""
    return None if player is None else int(player)


__all__ = [
    "CONTRACT_VERSION",
    "DEFAULT_BOARD_SIZE",
    "SUPPORTED_BOARD_SIZES",
    "DEFAULT_WIN_LENGTH",
    "Action",
    "BoardMatrix",
    "Player",
    "action_to_index",
    "index_to_action",
    "legal_action_mask",
    "InvalidConfigError",
    "InvalidActionReason",
    "InvalidActionError",
    "UndoError",
    "GameConfig",
    "GameState",
    "StepResult",
    "GameEnv",
    "SearchBudget",
    "AgentDecision",
    "Agent",
    "MoveRecord",
    "GameRecord",
    "action_to_json",
    "player_to_json",
]