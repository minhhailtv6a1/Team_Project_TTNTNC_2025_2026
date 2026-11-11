from __future__ import annotations

from pathlib import Path
import shutil
from uuid import uuid4

import pytest
import torch

from core.agents.neural_ai import (
    CHECKPOINT_SCHEMA,
    NeuralAgent,
    PolicyAgent,
    load_policy_agent,
)
from core.agents.random_ai import RandomAgent
from core.engine.game_env import CaroEnv
from core.engine.interfaces import CONTRACT_VERSION, Agent, SearchBudget
from core.ml.architectures import PolicyNet, PolicyNetConfig
from core.utils.tournament_runner import Participant, play_game


@pytest.fixture
def artifact_dir():
    path = Path("models/checkpoints") / f".pytest-neural-{uuid4().hex}"
    path.mkdir(parents=True)
    try:
        yield path
    finally:
        shutil.rmtree(path)


def write_checkpoint(
    path: Path,
    *,
    contract_version: str = CONTRACT_VERSION,
    preferred_index: int | None = None,
) -> Path:
    config = PolicyNetConfig(
        channels=4,
        residual_blocks=1,
        policy_channels=2,
        dropout=0.0,
    )
    model = PolicyNet(config)
    for parameter in model.parameters():
        parameter.data.zero_()
    if preferred_index is not None:
        model.policy_head[-1].bias.data[preferred_index] = 1000.0
    torch.save(
        {
            "checkpoint_schema": CHECKPOINT_SCHEMA,
            "contract_version": contract_version,
            "dataset_version": "fixture-v1",
            "dataset_manifest_sha256": "a" * 64,
            "model_config": config.to_dict(),
            "model_state_dict": model.state_dict(),
        },
        path,
    )
    return path


def play(env: CaroEnv, actions: list[tuple[int, int]]) -> CaroEnv:
    for action in actions:
        env.step(action)
    return env


def test_agent_loads_checkpoint_and_satisfies_protocol(artifact_dir: Path):
    checkpoint = write_checkpoint(artifact_dir / "policy.pt")
    agent = load_policy_agent(checkpoint, name="fixture-policy")

    assert isinstance(agent, Agent)
    assert isinstance(agent, PolicyAgent)
    assert agent.name == "fixture-policy"
    assert agent.checkpoint_path == checkpoint
    assert agent.model_config.architecture_version == "caro-policynet-resnet-v1"
    assert agent.dataset_version == "fixture-v1"
    assert agent.dataset_manifest_sha256 == "a" * 64
    assert "fixture-policy" in repr(agent)


def test_constructor_rejects_bad_name_missing_file_and_bad_schema(artifact_dir: Path):
    with pytest.raises(ValueError, match="name"):
        NeuralAgent(artifact_dir / "missing.pt", name="")
    with pytest.raises(FileNotFoundError):
        NeuralAgent(artifact_dir / "missing.pt")

    checkpoint = write_checkpoint(artifact_dir / "bad-schema.pt")
    payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
    payload["checkpoint_schema"] = "unknown"
    torch.save(payload, checkpoint)
    with pytest.raises(ValueError, match="schema"):
        NeuralAgent(checkpoint)


def test_action_is_legal_deterministic_and_does_not_mutate_env(artifact_dir: Path):
    checkpoint = write_checkpoint(artifact_dir / "policy.pt", preferred_index=60)
    agent = NeuralAgent(checkpoint)
    env = play(CaroEnv(), [(5, 5), (5, 6), (4, 4)])
    before = env.state
    legal = env.legal_actions()

    first = agent.choose_action(env, SearchBudget(seed=11))
    second = agent.choose_action(env, SearchBudget(seed=99))

    assert first.action in legal
    assert first.action == second.action
    assert first.score is not None and 0.0 <= first.score <= 1.0
    assert first.nodes == 0 and first.simulations == 0
    assert env.state == before


def test_illegal_highest_logit_is_masked_before_argmax(artifact_dir: Path):
    checkpoint = write_checkpoint(artifact_dir / "policy.pt", preferred_index=0)
    agent = NeuralAgent(checkpoint)
    env = play(CaroEnv(), [(0, 0)])

    decision = agent.choose_action(env)

    assert decision.action != (0, 0)
    assert decision.action in env.legal_actions()


def test_terminal_state_raises_runtime_error_without_mutation(artifact_dir: Path):
    checkpoint = write_checkpoint(artifact_dir / "policy.pt")
    agent = NeuralAgent(checkpoint)
    env = play(
        CaroEnv(),
        [(5, 3), (0, 0), (5, 4), (0, 2), (5, 5), (0, 4), (5, 6), (10, 10), (5, 7)],
    )
    before = env.state

    with pytest.raises(RuntimeError, match="terminal"):
        agent.choose_action(env)
    assert env.state == before


def test_incompatible_checkpoint_is_rejected(artifact_dir: Path):
    checkpoint = write_checkpoint(
        artifact_dir / "wrong-contract.pt",
        contract_version="caro-v1",
    )
    with pytest.raises(ValueError, match="contract_version"):
        NeuralAgent(checkpoint)

    valid = write_checkpoint(artifact_dir / "wrong-dataset.pt")
    with pytest.raises(ValueError, match="dataset_version"):
        NeuralAgent(valid, expected_dataset_version="another-dataset")
    with pytest.raises(ValueError, match="checksum"):
        NeuralAgent(valid, expected_dataset_manifest_sha256="b" * 64)


def test_neural_agent_completes_a_runner_game(artifact_dir: Path):
    checkpoint = write_checkpoint(artifact_dir / "policy.pt")
    neural = Participant("neural", NeuralAgent(checkpoint))
    random = Participant("random", RandomAgent(seed=7))

    outcome = play_game(
        CaroEnv,
        neural,
        random,
        game_id="neural-runner-smoke",
        seed=17,
    )

    assert outcome.record.terminated
    assert outcome.record.moves
    assert len(outcome.record.moves) <= 121
