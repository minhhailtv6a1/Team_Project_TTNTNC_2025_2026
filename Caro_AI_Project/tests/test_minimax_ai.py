# File: tests/test_minimax_ai.py
"""Test MinimaxAgent theo contract ``caro-v2`` (W34-T11 đến W34-T14).

Dùng ``SpyEnv`` bọc ``CaroEnv`` để đếm ``step`` và đo độ sâu thật của cây tìm
kiếm qua public API (``clone_env``/``step``/``undo``), không đọc private của agent.
"""
from __future__ import annotations

import pytest

from core.agents.minimax_ai import (
    WIN_VALUE,
    MinimaxAgent,
    candidate_actions,
    evaluate_board,
)
from core.engine.game_env import CaroEnv
from core.engine.interfaces import AgentDecision, Player, SearchBudget

SIZE = 11
WIN = 5
CLAMP = 500_000.0

X_FOUR_OPEN = [(5, 4), (0, 0), (5, 5), (0, 2), (5, 6), (0, 4), (5, 7), (10, 10)]
X_GAP_FOUR = [(5, 3), (0, 0), (5, 4), (0, 2), (5, 6), (0, 4), (5, 7)]
O_FOUR_OPEN = [
    (0, 0), (5, 4), (0, 2), (5, 5), (0, 4), (5, 6), (10, 10), (5, 7), (10, 8),
]
X_FOUR_AT_EDGE = [(0, 0), (5, 5), (0, 1), (5, 7), (0, 2), (7, 5), (0, 3), (7, 7)]
# O có bốn mở, X đến lượt và không thể thắng: X thua sau 2 ply dù chặn đầu nào.
X_TO_LOSE = [(0, 0), (5, 4), (0, 2), (5, 5), (0, 4), (5, 6), (10, 10), (5, 7)]
OPENING_TWO = [(5, 5), (5, 6)]
MIDGAME = [(5, 5), (4, 4), (5, 6), (6, 6), (3, 3), (7, 7)]

# Bàn 11x11 đầy, không có chuỗi 5 theo bất kỳ hướng nào (61 X, 60 O).
DRAW_BOARD = [
    "XXOOXXOOXXO",
    "OOXXOOXXOOX",
    "XXOOXXOOXXO",
    "OOXXOOXXOOX",
    "XXOOXXOOXXO",
    "OOXXOOXXOOX",
    "XXOOXXOOXXO",
    "OOXXOOXXOOX",
    "XXOOXXOOXXO",
    "OOXXOOXXOOX",
    "XXOOXXOOXXO",
]


def make_env(actions: list[tuple[int, int]]) -> CaroEnv:
    env = CaroEnv()
    for action in actions:
        env.step(action)
    return env


def draw_minus_one_actions() -> tuple[list[tuple[int, int]], tuple[int, int]]:
    """Chuỗi action dẫn tới bàn gần đầy; nước cuối (X) tạo hòa."""
    xs = [(r, c) for r in range(SIZE) for c in range(SIZE) if DRAW_BOARD[r][c] == "X"]
    os_ = [(r, c) for r in range(SIZE) for c in range(SIZE) if DRAW_BOARD[r][c] == "O"]
    assert len(xs) == 61 and len(os_) == 60
    last_x = xs[-1]
    seq: list[tuple[int, int]] = []
    for i in range(60):
        seq += [xs[i], os_[i]]
    return seq, last_x


class SpyEnv:
    """Bọc env: đếm ``step`` và độ sâu tối đa trên mọi clone."""

    def __init__(self, inner: CaroEnv, stats: dict | None = None) -> None:
        self._inner = inner
        self.stats = stats if stats is not None else {"steps": 0, "depth": 0, "max_depth": 0}

    config = property(lambda self: self._inner.config)
    state = property(lambda self: self._inner.state)

    def reset(self, seed=None):
        return self._inner.reset(seed)

    def legal_actions(self):
        return self._inner.legal_actions()

    def is_terminal(self):
        return self._inner.is_terminal()

    def result(self, player):
        return self._inner.result(player)

    def render(self):
        return self._inner.render()

    def step(self, action):
        result = self._inner.step(action)
        self.stats["steps"] += 1
        self.stats["depth"] += 1
        self.stats["max_depth"] = max(self.stats["max_depth"], self.stats["depth"])
        return result

    def undo(self):
        self.stats["depth"] -= 1
        return self._inner.undo()

    def clone_env(self):
        return SpyEnv(self._inner.clone_env(), self.stats)


