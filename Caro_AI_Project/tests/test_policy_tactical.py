"""W6 acceptance infrastructure; no neural/checkpoint dependency."""
import math

import pytest

from benchmarks.policy_acceptance import (
    build_env, evaluate, evaluate_case, load_cases, probability_summary, smoke_matches,
)
from core.agents.heuristic_ai import HeuristicAgent
from core.engine.interfaces import AgentDecision, Player
from core.engine.rules import RuleEngine

CASES = load_cases()


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_fixture_replays_and_teacher_passes_contract(case):
    env = build_env(case)
    assert env.is_terminal() == (case["kind"] == "terminal")
    if case["kind"] == "near_full":
        assert 1 <= len(env.legal_actions()) <= 3
    if case["id"] == "terminal_draw":
        assert env.state.winner is None
        assert env.state.move_count == 121
    result = evaluate_case(HeuristicAgent(), case)
    assert result["contract_pass"], result


@pytest.mark.parametrize("case", [c for c in CASES if c["kind"] in ("win", "block")],
                         ids=lambda c: c["id"])
def test_tactical_expected_matches_exhaustive_rules(case):
    env = build_env(case)
    state = env.state
    player = state.current_player if case["kind"] == "win" else Player(-state.current_player)
    winning = set()
    for row, col in env.legal_actions():
        board = [r[:] for r in state.board]
        board[row][col] = int(player)
        if any(RuleEngine.check_line(board, row, col, dr, dc, player, 11, 5)
               for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1))):
            winning.add((row, col))
    assert winning == {tuple(a) for a in case["expected_actions"]}
    if case["kind"] == "block":
        assert len(winning) == 1
        env.step(next(iter(winning)))
        assert not env.is_terminal()
        for action in env.legal_actions():
            trial = env.clone_env()
            trial.step(action)
            assert trial.state.winner != player


class StubAgent:
    name = "stub"

    def __init__(self, mode):
        self.mode = mode
        self.calls = 0

    def choose_action(self, env, budget=None):
        self.calls += 1
        if env.is_terminal() and self.mode != "terminal":
            raise RuntimeError("terminal")
        if self.mode == "terminal":
            return AgentDecision((0, 0))
        legal = env.legal_actions()
        action = legal[0]
        if self.mode == "illegal":
            action = (-1, 0)
        elif self.mode == "mutation":
            env.step(action)
        elif self.mode == "nondeterministic":
            action = legal[self.calls % 2]
        return AgentDecision(action)


@pytest.mark.parametrize("mode,case_id", [
    ("illegal", "midgame_x"), ("mutation", "opening_x"),
    ("nondeterministic", "opening_x"), ("terminal", "terminal_win"),
])
def test_contract_failures_are_reported(mode, case_id):
    result = evaluate_case(StubAgent(mode), next(c for c in CASES if c["id"] == case_id))
    assert not result["contract_pass"]
    assert result["contract_errors"]


def test_tactical_miss_is_advisory_and_top5_not_fabricated():
    result = evaluate_case(StubAgent("legal"), next(c for c in CASES if c["id"] == "win_x_gap"))
    assert result["contract_pass"]
    assert result["quality_action_hit"] is False
    assert result["top5"] is None


def test_probability_reader_reports_real_topk():
    def reader(agent, env):
        values = [0.0] * 121
        values[6 * 11 + 4] = 1.0
        return values

    result = evaluate_case(StubAgent("legal"), next(c for c in CASES if c["id"] == "win_x_gap"), reader)
    assert result["contract_pass"]
    assert result["top5"][0] == {"action": (6, 4), "probability": 1.0}
    assert result["quality_topk_hits"] == {"1": True, "3": True, "5": True}
    assert result["teacher_in_top5"]


@pytest.mark.parametrize("bad", ["length", "nan", "negative", "sum", "illegal"])
def test_invalid_probabilities_rejected(bad):
    env = build_env(next(c for c in CASES if c["id"] == "opening_o"))
    values = [0.0] * 121
    values[0] = 1.0
    if bad == "length":
        values.pop()
    elif bad == "nan":
        values[0] = math.nan
    elif bad == "negative":
        values[0] = -1.0
    elif bad == "sum":
        values[0] = 0.5
    else:
        values[0] = 0.0
        values[4 * 11 + 6] = 1.0
    with pytest.raises(ValueError):
        probability_summary(values, env)


def test_baseline_smoke_uses_runner_and_replay():
    report = smoke_matches(HeuristicAgent())
    assert report["pass"], report
    assert len(report["pairs"]) == 2
    assert all(len(pair["records"]) == 2 for pair in report["pairs"])


def test_smoke_records_agent_failure():
    report = smoke_matches(StubAgent("illegal"))
    assert not report["pass"]
    assert all(pair["errors"] for pair in report["pairs"])


def test_generic_report_never_claims_checkpoint_verified():
    report = evaluate(HeuristicAgent())
    assert report["contract_pass"]
    assert report["checkpoint_load_status"] == "not_checked_by_generic_harness"
