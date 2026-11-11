"""Run the frozen Week-7 five-agent Caro round-robin.

The script is the sole producer of W78 raw logs.  It balances sides in paired
seeds, appends safely after interruption, and never reruns an existing game ID.
Use a small ``--games-per-pair`` only for pilots; the frozen config requires
100 games per unordered pair and profile for the official results-v1 run.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.agents.heuristic_ai import HeuristicAgent
from core.agents.mcts_ai import MCTSAgent
from core.agents.minimax_ai import MinimaxAgent
from core.agents.neural_ai import NeuralAgent
from core.agents.random_ai import RandomAgent
from core.engine.game_env import CaroEnv
from core.engine.interfaces import GameConfig, SearchBudget
from core.utils.logger import GameLogger, read_games, write_manifest
from core.utils.tournament_runner import BudgetEnforcer, Participant, derive_seed, play_game

AGENT_NAMES = ("random", "heuristic", "minimax", "mcts", "neural")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def hardware_snapshot() -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "cpu_count": os.cpu_count(),
    }
    try:
        import psutil
        snapshot["process_rss_bytes"] = psutil.Process().memory_info().rss
    except ImportError:
        snapshot["process_rss_bytes"] = None
    try:
        import torch
        snapshot["cuda_available"] = bool(torch.cuda.is_available())
        snapshot["cuda_allocated_bytes"] = int(torch.cuda.memory_allocated()) if torch.cuda.is_available() else 0
    except ImportError:
        snapshot["cuda_available"] = False
        snapshot["cuda_allocated_bytes"] = None
    return snapshot


def load_w78_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("schema") != "caro-w78-tournament-v1":
        raise ValueError("unsupported W78 tournament config schema")
    if config.get("contract_version") != "caro-v2":
        raise ValueError("tournament config must use caro-v2")
    if tuple(config.get("agents", {})) != AGENT_NAMES:
        raise ValueError(f"agents must be exactly {AGENT_NAMES}")
    GameConfig(**config["game_config"])
    games = config.get("games_per_pair")
    if not isinstance(games, int) or games < 100 or games % 2:
        raise ValueError("games_per_pair must be an even integer >= 100")
    for profile, item in config.get("profiles", {}).items():
        if set(item.get("budgets", {})) != set(AGENT_NAMES):
            raise ValueError(f"{profile}: budgets must name all five agents")
    return config


def make_agent(label: str, spec: Mapping[str, Any], checkpoint: Path) -> object:
    options = dict(spec.get("options", {}))
    kind = spec["kind"]
    if kind == "random":
        return RandomAgent(name=label, **options)
    if kind == "heuristic":
        return HeuristicAgent(name=label, **options)
    if kind == "minimax":
        return MinimaxAgent(name=label, **options)
    if kind == "mcts":
        return MCTSAgent(name=label, **options)
    if kind == "neural":
        return NeuralAgent(checkpoint, name=label, **options)
    raise ValueError(f"unknown agent kind: {kind!r}")


def build_participants(config: Mapping[str, Any], profile: str, checkpoint: Path) -> dict[str, Participant]:
    budget_map = config["profiles"][profile]["budgets"]
    participants: dict[str, Participant] = {}
    for label, spec in config["agents"].items():
        participants[label] = Participant(
            label, make_agent(label, spec, checkpoint), SearchBudget(**budget_map[label])
        )
    return participants


def planned_games(profile: str, labels: Iterable[str], games_per_pair: int, base_seed: int) -> list[tuple[str, str, str, int]]:
    """Return ``(game_id, x_label, o_label, paired_seed)`` in canonical order."""
    names = list(labels)
    if games_per_pair < 2 or games_per_pair % 2:
        raise ValueError("games_per_pair must be even and >= 2 for side balancing")
    schedule: list[tuple[str, str, str, int]] = []
    pair_index = 0
    for first_index, a in enumerate(names):
        for b in names[first_index + 1:]:
            for game_index in range(games_per_pair):
                seed_index = game_index // 2
                seed = derive_seed(base_seed, pair_index, seed_index)
                x, o = (a, b) if game_index % 2 == 0 else (b, a)
                game_id = f"w78-{profile.lower()}-p{pair_index:02d}-g{game_index:03d}-{x}-vs-{o}"
                schedule.append((game_id, x, o, seed))
            pair_index += 1
    return schedule


def existing_ids(path: Path) -> set[str]:
    return {record.game_id for record in read_games(path)} if path.is_file() else set()


def run_profile(
    config: Mapping[str, Any], *, profile: str, out_root: Path,
    games_per_pair: int, checkpoint: Path, config_sha256: str,
) -> dict[str, Any]:
    if profile not in config["profiles"]:
        raise ValueError(f"unknown profile {profile!r}")
    profile_dir = out_root / profile.lower()
    raw_path = profile_dir / "games.jsonl"
    violations_path = profile_dir / "violations.jsonl"
    known_ids = existing_ids(raw_path)
    schedule = planned_games(profile, AGENT_NAMES, games_per_pair, int(config["base_seed"]))
    expected_ids = {item[0] for item in schedule}
    unexpected = known_ids - expected_ids
    if unexpected:
        raise ValueError(f"{raw_path} contains game ids from another schedule, e.g. {sorted(unexpected)[0]}")

    participants = build_participants(config, profile, checkpoint)
    cfg = GameConfig(**config["game_config"])
    enforce = config["budget_enforcer"]
    enforcer = BudgetEnforcer(tolerance_ms=float(enforce["tolerance_ms"]), fail_fast=False)
    added = 0
    with GameLogger(raw_path, mode="a", fsync=True) as logger, violations_path.open("a", encoding="utf-8", newline="\n") as violation_file:
        for game_id, x_label, o_label, seed in schedule:
            if game_id in known_ids:
                continue
            outcome = play_game(
                lambda: CaroEnv(cfg), participants[x_label], participants[o_label],
                game_id=game_id, seed=seed, enforcer=enforcer, logger=logger,
            )
            for violation in outcome.violations:
                violation_file.write(json.dumps(asdict(violation), ensure_ascii=False) + "\n")
            violation_file.flush()
            added += 1
            if added % 10 == 0:
                print(f"{profile}: appended {added} game(s)", flush=True)

    finished_ids = existing_ids(raw_path)
    complete = finished_ids == expected_ids
    violation_count = (
        sum(1 for line in violations_path.open(encoding="utf-8") if line.strip())
        if violations_path.is_file() else 0
    )
    manifest = {
        "schema": "caro-w78-results-manifest-v1",
        "profile": profile,
        "status": "complete" if complete else "partial",
        "commit_sha": git_sha(),
        "config_path": str(Path("configs") / "tournament_w78.json"),
        "config_sha256": config_sha256,
        "checkpoint": str(checkpoint.relative_to(PROJECT_ROOT)),
        "checkpoint_sha256": sha256_file(checkpoint),
        "raw_log": raw_path.name,
        "raw_log_sha256": sha256_file(raw_path),
        "violations_log": violations_path.name,
        "games_per_pair": games_per_pair,
        "expected_games": len(schedule),
        "completed_games": len(finished_ids),
        "side_balanced": True,
        "base_seed": config["base_seed"],
        "hardware": hardware_snapshot(),
        "budget_violations": violation_count,
    }
    write_manifest(profile_dir / "manifest.json", manifest)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "configs/tournament_w78.json")
    parser.add_argument("--results-dir", type=Path, default=PROJECT_ROOT / "results/w78")
    parser.add_argument("--profile", choices=("DEFAULT", "FAIR", "ALL"), default="ALL")
    parser.add_argument("--games-per-pair", type=int, help="Even pilot override; official config uses 100")
    parser.add_argument("--checkpoint", type=Path, help="Optional checkpoint override")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config_path = args.config.resolve()
    config = load_w78_config(config_path)
    games = args.games_per_pair or int(config["games_per_pair"])
    if games < 2 or games % 2:
        raise ValueError("--games-per-pair must be an even integer >= 2")
    checkpoint = (args.checkpoint or (PROJECT_ROOT / config["checkpoint"])).resolve()
    if not checkpoint.is_file():
        raise FileNotFoundError(f"Neural checkpoint not found: {checkpoint}")
    profiles = tuple(config["profiles"]) if args.profile == "ALL" else (args.profile,)
    config_sha = sha256_file(config_path)
    for profile in profiles:
        manifest = run_profile(config, profile=profile, out_root=args.results_dir,
                               games_per_pair=games, checkpoint=checkpoint, config_sha256=config_sha)
        print(f"{profile}: {manifest['completed_games']}/{manifest['expected_games']} games; status={manifest['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
