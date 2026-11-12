# Kết quả cá nhân — Hải

## 1. Protocol chung

- Seed cố định: `42`; đồng hồ đo `time.perf_counter()` sau khi đã chạy warm-up.
- Trong `tictactoe_and_or_tree_search.ipynb`, biến toàn cục `COUNT` được reset về `0` ở mỗi lần gọi `and_or_search()`, tắt `DEBUG = 0` khi đo thời gian và đấu tập lớn.
- Thời gian báo cáo chỉ tính thời gian chọn nước đi của tác tử (không bao gồm thời gian vẽ bàn cờ Matplotlib).
- `TB/nước agent (ms) = (Tổng thời gian suy nghĩ của agent / Tổng số nước agent đã đi) * 1000`.

---

## 2. Bài 1 — Định nghĩa Tic-Tac-Toe và Random vs. Random (1.000 ván)

### Kiểm tra mô hình trò chơi (`tictactoe.py`)

- **State:** `list` 9 phần tử với giá trị thuộc `{' ', 'x', 'o'}`, đánh số `0..8` theo hàng ngang từ trái sang phải, từ trên xuống dưới.
- **Actions(s):** Danh sách chỉ số các ô còn trống (`board[i] == ' '`).
- **Result(s, player, a):** Sao chép bàn cờ đầu vào (`state.copy()`) và gán `state[a] = player`, đảm bảo không mutate trạng thái gốc.
- **Terminal(s) & Utility(s, player):** Kiểm tra qua `check_board(s)` trên 3 hàng, 3 cột và 2 đường chéo. Trạng thái kết thúc trả về `+1` (thắng), `0` (hòa), `-1` (thua); chưa kết thúc trả về `None`.

### Kết quả thực nghiệm Random vs. Random (`N = 1000, seed = 42`)

| Tác tử | Đối thủ | Số ván | Thắng | Hòa | Thua | Tỷ lệ thắng (%) | Số nước đã đi | Tổng thời gian (s) | TB/nước (ms) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Random (vai X — đi trước) | Random (vai O) | 1.000 | 590 | 126 | 284 | 59,0% | 4.191 | 0,0615 | 0,0147 |
| Random (vai O — đi sau) | Random (vai X) | 1.000 | 284 | 126 | 590 | 28,4% | 3.475 | 0,0502 | 0,0145 |

**Nhận xét:**
- Người đi trước (`X`) có lợi thế rõ rệt khi cả hai chơi ngẫu nhiên (thắng `59,0%` so với `28,4%` của `O`, hòa `12,6%`), do `X` có tối đa 5 lượt đi ($\binom{5}{3} = 10$ tổ hợp 3 quân) so với tối đa 4 lượt đi của `O` ($\binom{4}{3} = 4$ tổ hợp 3 quân) và luôn đi trước ở các lượt lẻ.
- Đây là lợi thế thống kê trước đối thủ ngẫu nhiên; khi cả hai chơi tối ưu (Minimax/Alpha-Beta), giá trị lý thuyết của trò chơi là hòa (`0`).

---

## 3. Bài 2 — Giải Tic-Tac-Toe bằng AND-OR Tree Search

### Kết quả trên 4 trạng thái chuẩn (`T1–T4`, lượt của `X`)

| Trạng thái | Bàn cờ | Mục tiêu (`draw_is_win`) | Nước đi đầu | Có kế hoạch? | Số nút (`COUNT`) | Thời gian (ms) |
|---|---|---|---:|---|---:|---:|
| T1 — X sắp thắng | `xo·/ox·/···` | `True` (Thắng hoặc Hòa) | `2` | Có | 22 | 0,706 |
| T1 — X sắp thắng | `xo·/ox·/···` | `False` (Chỉ Thắng) | `2` | Có | 30 | 0,866 |
| T2 — X cần hòa | `xox/·o·/···` | `True` (Thắng hoặc Hòa) | `7` | Có | 64 | 1,741 |
| T2 — X cần hòa | `xox/·o·/···` | `False` (Chỉ Thắng) | `None` | Không | 69 | 1,577 |
| T3 — Tình huống bất lợi | `o·x/···/··o` | `True` (Thắng hoặc Hòa) | `None` | Không | 155 | 4,109 |
| T3 — Tình huống bất lợi | `o·x/···/··o` | `False` (Chỉ Thắng) | `None` | Không | 147 | 4,064 |
| T4 — Bàn cờ rỗng | `···/···/···` | `True` (Thắng hoặc Hòa) | `0` | Có | 966 | 41,473 |
| T4 — Bàn cờ rỗng | `···/···/···` | `False` (Chỉ Thắng) | `None` | Không | 16.213 | 545,762 |

