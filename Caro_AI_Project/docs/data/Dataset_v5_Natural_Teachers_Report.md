# Dataset v5 — Clean D4, natural teachers

- Version: `dataset-v5-clean-d4-natural-teachers`
- Manifest SHA-256: `2515e17c3037a4c632ce96d8f95ee3b9197c939f18464d14cd8c22c8a266fc72`
- Train: 309.136 samples từ 38.642 state–action gốc.
- Validation: 4.806 samples; test: 4.689 samples.
- D4 overlap giữa mọi split: 0.

Train giữ toàn bộ dữ liệu sau dedup theo phân phối tự nhiên:

| Teacher | State gốc | Sau D4 | Tỷ lệ |
|---|---:|---:|---:|
| Heuristic | 9.589 | 76.712 | 24,82% |
| MCTS | 19.579 | 156.632 | 50,66% |
| Minimax | 9.474 | 75.792 | 24,52% |

Không outcome sampling và không downsample train. Validation/test vẫn cân bằng ba teacher để so sánh với baseline v3.

Artifact:

- ZIP: `data/processed_tensors/w56_dataset_v5_natural.zip`
- Dataset config: `configs/train_w56_v5_natural.json`
- Training config: `configs/policy_train_v5_natural.json`
- Colab notebook: `notebooks/03_Train_Model_Colab.ipynb`
- Drive output mặc định: `model-v5-natural-teachers`
