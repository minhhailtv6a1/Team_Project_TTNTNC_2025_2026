"""Figma-aligned Streamlit UI for W1-M1-03.

Run from the project root with ``streamlit run ui/app.py``. The view talks
only to the ``caro-v1`` environment contract; week 1 uses ``MockGameEnv``.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.interfaces import GameConfig, InvalidActionError, Player, StepResult
from ui.mock_game_env import MockGameEnv


DEFAULT_BOARD_SIZE = 9
BOARD_SIZES = (9, 11)
GAME_MODES = ("Human vs AI", "Human vs Human", "AI vs AI")
AI_ALGORITHMS = (
    "Random",
    "Heuristic",
    "Minimax (Alpha-Beta)",
    "MCTS",
    "Neural Network",
)


def _new_stats() -> dict[str, int]:
    return {"x_wins": 0, "o_wins": 0, "draws": 0}


def _start_new_game(board_size: int | None = None) -> None:
    """Create a clean environment while keeping session statistics."""

    size = int(board_size or st.session_state.get("board_size", DEFAULT_BOARD_SIZE))
    current_env: MockGameEnv | None = st.session_state.get("env")
    if current_env is not None and current_env.config.board_size == size:
        current_env.reset()
        st.session_state.env = current_env
    else:
        st.session_state.env = MockGameEnv(GameConfig(board_size=size))
    st.session_state.move_history = []
    st.session_state.last_result = None
    st.session_state.error_message = None


def _initialize_session() -> None:
    if "board_size" not in st.session_state:
        st.session_state.board_size = DEFAULT_BOARD_SIZE
    if "stats" not in st.session_state:
        st.session_state.stats = _new_stats()
    if "move_history" not in st.session_state:
        st.session_state.move_history = []
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    if "env" not in st.session_state:
        _start_new_game(st.session_state.board_size)


def _record_result(result: StepResult) -> None:
    if not result.done:
        return
    if result.winner == Player.X:
        st.session_state.stats["x_wins"] += 1
    elif result.winner == Player.O:
        st.session_state.stats["o_wins"] += 1
    else:
        st.session_state.stats["draws"] += 1


def _play_move(row: int, col: int) -> None:
    """Execute one contract action and persist display-only metadata."""

    env: MockGameEnv = st.session_state.env
    player = env.state.current_player
    try:
        result = env.step((row, col))
    except InvalidActionError as exc:
        st.session_state.error_message = str(exc)
        return

    st.session_state.move_history.append(
        {
            "number": env.move_count,
            "player": player,
            "row": row,
            "col": col,
        }
    )
    st.session_state.last_result = result
    st.session_state.error_message = None
    _record_result(result)


def _player_name(player: Player) -> str:
    return "Player X" if player == Player.X else "Player O"


def _cell_label(value: int) -> str:
    if value == Player.X:
        return "X"
    if value == Player.O:
        return "O"
    return " "


def _build_dynamic_cell_css(env: MockGameEnv) -> str:
    """Style occupied and last-move cells from environment state."""

    board = env.board_array
    size = env.config.board_size
    rules: list[str] = []
    for row in range(size):
        for col in range(size):
            value = int(board[row, col])
            selector = f".st-key-cell_{size}_{row}_{col} button"
            if value == Player.X:
                rules.append(
                    f"{selector} {{color:#1E88E5!important;"
                    "background:#EAF4FE!important;font-weight:700!important;}"
                )
            elif value == Player.O:
                rules.append(
                    f"{selector} {{color:#E53935!important;"
                    "background:#FDEEEE!important;font-weight:700!important;}"
                )
            if env.last_action == (row, col):
                rules.append(
                    f"{selector} {{border:2px solid #FFA726!important;"
                    "box-shadow:none!important;}"
                )
    return "\n".join(rules)


def _inject_styles(env: MockGameEnv) -> None:
    size = env.config.board_size
    cell_size = 52 if size == 9 else 44
    board_width = cell_size * size + 2 * (size - 1)
    compact_cell_size = 44 if size == 9 else 36
    compact_board_width = compact_cell_size * size + 2 * (size - 1)
    dynamic_cell_css = _build_dynamic_cell_css(env)
    st.markdown(
        f"""
        <style>
        :root {{
            --caro-blue: #1E88E5;
            --caro-red: #E53935;
            --caro-orange: #FFA726;
            --caro-green: #43A047;
            --caro-warning: #FB8C00;
            --caro-error: #D32F2F;
            --caro-disabled: #BDBDBD;
            --caro-text: #242A31;
            --caro-muted: #7B8491;
            --caro-border: #E0E0E0;
            --caro-cell-size: {cell_size}px;
            --caro-board-width: {board_width}px;
        }}
        [data-testid="stHeader"], [data-testid="stToolbar"],
        #MainMenu, footer {{ display: none !important; }}
        html, body, [data-testid="stAppViewContainer"], .stApp {{
            background: #FFFFFF;
            color: var(--caro-text);
            font-family: Inter, "Segoe UI", Arial, sans-serif;
        }}
        .stMainBlockContainer {{ max-width: none; padding: 18px 24px 14px; }}

        [data-testid="stSidebar"] {{
            width: 300px !important;
            min-width: 300px !important;
            max-width: 300px !important;
            background: #F7F8FA;
            border-right: 1px solid #E6E8EC;
        }}
        [data-testid="stSidebar"] > div:first-child {{ padding: 28px 24px 18px; }}
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: #7B8491; }}
        [data-testid="stSidebar"] label p {{
            color: #39414C !important;
            font-size: 13px !important;
            font-weight: 500 !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            min-height: 40px;
            border-color: #DDE1E6;
            border-radius: 4px;
            background: #FFFFFF;
        }}
        .caro-brand {{
            color: #2D333B;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -.02em;
            line-height: 1.2;
        }}
        .caro-brand-subtitle {{ color: #7B8491; font-size: 12px; margin: 8px 0 18px; }}
        .caro-sidebar-rule {{ border-top: 1px solid #E6E8EC; margin: 6px 0 18px; }}
        .st-key-new_game_button button {{
            height: 40px;
            border: 1px solid #DDE1E6;
            border-radius: 4px;
            color: #343A43;
            background: #FFFFFF;
            font-weight: 600;
        }}
        .st-key-new_game_button button:hover {{ border-color: var(--caro-blue); color: var(--caro-blue); }}
        .caro-section-title {{ color: #343A43; font-size: 15px; font-weight: 700; margin-bottom: 12px; }}
        .caro-stat-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }}
        .caro-stat-label {{ color: #8A929E; font-size: 11px; margin-bottom: 4px; }}
        .caro-stat-value {{ font-size: 22px; font-weight: 600; line-height: 1; }}
        .caro-stat-x {{ color: var(--caro-blue); }}
        .caro-stat-o {{ color: var(--caro-red); }}
        .caro-stat-draw {{ color: #697386; }}
        .caro-session-label {{ color: #9AA1AB; font-size: 11px; margin: 14px 0; }}
        .caro-history {{
            border: 1px solid #E2E5E9;
            border-radius: 4px;
            background: #FFFFFF;
            overflow: hidden;
        }}
        .caro-history summary {{
            cursor: pointer;
            list-style: none;
            display: flex;
            justify-content: space-between;
            padding: 12px;
            color: #48515D;
            font-size: 12px;
            font-weight: 600;
        }}
        .caro-history summary::-webkit-details-marker {{ display: none; }}
        .caro-history-body {{
            min-height: 150px;
            max-height: 190px;
            overflow-y: auto;
            border-top: 1px solid #ECEEF1;
            padding: 12px;
            color: #7B8491;
            font: 12px/1.7 ui-monospace, SFMono-Regular, Consolas, monospace;
        }}
        .caro-sidebar-note {{ color: #9AA1AB; font-size: 10px; margin-top: 20px; }}

        .caro-meta {{
            display: flex;
            justify-content: space-between;
            color: #9AA1AB;
            font-size: 11px;
            line-height: 20px;
        }}
        .st-key-game_panel {{
            max-width: 590px;
            margin: 43px auto 0;
            gap: 0 !important;
        }}
        .caro-header h1 {{
            color: #242A31;
            font-size: 30px;
            font-weight: 750;
            letter-spacing: -.025em;
            line-height: 1.2;
            margin: 0;
        }}
        .caro-subtitle {{ color: #7B8491; font-size: 13px; margin-top: 8px; }}
        .caro-status {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            min-height: 58px;
            margin-top: 28px;
            border-bottom: 1px solid #E7E9EC;
            color: #3B424C;
            font-size: 14px;
            font-weight: 650;
        }}
        .caro-moves {{ color: #9299A3; font-size: 12px; font-weight: 400; }}
        .caro-dot {{
            display: inline-block;
            width: 10px;
            height: 10px;
            margin-right: 9px;
            border-radius: 50%;
            vertical-align: -1px;
        }}
        .caro-dot-x {{ background: var(--caro-blue); }}
        .caro-dot-o {{ background: var(--caro-red); }}
        .caro-dot-done {{ background: var(--caro-disabled); }}
        .st-key-game_panel [data-testid="stAlert"] {{
            margin-top: 14px;
            padding: 11px 14px;
            border: 0;
            border-radius: 4px;
            background: #FFF4E5;
            color: #7A5100;
            font-size: 13px;
        }}
        .st-key-board_stage {{
            width: var(--caro-board-width);
            max-width: 100%;
            margin: 48px auto 0;
            gap: 0 !important;
        }}
        .st-key-board_stage [data-testid="stHorizontalBlock"] {{
            flex-wrap: nowrap !important;
            gap: 2px !important;
        }}
        .st-key-board_stage [data-testid="stColumn"] {{
            flex: 1 1 0 !important;
            width: 0 !important;
            min-width: 0 !important;
        }}
        .st-key-board_stage [data-testid="stElementContainer"] {{ margin: 0 !important; }}
        .st-key-board_stage .stButton {{ margin: 0 0 2px !important; }}
        div[class*="st-key-cell_"] button {{
            width: 100%;
            height: var(--caro-cell-size);
            min-height: var(--caro-cell-size);
            padding: 0 !important;
            border: 1px solid var(--caro-border);
            border-radius: 4px;
            background: #FFFFFF;
            color: #343A43;
            font-size: 21px;
            line-height: 1;
            box-shadow: none;
        }}
        div[class*="st-key-cell_"] button:hover {{ border-color: #B8C0CA; background: #F7F8FA; }}
        div[class*="st-key-cell_"] button:disabled {{ opacity: .5; }}
        .caro-legend {{
            display: flex;
            justify-content: space-between;
            gap: 16px;
            width: var(--caro-board-width);
            max-width: 100%;
            margin: 8px auto 0;
            color: #9299A3;
            font-size: 11px;
        }}
        .caro-last-move {{ color: #8A6A34; }}
        .caro-last-box {{
            display: inline-block;
            width: 9px;
            height: 9px;
            margin-right: 5px;
            border: 2px solid var(--caro-orange);
            border-radius: 2px;
            vertical-align: -1px;
        }}
        .caro-hint {{ color: #9198A2; font-size: 11px; text-align: center; margin-top: 24px; }}
        .st-key-result_banner {{ margin-top: 18px; padding: 10px 12px; border-radius: 4px; background: #FFF4E5; }}
        .st-key-result_banner [data-testid="stHorizontalBlock"] {{ align-items: center; }}
        .caro-result-title {{ color: #333B45; font-size: 15px; font-weight: 700; }}
        .caro-result-copy {{ color: #7B8491; font-size: 11px; margin-top: 2px; }}
        .st-key-play_again_button button {{
            min-height: 36px;
            border-radius: 4px;
            border: 0;
            background: var(--caro-blue);
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 600;
        }}
        .caro-footer {{ color: #9AA1AB; font-size: 10px; text-align: center; margin-top: 70px; }}

        {dynamic_cell_css}

        /* Keep the complete board visible on common 1280x720 laptop screens. */
        @media (max-height: 820px) and (min-width: 769px) {{
            :root {{
                --caro-cell-size: {compact_cell_size}px;
                --caro-board-width: {compact_board_width}px;
            }}
            .stMainBlockContainer {{ padding-top: 10px; padding-bottom: 8px; }}
            [data-testid="stSidebar"] > div:first-child {{ padding: 14px 20px 10px; }}
            [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 8px; }}
            .caro-brand {{ font-size: 20px; }}
            .caro-brand-subtitle {{ margin: 4px 0 8px; }}
            .caro-sidebar-rule {{ margin: 4px 0 8px; }}
            .caro-session-label {{ margin: 8px 0; }}
            .caro-history-body {{ min-height: 104px; max-height: 130px; }}
            .caro-sidebar-note {{ margin-top: 10px; }}
            .st-key-game_panel {{ margin-top: 10px; }}
            .caro-header h1 {{ font-size: 25px; }}
            .caro-subtitle {{ font-size: 11px; margin-top: 3px; }}
            .caro-status {{ min-height: 40px; margin-top: 8px; }}
            .st-key-board_stage {{ margin-top: 12px; }}
            div[class*="st-key-cell_"] button {{ font-size: 18px; }}
            .caro-legend {{ margin-top: 5px; font-size: 10px; }}
            .caro-hint {{ margin-top: 10px; }}
            .caro-footer {{ margin-top: 10px; }}
        }}

        @media (max-width: 768px) {{
            [data-testid="stSidebar"] {{ width: min(300px, 86vw) !important; }}
            .stMainBlockContainer {{ padding: 16px 12px; }}
            .st-key-game_panel {{ margin-top: 28px; }}
            .st-key-board_stage {{ margin-top: 30px; }}
            .caro-header h1 {{ font-size: 27px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _history_html() -> str:
    history = st.session_state.move_history
    if not history:
        return '<span style="font-family:Inter,Segoe UI,sans-serif">No moves yet.<br>Your first move will appear here.</span>'
    return "<br>".join(
        f"{move['number']:>2}. {_player_name(move['player'])[-1]} → ({move['row']}, {move['col']})"
        for move in history
    )


def _render_sidebar() -> None:
    stats = st.session_state.stats
    with st.sidebar:
        st.markdown(
            '<div class="caro-brand">🎮 CARO AI</div>'
            '<div class="caro-brand-subtitle">A classic game. A smarter opponent.</div>'
            '<div class="caro-sidebar-rule"></div>',
            unsafe_allow_html=True,
        )
        st.selectbox("Game Mode", GAME_MODES, key="game_mode", on_change=_start_new_game)
        st.selectbox(
            "AI Algorithm",
            AI_ALGORITHMS,
            index=2,
            key="ai_algorithm",
            disabled=st.session_state.game_mode == "Human vs Human",
            help="AI execution is connected in later weekly tasks.",
        )
        st.selectbox(
            "Board Size",
            BOARD_SIZES,
            key="board_size",
            format_func=lambda value: f"{value}×{value}",
            on_change=_start_new_game,
        )
        st.button(
            "↻  New Game",
            key="new_game_button",
            use_container_width=True,
            on_click=_start_new_game,
        )
        st.markdown(
            f"""
            <div class="caro-sidebar-rule" style="margin-top:22px"></div>
            <div class="caro-section-title">⌁&nbsp; Statistics</div>
            <div class="caro-stat-grid">
              <div><div class="caro-stat-label">X wins</div><div class="caro-stat-value caro-stat-x">{stats['x_wins']}</div></div>
              <div><div class="caro-stat-label">O wins</div><div class="caro-stat-value caro-stat-o">{stats['o_wins']}</div></div>
              <div><div class="caro-stat-label">Draws</div><div class="caro-stat-value caro-stat-draw">{stats['draws']}</div></div>
            </div>
            <div class="caro-session-label">This session</div>
            <details class="caro-history" open>
              <summary><span>⌄ &nbsp;Move History</span><span>{len(st.session_state.move_history)}</span></summary>
              <div class="caro-history-body">{_history_html()}</div>
            </details>
            <div class="caro-sidebar-note">Coordinates use zero-based (row, col).</div>
            """,
            unsafe_allow_html=True,
        )


def _render_status(env: MockGameEnv) -> None:
    if env.is_terminal():
        dot_class, label = "caro-dot-done", "Game complete"
    else:
        current = env.state.current_player
        dot_class = "caro-dot-x" if current == Player.X else "caro-dot-o"
        label = f"{_player_name(current)}'s turn"

    st.markdown(
        f"""
        <div class="caro-status">
          <span><span class="caro-dot {dot_class}"></span>{html.escape(label)}</span>
          <span class="caro-moves">Moves: {env.move_count} / {env.config.board_size**2}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_board(env: MockGameEnv) -> None:
    state = env.state
    size = env.config.board_size
    with st.container(key="board_stage"):
        for row in range(size):
            columns = st.columns(size, gap=None)
            for col in range(size):
                columns[col].button(
                    _cell_label(int(state.board[row][col])),
                    key=f"cell_{size}_{row}_{col}",
                    use_container_width=True,
                    disabled=env.is_terminal(),
                    on_click=_play_move,
                    args=(row, col),
                    help=f"Row {row}, column {col}",
                )

    st.markdown(
        """
        <div class="caro-legend">
          <span><b style="color:#1E88E5">X · You</b>&nbsp;&nbsp;&nbsp;
                <b style="color:#E53935">O · Minimax</b></span>
          <span class="caro-last-move"><i class="caro-last-box"></i>Last move</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_result(env: MockGameEnv) -> None:
    if not env.is_terminal():
        return

    result: StepResult | None = st.session_state.last_result
    if result and result.winner == Player.X:
        title, copy = "🎉 Player X wins!", "Five in a row. Well played."
    elif result and result.winner == Player.O:
        title, copy = "🎉 Player O wins!", "Five in a row. Well played."
    else:
        title = "🤝 It's a draw!"
        copy = f"All {env.config.board_size**2} cells filled. Well played."

    with st.container(key="result_banner"):
        message_col, action_col = st.columns([4, 1])
        message_col.markdown(
            f'<div class="caro-result-title">{html.escape(title)}</div>'
            f'<div class="caro-result-copy">{html.escape(copy)}</div>',
            unsafe_allow_html=True,
        )
        action_col.button(
            "↻  Play Again",
            key="play_again_button",
            type="primary",
            use_container_width=True,
            on_click=_start_new_game,
        )


def main() -> None:
    st.set_page_config(
        page_title="Caro AI",
        page_icon="🎮",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _initialize_session()
    env: MockGameEnv = st.session_state.env
    _inject_styles(env)
    _render_sidebar()

    st.markdown(
        f'<div class="caro-meta"><span>Caro / {html.escape(st.session_state.game_mode)}</span>'
        f'<span>{env.config.board_size}×{env.config.board_size} board</span></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="game_panel"):
        st.markdown(
            '<div class="caro-header"><h1>Five in a row.</h1></div>'
            '<div class="caro-subtitle">You play X. Find your line before Minimax finds theirs.</div>',
            unsafe_allow_html=True,
        )
        _render_status(env)
        error_message = st.session_state.pop("error_message", None)
        if error_message:
            st.warning(f"⚠  {error_message}")
        _render_board(env)
        _render_result(env)
        if not env.is_terminal():
            hint = (
                "Choose any empty cell to make the first move."
                if env.move_count == 0
                else "Choose an empty cell to continue."
            )
            st.markdown(f'<div class="caro-hint">{hint}</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="caro-footer">Connect five horizontally, vertically or diagonally.</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
