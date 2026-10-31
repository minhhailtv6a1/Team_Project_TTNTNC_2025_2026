"""Runner chạy game / match / tournament giữa các ``Agent`` theo contract ``caro-v2``.

Trách nhiệm (kế hoạch W34-M3-01):
- Chạy một game từ ``reset`` đến terminal bằng hai object thỏa ``Agent``.
- Truyền budget từ profile vào mỗi lần ``choose_action``; runner là chủ sở hữu
  seed và suy ra seed xác định cho từng game và từng nước.
- Đo wall time độc lập, đối chiếu với ``decision.elapsed_ms``.
- Validate decision trước khi gọi ``env.step()``; lỗi báo rõ agent, ply, action.
- Tạo ``MoveRecord`` / ``GameRecord`` và là nơi duy nhất gọi logger.
- Đổi bên X/O, thống kê tách theo bên, budget enforcer (record hoặc fail-fast).

Runner chỉ dựa vào ``Agent`` / ``GameEnv`` protocol. Agent cụ thể được nạp qua
factory khai báo trong config, không import trực tiếp từng implementation.
"""

from __future__ import annotations

import argparse
import importlib
import itertools
import json
import math
import os
import platform
import sys
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from core.engine.interfaces import (
    CONTRACT_VERSION,
    Action,
    Agent,
    AgentDecision,
    GameConfig,
    GameEnv,
    GameRecord,
    MoveRecord,
    Player,
    SearchBudget,
)
from core.utils.logger import GameLogger, write_manifest

__all__ = [
    "AgentError",
    "BudgetEnforcer",
    "BudgetViolation",
    "BudgetViolationError",
    "GameOutcome",
    "Participant",
    "TournamentResult",
    "build_env_from_actions",
    "build_participants",
    "budget_from_dict",
    "check_scenario",
    "derive_seed",
    "load_config",
    "load_factory",
    "main",
    "play_game",
    "run_match",
    "run_tournament",
    "summarize_outcomes",
]

EnvFactory = Callable[[], GameEnv]

# ---------------------------------------------------------------------------
# Lỗi và vi phạm budget
# ---------------------------------------------------------------------------


class AgentError(RuntimeError):
    """Agent trả decision sai hoặc gây lỗi; thông báo luôn có agent, ply, action."""

    def __init__(
        self, agent: str, ply: int, action: object, message: str
    ) -> None:
        super().__init__(f"agent={agent!r} ply={ply} action={action!r}: {message}")
        self.agent = agent
        self.ply = ply
        self.action = action


@dataclass(frozen=True, slots=True)
class BudgetViolation:
    agent: str
    ply: int
    kind: str  # time_limit_ms | max_nodes | simulations | elapsed_mismatch
    limit: float
    observed: float
    action: Action | None = None


class BudgetViolationError(AgentError):
    """Phát sinh ở chế độ fail-fast khi agent vượt budget."""

    def __init__(self, violation: BudgetViolation) -> None:
        super().__init__(
            violation.agent,
            violation.ply,
            violation.action,
            f"budget violation {violation.kind} "
            f"(limit={violation.limit:g}, observed={violation.observed:g})",
        )
        self.violation = violation


@dataclass
class BudgetEnforcer:
    """Ghi lại (hoặc ném lỗi) khi agent không tuân budget.

    ``max_depth`` không quan sát được từ ``AgentDecision`` nên không kiểm tra ở
    đây; độ sâu được kiểm bằng test riêng của agent (W34-T13).
    """

    tolerance_ms: float = 50.0
    fail_fast: bool = False
    violations: list[BudgetViolation] = field(default_factory=list)

    def check(
        self,
        *,
        agent: str,
        ply: int,
        budget: SearchBudget | None,
        wall_ms: float,
        decision: AgentDecision,
    ) -> list[BudgetViolation]:
        found: list[BudgetViolation] = []
        action = decision.action

        def add(kind: str, limit: float, observed: float) -> None:
            found.append(BudgetViolation(agent, ply, kind, limit, observed, action))

        if budget is not None:
            if (
                budget.time_limit_ms is not None
                and wall_ms > budget.time_limit_ms + self.tolerance_ms
            ):
                add("time_limit_ms", budget.time_limit_ms, wall_ms)
            if budget.max_nodes is not None and decision.nodes > budget.max_nodes:
                add("max_nodes", budget.max_nodes, decision.nodes)
            if budget.simulations is not None and decision.simulations > budget.simulations:
                add("simulations", budget.simulations, decision.simulations)

        gap = abs(wall_ms - decision.elapsed_ms)
        if gap > self.tolerance_ms:
            add("elapsed_mismatch", self.tolerance_ms, gap)

        self.violations.extend(found)
        if found and self.fail_fast:
            raise BudgetViolationError(found[0])
        return found


