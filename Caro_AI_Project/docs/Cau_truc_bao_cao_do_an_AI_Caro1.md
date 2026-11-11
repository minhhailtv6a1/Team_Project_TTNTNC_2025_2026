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
- **Tóm tắt đóng góp chính của nhóm**: Bộ engine chuẩn xác, bộ 4 tác tử tìm kiếm hoàn chỉnh (Random, Heuristic, Minimax/Alpha-Beta, MCTS), bộ dữ liệu self-play `dataset-v1` (2.000 ván) cùng tác tử học được huấn luyện trên bộ dữ liệu đó, hệ thống giải đấu và đo lường tự động có seed, cùng ứng dụng giao diện trực quan Streamlit.
- **Bố cục báo cáo**: Tóm tắt ngắn gọn nội dung 6 chương tiếp theo.

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

> [!NOTE]
> Phân công theo tài liệu "Kế hoạch triển khai AI Caro" của nhóm (M1 = Hải, M2 = Ly, M3 = Thiện), đã đổi sang số mục của bố cục 6 chương. Những chỗ kế hoạch không quy định rõ được đánh dấu _(đề xuất)_ để nhóm xác nhận.

| Thành viên | Nội dung đảm nhiệm chính | Đóng góp % |
| ---------- | ------------------------ | :--------: |
| **Trần Hồ Minh Hải (M1)**<br>_(MSSV: 3123410092)_<br>Giao diện UI/UX và Mạng học sâu | - Thiết kế giao diện trực quan hóa bàn cờ bằng Streamlit, tích hợp với API backend (`ui/app.py`, `ui/human_controller.py`).<br>- Lập trình MCTS (Selection, Expansion, Simulation, Backpropagation).<br>- Xây dựng kiến trúc Neural Network và vòng lặp huấn luyện học có giám sát.<br>- Đo độ trễ (latency), xuất biểu đồ learning curve (loss/accuracy), tối ưu RAM/VRAM; hỗ trợ quay video demo. | **33%** |
| **Lê Thị Trúc Ly (M2)**<br>_(MSSV: 3123410210)_<br>Lõi game và thuật toán tìm kiếm | - Lập trình cấu trúc bàn cờ, thuật toán kiểm tra thắng 5 quân và chặn hai đầu (RuleEngine), quản lý logic luật chơi.<br>- Xây dựng tác tử Heuristic; lập trình Minimax và cắt tỉa Alpha-Beta.<br>- Tối ưu hiệu suất (độ sâu Minimax, số vòng lặp MCTS) để tăng tốc giải đấu tự động.<br>- Ablation study: Minimax bật/tắt Alpha-Beta; trích xuất và phân tích bình luận các thế cờ, nước đi điển hình. | **33%** |
| **Trương Văn Thiện (M3)**<br>_(MSSV: 3123410356)_<br>Thực nghiệm và kỹ sư dữ liệu | - Định nghĩa bộ API chuẩn (`reset`, `step`, `legal_actions`) theo Contract `caro-v2`; viết unit test ngăn nước đi bất hợp lệ.<br>- Lập trình tác tử Random (baseline), module đếm số nút duyệt và quản lý thời gian suy nghĩ.<br>- Viết script self-play, lọc trùng, chia tập dữ liệu (`dataset-v1`).<br>- Tổ chức giải đấu vòng tròn (từ 100 ván mỗi cặp, đảo bên), ma trận Thắng/Hòa/Thua, điểm Elo.<br>- Tổ chức mã nguồn GitHub, soạn `README.md`, `requirements.txt` và tệp ZIP nộp bài. | **33%** |

### Phân công viết báo cáo theo mục

| Mục | Người viết | Số liệu / đầu vào từ |
| --- | ---------- | -------------------- |
| Mở đầu, Lời cảm ơn, Chương 1 | M3 _(đề xuất)_ | Cả nhóm |
| 2.1–2.6 (gồm 2.3 Tác tử thông minh) | M2 | |
| 2.7 Monte Carlo Tree Search | M1 _(điều chỉnh theo vai trò: M1 lập trình MCTS)_ | |
| 2.8 Đánh giá tác tử chơi game | M3 _(điều chỉnh theo vai trò: thực nghiệm)_ | |
| 2.9 Học sâu cho trò chơi bàn cờ | M1 _(điều chỉnh theo vai trò: mạng nơ-ron)_ | |
| 3.1 Phân tích yêu cầu | M3 | |
| 3.2 Mô hình hóa bài toán | M2 | M3 rà soát Contract và mã lý do từ chối |
| 3.3 Kiến trúc tổng thể | M1 | |
| 3.4 Cài đặt engine và luật | M2 | |
| 3.5.1 Giao diện chung và budget, 3.5.2 Random | M3 | |
| 3.5.3 Heuristic, 3.5.4 Minimax và Alpha-Beta | M2 | |
| 3.5.5 MCTS | M1 | |
| 3.6.1 Sinh dữ liệu self-play | M3 | `Dataset_v1_Data_Card.md` |
| 3.6.2 Mạng và huấn luyện, 3.6.3 NeuralAgent | M1 | |
| 3.7 Thiết kế giải đấu và đánh giá, 3.8 Kiểm thử | M3 | |
| 4.1, 4.2, 4.6, 4.7.1 | M3 | Log giải đấu |
| 4.3 Kết quả Minimax/Alpha-Beta | M3 | M2 (ablation Alpha-Beta, Move Ordering) |
| 4.4 Kết quả MCTS | M3 | M1 (số simulation, độ ổn định theo seed) |
| 4.5 Kết quả tác tử học được | M3 | M1 (learning curve, latency, RAM/VRAM) |
| 4.7.2, 4.7.3 Ván điển hình và trường hợp thất bại | M2 | M3 (log ván đấu, quy tắc chọn ván) |
| Chương 5 Ứng dụng minh họa | M1 | Video demo |
| Chương 6 Kết luận và hướng phát triển | M3 tổng hợp _(đề xuất)_ | Mỗi thành viên nêu hạn chế phần mình |
| Phụ lục A, B, D, E, F | M3 | |
| Phụ lục C Bộ kịch bản chiến thuật | M2 | |

---

## DANH MỤC CÁC BẢNG

> [!NOTE]
> Số bảng là số **sau khi đánh lại** theo bố cục 6 chương. Bảng 3.1–3.8 hiện trong bản báo cáo chính mới đánh số đến Bảng 3.6, các bảng còn lại cần đánh lại khi hoàn thiện các mục 3.4 đến 3.8.

| Ký hiệu bảng | Tên bảng |
| ------------ | -------- |
| Bảng 1.1 | Ma trận mục tiêu, tiêu chí hoàn thành và sản phẩm bàn giao |
| Bảng 2.1 | Phân loại tám cấp độ tác tử Game AI |
| Bảng 2.2 | So sánh đặc điểm các thuật toán Random, Heuristic, Minimax và MCTS |
| Bảng 3.1 | Các yêu cầu chức năng (F01–F07) |
| Bảng 3.2 | Các yêu cầu phi chức năng (NFR01–NFR04) |
| Bảng 3.3 | Ánh xạ giữa mô hình trò chơi và giao diện của hệ thống |
| Bảng 3.4 | Quy ước tọa độ (row, col) trên bàn cờ 11×11 |
| Bảng 3.5 | Các thành phần của trạng thái trò chơi |
| Bảng 3.6 | Thứ tự kiểm tra hành động và các lý do từ chối nước đi (Reason Codes) |
| Bảng 3.7 | Phần thưởng theo trạng thái sau `step` |
| Bảng 3.8 | Giá trị trả về của `result(player)` |
| Bảng 3.9 | Các thành phần của phân hệ cốt lõi và quy tắc trò chơi |
| Bảng 3.10 | Các tác tử trong hệ thống |
| Bảng 3.11 | Các tiện ích điều khiển thực nghiệm |
| Bảng 3.12 | Các thành phần giao diện |
| Bảng 3.13 | Phân tích độ phức tạp thời gian và bộ nhớ của `step`, `undo`, `clone_env` |
| Bảng 3.14 | Trọng số điểm Heuristic của các mẫu hình (Patterns) tấn công và phòng thủ |
| Bảng 3.15 | Tham số cấu hình của các Agent (Heuristic, Minimax/Alpha-Beta, MCTS) |
| Bảng 3.16 | Số ván self-play theo cặp tác tử |
| Bảng 3.17 | Các kênh của tensor trạng thái |
| Bảng 3.18 | Số lượng mẫu theo từng tập (train/validation/test) |
| Bảng 4.1 | Cấu hình môi trường phần cứng, phần mềm và thông số benchmark |
| Bảng 4.2 | Kết quả kiểm thử bộ kịch bản chiến thuật (Tactical scenarios) của các tác tử |
| Bảng 4.3 | So sánh hiệu năng Minimax có/không có Alpha-Beta và Move Ordering theo độ sâu |
| Bảng 4.4 | Hiệu năng MCTS theo các mức ngân sách mô phỏng (100, 400, 1000 simulations) |
| Bảng 4.5 | Kết quả huấn luyện và so sánh của tác tử học được |
| Bảng 4.6 | Ma trận đối đầu tổng thể giải đấu (Cross-Table) và tỷ lệ thắng theo bên X/O |
| Bảng 5.1 | Danh mục chức năng giao diện Streamlit và trạng thái tích hợp thực tế |

