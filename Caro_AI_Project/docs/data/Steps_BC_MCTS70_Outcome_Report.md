# Báo cáo bước B+C — MCTS70 và outcome-weighted sampling

**Dataset:** `dataset-v4-clean-d4-mcts70-outcome-weighted`  
**Manifest SHA-256:** `3f927d0f301a107ee8e44948c35e143940eb3e54b5f49faa9e15d8ad69e8d868`

## Phạm vi

- Giữ clean-D4 split của bước A.
- Giữ nguyên PolicyNet và hyperparameter baseline.
- B: train source ratio MCTS/Minimax/Heuristic = 70/20/10.
- C: weighted sampling trong từng teacher theo thắng/hòa/thua = 1,0/0,5/0,25.
- Validation/test vẫn cân bằng ba teacher 1:1:1 để so sánh với bước A.

## Kết quả build

| Split | Samples |
|---|---:|
| Train | 223.760 |
| Validation | 4.806 |
| Test | 4.689 |

Train trước D4 có 27.970 state–action:

| Teacher | Trước sampling | Sau sampling | Tỷ lệ sau |
|---|---:|---:|---:|
| Heuristic | 9.589 | 2.797 | 10% |
| MCTS | 19.579 | 19.579 | 70% |
| Minimax | 9.474 | 5.594 | 20% |

Toàn bộ mẫu MCTS độc nhất được giữ lại thay vì downsample còn 9.474 như dataset v3.

| Outcome | Trước sampling | Sau sampling | Tỷ lệ sau |
|---|---:|---:|---:|
| Thắng | 11.741 | 11.261 | 40,26% |
| Hòa | 15.764 | 11.832 | 42,30% |
| Thua | 11.137 | 4.877 | 17,44% |

Weighted sampling giảm tỷ lệ nhãn từ bên thua từ 28,82% xuống 17,44% và tăng tỷ lệ nhãn bên thắng từ 30,38% lên 40,26%.

## Artifact Colab

- Dataset folder: `data/processed_tensors/w56_dataset_v4_bc`.
- Upload ZIP: `data/processed_tensors/w56_dataset_v4_bc.zip`.
- Dataset config: `configs/train_w56_v4_bc.json`.
- Training config: `configs/policy_train_v4_bc.json`.
- Notebook: `notebooks/03_Train_Model_Colab.ipynb`.
- Drive output mặc định: `model-v4-bc-mcts70-outcome`.

Upload folder hoặc ZIP v4 lên Drive, dán link vào `DATASET_DRIVE_URL`, giữ `FORCE_DATASET_REDOWNLOAD=True` cho lần tải đầu và chạy toàn bộ cell. Không chạy train local trong bước này.

## Tiêu chí đánh giá sau train

So với baseline v3 sạch:

- Test top-1 tham chiếu: 51,50%.
- Test top-3 tham chiếu: 81,21%.
- Best epoch tham chiếu: 4.

Mục tiêu chính của B+C là sức mạnh thi đấu tốt hơn nhờ học nhiều hơn từ MCTS và bên thắng. Offline accuracy trên validation/test cân bằng có thể không tăng tương ứng; chưa chạy tournament 666 cho đến khi hoàn tất các bước cải thiện model đã chọn.

## Kết quả production run

Run `policy-v4-bc-mcts70-outcome-colab` early-stop sau 8 epoch, best tại epoch 3:

| Metric | v3 clean baseline | v4 B+C | Chênh lệch |
|---|---:|---:|---:|
| Test loss | 1,5211 | 1,5654 | +0,0443 |
| Test top-1 | 51,50% | 48,30% | -3,20 điểm % |
| Test top-3 | 81,21% | 78,78% | -2,43 điểm % |
| Best epoch | 4 | 3 | -1 |

### Kết luận

B+C là **ablation âm trên held-out set cân bằng** và checkpoint v4 không được chọn làm model kế tiếp.

Hai thay đổi bị trộn trong cùng run nên chưa thể quy toàn bộ suy giảm cho riêng B hoặc C. Tuy nhiên:

- Train 70/20/10 lệch mạnh so với validation/test 1:1:1, nên accuracy tổng hợp giảm là có thể dự đoán.
- Outcome của cả ván là tín hiệu quá thô cho từng nước đi; loại bớt sample bên thua cũng loại nhiều trạng thái phòng thủ và recovery khó.
- MCTS strength-8 có policy ngẫu nhiên/noisy hơn hai teacher deterministic; tăng tỷ trọng MCTS làm mục tiêu one-hot khó bắt chước hơn.

Hướng tiếp theo hợp lý là bỏ outcome sampling và giữ toàn bộ dữ liệu sau dedup theo phân phối tự nhiên: khoảng 50,7% MCTS, 24,8% Heuristic và 24,5% Minimax. Cách này không bỏ hơn 10 nghìn mẫu MCTS như v3, đồng thời không loại state Heuristic/Minimax hoặc state từ bên thua như v4.
