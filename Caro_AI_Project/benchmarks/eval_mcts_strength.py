"""Paired-seed, side-swapped strength evaluation for upgraded MCTS profiles."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.agents.heuristic_ai import HeuristicAgent  # noqa: E402
from core.agents.mcts_ai import MCTSAgent  # noqa: E402
from core.agents.minimax_ai import MinimaxAgent  # noqa: E402
from core.engine.game_env import CaroEnv  # noqa: E402
from core.engine.interfaces import GameConfig, SearchBudget  # noqa: E402
from core.utils.tournament_runner import (  # noqa: E402
    BudgetEnforcer,
    Participant,
    run_match,
    summarize_outcomes,
)

DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "benchmark_mcts_v2.json"


def load_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("contract_version") != "caro-v2":
        raise ValueError("strength config must use contract_version='caro-v2'")
    return data


def game_counts(total_games: int, groups: int) -> list[int]:
    """Distribute an even game count as evenly as possible in side-swapped pairs."""

    if total_games < 2 or total_games % 2:
        raise ValueError("games must be an even integer >= 2")
    pairs, remainder = divmod(total_games // 2, groups)
    return [2 * (pairs + (1 if index < remainder else 0)) for index in range(groups)]


def make_opponent(name: str) -> Participant:
    if name == "legacy-mcts-20":
        return Participant(
            name,
            MCTSAgent(name=name),
            SearchBudget(simulations=20),
        )
    if name == "heuristic":
        return Participant(name, HeuristicAgent(name=name))
    if name == "minimax-d2":
        return Participant(
            name,
            MinimaxAgent(name=name, alpha_beta=True, default_depth=2),
            SearchBudget(max_depth=2),
        )
    raise ValueError(f"unknown opponent {name!r}")


def score_rate(stats: dict[str, Any]) -> float:
    games = int(stats["games"])
    return (int(stats["wins"]) + 0.5 * int(stats["draws"])) / games


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    config = load_config(args.config)
    try:
        profile = config["profiles"][args.profile]
    except KeyError as exc:
        known = ", ".join(sorted(config["profiles"]))
        raise ValueError(f"unknown profile {args.profile!r}; choose one of: {known}") from exc
    options = dict(profile.get("agent_options", {}))
    candidate = Participant(
        f"mcts@{args.profile}-{args.simulations}",
        MCTSAgent(name=f"mcts@{args.profile}", **options),
        SearchBudget(simulations=args.simulations),
    )
    opponent = make_opponent(args.opponent)
    game_config = GameConfig(**config["game_config"])
    enforcer = BudgetEnforcer(tolerance_ms=50.0, fail_fast=False)
    outcomes = []
    started = time.perf_counter()
    counts = game_counts(args.games, len(args.seed_groups))
    for group_index, (base_seed, count) in enumerate(zip(args.seed_groups, counts, strict=True)):
        outcomes.extend(
            run_match(
                lambda: CaroEnv(game_config),
                candidate,
                opponent,
                games=count,
                base_seed=base_seed,
                pair_index=group_index,
                swap_sides=True,
                enforcer=enforcer,
                game_id_prefix=f"strength-{args.profile}-{args.opponent}",
            )
        )
    elapsed = time.perf_counter() - started
    summary = summarize_outcomes(outcomes)
    candidate_stats = summary[candidate.label]
    candidate_stats["overall"]["score_rate"] = score_rate(candidate_stats["overall"])
    candidate_stats["as_x"]["score_rate"] = score_rate(candidate_stats["as_x"])
    candidate_stats["as_o"]["score_rate"] = score_rate(candidate_stats["as_o"])
    side_difference = abs(
        candidate_stats["as_x"]["score_rate"]
        - candidate_stats["as_o"]["score_rate"]
    )
    violations = [
        {
            "agent": violation.agent,
            "ply": violation.ply,
            "kind": violation.kind,
            "observed": violation.observed,
            "limit": violation.limit,
        }
        for outcome in outcomes
        for violation in outcome.violations
    ]
    return {
        "contract_version": config["contract_version"],
        "benchmark_version": config.get("benchmark_version"),
        "profile": args.profile,
        "agent_options": options,
        "simulations": args.simulations,
        "opponent": args.opponent,
        "games": args.games,
        "seed_groups": args.seed_groups,
        "games_by_seed_group": counts,
        "swap_sides": True,
        "candidate": candidate_stats,
        "side_score_rate_difference": side_difference,
        "opponent_summary": summary[opponent.label],
        "budget_violations": violations,
        "elapsed_seconds": elapsed,
        "hardware": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
        },
        "config_path": str(args.config),
    }


def print_result(result: dict[str, Any]) -> None:
    stats = result["candidate"]
    overall = stats["overall"]
    print(
        f"profile={result['profile']} sims={result['simulations']} "
        f"opponent={result['opponent']} games={result['games']}"
    )
    print(
        f"W/D/L={overall['wins']}/{overall['draws']}/{overall['losses']} "
        f"score_rate={overall['score_rate']:.3f} "
        f"as_x={stats['as_x']['score_rate']:.3f} "
        f"as_o={stats['as_o']['score_rate']:.3f} "
        f"side_diff={result['side_score_rate_difference']:.3f}"
    )
    print(
        f"mean_move_ms={overall['mean_move_ms']:.2f} "
        f"p95_move_ms={overall['p95_move_ms']:.2f} "
        f"total_simulations={overall['total_simulations']} "
        f"violations={len(result['budget_violations'])} "
        f"elapsed_s={result['elapsed_seconds']:.2f}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--simulations", type=int, required=True)
    parser.add_argument(
        "--opponent",
        choices=("legacy-mcts-20", "heuristic", "minimax-d2"),
        required=True,
    )
    parser.add_argument("--games", type=int, default=12)
    parser.add_argument("--seed-groups", type=int, nargs="+", default=[11, 22, 33])
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    if args.simulations <= 0:
        parser.error("--simulations must be positive")
    if args.games < 2 or args.games % 2:
        parser.error("--games must be an even integer >= 2")
    if not args.seed_groups or any(seed < 0 for seed in args.seed_groups):
        parser.error("--seed-groups must contain non-negative integers")
    return args


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    result = evaluate(args)
    print_result(result)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
