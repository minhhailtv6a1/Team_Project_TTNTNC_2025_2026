"""W34-M1: unit và contract tests cho MCTSAgent."""

from __future__ import annotations

import math
import random

import pytest

from core.agents.mcts_ai import (
    MCTSAgent,
    _MCTSNode,
    _backpropagate,
    _expand,
    _rollout,
    _select_child,
    _uct_score,
)
from core.engine.game_env import CaroEnv
from core.engine.interfaces import Agent, Player, SearchBudget, UndoError


MIDGAME = [(5, 5), (4, 4), (5, 6), (6, 6), (3, 3), (7, 7)]
TERMINAL = [
    (5, 3),
    (0, 0),
    (5, 4),
    (0, 2),
    (5, 5),
    (0, 4),
    (5, 6),
    (10, 10),
    (5, 7),
]


def env_from(actions: list[tuple[int, int]]) -> CaroEnv:
    env = CaroEnv()
    for action in actions:
        env.step(action)
    return env


def node(
    *,
    parent: _MCTSNode | None = None,
    action: tuple[int, int] | None = None,
    player: Player = Player.X,
    visits: int = 0,
    value: float = 0.0,
) -> _MCTSNode:
    return _MCTSNode(
        parent=parent,
        action=action,
        player_to_move=player,
        untried_actions=[],
        visits=visits,
        value_sum=value,
    )


# ---------------------------------------------------------------------------
# Protocol và validation
# ---------------------------------------------------------------------------
def test_agent_protocol_name_and_repr():
    agent = MCTSAgent()
    assert isinstance(agent, Agent)
    assert agent.name == "mcts"
    assert MCTSAgent(name="tree-search").name == "tree-search"
    assert "MCTSAgent" in repr(agent)


@pytest.mark.parametrize("bad_name", ["", None, 4])
def test_invalid_name_is_rejected(bad_name):
    with pytest.raises(ValueError):
        MCTSAgent(name=bad_name)


@pytest.mark.parametrize("bad", [-1.0, math.inf, math.nan, True, "uct"])
def test_invalid_exploration_weight_is_rejected(bad):
    with pytest.raises(ValueError):
        MCTSAgent(exploration_weight=bad)


@pytest.mark.parametrize("bad", [0, -1, True, 1.5])
def test_invalid_default_simulations_is_rejected(bad):
    with pytest.raises(ValueError):
        MCTSAgent(default_simulations=bad)


# ---------------------------------------------------------------------------
# W34-T15: Selection / UCT
# ---------------------------------------------------------------------------
def test_t15_unvisited_child_has_infinite_uct_without_division_by_zero():
    child = node()
    assert math.isinf(
        _uct_score(
            child,
            parent_visits=0,
            exploration_weight=math.sqrt(2.0),
            maximize_root_value=True,
        )
    )


def test_t15_selection_maximizes_on_root_turn_and_minimizes_on_opponent_turn():
    high = node(action=(1, 1), visits=10, value=8.0)
    low = node(action=(2, 2), visits=10, value=-4.0)

    root_turn = node(player=Player.X, visits=20)
    root_turn.children = [low, high]
    high.parent = low.parent = root_turn
    assert _select_child(
        root_turn,
        root_player=Player.X,
        exploration_weight=0.0,
        rng=random.Random(1),
    ) is high

    opponent_turn = node(player=Player.O, visits=20)
    opponent_turn.children = [low, high]
    high.parent = low.parent = opponent_turn
    assert _select_child(
        opponent_turn,
        root_player=Player.X,
        exploration_weight=0.0,
        rng=random.Random(1),
    ) is low


def test_t15_seeded_tie_break_is_reproducible():
    parent = node(visits=2)
    parent.children = [
        node(parent=parent, action=(1, 1), visits=1),
        node(parent=parent, action=(2, 2), visits=1),
    ]
    first = _select_child(
        parent,
        root_player=Player.X,
        exploration_weight=0.0,
        rng=random.Random(9),
    )
    second = _select_child(
        parent,
        root_player=Player.X,
        exploration_weight=0.0,
        rng=random.Random(9),
    )
    assert first.action == second.action


# ---------------------------------------------------------------------------
# W34-T16: Expansion
# ---------------------------------------------------------------------------
def test_t16_expansion_creates_only_unique_legal_children():
    original = env_from(MIDGAME)
    legal = set(original.legal_actions())
    root = _MCTSNode(
        parent=None,
        action=None,
        player_to_move=original.state.current_player,
        untried_actions=original.legal_actions(),
    )
    rng = random.Random(3)

    for _ in range(30):
        clone = original.clone_env()
        child = _expand(root, clone, rng)
        assert child.action in legal
        assert clone.state.last_action == child.action
        assert child.parent is root

    actions = [child.action for child in root.children]
    assert len(actions) == len(set(actions)) == 30
    assert not (set(actions) - legal)


# ---------------------------------------------------------------------------
# W34-T17: Rollout
# ---------------------------------------------------------------------------
def test_t17_rollout_reaches_terminal_and_returns_root_reward():
    env = env_from(MIDGAME)
    root_player = env.state.current_player
    reward = _rollout(
        env,
        root_player=root_player,
        rng=random.Random(12),
        deadline=None,
    )
    assert env.is_terminal()
    assert reward == env.result(root_player)
    assert reward in (-1.0, 0.0, 1.0)


