# Figma AI Agent Prompt — Caro (Gomoku) Game UI Design for Streamlit

> **Scope update:** The current UI develops and tests only the 11×11 (121-cell) board while keeping rendering parameterized by `board_size` for future expansion. 9×9 is deferred.

> **Task:** Design a complete wireframe and UI for a Caro (Gomoku) AI board game web application built with **Streamlit (Python)**. The design must cover the full screen flow including initial state, mid-game, win/draw/error states, and all interactive components.

---

## 🎯 Objective

Design a **single-page web application** for playing **Caro (Gomoku)** — a two-player strategy board game where players take turns placing pieces on a grid, aiming to get 5 in a row. The app supports Human vs Human, Human vs AI, and AI vs AI modes.

**Target framework: Streamlit** — a Python framework that renders UI top-to-bottom as a single page. Every designed component must be implementable using native Streamlit widgets (`st.columns`, `st.button`, `st.selectbox`, `st.sidebar`, `st.markdown`, `st.session_state`, `st.toast`, `st.dialog`...).

---

## 📐 Technical Specifications

### Board
- **Default and current scope:** 11×11 grid (121 cells); 9×9 is deferred
- **Cell values:** `0 = Empty`, `1 = Player X (goes first)`, `-1 = Player O (goes second)`
- **Action encoding:** Each cell click at `(row, col)` maps to an integer: `action = row * board_size + col`
- **Win condition:** 5 consecutive pieces (horizontal, vertical, or diagonal) that are NOT blocked on both ends by the opponent
- **Draw condition:** Board is full with no winner

### Players
- **Player X (value 1):** Always goes first. Displayed as "X" symbol (blue theme)
- **Player O (value -1):** Goes second. Displayed as "O" symbol (red theme)

---

## 🖥️ Overall Layout

Design a **single main screen** following Streamlit's typical sidebar + main content layout:

