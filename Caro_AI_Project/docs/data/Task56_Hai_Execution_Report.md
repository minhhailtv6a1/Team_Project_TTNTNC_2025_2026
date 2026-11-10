# Báo cáo thực thi Task 5–6 — Trần Hồ Minh Hải

**Ngày kiểm tra:** 2026-11-10  
**Task:** `W56-M1-01 — PolicyNet, huấn luyện và NeuralAgent`  
**Contract:** `caro-v2`, bàn cờ `11 x 11`, action public `(row, col)`

## 1. Phạm vi đã thực hiện

Báo cáo này chỉ thực hiện phần M1 — Hải trong kế hoạch Tuần 5–6:

- PolicyNet, legal-action masking và masked cross-entropy.
- Train/validation/test workflow, checkpoint và resume.
- NeuralAgent/PolicyAgent dùng checkpoint đã huấn luyện.
- Notebook 03 và các kiểm thử thuộc M1.
- Cấu hình riêng cho policy training và báo cáo kết quả.

Không thay đổi `core/ml/data_pipeline.py`, self-play generator, MCTS/Minimax/Heuristic, tournament runner hay các test thuộc M2/M3. Hai thay đổi có sẵn từ trước ở `core/agents/search_utils.py` và `docs/data/Dataset_v2_MCTS_Strength8_Report.md` được giữ nguyên, không chỉnh sửa trong task này.

## 2. Kết quả Task 5 — Encoder contract và PolicyNet

### 2.1. Kiến trúc

`core/ml/architectures.py` hiện cung cấp:

- `PolicyNetConfig` có `architecture_version`, board size, input channels, trunk channels, số residual block, policy channels và dropout.
- `PolicyNet` nhận tensor `[N, 3, 11, 11]` và trả đúng `121` raw logits; không đặt softmax trong `forward()`.
- Kiểm tra shape và floating-point dtype ở public boundary.
- `mask_policy_logits()` loại action bất hợp lệ trước softmax/argmax.
- `masked_policy_loss()` từ chối target ngoài miền hoặc target bất hợp lệ.
- Forward/backward CPU cho loss và gradient hữu hạn.
- State-dict round trip giữ nguyên logits ở eval mode.

Encoder ba channel không được viết lại trong task M1. Cả train và inference dùng API canonical `core.ml.data_pipeline.encode_policy_state()`:

1. Quân của current player.
2. Quân đối thủ.
3. Legal/empty plane.

### 2.2. Kiểm thử Task 5

`tests/test_architectures.py` kiểm tra:

- Batch size 1 và batch nhiều mẫu.
- Shape/dtype và dữ liệu đầu vào sai.
- Illegal probability bằng 0 sau mask.
- Empty legal set, mask sai dtype/shape và illegal target.
- Loss/gradient hữu hạn.
- Save/load state dict và model config version.

## 3. Kết quả Task 6 — Train, checkpoint và NeuralAgent

### 3.1. Training workflow

`scripts/train_policy.py` đã hỗ trợ:

- CLI: config, dataset, output, device, seed, epoch, giới hạn batch, smoke và resume.
- Seed Python, NumPy, PyTorch và deterministic algorithms; CPU là baseline tái lập.
- DataLoader train/val/test; chỉ train được shuffle.
- Masked cross-entropy, top-1/top-3 legal accuracy, learning rate và epoch time.
- TensorBoard, `history.csv`, `history.json` và `run_summary.json`.
- Early stopping chỉ theo validation loss.
- `best.pt` và `last.pt` được ghi nguyên tử.
- Checkpoint chứa contract, architecture/model config, state dict, optimizer state, dataset version/checksum, seed, epoch, metric, history và RNG state.
- Resume tiếp tục đúng epoch, optimizer và RNG; từ chối sai run id, contract, model config, dataset version/checksum, seed hoặc training config.
- Test split chỉ được mở sau khi validation đã chọn và đóng băng `best.pt`.

### 3.2. NeuralAgent

`core/agents/neural_ai.py` đã hỗ trợ:

- Load checkpoint bằng CPU mặc định và kiểm tra schema/contract/dataset/model.
- Dùng encoder canonical theo góc nhìn current player.
- Mask logits trước argmax; cùng state/checkpoint cho cùng action.
- Trả `AgentDecision` hợp lệ, không mutation environment.
- Terminal/no-legal guard bằng `RuntimeError`.
- `NeuralAgent`, alias `PolicyAgent` và factory `load_policy_agent()` cho runner.

### 3.3. Notebook

`notebooks/03_Train_Model.ipynb` gồm sáu cell canonical:

- Khai báo run id/config/dataset/output.
- Kiểm tra dataset version và manifest checksum.
- Load mini-batch từ public loader, forward/backward và kiểm tra gradient.
- Gọi `scripts/train_policy.py`, không copy train loop vào notebook.
- Đọc history, vẽ learning curve và trình bày best/test metrics.

Các cell đã được chạy tuần tự bằng Python project interpreter và hoàn tất. Notebook cũng đã chạy end-to-end bằng `nbconvert --execute` sau khi đặt Jupyter runtime trong workspace và ưu tiên `myenv/Scripts` cho kernel. Artifact thực thi được lưu cục bộ tại `models/checkpoints/model-v2-mcts-strength8/model-v2-notebook-smoke.ipynb` và được `.gitignore` loại trừ.

## 4. Dữ liệu sử dụng

| Thuộc tính | Giá trị |
|---|---:|
| Dataset version | `dataset-v2-three-agents-mcts-strength8-2000` |
| Manifest SHA-256 | `3818eac33d0757bf29d47fabe690bbdae06944d5548cd6b0979a941274e0aaef` |
| Train games | 1.400 |
| Validation games | 300 |
| Test games | 300 |
| Train samples sau export | 227.376 |
| Validation samples | 5.409 |
| Test samples | 5.139 |

Task M1 chỉ đọc các artifact trên qua public loader; không thay đổi dataset hoặc manifest của M3.

## 5. Kết quả chạy thực tế

### 5.1. Unit/integration test M1

Lệnh:

```powershell
.\myenv\Scripts\python.exe -m pytest `
  tests/test_architectures.py `
  tests/test_neural_ai.py `
  tests/test_policy_training.py `
  -q -p no:cacheprovider
```

Kết quả: **22 passed**.

Coverage:

| Module | Statement coverage |
|---|---:|
| `core/agents/neural_ai.py` | 92% |
| `core/ml/architectures.py` | 89% |
| `scripts/train_policy.py` | 88% |
| **Tổng M1** | **89%** |

Coverage vượt cổng đề xuất 85%. Bộ test bao gồm cả early stopping theo validation loss và resume checkpoint.

### 5.2. Full regression

Kết quả toàn repository:

- **1.787 passed**.
- **2 skipped**.
- **0 assertion failure**.
- **16 setup error** do `PermissionError [WinError 5]` tại `C:\Users\LOQ\AppData\Local\Temp\pytest-of-LOQ` khi các test cũ xin fixture `tmp_path`.

Các setup error xuất hiện trước khi test body chạy và cùng nguyên nhân ACL đã được ghi nhận trong baseline kế hoạch Tuần 5–6. Không phát hiện regression hành vi từ phần M1.

### 5.3. Smoke training trên dataset thật

Lệnh:

```powershell
.\myenv\Scripts\python.exe scripts/train_policy.py `
  --config configs/policy_train_v2_mcts_strength.json `
  --dataset data/processed_tensors/w56_dataset_v2_mcts_strength8_2000_balanced `
  --output models/checkpoints/model-v2-mcts-strength8 `
  --device cpu `
  --smoke
