# File: tests/test_invalid_actions.py
import pytest
from core.engine.interfaces import InvalidActionError, Player
from core.engine.game_env import CaroEnv

def test_out_of_bounds():
    env = CaroEnv()
    env.reset()

    size = env.config.board_size
    with pytest.raises(InvalidActionError):
        env.step((-1, 0))
        
    with pytest.raises(InvalidActionError):
        env.step((size,size))  

def test_occupied_cell_and_state_immutability():
    env = CaroEnv()
    env.reset()
    env.step((5, 5)) # X đánh
    
    original_player = env.state.current_player # Lượt của O
    
    with pytest.raises(InvalidActionError):
        env.step((5, 5)) # O cố tình đánh đè lên X
        
    # State không được đổi lượt hay đổi cờ sau khi ném lỗi
    assert env.state.current_player == original_player
    assert env.state.board[5][5] == Player.X