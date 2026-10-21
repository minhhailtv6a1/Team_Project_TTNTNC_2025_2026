# SƯỜN BÁO CÁO LAB 04 - BÀI TOÁN THỎA MÃN RÀNG BUỘC

> Môn học: Trí tuệ nhân tạo nâng cao  
> Nhóm: [Điền tên nhóm]  
> Thành viên: Hải - Ly - Thiện  
> Giảng viên: [Điền tên giảng viên]  
> Ngày nộp: [dd/mm/yyyy]

---

## Trang thông tin nhóm

| STT | Họ và tên | MSSV | Phạm vi phụ trách chính | Tỷ trọng dự kiến |
|---:|---|---|---|---:|
| 1 | Hải | [Điền MSSV] | Bài 1-4, CSP tô màu đồ thị | 35% |
| 2 | Ly | [Điền MSSV] | Bài 5-7, thuật toán n-Queens | 35% |
| 3 | Thiện | [Điền MSSV] | Bài 8, thí nghiệm tổng hợp, biểu đồ và tích hợp | 30% |

## Tóm tắt báo cáo

[Viết 150-250 từ, trình bày ngắn gọn hai nhóm bài toán, các thuật toán đã cài đặt, cách tổ chức thí nghiệm và những kết quả chính. Không đưa nhận định chưa được dữ liệu thực nghiệm hỗ trợ.]

**Từ khóa:** Constraint Satisfaction Problem, graph coloring, Backtracking, MRV, LCV, Forward Checking, Min-Conflicts, n-Queens, Hill Climbing, Random Restart, Simulated Annealing.

## Danh mục viết tắt

| Viết tắt | Nội dung |
|---|---|
| CSP | Constraint Satisfaction Problem - Bài toán thỏa mãn ràng buộc |
| MRV | Minimum Remaining Values |
| LCV | Least Constraining Value |
| FC | Forward Checking |
| HC | Hill Climbing |
| SA | Simulated Annealing |

## Danh mục bảng và hình

- [Cập nhật số thứ tự và tên bảng sau khi hoàn thiện báo cáo.]
- [Cập nhật số thứ tự và tên hình sau khi hoàn thiện báo cáo.]

---

## Mở đầu

### 1. Bối cảnh và mục tiêu

- Giới thiệu bài toán thỏa mãn ràng buộc và vai trò của tìm kiếm có hệ thống, tìm kiếm cục bộ.
- Nêu hai bài toán được khảo sát: tô màu đồ thị và n-Queens.
- Nêu các tiêu chí đánh giá: tính hợp lệ, số xung đột, `COUNT`/số lần đánh giá, số bước, thời gian, tỷ lệ thành công và khả năng mở rộng.

### 2. Dữ liệu và mã nguồn

- `CSP_graph_coloring_example.ipynb`: Bài 1-4.
- `n_queens.ipynb`: Bài 5-8.
- `README.md`: hướng dẫn chạy và thông tin chung.

### 3. Môi trường thực nghiệm

| Thành phần | Phiên bản/cấu hình |
|---|---|
| Python | [Điền phiên bản] |
| NumPy | [Điền phiên bản] |
| SciPy | [Điền phiên bản] |
| Matplotlib | [Điền phiên bản] |
| Jupyter/Colab | [Điền môi trường] |
| Hệ điều hành/phần cứng | [Điền thông tin] |

### 4. Quy ước đo lường chung

- Dùng seed cố định khi so sánh các thuật toán trên cùng dữ liệu đầu vào; dùng nhiều seed để đánh giá độ ổn định.
- Đo thời gian bằng `time.perf_counter()`; ghi rõ số lượt, điều kiện dừng và cách tính trung bình.
- `COUNT` trong Backtracking là số nút/lần thử theo định nghĩa được ghi trong notebook.
- `evaluations` trong n-Queens là số lần đánh giá hàm `conflicts()`; không so sánh trực tiếp với `COUNT`.
- Chỉ ghi `success = True` khi nghiệm được xác thực độc lập: `complete() and consistent()` đối với tô màu, hoặc `h == 0` đối với n-Queens.
- Hết `max_steps`, `max_attempts` hoặc thời gian chỉ là thất bại trong ngân sách tính toán, không tự động chứng minh bài toán vô nghiệm.

---

# Chương 1. Biểu diễn CSP và sinh đồ thị cần tô màu

**Tương ứng:** Bài 1 trong đề bài.  
**Phụ trách chính:** Hải.  
**Hỗ trợ/review:** Thiện kiểm tra tính tái lập, seed và cách trình bày kết quả.

## 1.1. Mục tiêu chương

