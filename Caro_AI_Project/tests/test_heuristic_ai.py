# File: tests/test_heuristic_ai.py
"""Test HeuristicAgent theo contract ``caro-v2`` (W34-T07 đến W34-T10).

Mọi scenario được dựng bằng chuỗi action public qua ``CaroEnv.step``; test chỉ
phụ thuộc public API (``state``, ``legal_actions``, ``choose_action``).
"""
from __future__ import annotations

import pytest

from core.agents.heuristic_ai import (
    BLOCK_SCORE,
    WIN_SCORE,
    HeuristicAgent,
    action_priority,
    center_bonus,
)
from core.engine.game_env import CaroEnv
from core.engine.interfaces import AgentDecision, Player

SIZE = 11
WIN = 5

# --- Scenario (tọa độ (row, col)) --------------------------------------------
# X có bốn liền hàng 5, hai đầu trống: thắng tại (5,3) hoặc (5,8).
X_FOUR_OPEN = [(5, 4), (0, 0), (5, 5), (0, 2), (5, 6), (0, 4), (5, 7), (10, 10)]
# X có thế X X _ X X ở hàng 5: O phải chặn (5,5).
X_GAP_FOUR = [(5, 3), (0, 0), (5, 4), (0, 2), (5, 6), (0, 4), (5, 7)]
# O có bốn liền hàng 5, X đang đi nhưng không có nước thắng: X phải chặn.
O_FOUR_OPEN = [
    (0, 0), (5, 4), (0, 2), (5, 5), (0, 4), (5, 6), (10, 10), (5, 7), (10, 8),
]  # O đi tiếp: thắng (5,3)/(5,8)
# X có bốn sát biên trên (0,0)-(0,3): chỉ thắng được tại (0,4).
X_FOUR_AT_EDGE = [
    (0, 0), (5, 5), (0, 1), (5, 7), (0, 2), (7, 5), (0, 3), (7, 7),
]
# O có bốn sát biên trái (0,0)-(3,0): X chỉ chặn được tại (4,0).
O_FOUR_AT_EDGE = [
    (5, 5), (0, 0), (5, 7), (1, 0), (7, 5), (2, 0), (7, 7), (3, 0),
]
# X có ba mở hàng 5 (cột 4-6), chưa ai có nước thắng.
X_OPEN_THREE = [(5, 4), (0, 0), (5, 5), (0, 2), (5, 6), (0, 4)]
MIDGAME = [(5, 5), (4, 4), (5, 6), (6, 6), (3, 3), (7, 7)]


def make_env(actions: list[tuple[int, int]]) -> CaroEnv:
    env = CaroEnv()
    for action in actions:
        env.step(action)
    return env


def best_priority_cells(env: CaroEnv) -> list[tuple[int, int]]:
    """Mọi ô đạt điểm ưu tiên cao nhất (độc lập với agent)."""
    state = env.state
    scored = {
        a: action_priority(state.board, a, state.current_player, WIN)
        for a in env.legal_actions()
    }
    top = max(scored.values())
    return sorted(a for a, s in scored.items() if s == top)


@pytest.fixture
def agent() -> HeuristicAgent:
    return HeuristicAgent()


# --- Hợp đồng chung -----------------------------------------------------------
def test_terminal_env_raises(agent):
    env = make_env([(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3), (0, 4)])
    assert env.is_terminal()
    with pytest.raises(RuntimeError):
        agent.choose_action(env)


def test_decision_shape_and_legality(agent):
    env = make_env(MIDGAME)
    decision = agent.choose_action(env)
    assert isinstance(decision, AgentDecision)
    assert isinstance(decision.action, tuple) and len(decision.action) == 2
    assert all(type(v) is int for v in decision.action)
    assert decision.action in env.legal_actions()
    assert decision.nodes == len(env.legal_actions())  # số candidate đã đánh giá
    assert decision.simulations == 0
    assert decision.elapsed_ms >= 0.0


