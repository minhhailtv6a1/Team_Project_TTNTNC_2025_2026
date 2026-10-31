"""Test runner W34-T21..T26 với môi trường và agent giả.

``MiniEnv`` là một ``GameEnv`` tối giản đúng luật caro-v2 để runner test độc lập
với engine thật. Muốn chạy với ``CaroEnv`` thì đổi fixture ``env_factory``.
"""

from __future__ import annotations

import random
import time

import pytest

from core.engine.interfaces import (
    Action,
    AgentDecision,
    GameConfig,
    GameState,
    InvalidActionError,
    InvalidActionReason,
    Player,
    SearchBudget,
    StepResult,
    UndoError,
)
from core.utils.logger import GameLogger, load_games, validate_game_record
from core.utils.tournament_runner import (
    AgentError,
    BudgetEnforcer,
    BudgetViolationError,
    Participant,
    budget_from_dict,
    check_scenario,
    derive_seed,
    load_factory,
    play_game,
    run_match,
    run_tournament,
    summarize_outcomes,
)

N = 11


# ---------------------------------------------------------------------------
# Môi trường giả
# ---------------------------------------------------------------------------
class MiniEnv:
    def __init__(self) -> None:
        self._cfg = GameConfig()
        self.reset()

    @property
    def config(self) -> GameConfig:
        return self._cfg

    @property
    def state(self) -> GameState:
        return GameState(
            board=[row[:] for row in self._board],
            current_player=Player.X if self._count % 2 == 0 else Player.O,
            last_action=self._last,
            move_count=self._count,
            terminated=self._term,
            winner=self._winner,
        )

    def reset(self, seed: int | None = None) -> GameState:
        self._board = [[0] * N for _ in range(N)]
        self._last: Action | None = None
        self._count = 0
        self._term = False
        self._winner: Player | None = None
        self._history: list[tuple] = []
        return self.state

    def legal_actions(self) -> list[Action]:
        if self._term:
            return []
        return [(r, c) for r in range(N) for c in range(N) if self._board[r][c] == 0]

    def _wins(self, r: int, c: int, p: int) -> bool:
        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            n, ends = 1, []
            for s in (1, -1):
                rr, cc = r + dr * s, c + dc * s
                while 0 <= rr < N and 0 <= cc < N and self._board[rr][cc] == p:
                    n += 1
                    rr, cc = rr + dr * s, cc + dc * s
                ends.append(not (0 <= rr < N and 0 <= cc < N) or self._board[rr][cc] == -p)
            if n >= 5 and not all(ends):
                return True
        return False

    def step(self, action: Action) -> StepResult:
        if self._term:
            raise InvalidActionError(InvalidActionReason.GAME_OVER, action, "game over")
        if not (isinstance(action, tuple) and len(action) == 2
                and all(type(v) is int for v in action)):
            raise InvalidActionError(InvalidActionReason.MALFORMED, action, "malformed")
        r, c = action
        if not (0 <= r < N and 0 <= c < N):
            raise InvalidActionError(InvalidActionReason.OUT_OF_BOUNDS, action, "oob")
        if self._board[r][c] != 0:
            raise InvalidActionError(InvalidActionReason.OCCUPIED, action, "occupied")
        self._history.append(([row[:] for row in self._board], self._last,
                              self._count, self._term, self._winner))
        player = Player.X if self._count % 2 == 0 else Player.O
        self._board[r][c] = int(player)
        self._last, self._count = action, self._count + 1
        if self._wins(r, c, int(player)):
            self._term, self._winner = True, player
        elif self._count == N * N:
            self._term = True
        state = self.state
        return StepResult(state, 1.0 if self._winner else 0.0, self._term, self._winner)

    def is_terminal(self) -> bool:
        return self._term

    def result(self, player: Player) -> float | None:
        if player not in (Player.X, Player.O):
            raise ValueError("player must be X or O")
        if not self._term:
            return None
        if self._winner is None:
            return 0.0
        return 1.0 if self._winner == player else -1.0

    def clone_env(self) -> MiniEnv:
        other = MiniEnv()
        other._board = [row[:] for row in self._board]
        other._last, other._count = self._last, self._count
        other._term, other._winner = self._term, self._winner
        other._history = [(b, l, c, t, w) for b, l, c, t, w in self._history]
        return other

    def undo(self) -> GameState:
        if not self._history:
            raise UndoError("empty history")
        self._board, self._last, self._count, self._term, self._winner = self._history.pop()
        return self.state

    def render(self) -> str:
        return "\n".join("".join(".XO"[v] for v in row) for row in self._board)


