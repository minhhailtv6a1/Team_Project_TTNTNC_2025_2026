from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_tournament_w78 import AGENT_NAMES, load_w78_config, planned_games


def test_frozen_config_declares_five_agents_two_profiles_and_real_checkpoint():
    config_path = PROJECT_ROOT / "configs/tournament_w78.json"
    config = load_w78_config(config_path)
    assert tuple(config["agents"]) == AGENT_NAMES
    assert set(config["profiles"]) == {"DEFAULT", "FAIR"}
    assert (PROJECT_ROOT / config["checkpoint"]).is_file()
    assert config["games_per_pair"] == 100


def test_schedule_has_ten_pairs_balanced_sides_and_paired_seeds():
    schedule = planned_games("DEFAULT", AGENT_NAMES, games_per_pair=100, base_seed=42)
    assert len(schedule) == 10 * 100
    seen = set()
    for game_index in range(0, len(schedule), 2):
        first, second = schedule[game_index], schedule[game_index + 1]
        assert first[0] not in seen
        seen.update((first[0], second[0]))
        assert first[1] == second[2] and first[2] == second[1]
        assert first[3] == second[3]
    counts = {name: {"x": 0, "o": 0} for name in AGENT_NAMES}
    for _, x, o, _ in schedule:
        counts[x]["x"] += 1
        counts[o]["o"] += 1
    assert all(value["x"] == value["o"] == 200 for value in counts.values())


def test_config_checksum_input_is_stable_json():
    path = PROJECT_ROOT / "configs/tournament_w78.json"
    assert json.loads(path.read_text(encoding="utf-8"))["schema"] == "caro-w78-tournament-v1"
