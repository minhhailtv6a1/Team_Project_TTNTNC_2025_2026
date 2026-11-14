# -*- coding: utf-8 -*-
"""
Generate `architecture.excalidraw` containing:
1. Left Panel: Layered System Architecture Diagram (modeled after Section 3.3.1 figure, keeping English technical terms).
2. Right Panel: Project Mind Map radiating from the central `CARO AI SYSTEM (11×11 · caro-v2)` hub.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT_DIR / "architecture.excalidraw"


class ExcalidrawBuilder:
    def __init__(self) -> None:
        self.elements: list[dict] = []
        self._seed = 1000

    def _next_seed(self) -> int:
        self._seed += 7
        return self._seed

    def rect(
        self,
        el_id: str,
        x: float,
        y: float,
        w: float,
        h: float,
        stroke: str = "#1e293b",
        bg: str = "#f8fafc",
        stroke_width: int = 2,
        stroke_style: str = "solid",
        opacity: int = 100,
        roundness: bool = True,
        group: str | None = None,
    ) -> dict:
        el = {
            "id": el_id,
            "type": "rectangle",
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "angle": 0,
            "strokeColor": stroke,
            "backgroundColor": bg,
            "fillStyle": "solid",
            "strokeWidth": stroke_width,
            "strokeStyle": stroke_style,
            "roughness": 0,
            "opacity": opacity,
            "groupIds": [group] if group else [],
            "frameId": None,
            "roundness": {"type": 3} if roundness else None,
            "seed": self._next_seed(),
            "version": 1,
            "versionNonce": self._next_seed(),
            "isDeleted": False,
            "boundElements": [],
            "updated": 1792720000000,
            "link": None,
            "locked": False,
        }
        self.elements.append(el)
        return el

    def ellipse(
        self,
        el_id: str,
        x: float,
        y: float,
        w: float,
        h: float,
        stroke: str = "#1e293b",
        bg: str = "#f8fafc",
        stroke_width: int = 2,
        group: str | None = None,
    ) -> dict:
        el = {
            "id": el_id,
            "type": "ellipse",
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "angle": 0,
            "strokeColor": stroke,
            "backgroundColor": bg,
            "fillStyle": "solid",
            "strokeWidth": stroke_width,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "groupIds": [group] if group else [],
            "frameId": None,
            "roundness": {"type": 2},
            "seed": self._next_seed(),
            "version": 1,
            "versionNonce": self._next_seed(),
            "isDeleted": False,
            "boundElements": [],
            "updated": 1792720000000,
            "link": None,
            "locked": False,
        }
        self.elements.append(el)
        return el

    def text(
        self,
        el_id: str,
        x: float,
        y: float,
        text_str: str,
        font_size: int = 16,
        color: str = "#0f172a",
        align: str = "center",
        w: float | None = None,
        font_family: int = 2,
        group: str | None = None,
    ) -> dict:
        lines = text_str.split("\n")
        max_chars = max(len(line) for line in lines) if lines else 1
        est_w = w if w is not None else max(40.0, max_chars * font_size * 0.56)
        est_h = len(lines) * font_size * 1.28
        el = {
            "id": el_id,
            "type": "text",
            "x": x,
            "y": y,
            "width": est_w,
            "height": est_h,
            "angle": 0,
            "strokeColor": color,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 1,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "groupIds": [group] if group else [],
            "frameId": None,
            "roundness": None,
            "seed": self._next_seed(),
            "version": 1,
            "versionNonce": self._next_seed(),
            "isDeleted": False,
            "boundElements": [],
            "updated": 1792720000000,
            "link": None,
            "locked": False,
            "fontSize": font_size,
            "fontFamily": font_family,
            "text": text_str,
            "originalText": text_str,
            "textAlign": align,
            "verticalAlign": "top",
            "containerId": None,
            "autoResize": True,
            "lineHeight": 1.25,
        }
        self.elements.append(el)
        return el

    def card(
        self,
        card_id: str,
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        body: str,
        stroke: str,
        bg: str,
        header_bg: str | None = None,
        title_color: str = "#0f172a",
        body_color: str = "#334155",
        title_size: int = 16,
        body_size: int = 13,
    ) -> None:
        grp = f"grp_{card_id}"
        self.rect(f"{card_id}_box", x, y, w, h, stroke=stroke, bg=bg, stroke_width=2, group=grp)
        if header_bg:
            self.rect(
                f"{card_id}_hdr",
                x + 4,
                y + 4,
                w - 8,
                34,
                stroke="transparent",
                bg=header_bg,
                stroke_width=1,
                group=grp,
            )
            self.text(
                f"{card_id}_title",
                x + 12,
                y + 10,
                title,
                font_size=title_size,
                color=title_color,
                align="center",
                w=w - 24,
                group=grp,
            )
            self.text(
                f"{card_id}_body",
                x + 12,
                y + 46,
                body,
                font_size=body_size,
                color=body_color,
                align="center",
                w=w - 24,
                group=grp,
            )
        else:
            self.text(
                f"{card_id}_title",
                x + 10,
                y + 12,
                title,
                font_size=title_size,
                color=title_color,
                align="center",
                w=w - 20,
                group=grp,
            )
            self.text(
                f"{card_id}_body",
                x + 10,
                y + 38,
                body,
                font_size=body_size,
                color=body_color,
                align="center",
                w=w - 20,
                group=grp,
            )

    def arrow(
        self,
        el_id: str,
        points: list[tuple[float, float]],
        stroke: str = "#475569",
        stroke_width: int = 2,
        stroke_style: str = "solid",
        start_arrow: str | None = None,
        end_arrow: str | None = "arrow",
        roundness: bool = True,
    ) -> dict:
        x0, y0 = points[0]
        rel_pts = [[px - x0, py - y0] for px, py in points]
        xs = [p[0] for p in rel_pts]
        ys = [p[1] for p in rel_pts]
        w = max(xs) - min(xs)
        h = max(ys) - min(ys)
        el = {
            "id": el_id,
            "type": "arrow",
            "x": x0,
            "y": y0,
            "width": w,
            "height": h,
            "angle": 0,
            "strokeColor": stroke,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": stroke_width,
            "strokeStyle": stroke_style,
            "roughness": 0,
            "opacity": 100,
            "groupIds": [],
            "frameId": None,
            "roundness": {"type": 2} if roundness else None,
            "seed": self._next_seed(),
            "version": 1,
            "versionNonce": self._next_seed(),
            "isDeleted": False,
            "boundElements": [],
            "updated": 1792720000000,
            "link": None,
            "locked": False,
            "points": rel_pts,
            "lastCommittedPoint": None,
            "startBinding": None,
            "endBinding": None,
            "startArrowhead": start_arrow,
            "endArrowhead": end_arrow,
        }
        self.elements.append(el)
        return el

    def build_layered_architecture(self) -> None:
        """Left Panel (x: 40..1540): 5-Layer System Architecture Diagram."""
        # Outer backdrop
        self.rect(
            "arch_backdrop",
            20,
            20,
            1540,
            1220,
            stroke="#cbd5e1",
            bg="#f8fafc",
            stroke_width=2,
        )
        # Main header
        self.text(
            "arch_title",
            40,
            40,
            "CARO AI (GOMOKU 11×11) · LAYERED SYSTEM ARCHITECTURE",
            font_size=30,
            color="#0f172a",
            align="center",
            w=1500,
        )
        self.text(
            "arch_subtitle",
            40,
            82,
            "Component-Based Layered Architecture  ·  Single Source of Truth Engine  ·  Strict Contract Boundary (caro-v2)",
            font_size=16,
            color="#475569",
            align="center",
            w=1500,
        )

        # =====================================================================
        # LAYER 1: PRESENTATION & INTERACTION LAYER (Sky Blue Theme)
        # =====================================================================
        ly1_y = 130
        ly1_h = 175
        self.rect(
            "layer1_container",
            50,
            ly1_y,
            1440,
            ly1_h,
            stroke="#0284c7",
            bg="#e0f2fe",
            stroke_width=2,
        )
        # Left Layer Badge
        self.card(
            "layer1_badge",
            70,
            ly1_y + 22,
            270,
            130,
            "LAYER 1 · PRESENTATION",
            "Interaction & UI Boundary\n• Streamlit Web App\n• Thin Event Controller\n• Zero Rule Duplication",
            stroke="#0369a1",
            bg="#bae6fd",
            header_bg="#0284c7",
            title_color="#ffffff",
            body_color="#0c4a6e",
            title_size=15,
            body_size=13,
        )
        # Layer 1 Component Cards
        self.card(
            "l1_app",
            365,
            ly1_y + 22,
            350,
            130,
            "ui/app.py (Streamlit App)",
            "• 11×11 Interactive Board & Sidebar\n• Modes: HvH, HvAI (X/O), AIvAI Auto-Play\n• Dynamic CSS & Winning Line Highlight\n• st.session_state & Agent Cache",
            stroke="#0284c7",
            bg="#ffffff",
            header_bg="#e0f2fe",
            title_color="#0369a1",
        )
        self.card(
            "l1_ctrl",
            740,
            ly1_y + 22,
            350,
            130,
            "ui/human_controller.py",
            "• submit_human_action(env, action)\n• Converts UI Click → Action Tuple (r, c)\n• Returns Immutable HumanMove\n• Atomic InvalidActionError Guard",
            stroke="#0284c7",
            bg="#ffffff",
            header_bg="#e0f2fe",
            title_color="#0369a1",
        )
        self.card(
            "l1_cli",
            1115,
            ly1_y + 22,
            350,
            130,
            "scripts/ (CLI Entrypoints)",
            "• run_tournament_w78.py (Round-Robin)\n• generate_selfplay.py & build_dataset.py\n• train_policy.py (Colab / Local CLI)\n• analyze_results_w78.py (Tables/Plots)",
            stroke="#0284c7",
            bg="#ffffff",
            header_bg="#e0f2fe",
            title_color="#0369a1",
        )

        # =====================================================================
        # LAYER 2: AI AGENTS LAYER (Purple / Violet Theme)
        # =====================================================================
        ly2_y = 345
        ly2_h = 230
        self.rect(
            "layer2_container",
            50,
            ly2_y,
            1440,
            ly2_h,
            stroke="#7c3aed",
            bg="#f3e8ff",
            stroke_width=2,
        )
        # Left Layer Badge
        self.card(
            "layer2_badge",
            70,
            ly2_y + 25,
            270,
            180,
            "LAYER 2 · AI AGENTS",
            "Search & Learned Agents\n(core/agents/ & core/ml/)\n\n• Read-Only on Real Env\n• Search on clone_env()\n• Local Seeded RNG\n• Respects SearchBudget",
            stroke="#6d28d9",
            bg="#e9d5ff",
            header_bg="#7c3aed",
            title_color="#ffffff",
            body_color="#4c1d95",
            title_size=15,
            body_size=13,
        )
        # Unified Agent Protocol Banner inside Layer 2
        self.rect(
            "l2_protocol_bar",
            365,
            ly2_y + 16,
            1100,
            36,
            stroke="#6d28d9",
            bg="#ddd6fe",
            stroke_width=2,
        )
        self.text(
            "l2_protocol_text",
            375,
            ly2_y + 25,
            "Agent Protocol (core/agents/base.py)  ·  choose_action(env: CaroEnv, budget: SearchBudget) -> AgentDecision",
            font_size=15,
            color="#4c1d95",
            align="center",
            w=1080,
        )

        # 5 Agent Cards (Level 1 -> Level 5)
        agent_specs = [
            (
                "l2_ag1",
                "Level 1 · RandomAgent",
                "random_ai.py\n• Uniform Legal Choice\n• Local Seeded RNG\n• Lower-Bound Baseline\n• ~0.03 ms / move",
                "#7c3aed",
                "#ede9fe",
            ),
            (
                "l2_ag2",
                "Level 2 · HeuristicAgent",
                "heuristic_ai.py\n• 1-Ply Pattern Eval\n• WIN / BLOCK Priority\n• Open/Closed 4, 3, 2\n• Defense Factor 0.9",
                "#7c3aed",
                "#ede9fe",
            ),
            (
                "l2_ag3",
                "Level 3 · MinimaxAgent",
                "minimax_ai.py\n• Alpha-Beta Pruning\n• Iterative Deepening\n• Move Ordering + PV\n• Candidate Radius r=2",
                "#9333ea",
                "#f5d0fe",
            ),
            (
                "l2_ag4",
                "Level 4 · MCTSAgent",
                "mcts_ai.py\n• UCT Selection (c=0.7)\n• Tactical Pre-Check\n• Progressive Widening\n• ε-Heuristic Rollout",
                "#c026d3",
                "#fae8ff",
            ),
            (
                "l2_ag5",
                "Level 5 · NeuralAgent",
                "neural_ai.py & core/ml/\n• PolicyNet ResNet (4B)\n• 768,537 Parameters\n• Masked Logits Softmax\n• ~3.66 ms CPU Inference",
                "#db2777",
                "#fce7f3",
            ),
        ]
        ag_x = 365
        ag_w = 208
        ag_gap = 15
        for cid, title, desc, st_col, hdr_col in agent_specs:
            self.card(
                cid,
                ag_x,
                ly2_y + 66,
                ag_w,
                148,
                title,
                desc,
                stroke=st_col,
                bg="#ffffff",
                header_bg=hdr_col,
                title_color="#4c1d95",
                title_size=14,
                body_size=12,
            )
            ag_x += ag_w + ag_gap

        # =====================================================================
        # LAYER 3: CONTRACT LAYER - CARO-V2 (Amber / Gold Theme)
        # =====================================================================
        ly3_y = 615
        ly3_h = 175
        self.rect(
            "layer3_container",
            50,
            ly3_y,
            1440,
            ly3_h,
            stroke="#d97706",
            bg="#fef3c7",
            stroke_width=2,
        )
        self.card(
            "layer3_badge",
            70,
            ly3_y + 22,
            270,
            130,
            "LAYER 3 · CONTRACT",
            "Contract Layer (caro-v2)\ncore/engine/interfaces.py\ncore/engine/types.py\n• Frozen Dataclasses\n• Type-Safe Boundaries",
            stroke="#b45309",
            bg="#fde68a",
            header_bg="#d97706",
            title_color="#ffffff",
            body_color="#78350f",
            title_size=15,
            body_size=13,
        )
        contract_cards = [
            (
                "l3_c1",
                "GameState (Frozen)",
                "• board: list[list[int]]\n• current_player: Player\n• last_action: Action | None\n• move_count, terminated, winner",
            ),
            (
                "l3_c2",
                "StepResult (Immutable)",
                "• state / next_state: GameState\n• reward: float (1.0 win, 0.0)\n• terminated / done: bool\n• winner: Player | None",
            ),
            (
                "l3_c3",
                "SearchBudget & Decision",
                "• time_limit_ms, max_depth\n• max_nodes, simulations, seed\n• AgentDecision(action, score,\n  nodes, simulations, elapsed_ms)",
            ),
            (
                "l3_c4",
                "InvalidActionReason",
                "• Cascade Validation Order:\n  1. GAME_OVER\n  2. MALFORMED\n  3. OUT_OF_BOUNDS\n  4. OCCUPIED",
            ),
        ]
        cx = 365
        cw = 260
        cgap = 20
        for cid, title, desc in contract_cards:
            self.card(
                cid,
                cx,
                ly3_y + 22,
                cw,
                130,
                title,
                desc,
                stroke="#d97706",
                bg="#ffffff",
                header_bg="#fef3c7",
                title_color="#92400e",
                title_size=14,
                body_size=12,
            )
            cx += cw + cgap

        # =====================================================================
        # LAYER 4: GAME ENGINE & RULES LAYER (Emerald Green Theme)
        # =====================================================================
        ly4_y = 830
        ly4_h = 175
        self.rect(
            "layer4_container",
            50,
            ly4_y,
            1440,
            ly4_h,
            stroke="#059669",
            bg="#d1fae5",
            stroke_width=2,
        )
        self.card(
            "layer4_badge",
            70,
            ly4_y + 22,
            270,
            130,
            "LAYER 4 · GAME ENGINE",
            "Core Engine & Rules Layer\n(core/engine/)\n• Single Source of Truth\n• O(n) Incremental Win Check\n• O(1) Undo & Fast Clone",
            stroke="#047857",
            bg="#a7f3d0",
            header_bg="#059669",
            title_color="#ffffff",
            body_color="#064e3b",
            title_size=15,
            body_size=13,
        )
        self.card(
            "l4_env",
            365,
            ly4_y + 22,
            350,
            130,
            "core/engine/game_env.py (CaroEnv)",
            "• Gym-Style API: reset(), step(), legal_actions()\n• Fast clone_env() via __new__ (~1.2 µs)\n• Stack-based undo() (~4.1 µs)\n• Defensive _snapshot() Isolation",
            stroke="#059669",
            bg="#ffffff",
            header_bg="#d1fae5",
            title_color="#065f46",
        )
        self.card(
            "l4_rules",
            740,
            ly4_y + 22,
            350,
            130,
            "core/engine/rules.py (RuleEngine)",
            "• 4 Directions: (0,1), (1,0), (1,1), (1,-1)\n• Maximal Contiguous Chain (count >= 5)\n• Blocked-Both-Ends Rule Check\n• check_winner_from_action O(n)",
            stroke="#059669",
            bg="#ffffff",
            header_bg="#d1fae5",
            title_color="#065f46",
        )
        self.card(
            "l4_board",
            1115,
            ly4_y + 22,
            350,
            130,
            "core/engine/board.py (Board)",
            "• 11×11 Grid (121 Cells, Row-Major)\n• Player Enum: EMPTY=0, X=1, O=-1\n• action_to_index & index_to_action\n• legal_action_mask (121-bool tuple)",
            stroke="#059669",
            bg="#ffffff",
            header_bg="#d1fae5",
            title_color="#065f46",
        )

        # =====================================================================
        # LAYER 5: INFRASTRUCTURE, ML PIPELINE & TESTING LAYER (Coral / Orange)
        # =====================================================================
        ly5_y = 1045
        ly5_h = 175
        self.rect(
            "layer5_container",
            50,
            ly5_y,
            1440,
            ly5_h,
            stroke="#ea580c",
            bg="#ffedd5",
            stroke_width=2,
        )
        self.card(
            "layer5_badge",
            70,
            ly5_y + 22,
            270,
            130,
            "LAYER 5 · INFRA & QA",
            "Experiment, Data & Testing\n(core/utils/, core/ml/, tests/)\n• Reproducible Evaluation\n• D4 Clean Datasets\n• 1,866 Automated Tests",
            stroke="#c2410c",
            bg="#fed7aa",
            header_bg="#ea580c",
            title_color="#ffffff",
            body_color="#7c2d12",
            title_size=15,
            body_size=13,
        )
        self.card(
            "l5_runner",
            365,
            ly5_y + 22,
            350,
            130,
            "core/utils/tournament_runner.py",
            "• Round-Robin 10 Pairs × 100 Games\n• Paired Seed Derivation & X/O Swap\n• BudgetEnforcer (DEFAULT & FAIR 150ms)\n• Safe JSONL Resume by game_id",
            stroke="#ea580c",
            bg="#ffffff",
            header_bg="#ffedd5",
            title_color="#9a3412",
        )
        self.card(
            "l5_logger",
            740,
            ly5_y + 22,
            350,
            130,
            "core/utils/logger.py & data_pipeline.py",
            "• Streaming GameRecord & MoveRecord JSONL\n• 100% Replay Validation & SHA-256 Hashes\n• D4 Canonical Orbit Isolation (dataset-v5)\n• 309,136 Train / 4,806 Val / 4,689 Test",
            stroke="#ea580c",
            bg="#ffffff",
            header_bg="#ffedd5",
            title_color="#9a3412",
        )
        self.card(
            "l5_tests",
            1115,
            ly5_y + 22,
            350,
            130,
            "tests/ & benchmarks/ (20+ Suites)",
            "• 1,866 Passed Pytest Cases (0 Failures)\n• Differential String Oracle (3,000 Boards)\n• Agent Contract W34-T01..T04 Checks\n• Headless Streamlit AppTest Suite",
            stroke="#ea580c",
            bg="#ffffff",
            header_bg="#ffedd5",
            title_color="#9a3412",
        )

        # Inter-Layer Vertical Arrows showing Architectural Flow
        for i, ax in enumerate([540, 915, 1290]):
            self.arrow(f"arr_l1_l2_{i}", [(ax, ly1_y + ly1_h), (ax, ly2_y)], stroke="#0284c7")
            self.arrow(f"arr_l2_l3_{i}", [(ax, ly2_y + ly2_h), (ax, ly3_y)], stroke="#7c3aed")
            self.arrow(f"arr_l3_l4_{i}", [(ax, ly3_y + ly3_h), (ax, ly4_y)], stroke="#d97706")
            self.arrow(
                f"arr_l4_l5_{i}",
                [(ax, ly4_y + ly4_h), (ax, ly5_y)],
                stroke="#ea580c",
                start_arrow="arrow",
                end_arrow="arrow",
            )

        # Right-hand Bus Line connecting Presentation/CLI directly to Contract & Engine
        bus_x = 1520
        self.arrow(
            "arr_right_bus_engine",
            [(1490, ly1_y + 88), (bus_x, ly1_y + 88), (bus_x, ly4_y + 88), (1490, ly4_y + 88)],
            stroke="#059669",
            stroke_style="dashed",
        )
        self.arrow(
            "arr_right_bus_infra",
            [(1490, ly2_y + 115), (bus_x - 12, ly2_y + 115), (bus_x - 12, ly5_y + 88), (1490, ly5_y + 88)],
            stroke="#ea580c",
            stroke_style="dashed",
        )

    def build_mind_map(self) -> None:
        """Right Panel (x: 1640..3260): Comprehensive Mind Map of the Caro AI Project."""
        mm_x0 = 1640
        mm_w = 1640
        mm_h = 1220
        self.rect(
            "mm_backdrop",
            mm_x0,
            20,
            mm_w,
            mm_h,
            stroke="#cbd5e1",
            bg="#ffffff",
            stroke_width=2,
        )
        self.text(
            "mm_title",
            mm_x0 + 40,
            40,
            "CARO AI PROJECT · SYSTEM & METHODOLOGY MIND MAP",
            font_size=30,
            color="#0f172a",
            align="center",
            w=mm_w - 80,
        )
        self.text(
            "mm_subtitle",
            mm_x0 + 40,
            82,
            "Visual Taxonomy of Core Modules, Search Algorithms, ML Pipeline, Evaluation Harness & Interactive UI",
            font_size=16,
            color="#475569",
            align="center",
            w=mm_w - 80,
        )

        # Central Hub Node
        cx = mm_x0 + mm_w / 2  # 2460
        cy = 640
        hub_w = 310
        hub_h = 136
        self.rect(
            "mm_hub_outer",
            cx - hub_w / 2 - 8,
            cy - hub_h / 2 - 8,
            hub_w + 16,
            hub_h + 16,
            stroke="#3b82f6",
            bg="#dbeafe",
            stroke_width=2,
        )
        self.card(
            "mm_hub",
            cx - hub_w / 2,
            cy - hub_h / 2,
            hub_w,
            hub_h,
            "CARO AI PROJECT",
            "11×11 Board · win_length = 5\nBlocked-Both-Ends Rule\nContract: caro-v2\nPython 3.13 · PyTorch · Streamlit",
            stroke="#1d4ed8",
            bg="#eff6ff",
            header_bg="#1d4ed8",
            title_color="#ffffff",
            body_color="#1e3a8a",
            title_size=18,
            body_size=13,
        )

        # 6 Mind-Map Branches (3 on Left of Hub, 3 on Right of Hub)
        left_branches = [
            {
                "id": "mm_b1",
                "y": 170,
                "title": "1. Presentation & Web UI (ui/)",
                "subtitle": "Streamlit Interactive App\n• ui/app.py & human_controller.py\n• 3 Modes: HvH, HvAI, AIvAI",
                "stroke": "#0284c7",
                "bg": "#e0f2fe",
                "hdr": "#0284c7",
                "leaves": [
                    ("Reactive 11×11 Grid", "121 st.button Cells + Dynamic CSS"),
                    ("Visual State Feedback", "Last Move (#FFA726) & Winning 5 Line (#E53935)"),
                    ("AI Telemetry & Cache", "Live elapsed_ms, nodes, sims & Agent Cache"),
                ],
            },
            {
                "id": "mm_b2",
                "y": 540,
                "title": "2. Contract Boundary (caro-v2)",
                "subtitle": "core/engine/interfaces.py & types.py\n• Immutable State & Result Schemas\n• Zero-Mutation Guarantee",
                "stroke": "#d97706",
                "bg": "#fef3c7",
                "hdr": "#d97706",
                "leaves": [
                    ("GameState & StepResult", "Frozen Board Snapshot, Turn, Winner, Reward"),
                    ("SearchBudget & Decision", "time_limit_ms, max_depth, nodes, sims, seed"),
                    ("Cascade Validation", "GAME_OVER → MALFORMED → OOB → OCCUPIED"),
                ],
            },
            {
                "id": "mm_b3",
                "y": 910,
                "title": "3. Core Game Engine (core/engine/)",
                "subtitle": "CaroEnv, RuleEngine & Board\n• Single Source of Truth\n• High-Speed Tree Search Support",
                "stroke": "#059669",
                "bg": "#d1fae5",
                "hdr": "#059669",
                "leaves": [
                    ("CaroEnv Lifecycle", "reset(), legal_actions(), step() (~12.9 µs)"),
                    ("Fast Search Primitives", "clone_env() (~1.2 µs) & History Stack undo() (~4.1 µs)"),
                    ("RuleEngine (4 Directions)", "Maximal Contiguous Run ≥ 5 & Blocked-Both-Ends"),
                ],
            },
        ]

        right_branches = [
            {
                "id": "mm_b4",
                "y": 170,
                "title": "4. Search Agents (core/agents/)",
                "subtitle": "Classical & Monte Carlo Tree Search\n• Unified choose_action() API\n• Seeded Reproducibility",
                "stroke": "#7c3aed",
                "bg": "#f3e8ff",
                "hdr": "#7c3aed",
                "leaves": [
                    ("Random & Heuristic", "Uniform Baseline & 1-Ply Pattern Priority Scorer"),
                    ("Minimax + Alpha-Beta", "Depth 2, Move Ordering, Chebyshev r=2 (-89.6% Nodes)"),
                    ("Guided MCTS (UCT)", "8 Sims, Tactical Precheck, Progressive Widening, ε-Rollout"),
                ],
            },
            {
                "id": "mm_b5",
                "y": 540,
                "title": "5. Deep Learning Pipeline (core/ml/)",
                "subtitle": "Supervised Policy Learning\n• Self-Play Data Pipeline\n• PolicyNet ResNet Architecture",
                "stroke": "#db2777",
                "bg": "#fce7f3",
                "hdr": "#db2777",
                "leaves": [
                    ("Dataset v5 (309K Train)", "2,000 Games, Replay Verified, D4 Orbit Clean"),
                    ("PolicyNet (768,537 Params)", "3×11×11 → Stem → 4 ResBlocks → 121 Logits"),
                    ("NeuralAgent Inference", "Epoch 5 Best, 52.68% Top-1, ~3.66 ms CPU"),
                ],
            },
            {
                "id": "mm_b6",
                "y": 910,
                "title": "6. Tournament, Ablation & QA",
                "subtitle": "scripts/, results/w78/ & tests/\n• W78 Round-Robin & Ablations\n• Multi-Layer Pytest Verification",
                "stroke": "#ea580c",
                "bg": "#ffedd5",
                "hdr": "#ea580c",
                "leaves": [
                    ("W78 Tournament (2,000 Games)", "DEFAULT & FAIR (150ms), Paired Seeds, 0 Violations"),
                    ("Ablation Studies (A1 & A2)", "Alpha-Beta Node Pruning & MCTS 100/400/1000 Sims"),
                    ("1,866 Automated Tests", "String Oracle (3,000 Boards), Contract W34 & UI AppTest"),
                ],
            },
        ]

        # Render Left Branches and their Leaves
        b_w = 270
        b_h = 115
        leaf_w = 290
        leaf_h = 68
        for br in left_branches:
            bx = cx - hub_w / 2 - 60 - b_w  # 1975
            by = br["y"]
            self.card(
                br["id"],
                bx,
                by,
                b_w,
                b_h,
                br["title"],
                br["subtitle"],
                stroke=br["stroke"],
                bg=br["bg"],
                header_bg=br["hdr"],
                title_color="#ffffff",
                title_size=14,
                body_size=12,
            )
            # Arrow from Hub to Branch
            self.arrow(
                f"arr_hub_{br['id']}",
                [(cx - hub_w / 2 - 8, cy), (bx + b_w + 25, by + b_h / 2), (bx + b_w, by + b_h / 2)],
                stroke=br["stroke"],
                stroke_width=3,
            )
            # 3 Leaf nodes to the left of the branch
            lx = bx - 50 - leaf_w  # 1635 -> shift to 1665
            lx = mm_x0 + 25
            for idx, (l_title, l_desc) in enumerate(br["leaves"]):
                ly = by - 55 + idx * 80
                lid = f"{br['id']}_leaf_{idx}"
                self.card(
                    lid,
                    lx,
                    ly,
                    leaf_w,
                    leaf_h,
                    l_title,
                    l_desc,
                    stroke=br["stroke"],
                    bg="#ffffff",
                    title_color=br["stroke"],
                    body_color="#334155",
                    title_size=13,
                    body_size=11,
                )
                self.arrow(
                    f"arr_{lid}",
                    [(bx, by + b_h / 2), (lx + leaf_w + 18, ly + leaf_h / 2), (lx + leaf_w, ly + leaf_h / 2)],
                    stroke=br["stroke"],
                    stroke_width=2,
                )

        # Render Right Branches and their Leaves
        for br in right_branches:
            bx = cx + hub_w / 2 + 60  # 2675
            by = br["y"]
            self.card(
                br["id"],
                bx,
                by,
                b_w,
                b_h,
                br["title"],
                br["subtitle"],
                stroke=br["stroke"],
                bg=br["bg"],
                header_bg=br["hdr"],
                title_color="#ffffff",
                title_size=14,
                body_size=12,
            )
            # Arrow from Hub to Branch
            self.arrow(
                f"arr_hub_{br['id']}",
                [(cx + hub_w / 2 + 8, cy), (bx - 25, by + b_h / 2), (bx, by + b_h / 2)],
                stroke=br["stroke"],
                stroke_width=3,
            )
            # 3 Leaf nodes to the right of the branch
            lx = bx + b_w + 40
            for idx, (l_title, l_desc) in enumerate(br["leaves"]):
                ly = by - 55 + idx * 80
                lid = f"{br['id']}_leaf_{idx}"
                self.card(
                    lid,
                    lx,
                    ly,
                    leaf_w,
                    leaf_h,
                    l_title,
                    l_desc,
                    stroke=br["stroke"],
                    bg="#ffffff",
                    title_color=br["stroke"],
                    body_color="#334155",
                    title_size=13,
                    body_size=11,
                )
                self.arrow(
                    f"arr_{lid}",
                    [(bx + b_w, by + b_h / 2), (lx - 18, ly + leaf_h / 2), (lx, ly + leaf_h / 2)],
                    stroke=br["stroke"],
                    stroke_width=2,
                )

    def to_json(self) -> str:
        payload = {
            "type": "excalidraw",
            "version": 2,
            "source": "https://excalidraw.com",
            "elements": self.elements,
            "appState": {
                "gridSize": 20,
                "viewBackgroundColor": "#f1f5f9",
            },
            "files": {},
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)


def main() -> None:
    builder = ExcalidrawBuilder()
    builder.build_layered_architecture()
    builder.build_mind_map()
    OUT_FILE.write_text(builder.to_json(), encoding="utf-8")
    print(f"Created {OUT_FILE} with {len(builder.elements)} Excalidraw elements.")


if __name__ == "__main__":
    main()
