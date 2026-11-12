import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import connect4_monte_carlo as mc


def winning_board(player=1):
    board = np.zeros((4, 4), dtype=int)
    board[-1, :3] = player
    return board


@pytest.mark.parametrize("player", [1, -1])
def test_playout_immediate_win_and_no_mutation(player):
    board = winning_board(player)
    before = board.copy()
    assert mc.playout(board, 3, player, np.random.default_rng(42)) == 1
    np.testing.assert_array_equal(board, before)


@pytest.mark.parametrize("budget", [1, 3, 10, 100])
def test_exact_even_budget_and_seed(budget, monkeypatch):
    calls = []
    def rollout(board, action, player, rng):
        calls.append(action)
        return int(rng.choice([-1, 0, 1]))
    monkeypatch.setattr(mc, "_rollout", rollout)
    board = np.zeros((4, 4), dtype=int)
    before = board.copy()
    first = mc.pmcs(board, n_playouts=budget, seed=17)
    assert len(calls) == budget == first["playouts"] == sum(first["visits"].values())
    assert max(first["visits"].values()) - min(first["visits"].values()) <= 1
    second = mc.pmcs(board, n_playouts=budget, seed=17)
    for key in ("move", "value", "visits", "action_values"):
        assert first[key] == second[key]
    assert first["move"] in mc.actions(board) and -1 <= first["value"] <= 1
    np.testing.assert_array_equal(board, before)


@pytest.mark.parametrize("player", [1, -1])
def test_pmcs_proven_win_over_equal_rollout_estimates(player, monkeypatch):
    monkeypatch.setattr(mc, "_rollout", lambda *args: 1)
    assert mc.pmcs(winning_board(player), player, n_playouts=1)["move"] == 3


def test_full_column_is_never_simulated():
    board = np.zeros((4, 4), dtype=int)
    board[:, 0] = [1, -1, 1, -1]
    found = mc.pmcs(board, n_playouts=10)
    assert 0 not in found["visits"] and found["move"] in (1, 2, 3)
    with pytest.raises(ValueError):
        mc.playout(board, 0)


def test_terminal_root_and_agent():
    board = winning_board()
    board[-1, 3] = 1
    found = mc.pmcs(board)
    assert found["move"] is None and found["value"] == 1 and found["playouts"] == 0
    with pytest.raises(ValueError):
        mc.PureMonteCarloAgent()(board)
    with pytest.raises(ValueError):
        mc.playout(board, 0)


@pytest.mark.parametrize("budget", [0, -1, 1.5, True])
def test_invalid_budget(budget):
    with pytest.raises(ValueError):
        mc.pmcs(np.zeros((4, 4)), n_playouts=budget)


def test_invalid_player_board_and_action():
    with pytest.raises(ValueError):
        mc.pmcs(np.zeros((4, 4)), player=0)
    with pytest.raises(ValueError):
        mc.pmcs(np.zeros(9))
    floating = np.zeros((4, 4), dtype=int)
    floating[0, 0] = 1
    with pytest.raises(ValueError):
        mc.pmcs(floating)
    with pytest.raises(ValueError):
        mc.playout(np.zeros((4, 4)), 99)


def test_real_playout_and_agents_use_local_rng():
    board = np.zeros((4, 4), dtype=int)
    assert mc.playout(board, 1, rng=np.random.default_rng(2)) in (-1, 0, 1)
    np.random.seed(123)
    expected = np.random.random(3)
    np.random.seed(123)
    a, b = mc.PureMonteCarloAgent(10, 8), mc.PureMonteCarloAgent(10, 8)
    assert [a(board) for _ in range(2)] == [b(board) for _ in range(2)]
    np.testing.assert_array_equal(np.random.random(3), expected)


@pytest.mark.skipif(importlib.util.find_spec("connect4_core") is None,
                    reason="Hai's connect4_core.py has not been supplied")
def test_official_core_backend():
    assert mc.RULES_BACKEND == "connect4_core"
    import connect4_core as core
    board = core.empty_board()
    assert mc.PureMonteCarloAgent(10)(board) in core.actions(board)
