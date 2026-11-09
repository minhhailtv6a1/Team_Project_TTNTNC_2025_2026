"""W34-M1: unit và contract tests cho MCTSAgent."""

from __future__ import annotations

import math
import random

import pytest

from core.agents.mcts_ai import (
    MCTSAgent,
    _MCTSNode,
    _backpropagate,
    _allowed_children,
    _expand,
    _rollout,
    _select_child,
    _uct_score,
)
from core.agents.search_utils import (
    choose_tactical_local_action,
    immediate_winning_actions,
    normalized_line_value,
    tactical_summary,
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


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"tactical_precheck": 1}, "tactical_precheck"),
        ({"candidate_policy": "heuristic"}, "candidate_policy"),
        ({"neighbor_radius": 0}, "neighbor_radius"),
        ({"progressive_widening_c": 0}, "progressive_widening_c"),
        ({"progressive_widening_c": math.inf}, "progressive_widening_c"),
        ({"progressive_widening_alpha": 0}, "progressive_widening_alpha"),
        ({"progressive_widening_alpha": 1.1}, "progressive_widening_alpha"),
        ({"rollout_policy": "greedy"}, "rollout_policy"),
        ({"rollout_epsilon": -0.1}, "rollout_epsilon"),
        ({"rollout_epsilon": 1.1}, "rollout_epsilon"),
        ({"reuse_simulation_env": 1}, "reuse_simulation_env"),
        ({"rollout_horizon": 0}, "rollout_horizon"),
        ({"leaf_evaluation": "network"}, "leaf_evaluation"),
    ],
)
def test_invalid_phase1_options_are_rejected(kwargs, message):
    with pytest.raises(ValueError, match=message):
        MCTSAgent(**kwargs)


# ---------------------------------------------------------------------------
# Phase 1: pure tactical helpers and tactical pre-check
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "stones",
    [
        [(5, 2), (5, 3), (5, 4), (5, 5)],
        [(2, 5), (3, 5), (4, 5), (5, 5)],
        [(2, 2), (3, 3), (4, 4), (5, 5)],
        [(2, 8), (3, 7), (4, 6), (5, 5)],
        [(0, 0), (0, 1), (0, 2), (0, 3)],
    ],
)
def test_phase1_immediate_win_detects_directions_and_edge_without_mutation(stones):
    board = [[0] * 11 for _ in range(11)]
    for row, col in stones:
        board[row][col] = int(Player.X)
    before = [row[:] for row in board]
    legal = [(r, c) for r in range(11) for c in range(11) if board[r][c] == 0]

    wins = immediate_winning_actions(board, legal, Player.X, CaroEnv().config)

    assert wins
    assert board == before


def test_phase1_immediate_win_detects_o_and_no_false_positive():
    board = [[0] * 11 for _ in range(11)]
    for col in range(3, 7):
        board[6][col] = int(Player.O)
    legal = [(r, c) for r in range(11) for c in range(11) if board[r][c] == 0]
    assert set(immediate_winning_actions(board, legal, Player.O, CaroEnv().config)) == {
        (6, 2),
        (6, 7),
    }

    quiet = [[0] * 11 for _ in range(11)]
    quiet[5][5] = int(Player.X)
    quiet_legal = [(r, c) for r in range(11) for c in range(11) if quiet[r][c] == 0]
    assert immediate_winning_actions(quiet, quiet_legal, Player.X, CaroEnv().config) == []


def test_phase1_tactical_summary_reports_unique_block_and_multiple_threats():
    block_env = env_from([(5, 3), (0, 0), (5, 4), (0, 2), (5, 6), (0, 4), (5, 7)])
    state = block_env.state
    summary = tactical_summary(
        state.board, block_env.legal_actions(), state.current_player, block_env.config
    )
    assert summary.unique_forced_block == (5, 5)
    assert not summary.has_unanswerable_threats

    board = [[0] * 11 for _ in range(11)]
    for col in range(3, 7):
        board[4][col] = int(Player.X)
    legal = [(r, c) for r in range(11) for c in range(11) if board[r][c] == 0]
    multiple = tactical_summary(board, legal, Player.O, CaroEnv().config)
    assert set(multiple.opponent_winning_actions) == {(4, 2), (4, 7)}
    assert multiple.unique_forced_block is None
    assert multiple.has_unanswerable_threats


