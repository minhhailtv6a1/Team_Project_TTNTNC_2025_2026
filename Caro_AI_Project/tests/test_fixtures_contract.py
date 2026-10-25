# File: tests/test_fixtures_contract.py
"""Test cho fixture ``caro-v2`` (contract mục 3, 8.2 và 11.3).

* ``fixtures/test_vectors.json``: các ca luật. ``board_moves`` là một chuỗi nước
  đi CHƠI ĐƯỢC từ bàn rỗng (X đi trước, luân phiên); quân hoàn tất chuỗi luôn là
  nước cuối và kết quả kỳ vọng áp dụng sau nước cuối.
* ``fixtures/caro_v2_cases.jsonl``: các ``GameState`` v2 (mỗi dòng một object),
  thay cho ``caro_v1_case.jsonl``.

Nhóm ``TestVectorSchema`` và ``TestStateFixtureSchema`` không cần engine. Nhóm
replay cần ``CaroEnv``; trước khi PR M2 merge có thể chạy với
``CARO_C2_XFAIL=1`` (xfail không strict).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import (
    CONTRACT_VERSION,
    GameConfig,
    GameState,
    Player,
)
from helpers.helpers_contract import check_state_invariants

FIXTURE_DIR = Path(__file__).parent / "fixtures"
VECTORS_PATH = FIXTURE_DIR / "test_vectors.json"
STATES_PATH = FIXTURE_DIR / "caro_v2_cases.jsonl"
N = 11

engine_pending = pytest.mark.xfail(
    os.environ.get("CARO_C2_XFAIL") == "1",
    reason="Chờ PR engine của M2 (contract mục 11.2)",
    strict=False,
)

REQUIRED_IDS = {
    "TC01_HORIZONTAL_WIN",
    "TC02_VERTICAL_WIN",
    "TC03_DIAGONAL_MAIN_WIN",
    "TC04_DIAGONAL_ANTI_WIN",
    "TC05_ONE_END_BLOCKED_WIN",
    "TC06_BOTH_ENDS_BLOCKED_BY_O",
    "TC07_BLOCKED_BY_O_AND_EDGE",
    "TC08_OVERLINE_WIN",
    "TC09_DRAW_BOARD_FULL",
    "TC10_GAPPED_LINE_NO_WIN",
    "TC11_OVERLINE_ONE_END_BLOCKED_WIN",
    "TC12_OVERLINE_BLOCKED_BOTH_ENDS",
}
# Ca có chuỗi 6: quân cuối phải NỐI hai đoạn (< 5 quân mỗi đoạn) thành đúng 6 quân.
OVERLINE_IDS = {"TC08_OVERLINE_WIN", "TC11_OVERLINE_ONE_END_BLOCKED_WIN", "TC12_OVERLINE_BLOCKED_BOTH_ENDS"}
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


# ---------------------------------------------------------------------------
# Nạp fixture
# ---------------------------------------------------------------------------
def _load_vectors() -> dict:
    with VECTORS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _load_state_rows() -> list[dict]:
    rows = []
    with STATES_PATH.open(encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            if line.strip():
                rows.append(json.loads(line))  # mỗi dòng phải là một JSON hoàn chỉnh
    return rows


VECTORS = _load_vectors()
CASES = [pytest.param(case, id=case["id"]) for case in VECTORS["test_cases"]]
WIN_CASES = [pytest.param(c, id=c["id"]) for c in VECTORS["test_cases"] if c["expected_winner"] is not None]
OVERLINE_CASES = [pytest.param(c, id=c["id"]) for c in VECTORS["test_cases"] if c["id"] in OVERLINE_IDS]
STATE_ROWS = [pytest.param(row, id=row["id"]) for row in _load_state_rows()]


def to_action(raw) -> tuple[int, int]:
    """JSON ``[row, col]`` -> ``Action`` tuple (mục 8.2 của contract)."""
    assert isinstance(raw, list) and len(raw) == 2, f"action must be [row, col]: {raw!r}"
    return (raw[0], raw[1])


def longest_run_through(stones: set, cell: tuple[int, int]) -> int:
    """Chuỗi liên tiếp dài nhất đi qua ``cell`` theo bốn hướng (không cần engine)."""
    best = 1
    for dr, dc in DIRECTIONS:
        count = 1
        for sign in (1, -1):
            r, c = cell[0] + dr * sign, cell[1] + dc * sign
            while (r, c) in stones:
                count += 1
                r, c = r + dr * sign, c + dc * sign
        best = max(best, count)
    return best


def stones_of(case, player: int) -> list[tuple[int, int]]:
    return [tuple(m["action"]) for m in case["board_moves"] if m["player"] == player]


def expected_winner(case) -> Player | None:
    return None if case["expected_winner"] is None else Player(case["expected_winner"])


# ---------------------------------------------------------------------------
# test_vectors.json - schema (không cần engine)
# ---------------------------------------------------------------------------
class TestVectorSchema:
    def test_header_matches_contract(self):
        assert VECTORS["game_version"] == CONTRACT_VERSION
        assert VECTORS["board_size"] == N
        assert VECTORS["win_length"] == 5
        assert VECTORS["blocked_both_ends_rule"] is True

    def test_ids_are_unique_and_cover_required_cases(self):
        ids = [case["id"] for case in VECTORS["test_cases"]]
        assert len(ids) == len(set(ids))
        assert REQUIRED_IDS <= set(ids), f"missing: {sorted(REQUIRED_IDS - set(ids))}"

    @pytest.mark.parametrize("case", CASES)
    def test_case_is_well_formed(self, case):
        assert {"id", "description", "board_moves", "expected_winner", "terminated"} <= set(case)
        assert isinstance(case["description"], str) and case["description"]
        assert case["expected_winner"] in (1, -1, None)
        assert isinstance(case["terminated"], bool)
        if case["expected_winner"] is not None:
            assert case["terminated"] is True, "a winner implies terminated"
        moves = case["board_moves"]
        assert moves, "board_moves must not be empty"

        seen = set()
        for index, move in enumerate(moves):
            action = to_action(move["action"])
            assert all(type(v) is int for v in action), f"coordinates must be ints: {action}"
            assert 0 <= action[0] < N and 0 <= action[1] < N, f"out of bounds: {action}"
            assert action not in seen, f"cell used twice: {action}"
            seen.add(action)
            expected = 1 if index % 2 == 0 else -1
            assert move["player"] == expected, (
                f"move {index + 1} must be played by {'X' if expected == 1 else 'O'} (strict alternation)"
            )

    @pytest.mark.parametrize("case", WIN_CASES)
    def test_winning_case_ends_with_the_completing_stone(self, case):
        """Ván thắng chỉ được kết thúc ở nước cuối: trước nước cuối người thắng chưa có chuỗi 5."""
        winner = case["expected_winner"]
        last = tuple(case["board_moves"][-1]["action"])
        assert case["board_moves"][-1]["player"] == winner, "last move must be the winner's"
        before = set(stones_of(case, winner)) - {last}
        assert all(longest_run_through(before, cell) < 5 for cell in before), (
            "winner already had five in a row before the last move"
        )
        assert longest_run_through(before | {last}, last) >= 5

    @pytest.mark.parametrize("case", OVERLINE_CASES)
    def test_overline_cases_really_form_a_six(self, case):
        last = tuple(case["board_moves"][-1]["action"])
        before = set(stones_of(case, 1)) - {last}
        assert all(longest_run_through(before, cell) < 5 for cell in before), (
            "five stones were already in a row before the last move, so no overline can form"
        )
        assert longest_run_through(before | {last}, last) == 6

    def test_draw_case_fills_the_whole_board(self):
        case = next(c for c in VECTORS["test_cases"] if c["id"] == "TC09_DRAW_BOARD_FULL")
        assert len(case["board_moves"]) == N * N
        assert case["expected_winner"] is None and case["terminated"] is True

    def test_tc07_follows_the_contract_note(self):
        """Contract mục 3: TC07 phải có expected_winner = null và terminated = false.

        Quân O chặn (0,5) phải được đặt TRƯỚC quân cuối của X; nếu đặt sau, X đã
        thắng ở nước hoàn tất chuỗi (biên chỉ chặn một đầu) và ván đã kết thúc.
        """
        case = next(c for c in VECTORS["test_cases"] if c["id"] == "TC07_BLOCKED_BY_O_AND_EDGE")
        assert case["expected_winner"] is None
        assert case["terminated"] is False
        moves = case["board_moves"]
        actions = [tuple(m["action"]) for m in moves]
        assert actions.index((0, 5)) < len(moves) - 1, "O blocker must precede the last move"
        assert moves[actions.index((0, 5))]["player"] == -1
        assert moves[-1]["player"] == 1 and set(actions[:-1]) >= {(0, 0), (0, 1), (0, 2), (0, 3)}
        assert actions[-1] == (0, 4)


# ---------------------------------------------------------------------------
# test_vectors.json - replay bằng engine
# ---------------------------------------------------------------------------
@engine_pending
class TestVectorReplay:
    @pytest.mark.parametrize("case", CASES)
    def test_case_replays_to_expected_outcome(self, case):
        env = CaroEnv()
        env.reset()
        moves = case["board_moves"]
        result = None
        for index, move in enumerate(moves, start=1):
            assert env.state.current_player == Player(move["player"]), f"turn mismatch at move {index}"
            result = env.step(to_action(move["action"]))
            if index < len(moves):
                assert result.done is False, (
                    f"{case['id']}: game ended early at move {index}; "
                    "blockers must be placed before the completing stone"
                )

        state = env.state
        assert state.terminated is case["terminated"]
        assert state.winner == expected_winner(case)
        assert result.done is case["terminated"]
        assert result.winner == expected_winner(case)
        assert state.move_count == len(moves)
        assert state.last_action == to_action(moves[-1]["action"])
        if case["expected_winner"] is not None:
            assert result.reward == 1.0
        else:
            assert result.reward == 0.0
        if case["terminated"]:
            assert env.legal_actions() == []
        else:
            assert len(env.legal_actions()) == N * N - len(moves)
        check_state_invariants(state)

    def test_non_terminal_cases_accept_a_further_move(self):
        for case in VECTORS["test_cases"]:
            if case["terminated"]:
                continue
            env = CaroEnv()
            env.reset()
            for move in case["board_moves"]:
                env.step(to_action(move["action"]))
            follow_up = env.legal_actions()[0]
            result = env.step(follow_up)
            assert result.next_state.move_count == len(case["board_moves"]) + 1, case["id"]


# ---------------------------------------------------------------------------
# caro_v2_cases.jsonl - schema (không cần engine)
# ---------------------------------------------------------------------------
def build_state(raw: dict) -> GameState:
    return GameState(
        board=raw["board"],
        current_player=Player(raw["current_player"]),
        last_action=None if raw["last_action"] is None else to_action(raw["last_action"]),
        move_count=raw["move_count"],
        terminated=raw["terminated"],
        winner=None if raw["winner"] is None else Player(raw["winner"]),
    )


class TestStateFixtureSchema:
    def test_file_is_utf8_jsonl_with_one_object_per_line(self):
        raw = STATES_PATH.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), "no BOM"
        text = raw.decode("utf-8")
        lines = [line for line in text.splitlines() if line.strip()]
        assert len(lines) == len(_load_state_rows()) >= 4
        for line in lines:
            assert line.startswith("{") and line.endswith("}"), "each line must be one complete object"

    def test_ids_are_unique(self):
        ids = [row.values[0]["id"] for row in STATE_ROWS]
        assert len(ids) == len(set(ids))

    @pytest.mark.parametrize("row", STATE_ROWS)
    def test_row_is_a_valid_v2_state(self, row):
        assert {"id", "description", "config", "moves", "state"} <= set(row)
        config = GameConfig(**row["config"])
        assert set(row["state"]) == {
            "board", "current_player", "last_action", "move_count", "terminated", "winner",
        }, "state must contain exactly the caro-v2 fields"
        for action in row["moves"]:
            to_action(action)
        check_state_invariants(build_state(row["state"]), config)

    @pytest.mark.parametrize("row", STATE_ROWS)
    def test_move_count_matches_move_list(self, row):
        assert row["state"]["move_count"] == len(row["moves"])
        if row["moves"]:
            assert row["state"]["last_action"] == row["moves"][-1]
        else:
            assert row["state"]["last_action"] is None


# ---------------------------------------------------------------------------
# caro_v2_cases.jsonl - replay bằng engine
# ---------------------------------------------------------------------------
@engine_pending
class TestStateFixtureReplay:
    @pytest.mark.parametrize("row", STATE_ROWS)
    def test_replaying_moves_reproduces_the_fixture_state(self, row):
        env = CaroEnv()
        env.reset()
        for action in row["moves"]:
            env.step(to_action(action))
        assert env.state == build_state(row["state"])

    @pytest.mark.parametrize("row", STATE_ROWS)
    def test_fixture_state_matches_terminal_flags(self, row):
        env = CaroEnv()
        env.reset()
        for action in row["moves"]:
            env.step(to_action(action))
        assert env.is_terminal() is row["state"]["terminated"]
        if row["state"]["terminated"]:
            assert env.legal_actions() == []
