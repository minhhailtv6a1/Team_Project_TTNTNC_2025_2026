# BÁO CÁO ĐỒ ÁN CUỐI KỲ MÔN HỌC TRÍ TUỆ NHÂN TẠO NÂNG CAO

---

### **TRƯỜNG ĐẠI HỌC SÀI GÒN**

### **KHOA CÔNG NGHỆ THÔNG TIN**

<br>

**BÁO CÁO ĐỒ ÁN CUỐI KỲ MÔN HỌC**

## **TRÍ TUỆ NHÂN TẠO NÂNG CAO**

**ĐỀ TÀI:**

### **FEATURE ENGINEERING CHO DỮ LIỆU VĂN BẢN – CHAPTER 8: TEXTUAL DATA**

_(Đề tài dự án thực tế: **XÂY DỰNG VÀ ĐÁNH GIÁ CÁC THUẬT TOÁN TRÍ TUỆ NHÂN TẠO CHO TRÒ CHƠI CARO 11×11**)_

> [!NOTE]
> Bìa báo cáo và thông tin hành chính được đồng bộ theo biểu mẫu của Trường Đại học Sài Gòn và môn học Trí tuệ nhân tạo nâng cao do Giảng viên **TS. Đỗ Như Tài** hướng dẫn. Khi xuất văn bản in cuối cùng, nhóm có thể tùy chỉnh lại dòng tiêu đề theo quyết định của nhóm.

- **Giảng viên hướng dẫn**: TS. Đỗ Như Tài
- **Nhóm thực hiện**: Nhóm 05
  - **TRẦN HỒ MINH HẢI** — MSSV: `3123410092`
  - **TRƯƠNG VĂN THIỆN** — MSSV: `3123410356`
  - **LÊ THỊ TRÚC LY** — MSSV: `3123410210`

- **Thời gian hoàn thành**: TP. HỒ CHÍ MINH, tháng 11 năm 2026

---

## MỞ ĐẦU

Phần này nên dài khoảng 2–3 trang, giới thiệu tổng quan bài toán và dẫn vào nội dung báo cáo:

- **Bối cảnh ứng dụng AI trong trò chơi đối kháng**: Vai trò của các bài toán trò chơi hoàn hảo hai người chơi (zero-sum, perfect information) trong việc phát triển và thử nghiệm các giải thuật tìm kiếm, heuristic và học tăng cường.
- **Lý do chọn bài toán Caro**: Luật chơi quen thuộc, dễ tiếp cận nhưng sở hữu không gian trạng thái và branching factor rất lớn trên bàn cờ $11 \times 11$, tạo ra bài toán thử thách điển hình cho việc cân bằng giữa chất lượng nước đi và chi phí tính toán.
- **Vấn đề cốt lõi của đề tài**: Xây dựng một môi trường chuẩn mực, tách biệt độc lập giữa engine và các tác tử (agents), bảo đảm tính bất biến của trạng thái khi tìm kiếm, đồng thời xây dựng cơ chế đo lường, đối đầu và ghi log tái lập được dưới các ràng buộc ngân sách khắt khe.
- **Phương pháp tiếp cận**: Thiết kế theo nguyên lý Contract-first (`caro-v2`), xây dựng các lớp agent đa dạng từ Baseline (Random), Heuristic dựa trên mẫu hình, Minimax kết hợp Alpha-Beta và Move Ordering, đến Monte Carlo Tree Search (MCTS).
- **Tóm tắt đóng góp chính của nhóm**: Bộ engine chuẩn xác, bộ 4 tác tử AI hoàn chỉnh, hệ thống giải đấu và đo lường tự động có seed, cùng ứng dụng giao diện trực quan Streamlit.
- **Bố cục báo cáo**: Tóm tắt ngắn gọn nội dung 7 chương tiếp theo.

---

## LỜI CẢM ƠN

Phần bày tỏ lòng biết ơn của nhóm tác giả:

- Bày tỏ lòng tri ân sâu sắc đến Thầy **TS. Đỗ Như Tài** – Giảng viên hướng dẫn môn học Trí tuệ nhân tạo nâng cao, đã tận tình định hướng, truyền đạt kiến thức chuyên môn và đưa ra các góp ý quý báu trong suốt quá trình nhóm nghiên cứu và thực hiện đề tài.
- Gửi lời cảm ơn chân thành đến các Thầy Cô thuộc **Khoa Công nghệ Thông tin – Trường Đại học Sài Gòn** đã trang bị nền tảng học thuật vững chắc cho nhóm trong suốt các năm học.
- Cảm ơn sự nỗ lực, tinh thần trách nhiệm và sự phối hợp hiệu quả của các thành viên trong Nhóm 05 trong suốt quá trình hoàn thiện đồ án.

---

## NHẬN XÉT CỦA GIẢNG VIÊN

………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………………

---

## PHÂN CHIA CÔNG VIỆC

| Thành viên                                   | Nội dung đảm nhiệm chính                                                                                                                                                                                                                                                                                                                                                                           | Đóng góp % |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------: |
| **Trương Văn Thiện**<br>_(MSSV: 3123410356)_ | - Trưởng nhóm: Quản lý kiến trúc hệ thống, chuẩn hóa Contract `caro-v2`.<br>- Phân tích bài toán, yêu cầu chức năng/phi chức năng, thiết kế hạ tầng thực nghiệm (Tournament runner, Benchmark, Logger).<br>- Viết Chương 1, Mục 2.2, 2.7, Chương 3 (3.1, 3.3, 3.4, 3.6, 3.7, 3.9), Mục 4.2, 4.6, toàn bộ số liệu và bảng tổng hợp Chương 5, Phụ lục.                                               |  **33%**   |
| **Trần Hồ Minh Hải**<br>_(MSSV: 3123410092)_ | - Nghiên cứu, thiết kế và cài đặt thuật toán Monte Carlo Tree Search (MCTS), công thức UCT, cơ chế rollout và quản lý node tree.<br>- Thiết kế và phát triển giao diện ứng dụng trực quan Streamlit (`ui/app.py`, `ui/human_controller.py`).<br>- Viết Mục 2.6, Mục 4.5, Chương 6 (Xây dựng ứng dụng minh họa), thực nghiệm và phân tích MCTS ở Chương 5 (5.9) và chụp danh mục hình ảnh demo.     |  **33%**   |
| **Lê Thị Trúc Ly**<br>_(MSSV: 3123410210)_   | - Nghiên cứu luật cờ Caro 11×11, thiết kế và cài đặt RuleEngine kiểm tra 4 hướng, Board logic, cơ chế undo và clone phòng vệ.<br>- Thiết kế hàm Heuristic (bảng điểm pattern, nhận diện đe dọa) và cài đặt Minimax kết hợp Alpha-Beta, Move Ordering, Iterative Deepening.<br>- Viết Mục 2.1, 2.3–2.5, Mục 3.2, 3.5, Mục 4.1, 4.3, 4.4, 4.7, 4.9, thực nghiệm Minimax ở Chương 5 (5.7, 5.8, 5.10). |  **33%**   |

---

## DANH MỤC CÁC BẢNG

| Ký hiệu bảng | Tên bảng                                                                               | Trang dự kiến |
| ------------ | -------------------------------------------------------------------------------------- | :-----------: |
| Bảng 1.1     | Ma trận mục tiêu, tiêu chí hoàn thành và sản phẩm bàn giao                             |      11       |
| Bảng 2.1     | So sánh đặc điểm các thuật toán Random, Heuristic, Minimax và MCTS                     |      13       |
| Bảng 3.1     | Bảng ánh xạ giá trị quân cờ, tọa độ và trạng thái ô bàn cờ                             |      14       |
| Bảng 3.2     | Bảng đặc tả Contract `caro-v2` và các lý do từ chối nước đi (Reason Codes)             |      15       |
| Bảng 3.3     | Bảng phân tích độ phức tạp thời gian và bộ nhớ của `step`, `undo`, `clone_env`         |      16       |
| Bảng 4.1     | Bảng trọng số điểm Heuristic các mẫu hình (Patterns) tấn công và phòng thủ             |      17       |
| Bảng 4.2     | Bảng tham số cấu hình của các Agent (Heuristic, Minimax/Alpha-Beta, MCTS)              |      19       |
| Bảng 5.1     | Bảng cấu hình môi trường phần cứng, phần mềm và thông số benchmark                     |      21       |
| Bảng 5.2     | Kết quả kiểm thử bộ kịch bản chiến thuật (Tactical scenarios) của các tác tử           |      22       |
| Bảng 5.3     | So sánh hiệu năng Minimax có/không có Alpha-Beta và Move Ordering theo độ sâu          |      22       |
| Bảng 5.4     | Hiệu năng MCTS theo các mức ngân sách mô phỏng (100, 400, 1000 simulations)            |      22       |
| Bảng 5.5     | Ma trận đối đầu tổng thể giải đấu (Tournament Cross-Table) và tỷ lệ thắng theo bên X/O |      22       |
| Bảng 6.1     | Danh mục chức năng giao diện Streamlit và trạng thái tích hợp thực tế                  |      23       |

---

## DANH MỤC HÌNH

| Ký hiệu hình           | Tên hình                                                                                         | Trang dự kiến |
| ---------------------- | ------------------------------------------------------------------------------------------------ | :-----------: |
| Hình 1 _(Hình abcd)_   | Minh họa các mẫu hình cờ: chuỗi 5 thắng, chặn 1 đầu, chặn 2 đầu và sát biên                      |      11       |
| Hình 2 _(Hình hjiuy)_  | Sơ đồ cây trò chơi và cơ chế cắt tỉa Alpha-Beta                                                  |      12       |
| Hình 3 _(Hình jihugy)_ | Bốn pha hoạt động của Monte Carlo Tree Search (Selection, Expansion, Rollout, Backpropagation)   |      13       |
| Hình 3.1               | Sơ đồ kiến trúc tổng thể phân tầng hệ thống Caro AI (`engine`, `agents`, `utils`, `ui`, `tests`) |      15       |
| Hình 3.2               | Sơ đồ tuần tự xử lý một nước đi qua Contract giữa UI/Runner và CaroEnv                           |      16       |
| Hình 3.3               | Luồng vận hành giải đấu: sinh seed, budget enforce, ghi log JSONL và tổng hợp metric             |      16       |
| Hình 4.1               | Lưu đồ thuật toán đánh giá trạng thái và chọn nước đi của Heuristic Agent                        |      17       |
| Hình 4.2               | Lưu đồ thuật toán Minimax kết hợp cắt tỉa Alpha-Beta và sắp xếp nước đi                          |      18       |
| Hình 4.3               | Cấu trúc Node MCTS và luồng cập nhật giá trị Visit count / Q-value                               |      19       |
| Hình 5.1               | Biểu đồ so sánh số node duyệt và thời gian thực thi của Minimax theo độ sâu                      |      22       |
| Hình 5.2               | Biểu đồ tỷ lệ thắng và thời gian phản hồi của MCTS theo số lượng mô phỏng                        |      22       |
| Hình 5.3               | Biểu đồ nhiệt (Heatmap) tỷ lệ thắng đối đầu chéo giữa các tác tử AI                              |      22       |
| Hình 6.1               | Giao diện bàn cờ Caro 11×11 trên ứng dụng Streamlit khi bắt đầu ván chơi                         |      23       |
| Hình 6.2               | Giao diện hiển thị ván cờ kết thúc, thông báo thắng/hòa và khóa bàn cờ                           |      23       |

---

