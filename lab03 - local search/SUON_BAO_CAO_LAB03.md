# Sườn báo cáo - Lab 03: Tìm kiếm cục bộ

> Mục đích: Dùng file này làm khung chung để viết báo cáo. Mỗi **Bài** trong đề được tổ chức thành một **chương**. Mỗi người phụ trách viết phần chương được phân công, đồng thời cung cấp mã nguồn, bảng số liệu và hình minh hoạ tương ứng.

## Phân chia 8 bài cho 3 thành viên

| Thành viên | Các chương/bài phụ trách | Phạm vi đóng góp |
|---|---|---|
| **Hải** | Chương 1 (Bài 1), Chương 2 (Bài 2), Chương 3 (Bài 3) | Mê cung, mô hình n-Queens và ba biến thể Hill Climbing cơ bản |
| **Thiện** | Chương 4 (Bài 4), Chương 5 (Bài 5), Chương 6 (Bài 6) | Random Restart, Simulated Annealing, lịch nhiệt và tối ưu Numba |
| **Ly** | Chương 7 (Bài 7), Chương 8 (Bài 8) | TSP, tổng hợp thực nghiệm, biểu đồ so sánh và tích hợp báo cáo |

## Thành phần đầu báo cáo

### Trang bìa

- Tên trường/khoa/môn học.
- Tên đồ án: **Lab 03 - Tìm kiếm cục bộ (Local Search)**.
- Tên giảng viên.
- Danh sách thành viên: Hải, Thiện, Ly; mã số sinh viên; lớp/nhóm.
- Thời gian nộp.

### Mức đóng góp của thành viên

| Thành viên | Nội dung phụ trách | Tỷ lệ đóng góp |
|---|---|---|
| Hải | Chương 1-3; thuật toán Hill Climbing n-Queens | ...% |
| Thiện | Chương 4-6; SA, lịch nhiệt, benchmark Numba | ...% |
| Ly | Chương 7-8; TSP, thực nghiệm tổng hợp, tích hợp báo cáo | ...% |

> Điền tỷ lệ sao cho tổng bằng 100% và phản ánh đúng đóng góp thực tế.

### Mục lục

Tạo tự động sau khi hoàn thành nội dung và đánh số hình/bảng/công thức nhất quán.

### Tóm tắt báo cáo

Viết khoảng 1/2 trang: nêu mục tiêu khảo sát Local Search, bài toán dùng để thực nghiệm, thuật toán so sánh, tiêu chí đánh giá và kết luận nổi bật.

---

# Chương 1. Bài 1 - Tìm kiếm cục bộ trên mê cung: Simple Hill Climbing

**Phụ trách: Hải**  
**Notebook liên quan:** `Maze_Example_LocalSearch.ipynb`

## 1.1. Mục tiêu

- Trình bày cách áp dụng Simple Hill Climbing để tìm đường trong mê cung.
- Quan sát tình huống thuật toán dừng tại local optimum trước khi đến đích.

## 1.2. Mô hình bài toán

- Mô tả trạng thái: vị trí hiện tại trong mê cung.
- Mô tả trạng thái đầu `S`, trạng thái đích `G`, vật cản và tập lân cận N/E/S/W.
- Hàm heuristic Manhattan:

\[
h(n) = |r_n-r_G| + |c_n-c_G|
\]

## 1.3. Thuật toán và cài đặt

- Giải thích `expand(maze, pos)`, thứ tự duyệt hướng và cơ chế chọn hàng xóm tốt nhất.
- Trình bày điều kiện dừng: không có hàng xóm nào làm giảm Manhattan distance.
- Nêu cấu hình `ORDER` và `RANDOMIZATION`.

## 1.4. Kết quả và minh hoạ

- **Hình 1:** Mê cung hoặc ảnh animation tại các bước đi chính.
- Bảng nhỏ: vị trí dừng, heuristic tại vị trí dừng, heuristic tại đích.
- Thử ít nhất hai thứ tự duyệt hướng hoặc chế độ ngẫu nhiên.

## 1.5. Nhận xét

- Giải thích local optimum, plateau hoặc ridge trong ví dụ mê cung.
- Nhận xét tại sao đổi thứ tự hướng có thể làm thay đổi đường đi/kết quả.

---

# Chương 2. Bài 2 - Mô hình hoá bài toán n-Queens

