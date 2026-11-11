"""Raw self-play boundary for the Week 5--6 data pipeline.

The raw format deliberately remains the public ``caro-v2`` ``GameRecord``
JSONL format.  A state tensor is *not* written to raw logs: it is recreated
from the empty board by replaying each recorded action.  Keeping that rule in
one module prevents a stale or mismatched board snapshot from becoming a
training label.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from collections import Counter
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from core.engine.game_env import CaroEnv
from core.engine.interfaces import (
    CONTRACT_VERSION,
    GameRecord,
    GameState,
    Player,
    action_to_index,
    legal_action_mask,
)
from core.utils.logger import LogFormatError, read_games, validate_game_record

RAW_SCHEMA_NAME = "caro-w56-raw-v1"
"""Name of the Week 5 raw-data profile layered on top of ``caro-v2``."""


class RawDataError(ValueError):
    """A raw game cannot safely be used to construct training samples."""


def iter_raw_games(path: str | Path) -> Iterator[GameRecord]:
    """Yield validated complete ``GameRecord`` objects from a raw JSONL shard.

    ``read_games`` is the canonical JSON parser and schema validator.  This
    wrapper only gives callers a data-pipeline-specific error type while
    preserving the path/line context supplied by the logger.
    """
    try:
        yield from read_games(path, validate=True)
    except LogFormatError as exc:
        raise RawDataError(f"invalid {RAW_SCHEMA_NAME} record: {exc}") from exc


def replay_raw_game(record: GameRecord) -> CaroEnv:
    """Replay ``record`` and return its terminal environment.

    Besides structural logger validation, replay detects records whose move
    player, action, reward, terminal flag, or winner contradict the engine.
    This is intentionally strict: callers must reject a bad game rather than
    attempting to repair labels or infer a missing state.
    """
    try:
        validate_game_record(record, require_complete=True)
    except LogFormatError as exc:
        raise RawDataError(f"game_id={record.game_id!r}: invalid record: {exc}") from exc

    env = CaroEnv(record.config)
    for move in record.moves:
        state = env.state
        if state.terminated:
            raise RawDataError(
                f"game_id={record.game_id!r}, ply={move.ply}: move after terminal state"
            )
        if move.player != state.current_player:
            raise RawDataError(
                f"game_id={record.game_id!r}, ply={move.ply}: "
                f"expected player {int(state.current_player)}, got {int(move.player)}"
            )
        try:
            result = env.step(move.action)
        except ValueError as exc:
            raise RawDataError(
                f"game_id={record.game_id!r}, ply={move.ply}: invalid action {move.action!r}"
            ) from exc
        if not math.isclose(move.reward, result.reward, rel_tol=0.0, abs_tol=1e-9):
            raise RawDataError(
                f"game_id={record.game_id!r}, ply={move.ply}: "
                f"reward {move.reward!r} disagrees with replay reward {result.reward!r}"
            )

    final = env.state
    if not final.terminated:
        raise RawDataError(f"game_id={record.game_id!r}: replay did not reach terminal state")
    if final.terminated != record.terminated or final.winner != record.winner:
        raise RawDataError(
            f"game_id={record.game_id!r}: replay terminal/winner "
            f"({final.terminated}, {final.winner}) disagrees with record "
            f"({record.terminated}, {record.winner})"
        )
    return env


DATASET_SCHEMA_NAME = "caro-w56-dataset-v1"


@dataclass(frozen=True, slots=True)
class PolicySample:
    """Perspective-normalized state immediately before one labelled action."""

    x: np.ndarray
    legal_mask: np.ndarray
    target: int
    metadata: dict[str, Any]


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def encode_policy_state(
    state: GameState,
    legal_actions: list[tuple[int, int]],
    board_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``[current, opponent, legal]`` float32 planes and bool mask."""
    board = np.asarray(state.board, dtype=np.int8)
    if board.shape != (board_size, board_size):
        raise RawDataError(f"unexpected board shape {board.shape}")
    current = int(state.current_player)
    mask = np.asarray(legal_action_mask(legal_actions, board_size), dtype=bool)
    x = np.empty((3, board_size, board_size), dtype=np.float32)
    x[0] = board == current
    x[1] = board == -current
    x[2] = mask.reshape(board_size, board_size)
    return x, mask


