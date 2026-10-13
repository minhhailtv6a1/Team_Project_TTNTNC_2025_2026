# Phân công công việc - Lab 03: Tìm kiếm cục bộ

## Thành viên nhóm

| STT | Họ tên | Vai trò chính |
|---|---|---|
| 1 | Hải | Algorithm Engineer - n-Queens |
| 2 | Thiện | Optimization & Simulated Annealing Engineer |
| 3 | Ly | TSP & Integration/Experiment Lead |

## 1. Mục tiêu và sản phẩm nộp

Nhóm hoàn thiện và đánh giá các thuật toán tìm kiếm cục bộ trên mê cung, n-Queens và Traveling Salesman Problem (TSP): Hill Climbing, các biến thể Stochastic/First-choice, Random Restart và Simulated Annealing (SA).

Sản phẩm cần bàn giao:

- Hoàn thành `n_queens.ipynb` (Task 1-6) và `traveling_salesman_problem.ipynb`.
- Chạy và có nhận xét cho notebook minh hoạ mê cung, lịch làm nguội SA và Numba.
- Bảng kết quả thực nghiệm n-Queens (tối thiểu `n=4, 8`) và TSP; các thuật toán ngẫu nhiên phải chạy lặp nhiều lần.
- Ít nhất ba hình: mê cung Hill Climbing, đồ thị hội tụ n-Queens, và đồ thị lịch nhiệt hoặc tour TSP.
- Nhận xét 1-2 trang về local optimum, Random Restart, SA, thời gian chạy, khả năng mở rộng và hạn chế.
- Notebook chạy được từ đầu, có seed/cấu hình thí nghiệm và không phụ thuộc đường dẫn tuyệt đối.
- Báo cáo có trang bìa, mục lục, họ tên/mã sinh viên và mức đóng góp của từng thành viên.

## 2. Chuẩn kỹ thuật chung

- Dùng Python với `numpy`, `matplotlib`, `pandas`, `scipy`, `numba`, `ipython` khi cần; không dùng thư viện cài sẵn thuật toán search/agent hoàn chỉnh.
- Dùng chung một danh sách seed cho các phép đo, cùng ngân sách vòng lặp và cùng số lần chạy khi so sánh.
- Mỗi thuật toán n-Queens nên trả về cùng cấu trúc:

```python
{
    "solution": final_board,
    "objective": final_conflicts,
    "history": objective_per_iteration,
    "iterations": iteration_count,
    "evaluations": conflict_evaluation_count,
}
```

- Với TSP, toàn bộ thuật toán phải dùng cùng toán tử lân cận. Nhóm chọn **2-opt** (hoặc đổi sang swap nếu cả nhóm đồng ý) và ghi rõ lựa chọn trong notebook.
- Với Simulated Annealing: luôn nhận bước tốt hơn; chỉ dùng `exp(-delta / T)` với bước xấu hơn và `T > 0`.
- Với Numba: gọi `conflicts_jit()` một lần trước khi đo để không tính thời gian biên dịch JIT.

## 3. Work Breakdown Structure

| Mã | Hạng mục | Kết quả đầu ra | Phụ thuộc |
|---|---|---|---|
| W1 | Chuẩn hoá môi trường/thí nghiệm | Seed, API kết quả, cấu hình lặp và cách đo thời gian thống nhất | - |
| W2 | Minh hoạ mê cung | Animation/hình mê cung và nhận xét về local optimum | - |
| W3 | n-Queens: Hill Climbing | Steepest, stochastic all-moves, first-choice; có history/metrics | W1 |
| W4 | n-Queens: thoát cực trị cục bộ | Random Restart và Simulated Annealing; ít nhất 2 lịch nhiệt | W1, W3 |
| W5 | n-Queens: đánh giá | Bảng 100 runs, success rate, convergence plot, log-log scalability | W3, W4 |
| W6 | Benchmark Numba | So sánh O(n²), O(n), JIT và nhận xét | - |
| W7 | TSP Local Search | 5 biến thể thuật toán, benchmark và tour before/after | W1 |
| W8 | Tích hợp/nộp bài | Markdown, biểu đồ, báo cáo, Run All, HTML export | W2-W7 |

## 4. Phân công chi tiết

### Thành viên 1 - Hải: Algorithm Engineer (n-Queens)

**File phụ trách:** `n_queens.ipynb`

| Hạng mục | Công việc cụ thể | Tiêu chí hoàn thành |
|---|---|---|
| Task 1 | Cài Steepest-ascent Hill Climbing: xét mọi nước đi cục bộ, chọn trạng thái có `conflicts` thấp nhất, dừng khi không cải thiện | Có nghiệm, objective, history, số iteration/evaluations; test được n=4 và n=8 |
| Task 2 | Cài Inefficient Stochastic: liệt kê toàn bộ nước đi tốt hơn, chọn ngẫu nhiên một nước | Có đếm chi phí đánh giá hàm mục tiêu để so sánh với Task 3 |
| Task 3 | Cài Efficient/First-choice Stochastic: sinh một hàng xóm ngẫu nhiên mỗi lần, nhận nếu tốt hơn, dừng theo số lần thử không cải thiện | Có giải thích tiêu chí dừng và giới hạn vòng lặp |
| Bàn giao | Viết Markdown giải thích thiết kế, ví dụ kết quả cho n=4/8, hướng dẫn cách gọi hàm | Các thuật toán chạy độc lập và theo API chung |

