from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.policy_acceptance import FIXTURES, build_env, load_cases
from core.agents.heuristic_ai import HeuristicAgent
from core.agents.mcts_ai import MCTSAgent
from core.agents.minimax_ai import MinimaxAgent
from core.engine.game_env import CaroEnv
from core.engine.interfaces import SearchBudget
from core.utils.logger import game_from_dict, game_to_dict, validate_game_record
from core.utils.tournament_runner import Participant, derive_seed, play_game

DEFAULT_CONFIG = ROOT / "configs/ablation_w78.json"
DEFAULT_OUTPUT = ROOT / "results/w78_ablation_ly"
DEFAULT_ASSETS = ROOT / "docs/report/assets"
FROZEN_FILES = sorted(p for p in (ROOT / "core").rglob("*.py")) + [FIXTURES]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source_hashes():
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in FROZEN_FILES}


def load_config(path=DEFAULT_CONFIG):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if config.get("schema") != "caro-ablation-w78-v1" or config.get("contract_version") != "caro-v2":
        raise ValueError("Expected frozen caro-v2 ablation config")
    if config.get("status") != "frozen":
        raise ValueError("Config must be frozen before measurement")
    seeds = config["seed_indices"]
    if len(seeds) < 30 or len(set(seeds)) != len(seeds) or any(type(s) is not int or s < 0 for s in seeds):
        raise ValueError("At least 30 distinct nonnegative paired seeds are required")
    if config["a2"]["simulations"] != [100, 400, 1000]:
        raise ValueError("A2 must compare exactly 100/400/1000 simulations")
    if any(k in config["a2"]["options"] for k in ("default_simulations", "name", "seed")):
        raise ValueError("A2 options must be identical; simulation count belongs only to SearchBudget")
    if any(k in config["a1"]["options"] for k in ("alpha_beta", "name")):
        raise ValueError("A1 toggles alpha_beta separately from common options")
    if config["a1"]["depth"] < 1:
        raise ValueError("A1 depth must be positive")
    if config["frozen_sources"] != source_hashes():
        raise ValueError("Frozen core or fixture changed; create a new config/run version")
    available = {c["id"] for c in load_cases() if c["kind"] != "terminal"}
    if not set(config["a1"]["scenarios"]) <= available:
        raise ValueError("Unknown or terminal A1 scenario")
    return config