- Biểu diễn bài toán tô màu đồ thị dưới dạng CSP.
- Sinh đồ thị phẳng từ `n = 10` điểm ngẫu nhiên bằng phép tam giác hóa Delaunay.
- Khảo sát miền 4 màu và 3 màu.
- Phân biệt phép gán đầy đủ với phép gán hợp lệ.

## 1.2. Mô hình bài toán

- Tập biến: `X = {0, 1, ..., n - 1}`, mỗi biến ứng với một đỉnh.
- Miền giá trị: `D_i = {red, blue, green, orange}` hoặc miền 3 màu.
- Ràng buộc: `C_ij: color(i) != color(j)` với mọi cạnh `(i, j)`.
- Giải thích vì sao chỉ lưu cạnh `i < j` để tránh lặp ràng buộc vô hướng.
- Nêu điều kiện một phép gán là nghiệm CSP: vừa đầy đủ, vừa nhất quán.

## 1.3. Sinh và mô tả đồ thị

- Trình bày cách sinh điểm, Delaunay triangulation, tập cạnh và danh sách `neighbors`.
- Ghi seed, số đỉnh, số cạnh và số bậc trung bình.
- Chèn hình đồ thị chưa tô màu.

> **Hình 1.1.** Đồ thị phẳng Delaunay với `n = 10`, seed `[điền seed]`.

## 1.4. Khảo sát miền 3 màu và 4 màu

| Cấu hình | Số đỉnh | Số cạnh | Số màu | Nhận xét ban đầu |
|---|---:|---:|---:|---|
| [Cấu hình 1] | 10 | [Điền] | 4 | [Điền] |
| [Cấu hình 2] | 10 | [Điền] | 3 | [Điền] |

## 1.5. Kết luận chương

[Tóm tắt mô hình `X, D, C`, đặc điểm đồ thị và ảnh hưởng dự kiến của kích thước miền.]

## 1.6. Phân công và đầu ra

- **Hải:** viết phần mô hình hóa; tạo đồ thị; xuất `neighbors`, số cạnh và hình minh họa; khảo sát miền 3/4 màu.
- **Thiện:** kiểm tra notebook có chạy lại đúng với seed đã công bố và thông tin cấu hình đủ để tái lập.
- **Đầu ra bắt buộc:** mô hình `X, D, C`; đồ thị `n = 10`; danh sách láng giềng; số cạnh; hình đồ thị; nhận xét về phép gán đầy đủ và hợp lệ.
- **Tiêu chí hoàn thành:** kết quả sinh đồ thị tái lập được, ký hiệu nhất quán và không phụ thuộc đường dẫn cá nhân.

---

# Chương 2. Kiểm tra tính đầy đủ và nhất quán

**Tương ứng:** Bài 2 trong đề bài.  
**Phụ trách chính:** Hải.  
**Hỗ trợ/review:** Ly review logic và kết quả các ca kiểm thử.

## 2.1. Mục tiêu chương

- Làm rõ vai trò của `complete(assignment, csp)` và `consistent(assignment, csp)`.
- Phân biệt phép gán rỗng, phép gán từng phần, phép gán đầy đủ và nghiệm CSP.
- Xác nhận cấu trúc lưu trữ `csp` gồm `variables`, `domains`, `constraints`.

## 2.2. Thiết kế hai hàm kiểm tra

### 2.2.1. Hàm `complete()`

[Mô tả điều kiện đầu vào, đầu ra và tiêu chí phép gán đầy đủ.]

### 2.2.2. Hàm `consistent()`

[Mô tả cách kiểm tra các ràng buộc giữa những biến đã được gán.]

## 2.3. Ca kiểm thử

| STT | Dữ liệu kiểm thử | `complete()` mong đợi | `consistent()` mong đợi | Kết quả thực tế | Đạt/Không đạt |
|---:|---|---:|---:|---|---|
| 1 | Phép gán rỗng | False | True | [Điền] | [Điền] |
| 2 | Phép gán một phần, không xung đột | False | True | [Điền] | [Điền] |
| 3 | Hai đỉnh kề nhau cùng màu | [Theo dữ liệu] | False | [Điền] | [Điền] |
| 4 | Phép gán đầy đủ nhưng có xung đột | True | False | [Điền] | [Điền] |
| 5 | Nghiệm do thuật toán tìm được | True | True | [Điền] | [Điền] |

## 2.4. Thảo luận

- Trả lời câu hỏi 1 của đề: `complete()` khác `consistent()` như thế nào?
- Giải thích vì sao một phép gán đầy đủ không nhất thiết là nghiệm CSP.
- Nêu vai trò của việc xác thực nghiệm độc lập sau khi thuật toán kết thúc.

## 2.5. Kết luận chương