---

## DANH MỤC HÌNH

| Ký hiệu hình | Tên hình |
| ------------ | -------- |
| Hình 2.1 | Minh họa các mẫu hình cờ: chuỗi 5 thắng, chặn 1 đầu, chặn 2 đầu và sát biên |
| Hình 2.2 | Sơ đồ cây trò chơi và cơ chế cắt tỉa Alpha-Beta |
| Hình 2.3 | Bốn pha hoạt động của Monte Carlo Tree Search (Selection, Expansion, Rollout, Backpropagation) |
| Hình 3.1 | Sơ đồ kiến trúc tổng thể phân tầng hệ thống Caro AI (`engine`, `agents`, `ml`, `utils`, `ui`, `tests`) |
| Hình 3.2 | Sơ đồ tương tác luồng dữ liệu của một lượt chơi giữa UI/Runner, Agent và CaroEnv |
| Hình 3.3 | Luồng vận hành giải đấu: sinh seed, budget enforce, ghi log JSONL và tổng hợp metric |
| Hình 3.4 | Lưu đồ thuật toán đánh giá trạng thái và chọn nước đi của Heuristic Agent |
| Hình 3.5 | Lưu đồ thuật toán Minimax kết hợp cắt tỉa Alpha-Beta và sắp xếp nước đi |
| Hình 3.6 | Cấu trúc Node MCTS và luồng cập nhật giá trị Visit count / Q-value |
| Hình 4.1 | Biểu đồ so sánh số node duyệt và thời gian thực thi của Minimax theo độ sâu |
| Hình 4.2 | Biểu đồ tỷ lệ thắng và thời gian phản hồi của MCTS theo số lượng mô phỏng |
| Hình 4.3 | Đường cong học tập của tác tử học được (loss/reward theo epoch) |
| Hình 4.4 | Biểu đồ nhiệt (Heatmap) tỷ lệ thắng đối đầu chéo giữa các tác tử |
| Hình 5.1 | Giao diện bàn cờ Caro 11×11 trên ứng dụng Streamlit khi bắt đầu ván chơi |
| Hình 5.2 | Giao diện hiển thị ván cờ kết thúc, thông báo thắng/hòa và khóa bàn cờ |

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

> [!NOTE]
> Số trang sẽ được điền khi xuất bản in cuối cùng (cập nhật mục lục tự động trong trình soạn thảo sau khi đánh lại số mục).

- **CHƯƠNG 1. TỔNG QUAN VỀ ĐỀ TÀI**
  - 1.1. Phát biểu đề tài
  - 1.2. Mục tiêu và phạm vi của đề tài
    - 1.2.1. Mục tiêu
    - 1.2.2. Phạm vi
  - 1.3. Đối tượng sử dụng
  - 1.4. Kết quả dự kiến
  - 1.5. Cấu trúc báo cáo
- **CHƯƠNG 2. CƠ SỞ LÝ THUYẾT LIÊN QUAN**
  - 2.1. Tổng quan trò chơi Caro
    - 2.1.1. Lịch sử và các biến thể Gomoku/Caro
    - 2.1.2. Luật Caro được sử dụng trong đề tài
    - 2.1.3. Đặc điểm không gian trạng thái và độ khó tìm kiếm
  - 2.2. Mô hình trò chơi đối kháng
    - 2.2.1. Trạng thái, hành động và hàm chuyển trạng thái
    - 2.2.2. Trạng thái kết thúc, utility và reward
    - 2.2.3. Cây trò chơi
  - 2.3. Tác tử thông minh trong trò chơi đối kháng
    - 2.3.1. Khái niệm tác tử trò chơi
    - 2.3.2. Phân loại các tác tử Game AI
  - 2.4. Hàm đánh giá heuristic
  - 2.5. Thuật toán Minimax
    - 2.5.1. Nguyên lý Minimax
    - 2.5.2. Độ phức tạp thời gian và bộ nhớ
    - 2.5.3. Minimax giới hạn độ sâu và đánh giá lá
  - 2.6. Các kỹ thuật tối ưu Minimax
    - 2.6.1. Cắt tỉa Alpha-Beta
    - 2.6.2. Sắp xếp nước đi (Move Ordering)
    - 2.6.3. Lọc nước ứng viên theo lân cận (Candidate Filtering)
    - 2.6.4. Tìm kiếm sâu dần (Iterative Deepening)
    - 2.6.5. Giới hạn theo độ sâu, số node và thời gian
  - 2.7. Monte Carlo Tree Search
    - 2.7.1. Tổng quan MCTS
    - 2.7.2. Selection và công thức UCT
    - 2.7.3. Expansion
    - 2.7.4. Simulation / Rollout
    - 2.7.5. Backpropagation
    - 2.7.6. Ngân sách số mô phỏng, số node và thời gian
    - 2.7.7. Vai trò của seed và tính tái lập
  - 2.8. Đánh giá tác tử chơi game
  - 2.9. Học sâu cho trò chơi bàn cờ
- **CHƯƠNG 3. PHƯƠNG PHÁP VÀ THIẾT KẾ HỆ THỐNG**
  - 3.1. Phân tích yêu cầu
    - 3.1.1. Yêu cầu chức năng
    - 3.1.2. Yêu cầu phi chức năng
  - 3.2. Mô hình hóa bài toán
    - 3.2.1. Biểu diễn bàn cờ
    - 3.2.2. Biểu diễn trạng thái
    - 3.2.3. Hành động hợp lệ, hàm chuyển và kết quả
    - 3.2.4. Clone và undo cho tìm kiếm
  - 3.3. Kiến trúc tổng thể
    - 3.3.1. Tổng quan mô hình kiến trúc
    - 3.3.2. Phân tích chi tiết các phân hệ chức năng
    - 3.3.3. Sơ đồ tương tác luồng dữ liệu
  - 3.4. Cài đặt engine và luật
    - 3.4.1. Board và dữ liệu bàn cờ
    - 3.4.2. RuleEngine, kiểm tra bốn hướng
    - 3.4.3. CaroEnv và vòng đời ván chơi
    - 3.4.4. Snapshot phòng vệ, clone, history stack
    - 3.4.5. Độ phức tạp của step, undo, clone_env
  - 3.5. Các tác tử tìm kiếm
    - 3.5.1. Giao diện chung và ngữ nghĩa budget
    - 3.5.2. Random Agent
    - 3.5.3. Heuristic Agent
    - 3.5.4. Minimax và Alpha-Beta
    - 3.5.5. MCTS
  - 3.6. Tác tử học được và dữ liệu
    - 3.6.1. Sinh dữ liệu self-play: số ván, cách gán nhãn, loại trùng, chia train/val/test theo ván
    - 3.6.2. Kiến trúc mạng, huấn luyện, checkpoint, seed, tài nguyên CPU/GPU
    - 3.6.3. NeuralAgent suy luận qua interface chung
  - 3.7. Thiết kế giải đấu và đánh giá
    - 3.7.1. Câu hỏi nghiên cứu
    - 3.7.2. Luồng chạy game, match, tournament; đổi bên X/O
    - 3.7.3. Sinh seed, budget enforcer
    - 3.7.4. Schema log JSONL và manifest
    - 3.7.5. Chỉ số và giao thức thí nghiệm
  - 3.8. Chiến lược kiểm thử
- **CHƯƠNG 4. THỰC NGHIỆM VÀ ĐÁNH GIÁ**
  - 4.1. Môi trường và cấu hình thực nghiệm
    - 4.1.1. Môi trường thực nghiệm
    - 4.1.2. Đối tượng và cấu hình so sánh
    - 4.1.3. Bộ kịch bản cố định
  - 4.2. Kết quả kiểm tra tính đúng
  - 4.3. Kết quả Minimax/Alpha-Beta
    - 4.3.1. Ảnh hưởng của độ sâu
    - 4.3.2. Alpha-Beta bật/tắt
    - 4.3.3. Move ordering bật/tắt
    - 4.3.4. Số node, thời gian và chất lượng nước đi
  - 4.4. Kết quả MCTS
    - 4.4.1. Ảnh hưởng của số simulation
    - 4.4.2. Độ ổn định theo seed
    - 4.4.3. Thời gian và chất lượng nước đi
  - 4.5. Kết quả tác tử học được
    - 4.5.1. Thiết lập huấn luyện thực tế
    - 4.5.2. Đường cong học tập
    - 4.5.3. So sánh với các baseline
  - 4.6. Kết quả giải đấu
  - 4.7. Phân tích ván đấu điển hình và trường hợp thất bại
    - 4.7.1. Ảnh hưởng của đi trước/đi sau
    - 4.7.2. Các ván đấu điển hình
    - 4.7.3. Các trường hợp agent mắc lỗi
