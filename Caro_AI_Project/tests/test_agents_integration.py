"""Test tích hợp contract chung cho Random, Heuristic, Minimax và MCTS.

Phủ W34-T01..T04 (contract chung), T27 (cả bốn agent qua một runner),
T29 (không hard-code phạm vi bàn cũ) và T30 (action public là tuple).

Cách hoạt động:
- Môi trường là ``CaroEnv`` thật. Mặc định ``core.engine.game_env:CaroEnv`` được
  gọi không tham số; đổi bằng biến môi trường ``CARO_ENV_FACTORY="module:callable"``.
- Agent chưa có (module không tồn tại hoặc file còn rỗng) thì test của agent đó
  được *skip*, nên PR đầu tiên chỉ có Random vẫn xanh và các agent tự được kiểm
  tra ngay khi merge. Module có nội dung mà thiếu class/tên sai thì test *fail*.
- Mọi budget dùng giới hạn đếm (depth, nodes, simulations), không dựa vào thời
  gian, để CI không flaky.
- Fixture dưới đây khớp với ``scenarios`` trong ``benchmark.json``.
"""

from __future__ import annotations

import ast
import importlib
import io
import os
import tokenize
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from core.engine.interfaces import (
    Agent,
    AgentDecision,
    GameEnv,
    SearchBudget,
    UndoError,
)
from core.utils.logger import GameLogger, load_games, validate_game_record
from core.utils.tournament_runner import (
    BudgetEnforcer,
    Participant,
    build_env_from_actions,
    load_factory,
    run_tournament,
)

# ---------------------------------------------------------------------------
# Cấu hình agent và scenario
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentSpec:
    key: str
    factory: str  # "module:Class"
    budget: dict = field(default_factory=dict)  # field của SearchBudget, trừ seed
    options: dict = field(default_factory=dict)  # kwargs cho constructor
    uses_simulations: bool = False  # chỉ MCTS/rollout có simulations > 0


AGENT_SPECS = [
    AgentSpec("random", "core.agents.random_ai:RandomAgent"),
    AgentSpec("heuristic", "core.agents.heuristic_ai:HeuristicAgent"),
    AgentSpec(
        "minimax",
        "core.agents.minimax_ai:MinimaxAgent",
        budget={"max_depth": 2, "max_nodes": 500},
    ),
    AgentSpec(
        "mcts",
        "core.agents.mcts_ai:MCTSAgent",
        budget={"simulations": 10},
        uses_simulations=True,
    ),
]
SPEC_BY_KEY = {spec.key: spec for spec in AGENT_SPECS}
SEEDS = (11, 22, 33)

# Chuỗi action public [row, col], dựng bằng env.step().
SCENARIOS = {
    "opening_empty": [],
    "opening_two_plies": [[5, 5], [5, 6]],
    "tactical_win_in_one": [[5, 4], [0, 0], [5, 5], [0, 2], [5, 6], [0, 4], [5, 7], [10, 10]],
    "tactical_block_in_one": [[5, 3], [0, 0], [5, 4], [0, 2], [5, 6], [0, 4], [5, 7]],
    "midgame_mixed": [[5, 5], [4, 4], [5, 6], [6, 6], [3, 3], [7, 7]],
}
# X thắng ở ply 9 bằng 5 quân hàng 5 (hai đầu trống).
TERMINAL_ACTIONS = [
    [5, 3], [0, 0], [5, 4], [0, 2], [5, 5], [0, 4], [5, 6], [10, 10], [5, 7],
]


# ---------------------------------------------------------------------------
# Fixture và helper
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def env_factory():
    spec = os.environ.get("CARO_ENV_FACTORY", "core.engine.game_env:CaroEnv")
    try:
        return load_factory(spec)
    except (ImportError, AttributeError) as exc:
        pytest.skip(f"cannot load environment factory {spec!r}: {exc}")


def make_budget(spec: AgentSpec, seed: int) -> SearchBudget:
    return SearchBudget(**spec.budget, seed=seed)


def make_agent(spec: AgentSpec) -> Agent:
    module_name, _, attr = spec.factory.partition(":")
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name and (module_name == exc.name or module_name.startswith(exc.name + ".")):
            pytest.skip(f"{module_name} is not implemented yet")
        raise
    if not hasattr(module, attr):
        source = Path(module.__file__ or "").read_text(encoding="utf-8")
        if not source.strip():
            pytest.skip(f"{module_name} is still empty")
        raise AttributeError(f"{module_name} has no attribute {attr!r}")
    return getattr(module, attr)(**spec.options)