def samples_from_raw_game(record: GameRecord) -> list[PolicySample]:
    """Replay one raw game and materialize a sample before every move."""
    try:
        validate_game_record(record, require_complete=True)
    except LogFormatError as exc:
        raise RawDataError(f"game_id={record.game_id!r}: {exc}") from exc
    env = CaroEnv(record.config)
    samples: list[PolicySample] = []
    for move in record.moves:
        state, legal = env.state, env.legal_actions()
        if state.terminated or move.player != state.current_player or move.action not in legal:
            raise RawDataError(f"game_id={record.game_id!r}, ply={move.ply}: replay mismatch")
        x, mask = encode_policy_state(state, legal, record.config.board_size)
        target = action_to_index(move.action, record.config.board_size)
        if not mask[target]:
            raise RawDataError(f"game_id={record.game_id!r}, ply={move.ply}: illegal target")
        samples.append(PolicySample(
            x=x,
            legal_mask=mask,
            target=target,
            metadata={
                "game_id": record.game_id,
                "ply": move.ply,
                "player": int(move.player),
                "source_agent": record.x_agent if move.player == Player.X else record.o_agent,
                "x_agent": record.x_agent,
                "o_agent": record.o_agent,
                "winner": None if record.winner is None else int(record.winner),
                "seed": record.seed,
            },
        ))
        result = env.step(move.action)
        if not math.isclose(move.reward, result.reward, rel_tol=0.0, abs_tol=1e-9):
            raise RawDataError(f"game_id={record.game_id!r}, ply={move.ply}: reward mismatch")
    if not env.is_terminal() or env.state.winner != record.winner:
        raise RawDataError(f"game_id={record.game_id!r}: terminal/winner mismatch")
    return samples


def split_game_ids(game_ids: Iterable[str], *, seed: int) -> dict[str, list[str]]:
    """Split whole games (never individual states) deterministically 70/15/15."""
    ids = sorted(set(game_ids))
    random.Random(seed).shuffle(ids)
    train_end = int(len(ids) * 0.70)
    val_end = train_end + int(len(ids) * 0.15)
    return {"train": ids[:train_end], "val": ids[train_end:val_end], "test": ids[val_end:]}


def _sample_hash(sample: PolicySample) -> bytes:
    digest = hashlib.sha256()
    digest.update(sample.x.tobytes())
    digest.update(sample.legal_mask.tobytes())
    digest.update(sample.target.to_bytes(8, "little", signed=True))
    return digest.digest()


def deduplicate_splits(
    splits: Mapping[str, list[PolicySample]],
) -> tuple[dict[str, list[PolicySample]], dict[str, int]]:
    """Remove duplicates, preferring train over val over test for leakage safety."""
    seen: set[bytes] = set()
    clean: dict[str, list[PolicySample]] = {}
    removed: dict[str, int] = {}
    for name in ("train", "val", "test"):
        kept: list[PolicySample] = []
        count = 0
        for sample in splits[name]:
            key = _sample_hash(sample)
            if key in seen:
                count += 1
            else:
                seen.add(key)
                kept.append(sample)
        clean[name], removed[name] = kept, count
    return clean, removed


def canonical_d4_state_hash(sample: PolicySample) -> bytes:
    """Return a symmetry-invariant hash for the encoded policy state.

    The target is deliberately excluded.  A board position and every one of
    its rotations/reflections must belong to only one dataset split even when
    different teachers selected different legal actions from that position.
    """

    variants: list[bytes] = []
    for turns in range(4):
        rotated = np.rot90(sample.x, turns, axes=(1, 2))
        for reflected in (False, True):
            transformed = np.flip(rotated, axis=2) if reflected else rotated
            packed = np.packbits(
                np.ascontiguousarray(transformed, dtype=np.float32)
                .astype(bool, copy=False)
                .reshape(-1),
                bitorder="little",
            )
            variants.append(packed.tobytes())
    return hashlib.sha256(min(variants)).digest()


