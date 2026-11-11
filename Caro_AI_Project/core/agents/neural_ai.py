"""Deterministic checkpoint-backed policy agent for ``caro-v2``.

The adapter is intentionally inference-only.  Training stays in
``scripts/train_policy.py`` and board encoding is delegated to the canonical
Week 5--6 data-pipeline encoder so training and inference cannot silently use
different channel conventions.
"""
from __future__ import annotations

from pathlib import Path
import time
from typing import Any, Mapping

import numpy as np
import torch

from core.engine.interfaces import (
    CONTRACT_VERSION,
    AgentDecision,
    GameEnv,
    SearchBudget,
    index_to_action,
)
from core.ml.architectures import PolicyNet, PolicyNetConfig, mask_policy_logits
from core.ml.data_pipeline import encode_policy_state

CHECKPOINT_SCHEMA = "caro-policy-v1"


def _require_mapping(value: object, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"checkpoint {name} must be a mapping")
    return value


class NeuralAgent:
    """Load a trained PolicyNet and select the highest-scoring legal action.

    Args:
        checkpoint_path: A checkpoint produced by ``train_policy.py``.
        name: Public participant label used by the tournament runner.
        device: PyTorch device.  CPU is the portable default.
        expected_dataset_version: Optional dataset-version compatibility gate.
        expected_dataset_manifest_sha256: Optional exact dataset checksum gate.
    """

    def __init__(
        self,
        checkpoint_path: str | Path,
        *,
        name: str = "neural-policy",
        device: str | torch.device = "cpu",
        expected_dataset_version: str | None = None,
        expected_dataset_manifest_sha256: str | None = None,
    ) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string")
        path = Path(checkpoint_path)
        if not path.is_file():
            raise FileNotFoundError(f"policy checkpoint not found: {path}")

        self._device = torch.device(device)
        if self._device.type == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available")

        raw = torch.load(path, map_location=self._device, weights_only=False)
        checkpoint = _require_mapping(raw, "payload")
        if checkpoint.get("checkpoint_schema") != CHECKPOINT_SCHEMA:
            raise ValueError("unsupported policy checkpoint schema")
        if checkpoint.get("contract_version") != CONTRACT_VERSION:
            raise ValueError("checkpoint contract_version is incompatible")

        model_config = PolicyNetConfig.from_mapping(
            _require_mapping(checkpoint.get("model_config"), "model_config")
        )
        dataset_version = checkpoint.get("dataset_version")
        dataset_hash = checkpoint.get("dataset_manifest_sha256")
        if not isinstance(dataset_version, str) or not dataset_version:
            raise ValueError("checkpoint has no dataset_version")
        if (
            not isinstance(dataset_hash, str)
            or len(dataset_hash) != 64
            or any(char not in "0123456789abcdefABCDEF" for char in dataset_hash)
        ):
            raise ValueError("checkpoint has no valid dataset manifest checksum")
        if expected_dataset_version is not None and dataset_version != expected_dataset_version:
            raise ValueError("checkpoint dataset_version is incompatible")
        if (
            expected_dataset_manifest_sha256 is not None
            and dataset_hash.lower() != expected_dataset_manifest_sha256.lower()
        ):
            raise ValueError("checkpoint dataset manifest checksum is incompatible")

        state_dict = _require_mapping(
            checkpoint.get("model_state_dict"), "model_state_dict"
        )
        self._model = PolicyNet(model_config).to(self._device)
        self._model.load_state_dict(state_dict, strict=True)
        self._model.eval()
        self._name = name
        self._checkpoint_path = path
        self._model_config = model_config
        self._dataset_version = dataset_version
        self._dataset_manifest_sha256 = dataset_hash.lower()

    @property
    def name(self) -> str:
        return self._name

    @property
    def checkpoint_path(self) -> Path:
        return self._checkpoint_path

    @property
    def model_config(self) -> PolicyNetConfig:
        return self._model_config

    @property
    def dataset_version(self) -> str:
        return self._dataset_version

    @property
    def dataset_manifest_sha256(self) -> str:
        return self._dataset_manifest_sha256

    def choose_action(
        self,
        env: GameEnv,
        budget: SearchBudget | None = None,
    ) -> AgentDecision:
        """Return deterministic legal argmax without mutating ``env``."""

        del budget  # Policy inference has no search budget.
        started = time.perf_counter()
        if env.is_terminal():
            raise RuntimeError(f"{self._name}: cannot choose an action in a terminal state")
        legal = env.legal_actions()
        if not legal:
            raise RuntimeError(f"{self._name}: no legal actions available")
        if env.config.board_size != self._model_config.board_size:
            raise ValueError("environment board_size does not match checkpoint")

        x, legal_mask = encode_policy_state(
            env.state,
            legal,
            env.config.board_size,
        )
        x_tensor = torch.from_numpy(np.ascontiguousarray(x)).unsqueeze(0).to(self._device)
        mask_tensor = (
            torch.from_numpy(np.ascontiguousarray(legal_mask))
            .unsqueeze(0)
            .to(self._device)
        )
        with torch.inference_mode():
            logits = self._model(x_tensor)
            masked = mask_policy_logits(logits, mask_tensor)
            action_index = int(masked.argmax(dim=1).item())
            score = float(torch.softmax(masked, dim=1)[0, action_index].item())

        action = index_to_action(action_index, env.config.board_size)
        if action not in legal:
            raise RuntimeError("policy selected an illegal action after masking")
        return AgentDecision(
            action=action,
            score=score,
            nodes=0,
            simulations=0,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )

    def __repr__(self) -> str:
        return (
            f"NeuralAgent(name={self._name!r}, "
            f"checkpoint_path={str(self._checkpoint_path)!r}, "
            f"device={str(self._device)!r})"
        )


PolicyAgent = NeuralAgent


def load_policy_agent(checkpoint_path: str | Path, **kwargs: Any) -> NeuralAgent:
    """Stable factory for runner configs and external integration."""

    return NeuralAgent(checkpoint_path, **kwargs)


__all__ = [
    "CHECKPOINT_SCHEMA",
    "NeuralAgent",
    "PolicyAgent",
    "load_policy_agent",
]
