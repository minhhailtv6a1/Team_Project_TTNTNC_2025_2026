# Prompt cho AI Agent Figma — Thiết kế giao diện Game Caro (Streamlit)

> Task: **W1-M1-01 — Thiết kế luồng màn hình** cho ứng dụng chơi cờ Caro AI, xây dựng bằng **Streamlit (Python)**

---

## 🎯 Mục tiêu

Thiết kế wireframe + UI hoàn chỉnh cho **một ứng dụng web chơi cờ Caro (Gomoku)** với AI. Ứng dụng sẽ được lập trình bằng **Streamlit** — framework Python render giao diện dạng top-to-bottom, single-page. Mọi thành phần thiết kế phải khả thi để implement bằng các widget có sẵn của Streamlit (`st.columns`, `st.button`, `st.selectbox`, `st.sidebar`, `st.markdown`, `st.session_state`, `st.toast`, `st.dialog`...).

---

## 📐 Thông số kỹ thuật bắt buộc

### Bàn cờ
- **Kích thước mặc định:** 9×9 (81 ô) — có thể mở rộng lên 11×11 trong tương lai
- **Giá trị mỗi ô:** `0 = Trống`, `1 = X (người đi trước)`, `-1 = O (người đi sau)`
- **Encoding action:** Mỗi click vào ô `(row, col)` sẽ được chuyển thành action số nguyên: `action = row * board_size + col`
- **Luật thắng:** 5 quân liên tiếp (ngang, dọc, chéo) + luật chặn 2 đầu
- **Điều kiện hòa:** Bàn đầy mà chưa ai thắng

### Người chơi
- **Player X (giá trị 1):** Luôn đi trước, hiển thị ký hiệu "X" hoặc icon tương ứng
- **Player O (giá trị -1):** Đi sau, hiển thị ký hiệu "O" hoặc icon tương ứng

---

## 🖥️ Bố cục tổng thể (Layout)

Thiết kế **một màn hình chính duy nhất (Single Page App)** theo layout Streamlit điển hình:

```
┌─────────────────────────────────────────────────────────┐
│                    SIDEBAR (trái)                        │
│  ┌───────────────────────────────────┐                  │
│  │  🎮 CARO AI                       │                  │
│  │  ─────────────────────            │                  │
│  │  Chế độ chơi: [Dropdown]         │                  │
│  │    • Người vs Người               │                  │
│  │    • Người vs AI                  │                  │
│  │    • AI vs AI                     │                  │
│  │                                   │                  │
│  │  Chọn AI (nếu có):               │                  │
│  │    [Dropdown thuật toán]          │                  │
│  │    • Random                       │                  │
│  │    • Heuristic                    │                  │
│  │    • Minimax (Alpha-Beta)         │                  │
│  │    • MCTS                         │                  │
│  │    • Neural Network               │                  │
│  │                                   │                  │
│  │  Kích thước bàn: [9x9 ▼]         │                  │
│  │                                   │                  │
│  │  [🔄 Ván mới / New Game]         │                  │
│  │                                   │                  │
│  │  ─────────────────────            │                  │
│  │  📊 Thống kê                      │                  │
│  │  X thắng: 3                       │                  │
│  │  O thắng: 1                       │                  │
│  │  Hòa: 0                          │                  │
│  │                                   │                  │
│  │  ─────────────────────            │                  │
│  │  📜 Lịch sử nước đi              │                  │
│  │  1. X → (4,4)                     │                  │
│  │  2. O → (4,5)                     │                  │
│  │  3. X → (3,4)                     │                  │
│  │  ...                              │                  │
│  └───────────────────────────────────┘                  │
│                                                         │
│              MAIN CONTENT (phải)                        │
│  ┌───────────────────────────────────────────────┐      │
│  │                                               │      │
│  │   ┌─ STATUS BAR ───────────────────────┐     │      │
│  │   │  🔵 Lượt của: Player X              │     │      │
│  │   │  Nước đi: 5/81                      │     │      │
│  │   └────────────────────────────────────┘     │      │
│  │                                               │      │
│  │   ┌─ ERROR / NOTIFICATION ZONE ────────┐     │      │
│  │   │  ⚠️ Ô này đã có quân! (toast)      │     │      │
│  │   └────────────────────────────────────┘     │      │
│  │                                               │      │
│  │   ┌─ BÀN CỜ 9×9 ─────────────────────┐     │      │
│  │   │  Lưới 9 cột × 9 hàng button       │     │      │
│  │   │  Mỗi ô là 1 st.button vuông       │     │      │
│  │   │                                     │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]      │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]      │     │      │
│  │   │  [ ][ ][ ][X][ ][ ][ ][ ][ ]      │     │      │
│  │   │  [ ][ ][ ][ ][O][ ][ ][ ][ ]      │     │      │
│  │   │  [ ][ ][ ][ ][ ][X][ ][ ][ ]      │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]      │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]      │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]      │     │      │
│  │   │  [ ][ ][ ][ ][ ][ ][ ][ ][ ]      │     │      │
│  │   │                                     │     │      │
│  │   └─────────────────────────────────────┘     │      │
│  │                                               │      │
│  │   ┌─ GAME RESULT BANNER ──────────────┐      │      │
│  │   │  🎉 Player X thắng! [Chơi lại]    │      │      │
│  │   └────────────────────────────────────┘      │      │
│  │                                               │      │
│  └───────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

---

## 🎨 Yêu cầu thiết kế chi tiết cho từng thành phần

### 1. Sidebar — Bảng điều khiển

| Thành phần | Streamlit Widget | Mô tả |
|---|---|---|
| Logo/Tiêu đề | `st.sidebar.title()` | Tên ứng dụng "🎮 CARO AI" |
| Chế độ chơi | `st.sidebar.selectbox()` | 3 option: Người vs Người, Người vs AI, AI vs AI |
| Chọn thuật toán AI | `st.sidebar.selectbox()` | Hiện khi chế độ có AI. Danh sách: Random, Heuristic, Minimax, MCTS, Neural Network |
| Kích thước bàn | `st.sidebar.selectbox()` | Option: 9×9, 11×11 |
| Nút New Game | `st.sidebar.button()` | Reset toàn bộ state, bắt đầu ván mới |
| Thống kê | `st.sidebar.metric()` | Số ván X thắng, O thắng, Hòa |
| Lịch sử nước đi | `st.sidebar.expander()` | Danh sách cuộn các nước đã đi: "1. X → (row, col)" |

### 2. Status Bar — Thanh trạng thái

- **Vị trí:** Phía trên bàn cờ, trong main content
- **Nội dung:**
  - Hiển thị **người đang đến lượt** kèm icon/màu sắc phân biệt (ví dụ: 🔵 cho X, 🔴 cho O)
  - Hiển thị **số nước đã đi** dạng `"Nước đi: {move_count}/{board_size²}"`
- **Widget:** `st.markdown()` hoặc `st.columns()` + `st.metric()`

### 3. Bàn cờ (Board Grid) — Thành phần chính

- **Render:** Dùng `st.columns(9)` lặp 9 hàng, mỗi cột chứa 1 `st.button()`
- **Mỗi ô (cell) có 5 trạng thái trực quan:**

| Trạng thái | Hiển thị | Màu/Style | Điều kiện |
|---|---|---|---|
| **Ô trống** | `" "` hoặc `"·"` | Nền trắng/xám nhạt, viền mỏng | `board[r][c] == 0` |
| **Quân X** | `"X"` | Chữ đậm màu **xanh dương (#1E88E5)**, nền xanh nhạt | `board[r][c] == 1` |
| **Quân O** | `"O"` | Chữ đậm màu **đỏ (#E53935)**, nền đỏ nhạt | `board[r][c] == -1` |
| **Nước vừa đi (highlight)** | `"X"` hoặc `"O"` kèm viền sáng | Viền vàng/cam nổi bật, nền highlight | `(r,c) == last_action` |
| **Game kết thúc** | Giữ nguyên quân | Toàn bộ ô `disabled=True`, opacity giảm | `terminated == True` |

- **Kích thước ô:** Vuông đều, tối thiểu 48×48px, font chữ lớn dễ đọc
- **Tương tác:** Click vào ô trống → gọi `env.step(action)` với `action = row * 9 + col`
- **Click vào ô đã có quân:** Không làm gì hoặc hiện toast lỗi

### 4. Vùng thông báo lỗi (Error/Notification Zone)

- **Vị trí:** Giữa Status Bar và Bàn cờ
- **Widget:** `st.toast()` hoặc `st.warning()`/`st.error()`
- **Các loại thông báo:**
  - ⚠️ `"Ô này đã có quân!"` — khi click ô đã đánh
  - ⚠️ `"Nước đi ngoài phạm vi!"` — khi action bất hợp lệ
  - ❌ `"Lỗi: InvalidActionError"` — khi engine trả exception
- **Hành vi:** Toast tự biến mất sau 3 giây, hoặc dùng `st.warning` sẽ mất khi rerun

### 5. Game Result Banner — Kết quả ván đấu

- **Hiển thị khi:** `terminated == True`
- **Các trường hợp:**

| Kết quả | Hiển thị | Style |
|---|---|---|
| X thắng | `"🎉 Player X đã thắng!"` | Banner xanh dương nổi bật, `st.success()` hoặc `st.balloons()` |
| O thắng | `"🎉 Player O đã thắng!"` | Banner đỏ nổi bật |
| Hòa | `"🤝 Ván đấu hòa!"` | Banner xám/vàng |

- **Kèm nút:** `[🔄 Chơi lại]` gọi `env.reset()`
- **Bàn cờ khi kết thúc:** Tất cả button ở trạng thái `disabled=True`, highlight 5 quân thắng nếu có

---

## 🔄 Luồng tương tác (User Flow)

### Flow chính: Một ván đấu Người vs AI

```
[Mở ứng dụng]
    │
    ▼
