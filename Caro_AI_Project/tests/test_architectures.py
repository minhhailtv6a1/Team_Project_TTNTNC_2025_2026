from __future__ import annotations

import io

import pytest
import torch

from core.ml.architectures import (
    PolicyNet,
    PolicyNetConfig,
    mask_policy_logits,
    masked_policy_loss,
)


def tiny_config() -> PolicyNetConfig:
    return PolicyNetConfig(
        channels=8,
        residual_blocks=1,
        policy_channels=4,
        dropout=0.0,
    )


@pytest.mark.parametrize("batch_size", [1, 4])
def test_policy_net_outputs_one_raw_logit_per_board_cell(batch_size: int):
    model = PolicyNet(tiny_config())
    x = torch.zeros((batch_size, 3, 11, 11), dtype=torch.float32)

    logits = model(x)

    assert logits.shape == (batch_size, 121)
    assert logits.dtype == torch.float32
    assert torch.isfinite(logits).all()


def test_forward_rejects_wrong_shape_and_integer_input():
    model = PolicyNet(tiny_config())
    with pytest.raises(ValueError, match="expected input"):
        model(torch.zeros((1, 3, 9, 9)))
    with pytest.raises(ValueError, match="floating-point"):
        model(torch.zeros((1, 3, 11, 11), dtype=torch.int64))


def test_mask_forces_illegal_probability_to_zero_and_keeps_legal_argmax():
    logits = torch.tensor([[1000.0, 3.0, 2.0, 1.0]])
    legal = torch.tensor([[False, True, True, False]])

    masked = mask_policy_logits(logits, legal)
    probabilities = torch.softmax(masked, dim=1)

    assert probabilities[0, 0].item() == 0.0
    assert probabilities[0, 3].item() == 0.0
    assert masked.argmax(dim=1).item() == 1


def test_mask_rejects_wrong_dtype_shape_and_empty_legal_set():
    logits = torch.zeros((1, 4))
    with pytest.raises(ValueError, match="dtype bool"):
        mask_policy_logits(logits, torch.ones((1, 4)))
    with pytest.raises(ValueError, match="same"):
        mask_policy_logits(logits, torch.ones((1, 3), dtype=torch.bool))
    with pytest.raises(ValueError, match="at least one"):
        mask_policy_logits(logits, torch.zeros((1, 4), dtype=torch.bool))


def test_masked_loss_rejects_illegal_target_and_has_finite_gradients():
    model = PolicyNet(tiny_config())
    x = torch.randn((3, 3, 11, 11), dtype=torch.float32)
    legal = torch.ones((3, 121), dtype=torch.bool)
    legal[:, 0] = False
    target = torch.tensor([1, 60, 120], dtype=torch.long)

    loss = masked_policy_loss(model(x), legal, target)
    loss.backward()

    assert torch.isfinite(loss)
    gradients = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
    assert gradients
    assert all(torch.isfinite(gradient).all() for gradient in gradients)

    with pytest.raises(ValueError, match="illegal"):
        masked_policy_loss(torch.zeros((1, 4)), torch.tensor([[False, True, True, True]]), torch.tensor([0]))


def test_state_dict_round_trip_preserves_logits_in_eval_mode():
    torch.manual_seed(17)
    config = tiny_config()
    original = PolicyNet(config).eval()
    x = torch.randn((2, 3, 11, 11), dtype=torch.float32)
    expected = original(x)
    buffer = io.BytesIO()
    torch.save(original.state_dict(), buffer)
    buffer.seek(0)

    restored = PolicyNet(PolicyNetConfig.from_mapping(config.to_dict())).eval()
    restored.load_state_dict(torch.load(buffer, weights_only=True))

    torch.testing.assert_close(restored(x), expected, rtol=0.0, atol=0.0)


def test_model_config_is_versioned_and_validated():
    config = tiny_config()
    assert config.to_dict()["architecture_version"] == "caro-policynet-resnet-v1"
    with pytest.raises(ValueError, match="architecture_version"):
        PolicyNetConfig(architecture_version="")