def purge_cross_split_d4_state_overlap(
    splits: Mapping[str, list[PolicySample]],
) -> tuple[dict[str, list[PolicySample]], dict[str, Any]]:
    """Keep each D4 state orbit in only one split.

    Existing game assignments remain unchanged.  When games in multiple
    splits visit symmetry-equivalent states, ownership follows the explicit
    train, validation, test priority and later copies are purged.  Alternative
    teacher targets inside the owning split are retained.
    """

    order = ("train", "val", "test")
    if set(splits) != set(order):
        raise RawDataError("D4 split isolation requires train, val, and test splits")
    owners: dict[bytes, str] = {}
    clean: dict[str, list[PolicySample]] = {}
    removed: dict[str, int] = {}
    unique_orbits: dict[str, int] = {}
    for name in order:
        kept: list[PolicySample] = []
        local_orbits: set[bytes] = set()
        count = 0
        for sample in splits[name]:
            key = canonical_d4_state_hash(sample)
            owner = owners.setdefault(key, name)
            if owner != name:
                count += 1
                continue
            kept.append(sample)
            local_orbits.add(key)
        clean[name] = kept
        removed[name] = count
        unique_orbits[name] = len(local_orbits)
    return clean, {
        "enabled": True,
        "priority": list(order),
        "removed": removed,
        "unique_orbits": unique_orbits,
        "cross_split_d4_state_overlap": 0,
    }


def balance_samples_by_source(
    samples: list[PolicySample],
    *,
    seed: int,
) -> tuple[list[PolicySample], dict[str, Any]]:
    """Deterministically downsample each teacher source to the smallest group."""

    groups: dict[str, list[PolicySample]] = {}
    for sample in samples:
        source = sample.metadata.get("source_agent")
        if not isinstance(source, str) or not source:
            raise RawDataError("source-agent balancing requires source_agent metadata")
        groups.setdefault(source, []).append(sample)
    if not groups:
        raise RawDataError("cannot balance an empty sample list")
    target = min(len(group) for group in groups.values())
    rng = random.Random(seed)
    balanced: list[PolicySample] = []
    before = {name: len(group) for name, group in sorted(groups.items())}
    for name in sorted(groups):
        group = list(groups[name])
        rng.shuffle(group)
        balanced.extend(group[:target])
    rng.shuffle(balanced)
    after = {name: target for name in sorted(groups)}
    return balanced, {
        "enabled": True,
        "before": before,
        "after": after,
        "per_source_target": target,
        "removed": sum(before.values()) - sum(after.values()),
    }


def sample_train_by_source_and_outcome(
    samples: list[PolicySample],
    *,
    source_ratios: Mapping[str, float],
    outcome_weights: Mapping[str, float],
    seed: int,
) -> tuple[list[PolicySample], dict[str, Any]]:
    """Deterministically curate train samples by teacher and game outcome."""

    ratios = {str(name): float(value) for name, value in source_ratios.items()}
    weights = {str(name): float(value) for name, value in outcome_weights.items()}
    if not ratios or any(value <= 0 for value in ratios.values()) or not math.isclose(sum(ratios.values()), 1.0):
        raise RawDataError("train source ratios must be positive and sum to one")
    if set(weights) != {"win", "draw", "loss"} or any(value <= 0 for value in weights.values()):
        raise RawDataError("outcome weights must contain positive win, draw, and loss values")
    groups: dict[str, list[PolicySample]] = {name: [] for name in ratios}
    for sample in samples:
        source = sample.metadata.get("source_agent")
        if source not in groups:
            raise RawDataError(f"unexpected source agent for train sampling: {source!r}")
        groups[str(source)].append(sample)
    total = math.floor(min(len(groups[name]) / ratio for name, ratio in ratios.items()))
    quotas = {name: math.floor(total * ratio) for name, ratio in ratios.items()}
    remainder = total - sum(quotas.values())
    ranked = sorted(ratios, key=lambda name: (-(total * ratios[name] - quotas[name]), name))
    for name in ranked:
        if remainder <= 0:
            break
        if quotas[name] < len(groups[name]):
            quotas[name] += 1
            remainder -= 1
    rng = random.Random(seed)

    def outcome(sample: PolicySample) -> str:
        winner, player = sample.metadata.get("winner"), sample.metadata.get("player")
        if winner is None:
            return "draw"
        if not isinstance(player, int) or not isinstance(winner, int):
            raise RawDataError("outcome sampling requires integer player/winner metadata")
        return "win" if winner == player else "loss"

    selected: list[PolicySample] = []
    before_outcomes: Counter[str] = Counter()
    after_outcomes: Counter[str] = Counter()
    for name in sorted(groups):
        group = groups[name]
        before_outcomes.update(outcome(sample) for sample in group)
        scored = [
            (math.log(max(rng.random(), 1e-300)) / weights[outcome(sample)], index, sample)
            for index, sample in enumerate(group)
        ]
        chosen = [item[2] for item in sorted(scored, reverse=True)[:quotas[name]]]
        selected.extend(chosen)
        after_outcomes.update(outcome(sample) for sample in chosen)
    rng.shuffle(selected)
    return selected, {
        "enabled": True,
        "seed": seed,
        "source_ratios": ratios,
        "outcome_weights": weights,
        "source_counts_before": {name: len(groups[name]) for name in sorted(groups)},
        "source_counts_after": {name: quotas[name] for name in sorted(quotas)},
        "outcome_counts_before": dict(sorted(before_outcomes.items())),
        "outcome_counts_after": dict(sorted(after_outcomes.items())),
        "samples_after": len(selected),
    }


