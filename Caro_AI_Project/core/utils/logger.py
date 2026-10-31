"""Logger JSONL cho ``GameRecord`` / ``MoveRecord`` theo contract ``caro-v2``.

Quy ước (contract mục 8):
- Mỗi dòng của file ``.jsonl`` là một ``GameRecord`` hoàn chỉnh.
- Action được lưu dạng ``[row, col]``; player là ``1`` hoặc ``-1``;
  winner là ``1``, ``-1`` hoặc ``null``.
- File luôn được ghi bằng UTF-8.
- ``contract_version`` phải là ``"caro-v2"``; dữ liệu khác version bị từ chối
  thay vì đoán schema.

Chỉ runner được tạo record và gọi logger; agent không tự ghi log.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
import threading
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from types import TracebackType
from typing import IO, Any

from core.engine.interfaces import (
    CONTRACT_VERSION,
    Action,
    GameConfig,
    GameRecord,
    MoveRecord,
    Player,
    action_to_json,
    player_to_json,
)

__all__ = [
    "GameLogger",
    "LogFormatError",
    "action_from_json",
    "game_from_dict",
    "game_to_dict",
    "load_games",
    "move_from_dict",
    "move_to_dict",
    "player_from_json",
        "read_games",
    "validate_game_record",
    "write_manifest",
]

ENCODING = "utf-8"


class LogFormatError(ValueError):
    """Record hoặc dòng log không đúng schema ``caro-v2``."""


# ---------------------------------------------------------------------------
# Kiểm tra kiểu nguyên thủy
# ---------------------------------------------------------------------------

def _is_int(value: object) -> bool:
    # bool là subclass của int nhưng contract không xem là số nguyên hợp lệ.
    return isinstance(value, int) and not isinstance(value, bool)


def _require_int(value: object, name: str) -> int:
    if not _is_int(value):
        raise LogFormatError(f"{name} must be an integer, got {value!r}")
    return value  # type: ignore[return-value]


def _require_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise LogFormatError(f"{name} must be a number, got {value!r}")
    number = float(value)
    if not math.isfinite(number):
        raise LogFormatError(f"{name} must be finite, got {value!r}")
    return number


def _require_str(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise LogFormatError(f"{name} must be a string, got {value!r}")
    return value


def _require_mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LogFormatError(f"{name} must be an object, got {type(value).__name__}")
    return value


def _get(data: Mapping[str, Any], key: str, ctx: str) -> Any:
    try:
        return data[key]
    except KeyError:
        raise LogFormatError(f"{ctx}: missing field {key!r}") from None


# ---------------------------------------------------------------------------
# Mapping JSON <-> kiểu public (contract mục 8.2)
# ---------------------------------------------------------------------------


def _encode_action(action: Action) -> list[int]:
    """Kiểm tra action rồi dùng ``action_to_json`` của interfaces để encode.

    Mapping JSON nằm ở một nguồn duy nhất là ``core.engine.interfaces``;
    logger chỉ thêm bước validate để không ghi action sai kiểu ra file.
    """
    if not isinstance(action, tuple) or len(action) != 2:
        raise LogFormatError(f"action must be a (row, col) tuple, got {action!r}")
    _require_int(action[0], "action.row")
    _require_int(action[1], "action.col")
    return action_to_json(action)


def action_from_json(value: object) -> Action:
    """``[row, col]`` -> ``(row, col)``; không chấp nhận index phẳng."""
    if not isinstance(value, list) or len(value) != 2:
        raise LogFormatError(f"action must be [row, col], got {value!r}")
    return (_require_int(value[0], "action.row"), _require_int(value[1], "action.col"))


def player_from_json(value: object, *, allow_none: bool = False) -> Player | None:
    """Đọc player; ``0`` (EMPTY) không bao giờ hợp lệ trong record."""
    if value is None:
        if allow_none:
            return None
        raise LogFormatError("player must not be null")
    number = _require_int(value, "player")
    if number == int(Player.X):
        return Player.X
    if number == int(Player.O):
        return Player.O
    raise LogFormatError(f"player must be 1 or -1, got {value!r}")


# ---------------------------------------------------------------------------
# Validation invariant của GameRecord (contract mục 8.1)
# ---------------------------------------------------------------------------


def validate_game_record(record: GameRecord, *, require_complete: bool = True) -> None:
    """Kiểm tra invariant của record; phát sinh ``LogFormatError`` nếu sai."""
    if record.contract_version != CONTRACT_VERSION:
        raise LogFormatError(
            f"contract_version must be {CONTRACT_VERSION!r}, "
            f"got {record.contract_version!r}"
        )
    if not isinstance(record.game_id, str) or not record.game_id:
        raise LogFormatError("game_id must be a non-empty string")
    if record.seed is not None:
        _require_int(record.seed, "seed")
    if record.winner is not None and record.winner not in (Player.X, Player.O):
        raise LogFormatError(f"winner must be X, O or None, got {record.winner!r}")
    if record.winner is not None and not record.terminated:
        raise LogFormatError("winner is set but terminated is False")
    if require_complete and not record.terminated:
        raise LogFormatError("a complete record must have terminated=True")

    board_size = record.config.board_size
    seen: set[Action] = set()
    for index, move in enumerate(record.moves):
        expected_ply = index + 1
        if move.ply != expected_ply:
            raise LogFormatError(
                f"move #{index}: ply must be {expected_ply}, got {move.ply}"
            )
        expected_player = Player.X if index % 2 == 0 else Player.O
        if move.player != expected_player:
            raise LogFormatError(
                f"ply {move.ply}: expected player {int(expected_player)}, "
                f"got {int(move.player)}"
            )
        row, col = move.action
        if not (0 <= row < board_size and 0 <= col < board_size):
            raise LogFormatError(
                f"ply {move.ply}: action {move.action!r} is out of bounds"
            )
        if move.action in seen:
            raise LogFormatError(f"ply {move.ply}: duplicate action {move.action!r}")
        seen.add(move.action)
        if move.elapsed_ms < 0 or move.nodes < 0 or move.simulations < 0:
            raise LogFormatError(f"ply {move.ply}: metrics must not be negative")


# ---------------------------------------------------------------------------
# Serialize / deserialize
# ---------------------------------------------------------------------------


def move_to_dict(move: MoveRecord) -> dict[str, Any]:
    return {
        "ply": move.ply,
        "player": player_to_json(move.player),
        "action": _encode_action(move.action),
        "reward": float(move.reward),
        "elapsed_ms": float(move.elapsed_ms),
        "nodes": int(move.nodes),
        "simulations": int(move.simulations),
    }


def move_from_dict(data: object, *, ctx: str = "move") -> MoveRecord:
    obj = _require_mapping(data, ctx)
    player = player_from_json(_get(obj, "player", ctx))
    assert player is not None
    return MoveRecord(
        ply=_require_int(_get(obj, "ply", ctx), f"{ctx}.ply"),
        player=player,
        action=action_from_json(_get(obj, "action", ctx)),
        reward=_require_number(_get(obj, "reward", ctx), f"{ctx}.reward"),
        elapsed_ms=_require_number(obj.get("elapsed_ms", 0.0), f"{ctx}.elapsed_ms"),
        nodes=_require_int(obj.get("nodes", 0), f"{ctx}.nodes"),
        simulations=_require_int(obj.get("simulations", 0), f"{ctx}.simulations"),
    )


def game_to_dict(record: GameRecord, *, validate: bool = True) -> dict[str, Any]:
    if validate:
        validate_game_record(record)
    return {
        "contract_version": record.contract_version,
        "game_id": record.game_id,
        "config": {
            "board_size": record.config.board_size,
            "win_length": record.config.win_length,
        },
        "seed": record.seed,
        "x_agent": record.x_agent,
        "o_agent": record.o_agent,
        "moves": [move_to_dict(m) for m in record.moves],
        "terminated": record.terminated,
        "winner": player_to_json(record.winner),
    }


def game_from_dict(data: object, *, validate: bool = True) -> GameRecord:
    obj = _require_mapping(data, "game")

    version = _get(obj, "contract_version", "game")
    if version != CONTRACT_VERSION:
        raise LogFormatError(
            f"unsupported contract_version {version!r}; expected {CONTRACT_VERSION!r}"
        )

    config_obj = _require_mapping(_get(obj, "config", "game"), "game.config")
    try:
        config = GameConfig(
            board_size=_require_int(_get(config_obj, "board_size", "config"), "board_size"),
            win_length=_require_int(_get(config_obj, "win_length", "config"), "win_length"),
        )
    except ValueError as exc:  # gồm InvalidConfigError
        if isinstance(exc, LogFormatError):
            raise
        raise LogFormatError(f"invalid config: {exc}") from exc

    raw_moves = _get(obj, "moves", "game")
    if not isinstance(raw_moves, list):
        raise LogFormatError("game.moves must be a list")
    moves = [
        move_from_dict(item, ctx=f"moves[{i}]") for i, item in enumerate(raw_moves)
    ]

    seed = obj.get("seed")
    if seed is not None:
        seed = _require_int(seed, "game.seed")

    terminated = _get(obj, "terminated", "game")
    if not isinstance(terminated, bool):
        raise LogFormatError(f"game.terminated must be a bool, got {terminated!r}")

    record = GameRecord(
        contract_version=version,
        game_id=_require_str(_get(obj, "game_id", "game"), "game.game_id"),
        config=config,
        seed=seed,
        x_agent=_require_str(_get(obj, "x_agent", "game"), "game.x_agent"),
        o_agent=_require_str(_get(obj, "o_agent", "game"), "game.o_agent"),
        moves=moves,
        terminated=terminated,
        winner=player_from_json(_get(obj, "winner", "game"), allow_none=True),
    )
    if validate:
        validate_game_record(record)
    return record


def _dumps(payload: Mapping[str, Any]) -> str:
    # ensure_ascii=False giữ nguyên Unicode; allow_nan=False chặn NaN/Infinity.
    return json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )


# ---------------------------------------------------------------------------
# Ghi / đọc JSONL
# ---------------------------------------------------------------------------


class GameLogger:
    """Ghi mỗi ``GameRecord`` thành một dòng JSONL.

    Mỗi game được serialize và validate *trước* khi ghi, rồi ghi bằng một lần
    ``write`` và ``flush`` ngay, nên một game lỗi không để lại dòng dở dang.
    Dùng được từ nhiều thread nhờ lock nội bộ.

    ``mode="a"`` (mặc định) nối thêm vào file; ``mode="w"`` ghi đè.
    ``fsync=True`` ép ghi xuống đĩa sau mỗi game (chậm hơn, an toàn hơn).
    """

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        mode: str = "a",
        fsync: bool = False,
        validate: bool = True,
    ) -> None:
        if mode not in ("a", "w"):
            raise ValueError("mode must be 'a' or 'w'")
        self._path = Path(path)
        self._fsync = fsync
        self._validate = validate
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._file: IO[str] | None = open(
            self._path, mode, encoding=ENCODING, newline="\n"
        )
        self._games_written = 0

    @property
    def path(self) -> Path:
        return self._path

    @property
    def games_written(self) -> int:
        return self._games_written

    def log_game(self, record: GameRecord) -> None:
        line = _dumps(game_to_dict(record, validate=self._validate)) + "\n"
        with self._lock:
            file = self._require_open()
            file.write(line)
            file.flush()
            if self._fsync:
                os.fsync(file.fileno())
            self._games_written += 1

    def log_games(self, records: Iterable[GameRecord]) -> None:
        for record in records:
            self.log_game(record)

    def close(self) -> None:
        with self._lock:
            if self._file is not None:
                self._file.close()
                self._file = None

    def __enter__(self) -> GameLogger:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def _require_open(self) -> IO[str]:
        if self._file is None:
            raise ValueError("logger is closed")
        return self._file


def read_games(
    path: str | os.PathLike[str], *, validate: bool = True
) -> Iterator[GameRecord]:
    """Đọc từng game từ file JSONL; lỗi kèm số dòng để dễ tìm."""
    with open(path, "r", encoding=ENCODING, newline=None) as file:
        for line_no, line in enumerate(file, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                yield game_from_dict(json.loads(text), validate=validate)
            except json.JSONDecodeError as exc:
                raise LogFormatError(f"{path}:{line_no}: invalid JSON ({exc})") from exc
            except LogFormatError as exc:
                raise LogFormatError(f"{path}:{line_no}: {exc}") from exc


def load_games(
    path: str | os.PathLike[str], *, validate: bool = True
) -> list[GameRecord]:
    return list(read_games(path, validate=validate))


def write_manifest(
    path: str | os.PathLike[str], manifest: Mapping[str, Any]
) -> Path:
    """Ghi manifest (config, seed, budget, hardware...) cạnh file log.

    Ghi vào file tạm rồi ``os.replace`` để file đích không bao giờ dở dang.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"contract_version": CONTRACT_VERSION, **manifest}
    fd, tmp_name = tempfile.mkstemp(
        dir=target.parent, prefix=target.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding=ENCODING, newline="\n") as tmp:
            json.dump(payload, tmp, ensure_ascii=False, indent=2, allow_nan=False)
            tmp.write("\n")
        os.replace(tmp_name, target)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    return target