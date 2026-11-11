from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.interfaces import GameConfig, GameRecord, MoveRecord, Player
from scripts.analyze_results_w78 import analyze_records, render_markdown_summary, wilson_interval


def _record(game_id: str, seed: int, x: str, o: str, winner: Player | None) -> GameRecord:
    return GameRecord(
        contract_version="caro-v2", game_id=game_id, config=GameConfig(), seed=seed,
        x_agent=x, o_agent=o,
        moves=[
            MoveRecord(1, Player.X, (5, 5), 0.0, 2.0, 3, 0),
            MoveRecord(2, Player.O, (5, 6), 0.0, 4.0, 0, 7),
        ], terminated=True, winner=winner,
    )


def test_wilson_interval_is_bounded_and_ordered():
    low, high = wilson_interval(7, 10)  # type: ignore[misc]
    assert 0 <= low <= 0.7 <= high <= 1


def test_analysis_reports_wdl_sides_costs_and_seed_note():
    result = analyze_records([
        _record("g1", 10, "a", "b", Player.X),
        _record("g2", 10, "b", "a", None),
    ], "DEFAULT")
    a = result["agents"]["a"]
    assert a["overall"]["wins"] == 1
    assert a["overall"]["draws"] == 1
    assert a["as_x"]["games"] == a["as_o"]["games"] == 1
    assert a["overall"]["mean_move_ms"] == 3.0
    assert a["overall"]["total_nodes"] == 3
    assert a["seed_sensitivity"]["paired_seed_groups"] == 1
    assert len(result["pair_matrix"]) == 1


def test_markdown_summary_contains_overall_side_and_pair_tables():
    profile = analyze_records([_record("g1", 10, "a", "b", Player.X)], "DEFAULT")
    rendered = render_markdown_summary({"profiles": {"DEFAULT": profile}})
    assert "Overall agent statistics" in rendered
    assert "Side split" in rendered
    assert "a vs b" in rendered