**Phụ trách: Hải**  
**Notebook liên quan:** `n_queens.ipynb`

## 2.1. Phát biểu bài toán

- Mục tiêu: đặt n quân hậu sao cho không quân nào tấn công nhau.
- Mô tả ràng buộc: mỗi cột có đúng một quân hậu.

## 2.2. Biểu diễn trạng thái và hàm mục tiêu

- Biểu diễn board bằng vector `board[i] = hàng của quân hậu ở cột i`.
- Hàm mục tiêu: số cặp quân hậu xung đột, cần tối thiểu hoá.

\[
f(board) = conflicts(board)
\]

- Nghiệm hợp lệ khi `conflicts(board) = 0`.

## 2.3. Phép di chuyển cục bộ

- Di chuyển một quân hậu sang một hàng khác trong cùng cột.
- Nêu số lượng hàng xóm: `n × (n - 1)`.

## 2.4. Minh hoạ đầu vào

- Minh hoạ một random board cho `n=4` và `n=8`.
- So sánh với nghiệm mẫu `[1, 3, 0, 2]` của n=4.
- Giải thích hàm `random_board`, `show_board`, `conflicts`.

## 2.5. Nhận xét

- Lý do biểu diễn một hậu/cột thu hẹp không gian tìm kiếm.
- Mối liên hệ giữa xung đột hàng, đường chéo và hàm mục tiêu.

---

# Chương 3. Bài 3 - Steepest-ascent và Stochastic Hill Climbing cho n-Queens

**Phụ trách: Hải**  
**Notebook liên quan:** `n_queens.ipynb` - Task 1, 2, 3

## 3.1. Steepest-ascent Hill Climbing

- Pseudocode/luồng xử lý: đánh giá mọi hàng xóm, chọn hàng xóm cải thiện tốt nhất, dừng khi không còn cải thiện.
- Nêu ưu điểm và chi phí: chất lượng bước đi tốt nhưng phải đánh giá nhiều hàng xóm.

## 3.2. Inefficient Stochastic Hill Climbing

- Liệt kê toàn bộ bước cải thiện, sau đó chọn ngẫu nhiên một bước.
- Phân tích khác biệt với Steepest-ascent về chất lượng bước đi và số lần đánh giá `conflicts()`.

## 3.3. Efficient Stochastic / First-choice Hill Climbing

- Sinh một hàng xóm ngẫu nhiên; nhận nếu tốt hơn.
- Nêu `max_non_improving_trials` và lý do chọn giá trị này.
- Giải thích đánh đổi: rẻ hơn mỗi iteration nhưng khó khẳng định đã ở local optimum.

## 3.4. Kết quả sơ bộ

- Bảng: thuật toán, n, `f` ban đầu/cuối, iterations, evaluations, runtime.
- Một ví dụ run cho n=4 và n=8.

## 3.5. Nhận xét

- So sánh ba thuật toán theo chi phí tính toán và mức độ dễ mắc kẹt.
- Dẫn sang nhu cầu Random Restart và SA.

---

# Chương 4. Bài 4 - Random Restart và Simulated Annealing cho n-Queens

**Phụ trách: Thiện**  
**Notebook liên quan:** `n_queens.ipynb` - Task 4, 5

## 4.1. Random Restart Hill Climbing

- Mô tả quy trình khởi tạo ngẫu nhiên và chạy lại tối đa 100 lần.
- Nêu cách lưu nghiệm tốt nhất, số restart và success rate.
- So sánh Random Restart cho các biến thể Hill Climbing.

## 4.2. Simulated Annealing

- Mô tả một bước chuyển ngẫu nhiên và biến thiên mục tiêu:

\[
\Delta = f(new) - f(current)
\]

- Quy tắc nhận: luôn nhận nếu `Δ < 0`; nếu `Δ > 0`, nhận với xác suất:

\[
p = \exp(-\Delta/T)
\]

- Nêu điều kiện dừng, số iteration tối đa và seed.

## 4.3. Thí nghiệm tham số

- Khảo sát `T0`, tốc độ làm nguội và ít nhất hai cooling schedules.
- **Hình 2:** Đồ thị `conflicts` theo iteration cho một lần chạy SA.

## 4.4. Kết quả

- Bảng: cấu hình, n, success rate, best/average final conflicts, runtime, số restart hoặc iteration.

