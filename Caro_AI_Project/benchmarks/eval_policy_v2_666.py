"""Paired-seed, side-balanced evaluation of a trained PolicyNet checkpoint."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
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

from core.agents.heuristic_ai import HeuristicAgent  # noqa: E402
from core.agents.mcts_ai import MCTSAgent  # noqa: E402
from core.agents.minimax_ai import MinimaxAgent  # noqa: E402
from core.agents.neural_ai import NeuralAgent  # noqa: E402
from core.engine.game_env import CaroEnv  # noqa: E402
from core.engine.interfaces import GameConfig, Player, SearchBudget  # noqa: E402
from core.utils.tournament_runner import (  # noqa: E402
    BudgetEnforcer,
    Participant,
    derive_seed,
    play_game,
)

OPPONENTS = ("heuristic", "minimax-d2", "mcts-strength8")


def _make_opponent(name: str) -> Participant:
    if name == "heuristic":
        return Participant(name, HeuristicAgent(name=name))
    if name == "minimax-d2":
        return Participant(
            name,
            MinimaxAgent(name=name, alpha_beta=True, default_depth=2),
            SearchBudget(max_depth=2),
        )
    if name == "mcts-strength8":
        return Participant(
            name,
            MCTSAgent(
                name=name,
                default_simulations=8,
                exploration_weight=0.7,
                tactical_precheck=True,
                candidate_policy="heuristic_seeded",
                neighbor_radius=2,
                progressive_widening_c=1.5,
                progressive_widening_alpha=0.5,
                rollout_policy="epsilon_heuristic",
                rollout_epsilon=0.15,
                rollout_horizon=8,
                leaf_evaluation="pattern",
                reuse_simulation_env=True,
            ),
            SearchBudget(simulations=8),
        )
    raise ValueError(f"unknown opponent {name!r}")


def _empty_stats() -> dict[str, Any]:
    return {
        "games": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "as_x": {"games": 0, "wins": 0, "draws": 0, "losses": 0},
        "as_o": {"games": 0, "wins": 0, "draws": 0, "losses": 0},
        "game_plies": [],
        "neural_move_ms": [],
        "opponent_move_ms": [],
        "opponent_nodes": 0,
        "opponent_simulations": 0,
        "budget_violations": [],
    }


def _record_game(
    stats: dict[str, Any],
    outcome: Any,
    *,
    neural_is_x: bool,
) -> None:
    record = outcome.record
    neural_player = Player.X if neural_is_x else Player.O
    side = stats["as_x" if neural_is_x else "as_o"]
    stats["games"] += 1
    side["games"] += 1
    if record.winner is None:
        stats["draws"] += 1
        side["draws"] += 1
    elif record.winner == neural_player:
        stats["wins"] += 1
        side["wins"] += 1
    else:
        stats["losses"] += 1
        side["losses"] += 1
    stats["game_plies"].append(len(record.moves))
    neural_parity = 0 if neural_is_x else 1
    for index, (move, wall_ms) in enumerate(zip(record.moves, outcome.wall_ms, strict=True)):
        if index % 2 == neural_parity:
            stats["neural_move_ms"].append(float(wall_ms))
        else:
            stats["opponent_move_ms"].append(float(wall_ms))
            stats["opponent_nodes"] += int(move.nodes)
            stats["opponent_simulations"] += int(move.simulations)
    stats["budget_violations"].extend(
        {
            "agent": violation.agent,
            "ply": violation.ply,
            "kind": violation.kind,
            "observed": violation.observed,
            "limit": violation.limit,
        }
        for violation in outcome.violations
    )


def _worker(
    worker_id: int,
    checkpoint: str,
    pair_indices: list[int],
    base_seed: int,
) -> dict[str, Any]:
    import torch

    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    neural = Participant(
        "policy-v2-best",
        NeuralAgent(checkpoint, name="policy-v2-best", device="cpu"),
    )
    game_config = GameConfig(board_size=11, win_length=5)
    results: dict[str, Any] = {}
    for opponent_index, opponent_name in enumerate(OPPONENTS):
        opponent = _make_opponent(opponent_name)
        enforcer = BudgetEnforcer(tolerance_ms=50.0, fail_fast=False)
        stats = _empty_stats()
        for local_index, pair_index in enumerate(pair_indices, start=1):
            seed = derive_seed(base_seed, opponent_index, pair_index)
            as_x = play_game(
                lambda: CaroEnv(game_config),
                neural,
                opponent,
                game_id=f"policy-v2-{opponent_name}-seed{pair_index:03d}-nx",
                seed=seed,
                enforcer=enforcer,
            )
            _record_game(stats, as_x, neural_is_x=True)
            as_o = play_game(
                lambda: CaroEnv(game_config),
                opponent,
                neural,
                game_id=f"policy-v2-{opponent_name}-seed{pair_index:03d}-no",
                seed=seed,
                enforcer=enforcer,
            )
            _record_game(stats, as_o, neural_is_x=False)
            if local_index % 5 == 0 or local_index == len(pair_indices):
                print(
                    f"worker={worker_id} opponent={opponent_name} "
                    f"pairs={local_index}/{len(pair_indices)}",
                    flush=True,
                )
        results[opponent_name] = stats
    return results


def _merge_stats(parts: list[dict[str, Any]], opponent: str) -> dict[str, Any]:
    merged = _empty_stats()
    for part in parts:
        stats = part[opponent]
        for key in ("games", "wins", "draws", "losses", "opponent_nodes", "opponent_simulations"):
            merged[key] += stats[key]
        for side_name in ("as_x", "as_o"):
            for key in ("games", "wins", "draws", "losses"):
                merged[side_name][key] += stats[side_name][key]
        for key in ("game_plies", "neural_move_ms", "opponent_move_ms", "budget_violations"):
            merged[key].extend(stats[key])
    return merged


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _finish_stats(stats: dict[str, Any]) -> dict[str, Any]:
    result = dict(stats)
    games = result["games"]
    result["win_rate"] = result["wins"] / games
    result["draw_rate"] = result["draws"] / games
    result["loss_rate"] = result["losses"] / games
    result["score_rate"] = (result["wins"] + 0.5 * result["draws"]) / games
    for side_name in ("as_x", "as_o"):
        side = dict(result[side_name])
        side_games = side["games"]
        side["win_rate"] = side["wins"] / side_games
        side["draw_rate"] = side["draws"] / side_games
        side["loss_rate"] = side["losses"] / side_games
        side["score_rate"] = (side["wins"] + 0.5 * side["draws"]) / side_games
        result[side_name] = side
    result["mean_game_plies"] = statistics.fmean(result.pop("game_plies"))
    neural_times = result.pop("neural_move_ms")
    opponent_times = result.pop("opponent_move_ms")
    result["neural_mean_move_ms"] = statistics.fmean(neural_times)
    result["neural_p95_move_ms"] = _p95(neural_times)
    result["opponent_mean_move_ms"] = statistics.fmean(opponent_times)
    result["opponent_p95_move_ms"] = _p95(opponent_times)
    result["budget_violation_count"] = len(result["budget_violations"])
    return result


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    if args.games < 2 or args.games % 2:
        raise ValueError("games must be an even integer >= 2")
    checkpoint = args.checkpoint.resolve()
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    pair_count = args.games // 2
    worker_count = min(args.workers, pair_count)
    pair_groups = [list(range(worker_id, pair_count, worker_count)) for worker_id in range(worker_count)]
    started = time.perf_counter()
    parts: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(_worker, worker_id, str(checkpoint), group, args.base_seed): worker_id
            for worker_id, group in enumerate(pair_groups)
        }
        for future in as_completed(futures):
            worker_id = futures[future]
            parts.append(future.result())
            print(f"worker {worker_id + 1}/{worker_count} complete", flush=True)
    opponents = {
        opponent: _finish_stats(_merge_stats(parts, opponent))
        for opponent in OPPONENTS
    }
    combined = _empty_stats()
    for opponent in OPPONENTS:
        source = _merge_stats(parts, opponent)
        for key in ("games", "wins", "draws", "losses", "opponent_nodes", "opponent_simulations"):
            combined[key] += source[key]
        for side_name in ("as_x", "as_o"):
            for key in ("games", "wins", "draws", "losses"):
                combined[side_name][key] += source[side_name][key]
        for key in ("game_plies", "neural_move_ms", "opponent_move_ms", "budget_violations"):
            combined[key].extend(source[key])
    return {
        "evaluation": "policy-v2-best-vs-three-teachers",
        "contract_version": "caro-v2",
        "checkpoint": str(checkpoint),
        "games_per_opponent": args.games,
        "total_games": args.games * len(OPPONENTS),
        "paired_seeds_per_opponent": pair_count,
        "base_seed": args.base_seed,
        "swap_sides": True,
        "workers": worker_count,
        "opponent_profiles": {
            "heuristic": {},
            "minimax-d2": {"alpha_beta": True, "max_depth": 2},
            "mcts-strength8": {
                "simulations": 8,
                "exploration_weight": 0.7,
                "tactical_precheck": True,
                "candidate_policy": "heuristic_seeded",
                "rollout_policy": "epsilon_heuristic",
                "rollout_horizon": 8,
                "leaf_evaluation": "pattern",
            },
        },
        "opponents": opponents,
        "combined": _finish_stats(combined),
        "elapsed_seconds": time.perf_counter() - started,
        "hardware": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--games", type=int, default=666)
    parser.add_argument("--base-seed", type=int, default=20261201)
    parser.add_argument("--workers", type=int, default=min(os.cpu_count() or 1, 8))
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args()
    if args.workers <= 0:
        parser.error("--workers must be positive")
    return args


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    result = evaluate(args)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        opponent: {
            "W": stats["wins"],
            "D": stats["draws"],
            "L": stats["losses"],
            "win_rate": stats["win_rate"],
            "score_rate": stats["score_rate"],
        }
        for opponent, stats in result["opponents"].items()
    }, indent=2))
    print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