```
┌──────────────────────────────────────────────────────────┐
│                   SIDEBAR (left)                          │
│  ┌────────────────────────────────────┐                  │
│  │  🎮 CARO AI                        │                  │
│  │  ──────────────────────            │                  │
│  │  Game Mode: [Dropdown]            │                  │
│  │    • Human vs Human                │                  │
│  │    • Human vs AI                   │                  │
│  │    • AI vs AI                      │                  │
│  │                                    │                  │
│  │  AI Algorithm (if applicable):    │                  │
│  │    [Dropdown]                      │                  │
│  │    • Random                        │                  │
│  │    • Heuristic                     │                  │
│  │    • Minimax (Alpha-Beta)          │                  │
│  │    • MCTS                          │                  │
│  │    • Neural Network                │                  │
│  │                                    │                  │
│  │  Board Size: [11x11]               │                  │
│  │                                    │                  │
│  │  [🔄 New Game]                    │                  │
│  │                                    │                  │
│  │  ──────────────────────            │                  │
│  │  📊 Statistics                     │                  │
│  │  X wins: 3                         │                  │
│  │  O wins: 1                         │                  │
│  │  Draws: 0                          │                  │
│  │                                    │                  │
│  │  ──────────────────────            │                  │
│  │  📜 Move History                   │                  │
│  │  1. X → (4,4)                      │                  │
│  │  2. O → (4,5)                      │                  │
│  │  3. X → (3,4)                      │                  │
│  │  ...                               │                  │
│  └────────────────────────────────────┘                  │
│                                                          │
│              MAIN CONTENT (right)                        │
│  ┌────────────────────────────────────────────────┐      │
│  │                                                │      │
│  │   ┌─ STATUS BAR ────────────────────────┐     │      │
│  │   │  🔵 Current Turn: Player X           │     │      │
│  │   │  Moves: 5 / 121                      │     │      │
│  │   └─────────────────────────────────────┘     │      │
│  │                                                │      │
│  │   ┌─ ERROR / NOTIFICATION ZONE ─────────┐     │      │
│  │   │  ⚠️ Cell already occupied! (toast)   │     │      │
│  │   └─────────────────────────────────────┘     │      │
│  │                                                │      │
│  │   ┌─ GAME BOARD 11×11 ──────────────────┐     │      │
│  │   │  11-column × 11-row button grid     │     │      │
│  │   │  Each cell is one st.button         │     │      │
│  │   │                                      │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]       │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]       │     │      │
│  │   │  [ ][ ][ ][X][ ][ ][ ][ ][ ]       │     │      │
│  │   │  [ ][ ][ ][ ][O][ ][ ][ ][ ]       │     │      │
│  │   │  [ ][ ][ ][ ][ ][X][ ][ ][ ]       │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]       │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]       │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]       │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]       │     │      │
│  │   │                                      │     │      │
│  │   └──────────────────────────────────────┘     │      │
│  │                                                │      │
│  │   ┌─ GAME RESULT BANNER ───────────────┐      │      │
│  │   │  🎉 Player X wins! [Play Again]     │      │      │
│  │   └─────────────────────────────────────┘      │      │
│  │                                                │      │
│  └────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

---

## 🎨 Detailed Component Design

### 1. Sidebar — Control Panel

| Component | Streamlit Widget | Description |
|---|---|---|
| App Title / Logo | `st.sidebar.title()` | Display "🎮 CARO AI" |
| Game Mode | `st.sidebar.selectbox()` | 3 options: Human vs Human, Human vs AI, AI vs AI |
| AI Algorithm Selector | `st.sidebar.selectbox()` | Shown only when mode includes AI. Options: Random, Heuristic, Minimax, MCTS, Neural Network |
| Board Size | `st.sidebar.selectbox()` | 11×11 only; configuration keeps the extension point |
| New Game Button | `st.sidebar.button()` | Resets all state, starts a fresh game |
| Statistics | `st.sidebar.metric()` | Session win/loss/draw counts for X and O |
| Move History | `st.sidebar.expander()` | Scrollable list: "1. X → (row, col)", "2. O → (row, col)", ... |

### 2. Status Bar — Turn & Progress Indicator

- **Position:** Above the board in main content area
- **Content:**
  - **Current turn indicator** with color-coded icon (🔵 for X, 🔴 for O)
  - **Move counter** displayed as `"Moves: {move_count} / {board_size²}"`
- **Widget:** `st.markdown()` or `st.columns()` + `st.metric()`

### 3. Game Board (Grid) — Primary Component

- **Rendering:** Use `st.columns(board_size)` for `board_size` rows. Each column contains one `st.button()`
- **Each cell has 5 visual states:**

| State | Display | Color / Style | Condition |
|---|---|---|---|
| **Empty** | `" "` or `"·"` | White/light gray background, thin border | `board[r][c] == 0` |
| **Player X** | `"X"` | Bold **blue text (#1E88E5)**, light blue background | `board[r][c] == 1` |
| **Player O** | `"O"` | Bold **red text (#E53935)**, light red background | `board[r][c] == -1` |
| **Last move (highlight)** | `"X"` or `"O"` with glowing border | Yellow/orange prominent border, highlighted background | `(r, c) == last_action` |
| **Game over** | Keep existing pieces | All cells set to `disabled=True`, reduced opacity | `terminated == True` |

- **Cell size:** Square, minimum 48×48px, large readable font
- **Interaction:** Click empty cell → call `env.step((row, col))`
- **Click occupied cell:** No action or show error toast

### 4. Error / Notification Zone

- **Position:** Between Status Bar and Board
- **Widget:** `st.toast()` or `st.warning()` / `st.error()`
- **Message types:**
  - ⚠️ `"Cell already occupied!"` — when clicking an occupied cell
  - ⚠️ `"Move out of bounds!"` — when action is out of range
  - ❌ `"Error: InvalidActionError"` — when engine raises an exception
- **Behavior:** Toast auto-dismisses after 3 seconds; `st.warning` clears on rerun

### 5. Game Result Banner

- **Shown when:** `terminated == True`
- **Variants:**

| Result | Display | Style |
|---|---|---|
| X wins | `"🎉 Player X wins!"` | Blue prominent banner, `st.success()` or `st.balloons()` |
| O wins | `"🎉 Player O wins!"` | Red prominent banner |
| Draw | `"🤝 It's a draw!"` | Gray/yellow banner |

- **Includes:** `[🔄 Play Again]` button that calls `env.reset()`
- **Board on game over:** All buttons `disabled=True`, highlight the winning 5 pieces if applicable

---

## 🔄 User Flow

### Primary Flow: Human vs AI Game

```
[App opens]
    │
    ▼
[Sidebar] Select mode: "Human vs AI"
    │
    ▼
[Sidebar] Select AI algorithm: "Minimax"
    │
    ▼
[Sidebar] Click "🔄 New Game"
    │
    ▼
[Main] Empty 11×11 board renders
[Status] "🔵 Current Turn: Player X | Moves: 0/121"
    │
    ▼
[Human Player X] Clicks cell (4, 4) ─────────────────┐
    │                                                   │
    ▼                                                   │
action = (5, 5)                                       │
env.step(40)                                            │
    │                                                   │
    ▼                                                   │
[Board updates] Cell (4,4) shows "X" with yellow border │
[Status] "🔴 Current Turn: Player O (AI) | Moves: 1/121"│
[Sidebar] History: "1. X → (4,4)"                      │
    │                                                   │
    ▼                                                   │
[AI auto-plays] env.step(ai_action)                     │
[Board updates] AI's chosen cell shows "O" highlighted  │
[Status] "🔵 Current Turn: Player X | Moves: 2/121"    │
[Sidebar] History: "2. O → (r, c)"                     │
    │                                                   │
    ▼                                                   │
... repeat until terminated == True ...                 │
    │                                                   │
    ▼                                                   │
[Result Banner] "🎉 Player X wins!"                    │
[Board disabled] Winning 5 pieces highlighted           │
[Sidebar] Stats updated: X wins +1                     │
    │                                                   │
    ▼                                                   │
[Click "Play Again"] → env.reset() → Back to empty board
```

### Error Handling Flow

```
[Player clicks an occupied cell]
    │
    ▼