[Tóm tắt ý nghĩa của hai tiêu chí và kết quả kiểm thử.]

## 2.6. Phân công và đầu ra

- **Hải:** chuẩn bị dữ liệu kiểm thử, chạy test, ghi expected/actual và giải thích cấu trúc `csp`.
- **Ly:** review các trường hợp biên, nhất là phép gán một phần và phép gán đầy đủ có xung đột.
- **Đầu ra bắt buộc:** tối thiểu 3 ca kiểm thử có kết quả mong đợi và thực tế; phần trả lời câu hỏi thảo luận 1.
- **Tiêu chí hoàn thành:** các test chạy được từ kernel sạch và minh họa rõ `complete()` không đồng nghĩa với `consistent()`.

---

# Chương 3. Backtracking Search và thứ tự chọn biến/giá trị

**Tương ứng:** Bài 3 trong đề bài.  
**Phụ trách chính:** Hải.  
**Hỗ trợ/review:** Thiện kiểm tra quy ước `COUNT`, thời gian và tính công bằng của so sánh.

## 3.1. Mục tiêu chương

- Cài đặt và đánh giá Backtracking cơ bản.
- Cài đặt chiến lược chọn biến MRV trên miền còn hợp lệ.
- Cài đặt chiến lược thứ tự giá trị LCV.
- So sánh ba cấu hình trên cùng đồ thị.

## 3.2. Backtracking cơ bản

- Trình bày giả mã hoặc lưu đồ.
- Mô tả cách chọn biến chưa gán đầu tiên.
- Định nghĩa chính xác cách tăng biến `COUNT`.
- Nêu điều kiện dừng và cách xác thực nghiệm.

## 3.3. Minimum Remaining Values

- Nêu nguyên tắc chọn biến có ít giá trị còn hợp lệ nhất.
- Làm rõ MRV được tính trên miền còn hợp lệ, không chỉ độ dài miền ban đầu.
- Nêu quy tắc phá hòa nếu nhiều biến có cùng giá trị MRV.

## 3.4. Least Constraining Value

- Nêu cách chấm điểm một màu theo số giá trị nó loại khỏi các láng giềng chưa gán.
- Nêu quy tắc phá hòa và thứ tự màu để thí nghiệm có thể tái lập.

## 3.5. Thiết kế thí nghiệm

- Giữ nguyên tập điểm, cạnh, seed và thứ tự màu giữa các cấu hình.
- So sánh: Backtracking gốc; Backtracking + MRV; Backtracking + MRV + LCV.
- Chỉ số: thành công, `COUNT`, thời gian và tính hợp lệ của nghiệm.

| Thuật toán | Seed | Số màu | Thành công | `COUNT` | Thời gian (s) | Nghiệm hợp lệ |
|---|---:|---:|---:|---:|---:|---:|
| Backtracking | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Backtracking + MRV | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Backtracking + MRV + LCV | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |

## 3.6. Kết quả trực quan và nhận xét

> **Hình 3.1.** Một nghiệm tô màu hợp lệ tìm được bằng `[điền thuật toán]`.

- So sánh kích thước cây tìm kiếm qua `COUNT`.
- Phân tích trường hợp heuristic giúp giảm nhánh và trường hợp chi phí tính heuristic làm tăng thời gian.
- Trả lời phần MRV trong câu hỏi thảo luận 2 của đề.

## 3.7. Kết luận chương

[Nêu cấu hình hiệu quả nhất trên dữ liệu đã thử, kèm giới hạn của kết luận.]

## 3.8. Phân công và đầu ra

- **Hải:** duy trì bản baseline; cài MRV và LCV; chạy so sánh; xác thực và trực quan hóa nghiệm.
- **Thiện:** review định nghĩa `COUNT`, cách đo thời gian và việc dùng cùng đầu vào giữa các cấu hình.
- **Đầu ra bắt buộc:** ba cấu hình thuật toán; bảng so sánh `COUNT`/thời gian; ít nhất một hình tô màu; phần thảo luận MRV.
- **Tiêu chí hoàn thành:** mọi nghiệm báo thành công đều qua `complete() and consistent()` và bảng ghi đủ điều kiện thí nghiệm.

---

# Chương 4. Forward Checking và Min-Conflicts

**Tương ứng:** Bài 4 trong đề bài.  
**Phụ trách chính:** Hải.  
**Hỗ trợ/review:** Thiện thống nhất schema dữ liệu và cấu hình thí nghiệm tổng hợp.

## 4.1. Mục tiêu chương

- Bổ sung Forward Checking vào Backtracking.
- Cài đặt Min-Conflicts cho phép gán đầy đủ.
- Đánh giá trên nhiều kích thước đồ thị, nhiều seed và miền 3/4 màu.