def build(env_factory, name: str) -> GameEnv:
    actions = TERMINAL_ACTIONS if name == "terminal" else SCENARIOS[name]
    return build_env_from_actions(env_factory, actions)


agent_params = pytest.mark.parametrize("spec", AGENT_SPECS, ids=lambda s: s.key)
scenario_params = pytest.mark.parametrize("scenario", list(SCENARIOS))


# ---------------------------------------------------------------------------
# W34-T01: env terminal -> RuntimeError
# ---------------------------------------------------------------------------


@agent_params
def test_t01_terminal_env_raises_runtime_error(env_factory, spec):
    agent = make_agent(spec)
    env = build(env_factory, "terminal")
    assert env.is_terminal() and env.legal_actions() == []  # kiểm tra fixture
    before = env.state
    with pytest.raises(RuntimeError):
        agent.choose_action(env, make_budget(spec, SEEDS[0]))
    assert env.state == before


# ---------------------------------------------------------------------------
# W34-T02: env đang chơi -> action thuộc legal actions
# ---------------------------------------------------------------------------


@agent_params
@scenario_params
def test_t02_action_is_legal_and_decision_is_well_formed(env_factory, spec, scenario):
    agent = make_agent(spec)
    env = build(env_factory, scenario)
    assert not env.is_terminal()
    legal = env.legal_actions()

    decision = agent.choose_action(env, make_budget(spec, SEEDS[0]))

    assert isinstance(decision, AgentDecision)
    assert decision.action in legal
    assert decision.elapsed_ms >= 0
    assert decision.nodes >= 0 and decision.simulations >= 0
    if decision.score is not None:
        assert decision.score == decision.score  # không NaN
        assert abs(decision.score) != float("inf")
    if spec.uses_simulations:
        assert decision.simulations > 0
    else:
        assert decision.simulations == 0


@agent_params
def test_agent_has_name_and_satisfies_protocol(spec):
    agent = make_agent(spec)
    assert isinstance(agent, Agent)
    assert isinstance(agent.name, str) and agent.name


@agent_params
def test_works_without_budget(env_factory, spec):
    agent = make_agent(spec)
    if spec.budget:
        pytest.skip("agent này cần budget để giới hạn thời gian chạy trong CI")
    env = build(env_factory, "midgame_mixed")
    assert agent.choose_action(env).action in env.legal_actions()


@agent_params
@scenario_params
def test_counters_respect_count_budgets(env_factory, spec, scenario):
    agent = make_agent(spec)
    env = build(env_factory, scenario)
    budget = make_budget(spec, SEEDS[0])
    decision = agent.choose_action(env, budget)
    if budget.max_nodes is not None:
        assert decision.nodes <= budget.max_nodes
    if budget.simulations is not None:
        assert decision.simulations <= budget.simulations


# ---------------------------------------------------------------------------
# W34-T03: snapshot trước và sau choose_action bằng nhau
# ---------------------------------------------------------------------------


@agent_params
@scenario_params
def test_t03_env_is_unchanged_after_choose_action(env_factory, spec, scenario):
    agent = make_agent(spec)
    env = build(env_factory, scenario)

    state_before = env.state
    legal_before = env.legal_actions()
    render_before = env.render()
    undo_before = _state_after_undo(env)

    agent.choose_action(env, make_budget(spec, SEEDS[0]))

    assert env.state == state_before
    assert env.legal_actions() == legal_before
    assert env.render() == render_before
    assert _state_after_undo(env) == undo_before  # history undo cũng không đổi


def _state_after_undo(env: GameEnv):
    """State sau một undo trên clone; ``None`` nếu chưa có nước nào."""
    probe = env.clone_env()
    try:
        return probe.undo()
    except UndoError:
        return None


# ---------------------------------------------------------------------------
# W34-T04: cùng state, budget, seed -> kết quả tái lập
# ---------------------------------------------------------------------------


@agent_params
@scenario_params
@pytest.mark.parametrize("seed", SEEDS)
def test_t04_same_state_budget_seed_is_reproducible(env_factory, spec, scenario, seed):
    budget = make_budget(spec, seed)
    first = make_agent(spec).choose_action(build(env_factory, scenario), budget)
    second = make_agent(spec).choose_action(build(env_factory, scenario), budget)

    assert first.action == second.action
    assert first.score == second.score
    assert first.nodes == second.nodes
    assert first.simulations == second.simulations


@agent_params
def test_t04_reusing_one_agent_instance_is_reproducible(env_factory, spec):
    agent = make_agent(spec)
    budget = make_budget(spec, SEEDS[1])
    env = build(env_factory, "midgame_mixed")
    first = agent.choose_action(env, budget)
    second = agent.choose_action(env, budget)
    assert first.action == second.action