- **CHƯƠNG 5. XÂY DỰNG ỨNG DỤNG MINH HỌA**
  - 5.1. Mục tiêu ứng dụng
  - 5.2. Công nghệ sử dụng
  - 5.3. Thiết kế giao diện và trải nghiệm
  - 5.4. Tích hợp UI với engine
  - 5.5. Các chức năng đã hoàn thành
  - 5.6. Kiểm thử ứng dụng
  - 5.7. Hạn chế hiện tại
- **CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN**
  - 6.1. Kết luận
  - 6.2. Hạn chế
  - 6.3. Hướng phát triển

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
  - Cài đặt và tinh chỉnh 4 nhóm tác tử tìm kiếm (Random, Heuristic, Minimax/Alpha-Beta, MCTS) tuân thủ nguyên tắc không làm biến đổi (mutation) môi trường thật và tuân thủ ngân sách tìm kiếm (`SearchBudget`).
  - Sinh bộ dữ liệu self-play `dataset-v1` và huấn luyện ít nhất một tác tử học được (`NeuralAgent`) theo yêu cầu của đề.
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
  - Học tăng cường và các tác tử AlphaGo/AlphaZero-inspired (cấp 6–8 của đề) không nằm trong phạm vi chính; tác tử học được trong đề tài chỉ học policy có giám sát từ dữ liệu self-play, còn RL/AlphaZero-inspired được định vị là hướng phát triển.

## 1.3. Đối tượng sử dụng

- **Sinh viên và người học AI**: Quan sát trực quan cơ chế vận hành, sự khác biệt về triết lý giữa tìm kiếm vét cạn/cắt tỉa (Minimax/Alpha-Beta) và tìm kiếm lấy mẫu thống kê (MCTS).
- **Nhà nghiên cứu / Lập trình viên game**: Sử dụng engine và harness benchmark có sẵn để thử nghiệm các ý tưởng thuật toán mới với tính tái lập được bảo đảm tuyệt đối.
- **Người dùng phổ thông**: Trải nghiệm giao diện chơi cờ trực quan, tương tác đối kháng trực tiếp trên nền tảng web Streamlit.

## 1.4. Kết quả dự kiến

- Engine trò chơi chuẩn mực, không lỗi rò rỉ trạng thái, tốc độ cao.
- Bộ mã nguồn 4 tác tử AI hoàn chỉnh, chạy ổn định theo interface chung.
- Bộ dữ liệu self-play `dataset-v1` có manifest và checksum, cùng tác tử học được huấn luyện trên bộ dữ liệu này.
- Bộ log thực nghiệm JSONL, bảng tổng hợp metric chi tiết và biểu đồ phân tích.
- Ứng dụng Streamlit minh họa hoạt động ổn định và thân thiện.

## 1.5. Cấu trúc báo cáo

Báo cáo được bố cục thành 6 chương chính:

- **Chương 1**: Tổng quan về đề tài, mục tiêu, phạm vi và đối tượng nghiên cứu.
- **Chương 2**: Cơ sở lý thuyết nền tảng về trò chơi đối kháng, tác tử Game AI, Heuristic, Minimax/Alpha-Beta, MCTS và học sâu cho trò chơi bàn cờ.
- **Chương 3**: Phương pháp và thiết kế hệ thống: phân tích yêu cầu, mô hình hóa bài toán, kiến trúc, cài đặt engine, các tác tử tìm kiếm, tác tử học được và dữ liệu, thiết kế giải đấu và chiến lược kiểm thử.
- **Chương 4**: Thực nghiệm và đánh giá: môi trường thực nghiệm, kiểm tra tính đúng, kết quả Minimax/Alpha-Beta, MCTS, tác tử học được, giải đấu giữa các tác tử, cùng phân tích ván đấu điển hình và các trường hợp thất bại.
- **Chương 5**: Xây dựng ứng dụng minh họa trên nền tảng Streamlit.
- **Chương 6**: Kết luận, hạn chế và hướng phát triển trong tương lai.

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

### 2.2.3. Cây trò chơi

- Cấu trúc cây trò chơi (Game Tree): Gốc là trạng thái hiện tại, mỗi nhánh tương ứng với một nước đi hợp lệ, các node lá biểu diễn trạng thái kết thúc hoặc trạng thái đạt độ sâu giới hạn.
- Nguyên lý chọn nước đi tối ưu theo nguyên tắc Minimax: Giả định đối phương luôn đưa ra quyết định tốt nhất để giảm thiểu tối đa điểm số của mình.

## 2.3. Tác tử thông minh trong trò chơi đối kháng

### 2.3.1. Khái niệm tác tử trò chơi

- Tác tử trò chơi (Game Agent): hệ thống tự đưa ra quyết định dựa trên thông tin nhận được từ môi trường.
- Chính sách (policy) của tác tử: $a^* = \pi(s)$ với chính sách tất định; $\pi(a \mid s)$ với phương pháp có yếu tố ngẫu nhiên.
- Sự khác biệt giữa các tác tử nằm ở cách xây dựng chính sách: thiết lập sẵn bằng luật, xác định bằng thuật toán tìm kiếm, hoặc hình thành từ huấn luyện trên dữ liệu.

### 2.3.2. Phân loại các tác tử Game AI

- Bảng tám cấp độ tác tử theo đề: Random, Rule-based/Heuristic, Minimax/Alpha-Beta, MCTS (UCT), Neural Network, Reinforcement Learning, AlphaGo-inspired, AlphaZero-inspired (Bảng 2.1).
- Lưu ý: cấp độ phản ánh mức độ phức tạp của phương pháp, không mặc nhiên tương ứng với sức mạnh thi đấu thực tế.
- Phạm vi đề tài: cấp 1–4 (tìm kiếm) và cấp 5 (Neural Network, học policy có giám sát); cấp 6–8 là hướng phát triển.

## 2.4. Hàm đánh giá heuristic

- Định nghĩa và vai trò của hàm Heuristic tĩnh $h(s)$ khi cây trò chơi không thể duyệt tới các node kết thúc do giới hạn tài nguyên tính toán.
- Phân tích các mẫu hình (Patterns) mang tính quyết định:
  - Chuỗi 5 quân (Win): Đã hoàn thành 5 quân liên tiếp.
  - Chuỗi 4 quân mở hai đầu (Open 4): Đe dọa không thể ngăn cản trong 1 nước.
  - Chuỗi 4 quân chặn một đầu (Closed 4): Buộc đối thủ phải phản ứng chặn ngay lập tức.
  - Chuỗi 3 quân mở hai đầu (Open 3): Tiền đề tạo thế công đôi (Double threat).
  - Chuỗi 2 quân mở hai đầu (Open 2) và các vị trí chiếm đóng trung tâm bàn cờ.
- Cân bằng giữa yếu tố tấn công (Offense) và phòng thủ (Defense).
- Kỹ thuật phá vỡ thế hòa (Tie-break) tất định để tránh hành vi bất định.

## 2.5. Thuật toán Minimax

### 2.5.1. Nguyên lý Minimax

- Công thức đệ quy Minimax tìm kiếm nước đi:
  $$V(s) = \begin{cases} U(s) & \text{nếu } s \in S_{term} \\ \max_{a \in A(s)} V(T(s, a)) & \text{nếu lượt MAX} \\ \min_{a \in A(s)} V(T(s, a)) & \text{nếu lượt MIN} \end{cases}$$

### 2.5.2. Độ phức tạp thời gian và bộ nhớ

- Độ phức tạp thời gian vét cạn: $\mathcal{O}(b^d)$ với $b$ là hệ số phân nhánh trung bình và $d$ là độ sâu tìm kiếm.
- Độ phức tạp bộ nhớ: $\mathcal{O}(b \cdot d)$ đối với thuật toán duyệt theo chiều sâu (DFS).

### 2.5.3. Minimax giới hạn độ sâu và đánh giá lá

- Cắt tỉa cây ở độ sâu cố định $d_{max}$ và thay thế giá trị kết thúc bằng hàm đánh giá Heuristic $h(s)$ tại các node lá.
- Vấn đề hiệu ứng chân trời (Horizon Effect) và sai số đánh giá trạng thái.

## 2.6. Các kỹ thuật tối ưu Minimax

### 2.6.1. Cắt tỉa Alpha-Beta

