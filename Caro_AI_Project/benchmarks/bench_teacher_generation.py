"""Benchmark throughput sinh dữ liệu của teacher Heuristic vs MCTS (W56-M2-01).

Chạy từ repo:

    .\\myenv\\Scripts\\python.exe benchmarks\\bench_teacher_generation.py ^
        --config configs\\teacher_w56.json --games 4 --json reports\\teacher_bench.json

Mục đích: đo thời gian/nước, thời gian/ván, sims/s cho từng profile MCTS ứng viên,
rồi ước lượng thời gian hoàn thành 200 và 300 ván. Không đặt ngưỡng pass/fail theo
thời gian vì latency phụ thuộc máy. Script chỉ dùng runner public, không dùng global RNG.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import statistics
import sys
import time
from importlib import metadata
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.agents.heuristic_ai import HeuristicAgent  # noqa: E402
from core.agents.mcts_ai import MCTSAgent  # noqa: E402
from core.engine.game_env import CaroEnv  # noqa: E402
from core.engine.interfaces import GameConfig, SearchBudget  # noqa: E402
from core.utils.tournament_runner import (  # noqa: E402
    BudgetEnforcer,
    GameOutcome,
    Participant,
    run_match,
)

DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "teacher_w56.json"
TARGET_GAMES = (200, 300)


def load_config(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("contract_version") != "caro-v2":
        raise ValueError("teacher config must use contract_version='caro-v2'")
    if not data.get("candidates"):
        raise ValueError("teacher config needs a non-empty 'candidates' list")
    return data


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for pkg in ("numpy", "pandas", "torch", "tensorboard", "scikit-learn"):
        try:
            versions[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            versions[pkg] = None
    return versions


def percentile95(values: list[float]) -> float:
    ordered = sorted(values)
    import math

    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def logical_signature(outcomes: list[GameOutcome]) -> list[tuple]:
    """Chuỗi action + winner của từng ván, dùng kiểm tra tái lập."""
    return [
        (o.record.game_id, tuple(m.action for m in o.record.moves), o.record.winner)
        for o in outcomes
    ]


def run_candidate(
    candidate: dict[str, Any],
    *,
    game_config: GameConfig,
    games: int,
    base_seed: int,
    check_determinism: bool,
) -> dict[str, Any]:
    label = candidate["label"]
    sims = int(candidate["simulations"])
    options = dict(candidate.get("agent_options", {}))

    def build() -> tuple[Participant, Participant]:
        heuristic = Participant("heuristic", HeuristicAgent(name="heuristic"))
        mcts = Participant(
            f"mcts@{label}",
            MCTSAgent(name=f"mcts@{label}", **options),
            SearchBudget(simulations=sims),
        )
        return heuristic, mcts

    heuristic, mcts = build()
    enforcer = BudgetEnforcer(tolerance_ms=50.0, fail_fast=False)
    started = time.perf_counter()
    outcomes = run_match(
        lambda: CaroEnv(game_config),
        heuristic,
        mcts,
        games=games,
        base_seed=base_seed,
        pair_index=0,
        swap_sides=True,
        enforcer=enforcer,
        game_id_prefix=f"bench-{label}",
    )
    wall_s = time.perf_counter() - started

    game_seconds = [sum(o.wall_ms) / 1000.0 for o in outcomes]
    plies = [len(o.record.moves) for o in outcomes]
    mcts_ms: list[float] = []
    heur_ms: list[float] = []
    total_sims = 0
    for o in outcomes:
        for move, wall in zip(o.record.moves, o.wall_ms, strict=True):
            is_mcts = (
                (move.player.name == "X" and o.record.x_agent == mcts.label)
                or (move.player.name == "O" and o.record.o_agent == mcts.label)
            )
            (mcts_ms if is_mcts else heur_ms).append(wall)
            total_sims += move.simulations

    mean_game_s = statistics.fmean(game_seconds)
    mcts_total_s = sum(mcts_ms) / 1000.0
    result: dict[str, Any] = {
        "label": label,
        "simulations": sims,
        "agent_options": options,
        "games": games,
        "base_seed": base_seed,
        "total_plies": sum(plies),
        "mean_plies_per_game": statistics.fmean(plies),
        "mean_game_seconds": mean_game_s,
        "median_game_seconds": statistics.median(game_seconds),
        "games_per_hour": 3600.0 / mean_game_s if mean_game_s > 0 else float("inf"),
        "mcts_mean_move_ms": statistics.fmean(mcts_ms) if mcts_ms else None,
        "mcts_p95_move_ms": percentile95(mcts_ms) if mcts_ms else None,
        "heuristic_mean_move_ms": statistics.fmean(heur_ms) if heur_ms else None,
        "heuristic_p95_move_ms": percentile95(heur_ms) if heur_ms else None,
        "mcts_simulations_per_second": (
            total_sims / mcts_total_s if mcts_total_s > 0 else None
        ),
        "eta_hours": {
            str(n): n * mean_game_s / 3600.0 for n in TARGET_GAMES
        },
        "winner_counts": {
            "X": sum(1 for o in outcomes if o.record.winner is not None and o.record.winner.name == "X"),
            "O": sum(1 for o in outcomes if o.record.winner is not None and o.record.winner.name == "O"),
            "draw": sum(1 for o in outcomes if o.record.winner is None),
        },
        "budget_violations": len(enforcer.violations),
        "wall_seconds": wall_s,
    }

    if check_determinism:
        heuristic2, mcts2 = build()
        again = run_match(
            lambda: CaroEnv(game_config),
            heuristic2,
            mcts2,
            games=games,
            base_seed=base_seed,
            pair_index=0,
            swap_sides=True,
            game_id_prefix=f"bench-{label}",
        )
        result["deterministic_replay"] = logical_signature(outcomes) == logical_signature(again)
    return result


def print_report(rows: list[dict[str, Any]]) -> None:
    print(
        f"Python {platform.python_version()} | {platform.system()} {platform.release()} "
        f"| {platform.machine()} | CPU={os.cpu_count()}"
    )
    header = (
        f"{'profile':<14}{'sims':>6}{'games':>7}{'plies/g':>9}{'s/game':>9}"
        f"{'mcts ms':>10}{'p95 ms':>9}{'heur ms':>9}{'sims/s':>9}"
        f"{'ETA200 h':>10}{'ETA300 h':>10}{'viol':>6}"
    )
    print(header)
    for r in rows:
        print(
            f"{r['label']:<14}{r['simulations']:>6}{r['games']:>7}"
            f"{r['mean_plies_per_game']:>9.1f}{r['mean_game_seconds']:>9.2f}"
            f"{(r['mcts_mean_move_ms'] or 0):>10.1f}{(r['mcts_p95_move_ms'] or 0):>9.1f}"
            f"{(r['heuristic_mean_move_ms'] or 0):>9.2f}"
            f"{(r['mcts_simulations_per_second'] or 0):>9.0f}"
            f"{r['eta_hours']['200']:>10.2f}{r['eta_hours']['300']:>10.2f}"
            f"{r['budget_violations']:>6}"
        )
        if "deterministic_replay" in r:
            print(f"    deterministic_replay={r['deterministic_replay']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--games", type=int, default=4, help="số ván mỗi profile (chẵn, >=2)")
    parser.add_argument("--seed", type=int, help="base seed; mặc định lấy seeds[0] trong config")
    parser.add_argument("--only", nargs="+", help="chỉ chạy các label ứng viên này")
    parser.add_argument("--no-determinism-check", action="store_true")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    if args.games < 2 or args.games % 2:
        parser.error("--games must be an even integer >= 2")
    if args.seed is not None and args.seed < 0:
        parser.error("--seed must be non-negative")
    return args


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    config = load_config(args.config)
    seed = config["seeds"][0] if args.seed is None else args.seed
    game_config = GameConfig(**config["game_config"])
    candidates = config["candidates"]
    if args.only:
        known = {c["label"] for c in candidates}
        missing = set(args.only) - known
        if missing:
            raise ValueError(f"unknown candidate(s) {sorted(missing)}; known: {sorted(known)}")
        candidates = [c for c in candidates if c["label"] in set(args.only)]

    rows = [
        run_candidate(
            c,
            game_config=game_config,
            games=args.games,
            base_seed=seed,
            check_determinism=not args.no_determinism_check,
        )
        for c in candidates
    ]
    print_report(rows)
    if args.json is not None:
        payload = {
            "contract_version": config["contract_version"],
            "config_path": str(args.config),
            "seed": seed,
            "games_per_profile": args.games,
            "hardware": {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "processor": platform.processor(),
                "cpu_count": os.cpu_count(),
            },
            "package_versions": package_versions(),
            "generated_unix_time": time.time(),
            "rows": rows,
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()