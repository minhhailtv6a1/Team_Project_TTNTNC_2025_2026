"""Rebuild Week-7 tables and statistics from canonical tournament JSONL logs."""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
import statistics
import sys
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.interfaces import Player
from core.utils.logger import read_games


def percentile95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    """Two-sided 95% Wilson interval for a binomial proportion."""
    if total == 0:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half_width = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - half_width), min(1.0, centre + half_width)]


def score_for(record: Any, label: str) -> float:
    side = Player.X if record.x_agent == label else Player.O
    if record.winner is None:
        return 0.5
    return 1.0 if record.winner == side else 0.0


def _blank() -> dict[str, Any]:
    return {"games": 0, "wins": 0, "draws": 0, "losses": 0, "times": [], "nodes": 0, "simulations": 0}


def _add(acc: dict[str, Any], record: Any, label: str) -> None:
    acc["games"] += 1
    side = Player.X if record.x_agent == label else Player.O
    if record.winner is None:
        acc["draws"] += 1
    elif record.winner == side:
        acc["wins"] += 1
    else:
        acc["losses"] += 1
    parity = 0 if side == Player.X else 1
    for index, move in enumerate(record.moves):
        if index % 2 == parity:
            acc["times"].append(float(move.elapsed_ms))
            acc["nodes"] += int(move.nodes)
            acc["simulations"] += int(move.simulations)


def _finish(acc: dict[str, Any]) -> dict[str, Any]:
    games, times = acc["games"], acc["times"]
    return {
        "games": games, "wins": acc["wins"], "draws": acc["draws"], "losses": acc["losses"],
        "score_rate": (acc["wins"] + 0.5 * acc["draws"]) / games if games else None,
        "win_ci95": wilson_interval(acc["wins"], games),
        "draw_ci95": wilson_interval(acc["draws"], games),
        "loss_ci95": wilson_interval(acc["losses"], games),
        "moves": len(times), "mean_move_ms": statistics.fmean(times) if times else None,
        "p95_move_ms": percentile95(times), "total_nodes": acc["nodes"],
        "mean_nodes_per_move": acc["nodes"] / len(times) if times else None,
        "total_simulations": acc["simulations"],
        "mean_simulations_per_move": acc["simulations"] / len(times) if times else None,
    }


