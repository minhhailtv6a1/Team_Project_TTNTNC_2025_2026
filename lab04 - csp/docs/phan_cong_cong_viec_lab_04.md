# Phân công công việc Lab 04 - Bài toán thỏa mãn ràng buộc

## 1. Mục tiêu và phạm vi

Hoàn thành đầy đủ **8 bài** trong đề Lab 04 trên hai notebook:

- `CSP_graph_coloring_example.ipynb`: Bài 1 đến Bài 4 - CSP tô màu đồ thị.
- `n_queens.ipynb`: Bài 5 đến Bài 8 - tìm kiếm cục bộ cho n-Queens.

Sản phẩm cuối phải có:

1. Hai notebook đã điền đủ mã, giải thích bằng Markdown và giữ lại kết quả chạy.
2. Bảng thí nghiệm tô màu đồ thị với 3/4 màu, nhiều kích thước và nhiều seed.
3. Bảng thí nghiệm n-Queens với `n = 4` và `n = 8`, tối thiểu 100 lượt cho mỗi thiết lập.
4. Tối thiểu bốn hình để đáp ứng chắc chắn yêu cầu: một đồ thị đã tô màu, một bàn cờ n-Queens, một biểu đồ hội tụ và một biểu đồ log-log thời gian chạy.
5. Nhận xét về tính hợp lệ, hiệu năng, trường hợp thất bại và hạn chế thí nghiệm.
6. Thông tin nhóm, môi trường, thư viện và khả năng chạy lại từ đầu mà không dùng đường dẫn cá nhân.

Phần Advanced task của n-Queens là **tùy chọn**; chỉ thực hiện sau khi tám bài bắt buộc đã hoàn thành và kiểm thử.

## 2. Hiện trạng dự án

### Notebook tô màu đồ thị

Đã có:

- Sinh đồ thị phẳng bằng Delaunay với `n = 10`, seed `1111`.
- Tạo `variables`, `domains`, `constraints` và danh sách láng giềng.
- Hàm `complete()`, `consistent()` và Backtracking cơ bản.
- Mã trực quan hóa đồ thị và kết quả tô màu.

Còn thiếu:

- Các ca kiểm thử có kết quả mong đợi và phần giải thích CSP.
- MRV, LCV, Forward Checking và cơ chế hoàn tác miền.
- Min-Conflicts.
- Bộ chạy thí nghiệm nhiều `n`, nhiều seed, 3/4 màu và bảng so sánh.

### Notebook n-Queens

Đã có:

- `random_board(n)`, `conflicts(board)`, `show_board(board)`.
- Ví dụ bàn cờ `[1, 3, 0, 2]`.

Còn thiếu:

- Toàn bộ mã ở Task 1 đến Task 6.
- Ba biến thể Hill Climbing, Random Restart và Simulated Annealing.
- Đo thời gian, số bước, số lần đánh giá, lịch sử hội tụ và tỷ lệ thành công.
- Bảng 100 lượt, biểu đồ hội tụ và biểu đồ log-log.
- Cell đổi thư mục Google Drive hiện tại cần được bỏ hoặc sửa để notebook không phụ thuộc đường dẫn cá nhân.

## 3. Nguyên tắc phân chia

- Phân theo cụm chức năng để một người sở hữu một mảng mã tương đối độc lập.
- Cân bằng theo độ khó, không chỉ theo số bài: Bài 4, 6, 7 và 8 nặng hơn các bài mô hình hóa.
- Mỗi bài có đúng một người chịu trách nhiệm chính; người hỗ trợ cung cấp dữ liệu hoặc review nhưng không thay đổi phạm vi trách nhiệm.
- Dùng chung tên chỉ số và định dạng kết quả để Thiện có thể tổng hợp mà không phải viết lại thuật toán.

Ước lượng tải công việc:

| Thành viên | Phạm vi chính | Tỷ trọng dự kiến |
|---|---|---:|
| Hải | Bài 1-4, toàn bộ mảng tô màu đồ thị | 35% |
| Ly | Bài 5-7, toàn bộ thuật toán n-Queens | 35% |
| Thiện | Bài 8, thí nghiệm tổng hợp, biểu đồ và kiểm thử tích hợp | 30% |

