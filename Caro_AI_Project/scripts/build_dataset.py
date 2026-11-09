"""Build a reproducible policy-learning dataset from self-play JSONL."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.ml.data_pipeline import RawDataError, build_dataset, sha256_file
from core.utils.logger import write_manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build dataset-v1 from validated self-play JSONL")
    parser.add_argument("--input", required=True, help="Raw directory containing run_manifest.json")
    parser.add_argument("--output", required=True, help="Directory for NPZ and metadata artifacts")
    parser.add_argument("--config", default="configs/train_w56.json")
    args = parser.parse_args(argv)
    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
        manifest = build_dataset(args.input, args.output, config)
        manifest["config"] = {"path": Path(args.config).name, "sha256": sha256_file(args.config)}
        path = write_manifest(Path(args.output) / "dataset_manifest.json", manifest)
    except (OSError, ValueError, RawDataError) as exc:
        parser.error(str(exc))
    print(f"dataset manifest -> {path}")
    for split, artifact in manifest["artifacts"].items():
        print(f"{split}: {artifact['samples']} samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