def baseline_status(path):
    path = Path(path)
    if not path.is_file():
        return {"pass": False, "reason": "Full regression JUnit XML is missing"}
    tree = ET.parse(path).getroot()
    suites = [tree] if tree.tag == "testsuite" else list(tree.findall("testsuite"))
    totals = {key: sum(int(s.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
    return {"pass": totals["tests"] > 0 and totals["failures"] == totals["errors"] == 0,
            **totals, "xml_sha256": digest(path)}


def a1_job(config, seed_index):
    seed = derive_seed(config["base_seed"], 1, seed_index)
    cases = {c["id"]: c for c in load_cases()}
    rows = []
    for name in config["a1"]["scenarios"]:
        env = build_env(cases[name])
        before = env.state
        order = (False, True) if seed_index % 2 == 0 else (True, False)
        for enabled in order:
            agent = MinimaxAgent(alpha_beta=enabled, **config["a1"]["options"])
            budget = SearchBudget(max_depth=config["a1"]["depth"], seed=seed)
            agent.choose_action(env, budget)  # Warm-up is outside the timer.
            started = time.perf_counter()
            decision = agent.choose_action(env, budget)
            elapsed = (time.perf_counter() - started) * 1000
            if env.state != before or decision.action not in env.legal_actions():
                raise RuntimeError("A1 mutated input or selected an illegal action")
            if decision.score is None:
                raise RuntimeError("A1 failed to complete its fixed depth")
            rows.append({"scenario": name, "seed_index": seed_index, "seed": seed,
                         "alpha_beta": enabled, "depth": config["a1"]["depth"],
                         **asdict(decision), "wall_ms": elapsed})
    for name in config["a1"]["scenarios"]:
        pair = [r for r in rows if r["scenario"] == name]
        if (pair[0]["action"], pair[0]["score"]) != (pair[1]["action"], pair[1]["score"]):
            raise RuntimeError(f"Alpha-Beta changed exact action/score: {name}")
    return {"experiment": "A1", "seed_index": seed_index, "rows": rows}


def replay_record(record):
    record = game_from_dict(record)
    validate_game_record(record)
    env = CaroEnv(record.config)
    for move in record.moves:
        if move.player != env.state.current_player:
            raise ValueError("Replay player mismatch")
        env.step(move.action)
    if not env.is_terminal() or env.state.winner != record.winner:
        raise ValueError("Replay result mismatch")
    return record


def a2_job(config, seed_index, simulations):
    seed = derive_seed(config["base_seed"], 2, seed_index)
    MCTSAgent(**config["a2"]["options"]).choose_action(
        CaroEnv(), SearchBudget(simulations=simulations, seed=seed))  # Untimed warm-up.
    games = []
    for candidate_side in (1, -1):
        candidate = Participant("mcts", MCTSAgent(**config["a2"]["options"]),
                                SearchBudget(simulations=simulations))
        opponent = Participant("heuristic", HeuristicAgent(**config["a2"]["opponent_options"]))
        x, o = (candidate, opponent) if candidate_side == 1 else (opponent, candidate)
        outcome = play_game(CaroEnv, x, o,
            game_id=f"A2-n{simulations}-s{seed_index}-side{candidate_side}", seed=seed)
        record = game_to_dict(outcome.record)
        replay_record(record)
        parity = 0 if candidate_side == 1 else 1
        times = outcome.wall_ms[parity::2]
        moves = outcome.record.moves[parity::2]
        if any(m.simulations not in (0, simulations) for m in moves):
            raise RuntimeError("MCTS failed to execute the requested simulation budget")
        score = 0.5 if record["winner"] is None else float(record["winner"] == candidate_side)
        games.append({"record": record, "wall_ms": list(outcome.wall_ms),
                      "candidate_side": candidate_side, "score": score,
                      "candidate_times_ms": list(times),
                      "completed_simulations": sum(m.simulations for m in moves),
                      "candidate_nodes": sum(m.nodes for m in moves),
                      "tactical_override_moves": sum(m.simulations == 0 for m in moves),
                      "trajectory_sha256": canonical_hash([m["action"] for m in record["moves"]])})
    return {"experiment": "A2", "seed_index": seed_index, "seed": seed,
            "requested_simulations": simulations, "games": games}


def execute_job(spec):
    kind, config, index, budget = spec
    return a1_job(config, index) if kind == "A1" else a2_job(config, index, budget)


def schedule(config):
    jobs = []
    for index in config["seed_indices"]:
        jobs.append((f"a1_{index:03d}", ("A1", config, index, None)))
        for budget in config["a2"]["simulations"]:
            jobs.append((f"a2_{budget}_{index:03d}", ("A2", config, index, budget)))
    return jobs


def run_experiments(config_path=DEFAULT_CONFIG, output=DEFAULT_OUTPUT, *, workers=3,
                    official=False, baseline_xml=None):
    config_path, output = Path(config_path), Path(output)
    config = load_config(config_path)
    regression = baseline_status(baseline_xml or ROOT / config["baseline_test_xml"])
    dirty = git("status", "--porcelain=v1", "--untracked-files=normal")
    if official and (dirty or not regression["pass"]):
        raise ValueError("Official ablations require a clean working tree and a passing full regression XML")
    identity = {"config_sha256": digest(config_path), "runner_sha256": digest(__file__),
                "frozen_sources": config["frozen_sources"], "git_commit": git("rev-parse", "HEAD"),
                "official": official, "workers": workers, "baseline_regression": regression}
    manifest_path = output / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["identity"] != identity:
            raise ValueError("Resume identity changed; use a new output directory")
    else:
        manifest = {"identity": identity, "config": config,
                    "hardware": {"platform": platform.platform(), "processor": platform.processor(),
                                 "logical_cpus": os.cpu_count(), "python": platform.python_version()},
                    "working_tree_at_start": dirty, "complete": False, "shards": {}}
        atomic_json(manifest_path, manifest)
    jobs = schedule(config)
    pending = []
    for name, spec in jobs:
        path = output / "raw" / f"{name}.json"
        if name in manifest["shards"]:
            if not path.is_file() or digest(path) != manifest["shards"][name]:
                raise ValueError(f"Raw shard checksum failed: {name}")
        else:
            pending.append((name, spec))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(execute_job, spec): name for name, spec in pending}
        for future in as_completed(futures):
            name = futures[future]
            path = output / "raw" / f"{name}.json"
            atomic_json(path, future.result())
            manifest["shards"][name] = digest(path)
            atomic_json(manifest_path, manifest)
            done = len(manifest["shards"])
            if done % 5 == 0 or done == len(jobs):
                print(f"Completed {done}/{len(jobs)} paired jobs", flush=True)
    if source_hashes() != config["frozen_sources"] or digest(__file__) != identity["runner_sha256"]:
        raise RuntimeError("Source changed during measurement")
    manifest["complete"] = len(manifest["shards"]) == len(jobs)
    atomic_json(manifest_path, manifest)
    return manifest


def percentile95(values):
    return sorted(values)[max(0, math.ceil(0.95 * len(values)) - 1)]


def load_raw(output):
    output = Path(output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    if not manifest["complete"] or set(manifest["shards"]) != {name for name, _ in schedule(manifest["config"])}:
        raise ValueError("The raw run is incomplete")
    shards = []
    for name, expected in sorted(manifest["shards"].items()):
        path = output / "raw" / f"{name}.json"
        if digest(path) != expected:
            raise ValueError(f"Raw shard checksum failed: {name}")
        shards.append(json.loads(path.read_text(encoding="utf-8")))
    return manifest, shards


def summarize(shards):
    a1, a2, paired, sensitivity = [], [], [], []
    rows = [row for shard in shards if shard["experiment"] == "A1" for row in shard["rows"]]
    for name in sorted({row["scenario"] for row in rows}):
        pair = {}
        for enabled in (False, True):
            group = [r for r in rows if r["scenario"] == name and r["alpha_beta"] == enabled]
            values = {(tuple(r["action"]), r["score"]) for r in group}
            if len(values) != 1:
                raise ValueError("Deterministic A1 action/score changed across seeds")
            action, score = next(iter(values))
            row = {"scenario": name, "alpha_beta": enabled, "runs": len(group), "action": str(action),
                   "score": score, "nodes_mean": statistics.fmean(r["nodes"] for r in group),
                   "mean_ms": statistics.fmean(r["wall_ms"] for r in group),
                   "p95_ms": percentile95([r["wall_ms"] for r in group])}
            pair[enabled] = row
            a1.append(row)
        if (pair[False]["action"], pair[False]["score"]) != (pair[True]["action"], pair[True]["score"]):
            raise ValueError("A1 equivalence failed")
        reduction = 1 - pair[True]["nodes_mean"] / pair[False]["nodes_mean"]
        for row in pair.values():
            row["node_reduction_fraction"] = reduction
    profiles = sorted({s["requested_simulations"] for s in shards if s["experiment"] == "A2"})
    for budget in profiles:
        group = [s for s in shards if s["experiment"] == "A2" and s["requested_simulations"] == budget]
        games = [g for s in group for g in s["games"]]
        times = [t for g in games for t in g["candidate_times_ms"]]
        a2.append({"simulations": budget, "paired_seeds": len(group), "games": len(games),
                   "wins": sum(g["score"] == 1 for g in games), "draws": sum(g["score"] == .5 for g in games),
                   "losses": sum(g["score"] == 0 for g in games),
                   "score_rate": statistics.fmean(g["score"] for g in games),
                   "score_as_x": statistics.fmean(g["score"] for g in games if g["candidate_side"] == 1),
                   "score_as_o": statistics.fmean(g["score"] for g in games if g["candidate_side"] == -1),
                   "mean_ms": statistics.fmean(times), "p95_ms": percentile95(times),
                   "agent_moves": len(times), "actual_simulations": sum(g["completed_simulations"] for g in games),
                   "nodes": sum(g["candidate_nodes"] for g in games),
                   "tactical_override_moves": sum(g["tactical_override_moves"] for g in games),
                   "unique_trajectories": len({g["trajectory_sha256"] for g in games}),
                   "seed_score_std": statistics.pstdev(statistics.fmean(g["score"] for g in s["games"]) for s in group)})
        for shard in group:
            sensitivity.append({"simulations": budget, "seed_index": shard["seed_index"], "seed": shard["seed"],
                "paired_score": statistics.fmean(g["score"] for g in shard["games"]),
                "score_as_x": shard["games"][0]["score"], "score_as_o": shard["games"][1]["score"]})
    if profiles:
        baseline = profiles[0]
        for budget in profiles[1:]:
            low = {r["seed_index"]: r["paired_score"] for r in sensitivity if r["simulations"] == baseline}
            high = {r["seed_index"]: r["paired_score"] for r in sensitivity if r["simulations"] == budget}
            if low.keys() != high.keys():
                raise ValueError("A2 profiles do not share the same paired seeds")
            differences = [high[index] - low[index] for index in sorted(low)]
            paired.append({"comparison": f"{budget}-{baseline}", "paired_seeds": len(differences),
                           "mean_score_delta": statistics.fmean(differences),
                           "seed_delta_std": statistics.pstdev(differences)})
    return {"a1": a1, "a2": a2, "paired": paired, "sensitivity": sensitivity}


def select_cases(shards):
    selected = []
    games = [g for s in shards if s["experiment"] == "A2" for g in s["games"]]
    # Choose distinct trajectories, not four copies of an identical seeded game.
    for outcome, wanted in ((1, "win"), (0, "failure")):
        seen = set()
        for game in games:
            if game["score"] == outcome and game["trajectory_sha256"] not in seen:
                selected.append((wanted, game))
                seen.add(game["trajectory_sha256"])
                if len(seen) == 2:
                    break
    return selected


def render_cases(shards, assets):
    import matplotlib.pyplot as plt
    from core.engine.rules import RuleEngine

    cases = []
    for index, (kind, game) in enumerate(select_cases(shards), 1):
        record = game["record"]
        replay_record(record)
        side = game["candidate_side"]
        candidate_indices = [i for i, m in enumerate(record["moves"]) if m["player"] == side]
        chosen = candidate_indices[-1]
        env = CaroEnv()
        for move in record["moves"][:chosen]:
            env.step(tuple(move["action"]))
        board = env.state.board
        def winning_actions(player):
            found = []
            for row, col in env.legal_actions():
                trial = [r[:] for r in board]
                trial[row][col] = player
                if any(RuleEngine.check_line(trial, row, col, dr, dc, player, 11, 5)
                       for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1))):
                    found.append((row, col))
            return found
        own_wins, threats = winning_actions(side), winning_actions(-side)
        action = tuple(record["moves"][chosen]["action"])
        filename = f"case_{index}_{kind}.svg"
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set(xticks=range(11), yticks=range(11), xlim=(-.5,10.5), ylim=(10.5,-.5),
               xlabel="Column (0-based)", ylabel="Row (0-based)", title=f"{kind}: {record['game_id']}\nbefore ply {chosen+1}, MCTS={'X' if side==1 else 'O'}")
        ax.grid(alpha=.4)
        for row in range(11):
            for col in range(11):
                if board[row][col]:
                    ax.text(col, row, "X" if board[row][col] == 1 else "O", ha="center", va="center", fontsize=15)
        ax.scatter([action[1]], [action[0]], s=220, facecolors="none", edgecolors="green", linewidths=2, label="Actual move")
        if threats:
            ax.scatter([a[1] for a in threats], [a[0] for a in threats], marker="s", s=260, facecolors="none", edgecolors="red", label="Opponent immediate wins")
        ax.legend(loc="upper left", fontsize=7)
        fig.tight_layout(); fig.savefig(assets / filename); plt.close(fig)
        note = ("MCTS chọn nước thắng ngay hợp lệ." if action in own_wins else
                "Có nhiều hơn một nước thắng ngay của đối thủ: một nước chặn không thể giải hết threat." if len(threats) > 1 else
                "MCTS bỏ sót nước chặn threat duy nhất." if len(threats) == 1 and action != threats[0] else
                "Ở snapshot này chưa có nước thắng/chặn tức thời; cần phân tích các ply trước, không quy nguyên nhân chỉ cho nước cuối.")
        cases.append({"kind": kind, "game_id": record["game_id"], "candidate_side": side,
                      "winner": record["winner"], "ply": chosen+1, "action": action,
                      "own_immediate_wins": own_wins, "opponent_immediate_wins": threats,
                      "board_before": board, "snapshot": filename, "note": note,
                      "raw_trajectory_sha256": game["trajectory_sha256"]})
    return cases


def analyze(output=DEFAULT_OUTPUT, assets=DEFAULT_ASSETS):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    output, assets = Path(output), Path(assets)
    manifest, shards = load_raw(output)
    assets.mkdir(parents=True, exist_ok=True)
    summary = summarize(shards)
    for key, rows in summary.items():
        pd.DataFrame(rows).to_csv(assets / f"ablation_{key}.csv", index=False)
    a1, a2 = pd.DataFrame(summary["a1"]), pd.DataFrame(summary["a2"])
    fig, axes = plt.subplots(1,2,figsize=(12,4))
    a1.pivot(index="scenario",columns="alpha_beta",values="nodes_mean").plot.bar(ax=axes[0], ylabel="Mean nodes (step calls)", title="A1: same state/depth")
    a1.pivot(index="scenario",columns="alpha_beta",values="mean_ms").plot.bar(ax=axes[1], ylabel="Mean decision latency (ms)")
    fig.tight_layout(); fig.savefig(assets / "ablation_a1.svg"); plt.close(fig)
    fig, axes = plt.subplots(1,2,figsize=(10,4))
    axes[0].plot(a2["simulations"],a2["score_rate"],marker="o")
    axes[0].set(xlabel="Requested simulations",ylabel="Score rate vs Heuristic",ylim=(-.05,1.05))
    axes[1].plot(a2["simulations"],a2["mean_ms"],marker="o",label="mean")
    axes[1].plot(a2["simulations"],a2["p95_ms"],marker="o",label="p95")
    axes[1].set(xlabel="Requested simulations",ylabel="Decision latency (ms)"); axes[1].legend()
    fig.tight_layout(); fig.savefig(assets / "ablation_a2.svg"); plt.close(fig)
    cases = render_cases(shards, assets)
    atomic_json(assets / "tactical_cases.json", cases)
    atomic_json(assets / "ablation_summary.json", {"manifest_sha256": digest(output / "manifest.json"), **summary})
    def table(rows):
        if not rows:
            return "Không có dữ liệu."
        columns = list(rows[0])
        lines = ["|"+"|".join(columns)+"|", "|"+"|".join("---" for _ in columns)+"|"]
        for row in rows:
            lines.append("|"+"|".join(f"{row[c]:.4f}" if isinstance(row[c],float) else str(row[c]) for c in columns)+"|")
        return "\n".join(lines)
    text = ["# Hai ablation tuần 7–8 — Ly", "", f"Run: `{manifest['config']['run_id']}`; commit `{manifest['identity']['git_commit']}`; official={manifest['identity']['official']}.",
            "", "## A1 — Alpha-Beta ON/OFF", "", table(summary["a1"]), "",
            "Action và score trùng trong mọi cặp. Node là số lần step, cộng dồn iterative deepening; không phải số state duy nhất. Đây là 30 phép lặp thời gian trên từng state cố định, không phải 30 vị trí chiến thuật độc lập.",
            "", "## A2 — Chỉ thay simulations", "", table(summary["a2"]), "", table(summary["paired"]), "",
            "Mỗi mức có 30 cặp seed × 2 vai = 60 ván từ bàn rỗng, cùng đối thủ Heuristic. Rollout random có horizon 4, leaf evaluation pattern; các tham số khác giữ nguyên. Đây là cấu hình ablation công bố riêng, không đồng nhất với MCTS 8 simulations/epsilon_heuristic của tournament.",
            "Tactical pre-check có thể trả ngay với 0 simulations; bảng ghi cả tổng simulations thực tế và số nước override. Latency dùng thời gian bao quanh choose_action, không gồm render.",
            "Seed sensitivity nằm trong ablation_sensitivity.csv; paired delta dùng cùng seed giữa các ngân sách. Các trajectory trùng không được coi là quan sát độc lập. Chênh lệch X/O là mô tả theo vai, không chứng minh quan hệ nhân quả hoặc sức mạnh tổng quát.",
            "", "## Hai ván thắng và hai failure case", ""]
    for case in cases:
        text.extend([f"### {case['kind']} — {case['game_id']}", "", f"![Snapshot]({case['snapshot']})", "",
                     f"MCTS là {'X (đi trước)' if case['candidate_side']==1 else 'O (đi sau)'}, ply {case['ply']}, action {case['action']}. {case['note']}", ""])
    if len(cases) < 4:
        text.append("Chưa đủ hai trajectory thắng và hai trajectory thua phân biệt trong raw run; không dựng case giả.")
    text.extend(["## Tái tạo và giới hạn", "", "Tất cả bảng, hình và snapshot sinh từ raw shard đã đối chiếu checksum và replay. Không có số liệu nhập tay. Chạy `python benchmarks/run_ablation_w78.py analyze` để tái tạo.",
                 "Không tune agent/model từ kết quả này. Poster và chương thuật toán do Ly tự thực hiện. Bản báo cáo cuối/results-v1 của nhóm chưa có để review đối chiếu đầy đủ.",
                 "", f"Hardware: `{json.dumps(manifest['hardware'],ensure_ascii=False)}`."])
    (assets / "Ket_qua_Ablation_W78.md").write_text("\n".join(text)+"\n",encoding="utf-8")
    return summary, cases


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run","analyze"))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--assets", type=Path, default=DEFAULT_ASSETS)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--official", action="store_true")
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("workers must be positive")
    if args.mode == "run":
        run_experiments(args.config,args.output,workers=args.workers,official=args.official)
    else:
        summary,cases=analyze(args.output,args.assets)
        print(json.dumps({"A1":len(summary['a1']),"A2":summary['a2'],"case_count":len(cases)},indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