def upgraded_agent(**kwargs) -> MCTSAgent:
    options = {
        "tactical_precheck": True,
        "candidate_policy": "tactical_local_seeded",
        "progressive_widening_c": 2.0,
        "progressive_widening_alpha": 0.5,
    }
    options.update(kwargs)
    return MCTSAgent(**options)


def test_phase1_tactical_override_win_and_block_have_defined_counters():
    win_env = env_from([(5, 4), (0, 0), (5, 5), (0, 2), (5, 6), (0, 4), (5, 7), (10, 10)])
    win = upgraded_agent().choose_action(win_env, SearchBudget(simulations=100, seed=11))
    assert win.action in {(5, 3), (5, 8)}
    assert (win.nodes, win.simulations, win.score) == (1, 0, 1.0)

    block_env = env_from([(5, 3), (0, 0), (5, 4), (0, 2), (5, 6), (0, 4), (5, 7)])
    agent = upgraded_agent()
    block = agent.choose_action(block_env, SearchBudget(simulations=100, seed=11))
    assert block.action == (5, 5)
    assert (block.nodes, block.simulations, block.score) == (1, 0, 0.0)
    assert agent.last_search_stats["tactical_override"] == "block"


def test_phase1_progressive_widening_revisits_root_and_reaches_depth_two():
    agent = upgraded_agent(tactical_precheck=False)
    decision = agent.choose_action(env_from(MIDGAME), SearchBudget(simulations=100, seed=11))
    stats = agent.last_search_stats

    assert decision.simulations == 100
    assert stats["root_children"] < 100
    assert stats["root_max_visits"] > 1
    assert stats["max_tree_depth"] >= 2


def test_phase1_progressive_widening_limits_and_eventually_allows_every_action():
    root = node(visits=0)
    root.untried_actions = [(0, i) for i in range(10)]
    assert _allowed_children(root, widening_c=2.0, widening_alpha=0.5) == 2
    root.visits = 10_000
    assert _allowed_children(root, widening_c=2.0, widening_alpha=0.5) == 10
    assert _allowed_children(root, widening_c=None, widening_alpha=0.5) == 10


def test_phase1_upgraded_mode_respects_node_budget_and_is_reproducible():
    budget = SearchBudget(simulations=100, max_nodes=20, seed=33)
    first_agent = upgraded_agent(tactical_precheck=False)
    second_agent = upgraded_agent(tactical_precheck=False)
    first_env, second_env = env_from(MIDGAME), env_from(MIDGAME)
    first = first_agent.choose_action(first_env, budget)
    second = second_agent.choose_action(second_env, budget)
    assert first.nodes <= 20
    assert first.action == second.action
    assert first.score == second.score
    assert first.nodes == second.nodes
    assert first.simulations == second.simulations
    assert first_env.state == env_from(MIDGAME).state


# ---------------------------------------------------------------------------
# Phase 2: tactical-local rollout and clone-once/undo optimization
# ---------------------------------------------------------------------------
def test_phase2_rollout_policy_takes_immediate_win_and_unique_block():
    win_env = env_from([(5, 4), (0, 0), (5, 5), (0, 2), (5, 6), (0, 4), (5, 7), (10, 10)])
    state = win_env.state
    action = choose_tactical_local_action(
        state.board,
        win_env.legal_actions(),
        state.current_player,
        win_env.config,
        neighbor_radius=2,
        epsilon=1.0,
        rng=random.Random(1),
    )
    assert action in {(5, 3), (5, 8)}

    block_env = env_from([(5, 3), (0, 0), (5, 4), (0, 2), (5, 6), (0, 4), (5, 7)])
    state = block_env.state
    action = choose_tactical_local_action(
        state.board,
        block_env.legal_actions(),
        state.current_player,
        block_env.config,
        neighbor_radius=2,
        epsilon=1.0,
        rng=random.Random(1),
    )
    assert action == (5, 5)