def d4_augment(sample: PolicySample) -> list[PolicySample]:
    """Create all D4 transforms while transforming action and legal mask too."""
    size = sample.x.shape[-1]
    target_grid = np.zeros((size, size), dtype=bool)
    target_grid.flat[sample.target] = True
    mask_grid = sample.legal_mask.reshape(size, size)
    variants: list[PolicySample] = []
    for turns in range(4):
        x = np.rot90(sample.x, turns, axes=(1, 2))
        mask, target = np.rot90(mask_grid, turns), np.rot90(target_grid, turns)
        for reflected in (False, True):
            out_x = np.flip(x, axis=2) if reflected else x
            out_mask = np.fliplr(mask) if reflected else mask
            out_target = np.fliplr(target) if reflected else target
            variants.append(PolicySample(
                x=np.ascontiguousarray(out_x, dtype=np.float32),
                legal_mask=np.ascontiguousarray(out_mask.reshape(-1), dtype=bool),
                target=int(np.flatnonzero(out_target)[0]),
                metadata={**sample.metadata, "d4_rotation": turns, "d4_reflected": reflected},
            ))
    return variants


def _write_split(output: Path, name: str, samples: list[PolicySample]) -> dict[str, Any]:
    if not samples:
        raise RawDataError(f"{name} split is empty")
    tensors, metadata = output / f"{name}.npz", output / f"{name}_metadata.jsonl"
    cache = output / ".build_cache"
    cache.mkdir(exist_ok=True)
    paths = {field: cache / f"{name}_{field}.npy" for field in ("x", "legal_mask", "target")}
    x = np.lib.format.open_memmap(paths["x"], mode="w+", dtype=np.float32, shape=(len(samples), *samples[0].x.shape))
    mask = np.lib.format.open_memmap(paths["legal_mask"], mode="w+", dtype=bool, shape=(len(samples), *samples[0].legal_mask.shape))
    target = np.lib.format.open_memmap(paths["target"], mode="w+", dtype=np.int64, shape=(len(samples),))
    try:
        for index, sample in enumerate(samples):
            x[index] = sample.x
            mask[index] = sample.legal_mask
            target[index] = sample.target
        if not np.all(mask[np.arange(len(target)), target]):
            raise RawDataError(f"{name} split has illegal target")
        x.flush(); mask.flush(); target.flush()
        np.savez_compressed(tensors, x=x, legal_mask=mask, target=target)
    finally:
        del x, mask, target
        for path in paths.values():
            path.unlink(missing_ok=True)
        try:
            cache.rmdir()
        except OSError:
            pass
    with metadata.open("w", encoding="utf-8", newline="\n") as stream:
        for sample in samples:
            stream.write(json.dumps(sample.metadata, ensure_ascii=False, separators=(",", ":")) + "\n")
    return {"samples": len(samples), "tensor": tensors.name, "tensor_sha256": sha256_file(tensors), "metadata": metadata.name, "metadata_sha256": sha256_file(metadata)}


