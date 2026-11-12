# Lab 05 — Tìm kiếm đối kháng và trò chơi (Adversarial Search and Games)

Dự án thực hành môn **Trí tuệ nhân tạo nâng cao (Lab 05)**: mô hình hóa trò chơi hai người tổng bằng không, cài đặt và thực nghiệm các thuật toán **AND-OR Tree Search**, **Minimax**, **Alpha-Beta Pruning (với Move Ordering)**, **Heuristic Alpha-Beta với giới hạn độ sâu (Cutoff)**, **Pure Monte Carlo Search (PMCS)** và **Monte Carlo Tree Search với chính sách chọn UCB1** trên hai trò chơi **Tic-Tac-Toe** (Bài 1–7) và **Connect 4** (Bài 8 mở rộng).

---

## 1. Cấu trúc thư mục dự án

```text
lab05 - game/
├── tictactoe.py                                         # Module nền tảng Tic-Tac-Toe (state, actions, result, terminal, utility, play)
├── tictactoe_definitions.ipynb                          # Bài 1: Định nghĩa Tic-Tac-Toe & thực nghiệm Random vs Random (1.000 ván)
├── tictactoe_and_or_tree_search.ipynb                   # Bài 2: Giải Tic-Tac-Toe bằng AND-OR Tree Search (T1–T4 & đấu Random)
├── tictactoe_alpha_beta_tree_search.ipynb               # Bài 3: Minimax, cắt tỉa Alpha-Beta và Move Ordering
├── tictactoe_heuristic_alpha_beta_tree_search.ipynb     # Bài 4: Heuristic Alpha-Beta với giới hạn độ sâu (cutoff = 2, 4, full)
├── tictactoe_pure_monte_carlo_search.ipynb              # Bài 5: Pure Monte Carlo Search (N = 10, 100, 1000)
├── tictactoe_monte_carlo_tree_search_restricted.ipynb   # Bài 6: Monte Carlo Tree Search với UCB1 ở độ sâu 1 (N = 10, 100)
├── tictactoe_interactive.ipynb                          # Bài 7: Chơi Tic-Tac-Toe tương tác (cả 2 vai X và O) & biên bản ván đấu
├── connect4_core.py                                     # Bài 8 (Core): Luật Connect 4, trọng lực, terminal/utility, Random & play()
├── connect4_search.py                                   # Bài 8 (Search): Full Alpha-Beta, Move Ordering, Heuristic & Cutoff
├── connect4_monte_carlo.py                              # Bài 8 (Monte Carlo): Playout, PMCS & PureMonteCarloAgent
├── assignment_connect4.ipynb                            # Bài 8 (Notebook tích hợp): Toàn bộ Task 1–5 của Connect 4
├── tests/
│   ├── test_connect4_core.py                            # Unit tests cho connect4_core.py
│   ├── test_connect4_search.py                          # Unit tests cho connect4_search.py
│   └── test_connect4_monte_carlo.py                     # Unit tests cho connect4_monte_carlo.py
├── results/
│   ├── hai_results.md                                   # Số liệu thực nghiệm của Hải (Bài 1, 2, 7, Connect 4 Core & Bảng tổng hợp)
│   ├── thien_results.md                                 # Số liệu thực nghiệm của Thiện (Bài 3, 4 & Connect 4 Search)
│   └── ly_results.md                                    # Số liệu thực nghiệm của Ly (Bài 5, 6 & Connect 4 Monte Carlo)
├── BAO_CAO_KET_QUA.md                                   # Báo cáo tổng hợp và trả lời các câu hỏi thảo luận
├── PHAN_CONG_LAB05.md                                   # Tài liệu phân công nhiệm vụ, API contract và quy ước thực nghiệm
└── README.md                                            # Hướng dẫn cài đặt, chạy thực nghiệm và tái lập kết quả
```

---

## 2. Yêu cầu môi trường và cài đặt

- **Python:** `>= 3.10` (đã kiểm thử trên Python `3.13` và `3.14`).
- **Thư viện cần thiết:** `numpy`, `pandas`, `matplotlib`, `jupyter`, `nbconvert`, `ipykernel`, `pytest`.

Cài đặt nhanh các gói phụ thuộc:

```bash
pip install numpy pandas matplotlib jupyter nbconvert ipykernel pytest
```

---

