# Advanced Artificial Intelligence — Nhóm dự án 2025–2026

Kho mã nguồn và tài liệu thực hành cho học phần **Trí tuệ nhân tạo nâng cao** (*Advanced Artificial Intelligence*). Repository gồm năm lab theo các chủ đề nền tảng của AI và đồ án cuối kỳ xây dựng hệ thống chơi **Caro 11×11** với nhiều tác tử AI, dữ liệu self-play, huấn luyện mạng policy và giao diện web.

## Nội dung

| Thành phần | Chủ đề | Nội dung chính |
| --- | --- | --- |
| [`lab01 - Agent`](Team_Project_TTNTNC_2025_2026/lab01%20-%20Agent) | Intelligent Agents | Reflex agent, Robot Vacuum, Lunar Lander và Gridhunt đơn/đa tác tử. |
| [`lab02 - Searching`](Team_Project_TTNTNC_2025_2026/lab02%20-%20Searching) | Problem Solving by Search | Cây tìm kiếm; BFS, DFS, A*; trực quan hóa và so sánh lời giải mê cung. |
| [`lab03 - local search`](Team_Project_TTNTNC_2025_2026/lab03%20-%20local%20search) | Local Search | Hill Climbing, Simulated Annealing, N-Queens và Traveling Salesman Problem. |
| [`lab04 - csp`](Team_Project_TTNTNC_2025_2026/lab04%20-%20csp) | Constraint Satisfaction Problems | Tô màu đồ thị bằng backtracking và bài toán N-Queens dưới góc nhìn CSP. |
| [`lab05 - game`](Team_Project_TTNTNC_2025_2026/lab05%20-%20game) | Adversarial Search & Games | Tic-Tac-Toe và Connect 4 với AND-OR, Minimax, Alpha-Beta, Monte Carlo và MCTS. |
| [`Caro_AI_Project`](Team_Project_TTNTNC_2025_2026/Caro_AI_Project) | Đồ án môn học | Hệ thống Caro 11×11: game engine, AI cổ điển, MCTS, Neural Agent, self-play, training, tournament và Streamlit UI. |

## Cấu trúc thư mục

```text
Team_Project_TTNTNC_2025_2026/
├── lab01 - Agent/          # Intelligent Agents
├── lab02 - Searching/      # Search-based problem solving
├── lab03 - local search/   # Local-search algorithms
├── lab04 - csp/            # Constraint Satisfaction Problems
├── lab05 - game/           # Adversarial search and games
└── Caro_AI_Project/        # Đồ án Caro AI
```

Mỗi lab ưu tiên notebook Jupyter để minh họa, chạy thực nghiệm và ghi nhận kết quả. Tài liệu phân công, báo cáo và hình minh họa được lưu ngay trong thư mục tương ứng.

## Đồ án trọng tâm: Caro AI

`Caro_AI_Project` là một môi trường Caro 11×11 có luật thắng chuỗi 5 quân (xét luật chặn hai đầu), với quy trình từ luật chơi đến đánh giá mô hình:

```text
Game engine → AI/self-play → dữ liệu JSONL → tensor dataset
                                      ↓
                         Policy network (PyTorch)
                                      ↓
                tournament tái lập được / Streamlit UI
```

Các tác tử hiện có:

- `RandomAgent`: baseline chọn nước đi hợp lệ.
- `HeuristicAgent`: đánh giá các mẫu hình tấn công và phòng thủ.
- `MinimaxAgent`: Minimax có Alpha-Beta pruning và sắp thứ tự nước đi.
- `MCTSAgent`: Monte Carlo Tree Search với tactical pre-check và progressive widening.
- `NeuralAgent`: suy luận policy network PyTorch với legal-action mask.

Theo giải đấu W78 được ghi nhận trong dự án, MCTS đạt score rate cao nhất (75,75% trên 400 ván), tiếp theo là NeuralAgent (65,38%); kết quả phụ thuộc checkpoint, seed và budget đã công bố. Xem chi tiết tại [README của đồ án](Team_Project_TTNTNC_2025_2026/Caro_AI_Project/README.md).

## Yêu cầu môi trường

- Python 3.10 trở lên; phần Caro AI đã được kiểm thử với Python 3.13 trên Windows.
- JupyterLab để mở và thực thi notebook.
- Dùng môi trường ảo riêng cho từng phần nếu cài cả lab và đồ án, vì bộ phụ thuộc có thể khác nhau.

Ví dụ tạo môi trường cho đồ án Caro:

```powershell
cd Team_Project_TTNTNC_2025_2026\Caro_AI_Project
py -3.13 -m venv myenv
.\myenv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Đối với Lab 04, cài các gói được liệt kê trong `lab04 - csp/requirements.txt`. Lab 05 cần các gói `numpy`, `pandas`, `matplotlib`, `jupyter`, `nbconvert`, `ipykernel` và `pytest`; chi tiết chạy lại notebook và test có trong [README Lab 05](Team_Project_TTNTNC_2025_2026/lab05%20-%20game/README.md).

## Chạy nhanh

### Mở notebook lab

```powershell
cd Team_Project_TTNTNC_2025_2026
jupyter lab
```

Sau đó mở notebook mong muốn trong các thư mục `lab01` đến `lab05`.

### Chạy giao diện Caro AI

```powershell
cd Team_Project_TTNTNC_2025_2026\Caro_AI_Project
python -m streamlit run ui/app.py
```

Truy cập `http://localhost:8501`. Chế độ `NeuralAgent` yêu cầu checkpoint tương thích, mặc định tại `models/checkpoints/model-v5-natural-teachers-run2/best.pt`; checkpoint có thể không được đưa vào repository.

### Chạy kiểm thử

```powershell
# Lab 05: các module Connect 4
cd "Team_Project_TTNTNC_2025_2026\lab05 - game"
python -m pytest tests -v

# Đồ án Caro AI
cd ..\Caro_AI_Project
python -m pytest tests -q -p no:cacheprovider
```

## Tài liệu và kết quả

- Lab 05 có báo cáo tổng hợp tại [`BAO_CAO_KET_QUA.md`](Team_Project_TTNTNC_2025_2026/lab05%20-%20game/BAO_CAO_KET_QUA.md), các kết quả thực nghiệm theo thành viên trong `results/`, và test cho Connect 4.
- Đồ án Caro có contract luật chơi, data card, báo cáo training, đánh giá policy và ablation trong [`docs/`](Team_Project_TTNTNC_2025_2026/Caro_AI_Project/docs).
- Cấu hình thực nghiệm của Caro (self-play, train, tournament và ablation) được version hóa trong [`configs/`](Team_Project_TTNTNC_2025_2026/Caro_AI_Project/configs).

## Thành viên

- Trần Hồ Minh Hải — UI, API, MCTS và mạng học sâu.
- Lê Thị Trúc Ly — game engine, luật chơi, heuristic và Minimax.
- Trương Văn Thiện — môi trường, dữ liệu self-play và thực nghiệm/tournament.

Phân công và quy tắc cộng tác chi tiết: [`PhanCongVaQuyTacLamViec.md`](Team_Project_TTNTNC_2025_2026/Caro_AI_Project/PhanCongVaQuyTacLamViec.md).

## Lưu ý

- Các notebook có thể tạo cache, video, log, tensor dataset hoặc checkpoint lớn; các artefact này thường không được commit.
- Để tái lập kết quả, dùng đúng cấu hình, seed, version phụ thuộc và checkpoint được nêu trong tài liệu của từng phần.
- Đây là repository phục vụ học tập và thực nghiệm; số liệu benchmark không là tuyên bố về tính tối ưu tổng quát của các thuật toán.