## 4. Ma trận phân công đủ 8 bài

| Bài | Nội dung | Phụ trách chính | Người hỗ trợ/review | Đầu ra chính |
|---:|---|---|---|---|
| 1 | Biểu diễn CSP và sinh đồ thị | **Hải** | Thiện review tính tái lập | Markdown mô hình `X, D, C`, đồ thị `n = 10`, neighbors, thử 3/4 màu |
| 2 | Kiểm tra đầy đủ và nhất quán | **Hải** | Ly review test | Tối thiểu 3 test có expected/actual; phân biệt partial, complete, consistent và solution |
| 3 | Backtracking, MRV và LCV | **Hải** | Thiện review chỉ số | Baseline, MRV, LCV; nghiệm hợp lệ; `COUNT` và thời gian trên cùng đồ thị |
| 4 | Forward Checking và Min-Conflicts | **Hải** | Thiện thống nhất schema thí nghiệm | Hai thuật toán, hoàn tác miền đúng, nhiều `n`/seed, 3/4 màu, bảng kết quả |
| 5 | Biểu diễn n-Queens | **Ly** | Hải review logic xung đột | Giải thích trạng thái và `h(board)`; ví dụ `n = 4, 8`; bàn cờ trực quan |
| 6 | Ba biến thể Hill Climbing | **Ly** | Thiện review log đo lường | Steepest, Inefficient Stochastic, Efficient Stochastic; điều kiện dừng; metrics/history |
| 7 | Random Restart và Simulated Annealing | **Ly** | Thiện review tính công bằng | Restart tối đa 100; SA với ít nhất 2 lịch làm nguội; success và best-so-far |
| 8 | Đánh giá tổng hợp và bài nâng cao | **Thiện** | Hải cung cấp dữ liệu đồ thị; Ly cung cấp API/log n-Queens | Bảng 100 lượt, hội tụ `n = 8`, log-log `n = 4,8,12,16,20`, nhận xét và QA cuối |

## 5. Công việc chi tiết theo thành viên

### 5.1 Hải - Bài 1 đến Bài 4

**Phạm vi chỉnh sửa chính:** `CSP_graph_coloring_example.ipynb`.

#### Bài 1 - Mô hình CSP

- Giữ seed cố định khi so sánh thuật toán trên cùng một đồ thị.
- Giải thích:
  - `X = {0, 1, ..., n-1}` là tập đỉnh.
  - `D_i` là tập 3 hoặc 4 màu.
  - `C_ij: color(i) != color(j)` với mọi cạnh `(i, j)`.
  - Chỉ lưu cạnh `i < j` để tránh lặp một ràng buộc vô hướng hai lần.
- Hiển thị đồ thị, danh sách láng giềng và số cạnh.
- Nêu rõ: gán đầy đủ chưa chắc hợp lệ; nghiệm CSP phải vừa đầy đủ vừa nhất quán.

#### Bài 2 - `complete()` và `consistent()`

- Viết ít nhất các test sau, có expected và actual:
  1. Gán rỗng: chưa đầy đủ nhưng nhất quán.
  2. Gán một phần không xung đột: chưa đầy đủ và nhất quán.
  3. Hai đỉnh kề cùng màu: không nhất quán.
  4. Gán đầy đủ nhưng có xung đột: đầy đủ nhưng không phải nghiệm.
  5. Nghiệm từ thuật toán: đầy đủ và nhất quán.
- Xác nhận cấu trúc `csp` gồm `variables`, `domains`, `constraints`.

#### Bài 3 - Backtracking, MRV và LCV

- Giữ một phiên bản baseline để so sánh công bằng.
- Cài MRV dựa trên **số giá trị còn hợp lệ**, không chỉ độ dài domain ban đầu.
- Cài LCV bằng số giá trị mà một lựa chọn sẽ loại khỏi các láng giềng chưa gán.
- Với cùng điểm, cạnh, thứ tự màu và seed, so sánh:
  - Backtracking gốc.
  - Backtracking + MRV.
  - Backtracking + MRV + LCV.
- Ghi `COUNT`, thời gian và xác nhận nghiệm bằng `complete() and consistent()`.

#### Bài 4 - Forward Checking và Min-Conflicts