## 4.5. Nhận xét

- Vì sao SA thoát local optimum.
- Khi nào nhiệt độ cao/thấp làm giảm hiệu quả.
- So sánh SA và Random Restart.

---

# Chương 5. Bài 5 - Khảo sát lịch giảm nhiệt độ

**Phụ trách: Thiện**  
**Notebook liên quan:** `Simulated_Annealing_Schedules.ipynb`

## 5.1. Các lịch nhiệt độ khảo sát

- Exponential: `T(t) = T0 × alpha^t`.
- Linear: `T(t) = T0 - eta × t`.
- Fast: `T(t) = T0 / (1 + t)`.
- Logarithmic: `T(t) = T0 / ln(1 + t)`, với `t > 0`.

## 5.2. Thiết lập so sánh

- Giữ cùng `T0` và cùng khoảng thời gian khi vẽ đồ thị.
- Thay đổi `alpha`, `eta`, `T0`; ghi rõ các giá trị dùng trong thí nghiệm.

## 5.3. Kết quả

- **Hình 3:** Đồ thị chuẩn hoá `T(t)/T0` của bốn lịch nhiệt.
- Bảng: lịch nhiệt, tham số, final conflicts, success rate, runtime của SA n-Queens.

## 5.4. Nhận xét

- Lịch nào giữ khả năng chấp nhận bước xấu lâu hơn.
- Đánh đổi giữa thăm dò (exploration), khai thác (exploitation) và thời gian chạy.
- Chọn lịch nhiệt chính thức dùng cho thí nghiệm trong Chương 8.

---

# Chương 6. Bài 6 - Tối ưu hàm đếm xung đột bằng Numba

**Phụ trách: Thiện**  
**Notebook liên quan:** `n_queens_fast_conflict_calculation_with_numba.ipynb`

## 6.1. Ba cách tính conflicts

- `conflicts_naive()`: so sánh theo cách O(n²).
- `conflicts()`: đếm quân hậu theo hàng/đường chéo, O(n).
- `conflicts_jit()`: bản O(n) được JIT bằng Numba.

## 6.2. Cơ sở tối ưu

- Dùng công thức số cặp xung đột trong cùng hàng/đường chéo:

\[
C(k,2) = k(k-1)/2
\]

- Giải thích vì sao đếm tần suất giúp tránh so sánh từng cặp quân hậu.

## 6.3. Thiết lập đo thời gian

- Dùng nhiều kích thước board và số lần lặp cố định.
- Gọi trước `conflicts_jit()` để warm-up JIT.
- Không gộp thời gian biên dịch lần đầu vào benchmark.

## 6.4. Kết quả

- **Hình 4:** Runtime theo kích thước board cho ba cách tính.
- Bảng: n, naive, linear, JIT runtime và speedup.

## 6.5. Nhận xét

- Phân biệt lợi ích do độ phức tạp O(n) với lợi ích do JIT.
- Nêu khi nào JIT có overhead và khi nào lợi ích rõ rệt.

---

# Chương 7. Bài 7 - Local Search cho Traveling Salesman Problem

**Phụ trách: Ly**  
**Notebook liên quan:** `traveling_salesman_problem.ipynb`

## 7.1. Phát biểu và mô hình bài toán

- Trạng thái là hoán vị thứ tự các thành phố.
- Hàm mục tiêu là tổng chiều dài tour khép kín.
- Trình bày `random_tsp`, `random_tour`, `tour_length`, `show_tsp`.

## 7.2. Toán tử lân cận

- Mô tả rõ toán tử **2-opt** (hoặc swap nếu nhóm chọn swap).
- Giải thích vì sao phải giữ cùng toán tử cho mọi thuật toán.
- Nêu số hàng xóm và ảnh hưởng đến chi phí tính toán.

## 7.3. Các thuật toán cài đặt

- Steepest-ascent Hill Climbing.
- Random Restart.
- Stochastic Hill Climbing.
- First-choice Hill Climbing.
- Simulated Annealing.

## 7.4. Thực nghiệm và trực quan hoá

- Chọn các kích thước TSP; ghi rõ số thành phố, seed, số runs và ngân sách iteration.
- **Hình 5:** Tour trước và sau tối ưu của một cấu hình đại diện.
- Bảng: thuật toán, số thành phố, initial/best tour length, mức cải thiện tương đối, runtime.

