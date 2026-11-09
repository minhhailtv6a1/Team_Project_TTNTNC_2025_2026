"""Generate a resumable self-play run in independent process shards."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.utils.logger import write_manifest  # noqa: E402
from scripts.generate_selfplay import (  # noqa: E402
    _hardware_info,
    load_selfplay_config,
    run_selfplay,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def partition_even(total: int, workers: int, *, offset: int = 0) -> list[int]:
    """Split an even game count into positive even, near-equal chunks."""

    if total < 2 or total % 2:
        raise ValueError("total must be an even integer >= 2")
    if workers <= 0 or total < 2 * workers:
        raise ValueError("workers must be positive and each shard needs >= 2 games")
    pairs, remainder = divmod(total // 2, workers)
    counts = [2 * pairs] * workers
    for index in range(remainder):
        counts[(offset + index) % workers] += 2
    return counts


def shard_game_counts(pair_games: list[int], workers: int) -> list[list[int]]:
    """Return per-worker counts while preserving every pair total exactly."""

    columns = [
        partition_even(total, workers, offset=(pair_index * 3) % workers)
        for pair_index, total in enumerate(pair_games)
    ]
    return [[column[index] for column in columns] for index in range(workers)]


def _run_part(config: dict[str, Any], output: str) -> str:
    output_path = Path(output)
    existing = output_path / "run_manifest.json"
    if existing.is_file():
        manifest = json.loads(existing.read_text(encoding="utf-8"))
        if (
            manifest.get("run_id") != config["run_id"]
            or manifest.get("pair_games") != config["_games_by_pair"]
            or manifest.get("successful_games") != sum(config["_games_by_pair"])
        ):
            raise RuntimeError(f"incompatible existing shard: {output_path}")
        return str(existing)
    return str(run_selfplay(config, output_path))


def run_sharded(config_path: Path, output: Path, workers: int) -> Path:
    config = load_selfplay_config(config_path)
    original_counts = list(config["_games_by_pair"])
    counts_by_worker = shard_game_counts(original_counts, workers)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "run_manifest.json").exists():
        raise RuntimeError(f"completed output already exists: {output}")

    part_jobs: list[tuple[dict[str, Any], Path]] = []
    for index, counts in enumerate(counts_by_worker):
        part_config = dict(config)
        part_config["run_id"] = f"{config['run_id']}-part{index:03d}"
        part_config["base_seed"] = int(config["base_seed"]) + index * 10_000
        part_config["pair_games"] = counts
        part_config["_games_by_pair"] = counts
        part_jobs.append((part_config, output / f"part_{index:03d}"))

    manifests: list[Path] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_run_part, part_config, str(part_output)): index
            for index, (part_config, part_output) in enumerate(part_jobs)
        }
        for future in as_completed(futures):
            index = futures[future]
            path = Path(future.result())
            manifests.append(path)
            print(f"part {index + 1}/{workers} complete -> {path}", flush=True)

    part_data = [json.loads(path.read_text(encoding="utf-8")) for path in manifests]
    shards: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    for manifest_path, manifest in sorted(zip(manifests, part_data), key=lambda item: str(item[0])):
        relative_dir = manifest_path.parent.relative_to(output)
        for shard in manifest["shards"]:
            shard_path = manifest_path.parent / shard["path"]
            if _sha256(shard_path) != shard["sha256"]:
                raise RuntimeError(f"checksum mismatch after shard generation: {shard_path}")
            shards.append(
                {
                    "path": (relative_dir / shard["path"]).as_posix(),
                    "games": shard["games"],
                    "sha256": shard["sha256"],
                }
            )
        violations.extend(manifest.get("budget_violations", []))

    persisted_config = {key: value for key, value in config.items() if not key.startswith("_")}
    config_snapshot = output / "selfplay_config.json"
    config_snapshot.write_text(
        json.dumps(persisted_config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    total_games = sum(original_counts)
    successful = sum(int(part["successful_games"]) for part in part_data)
    if successful != total_games or sum(int(item["games"]) for item in shards) != total_games:
        raise RuntimeError("sharded game count mismatch")

    manifest = {
        "schema_name": "caro-w56-raw-v1",
        "run_id": config["run_id"],
        "game_config": persisted_config["game_config"],
        "base_seed": config["base_seed"],
        "pairs": persisted_config["pairs"],
        "pair_games": original_counts,
        "agents": persisted_config["agents"],
        "requested_games": total_games,
        "successful_games": successful,
        "failed_games": 0,
        "shards": shards,
        "config": {"path": config_snapshot.name, "sha256": _sha256(config_snapshot)},
        "budget_violations": violations,
        "hardware": _hardware_info(),
        "generation": {
            "mode": "process_sharded",
            "workers": workers,
            "part_game_counts": counts_by_worker,
        },
    }
    return write_manifest(output / "run_manifest.json", manifest)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args(argv)
    if args.workers <= 0:
        parser.error("--workers must be positive")
    manifest = run_sharded(args.config, args.output, args.workers)
    print(f"manifest -> {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
