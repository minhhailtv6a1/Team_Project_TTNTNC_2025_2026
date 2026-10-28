"""Streamlit integration tests for Hải's Week 2 UI tasks and caro-v2."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import GameEnv, Player


APP_PATH = Path(__file__).parents[1] / "ui" / "app.py"

X_WIN_MOVES = [
    (5, 1), (6, 1),
    (5, 2), (6, 2),
    (5, 3), (6, 3),
    (5, 4), (6, 4),
    (5, 5),
]

O_WIN_MOVES = [
    (0, 0), (5, 1),
    (0, 2), (5, 2),
    (0, 4), (5, 3),
    (2, 0), (5, 4),
    (2, 2), (5, 5),
]

NON_TERMINAL_MOVES = [
    (0, 0), (0, 1),
    (0, 2), (1, 0),
    (2, 0), (1, 2),
    (2, 2), (3, 0),
    (4, 0), (3, 2),
]


def _draw_moves() -> list[tuple[int, int]]:
    """Return a full 11x11 sequence that contains no winning line."""

    x_cells = [
        (row, col)
        for row in range(11)
        for col in range(11)
        if ((row + 2 * col) // 2) % 2 == 0
    ]
    o_cells = [
        (row, col)
        for row in range(11)
        for col in range(11)
        if ((row + 2 * col) // 2) % 2 == 1
    ]
    return [
        x_cells[index // 2] if index % 2 == 0 else o_cells[index // 2]
        for index in range(121)
    ]


DRAW_MOVES = _draw_moves()


def _run_app() -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    assert not app.exception
    return app


def _cell_buttons(app: AppTest, board_size: int = 11) -> list:
    prefix = f"cell_{board_size}_"
    return [button for button in app.button if (button.key or "").startswith(prefix)]


def _play(app: AppTest, actions: list[tuple[int, int]]) -> None:
    for row, col in actions:
        app.button(key=f"cell_11_{row}_{col}").click().run()
        assert not app.exception


def _page_contains(app: AppTest, text: str) -> bool:
    return any(text in element.value for element in app.markdown)


def test_app_uses_real_caro_env_and_renders_default_11x11_board() -> None:
    app = _run_app()
    env = app.session_state.env
    state = env.state

    assert isinstance(env, CaroEnv)
    assert isinstance(env, GameEnv)
    assert app.session_state.board_size == 11
    assert len(state.board) == 11
    assert all(len(row) == 11 for row in state.board)
    assert state.current_player == Player.X
    assert state.move_count == 0
    assert state.last_action is None
    assert len(env.legal_actions()) == 121
    assert app.selectbox(key="game_mode").value == "Human vs Human"
    assert app.selectbox(key="ai_algorithm").disabled is True
    assert app.selectbox(key="board_size").value == 11
    assert app.selectbox(key="board_size").disabled is True
    assert app.button(key="new_game_button")
    assert len(_cell_buttons(app)) == 121


def test_click_uses_tuple_action_and_occupied_error_is_atomic() -> None:
    app = _run_app()

    app.button(key="cell_11_5_5").click().run()
    assert not app.exception
    state_after_move = app.session_state.env.state
    history_after_move = list(app.session_state.move_history)

    assert state_after_move.board[5][5] == Player.X
    assert state_after_move.current_player == Player.O
    assert state_after_move.move_count == 1
    assert state_after_move.last_action == (5, 5)
    assert history_after_move == [
        {"number": 1, "player": Player.X, "action": (5, 5)}
    ]

    app.button(key="cell_11_5_5").click().run()

    assert not app.exception
    assert app.session_state.env.state == state_after_move
    assert app.session_state.move_history == history_after_move
    assert len(app.warning) == 1
    assert "already occupied" in app.warning[0].value


def test_new_game_resets_public_state_and_preserves_statistics() -> None:
    app = _run_app()
    env_before_reset = app.session_state.env
    app.session_state.stats["x_wins"] = 3
    app.button(key="cell_11_0_0").click().run()

    app.button(key="new_game_button").click().run()

    state = app.session_state.env.state
    assert not app.exception
    assert app.session_state.env is env_before_reset
    assert state.move_count == 0
    assert state.current_player == Player.X
    assert state.last_action is None
    assert state.terminated is False
    assert state.winner is None
    assert len(app.session_state.env.legal_actions()) == 121
    assert app.session_state.move_history == []
    assert app.session_state.stats["x_wins"] == 3


def test_board_size_selector_is_fixed_to_caro_v2_config() -> None:
    app = _run_app()
    state = app.session_state.env.state

    assert app.session_state.board_size == 11
    assert len(state.board) == 11
    assert len(app.session_state.env.legal_actions()) == 121
    assert len(_cell_buttons(app)) == 121
    assert app.selectbox(key="board_size").options == ["11×11"]
    assert app.selectbox(key="board_size").disabled is True


def test_moves_and_contract_metadata_survive_streamlit_rerun() -> None:
    app = _run_app()
    _play(app, NON_TERMINAL_MOVES)

    state_before_rerun = app.session_state.env.state
    history_before_rerun = list(app.session_state.move_history)
    app.run()

    assert not app.exception
    assert state_before_rerun.terminated is False
    assert state_before_rerun.move_count == 10
    assert state_before_rerun.last_action == NON_TERMINAL_MOVES[-1]
    assert app.session_state.env.state == state_before_rerun
    assert app.session_state.move_history == history_before_rerun


def test_changing_mode_resets_game_and_toggles_ai_control() -> None:
    app = _run_app()
    app.button(key="cell_11_5_5").click().run()

    app.selectbox(key="game_mode").set_value("Human vs AI").run()

    assert not app.exception
    assert app.session_state.env.state.move_count == 0
    assert app.session_state.move_history == []
    assert app.selectbox(key="ai_algorithm").disabled is False

    app.selectbox(key="game_mode").set_value("Human vs Human").run()

    assert not app.exception
    assert app.selectbox(key="ai_algorithm").disabled is True
    assert app.session_state.env.state.move_count == 0


def test_x_win_comes_from_engine_disables_board_and_play_again_resets() -> None:
    app = _run_app()
    _play(app, X_WIN_MOVES)

    state = app.session_state.env.state
    assert state.terminated is True
    assert state.winner == Player.X
    assert state.move_count == 9
    assert state.last_action == X_WIN_MOVES[-1]
    assert app.session_state.env.result(Player.X) == 1.0
    assert app.session_state.stats["x_wins"] == 1
    assert len(app.session_state.move_history) == 9
    assert _page_contains(app, "Player X wins!")
    assert app.button(key="play_again_button")
    assert all(button.disabled for button in _cell_buttons(app))

    app.button(key="play_again_button").click().run()

    reset_state = app.session_state.env.state
    assert not app.exception
    assert reset_state.terminated is False
    assert reset_state.current_player == Player.X
    assert reset_state.move_count == 0
    assert app.session_state.move_history == []
    assert app.session_state.stats["x_wins"] == 1
    assert all(not button.disabled for button in _cell_buttons(app))


def test_o_win_banner_and_history_match_engine_result() -> None:
    app = _run_app()
    _play(app, O_WIN_MOVES)

    state = app.session_state.env.state
    assert state.terminated is True
    assert state.winner == Player.O
    assert state.move_count == 10
    assert state.last_action == O_WIN_MOVES[-1]
    assert app.session_state.env.result(Player.O) == 1.0
    assert app.session_state.stats["o_wins"] == 1
    assert [move["action"] for move in app.session_state.move_history] == O_WIN_MOVES
    assert _page_contains(app, "Player O wins!")
    assert all(button.disabled for button in _cell_buttons(app))


def test_draw_banner_uses_engine_terminal_metadata() -> None:
    app = _run_app()
    env = app.session_state.env

    for action in DRAW_MOVES[:-1]:
        env.step(action)
    app.session_state.move_history = [
        {
            "number": index,
            "player": Player.X if index % 2 else Player.O,
            "action": action,
        }
        for index, action in enumerate(DRAW_MOVES[:-1], start=1)
    ]
    app.run()

    final_row, final_col = DRAW_MOVES[-1]
    app.button(key=f"cell_11_{final_row}_{final_col}").click().run()

    state = app.session_state.env.state
    assert not app.exception
    assert state.terminated is True
    assert state.winner is None
    assert state.move_count == 121
    assert app.session_state.env.result(Player.X) == 0.0
    assert app.session_state.stats["draws"] == 1
    assert len(app.session_state.move_history) == 121
    assert _page_contains(app, "draw!")
    assert all(button.disabled for button in _cell_buttons(app))
