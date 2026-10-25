# File: tests/test_interfaces_contract.py
"""Contract test cho ``core/engine/interfaces.py`` (caro-v2).

Phủ: C2-CONFIG, C2-STATE, C2-DATA và các quy ước nền (action/index, lỗi
public, SearchBudget, Protocol). Không phụ thuộc engine/UI.
"""
from __future__ import annotations

import dataclasses
import json

import pytest

from core.engine.interfaces import (
    CONTRACT_VERSION,
    DEFAULT_BOARD_SIZE,
    SUPPORTED_BOARD_SIZES,
    Agent,
    AgentDecision,
    GameConfig,
    GameEnv,
    GameRecord,
    GameState,
    InvalidActionError,
    InvalidActionReason,
    InvalidConfigError,
    MoveRecord,
    Player,
    SearchBudget,
    StepResult,
    UndoError,
    action_to_index,
    action_to_json,
    index_to_action,
    legal_action_mask,
    player_to_json,
)
from helpers.helpers_contract import (
    check_record_invariants,
    check_state_invariants,
    record_from_json,
    record_to_json,
)

N = DEFAULT_BOARD_SIZE


def empty_board() -> list[list[int]]:
    return [[0] * N for _ in range(N)]


def board_with(*stones: tuple[int, int, int]) -> list[list[int]]:
    board = empty_board()
    for row, col, value in stones:
        board[row][col] = value
    return board


# ---------------------------------------------------------------------------
# C2-CONFIG
# ---------------------------------------------------------------------------
class TestConfig:
    def test_contract_version(self):
        assert CONTRACT_VERSION == "caro-v2"

    def test_default_is_11x11_win5(self):
        config = GameConfig()
        assert (config.board_size, config.win_length) == (11, 5)
        assert SUPPORTED_BOARD_SIZES == (11,)

    @pytest.mark.parametrize("size", [9, 10, 12, 0, -11, True, False, 11.0, "11", None])
    def test_rejects_unsupported_board_size(self, size):
        with pytest.raises(InvalidConfigError):
            GameConfig(board_size=size)

    @pytest.mark.parametrize("length", [3, 4, 6, 0, -5, True, 5.0, "5", None])
    def test_rejects_unsupported_win_length(self, length):
        with pytest.raises(InvalidConfigError):
            GameConfig(win_length=length)

    def test_invalid_config_is_value_error(self):
        assert issubclass(InvalidConfigError, ValueError)

    def test_config_is_immutable_and_shareable(self):
        config = GameConfig()
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.board_size = 9  # type: ignore[misc]
        assert config == GameConfig()
        assert hash(config) == hash(GameConfig())