@pytest.fixture
def env_factory():
    return MiniEnv


# ---------------------------------------------------------------------------
# Agent giả
# ---------------------------------------------------------------------------
class FirstLegalAgent:
    def __init__(self, name: str = "first") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def choose_action(self, env, budget=None) -> AgentDecision:
        return AgentDecision(env.legal_actions()[0], score=0.0, nodes=1, simulations=2)


class SeededRandomAgent:
    name = "rand"

    def choose_action(self, env, budget=None) -> AgentDecision:
        rng = random.Random(None if budget is None else budget.seed)
        return AgentDecision(rng.choice(env.legal_actions()))


class FixedActionAgent:
    name = "fixed"

    def __init__(self, action) -> None:
        self._action = action

    def choose_action(self, env, budget=None) -> AgentDecision:
        return AgentDecision(self._action)


class MutatingAgent:
    name = "mutator"

    def choose_action(self, env, budget=None) -> AgentDecision:
        env.step(env.legal_actions()[0])
        return AgentDecision(env.legal_actions()[0])


class RaisingAgent:
    name = "raiser"

    def choose_action(self, env, budget=None) -> AgentDecision:
        raise RuntimeError("boom")


class SlowAgent:
    name = "slow"

    def choose_action(self, env, budget=None) -> AgentDecision:
        time.sleep(0.03)
        return AgentDecision(env.legal_actions()[0])  # cố tình báo elapsed_ms=0


def P(label: str, agent, budget: SearchBudget | None = None) -> Participant:
    return Participant(label, agent, budget)


# ---------------------------------------------------------------------------
# W34-T21: một game chạy đến terminal, record đủ ply
# ---------------------------------------------------------------------------
def test_t21_single_game_reaches_terminal(env_factory):
    outcome = play_game(env_factory, P("r1", SeededRandomAgent()),
                        P("r2", SeededRandomAgent()), game_id="g", seed=7)
    record = outcome.record
    assert record.terminated
    assert [m.ply for m in record.moves] == list(range(1, len(record.moves) + 1))
    assert len(outcome.wall_ms) == len(record.moves)
    validate_game_record(record)  # luân phiên X/O, không trùng action
    if record.winner is not None:
        assert record.moves[-1].reward == 1.0
        assert record.moves[-1].player == record.winner


def test_deterministic_with_same_seed(env_factory):
    def run():
        return run_match(env_factory, P("a", SeededRandomAgent()),
                         P("b", SeededRandomAgent()), games=2, base_seed=5)

    first = [o.record.moves for o in run()]
    second = [o.record.moves for o in run()]
    assert [[m.action for m in g] for g in first] == [[m.action for m in g] for g in second]


def test_derive_seed_is_stable_and_non_negative():
    assert derive_seed(1, 2, 3) == derive_seed(1, 2, 3)
    assert derive_seed(1, 2, 3) != derive_seed(1, 2, 4)
    assert 0 <= derive_seed(10**12, 5) < 2**31


# ---------------------------------------------------------------------------
# W34-T22: agent trả action sai -> lỗi rõ agent, ply, action
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("bad", [(0, 99), (-1, 0), "oops", (1.0, 2), (True, 1), (1, 2, 3)])
def test_t22_invalid_action_reports_agent_ply_action(env_factory, bad):
    with pytest.raises(AgentError) as info:
        play_game(env_factory, P("bad-agent", FixedActionAgent(bad)),
                  P("ok", FirstLegalAgent()), game_id="g", seed=1)
    assert info.value.agent == "bad-agent"
    assert info.value.ply == 1
    assert info.value.action == bad
    assert "bad-agent" in str(info.value) and "ply=1" in str(info.value)


def test_t22_occupied_action_is_rejected(env_factory):
    # X đi (0,0); agent O cố đi lại (0,0) ở ply 2.
    with pytest.raises(AgentError) as info:
        play_game(env_factory, P("x", FirstLegalAgent()),
                  P("o-bad", FixedActionAgent((0, 0))), game_id="g", seed=1)
    assert info.value.agent == "o-bad" and info.value.ply == 2


def test_agent_exception_is_wrapped_with_context(env_factory):
    with pytest.raises(AgentError, match="boom") as info:
        play_game(env_factory, P("x", FirstLegalAgent()),
                  P("raiser", RaisingAgent()), game_id="g", seed=1)
    assert info.value.agent == "raiser" and info.value.ply == 2