def search(actions, depth=None, *, budget=None, **kwargs):
    env = make_env(actions)
    agent = MinimaxAgent(**kwargs)
    if budget is None and depth is not None:
        budget = SearchBudget(max_depth=depth)
    return agent, agent.choose_action(env, budget)


# --- Hợp đồng chung --------------------------------------------------------------
def test_terminal_env_raises():
    env = make_env([(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3), (0, 4)])
    with pytest.raises(RuntimeError):
        MinimaxAgent().choose_action(env)


def test_decision_shape_and_legality():
    env = make_env(MIDGAME)
    decision = MinimaxAgent().choose_action(env, SearchBudget(max_depth=2))
    assert isinstance(decision, AgentDecision)
    assert isinstance(decision.action, tuple) and len(decision.action) == 2
    assert all(type(v) is int for v in decision.action)
    assert decision.action in env.legal_actions()
    assert decision.score is not None
    assert decision.nodes > 0 and decision.simulations == 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"default_depth": 0},
        {"neighbor_radius": 0},
        {"max_candidates": 0},
        {"max_candidates": 5, "move_ordering": False},
    ],
)
def test_constructor_rejects_invalid_arguments(kwargs):
    with pytest.raises(ValueError):
        MinimaxAgent(**kwargs)


def test_opening_empty_board_plays_center():
    env = CaroEnv()
    assert MinimaxAgent().choose_action(env, SearchBudget(max_depth=2)).action == (5, 5)


# --- Evaluation / candidate -------------------------------------------------------
def test_candidate_actions_empty_board_is_center():
    assert candidate_actions(CaroEnv().state.board) == [(5, 5)]


def test_candidate_actions_at_corner_stay_in_bounds():
    env = make_env([(0, 0)])
    cells = candidate_actions(env.state.board, env.legal_actions(), radius=2)
    assert cells == [(0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)]


def test_candidate_actions_exclude_occupied_and_are_legal():
    env = make_env(MIDGAME)
    legal = set(env.legal_actions())
    cells = candidate_actions(env.state.board, env.legal_actions())
    assert cells == sorted(cells)  # row-major
    assert set(cells) <= legal and len(cells) == len(set(cells))


def test_evaluate_board_is_zero_sum_across_perspectives():
    board = make_env(MIDGAME).state.board
    assert evaluate_board(board, Player.X, WIN) == pytest.approx(
        -evaluate_board(board, Player.O, WIN)
    )
    assert evaluate_board(CaroEnv().state.board, Player.X, WIN) == 0.0


def test_evaluate_board_favors_player_with_open_three():
    board = make_env([(5, 4), (0, 0), (5, 5), (0, 2), (5, 6), (0, 4)]).state.board
    assert evaluate_board(board, Player.X, WIN) > 0 > evaluate_board(board, Player.O, WIN)
    assert abs(evaluate_board(board, Player.X, WIN)) <= CLAMP


# --- T11: terminal leaf X/O/draw, score theo góc nhìn root -------------------------
def test_t11_x_wins_in_one():
    _, d = search(X_FOUR_OPEN, 1)
    assert d.action in {(5, 3), (5, 8)}
    assert d.score == WIN_VALUE - 1


def test_t11_o_wins_in_one_score_is_from_o_perspective():
    env = make_env(O_FOUR_OPEN)
    assert env.state.current_player == Player.O
    d = MinimaxAgent().choose_action(env, SearchBudget(max_depth=1))
    assert d.action in {(5, 3), (5, 8)}
    assert d.score == WIN_VALUE - 1  # dương: tốt cho root dù root là O


def test_t11_x_loses_in_two_gives_negative_win_value():
    _, d = search(X_TO_LOSE, 2)
    assert d.score == -(WIN_VALUE - 2)
    assert d.action in {(5, 3), (5, 8)}  # chặn một đầu cũng thua, vẫn là nước legal


def test_t11_o_loses_in_two_gives_negative_win_value():
    # X có bốn mở, O đi: O không thắng được, thua sau 2 ply.
    env = make_env(
        [(5, 4), (0, 0), (5, 5), (0, 2), (5, 6), (0, 4), (5, 7)]
    )
    assert env.state.current_player == Player.O
    d = MinimaxAgent().choose_action(env, SearchBudget(max_depth=2))
    assert d.score == -(WIN_VALUE - 2)


def test_t11_draw_leaf_scores_zero():
    seq, last_x = draw_minus_one_actions()
    env = make_env(seq)
    assert env.state.current_player == Player.X and env.state.move_count == 120
    assert env.legal_actions() == [last_x]
    d = MinimaxAgent().choose_action(env, SearchBudget(max_depth=3))
    assert d.action == last_x
    assert d.score == 0.0
    assert env.state.move_count == 120  # không mutation