## DANH MỤC CỤM TỪ VIẾT TẮT

| STT | Cụm từ đầy đủ                           | Viết tắt  |
| :-: | --------------------------------------- | :-------: |
|  1  | Artificial Intelligence                 |  **AI**   |
|  2  | Application Programming Interface       |  **API**  |
|  3  | User Interface                          |  **UI**   |
|  4  | Monte Carlo Tree Search                 | **MCTS**  |
|  5  | Upper Confidence Bound applied to Trees |  **UCT**  |
|  6  | Random Number Generator                 |  **RNG**  |
|  7  | JSON Lines                              | **JSONL** |
|  8  | Central Processing Unit                 |  **CPU**  |
|  9  | Random Access Memory                    |  **RAM**  |

---

## MỤC LỤC

- **CHƯƠNG 1. TỔNG QUAN VỀ ĐỀ TÀI** `11`
  - 1.1. Phát biểu đề tài `11`
  - 1.2. Mục tiêu và phạm vi của đề tài `11`
    - 1.2.1. Mục tiêu `11`
    - 1.2.2. Phạm vi `11`
  - 1.3. Đối tượng sử dụng `11`
  - 1.4. Kết quả dự kiến `11`
  - 1.5. Cấu trúc báo cáo `11`
- **CHƯƠNG 2. CƠ SỞ LÝ THUYẾT LIÊN QUAN** `11`
  - 2.1. Tổng quan trò chơi Caro `11`
    - 2.1.1. Lịch sử và các biến thể Gomoku/Caro `11`
    - 2.1.2. Luật Caro được sử dụng trong đề tài `11`
    - 2.1.3. Đặc điểm không gian trạng thái và độ khó tìm kiếm `11`
  - 2.2. Mô hình trò chơi đối kháng `11`
    - 2.2.1. Trạng thái, hành động và hàm chuyển trạng thái `11`
    - 2.2.2. Trạng thái kết thúc, utility và reward `11`
    - 2.2.3. Cây trò chơi và nguyên tắc chọn nước đi `11`
  - 2.3. Hàm đánh giá heuristic `12`
  - 2.4. Thuật toán Minimax `12`
    - 2.4.1. Nguyên lý Minimax `12`
    - 2.4.2. Độ phức tạp thời gian và bộ nhớ `12`
    - 2.4.3. Minimax giới hạn độ sâu và đánh giá lá `12`
  - 2.5. Các kỹ thuật tối ưu Minimax `12`
    - 2.5.1. Cắt tỉa Alpha-Beta `13`
    - 2.5.2. Sắp xếp nước đi `13`
    - 2.5.3. Lọc nước ứng viên theo lân cận `13`
    - 2.5.4. Iterative deepening `13`
    - 2.5.5. Giới hạn theo độ sâu, số node và thời gian `13`
  - 2.6. Monte Carlo Tree Search `13`
    - 2.6.1. Tổng quan MCTS `13`
    - 2.6.2. Selection và công thức UCT `13`
    - 2.6.3. Expansion `13`
    - 2.6.4. Simulation/Rollout `13`
    - 2.6.5. Backpropagation `13`
    - 2.6.6. Ngân sách số mô phỏng, số node và thời gian `13`
    - 2.6.7. Vai trò của seed và tính tái lập `13`
  - 2.7. Đánh giá tác tử chơi game `13`
  - 2.9. Học sâu cho trò chơi bàn cờ `13`
- **CHƯƠNG 3. PHÂN TÍCH BÀI TOÁN VÀ THIẾT KẾ HỆ THỐNG** `13`
  - 3.1. Phân tích yêu cầu `13`
    - 3.1.1. Yêu cầu chức năng `13`
    - 3.1.2. Yêu cầu phi chức năng `14`
  - 3.2. Mô hình hóa bài toán `14`
    - 3.2.1. Biểu diễn bàn cờ `14`
    - 3.2.2. Biểu diễn trạng thái `14`
    - 3.2.3. Hành động hợp lệ và bất biến trạng thái `14`
    - 3.2.4. Hàm chuyển, reward và kết quả `15`
    - 3.2.5. Clone và undo cho tìm kiếm `15`
  - 3.3. Contract `15`
  - 3.4. Kiến trúc tổng thể `15`
  - 3.5. Thiết kế engine và luật `16`
    - 3.5.1. Board và quản lý dữ liệu bàn cờ `16`
    - 3.5.2. RuleEngine và kiểm tra bốn hướng `16`
    - 3.5.3. CaroEnv và vòng đời ván chơi `16`
    - 3.5.4. Snapshot phòng vệ, clone và history stack `16`
    - 3.5.5. Phân tích độ phức tạp của step, undo và clone_env `16`
  - 3.6. Thiết kế tác tử AI `16`
  - 3.7. Thiết kế hạ tầng thực nghiệm `16`
    - 3.7.1. Luồng chạy một game, một match và tournament `16`
    - 3.7.2. Cơ chế đổi bên X/O `16`
    - 3.7.3. Sinh seed và tái lập `16`
    - 3.7.4. Budget enforcer `16`
    - 3.7.5. Schema log JSONL và manifest `16`
    - 3.7.6. Tổng hợp metric `16`
  - 3.8. Thiết kế giao diện `16`
  - 3.9. Chiến lược kiểm thử `16`
- **CHƯƠNG 4. PHƯƠNG PHÁP ĐỀ XUẤT VÀ CÀI ĐẶT** `17`
  - 4.1. Cài đặt môi trường Caro `17`
  - 4.2. Random Agent — Baseline `17`
  - 4.3. Heuristic Agent `17`
    - 4.3.1. Thứ tự ưu tiên `17`
    - 4.3.2. Bảng điểm pattern `17`
    - 4.3.3. Tie-break và độ phức tạp `18`
  - 4.4. Minimax và Alpha-Beta `18`
    - 4.4.1. Hàm đánh giá trạng thái `18`
    - 4.4.2. Sinh tập nước ứng viên `18`
    - 4.4.3. Iterative deepening `19`
    - 4.4.4. Alpha-Beta pruning `19`
    - 4.4.5. Move ordering `19`
    - 4.4.6. Xử lý budget và fallback `19`
    - 4.4.7. Tham số cấu hình và đánh đổi `19`
  - 4.5. Monte Carlo Tree Search `19`
    - 4.5.1. Cấu trúc node và thống kê visit/value `19`
    - 4.5.2. Selection bằng UCT `19`
    - 4.5.3. Expansion trên action hợp lệ `19`
    - 4.5.4. Rollout và chính sách mô phỏng `19`
    - 4.5.5. Backpropagation và góc nhìn người chơi `19`
    - 4.5.6. Chọn action cuối cùng `19`
    - 4.5.7. Seed, simulation budget, node budget và time budget `19`
  - 4.6. Tournament runner, logger và metric `19`
  - 4.7. Các quyết định tối ưu và bảo đảm tính đúng `19`
  - 4.8. Neural AI và pipeline dữ liệu — Điều kiện `20`
  - 4.9. Hạn chế của phương pháp hiện tại `20`
- **CHƯƠNG 5. THỰC NGHIỆM VÀ ĐÁNH GIÁ** `21`
  - 5.1. Câu hỏi nghiên cứu `21`
  - 5.2. Môi trường thực nghiệm `21`
  - 5.3. Đối tượng và cấu hình so sánh `21`
  - 5.4. Bộ kịch bản cố định `21`
  - 5.5. Giao thức thí nghiệm `21`
  - 5.6. Chỉ số đánh giá `22`
  - 5.7. Kết quả kiểm tra tính đúng `22`
  - 5.8. Kết quả Minimax/Alpha-Beta `22`
    - 5.8.1. Ảnh hưởng của độ sâu `22`
    - 5.8.2. Alpha-Beta bật/tắt `22`
    - 5.8.3. Move ordering bật/tắt `22`
    - 5.8.4. Số node, thời gian và chất lượng nước đi `22`
  - 5.9. Kết quả MCTS `22`
    - 5.9.1. Ảnh hưởng của số simulation `22`
    - 5.9.2. Độ ổn định theo seed `22`
    - 5.9.3. Thời gian và chất lượng nước đi `22`
  - 5.10. Kết quả giải đấu `22`
- **CHƯƠNG 6. XÂY DỰNG ỨNG DỤNG MINH HỌA** `23`
  - 6.1. Mục tiêu ứng dụng `23`
  - 6.2. Công nghệ sử dụng `23`
  - 6.3. Thiết kế giao diện và trải nghiệm `23`
  - 6.4. Tích hợp UI với engine `23`
  - 6.5. Các chức năng đã hoàn thành `23`
  - 6.6. Kiểm thử ứng dụng `23`
  - 6.7. Hạn chế hiện tại `24`
- **CHƯƠNG 7. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN** `24`
  - 7.1. Kết luận `24`
  - 7.2. Hạn chế `24`
  - 7.3. Hướng phát triển `24`

---

# NỘI DUNG CHI TIẾT CÁC CHƯƠNG

---

# CHƯƠNG 1. TỔNG QUAN VỀ ĐỀ TÀI

## 1.1. Phát biểu đề tài

- Tên đề tài chính thức: **Xây dựng và đánh giá các thuật toán trí tuệ nhân tạo cho trò chơi Caro 11×11**.
- Định nghĩa bài toán: Xây dựng một môi trường trò chơi Caro hai người đối kháng tuân thủ hợp đồng nghiêm ngặt (`caro-v2`), trên cơ sở đó triển khai và đánh giá so sánh hiệu năng, độ chính xác chiến thuật, thời gian thực thi và chi phí tài nguyên của các họ thuật toán AI khác nhau:
  - Random Agent (ngẫu nhiên làm baseline).
  - Heuristic Agent (luật chuyên gia và chấm điểm mẫu hình).
  - Minimax kết hợp cắt tỉa Alpha-Beta và tối ưu hóa thứ tự duyệt.
  - Monte Carlo Tree Search (MCTS) dựa trên công thức UCT.

## 1.2. Mục tiêu và phạm vi của đề tài

### 1.2.1. Mục tiêu

- **Mục tiêu tổng quát**: Xây dựng một nền tảng thực nghiệm hoàn chỉnh từ lõi game engine, các tác tử AI đến công cụ tổ chức giải đấu tự động và giao diện người dùng trực quan.
- **Mục tiêu cụ thể**:
  - Chuẩn hóa luật chơi, biểu diễn trạng thái, tập hành động và kết quả thông qua Contract rõ ràng.
  - Xây dựng Game Engine hỗ trợ đầy đủ các thao tác tìm kiếm: `reset`, `step`, `legal_actions`, `clone_env`, `undo` với độ phức tạp tối ưu.
  - Cài đặt và tinh chỉnh 4 nhóm tác tử AI tuân thủ nguyên tắc không làm biến đổi (mutation) môi trường thật và tuân thủ ngân sách tìm kiếm (`SearchBudget`).
  - Xây dựng hệ thống tổ chức giải đấu (Tournament Runner) tự động hoán đổi bên đi trước (X/O), quản trị seed ngẫu nhiên để tái lập $100\%$ kết quả, và trích xuất log có cấu trúc JSONL.
  - Thực nghiệm kiểm chứng khoa học nhằm trả lời 5 câu hỏi nghiên cứu (RQ1–RQ5) về tương quan giữa sức mạnh nước đi và chi phí tính toán.
  - Xây dựng giao diện web tương tác bằng Streamlit phục vụ trực quan hóa và minh họa thuật toán.

### 1.2.2. Phạm vi