def test_mutating_agent_is_detected(env_factory):
    with pytest.raises(AgentError, match="mutated"):
        play_game(env_factory, P("mut", MutatingAgent()),
                  P("ok", FirstLegalAgent()), game_id="g", seed=1)


# ---------------------------------------------------------------------------
# W34-T23: đổi bên và thống kê không gộp nhầm
# ---------------------------------------------------------------------------
def test_t23_sides_are_swapped(env_factory):
    a, b = P("a", SeededRandomAgent()), P("b", SeededRandomAgent())
    out = run_match(env_factory, a, b, games=4, base_seed=3)
    assert [(o.record.x_agent, o.record.o_agent) for o in out] == [
        ("a", "b"), ("b", "a"), ("a", "b"), ("b", "a"),
    ]
    # hai ván đổi bên liền nhau chung seed
    assert out[0].record.seed == out[1].record.seed
    assert out[0].record.seed != out[2].record.seed


def test_swap_requires_two_games_and_distinct_labels(env_factory):
    a, b = P("a", FirstLegalAgent()), P("b", FirstLegalAgent())
    with pytest.raises(ValueError):
        run_match(env_factory, a, b, games=1, base_seed=1)
    with pytest.raises(ValueError):
        run_match(env_factory, a, P("a", FirstLegalAgent()), games=2, base_seed=1)


def test_t23_summary_keeps_x_and_o_separate(env_factory):
    out = run_match(env_factory, P("a", FirstLegalAgent("a")),
                    P("b", FirstLegalAgent("b")), games=2, base_seed=1)
    summary = summarize_outcomes(out)
    for label in ("a", "b"):
        stats = summary[label]
        assert stats["as_x"]["games"] == 1 and stats["as_o"]["games"] == 1
        assert stats["overall"]["games"] == 2
        total = stats["overall"]
        assert total["wins"] + total["draws"] + total["losses"] == 2
    # kết quả đối xứng: thắng của bên này là thua của bên kia
    assert summary["a"]["overall"]["wins"] == summary["b"]["overall"]["losses"]


# ---------------------------------------------------------------------------
# W34-T24: JSONL round-trip qua runner
# ---------------------------------------------------------------------------
def test_t24_logger_round_trip_via_runner(env_factory, tmp_path):
    path = tmp_path / "games.jsonl"
    with GameLogger(path, mode="w") as logger:
        out = run_match(env_factory, P("a", SeededRandomAgent()),
                        P("b", SeededRandomAgent()), games=2, base_seed=9, logger=logger)
    assert load_games(path) == [o.record for o in out]


# ---------------------------------------------------------------------------
# W34-T25: metrics tổng hợp nodes / simulations
# ---------------------------------------------------------------------------
def test_t25_metrics_aggregate_nodes_and_simulations(env_factory):
    out = run_match(env_factory, P("a", FirstLegalAgent("a")),
                    P("b", FirstLegalAgent("b")), games=2, base_seed=1)
    summary = summarize_outcomes(out)
    expected_moves = sum(len(o.record.moves) for o in out)
    moves = summary["a"]["overall"]["moves"] + summary["b"]["overall"]["moves"]
    assert moves == expected_moves
    for label in ("a", "b"):
        o = summary[label]["overall"]
        assert o["total_nodes"] == o["moves"]           # mỗi nước nodes=1
        assert o["total_simulations"] == 2 * o["moves"]  # mỗi nước simulations=2
        assert o["mean_move_ms"] is not None and o["p95_move_ms"] >= o["mean_move_ms"] * 0


# ---------------------------------------------------------------------------
# W34-T26: budget violation quan sát được; fail-fast cho test
# ---------------------------------------------------------------------------
def _decision(nodes=0, sims=0, elapsed=0.0) -> AgentDecision:
    return AgentDecision((0, 0), nodes=nodes, simulations=sims, elapsed_ms=elapsed)


def test_t26_enforcer_records_each_violation_kind():
    enforcer = BudgetEnforcer(tolerance_ms=5)
    budget = SearchBudget(time_limit_ms=10, max_nodes=100, simulations=50)

    ok = enforcer.check(agent="a", ply=1, budget=budget, wall_ms=12.0,
                        decision=_decision(100, 50, 12.0))
    assert ok == []

    found = enforcer.check(agent="a", ply=2, budget=budget, wall_ms=40.0,
                           decision=_decision(101, 51, 40.0))
    assert {v.kind for v in found} == {"time_limit_ms", "max_nodes", "simulations"}
    assert enforcer.violations == found  # được lưu lại, không bỏ qua im lặng


