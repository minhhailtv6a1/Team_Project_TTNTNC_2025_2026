"""Streamlit UI backed by the real ``caro-v2`` game environment.

Run from the project root with ``streamlit run ui/app.py``.  This module only
uses public ``GameEnv`` data and delegates all game rules to ``CaroEnv``.
"""

from __future__ import annotations

import html
import sys
import time
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.engine.interfaces import (
    Agent,
    AgentDecision,
    DEFAULT_BOARD_SIZE,
    SUPPORTED_BOARD_SIZES,
    GameEnv,
    GameConfig,
    InvalidActionError,
    Player,
    SearchBudget,
    StepResult,
)
from core.engine.game_env import CaroEnv
from core.agents.heuristic_ai import HeuristicAgent
from core.agents.mcts_ai import MCTSAgent
from core.agents.minimax_ai import MinimaxAgent
from core.agents.neural_ai import NeuralAgent
from core.agents.random_ai import RandomAgent
from ui.human_controller import submit_human_action


# The selector intentionally exposes only the active 11x11 module. Adding a
# future board size only requires extending SUPPORTED_BOARD_SIZES centrally.
BOARD_SIZES = SUPPORTED_BOARD_SIZES
GAME_MODES = ("Human vs Human", "Human vs AI", "AI vs AI")
AI_ALGORITHMS = (
    "Random",
    "Heuristic",
    "Minimax (Alpha-Beta)",
    "MCTS",
    "Neural Network",
)
DEFAULT_CHECKPOINT = "models/checkpoints/model-v5-natural-teachers-run2/best.pt"
AI_MOVE_DELAY_SECONDS = 0.12


def _new_stats() -> dict[str, int]:
    return {"x_wins": 0, "o_wins": 0, "draws": 0}


def _start_new_game(board_size: int | None = None) -> None:
    """Reset the public environment while keeping session statistics."""

    size = int(board_size or st.session_state.get("board_size", DEFAULT_BOARD_SIZE))
    current_env: GameEnv | None = st.session_state.get("env")
    if current_env is not None and current_env.config.board_size == size:
        current_env.reset()
        st.session_state.env = current_env
    else:
        st.session_state.env = CaroEnv(GameConfig(board_size=size))
    st.session_state.move_history = []
    st.session_state.error_message = None
    st.session_state.ai_thinking = False
    st.session_state.auto_play = False
    st.session_state.last_ai_decision = None


def _initialize_session() -> None:
    if "board_size" not in st.session_state:
        st.session_state.board_size = DEFAULT_BOARD_SIZE
    if "stats" not in st.session_state:
        st.session_state.stats = _new_stats()
    if "move_history" not in st.session_state:
        st.session_state.move_history = []
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    if "ai_thinking" not in st.session_state:
        st.session_state.ai_thinking = False
    if "auto_play" not in st.session_state:
        st.session_state.auto_play = False
    if "last_ai_decision" not in st.session_state:
        st.session_state.last_ai_decision = None
    if "agent_cache" not in st.session_state:
        st.session_state.agent_cache = {}
    if "checkpoint_path" not in st.session_state:
        st.session_state.checkpoint_path = DEFAULT_CHECKPOINT
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


def _append_move(player: Player, action: tuple[int, int], result: StepResult) -> None:
    st.session_state.move_history.append(
        {
            "number": result.next_state.move_count,
            "player": player,
            "action": action,
        }
    )
    _record_result(result)


def _human_player() -> Player:
    return Player.X if st.session_state.get("human_side", "X") == "X" else Player.O


def _is_ai_turn(env: GameEnv | None = None) -> bool:
    env = env or st.session_state.env
    if env.state.terminated:
        return False
    mode = st.session_state.get("game_mode", GAME_MODES[0])
    if mode == "AI vs AI":
        return True
    if mode == "Human vs AI":
        return env.state.current_player != _human_player()
    return False


def _selected_ai(player: Player) -> str:
    if st.session_state.get("game_mode") == "AI vs AI":
        key = "ai_x_algorithm" if player == Player.X else "ai_o_algorithm"
        return st.session_state.get(key, AI_ALGORITHMS[0])
    return st.session_state.get("ai_algorithm", AI_ALGORITHMS[2])