- Forward Checking phải dùng miền riêng cho từng biến, loại màu ở láng giềng và hoàn tác đầy đủ khi quay lui.
- Phát hiện sớm thất bại nếu một biến chưa gán có miền rỗng.
- Min-Conflicts:
  - Khởi tạo phép gán đầy đủ.
  - Chọn ngẫu nhiên một biến đang xung đột.
  - Chọn màu làm nhỏ nhất số xung đột; phá hòa ngẫu nhiên.
  - Có `max_steps`, số bước, lịch sử xung đột và trạng thái thành công.
- Chạy nhiều đồ thị cho mỗi kích thước và cả 3/4 màu; không kết luận "vô nghiệm" chỉ vì Min-Conflicts hết bước.
- Xuất dữ liệu/bảng cho Thiện với số cạnh trung bình, tỷ lệ thành công, `COUNT` hoặc số bước và thời gian.

**Definition of Done của Hải:** Bài 1-4 chạy từ đầu; mọi nghiệm báo thành công đều đầy đủ và nhất quán; có ít nhất một hình tô màu; có bảng so sánh nhiều kích thước và seed.

### 5.2 Ly - Bài 5 đến Bài 7

**Phạm vi chỉnh sửa chính:** phần mô hình và thuật toán, đến hết Task 5 trong `n_queens.ipynb`.

#### Bài 5 - Biểu diễn n-Queens

- Giải thích `board[i]` là hàng của quân hậu tại cột `i`; mỗi cột luôn có đúng một quân.
- Viết rõ `h(board)` là tổng số cặp cùng hàng hoặc cùng đường chéo.
- Kiểm tra bàn cờ mẫu `[1, 3, 0, 2]` có `h = 0`.
- Tạo ví dụ `n = 4` và `n = 8`, hiển thị bàn cờ và giá trị `h`.
- Nêu rõ `h = 0` khi và chỉ khi không còn cặp quân hậu tấn công nhau trong biểu diễn này.

#### Bài 6 - Ba biến thể Hill Climbing

- Cài ba hàm độc lập hoặc cùng một lõi có chế độ rõ ràng:
  1. **Steepest-ascent:** đánh giá toàn bộ láng giềng, chọn giá trị tốt nhất; dừng khi không cải thiện.
  2. **Inefficient Stochastic:** liệt kê toàn bộ nước đi cải thiện rồi chọn ngẫu nhiên.
  3. **Efficient Stochastic/First-choice:** sinh từng láng giềng ngẫu nhiên và nhận nước đi đầu tiên cải thiện.
- Efficient Stochastic phải có `max_attempts` hoặc `max_steps` để không lặp vô hạn trên plateau.
- Mỗi hàm trả về tối thiểu: bàn cờ cuối, `final_conflicts`, `success`, `steps`, `evaluations`, `history`.
- Mọi lần gọi `conflicts()` để chấm một trạng thái phải được tính vào `evaluations` theo cùng quy ước.

#### Bài 7 - Random Restart và Simulated Annealing

- Viết wrapper Random Restart cho cả ba biến thể Hill Climbing, tối đa 100 restart.
- Dừng sớm nếu `h = 0`, nhưng vẫn trả số restart và tổng chi phí đánh giá.
- Simulated Annealing:
  - Dùng xác suất `exp(-delta_h / T)` cho nước đi tệ hơn khi `delta_h > 0`.
  - Thử ít nhất hai lịch làm nguội, ví dụ geometric và inverse/logarithmic.
  - Trả cả nghiệm cuối và nghiệm tốt nhất đã gặp để tránh mất nghiệm tốt do một bước được chấp nhận sau đó.
  - Có điều kiện dừng theo số vòng, nhiệt độ nhỏ nhất hoặc đạt `h = 0`.
- Bàn giao cho Thiện các hàm có giao diện thống nhất và lịch sử hội tụ.

**Definition of Done của Ly:** Bài 5-7 chạy được với seed truyền vào; ba HC, Random Restart và SA đều trả đủ metrics; có minh họa bàn cờ; không có vòng lặp vô hạn; không dùng đường dẫn Google Drive cá nhân.

### 5.3 Thiện - Bài 8 và tích hợp