# ---------------------------------------------------------------------------
# Seed xác định
# ---------------------------------------------------------------------------


def derive_seed(*parts: int) -> int:
    """Suy ra seed không âm (< 2**31) một cách xác định từ các số nguyên."""
    value = 0x9E3779B1
    for part in parts:
        value = (value * 1_000_003 + int(part) + 1) % (2**31)
    return value


# ---------------------------------------------------------------------------
# Kiểu dữ liệu của runner
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Participant:
    """Một agent cùng budget và nhãn; nhãn được ghi vào ``GameRecord``."""

    label: str
    agent: Agent
    budget: SearchBudget | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("Participant.label must be a non-empty string")


@dataclass(slots=True)
class GameOutcome:
    record: GameRecord
    wall_ms: list[float]  # wall time đo bởi runner, song song với record.moves
    violations: list[BudgetViolation] = field(default_factory=list)

    @property
    def winner_label(self) -> str | None:
        winner = self.record.winner
        if winner is None:
            return None
        return self.record.x_agent if winner == Player.X else self.record.o_agent


@dataclass(slots=True)
class TournamentResult:
    outcomes: list[GameOutcome]
    summary: dict[str, dict[str, Any]]
    violations: list[BudgetViolation]


# ---------------------------------------------------------------------------
# Chạy một game
# ---------------------------------------------------------------------------


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _budget_for_move(
    budget: SearchBudget | None, game_seed: int | None, ply: int
) -> SearchBudget | None:
    seed = None if game_seed is None else derive_seed(game_seed, ply)
    if budget is None and seed is None:
        return None
    return replace(budget or SearchBudget(), seed=seed)


def _validate_decision(
    env: GameEnv, label: str, ply: int, decision: object
) -> AgentDecision:
    if not isinstance(decision, AgentDecision):
        raise AgentError(
            label, ply, None, f"expected AgentDecision, got {type(decision).__name__}"
        )
    action = decision.action
    if not (
        isinstance(action, tuple)
        and len(action) == 2
        and all(_is_plain_int(v) for v in action)
    ):
        raise AgentError(label, ply, action, "action must be a (row, col) tuple of ints")
    if action not in env.legal_actions():
        raise AgentError(label, ply, action, "action is not legal in the current state")
    if not decision.elapsed_ms >= 0:  # bắt cả NaN
        raise AgentError(label, ply, action, f"invalid elapsed_ms {decision.elapsed_ms!r}")
    if decision.nodes < 0 or decision.simulations < 0:
        raise AgentError(label, ply, action, "nodes and simulations must not be negative")
    return decision


def play_game(
    env_factory: EnvFactory,
    x: Participant,
    o: Participant,
    *,
    game_id: str,
    seed: int | None,
    enforcer: BudgetEnforcer | None = None,
    logger: GameLogger | None = None,
) -> GameOutcome:
    """Chạy một game từ reset đến terminal; ghi log nếu có ``logger``."""
    env = env_factory()
    env.reset(seed=seed)
    by_player = {Player.X: x, Player.O: o}
    max_plies = env.config.board_size**2

    moves: list[MoveRecord] = []
    wall_times: list[float] = []
    violations: list[BudgetViolation] = []
    ply = 0

    while not env.is_terminal():
        ply += 1
        if ply > max_plies:
            raise RuntimeError(
                f"game {game_id!r}: environment did not terminate after {max_plies} plies"
            )
        player = env.state.current_player
        participant = by_player[player]
        budget = _budget_for_move(participant.budget, seed, ply)
        state_before = env.state

        started = time.perf_counter()
        try:
            raw = participant.agent.choose_action(env, budget)
        except Exception as exc:
            raise AgentError(
                participant.label,
                ply,
                None,
                f"choose_action raised {type(exc).__name__}: {exc}",
            ) from exc
        wall_ms = (time.perf_counter() - started) * 1000.0

        if env.state != state_before:
            raise AgentError(
                participant.label, ply, getattr(raw, "action", None),
                "agent mutated the environment passed to choose_action",
            )
        decision = _validate_decision(env, participant.label, ply, raw)

        if enforcer is not None:
            violations.extend(
                enforcer.check(
                    agent=participant.label,
                    ply=ply,
                    budget=budget,
                    wall_ms=wall_ms,
                    decision=decision,
                )
            )

        result = env.step(decision.action)
        moves.append(
            MoveRecord(
                ply=ply,
                player=player,
                action=decision.action,
                reward=float(result.reward),
                elapsed_ms=float(decision.elapsed_ms),
                nodes=int(decision.nodes),
                simulations=int(decision.simulations),
            )
        )
        wall_times.append(wall_ms)

    final = env.state
    record = GameRecord(
        contract_version=CONTRACT_VERSION,
        game_id=game_id,
        config=env.config,
        seed=seed,
        x_agent=x.label,
        o_agent=o.label,
        moves=moves,
        terminated=True,
        winner=final.winner,
    )
    if logger is not None:
        logger.log_game(record)
    return GameOutcome(record=record, wall_ms=wall_times, violations=violations)


