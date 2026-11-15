# Caro AI Project

Đồ án **Trí tuệ nhân tạo nâng cao** về Caro 11×11. Dự án xây dựng môi trường chơi cờ chuẩn, các tác tử AI, pipeline dữ liệu self-play, huấn luyện policy network, giải đấu tái lập được và giao diện Streamlit.

## Tổng quan

- Engine theo contract `caro-v2`: luật chơi, clone/undo, history và trạng thái terminal.
- Năm tác tử: Random, Heuristic, Minimax/Alpha-Beta, MCTS và NeuralAgent.
- Pipeline: self-play → replay validation → tensor dataset → policy training.
- Tournament runner có seed, đổi bên X/O, giới hạn budget và log JSONL.
- UI Streamlit: Human vs Human, Human vs AI và AI vs AI.

## Luật chơi và bàn cờ

Hệ thống hiện chỉ hỗ trợ bàn **11×11**. X đi trước, O đi sau. Action công khai có dạng `(row, col)`, với tọa độ gốc 0 ở góc trên trái. Ô bàn cờ được biểu diễn bằng `X = 1`, `O = -1`, `EMPTY = 0`.

Một chuỗi liên tiếp từ 5 quân trở lên theo ngang, dọc, chéo chính hoặc chéo phụ là ứng viên thắng. Chuỗi không thắng nếu **cả hai đầu** bị chặn bởi quân đối phương hoặc biên; overline vẫn thắng nếu không bị chặn cả hai đầu. Ván hòa khi bàn đầy mà chưa có người thắng.

`CaroEnv` là nguồn chân lý của luật. Agent chỉ đọc snapshot `GameState`, trả về nước đi qua `choose_action(env, budget)` và không được thay đổi môi trường trong lúc tìm kiếm.

## Các thuật toán

| Agent            | Mô tả                                                                                                  |
| ---------------- | ------------------------------------------------------------------------------------------------------ |
| `RandomAgent`    | Chọn nước hợp lệ theo seed; baseline.                                                                  |
| `HeuristicAgent` | Chấm điểm mẫu hình tấn công/phòng thủ.                                                                 |
| `MinimaxAgent`   | Minimax giới hạn độ sâu; W78 dùng Alpha-Beta, move ordering, depth 2 và lọc nước lân cận.              |
| `MCTSAgent`      | Selection, expansion, rollout, backpropagation; có tactical pre-check và progressive widening.         |
| `NeuralAgent`    | Suy luận policy PyTorch từ checkpoint, dùng ba kênh `[current_player, opponent, legal]` và legal mask. |

## Cấu trúc dự án

```text
core/
├── engine/       # Board, CaroEnv, interfaces, RuleEngine
├── agents/       # Các tác tử AI và tiện ích tìm kiếm
├── ml/           # Kiến trúc mạng và pipeline dữ liệu
└── utils/        # Logger JSONL và tournament runner
ui/               # Streamlit UI và human controller
scripts/          # Self-play, build dataset, train, tournament, phân tích
configs/          # Cấu hình version hóa
tests/            # Unit, contract, integration và tournament tests
results/w78/      # Log và kết quả giải đấu W78
docs/             # Contract, data card và báo cáo kỹ thuật
```

## Kết quả W78

Giải đấu chính gồm năm agent, 100 ván mỗi cặp, đổi bên X/O. Mỗi profile `DEFAULT` và `FAIR` hoàn tất 1.000 ván; tổng cộng 2.000 ván và 0 budget violation. `FAIR` áp 150 ms mỗi nước, còn `DEFAULT` giữ budget frozen của từng agent.

Score rate:

$$
\text{Score rate} = \frac{\text{thắng} + 0{,}5 \times \text{hòa}}{\text{tổng số ván}}
$$

| Agent           | W / D / L trên 400 ván | Score rate | Mean / p95 mỗi nước |
| --------------- | ---------------------- | ---------- | ------------------- |
| MCTS            | 274 / 58 / 68          | 75,75%     | 30,79 / 50,24 ms    |
| NeuralAgent     | 222 / 79 / 99          | 65,38%     | 3,66 / 5,13 ms      |
| Heuristic       | 168 / 115 / 117        | 56,38%     | 0,47 / 0,75 ms      |
| Minimax depth 2 | 178 / 64 / 158         | 52,50%     | 37,20 / 66,48 ms    |
| Random          | 0 / 0 / 400            | 0,00%      | 0,02 / 0,04 ms      |