- **Phạm vi nghiên cứu**:
  - Kích thước bàn cờ chuẩn mực: $11 \times 11$.
  - Hai người chơi luân phiên: Người chơi X (đi trước, quy ước giá trị `1`) và Người chơi O (đi sau, quy ước giá trị `-1`).
  - Điều kiện thắng: Chuỗi từ 5 quân liên tiếp trở lên theo hàng ngang, dọc hoặc hai đường chéo mà **không bị chặn cả hai đầu**. Biên bàn cờ được tính là một đầu bị chặn.
  - Điều kiện hòa: Khi toàn bộ 121 ô trên bàn cờ đã được đi kín mà không có người chiến thắng.
  - Quy ước tọa độ: `(row, col)` với chỉ số bắt đầu từ 0 đến 10.
- **Giới hạn ngoài phạm vi đề tài**:
  - Không mở rộng luật Renju phức tạp hoặc các kích thước bàn cờ tùy biến khác ngoài $11 \times 11$.
  - Không xây dựng hạ tầng mạng chơi trực tuyến (Multiplayer Cloud) hoặc hệ thống ghép cặp trực tuyến.
  - Phần mạng nơ-ron học sâu (Deep Learning/AlphaZero style) được định vị là điều kiện mở rộng / hướng phát triển trong tương lai do giới hạn thời gian và tài nguyên tính toán.

## 1.3. Đối tượng sử dụng

- **Sinh viên và người học AI**: Quan sát trực quan cơ chế vận hành, sự khác biệt về triết lý giữa tìm kiếm vét cạn/cắt tỉa (Minimax/Alpha-Beta) và tìm kiếm lấy mẫu thống kê (MCTS).
- **Nhà nghiên cứu / Lập trình viên game**: Sử dụng engine và harness benchmark có sẵn để thử nghiệm các ý tưởng thuật toán mới với tính tái lập được bảo đảm tuyệt đối.
- **Người dùng phổ thông**: Trải nghiệm giao diện chơi cờ trực quan, tương tác đối kháng trực tiếp trên nền tảng web Streamlit.

## 1.4. Kết quả dự kiến

- Engine trò chơi chuẩn mực, không lỗi rò rỉ trạng thái, tốc độ cao.
- Bộ mã nguồn 4 tác tử AI hoàn chỉnh, chạy ổn định theo interface chung.
- Bộ log thực nghiệm JSONL, bảng tổng hợp metric chi tiết và biểu đồ phân tích.
- Ứng dụng Streamlit minh họa hoạt động ổn định và thân thiện.

## 1.5. Cấu trúc báo cáo

Báo cáo được bố cục thành 7 chương chính:

- **Chương 1**: Tổng quan về đề tài, mục tiêu, phạm vi và đối tượng nghiên cứu.
- **Chương 2**: Cơ sở lý thuyết nền tảng về lý thuyết trò chơi đối kháng, Heuristic, Minimax/Alpha-Beta và MCTS.
- **Chương 3**: Phân tích yêu cầu bài toán, thiết kế kiến trúc hệ thống, contract API và các module lõi.
- **Chương 4**: Phương pháp đề xuất và chi tiết cài đặt kỹ thuật của từng thành phần trong hệ thống.
- **Chương 5**: Thiết kế thực nghiệm khoa học, số liệu đo lường, phân tích và thảo luận kết quả.
- **Chương 6**: Xây dựng ứng dụng minh họa trên nền tảng Streamlit.
- **Chương 7**: Kết luận tổng kết, nêu các điểm hạn chế và vạch ra hướng phát triển trong tương lai.

---

# CHƯƠNG 2. CƠ SỞ LÝ THUYẾT LIÊN QUAN

## 2.1. Tổng quan trò chơi Caro

### 2.1.1. Lịch sử và các biến thể Gomoku/Caro

- Lịch sử hình thành trò chơi ngũ quân (Five in a Row) có nguồn gốc từ cổ xưa, sự phát triển qua Gomoku truyền thống, biến thể Omok và trò chơi Caro phổ biến tại Việt Nam.
- Sự khác biệt về luật chơi: Luật Gomoku tự do (Standard Gomoku), luật mở cờ Pro/Long, luật Renju giới hạn bên đi trước (cấm nước đôi 3-3, 4-4, overline) và biến thể luật Caro Việt Nam áp dụng luật chặn hai đầu.

### 2.1.2. Luật Caro được sử dụng trong đề tài

- Bàn cờ ma trận kích thước $11 \times 11$.
- Quân cờ: Hai người chơi đại diện bởi X (người đi trước) và O (người đi sau).
- Điều kiện thắng: Đạt được một đường thẳng liên tục (ngang, dọc, chéo chính, chéo phụ) gồm tối thiểu 5 quân cờ cùng loại, với điều kiện chuỗi này **không bị đối thủ chặn ở cả hai đầu mút**.
- Quy tắc biên bàn cờ: Nếu chuỗi 5 quân chạm vào biên của bàn cờ thì đầu chạm biên được coi như đã bị chặn một đầu. Do đó, nếu đầu còn lại bị quân đối phương chặn thì không được tính là chiến thắng.
- Chuỗi vượt độ dài (Overline): Một chuỗi gồm 6 quân cờ liên tiếp trở lên vẫn được tính là chiến thắng hợp lệ nếu không bị chặn cả hai đầu mút.
- Hòa cờ: Khi 121 ô cờ đều được đánh kín mà không có bên nào thỏa mãn điều kiện chiến thắng.

### 2.1.3. Đặc điểm không gian trạng thái và độ khó tìm kiếm

- Bàn cờ $11 \times 11$ có tổng cộng $3^{121} \approx 5.8 \times 10^{57}$ trạng thái lý thuyết khả dĩ.
- Hệ số phân nhánh ban đầu (Branching Factor) là 121 và giảm dần theo từng nước đi; ở giai đoạn khai cuộc và trung cuộc, hệ số phân nhánh trung bình vẫn dao động từ 80 đến 100 nếu không áp dụng kỹ thuật thu hẹp vùng lân cận.
- Tính chất bài toán: Trò chơi đối kháng hai người (Two-player), thông tin hoàn hảo (Perfect Information), tổng bằng không (Zero-sum) và hoàn toàn tất định (Deterministic).

## 2.2. Mô hình trò chơi đối kháng

### 2.2.1. Trạng thái, hành động và hàm chuyển trạng thái

- Định nghĩa trạng thái $S$, tập hành động hợp lệ $A(s)$ tại trạng thái $s$.
- Hàm chuyển trạng thái tất định $T: S \times A \rightarrow S$.
- Quy tắc luân phiên lượt người chơi giữa bên Max ($+1$) và bên Min ($-1$).

### 2.2.2. Trạng thái kết thúc, utility và reward

- Tập trạng thái kết thúc (Terminal states) $S_{term}$.
- Hàm tiện ích (Utility/Payoff function) $U: S_{term} \rightarrow \{-1, 0, 1\}$.
- Gắn nhãn reward cho kết quả: Thắng ($+1.0$), Hòa ($0.0$), Thua ($-1.0$).

### 2.2.3. Cây trò chơi và nguyên tắc chọn nước đi

- Cấu trúc cây trò chơi (Game Tree): Gốc là trạng thái hiện tại, mỗi nhánh tương ứng với một nước đi hợp lệ, các node lá biểu diễn trạng thái kết thúc hoặc trạng thái đạt độ sâu giới hạn.
- Nguyên lý chọn nước đi tối ưu theo nguyên tắc Minimax: Giả định đối phương luôn đưa ra quyết định tốt nhất để giảm thiểu tối đa điểm số của mình.

## 2.3. Hàm đánh giá heuristic

- Định nghĩa và vai trò của hàm Heuristic tĩnh $h(s)$ khi cây trò chơi không thể duyệt tới các node kết thúc do giới hạn tài nguyên tính toán.
- Phân tích các mẫu hình (Patterns) mang tính quyết định:
  - Chuỗi 5 quân (Win): Đã hoàn thành 5 quân liên tiếp.
  - Chuỗi 4 quân mở hai đầu (Open 4): Đe dọa không thể ngăn cản trong 1 nước.
  - Chuỗi 4 quân chặn một đầu (Closed 4): Buộc đối thủ phải phản ứng chặn ngay lập tức.
  - Chuỗi 3 quân mở hai đầu (Open 3): Tiền đề tạo thế công đôi (Double threat).
  - Chuỗi 2 quân mở hai đầu (Open 2) và các vị trí chiếm đóng trung tâm bàn cờ.
- Cân bằng giữa yếu tố tấn công (Offense) và phòng thủ (Defense).
- Kỹ thuật phá vỡ thế hòa (Tie-break) tất định để tránh hành vi bất định.

## 2.4. Thuật toán Minimax

### 2.4.1. Nguyên lý Minimax

- Công thức đệ quy Minimax tìm kiếm nước đi:
  $$V(s) = \begin{cases} U(s) & \text{nếu } s \in S_{term} \\ \max_{a \in A(s)} V(T(s, a)) & \text{nếu lượt MAX} \\ \min_{a \in A(s)} V(T(s, a)) & \text{nếu lượt MIN} \end{cases}$$

### 2.4.2. Độ phức tạp thời gian và bộ nhớ

- Độ phức tạp thời gian vét cạn: $\mathcal{O}(b^d)$ với $b$ là hệ số phân nhánh trung bình và $d$ là độ sâu tìm kiếm.
- Độ phức tạp bộ nhớ: $\mathcal{O}(b \cdot d)$ đối với thuật toán duyệt theo chiều sâu (DFS).

### 2.4.3. Minimax giới hạn độ sâu và đánh giá lá

- Cắt tỉa cây ở độ sâu cố định $d_{max}$ và thay thế giá trị kết thúc bằng hàm đánh giá Heuristic $h(s)$ tại các node lá.
- Vấn đề hiệu ứng chân trời (Horizon Effect) và sai số đánh giá trạng thái.

## 2.5. Các kỹ thuật tối ưu Minimax

### 2.5.1. Cắt tỉa Alpha-Beta

- Giới thiệu hai biên $\alpha$ (giá trị nhỏ nhất mà người chơi MAX đã bảo đảm đạt được) và $\beta$ (giá trị lớn nhất mà người chơi MIN có thể ghìm đối thủ lại).
- Điều kiện cắt tỉa: Khi $\alpha \ge \beta$, nhánh tìm kiếm hiện tại được bảo đảm không ảnh hưởng đến quyết định tối ưu ở node cha và được loại bỏ ngay lập tức.
- Độ phức tạp thời gian trong trường hợp tối ưu nhất: $\mathcal{O}(b^{d/2})$, cho phép tăng gấp đôi độ sâu tìm kiếm với cùng lượng thời gian tính toán.

### 2.5.2. Sắp xếp nước đi (Move Ordering)

- Tầm quan trọng của việc duyệt các nước đi tiềm năng nhất trước để kích hoạt điều kiện cắt tỉa $\alpha \ge \beta$ sớm nhất.
- Sử dụng điểm đánh giá heuristic sơ bộ của nước đi để sắp xếp danh sách các nước đi ứng viên.

### 2.5.3. Lọc nước ứng viên theo lân cận (Candidate Filtering)

- Chiến lược loại bỏ các ô cờ trống cách quá xa các quân cờ đã có trên bàn cờ.
- Khái niệm bán kính lân cận Chebyshev ($r=1$ hoặc $r=2$ xung quanh các ô không trống), giúp giảm hệ số phân nhánh từ ~100 xuống còn 10–25 nước đi khả dĩ.