# ---------------------------------------------------------------------------
# Match và tournament
# ---------------------------------------------------------------------------


def run_match(
    env_factory: EnvFactory,
    a: Participant,
    b: Participant,
    *,
    games: int,
    base_seed: int,
    pair_index: int = 0,
    swap_sides: bool = True,
    enforcer: BudgetEnforcer | None = None,
    logger: GameLogger | None = None,
) -> list[GameOutcome]:
    """Chạy ``games`` ván giữa ``a`` và ``b``, đổi bên luân phiên.

    Ván chẵn: ``a`` là X; ván lẻ: ``a`` là O. Hai ván đổi bên liền nhau dùng
    chung seed để so sánh công bằng. Cùng ``base_seed`` luôn cho cùng chuỗi seed.
    """
    if games < 1:
        raise ValueError("games must be >= 1")
    if swap_sides and games < 2:
        raise ValueError("swap_sides requires games >= 2 so both sides are played")
    if a.label == b.label:
        raise ValueError(f"participants must have distinct labels, got {a.label!r} twice")

    outcomes: list[GameOutcome] = []
    for game_index in range(games):
        a_is_x = (game_index % 2 == 0) or not swap_sides
        x, o = (a, b) if a_is_x else (b, a)
        seed_index = game_index // 2 if swap_sides else game_index
        seed = derive_seed(base_seed, pair_index, seed_index)
        game_id = f"s{base_seed}-p{pair_index}-g{game_index:03d}-{x.label}-vs-{o.label}"
        outcomes.append(
            play_game(
                env_factory, x, o,
                game_id=game_id, seed=seed, enforcer=enforcer, logger=logger,
            )
        )
    return outcomes


def run_tournament(
    env_factory: EnvFactory,
    participants: Sequence[Participant],
    *,
    games_per_pair: int,
    base_seed: int,
    swap_sides: bool = True,
    enforcer: BudgetEnforcer | None = None,
    logger: GameLogger | None = None,
) -> TournamentResult:
    """Smoke tournament: mọi cặp không thứ tự, mỗi cặp đổi bên."""
    labels = [p.label for p in participants]
    if len(set(labels)) != len(labels):
        raise ValueError(f"participant labels must be unique, got {labels}")
    if len(participants) < 2:
        raise ValueError("a tournament needs at least two participants")

    outcomes: list[GameOutcome] = []
    for pair_index, (a, b) in enumerate(itertools.combinations(participants, 2)):
        outcomes.extend(
            run_match(
                env_factory, a, b,
                games=games_per_pair, base_seed=base_seed, pair_index=pair_index,
                swap_sides=swap_sides, enforcer=enforcer, logger=logger,
            )
        )
    violations = [v for outcome in outcomes for v in outcome.violations]
    return TournamentResult(outcomes, summarize_outcomes(outcomes), violations)


# ---------------------------------------------------------------------------
# Metrics tổng hợp (tách theo bên, không gộp nhầm X và O)
# ---------------------------------------------------------------------------