### Thành viên 2 - Thiện: Optimization & Simulated Annealing Engineer

**File phụ trách:** `n_queens.ipynb`, `Simulated_Annealing_Schedules.ipynb`, `n_queens_fast_conflict_calculation_with_numba.ipynb`

| Hạng mục | Công việc cụ thể | Tiêu chí hoàn thành |
|---|---|---|
| Task 4 | Viết Random Restart cho ba biến thể Hill Climbing, tối đa 100 restart | Lưu best objective, số restart thực tế, success rate |
| Task 5 | Cài SA n-Queens, lưu history và khảo sát ít nhất 2 lịch giảm nhiệt | Có đồ thị conflicts theo iteration và nhận xét ảnh hưởng của `T0`, `alpha`/`eta` |
| Lịch nhiệt | Chạy/ghi nhận xét exponential, linear, fast và logarithmic | Có biểu đồ so sánh và chọn lịch dùng cho SA |
| Numba | Xác minh ba hàm conflict cho cùng đầu vào; benchmark O(n²), O(n), JIT sau warm-up | Có biểu đồ thời gian và giải thích sự khác nhau giữa độ phức tạp/JIT |
| Bàn giao | Chốt hàm SA theo API chung, nêu rõ default parameters | Có thể được Thành viên 3 gọi trực tiếp khi chạy Task 6 |

### Thành viên 3 - Ly: TSP & Integration/Experiment Lead

**File phụ trách:** `traveling_salesman_problem.ipynb`, Task 6 của `n_queens.ipynb`, báo cáo/HTML xuất cuối

| Hạng mục | Công việc cụ thể | Tiêu chí hoàn thành |
|---|---|---|
| TSP | Cài Steepest-ascent, Random Restart, Stochastic, First-choice và SA | Tất cả dùng cùng toán tử 2-opt/swap đã chốt |
| TSP benchmark | So sánh runtime, kích thước TSP, best tour length và mức cải thiện tương đối | Có bảng kết quả và hình tour trước/sau tối ưu |
| Task 6 n-Queens | Chạy ít nhất 100 lần/thuật toán cho n=4,8; tổng hợp average runtime, conflicts, success rate | Hoàn thành bảng trong notebook |
| Phân tích mở rộng | Vẽ convergence cho mỗi thuật toán; chạy tối thiểu 2 thuật toán ở n=4,8,12,16,20 và vẽ log-log runtime | Có nhận xét plateau/local optimum và độ phức tạp thực nghiệm |
| Tích hợp | Thu nhận thay đổi của A/B, rà soát Markdown, kiểm tra Run All, xuất HTML và biên soạn báo cáo | Không lỗi cell, đủ hình/bảng, có thông tin đóng góp |

## 5. Trình tự phối hợp

1. Cả nhóm chốt W1: định dạng API, seed list, `max_iterations`, số lần chạy và toán tử TSP.
2. Hải và Thiện làm song song các thuật toán n-Queens nhưng không sửa cùng một cell/notebook trên cùng branch.
3. Ly xây phần TSP song song; sau khi Hải/Thiện bàn giao API, thực hiện Task 6 và tổng hợp số liệu n-Queens.
4. Cả nhóm review kết quả: kiểm tra nghiệm hợp lệ, cùng seed/config, biểu đồ có nhãn/trục/đơn vị.
5. Ly tích hợp; cả nhóm chạy lại notebook từ Kernel mới trước khi export.

## 6. Quy tắc Git và notebook

- Mỗi người làm trên branch riêng: `feature/nqueens-hillclimb`, `feature/nqueens-sa-numba`, `feature/tsp-integration`.
- Commit nhỏ, theo một chức năng; không commit cell debug hoặc output quá lớn.
- Không đồng thời chỉnh cùng một file `.ipynb`. Nếu bắt buộc, phân vùng cell và merge theo thứ tự đã thống nhất.
- Trước khi merge: Restart Kernel -> Run All -> kiểm tra bảng và hình được tạo lại.
- Chỉ export HTML sau khi đã kiểm tra đầu ra; giữ output cuối vì đề yêu cầu notebook được render kèm hình.

## 7. Checklist trước khi nộp

- [ ] `n_queens.ipynb` hoàn thành Task 1-6.
- [ ] `traveling_salesman_problem.ipynb` hoàn thành các thuật toán và benchmark.
- [ ] Có bảng kết quả n-Queens và TSP.
- [ ] Có tối thiểu 3 hình minh hoạ bắt buộc.
- [ ] Có thảo luận local optimum, Random Restart, SA, lịch nhiệt, độ phức tạp và khả năng mở rộng.
- [ ] Seed, tham số và đơn vị thời gian được ghi rõ.
- [ ] Numba được warm-up trước phép đo.
- [ ] Restart Kernel -> Run All không lỗi.
- [ ] Đã export HTML và hoàn thành báo cáo có mức đóng góp từng thành viên.