# ---------------------------------------------------------------------------
# W34-T30: action public luôn là tuple (row, col)
# ---------------------------------------------------------------------------


@agent_params
@scenario_params
def test_t30_public_action_is_row_col_tuple(env_factory, spec, scenario):
    agent = make_agent(spec)
    env = build(env_factory, scenario)
    action = agent.choose_action(env, make_budget(spec, SEEDS[0])).action
    size = env.config.board_size

    assert type(action) is tuple and len(action) == 2
    row, col = action
    assert type(row) is int and type(col) is int  # không bool, không numpy, không index phẳng
    assert 0 <= row < size and 0 <= col < size


# ---------------------------------------------------------------------------
# W34-T27: cả bốn agent chạy qua cùng một runner
# ---------------------------------------------------------------------------


def test_t27_all_agents_run_through_one_runner(env_factory, tmp_path):
    participants = [
        Participant(f"{spec.key}@ci", make_agent(spec), make_budget(spec, 0))
        for spec in AGENT_SPECS
        if _is_available(spec)
    ]
    if len(participants) < 2:
        pytest.skip("cần ít nhất hai agent đã được implement để chạy tournament")

    enforcer = BudgetEnforcer(tolerance_ms=1_000.0)  # chỉ quan sát giới hạn đếm
    games_path = tmp_path / "games.jsonl"
    with GameLogger(games_path, mode="w") as logger:
        result = run_tournament(
            env_factory,
            participants,
            games_per_pair=2,
            base_seed=SEEDS[0],
            swap_sides=True,
            enforcer=enforcer,
            logger=logger,
        )

    n = len(participants)
    assert len(result.outcomes) == n * (n - 1) // 2 * 2
    labels = {p.label for p in participants}
    assert set(result.summary) == labels

    for outcome in result.outcomes:
        validate_game_record(outcome.record)  # terminated, ply liên tục, luân phiên X/O
        assert outcome.record.moves

    for label in labels:  # mỗi agent chơi cả hai bên
        stats = result.summary[label]
        assert stats["as_x"]["games"] > 0 and stats["as_o"]["games"] > 0

    counted = {"max_nodes", "simulations"}
    assert not [v for v in result.violations if v.kind in counted], result.violations

    assert load_games(games_path) == [o.record for o in result.outcomes]  # round-trip


def _is_available(spec: AgentSpec) -> bool:
    try:
        make_agent(spec)
    except pytest.skip.Exception:
        return False
    return True


# ---------------------------------------------------------------------------
# W34-T29: không hard-code phạm vi cũ; agent chỉ dùng public API
# ---------------------------------------------------------------------------


def _agent_sources() -> list[Path]:
    import core.agents as package

    return sorted(Path(package.__path__[0]).glob("*.py"))


@pytest.mark.parametrize("path", _agent_sources(), ids=lambda p: p.name)
def test_t29_no_hardcoded_old_board_literals(path):
    text = path.read_text(encoding="utf-8")
    offenders = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.NUMBER:
            continue
        try:
            value = int(token.string, 0)
        except ValueError:  # số thực
            continue
        if value in (9, 81):
            offenders.append((token.start[0], token.string))
    assert not offenders, f"{path.name}: literal của phạm vi cũ tại {offenders}"


_FORBIDDEN_ATTRS = {"grid", "_history", "board_array"}


@pytest.mark.parametrize("path", _agent_sources(), ids=lambda p: p.name)
def test_agents_use_only_public_engine_api(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    problems: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "core.engine":
                problems += [
                    f"line {node.lineno}: import core.engine.{a.name}"
                    for a in node.names
                    if a.name != "interfaces"
                ]
            elif node.module.startswith("core.engine.") and node.module != "core.engine.interfaces":
                problems.append(f"line {node.lineno}: import {node.module}")
        elif isinstance(node, ast.Import):
            problems += [
                f"line {node.lineno}: import {a.name}"
                for a in node.names
                if a.name.startswith("core.engine") and a.name != "core.engine.interfaces"
            ]
        elif isinstance(node, ast.Attribute):
            if node.attr in _FORBIDDEN_ATTRS:
                problems.append(f"line {node.lineno}: access .{node.attr}")
            elif (
                node.attr.startswith("_")
                and not node.attr.startswith("__")
                and isinstance(node.value, ast.Name)
                and node.value.id == "env"
            ):
                problems.append(f"line {node.lineno}: access env.{node.attr}")

    assert not problems, f"{path.name}: {problems}"