- Giới thiệu hai biên $\alpha$ (giá trị nhỏ nhất mà người chơi MAX đã bảo đảm đạt được) và $\beta$ (giá trị lớn nhất mà người chơi MIN có thể ghìm đối thủ lại).
- Điều kiện cắt tỉa: Khi $\alpha \ge \beta$, nhánh tìm kiếm hiện tại được bảo đảm không ảnh hưởng đến quyết định tối ưu ở node cha và được loại bỏ ngay lập tức.
- Độ phức tạp thời gian trong trường hợp tối ưu nhất: $\mathcal{O}(b^{d/2})$, cho phép tăng gấp đôi độ sâu tìm kiếm với cùng lượng thời gian tính toán.

### 2.6.2. Sắp xếp nước đi (Move Ordering)

- Tầm quan trọng của việc duyệt các nước đi tiềm năng nhất trước để kích hoạt điều kiện cắt tỉa $\alpha \ge \beta$ sớm nhất.
- Sử dụng điểm đánh giá heuristic sơ bộ của nước đi để sắp xếp danh sách các nước đi ứng viên.

### 2.6.3. Lọc nước ứng viên theo lân cận (Candidate Filtering)

- Chiến lược loại bỏ các ô cờ trống cách quá xa các quân cờ đã có trên bàn cờ.
- Khái niệm bán kính lân cận Chebyshev ($r=1$ hoặc $r=2$ xung quanh các ô không trống), giúp giảm hệ số phân nhánh từ ~100 xuống còn 10–25 nước đi khả dĩ.

### 2.6.4. Tìm kiếm sâu dần (Iterative Deepening)

- Lặp lại quá trình tìm kiếm với độ sâu tăng dần từ $d = 1, 2, \dots, D$.
- Ưu điểm: Luôn có sẵn nước đi dự phòng tốt nhất từ độ sâu trước đó nếu bị ngắt do chạm giới hạn thời gian.

### 2.6.5. Giới hạn theo độ sâu, số node và thời gian

- Kiểm soát đa chiều: Dừng tìm kiếm khi vượt quá độ sâu tối đa (`max_depth`), số lượng node đã duyệt (`max_nodes`) hoặc thời gian cho phép (`time_limit_ms`).

## 2.7. Monte Carlo Tree Search

### 2.7.1. Tổng quan MCTS

- Giới thiệu họ thuật toán tìm kiếm heuristic dựa trên mô phỏng ngẫu nhiên, không đòi hỏi hàm đánh giá trạng thái tĩnh phức tạp.
- Khả năng hội tụ tiệm cận về quyết định tối ưu theo định lý giới hạn trung tâm.

### 2.7.2. Selection và công thức UCT

- Quá trình duyệt từ node gốc xuống các node lá của cây tìm kiếm dựa trên chỉ số UCT (Upper Confidence Bound applied to Trees):
  $$UCT(i) = \frac{Q(i)}{N(i)} + C \times \sqrt{\frac{\ln N(p)}{N(i)}}$$
  Trong đó $Q(i)$ là tổng phần thưởng tích lũy, $N(i)$ là số lần node $i$ được thăm, $N(p)$ là số lần thăm của node cha, và hằng số khám phá $C = \sqrt{2}$.
- Cân bằng giữa khai thác (Exploitation) và khám phá (Exploration).

### 2.7.3. Expansion

- Điều kiện mở rộng: Khi chạm vào một node chưa được khám phá hết các hành động hợp lệ, tạo thêm một node con mới tương ứng với một nước đi chưa thử.

### 2.7.4. Simulation / Rollout

- Từ node mới tạo, thực hiện một ván chơi giả lập nhanh (Playout/Rollout) đến khi đạt trạng thái kết thúc hoặc chạm độ sâu mô phỏng tối đa bằng chính sách ngẫu nhiên hoặc heuristic nhẹ.

### 2.7.5. Backpropagation

- Truyền ngược kết quả ván chơi giả lập (thắng/hòa/thua) từ node lá lên tất cả các node tổ tiên đến tận node gốc.
- Góc nhìn người chơi: Đảm bảo điểm số thưởng được đảo dấu phù hợp tương ứng với góc nhìn của bên đi tại mỗi node.

### 2.7.6. Ngân sách số mô phỏng, số node và thời gian

- Thiết lập ngưỡng dừng của MCTS: Giới hạn số lượt mô phỏng (`max_simulations`), số node mở rộng tối đa (`max_nodes`), và thời gian tối đa (`time_limit_ms`).

### 2.7.7. Vai trò của seed và tính tái lập

- Sự cần thiết của bộ sinh số ngẫu nhiên cục bộ (`random.Random(seed)`), bảo đảm mọi chuỗi rollout và quyết định của MCTS đều có thể tái tạo hoàn toàn trong các lần chạy kiểm thử.

## 2.8. Đánh giá tác tử chơi game

- Tiêu chí định lượng: Tỷ lệ thắng (Win rate), tỷ lệ hòa (Draw rate), tỷ lệ thua (Loss rate).
- Tiêu chí định tính: Khả năng giải quyết các thế cờ chiến thuật chuẩn (Tactical benchmark: phát hiện nước thắng ngay trong 1 nước, chặn nước thắng của đối thủ).
- Chi phí tài nguyên: Thời gian trung bình mỗi nước đi, phân vị 95th (p95 latency), số node Minimax duyệt, số mô phỏng MCTS hoàn tất.
- Yêu cầu công bằng: Hoán đổi lượt đi trước/sau (X và O) trong các cặp đấu để loại bỏ triệt để lợi thế bên đi trước.

## 2.9. Học sâu cho trò chơi bàn cờ

- Biểu diễn bàn cờ dạng tensor nhiều kênh (current player, opponent, legal) làm đầu vào cho mạng tích chập.
- Mạng policy dự đoán phân phối xác suất nước đi, mạng value đánh giá trạng thái; học có giám sát từ dữ liệu self-play/expert so với học tăng cường và self-play.
- Rủi ro khi học bắt chước: nhãn kế thừa thiên kiến của tác tử giáo viên và nguy cơ học lại heuristic.
- Phân biệt AlphaGo-inspired (policy/value kết hợp MCTS) và AlphaZero-inspired (mạng policy-value, tìm kiếm PUCT, self-play lặp); đề tài **không** khẳng định tái hiện đầy đủ các hệ thống nguyên bản.
- Tăng cường dữ liệu theo nhóm đối xứng $D_4$ của bàn cờ vuông (4 phép quay × phản chiếu).

---

# CHƯƠNG 3. PHƯƠNG PHÁP VÀ THIẾT KẾ HỆ THỐNG

> [!NOTE]
> Chương này gộp nội dung của Chương 3 và Chương 4 trong bản cấu trúc cũ, theo gợi ý của giảng viên (Chương 3: biểu diễn game/state/action/reward, kiến trúc, thuật toán từng cấp, dữ liệu, quy trình train và thiết kế giải đấu công bằng).

## 3.1. Phân tích yêu cầu

### 3.1.1. Yêu cầu chức năng

- Trình bày dưới dạng bảng (Bảng 3.1), mỗi yêu cầu 1–2 câu; chi tiết cơ chế của F01–F04 nằm ở mục 3.2.
  - F01: Khởi tạo và làm mới ván chơi (`reset()`).
  - F02: Xác thực và thực hiện nước đi (`step(action)`), hành động không hợp lệ ném `InvalidActionError` và giữ nguyên trạng thái.
  - F03: Xác định kết thúc và kết quả (quét 4 hướng; thắng khi chuỗi từ 5 quân không bị chặn đồng thời cả hai đầu; hòa khi đủ 121 ô; từ chối mọi hành động sau khi ván kết thúc).
  - F04: Hỗ trợ thuật toán tìm kiếm (`legal_actions()`, `clone_env()`, `undo()`).
  - F05: Chuẩn hóa giao diện Agent (`choose_action(env, budget)` trả về `AgentDecision`).
  - F06: Điều phối trận đấu và giải đấu (đổi bên X/O, ghi log, tổng hợp metric).
  - F07: Trực quan hóa trên giao diện Streamlit.

### 3.1.2. Yêu cầu phi chức năng

- Trình bày dưới dạng bảng (Bảng 3.2):
  - NFR01: Tính tái lập (đồng bộ seed trên engine và các agent ngẫu nhiên).
  - NFR02: Tính mô-đun, dễ kiểm thử và mở rộng (`pytest`, interface Agent chuẩn hóa).
  - NFR03: Kiểm soát ngân sách tài nguyên (`SearchBudget`).
  - NFR04: Chuẩn hóa log và mã hóa (JSON/JSONL, UTF-8).

## 3.2. Mô hình hóa bài toán

- Bảng ánh xạ giữa mô hình trò chơi và giao diện hệ thống (Bảng 3.3).

### 3.2.1. Biểu diễn bàn cờ