def _checkpoint_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _create_agent(algorithm: str, checkpoint: str = DEFAULT_CHECKPOINT) -> Agent:
    """Build one UI agent using the frozen Week 7-8 settings."""

    if algorithm == "Random":
        return RandomAgent(seed=20261113)
    if algorithm == "Heuristic":
        return HeuristicAgent()
    if algorithm == "Minimax (Alpha-Beta)":
        return MinimaxAgent(default_depth=2, alpha_beta=True, move_ordering=True)
    if algorithm == "MCTS":
        return MCTSAgent(
            default_simulations=8,
            exploration_weight=0.7,
            seed=20261113,
            tactical_precheck=True,
            candidate_policy="heuristic_seeded",
            progressive_widening_c=1.5,
            rollout_policy="epsilon_heuristic",
            rollout_horizon=8,
            leaf_evaluation="pattern",
        )
    if algorithm == "Neural Network":
        return NeuralAgent(_checkpoint_path(checkpoint))
    raise ValueError(f"Unknown AI algorithm: {algorithm}")


def _get_agent(algorithm: str) -> Agent:
    checkpoint = st.session_state.get("checkpoint_path", DEFAULT_CHECKPOINT)
    cache_key = (algorithm, checkpoint if algorithm == "Neural Network" else None)
    cache = st.session_state.agent_cache
    if cache_key not in cache:
        cache[cache_key] = _create_agent(algorithm, checkpoint)
    return cache[cache_key]


def _apply_ai_decision(
    env: GameEnv,
    player: Player,
    algorithm: str,
    decision: AgentDecision,
) -> None:
    if decision.action not in env.legal_actions():
        raise RuntimeError(f"{algorithm} returned an illegal action: {decision.action}")
    result = env.step(decision.action)
    _append_move(player, decision.action, result)
    st.session_state.move_history[-1].update(
        {
            "algorithm": algorithm,
            "elapsed_ms": decision.elapsed_ms,
            "nodes": decision.nodes,
            "simulations": decision.simulations,
        }
    )
    if result.done:
        st.session_state.auto_play = False
    st.session_state.last_ai_decision = {
        "player": player,
        "algorithm": algorithm,
        "elapsed_ms": decision.elapsed_ms,
        "nodes": decision.nodes,
        "simulations": decision.simulations,
    }


def _play_ai_turn() -> bool:
    """Play exactly one AI move and leave the board unchanged on failure."""

    env: GameEnv = st.session_state.env
    if not _is_ai_turn(env) or st.session_state.ai_thinking:
        return False
    player = env.state.current_player
    algorithm = _selected_ai(player)
    st.session_state.ai_thinking = True
    try:
        agent = _get_agent(algorithm)
        decision = agent.choose_action(env, SearchBudget(seed=20261113 + env.state.move_count))
        _apply_ai_decision(env, player, algorithm, decision)
        st.session_state.error_message = None
        return True
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        st.session_state.error_message = f"{algorithm}: {exc}"
        st.session_state.auto_play = False
        return False
    finally:
        st.session_state.ai_thinking = False


def _start_ai_game() -> None:
    """Start step-by-step AI-vs-AI playback on successive reruns."""

    if not st.session_state.env.state.terminated:
        st.session_state.auto_play = True


def _play_move(row: int, col: int) -> None:
    """Submit one human action and, in Human-vs-AI, one AI reply."""

    env: GameEnv = st.session_state.env
    if _is_ai_turn(env):
        st.session_state.error_message = "Please wait for the AI turn to finish."
        return
    try:
        move = submit_human_action(env, (row, col))
    except InvalidActionError as exc:
        st.session_state.error_message = str(exc)
        return

    result = move.result
    _append_move(move.player, move.action, result)
    st.session_state.error_message = None
    if not result.done and st.session_state.get("game_mode") == "Human vs AI":
        _play_ai_turn()


def _player_name(player: Player) -> str:
    return "Player X" if player == Player.X else "Player O"


def _cell_label(value: int) -> str:
    if value == Player.X:
        return "X"
    if value == Player.O:
        return "O"
    return " "


def _winning_cells(env: GameEnv) -> tuple[tuple[int, int], ...]:
    """Return every winning line through the terminal state's last action."""

    state = env.state
    if not state.terminated or state.winner is None or state.last_action is None:
        return ()

    board = state.board
    size = env.config.board_size
    winner = int(state.winner)
    start_row, start_col = state.last_action
    winning: set[tuple[int, int]] = set()
    for row_step, col_step in ((0, 1), (1, 0), (1, 1), (1, -1)):
        line = [(start_row, start_col)]
        for direction in (-1, 1):
            row = start_row + direction * row_step
            col = start_col + direction * col_step
            while 0 <= row < size and 0 <= col < size and int(board[row][col]) == winner:
                line.append((row, col))
                row += direction * row_step
                col += direction * col_step
        if len(line) >= env.config.win_length:
            winning.update(line)
    return tuple(sorted(winning))