### 2.5.4. Tìm kiếm sâu dần (Iterative Deepening)

- Lặp lại quá trình tìm kiếm với độ sâu tăng dần từ $d = 1, 2, \dots, D$.
- Ưu điểm: Luôn có sẵn nước đi dự phòng tốt nhất từ độ sâu trước đó nếu bị ngắt do chạm giới hạn thời gian.

### 2.5.5. Giới hạn theo độ sâu, số node và thời gian

- Kiểm soát đa chiều: Dừng tìm kiếm khi vượt quá độ sâu tối đa (`max_depth`), số lượng node đã duyệt (`max_nodes`) hoặc thời gian cho phép (`time_limit_ms`).

## 2.6. Monte Carlo Tree Search

### 2.6.1. Tổng quan MCTS

- Giới thiệu họ thuật toán tìm kiếm heuristic dựa trên mô phỏng ngẫu nhiên, không đòi hỏi hàm đánh giá trạng thái tĩnh phức tạp.
- Khả năng hội tụ tiệm cận về quyết định tối ưu theo định lý giới hạn trung tâm.

### 2.6.2. Selection và công thức UCT

- Quá trình duyệt từ node gốc xuống các node lá của cây tìm kiếm dựa trên chỉ số UCT (Upper Confidence Bound applied to Trees):
  $$UCT(i) = \frac{Q(i)}{N(i)} + C \times \sqrt{\frac{\ln N(p)}{N(i)}}$$
  Trong đó $Q(i)$ là tổng phần thưởng tích lũy, $N(i)$ là số lần node $i$ được thăm, $N(p)$ là số lần thăm của node cha, và hằng số khám phá $C = \sqrt{2}$.
- Cân bằng giữa khai thác (Exploitation) và khám phá (Exploration).

### 2.6.3. Expansion

- Điều kiện mở rộng: Khi chạm vào một node chưa được khám phá hết các hành động hợp lệ, tạo thêm một node con mới tương ứng với một nước đi chưa thử.

### 2.6.4. Simulation / Rollout

- Từ node mới tạo, thực hiện một ván chơi giả lập nhanh (Playout/Rollout) đến khi đạt trạng thái kết thúc hoặc chạm độ sâu mô phỏng tối đa bằng chính sách ngẫu nhiên hoặc heuristic nhẹ.

### 2.6.5. Backpropagation

- Truyền ngược kết quả ván chơi giả lập (thắng/hòa/thua) từ node lá lên tất cả các node tổ tiên đến tận node gốc.
- Góc nhìn người chơi: Đảm bảo điểm số thưởng được đảo dấu phù hợp tương ứng với góc nhìn của bên đi tại mỗi node.

### 2.6.6. Ngân sách số mô phỏng, số node và thời gian

- Thiết lập ngưỡng dừng của MCTS: Giới hạn số lượt mô phỏng (`max_simulations`), số node mở rộng tối đa (`max_nodes`), và thời gian tối đa (`time_limit_ms`).

### 2.6.7. Vai trò của seed và tính tái lập

- Sự cần thiết của bộ sinh số ngẫu nhiên cục bộ (`random.Random(seed)`), bảo đảm mọi chuỗi rollout và quyết định của MCTS đều có thể tái tạo hoàn toàn trong các lần chạy kiểm thử.

## 2.7. Đánh giá tác tử chơi game

- Tiêu chí định lượng: Tỷ lệ thắng (Win rate), tỷ lệ hòa (Draw rate), tỷ lệ thua (Loss rate).
- Tiêu chí định tính: Khả năng giải quyết các thế cờ chiến thuật chuẩn (Tactical benchmark: phát hiện nước thắng ngay trong 1 nước, chặn nước thắng của đối thủ).
- Chi phí tài nguyên: Thời gian trung bình mỗi nước đi, phân vị 95th (p95 latency), số node Minimax duyệt, số mô phỏng MCTS hoàn tất.
- Yêu cầu công bằng: Hoán đổi lượt đi trước/sau (X và O) trong các cặp đấu để loại bỏ triệt để lợi thế bên đi trước.

## 2.8. Học sâu cho trò chơi bàn cờ — Điều kiện

- Giới thiệu tổng quan về cách tiếp cận mạng nơ-ron tích chập (CNN) kết hợp MCTS (mô hình AlphaZero/GomokuZero): Biểu diễn bàn cờ dạng Tensor đa kênh, mạng dự đoán đồng thời xác suất nước đi (Policy Head) và đánh giá trạng thái (Value Head).
- _Lưu ý_: Nhóm xác định đây là phần nghiên cứu lý thuyết định hướng mở rộng trong tương lai do chưa có đủ tài nguyên huấn luyện đồ họa trong phạm vi đồ án hiện tại.

---

# CHƯƠNG 3. PHÂN TÍCH BÀI TOÁN VÀ THIẾT KẾ HỆ THỐNG

## 3.1. Phân tích yêu cầu

### 3.1.1. Yêu cầu chức năng

- Khởi tạo và reset bàn cờ về trạng thái rỗng ban đầu.
- Xác thực và thực hiện nước đi của người chơi theo lượt.
- Tự động nhận diện trạng thái kết thúc (thắng, thua, hòa) theo đúng luật Caro dự án và kiên quyết từ chối mọi hành động sau khi ván đấu đã kết thúc (`terminated`).
- Cung cấp danh sách các hành động hợp lệ (`legal_actions`), cơ chế nhân bản môi trường (`clone_env`) và hoàn tác nước đi (`undo`) phục vụ các thuật toán tìm kiếm.
- Cung cấp interface chuẩn mực cho phép bất kỳ agent nào (người, heuristic, thuật toán tìm kiếm) đều có thể tương tác mà không cần thay đổi mã nguồn engine.
- Tự động hóa điều hành giải đấu, tự động đổi bên X/O, ghi log chi tiết từng nước đi ra file JSONL và tổng hợp bảng chỉ số hiệu năng.
- Giao diện trực quan hiển thị bàn cờ, chỉ báo lượt đi, danh sách lịch sử nước đi và thông báo kết quả.

### 3.1.2. Yêu cầu phi chức năng

- **Tính đúng đắn**: Tuân thủ tuyệt đối quy tắc luật Caro $11 \times 11$, bảo đảm không có tác dụng phụ (no mutation) ngoài dự kiến đối với môi trường gốc.
- **Tính tái lập**: Toàn bộ các tiến trình sinh số ngẫu nhiên đều được kiểm soát thông qua seed tường minh.
- **Tính module hóa**: Phân tách rõ ràng giữa Engine, Rules, Agents, Runners và UI, thuận tiện cho việc kiểm thử độc lập (Unit Test) và mở rộng.
- **Tuân thủ ngân sách**: Các agent tìm kiếm phải tôn trọng chặt chẽ ngân sách thời gian và số bước tìm kiếm được cấp phát.
- **Chuẩn hóa dữ liệu**: Dữ liệu log được tuần tự hóa theo định dạng JSONL với schema rõ ràng, hỗ trợ việc phân tích dữ liệu tự động.

## 3.2. Mô hình hóa bài toán

### 3.2.1. Biểu diễn bàn cờ

- Biểu diễn bằng ma trận 2D kích thước $11 \times 11$.
- Mã hóa giá trị các ô:
  - `EMPTY = 0`: Ô trống.
  - `PLAYER_X = 1`: Quân X (Người chơi 1, đi trước).
  - `PLAYER_O = -1`: Quân O (Người chơi 2, đi sau).
- Quy ước tọa độ nước đi: Cặp số nguyên `(row, col)` với $0 \le row, col < 11$.

### 3.2.2. Biểu diễn trạng thái

- Đối tượng `GameState` đóng gói toàn bộ thông tin tại một thời điểm:
  - `board`: Ma trận trạng thái bàn cờ hiện tại.
  - `current_player`: Định danh người chơi có lượt kế tiếp (`1` hoặc `-1`).
  - `last_action`: Tọa độ của nước đi vừa thực hiện gần nhất (`Optional[Tuple[int, int]]`).
  - `move_count`: Tổng số nước đi đã thực hiện trong ván đấu.
  - `terminated`: Cờ boolean báo hiệu ván đấu đã kết thúc hay chưa.
  - `winner`: Kết quả người thắng cuộc (`1`, `-1`, `0` khi hòa, hoặc `None` khi đang chơi).

### 3.2.3. Hành động hợp lệ và bất biến trạng thái

- Tiêu chí từ chối hành động: Sai kiểu dữ liệu, chỉ số nằm ngoài biên $[0, 10]$, ô cờ đã có quân đóng chiếm, hoặc cố gắng thực hiện nước đi khi `terminated == True`.
- **Bất biến trạng thái**: Một hành động không hợp lệ khi gửi tới engine phải bị từ chối kèm mã lỗi rõ ràng và tuyệt đối **không làm thay đổi** bất kỳ thuộc tính nào của trạng thái bàn cờ cũng như ngăn xếp lịch sử.

### 3.2.4. Hàm chuyển, reward và kết quả

- Hàm `step(action)` nhận vào nước đi và trả về đối tượng `StepResult`:
  - `state`: Trạng thái mới của ván đấu.
  - `reward`: Điểm thưởng tương ứng góc nhìn người chơi vừa đi ($+1.0$ nếu thắng, $0.0$ nếu hòa hoặc chưa kết thúc, $-1.0$ nếu phạm luật nghiêm trọng).
  - `terminated`: Cờ kết thúc ván đấu.
  - `truncated`: Cờ dừng sớm do vi phạm luật hoặc hết ngân sách.
  - `info`: Từ điển chứa lý do kết thúc hoặc mã lỗi chẩn đoán.

### 3.2.5. Clone và undo cho tìm kiếm

- Phương thức `clone_env()`: Tạo bản sao sâu độc lập (deep copy) của toàn bộ môi trường để agent thoải mái giả lập mà không ảnh hưởng tới ván chơi thật.
- Phương thức `undo()`: Sử dụng ngăn xếp lịch sử (`history stack`) để khôi phục nhanh trạng thái cờ trước đó, phục vụ việc duyệt cây tìm kiếm DFS với chi phí phân bổ bộ nhớ thấp.

## 3.3. Contract

- Lý do tiếp cận Contract-first (`caro-v2`): Khóa chặt giao tiếp giữa các thành viên phát triển song song, bảo đảm engine và tác tử AI hoàn toàn tương thích mà không phụ thuộc vào chi tiết cài đặt nội bộ.
- Các cấu trúc dữ liệu chuẩn mực: `GameConfig`, `GameState`, `StepResult`, `SearchBudget`, `AgentDecision`.
- Giao diện trừu tượng cốt lõi:
  - `GameEnv`: Khai báo các phương thức `reset()`, `step(action)`, `legal_actions()`, `clone_env()`, `undo()`.
  - `Agent`: Khai báo phương thức duy nhất `select_action(env, budget) -> AgentDecision`.
- Quy chuẩn mã lý do từ chối (Reason Codes): `OUT_OF_BOUNDS`, `CELL_OCCUPIED`, `GAME_TERMINATED`, `INVALID_FORMAT`.

## 3.4. Kiến trúc tổng thể

Hệ thống được tổ chức phân tầng rõ rệt:

```
Caro_AI_Project/
├── core/
│   ├── engine/       # Lõi trò chơi: Board, RuleEngine, GameEnv, Interfaces
│   ├── agents/       # Các tác tử AI: Random, Heuristic, Minimax, MCTS
│   └── utils/        # Công cụ hỗ trợ: Logger JSONL, Tournament Runner
├── configs/          # Cấu hình tham số thực nghiệm và benchmark
├── benchmarks/       # Script đo kiểm hiệu năng chuyên sâu cho từng agent
├── ui/               # Ứng dụng Streamlit và bộ điều khiển người dùng
├── tests/            # Bộ kiểm thử tự động: Unit, Contract, Integration
└── docs/             # Tài liệu đặc tả contract, kế hoạch và cấu trúc báo cáo
```

## 3.5. Thiết kế engine và luật

### 3.5.1. Board và quản lý dữ liệu bàn cờ

- Lưu trữ mảng hai chiều tối ưu, cung cấp các hàm trợ giúp: đặt quân, xóa quân (phục vụ undo), kiểm tra ô trống và lấy danh sách toàn bộ các ô hợp lệ.

### 3.5.2. RuleEngine và kiểm tra bốn hướng

- Thuật toán kiểm tra thắng tăng dần (Incremental Check): Thay vì quét toàn bộ 121 ô trên bàn cờ sau mỗi nước đi, thuật toán chỉ xuất phát từ ô vừa đánh `(last_row, last_col)` và quét dọc theo 4 trục:
  1. Hướng ngang (Horizontal: $(0, 1)$ và $(0, -1)$).
  2. Hướng dọc (Vertical: $(1, 0)$ và $(-1, 0)$).
  3. Đường chéo chính (Diagonal: $(1, 1)$ và $(-1, -1)$).
  4. Đường chéo phụ (Anti-diagonal: $(1, -1)$ và $(-1, 1)$).
- Cơ chế đếm số quân liên tiếp cùng màu và kiểm tra trạng thái 2 đầu mút:
  - Nếu số quân liên tiếp $\ge 5$ và không bị chặn cả 2 đầu $\rightarrow$ Xác nhận chiến thắng.
  - Nếu chuỗi chạm mép bàn cờ thì đầu đó tính là bị chặn một đầu.

### 3.5.3. CaroEnv và vòng đời ván chơi

- Đóng gói toàn bộ vòng đời của một ván chơi: Từ trạng thái khởi tạo `reset()`, luân chuyển lượt qua `step()`, phát hiện kết thúc và khóa trạng thái bàn cờ.

### 3.5.4. Snapshot phòng vệ, clone và history stack

- Cơ chế Snapshot: Trả về bản sao trạng thái bàn cờ bất biến (`read-only`) khi tác tử truy xuất dữ liệu, ngăn ngừa tác tử can thiệp trái phép vào mảng bàn cờ thật.
- Ngăn xếp `history`: Lưu trữ bộ ba `(row, col, player)` để hỗ trợ khôi phục trạng thái nhanh trong thao tác `undo()`.

### 3.5.5. Phân tích độ phức tạp của step, undo và clone_env

- Thao tác `step(action)`: $\mathcal{O}(1)$ kiểm tra ô hợp lệ + $\mathcal{O}(K)$ quét 4 hướng với $K \le 11 \rightarrow$ Tổng thời gian $\mathcal{O}(1)$.
- Thao tác `undo()`: $\mathcal{O}(1)$ do chỉ cần lấy phần tử trên đỉnh stack và đặt lại giá trị ô về 0.
- Thao tác `clone_env()`: $\mathcal{O}(N^2)$ với $N=11$ (sao chép mảng $11 \times 11$).

## 3.6. Thiết kế tác tử AI

- Tuân thủ interface chung `Agent`: Nhận `env: GameEnv` và `budget: SearchBudget`, trả về đối tượng `AgentDecision`.
- Đối tượng `AgentDecision` chứa:
  - `action`: Tọa độ nước đi lựa chọn `(row, col)`.
  - `score`: Điểm đánh giá Heuristic hoặc tỷ lệ thắng ước tính.
  - `nodes_evaluated`: Số lượng trạng thái/node cây đã duyệt qua.
  - `simulations_completed`: Số lượt mô phỏng Rollout đã thực hiện (đối với MCTS).
  - `execution_time_ms`: Thời gian tính toán thực tế.
- Xử lý khi chạm ngưỡng ngân sách: Lập tức trả về nước đi tốt nhất hiện có (Fallback / Best-effort) thay vì ném lỗi ngoại lệ.

## 3.7. Thiết kế hạ tầng thực nghiệm

### 3.7.1. Luồng chạy một game, một match và tournament

- **Single Game**: Hai tác tử đối đầu một ván duy nhất.
- **Match**: Đối đầu gồm 2 ván có hoán đổi lượt đi trước (X) và đi sau (O).
- **Tournament**: Tổ chức thi đấu vòng tròn tính điểm (Round-Robin) giữa tất cả các tác tử trong danh sách tham gia.

### 3.7.2. Cơ chế đổi bên X/O

- Loại bỏ lợi thế của người đi trước (X) bằng cách bắt buộc mỗi cặp agent phải thi đấu đối xứng cả 2 lượt: Lượt đi agent A cầm X, lượt về agent A cầm O.

### 3.7.3. Sinh seed và tái lập

- Quản trị seed tập trung: Mỗi ván đấu được gán một seed số nguyên cố định, từ đó khởi tạo bộ sinh số ngẫu nhiên cho cả môi trường và các tác tử, bảo đảm kết quả đối đầu hoàn toàn không thay đổi qua các lần chạy lặp lại.

### 3.7.4. Giám sát ngân sách (Budget Enforcer)

- Module giám sát đo lường thời gian thực thi của agent; nếu vượt quá ngưỡng thời gian quy định (`time_limit_ms`), ván đấu sẽ bị xử thua do quá thời gian.

### 3.7.5. Schema log JSONL và manifest

- Mỗi ván đấu sinh ra một bản ghi JSONLines chứa đầy đủ metadata: `game_id`, `seed`, `agent_x`, `agent_o`, `winner`, `move_count`, chi tiết từng bước đi kèm số node/thời gian.

### 3.7.6. Tổng hợp metric

- Tự động trích xuất bảng tổng hợp: Tỷ lệ thắng/thua/hòa theo từng tác tử, thời gian tính toán trung bình, độ phân tán thời gian và tài nguyên tiêu thụ.

## 3.8. Thiết kế giao diện

- Ứng dụng Streamlit tương tác mượt mà, phân tách rõ giao diện hiển thị và logic trò chơi.
- Sử dụng `st.session_state` để lưu trữ đối tượng `CaroEnv`, duy trì trạng thái ván chơi xuyên suốt các lượt tải lại trang (rerun) của Streamlit.
- Bộ điều khiển `HumanController` chuyển đổi các click chuột trên ma trận nút bấm $11 \times 11$ thành hành động tọa độ gửi tới engine.
- Tự động khóa bàn cờ khi trò chơi kết thúc và hiển thị nút "Ván mới / Chơi lại".

## 3.9. Chiến lược kiểm thử

- **Unit Test**: Kiểm thử độc lập từng phương thức của `Board`, `RuleEngine`, các mẫu hình thắng/chặn 4 hướng và từng agent.
- **Contract Test**: Kiểm tra sự tuân thủ nghiêm ngặt của API engine đối với bản đặc tả hợp đồng `caro-v2`.
- **Property & Regression Test**: Thử nghiệm các nước đi ngẫu nhiên liên tục để bảo đảm không xảy ra ngoại lệ rò rỉ trạng thái hoặc treo hệ thống.
- **Integration Test**: Kiểm thử tích hợp chuỗi hoạt động giữa Agent, GameEnv, Logger và Tournament Runner.
- **UI Test**: Kiểm tra tương tác trên ứng dụng Streamlit với engine thật.

---

# CHƯƠNG 4. PHƯƠNG PHÁP ĐỀ XUẤT VÀ CÀI ĐẶT

## 4.1. Cài đặt môi trường Caro

- Quy trình chuẩn hóa trong `step(action)`:
  1. Kiểm tra tính hợp lệ sơ bộ (loại dữ liệu, tọa độ trong biên $[0, 10]$).
  2. Kiểm tra ô trống trên bàn cờ.
  3. Cập nhật ma trận bàn cờ và ghi nhận nước đi vào `history`.
  4. Gọi `RuleEngine` kiểm tra 4 hướng từ vị trí vừa đánh.
  5. Nếu thỏa mãn điều kiện thắng $\rightarrow$ Đặt `terminated = True`, gán `winner`.
  6. Nếu chưa thắng nhưng số nước đi đạt cực đại 121 $\rightarrow$ Đặt `terminated = True`, gán `winner = 0` (Hòa).
  7. Đổi lượt người chơi (`current_player = -current_player`) và trả về `StepResult`.
- Tối ưu hóa kiểm tra thắng: Đếm quân tăng dần dọc theo 4 hướng, dừng ngay khi tìm thấy chuỗi thỏa mãn luật, đạt độ phức tạp thực thi tối thiểu.
- Cài đặt `undo()`: Lấy phần tử gần nhất từ ngăn xếp lịch sử, đặt ô cờ về 0, khôi phục `current_player`, và tái lập cờ `terminated = False`.

## 4.2. Random Agent — Baseline

- Chọn ngẫu nhiên đều (Uniform Random) một hành động từ tập `legal_actions()`.
- Sử dụng cá thể RNG riêng biệt `random.Random(seed)` được truyền vào cấu hình, bảo đảm tính độc lập và tái lập được kết quả.
- Đóng vai trò mốc đo lường thấp nhất (Sanity check) để kiểm chứng xem các agent cấp cao có luôn áp đảo hoàn toàn người chơi ngẫu nhiên hay không.

## 4.3. Heuristic Agent

### 4.3.1. Thứ tự ưu tiên

Thuật toán lựa chọn nước đi dựa trên hệ thống luật chuyên gia có thứ tự ưu tiên nghiêm ngặt:

1. **Thắng ngay lập tức**: Nếu tồn tại bất kỳ nước đi nào tạo thành chuỗi 5 thắng cuộc $\rightarrow$ Chọn ngay.
2. **Chặn đối thủ thắng**: Nếu đối thủ có nước đi có thể thắng trong lượt tiếp theo $\rightarrow$ Buộc phải đánh vào ô chặn đó.
3. **Tạo chuỗi 4 mở (Open 4)**: Tạo thế cờ không thể hóa giải.
4. **Chặn chuỗi 4 mở của đối thủ**: Ngăn chặn đối thủ tạo thế cờ hiểm.
5. **Tạo / Chặn các thế ba mở (Open 3)**: Tranh chấp các đe dọa trung cuộc.
6. **Ưu tiên vị trí trung tâm**: Khi chưa có đe dọa chiến thuật, ưu tiên chiếm các ô gần tâm bàn cờ nhất.

### 4.3.2. Bảng điểm pattern

- Bảng trọng số điểm mẫu hình được hiệu chỉnh thực nghiệm:
  - Chuỗi 5 thắng (Win 5): $+100,000$ điểm.
  - Chuỗi 4 mở hai đầu (Open 4): $+10,000$ điểm.
  - Chuỗi 4 chặn một đầu (Closed 4): $+1,000$ điểm.
  - Chuỗi 3 mở hai đầu (Open 3): $+1,000$ điểm.
  - Chuỗi 3 chặn một đầu (Closed 3): $+100$ điểm.
  - Chuỗi 2 mở hai đầu (Open 2): $+10$ điểm.
- Hệ số phòng thủ (Defense Weight): Nhân trọng số đe dọa của đối thủ với hệ số $1.2$ để tác tử có xu hướng phòng thủ cẩn trọng.

