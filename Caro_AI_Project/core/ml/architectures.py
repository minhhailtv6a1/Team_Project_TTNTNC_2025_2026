"""Neural policy architecture and legal-action masking for Caro."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

import torch
from torch import Tensor, nn
import torch.nn.functional as F


@dataclass(frozen=True, slots=True)
class PolicyNetConfig:
    architecture_version: str = "caro-policynet-resnet-v1"
    board_size: int = 11
    input_channels: int = 3
    channels: int = 64
    residual_blocks: int = 4
    policy_channels: int = 32
    dropout: float = 0.10

    def __post_init__(self) -> None:
        if not isinstance(self.architecture_version, str) or not self.architecture_version:
            raise ValueError("architecture_version must be a non-empty string")
        for name in (
            "board_size",
            "input_channels",
            "channels",
            "residual_blocks",
            "policy_channels",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not isinstance(self.dropout, (int, float)) or not 0 <= self.dropout < 1:
            raise ValueError("dropout must be in [0, 1)")

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "PolicyNetConfig":
        return cls(**dict(data))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class _ResidualBlock(nn.Module):
    def __init__(self, channels: int, dropout: float) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)
        self.dropout = nn.Dropout2d(dropout) if dropout else nn.Identity()

    def forward(self, x: Tensor) -> Tensor:
        residual = x
        x = F.relu(self.bn1(self.conv1(x)), inplace=True)
        x = self.dropout(x)
        x = self.bn2(self.conv2(x))
        return F.relu(x + residual, inplace=True)


class PolicyNet(nn.Module):
    """Small residual CNN mapping ``[N, 3, B, B]`` to ``[N, B*B]`` logits."""

    def __init__(self, config: PolicyNetConfig | Mapping[str, Any] | None = None) -> None:
        super().__init__()
        if config is None:
            config = PolicyNetConfig()
        elif not isinstance(config, PolicyNetConfig):
            config = PolicyNetConfig.from_mapping(config)
        self.config = config
        self.stem = nn.Sequential(
            nn.Conv2d(
                config.input_channels,
                config.channels,
                kernel_size=3,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(config.channels),
            nn.ReLU(inplace=True),
        )
        self.tower = nn.Sequential(
            *[
                _ResidualBlock(config.channels, float(config.dropout))
                for _ in range(config.residual_blocks)
            ]
        )
        self.policy_head = nn.Sequential(
            nn.Conv2d(config.channels, config.policy_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(config.policy_channels),
            nn.ReLU(inplace=True),
            nn.Flatten(),
            nn.Linear(
                config.policy_channels * config.board_size * config.board_size,
                config.board_size * config.board_size,
            ),
        )

    def forward(self, x: Tensor) -> Tensor:
        expected = (
            self.config.input_channels,
            self.config.board_size,
            self.config.board_size,
        )
        if x.ndim != 4 or tuple(x.shape[1:]) != expected:
            raise ValueError(f"expected input [N, {expected}], got {tuple(x.shape)}")
        if not x.is_floating_point():
            raise ValueError("PolicyNet input must use a floating-point dtype")
        return self.policy_head(self.tower(self.stem(x)))


def mask_policy_logits(logits: Tensor, legal_mask: Tensor) -> Tensor:
    """Replace illegal-action logits by the minimum finite value of the dtype."""

    if logits.ndim != 2 or legal_mask.shape != logits.shape:
        raise ValueError("logits and legal_mask must have the same [N, actions] shape")
    if not logits.is_floating_point():
        raise ValueError("logits must use a floating-point dtype")
    if legal_mask.dtype != torch.bool:
        raise ValueError("legal_mask must have dtype bool")
    if not torch.all(legal_mask.any(dim=1)):
        raise ValueError("every sample must contain at least one legal action")
    return logits.masked_fill(~legal_mask, torch.finfo(logits.dtype).min)


def masked_policy_loss(logits: Tensor, legal_mask: Tensor, target: Tensor) -> Tensor:
    """Cross entropy over legal actions only, rejecting illegal target labels."""

    if logits.ndim != 2 or legal_mask.shape != logits.shape:
        raise ValueError("logits and legal_mask must have the same [N, actions] shape")
    if legal_mask.dtype != torch.bool:
        raise ValueError("legal_mask must have dtype bool")
    if target.ndim != 1 or target.shape[0] != logits.shape[0]:
        raise ValueError("target must have shape [N]")
    if target.dtype != torch.long:
        raise ValueError("target must have dtype int64/long")
    if torch.any(target < 0) or torch.any(target >= logits.shape[1]):
        raise ValueError("target contains an out-of-range action")
    if not torch.all(legal_mask.gather(1, target[:, None]).squeeze(1)):
        raise ValueError("target contains an illegal action")
    return F.cross_entropy(mask_policy_logits(logits, legal_mask), target)


__all__ = [
    "PolicyNetConfig",
    "PolicyNet",
    "mask_policy_logits",
    "masked_policy_loss",
]