- Ma trận 2D $11 \times 11$; mã hóa `EMPTY = 0`, `PLAYER_X = 1`, `PLAYER_O = -1`.
- Quy ước tọa độ `(row, col)` với $0 \le row, col < 11$ (Bảng 3.4).

### 3.2.2. Biểu diễn trạng thái

- Bộ trạng thái $s = (B, p, \ell, m, \tau, w)$: bàn cờ, người chơi hiện tại, nước đi gần nhất, số nước đã đi, cờ kết thúc, người thắng (Bảng 3.5).
- Các bất biến của trạng thái (6 bất biến).

### 3.2.3. Hành động hợp lệ, hàm chuyển và kết quả

- Không gian hành động $A$ và tập hành động hợp lệ $L(s)$; `legal_actions()` trả về danh sách mới theo thứ tự hàng trước.
- Thứ tự kiểm tra hành động và các mã lý do `InvalidActionReason` (Bảng 3.6): `GAME_OVER`, `MALFORMED`, `OUT_OF_BOUNDS`, `OCCUPIED`.
- Tính nguyên tử: kiểm tra xong toàn bộ trước khi thay đổi bất kỳ dữ liệu nào; hành động không hợp lệ giữ nguyên trạng thái.
- Hàm chuyển $\delta(s, a) \rightarrow s'$ gồm 5 bước (lưu snapshot, đặt quân, cập nhật $\ell$ và $m$, đánh giá luật, đổi lượt).
- Phần thưởng theo góc nhìn người vừa đi (Bảng 3.7) và hàm `result(player)` (Bảng 3.8).

### 3.2.4. Clone và undo cho tìm kiếm

- `clone_env()`: bản sao độc lập, bảo đảm tính chất cô lập (clone isolation).
- `undo()`: khôi phục từ ngăn xếp lịch sử; tính chất round-trip `step` rồi `undo` trả về đúng trạng thái trước đó.
- Dùng thống nhất ký hiệu $s$ theo mục 3.2.2 (không dùng $S_t$, $a_{last}$).

## 3.3. Kiến trúc tổng thể

### 3.3.1. Tổng quan mô hình kiến trúc

- Kiến trúc phân lớp kết hợp hướng thành phần, dựa trên Contract `caro-v2`; không có phụ thuộc vòng giữa các phân hệ.
- Lý do tiếp cận Contract-first: khóa giao tiếp giữa các thành viên phát triển song song; các kiểu dữ liệu chuẩn `GameConfig`, `GameState`, `StepResult`, `SearchBudget`, `AgentDecision`; đặc tả đầy đủ ở Phụ lục A.
- Cấu trúc thư mục dự án:

```
Caro_AI_Project/
├── core/
│   ├── engine/       # Lõi trò chơi: Board, RuleEngine, GameEnv, Interfaces
│   ├── agents/       # Các tác tử: Random, Heuristic, Minimax, MCTS, Neural
│   ├── ml/           # Chuỗi xử lý dữ liệu: replay, mã hóa, chia tập, loại trùng
│   └── utils/        # Logger JSONL, Tournament Runner
├── scripts/          # Sinh self-play, dựng dataset
├── configs/          # Cấu hình thực nghiệm, self-play, huấn luyện
├── benchmarks/       # Script đo kiểm hiệu năng cho từng agent
├── ui/               # Ứng dụng Streamlit và bộ điều khiển người dùng
├── tests/            # Unit, Contract, Integration
└── docs/             # Đặc tả contract, Data Card, tài liệu báo cáo
```

- Sơ đồ các tầng của hệ thống (Hình 3.1).

### 3.3.2. Phân tích chi tiết các phân hệ chức năng

- Phân hệ Cốt lõi và Quy tắc Trò chơi: `interfaces.py`, `board.py`, `rules.py`, `game_env.py` (Bảng 3.9).
- Phân hệ Tác tử Thông minh: mỗi agent mô tả **một dòng** (Bảng 3.10), chi tiết thuật toán chuyển sang mục 3.5 và 3.6; bất biến: agent chỉ làm việc trên bản sao từ `clone_env()` và trả về `AgentDecision` bất biến.
- Phân hệ Tiện ích và Điều khiển Thực nghiệm: `logger.py`, `tournament_runner.py` (Bảng 3.11).
- Phân hệ Cấu hình và Kịch bản Đo kiểm: `SearchBudget` (`time_limit_ms`, `max_depth`, `max_nodes`, simulations, seed) và các benchmark profile.
- Phân hệ Giao diện: `app.py`, `human_controller.py` (Bảng 3.12), chỉ nêu ngắn gọn và dẫn sang Chương 5.
- Phân hệ Học máy và Chuỗi xử lý dữ liệu: `core/ml/data_pipeline.py`, `scripts/generate_selfplay.py`, `scripts/build_dataset.py`; chi tiết ở mục 3.6.

### 3.3.3. Sơ đồ tương tác luồng dữ liệu

- Chu trình một lượt chơi (Hình 3.2): khởi tạo `CaroEnv` → yêu cầu nước đi (`choose_action` trên bản sao `clone_env()` kèm `SearchBudget`) → cập nhật và đánh giá (`step`, `RuleEngine`) → ghi nhận và hiển thị (`MoveRecord`, UI).

## 3.4. Cài đặt engine và luật

_(Gộp từ mục 3.5, 4.1 và 4.7 của bản cũ.)_

### 3.4.1. Board và dữ liệu bàn cờ

- Lưu trữ mảng hai chiều; chuyển đổi tọa độ tuple `(row, col)` và chỉ số phẳng; các hàm đặt quân, xóa quân (phục vụ undo), kiểm tra ô trống.

### 3.4.2. RuleEngine, kiểm tra bốn hướng

- Kiểm tra thắng tăng dần từ ô vừa đánh: quét 4 trục (ngang, dọc, chéo chính, chéo phụ), mỗi trục hai chiều.
- Điều kiện thắng: chuỗi từ 5 quân trở lên (kể cả overline) không bị chặn đồng thời cả hai đầu; biên bàn cờ tính là một đầu chặn.
- Thắng được xét trước hòa; hòa khi đủ 121 ô.

### 3.4.3. CaroEnv và vòng đời ván chơi

- Quy trình xử lý một `step(action)`: kiểm tra hợp lệ → đặt quân và ghi `history` → gọi `RuleEngine` → xác định thắng/hòa → đổi lượt → trả về `StepResult`.
- Khóa trạng thái khi ván kết thúc.

### 3.4.4. Snapshot phòng vệ, clone, history stack

- Snapshot bất biến (read-only) khi agent truy xuất trạng thái; ngăn xếp `history` lưu `(row, col, player)`; `undo()` khôi phục ô cờ, `current_player` và cờ `terminated`.
- Tách hoàn toàn Engine và UI; UI không tự cài đặt luật.
- Bộ kiểm thử biên: thắng sát biên, bị chặn một đầu sát góc, bị chặn hai đầu, chuỗi overline 6 quân.

### 3.4.5. Độ phức tạp của step, undo, clone_env

- `step`: $\mathcal{O}(1)$; `undo`: $\mathcal{O}(1)$; `clone_env`: $\mathcal{O}(N^2)$ với $N = 11$ (Bảng 3.13).

## 3.5. Các tác tử tìm kiếm

_(Gộp từ mục 3.6 và 4.2–4.5 của bản cũ.)_

### 3.5.1. Giao diện chung và ngữ nghĩa budget

- Giao diện `Agent`: `choose_action(env, budget) -> AgentDecision` với `action`, `score`, `nodes`, `simulations`, `elapsed_ms`.
- Chạm ngân sách thì trả về nước đi tốt nhất hiện có (fallback), không ném ngoại lệ.
- RNG cục bộ `random.Random(seed)`, không dùng RNG toàn cục.
- Bảng tham số cấu hình các agent (Bảng 3.15).

### 3.5.2. Random Agent

- Chọn ngẫu nhiên đều từ `legal_actions()` bằng RNG riêng; làm baseline và kiểm tra tính hợp lý (sanity check).

### 3.5.3. Heuristic Agent

- Thứ tự ưu tiên: thắng ngay → chặn đối thủ thắng → tạo Open 4 → chặn Open 4 → tạo/chặn Open 3 → ưu tiên trung tâm.
- Bảng điểm pattern và hệ số phòng thủ (Bảng 3.14); tie-break tất định; độ phức tạp.
- Lưu đồ thuật toán (Hình 3.4).

### 3.5.4. Minimax và Alpha-Beta

- Hàm đánh giá trạng thái; giá trị terminal (thắng sớm, thua muộn).
- Sinh tập nước ứng viên theo bán kính Chebyshev; bàn cờ rỗng chọn tâm $(5,5)$.
- Iterative deepening; cắt tỉa Alpha-Beta; move ordering; xử lý budget và fallback.
- Tham số cấu hình và đánh đổi độ sâu so với thời gian (Hình 3.5).

