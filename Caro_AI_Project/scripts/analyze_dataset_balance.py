"""Measure game, teacher-source and policy-target balance for an exported dataset."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import sys
from typing import Any, Sequence

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.interfaces import Player  # noqa: E402
from core.ml.data_pipeline import iter_raw_games, load_dataset_split  # noqa: E402


def _pair_key(left: str, right: str) -> str:
    return "-vs-".join(sorted((left, right)))


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def analyze_raw(raw_dir: Path) -> dict[str, Any]:
    manifest = json.loads((raw_dir / "run_manifest.json").read_text(encoding="utf-8"))
    agents: dict[str, Counter[str]] = defaultdict(Counter)
    pairs: dict[str, Counter[str]] = defaultdict(Counter)
    total_games = 0
    total_moves = 0
    for shard in manifest["shards"]:
        for record in iter_raw_games(raw_dir / shard["path"]):
            total_games += 1
            total_moves += len(record.moves)
            left, right = record.x_agent, record.o_agent
            pair = pairs[_pair_key(left, right)]
            pair["games"] += 1
            agents[left]["games"] += 1
            agents[left]["as_x"] += 1
            agents[right]["games"] += 1
            agents[right]["as_o"] += 1
            if record.winner is None:
                pair["draws"] += 1
                agents[left]["draws"] += 1
                agents[right]["draws"] += 1
            else:
                winner = left if record.winner == Player.X else right
                loser = right if winner == left else left
                pair[f"wins_{winner}"] += 1
                agents[winner]["wins"] += 1
                agents[loser]["losses"] += 1
            for move in record.moves:
                source = left if move.player == Player.X else right
                agents[source]["move_labels"] += 1

    agent_report: dict[str, Any] = {}
    for name, stats in sorted(agents.items()):
        games = stats["games"]
        labels = stats["move_labels"]
        agent_report[name] = {
            **dict(stats),
            "win_rate": _rate(stats["wins"], games),
            "score_rate": _rate(stats["wins"] + 0.5 * stats["draws"], games),
            "move_label_fraction": _rate(labels, total_moves),
        }
    return {
        "games": total_games,
        "moves": total_moves,
        "average_moves_per_game": _rate(total_moves, total_games),
        "pair_stats": {name: dict(stats) for name, stats in sorted(pairs.items())},
        "agent_stats": agent_report,
        "manifest_budget_violations": manifest.get("budget_violations", []),
    }


def _target_stats(target: np.ndarray, board_size: int) -> dict[str, Any]:
    counts = np.bincount(target, minlength=board_size * board_size)
    probabilities = counts[counts > 0] / counts.sum()
    entropy = float(-(probabilities * np.log(probabilities)).sum())
    normalized_entropy = entropy / math.log(board_size * board_size)
    order = np.argsort(counts)[::-1][:10]
    return {
        "covered_classes": int(np.count_nonzero(counts)),
        "total_classes": int(len(counts)),
        "normalized_entropy": normalized_entropy,
        "max_class_fraction": float(counts.max() / counts.sum()),
        "max_to_mean_ratio": float(counts.max() / counts.mean()),
        "top_targets": [
            {
                "action": [int(index // board_size), int(index % board_size)],
                "count": int(counts[index]),
                "fraction": float(counts[index] / counts.sum()),
            }
            for index in order
        ],
    }


def analyze_processed(dataset_dir: Path) -> dict[str, Any]:
    manifest = json.loads((dataset_dir / "dataset_manifest.json").read_text(encoding="utf-8"))
    board_size = int(manifest["board_size"])
    splits: dict[str, Any] = {}
    for split in ("train", "val", "test"):
        arrays = load_dataset_split(dataset_dir, split, verify_checksum=True)
        metadata_path = dataset_dir / manifest["artifacts"][split]["metadata"]
        sources: Counter[str] = Counter()
        with metadata_path.open(encoding="utf-8") as stream:
            for line in stream:
                sources[json.loads(line)["source_agent"]] += 1
        sample_count = len(arrays["target"])
        splits[split] = {
            "samples": sample_count,
            "source_agent_counts": dict(sorted(sources.items())),
            "source_agent_fractions": {
                name: count / sample_count for name, count in sorted(sources.items())
            },
            "target_distribution": _target_stats(arrays["target"], board_size),
            "checksum_and_tensor_contract_valid": True,
        }
        del arrays
    return {
        "dataset_version": manifest["dataset_version"],
        "split_games": manifest["validation"]["games"],
        "duplicates_removed": manifest["validation"]["duplicates_removed"],
        "train_d4_augmentation": manifest["train_d4_augmentation"],
        "splits": splits,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    args = parser.parse_args(argv)
    report = {
        "raw": analyze_raw(args.raw),
        "processed": analyze_processed(args.dataset),
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"balance report -> {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