# ---------------------------------------------------------------------------
# C2-STATE
# ---------------------------------------------------------------------------
class TestState:
    def test_defaults_describe_initial_state(self):
        state = GameState(board=empty_board(), current_player=Player.X)
        assert state.last_action is None
        assert state.move_count == 0
        assert state.terminated is False
        assert state.winner is None
        check_state_invariants(state)

    def test_state_is_frozen(self):
        state = GameState(board=empty_board(), current_player=Player.X)
        with pytest.raises(dataclasses.FrozenInstanceError):
            state.move_count = 1  # type: ignore[misc]

    def test_equality_is_by_value(self):
        a = GameState(board=empty_board(), current_player=Player.X)
        b = GameState(board=empty_board(), current_player=Player.X)
        assert a == b
        assert a != GameState(board=empty_board(), current_player=Player.O)

    def test_player_values(self):
        assert (int(Player.X), int(Player.O), int(Player.EMPTY)) == (1, -1, 0)

    @pytest.mark.parametrize(
        "state",
        [
            # một nước: X đã đi, tới lượt O
            GameState(board_with((5, 5, 1)), Player.O, (5, 5), 1),
            # hai nước
            GameState(board_with((5, 5, 1), (5, 6, -1)), Player.X, (5, 6), 2),
            # X thắng: lượt vẫn đổi sang O, winner = X
            GameState(
                board_with(*[(0, c, 1) for c in range(5)], *[(1, c, -1) for c in range(4)]),
                Player.O, (0, 4), 9, True, Player.X,
            ),
            # O thắng: lượt đổi sang X, winner = O
            GameState(
                board_with(*[(0, c, 1) for c in range(4)], (9, 9, 1), *[(1, c, -1) for c in range(5)]),
                Player.X, (1, 4), 10, True, Player.O,
            ),
        ],
    )
    def test_valid_states_pass_invariants(self, state):
        check_state_invariants(state)

    def test_valid_draw_state_passes_invariants(self):
        # Bàn 11x11 đầy (121 quân): X 61, O 60, X đi nước cuối -> tới lượt O.
        board = [[1 if (r * N + c) % 2 == 0 else -1 for c in range(N)] for r in range(N)]
        state = GameState(board, Player.O, (10, 10), 121, True, None)
        check_state_invariants(state)

    @pytest.mark.parametrize(
        "bad_state, reason",
        [
            (GameState(board_with((0, 0, 1)), Player.O, (0, 0), 0), "move_count != stones"),
            (GameState(board_with((0, 0, 1)), Player.X, (0, 0), 1), "wrong player for odd move_count"),
            (GameState(empty_board(), Player.X, (0, 0), 0), "last_action with move_count 0"),
            (GameState(board_with((0, 0, 1)), Player.O, None, 1), "missing last_action"),
            (GameState(board_with((0, 0, 1)), Player.O, (3, 3), 1), "last_action on empty cell"),
            (GameState(board_with((0, 0, 1)), Player.O, (11, 0), 1), "last_action out of bounds"),
            (GameState(board_with((0, 0, 2)), Player.O, (0, 0), 1), "cell outside domain"),
            (GameState(board_with((0, 0, 1)), Player.O, (0, 0), 1, False, Player.X), "winner without terminated"),
            (GameState(board_with((0, 0, 1)), Player.O, (0, 0), 1, True, Player.EMPTY), "winner EMPTY"),
            (GameState(board_with((0, 0, 1)), Player.O, (0, 0), 1, True, Player.O), "loser flagged as winner"),
            (GameState(empty_board()[:-1], Player.X), "too few rows"),
            (GameState([row[:-1] for row in empty_board()], Player.X), "too few columns"),
            (GameState(board_with((0, 0, 1), (0, 1, 1)), Player.X, (0, 1), 2), "two X stones in a row"),
        ],
    )
    def test_helper_detects_invalid_states(self, bad_state, reason):
        with pytest.raises(AssertionError):
            check_state_invariants(bad_state)

    def test_helper_rejects_bool_cell(self):
        board = empty_board()
        board[0][0] = True
        with pytest.raises(AssertionError):
            check_state_invariants(GameState(board, Player.O, (0, 0), 1))


class TestStepResult:
    def test_is_frozen_with_default_winner(self):
        state = GameState(board=empty_board(), current_player=Player.X)
        result = StepResult(next_state=state, reward=0.0, done=False)
        assert result.winner is None
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.reward = 1.0  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Action <-> index và legal mask
# ---------------------------------------------------------------------------
class TestActionIndex:
    def test_round_trip_every_cell(self):
        for row in range(N):
            for col in range(N):
                index = action_to_index((row, col), N)
                assert index_to_action(index, N) == (row, col)

    def test_row_major_order(self):
        assert action_to_index((0, 0), N) == 0
        assert action_to_index((0, 10), N) == 10
        assert action_to_index((1, 0), N) == 11
        assert action_to_index((10, 10), N) == 120
        assert index_to_action(25, N) == (2, 3)

    def test_index_to_action_returns_tuple_of_ints(self):
        action = index_to_action(60, N)
        assert isinstance(action, tuple) and len(action) == 2
        assert all(isinstance(v, int) for v in action)

    def test_mask_marks_only_legal_actions(self):
        legal = [(0, 0), (5, 5), (10, 10)]
        mask = legal_action_mask(legal, N)
        assert len(mask) == N * N == 121
        assert [i for i, ok in enumerate(mask) if ok] == [0, 60, 120]

    def test_mask_empty_when_no_legal_actions(self):
        assert not any(legal_action_mask([], N))

    def test_mask_all_true_for_full_row_major_list(self):
        legal = [(r, c) for r in range(N) for c in range(N)]
        assert all(legal_action_mask(legal, N))