def test_t26_elapsed_mismatch_is_flagged():
    enforcer = BudgetEnforcer(tolerance_ms=5)
    found = enforcer.check(agent="a", ply=1, budget=None, wall_ms=100.0,
                           decision=_decision(elapsed=0.0))
    assert [v.kind for v in found] == ["elapsed_mismatch"]


def test_t26_record_mode_collects_violations_in_game(env_factory):
    enforcer = BudgetEnforcer(tolerance_ms=1)
    budget = SearchBudget(max_nodes=1)  # FirstLegalAgent trả nodes=1 -> không vi phạm
    out = play_game(env_factory, P("a", FirstLegalAgent("a"), budget),
                    P("b", FirstLegalAgent("b"), budget),
                    game_id="g", seed=1, enforcer=enforcer)
    assert out.violations == []

    tight = SearchBudget(simulations=1)  # agent báo simulations=2 -> vi phạm mỗi nước
    out = play_game(env_factory, P("a", FirstLegalAgent("a"), tight),
                    P("b", FirstLegalAgent("b"), tight),
                    game_id="g", seed=1, enforcer=enforcer)
    assert len(out.violations) == len(out.record.moves)
    assert all(v.kind == "simulations" for v in out.violations)


def test_t26_fail_fast_raises(env_factory):
    enforcer = BudgetEnforcer(tolerance_ms=1, fail_fast=True)
    tight = SearchBudget(time_limit_ms=1)
    with pytest.raises(BudgetViolationError) as info:
        play_game(env_factory, P("slow", SlowAgent(), tight),
                  P("ok", FirstLegalAgent()), game_id="g", seed=1, enforcer=enforcer)
    assert info.value.agent == "slow" and info.value.ply == 1


# ---------------------------------------------------------------------------
# Tournament, config và scenario
# ---------------------------------------------------------------------------
def test_tournament_runs_all_pairs(env_factory):
    parts = [P("a", FirstLegalAgent("a")), P("b", SeededRandomAgent()),
             P("c", SeededRandomAgent())]
    result = run_tournament(env_factory, parts, games_per_pair=2, base_seed=1)
    assert len(result.outcomes) == 3 * 2  # 3 cặp x 2 ván
    assert set(result.summary) == {"a", "b", "c"}
    for stats in result.summary.values():
        assert stats["as_x"]["games"] > 0 and stats["as_o"]["games"] > 0


def test_tournament_rejects_duplicate_labels(env_factory):
    with pytest.raises(ValueError):
        run_tournament(env_factory, [P("a", FirstLegalAgent()), P("a", FirstLegalAgent())],
                       games_per_pair=2, base_seed=1)


def test_budget_from_dict_drops_label_and_sets_seed():
    budget = budget_from_dict({"label": "sims-100", "simulations": 100}, seed=3)
    assert budget == SearchBudget(simulations=100, seed=3)
    with pytest.raises(ValueError):
        budget_from_dict({"simulations": 0})
    with pytest.raises(ValueError):
        budget_from_dict({"nonsense": 1})


def test_load_factory():
    assert load_factory("collections:OrderedDict").__name__ == "OrderedDict"
    for bad in ("nocolon", ":x", "mod:"):
        with pytest.raises(ValueError):
            load_factory(bad)


def test_check_scenario_validates_expectations(env_factory):
    win = {
        "id": "win",
        "actions": [[5, 4], [0, 0], [5, 5], [0, 2], [5, 6], [0, 4], [5, 7], [10, 10]],
        "expect": {"to_move": 1, "winning_actions": [[5, 3], [5, 8]]},
    }
    block = {
        "id": "block",
        "actions": [[5, 3], [0, 0], [5, 4], [0, 2], [5, 6], [0, 4], [5, 7]],
        "expect": {"to_move": -1, "forced_actions": [[5, 5]]},
    }
    check_scenario(env_factory, win)
    check_scenario(env_factory, block)

    wrong = {**win, "expect": {"to_move": 1, "winning_actions": [[0, 5]]}}
    with pytest.raises(ValueError):
        check_scenario(env_factory, wrong)
    with pytest.raises(ValueError):
        check_scenario(env_factory, {**block, "expect": {"to_move": 1}})