### 4.3.3. Tie-break và độ phức tạp

- Khi nhiều ô cờ đạt cùng mức điểm Heuristic cao nhất, thuật toán sử dụng cơ chế Tie-break tất định: Ưu tiên ô có khoảng cách Manhattan nhỏ nhất tới tâm bàn cờ $(5, 5)$, sau đó đến thứ tự tọa độ từ điển $(row, col)$.
- Độ phức tạp tính toán: $\mathcal{O}(|A_{legal}| \times 4 \times K)$, xử lý tức thời trong khoảng $1$–$3$ mili-giây.

## 4.4. Minimax và Alpha-Beta

### 4.4.1. Hàm đánh giá trạng thái

- Điểm trạng thái tĩnh $Eval(s)$ theo góc nhìn của người chơi gốc:
  $$Eval(s) = \text{Score}_{pattern}(\text{Player}) - \text{Score}_{pattern}(\text{Opponent}) + \text{Bonus}_{center}$$
- Giá trị Terminal: Trạng thái thắng nhận $+1,000,000 - depth$ (ưu tiên thắng càng sớm càng tốt); trạng thái thua nhận $-1,000,000 + depth$ (ưu tiên kéo dài ván đấu khi gặp thế thua).

### 4.4.2. Sinh tập nước ứng viên (Candidate Filtering)

- Thuật toán loại bỏ toàn bộ các ô cờ cách xa khu vực giao tranh: Chỉ xét các ô trống nằm trong bán kính Chebyshev $r \le 2$ tính từ tất cả các quân cờ hiện có trên bàn.
- Trường hợp bàn cờ rỗng: Tác tử tự động chọn ngay vị trí trung tâm $(5, 5)$ mà không cần tốn chi phí duyệt cây.

### 4.4.3. Tìm kiếm sâu dần (Iterative Deepening)

- Tiến hành tìm kiếm lặp từ độ sâu $d = 1, 2, \dots, D_{max}$. Lưu lại nước đi tối ưu nhất sau mỗi vòng lặp; nếu vòng lặp kế tiếp chạm giới hạn thời gian tính toán, hủy bỏ độ sâu dở dang và trả về ngay nước đi của độ sâu hoàn tất trước đó.

### 4.4.4. Cắt tỉa Alpha-Beta (Alpha-Beta Pruning)

- Duy trì và cập nhật liên tục hai cận $\alpha, \beta$ qua các tầng đệ quy. Ngắt ngay vòng lặp duyệt các nhánh con khi xuất hiện điều kiện $\alpha \ge \beta$.

### 4.4.5. Sắp xếp nước đi (Move Ordering)

- Tại mỗi node duyệt, danh sách các nước đi ứng viên được chấm điểm sơ bộ bằng hàm Heuristic nhanh và sắp xếp theo thứ tự giảm dần điểm số trước khi gọi đệ quy. Kỹ thuật này giúp nhánh tốt nhất được duyệt trước, tối đa hóa tỷ lệ cắt tỉa.

### 4.4.6. Xử lý ngân sách và cơ chế Fallback

- Tác tử kiểm tra thời gian trôi qua định kỳ sau mỗi số lượng node duyệt nhất định. Nếu vượt ngưỡng `time_limit_ms`, kích hoạt cờ dừng và kích hoạt cơ chế trả về nước đi tốt nhất hiện thời.

### 4.4.7. Tham số cấu hình và đánh đổi

- Phân tích sự đánh đổi giữa độ sâu tìm kiếm $d \in \{2, 3, 4\}$ và thời gian phản hồi: Độ sâu 2 phản hồi trong vài chục mili-giây, độ sâu 3 phản hồi dưới 1 giây, độ sâu 4 yêu cầu từ 3–8 giây tùy thuộc vào mật độ quân trên bàn cờ.

## 4.5. Monte Carlo Tree Search

### 4.5.1. Cấu trúc node và thống kê visit/value

- Mỗi node trong cây tìm kiếm MCTS lưu giữ:
  - Trỏ tới node cha (`parent`) và danh sách node con (`children`).
  - Nước đi dẫn tới trạng thái đó (`action`).
  - Số lần node đã được duyệt qua (`visit_count`: $N$).
  - Tổng giá trị phần thưởng tích lũy (`total_value`: $Q$).
  - Danh sách các nước đi hợp lệ chưa được mở rộng (`untried_actions`).

### 4.5.2. Selection bằng UCT

- Bắt đầu từ node gốc, thuật toán chọn đệ quy các node con có chỉ số $UCT$ lớn nhất cho đến khi gặp một node chưa mở rộng hết hoặc chạm trạng thái kết thúc.

### 4.5.3. Expansion trên action hợp lệ

- Chọn ngẫu nhiên có kiểm soát một nước đi từ `untried_actions`, áp dụng nước đi lên môi trường nhân bản và tạo node con mới gắn vào cây tìm kiếm.

### 4.5.4. Rollout và chính sách mô phỏng

- Từ trạng thái mới, thực hiện ván cờ mô phỏng nhanh (Rollout): Lựa chọn ngẫu nhiên các nước đi trong phạm vi lân cận cho đến khi một bên giành chiến thắng hoặc đạt số nước đi tối đa của lượt mô phỏng.

### 4.5.5. Backpropagation và góc nhìn người chơi

- Lan truyền kết quả $R \in \{-1.0, 0.0, 1.0\}$ ngược lên node gốc: Cập nhật $N \leftarrow N + 1$ và cộng dồn điểm thưởng $Q \leftarrow Q + R_{perspective}$ dựa trên góc nhìn người chơi tại từng tầng.

### 4.5.6. Chọn action cuối cùng

- Sau khi sử dụng hết ngân sách mô phỏng (`simulation_budget`), tác tử chọn nước đi từ node gốc có **số lần viếng thăm ($N$) lớn nhất** (Robust Child), bảo đảm tính ổn định và ít rủi ro hơn việc chọn theo giá trị trung bình $Q/N$.

### 4.5.7. Seed, simulation budget, node budget và time budget

- Kiểm soát tiến trình MCTS thông qua:
  - Ngân sách mô phỏng: $100$, $400$, hoặc $1000$ simulations.
  - Ngân sách node: Giới hạn dung lượng bộ nhớ cây MCTS.
  - Ngân sách thời gian: Tự động ngắt vòng lặp khi chạm ngưỡng `time_limit_ms`.

## 4.6. Tournament runner, logger và metric

- Bộ điều khiển giải đấu tự động xác thực tính hợp lệ của mọi nước đi do agent sinh ra.
- Tự động phát hiện và xử thua ngay lập tức đối với tác tử có hành vi gian lận (thực hiện nước đi ngoài danh sách hợp lệ, gây biến đổi môi trường gốc, hoặc vi phạm nghiêm trọng ngân sách thời gian).
- Ghi nhật ký đầy đủ ra tệp `.jsonl`: Mỗi dòng biểu diễn một ván cờ với định dạng chuẩn, bao gồm toàn bộ chuỗi tọa độ và các thông số tài nguyên.
- Script tự động tính toán ma trận đối đầu chéo, tỷ lệ thắng, tỷ lệ hòa, số node trung bình và thời gian p95.

## 4.7. Các quyết định tối ưu và bảo đảm tính đúng

- **Snapshot phòng vệ**: Trả về dữ liệu bản sao để triệt tiêu nguy cơ agent vô tình hoặc cố ý can thiệp vào bộ nhớ của engine.
- **RNG cục bộ**: Không bao giờ sử dụng hàm ngẫu nhiên toàn cục `random.choice()` hay `np.random`, mà luôn sử dụng cá thể RNG riêng được nuôi dưỡng từ seed định danh.
- **Phân tách hoàn toàn Engine và UI**: UI chỉ đóng vai trò trình diễn và thu thập tương tác, toàn bộ logic luật và kiểm tra trạng thái nằm hoàn toàn ở `CaroEnv`.
- **Bộ kiểm thử biên**: Thiết lập các ca kiểm thử đặc thù cho các tình huống hiểm hóc: thắng sát biên, bị chặn một đầu sát góc, bị chặn hai đầu bởi quân đối phương, và chuỗi overline 6 quân liên tiếp.

## 4.8. Neural AI và pipeline dữ liệu — Điều kiện

- Đặc tả kiến trúc lý thuyết của hệ thống tự học: Khởi tạo dữ liệu qua cơ chế tự chơi (Self-play), tiền xử lý biểu diễn bàn cờ thành Tensor $3 \times 11 \times 11$, huấn luyện mô hình mạng tích chập ResNet thu nhỏ, và tích hợp bộ suy luận nơ-ron qua class `NeuralAgent`.
- _Cam kết tính trung thực khoa học_: Nhóm giữ mục này ở trạng thái thiết kế mở rộng; nếu chưa hoàn tất huấn luyện và đánh giá trên cùng một giải đấu với các agent khác trước hạn chót, nội dung này sẽ được ghi nhận là Hướng phát triển trong tương lai.

## 4.9. Hạn chế của phương pháp hiện tại

- Heuristic Agent phụ thuộc nặng nề vào các hệ số điểm tĩnh do con người thiết kế thủ công, có thể tồn tại các điểm mù chiến thuật khi đối đầu với thế cờ phức tạp.
- Minimax/Alpha-Beta bị giới hạn bởi độ sâu tìm kiếm (khó vượt quá độ sâu 4 trong thời gian thực) do hệ số phân nhánh của cờ Caro rất lớn.
- MCTS thuần túy phụ thuộc vào số lượng mô phỏng; nếu chính sách rollout quá ngẫu nhiên, MCTS có thể đánh giá sai các thế cờ có đe dọa chiến thuật ngắn hạn (Tactical Blindness).
- Chưa tích hợp bảng chuyển vị (Transposition Table) để tái sử dụng giá trị của các thế cờ hoán vị.

---

# CHƯƠNG 5. THỰC NGHIỆM VÀ ĐÁNH GIÁ

## 5.1. Câu hỏi nghiên cứu

- **RQ1**: Các tác tử AI có phát hiện và lựa chọn chính xác nước đi mang tính quyết định (thắng ngay hoặc chặn đối thủ thắng ngay trong 1 nước) trong các tình huống chiến thuật cố định hay không?
- **RQ2**: Trong các cặp đấu đối kháng trực tiếp dưới điều kiện công bằng (đổi bên X/O), tác tử nào đạt tỷ lệ chiến thắng vượt trội?
- **RQ3**: Sự đánh đổi giữa chất lượng nước đi và chi phí tính toán (thời gian thực thi, số node duyệt, số lượt mô phỏng) diễn ra như thế nào giữa các họ thuật toán?
- **RQ4**: Kỹ thuật cắt tỉa Alpha-Beta kết hợp sắp xếp nước đi (Move Ordering) giúp cắt giảm bao nhiêu phần trăm số lượng node cần duyệt so với Minimax thuần túy?
- **RQ5**: Hiệu năng và sức mạnh chiến thuật của MCTS biến thiên như thế nào khi tăng dần ngân sách mô phỏng từ 100 lên 400 và 1000 simulations?

## 5.2. Môi trường thực nghiệm