# ---------------------------------------------------------------------------
# Lỗi public
# ---------------------------------------------------------------------------
class TestErrors:
    def test_reason_values(self):
        assert {r.value for r in InvalidActionReason} == {
            "malformed", "out_of_bounds", "occupied", "game_over",
        }
        assert InvalidActionReason.OCCUPIED == "occupied"  # str subclass

    def test_invalid_action_error_carries_reason_and_action(self):
        error = InvalidActionError(InvalidActionReason.OUT_OF_BOUNDS, (11, 0), "bad cell")
        assert error.reason is InvalidActionReason.OUT_OF_BOUNDS
        assert error.action == (11, 0)
        assert str(error) == "bad cell"
        assert isinstance(error, ValueError)

    def test_action_may_be_any_object(self):
        error = InvalidActionError(InvalidActionReason.MALFORMED, "abc", "not a tuple")
        assert error.action == "abc"

    def test_undo_error_is_runtime_error(self):
        assert issubclass(UndoError, RuntimeError)
        assert not issubclass(UndoError, ValueError)


# ---------------------------------------------------------------------------
# SearchBudget / AgentDecision
# ---------------------------------------------------------------------------
class TestSearchBudget:
    def test_defaults_are_all_none(self):
        assert SearchBudget() == SearchBudget(None, None, None, None, None)

    def test_accepts_valid_values(self):
        SearchBudget(time_limit_ms=0, max_depth=1, max_nodes=1, simulations=1, seed=0)

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"time_limit_ms": -1},
            {"seed": -1},
            {"max_depth": 0},
            {"max_nodes": 0},
            {"simulations": 0},
            {"max_depth": -3},
            {"simulations": True},
            {"time_limit_ms": 1.5},
        ],
    )
    def test_rejects_invalid_values(self, kwargs):
        with pytest.raises(ValueError):
            SearchBudget(**kwargs)

    def test_decision_defaults(self):
        decision = AgentDecision(action=(5, 5))
        assert (decision.score, decision.nodes, decision.simulations, decision.elapsed_ms) == (
            None, 0, 0, 0.0,
        )


# ---------------------------------------------------------------------------
# Protocol (runtime_checkable)
# ---------------------------------------------------------------------------
class _FakeEnv:
    config = GameConfig()
    state = GameState(board=empty_board(), current_player=Player.X)

    def reset(self, seed=None): ...
    def legal_actions(self): ...
    def step(self, action): ...
    def is_terminal(self): ...
    def result(self, player): ...
    def clone_env(self): ...
    def undo(self): ...
    def render(self): ...


class _FakeEnvMissingUndo:
    config = GameConfig()
    state = GameState(board=empty_board(), current_player=Player.X)

    def reset(self, seed=None): ...
    def legal_actions(self): ...
    def step(self, action): ...
    def is_terminal(self): ...
    def result(self, player): ...
    def clone_env(self): ...
    def render(self): ...


class _FakeAgent:
    name = "fake"

    def choose_action(self, env, budget=None): ...


class TestProtocols:
    def test_env_with_all_methods_matches(self):
        assert isinstance(_FakeEnv(), GameEnv)

    def test_env_missing_undo_does_not_match(self):
        assert not isinstance(_FakeEnvMissingUndo(), GameEnv)

    def test_agent_matches(self):
        assert isinstance(_FakeAgent(), Agent)

    def test_object_without_choose_action_is_not_agent(self):
        class NoChoose:
            name = "x"

        assert not isinstance(NoChoose(), Agent)


# ---------------------------------------------------------------------------
# C2-DATA
# ---------------------------------------------------------------------------
def make_record(**overrides) -> GameRecord:
    moves = [
        MoveRecord(ply=1, player=Player.X, action=(5, 5), reward=0.0, elapsed_ms=1.5, nodes=10, simulations=0),
        MoveRecord(ply=2, player=Player.O, action=(5, 6), reward=0.0),
        MoveRecord(ply=3, player=Player.X, action=(6, 6), reward=1.0, simulations=50),
    ]
    base = dict(
        contract_version=CONTRACT_VERSION,
        game_id="g-001",
        config=GameConfig(),
        seed=42,
        x_agent="Minimax-Thiện",
        o_agent="MCTS",
        moves=moves,
        terminated=True,
        winner=Player.X,
    )
    base.update(overrides)
    return GameRecord(**base)