**Giải thích kế hoạch điều kiện (Conditional Plan):**
- **T1 (`X sắp thắng`):** `or_search` duyệt các ô trống theo thứ tự `[2, 5, 6, 7, 8]`. Ngay ở `action = 2`, mọi phản ứng của `O` trong `and_search` đều dẫn tới nhánh `X` thắng (hoặc hòa), nên thuật toán trả về ngay kế hoạch bắt đầu bằng ô `2` trước khi xét đến ô `8`.
- **T2 (`X cần hòa`):** `X` bắt buộc chọn ô `7` để chặn cột giữa `(1, 4, 7)` của `O` và bảo đảm hòa/thắng với `draw_is_win=True`. Khi `draw_is_win=False`, trả về `None` vì không thể ép thắng nếu `O` phòng thủ đúng.
- **T3 (`Bất lợi`):** `O` đã giữ hai góc đối diện `0` và `8`, luôn tạo được thế đôi (fork) bất kể `X` đi đâu; `and_or_search` trả về `None` ở cả hai chế độ.
- **T4 (`Bàn rỗng`):** Với `draw_is_win=True`, thuật toán chọn ô mở đầu `0` sau 966 nút và sinh cây kế hoạch `if-then` hoàn chỉnh đảm bảo không thua. Với `draw_is_win=False`, duyệt 16.213 nút và trả về `None` (khẳng định Tic-Tac-Toe không có chiến lược tiên thắng tuyệt đối).

### Thi đấu `and_or_player` vs. `random_player` (`SEED = 42`, 100 ván mỗi vai)

| Agent | Vai | Số ván | Thắng | Hòa | Thua | Số nước agent | Tổng thời gian (s) | TB/nước agent (ms) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| AND-OR Tree Search | X | 100 | 96 | 4 | 0 | 353 | 3,8463 | 10,896 |
| AND-OR Tree Search | O | 100 | 77 | 23 | 0 | 361 | 6,0609 | 16,789 |
| **AND-OR Tree Search (Gộp X + O)** | **X & O** | **200** | **173** | **27** | **0** | **714** | **9,9072** | **13,876** |

- Khi hai `and_or_player` đấu với nhau (`N = 1`), ván đấu kết thúc **Hòa** (`{'x': 0, 'o': 0, 'd': 1}`).

---

## 4. Bài 7 — Chơi Tic-Tac-Toe tương tác (`tictactoe_interactive.ipynb`)

Đã thực hiện và lưu biên bản đầy đủ trong notebook cho cả hai vai:
1. **Vai `X` (Human đi trước) vs. `and_or_player` (`O`):** Người chơi chiếm tâm `4`, tấn công góc `2` và cạnh `3`; tác tử `and_or_player` đáp trả chính xác ở góc `0`, chặn `6` và `5`, đưa ván cờ về kết quả **Hòa sau 9 lượt**.
2. **Vai `O` (Human đi sau) vs. `and_or_player` (`X`):** Tác tử mở góc `0`; khi người chơi đi cạnh `1` thay vì chiếm tâm `4`, tác tử lập tức lấy góc `2` rồi tâm `4` tạo thế đôi (fork) trên hai đường chéo `2-4-6` và `0-4-8`, giành **chiến thắng ở lượt 7**.
3. **Đấu với `random_player` ở cả hai vai `X` và `O`:** Người chơi thắng dễ dàng nhờ ưu tiên chiếm tâm và các ô góc.

---

## 5. Bài 8 — Connect 4 Core (`connect4_core.py`) và Thực nghiệm cơ sở

### Ước lượng không gian trạng thái và cây trò chơi Connect 4 ($6 \times 7$)

- **Không gian trạng thái (State Space):**
  - Cận trên thô: mỗi ô trong $6 \times 7 = 42$ ô có 3 giá trị (`0, 1, -1`), suy ra tối đa $3^{42} \approx 1,094 \times 10^{20}$ cấu hình.
  - Ràng buộc trọng lực (quân rơi xuống đáy cột): mỗi cột cao 6 ô chỉ có thể chứa $h \in \{0..6\}$ quân nằm liên tiếp từ đáy lên, tương ứng $\sum_{h=0}^6 2^h = 127$ cách xếp hợp lệ mỗi cột. Do đó toàn bàn có cận trên $127^7 \approx 5,329 \times 10^{14}$ trạng thái (số trạng thái hợp lệ thực tế đạt được theo lượt đi là $\approx 4,53 \times 10^{12}$).