def test_phase2_guided_rollout_is_seeded_and_reaches_terminal():
    def run():
        env = env_from(MIDGAME)
        reward = _rollout(
            env,
            root_player=env.state.current_player,
            rng=random.Random(19),
            deadline=None,
            policy="epsilon_tactical_local",
            epsilon=0.15,
            neighbor_radius=2,
        )
        return reward, env.state

    assert run() == run()
    reward, state = run()
    assert state.terminated
    assert reward in (-1.0, 0.0, 1.0)


def phase2_agent(*, reuse_simulation_env: bool) -> MCTSAgent:
    return upgraded_agent(
        tactical_precheck=False,
        rollout_policy="epsilon_tactical_local",
        rollout_epsilon=0.15,
        reuse_simulation_env=reuse_simulation_env,
    )


def test_phase2_clone_once_undo_matches_per_simulation_clone_and_preserves_env():
    budget = SearchBudget(simulations=80, seed=23)
    original = env_from(MIDGAME)
    before = original.state
    clone_each = phase2_agent(reuse_simulation_env=False).choose_action(original, budget)
    shared_agent = phase2_agent(reuse_simulation_env=True)
    clone_once = shared_agent.choose_action(original, budget)

    assert (clone_once.action, clone_once.score, clone_once.nodes, clone_once.simulations) == (
        clone_each.action,
        clone_each.score,
        clone_each.nodes,
        clone_each.simulations,
    )
    assert original.state == before
    assert shared_agent.last_search_stats["timing_ms"]["clone"] >= 0.0


def test_phase2_clone_once_rewinds_when_time_budget_interrupts_rollout():
    env = env_from(MIDGAME)
    before = env.state
    decision = phase2_agent(reuse_simulation_env=True).choose_action(
        env, SearchBudget(simulations=100_000, time_limit_ms=10, seed=7)
    )
    assert decision.action in env.legal_actions()
    assert decision.simulations < 100_000
    assert env.state == before


def test_phase2_normalized_line_value_is_bounded_and_antisymmetric():
    env = env_from(MIDGAME)
    board = env.state.board
    x_value = normalized_line_value(board, Player.X, env.config.win_length)
    o_value = normalized_line_value(board, Player.O, env.config.win_length)
    assert -1.0 <= x_value <= 1.0
    assert -1.0 <= o_value <= 1.0
    assert x_value == pytest.approx(-o_value)


def test_phase2_rollout_horizon_uses_normalized_nonterminal_value():
    env = env_from(MIDGAME)
    before_count = env.state.move_count
    reward = _rollout(
        env,
        root_player=env.state.current_player,
        rng=random.Random(5),
        deadline=None,
        policy="epsilon_tactical_local",
        epsilon=0.15,
        neighbor_radius=2,
        horizon=4,
    )
    assert not env.is_terminal()
    assert env.state.move_count == before_count + 4
    assert reward is not None and -1.0 <= reward <= 1.0


def test_strength_profile_is_seeded_legal_and_uses_bounded_pattern_leaf():
    options = {
        "tactical_precheck": True,
        "candidate_policy": "heuristic_seeded",
        "progressive_widening_c": 1.5,
        "progressive_widening_alpha": 0.5,
        "rollout_policy": "epsilon_heuristic",
        "rollout_epsilon": 0.15,
        "rollout_horizon": 8,
        "leaf_evaluation": "pattern",
        "reuse_simulation_env": True,
        "exploration_weight": 0.7,
    }
    budget = SearchBudget(simulations=80, seed=31)
    env = env_from(MIDGAME)
    before = env.state
    first = MCTSAgent(**options).choose_action(env, budget)
    second = MCTSAgent(**options).choose_action(env, budget)
    assert first.action in env.legal_actions()
    assert (first.action, first.score, first.nodes, first.simulations) == (
        second.action,
        second.score,
        second.nodes,
        second.simulations,
    )
    assert -1.0 <= float(first.score) <= 1.0
    assert env.state == before


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