[Sidebar] Chọn chế độ: "Người vs AI"
    │
    ▼
[Sidebar] Chọn thuật toán AI: "Minimax"
    │
    ▼
[Sidebar] Nhấn "🔄 Ván mới"
    │
    ▼
[Main] Bàn cờ 9×9 trống hiện ra
[Status] "🔵 Lượt của: Player X | Nước đi: 0/81"
    │
    ▼
[Người chơi X] Click ô (4, 4) ──────────────────┐
    │                                              │
    ▼                                              │
action = 4 * 9 + 4 = 40                           │
env.step(40)                                       │
    │                                              │
    ▼                                              │
[Board cập nhật] Ô (4,4) hiện "X" viền vàng       │
[Status] "🔴 Lượt của: Player O (AI) | Nước đi: 1/81"
[Sidebar] Lịch sử: "1. X → (4,4)"                 │
    │                                              │
    ▼                                              │
[AI tự động đi] env.step(ai_action)                │
[Board cập nhật] Ô AI chọn hiện "O" viền vàng     │
[Status] "🔵 Lượt của: Player X | Nước đi: 2/81"  │
[Sidebar] Lịch sử: "2. O → (r, c)"                │
    │                                              │
    ▼                                              │
... lặp lại cho đến khi terminated == True ...     │
    │                                              │
    ▼                                              │
[Result Banner] "🎉 Player X thắng!"              │
[Bàn cờ disabled] Highlight 5 quân thắng          │
[Sidebar] Thống kê cập nhật: X thắng +1           │
    │                                              │
    ▼                                              │
[Nút "Chơi lại"] → env.reset() → Quay lại bàn trống
```

### Flow xử lý lỗi

```
[Người chơi click ô đã có quân]
    │
    ▼
InvalidActionError được raise
    │
    ▼
[Toast] "⚠️ Ô này đã có quân! Hãy chọn ô khác."
[State KHÔNG thay đổi] — bàn cờ, lượt chơi giữ nguyên
```

---

## 📋 Bảng mapping sự kiện UI → API

| Sự kiện UI | Widget Streamlit | Lời gọi API | Response xử lý |
|---|---|---|---|
| Nhấn ô trống `(r, c)` | `st.button()` callback | `env.step((r, c))` | Cập nhật board từ `StepResult.next_state` |
| Nhấn ô đã có quân | `st.button()` callback | `env.step((r, c))` | Catch `InvalidActionError`, hiện toast |
| Nhấn "Ván mới" | `st.sidebar.button("🔄 Ván mới")` | `env.reset()` | Nhận `GameState` mới, reset UI |
| Đổi chế độ chơi | `st.sidebar.selectbox()` | Tự động `env.reset()` | Reset board + config |
| Đổi thuật toán AI | `st.sidebar.selectbox()` | Cập nhật `session_state` | Thay AI agent cho ván sau |
| Đổi kích thước bàn | `st.sidebar.selectbox()` | `env = CaroEnv(GameConfig(board_size=n))` | Tạo env mới, reset board |

---

## 🎨 Hướng dẫn phong cách thiết kế (Design Tokens)

### Bảng màu

| Vai trò | Mã màu | Dùng cho |
|---|---|---|
| Primary (X) | `#1E88E5` (Blue 600) | Quân X, icon lượt X, banner X thắng |
| Secondary (O) | `#E53935` (Red 600) | Quân O, icon lượt O, banner O thắng |
| Accent / Highlight | `#FFA726` (Orange 400) | Viền nước vừa đi, quân thắng highlight |
| Background | `#FAFAFA` | Nền main content |
| Board Cell | `#FFFFFF` viền `#E0E0E0` | Ô trống bàn cờ |
| Board Cell Hover | `#F5F5F5` | Hover ô trống |
| Disabled | `#BDBDBD` opacity 0.5 | Ô sau khi game kết thúc |
| Success | `#43A047` (Green 600) | Banner thắng, toast thành công |
| Warning | `#FB8C00` (Orange 700) | Toast lỗi nhẹ |
| Error | `#D32F2F` (Red 700) | Toast lỗi nghiêm trọng |