**Phạm vi chỉnh sửa chính:** Task 6 và các cell phân tích cuối trong `n_queens.ipynb`, sau khi nhận thuật toán từ Ly; tổng hợp và kiểm thử cả hai notebook.

#### Bài 8 - Đánh giá tổng hợp

- Xây dựng hàm benchmark dùng `time.perf_counter()` và lưu từng lượt chạy thay vì chỉ lưu giá trị trung bình.
- Với mỗi thuật toán n-Queens, chạy tối thiểu 100 lượt ở `n = 4` và `n = 8` trên các bàn cờ đầu vào tương ứng/cùng seed khi có thể.
- Bảng bắt buộc gồm:
  - Thời gian trung bình.
  - Xung đột cuối trung bình.
  - Tỷ lệ đạt `h = 0`.
  - Nên bổ sung số bước và số lần đánh giá trung bình.
- Chọn một lượt đại diện ở `n = 8` và vẽ đường `h` theo iteration cho từng thuật toán.
- Vẽ biểu đồ log-log thời gian theo `n in {4, 8, 12, 16, 20}` cho ít nhất hai thuật toán; ước lượng hệ số góc trên log-log và chỉ gọi đó là độ phức tạp thực nghiệm.
- Tổng hợp bảng tô màu do Hải cung cấp và kiểm tra 3/4 màu, nhiều kích thước, nhiều seed.
- Viết phần nhận xét cuối và trả lời câu hỏi thảo luận:
  - Hải dự thảo câu 1-3.
  - Ly dự thảo câu 4-5.
  - Thiện dự thảo câu 6 và biên tập toàn bộ.

#### Kiểm thử tích hợp và khả năng tái lập

- Restart kernel và chạy `Run All` cho cả hai notebook.
- Đảm bảo không cell nào phụ thuộc thứ tự chạy cũ hoặc biến chưa khởi tạo.
- Xóa output debug quá dài; giữ bảng, hình và output chứng minh kết quả.
- Ghi Python, NumPy, SciPy, Matplotlib, môi trường chạy và thông tin nhóm.
- Kiểm tra không còn placeholder như `Code and description go here`, `TODO` bắt buộc hoặc tên sinh viên mẫu.
- Kiểm tra không còn đường dẫn tuyệt đối/Google Drive bắt buộc.

**Definition of Done của Thiện:** Bài 8 có bảng 100 lượt, biểu đồ hội tụ và log-log, nhận xét đúng giới hạn dữ liệu; cả hai notebook chạy lại từ đầu; toàn bộ checklist nộp bài đạt.

## 6. Chuẩn giao tiếp giữa mã thuật toán và benchmark

Để tránh Thiện phải sửa lại mã của Hải/Ly, mỗi lần chạy thuật toán nên chuẩn hóa kết quả thành `dict` với các trường phù hợp:

```python
{
    "algorithm": "...",
    "problem": "graph_coloring | n_queens",
    "n": 8,
    "seed": 1234,
    "success": True,
    "runtime_s": 0.001,
    "steps": 12,
    "evaluations": 120,
    "final_conflicts": 0,
    "history": [7, 5, 3, 1, 0],
}
```

Riêng tô màu đồ thị bổ sung `num_colors`, `num_edges`, `count`; riêng Random Restart bổ sung `restarts`. Trường không áp dụng có thể để `None`.

Quy ước quan trọng:

- `COUNT` của Backtracking là số nút/lần thử theo định nghĩa được ghi rõ trong notebook.
- `evaluations` của n-Queens là số lần đánh giá hàm mục tiêu; không so sánh trực tiếp với `COUNT`.
- `success` chỉ là `True` khi nghiệm thực sự hợp lệ (`complete and consistent` hoặc `h == 0`).
- Một lần hết giới hạn bước chỉ là thất bại trong ngân sách tính toán, không phải chứng minh vô nghiệm.

## 7. Trình tự thực hiện và bàn giao

### Giai đoạn 1 - Hoàn thiện thuật toán độc lập

- Hải làm Bài 1-4 trên notebook tô màu.
- Ly làm Bài 5-7 và hoàn thiện API kết quả trước Task 6.
- Thiện chuẩn bị hàm benchmark, schema bảng và khung biểu đồ bằng dữ liệu giả nhỏ.

### Giai đoạn 2 - Bàn giao cho đánh giá

