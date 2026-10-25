import random

import pytest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import (
    GameEnv, InvalidActionError, InvalidActionReason, Player, UndoError,
)

N = 11


def play(env, actions):
    last = None
    for a in actions:
        last = env.step(a)
    return last


X_WIN = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3), (0, 4)]  # X thắng ở nước 9


def draw_sequence():
    xs = [(r, c) for r in range(N) for c in range(N) if (r // 2 + c) % 2 == 0]
    os_ = [(r, c) for r in range(N) for c in range(N) if (r // 2 + c) % 2 == 1]
    seq = []
    for i in range(61):
        seq.append(xs[i])
        if i < 60:
            seq.append(os_[i])
    return seq


def snap(env):
    return (env.state, env.legal_actions(), env.render(), env.is_terminal())


def random_prefix(env, rng, k):
    for _ in range(k):
        env.step(rng.choice(env.legal_actions()))


# undo: round-trip
@pytest.mark.parametrize("seed", range(10))
def test_step_then_undo_restores_exact_state(seed):
    """Property của contract mục 10."""
    rng = random.Random(seed)
    env = CaroEnv()
    random_prefix(env, rng, rng.randint(0, 40))
    before = env.state
    legal_before = env.legal_actions()
    result = env.step(rng.choice(legal_before))
    after_undo = env.undo()
    assert after_undo == before
    assert result.next_state.move_count == before.move_count + 1
    assert env.state == before and env.legal_actions() == legal_before


def test_n_steps_then_n_undos_returns_to_initial_and_every_intermediate_state():
    rng = random.Random(5)
    env = CaroEnv()
    states = [env.state]
    for _ in range(60):
        if env.is_terminal():
            break
        env.step(rng.choice(env.legal_actions()))
        states.append(env.state)
    for expected in reversed(states[:-1]):
        assert env.undo() == expected
    assert env.state == CaroEnv().state
    assert all(v == 0 for row in env.state.board for v in row)
    assert len(env.legal_actions()) == 121 and env.state.current_player == Player.X
    with pytest.raises(UndoError):
        env.undo()


def test_undo_restores_turn_and_legal_actions_order():
    env = CaroEnv()
    play(env, [(5, 5), (5, 6), (0, 0)])
    env.undo()
    assert env.state.current_player == Player.X and env.state.last_action == (5, 6)
    la = env.legal_actions()
    assert la == sorted(la) and (0, 0) in la and len(la) == 119
    env.step((0, 0))  # X đi lại đúng lượt
    assert env.state.board[0][0] == 1


def test_undo_restores_last_action_chain():
    env = CaroEnv()
    play(env, [(1, 1), (2, 2), (3, 3)])
    assert env.undo().last_action == (2, 2)
    assert env.undo().last_action == (1, 1)
    assert env.undo().last_action is None and env.state.move_count == 0


def test_undo_returns_defensive_snapshot():
    env = CaroEnv()
    play(env, [(1, 1), (2, 2)])
    s = env.undo()
    s.board[7][7] = 1
    assert env.state.board[7][7] == 0
    assert s is not env.state


# undo sau terminal
def test_undo_after_win_reopens_game():
    env = CaroEnv()
    play(env, X_WIN[:-1])
    before_win = snap(env)
    r = env.step(X_WIN[-1])
    assert r.done and env.is_terminal() and env.legal_actions() == []
    s = env.undo()
    assert snap(env) == before_win
    assert (s.terminated, s.winner, s.last_action, s.move_count, s.current_player) == (False, None, (1, 3), 8, Player.X)
    assert env.result(Player.X) is None and env.is_terminal() is False
    assert len(env.legal_actions()) == 121 - 8
    # chơi tiếp được: nước khác không thắng, rồi quay lại nước thắng
    r2 = env.step((10, 10))
    assert not r2.done and r2.reward == 0.0
    env.undo()
    r3 = env.step(X_WIN[-1])
    assert r3.done and r3.winner == Player.X and r3.reward == 1.0


def test_step_after_undo_of_win_is_accepted_and_after_win_rejected():
    env = CaroEnv()
    play(env, X_WIN)
    with pytest.raises(InvalidActionError) as ei:
        env.step((9, 9))
    assert ei.value.reason == InvalidActionReason.GAME_OVER
    env.undo()
    env.step((9, 9))  # không còn GAME_OVER


def test_undo_after_o_win():
    env = CaroEnv()
    play(env, [(5, 10), (0, 0), (6, 10), (0, 1), (7, 10), (0, 2), (8, 10), (0, 3), (5, 0), (0, 4)])
    assert env.result(Player.O) == 1.0
    s = env.undo()
    assert not s.terminated and s.winner is None and s.current_player == Player.O
    assert env.result(Player.O) is None


def test_undo_after_draw_reopens_game():
    env = CaroEnv()
    seq = draw_sequence()
    play(env, seq[:-1])
    before = snap(env)
    env.step(seq[-1])
    assert env.is_terminal() and env.result(Player.X) == 0.0
    s = env.undo()
    assert snap(env) == before
    assert not s.terminated and s.winner is None and s.move_count == 120
    assert env.legal_actions() == [seq[-1]]
    r = env.step(seq[-1])
    assert r.done and r.winner is None


# undo lỗi
def test_undo_on_fresh_env_raises_and_keeps_state():
    env = CaroEnv()
    before = snap(env)
    with pytest.raises(UndoError):
        env.undo()
    assert snap(env) == before
    env.step((0, 0))  # env vẫn dùng bình thường sau lỗi


def test_undo_error_message_is_clear():
    with pytest.raises(UndoError, match="(?i)nothing to undo"):
        CaroEnv().undo()


def test_undo_empty_after_reset():
    env = CaroEnv()
    play(env, [(0, 0), (1, 1)])
    env.reset()
    with pytest.raises(UndoError):
        env.undo()


def test_invalid_actions_do_not_touch_history():
    env = CaroEnv()
    play(env, [(2, 2), (3, 3)])
    for bad in [(2, 2), (-1, 0), (0, 11), "x", (1.5, 2)]:
        with pytest.raises(InvalidActionError):
            env.step(bad)
    assert len(env._history) == 2
    assert env.undo().last_action == (2, 2)  # undo vẫn hoàn tác đúng nước hợp lệ gần nhất
    assert env.undo().move_count == 0


def test_step_after_terminal_error_does_not_touch_history():
    env = CaroEnv()
    play(env, X_WIN)
    n = len(env._history)
    with pytest.raises(InvalidActionError):
        env.step((9, 9))
    assert len(env._history) == n


# undo/step đan xen (đối chiếu mô hình tham chiếu)
def test_random_step_undo_walk_matches_reference_model():
    rng = random.Random(77)
    env = CaroEnv()
    stack = [env.state]  # mô hình tham chiếu: chồng state đầy đủ
    for _ in range(600):
        if len(stack) > 1 and (env.is_terminal() or rng.random() < 0.3):
            stack.pop()
            assert env.undo() == stack[-1]
        else:
            env.step(rng.choice(env.legal_actions()))
            stack.append(env.state)
        assert env.state == stack[-1]
        assert env.legal_actions() == (
            [] if stack[-1].terminated
            else [(r, c) for r in range(N) for c in range(N) if stack[-1].board[r][c] == 0]
        )
        assert stack[-1].move_count == len(stack) - 1
    assert len(stack) > 5


# clone độc lập
def test_clone_copies_state_config_and_history():
    env = CaroEnv()
    play(env, [(5, 5), (5, 6), (6, 6)])
    clone = env.clone_env()
    assert clone is not env and clone.config == env.config
    assert clone.state == env.state and clone.legal_actions() == env.legal_actions()
    assert clone.render() == env.render()
    assert clone._history == env._history and clone._history is not env._history
    assert clone.state.board is not env.state.board


def test_clone_step_does_not_affect_original_and_vice_versa():
    env = CaroEnv()
    play(env, [(5, 5), (5, 6)])
    state_before_clone_move = env.state
    clone = env.clone_env()
    clone.step(clone.legal_actions()[0])
    assert env.state != clone.state
    assert env.state == state_before_clone_move  # property của contract mục 10
    env_hist = len(env._history)
    env.step((9, 9))
    assert clone.state.board[9][9] == 0 and len(clone._history) == env_hist + 1
    assert len(env._history) == env_hist + 1


def test_clone_undo_does_not_affect_original():
    env = CaroEnv()
    play(env, [(1, 1), (2, 2), (3, 3)])
    snapshot = snap(env)
    clone = env.clone_env()
    clone.undo()
    clone.undo()
    assert clone.state.move_count == 1
    assert snap(env) == snapshot and len(env._history) == 3
    assert env.undo().move_count == 2  # original vẫn undo đủ 3 nước


def test_original_undo_does_not_affect_clone():
    env = CaroEnv()
    play(env, [(1, 1), (2, 2)])
    clone = env.clone_env()
    snapshot = snap(clone)
    env.undo()
    env.undo()
    assert snap(clone) == snapshot and len(clone._history) == 2
    assert clone.undo().move_count == 1


def test_clone_reset_does_not_affect_original():
    env = CaroEnv()
    play(env, [(1, 1), (2, 2)])
    snapshot = snap(env)
    clone = env.clone_env()
    clone.reset()
    assert snap(env) == snapshot and len(env._history) == 2


def test_clone_of_terminal_env_is_terminal_and_undoable():
    env = CaroEnv()
    play(env, X_WIN)
    clone = env.clone_env()
    assert clone.is_terminal() and clone.legal_actions() == [] and clone.result(Player.X) == 1.0
    with pytest.raises(InvalidActionError):
        clone.step((9, 9))
    clone.undo()
    assert not clone.is_terminal() and env.is_terminal()  # chỉ clone mở lại


def test_clone_chain_is_independent():
    env = CaroEnv()
    play(env, [(0, 0)])
    c1 = env.clone_env()
    c1.step((1, 1))
    c2 = c1.clone_env()
    c2.step((2, 2))
    assert (env.state.move_count, c1.state.move_count, c2.state.move_count) == (1, 2, 3)
    c2.undo(); c2.undo(); c2.undo()
    assert c1.state.move_count == 2 and env.state.move_count == 1
    with pytest.raises(UndoError):
        c2.undo()


def test_clone_satisfies_game_env_protocol():
    assert isinstance(CaroEnv().clone_env(), GameEnv)


def test_rollouts_on_clones_never_change_original():
    """Mô phỏng kiểu MCTS/Minimax: chơi random + undo trên clone, env thật bất biến."""
    rng = random.Random(3)
    env = CaroEnv()
    random_prefix(env, rng, 15)
    snapshot = snap(env)
    hist = list(env._history)
    for _ in range(40):
        sim = env.clone_env()
        while not sim.is_terminal():
            sim.step(rng.choice(sim.legal_actions()))
        for _ in range(rng.randint(0, 10)):
            sim.undo()
        assert snap(env) == snapshot and env._history == hist


# reset xóa history
def test_reset_clears_history():
    env = CaroEnv()
    play(env, [(0, 0), (1, 1)])
    assert len(env._history) == 2
    env.reset()
    assert env._history == []


# bổ sung: độc lập cơ bản và không chia sẻ đối tượng mutable
def test_clone_is_independent_both_ways():
    env = CaroEnv()
    env.step((5, 5))
    before = env.state
    clone = env.clone_env()
    assert clone.state == env.state and clone.config == env.config
    clone.step(clone.legal_actions()[0])
    assert env.state == before and clone.state != env.state
    env.step((6, 6))
    assert clone.state.board[6][6] == 0


def test_clone_preserves_terminal_status():
    env = CaroEnv()
    play(env, X_WIN)
    clone = env.clone_env()
    assert clone.is_terminal() and clone.legal_actions() == [] and clone.result(Player.X) == 1.0
    with pytest.raises(InvalidActionError):
        clone.step((9, 9))


def test_clone_shares_no_mutable_objects():
    env = CaroEnv()
    play(env, [(1, 1), (2, 2)])
    clone = env.clone_env()
    assert clone._board is not env._board
    assert all(a is not b for a, b in zip(clone._board, env._board))  # từng hàng cũng độc lập
    assert clone._history is not env._history
    assert clone._config is env._config or clone._config == env._config  # config bất biến, được phép dùng chung


def test_undo_never_shares_board_with_returned_snapshot():
    env = CaroEnv()
    play(env, [(1, 1), (2, 2)])
    s = env.undo()
    assert s.board is not env._board and all(a is not b for a, b in zip(s.board, env._board))


def test_step_undo_step_gives_same_result_as_fresh_step():
    env = CaroEnv()
    play(env, [(4, 4), (4, 5)])
    r1 = env.step((5, 5))
    env.undo()
    r2 = env.step((5, 5))
    assert r1 == r2