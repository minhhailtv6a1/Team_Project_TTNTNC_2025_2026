"""Smoke benchmark MCTS cho profile W34 100/400/1000 simulations.

Chạy từ repo:

    .\\myenv\\Scripts\\python.exe benchmarks\\bench_mcts.py

Benchmark không đặt ngưỡng pass/fail theo thời gian vì latency phụ thuộc máy.
Correctness và counter được kiểm tra trong ``tests/test_mcts_ai.py``.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.agents.mcts_ai import MCTSAgent  # noqa: E402
from core.engine.game_env import CaroEnv  # noqa: E402
from core.engine.interfaces import AgentDecision, SearchBudget  # noqa: E402


DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "benchmark.json"
SEARCH_BUDGET_FIELDS = {
    "time_limit_ms",
    "max_depth",
    "max_nodes",
    "simulations",
    "seed",
}


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    if config.get("contract_version") != "caro-v2":
        raise ValueError("benchmark config must use contract_version='caro-v2'")
    return config


def find_scenario(config: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    for scenario in config["scenarios"]:
        if scenario["id"] == scenario_id:
            return scenario
    known = ", ".join(s["id"] for s in config["scenarios"])
    raise ValueError(f"unknown scenario {scenario_id!r}; choose one of: {known}")


def build_env(actions: list[list[int]]) -> CaroEnv:
    env = CaroEnv()
    for raw_action in actions:
        env.step((int(raw_action[0]), int(raw_action[1])))
    if env.is_terminal():
        raise ValueError("benchmark scenario must be non-terminal")
    return env


def make_budget(data: dict[str, Any], seed: int) -> SearchBudget:
    fields = {key: value for key, value in data.items() if key in SEARCH_BUDGET_FIELDS}
    fields["seed"] = seed
    return SearchBudget(**fields)


def run_profile(
    *,
    scenario: dict[str, Any],
    budget_data: dict[str, Any],
    seed: int,
    repeats: int,
) -> dict[str, Any]:
    decisions: list[AgentDecision] = []
    budget = make_budget(budget_data, seed)
    for _ in range(repeats):
        env = build_env(scenario["actions"])
        decision = MCTSAgent().choose_action(env, budget)
        if decision.action not in env.legal_actions():
            raise RuntimeError(f"MCTS returned illegal action {decision.action!r}")
        decisions.append(decision)

    logical = {
        (d.action, d.score, d.nodes, d.simulations)
        for d in decisions
    }
    if len(logical) != 1:
        raise RuntimeError("same scenario, seed and budget produced different logical results")

    first = decisions[0]
    elapsed_ms = statistics.median(d.elapsed_ms for d in decisions)
    throughput = (
        first.simulations / (elapsed_ms / 1000.0)
        if elapsed_ms > 0.0
        else float("inf")
    )
    return {
        "profile": budget_data.get("label", "mcts"),
        "seed": seed,
        "action": first.action,
        "score": first.score,
        "elapsed_ms": elapsed_ms,
        "nodes": first.nodes,
        "simulations": first.simulations,
        "simulations_per_second": throughput,
    }


def print_report(
    rows: list[dict[str, Any]],
    *,
    scenario_id: str,
    repeats: int,
) -> None:
    print(
        f"Python {platform.python_version()} | {platform.system()} "
        f"{platform.release()} | {platform.machine()} | CPU={os.cpu_count()}"
    )
    print(f"scenario={scenario_id} | repeats={repeats} | contract=caro-v2")
    print(
        f"{'profile':<12}{'seed':>7}{'action':>13}{'score':>10}"
        f"{'elapsed ms':>14}{'nodes':>10}{'sims':>10}{'sims/s':>12}"
    )
    for row in rows:
        print(
            f"{row['profile']:<12}{row['seed']:>7}{str(row['action']):>13}"
            f"{row['score']:>10.3f}{row['elapsed_ms']:>14.2f}"
            f"{row['nodes']:>10}{row['simulations']:>10}"
            f"{row['simulations_per_second']:>12.1f}"
        )

    slowest = min(rows, key=lambda row: row["simulations_per_second"])
    fastest = max(rows, key=lambda row: row["simulations_per_second"])
    print(
        "Bottleneck quan sát: throughput end-to-end thấp nhất ở "
        f"{slowest['profile']} ({slowest['simulations_per_second']:.1f} sims/s); "
        f"cao nhất {fastest['simulations_per_second']:.1f} sims/s. "
        "Script này đo toàn vòng MCTS; cần profiler nếu muốn tách clone, step, "
        "legal_actions và rollout."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--scenario", default="midgame_mixed")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--repeats", type=int, default=1)
    args = parser.parse_args()
    if args.repeats <= 0:
        parser.error("--repeats must be positive")
    if args.seed is not None and args.seed < 0:
        parser.error("--seed must be non-negative")
    return args


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    config = load_config(args.config)
    scenario = find_scenario(config, args.scenario)
    seed = config["seeds"][0] if args.seed is None else args.seed
    budgets = config["profiles"]["MCTS-S"]["budgets"]
    rows = [
        run_profile(
            scenario=scenario,
            budget_data=budget_data,
            seed=seed,
            repeats=args.repeats,
        )
        for budget_data in budgets
    ]
    print_report(rows, scenario_id=args.scenario, repeats=args.repeats)


if __name__ == "__main__":
    main()
