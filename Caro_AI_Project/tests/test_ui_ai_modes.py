"""Week 7-8 tests for Hải's AI-backed Streamlit modes."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import GameConfig, Player, SearchBudget
from ui.app import (
    AI_ALGORITHMS,
    DEFAULT_CHECKPOINT,
    _build_dynamic_cell_css,
    _create_agent,
    _winning_cells,
)


APP_PATH = Path(__file__).parents[1] / "ui" / "app.py"
X_WIN_MOVES = [
    (5, 1), (6, 1),
    (5, 2), (6, 2),
    (5, 3), (6, 3),
    (5, 4), (6, 4),
    (5, 5),
]


def _run_app() -> AppTest:
    app = AppTest.from_file(str(APP_PATH), default_timeout=60).run()
    assert not app.exception
    return app


def _cell_buttons(app: AppTest) -> list:
    return [button for button in app.button if (button.key or "").startswith("cell_11_")]


def test_all_five_ui_agents_choose_legal_action_without_mutation() -> None:
    checkpoint = str(Path(__file__).parents[1] / DEFAULT_CHECKPOINT)

    for algorithm in AI_ALGORITHMS:
        env = CaroEnv(GameConfig())
        before = env.state
        agent = _create_agent(algorithm, checkpoint)
        decision = agent.choose_action(env, SearchBudget(seed=7))

        assert env.state == before
        assert decision.action in env.legal_actions()
        assert decision.elapsed_ms >= 0


def test_human_vs_ai_applies_exactly_one_ai_reply() -> None:
    app = _run_app()
    app.selectbox(key="game_mode").set_value("Human vs AI").run()
    app.selectbox(key="ai_algorithm").set_value("Random").run()

    app.button(key="cell_11_5_5").click().run()

    state = app.session_state.env.state
    assert not app.exception
    assert state.move_count == 2
    assert state.current_player == Player.X
    assert [move["player"] for move in app.session_state.move_history] == [
        Player.X,
        Player.O,
    ]
    assert app.session_state.move_history[0]["action"] == (5, 5)
    assert app.session_state.last_ai_decision["algorithm"] == "Random"
    assert all(not button.disabled for button in _cell_buttons(app))


def test_human_can_choose_o_and_ai_opens_as_x() -> None:
    app = _run_app()
    app.selectbox(key="game_mode").set_value("Human vs AI").run()
    app.selectbox(key="ai_algorithm").set_value("Random").run()
    app.selectbox(key="human_side").set_value("O").run()

    state = app.session_state.env.state
    assert not app.exception
    assert state.move_count == 1
    assert state.current_player == Player.O
    assert app.session_state.move_history[0]["player"] == Player.X
    assert all(not button.disabled for button in _cell_buttons(app))


def test_neural_checkpoint_error_is_clear_and_atomic_for_ai_turn() -> None:
    app = _run_app()
    app.selectbox(key="game_mode").set_value("Human vs AI").run()
    app.selectbox(key="ai_algorithm").set_value("Neural Network").run()
    app.text_input(key="checkpoint_path").set_value("missing-policy-checkpoint.pt").run()

    app.button(key="cell_11_5_5").click().run()

    state = app.session_state.env.state
    assert not app.exception
    assert state.move_count == 1
    assert state.current_player == Player.O
    assert state.board[5][5] == Player.X
    assert len(app.session_state.move_history) == 1
    assert "policy checkpoint not found" in app.warning[0].value
    assert all(button.disabled for button in _cell_buttons(app))


def test_terminal_win_highlights_the_complete_winning_line() -> None:
    env = CaroEnv(GameConfig())
    for action in X_WIN_MOVES:
        env.step(action)

    assert _winning_cells(env) == tuple((5, col) for col in range(1, 6))
    css = _build_dynamic_cell_css(env)
    for col in range(1, 6):
        assert f".st-key-cell_11_5_{col} button" in css
    assert css.count("background:#FFE3E3!important") == 5


def test_ai_vs_ai_finishes_one_game_and_reset_is_clean() -> None:
    app = _run_app()
    app.selectbox(key="game_mode").set_value("AI vs AI").run()
    app.selectbox(key="ai_x_algorithm").set_value("Random").run()
    app.selectbox(key="ai_o_algorithm").set_value("Random").run()

    assert all(button.disabled for button in _cell_buttons(app))
    app.button(key="ai_move_button").click().run()

    state = app.session_state.env.state
    assert not app.exception
    assert state.terminated is True
    assert app.session_state.auto_play is False
    assert state.move_count == len(app.session_state.move_history)
    assert {move["player"] for move in app.session_state.move_history} == {
        Player.X,
        Player.O,
    }
    assert app.button(key="ai_move_button").disabled is True
    assert sum(app.session_state.stats.values()) == 1

    app.button(key="new_game_button").click().run()

    reset_state = app.session_state.env.state
    assert reset_state.terminated is False
    assert reset_state.move_count == 0
    assert app.session_state.move_history == []
    assert sum(app.session_state.stats.values()) == 1

