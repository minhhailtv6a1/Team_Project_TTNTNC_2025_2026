"""W6 acceptance infrastructure and optional real-checkpoint contract tests."""
import math
import os
from pathlib import Path

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


def test_smoke_loss_diagnostics_follow_serialized_record_schema():
    from benchmarks.policy_checkpoint_acceptance import smoke_failure_examples

    case = next(c for c in CASES if c["id"] == "terminal_win")
    record = {"game_id": "diagnostic-fixture", "x_agent": "opponent-heuristic",
              "o_agent": "candidate", "winner": 1,
              "moves": [{"action": action, "player": 1 if i % 2 == 0 else -1}
                        for i, action in enumerate(case["actions"])]}

    def uniform_reader(agent, env):
        legal = set(env.legal_actions())
        return [1 / len(legal) if divmod(i, 11) in legal else 0 for i in range(121)]

    examples = smoke_failure_examples(StubAgent("legal"), uniform_reader,
        {"pairs": [{"opponent": "heuristic", "records": [record]}]})
    assert len(examples) == 1
    example = examples[0]
    assert example["candidate_side"] == -1
    assert example["action"] == case["actions"][-2]
    assert example["opponent_winning_reply"] == case["actions"][-1]
    assert example["history_before"] == case["actions"][:-2]
    assert len(example["top5"]) == 5
    assert sum(example["legal_probabilities"]) == pytest.approx(1)


@pytest.fixture(scope="module")
def checkpoint_candidate():
    path = os.environ.get("CARO_POLICY_CHECKPOINT")
    if not path:
        pytest.skip("Set CARO_POLICY_CHECKPOINT to evaluate a trained checkpoint")
    assert Path(path).is_file(), f"Checkpoint not found: {path}"
    torch = pytest.importorskip("torch")
    from core.agents.neural_ai import NeuralAgent
    from benchmarks.policy_checkpoint_acceptance import CheckpointProbabilityReader

    previous_threads = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        agent = NeuralAgent(path, device="cpu")
        yield agent, CheckpointProbabilityReader(agent)
    finally:
        torch.set_num_threads(previous_threads)


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_trained_policy_contract_and_real_probabilities(checkpoint_candidate, case):
    agent, reader = checkpoint_candidate
    result = evaluate_case(agent, case, reader)
    assert result["contract_pass"], result
    if case["kind"] == "terminal":
        return
    env = build_env(case)
    values = reader(agent, env)
    legal = set(env.legal_actions())
    assert sum(values) == pytest.approx(1, abs=1e-6)
    assert all(p == 0 for i, p in enumerate(values) if divmod(i, 11) not in legal)
    assert result["action"] == tuple(result["top5"][0]["action"])
    assert agent.choose_action(env).score == pytest.approx(max(values), abs=1e-6)
    # Tactical success is advisory; do not turn this into a quality assertion.


def test_checkpoint_acceptance_rejects_wrong_digest(checkpoint_candidate):
    from benchmarks.policy_checkpoint_acceptance import evaluate_checkpoint

    agent, _ = checkpoint_candidate
    with pytest.raises(ValueError, match="SHA-256"):
        evaluate_checkpoint(agent.checkpoint_path, expected={"checkpoint_sha256": "0" * 64})


def test_dataset_independence_is_not_inferred_from_provenance(checkpoint_candidate, tmp_path):
    import json
    from benchmarks.policy_checkpoint_acceptance import audit_fixture_overlap

    agent, _ = checkpoint_candidate
    unavailable = audit_fixture_overlap(agent)
    assert unavailable["pass"] is None
    assert unavailable["status"] == "not_audited_dataset_unavailable"
    (tmp_path / "dataset_manifest.json").write_text(
        json.dumps({"dataset_version": "wrong-dataset"}), encoding="utf-8")
    with pytest.raises(ValueError, match="exact checkpoint dataset"):
        audit_fixture_overlap(agent, tmp_path)


def test_overlap_audit_detects_real_encoded_state_collision(tmp_path):
    import json
    from types import SimpleNamespace
    import numpy as np
    from benchmarks.policy_checkpoint_acceptance import audit_fixture_overlap, sha256
    from core.ml.data_pipeline import encode_policy_state

    env = build_env(next(c for c in CASES if c["id"] == "opening_x"))
    x, mask = encode_policy_state(env.state, env.legal_actions(), 11)
    manifest = {"contract_version": "caro-v2", "board_size": 11,
                "dataset_version": "overlap-test-only", "artifacts": {}}
    for split in ("val", "test"):
        path = tmp_path / f"{split}.npz"
        np.savez(path, x=x[None], legal_mask=mask[None], target=np.array([0], dtype=np.int64))
        manifest["artifacts"][split] = {"tensor": path.name, "tensor_sha256": sha256(path)}
    manifest_path = tmp_path / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    agent = SimpleNamespace(dataset_version=manifest["dataset_version"],
                            dataset_manifest_sha256=sha256(manifest_path))
    result = audit_fixture_overlap(agent, tmp_path)
    assert result["pass"] is False
    assert result["overlaps"] == {"val": ["opening_x"], "test": ["opening_x"]}


def test_real_checkpoint_smoke_through_runner(checkpoint_candidate):
    agent, _ = checkpoint_candidate
    report = smoke_matches(agent, games=2)
    assert report["pass"], report
    for pair in report["pairs"]:
        assert len(pair["records"]) == 2
        assert {r["x_agent"] for r in pair["records"]} == {
            "candidate", f"opponent-{pair['opponent']}"}