## 4.2. Forward Checking

- Mô tả miền riêng của từng biến.
- Trình bày cách loại màu xung đột khỏi láng giềng chưa gán.
- Trình bày cơ chế ghi nhận và hoàn tác miền khi quay lui.
- Nêu cách phát hiện sớm thất bại khi một biến chưa gán có miền rỗng.

## 4.3. Min-Conflicts

- Khởi tạo một phép gán đầy đủ.
- Chọn ngẫu nhiên một biến đang xung đột.
- Chọn màu làm nhỏ nhất số ràng buộc vi phạm; phá hòa ngẫu nhiên.
- Ghi `max_steps`, số bước, lịch sử xung đột, thời gian và trạng thái thành công.
- Làm rõ Min-Conflicts hết bước không chứng minh bài toán vô nghiệm.

## 4.4. Thiết kế thí nghiệm

- Kích thước đồ thị: `[điền các n]`.
- Miền màu: 3 màu và 4 màu.
- Seed: `[điền danh sách hoặc quy tắc sinh seed]`.
- Số lượt cho mỗi cấu hình: `[điền]`.
- Thuật toán: Backtracking/Forward Checking và Min-Conflicts.

| Thuật toán | `n` | Số màu | Số seed/lượt | Số cạnh TB | Tỷ lệ thành công | `COUNT`/số bước TB | Thời gian TB (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Forward Checking | [Điền] | 3 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Forward Checking | [Điền] | 4 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Min-Conflicts | [Điền] | 3 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Min-Conflicts | [Điền] | 4 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |

## 4.5. Phân tích kết quả

- So sánh tác động của Forward Checking lên cây Backtracking và chi phí quản lý miền.
- Phân tích sự khác nhau giữa miền 3 màu và 4 màu.
- Phân biệt ba tình huống: tìm được nghiệm; heuristic hết giới hạn; Backtracking đầy đủ chứng minh vô nghiệm.
- Trả lời phần Forward Checking trong câu hỏi 2 và toàn bộ câu hỏi 3 của đề.

## 4.6. Kết luận chương

[Nêu ưu/nhược điểm của Forward Checking và Min-Conflicts dựa trên dữ liệu.]

## 4.7. Phân công và đầu ra

- **Hải:** cài Forward Checking và hoàn tác miền; cài Min-Conflicts; chạy nhiều `n`, seed, miền 3/4 màu; xuất dữ liệu thô.
- **Thiện:** thống nhất tên cột/chỉ số, kiểm tra dữ liệu đủ để tổng hợp ở Chương 8 và review tính công bằng.
- **Đầu ra bắt buộc:** hai thuật toán; bảng nhiều kích thước/seed; tỷ lệ thành công; `COUNT` hoặc số bước; thời gian; trả lời câu hỏi 2-3.
- **Tiêu chí hoàn thành:** miền được khôi phục đúng sau backtrack; không diễn giải thất bại của Min-Conflicts như một chứng minh vô nghiệm.

---

# Chương 5. Biểu diễn bài toán n-Queens

**Tương ứng:** Bài 5 trong đề bài.  
**Phụ trách chính:** Ly.  
**Hỗ trợ/review:** Hải kiểm tra logic đếm xung đột.

## 5.1. Mục tiêu chương

- Trình bày cách biểu diễn một trạng thái n-Queens.
- Định nghĩa hàm mục tiêu `h(board)`.
- Kiểm tra các ví dụ `n = 4`, `n = 8` và trực quan hóa bàn cờ.

## 5.2. Biểu diễn trạng thái

- `board[i]` là chỉ số hàng của quân hậu tại cột `i`.
- Mỗi cột luôn có đúng một quân hậu.
- Không gian trạng thái và kiểu dữ liệu được sử dụng.

## 5.3. Hàm đánh giá xung đột

- `h(board)` là số cặp quân hậu cùng hàng hoặc cùng đường chéo.
- Nêu công thức/điều kiện kiểm tra xung đột của cặp cột `i`, `j`.
- Giải thích vì sao `h = 0` khi và chỉ khi không có cặp quân hậu tấn công nhau trong biểu diễn này.

## 5.4. Kiểm thử và trực quan hóa

| Bàn cờ | `n` | `h(board)` mong đợi | Kết quả thực tế | Nhận xét |
|---|---:|---:|---:|---|
| `[1, 3, 0, 2]` | 4 | 0 | [Điền] | Nghiệm hợp lệ |
| `[Điền bàn cờ]` | 4 | [Điền] | [Điền] | [Điền] |
| `[Điền bàn cờ]` | 8 | [Điền] | [Điền] | [Điền] |

> **Hình 5.1.** Bàn cờ n-Queens với `n = [điền]`, `h = [điền]`.

## 5.5. Kết luận chương

[Tóm tắt ưu điểm của biểu diễn một quân hậu trên mỗi cột và vai trò của `h(board)`.]

## 5.6. Phân công và đầu ra

- **Ly:** giải thích trạng thái; định nghĩa/kiểm thử `h(board)`; tạo ví dụ `n = 4, 8`; chèn hình bàn cờ.
- **Hải:** review cách đếm mỗi cặp xung đột đúng một lần và các trường hợp cùng hàng/đường chéo.
- **Đầu ra bắt buộc:** giải thích `board[i]`; định nghĩa `h`; kiểm tra `[1, 3, 0, 2]`; ví dụ `n = 4, 8`; ít nhất một hình bàn cờ.
- **Tiêu chí hoàn thành:** hàm xung đột cho kết quả đúng trên các test đã biết và hình khớp với dữ liệu bàn cờ.

---

# Chương 6. Các biến thể Hill Climbing

**Tương ứng:** Bài 6 trong đề bài.  
**Phụ trách chính:** Ly.  
**Hỗ trợ/review:** Thiện kiểm tra quy ước metrics và lịch sử hội tụ.

## 6.1. Mục tiêu chương

- Cài đặt Steepest-ascent Hill Climbing.
- Cài đặt Inefficient Stochastic Hill Climbing.
- Cài đặt Efficient Stochastic/First-choice Hill Climbing.
- So sánh số bước, số lần đánh giá và khả năng mắc kẹt.

## 6.2. Không gian lân cận và điều kiện dừng

- Định nghĩa một nước đi lân cận: `[mô tả toán tử đổi hàng của một quân hậu]`.
- Nêu cách sinh/duyệt láng giềng.
- Nêu điều kiện thành công, local optimum, plateau, `max_steps` và `max_attempts`.

## 6.3. Steepest-ascent Hill Climbing

- Đánh giá toàn bộ láng giềng.
- Chọn nước đi cải thiện tốt nhất.
- Dừng khi không còn cải thiện.
- Trình bày giả mã và độ lớn lân cận.

## 6.4. Inefficient Stochastic Hill Climbing

- Liệt kê toàn bộ các nước đi cải thiện.
- Chọn ngẫu nhiên một nước đi trong danh sách.
- Trình bày ảnh hưởng đến số lần đánh giá.

## 6.5. Efficient Stochastic/First-choice Hill Climbing

- Sinh từng láng giềng ngẫu nhiên.
- Chấp nhận nước đi đầu tiên cải thiện.
- Nêu rõ giới hạn thử để tránh lặp vô hạn trên plateau.

## 6.6. Giao diện kết quả và quy ước metrics

Mỗi thuật toán trả về tối thiểu:

```python
{
    "board": [...],
    "final_conflicts": 0,
    "success": True,
    "steps": 12,
    "evaluations": 120,
    "history": [7, 5, 3, 1, 0],
}
```

- Định nghĩa `steps` và `evaluations` thống nhất giữa ba biến thể.
- Mọi lần gọi `conflicts()` để chấm một trạng thái phải được tính vào `evaluations`.

## 6.7. Kết quả thử nghiệm ban đầu

| Thuật toán | `n` | Seed | Thành công | Xung đột cuối | Số bước | Số lần đánh giá | Thời gian (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Steepest HC | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Inefficient Stochastic HC | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Efficient Stochastic HC | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |

## 6.8. Thảo luận

- So sánh ba biến thể về cách chọn nước đi và số lần đánh giá láng giềng.
- Phân tích local optimum và plateau quan sát được.
- Trả lời câu hỏi 5 của đề.

## 6.9. Kết luận chương

[Tóm tắt đánh đổi giữa chất lượng nghiệm và chi phí đánh giá của ba biến thể.]

## 6.10. Phân công và đầu ra

- **Ly:** cài ba biến thể; định nghĩa điều kiện dừng; ghi đủ metrics/history; viết phần so sánh.
- **Thiện:** review cách đếm `evaluations`, định dạng kết quả và khả năng sử dụng lịch sử cho biểu đồ Chương 8.
- **Đầu ra bắt buộc:** ba thuật toán; metrics thống nhất; bảng thử nghiệm; trả lời câu hỏi 5.
- **Tiêu chí hoàn thành:** không có vòng lặp vô hạn; cùng quy ước đo giữa ba biến thể; chạy được với seed truyền vào.

---

# Chương 7. Random Restart và Simulated Annealing

**Tương ứng:** Bài 7 trong đề bài.  
**Phụ trách chính:** Ly.  
**Hỗ trợ/review:** Thiện kiểm tra tính công bằng của so sánh và tham số thí nghiệm.

## 7.1. Mục tiêu chương

- Bổ sung Random Restart cho ba biến thể Hill Climbing.
- Cài đặt Simulated Annealing với ít nhất hai lịch làm nguội.
- Đánh giá cách các phương pháp thoát local optimum/plateau.

## 7.2. Random Restart

- Khởi tạo lại bàn cờ ngẫu nhiên và chạy thuật toán cơ sở.
- Giới hạn tối đa 100 lần khởi động lại.
- Dừng sớm khi `h = 0`.
- Ghi số restart, tổng số bước, tổng số lần đánh giá, thời gian và nghiệm tốt nhất.

## 7.3. Simulated Annealing

- Định nghĩa `delta_h` và xác suất chấp nhận nước đi tệ hơn: `p = exp(-delta_h / T)` khi `delta_h > 0`.
- Nêu nhiệt độ ban đầu, nhiệt độ tối thiểu và giới hạn vòng lặp.
- Lưu cả trạng thái cuối và trạng thái tốt nhất đã gặp.

### 7.3.1. Lịch làm nguội 1 - Geometric

[Nêu công thức, tham số và lý do chọn.]

### 7.3.2. Lịch làm nguội 2 - Inverse hoặc logarithmic

[Nêu công thức, tham số và lý do chọn.]

## 7.4. Thiết kế so sánh

- Dùng cùng `n`, tập seed/bàn cờ đầu vào và ngân sách tính toán khi hợp lý.
- Phân biệt `success` (`h = 0`) với nghiệm tốt nhất (`h` nhỏ nhất).
- Ghi rõ cách cộng chi phí qua các lần restart.

| Thuật toán | `n` | Số lượt | Giới hạn | Tỷ lệ thành công | Xung đột cuối TB | Bước TB | Đánh giá TB | Thời gian TB (s) |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| Random Restart + Steepest | [Điền] | [Điền] | 100 restart | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Random Restart + Inefficient Stochastic | [Điền] | [Điền] | 100 restart | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Random Restart + Efficient Stochastic | [Điền] | [Điền] | 100 restart | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| SA - lịch 1 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| SA - lịch 2 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |

## 7.5. Thảo luận

- Mô tả biểu hiện của local optimum/plateau trong Hill Climbing.
- Giải thích Random Restart xử lý bằng đa dạng hóa trạng thái khởi tạo.
- Giải thích Simulated Annealing có thể thoát bẫy nhờ chấp nhận có kiểm soát nước đi tệ hơn.
- Trả lời câu hỏi 4 của đề.

## 7.6. Kết luận chương

[So sánh hiệu quả, chi phí và độ nhạy tham số của Random Restart và Simulated Annealing.]

## 7.7. Phân công và đầu ra

- **Ly:** cài wrapper Random Restart cho ba HC; cài SA và hai lịch làm nguội; xuất nghiệm cuối/best-so-far cùng metrics/history.
- **Thiện:** review cách dùng seed, điều kiện dừng, ngân sách so sánh và dữ liệu bàn giao cho Chương 8.
- **Đầu ra bắt buộc:** Random Restart tối đa 100 lần; SA với ít nhất hai lịch; bảng kết quả; trả lời câu hỏi 4.
- **Tiêu chí hoàn thành:** phép đo cộng dồn đúng qua restart; SA giữ được nghiệm tốt nhất; mọi cấu hình có điều kiện dừng hữu hạn.

---

# Chương 8. Đánh giá tổng hợp và bài nâng cao

**Tương ứng:** Bài 8 trong đề bài.  
**Phụ trách chính:** Thiện.  
**Hỗ trợ:** Hải cung cấp dữ liệu tô màu; Ly cung cấp API, log và dữ liệu n-Queens.  
**Review:** Hải review phần tô màu và câu hỏi 1-3; Ly review phần n-Queens và câu hỏi 4-5; Thiện biên tập toàn bộ.

## 8.1. Mục tiêu chương

- Tổng hợp và đánh giá các thuật toán bằng một quy trình thực nghiệm tái lập được.
- Chạy tối thiểu 100 lượt cho mỗi thiết lập n-Queens tại `n = 4` và `n = 8`.
- Vẽ biểu đồ hội tụ tại `n = 8`.
- Vẽ biểu đồ log-log thời gian theo `n in {4, 8, 12, 16, 20}` cho ít nhất hai thuật toán.
- Tổng hợp thí nghiệm tô màu với 3/4 màu, nhiều kích thước và nhiều seed.

## 8.2. Thiết kế benchmark

- Danh sách thuật toán: `[điền đầy đủ]`.
- Danh sách kích thước, seed, số lượt và điều kiện dừng.
- Cách tạo bàn cờ/đồ thị đầu vào chung cho các thuật toán.
- Cách đo thời gian bằng `time.perf_counter()`.
- Cách lưu dữ liệu từng lượt thay vì chỉ lưu trung bình.
- Cách tính tỷ lệ thành công, trung bình và độ phân tán `[độ lệch chuẩn/IQR nếu có]`.

### 8.2.1. Schema kết quả thống nhất

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

- Tô màu bổ sung: `num_colors`, `num_edges`, `count`.
- Random Restart bổ sung: `restarts`.
- Trường không áp dụng có thể đặt là `None`.

## 8.3. Kết quả tổng hợp tô màu đồ thị

| Thuật toán | `n` | Số màu | Số seed/lượt | Tỷ lệ thành công | `COUNT`/bước TB | Thời gian TB (s) | Ghi chú |
|---|---:|---:|---:|---:|---:|---:|---|
| Backtracking | [Điền] | 4 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| MRV + LCV | [Điền] | 4 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Forward Checking | [Điền] | 3/4 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Min-Conflicts | [Điền] | 3/4 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |

## 8.4. Kết quả tổng hợp n-Queens

Mỗi thuật toán phải có tối thiểu 100 lượt ở `n = 4` và `n = 8`.

| Thuật toán | `n` | Số lượt | Thời gian TB (s) | Xung đột cuối TB | Tỷ lệ `h = 0` | Bước TB | Đánh giá TB |
|---|---:|---:|---:|---:|---:|---:|---:|
| Steepest HC | 4 | >=100 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Steepest HC | 8 | >=100 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Inefficient Stochastic HC | 4/8 | >=100 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Efficient Stochastic HC | 4/8 | >=100 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Random Restart | 4/8 | >=100 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |
| Simulated Annealing | 4/8 | >=100 | [Điền] | [Điền] | [Điền] | [Điền] | [Điền] |

## 8.5. Phân tích hội tụ tại `n = 8`

- Chọn một lượt đại diện theo tiêu chí công bố trước, không chọn tùy ý sau khi xem kết quả.
- Vẽ `h` theo iteration cho từng thuật toán.
- Nếu độ dài lịch sử khác nhau, nêu rõ cách căn chỉnh hoặc trình bày riêng.

> **Hình 8.1.** Đường hội tụ `h` theo iteration của các thuật toán tại `n = 8`.

[Nhận xét tốc độ giảm xung đột, plateau, dao động của SA và thời điểm đạt nghiệm.]

## 8.6. Khả năng mở rộng và biểu đồ log-log

- Chọn ít nhất hai thuật toán.
- Chạy với `n in {4, 8, 12, 16, 20}` theo cùng quy trình đo.
- Vẽ `log(thời gian)` theo `log(n)`.
- Ước lượng hệ số góc và chỉ diễn giải là độ phức tạp thực nghiệm, phụ thuộc cài đặt và cấu hình máy.

> **Hình 8.2.** Biểu đồ log-log thời gian chạy theo kích thước `n`.

| Thuật toán | Miền `n` | Hệ số góc ước lượng | Độ phù hợp `[R² nếu có]` | Nhận xét |
|---|---|---:|---:|---|
| [Thuật toán 1] | 4-20 | [Điền] | [Điền] | [Điền] |
| [Thuật toán 2] | 4-20 | [Điền] | [Điền] | [Điền] |

## 8.7. Thảo luận tổng hợp

- So sánh tính hợp lệ, hiệu quả, tỷ lệ thành công và trường hợp thất bại.
- Nêu tác động của ngẫu nhiên, seed và số lượt thử.
- Trả lời câu hỏi 6: vì sao cần nhiều lần chạy và cố định điều kiện khi đánh giá thuật toán ngẫu nhiên?
- Nêu giới hạn: số cấu hình, thời gian đo, phần cứng, lựa chọn siêu tham số và khả năng khái quát hóa.

## 8.8. Bài nâng cao - tùy chọn

- Mô tả toán tử di chuyển cục bộ khác.
- Giữ nguyên quy trình benchmark để so sánh với toán tử ban đầu.
- Chỉ thực hiện sau khi tám bài bắt buộc đã hoàn thành và kiểm thử.

## 8.9. Kiểm thử tích hợp và khả năng tái lập

- Restart kernel và `Run All` thành công cho cả hai notebook.
- Không phụ thuộc biến từ lần chạy cũ hoặc thứ tự chạy thủ công.
- Không còn `TODO`, `Code and description go here`, tên sinh viên mẫu hoặc đường dẫn Google Drive/cá nhân bắt buộc.
- Giữ bảng, hình và output chứng minh kết quả; loại debug output quá dài.
- Ghi đủ phiên bản môi trường và thư viện.

## 8.10. Kết luận chương

[Tổng kết phát hiện chính, thuật toán phù hợp cho từng bài toán và mức độ đạt yêu cầu thực nghiệm.]

## 8.11. Phân công và đầu ra

- **Thiện:** xây benchmark; lưu từng lượt; tạo bảng 100 lượt; vẽ hội tụ và log-log; viết câu hỏi 6; biên tập, kiểm thử tích hợp.
- **Hải:** bàn giao cấu hình, seed, dữ liệu thô và hình tô màu; dự thảo/review câu hỏi 1-3 và phần kết quả CSP.
- **Ly:** bàn giao API, metrics, history và smoke test của n-Queens; dự thảo/review câu hỏi 4-5 và phần kết quả n-Queens.
- **Đầu ra bắt buộc:** bảng tổng hợp tô màu; bảng n-Queens tối thiểu 100 lượt cho mỗi thiết lập `n = 4, 8`; biểu đồ hội tụ; biểu đồ log-log; nhận xét và QA cuối.
- **Tiêu chí hoàn thành:** hai notebook chạy lại từ đầu; dữ liệu/bảng/hình thống nhất; kết luận có giới hạn rõ ràng; đủ thông tin tái lập.

---

## Kết luận chung

- Tóm tắt mức độ hoàn thành mục tiêu của tám bài.
- So sánh vai trò của tìm kiếm có hệ thống và tìm kiếm cục bộ.
- Nêu những kết quả nổi bật có số liệu hỗ trợ.
- Nêu hạn chế và hướng cải tiến.

## Tài liệu tham khảo

1. Đề bài Lab 04 - Bài toán thỏa mãn ràng buộc.
2. `[Bổ sung giáo trình, tài liệu thuật toán hoặc tài liệu thư viện đã sử dụng theo một chuẩn trích dẫn thống nhất.]`

## Phụ lục A. Bảng trả lời câu hỏi thảo luận

| Câu | Nội dung | Người dự thảo | Chương trình bày |
|---:|---|---|---:|
| 1 | `complete()` và `consistent()` | Hải | 2 |
| 2 | MRV và Forward Checking | Hải | 3-4 |
| 3 | Thất bại của tô màu 3 màu | Hải | 4 |
| 4 | Local optimum/plateau, Random Restart và SA | Ly | 7 |
| 5 | So sánh ba biến thể HC về số lần đánh giá | Ly | 6 |
| 6 | Nhiều lượt chạy và điều kiện thí nghiệm | Thiện | 8 |

## Phụ lục B. Checklist nghiệm thu

### Nội dung bắt buộc

- [ ] Chương 1 có mô hình `X, D, C`, đồ thị, `neighbors` và miền 3/4 màu.
- [ ] Chương 2 có ít nhất 3 test và giải thích `complete/consistent`.
- [ ] Chương 3 có Backtracking, MRV, LCV và bảng so sánh.
- [ ] Chương 4 có Forward Checking, Min-Conflicts và thí nghiệm nhiều `n`/seed.
- [ ] Chương 5 có mô hình n-Queens, `h(board)`, ví dụ `n = 4, 8` và hình bàn cờ.
- [ ] Chương 6 có đủ ba biến thể Hill Climbing và metrics.
- [ ] Chương 7 có Random Restart và SA với ít nhất hai lịch làm nguội.
- [ ] Chương 8 có bảng tối thiểu 100 lượt, biểu đồ hội tụ, biểu đồ log-log và nhận xét tổng hợp.

### Chất lượng và khả năng tái lập

- [ ] Mọi nghiệm báo thành công đều được xác thực độc lập.
- [ ] Các thuật toán được so sánh trên cùng dữ liệu/seed và ngân sách hợp lý.
- [ ] Ghi rõ số lượt, seed, giới hạn bước/restart, lịch làm nguội và cách tính trung bình.
- [ ] Có tối thiểu bốn hình: đồ thị tô màu, bàn cờ n-Queens, hội tụ và log-log.
- [ ] Hai notebook `Run All` thành công trong kernel sạch.
- [ ] Không còn placeholder bắt buộc, lỗi, debug output dài hoặc đường dẫn cá nhân.
- [ ] Có thông tin nhóm, môi trường và phiên bản thư viện.

## Phụ lục C. Nhật ký đóng góp

| Ngày | Thành viên | Chương/bài | Công việc thực hiện | Commit/Minh chứng | Người review |
|---|---|---:|---|---|---|
| [dd/mm] | [Tên] | [Số] | [Mô tả] | [Hash/link] | [Tên] |