### 3.5.5. MCTS

- Cấu trúc node (`parent`, `children`, `action`, `visit_count`, `total_value`, `untried_actions`) (Hình 3.6).
- Selection bằng UCT; Expansion; Rollout; Backpropagation theo góc nhìn người chơi.
- Chọn action cuối cùng theo số lần viếng thăm lớn nhất (robust child).
- Seed, simulation budget, node budget và time budget.

## 3.6. Tác tử học được và dữ liệu

> [!NOTE]
> Theo đề của giảng viên, tối thiểu một tác tử học được (cấp 5 hoặc 6) phải được huấn luyện thật. Mục 3.6.1 do M3 (Thiện) viết từ `dataset-v1`; mục 3.6.2 và 3.6.3 do M1 (Hải) viết.

### 3.6.1. Sinh dữ liệu self-play: số ván, cách gán nhãn, loại trùng, chia train/val/test theo ván

- Nguồn dữ liệu: self-play giữa ba tác tử lập trình (Heuristic không dùng ngân sách tìm kiếm, Minimax Alpha-Beta độ sâu 2, MCTS 20 simulations), không dùng ván của người chơi; đổi bên X/O sau mỗi ván.
- Số ván: 2.000 (Heuristic–Minimax 668, Heuristic–MCTS 666, Minimax–MCTS 666) (Bảng 3.16); giữ toàn bộ ván hợp lệ, không chọn ván theo bên thắng; cả 2.000 ván vượt qua kiểm tra replay.
- Mã hóa: tensor $3 \times 11 \times 11$ `float32` gồm quân người chơi hiện tại, quân đối thủ, ô hợp lệ (Bảng 3.17); nhãn $y = row \times 11 + col$ là nước đi thực tế của tác tử giáo viên; kèm `legal_mask` 121 giá trị.
- Chia theo ván (không chia theo trạng thái), seed `20261107`, tỷ lệ 70/15/15: 1.400/300/300 ván; số ván giao nhau bằng 0.
- Loại trùng theo mã băm SHA-256 của (trạng thái, mặt nạ, nhãn), ưu tiên train rồi validation rồi test.
- Tăng cường $D_4$ (8 biến thể) chỉ trên train: 8.792 mẫu duy nhất thành 70.336 mẫu; validation 1.833 mẫu, test 1.573 mẫu (Bảng 3.18).
- Nguồn nhãn và hạn chế: nhãn bắt chước ba tác tử lập trình; MCTS yếu hơn rõ rệt; độ đa dạng quỹ đạo thấp; không phải bằng chứng của năng lực ngang người hay của học tăng cường.
- Tính toàn vẹn: checksum SHA-256 trong `dataset_manifest.json`; chỉ dùng validation để chọn mô hình, mở tập test một lần sau khi chốt cấu hình.
- _Cần bổ sung_: seed cơ sở của lượt self-play, cấu hình phần cứng và thời gian chạy (lấy từ `run_manifest.json`).

### 3.6.2. Kiến trúc mạng, huấn luyện, checkpoint, seed, tài nguyên CPU/GPU

- Kiến trúc mạng (policy hoặc policy-value), hàm mất mát, bộ tối ưu, siêu tham số.
- Quy trình huấn luyện: chỉ dùng validation để chọn siêu tham số và checkpoint; lưu checkpoint và seed.
- Khai báo tài nguyên CPU/GPU và thời gian huấn luyện.
- Chỉ ghi số liệu của lần huấn luyện đã thực hiện thật.

### 3.6.3. NeuralAgent suy luận qua interface chung

- `NeuralAgent` tuân thủ `Agent Protocol` và `SearchBudget`; áp mặt nạ hợp lệ lên đầu ra của mạng trước khi chọn nước đi.
- Chế độ policy-only; nếu có làm, thêm chế độ policy kết hợp MCTS để so sánh.
- Không dùng mạng chưa qua huấn luyện làm bằng chứng đã triển khai cấp Neural.

## 3.7. Thiết kế giải đấu và đánh giá

_(Gộp từ mục 3.7 của bản cũ, mục 4.6 và các mục 5.1, 5.5, 5.6 của Chương 5 cũ.)_

### 3.7.1. Câu hỏi nghiên cứu

- RQ1: Các tác tử có phát hiện đúng nước thắng ngay hoặc chặn thắng ngay trong các kịch bản chiến thuật cố định không?
- RQ2: Dưới điều kiện công bằng (đổi bên X/O), tác tử nào đạt tỷ lệ thắng vượt trội?
- RQ3: Đánh đổi giữa chất lượng nước đi và chi phí tính toán diễn ra như thế nào giữa các họ thuật toán?
- RQ4: Alpha-Beta kết hợp Move Ordering cắt giảm bao nhiêu phần trăm số node so với Minimax thuần?
- RQ5: Sức mạnh của MCTS biến thiên ra sao khi tăng ngân sách simulation từ 100 lên 400 và 1000?
- _Nếu bổ sung câu hỏi về tác tử học được (ví dụ self-play/policy-only so với heuristic), thêm RQ6 tại đây._

### 3.7.2. Luồng chạy game, match, tournament; đổi bên X/O

- Single game, match (2 ván đổi bên), tournament round-robin giữa các tác tử (Hình 3.3).
- Mỗi cặp đấu đối xứng cả hai bên; chia đều quyền đi trước và đi sau.

### 3.7.3. Sinh seed, budget enforcer

- Seed được gán cho từng ván và khởi tạo RNG cho cả môi trường lẫn agent; cùng cấu hình và seed cho cùng kết quả.
- Budget enforcer đo thời gian thực thi, ghi nhận vi phạm (`budget_violations`) và xử lý theo chế độ cấu hình (`fail_fast` hoặc ghi nhận).

### 3.7.4. Schema log JSONL và manifest

- Mỗi ván một bản ghi `GameRecord` chuẩn `caro-v2`: `game_id`, `seed`, `x_agent`, `o_agent`, `winner`, chi tiết từng nước đi kèm node, simulations, thời gian.
- Manifest ghi cấu hình, seed, mã checksum shard, thông tin phần cứng; mã hóa UTF-8.

### 3.7.5. Chỉ số và giao thức thí nghiệm

- Mỗi cặp đấu **tối thiểu 100 ván** (khuyến nghị 200), chia đều bên đi trước và đi sau; dùng nhiều seed với phương pháp có yếu tố ngẫu nhiên.
- Báo cáo theo **ít nhất hai chế độ**: ngân sách tính toán quy định rõ (thời gian mỗi nước hoặc số simulation) và cấu hình mặc định minh bạch; không suy diễn công bằng tính toán chỉ vì cùng độ sâu.
- Chỉ số: số và tỷ lệ thắng/hòa/thua; `score = (thắng + 0,5 × hòa) / tổng số ván`; thời gian trung bình mỗi nước và độ trễ p95; số node và số simulation; RAM/VRAM nếu phù hợp; thời gian huấn luyện; độ chính xác kịch bản chiến thuật; số vi phạm ngân sách (mục tiêu 0).
- Ma trận đối đầu và khoảng tin cậy (Wilson hoặc Bootstrap); kiểm tra ảnh hưởng của thứ tự đi trước, seed, độ sâu và ngân sách simulation.
- Ít nhất 2 ablation/sensitivity analysis: Alpha-Beta bật/tắt, Move Ordering bật/tắt, số simulation của MCTS (và policy-only so với policy+MCTS nếu có).
- Tiêu chí loại bỏ ván: vi phạm ngân sách quá 3 lần hoặc ném ngoại lệ thì xử thua.
- Toàn bộ log thô JSONL và mã sinh biểu đồ được lưu để tái lập.

## 3.8. Chiến lược kiểm thử

- Unit Test: `Board`, `RuleEngine`, các mẫu hình thắng/chặn 4 hướng và từng agent.
- Contract Test: tuân thủ đặc tả `caro-v2`.
- Property & Regression Test: nước đi ngẫu nhiên liên tục để bảo đảm không rò rỉ trạng thái hoặc treo hệ thống.
- Integration Test: chuỗi Agent, GameEnv, Logger, Tournament Runner.
- UI Test: tương tác Streamlit với engine thật (kết quả ở mục 5.6).
- Kiểm tra dữ liệu: replay toàn bộ ván, xác minh checksum, số ván giao nhau giữa các tập bằng 0, nhãn luôn nằm trong mặt nạ hợp lệ.

---

# CHƯƠNG 4. THỰC NGHIỆM VÀ ĐÁNH GIÁ

> [!NOTE]
> Các mục 4.1, 4.5 và 4.7 là mục mới so với bản cấu trúc cũ, được thêm để đáp ứng yêu cầu của đề (môi trường chạy, tác tử học được, phân tích ván đấu và trường hợp thất bại). Thiết kế thí nghiệm (câu hỏi nghiên cứu, giao thức, chỉ số) nằm ở mục 3.7.

