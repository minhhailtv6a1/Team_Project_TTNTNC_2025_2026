# File: benchmarks/bench_minimax.py
"""Benchmark depth cho MinimaxAgent theo contract ``caro-v2`` (W34-M2-01, commit 5).

Chạy profile ``AB-D`` (depth 2/3/4) trên các scenario cố định 11x11 trong
``configs/benchmark_w34.json``, mỗi (scenario, depth) chạy hai lần: Alpha-Beta
bật và tắt, rồi in bảng ``depth | pruning | nodes | elapsed | action | score``.

Kiểm tra tự động (thoát mã 1 nếu vi phạm; tắt bằng ``--no-check``):
  * Action và score của pruning on/off phải trùng nhau (cùng thứ tự duyệt).
  * ``nodes`` của pruning on không được lớn hơn pruning off.
  * Mọi run đều dừng đúng lý do và action thuộc ``env.legal_actions()``.
Run bị cắt vì ``--max-nodes`` hoặc ``--time-limit-ms`` được đánh dấu ``truncated``
và bị loại khỏi so sánh on/off (so sánh trên depth chưa hoàn tất không có nghĩa).

Cách chạy (từ thư mục gốc repo)::

    python -m benchmarks.bench_minimax
    python -m benchmarks.bench_minimax --max-candidates 0          # exact, chậm
    python -m benchmarks.bench_minimax --json artifacts/w34_minimax_depth.json

``--max-candidates K`` (mặc định 8) giới hạn top-K nước mỗi node theo move
ordering để depth 4 chạy được trong thời gian ngắn; ``0`` nghĩa là không giới
hạn (minimax chính xác, depth 4 với pruning tắt có thể rất lâu: dùng kèm
``--max-nodes``).

Bàn giao cho M3 (Thiện): agent được tạo qua ``build_agent`` hoặc trực tiếp::

    MinimaxAgent(name="minimax", alpha_beta=True)           # chế độ thi đấu
    MinimaxAgent(name="minimax-d3", default_depth=3)        # depth mặc định 3
    agent.choose_action(env, SearchBudget(max_depth=3))     # depth theo budget

Khớp ``benchmark.json``: factory ``core.agents.minimax_ai:MinimaxAgent``,
options ``{"alpha_beta": true}``, profile ``AB-D``. Sau ``choose_action``,
``agent.last_depth_completed`` và ``agent.last_stop_reason`` mô tả lần tìm kiếm.
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

if __package__ in (None, ""):  # chạy trực tiếp: python benchmarks/bench_minimax.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.agents.minimax_ai import MinimaxAgent  # noqa: E402
from core.engine.game_env import CaroEnv  # noqa: E402
from core.engine.interfaces import SearchBudget  # noqa: E402

DEFAULT_CONFIG = Path("configs/benchmark.json")
DEFAULT_PROFILE = "AB-D"
COMPLETE_REASONS = {"depth_limit", "forced_win"}


@dataclass(frozen=True)
class Row:
    scenario: str
    depth: int  # max_depth được yêu cầu
    pruning: bool
    nodes: int
    elapsed_ms: float  # median qua --repeat
    action: tuple[int, int]
    score: float | None
    depth_completed: int
    stop_reason: str
    truncated: bool


# --- Cấu hình / scenario -------------------------------------------------------
def load_config(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"Không tìm thấy config benchmark: {path} (dùng --config)")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_env(actions: list[list[int]]) -> CaroEnv:
    env = CaroEnv()
    for row, col in actions:
        env.step((row, col))
    return env


def build_agent(
    alpha_beta: bool,
    max_candidates: int | None,
    name: str = "minimax",
) -> MinimaxAgent:
    """Factory dùng chung cho benchmark và bàn giao runner (xem docstring module)."""
    return MinimaxAgent(name=name, alpha_beta=alpha_beta, max_candidates=max_candidates)


def depth_budgets(config: dict, profile: str) -> list[dict]:
    try:
        budgets = config["profiles"][profile]["budgets"]
    except KeyError as exc:
        raise SystemExit(f"Profile {profile!r} không có trong config") from exc
    return [b for b in budgets if "max_depth" in b]


# --- Chạy ----------------------------------------------------------------------
def run_one(
    scenario: dict,
    depth: int,
    pruning: bool,
    *,
    max_candidates: int | None,
    max_nodes: int | None,
    time_limit_ms: int | None,
    repeat: int,
) -> Row:
    elapsed: list[float] = []
    decision = agent = None
    for _ in range(repeat):
        env = build_env(scenario["actions"])  # env mới mỗi lần: không phụ thuộc lần trước
        expected = scenario.get("expect", {}).get("to_move")
        if expected is not None and int(env.state.current_player) != expected:
            raise SystemExit(f"Scenario {scenario['id']}: to_move không khớp expect")
        agent = build_agent(pruning, max_candidates)
        budget = SearchBudget(max_depth=depth, max_nodes=max_nodes, time_limit_ms=time_limit_ms)
        before = env.state
        decision = agent.choose_action(env, budget)
        if env.state != before:
            raise AssertionError(f"{scenario['id']}: agent làm thay đổi env gốc")
        if decision.action not in env.legal_actions():
            raise AssertionError(f"{scenario['id']}: action {decision.action} không legal")
        elapsed.append(decision.elapsed_ms)
    assert decision is not None and agent is not None
    return Row(
        scenario=scenario["id"],
        depth=depth,
        pruning=pruning,
        nodes=decision.nodes,
        elapsed_ms=statistics.median(elapsed),
        action=decision.action,
        score=decision.score,
        depth_completed=agent.last_depth_completed,
        stop_reason=agent.last_stop_reason,
        truncated=agent.last_stop_reason not in COMPLETE_REASONS,
    )


def check_rows(rows: list[Row]) -> list[str]:
    """Trả về danh sách vi phạm (rỗng nếu pruning on/off nhất quán)."""
    problems: list[str] = []
    index = {(r.scenario, r.depth, r.pruning): r for r in rows}
    for (scenario, depth, pruning), on in index.items():
        if not pruning:
            continue
        off = index.get((scenario, depth, False))
        if off is None or on.truncated or off.truncated:
            continue  # chưa hoàn tất depth: không so sánh
        tag = f"{scenario} depth={depth}"
        if on.action != off.action:
            problems.append(f"{tag}: action khác nhau on={on.action} off={off.action}")
        if on.score != off.score:
            problems.append(f"{tag}: score khác nhau on={on.score} off={off.score}")
        if on.nodes > off.nodes:
            problems.append(f"{tag}: pruning tăng nodes ({on.nodes} > {off.nodes})")
    return problems


# --- Báo cáo ---------------------------------------------------------------------
def format_table(rows: list[Row]) -> str:
    header = (
        "| scenario | depth | pruning | done | nodes | elapsed_ms | action | score | stop |",
        "|---|---:|---|---:|---:|---:|---|---:|---|",
    )
    lines = list(header)
    for r in rows:
        score = "None" if r.score is None else f"{r.score:.2f}"
        flag = " (truncated)" if r.truncated else ""
        lines.append(
            f"| {r.scenario} | {r.depth} | {'on' if r.pruning else 'off'} | "
            f"{r.depth_completed} | {r.nodes} | {r.elapsed_ms:.1f} | "
            f"({r.action[0]},{r.action[1]}) | {score} | {r.stop_reason}{flag} |"
        )
    return "\n".join(lines)


def format_summary(rows: list[Row]) -> str:
    """Tỷ lệ nodes và thời gian on/off cho các cặp đã hoàn tất."""
    index = {(r.scenario, r.depth, r.pruning): r for r in rows}
    lines = ["| scenario | depth | nodes on/off | speedup (time off/on) |", "|---|---:|---:|---:|"]
    for (scenario, depth, pruning), on in index.items():
        off = index.get((scenario, depth, False))
        if not pruning or off is None or on.truncated or off.truncated:
            continue
        ratio = on.nodes / off.nodes if off.nodes else 1.0
        speed = off.elapsed_ms / on.elapsed_ms if on.elapsed_ms else float("inf")
        lines.append(f"| {scenario} | {depth} | {ratio:.2f} | {speed:.1f}x |")
    return "\n".join(lines)


def environment_info() -> dict:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor() or platform.machine(),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--profile", default=DEFAULT_PROFILE)
    parser.add_argument("--scenarios", nargs="*", help="chỉ chạy các scenario id này")
    parser.add_argument(
        "--max-candidates", type=int, default=8,
        help="top-K nước mỗi node theo ordering; 0 = không giới hạn (exact)",
    )
    parser.add_argument("--max-nodes", type=int, default=None, help="chặn trên nodes mỗi run")
    parser.add_argument("--time-limit-ms", type=int, default=None)
    parser.add_argument("--repeat", type=int, default=1, help="số lần lặp, lấy median elapsed")
    parser.add_argument("--json", type=Path, default=None, help="ghi kết quả JSON ra file")
    parser.add_argument("--no-check", action="store_true", help="bỏ kiểm tra on/off")
    args = parser.parse_args(argv)
    if args.repeat <= 0:
        parser.error("--repeat phải > 0")
    if args.max_candidates < 0:
        parser.error("--max-candidates phải >= 0")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    max_candidates = args.max_candidates or None
    scenarios = config["scenarios"]
    if args.scenarios:
        wanted = set(args.scenarios)
        unknown = wanted - {s["id"] for s in scenarios}
        if unknown:
            raise SystemExit(f"Scenario không tồn tại: {sorted(unknown)}")
        scenarios = [s for s in scenarios if s["id"] in wanted]
    depths = sorted(b["max_depth"] for b in depth_budgets(config, args.profile))
    if not depths:
        raise SystemExit(f"Profile {args.profile!r} không có budget max_depth")

    rows: list[Row] = []
    for scenario in scenarios:
        for depth in depths:
            for pruning in (True, False):
                rows.append(
                    run_one(
                        scenario, depth, pruning,
                        max_candidates=max_candidates,
                        max_nodes=args.max_nodes,
                        time_limit_ms=args.time_limit_ms,
                        repeat=args.repeat,
                    )
                )

    info = environment_info()
    print(f"# bench_minimax - profile {args.profile}, contract {config['contract_version']}")
    print(
        f"python {info['python']} | {info['platform']} | "
        f"max_candidates={max_candidates} max_nodes={args.max_nodes} "
        f"time_limit_ms={args.time_limit_ms} repeat={args.repeat}\n"
    )
    print(format_table(rows))
    print("\n" + format_summary(rows))

    problems = [] if args.no_check else check_rows(rows)
    if problems:
        print("\nVI PHẠM:", *problems, sep="\n  - ")

    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "contract_version": config["contract_version"],
            "profile": args.profile,
            "environment": info,
            "options": {
                "max_candidates": max_candidates,
                "max_nodes": args.max_nodes,
                "time_limit_ms": args.time_limit_ms,
                "repeat": args.repeat,
            },
            "rows": [asdict(r) for r in rows],
            "violations": problems,
        }
        args.json.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())