# Xây dựng và Đánh giá các Thuật toán Trí tuệ Nhân tạo cho Trò chơi Caro 11×11

Đồ án cuối kỳ môn **Trí tuệ nhân tạo nâng cao** — Khoa Công nghệ Thông tin, Trường Đại học Sài Gòn.

- **Giảng viên hướng dẫn:** TS. Đỗ Như Tài
- **Nhóm thực hiện:** Nhóm 05
- **Repository chính thức:** [https://github.com/minhhailtv6a1/Team_Project_TTNTNC_2025_2026](https://github.com/minhhailtv6a1/Team_Project_TTNTNC_2025_2026)

---

## 1. Tài nguyên trực tuyến (Colab, Dataset & Kết quả thực nghiệm)

Do các tệp tensor dữ liệu lớn và checkpoint trọng số mô hình không được commit trực tiếp lên GitHub, toàn bộ tài nguyên huấn luyện và kết quả thực nghiệm được lưu trữ đồng bộ trên Google Colab và Google Drive:

| Tài nguyên                              | Đường dẫn                                                                                                           | Ghi chú                                                                                     |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **GitHub Repository chính**             | [Team_Project_TTNTNC_2025_2026](https://github.com/minhhailtv6a1/Team_Project_TTNTNC_2025_2026)                     | Mã nguồn, notebook, cấu hình, bộ test và tài liệu báo cáo                                   |
| **Google Colab huấn luyện Policy v5**   | [Mở trên Google Colab](https://colab.research.google.com/drive/1iNnw1IGKxExAPY-JDRXOYKPiUwzsUgcf?usp=sharing)       | Notebook huấn luyện `PolicyNet` trên GPU (tương ứng `notebooks/03_Train_Model_Colab.ipynb`) |
| **Google Drive lưu Dataset**            | [Thư mục Dataset](https://drive.google.com/drive/folders/15My5r56Isg6slHyGRgtzqGGr4Z2GYHnq?usp=sharing)             | Dữ liệu self-play thô và các bộ tensor đã xử lý (`dataset-v1`, `v2`, `v5`)                  |
| **Google Drive lưu kết quả huấn luyện** | [Thư mục Kết quả thực nghiệm](https://drive.google.com/drive/folders/1yFZf5EoeQHelnZOZOK8w87Pio_AFnOSZ?usp=sharing) | Checkpoint `best.pt`, `last.pt`, `history.csv`, `run_summary.json` và log đánh giá          |

---

## 2. Giới thiệu đề tài

Đề tài xây dựng một nền tảng thực nghiệm Game AI khép kín cho trò chơi **Caro 11×11** (biến thể thắng với chuỗi từ 5 quân liên tiếp trở lên không bị chặn đồng thời ở cả hai đầu; biên bàn cờ được tính là một đầu bị chặn; hòa khi kín 121 ô).

Hệ thống bao gồm năm thành phần chính tách biệt theo kiến trúc phân tầng và nguyên lý **Single Responsibility Principle**:

1. **Lõi môi trường & luật chơi (`core/engine/`):** Quản lý bàn cờ 11×11, kiểm tra thắng cục bộ theo 4 hướng với độ phức tạp $O(n)$, xác thực nước đi nguyên tử và hỗ trợ sao chép/hoàn tác an toàn cho tìm kiếm cây.
2. **Năm nhóm tác tử AI (`core/agents/`):** `Random`, `Heuristic`, `Minimax` (Alpha-Beta Pruning + Move Ordering + Candidate Filtering + Iterative Deepening), `MCTS` (UCT + Progressive Widening + Epsilon-Heuristic Rollout) và `Policy Network` (ResNet 4 khối dư, 768.537 tham số).
3. **Chuỗi dữ liệu & học sâu (`core/ml/`, `scripts/`, `notebooks/`):** Sinh dữ liệu Self-play 2.000 ván giữa 3 tác tử giáo viên, phát lại kiểm chứng 100%, chia tập theo ván đấu (70/15/15), cô lập quỹ đạo đối xứng $D_4$ chống rò rỉ dữ liệu và huấn luyện với AdamW + Masked Cross-Entropy.
4. **Hạ tầng thực nghiệm & kiểm thử (`core/utils/`, `benchmarks/`, `tests/`):** Tổ chức giải đấu vòng tròn đổi bên X/O cân bằng theo seed ghép cặp, kiểm soát ngân sách tính toán và bộ kiểm thử hồi quy tự động (1.866 bài test vượt qua, 0 lỗi).
5. **Ứng dụng web minh họa (`ui/`):** Giao diện Streamlit hỗ trợ 3 chế độ chơi (**Human vs Human**, **Human vs AI**, **AI vs AI**), hiển thị độ trễ/số nút/số lượt mô phỏng theo từng nước và tô sáng chuỗi thắng.

---

## 3. Phân công thành viên & Quản lý GitHub

| Thành viên           | MSSV       | Phụ trách chính                                                                                                            | Đóng góp |
| -------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------- | -------- |
| **Trương Văn Thiện** | 3123410356 | Xây dựng lõi môi trường & luật Caro 11×11; cài đặt `Random`, `Heuristic`; phát triển giao diện Streamlit                   | 33,3%    |
| **Trần Hồ Minh Hải** | 3123410092 | Cài đặt và tối ưu `Minimax/Alpha-Beta`, `MCTS (UCT)`; thực hiện ablation study cho Alpha-Beta và MCTS                      | 33,3%    |
| **Lê Thị Trúc Ly**   | 3123410210 | Xây dựng pipeline dữ liệu Self-play, huấn luyện & đánh giá `Policy Network`; tổ chức giải đấu vòng tròn và tổng hợp chỉ số | 33,4%    |

### Quy trình làm việc và minh chứng đóng góp trên GitHub

Nhóm tuân thủ quy trình quản lý mã nguồn xuyên suốt thời gian thực hiện đồ án (chi tiết xem tại [`PhanCongVaQuyTacLamViec.md`](PhanCongVaQuyTacLamViec.md)):

- **Phân nhánh theo thành viên / tính năng (Branch & Pull Request):** Mỗi thành viên phát triển trên nhánh riêng (ví dụ `hai`, nhánh tính năng theo từng tuần/hạng mục), kiểm thử xanh trước khi gộp vào `main` qua Pull Request.
- **Lịch sử commit minh bạch:** Các commit được cập nhật đều đặn theo từng mốc tiến độ (Engine → Agents → Self-play & Dataset → Training → Evaluation & UI → Report), ghi rõ người thực hiện và nội dung thay đổi, không dồn mã nguồn vào sát ngày nộp.
- **Theo dõi đóng góp:** Giảng viên có thể đối chiếu trực tiếp tiến độ và đóng góp cá nhân tại mục **Commits**, **Branches**, **Pull Requests** và **Insights → Contributors** trên [GitHub Repository](https://github.com/minhhailtv6a1/Team_Project_TTNTNC_2025_2026).

---

## 4. Hướng dẫn thiết lập môi trường và chạy ứng dụng Streamlit

### Yêu cầu hệ thống

- **Hệ điều hành:** Windows 10/11 (hoặc macOS/Linux)
- **Python:** Python 3.13 (không bắt buộc GPU để chạy giao diện và suy luận trên CPU)

### Bước 1: Clone repository

```powershell
git clone https://github.com/minhhailtv6a1/Team_Project_TTNTNC_2025_2026.git
cd Team_Project_TTNTNC_2025_2026/Caro_AI_Project
```

### Bước 2: Tạo môi trường ảo và cài đặt thư viện

**Trên Windows (PowerShell):**

```powershell
py -3.13 -m venv myenv
.\myenv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Trên macOS / Linux:**

```bash
python3.13 -m venv myenv
source myenv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 3: Tải trọng số mô hình Policy v5 (để dùng chế độ Neural Network)

Tải tệp checkpoint `best.pt` của mô hình chính thức **Policy v5** từ [Thư mục Kết quả thực nghiệm trên Google Drive](https://drive.google.com/drive/folders/1yFZf5EoeQHelnZOZOK8w87Pio_AFnOSZ?usp=sharing) và đặt vào đường dẫn mặc định:

```text
models/checkpoints/model-v5-natural-teachers-run2/best.pt
```

_(Bạn cũng có thể lưu ở vị trí khác và nhập trực tiếp đường dẫn tệp `.pt` tại thanh Sidebar của ứng dụng Streamlit.)_

### Bước 4: Khởi chạy ứng dụng Streamlit

```powershell
# Trên Windows (khi đang kích hoạt venv hoặc gọi trực tiếp python trong myenv)
.\myenv\Scripts\python.exe -m streamlit run ui/app.py
```

Hoặc nếu đã kích hoạt môi trường ảo:

```bash
streamlit run ui/app.py
```

Mở trình duyệt tại địa chỉ **http://localhost:8501**. Nếu cổng `8501` đang bận, đổi sang cổng khác:

```powershell
.\myenv\Scripts\python.exe -m streamlit run ui/app.py --server.port 8502
```

---

## 5. Huấn luyện Policy Network v5 trên Google Colab & Chạy thực nghiệm

### 5.1 Huấn luyện mô hình Policy v5 trên Google Colab (khuyến nghị)

1. Mở trực tiếp notebook huấn luyện trên Google Colab:
   **[Google Colab — Train Policy v5](https://colab.research.google.com/drive/1iNnw1IGKxExAPY-JDRXOYKPiUwzsUgcf?usp=sharing)**
2. Chọn Runtime sử dụng GPU (**Runtime → Change runtime type → T4 GPU**).
3. Kết nối Google Drive chứa bộ dữ liệu từ [Thư mục Dataset](https://drive.google.com/drive/folders/15My5r56Isg6slHyGRgtzqGGr4Z2GYHnq?usp=sharing) và thư mục lưu checkpoint đầu ra tại [Thư mục Kết quả thực nghiệm](https://drive.google.com/drive/folders/1yFZf5EoeQHelnZOZOK8w87Pio_AFnOSZ?usp=sharing).
4. Chạy tuần tự các cell để huấn luyện mô hình `PolicyNet` (ResNet 4 khối, AdamW, `lr = 1e-3`, `batch_size = 256`, early stopping `patience = 5`) và xuất `best.pt`, `history.csv`, `run_summary.json`.

### 5.2 Chạy quy trình Self-play, xây dựng Dataset và huấn luyện cục bộ

```powershell
# 1. Sinh dữ liệu self-play
.\myenv\Scripts\python.exe scripts/generate_selfplay.py `
  --config configs/selfplay_w56.json `
  --output data/raw_logs/my_selfplay

# 2. Xây dựng bộ dữ liệu tensor (kiểm tra phát lại + loại trùng đối xứng D4)
.\myenv\Scripts\python.exe scripts/build_dataset.py `
  --input data/raw_logs/my_selfplay `
  --output data/processed_tensors/my_dataset `
  --config configs/train_w56.json

# 3. Huấn luyện Policy Network
.\myenv\Scripts\python.exe scripts/train_policy.py `
  --config configs/policy_train_v5_natural.json `
  --dataset data/processed_tensors/my_dataset `
  --output runs/my_policy `
  --device auto
```

### 5.3 Chạy bộ kiểm thử tự động và tái lập giải đấu

```powershell
# Chạy toàn bộ bộ kiểm thử (engine, luật, agents, data pipeline, UI)
.\myenv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider

# Tái lập giải đấu vòng tròn 5 tác tử
.\myenv\Scripts\python.exe scripts/run_tournament_w78.py `
  --results-dir results/w78-local `
  --checkpoint models/checkpoints/model-v5-natural-teachers-run2/best.pt

# Phân tích và tổng hợp số liệu
.\myenv\Scripts\python.exe scripts/analyze_results_w78.py `
  --results-dir results/w78-local `
  --profile ALL
```

---

## 6. Tóm tắt kết quả thực nghiệm chính

### 6.1 Giải đấu vòng tròn 5 tác tử (400 ván/tác tử, đổi bên X/O cân bằng)

| Tác tử                          | Thắng / Hòa / Thua | Score rate | Độ trễ trung bình / p95 (CPU) |
| ------------------------------- | -----------------: | ---------: | ----------------------------: |
| **MCTS (8 lượt có hướng dẫn)**  |      274 / 58 / 68 | **75,75%** |              30,79 / 50,24 ms |
| **Policy Network (v5)**         |      222 / 79 / 99 | **65,38%** |            **3,66 / 5,13 ms** |
| **Heuristic**                   |    168 / 115 / 117 |     56,38% |                0,47 / 0,75 ms |
| **Minimax (Alpha-Beta, d = 2)** |     178 / 64 / 158 |     52,50% |              37,20 / 66,48 ms |
| **Random**                      |        0 / 0 / 400 |      0,00% |                0,02 / 0,04 ms |

### 6.2 Các phát hiện định lượng nổi bật khác

- **Alpha-Beta Pruning & Move Ordering (RQ1):** Giữ nguyên 100% quyết định của Minimax, cắt giảm **89,07%–89,60%** số nút ở trung cuộc tại độ sâu 2 (tăng tốc 3,85–4,14 lần) và giảm tới **99,48%** số nút ở độ sâu 3 (từ 94.319 xuống 494 nút).
- **Policy v5 vs Policy v2 (RQ3):** Trên 1.998 ván đối đầu trực tiếp với ba giáo viên (`results/policy_v5_best_666.json`), Policy v5 đạt **53,38%** score rate (**+18,02 điểm %** so với Policy v2 ở mức 35,36%), đạt Test Top-1 **52,68%**, Test Top-3 **81,49%** và giải đúng **9/9** thế cờ chiến thuật bắt buộc.

---

## 7. Cấu trúc thư mục dự án

```text
Caro_AI_Project/
├── core/
│   ├── engine/         # Bàn cờ 11x11, luật thắng 4 hướng chặn hai đầu, môi trường CaroEnv
│   ├── agents/         # 5 tác tử: Random, Heuristic, Minimax, MCTS, NeuralAgent
│   ├── ml/             # Kiến trúc PolicyNet (ResNet) và pipeline dữ liệu đối xứng D4
│   └── utils/          # Tournament runner, kiểm soát ngân sách và ghi nhật ký
├── ui/                 # Ứng dụng web Streamlit và bộ điều khiển tương tác
├── notebooks/          # Notebook self-play, tiền xử lý, huấn luyện Colab, đánh giá & ablation
├── scripts/            # Kịch bản dòng lệnh sinh dữ liệu, huấn luyện, giải đấu và phân tích
├── benchmarks/         # Kịch bản đo độ trễ engine, Minimax, MCTS và đánh giá Policy
├── configs/            # Cấu hình thí nghiệm được quản lý phiên bản
├── tests/              # Bộ kiểm thử đơn vị, hợp đồng giao tiếp và tích hợp giao diện
├── results/            # Kết quả định lượng đối đầu Policy v2 / v5
├── docs/               # Tài liệu thiết kế, data card và kết quả ablation
├── output/reports/     # Báo cáo đồ án hoàn chỉnh
├── PhanCongVaQuyTacLamViec.md
├── requirements.txt
└── README.md
```