## 7.5. Nhận xét

- So sánh khả năng tìm tour ngắn và chi phí tính toán.
- Phân tích ảnh hưởng của kích thước bài toán và toán tử lân cận.

---

# Chương 8. Bài 8 - Tổng hợp thí nghiệm và phân tích

**Phụ trách: Ly; Hải và Thiện kiểm tra số liệu phần mình**  
**Notebook liên quan:** `n_queens.ipynb` - Task 6; `traveling_salesman_problem.ipynb`

## 8.1. Thiết kế thực nghiệm chung

- Nêu môi trường chạy, phiên bản Python/thư viện (nếu có), seed, số lần lặp, ngân sách iteration và cách đo runtime.
- Nhấn mạnh tính công bằng: cùng điều kiện đầu vào/cùng seed list khi so sánh.

## 8.2. Bảng tổng hợp n-Queens

Chạy tối thiểu 100 lần với n=4, 8.

| Algorithm | Board size | Avg. runtime | Avg. conflicts | Success rate | Avg. iterations | Avg. evaluations |
|---|---:|---:|---:|---:|---:|---:|
| Steepest-ascent | 4 | | | | | |
| Inefficient Stochastic | 4 | | | | | |
| Efficient Stochastic | 4 | | | | | |
| Random Restart | 4 / 8 | | | | | |
| Simulated Annealing | 4 / 8 | | | | | |

## 8.3. Phân tích hội tụ

- **Hình 6:** Đồ thị `f(board)` theo iteration của mỗi thuật toán trên n=8.
- Nhận xét giai đoạn cải thiện nhanh, plateau, local optimum và sự khác biệt khi có Random Restart/SA.

## 8.4. Khả năng mở rộng n-Queens

- Chọn ít nhất hai thuật toán, chạy `n = 4, 8, 12, 16, 20`.
- **Hình 7:** Đồ thị log-log runtime theo n.
- Ước lượng độ phức tạp thực nghiệm và nêu thuật toán phù hợp hơn khi n lớn.

## 8.5. Tổng hợp kết quả TSP

| Algorithm | Number of cities | Initial length | Best length | Improvement (%) | Runtime | Runs |
|---|---:|---:|---:|---:|---:|---:|
| Steepest-ascent | | | | | | |
| Random Restart | | | | | | |
| Stochastic | | | | | | |
| First-choice | | | | | | |
| Simulated Annealing | | | | | | |

## 8.6. Thảo luận chung

Trả lời ngắn gọn các điểm sau:

1. Local Search khác BFS/A* thế nào về mục tiêu, bộ nhớ và trạng thái cần lưu?
2. Vì sao Hill Climbing mắc local optimum, plateau hoặc ridge?
3. Đánh đổi giữa Steepest, Stochastic all-moves và First-choice theo số lần đánh giá hàm mục tiêu là gì?
4. Random Restart cải thiện xác suất thành công thế nào, và khi nào tăng restart không còn hiệu quả?
5. Nhiệt độ trong SA ảnh hưởng exploration/exploitation ra sao?
6. 2-opt so với swap thay đổi chất lượng tour và số hàng xóm như thế nào?

---

# Kết luận

- Tóm tắt thuật toán cho hiệu quả tốt nhất cho n-Queens và TSP theo số liệu thực nghiệm.
- Tóm tắt đánh đổi giữa chất lượng nghiệm, thời gian chạy, tính ổn định và khả năng mở rộng.
- Nêu hạn chế: số lần chạy hữu hạn, phụ thuộc tham số/seed/lịch nhiệt, dữ liệu TSP ngẫu nhiên.
- Nêu hướng phát triển: toán tử di chuyển thích nghi cho n-Queens, 2-opt nâng cao, Genetic Algorithm (bonus).

# Tài liệu tham khảo

- Tài liệu Lab 03 - Tìm kiếm cục bộ.
- Tài liệu/tham khảo về Simulated Annealing được trích trong notebook `Simulated_Annealing_Schedules.ipynb`.
- Các thư viện/nguồn khác nếu nhóm sử dụng.

# Phụ lục (nếu cần)

- Tham số đầy đủ của các phép chạy.
- Bảng số liệu thô của 100 runs.
- Liên kết repository hoặc notebook HTML đã render.
