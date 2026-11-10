from __future__ import annotations

import json
from pathlib import Path
import shutil
from uuid import uuid4

import numpy as np
import pytest
import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
import scripts.train_policy as training_module

from core.ml.architectures import (
    PolicyNet,
    PolicyNetConfig,
    mask_policy_logits,
    masked_policy_loss,
)
from core.ml.data_pipeline import sha256_file
from scripts.train_policy import (
    CHECKPOINT_SCHEMA,
    PolicyTensorDataset,
    load_training_config,
    parse_args,
    run_epoch,
    train,
    validate_dataset_contract,
)


@pytest.fixture
def artifact_dir():
    path = Path("models/checkpoints") / f".pytest-training-{uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path)


def make_dataset_and_config(root: Path) -> tuple[Path, Path]:
    dataset_dir = root / "dataset"
    dataset_dir.mkdir()
    rng = np.random.default_rng(20261110)
    artifacts: dict[str, dict[str, object]] = {}
    for split, samples in (("train", 16), ("val", 8), ("test", 8)):
        x = rng.integers(0, 2, size=(samples, 3, 11, 11)).astype(np.float32)
        legal_mask = np.ones((samples, 121), dtype=bool)
        target = np.arange(samples, dtype=np.int64) % 121
        tensor_path = dataset_dir / f"{split}.npz"
        np.savez_compressed(tensor_path, x=x, legal_mask=legal_mask, target=target)
        artifacts[split] = {
            "samples": samples,
            "tensor": tensor_path.name,
            "tensor_sha256": sha256_file(tensor_path),
        }
    manifest_path = dataset_dir / "dataset_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "contract_version": "caro-v2",
                "dataset_version": "fixture-v1",
                "board_size": 11,
                "encoder": {
                    "channels": ["current_player", "opponent", "legal"],
                    "dtype": "float32",
                },
                "artifacts": artifacts,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    config_path = root / "train.json"
    config_path.write_text(
        json.dumps(
            {
                "contract_version": "caro-v2",
                "run_id": "pytest-policy",
                "dataset": {
                    "version": "fixture-v1",
                    "manifest_sha256": sha256_file(manifest_path),
                },
                "model": {
                    "architecture_version": "caro-policynet-resnet-v1",
                    "board_size": 11,
                    "input_channels": 3,
                    "channels": 4,
                    "residual_blocks": 1,
                    "policy_channels": 2,
                    "dropout": 0.0,
                },
                "training": {
                    "seed": 17,
                    "batch_size": 4,
                    "epochs": 3,
                    "learning_rate": 0.001,
                    "weight_decay": 0.0,
                    "early_stopping_patience": 2,
                    "num_workers": 0,
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return dataset_dir, config_path


def test_policy_net_shape_and_backward_with_legal_mask():
    config = PolicyNetConfig(channels=8, residual_blocks=1, policy_channels=4, dropout=0)
    model = PolicyNet(config)
    x = torch.zeros((3, 3, 11, 11), dtype=torch.float32)
    legal = torch.ones((3, 121), dtype=torch.bool)
    legal[:, 0] = False
    target = torch.tensor([1, 60, 120], dtype=torch.long)

    logits = model(x)
    loss = masked_policy_loss(logits, legal, target)
    loss.backward()

    assert logits.shape == (3, 121)
    assert torch.isfinite(loss)
    assert any(parameter.grad is not None for parameter in model.parameters())
    assert torch.all(mask_policy_logits(logits, legal)[:, 0] < -1e20)


def test_masked_loss_rejects_illegal_target():
    logits = torch.zeros((1, 4))
    legal = torch.tensor([[True, False, True, True]])
    with pytest.raises(ValueError, match="illegal"):
        masked_policy_loss(logits, legal, torch.tensor([1]))


def test_run_epoch_updates_parameters_and_reports_legal_metrics():
    arrays = {
        "x": np.zeros((8, 3, 11, 11), dtype=np.float32),
        "legal_mask": np.ones((8, 121), dtype=bool),
        "target": np.arange(8, dtype=np.int64),
    }
    loader = DataLoader(PolicyTensorDataset(arrays), batch_size=4, shuffle=False)
    model = PolicyNet(
        PolicyNetConfig(channels=8, residual_blocks=1, policy_channels=4, dropout=0)
    )
    before = [parameter.detach().clone() for parameter in model.parameters()]
    optimizer = AdamW(model.parameters(), lr=1e-3)

    metrics = run_epoch(model, loader, torch.device("cpu"), optimizer=optimizer)

    assert metrics["samples"] == 8
    assert metrics["loss"] > 0
    assert 0 <= metrics["top1"] <= metrics["top3"] <= 1
    assert any(not torch.equal(old, new) for old, new in zip(before, model.parameters(), strict=True))


def test_training_config_and_dataset_checksum_are_strict(artifact_dir: Path):
    dataset_dir, config_path = make_dataset_and_config(artifact_dir)
    config = load_training_config(config_path)
    model = PolicyNetConfig.from_mapping(config["model"])

    validate_dataset_contract(dataset_dir, model, config["dataset"])
    config["dataset"]["manifest_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="checksum"):
        validate_dataset_contract(dataset_dir, model, config["dataset"])


def test_smoke_training_writes_history_tensorboard_and_both_checkpoints(artifact_dir: Path):
    dataset_dir, config_path = make_dataset_and_config(artifact_dir)
    output = artifact_dir / "run"
    args = parse_args(
        [
            "--config", str(config_path),
            "--dataset", str(dataset_dir),
            "--output", str(output),
            "--device", "cpu",
            "--smoke",
        ]
    )

    summary = train(args)

    assert summary["epochs_completed"] == 1
    assert summary["test_metrics"]["samples"] == 8
    assert summary["parameter_count"] > 0
    assert (output / "best.pt").is_file()
    assert (output / "last.pt").is_file()
    assert (output / "history.csv").is_file()
    assert (output / "history.json").is_file()
    assert (output / "run_summary.json").is_file()
    assert any((output / "tensorboard").iterdir())
    checkpoint = torch.load(output / "best.pt", map_location="cpu", weights_only=False)
    assert checkpoint["checkpoint_schema"] == CHECKPOINT_SCHEMA
    assert checkpoint["selection_metric"] == "val_loss"
    assert checkpoint["test_evaluated_after_selection"] is True
    assert checkpoint["model_config"]["architecture_version"]


def test_resume_continues_epoch_and_rejects_incompatible_checkpoint(artifact_dir: Path):
    dataset_dir, config_path = make_dataset_and_config(artifact_dir)
    output = artifact_dir / "run"
    common = [
        "--config", str(config_path),
        "--dataset", str(dataset_dir),
        "--output", str(output),
        "--device", "cpu",
        "--max-train-batches", "1",
        "--max-val-batches", "1",
        "--max-test-batches", "1",
    ]
    train(parse_args([*common, "--epochs", "1"]))

    summary = train(
        parse_args(
            [*common, "--epochs", "2", "--resume", str(output / "last.pt")]
        )
    )

    assert summary["epochs_completed"] == 2
    assert summary["resumed_from"].endswith("last.pt")
    history = json.loads((output / "history.json").read_text(encoding="utf-8"))
    assert [row["epoch"] for row in history] == [1, 2]

    bad_path = output / "bad.pt"
    bad = torch.load(output / "last.pt", map_location="cpu", weights_only=False)
    bad["dataset_manifest_sha256"] = "f" * 64
    torch.save(bad, bad_path)
    with pytest.raises(ValueError, match="dataset_manifest_sha256"):
        train(parse_args([*common, "--epochs", "3", "--resume", str(bad_path)]))


def test_early_stopping_is_driven_only_by_validation_loss(
    artifact_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    dataset_dir, config_path = make_dataset_and_config(artifact_dir)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["training"]["epochs"] = 10
    config["training"]["early_stopping_patience"] = 2
    config_path.write_text(json.dumps(config), encoding="utf-8")

    def fixed_metrics(*args, optimizer=None, **kwargs):
        del args, kwargs
        return {
            "loss": 2.0 if optimizer is not None else 1.0,
            "top1": 0.25,
            "top3": 0.5,
            "samples": 4.0,
        }

    monkeypatch.setattr(training_module, "run_epoch", fixed_metrics)
    output = artifact_dir / "early-stop-run"
    summary = training_module.train(
        training_module.parse_args(
            [
                "--config", str(config_path),
                "--dataset", str(dataset_dir),
                "--output", str(output),
                "--device", "cpu",
            ]
        )
    )

    assert summary["epochs_completed"] == 3
    assert summary["best_epoch"] == 1
    assert summary["best_val_loss"] == 1.0