def load_dataset_split(
    dataset_dir: str | Path,
    split: str,
    *,
    verify_checksum: bool = True,
) -> dict[str, np.ndarray]:
    """Load one exported split for M1 without parsing raw JSONL.

    The returned mapping always contains ``x`` (`float32`), ``legal_mask``
    (`bool`) and ``target`` (`int64`).  Checksum and target-legality guards
    make a changed or incompatible dataset fail before training starts.
    """
    if split not in {"train", "val", "test"}:
        raise ValueError("split must be one of: train, val, test")
    directory = Path(dataset_dir)
    manifest_path = directory / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contract_version") != CONTRACT_VERSION:
        raise RawDataError("dataset manifest has unsupported contract_version")
    artifact = manifest.get("artifacts", {}).get(split)
    if not isinstance(artifact, Mapping):
        raise RawDataError(f"dataset manifest has no {split!r} artifact")
    tensor_path = directory / str(artifact["tensor"])
    if verify_checksum and sha256_file(tensor_path) != artifact.get("tensor_sha256"):
        raise RawDataError(f"dataset tensor checksum failed: {tensor_path.name}")
    with np.load(tensor_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ("x", "legal_mask", "target")}
    board_size = int(manifest["board_size"])
    x, mask, target = arrays["x"], arrays["legal_mask"], arrays["target"]
    if x.dtype != np.float32 or x.ndim != 4 or x.shape[1:] != (3, board_size, board_size):
        raise RawDataError(f"invalid x shape/dtype in {tensor_path.name}")
    if mask.dtype != bool or mask.shape != (len(x), board_size * board_size):
        raise RawDataError(f"invalid legal_mask shape/dtype in {tensor_path.name}")
    if target.dtype != np.int64 or target.shape != (len(x),):
        raise RawDataError(f"invalid target shape/dtype in {tensor_path.name}")
    if np.any(target < 0) or np.any(target >= board_size * board_size) or not np.all(mask[np.arange(len(target)), target]):
        raise RawDataError(f"illegal target in {tensor_path.name}")
    return arrays