- **Kích thước cây trò chơi (Game Tree):**
  - Hệ số phân nhánh tối đa $b = 7$ (7 cột), độ sâu tối đa $m = 42$ lượt.
  - Cận trên số lá là $7^{42} \approx 3,120 \times 10^{35}$ và tổng số nút $\frac{7^{43}-1}{6} \approx 3,64 \times 10^{35}$. Vì cây tìm kiếm quá lớn, Minimax/Alpha-Beta đầy đủ chỉ khả thi trên bàn nhỏ ($4 \times 4$) hoặc cuối ván; trên bàn chuẩn $6 \times 7$ bắt buộc dùng giới hạn độ sâu (`cutoff`) kết hợp hàm đánh giá `heuristic` hoặc Monte Carlo Search.

### Kết quả `core.play(core.random_player, core.random_player)` trên bàn $6 \times 7$ (`1.000 ván, seed = 42`)

| Tác tử | Vai | Số ván | Thắng | Hòa | Thua | Tỷ lệ thắng (%) | Số nước đã đi | Tổng thời gian (s) | TB/nước (ms) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Random (`+1` — đi trước) | `+1` | 1.000 | 564 | 1 | 435 | 56,4% | 10.887 | 0,3736 | 0,0343 |
| Random (`-1` — đi sau) | `-1` | 1.000 | 435 | 1 | 564 | 43,5% | 10.323 | 0,3465 | 0,0336 |

### Kiểm thử tự động (Unit Tests)

Toàn bộ 3 bộ unit test Connect 4 của nhóm (`tests/test_connect4_core.py`, `tests/test_connect4_search.py`, `tests/test_connect4_monte_carlo.py`) đã chạy chung với `connect4_core.py` chính thức:

```text
python -m pytest tests/ -v
33 passed in 2.77s
```

---

## 6. Bảng tổng hợp 6 chiến lược Tic-Tac-Toe (Tích hợp toàn nhóm)

| Tác tử / Thuật toán | Đối thủ | Vai | Số ván | Thắng | Hòa | Thua | Thời gian TB/nước (ms) | Nguồn |
|---|---|---|---:|---:|---:|---:|---:|---|
| **Random** | Random | X / O | 1.000 | 590 (X) | 126 | 284 (X thua) | 0,015 | Hải |
| **AND-OR Tree Search** | Random | X | 100 | 96 | 4 | 0 | 10,896 | Hải |
| **AND-OR Tree Search** | Random | O | 100 | 77 | 23 | 0 | 16,789 | Hải |
| **Alpha-Beta (Exact)** | *(Đo trên T4 bàn rỗng)* | X | — | *(Giá trị 0)* | *(18.297 nút)* | — | 1.008,932 (T4) / 363,398 (Move ordering) | Thiện |
| **Heuristic Alpha-Beta (cutoff = 2)** | Random | X | 100 | 96 | 4 | 0 | 4,644 | Thiện |
| **Heuristic Alpha-Beta (cutoff = 2)** | Random | O | 100 | 89 | 11 | 0 | 3,482 | Thiện |
| **Heuristic Alpha-Beta (cutoff = 4)** | Random | X | 100 | 96 | 4 | 0 | 31,115 | Thiện |
| **Heuristic Alpha-Beta (cutoff = 4)** | Random | O | 100 | 83 | 17 | 0 | 24,913 | Thiện |
| **Pure Monte Carlo (PMCS-10)** | Random | X | 100 | 94 | 2 | 4 | 1,123 | Ly |
| **Pure Monte Carlo (PMCS-10)** | Random | O | 100 | 74 | 8 | 18 | 1,348 | Ly |
| **Pure Monte Carlo (PMCS-100)** | Random | X | 100 | 97 | 3 | 0 | 9,487 | Ly |
| **Pure Monte Carlo (PMCS-100)** | Random | O | 100 | 90 | 6 | 4 | 8,095 | Ly |
| **UCB1 / MCTS restricted (N = 10)** | Random | X | 100 | 94 | 4 | 2 | 1,373 | Ly |
| **UCB1 / MCTS restricted (N = 10)** | Random | O | 100 | 70 | 12 | 18 | 1,616 | Ly |
| **UCB1 / MCTS restricted (N = 100)** | Random | X | 100 | 99 | 1 | 0 | 15,052 | Ly |
| **UCB1 / MCTS restricted (N = 100)** | Random | O | 100 | 87 | 6 | 7 | 12,465 | Ly |