def test_t11_faster_win_scores_higher_than_slower_win():
    # X có bốn mở: thắng ở ply 1 (WIN-1) phải cao hơn mọi thắng ply 3 (WIN-3).
    _, d = search(X_FOUR_OPEN, 3, max_candidates=6)
    assert d.score == WIN_VALUE - 1


def test_t11_forced_win_stops_deepening():
    agent, d = search(X_FOUR_OPEN, 4)
    assert agent.last_depth_completed == 1
    assert agent.last_stop_reason == "forced_win"
    assert d.score == WIN_VALUE - 1


def test_t11_winning_move_at_board_edge():
    _, d = search(X_FOUR_AT_EDGE, 2)
    assert d.action == (0, 4)
    assert d.score == WIN_VALUE - 1


def test_t11_must_block_forced_action_at_depth_two():
    # X X _ X X: O phải chặn đúng (5,5) mới không thua ngay.
    env = make_env(X_GAP_FOUR)
    assert env.state.current_player == Player.O
    d = MinimaxAgent().choose_action(env, SearchBudget(max_depth=2))
    assert d.action == (5, 5)
    assert d.score > -CLAMP


# --- T12: pruning on/off tương thích -------------------------------------------------
CASES = [
    (OPENING_TWO, 2, None),
    (MIDGAME, 2, None),
    (MIDGAME, 3, 8),
    (X_GAP_FOUR, 2, None),
    (X_FOUR_AT_EDGE, 2, None),
    (O_FOUR_OPEN, 2, None),
]


@pytest.mark.parametrize("actions,depth,cap", CASES)
def test_t12_pruning_on_off_same_action_and_score(actions, depth, cap):
    _, plain = search(actions, depth, alpha_beta=False, max_candidates=cap)
    _, pruned = search(actions, depth, alpha_beta=True, max_candidates=cap)
    assert pruned.action == plain.action
    assert pruned.score == plain.score
    assert pruned.nodes <= plain.nodes  # pruning không được tăng nodes


def test_t12_pruning_strictly_reduces_nodes_on_wide_tree():
    _, plain = search(MIDGAME, 3, alpha_beta=False, max_candidates=8)
    _, pruned = search(MIDGAME, 3, alpha_beta=True, max_candidates=8)
    assert pruned.nodes < plain.nodes


def test_t12_move_ordering_does_not_change_score():
    _, ordered = search(MIDGAME, 2, move_ordering=True)
    _, unordered = search(MIDGAME, 2, move_ordering=False)
    assert ordered.score == unordered.score
    assert ordered.action in make_env(MIDGAME).legal_actions()


def test_t12_nodes_equal_number_of_step_calls_for_both_modes():
    for alpha_beta in (False, True):
        spy = SpyEnv(make_env(MIDGAME))
        d = MinimaxAgent(alpha_beta=alpha_beta).choose_action(spy, SearchBudget(max_depth=2))
        assert d.nodes == spy.stats["steps"]


def test_t12_search_is_deterministic():
    _, a = search(MIDGAME, 2)
    _, b = search(MIDGAME, 2)
    assert (a.action, a.score, a.nodes) == (b.action, b.score, b.nodes)


# --- T13: max_depth 2/3/4 không bị vượt ----------------------------------------------
@pytest.mark.parametrize("depth", [2, 3, 4])
@pytest.mark.parametrize("alpha_beta", [True, False])
def test_t13_never_exceeds_max_depth(depth, alpha_beta):
    spy = SpyEnv(make_env(MIDGAME))
    agent = MinimaxAgent(alpha_beta=alpha_beta, max_candidates=5)
    d = agent.choose_action(spy, SearchBudget(max_depth=depth))
    assert spy.stats["max_depth"] == depth  # đạt đúng depth, không vượt
    assert spy.stats["depth"] == 0  # mọi step đã được undo
    assert agent.last_depth_completed == depth
    assert agent.last_stop_reason == "depth_limit"
    assert d.action in make_env(MIDGAME).legal_actions()


def test_t13_default_depth_used_without_budget():
    spy = SpyEnv(make_env(MIDGAME))
    agent = MinimaxAgent(default_depth=2)
    agent.choose_action(spy)
    assert spy.stats["max_depth"] == 2