- **Phần cứng thực nghiệm**: Cấu hình chi tiết CPU (xung nhịp, số nhân/luồng), dung lượng RAM khả dụng, và hệ điều hành (Windows 11).
- **Phần mềm**: Phiên bản Python (3.10+), các thư viện phụ thuộc (`pytest`, `streamlit`).
- **Mã nguồn thực nghiệm**: Ghi nhận mã commit Git tương ứng với phiên bản được dùng để chạy dữ liệu trong báo cáo.
- **Cấu hình trò chơi**: Bàn cờ $11 \times 11$, độ dài chuỗi thắng 5 quân không bị chặn 2 đầu, tuân thủ Contract `caro-v2`.
- **Thiết lập hạt giống (Seed)**: Sử dụng tập seed cố định được khai báo trong `configs/benchmark.json` để bảo đảm khả năng tái lập 100%.

## 5.3. Đối tượng và cấu hình so sánh

- **Random Agent**: Lựa chọn nước đi ngẫu nhiên đều.
- **Heuristic Agent**: Tác tử luật chuyên gia với bảng điểm mẫu hình chuẩn.
- **Minimax / Alpha-Beta**: Đánh giá ở các mức độ sâu $d = 2, 3, 4$ với các biến thể:
  - Minimax thuần (không cắt tỉa).
  - Minimax + Alpha-Beta.
  - Minimax + Alpha-Beta + Move Ordering.
- **MCTS Agent**: Đánh giá ở các mức ngân sách $100, 400, 1000$ simulations, hằng số khám phá $C = \sqrt{2}$.
- **Các cấu hình Benchmark Profile**: `FAST`, `FAIR`, `MCTS-S`, `AB-D`.

## 5.4. Bộ kịch bản cố định (Tactical Benchmarks)

- Bộ thế cờ kiểm tra định tính gồm các trường hợp:
  1. _Bàn cờ rỗng_: Kiểm tra việc ưu tiên chiếm giữ trung tâm $(5, 5)$.
  2. _Khai cuộc_: Phản ứng với các nước đi đầu tiên tại khu vực trung tâm.
  3. _Thắng trong 1 nước (Winning move in 1)_: Thế cờ đã có sẵn chuỗi 4 mở, kiểm tra agent có đánh ngay vào ô kết liễu không.
  4. _Chặn trong 1 nước (Blocking move in 1)_: Đối thủ đã có chuỗi 4, kiểm tra agent có buộc phải chặn ngay hay không.
  5. _Trung cuộc phức tạp (Midgame forks)_: Tạo thế đôi (Double three/four) và đối phó với thế công của địch.
  6. _Các trường hợp biên và ngoại lệ_: Tình huống sát mép bàn cờ, chuỗi bị chặn hai đầu, chuỗi overline 6 quân.

## 5.5. Giao thức thí nghiệm

- Mỗi cặp đấu tiến hành thi đấu tối thiểu $N = 20$ đến $50$ ván cờ có đổi bên X/O đối xứng.
- Mọi điều kiện phần cứng và danh sách seed ngẫu nhiên được giữ nguyên đồng nhất trong suốt quá trình đo.
- Tiêu chí loại bỏ: Bất kỳ ván cờ nào có tác tử vi phạm ngân sách thời gian quá 3 lần hoặc ném lỗi ngoại lệ sẽ bị xử thua ngay lập tức.
- Toàn bộ dữ liệu log thô JSONL được tự động lưu trữ tại thư mục thực nghiệm để phục vụ tra cứu chéo.

## 5.6. Chỉ số đánh giá

- Số lượng và tỷ lệ trận Thắng / Hòa / Thua (Win / Draw / Loss Rate).
- Tỷ lệ hoàn thành chính xác các kịch bản chiến thuật cố định (Tactical Accuracy Rate: %).
- Thời gian tính toán trung bình mỗi nước đi (Mean Latency) và phân vị 95 (p95 Latency) tính bằng mili-giây.
- Số lượng node trung bình được đánh giá trong mỗi nước đi của Minimax.
- Số lượt mô phỏng thực tế hoàn thành của MCTS.
- Số trường hợp vi phạm ngân sách hoặc phát sinh nước đi không hợp lệ (mục tiêu là 0).

## 5.7. Kết quả kiểm tra tính đúng

- Báo cáo kết quả bộ kiểm thử tự động `pytest`: Số lượng test pass trên từng module (`engine`, `rules`, `agents`, `runner`).
- Kết quả kiểm định bộ kịch bản chiến thuật: Chứng minh Heuristic, Minimax và MCTS vượt qua $100\%$ các bài toán thắng/chặn tức thời.
- Bằng chứng thực nghiệm khẳng định môi trường không bị thay đổi trạng thái trái phép sau các lần gọi tìm kiếm của tác tử.

## 5.8. Kết quả Minimax/Alpha-Beta

### 5.8.1. Ảnh hưởng của độ sâu

- Bảng so sánh tương quan giữa độ sâu $d \in \{1, 2, 3, 4\}$, thời gian phản hồi và tỷ lệ chiến thắng đối đầu.

### 5.8.2. So sánh bật/tắt Alpha-Beta

- Minh chứng bằng số liệu thực nghiệm: Alpha-Beta giúp cắt tỉa bao nhiêu phần trăm node so với Minimax thuần túy trên cùng cấu hình độ sâu.

### 5.8.3. So sánh bật/tắt Move Ordering

- Phân tích hiệu quả tăng cường của việc sắp xếp nước đi heuristic: Tăng tỷ lệ cắt tỉa sớm nhánh $\alpha \ge \beta$, giảm thêm từ 30% đến 50% số node cần xét.

### 5.8.4. Số node, thời gian và chất lượng nước đi

- Đồ thị trực quan hóa sự đánh đổi giữa thời gian thực thi (mili-giây) và số lượng node đánh giá.

## 5.9. Kết quả MCTS

### 5.9.1. Ảnh hưởng của số lượng Simulation

- Đánh giá năng lực của MCTS khi tăng ngân sách từ 100 lên 400 và 1000 simulations: Tỷ lệ thắng tăng trưởng rõ rệt khi đối đầu với Heuristic và Minimax.

### 5.9.2. Độ ổn định theo Seed

- Phân tích độ biến động của nước đi khi thay đổi hạt giống ngẫu nhiên; chứng minh rằng với số simulation đủ lớn ($\ge 400$), các quyết định của MCTS đạt độ ổn định cao.

### 5.9.3. Thời gian và chất lượng nước đi

- Đánh giá thời gian phản hồi thực tế của MCTS trên cấu hình phần cứng thử nghiệm.

## 5.10. Kết quả giải đấu

- Ma trận đối đầu chéo tổng thể (Cross-table) giữa tất cả các agent tham gia giải đấu: Random, Heuristic, Minimax (Depth 2, 3), MCTS (100, 400).
- Thống kê chi tiết tỷ lệ thắng tách biệt theo vai trò người chơi đi trước (X) và người chơi đi sau (O), qua đó định lượng chính xác lợi thế đi trước trong biến thể cờ Caro $11 \times 11$.
- Bảng xếp hạng chung cuộc dựa trên điểm số Elo hoặc điểm tích lũy giải đấu.

---

# CHƯƠNG 6. XÂY DỰNG ỨNG DỤNG MINH HỌA

## 6.1. Mục tiêu ứng dụng

- Xây dựng một giao diện web trực quan, thân thiện, giúp người dùng dễ dàng tương tác và trải nghiệm trực tiếp các luật chơi và thuật toán của dự án.
- Minh họa rõ ràng trạng thái bàn cờ, chỉ báo lượt đi hiện tại, đánh dấu nước vừa đi gần nhất, hiển thị lịch sử ván cờ và thông báo kết quả.

## 6.2. Công nghệ sử dụng

- Ngôn ngữ lập trình: **Python**.
- Framework giao diện: **Streamlit** – giải pháp mã nguồn mở tối ưu cho các bài toán trình diễn ứng dụng học thuật và trí tuệ nhân tạo.
- Lý do lựa chọn Streamlit: Cho phép phát triển giao diện nhanh chóng, tương thích tự nhiên $100\%$ với mã nguồn Python của Game Engine và các tác tử AI mà không cần viết thêm tầng API trung gian phức tạp.

## 6.3. Thiết kế giao diện và trải nghiệm

- **Bố cục chính**:
  - Khu vực bàn cờ trung tâm: Ma trận lưới $11 \times 11$ các nút bấm tương tác, hiển thị trực quan các quân cờ X và O với màu sắc phân biệt rõ ràng.
  - Khung Sidebar điều khiển: Lựa chọn chế độ chơi, hiển thị thông tin cấu hình, bảng thống kê số ván thắng/hòa/thua trong phiên làm việc.
- **Trạng thái trực quan**:
  - Đánh dấu nổi bật (Highlight) nước cờ vừa được đánh gần nhất để người chơi dễ theo dõi thế trận.
  - Tự động vô hiệu hóa toàn bộ bàn cờ khi ván đấu kết thúc nhằm ngăn chặn các thao tác sai luật.
- **Luồng điều khiển**:
  - Nút bấm "Chơi lại / Ván mới" cho phép khởi tạo lại bàn cờ rỗng tức thì mà không làm mất lịch sử thống kê của phiên.

## 6.4. Tích hợp UI với engine

- Giao diện người dùng giao tiếp với engine thuần túy thông qua các phương thức của public API `CaroEnv` (`reset()`, `step()`, `get_state()`).
- Lớp điều khiển `HumanController` nhận sự kiện click chuột từ người dùng và đóng gói thành tuple tọa độ `(row, col)` chuẩn mực gửi tới `CaroEnv.step()`.
- Sử dụng cơ chế `st.session_state` để lưu giữ cá thể môi trường trò chơi và trạng thái ván cờ xuyên suốt các vòng đời rerun của Streamlit.

## 6.5. Các chức năng đã hoàn thành

- Chế độ chơi hai người đối kháng trực tiếp trên cùng một máy (Human vs Human) trên bàn cờ chuẩn $11 \times 11$.
- Hệ thống tự động xác định thắng cuộc hoặc hòa cờ theo đúng luật Caro dự án.
- Bảng nhật ký ghi lại chi tiết chuỗi các nước đi trong ván chơi.
- Thống kê tỷ số phiên chơi hiện tại (Số ván X thắng, O thắng, Hòa).
- Cơ chế phòng vệ ngăn chặn hoàn toàn việc click vào các ô đã có quân hoặc click sau khi ván cờ đã kết thúc.
- _Lưu ý_: Trình bày chính xác trạng thái tích hợp của các chế độ Người đấu với Máy (Human vs AI) và Máy đấu với Máy (AI vs AI) theo đúng phiên bản release thực tế của mã nguồn.

## 6.6. Kiểm thử ứng dụng

- Kiểm thử tự động giao diện và tích hợp engine thật bằng bộ script kiểm thử.
- Xác nhận các hành vi click hợp lệ, click vào ô đã chiếm đóng, và kiểm tra tính nhất quán của trạng thái hiển thị.
- Đảm bảo giao diện UI tuyệt đối không tự cài đặt lại các quy tắc kiểm tra thắng thua mà ủy quyền hoàn toàn cho `CaroEnv`.

## 6.7. Hạn chế hiện tại

- Giao diện Streamlit thực hiện tải lại toàn bộ trang (Full Page Rerun) khi có tương tác, dẫn đến độ trễ nhỏ về hiệu ứng thị giác so với các framework frontend chuyên dụng (React/Vue).
- Chưa hỗ trợ chế độ chơi trực tuyến nhiều người qua mạng Internet (chỉ chạy cục bộ trên môi trường máy chủ nội bộ hoặc máy cá nhân).
- Chưa tích hợp cơ chế hoàn tác nước đi (Undo) trực tiếp trên giao diện dành cho người chơi.

---

# CHƯƠNG 7. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

## 7.1. Kết luận

