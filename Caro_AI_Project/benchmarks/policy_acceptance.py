"""W6 acceptance independent of neural implementation and checkpoint format.

Optional probability_reader(agent, env) returns row-major legal probabilities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.agents.heuristic_ai import HeuristicAgent
from core.agents.random_ai import RandomAgent
from core.engine.game_env import CaroEnv
from core.engine.interfaces import AgentDecision, SearchBudget, index_to_action
from core.utils.logger import game_to_dict, validate_game_record
from core.utils.tournament_runner import Participant, load_factory, run_match

FIXTURES = ROOT / "tests/fixtures/policy_tactical_w6.json"


def load_cases():
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    if data["contract_version"] != "caro-v2" or data["board_size"] != 11:
        raise ValueError("Expected caro-v2, 11x11 fixtures")
    return data["cases"]


def build_env(case):
    env = CaroEnv()
    for action in case["actions"]:
        env.step(tuple(action))
    return env


def snapshot(env):
    return env.config, env.state, env.legal_actions()


def probability_summary(values, env):
    values = [float(v) for v in values]
    size = env.config.board_size
    legal = set(env.legal_actions())
    if len(values) != size * size or any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("Expected finite nonnegative probabilities for every cell")
    if not math.isclose(sum(values), 1.0, rel_tol=0, abs_tol=1e-6):
        raise ValueError("Legal probabilities must sum to one")
    if any(v != 0 for i, v in enumerate(values) if index_to_action(i, size) not in legal):
        raise ValueError("Illegal cells must have zero probability")
    ranked = sorted(legal, key=lambda a: (-values[a[0] * size + a[1]], a))[:5]
    return [{"action": a, "probability": values[a[0] * size + a[1]]} for a in ranked]


def evaluate_case(agent, case, probability_reader=None):
    env = build_env(case)
    before = snapshot(env)
    errors = []
    result = {"case_id": case["id"], "actions": case["actions"],
              "expected_actions": case.get("expected_actions", []),
              "kind": case["kind"], "contract_errors": errors,
              "top5": None, "top5_status": "unavailable: no probability reader"}
    budget = SearchBudget(seed=11)
    if env.is_terminal():
        try:
            agent.choose_action(env, budget)
        except RuntimeError:
            pass
        except Exception as exc:
            errors.append(f"terminal guard raised {type(exc).__name__}: {exc}")
        else:
            errors.append("terminal guard did not raise RuntimeError")
    else:
        try:
            decisions = []
            for _ in range(2):
                decision = agent.choose_action(env, budget)
                if snapshot(env) != before:
                    errors.append("Inference mutated environment")
                if not isinstance(decision, AgentDecision):
                    raise TypeError("Expected AgentDecision")
                action = decision.action
                if (not isinstance(action, tuple) or len(action) != 2
                        or any(type(v) is not int for v in action) or action not in before[2]):
                    errors.append(f"Illegal or malformed action: {action!r}")
                if any(type(v) is not int or v < 0 for v in (decision.nodes, decision.simulations)):
                    errors.append("Invalid decision counters")
                if not math.isfinite(decision.elapsed_ms) or decision.elapsed_ms < 0:
                    errors.append("Invalid elapsed time")
                if decision.score is not None and not math.isfinite(decision.score):
                    errors.append("Non-finite score")
                decisions.append(decision)
            result["action"] = decisions[0].action
            if decisions[0].action != decisions[1].action:
                errors.append("Repeated inference returned different actions")
            expected = [tuple(a) for a in case.get("expected_actions", [])]
            teacher = HeuristicAgent().choose_action(build_env(case)).action
            result["teacher_action"] = teacher
            result["quality_action_hit"] = result["action"] in expected if expected else None
            if probability_reader is not None:
                result["top5"] = probability_summary(probability_reader(agent, env), env)
                result["top5_status"] = "measured"
                top = [row["action"] for row in result["top5"]]
                result["quality_topk_hits"] = {
                    str(k): any(a in top[:k] for a in expected) if expected else None
                    for k in (1, 3, 5)}
                result["teacher_in_top5"] = teacher in top
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    if snapshot(env) != before:
        errors.append("Inference mutated environment")
    result["contract_pass"] = not errors
    return result


def evaluate(agent, probability_reader=None):
    results = [evaluate_case(agent, c, probability_reader) for c in load_cases()]
    return {"contract_version": "caro-v2", "agent": agent.name,
            "checkpoint_load_status": "not_checked_by_generic_harness",
            "fixture_sha256": hashlib.sha256(FIXTURES.read_bytes()).hexdigest(),
            "contract_pass": all(r["contract_pass"] for r in results),
            "quality_is_advisory": True, "cases": results}


def smoke_matches(agent, games=2):
    """Swapped sides, complete records; no strength claim."""
    if games not in (2, 4):
        raise ValueError("Smoke requires 2 or 4 games per pair")
    results = []
    for opponent in (RandomAgent(), HeuristicAgent()):
        pair = {"opponent": opponent.name, "records": [], "errors": []}
        try:
            outcomes = run_match(CaroEnv, Participant("candidate", agent),
                                 Participant(f"opponent-{opponent.name}", opponent),
                                 games=games, base_seed=11)
            for outcome in outcomes:
                validate_game_record(outcome.record)
                replay = CaroEnv()
                for move in outcome.record.moves:
                    if move.player != replay.state.current_player:
                        raise ValueError("Smoke replay player mismatch")
                    replay.step(move.action)
                if not replay.is_terminal() or replay.state.winner != outcome.record.winner:
                    raise ValueError("Smoke replay terminal/winner mismatch")
                pair["records"].append(game_to_dict(outcome.record))
        except Exception as exc:
            pair["errors"].append(f"{type(exc).__name__}: {exc}")
        pair["pass"] = not pair["errors"] and len(pair["records"]) == games
        results.append(pair)
    return {"purpose": "pipeline only; no strength conclusion", "pairs": results,
            "pass": all(p["pass"] for p in results)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factory", default="core.agents.heuristic_ai:HeuristicAgent")
    parser.add_argument("--options", default="{}", help="JSON constructor kwargs")
    parser.add_argument("--probability-reader", help="Optional module:function(agent, env)")
    parser.add_argument("--smoke-games", type=int, choices=(0, 2, 4), default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    agent = load_factory(args.factory)(**json.loads(args.options))
    reader = load_factory(args.probability_reader) if args.probability_reader else None
    report = evaluate(agent, reader)
    report["factory"] = args.factory
    if args.smoke_games:
        report["smoke"] = smoke_matches(agent, args.smoke_games)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if report["contract_pass"] and report.get("smoke", {}).get("pass", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