def test_empty_board_prefers_center(agent):
    env = CaroEnv()
    assert agent.choose_action(env).action == (SIZE // 2, SIZE // 2)


# --- T07: nước thắng ngay -------------------------------------------------------
def test_t07_x_takes_immediate_win(agent):
    env = make_env(X_FOUR_OPEN)
    decision = agent.choose_action(env)
    assert decision.action in {(5, 3), (5, 8)}
    assert decision.score >= WIN_SCORE


def test_t07_o_takes_immediate_win(agent):
    env = make_env(O_FOUR_OPEN)
    assert env.state.current_player == Player.O
    decision = agent.choose_action(env)
    assert decision.action in {(5, 3), (5, 8)}
    assert decision.score >= WIN_SCORE


def test_t07_win_through_gap(agent):
    # X X _ X X: đặt vào ô giữa cũng là chuỗi 5.
    env = make_env([(5, 3), (0, 0), (5, 4), (0, 2), (5, 6), (0, 4), (5, 7), (10, 10)])
    assert agent.choose_action(env).action == (5, 5)


def test_t07_win_at_board_edge(agent):
    env = make_env(X_FOUR_AT_EDGE)
    assert agent.choose_action(env).action == (0, 4)


def test_t07_win_beats_block(agent):
    # Cả X và O đều có bốn; người đang đi (X) phải chọn thắng, không chặn.
    env = make_env(
        [(5, 3), (7, 3), (5, 4), (7, 4), (5, 5), (7, 5), (5, 6), (7, 6)]
    )
    assert env.state.current_player == Player.X
    action = agent.choose_action(env).action
    assert action in {(5, 2), (5, 7)}  # thắng, không phải (7,2)/(7,7)


# --- T08: chặn nước thắng của đối thủ ------------------------------------------
def test_t08_o_blocks_gap_four(agent):
    env = make_env(X_GAP_FOUR)
    assert env.state.current_player == Player.O
    decision = agent.choose_action(env)
    assert decision.action == (5, 5)
    assert decision.score >= BLOCK_SCORE


def test_t08_x_blocks_open_four_side(agent):
    # O có bốn mở hàng 5, X đến lượt và không thể thắng: X chặn một đầu.
    env = make_env(
        [(0, 0), (5, 4), (0, 2), (5, 5), (0, 4), (5, 6), (10, 10), (5, 7)]
    )
    assert env.state.current_player == Player.X
    assert agent.choose_action(env).action in {(5, 3), (5, 8)}


def test_t08_block_at_board_edge(agent):
    env = make_env(O_FOUR_AT_EDGE)
    assert env.state.current_player == Player.X
    assert agent.choose_action(env).action == (4, 0)


def test_t08_block_beats_own_threat(agent):
    # X có ba mở nhưng O đã có bốn: X phải chặn trước khi tấn công.
    env = make_env(
        [(5, 4), (8, 0), (5, 5), (8, 1), (5, 6), (8, 2), (0, 0), (8, 3)]
    )
    assert env.state.current_player == Player.X
    assert agent.choose_action(env).action in {(8, 4)}  # đầu trái (8,-1) ngoài bàn


# --- T09: tie-break deterministic -----------------------------------------------
def test_t09_tie_break_is_first_in_row_major(agent):
    # Một quân X ở giữa: O có nhiều ô điểm bằng nhau (đối xứng quanh tâm).
    env = make_env([(5, 5)])
    tied = best_priority_cells(env)
    assert len(tied) >= 2, "scenario phải có hòa điểm để test tie-break"
    assert agent.choose_action(env).action == tied[0]


@pytest.mark.parametrize(
    "actions", [[], [(5, 5)], MIDGAME, X_OPEN_THREE, X_GAP_FOUR, O_FOUR_AT_EDGE]
)
def test_t09_choice_is_first_best_and_reproducible(actions):
    env = make_env(actions)
    first = HeuristicAgent().choose_action(env)
    second = HeuristicAgent().choose_action(env)
    assert first.action == second.action == best_priority_cells(env)[0]
    assert first.score == second.score


def test_t09_equal_open_four_extensions_pick_lower_column(agent):
    # (5,3) và (5,7) cùng tạo open four, cách tâm bằng nhau => chọn (5,3).
    env = make_env(X_OPEN_THREE)
    assert agent.choose_action(env).action == (5, 3)


# --- T10: threat và center theo thứ tự công bố ----------------------------------
def test_t10_priority_tiers_are_ordered():
    env = make_env(X_FOUR_OPEN)
    board = env.state.board
    win = action_priority(board, (5, 3), Player.X, WIN)
    threat = action_priority(board, (4, 4), Player.X, WIN)
    center = action_priority(board, (10, 0), Player.X, WIN)
    assert win >= WIN_SCORE > BLOCK_SCORE > threat > center >= 0

    env = make_env(X_GAP_FOUR)  # O đi: ô (5,5) là block
    board = env.state.board
    block = action_priority(board, (5, 5), Player.O, WIN)
    other = action_priority(board, (5, 2), Player.O, WIN)
    assert BLOCK_SCORE <= block < WIN_SCORE
    assert other < BLOCK_SCORE


def test_t10_threat_beats_center(agent):
    # Có ba mở: mở rộng thành bốn mở tốt hơn đặt gần tâm.
    env = make_env(X_OPEN_THREE)
    assert agent.choose_action(env).action in {(5, 3), (5, 7)}


def test_t10_defends_open_four_over_center(agent):
    # X vừa mở rộng ba mở thành bốn mở; O chặn một đầu thay vì đặt ở tâm.
    env = make_env(X_OPEN_THREE)
    env.step((5, 3))
    assert env.state.current_player == Player.O
    assert agent.choose_action(env).action in {(5, 2), (5, 7)}


def test_center_bonus_range_and_monotonic():
    values = [center_bonus((r, c), SIZE) for r in range(SIZE) for c in range(SIZE)]
    assert all(0.0 <= v < 1.0 for v in values)
    assert center_bonus((5, 5), SIZE) == max(values)
    assert center_bonus((0, 0), SIZE) == min(values)
    assert center_bonus((5, 6), SIZE) > center_bonus((5, 9), SIZE)
    assert center_bonus((2, 3), SIZE) == center_bonus((8, 7), SIZE)  # đối xứng tâm


# --- Nhiều candidate + no-mutation -----------------------------------------------
def test_many_candidates_midgame_legal_and_no_win_available(agent):
    env = make_env(MIDGAME)
    decision = agent.choose_action(env)
    assert decision.action in env.legal_actions()
    assert decision.score < WIN_SCORE  # chưa có nước thắng ngay
    assert decision.nodes > 50


@pytest.mark.parametrize(
    "actions", [[], MIDGAME, X_FOUR_OPEN, X_GAP_FOUR, O_FOUR_AT_EDGE]
)
def test_no_mutation_of_env(agent, actions):
    env = make_env(actions)
    before_state = env.state
    before_render = env.render()
    before_legal = env.legal_actions()

    agent.choose_action(env)

    assert env.state == before_state
    assert env.render() == before_render
    assert env.legal_actions() == before_legal


def test_history_is_untouched(agent):
    env = make_env(MIDGAME)
    agent.choose_action(env)
    # Undo phải lùi đúng nước thật cuối cùng, chứng tỏ history không bị đụng.
    assert env.undo() == make_env(MIDGAME[:-1]).state