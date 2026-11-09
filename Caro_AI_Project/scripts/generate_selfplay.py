"""Generate three-agent self-play data from a versioned JSON config.

The default config runs every unordered pairing of Heuristic, Minimax and
MCTS.  Each pair may have its own even game count, while sides are swapped
every game. The pilot config produces 60 games; the dataset-v1 config produces
2,000 games.
It delegates gameplay, agent checks and JSONL serialization to the public
tournament runner/logger rather than copying a game loop into this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.game_env import CaroEnv
from core.engine.interfaces import CONTRACT_VERSION, GameConfig
from core.ml.data_pipeline import replay_raw_game
from core.utils.logger import GameLogger, write_manifest
from core.utils.tournament_runner import (
    BudgetEnforcer,
    Participant,
    budget_from_dict,
    load_factory,
    run_match,
)

DEFAULT_CONFIG = "configs/selfplay_w56.json"
DEFAULT_OUTPUT = "data/raw_logs/w56_selfplay_pilot"
REQUIRED_AGENTS = frozenset({"heuristic", "minimax", "mcts"})


class SelfPlayConfigError(ValueError):
    """The self-play configuration is incomplete or would be unreproducible."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SelfPlayConfigError(f"{field} must be an object")
    return value


def load_selfplay_config(path: str | Path) -> dict[str, Any]:
    """Load and validate a balanced three-agent self-play configuration."""
    config_path = Path(path)
    with config_path.open(encoding="utf-8") as stream:
        data: object = json.load(stream)
    config = dict(_require_mapping(data, "config"))

    if config.get("contract_version") != CONTRACT_VERSION:
        raise SelfPlayConfigError(
            f"contract_version must be {CONTRACT_VERSION!r}, "
            f"got {config.get('contract_version')!r}"
        )
    run_id = config.get("run_id")
    if not isinstance(run_id, str) or not run_id or any(char in run_id for char in "\\/ "):
        raise SelfPlayConfigError("run_id must be a non-empty path-safe string")
    try:
        GameConfig(**dict(_require_mapping(config.get("game_config"), "game_config")))
    except ValueError as exc:
        raise SelfPlayConfigError(f"invalid game_config: {exc}") from exc

    base_seed = config.get("base_seed")
    if isinstance(base_seed, bool) or not isinstance(base_seed, int) or base_seed < 0:
        raise SelfPlayConfigError("base_seed must be a non-negative integer")
    if config.get("swap_sides") is not True:
        raise SelfPlayConfigError("swap_sides must be true for balanced X/O data")

    agents = _require_mapping(config.get("agents"), "agents")
    if set(agents) != REQUIRED_AGENTS:
        raise SelfPlayConfigError(
            "agents must contain exactly heuristic, minimax and mcts"
        )
    for name, spec in agents.items():
        details = _require_mapping(spec, f"agents.{name}")
        if not isinstance(details.get("factory"), str):
            raise SelfPlayConfigError(f"agents.{name}.factory must be a string")
        _require_mapping(details.get("options", {}), f"agents.{name}.options")
        _require_mapping(details.get("budget", {}), f"agents.{name}.budget")

    raw_pairs = config.get("pairs")
    if not isinstance(raw_pairs, list) or len(raw_pairs) != 3:
        raise SelfPlayConfigError("pairs must list the three distinct agent pairings")
    pairs: set[frozenset[str]] = set()
    for pair in raw_pairs:
        if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(x, str) for x in pair):
            raise SelfPlayConfigError("each pair must be a two-element agent-name list")
        if pair[0] == pair[1] or pair[0] not in agents or pair[1] not in agents:
            raise SelfPlayConfigError(f"invalid pair {pair!r}")
        pairs.add(frozenset(pair))
    expected_pairs = {
        frozenset(("heuristic", "minimax")),
        frozenset(("heuristic", "mcts")),
        frozenset(("minimax", "mcts")),
    }
    if pairs != expected_pairs:
        raise SelfPlayConfigError("pairs must cover each unordered pair exactly once")

    games_per_pair = config.get("games_per_pair")
    raw_pair_games = config.get("pair_games")
    if games_per_pair is not None and raw_pair_games is not None:
        raise SelfPlayConfigError("use either games_per_pair or pair_games, not both")
    if games_per_pair is not None:
        if isinstance(games_per_pair, bool) or not isinstance(games_per_pair, int):
            raise SelfPlayConfigError("games_per_pair must be an integer")
        games_by_pair = [games_per_pair] * len(raw_pairs)
    else:
        if not isinstance(raw_pair_games, list) or len(raw_pair_games) != len(raw_pairs):
            raise SelfPlayConfigError("pair_games must contain one count for each pair")
        games_by_pair = raw_pair_games
    if any(isinstance(games, bool) or not isinstance(games, int) or games < 2 or games % 2 for games in games_by_pair):
        raise SelfPlayConfigError("every pair game count must be an even integer >= 2")
    config["_games_by_pair"] = games_by_pair
    return config