### Typography

| Phần tử | Font | Size | Weight |
|---|---|---|---|
| Tiêu đề app | Sans-serif (mặc định Streamlit) | 28px | Bold |
| Status bar | Sans-serif | 18px | Semi-bold |
| Quân cờ trong ô | Monospace hoặc Sans-serif | 24px | Bold |
| Sidebar label | Sans-serif | 14px | Regular |
| Lịch sử nước đi | Monospace | 13px | Regular |
| Toast / Error | Sans-serif | 14px | Medium |

### Spacing & Sizing

| Phần tử | Giá trị |
|---|---|
| Ô bàn cờ | 48×48px min, gap 2px |
| Sidebar width | ~300px (Streamlit default) |
| Padding main content | 16px |
| Border radius ô cờ | 4px |
| Button border | 1px solid #E0E0E0 |

---

## 📱 Responsive

- **Desktop (>768px):** Sidebar bên trái + Bàn cờ ở giữa main content
- **Mobile (<768px):** Sidebar collapse thành hamburger menu (Streamlit default), bàn cờ full-width, ô nhỏ hơn nhưng vẫn nhấn được (min 36×36px)

---

## 📦 Danh sách Frame/Screen cần thiết kế trong Figma

Tạo các frame sau trong file Figma:

1. **Main Screen — Trạng thái ban đầu:** Bàn cờ trống 9×9, sidebar đầy đủ, status "Lượt X"
2. **Main Screen — Đang chơi (mid-game):** Có 10+ quân trên bàn, highlight nước vừa đi, lịch sử nước đi trong sidebar
3. **Main Screen — X thắng:** Banner kết quả, 5 quân thắng highlight, bàn cờ disabled
4. **Main Screen — Hòa:** Banner hòa, bàn đầy
5. **Main Screen — Hiển thị lỗi:** Toast "Ô đã có quân" đang hiện
6. **Component Sheet:** Tất cả trạng thái của ô cờ (trống, X, O, highlight, disabled), button states, toast variants

---

## ⚠️ Lưu ý quan trọng

> [!IMPORTANT]
> - UI **KHÔNG chứa bất kỳ logic xác định thắng/thua** nào. Mọi logic game đều nằm trong Engine.
> - UI chỉ **đọc** `GameState` và **gọi** `env.step()` / `env.reset()`.
> - Khi game kết thúc (`terminated == True`), UI chỉ **disable tương tác** và hiển thị kết quả từ `StepResult.winner`.
> - Thiết kế phải **mapping 1:1 với khả năng của Streamlit** — không thiết kế animation phức tạp, drag-and-drop, hay custom canvas mà Streamlit không hỗ trợ native.
> - Mỗi ô cờ là một `st.button()` riêng biệt — đây là cách render grid phổ biến nhất trong Streamlit.

---

## 📎 Tài liệu tham chiếu

- Contract API: `docs/contracts/caro_v1.md`
- Data types: `core/engine/interfaces.py` — `GameState`, `StepResult`, `Player`, `InvalidActionError`
- Action encoding: `action = row * board_size + col` (dạng tuple `(row, col)` theo contract v1)
- Board size: 9×9 (default) hoặc 11×11
- Target framework: **Streamlit** (Python)
