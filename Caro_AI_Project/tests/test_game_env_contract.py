# File: tests/test_game_env_contract.py
import pytest
from core.engine.interfaces import GameConfig, InvalidConfigError, Player, InvalidActionError
from core.engine.game_env import CaroEnv

def test_reset():
    env = CaroEnv(GameConfig(board_size=11))
    state = env.reset()
    assert len(state.board) == 11
    assert len(state.board[0]) == 11
    assert state.current_player == Player.X
    assert env.legal_actions() == [(r, c) for r in range(11) for c in range(11)]

def test_legal_actions_count():
    env = CaroEnv(GameConfig(board_size=11))
    env.reset()
    assert len(env.legal_actions()) == 121
    env.step((5, 5))
    assert len(env.legal_actions()) == 120

def test_clone_independence():
    env = CaroEnv()
    env.reset()
    clone_env = env.clone_env()
    
    clone_env.step((0, 0)) # Đánh trên env clone
    
    # Đảm bảo env gốc không bị ảnh hưởng
    assert env.state.board[0][0] == Player.EMPTY
    assert clone_env.state.board[0][0] == Player.X


def test_only_11x11_is_supported_in_the_current_scope():
    assert GameConfig().board_size == 11

    with pytest.raises(InvalidConfigError, match="board_size"):
        GameConfig(board_size=9)

    with pytest.raises(InvalidConfigError, match="board_size"):
        GameConfig(board_size=11.0)  # type: ignore[arg-type]