MCTS có score cao nhất trong cấu hình W78. NeuralAgent đứng thứ hai và có độ trễ suy luận thấp hơn rõ rệt. Xem ma trận đối đầu, tách theo X/O và khoảng tin cậy Wilson tại [`results/w78/summary.md`](results/w78/summary.md).

> **Lưu ý:** Khoảng tin cậy cần được đọc thận trọng: một số agent xác định có thể lặp cùng quỹ đạo khi dùng paired seed.

## Cài đặt

Yêu cầu: Windows 10/11, Python 3.13; GPU không bắt buộc.

```powershell
py -3.13 --version
py -3.13 -m venv myenv
.\myenv\Scripts\python.exe -m pip install --upgrade pip
.\myenv\Scripts\python.exe -m pip install -r requirements.txt
```

## Chạy ứng dụng

```powershell
.\myenv\Scripts\python.exe -m streamlit run ui/app.py
```

Mở <http://localhost:8501>. Nếu port này bận:

```powershell
.\myenv\Scripts\python.exe -m streamlit run ui/app.py --server.port 8502
```

UI đã nối với Random, Heuristic, Minimax, MCTS và NeuralAgent. NeuralAgent cần checkpoint tương thích; đường dẫn mặc định là:

```text
models/checkpoints/model-v5-natural-teachers-run2/best.pt
```

## Chạy kiểm thử

```powershell
.\myenv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

Suite kiểm tra engine, luật, action invalid, clone/undo, tác tử, pipeline dữ liệu, tournament runner và UI.

## Tái lập giải đấu W78

Checkpoint NeuralAgent có thể không được commit cùng mã nguồn. Cung cấp checkpoint hợp lệ và dùng thư mục output mới:

```powershell
.\myenv\Scripts\python.exe scripts/run_tournament_w78.py `
  --results-dir results/w78-local `
  --checkpoint <duong-dan-den-best.pt>
```

Phân tích log JSONL:

```powershell
.\myenv\Scripts\python.exe scripts/analyze_results_w78.py `
  --results-dir results/w78-local `
  --profile ALL
```

Có thể chạy riêng profile mặc định bằng cách thay bằng `--profile DEFAULT`.

## Self-play, dataset và huấn luyện

```powershell
# 1. Sinh dữ liệu self-play
.\myenv\Scripts\python.exe scripts/generate_selfplay.py `
  --config configs/selfplay_w56.json `
  --output data/raw_logs/my_selfplay

# 2. Xây dựng dataset tensor
.\myenv\Scripts\python.exe scripts/build_dataset.py `
  --input data/raw_logs/my_selfplay `
  --output data/processed_tensors/my_dataset `
  --config configs/train_w56.json

# 3. Huấn luyện policy network
.\myenv\Scripts\python.exe scripts/train_policy.py `
  --config configs/policy_train_v5_natural.json `
  --dataset data/processed_tensors/my_dataset `
  --output runs/my_policy `
  --device auto
```

Pipeline replay raw game, chia split theo ván trước augmentation, kiểm tra checksum và loại trùng lặp xuyên split. Không nên sửa trực tiếp JSONL hoặc tensor sau khi manifest được tạo.

## Tài liệu trong repository

- [`docs/contract/docs_contracts_caro_v2.md`](docs/contract/docs_contracts_caro_v2.md): contract và luật chơi.
- [`docs/data/Dataset_v5_Natural_Teachers_Report.md`](docs/data/Dataset_v5_Natural_Teachers_Report.md): self-play 2.000 ván và dataset-v2.
- [`docs/data/Policy_v5_Best_666_Evaluation_Report.md`](docs/data/Policy_v5_Best_666_Evaluation_Report.md): đánh giá policy v5.
- [`docs/report/assets/Ket_qua_Ablation_W78.md`](docs/report/assets/Ket_qua_Ablation_W78.md): ablation Alpha-Beta và MCTS.

## Giới hạn

- Chỉ bàn 11×11 được hỗ trợ chính thức.
- Kết quả phụ thuộc checkpoint, seed, budget và cấu hình công bố; không phải chứng minh tính tối ưu hoặc khả năng áp dụng sang trò chơi khác.
- NeuralAgent cần checkpoint tương thích ở máy chạy.