InvalidActionError is raised
    │
    ▼
[Toast] "⚠️ Cell already occupied! Choose another cell."
[State UNCHANGED] — board, turn, and move count remain the same
```

---

## 📋 UI Event → API Call Mapping Table

| UI Event | Streamlit Widget | API Call | Response Handling |
|---|---|---|---|
| Click empty cell `(r, c)` | `st.button()` callback | `env.step((r, c))` | Update board from `StepResult.next_state` |
| Click occupied cell | `st.button()` callback | `env.step((r, c))` | Catch `InvalidActionError`, show toast |
| Click "New Game" | `st.sidebar.button("🔄 New Game")` | `env.reset()` | Receive new `GameState`, reset entire UI |
| Change game mode | `st.sidebar.selectbox()` | Auto-trigger `env.reset()` | Reset board + config |
| Change AI algorithm | `st.sidebar.selectbox()` | Update `session_state` | Swap AI agent for next game |
| Change board size | `st.sidebar.selectbox()` | `env = CaroEnv(GameConfig(board_size=n))` | Create new env, reset board |

---

## 🎨 Design Tokens

### Color Palette

| Role | Hex Code | Usage |
|---|---|---|
| Primary (Player X) | `#1E88E5` (Blue 600) | X pieces, X turn icon, X wins banner |
| Secondary (Player O) | `#E53935` (Red 600) | O pieces, O turn icon, O wins banner |
| Accent / Highlight | `#FFA726` (Orange 400) | Last move border, winning pieces highlight |
| Background | `#FAFAFA` | Main content background |
| Board Cell | `#FFFFFF` border `#E0E0E0` | Empty board cells |
| Board Cell Hover | `#F5F5F5` | Hover state for empty cells |
| Disabled | `#BDBDBD` opacity 0.5 | Cells after game ends |
| Success | `#43A047` (Green 600) | Win banner, success toast |
| Warning | `#FB8C00` (Orange 700) | Soft error toast |
| Error | `#D32F2F` (Red 700) | Critical error toast |

### Typography

| Element | Font | Size | Weight |
|---|---|---|---|
| App title | Sans-serif (Streamlit default) | 28px | Bold |
| Status bar | Sans-serif | 18px | Semi-bold |
| Board cell piece | Monospace or Sans-serif | 24px | Bold |
| Sidebar labels | Sans-serif | 14px | Regular |
| Move history | Monospace | 13px | Regular |
| Toast / Error | Sans-serif | 14px | Medium |

### Spacing & Sizing

| Element | Value |
|---|---|
| Board cell | 48×48px min, 2px gap |
| Sidebar width | ~300px (Streamlit default) |
| Main content padding | 16px |
| Cell border radius | 4px |
| Cell border | 1px solid #E0E0E0 |

---

## 📱 Responsive Behavior

- **Desktop (>768px):** Sidebar on left + Board centered in main content
- **Mobile (<768px):** Sidebar collapses to hamburger menu (Streamlit default behavior), board goes full-width with smaller cells (min 36×36px, still tappable)

---

## 📦 Required Figma Frames

Design the following frames/screens in the Figma file:

1. **Main Screen — Initial State:** Empty 11×11 board, full sidebar with all controls, status shows "Player X's turn"
2. **Main Screen — Mid-Game:** 10+ pieces on board, last move highlighted with yellow/orange border, move history populated in sidebar
3. **Main Screen — X Wins:** Result banner displayed, 5 winning pieces highlighted, entire board disabled (grayed out)
4. **Main Screen — Draw:** Draw banner, board completely full, all cells occupied
5. **Main Screen — Error Toast:** Toast notification "Cell already occupied!" visible between status bar and board
6. **Component Sheet:** All cell states (empty, X, O, highlighted, disabled) side by side, button states (default, hover, active, disabled), toast variants (warning, error, success)

---

## ⚠️ Critical Design Constraints

> [!IMPORTANT]
> - The UI contains **NO game logic** whatsoever (no win checking, no rule enforcement). All logic lives in the Engine backend.
> - The UI only **reads** `GameState` and **calls** `env.step()` / `env.reset()`.
> - When the game ends (`terminated == True`), the UI simply **disables interaction** and displays the result from `StepResult.winner`.
> - All designs must **map 1:1 to Streamlit's native capabilities** — do NOT design complex animations, drag-and-drop, or custom canvas elements that Streamlit cannot support natively.
> - Each board cell is an individual `st.button()` — this is the standard approach for rendering interactive grids in Streamlit.
> - Streamlit reruns the entire script on every interaction — design must account for state persistence via `st.session_state`.

---

## 📎 Reference Documents

- **API Contract:** `docs/contracts/caro_v1.md`
- **Data Types:** `core/engine/interfaces.py` — `GameState`, `StepResult`, `Player`, `InvalidActionError`
- **Action Encoding:** Tuple `(row, col)` passed to `env.step()` (per contract v1)
- **Board Sizes:** 11×11 only in the current scope; 9×9 is deferred
- **Target Framework:** Streamlit (Python)
