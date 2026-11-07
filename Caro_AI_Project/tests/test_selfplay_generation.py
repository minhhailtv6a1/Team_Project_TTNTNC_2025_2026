"""Tests for the three-agent, 20-games-per-pair self-play pilot."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.engine.interfaces import AgentDecision
from core.utils.logger import load_games
from scripts.generate_selfplay import SelfPlayConfigError, load_selfplay_config, run_pilot


class FirstLegalAgent:
    """Fast deterministic agent used only to test generator plumbing."""

    def __init__(self, name: str = "test") -> None:
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def choose_action(self, env, budget=None) -> AgentDecision:
        return AgentDecision(env.legal_actions()[0], nodes=1)


def _config() -> dict:
    factory = "test_selfplay_generation:FirstLegalAgent"
    return {
        "contract_version": "caro-v2",
        "run_id": "test-three-agent-pilot",
        "game_config": {"board_size": 11, "win_length": 5},
        "base_seed": 7,
        "games_per_pair": 20,
        "swap_sides": True,
        "agents": {
            name: {"factory": factory, "options": {"name": name}, "budget": {}}
            for name in ("heuristic", "minimax", "mcts")
        },
        "pairs": [
            ["heuristic", "minimax"],
            ["heuristic", "mcts"],
            ["minimax", "mcts"],
        ],
    }


def test_pilot_runs_all_three_pairs_with_twenty_balanced_games(tmp_path):
    manifest_path = run_pilot(_config(), tmp_path)
    records = load_games(tmp_path / "shard_000.jsonl")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert len(records) == 60
    assert len({record.game_id for record in records}) == 60
    assert all(record.game_id.startswith("test-three-agent-pilot-") for record in records)
    assert manifest["successful_games"] == 60
    assert manifest["shards"][0]["games"] == 60
    for left, right in _config()["pairs"]:
        pair_records = [
            record for record in records if {record.x_agent, record.o_agent} == {left, right}
        ]
        assert len(pair_records) == 20
        assert sum(record.x_agent == left for record in pair_records) == 10
        assert sum(record.x_agent == right for record in pair_records) == 10


def test_config_accepts_the_balanced_2000_game_dataset_plan(tmp_path):
    config = _config()
    config.pop("games_per_pair")
    config["pair_games"] = [668, 666, 666]
    path = tmp_path / "dataset.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    loaded = load_selfplay_config(path)
    assert loaded["_games_by_pair"] == [668, 666, 666]
    assert sum(loaded["_games_by_pair"]) == 2_000


def test_config_rejects_an_odd_pair_count(tmp_path):
    config = _config()
    config.pop("games_per_pair")
    config["pair_games"] = [668, 665, 667]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(SelfPlayConfigError, match="even"):
        load_selfplay_config(path)