def test_t17_expired_deadline_aborts_rollout_without_fake_reward():
    env = CaroEnv()
    assert _rollout(
        env,
        root_player=Player.X,
        rng=random.Random(1),
        deadline=0.0,
    ) is None
    assert env.state.move_count == 0


# ---------------------------------------------------------------------------
# W34-T18: Backpropagation
# ---------------------------------------------------------------------------
def test_t18_backpropagation_updates_exact_path():
    root = node()
    child = node(parent=root, action=(1, 1), player=Player.O)
    leaf = node(parent=child, action=(2, 2), player=Player.X)

    _backpropagate(leaf, 1.0)
    _backpropagate(leaf, -1.0)

    for current in (root, child, leaf):
        assert current.visits == 2
        assert current.value_sum == 0.0
        assert current.mean_value == 0.0


# ---------------------------------------------------------------------------
# W34-T19: simulation/node/time budgets và counter
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("simulations", [100, 400, 1000])
def test_t19_profile_simulation_counter_is_exact(simulations):
    decision = MCTSAgent().choose_action(
        env_from(MIDGAME),
        SearchBudget(simulations=simulations, seed=11),
    )
    assert decision.simulations == simulations
    assert decision.nodes == simulations + 1


def test_t19_max_nodes_stops_tree_growth_safely():
    env = env_from(MIDGAME)
    decision = MCTSAgent().choose_action(
        env,
        SearchBudget(simulations=100, max_nodes=3, seed=2),
    )
    assert decision.nodes == 3
    assert decision.simulations == 2
    assert decision.action in env.legal_actions()


def test_t19_zero_time_budget_returns_legal_fallback_without_simulation():
    env = env_from(MIDGAME)
    decision = MCTSAgent().choose_action(
        env,
        SearchBudget(time_limit_ms=0, simulations=100, seed=2),
    )
    assert decision.action in env.legal_actions()
    assert decision.nodes == 1
    assert decision.simulations == 0
    assert decision.elapsed_ms >= 0.0


def test_t19_positive_time_budget_stops_with_tolerance():
    env = env_from(MIDGAME)
    decision = MCTSAgent().choose_action(
        env,
        SearchBudget(time_limit_ms=10, simulations=100_000, seed=2),
    )
    assert decision.action in env.legal_actions()
    assert decision.simulations < 100_000
    # CI không assert chính xác millisecond; 250 ms là tolerance rộng cho máy chậm.
    assert decision.elapsed_ms < 250.0


def test_default_simulation_budget_is_used_when_budget_omits_limit():
    decision = MCTSAgent(default_simulations=7).choose_action(
        env_from(MIDGAME), SearchBudget(seed=1)
    )
    assert decision.simulations == 7
    assert decision.nodes == 8


# ---------------------------------------------------------------------------
# W34-T20: deterministic seed, legality và no-mutation
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("seed", [0, 11, 33])
def test_t20_same_state_seed_and_budget_are_reproducible(seed):
    budget = SearchBudget(simulations=40, seed=seed)
    first = MCTSAgent().choose_action(env_from(MIDGAME), budget)
    second = MCTSAgent().choose_action(env_from(MIDGAME), budget)
    assert first.action == second.action
    assert first.score == second.score
    assert first.nodes == second.nodes
    assert first.simulations == second.simulations


def test_t20_reusing_agent_with_budget_seed_is_reproducible():
    env = env_from(MIDGAME)
    agent = MCTSAgent(seed=999)
    budget = SearchBudget(simulations=25, seed=7)
    first = agent.choose_action(env, budget)
    second = agent.choose_action(env, budget)
    assert (first.action, first.score, first.nodes, first.simulations) == (
        second.action,
        second.score,
        second.nodes,
        second.simulations,
    )


def test_choose_action_does_not_mutate_board_metadata_or_history():
    env = env_from(MIDGAME)
    before_state = env.state
    before_legal = env.legal_actions()
    before_render = env.render()
    probe = env.clone_env()
    before_undo = probe.undo()

    decision = MCTSAgent().choose_action(
        env, SearchBudget(simulations=50, seed=5)
    )

    assert decision.action in before_legal
    assert env.state == before_state
    assert env.legal_actions() == before_legal
    assert env.render() == before_render
    after_probe = env.clone_env()
    assert after_probe.undo() == before_undo


def test_empty_history_stays_empty_after_search():
    env = CaroEnv()
    MCTSAgent().choose_action(env, SearchBudget(simulations=5, seed=4))
    with pytest.raises(UndoError):
        env.undo()


def test_terminal_environment_is_rejected_without_mutation():
    env = env_from(TERMINAL)
    before = env.state
    with pytest.raises(RuntimeError):
        MCTSAgent().choose_action(env, SearchBudget(simulations=5, seed=1))
    assert env.state == before


def test_public_action_is_row_col_tuple_and_score_is_finite():
    env = env_from(MIDGAME)
    decision = MCTSAgent().choose_action(
        env, SearchBudget(simulations=20, seed=2)
    )
    assert type(decision.action) is tuple and len(decision.action) == 2
    assert all(type(part) is int for part in decision.action)
    assert decision.action in env.legal_actions()
    assert math.isfinite(decision.score)


def test_agent_does_not_touch_global_random_state():
    random.seed(12345)
    before = random.getstate()
    MCTSAgent().choose_action(
        env_from(MIDGAME), SearchBudget(simulations=10, seed=8)
    )
    assert random.getstate() == before