def build_dataset(raw_dir: str | Path, output_dir: str | Path, config: Mapping[str, Any]) -> dict[str, Any]:
    """Validate raw shards, replay them, then export grouped split artifacts."""
    if config.get("contract_version") != CONTRACT_VERSION:
        raise RawDataError("unsupported dataset contract_version")
    seed = config.get("split_seed")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise RawDataError("split_seed must be an integer")
    raw_dir, output = Path(raw_dir), Path(output_dir)
    raw_manifest_path = raw_dir / "run_manifest.json"
    raw_manifest = json.loads(raw_manifest_path.read_text(encoding="utf-8"))
    shards = [raw_dir / item["path"] for item in raw_manifest.get("shards", [])]
    if not shards:
        raise RawDataError("raw manifest has no shards")
    for item, shard in zip(raw_manifest["shards"], shards, strict=True):
        if not shard.is_file() or sha256_file(shard) != item.get("sha256"):
            raise RawDataError(f"checksum failed for {shard.name}")
    records = [record for shard in shards for record in iter_raw_games(shard)]
    game_ids = [record.game_id for record in records]
    if len(game_ids) != len(set(game_ids)):
        raise RawDataError("duplicate game_id")
    assignments = split_game_ids(game_ids, seed=seed)
    split_sets = {name: set(ids) for name, ids in assignments.items()}
    if split_sets["train"] & split_sets["val"] or split_sets["train"] & split_sets["test"] or split_sets["val"] & split_sets["test"]:
        raise RawDataError("cross-split game leakage")
    splits: dict[str, list[PolicySample]] = {"train": [], "val": [], "test": []}
    for record in records:
        name = next(key for key, ids in split_sets.items() if record.game_id in ids)
        splits[name].extend(samples_from_raw_game(record))
    before = {name: len(value) for name, value in splits.items()}
    splits, removed = deduplicate_splits(splits)
    d4_split_isolation: dict[str, Any] = {
        "enabled": False,
        "cross_split_d4_state_overlap": None,
    }
    if config.get("d4_split_isolation", False):
        splits, d4_split_isolation = purge_cross_split_d4_state_overlap(splits)
    source_balance: dict[str, Any] = {
        name: {"enabled": False} for name in ("train", "val", "test")
    }
    train_policy_sampling: dict[str, Any] = {"enabled": False}
    train_source_ratios = config.get("train_source_ratios")
    if train_source_ratios is not None:
        if not isinstance(train_source_ratios, Mapping) or not isinstance(config.get("train_outcome_weights"), Mapping):
            raise RawDataError("train source ratios and outcome weights must be mappings")
        splits["train"], train_policy_sampling = sample_train_by_source_and_outcome(
            splits["train"],
            source_ratios=train_source_ratios,
            outcome_weights=config["train_outcome_weights"],
            seed=seed,
        )
        source_balance["train"] = {"enabled": False, "replaced_by": "train_policy_sampling"}
    if config.get("balance_source_agents", False):
        balance_train = bool(config.get("balance_train_source_agents", True))
        names = ("val", "test") if train_source_ratios is not None or not balance_train else ("train", "val", "test")
        if not balance_train and train_source_ratios is None:
            source_balance["train"] = {"enabled": False, "reason": "natural_source_distribution"}
        for offset, name in enumerate(names):
            splits[name], source_balance[name] = balance_samples_by_source(
                splits[name], seed=seed + offset
            )
    if config.get("train_d4_augmentation", True):
        splits["train"] = [variant for sample in splits["train"] for variant in d4_augment(sample)]
    output.mkdir(parents=True, exist_ok=True)
    split_path = output / "split_game_ids.json"
    split_path.write_text(json.dumps(assignments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    artifacts = {name: _write_split(output, name, samples) for name, samples in splits.items()}
    validation = {"games": {name: len(value) for name, value in assignments.items()}, "samples_before_dedup": before, "duplicates_removed": removed, "d4_split_isolation": d4_split_isolation, "train_policy_sampling": train_policy_sampling, "source_agent_balance": source_balance, "samples_after_export": {name: item["samples"] for name, item in artifacts.items()}, "cross_split_game_overlap": 0}
    report_path = output / "validation_report.json"
    report_path.write_text(json.dumps(validation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"dataset_schema": DATASET_SCHEMA_NAME, "dataset_version": config.get("dataset_version", "dataset-v1"), "contract_version": CONTRACT_VERSION, "board_size": records[0].config.board_size, "win_length": records[0].config.win_length, "raw_run_id": raw_manifest.get("run_id"), "raw_manifest_sha256": sha256_file(raw_manifest_path), "split_seed": seed, "split_game_ids": {"path": split_path.name, "sha256": sha256_file(split_path)}, "encoder": {"channels": ["current_player", "opponent", "legal"], "dtype": "float32"}, "train_d4_augmentation": bool(config.get("train_d4_augmentation", True)), "d4_split_isolation": bool(config.get("d4_split_isolation", False)), "balance_source_agents": bool(config.get("balance_source_agents", False)), "balance_train_source_agents": bool(config.get("balance_train_source_agents", True)), "train_source_ratios": train_source_ratios, "train_outcome_weights": config.get("train_outcome_weights"), "artifacts": artifacts, "validation": validation, "validation_report": {"path": report_path.name, "sha256": sha256_file(report_path)}}


__all__ = ["RAW_SCHEMA_NAME", "DATASET_SCHEMA_NAME", "RawDataError", "PolicySample", "sha256_file", "iter_raw_games", "replay_raw_game", "encode_policy_state", "samples_from_raw_game", "split_game_ids", "deduplicate_splits", "canonical_d4_state_hash", "purge_cross_split_d4_state_overlap", "balance_samples_by_source", "sample_train_by_source_and_outcome", "d4_augment", "load_dataset_split", "build_dataset"]
