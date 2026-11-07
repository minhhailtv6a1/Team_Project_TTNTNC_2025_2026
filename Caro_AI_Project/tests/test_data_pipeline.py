"""Contract tests for the Week 5 raw self-play schema and fixture."""
from __future__ import annotations

from pathlib import Path

import json
import numpy as np

import pytest

from core.agents.random_ai import RandomAgent
from core.engine.game_env import CaroEnv
from core.engine.interfaces import Player, SearchBudget
from core.ml.data_pipeline import (
    RAW_SCHEMA_NAME,
    RawDataError,
    d4_augment,
    build_dataset,
    iter_raw_games,
    replay_raw_game,
    load_dataset_split,
    sha256_file,
    samples_from_raw_game,
    split_game_ids,
)
from core.utils.logger import GameLogger, game_to_dict, write_manifest
from core.utils.tournament_runner import Participant, play_game, run_match


FIXTURE = Path(__file__).parent / "fixtures" / "w56_selfplay_one_game.jsonl"


def test_raw_fixture_uses_versioned_schema_and_replays_to_terminal():
    records = list(iter_raw_games(FIXTURE))

    assert RAW_SCHEMA_NAME == "caro-w56-raw-v1"
    assert len(records) == 1
    record = records[0]
    assert record.game_id == "w56-fixture-0000-s314159-heuristic-x"
    assert record.config.board_size == 11
    assert record.x_agent == "HeuristicAgent"
    assert record.o_agent == "MCTSAgent"
    assert [move.ply for move in record.moves] == list(range(1, 10))

    env = replay_raw_game(record)
    assert env.is_terminal()
    assert env.state.winner == Player.X
    assert env.state.move_count == 9


def test_raw_fixture_has_a_stable_pre_move_encoder_case():
    record = next(iter_raw_games(FIXTURE))
    env = replay_raw_game(record)  # first prove the complete raw fixture is valid

    # The pre-move state for ply 7 is part of the M1/M3 encoder hand-off.
    # Recreate it independently from an empty board, never from a raw tensor.
    from core.engine.game_env import CaroEnv

    sample_env = CaroEnv(record.config)
    for move in record.moves[:6]:
        sample_env.step(move.action)
    assert sample_env.state.current_player == Player.X
    assert sample_env.state.board[5][2:5] == [1, 1, 1]
    assert sample_env.state.board[0][0] == -1
    assert record.moves[6].action == (5, 5)
    assert record.moves[6].action in sample_env.legal_actions()
    assert env.state.winner == Player.X


def test_replay_rejects_reward_that_disagrees_with_engine():
    record = next(iter_raw_games(FIXTURE))
    payload = game_to_dict(record)
    payload["moves"][-1]["reward"] = 0.0
    from core.utils.logger import game_from_dict

    with pytest.raises(RawDataError, match="reward"):
        replay_raw_game(game_from_dict(payload))


def test_samples_have_perspective_channels_and_legal_target():
    samples = samples_from_raw_game(next(iter_raw_games(FIXTURE)))
    sample = samples[6]  # state before X plays (5, 5)

    assert len(samples) == 9
    assert sample.x.shape == (3, 11, 11)
    assert sample.x.dtype.name == "float32"
    assert sample.target == 60 and sample.legal_mask[sample.target]
    assert sample.x[0, 5, 2:5].tolist() == [1.0, 1.0, 1.0]
    assert sample.x[1, 0, 0] == 1.0


def test_d4_transforms_keep_mask_and_target_aligned():
    sample = samples_from_raw_game(next(iter_raw_games(FIXTURE)))[6]
    variants = d4_augment(sample)

    assert len(variants) == 8
    for variant in variants:
        assert variant.legal_mask[variant.target]
        assert (variant.x[2].reshape(-1).astype(bool) == variant.legal_mask).all()


def test_game_split_is_deterministic_and_disjoint():
    ids = [f"g{i}" for i in range(20)]
    split = split_game_ids(ids, seed=9)

    assert split == split_game_ids(reversed(ids), seed=9)
    assert len(split["train"]) == 14 and len(split["val"]) == len(split["test"]) == 3
    assert not (set(split["train"]) & set(split["val"]))
    assert not (set(split["train"]) & set(split["test"]))


def test_public_loader_validates_and_returns_training_arrays(tmp_path):
    tensor_path = tmp_path / "train.npz"
    x = np.zeros((2, 3, 11, 11), dtype=np.float32)
    legal = np.ones((2, 121), dtype=bool)
    target = np.array([0, 120], dtype=np.int64)
    np.savez_compressed(tensor_path, x=x, legal_mask=legal, target=target)
    (tmp_path / "dataset_manifest.json").write_text(json.dumps({
        "contract_version": "caro-v2", "board_size": 11,
        "artifacts": {"train": {"tensor": "train.npz", "tensor_sha256": sha256_file(tensor_path)}},
    }), encoding="utf-8")

    loaded = load_dataset_split(tmp_path, "train")
    assert loaded["x"].shape == (2, 3, 11, 11)
    assert loaded["legal_mask"].dtype == bool
    assert loaded["target"].tolist() == [0, 120]


def test_integration_raw_replay_split_export_and_load_batch(tmp_path):
    raw_dir, dataset_dir = tmp_path / "raw", tmp_path / "dataset"
    raw_dir.mkdir()
    shard = raw_dir / "shard_000.jsonl"
    with GameLogger(shard, mode="w") as logger:
        outcomes = [
            play_game(
                CaroEnv,
                Participant("random-x", RandomAgent("random-x", seed=index)),
                Participant("random-o", RandomAgent("random-o", seed=100 + index)),
                game_id=f"integration-{index:03d}", seed=index, logger=logger,
            )
            for index in range(20)
        ]
    write_manifest(raw_dir / "run_manifest.json", {
        "run_id": "integration-fixture",
        "shards": [{"path": shard.name, "games": len(outcomes), "sha256": sha256_file(shard)}],
    })

    manifest = build_dataset(raw_dir, dataset_dir, {
        "contract_version": "caro-v2", "dataset_version": "fixture-v1",
        "split_seed": 7, "train_d4_augmentation": False,
    })
    write_manifest(dataset_dir / "dataset_manifest.json", manifest)
    assert manifest["validation"]["games"] == {"train": 14, "val": 3, "test": 3}
    for split in ("train", "val", "test"):
        batch = load_dataset_split(dataset_dir, split)
        assert batch["x"].shape[1:] == (3, 11, 11)
        assert np.all(batch["legal_mask"][np.arange(len(batch["target"])), batch["target"]])