## 3. Hướng dẫn chạy kiểm thử (Unit Tests) và tái lập kết quả

Từ thư mục `lab05 - game`, chạy toàn bộ bộ kiểm thử tự động cho 3 module Connect 4 (`connect4_core.py`, `connect4_search.py`, `connect4_monte_carlo.py`):

```bash
python -m pytest tests/ -v
```

Kết quả mong đợi: **`33 passed`** (bao gồm kiểm tra bàn cờ nhiều kích thước, luật rơi quân theo trọng lực, thắng ngang/dọc/2 đường chéo, hòa, không làm thay đổi bàn cờ đầu vào, Alpha-Beta, Heuristic cutoff và phân bổ ngân sách PMCS).

### Chạy lại các Notebook từ Kernel mới

Tất cả các notebook trong dự án sử dụng `SEED = 42` để đảm bảo tính tái lập của số nút duyệt, giá trị tối ưu và kết quả thắng/hòa/thua. Có thể mở trực tiếp trong **JupyterLab / VS Code** hoặc thực thi tự động bằng `nbconvert`:

```bash
# Nhóm Bài 1, 2, 7 (Hải phụ trách)
python -m jupyter nbconvert --to notebook --execute --inplace tictactoe_definitions.ipynb tictactoe_and_or_tree_search.ipynb tictactoe_interactive.ipynb

# Nhóm Bài 3, 4 (Thiện phụ trách)
python -m jupyter nbconvert --to notebook --execute --inplace tictactoe_alpha_beta_tree_search.ipynb tictactoe_heuristic_alpha_beta_tree_search.ipynb

# Nhóm Bài 5, 6 và Bài 8 Connect 4 (Ly phụ trách)
python -m jupyter nbconvert --to notebook --execute --inplace tictactoe_pure_monte_carlo_search.ipynb tictactoe_monte_carlo_tree_search_restricted.ipynb assignment_connect4.ipynb
```

> **Lưu ý với `tictactoe_interactive.ipynb` (Bài 7):** Khi chạy tự động toàn bộ notebook (`Run All`), hàm `interactive_player()` sử dụng kịch bản nước đi mẫu (`SCRIPTED_MOVES`) để tạo biên bản ván đấu ở cả vai `X` và `O`. Để tự nhập nước đi từ bàn phím (`0..8`, hoặc `-1` để thoát), chỉ cần đặt `SCRIPTED_MOVES = []` trước khi gọi `play(interactive_player, ...)`.

---

## 4. Tóm tắt kết quả thực nghiệm chính và thảo luận

### Bảng tổng hợp các chiến lược trên Tic-Tac-Toe (`SEED = 42`)

| Tác tử / Thuật toán | Đối thủ | Vai | Số ván | Thắng | Hòa | Thua | Thời gian TB/nước (ms) |
|---|---|---|---:|---:|---:|---:|---:|
| **Random** | Random | X / O | 1.000 | 590 (X) | 126 | 284 (O thắng) | 0,015 |
| **AND-OR Tree Search** | Random | X | 100 | 96 | 4 | 0 | 10,896 |
| **AND-OR Tree Search** | Random | O | 100 | 77 | 23 | 0 | 16,789 |
| **Alpha-Beta (Exact)** | *(Trên T4 bàn rỗng)* | X | — | *(Value = 0)* | *(18.297 nút)* | — | 1.008,932 (Off) / 363,398 (On) |
| **Heuristic Alpha-Beta (`cutoff=2`)** | Random | X | 100 | 96 | 4 | 0 | 4,644 |
| **Heuristic Alpha-Beta (`cutoff=2`)** | Random | O | 100 | 89 | 11 | 0 | 3,482 |
| **Heuristic Alpha-Beta (`cutoff=4`)** | Random | X | 100 | 96 | 4 | 0 | 31,115 |
| **Heuristic Alpha-Beta (`cutoff=4`)** | Random | O | 100 | 83 | 17 | 0 | 24,913 |
| **Pure Monte Carlo (`PMCS-10`)** | Random | X / O | 100 / vai | 94 (X) / 74 (O) | 2 / 8 | 4 / 18 | 1,123 (X) / 1,348 (O) |
| **Pure Monte Carlo (`PMCS-100`)** | Random | X / O | 100 / vai | 97 (X) / 90 (O) | 3 / 6 | 0 / 4 | 9,487 (X) / 8,095 (O) |
| **UCB1 / MCTS (`N=10`)** | Random | X / O | 100 / vai | 94 (X) / 70 (O) | 4 / 12 | 2 / 18 | 1,373 (X) / 1,616 (O) |
| **UCB1 / MCTS (`N=100`)** | Random | X / O | 100 / vai | 99 (X) / 87 (O) | 1 / 6 | 0 / 7 | 15,052 (X) / 12,465 (O) |