@dataclass
class _Acc:
    games: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    moves: int = 0
    nodes: int = 0
    simulations: int = 0
    violations: int = 0
    wall_ms: list[float] = field(default_factory=list)

    def merge(self, other: _Acc) -> None:
        self.games += other.games
        self.wins += other.wins
        self.draws += other.draws
        self.losses += other.losses
        self.moves += other.moves
        self.nodes += other.nodes
        self.simulations += other.simulations
        self.violations += other.violations
        self.wall_ms.extend(other.wall_ms)

    def as_dict(self) -> dict[str, Any]:
        return {
            "games": self.games,
            "wins": self.wins,
            "draws": self.draws,
            "losses": self.losses,
            "moves": self.moves,
            "mean_move_ms": (
                sum(self.wall_ms) / len(self.wall_ms) if self.wall_ms else None
            ),
            "p95_move_ms": _percentile95(self.wall_ms),
            "total_nodes": self.nodes,
            "total_simulations": self.simulations,
            "budget_violations": self.violations,
        }


def _percentile95(values: Sequence[float]) -> float | None:
    """Percentile 95 theo nearest-rank."""
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def summarize_outcomes(outcomes: Iterable[GameOutcome]) -> dict[str, dict[str, Any]]:
    """Gom thống kê theo nhãn agent, với ``overall``, ``as_x`` và ``as_o``.

    Thời gian nước đi là wall time do runner đo. Kết quả smoke chỉ để kiểm tra
    pipeline, không dùng để kết luận agent nào mạnh hơn.
    """
    per_label: dict[str, dict[str, _Acc]] = {}
    for outcome in outcomes:
        record = outcome.record
        for side, label in ((Player.X, record.x_agent), (Player.O, record.o_agent)):
            key = "as_x" if side == Player.X else "as_o"
            acc = per_label.setdefault(label, {"as_x": _Acc(), "as_o": _Acc()})[key]
            acc.games += 1
            if record.winner is None:
                acc.draws += 1
            elif record.winner == side:
                acc.wins += 1
            else:
                acc.losses += 1
            parity = 0 if side == Player.X else 1
            for index, move in enumerate(record.moves):
                if index % 2 == parity:
                    acc.moves += 1
                    acc.nodes += move.nodes
                    acc.simulations += move.simulations
                    acc.wall_ms.append(outcome.wall_ms[index])
            acc.violations += sum(1 for v in outcome.violations if v.agent == label)

    summary: dict[str, dict[str, Any]] = {}
    for label, sides in per_label.items():
        overall = _Acc()
        overall.merge(sides["as_x"])
        overall.merge(sides["as_o"])
        summary[label] = {
            "overall": overall.as_dict(),
            "as_x": sides["as_x"].as_dict(),
            "as_o": sides["as_o"].as_dict(),
        }
    return summary


# ---------------------------------------------------------------------------
# Config benchmark và scenario
# ---------------------------------------------------------------------------


def load_config(path: str | os.PathLike[str]) -> dict[str, Any]:
    """Đọc config benchmark (UTF-8) và kiểm tra version/cấu hình game."""
    with open(path, "r", encoding="utf-8") as file:
        config = json.load(file)
    if config.get("contract_version") != CONTRACT_VERSION:
        raise ValueError(
            f"config contract_version must be {CONTRACT_VERSION!r}, "
            f"got {config.get('contract_version')!r}"
        )
    GameConfig(**config.get("game_config", {}))  # ném InvalidConfigError nếu sai
    return config


def budget_from_dict(data: Mapping[str, Any], seed: int | None = None) -> SearchBudget:
    """Dựng ``SearchBudget`` từ một phần tử ``budgets`` (bỏ key ``label``)."""
    fields = {k: v for k, v in data.items() if k != "label"}
    fields.setdefault("seed", seed)
    try:
        return SearchBudget(**fields)
    except TypeError as exc:
        raise ValueError(f"invalid budget {dict(data)!r}: {exc}") from exc


def load_factory(spec: str) -> Callable[..., Any]:
    """Nạp callable từ chuỗi ``"package.module:Attribute"``."""
    module_name, sep, attr = spec.partition(":")
    if not sep or not module_name or not attr:
        raise ValueError(f"factory must look like 'module:Attribute', got {spec!r}")
    return getattr(importlib.import_module(module_name), attr)


def build_participants(
    config: Mapping[str, Any], profile: str | None = None
) -> list[Participant]:
    """Tạo participant cho mọi agent trong config với budget của ``profile``.

    Nhãn có dạng ``<agent>@<budget-label>``. Profile có nhiều budget (ví dụ
    MCTS-S) tạo một participant cho mỗi budget.
    """
    profile = profile or config["smoke_tournament"]["profile"]
    budgets = config["profiles"][profile]["budgets"]
    participants: list[Participant] = []
    for key, spec in config["agents"].items():
        factory = load_factory(spec["factory"])
        for budget_data in budgets:
            agent = factory(**spec.get("options", {}))
            label = f"{key}@{budget_data.get('label', profile)}"
            participants.append(Participant(label, agent, budget_from_dict(budget_data)))
    return participants