## 4.1. Môi trường và cấu hình thực nghiệm

### 4.1.1. Môi trường thực nghiệm

- Phần cứng (CPU, số nhân/luồng, RAM, GPU nếu có), hệ điều hành, phiên bản Python và thư viện.
- Mã commit Git tương ứng, cấu hình trò chơi (bàn $11 \times 11$, thắng 5 quân không bị chặn hai đầu, Contract `caro-v2`).
- Tập seed cố định khai báo trong `configs/benchmark.json`.

### 4.1.2. Đối tượng và cấu hình so sánh

- Random; Heuristic; Minimax với độ sâu $d \in \{2, 3, 4\}$ ở ba biến thể (thuần, Alpha-Beta, Alpha-Beta + Move Ordering); MCTS ở 100, 400, 1000 simulations với $C = \sqrt{2}$; `NeuralAgent` (policy-only, và policy+MCTS nếu có).
- Các benchmark profile: `FAST`, `FAIR`, `MCTS-S`, `AB-D`.

### 4.1.3. Bộ kịch bản cố định

- Bàn cờ rỗng, khai cuộc, thắng trong 1 nước, chặn trong 1 nước, trung cuộc có thế đôi, các trường hợp biên và overline.

## 4.2. Kết quả kiểm tra tính đúng

- Kết quả `pytest` theo từng module (`engine`, `rules`, `agents`, `runner`).
- Độ chính xác trên bộ kịch bản chiến thuật (RQ1).
- Bằng chứng môi trường không bị thay đổi trái phép sau các lần agent tìm kiếm.
- Kết quả kiểm tra `dataset-v1`: số ván vượt qua replay, số ván giao nhau giữa các tập (0), checksum hợp lệ.

## 4.3. Kết quả Minimax/Alpha-Beta

### 4.3.1. Ảnh hưởng của độ sâu

- Tương quan giữa độ sâu, thời gian phản hồi và tỷ lệ thắng (Hình 4.1).

### 4.3.2. Alpha-Beta bật/tắt

- Phần trăm node được cắt tỉa so với Minimax thuần trên cùng độ sâu (RQ4).

### 4.3.3. Move ordering bật/tắt

- Mức giảm thêm số node nhờ sắp xếp nước đi.

### 4.3.4. Số node, thời gian và chất lượng nước đi

- Đồ thị đánh đổi giữa thời gian thực thi và số node.

## 4.4. Kết quả MCTS

### 4.4.1. Ảnh hưởng của số simulation

- Tỷ lệ thắng và thời gian khi tăng ngân sách từ 100 lên 400 và 1000 (RQ5, Hình 4.2).

### 4.4.2. Độ ổn định theo seed

- Độ biến động của nước đi khi đổi seed.

### 4.4.3. Thời gian và chất lượng nước đi

- Thời gian phản hồi thực tế trên phần cứng thử nghiệm.

## 4.5. Kết quả tác tử học được

### 4.5.1. Thiết lập huấn luyện thực tế

- Số ván, tỷ lệ chia train/val/test, tài nguyên CPU/GPU, thời gian huấn luyện (liên kết với mục 3.6).

### 4.5.2. Đường cong học tập

- Loss hoặc reward theo epoch/episode trên train và validation (Hình 4.3).

### 4.5.3. So sánh với các baseline

- So sánh `NeuralAgent` với Heuristic và MCTS; policy-only so với policy+MCTS nếu có thực hiện.
- Chỉ báo cáo số liệu của lần huấn luyện đã chạy thật; tập test chỉ mở một lần sau khi chốt cấu hình.

## 4.6. Kết quả giải đấu

- Ma trận đối đầu chéo (round-robin) giữa Random, Heuristic, Minimax (độ sâu 2, 3), MCTS (100, 400) và `NeuralAgent`, kèm khoảng tin cậy (Hình 4.4).
- Tỷ lệ thắng tách theo bên đi trước (X) và đi sau (O).
- Bảng xếp hạng theo `score` (hoặc Elo), báo cáo tối thiểu hai chế độ ngân sách (RQ2, RQ3).

## 4.7. Phân tích ván đấu điển hình và trường hợp thất bại

### 4.7.1. Ảnh hưởng của đi trước/đi sau

- Định lượng lợi thế đi trước (first-player advantage) từ kết quả giải đấu.

### 4.7.2. Các ván đấu điển hình

- Chọn ván theo quy tắc xác định (ví dụ ván có seed nhỏ nhất của mỗi cặp), nêu rõ quy tắc trong báo cáo; có cả ván thắng, thua và hòa; không chọn riêng ván thắng.

### 4.7.3. Các trường hợp agent mắc lỗi

- Vị trí chiến thuật dẫn đến thua, nguyên nhân (điểm mù heuristic, giới hạn độ sâu, tactical blindness của MCTS, thiên kiến học từ giáo viên).
- Phân biệt sức mạnh thi đấu thực nghiệm với tính tối ưu đã được chứng minh; kết quả không ngoại suy sang trò chơi khác.

---

# CHƯƠNG 5. XÂY DỰNG ỨNG DỤNG MINH HỌA

## 5.1. Mục tiêu ứng dụng

- Xây dựng một giao diện web trực quan, thân thiện, giúp người dùng dễ dàng tương tác và trải nghiệm trực tiếp các luật chơi và thuật toán của dự án.
- Minh họa rõ ràng trạng thái bàn cờ, chỉ báo lượt đi hiện tại, đánh dấu nước vừa đi gần nhất, hiển thị lịch sử ván cờ và thông báo kết quả.

## 5.2. Công nghệ sử dụng

- Ngôn ngữ lập trình: **Python**.
- Framework giao diện: **Streamlit** – giải pháp mã nguồn mở tối ưu cho các bài toán trình diễn ứng dụng học thuật và trí tuệ nhân tạo.
- Lý do lựa chọn Streamlit: Cho phép phát triển giao diện nhanh chóng, tương thích tự nhiên $100\%$ với mã nguồn Python của Game Engine và các tác tử AI mà không cần viết thêm tầng API trung gian phức tạp.

## 5.3. Thiết kế giao diện và trải nghiệm

- **Bố cục chính**:
  - Khu vực bàn cờ trung tâm: Ma trận lưới $11 \times 11$ các nút bấm tương tác, hiển thị trực quan các quân cờ X và O với màu sắc phân biệt rõ ràng.
  - Khung Sidebar điều khiển: Lựa chọn chế độ chơi, hiển thị thông tin cấu hình, bảng thống kê số ván thắng/hòa/thua trong phiên làm việc.
- **Trạng thái trực quan**:
  - Đánh dấu nổi bật (Highlight) nước cờ vừa được đánh gần nhất để người chơi dễ theo dõi thế trận.
  - Tự động vô hiệu hóa toàn bộ bàn cờ khi ván đấu kết thúc nhằm ngăn chặn các thao tác sai luật.
- **Luồng điều khiển**:
  - Nút bấm "Chơi lại / Ván mới" cho phép khởi tạo lại bàn cờ rỗng tức thì mà không làm mất lịch sử thống kê của phiên.

## 5.4. Tích hợp UI với engine

- Giao diện người dùng giao tiếp với engine thuần túy thông qua các phương thức của public API `CaroEnv` (`reset()`, `step()`, `get_state()`).
- Lớp điều khiển `HumanController` nhận sự kiện click chuột từ người dùng và đóng gói thành tuple tọa độ `(row, col)` chuẩn mực gửi tới `CaroEnv.step()`.
- Sử dụng cơ chế `st.session_state` để lưu giữ cá thể môi trường trò chơi và trạng thái ván cờ xuyên suốt các vòng đời rerun của Streamlit.

## 5.5. Các chức năng đã hoàn thành

- Chế độ chơi hai người đối kháng trực tiếp trên cùng một máy (Human vs Human) trên bàn cờ chuẩn $11 \times 11$.
- Hệ thống tự động xác định thắng cuộc hoặc hòa cờ theo đúng luật Caro dự án.
- Bảng nhật ký ghi lại chi tiết chuỗi các nước đi trong ván chơi.
- Thống kê tỷ số phiên chơi hiện tại (Số ván X thắng, O thắng, Hòa).
- Cơ chế phòng vệ ngăn chặn hoàn toàn việc click vào các ô đã có quân hoặc click sau khi ván cờ đã kết thúc.
- _Lưu ý_: Trình bày chính xác trạng thái tích hợp của các chế độ Người đấu với Máy (Human vs AI) và Máy đấu với Máy (AI vs AI) theo đúng phiên bản release thực tế của mã nguồn.

## 5.6. Kiểm thử ứng dụng