```

Kết quả thực tế:

| Metric | Giá trị |
|---|---:|
| Device | CPU |
| Seed | 20261109 |
| Số tham số | 768.537 |
| Epoch | 1 smoke epoch |
| Train samples đã đọc | 512 |
| Validation samples đã đọc | 512 |
| Test samples đã đọc | 512 |
| Train loss | 4,218260 |
| Train top-1 / top-3 | 4,492% / 9,570% |
| Validation loss | 4,029634 |
| Validation top-1 / top-3 | 3,906% / 11,719% |
| Test loss | 4,105752 |
| Test top-1 / top-3 | 5,859% / 12,695% |
| Training/evaluation elapsed | 8,687 giây |

Đây là smoke run hai batch cho mỗi split nhằm kiểm tra toàn pipeline, không phải production metric và không được dùng để kết luận sức mạnh agent.

Artifact local đã tạo, đều nằm trong vùng `.gitignore`:

- `models/checkpoints/model-v2-mcts-strength8/best.pt`
- `models/checkpoints/model-v2-mcts-strength8/last.pt`
- `models/checkpoints/model-v2-mcts-strength8/history.csv`
- `models/checkpoints/model-v2-mcts-strength8/history.json`
- `models/checkpoints/model-v2-mcts-strength8/run_summary.json`
- `models/checkpoints/model-v2-mcts-strength8/tensorboard/`

### 5.4. Agent/runner integration bằng checkpoint thật

- Opening action: `(7, 5)`.
- Action thuộc `env.legal_actions()`: đạt.
- Snapshot environment trước/sau inference: không đổi.
- NeuralAgent vs Random qua `TournamentRunner`: terminal sau 59 ply.
- Winner: X.
- Budget/runner violation: 0.

Đây chỉ là smoke integration một ván, không phải đánh giá tỷ lệ thắng.

## 6. Trạng thái nghiệm thu

| Tiêu chí M1 | Trạng thái |
|---|---|
| Encoder ba channel đúng current-player perspective | Đạt qua canonical encoder/test M3 |
| PolicyNet xuất 121 logits | Đạt |
| Mask/loss từ chối illegal action/target | Đạt |
| Forward/backward CPU | Đạt |
| Train loop seed/val/early stop/history | Đạt |
| Best/last checkpoint đủ metadata | Đạt |
| Resume và compatibility guard | Đạt |
| NeuralAgent legal/deterministic/no-mutation/terminal guard | Đạt |
| NeuralAgent chạy qua runner | Đạt |
| Notebook 03 gọi code canonical và chạy end-to-end | Đạt |
| Statement coverage tối thiểu 85% | Đạt, tổng 89% |
| Production train đầy đủ trên 227.376 mẫu/epoch | **Chưa chạy** |

## 7. Giới hạn và lệnh production

Máy hiện tại không có CUDA. Smoke profile đo khoảng 512 train samples trong 7,23 giây với model 768.537 tham số; production 30 epoch trên 227.376 train samples là tác vụ nhiều giờ trên CPU. Vì vậy báo cáo không giả lập hoặc gắn nhãn smoke checkpoint thành production model.

Lệnh production đã sẵn sàng:

```powershell
.\myenv\Scripts\python.exe scripts/train_policy.py `
  --config configs/policy_train_v2_mcts_strength.json `
  --dataset data/processed_tensors/w56_dataset_v2_mcts_strength8_2000_balanced `
  --output models/checkpoints/model-v2-mcts-strength8-production `
  --device cpu
```

Nếu dừng giữa chừng, tiếp tục bằng:

```powershell
.\myenv\Scripts\python.exe scripts/train_policy.py `
  --config configs/policy_train_v2_mcts_strength.json `
  --dataset data/processed_tensors/w56_dataset_v2_mcts_strength8_2000_balanced `
  --output models/checkpoints/model-v2-mcts-strength8-production `
  --device cpu `
  --resume models/checkpoints/model-v2-mcts-strength8-production/last.pt
```

## 8. Kết luận

Phần code, test, notebook và smoke integration thuộc Task 5–6 của Hải đã được triển khai và kiểm tra đúng phạm vi. Pipeline đã sẵn sàng để chạy production và NeuralAgent đã sử dụng được checkpoint thật. Điều kiện còn lại để gắn nhãn `model-v1/model-v2 production` là hoàn tất production training trên toàn bộ dataset và lưu best epoch/metrics cuối; smoke checkpoint hiện tại không được xem là production model.