def build_env_from_actions(
    env_factory: EnvFactory,
    actions: Iterable[Sequence[int]],
    seed: int | None = None,
) -> GameEnv:
    """Dựng state fixture chỉ bằng ``reset`` và ``step`` public."""
    env = env_factory()
    env.reset(seed=seed)
    for row, col in actions:
        env.step((row, col))
    return env


def check_scenario(env_factory: EnvFactory, scenario: Mapping[str, Any]) -> None:
    """Kiểm tra ``expect`` của scenario bằng public API; sai thì ném ``ValueError``."""
    sid = scenario.get("id", "?")
    env = build_env_from_actions(env_factory, scenario["actions"])
    expect = scenario.get("expect", {})

    if "to_move" in expect and env.state.current_player != Player(expect["to_move"]):
        raise ValueError(f"{sid}: wrong player to move")

    mover = env.state.current_player
    for row, col in expect.get("winning_actions", []):
        probe = env.clone_env()
        result = probe.step((row, col))
        if not (result.done and result.winner == mover):
            raise ValueError(f"{sid}: {(row, col)} does not win immediately")

    for forced in map(tuple, expect.get("forced_actions", [])):
        for other in env.legal_actions():
            if other == forced:
                continue
            probe = env.clone_env()
            probe.step(other)
            if probe.is_terminal():
                continue
            result = probe.step(forced)
            if not (result.done and result.winner == -mover):
                raise ValueError(f"{sid}: skipping {forced} does not lose")


# ---------------------------------------------------------------------------
# CLI smoke tournament
# ---------------------------------------------------------------------------


def _hardware_info() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "python": sys.version.split()[0],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke tournament caro-v2")
    parser.add_argument("--config", default="configs/benchmark.json")
    parser.add_argument(
        "--env-factory",
        default="core.engine.game_env:CaroEnv",
        help="module:callable, gọi không tham số để tạo GameEnv",
    )
    parser.add_argument("--profile", default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--games-per-pair", type=int, default=None)
    parser.add_argument("--out-dir", default=None)
    parser.add_argument("--fail-fast", action="store_true")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    smoke = config["smoke_tournament"]
    profile = args.profile or smoke["profile"]
    seed = args.seed if args.seed is not None else config["seeds"][0]
    games_per_pair = args.games_per_pair or smoke["games_per_pair"]
    out_dir = Path(args.out_dir or smoke["log_dir"])
    enforcer_cfg = config.get("budget_enforcer", {})
    enforcer = BudgetEnforcer(
        tolerance_ms=float(enforcer_cfg.get("tolerance_ms", 50.0)),
        fail_fast=args.fail_fast or enforcer_cfg.get("mode") == "fail_fast",
    )

    env_factory = load_factory(args.env_factory)
    participants = build_participants(config, profile)

    games_path = out_dir / f"games_s{seed}.jsonl"
    with GameLogger(games_path, mode="w") as logger:
        result = run_tournament(
            env_factory, participants,
            games_per_pair=games_per_pair, base_seed=seed,
            swap_sides=bool(smoke.get("swap_sides", True)),
            enforcer=enforcer, logger=logger,
        )

    manifest_path = write_manifest(
        out_dir / f"manifest_s{seed}.json",
        {
            "seed": seed,
            "profile": profile,
            "games_per_pair": games_per_pair,
            "swap_sides": bool(smoke.get("swap_sides", True)),
            "participants": [p.label for p in participants],
            "games_file": str(games_path),
            "total_games": len(result.outcomes),
            "summary": result.summary,
            "budget_violations": [asdict(v) for v in result.violations],
            "hardware": _hardware_info(),
            "command": list(sys.argv if argv is None else argv),
            "config": config,
        },
    )

    print(f"{len(result.outcomes)} games -> {games_path}")
    for label, stats in result.summary.items():
        o = stats["overall"]
        mean = o["mean_move_ms"]
        print(
            f"{label}: W/D/L={o['wins']}/{o['draws']}/{o['losses']} "
            f"mean_move_ms={'n/a' if mean is None else f'{mean:.2f}'} "
            f"violations={o['budget_violations']}"
        )
    print(f"manifest -> {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())