"""Streamlit smoke tests for W1-M1-03."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.engine.interfaces import Player


APP_PATH = Path(__file__).parents[1] / "ui" / "app.py"


def _run_app() -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=10).run()
    assert not app.exception
    return app


def _cell_buttons(app: AppTest, board_size: int) -> list:
    prefix = f"cell_{board_size}_"
    return [button for button in app.button if (button.key or "").startswith(prefix)]


def test_app_renders_week_1_controls_and_default_board() -> None:
    app = _run_app()

    assert app.session_state.board_size == 11
    assert app.session_state.env.board_array.shape == (11, 11)
    assert app.session_state.env.state.current_player == Player.X
    assert len(app.session_state.env.legal_actions()) == 121
    assert app.selectbox(key="game_mode").value == "Human vs AI"
    assert app.selectbox(key="ai_algorithm").value == "Minimax (Alpha-Beta)"
    assert app.selectbox(key="board_size").value == 11
    assert app.selectbox(key="board_size").disabled is True
    assert app.button(key="new_game_button")
    assert len(_cell_buttons(app, 11)) == 121


def test_clicking_empty_then_occupied_cell_updates_and_reports_error() -> None:
    app = _run_app()

    app.button(key="cell_11_5_5").click().run()
    assert not app.exception
    assert app.session_state.env.state.board[5][5] == Player.X
    assert app.session_state.env.state.current_player == Player.O
    assert app.session_state.env.move_count == 1
    assert len(app.session_state.move_history) == 1

    app.button(key="cell_11_5_5").click().run()
    assert not app.exception
    assert app.session_state.env.state.board[5][5] == Player.X
    assert app.session_state.env.state.current_player == Player.O
    assert app.session_state.env.move_count == 1
    assert len(app.warning) == 1
    assert "already occupied" in app.warning[0].value


def test_new_game_resets_board_but_preserves_statistics() -> None:
    app = _run_app()
    env_before_reset = app.session_state.env
    app.session_state.stats["x_wins"] = 3
    app.button(key="cell_11_0_0").click().run()

    app.button(key="new_game_button").click().run()

    assert not app.exception
    assert app.session_state.env.move_count == 0
    assert app.session_state.env is env_before_reset
    assert len(app.session_state.env.legal_actions()) == 121
    assert app.session_state.move_history == []
    assert app.session_state.stats["x_wins"] == 3


def test_board_size_selector_is_fixed_to_the_active_11x11_module() -> None:
    app = _run_app()

    assert app.session_state.board_size == 11
    assert app.session_state.env.board_array.shape == (11, 11)
    assert len(app.session_state.env.legal_actions()) == 121
    assert len(_cell_buttons(app, 11)) == 121
    assert app.selectbox(key="board_size").options == ["11×11"]
    assert app.selectbox(key="board_size").disabled is True


def test_ten_consecutive_moves_survive_an_explicit_streamlit_rerun() -> None:
    app = _run_app()
    actions = [
        (4, 4),
        (4, 5),
        (3, 4),
        (3, 5),
        (5, 4),
        (5, 5),
        (2, 4),
        (2, 5),
        (6, 4),
        (6, 5),
    ]

    for row, col in actions:
        app.button(key=f"cell_11_{row}_{col}").click().run()
        assert not app.exception

    assert app.session_state.env.move_count == 10
    assert len(app.session_state.move_history) == 10
    assert app.session_state.env.state.current_player == Player.X
    for move_number, (row, col) in enumerate(actions):
        expected_player = Player.X if move_number % 2 == 0 else Player.O
        assert app.session_state.env.state.board[row][col] == expected_player

    board_before_rerun = app.session_state.env.state.board
    app.run()

    assert not app.exception
    assert app.session_state.env.move_count == 10
    assert app.session_state.env.state.board == board_before_rerun
    assert len(app.session_state.move_history) == 10


def test_changing_game_mode_resets_board_and_toggles_ai_control() -> None:
    app = _run_app()
    app.button(key="cell_11_5_5").click().run()

    app.selectbox(key="game_mode").set_value("Human vs Human").run()

    assert not app.exception
    assert app.session_state.env.move_count == 0
    assert app.session_state.move_history == []
    assert app.selectbox(key="ai_algorithm").disabled is True

    app.selectbox(key="game_mode").set_value("AI vs AI").run()

    assert not app.exception
    assert app.selectbox(key="ai_algorithm").disabled is False
    assert app.session_state.env.move_count == 0


def test_terminal_draw_disables_board_updates_stats_and_play_again_resets() -> None:
    app = _run_app()
    final_action = (10, 10)

    for row in range(11):
        for col in range(11):
            if (row, col) != final_action:
                app.session_state.env.step((row, col))
    app.run()

    app.button(key="cell_11_10_10").click().run()

    assert not app.exception
    assert app.session_state.env.is_terminal() is True
    assert app.session_state.env.move_count == 121
    assert app.session_state.stats["draws"] == 1
    assert app.button(key="play_again_button")
    assert all(button.disabled for button in _cell_buttons(app, 11))

    app.button(key="play_again_button").click().run()

    assert not app.exception
    assert app.session_state.env.is_terminal() is False
    assert app.session_state.env.move_count == 0
    assert len(app.session_state.env.legal_actions()) == 121
    assert app.session_state.stats["draws"] == 1
    assert len(_cell_buttons(app, 11)) == 121
    assert all(not button.disabled for button in _cell_buttons(app, 11))