def _build_participant(name: str, spec: Mapping[str, Any]) -> Participant:
    factory = load_factory(str(spec["factory"]))
    try:
        agent = factory(**dict(_require_mapping(spec.get("options", {}), "options")))
        budget = budget_from_dict(
            _require_mapping(spec.get("budget", {}), "budget"), seed=None
        )
    except (TypeError, ValueError) as exc:
        raise SelfPlayConfigError(f"cannot create agent {name!r}: {exc}") from exc
    return Participant(name, agent, budget)


def _hardware_info() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python": sys.version.split()[0],
    }


def run_selfplay(config: Mapping[str, Any], output_dir: str | Path) -> Path:
    """Run a config returned by :func:`load_selfplay_config` and return its manifest."""
    config = dict(config)
    if config.get("contract_version") != CONTRACT_VERSION:
        raise SelfPlayConfigError("invalid in-memory self-play config")
    if config.get("swap_sides") is not True:
        raise SelfPlayConfigError("self-play must swap sides")
    games_by_pair = config.get("_games_by_pair")
    if games_by_pair is None:
        games_per_pair = config.get("games_per_pair")
        games_by_pair = [games_per_pair] * len(config.get("pairs", []))
    if not isinstance(games_by_pair, list) or any(
        isinstance(games, bool) or not isinstance(games, int) or games < 2 or games % 2
        for games in games_by_pair
    ):
        raise SelfPlayConfigError("every pair game count must be an even integer >= 2")
    if len(games_by_pair) != len(config.get("pairs", [])):
        raise SelfPlayConfigError("pair game counts do not match pairs")
    total_games = sum(games_by_pair)
    persisted_config = {key: value for key, value in config.items() if not key.startswith("_")}

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    shard_path = output / "shard_000.jsonl"
    config_snapshot = output / "selfplay_config.json"
    config_snapshot.write_text(json.dumps(persisted_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    game_config = GameConfig(**dict(config["game_config"]))
    participants = {
        name: _build_participant(name, _require_mapping(spec, f"agents.{name}"))
        for name, spec in _require_mapping(config["agents"], "agents").items()
    }
    enforcer_cfg = _require_mapping(config.get("budget_enforcer", {}), "budget_enforcer")
    enforcer = BudgetEnforcer(
        tolerance_ms=float(enforcer_cfg.get("tolerance_ms", 50.0)),
        fail_fast=enforcer_cfg.get("mode") == "fail_fast",
    )

    outcomes = []
    with GameLogger(shard_path, mode="w") as logger:
        for pair_index, (left, right) in enumerate(config["pairs"]):
            games = games_by_pair[pair_index]
            pair_outcomes = run_match(
                lambda: CaroEnv(game_config),
                participants[left],
                participants[right],
                games=games,
                base_seed=config["base_seed"],
                pair_index=pair_index,
                swap_sides=True,
                enforcer=enforcer,
                logger=logger,
                game_id_prefix=config["run_id"],
            )
            if sum(record.record.x_agent == left for record in pair_outcomes) != games // 2:
                raise RuntimeError(f"side balance failed for {left} vs {right}")
            if sum(record.record.x_agent == right for record in pair_outcomes) != games // 2:
                raise RuntimeError(f"side balance failed for {left} vs {right}")
            outcomes.extend(pair_outcomes)

    if len(outcomes) != total_games:
        raise RuntimeError(f"self-play wrote {len(outcomes)} games, expected {total_games}")
    game_ids = [outcome.record.game_id for outcome in outcomes]
    if len(set(game_ids)) != len(game_ids):
        raise RuntimeError("pilot produced duplicate game IDs")
    for outcome in outcomes:
        replay_raw_game(outcome.record)

    manifest = {
        "schema_name": "caro-w56-raw-v1",
        "run_id": config["run_id"],
        "game_config": persisted_config["game_config"],
        "base_seed": config["base_seed"],
        "pairs": persisted_config["pairs"],
        "pair_games": games_by_pair,
        "agents": persisted_config["agents"],
        "requested_games": total_games,
        "successful_games": total_games,
        "failed_games": 0,
        "shards": [{"path": shard_path.name, "games": total_games, "sha256": _sha256(shard_path)}],
        "config": {"path": config_snapshot.name, "sha256": _sha256(config_snapshot)},
        "budget_violations": [
            {"agent": item.agent, "ply": item.ply, "kind": item.kind, "observed": item.observed, "limit": item.limit}
            for outcome in outcomes for item in outcome.violations
        ],
        "hardware": _hardware_info(),
    }
    return write_manifest(output / "run_manifest.json", manifest)


# Backward-compatible public name for the 60-game pilot workflow.
run_pilot = run_selfplay


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run versioned three-agent self-play")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    config = load_selfplay_config(args.config)
    manifest = run_selfplay(config, args.output)
    print(f"{sum(config['_games_by_pair'])} self-play games -> {manifest.parent / 'shard_000.jsonl'}")
    print(f"manifest -> {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
