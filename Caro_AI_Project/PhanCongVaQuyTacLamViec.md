# Phân công Công việc và Quy tắc Làm việc Nhóm - Đề tài AI Caro

Tài liệu này quy định cấu trúc thư mục toàn dự án, quyền sở hữu mã nguồn (Code Ownership) của từng cá nhân và các quy tắc phối hợp chung khi sử dụng Git. Việc tuân thủ tuyệt đối cấu trúc này sẽ giúp dự án gọn gàng và triệt tiêu hoàn toàn rủi ro xung đột mã (Merge Conflict).

## 1. Cấu trúc Thư mục Dự án

Cấu trúc dưới đây lấy Jupyter Notebook làm trung tâm thực thi, tách biệt hoàn toàn phần lõi tĩnh (Engine/AI) và không gian phân tích động.

```text
Caro_AI_Project/
├── core/                           # CHỈ CHỨA LOGIC CỐT LÕI (Các tệp .py tĩnh)
│   ├── __init__.py
│   ├── engine/                     # Xử lý luật chơi, bàn cờ, trạng thái
│   │   ├── board.py                # Quản lý mảng bàn cờ, thay đổi kích thước
│   │   ├── rules.py                # Kiểm tra thắng/thua, luật chặn 2 đầu
│   │   └── game_env.py             # API môi trường tương tác (reset, step)
│   ├── agents/                     # Danh sách các thuật toán AI
│   │   ├── random_ai.py            # Tác tử Baseline Cấp 1
│   │   ├── heuristic_ai.py         # Tác tử Rule-based Cấp 2
│   │   ├── minimax_ai.py           # Tác tử Cấp 3 (hỗ trợ Alpha-Beta pruning)
│   │   ├── mcts_ai.py              # Tác tử MCTS Cấp 4
│   │   └── neural_ai.py            # Lớp bọc gọi mạng học sâu (Cấp 5)
│   ├── ml/                         # Mô-đun Học Máy
│   │   ├── architectures.py        # Kiến trúc mạng Neural (PyTorch/TensorFlow)
│   │   └── data_pipeline.py        # Xử lý dữ liệu self-play, parser SGF
│   └── utils/                      # Công cụ hỗ trợ
│       ├── logger.py               # Ghi nhận log ván đấu, số nút duyệt
│       └── tournament_runner.py    # Logic tổ chức giải đấu vòng tròn
│
├── notebooks/                      # TRUNG TÂM THỰC THI CHÍNH (Các tệp .ipynb)
│   ├── 01_SelfPlay_DataGen.ipynb   # Gọi các AI đấu nhau sinh dữ liệu thô
│   ├── 02_Data_Preprocessing.ipynb # Dùng Pandas làm sạch dữ liệu, chia tập Train/Val/Test
│   ├── 03_Train_Model.ipynb        # Khởi tạo mô hình Neural, chạy vòng lặp train, lưu Checkpoint
│   ├── 04_Tournament_Eval.ipynb    # Tổ chức giải đấu, tính ma trận Thắng/Thua, vẽ biểu đồ
│   └── 05_Ablation_Study.ipynb     # Phân tích độ nhạy (bật/tắt cắt tỉa, số mô phỏng MCTS)
│
├── data/                           # Lưu trữ dữ liệu hệ thống
│   ├── raw_logs/                   # File log lịch sử tự chơi thô (.json hoặc .txt)
│   └── processed_tensors/          # Dữ liệu dạng ma trận chuẩn bị cho train
│
├── models/                         # Trọng số của mô hình học sâu
│   └── checkpoints/                # Các file trọng số (.pth, .h5) từ bước huấn luyện
│
├── api/                            # Backend kết nối giao diện
│   └── main.py                     # Chạy FastAPI/Flask để bọc mạng Neural phục vụ UI
│
├── ui/                             # Giao diện ứng dụng người chơi
│   └── app.py                      # Giao diện web Next.js / Streamlit / Windows Forms
│
├── .gitignore                      # Bỏ qua file rác, checkpoint nặng, thư mục ảo
├── requirements.txt                # Khai báo: py_torch, pandas, numpy, jupyterlab, fastapi...
└── README.md                       # Hướng dẫn quy trình cài đặt, import và chạy code
```

## 2. Phân bổ Quyền Sở hữu Mã nguồn (Code Ownership)

Mỗi thành viên chỉ được phép chỉnh sửa logic trong các tệp tin và thư mục được phân công dưới đây.

### Trần Hồ Minh Hải: Chuyên trách UI, API & Mạng Học Sâu

*Chịu trách nhiệm ở lớp frontend, tầng xử lý API và mạng nơ-ron học sâu.*

* **`core/agents/mcts_ai.py`**: Lập trình thuật toán Monte Carlo Tree Search (4 bước: Selection, Expansion, Simulation, Backpropagation).
* **`core/agents/neural_ai.py`**: Lớp trung gian để tải trọng số mô hình Cấp 5 và gọi hàm dự đoán nước đi.
* **`core/ml/architectures.py`**: Định nghĩa kiến trúc mạng nơ-ron bằng PyTorch/TensorFlow.
* **`api/main.py`**: Khởi tạo API bằng FastAPI kết nối lõi AI với giao diện.
* **`ui/app.py`**: Xây dựng frontend (Next.js hoặc Streamlit).
* **`notebooks/03_Train_Model.ipynb`**: File thực thi huấn luyện mô hình (Supervised Learning).