def analyze_records(records: Iterable[Any], profile: str) -> dict[str, Any]:
    records = list(records)
    ids = [record.game_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{profile}: duplicate game_id in raw log")
    labels = sorted({name for record in records for name in (record.x_agent, record.o_agent)})
    overall = {label: _blank() for label in labels}
    as_x = {label: _blank() for label in labels}
    as_o = {label: _blank() for label in labels}
    pairs: dict[tuple[str, str], dict[str, dict[str, Any]]] = {}
    paired_seed_scores: dict[str, dict[int, list[float]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        pair = tuple(sorted((record.x_agent, record.o_agent)))
        table = pairs.setdefault(pair, {label: _blank() for label in pair})
        for label in pair:
            _add(overall[label], record, label)
            _add(as_x[label] if record.x_agent == label else as_o[label], record, label)
            _add(table[label], record, label)
            if record.seed is not None:
                paired_seed_scores[label][int(record.seed)].append(score_for(record, label))

    agent_summary = {
        label: {"overall": _finish(overall[label]), "as_x": _finish(as_x[label]), "as_o": _finish(as_o[label])}
        for label in labels
    }
    for label in labels:
        per_seed = [statistics.fmean(scores) for scores in paired_seed_scores[label].values()]
        agent_summary[label]["seed_sensitivity"] = {
            "paired_seed_groups": len(per_seed),
            "score_mean": statistics.fmean(per_seed) if per_seed else None,
            "score_sample_stdev": statistics.stdev(per_seed) if len(per_seed) >= 2 else None,
            "note": "Paired trajectories may be deterministic; CI assumes independent games and must be interpreted cautiously.",
        }

    pair_rows: list[dict[str, Any]] = []
    for (left, right), table in sorted(pairs.items()):
        a, b = _finish(table[left]), _finish(table[right])
        pair_rows.append({
            "profile": profile, "agent_a": left, "agent_b": right, "games": a["games"],
            "a_wins": a["wins"], "draws": a["draws"], "b_wins": a["losses"],
            "a_score_rate": a["score_rate"], "b_score_rate": b["score_rate"],
            "a_win_ci95": a["win_ci95"], "b_win_ci95": b["win_ci95"],
        })
    return {"profile": profile, "games": len(records), "agents": agent_summary, "pair_matrix": pair_rows}


def _json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else "" if value is None else str(value)


def _wdl(value: dict[str, Any]) -> str:
    return f"{value['wins']}/{value['draws']}/{value['losses']}"


def _percent(value: float | None) -> str:
    return "—" if value is None else f"{value * 100:.2f}%"


def _number(value: float | None, digits: int = 2) -> str:
    return "—" if value is None else f"{value:.{digits}f}"


def render_markdown_summary(analysis: dict[str, Any]) -> str:
    """Render human-readable tables while retaining JSON as the source of truth."""
    lines = ["# W78 tournament summary", "", "Generated from `analysis.json`; W/D/L is from the agent perspective.", ""]
    for profile, result in analysis["profiles"].items():
        manifest = result.get("manifest", {})
        lines.extend([
            f"## {profile}", "",
            f"- Games: **{result['games']}**; pairs: **{len(result['pair_matrix'])}**; budget violations: **{result.get('budget_violations', 0)}**.",
            f"- Checkpoint SHA-256: `{manifest.get('checkpoint_sha256', '—')}`.", "",
            "### Overall agent statistics", "",
            "|Agent|W/D/L|Score|Win 95% CI|Mean / p95 move (ms)|Nodes/move|Sims/move|Seed score SD|",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ])
        ordered_agents = sorted(
            result["agents"].items(), key=lambda item: item[1]["overall"]["score_rate"], reverse=True
        )
        for agent, values in ordered_agents:
            stats, sensitivity = values["overall"], values["seed_sensitivity"]
            ci = stats["win_ci95"]
            ci_text = "—" if ci is None else f"{ci[0] * 100:.2f}–{ci[1] * 100:.2f}%"
            lines.append(
                f"|{agent}|{_wdl(stats)}|{_percent(stats['score_rate'])}|{ci_text}|"
                f"{_number(stats['mean_move_ms'])} / {_number(stats['p95_move_ms'])}|"
                f"{_number(stats['mean_nodes_per_move'])}|{_number(stats['mean_simulations_per_move'])}|"
                f"{_number(sensitivity['score_sample_stdev'], 3)}|"
            )

        lines.extend(["", "### Side split", "", "|Agent|As X: W/D/L (score)|As O: W/D/L (score)|", "|---|---:|---:|"])
        for agent, values in ordered_agents:
            x, o = values["as_x"], values["as_o"]
            lines.append(f"|{agent}|{_wdl(x)} ({_percent(x['score_rate'])})|{_wdl(o)} ({_percent(o['score_rate'])})|")

        lines.extend(["", "### Pair matrix", "", "|Pair|W/D/L (agent A)|Score A|Score B|", "|---|---:|---:|---:|"])
        for row in result["pair_matrix"]:
            lines.append(
                f"|{row['agent_a']} vs {row['agent_b']}|{row['a_wins']}/{row['draws']}/{row['b_wins']}|"
                f"{_percent(row['a_score_rate'])}|{_percent(row['b_score_rate'])}|"
            )
        lines.append("")
    lines.extend([
        "## Interpretation note", "",
        "Wilson intervals assume independent games. Deterministic paired trajectories reduce effective independence; interpret them together with the seed-score standard deviation rather than as a standalone significance claim.", "",
    ])
    return "\n".join(lines)


def write_analysis(results_dir: Path, profiles: list[str]) -> dict[str, Any]:
    output: dict[str, Any] = {"schema": "caro-w78-analysis-v1", "profiles": {}}
    csv_rows: list[dict[str, Any]] = []
    for profile in profiles:
        profile_dir = results_dir / profile.lower()
        records = list(read_games(profile_dir / "games.jsonl"))
        result = analyze_records(records, profile)
        manifest_path = profile_dir / "manifest.json"
        if manifest_path.is_file():
            result["manifest"] = json.loads(manifest_path.read_text(encoding="utf-8"))
        violations_path = profile_dir / "violations.jsonl"
        result["budget_violations"] = sum(1 for line in violations_path.open(encoding="utf-8") if line.strip()) if violations_path.is_file() else 0
        output["profiles"][profile] = result
        csv_rows.extend(result["pair_matrix"])
    (results_dir / "analysis.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (results_dir / "pair_matrix.csv").open("w", newline="", encoding="utf-8") as target:
        fields = ["profile", "agent_a", "agent_b", "games", "a_wins", "draws", "b_wins", "a_score_rate", "b_score_rate", "a_win_ci95", "b_win_ci95"]
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows([{key: _json_cell(row.get(key)) for key in fields} for row in csv_rows])
    (results_dir / "summary.md").write_text(render_markdown_summary(output), encoding="utf-8")
    return output


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=PROJECT_ROOT / "results/w78")
    parser.add_argument("--profile", choices=("DEFAULT", "FAIR", "ALL"), default="ALL")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    profiles = ["DEFAULT", "FAIR"] if args.profile == "ALL" else [args.profile]
    result = write_analysis(args.results_dir, profiles)
    for profile, value in result["profiles"].items():
        print(f"{profile}: {value['games']} games, {len(value['pair_matrix'])} pairs, violations={value['budget_violations']}")
    print(f"analysis -> {args.results_dir / 'analysis.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
