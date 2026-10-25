# File: tests/helpers_contract.py
"""Helper dùng chung cho contract test ``caro-v2`` (chỉ dùng trong tests/).

* ``check_state_invariants``: kiểm tra invariant của ``GameState`` (mục 4.2).
* ``check_record_invariants``: kiểm tra invariant của ``GameRecord`` (mục 8.1).
* ``record_to_json`` / ``record_from_json``: bộ mã hóa JSON dùng cho test
  C2-DATA theo mục 8.2. Khi data pipeline thật có serializer riêng, test này
  nên chuyển sang dùng serializer đó.
"""
from __future__ import annotations

from core.engine.interfaces import (
    CONTRACT_VERSION,
    Action,
    GameConfig,
    GameRecord,
    GameState,
    MoveRecord,
    Player,
    action_to_json,
    player_to_json,
)


def check_state_invariants(state: GameState, config: GameConfig | None = None) -> None:
    """Assert mọi invariant bắt buộc của ``GameState``. Ném ``AssertionError``."""
    config = config or GameConfig()
    n = config.board_size

    # Hình dạng và miền giá trị của board
    assert len(state.board) == n, "board must have board_size rows"
    for row in state.board:
        assert len(row) == n, "every row must have board_size cells"
        for cell in row:
            assert not isinstance(cell, bool), "cell must not be bool"
            assert cell in (-1, 0, 1), f"invalid cell value: {cell!r}"

    stones = sum(1 for row in state.board for cell in row if cell != 0)
    x_count = sum(1 for row in state.board for cell in row if cell == Player.X)
    o_count = sum(1 for row in state.board for cell in row if cell == Player.O)

    # move_count / lượt / số quân
    assert state.move_count == stones, "move_count must equal number of stones"
    assert x_count == (state.move_count + 1) // 2, "X stone count inconsistent"
    assert o_count == state.move_count // 2, "O stone count inconsistent"
    expected_player = Player.X if state.move_count % 2 == 0 else Player.O
    assert state.current_player == expected_player, "wrong current_player"

    # last_action
    assert (state.last_action is None) == (state.move_count == 0), (
        "last_action is None iff move_count == 0"
    )
    if state.last_action is not None:
        row, col = state.last_action
        assert isinstance(state.last_action, tuple) and len(state.last_action) == 2
        assert 0 <= row < n and 0 <= col < n, "last_action out of bounds"
        # Người vừa đi là đối thủ của current_player (lượt luôn đã đổi).
        assert state.board[row][col] == -state.current_player, (
            "last_action must hold the stone of the player who just moved"
        )

    # terminated / winner
    assert state.winner in (Player.X, Player.O, None), "winner must be X, O or None"
    assert state.winner is not Player.EMPTY
    if not state.terminated:
        assert state.winner is None, "non-terminal state must have winner=None"
    elif state.winner is not None:
        assert state.winner == -state.current_player, "only the last mover can win"


def check_record_invariants(record: GameRecord, *, complete: bool = True) -> None:
    """Assert invariant của ``GameRecord`` (contract mục 8.1)."""
    assert record.contract_version == CONTRACT_VERSION
    seen: set[Action] = set()
    for index, move in enumerate(record.moves):
        assert move.ply == index + 1, "ply must be continuous from 1"
        expected = Player.X if index % 2 == 0 else Player.O
        assert move.player == expected, "players must alternate, X first"
        assert move.action not in seen, "actions must be unique"
        seen.add(move.action)
    assert record.winner in (Player.X, Player.O, None)
    if complete:
        assert record.terminated is True, "complete record must be terminated"


def record_to_json(record: GameRecord) -> dict:
    """GameRecord -> dict chỉ gồm kiểu JSON (action là [row, col])."""
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
        "moves": [
            {
                "ply": m.ply,
                "player": player_to_json(m.player),
                "action": action_to_json(m.action),
                "reward": m.reward,
                "elapsed_ms": m.elapsed_ms,
                "nodes": m.nodes,
                "simulations": m.simulations,
            }
            for m in record.moves
        ],
        "terminated": record.terminated,
        "winner": player_to_json(record.winner),
    }


def record_from_json(data: dict) -> GameRecord:
    """dict -> GameRecord; từ chối version khác thay vì đoán schema."""
    if data.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(f"unsupported contract_version: {data.get('contract_version')!r}")
    winner = data["winner"]
    return GameRecord(
        contract_version=data["contract_version"],
        game_id=data["game_id"],
        config=GameConfig(**data["config"]),
        seed=data["seed"],
        x_agent=data["x_agent"],
        o_agent=data["o_agent"],
        moves=[
            MoveRecord(
                ply=m["ply"],
                player=Player(m["player"]),
                action=(m["action"][0], m["action"][1]),
                reward=m["reward"],
                elapsed_ms=m["elapsed_ms"],
                nodes=m["nodes"],
                simulations=m["simulations"],
            )
            for m in data["moves"]
        ],
        terminated=data["terminated"],
        winner=None if winner is None else Player(winner),
    )