### Lê Thị Trúc Ly: Chuyên trách Lõi Game & AI Tìm Kiếm

*Chịu trách nhiệm xây dựng luật chơi chuẩn xác và các thuật toán tìm kiếm truyền thống.*

* **`core/engine/board.py`**: Xử lý logic cấu trúc mảng lưới bàn cờ (9x9 hoặc 11x11).
* **`core/engine/rules.py`**: Viết thuật toán kiểm tra điều kiện thắng 5 quân và luật chặn 2 đầu.
* **`core/agents/heuristic_ai.py`**: Xây dựng bộ luật ưu tiên tĩnh (ưu tiên thắng, chặn đối thủ).
* **`core/agents/minimax_ai.py`**: Cài đặt thuật toán Minimax kết hợp tham số bật/tắt kỹ thuật cắt tỉa Alpha-Beta.
* **`notebooks/05_Ablation_Study.ipynb`**: File thực thi và vẽ biểu đồ đánh giá độ nhạy của thuật toán tìm kiếm.

### Trương Văn Thiện: Chuyên trách Thực Nghiệm & Luồng Dữ Liệu

*Chịu trách nhiệm quản lý môi trường tương tác, kịch bản tự động hóa và thao tác dữ liệu.*

* **`core/engine/game_env.py`**: Đóng gói bộ API Game chuẩn (`reset`, `step`, `legal_actions`).
* **`core/agents/random_ai.py`**: Cài đặt baseline Cấp 1 (đi ngẫu nhiên hợp lệ).
* **`core/ml/data_pipeline.py`**: Quy trình thu thập, parse dữ liệu SGF/log ra ma trận.
* **`core/utils/logger.py`** & **`core/utils/tournament_runner.py`**: Viết script tổ chức giải đấu vòng tròn tự động.
* **`notebooks/01_SelfPlay_DataGen.ipynb`**: Kịch bản kích hoạt AI tự chơi sinh dữ liệu thô.
* **`notebooks/02_Data_Preprocessing.ipynb`**: Dùng Pandas làm sạch log lỗi và chia tập Train/Validation.
* **`notebooks/04_Tournament_Eval.ipynb`**: File thực thi giải đấu và tính toán ma trận Tỷ lệ Thắng/Hòa/Thua.

## 3. Quy tắc Phối hợp và Sử dụng Git (Chống Conflict)

Để quá trình làm việc chung diễn ra trơn tru, toàn nhóm thống nhất tuân thủ 3 nguyên tắc sau:

### Nguyên tắc 1: Giao ước API (Contract First)

* **Thời hạn:** Trong tuần đầu tiên, Thành viên 2 và Thành viên 3 phải họp để chốt xong định dạng dữ liệu đầu vào/đầu ra của file `core/engine/game_env.py` (cấu trúc mảng `board`, input của hàm `step()`).
* **Cam kết:** Một khi đã chốt cấu trúc này, không ai được tự ý thay đổi cấu trúc dữ liệu trả về vì sẽ làm vỡ toàn bộ các model AI đang chạy.

### Nguyên tắc 2: Tôn trọng Quyền Sở Hữu (Import Only)

* Thành viên nào được phân công file nào thì mới có quyền viết mã (sửa đổi) trên file đó.
* Nếu Thành viên 1 cần dùng hàm luật game do Thành viên 2 viết, chỉ được phép `import` để sử dụng. **Tuyệt đối không vào file của người khác để chỉnh sửa code trực tiếp.**
* Nếu phát hiện lỗi (bug) nằm ở file của người khác, phải báo lại (issue) để người đó tự sửa trên nhánh (branch) của họ.

### Nguyên tắc 3: Chiến lược Nhánh (Branching) và `.gitignore`

* **Mỗi người một nhánh:** Nhóm làm việc theo mô hình Feature Branch. Mọi người tạo nhánh riêng (ví dụ: `feature/ui-haim1`, `feature/engine-lym2`) để làm việc. Chỉ gộp code (Merge vào nhánh `main`) khi đã chạy test nội bộ thành công.
* **Chặn tệp rác:** Phải tạo file `.gitignore` ngay từ commit đầu tiên. Bắt buộc đưa các thành phần sau vào `.gitignore` vì chúng là nguyên nhân số 1 gây conflict không thể sửa:
  * Các thư mục ẩn của Jupyter: `.ipynb_checkpoints/`
  * Các file cache của Python: `__pycache__/`, `*.pyc`
  * Môi trường ảo: `venv/`, `.env`
  * Dữ liệu thô và trọng số nặng: `models/checkpoints/*.pth`, `data/raw_logs/*` (Tránh làm đầy dung lượng kho chứa GitHub).