def test_t13_budget_depth_overrides_default():
    spy = SpyEnv(make_env(MIDGAME))
    MinimaxAgent(default_depth=3, max_candidates=5).choose_action(spy, SearchBudget(max_depth=1))
    assert spy.stats["max_depth"] == 1


def test_t13_depth_reached_on_opening_and_opening_two_plies():
    for actions in ([], OPENING_TWO):
        spy = SpyEnv(make_env(actions))
        MinimaxAgent(max_candidates=5).choose_action(spy, SearchBudget(max_depth=3))
        assert spy.stats["max_depth"] == 3


# --- T14: nodes/time budget, dừng an toàn ----------------------------------------------
@pytest.mark.parametrize("max_nodes", [1, 5, 40, 300])
@pytest.mark.parametrize("alpha_beta", [True, False])
def test_t14_max_nodes_never_exceeded_and_action_legal(max_nodes, alpha_beta):
    env = make_env(MIDGAME)
    agent = MinimaxAgent(alpha_beta=alpha_beta)
    d = agent.choose_action(env, SearchBudget(max_depth=6, max_nodes=max_nodes))
    assert d.nodes <= max_nodes
    assert d.action in env.legal_actions()
    assert agent.last_stop_reason == "max_nodes"


def test_t14_budget_hit_before_depth_one_returns_heuristic_move_without_score():
    env = make_env(MIDGAME)
    agent = MinimaxAgent()
    d = agent.choose_action(env, SearchBudget(max_depth=4, max_nodes=2))
    assert d.score is None
    assert agent.last_depth_completed == 0
    assert d.action in env.legal_actions()


def test_t14_budget_rejects_non_positive_nodes():
    with pytest.raises(ValueError):
        SearchBudget(max_nodes=0)


def test_t14_cut_mid_iteration_keeps_last_completed_depth():
    env = make_env(MIDGAME)
    ref_agent = MinimaxAgent()
    ref = ref_agent.choose_action(env, SearchBudget(max_depth=1))
    root_nodes = ref.nodes
    agent = MinimaxAgent()
    d = agent.choose_action(env, SearchBudget(max_depth=3, max_nodes=root_nodes + 1))
    assert agent.last_depth_completed == 1
    assert agent.last_stop_reason == "max_nodes"
    assert d.action == ref.action and d.score == ref.score  # đáp án depth 1 giữ nguyên
    assert d.nodes == root_nodes + 1


def test_t14_time_limit_zero_stops_before_any_node():
    env = make_env(MIDGAME)
    agent = MinimaxAgent()
    d = agent.choose_action(env, SearchBudget(max_depth=4, time_limit_ms=0))
    assert agent.last_stop_reason == "time_limit"
    assert d.score is None and d.nodes == 0
    assert d.action in env.legal_actions()


def test_t14_time_limit_stops_deep_search_safely():
    env = make_env(MIDGAME)
    agent = MinimaxAgent()  # không giới hạn candidate: depth 6 không thể xong trong 40ms
    d = agent.choose_action(env, SearchBudget(max_depth=6, time_limit_ms=40))
    assert agent.last_stop_reason == "time_limit"
    assert d.action in env.legal_actions()
    assert d.elapsed_ms < 40 + 150  # sai số cỡ một lần ordering/evaluation


def test_t14_nodes_and_time_precedence_first_limit_wins():
    env = make_env(MIDGAME)
    agent = MinimaxAgent()
    agent.choose_action(env, SearchBudget(max_depth=6, max_nodes=3, time_limit_ms=60_000))
    assert agent.last_stop_reason == "max_nodes"


# --- No-mutation -------------------------------------------------------------------------
@pytest.mark.parametrize(
    "actions", [[], OPENING_TWO, MIDGAME, X_FOUR_OPEN, X_GAP_FOUR, O_FOUR_OPEN]
)
@pytest.mark.parametrize(
    "budget",
    [
        SearchBudget(max_depth=2),
        SearchBudget(max_depth=4, max_nodes=50),
        SearchBudget(max_depth=4, time_limit_ms=0),
    ],
)
def test_no_mutation_of_env_including_early_stop(actions, budget):
    env = make_env(actions)
    before_state, before_render, before_legal = env.state, env.render(), env.legal_actions()

    MinimaxAgent(max_candidates=6).choose_action(env, budget)

    assert env.state == before_state
    assert env.render() == before_render
    assert env.legal_actions() == before_legal


def test_history_of_original_env_is_untouched():
    env = make_env(MIDGAME)
    MinimaxAgent().choose_action(env, SearchBudget(max_depth=2, max_nodes=200))
    assert env.undo() == make_env(MIDGAME[:-1]).state