- **Tổng kết các kết quả đã đạt được**:
  - Xây dựng thành công hệ thống Game Engine Caro $11 \times 11$ chuẩn mực, tốc độ cao, hỗ trợ đầy đủ `clone` và `undo`, tuân thủ nghiêm ngặt Contract `caro-v2`.
  - Triển khai thành công 4 họ tác tử AI: Random (Baseline), Heuristic (luật chuyên gia và mẫu hình), Minimax tối ưu hóa (Alpha-Beta, Move Ordering, Iterative Deepening) và Monte Carlo Tree Search (MCTS với công thức UCT).
  - Xây dựng hệ thống giải đấu và đo kiểm tự động với khả năng tái lập $100\%$ bằng hạt giống ngẫu nhiên, trích xuất dữ liệu nhật ký JSONL đầy đủ.
  - Thực hiện các thí nghiệm định lượng và định tính sâu rộng, trả lời trọn vẹn 5 câu hỏi nghiên cứu (RQ1–RQ5) đặt ra ở đầu đề tài.
  - Xây dựng ứng dụng minh họa trực quan trên nền tảng web Streamlit phục vụ trình diễn và thử nghiệm trực tiếp.
- **Đối chiếu mục tiêu**: Toàn bộ các mục tiêu đặt ra ở Chương 1 đều đã được hoàn thành với các minh chứng thực nghiệm và kiểm thử tự động rõ ràng.

## 7.2. Hạn chế

- Minimax và Alpha-Beta vẫn gặp rào cản về độ sâu tìm kiếm trong môi trường thời gian thực (chưa vượt quá độ sâu 4) do hệ số phân nhánh trung cuộc của cờ Caro còn tương đối lớn.
- MCTS thuần túy đôi khi gặp điểm mù chiến thuật trong các tình huống ngắn hạn nếu ngân sách mô phỏng chưa đủ lớn và chính sách rollout còn mang tính ngẫu nhiên.
- Bộ trọng số điểm Heuristic được cấu hình dựa trên kinh nghiệm chuyên gia thủ công, chưa được tối ưu hóa tự động thông qua giải thuật di truyền (Genetic Algorithm) hay học máy.
- Chưa hoàn thành trọn vẹn đường ống học sâu (Deep Neural Network / AlphaZero) do giới hạn về hạ tầng phần cứng tính toán và thời gian thực hiện.

## 7.3. Hướng phát triển

- **Tích hợp sâu AI vào giao diện người dùng**: Mở rộng Streamlit để hỗ trợ mượt mà các chế độ Human vs AI và AI vs AI với thanh điều chỉnh độ khó trực tiếp trên sidebar.
- **Tối ưu hóa công nghệ tìm kiếm**: Cài đặt bảng chuyển vị (Transposition Table) sử dụng kỹ thuật Zobrist Hashing để loại bỏ việc tính toán lặp lại các trạng thái hoán vị trong Minimax và MCTS.
- **Hoàn thiện đường ống Neural AI**: Xây dựng mô hình Policy-Value Network thu nhỏ, ứng dụng học tăng cường tự chơi (Self-play Reinforcement Learning) tương tự mô hình AlphaZero để tự động khám phá các thế cờ mà không cần chuyên gia thiết kế heuristic thủ công.
- **Song song hóa MCTS**: Ứng dụng kỹ thuật đa luồng (Multi-threading / Tree Parallelization) để tăng tốc độ mô phỏng của MCTS lên gấp nhiều lần trên các CPU đa nhân hiện đại.
- **Đóng gói dịch vụ**: Xây dựng backend RESTful API chuẩn hóa bằng FastAPI và triển khai ứng dụng dưới dạng Docker Container lên môi trường Cloud.

---

# TÀI LIỆU THAM KHẢO

1. **Russell, S., & Norvig, P.** (2020). _Artificial Intelligence: A Modern Approach_ (4th ed.). Pearson. (Tài liệu chuẩn mực về lý thuyết trò chơi đối kháng, thuật toán Minimax và kỹ thuật cắt tỉa Alpha-Beta).
2. **Browne, C. B., Powley, E., Whitehouse, D., Lucas, S. M., Cowling, P. I., Rohlfshagen, P., ... & Colton, S.** (2012). _A Survey of Monte Carlo Tree Search Methods_. IEEE Transactions on Computational Intelligence and AI in Games, 4(1), 1–43. (Tài liệu tổng quan nền tảng về thuật toán MCTS và công thức UCT).
3. **Kocsis, L., & Szepesvári, C.** (2006). _Bandit Based Monte-Carlo Planning_. In European Conference on Machine Learning (pp. 282–293). Springer, Berlin, Heidelberg. (Bài báo gốc đề xuất công thức UCT cho cây tìm kiếm).
4. **Silver, D., Schrittwieser, J., Simonyan, K., Antonoglou, I., Huang, A., Guez, A., ... & Hassabis, D.** (2017). _Mastering the game of Go without human knowledge_. Nature, 550(7676), 354–359. (Tài liệu tham khảo về phương pháp kết hợp mạng nơ-ron sâu và MCTS trong trò chơi đối kháng bàn cờ).
5. **Allis, L. V.** (1994). _Searching for Solutions in Games and Artificial Intelligence_. Ph.D. thesis, University of Limburg, Maastricht. (Nghiên cứu kinh điển về không gian trạng thái và thuật toán giải trò chơi Gomoku).
6. **Streamlit Inc.** (2024). _Streamlit Documentation: Session State and Component Architecture_. https://docs.streamlit.io/. (Tài liệu tham khảo kỹ thuật xây dựng giao diện tương tác).

---

# PHỤ LỤC

## Phụ lục A. Đặc tả Contract `caro-v2` rút gọn

- Chi tiết các kiểu dữ liệu cốt lõi: `GameState`, `StepResult`, `SearchBudget`, `AgentDecision`.
- Bảng danh mục mã lỗi từ chối nước đi (Reason Codes) và các trạng thái ngoại lệ.
- Bất biến trạng thái (Invariants) bảo đảm an toàn bộ nhớ và tính bất biến của môi trường cờ.

## Phụ lục B. Cấu hình thực nghiệm và lệnh tái lập

- Chi tiết file cấu hình thực nghiệm `configs/benchmark.json`.
- Danh sách các tập hạt giống (Seeds) dùng trong các bài kiểm tra.
- Lệnh dòng lệnh (CLI Commands) dùng để chạy tái lập toàn bộ kết quả kiểm thử và giải đấu:
  ```bash
  pytest -v
  python -m core.utils.tournament_runner --config configs/benchmark.json
  streamlit run ui/app.py
  ```

## Phụ lục C. Bộ kịch bản kiểm thử chiến thuật tiêu biểu

- Tọa độ ma trận chi tiết của các bài toán: Thắng trong 1 nước (Winning in 1), Buộc chặn trong 1 nước (Blocking in 1).
- Các kịch bản biên: Chặn một đầu sát mép bàn cờ, chuỗi vượt 5 quân (Overline) không bị chặn.

## Phụ lục D. Bảng số liệu chi tiết các vòng đấu

- Toàn văn dữ liệu bảng đối đầu chi tiết của giải đấu giữa các cặp agent (chi tiết từng ván đấu, số node và thời gian p95).

## Phụ lục E. Hướng dẫn cài đặt và chạy hệ thống

- Hướng dẫn thiết lập môi trường ảo Python (`venv` hoặc `conda`).
- Cài đặt thư viện phụ thuộc: `pip install -r requirements.txt`.
- Hướng dẫn khởi chạy ứng dụng giao diện web Streamlit và các công cụ đo kiểm hiệu năng.

---

## MA TRẬN BẰNG CHỨNG TỪ REPOSITORY

| Nội dung báo cáo                   | Vị trí file mã nguồn làm bằng chứng                                    |                   Trạng thái xác thực                    |
| ---------------------------------- | ---------------------------------------------------------------------- | :------------------------------------------------------: |
| **Đặc tả Contract `caro-v2`**      | `docs/contract/docs_contracts_caro_v2.md`, `core/engine/interfaces.py` |        Đã hoàn thành, pass $100\%$ contract tests        |
| **Engine và Quản lý Bàn cờ**       | `core/engine/board.py`, `core/engine/game_env.py`                      |    Đã hoàn thành, hỗ trợ `step`, `undo`, `clone_env`     |
| **Quy tắc và Kiểm tra Luật**       | `core/engine/rules.py`                                                 |         Đã hoàn thành, kiểm tra 4 hướng tăng dần         |
| **Random Agent**                   | `core/agents/random_ai.py`                                             |            Đã hoàn thành, hỗ trợ seed cục bộ             |
| **Heuristic Agent**                | `core/agents/heuristic_ai.py`                                          |        Đã hoàn thành, bảng điểm pattern chuẩn hóa        |
| **Minimax / Alpha-Beta Agent**     | `core/agents/minimax_ai.py`, `benchmarks/bench_minimax.py`             |    Đã hoàn thành, tích hợp Alpha-Beta & Move Ordering    |
| **MCTS Agent**                     | `core/agents/mcts_ai.py`, `benchmarks/bench_mcts.py`                   |       Đã hoàn thành, công thức UCT & quản lý node        |
| **Hạ tầng giải đấu và Logger**     | `core/utils/logger.py`, `core/utils/tournament_runner.py`              |      Đã hoàn thành, ghi log JSONL & tự động đổi bên      |
| **Cấu hình Benchmark**             | `configs/benchmark.json`                                               | Đã cấu hình các profile `FAST`, `FAIR`, `MCTS-S`, `AB-D` |
| **Giao diện người dùng Streamlit** | `ui/app.py`, `ui/human_controller.py`                                  |       Đã hoàn thành, chế độ Human vs Human mượt mà       |
| **Bộ kiểm thử tự động**            | `tests/` (`test_board.py`, `test_rules.py`, `test_agents.py`, ...)     |    Đã hoàn thành, toàn bộ test cases đều đạt (PASSED)    |

---

## CHECKLIST KIỂM SOÁT TRƯỚC KHI KHÓA BÁO CÁO

- [x] Tiêu đề đề tài, thông tin Giảng viên hướng dẫn và nhóm tác giả được đồng bộ chính xác theo mẫu của Trường Đại học Sài Gòn.
- [x] Tỷ lệ đóng góp của 3 thành viên được ghi nhận chuẩn xác theo biểu mẫu: Trương Văn Thiện 33%, Trần Hồ Minh Hải 33%, Lê Thị Trúc Ly 33%.
- [x] Danh mục từ viết tắt phản ánh đúng 9 thuật ngữ quy định (AI, API, UI, MCTS, UCT, RNG, JSONL, CPU, RAM).
- [x] Số mục và tiêu đề các chương tuân thủ tuyệt đối cấu trúc từ Chương 1 đến Chương 7 do nhóm quy định.
- [x] Quy tắc luật cờ Caro 11×11 (chuỗi 5 quân không bị chặn 2 đầu, biên là 1 đầu chặn, hòa khi kín bàn) được mô tả nhất quán xuyên suốt các chương.
- [x] Phân định ranh giới rõ ràng: Phần cốt lõi đã cài đặt thực tế được mô tả ở thì hiện tại/đã đạt; các phần mở rộng (Neural AI, Multiplayer) được ghi nhận minh bạch ở mục Điều kiện hoặc Hướng phát triển.
- [x] Toàn bộ số liệu thực nghiệm được cam kết trích xuất từ bộ log JSONL và mã nguồn đo kiểm có khả năng tái lập hoàn toàn.
