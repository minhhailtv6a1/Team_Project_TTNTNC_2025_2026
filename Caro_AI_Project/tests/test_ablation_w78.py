"""Paired design, frozen input, genuine counters and auditable raw outputs."""
import copy
import json

import pytest

from benchmarks.run_ablation_w78 import (
    DEFAULT_CONFIG, a1_job, a2_job, atomic_json, baseline_status, canonical_hash,
    digest, load_config, load_raw, replay_record, schedule, select_cases, summarize,
)


def test_config_freezes_exactly_two_ablations_and_thirty_paired_seeds():
    config = load_config()
    assert len(config["seed_indices"]) == 30
    jobs = schedule(config)
    assert len(jobs) == 120
    assert len({name for name, _ in jobs}) == 120
    assert config["a2"]["simulations"] == [100, 400, 1000]
    assert "default_simulations" not in config["a2"]["options"]
    # Every seed occurs once in A1 and once in every A2 profile.
    for index in config["seed_indices"]:
        assert len([spec for _, spec in jobs if spec[2] == index]) == 4


@pytest.mark.parametrize("change", ["seeds", "budgets", "sources", "options"])
def test_config_rejects_unpaired_or_unfrozen_changes(tmp_path, change):
    config = load_config()
    if change == "seeds":
        config["seed_indices"] = [0] * 30
    elif change == "budgets":
        config["a2"]["simulations"] = [10, 20, 30]
    elif change == "sources":
        config["frozen_sources"] = {}
    else:
        config["a2"]["options"]["default_simulations"] = 100
    path = tmp_path / "config.json"
    atomic_json(path, config)
    with pytest.raises(ValueError):
        load_config(path)


def test_a1_actual_search_preserves_action_score_and_reduces_nodes():
    config = copy.deepcopy(load_config())
    config["a1"]["scenarios"] = ["midgame_x", "near_full_x"]
    shard = a1_job(config, 0)
    for name in config["a1"]["scenarios"]:
        off, on = sorted((r for r in shard["rows"] if r["scenario"] == name), key=lambda r: r["alpha_beta"])
        assert (off["action"], off["score"]) == (on["action"], on["score"])
        assert on["nodes"] <= off["nodes"]
        assert on["wall_ms"] >= 0


@pytest.fixture(scope="module")
def actual_a2_pair():
    return a2_job(load_config(), 0, 100)


def test_a2_actual_pair_starts_empty_swaps_sides_and_replays(actual_a2_pair):
    pair = actual_a2_pair
    assert len(pair["games"]) == 2
    assert [g["candidate_side"] for g in pair["games"]] == [1, -1]
    assert len({g["record"]["seed"] for g in pair["games"]}) == 1
    for game in pair["games"]:
        record = replay_record(game["record"])
        assert record.moves[0].ply == 1
        parity = 0 if game["candidate_side"] == 1 else 1
        assert len(game["candidate_times_ms"]) == len(record.moves[parity::2])
        assert game["completed_simulations"] == sum(m.simulations for m in record.moves[parity::2])


def test_summary_counts_wdl_per_move_latency_and_seed_pairs(actual_a2_pair):
    shards = [actual_a2_pair]
    # The synthetic copy tests aggregation, not the quality of a second budget.
    other = copy.deepcopy(actual_a2_pair)
    other["requested_simulations"] = 400
    shards.append(other)
    summary = summarize(shards)
    for row in summary["a2"]:
        assert row["games"] == row["wins"] + row["draws"] + row["losses"] == 2
        assert row["score_rate"] == pytest.approx((row["wins"] + .5 * row["draws"]) / 2)
        times = [t for g in actual_a2_pair["games"] for t in g["candidate_times_ms"]]
        assert row["mean_ms"] == pytest.approx(sum(times) / len(times))
    assert summary["paired"][0]["mean_score_delta"] == 0


def test_checksum_validation_rejects_tampered_raw_shard(tmp_path):
    config = load_config()
    shards = {}
    for name, _ in schedule(config):
        path = tmp_path / "raw" / f"{name}.json"
        atomic_json(path, {"experiment": "unit-test-only"})
        shards[name] = digest(path)
    atomic_json(tmp_path / "manifest.json", {"complete": True, "config": config, "shards": shards})
    assert len(load_raw(tmp_path)[1]) == 120
    first = next(iter(shards))
    atomic_json(tmp_path / "raw" / f"{first}.json", {"tampered": True})
    with pytest.raises(ValueError, match="checksum"):
        load_raw(tmp_path)


def test_baseline_gate_rejects_assertion_failures(tmp_path):
    path = tmp_path / "baseline.xml"
    path.write_text('<testsuites><testsuite tests="10" failures="1" errors="0" skipped="0"/></testsuites>')
    assert not baseline_status(path)["pass"]
    path.write_text('<testsuites><testsuite tests="10" failures="0" errors="0" skipped="2"/></testsuites>')
    assert baseline_status(path)["pass"]


def test_case_selection_never_fabricates_or_duplicates_trajectories(actual_a2_pair):
    selected = select_cases([actual_a2_pair, actual_a2_pair])
    for kind in ("win", "failure"):
        trajectories = [g["trajectory_sha256"] for k, g in selected if k == kind]
        assert len(trajectories) == len(set(trajectories))
    assert select_cases([]) == []


def test_canonical_hash_ignores_dictionary_order():
    assert canonical_hash({"seed": 1, "budget": 100}) == canonical_hash({"budget": 100, "seed": 1})