- Kiểm thử tự động giao diện và tích hợp engine thật bằng bộ script kiểm thử.
- Xác nhận các hành vi click hợp lệ, click vào ô đã chiếm đóng, và kiểm tra tính nhất quán của trạng thái hiển thị.
- Đảm bảo giao diện UI tuyệt đối không tự cài đặt lại các quy tắc kiểm tra thắng thua mà ủy quyền hoàn toàn cho `CaroEnv`.

## 5.7. Hạn chế hiện tại

- Giao diện Streamlit thực hiện tải lại toàn bộ trang (Full Page Rerun) khi có tương tác, dẫn đến độ trễ nhỏ về hiệu ứng thị giác so với các framework frontend chuyên dụng (React/Vue).
- Chưa hỗ trợ chế độ chơi trực tuyến nhiều người qua mạng Internet (chỉ chạy cục bộ trên môi trường máy chủ nội bộ hoặc máy cá nhân).
- Chưa tích hợp cơ chế hoàn tác nước đi (Undo) trực tiếp trên giao diện dành cho người chơi.

---

# CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

## 6.1. Kết luận

- **Tổng kết các kết quả đã đạt được**:
  - Xây dựng thành công hệ thống Game Engine Caro $11 \times 11$ chuẩn mực, tốc độ cao, hỗ trợ đầy đủ `clone` và `undo`, tuân thủ nghiêm ngặt Contract `caro-v2`.
  - Triển khai thành công 4 họ tác tử tìm kiếm: Random (Baseline), Heuristic (luật chuyên gia và mẫu hình), Minimax tối ưu hóa (Alpha-Beta, Move Ordering, Iterative Deepening) và Monte Carlo Tree Search (MCTS với công thức UCT).
  - Sinh bộ dữ liệu self-play `dataset-v1` (2.000 ván, chia 1.400/300/300 theo ván) và huấn luyện tác tử học được `NeuralAgent` _(điều chỉnh câu này theo kết quả thực tế của mục 3.6 và 4.5)_.
  - Xây dựng hệ thống giải đấu và đo kiểm tự động với khả năng tái lập $100\%$ bằng hạt giống ngẫu nhiên, trích xuất dữ liệu nhật ký JSONL đầy đủ.
  - Thực hiện các thí nghiệm định lượng và định tính sâu rộng, trả lời trọn vẹn 5 câu hỏi nghiên cứu (RQ1–RQ5) đặt ra ở đầu đề tài.
  - Xây dựng ứng dụng minh họa trực quan trên nền tảng web Streamlit phục vụ trình diễn và thử nghiệm trực tiếp.
- **Đối chiếu mục tiêu**: Toàn bộ các mục tiêu đặt ra ở Chương 1 đều đã được hoàn thành với các minh chứng thực nghiệm và kiểm thử tự động rõ ràng.

## 6.2. Hạn chế

- Minimax và Alpha-Beta vẫn gặp rào cản về độ sâu tìm kiếm trong môi trường thời gian thực (chưa vượt quá độ sâu 4) do hệ số phân nhánh trung cuộc của cờ Caro còn tương đối lớn.
- MCTS thuần túy đôi khi gặp điểm mù chiến thuật trong các tình huống ngắn hạn nếu ngân sách mô phỏng chưa đủ lớn và chính sách rollout còn mang tính ngẫu nhiên.
- Bộ trọng số điểm Heuristic được cấu hình dựa trên kinh nghiệm chuyên gia thủ công, chưa được tối ưu hóa tự động thông qua giải thuật di truyền (Genetic Algorithm) hay học máy.
- Tác tử học được chỉ học bắt chước ba tác tử lập trình trên `dataset-v1`, chưa có học tăng cường hay vòng lặp AlphaZero-inspired; chất lượng nhãn bị giới hạn bởi giáo viên (MCTS ở 20 simulations yếu hơn rõ rệt) và độ đa dạng quỹ đạo còn thấp (khoảng 82% mẫu bị loại do trùng). _(Chỉ giữ mục này ở phần Hạn chế tổng hợp; hạn chế riêng của giao diện đã nêu ở mục 5.7.)_

## 6.3. Hướng phát triển

- **Tích hợp sâu AI vào giao diện người dùng**: Mở rộng Streamlit để hỗ trợ mượt mà các chế độ Human vs AI và AI vs AI với thanh điều chỉnh độ khó trực tiếp trên sidebar.
- **Tối ưu hóa công nghệ tìm kiếm**: Cài đặt bảng chuyển vị (Transposition Table) sử dụng kỹ thuật Zobrist Hashing để loại bỏ việc tính toán lặp lại các trạng thái hoán vị trong Minimax và MCTS.
- **Mở rộng tác tử học được**: Bổ sung học tăng cường tự chơi (Self-play RL), mạng Policy-Value kết hợp MCTS (AlphaGo-inspired) và vòng lặp AlphaZero-inspired để thoát khỏi giới hạn học bắt chước từ các tác tử lập trình.
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

## Phụ lục F. Data Card của `dataset-v1`

- Toàn văn `Dataset_v1_Data_Card.md`: nguồn gốc dữ liệu, số ván theo cặp tác tử, cách mã hóa, loại trùng, chia theo ván, checksum các tệp và hạn chế.
- Lệnh tái lập dựng bộ dữ liệu (`scripts/build_dataset.py` với `configs/train_w56.json`).

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
| **Chuỗi xử lý dữ liệu `dataset-v1`** | `core/ml/data_pipeline.py`, `scripts/build_dataset.py`, `configs/train_w56.json`, `Dataset_v1_Data_Card.md` | Đã hoàn thành: replay 2.000 ván, chia 1.400/300/300 theo ván, loại trùng, $D_4$ chỉ trên train, checksum trong manifest |
| **Sinh dữ liệu self-play** | `scripts/generate_selfplay.py`, `configs/selfplay_w56.json` | Đã hoàn thành: 3 cặp tác tử, đổi bên X/O, manifest và checksum shard |
| **Mạng nơ-ron và `NeuralAgent`** | _(cần bổ sung đường dẫn mã huấn luyện, checkpoint và `NeuralAgent`)_ | _Cần xác nhận_: chỉ ghi "đã hoàn thành" khi đã huấn luyện và đánh giá thật |

---

## CHECKLIST KIỂM SOÁT TRƯỚC KHI KHÓA BÁO CÁO

- [x] Tiêu đề đề tài, thông tin Giảng viên hướng dẫn và nhóm tác giả được đồng bộ chính xác theo mẫu của Trường Đại học Sài Gòn.
- [x] Tỷ lệ đóng góp của 3 thành viên được ghi nhận chuẩn xác theo biểu mẫu: Trương Văn Thiện 33%, Trần Hồ Minh Hải 33%, Lê Thị Trúc Ly 33%.
- [x] Danh mục từ viết tắt phản ánh đúng 9 thuật ngữ quy định (AI, API, UI, MCTS, UCT, RNG, JSONL, CPU, RAM).
- [x] Số mục và tiêu đề các chương tuân thủ bố cục 6 chương do nhóm quy định (mục lục khớp với nội dung chi tiết).
- [x] Quy tắc luật cờ Caro 11×11 (chuỗi 5 quân không bị chặn 2 đầu, biên là 1 đầu chặn, hòa khi kín bàn) được mô tả nhất quán xuyên suốt các chương.
- [x] Phân định ranh giới rõ ràng: Phần cốt lõi đã cài đặt thực tế được mô tả ở thì hiện tại/đã đạt; các phần mở rộng (học tăng cường, AlphaGo/AlphaZero-inspired, Multiplayer) được ghi nhận minh bạch ở mục Hướng phát triển; Neural AI chỉ báo cáo kết quả của lần huấn luyện đã thực hiện thật.
- [x] Toàn bộ số liệu thực nghiệm được cam kết trích xuất từ bộ log JSONL và mã nguồn đo kiểm có khả năng tái lập hoàn toàn.
- [ ] Mỗi cặp đấu có tối thiểu 100 ván (khuyến nghị 200), chia đều bên đi trước/đi sau, có ma trận đối đầu và khoảng tin cậy (Wilson hoặc Bootstrap).
- [ ] Báo cáo theo ít nhất hai chế độ ngân sách và có ít nhất hai ablation/sensitivity analysis.
- [ ] Tác tử học được đã được huấn luyện thật, có đường cong học tập, checkpoint, seed và khai báo tài nguyên CPU/GPU, thời gian huấn luyện.
- [ ] Không dùng tập test hoặc các ván đánh giá cuối để chọn siêu tham số; tập test chỉ mở một lần.
- [ ] Các ván đấu minh họa ở mục 4.7 được chọn theo quy tắc xác định, có cả ván thắng, thua và hòa.
- [ ] Bảng "Phân chia công việc" (theo Kế hoạch triển khai), mục lục, danh mục bảng/hình và mục 1.5 trong báo cáo chính đã khớp với cấu trúc này.