- Hải gửi danh sách cấu hình, seed, kết quả thô và hình tô màu cho Thiện.
- Ly gửi API các thuật toán, quy ước metric và một smoke test cho mỗi thuật toán cho Thiện.
- Thiện khóa danh sách cấu hình benchmark trước khi chạy 100 lượt để tránh chọn tham số theo kết quả có lợi.

### Giai đoạn 3 - Tích hợp

- Thiện chạy thí nghiệm chính, tạo bảng/biểu đồ và điền Bài 8.
- Hải review phần tô màu và câu hỏi 1-3.
- Ly review phần n-Queens và câu hỏi 4-5.
- Cả nhóm kiểm tra tên, môi trường, thư viện và kết quả `Run All`.

## 8. Quy tắc tránh xung đột notebook

- Hải là người duy nhất chỉnh `CSP_graph_coloring_example.ipynb` trong giai đoạn thuật toán.
- Ly hoàn tất phần đến Task 5 của `n_queens.ipynb` trước khi Thiện tích hợp Task 6.
- Thiện chỉ bắt đầu chỉnh `n_queens.ipynb` sau khi đã nhận phiên bản mới nhất từ Ly.
- Không để hai người đồng thời sửa cùng một notebook vì JSON của `.ipynb` rất dễ xung đột khi merge.
- Mỗi commit chỉ nên chứa một cụm thay đổi rõ ràng, ví dụ `graph: add MRV and LCV` hoặc `queens: implement simulated annealing`.

## 9. Checklist nghiệm thu cuối

### Đủ nội dung

- [ ] Bài 1: mô hình CSP, đồ thị, neighbors, 3/4 màu.
- [ ] Bài 2: ít nhất 3 test và giải thích complete/consistent.
- [ ] Bài 3: Backtracking, MRV, LCV và so sánh.
- [ ] Bài 4: Forward Checking, Min-Conflicts và thí nghiệm nhiều `n`/seed.
- [ ] Bài 5: mô hình n-Queens, `h(board)`, ví dụ `n = 4, 8`.
- [ ] Bài 6: đủ ba biến thể Hill Climbing và metrics.
- [ ] Bài 7: Random Restart, Simulated Annealing với hai lịch làm nguội.
- [ ] Bài 8: 100 lượt, bảng tổng hợp, hội tụ, log-log và nhận xét.

### Chất lượng sản phẩm

- [ ] Mọi nghiệm báo thành công đều được kiểm tra lại bằng hàm xác thực độc lập.
- [ ] Cùng một cấu hình so sánh dùng cùng dữ liệu đầu vào/seed khi hợp lý.
- [ ] Ghi rõ số lượt, seed, giới hạn bước/restart, lịch làm nguội và cách tính trung bình.
- [ ] Có đồ thị tô màu, bàn cờ n-Queens, biểu đồ hội tụ và biểu đồ log-log.
- [ ] Hai notebook `Run All` thành công trong kernel sạch.
- [ ] Không còn placeholder, lỗi, debug output dài hoặc đường dẫn cá nhân.
- [ ] Có thông tin nhóm, môi trường và phiên bản thư viện.

## 10. Rủi ro cần theo dõi

| Rủi ro | Cách xử lý |
|---|---|
| Đồ thị 3 màu không tìm được nghiệm | Tách rõ timeout/max-steps, thất bại heuristic và chứng minh vô nghiệm của Backtracking đầy đủ |
| Forward Checking làm hỏng domain khi quay lui | Sao lưu/ghi log các giá trị bị loại theo từng nhánh và khôi phục đúng khi backtrack |
| Hill Climbing kẹt plateau | Ghi rõ điều kiện dừng; dùng Random Restart hoặc SA thay vì lặp vô hạn |
| So sánh thiếu công bằng | Dùng cùng seed/bàn cờ đầu vào, cùng giới hạn và cùng quy ước metric |
| Benchmark 100 lượt quá lâu | Smoke test trước, ước lượng thời gian, lưu dữ liệu thô và chỉ tăng quy mô sau khi mã ổn định |
| Merge conflict notebook | Tuân thủ thứ tự Ly bàn giao trước, Thiện tích hợp sau; không sửa song song cùng file |

