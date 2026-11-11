"""Train PolicyNet from a validated processed dataset manifest."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import random
import sys
import time
from typing import Any, Sequence

import numpy as np
import torch
from torch import Tensor
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from torch.utils.tensorboard import SummaryWriter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.interfaces import CONTRACT_VERSION  # noqa: E402
from core.ml.architectures import (  # noqa: E402
    PolicyNet,
    PolicyNetConfig,
    mask_policy_logits,
    masked_policy_loss,
)
from core.ml.data_pipeline import load_dataset_split, sha256_file  # noqa: E402

CHECKPOINT_SCHEMA = "caro-policy-v1"


class PolicyTensorDataset(Dataset[tuple[Tensor, Tensor, Tensor]]):
    """Zero-copy tensor view over arrays returned by the public dataset loader."""

    def __init__(self, arrays: dict[str, np.ndarray]) -> None:
        self.x = torch.from_numpy(arrays["x"])
        self.legal_mask = torch.from_numpy(arrays["legal_mask"])
        self.target = torch.from_numpy(arrays["target"])

    def __len__(self) -> int:
        return len(self.target)

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor, Tensor]:
        return self.x[index], self.legal_mask[index], self.target[index]


def seed_everything(seed: int) -> dict[str, Any]:
    """Seed all RNGs and request deterministic PyTorch kernels where possible."""

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)
    if hasattr(torch.backends, "cudnn"):
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
    return {
        "python_numpy_torch_seeded": True,
        "deterministic_algorithms": True,
        "gpu_limit": (
            "CUDA libraries or hardware may still introduce version-specific "
            "floating-point differences. CPU is the reproducibility baseline."
        ),
    }


def load_training_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(f"training config must use {CONTRACT_VERSION!r}")
    if not isinstance(config.get("run_id"), str) or not config["run_id"]:
        raise ValueError("training config requires a non-empty run_id")
    dataset = config.get("dataset")
    if not isinstance(dataset, dict):
        raise ValueError("training config requires a dataset object")
    if not isinstance(dataset.get("version"), str) or not dataset["version"]:
        raise ValueError("dataset.version must be a non-empty string")
    expected_hash = dataset.get("manifest_sha256")
    if (
        not isinstance(expected_hash, str)
        or len(expected_hash) != 64
        or any(char not in "0123456789abcdefABCDEF" for char in expected_hash)
    ):
        raise ValueError("dataset.manifest_sha256 must be a SHA-256 hex digest")
    PolicyNetConfig.from_mapping(config.get("model", {}))
    training = config.get("training")
    if not isinstance(training, dict):
        raise ValueError("training config requires a training object")
    seed = training.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("training.seed must be a non-negative integer")
    positive_ints = ("batch_size", "epochs", "early_stopping_patience")
    for name in positive_ints:
        value = training.get(name)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"training.{name} must be a positive integer")
    workers = training.get("num_workers", 0)
    if isinstance(workers, bool) or not isinstance(workers, int) or workers < 0:
        raise ValueError("training.num_workers must be a non-negative integer")
    for name in ("learning_rate", "weight_decay"):
        value = training.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or value < 0
            or (name == "learning_rate" and value == 0)
        ):
            raise ValueError(f"training.{name} must be finite and valid")
    return config


def validate_dataset_contract(
    dataset_dir: Path,
    model: PolicyNetConfig,
    expected: dict[str, Any],
) -> dict[str, Any]:
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("contract_version") != CONTRACT_VERSION:
        raise ValueError("dataset contract_version is incompatible")
    if int(manifest.get("board_size", -1)) != model.board_size:
        raise ValueError("dataset board_size does not match model")
    channels = manifest.get("encoder", {}).get("channels", [])
    if len(channels) != model.input_channels:
        raise ValueError("dataset encoder channel count does not match model")
    if manifest.get("dataset_version") != expected["version"]:
        raise ValueError("dataset version does not match training config")
    if sha256_file(manifest_path).lower() != expected["manifest_sha256"].lower():
        raise ValueError("dataset manifest checksum does not match training config")
    for split in ("train", "val", "test"):
        if split not in manifest.get("artifacts", {}):
            raise ValueError(f"dataset manifest has no {split!r} artifact")
    return manifest


def make_loader(
    dataset_dir: Path,
    split: str,
    *,
    batch_size: int,
    shuffle: bool,
    seed: int,
    num_workers: int,
) -> DataLoader[tuple[Tensor, Tensor, Tensor]]:
    arrays = load_dataset_split(dataset_dir, split, verify_checksum=True)
    dataset = PolicyTensorDataset(arrays)
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        generator=generator,
        persistent_workers=num_workers > 0,
    )


def run_epoch(
    model: PolicyNet,
    loader: DataLoader[tuple[Tensor, Tensor, Tensor]],
    device: torch.device,
    *,
    optimizer: AdamW | None,
    max_batches: int | None = None,
) -> dict[str, float]:
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    total_top1 = 0
    total_top3 = 0
    total_samples = 0
    for batch_index, (x, legal_mask, target) in enumerate(loader):
        if max_batches is not None and batch_index >= max_batches:
            break
        x = x.to(device, non_blocking=True)
        legal_mask = legal_mask.to(device, non_blocking=True)
        target = target.to(device, non_blocking=True)
        if training:
            optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            logits = model(x)
            loss = masked_policy_loss(logits, legal_mask, target)
            if training:
                loss.backward()
                optimizer.step()
        with torch.no_grad():
            masked = mask_policy_logits(logits, legal_mask)
            top = masked.topk(k=min(3, masked.shape[1]), dim=1).indices
            total_top1 += int((top[:, 0] == target).sum().item())
            total_top3 += int((top == target[:, None]).any(dim=1).sum().item())
        batch_size = len(target)
        total_loss += float(loss.item()) * batch_size
        total_samples += batch_size
    if total_samples == 0:
        raise RuntimeError("epoch consumed zero samples")
    return {
        "loss": total_loss / total_samples,
        "top1": total_top1 / total_samples,
        "top3": total_top3 / total_samples,
        "samples": float(total_samples),
    }


def _save_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, temporary)
    temporary.replace(path)


def _checkpoint_payload(
    *,
    config: dict[str, Any],
    model_config: PolicyNetConfig,
    model: PolicyNet,
    optimizer: AdamW,
    dataset_version: str,
    dataset_manifest_sha256: str,
    seed: int,
    epoch: int,
    val_metrics: dict[str, float],
    best_epoch: int,
    best_val_loss: float,
    stale_epochs: int,
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "run_id": config["run_id"],
        "dataset_version": dataset_version,
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "model_config": model_config.to_dict(),
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "training_config": dict(config["training"]),
        "training_seed": seed,
        "epoch": epoch,
        "val_metrics": dict(val_metrics),
        "selection_metric": "val_loss",
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "stale_epochs": stale_epochs,
        "history": list(history),
        "rng_state": {
            "python": random.getstate(),
            "numpy": np.random.get_state(),
            "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None,
        },
    }


def _load_resume_checkpoint(
    path: Path,
    *,
    config: dict[str, Any],
    model_config: PolicyNetConfig,
    model: PolicyNet,
    optimizer: AdamW,
    dataset_version: str,
    dataset_manifest_sha256: str,
    seed: int,
    device: torch.device,
) -> tuple[int, float, int, int, list[dict[str, Any]]]:
    raw = torch.load(path, map_location=device, weights_only=False)
    if not isinstance(raw, dict):
        raise ValueError("resume checkpoint payload must be a mapping")
    checks = {
        "checkpoint_schema": CHECKPOINT_SCHEMA,
        "contract_version": CONTRACT_VERSION,
        "run_id": config["run_id"],
        "dataset_version": dataset_version,
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "model_config": model_config.to_dict(),
        "training_seed": seed,
    }
    for name, expected in checks.items():
        observed = raw.get(name)
        if name == "dataset_manifest_sha256" and isinstance(observed, str):
            observed = observed.lower()
            expected = str(expected).lower()
        if observed != expected:
            raise ValueError(f"resume checkpoint {name} is incompatible")
    if raw.get("training_config") != config["training"]:
        raise ValueError("resume checkpoint training_config is incompatible")
    try:
        model.load_state_dict(raw["model_state_dict"], strict=True)
        optimizer.load_state_dict(raw["optimizer_state_dict"])
        epoch = int(raw["epoch"])
        best_val_loss = float(raw["best_val_loss"])
        best_epoch = int(raw["best_epoch"])
        stale_epochs = int(raw["stale_epochs"])
        history = list(raw["history"])
        rng_state = raw["rng_state"]
        random.setstate(rng_state["python"])
        np.random.set_state(rng_state["numpy"])
        torch.set_rng_state(rng_state["torch"].cpu())
        if torch.cuda.is_available() and rng_state.get("cuda") is not None:
            torch.cuda.set_rng_state_all(rng_state["cuda"])
    except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        raise ValueError("resume checkpoint is incomplete or corrupted") from exc
    if epoch < 1 or best_epoch < 1 or not math.isfinite(best_val_loss):
        raise ValueError("resume checkpoint contains invalid training progress")
    return epoch + 1, best_val_loss, best_epoch, stale_epochs, history


def _write_history(
    csv_path: Path,
    json_path: Path,
    history: list[dict[str, Any]],
) -> None:
    if not history:
        raise RuntimeError("training history is empty")
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer_csv = csv.DictWriter(stream, fieldnames=list(history[0]))
        writer_csv.writeheader()
        writer_csv.writerows(history)
    json_path.write_text(
        json.dumps(history, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def train(args: argparse.Namespace) -> dict[str, Any]:
    config = load_training_config(args.config)
    model_config = PolicyNetConfig.from_mapping(config["model"])
    manifest = validate_dataset_contract(args.dataset, model_config, config["dataset"])
    training = config["training"]
    seed = int(args.seed if args.seed is not None else training["seed"])
    determinism = seed_everything(seed)
    device_name = args.device
    if device_name == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")

    epochs = int(args.epochs if args.epochs is not None else training["epochs"])
    max_train_batches = args.max_train_batches
    max_val_batches = args.max_val_batches
    max_test_batches = args.max_test_batches
    if args.smoke:
        epochs = 1
        max_train_batches = 2 if max_train_batches is None else max_train_batches
        max_val_batches = 2 if max_val_batches is None else max_val_batches
        max_test_batches = 2 if max_test_batches is None else max_test_batches

    val_loader = make_loader(
        args.dataset,
        "val",
        batch_size=int(training["batch_size"]),
        shuffle=False,
        seed=seed,
        num_workers=int(training.get("num_workers", 0)),
    )
    model = PolicyNet(model_config).to(device)
    optimizer = AdamW(
        model.parameters(),
        lr=float(training["learning_rate"]),
        weight_decay=float(training["weight_decay"]),
    )
    args.output.mkdir(parents=True, exist_ok=True)
    history_path = args.output / "history.csv"
    history_json_path = args.output / "history.json"
    best_path = args.output / "best.pt"
    last_path = args.output / "last.pt"
    manifest_path = args.dataset / "dataset_manifest.json"
    dataset_manifest_sha256 = sha256_file(manifest_path)
    best_val_loss = math.inf
    best_epoch = 0
    stale_epochs = 0
    history: list[dict[str, Any]] = []
    start_epoch = 1

    if args.resume is not None:
        resume_path = args.resume
        if not resume_path.is_absolute():
            resume_path = (Path.cwd() / resume_path).resolve()
        if resume_path.parent != args.output.resolve():
            raise ValueError("resume checkpoint must belong to the selected output directory")
        start_epoch, best_val_loss, best_epoch, stale_epochs, history = (
            _load_resume_checkpoint(
                resume_path,
                config=config,
                model_config=model_config,
                model=model,
                optimizer=optimizer,
                dataset_version=str(manifest["dataset_version"]),
                dataset_manifest_sha256=dataset_manifest_sha256,
                seed=seed,
                device=device,
            )
        )
        if start_epoch > epochs:
            raise ValueError("resume checkpoint already reached the configured epoch limit")

    writer = SummaryWriter(log_dir=str(args.output / "tensorboard"))
    started = time.perf_counter()
    try:
        for epoch in range(start_epoch, epochs + 1):
            epoch_started = time.perf_counter()
            # Epoch-derived shuffle seed makes resumed epoch N identical to
            # uninterrupted epoch N without serializing DataLoader internals.
            train_loader = make_loader(
                args.dataset,
                "train",
                batch_size=int(training["batch_size"]),
                shuffle=True,
                seed=seed + epoch,
                num_workers=int(training.get("num_workers", 0)),
            )
            train_metrics = run_epoch(
                model,
                train_loader,
                device,
                optimizer=optimizer,
                max_batches=max_train_batches,
            )
            val_metrics = run_epoch(
                model,
                val_loader,
                device,
                optimizer=None,
                max_batches=max_val_batches,
            )
            row = {
                "epoch": epoch,
                "train_loss": train_metrics["loss"],
                "train_top1": train_metrics["top1"],
                "train_top3": train_metrics["top3"],
                "val_loss": val_metrics["loss"],
                "val_top1": val_metrics["top1"],
                "val_top3": val_metrics["top3"],
                "learning_rate": float(optimizer.param_groups[0]["lr"]),
                "epoch_seconds": time.perf_counter() - epoch_started,
            }
            history.append(row)
            for name, value in row.items():
                if name != "epoch":
                    writer.add_scalar(name, value, epoch)
            print(json.dumps(row, ensure_ascii=False), flush=True)
            if val_metrics["loss"] < best_val_loss:
                best_val_loss = val_metrics["loss"]
                best_epoch = epoch
                stale_epochs = 0
            else:
                stale_epochs += 1
            payload = _checkpoint_payload(
                config=config,
                model_config=model_config,
                model=model,
                optimizer=optimizer,
                dataset_version=str(manifest["dataset_version"]),
                dataset_manifest_sha256=dataset_manifest_sha256,
                seed=seed,
                epoch=epoch,
                val_metrics=val_metrics,
                best_epoch=best_epoch,
                best_val_loss=best_val_loss,
                stale_epochs=stale_epochs,
                history=history,
            )
            _save_checkpoint(last_path, payload)
            if best_epoch == epoch:
                _save_checkpoint(best_path, payload)
            _write_history(history_path, history_json_path, history)
            writer.flush()
            if stale_epochs >= int(training["early_stopping_patience"]):
                break
    finally:
        writer.close()

    if not best_path.is_file():
        raise RuntimeError("training did not produce best.pt")

    # The test split is deliberately opened only after validation has selected
    # and frozen best.pt.
    best_checkpoint = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(best_checkpoint["model_state_dict"], strict=True)
    test_loader = make_loader(
        args.dataset,
        "test",
        batch_size=int(training["batch_size"]),
        shuffle=False,
        seed=seed,
        num_workers=int(training.get("num_workers", 0)),
    )
    test_metrics = run_epoch(
        model,
        test_loader,
        device,
        optimizer=None,
        max_batches=max_test_batches,
    )
    best_checkpoint["test_metrics"] = test_metrics
    best_checkpoint["test_evaluated_after_selection"] = True
    _save_checkpoint(best_path, best_checkpoint)

    summary = {
        "run_id": config["run_id"],
        "device": str(device),
        "seed": seed,
        "determinism": determinism,
        "dataset": str(args.dataset),
        "dataset_version": manifest.get("dataset_version"),
        "dataset_manifest_sha256": dataset_manifest_sha256,
        "epochs_completed": len(history),
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "test_metrics": test_metrics,
        "smoke": bool(args.smoke),
        "resumed_from": str(args.resume) if args.resume is not None else None,
        "elapsed_seconds": time.perf_counter() - started,
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "best_checkpoint": str(best_path),
        "last_checkpoint": str(last_path),
        "history_csv": str(history_path),
        "history_json": str(history_json_path),
        "tensorboard_dir": str(args.output / "tensorboard"),
    }
    (args.output / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--max-train-batches", type=int)
    parser.add_argument("--max-val-batches", type=int)
    parser.add_argument("--max-test-batches", type=int)
    parser.add_argument(
        "--resume",
        type=Path,
        help="Resume from a compatible last.pt in the selected output directory.",
    )
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(argv)
    for name in ("epochs", "max_train_batches", "max_val_batches", "max_test_batches"):
        value = getattr(args, name)
        if value is not None and value <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    if args.seed is not None and args.seed < 0:
        parser.error("--seed must be non-negative")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    summary = train(parse_args(argv))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
