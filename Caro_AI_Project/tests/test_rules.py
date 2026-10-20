import pytest
from core.engine.interfaces import GameConfig, Player
from core.engine.rules import RuleEngine


def test_horizontal_win():
    # TC01: X thắng hàng ngang (5 quân liên tiếp)
    config = GameConfig(board_size=11, win_length=5)
    board = [[Player.EMPTY for _ in range(11)] for _ in range(11)]
    for c in range(5):
        board[0][c] = Player.X

    winner = RuleEngine.check_winner(board, config)
    assert winner == Player.X


def test_vertical_win_player_o():
    # TC02: O thắng cột dọc (5 quân liên tiếp)
    config = GameConfig(board_size=11, win_length=5)
    board = [[Player.EMPTY for _ in range(11)] for _ in range(11)]
    for r in range(5):
        board[r][0] = Player.O

    winner = RuleEngine.check_winner(board, config)
    assert winner == Player.O


def test_blocked_both_ends_no_win():
    # TC06: 5 quân X bị quân O chặn CẢ 2 ĐẦU -> Chưa thắng
    config = GameConfig(board_size=11, win_length=5)
    board = [[Player.EMPTY for _ in range(11)] for _ in range(11)]
    
    board[1][0] = Player.O
    for c in range(1, 6):
        board[1][c] = Player.X
    board[1][6] = Player.O

    assert RuleEngine.check_winner(board, config) is None


def test_blocked_by_o_and_edge():
    # TC07: 1 đầu sát biên (col=0) và 1 đầu bị O chặn (col=5) -> Bị chặn 2 đầu -> Chưa thắng
    config = GameConfig(board_size=11, win_length=5)
    board = [[Player.EMPTY for _ in range(11)] for _ in range(11)]
    
    for c in range(0, 5):
        board[0][c] = Player.X
    board[0][5] = Player.O

    assert RuleEngine.check_winner(board, config) is None


def test_one_end_blocked_win():
    # TC05: 5 quân X bị O chặn 1 đầu, đầu kia trống -> Vẫn THẮNG
    config = GameConfig(board_size=11, win_length=5)
    board = [[Player.EMPTY for _ in range(11)] for _ in range(11)]
    
    board[2][0] = Player.O
    for c in range(1, 6):
        board[2][c] = Player.X

    assert RuleEngine.check_winner(board, config) == Player.X


def test_is_terminal_draw():
    # TC14: Hòa khi bàn cờ đầy
    config = GameConfig(board_size=11, win_length=5)
    board = [[Player.X if (r + c) % 2 == 0 else Player.O for c in range(11)] for r in range(11)]
    
    done, winner = RuleEngine.is_terminal(board, config)
    assert done is True
    assert winner is None