### Trả lời tóm tắt 6 câu hỏi thảo luận

1. **Minimax khác AND-OR Search ở cách mô hình hóa đối thủ như thế nào?**  
   AND-OR Search xem đối thủ như sự không xác định của môi trường và chỉ kiểm tra tính khả thỏa nhị phân (mọi phản ứng ở nút AND đều dẫn tới mục tiêu `win`/`draw`), dừng ngay ở nhánh thỏa mãn đầu tiên. Minimax gán giá trị lợi ích định lượng (`+1, 0, -1`) và giả định đối thủ (Min) luôn chọn nước tối thiểu hóa lợi ích của Max, từ đó chọn nước tối ưu hóa giá trị kỳ vọng xấu nhất.
2. **Alpha-Beta có làm thay đổi nước đi tối ưu của Minimax không? Vì sao?**  
   Không làm thay đổi giá trị Minimax cũng như tập nước đi tối ưu, vì cắt tỉa Alpha-Beta chỉ loại bỏ các nhánh con chắc chắn không thể cải thiện cận $\alpha$ hoặc $\beta$ đã tìm được. Trên bàn rỗng Tic-Tac-Toe (`T4`), Alpha-Beta giảm số nút từ `549.946` xuống `18.297` (giảm `96,7%`) và còn `7.275` nút khi kết hợp ưu tiên ô trung tâm $\rightarrow$ góc $\rightarrow$ cạnh.
3. **Khi nào cần dùng heuristic và cutoff thay vì tìm kiếm tới trạng thái kết thúc?**  
   Khi độ sâu $m$ và hệ số phân nhánh $b$ lớn làm số nút $O(b^m)$ bùng nổ theo hàm mũ (như Connect 4 chuẩn $6 \times 7$ với $b \le 7, m = 42$). Giới hạn độ sâu `cutoff` kết hợp hàm `evaluate` giúp đưa thời gian suy nghĩ mỗi nước về mức mili-giây thực tế.
4. **Pure Monte Carlo Search có ưu điểm gì so với heuristic search? Hạn chế chính là gì?**  
   *Ưu điểm:* Không cần thiết kế hàm đánh giá heuristic đặc thù theo miền bài toán; chỉ cần luật trò chơi để mô phỏng ngẫu nhiên (`playout`). *Hạn chế:* Chia đều ngân sách cho mọi nước đi (kể cả nước rất tệ), phương sai cao khi `N` nhỏ và giả định đối thủ đi ngẫu nhiên trong rollout nên dễ bỏ sót bẫy chiến thuật bắt buộc.
5. **UCB1 cải thiện việc phân bổ số lần mô phỏng so với chia đều playout như thế nào?**  
   UCB1 cân bằng giữa **khai thác (exploitation)** các nước đi đang có tỷ lệ thắng trung bình cao và **khám phá (exploration)** các nước đi ít được thử thông qua số hạng $\sqrt{\frac{2 \ln N}{n_i}}$, giúp tập trung ngân sách mô phỏng vào các nhánh hứa hẹn hơn thay vì lãng phí đồng đều.
6. **Trong Connect 4 và Dots and Boxes, yếu tố nào làm không gian tìm kiếm tăng nhanh nhất?**  
   Đó là tích số giữa **độ sâu ván đấu tối đa $m$** (số ô/cạnh có thể đi) và **hệ số phân nhánh $b$** ở mỗi lượt, khiến kích thước cây trò chơi tăng theo hàm mũ $O(b^m)$ (trong Connect 4 $6 \times 7$ là $7^{42} \approx 3,12 \times 10^{35}$).

Chi tiết đầy đủ về số liệu và phân tích được trình bày trong `results/hai_results.md`, `results/thien_results.md`, `results/ly_results.md` và `BAO_CAO_KET_QUA.md`.