class TestJsonEncoding:
    def test_action_json_is_row_col_list(self):
        assert action_to_json((3, 7)) == [3, 7]
        assert isinstance(action_to_json((3, 7)), list)

    @pytest.mark.parametrize(
        "player, expected",
        [(Player.X, 1), (Player.O, -1), (Player.EMPTY, 0), (None, None)],
    )
    def test_player_json(self, player, expected):
        encoded = player_to_json(player)
        assert encoded == expected
        assert encoded is None or type(encoded) is int


class TestGameRecord:
    def test_default_moves_are_independent_lists(self):
        a = GameRecord(CONTRACT_VERSION, "a", GameConfig(), None, "x", "o")
        b = GameRecord(CONTRACT_VERSION, "b", GameConfig(), None, "x", "o")
        assert a.moves == [] and a.moves is not b.moves
        assert a.terminated is False and a.winner is None

    def test_record_is_frozen(self):
        with pytest.raises(dataclasses.FrozenInstanceError):
            make_record().winner = None  # type: ignore[misc]

    def test_valid_complete_record_passes_invariants(self):
        check_record_invariants(make_record())

    def test_draw_record_is_terminated_without_winner(self):
        check_record_invariants(make_record(winner=None))

    @pytest.mark.parametrize(
        "overrides",
        [
            {"contract_version": "caro-v1"},
            {"terminated": False},
            {"winner": Player.EMPTY},
            {
                "moves": [
                    MoveRecord(1, Player.X, (0, 0), 0.0),
                    MoveRecord(3, Player.O, (0, 1), 0.0),
                ]
            },
            {
                "moves": [
                    MoveRecord(1, Player.X, (0, 0), 0.0),
                    MoveRecord(2, Player.X, (0, 1), 0.0),
                ]
            },
            {
                "moves": [
                    MoveRecord(1, Player.X, (0, 0), 0.0),
                    MoveRecord(2, Player.O, (0, 0), 0.0),
                ]
            },
            {"moves": [MoveRecord(1, Player.O, (0, 0), 0.0)]},
        ],
    )
    def test_helper_detects_invalid_records(self, overrides):
        with pytest.raises(AssertionError):
            check_record_invariants(make_record(**overrides))

    def test_json_round_trip_in_memory(self):
        record = make_record()
        assert record_from_json(record_to_json(record)) == record

    def test_json_round_trip_draw_and_unfinished(self):
        for record in (make_record(winner=None), make_record(terminated=False, winner=None, moves=[])):
            assert record_from_json(record_to_json(record)) == record

    def test_json_payload_uses_only_json_types(self):
        payload = record_to_json(make_record())
        assert payload["moves"][0]["action"] == [5, 5]
        assert payload["moves"][0]["player"] == 1
        assert payload["moves"][1]["player"] == -1
        assert payload["winner"] == 1
        assert payload["config"] == {"board_size": 11, "win_length": 5}
        assert json.loads(json.dumps(payload)) == payload

    def test_round_trip_through_utf8_file(self, tmp_path):
        record = make_record()
        path = tmp_path / "games.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(record_to_json(record), ensure_ascii=False) + "\n")
        with path.open(encoding="utf-8") as handle:
            loaded = record_from_json(json.loads(handle.readline()))
        assert loaded == record
        assert loaded.x_agent == "Minimax-Thiện"

    def test_loader_rejects_other_contract_version(self):
        payload = record_to_json(make_record())
        payload["contract_version"] = "caro-v1"
        with pytest.raises(ValueError):
            record_from_json(payload)

    def test_loader_rejects_unsupported_config(self):
        payload = record_to_json(make_record())
        payload["config"]["board_size"] = 9
        with pytest.raises(InvalidConfigError):
            record_from_json(payload)