def _build_dynamic_cell_css(env: GameEnv) -> str:
    """Style occupied, last-move and winning cells from environment state."""

    state = env.state
    board = state.board
    size = env.config.board_size
    winning = set(_winning_cells(env))
    rules: list[str] = []
    for row in range(size):
        for col in range(size):
            value = int(board[row][col])
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
            if state.last_action == (row, col):
                rules.append(
                    f"{selector} {{border:2px solid #FFA726!important;"
                    "box-shadow:none!important;}"
                )
            if (row, col) in winning:
                rules.append(
                    f"{selector} {{color:#B71C1C!important;"
                    "background:#FFE3E3!important;border:3px solid #E53935!important;"
                    "box-shadow:0 0 0 2px rgba(229,57,53,.18)!important;}"
                )
    return "\n".join(rules)


def _inject_styles(env: GameEnv) -> None:
    size = env.config.board_size
    cell_size = max(30, min(44, 484 // size))
    board_width = cell_size * size + 2 * (size - 1)
    compact_cell_size = max(26, min(36, 396 // size))
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
        #MainMenu, footer {{ display: none !important; }}
        [data-testid="stHeader"] {{
            display: flex !important;
            background: transparent !important;
            pointer-events: none !important;
        }}
        [data-testid="stToolbar"] {{
            display: flex !important;
            background: transparent !important;
            pointer-events: none !important;
        }}
        [data-testid="stToolbar"] > div > *:not(:has([data-testid="stExpandSidebarButton"])) {{
            display: none !important;
        }}
        [data-testid="stExpandSidebarButton"] {{
            position: fixed !important;
            top: 12px !important;
            left: 12px !important;
            z-index: 1000000 !important;
            display: flex !important;
            width: 38px !important;
            height: 38px !important;
            align-items: center !important;
            justify-content: center !important;
            border: 1px solid #DDE1E6 !important;
            border-radius: 8px !important;
            background: #FFFFFF !important;
            box-shadow: 0 2px 8px rgba(36, 42, 49, .12) !important;
            pointer-events: auto !important;
        }}
        [data-testid="stExpandSidebarButton"]:hover {{
            border-color: var(--caro-blue) !important;
            color: var(--caro-blue) !important;
        }}
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
        .st-key-result_banner, .st-key-win_result_banner {{
            margin-top: 18px; padding: 10px 12px; border-radius: 4px; background: #FFF4E5;
        }}
        .st-key-win_result_banner {{
            border-left: 4px solid var(--caro-red);
            background: #FDEEEE;
        }}
        .st-key-result_banner [data-testid="stHorizontalBlock"],
        .st-key-win_result_banner [data-testid="stHorizontalBlock"] {{ align-items: center; }}
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
    lines: list[str] = []
    for move in history:
        line = (
            f"{move['number']:>2}. {_player_name(move['player'])[-1]} → "
            f"({move['action'][0]}, {move['action'][1]})"
        )
        if "algorithm" in move:
            line += (
                f" · {html.escape(str(move['algorithm']))}"
                f" · {float(move['elapsed_ms']):.1f} ms"
            )
            if move["nodes"]:
                line += f" · {move['nodes']} nodes"
            if move["simulations"]:
                line += f" · {move['simulations']} sims"
        lines.append(line)
    return "<br>".join(lines)


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
            disabled=st.session_state.game_mode != "Human vs AI",
            on_change=_start_new_game,
            help="AI level used in Human vs AI mode.",
        )
        if st.session_state.game_mode == "Human vs AI":
            st.selectbox(
                "Human Side",
                ("X", "O"),
                key="human_side",
                on_change=_start_new_game,
                help="X always moves first.",
            )
        elif st.session_state.game_mode == "AI vs AI":
            st.selectbox(
                "Player X AI",
                AI_ALGORITHMS,
                key="ai_x_algorithm",
                on_change=_start_new_game,
            )
            st.selectbox(
                "Player O AI",
                AI_ALGORITHMS,
                index=1,
                key="ai_o_algorithm",
                on_change=_start_new_game,
            )

        selected_algorithms = {
            st.session_state.get("ai_algorithm"),
            st.session_state.get("ai_x_algorithm"),
            st.session_state.get("ai_o_algorithm"),
        }
        if (
            st.session_state.game_mode != "Human vs Human"
            and "Neural Network" in selected_algorithms
        ):
            st.text_input(
                "Neural Checkpoint",
                key="checkpoint_path",
                on_change=_start_new_game,
                help="Absolute path or path relative to the project root.",
            )
        st.selectbox(
            "Board Size",
            BOARD_SIZES,
            key="board_size",
            format_func=lambda value: f"{value}×{value}",
            on_change=_start_new_game,
            disabled=len(BOARD_SIZES) == 1,
            help="11×11 is the active module; other sizes are deferred.",
        )
        st.button(
            "↻  New Game",
            key="new_game_button",
            use_container_width=True,
            on_click=_start_new_game,
        )
        if st.session_state.game_mode == "AI vs AI":
            st.button(
                "▶  Run AI Game",
                key="ai_move_button",
                use_container_width=True,
                disabled=(
                    st.session_state.env.state.terminated
                    or st.session_state.auto_play
                ),
                on_click=_start_ai_game,
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


def _render_status(env: GameEnv) -> None:
    state = env.state
    if state.terminated:
        dot_class, label = "caro-dot-done", "Game complete"
    else:
        current = state.current_player
        dot_class = "caro-dot-x" if current == Player.X else "caro-dot-o"
        label = f"{_player_name(current)}'s turn"

    st.markdown(
        f"""
        <div class="caro-status">
          <span><span class="caro-dot {dot_class}"></span>{html.escape(label)}</span>
          <span class="caro-moves">Moves: {state.move_count} / {env.config.board_size**2}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    decision = st.session_state.get("last_ai_decision")
    if decision:
        details = [f"{decision['elapsed_ms']:.1f} ms"]
        if decision["nodes"]:
            details.append(f"{decision['nodes']} nodes")
        if decision["simulations"]:
            details.append(f"{decision['simulations']} simulations")
        st.caption(
            f"Last AI move: {decision['algorithm']} ({_player_name(decision['player'])}) · "
            + " · ".join(details)
        )


def _render_board(env: GameEnv) -> None:
    state = env.state
    size = env.config.board_size
    board_locked = state.terminated or _is_ai_turn(env) or st.session_state.ai_thinking
    with st.container(key="board_stage"):
        for row in range(size):
            columns = st.columns(size, gap=None)
            for col in range(size):
                columns[col].button(
                    _cell_label(int(state.board[row][col])),
                    key=f"cell_{size}_{row}_{col}",
                    use_container_width=True,
                    disabled=board_locked,
                    on_click=_play_move,
                    args=(row, col),
                )

    st.markdown(
        """
        <div class="caro-legend">
          <span><b style="color:#1E88E5">X · Player 1</b>&nbsp;&nbsp;&nbsp;
                <b style="color:#E53935">O · Player 2</b></span>
          <span class="caro-last-move"><i class="caro-last-box"></i>Last move</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_result(env: GameEnv) -> None:
    state = env.state
    if not state.terminated:
        return

    if state.winner == Player.X:
        title, copy = "🎉 Player X wins!", "Five in a row. Well played."
    elif state.winner == Player.O:
        title, copy = "🎉 Player O wins!", "Five in a row. Well played."
    else:
        title = "🤝 It's a draw!"
        copy = f"All {env.config.board_size**2} cells filled. Well played."

    banner_key = "win_result_banner" if state.winner is not None else "result_banner"
    with st.container(key=banner_key):
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
    env: GameEnv = st.session_state.env
    _inject_styles(env)
    _render_sidebar()
    if (
        st.session_state.game_mode == "Human vs AI"
        and env.state.move_count == 0
        and _is_ai_turn(env)
    ):
        _play_ai_turn()

    st.markdown(
        f'<div class="caro-meta"><span>Caro / {html.escape(st.session_state.game_mode)}</span>'
        f'<span>{env.config.board_size}×{env.config.board_size} board</span></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="game_panel"):
        st.markdown(
            '<div class="caro-header"><h1>Five in a row.</h1></div>'
            '<div class="caro-subtitle">Player X starts. Take turns and connect five to win.</div>',
            unsafe_allow_html=True,
        )
        _render_status(env)
        error_message = st.session_state.pop("error_message", None)
        if error_message:
            st.warning(f"⚠  {error_message}")
        _render_board(env)
        _render_result(env)
        state = env.state
        if not state.terminated:
            if st.session_state.auto_play:
                hint = "AI game is running step by step."
            elif _is_ai_turn(env):
                hint = "The board is locked during the AI turn."
            else:
                hint = (
                    "Choose any empty cell to make the first move."
                    if state.move_count == 0
                    else "Choose an empty cell to continue."
                )
            st.markdown(f'<div class="caro-hint">{hint}</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="caro-footer">Connect five horizontally, vertically or diagonally.</div>',
        unsafe_allow_html=True,
    )
    if (
        st.session_state.auto_play
        and st.session_state.game_mode == "AI vs AI"
        and not env.state.terminated
    ):
        time.sleep(AI_MOVE_DELAY_SECONDS)
        if _play_ai_turn():
            st.rerun()


if __name__ == "__main__":
    main()
