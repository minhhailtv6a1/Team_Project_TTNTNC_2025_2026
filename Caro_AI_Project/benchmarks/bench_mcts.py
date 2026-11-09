"""Smoke benchmark MCTS cho profile W34 100/400/1000 simulations.

Chạy từ repo:

    .\\myenv\\Scripts\\python.exe benchmarks\\bench_mcts.py

Benchmark không đặt ngưỡng pass/fail theo thời gian vì latency phụ thuộc máy.
Correctness và counter được kiểm tra trong ``tests/test_mcts_ai.py``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import platform
import statistics
import sys
import time
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
    agent_options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decisions: list[AgentDecision] = []
    search_stats: list[dict[str, Any]] = []
    budget = make_budget(budget_data, seed)
    for _ in range(repeats):
        env = build_env(scenario["actions"])
        agent = MCTSAgent(**(agent_options or {}))
        decision = agent.choose_action(env, budget)
        if decision.action not in env.legal_actions():
            raise RuntimeError(f"MCTS returned illegal action {decision.action!r}")
        decisions.append(decision)
        search_stats.append(agent.last_search_stats)

    logical = {
        (d.action, d.score, d.nodes, d.simulations)
        for d in decisions
    }
    if len(logical) != 1:
        raise RuntimeError("same scenario, seed and budget produced different logical results")

    first = decisions[0]
    elapsed_ms = statistics.median(d.elapsed_ms for d in decisions)
    ordered_elapsed = sorted(d.elapsed_ms for d in decisions)
    p95_elapsed_ms = ordered_elapsed[max(0, math.ceil(0.95 * len(ordered_elapsed)) - 1)]
    throughput = (
        first.simulations / (elapsed_ms / 1000.0)
        if elapsed_ms > 0.0
        else float("inf")
    )
    first_stats = search_stats[0]
    timing_keys = ("clone", "selection", "expansion", "rollout")
    timing_ms = {
        key: statistics.median(
            float(stats.get("timing_ms", {}).get(key, 0.0)) for stats in search_stats
        )
        for key in timing_keys
    }
    return {
        "profile": budget_data.get("label", "mcts"),
        "seed": seed,
        "action": first.action,
        "score": first.score,
        "elapsed_ms": elapsed_ms,
        "p95_elapsed_ms": p95_elapsed_ms,
        "nodes": first.nodes,
        "simulations": first.simulations,
        "simulations_per_second": throughput,
        "root_children": int(first_stats.get("root_children", 0)),
        "root_max_visits": int(first_stats.get("root_max_visits", 0)),
        "root_mean_visits": float(first_stats.get("root_mean_visits", 0.0)),
        "mean_tree_depth": float(first_stats.get("mean_tree_depth", 0.0)),
        "max_tree_depth": int(first_stats.get("max_tree_depth", 0)),
        "timing_ms": timing_ms,
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
        f"{'elapsed ms':>14}{'p95 ms':>11}{'nodes':>9}{'sims':>8}"
        f"{'children':>10}{'max-v':>8}{'depth':>7}{'sims/s':>11}"
    )
    for row in rows:
        print(
            f"{row['profile']:<12}{row['seed']:>7}{str(row['action']):>13}"
            f"{row['score']:>10.3f}{row['elapsed_ms']:>14.2f}"
            f"{row['p95_elapsed_ms']:>11.2f}{row['nodes']:>9}"
            f"{row['simulations']:>8}{row['root_children']:>10}"
            f"{row['root_max_visits']:>8}{row['max_tree_depth']:>7}"
            f"{row['simulations_per_second']:>11.1f}"
        )
        timing = row["timing_ms"]
        print(
            " " * 4
            + "timing ms: "
            + ", ".join(f"{key}={value:.2f}" for key, value in timing.items())
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
    parser.add_argument("--profile", default="MCTS-S")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--json", type=Path)
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
    try:
        profile = config["profiles"][args.profile]
    except KeyError as exc:
        known = ", ".join(sorted(config["profiles"]))
        raise ValueError(f"unknown profile {args.profile!r}; choose one of: {known}") from exc
    budgets = profile["budgets"]
    agent_options = dict(profile.get("agent_options", {}))
    rows = [
        run_profile(
            scenario=scenario,
            budget_data=budget_data,
            seed=seed,
            repeats=args.repeats,
            agent_options=agent_options,
        )
        for budget_data in budgets
    ]
    print_report(rows, scenario_id=args.scenario, repeats=args.repeats)
    if args.json is not None:
        payload = {
            "contract_version": config["contract_version"],
            "benchmark_profile": args.profile,
            "scenario": args.scenario,
            "seed": seed,
            "repeats": args.repeats,
            "agent_options": agent_options,
            "hardware": {
                "python": platform.python_version(),
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "cpu_count": os.cpu_count(),
            },
            "generated_unix_time": time.time(),
            "rows": rows,
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
