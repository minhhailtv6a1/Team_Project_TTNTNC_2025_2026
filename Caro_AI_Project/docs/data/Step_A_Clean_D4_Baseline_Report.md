# Báo cáo bước A — Clean D4 split baseline

**Ngày thực hiện:** 2026-11-10  
**Phạm vi:** làm sạch split theo D4, giữ nguyên teacher balance, model và hyperparameter v2  
**Trạng thái train:** production run trên Colab đã hoàn tất

## 1. Kết quả thực hiện

Bước A đã hoàn thành phần pipeline và dataset:

- Mỗi state orbit gồm trạng thái gốc và 7 phép xoay/lật D4 chỉ được thuộc một split.
- Giữ nguyên game split 1.400 train, 300 validation và 300 test.
- Giữ nguyên cân bằng ba teacher 1:1:1.
- Giữ nguyên D4 augmentation cho train.
- Giữ nguyên PolicyNet 768.537 tham số và toàn bộ hyperparameter của run v2.
- Đã xác minh độc lập không còn D4 state orbit giao nhau giữa bất kỳ hai split nào.

| Kiểm tra giao split | Dataset v2 | Dataset v3 clean-D4 |
|---|---:|---:|
| Train–validation, exact state–target | 449 | 0 |
| Train–test, exact state–target | 344 | 0 |
| Train–validation, D4 state orbit | Có | 0 |
| Train–test, D4 state orbit | Có | 0 |
| Validation–test, D4 state orbit | Có | 0 |

## 2. Cơ chế isolation

Pipeline tạo hash canonical không chứa target cho toàn bộ 8 biến thể D4 của một encoded state. Ownership được xét theo thứ tự:

1. Train.
2. Validation.
3. Test.

Nếu một game ở split sau đi qua state đối xứng với state đã có ở split trước, sample ở split sau bị purge. Các target khác nhau của nhiều teacher trong cùng split vẫn được giữ; bước A không thay đổi chính sách nhãn.

Cơ chế chỉ bật khi config có:

```json
"d4_split_isolation": true
```

Dataset/config v2 cũ không bị đổi hành vi ngầm.

## 3. Dataset v3

**Version:** `dataset-v3-three-agents-mcts-strength8-2000-clean-d4`  
**Manifest SHA-256:** `77ffbd5473c328b4452438481624aca8217693658fda0ca3d9e1ec57e3458976`

| Split | Games | Mẫu v2 | Mẫu v3 | Heuristic | MCTS | Minimax |
|---|---:|---:|---:|---:|---:|---:|
| Train | 1.400 | 227.376 | 227.376 | 75.792 | 75.792 | 75.792 |
| Validation | 300 | 5.409 | 4.806 | 1.602 | 1.602 | 1.602 |
| Test | 300 | 5.139 | 4.689 | 1.563 | 1.563 | 1.563 |

Purge trước bước balance đã loại:

- Train: 0 sample.
- Validation: 930 sample.
- Test: 790 sample.

Sau khi balance, validation giảm 603 mẫu và test giảm 450 mẫu so với v2. Train được giữ nguyên nên thí nghiệm A chỉ thay đổi độ sạch của held-out evaluation.

Kiểm tra canonical orbit độc lập trên các file NPZ đã export:

```text
train-val: 0 shared D4 state orbits
train-test: 0 shared D4 state orbits
val-test: 0 shared D4 state orbits
```

## 4. Baseline giữ nguyên

| Thuộc tính | Giá trị |
|---|---:|
| Channels | 64 |
| Residual blocks | 4 |
| Policy channels | 32 |
| Dropout | 0,1 |
| Batch size | 256 |
| Learning rate | 0,001 |
| Weight decay | 0,0001 |
| Max epochs | 30 |
| Early stopping patience | 5 |
| Seed | 20261109 |

Không áp dụng scheduler, label smoothing, teacher weighting, outcome weighting hoặc kiến trúc head mới ở bước A.

## 5. Artifact dùng trên Colab

### Dataset upload

File:

`data/processed_tensors/w56_dataset_v3_mcts_strength8_2000_clean_split.zip`

- Kích thước: 17.634.098 bytes.
- ZIP SHA-256: `74a391c90b357350a85ffba7c4fed8bdf66f47434d1b91a4155d4660ed3d4fd9`.
- ZIP chứa đúng một `dataset_manifest.json`.

### Notebook

`notebooks/03_Train_Model_Colab.ipynb`

Notebook đã được cấu hình:

- Expected dataset version và manifest checksum cố định theo dataset v3.
- Kiểm tra `d4_split_isolation=true` và overlap bằng 0 trước train.
- Output Drive riêng: `/content/drive/MyDrive/Caro_AI_Project/policy_runs/model-v3-clean-d4-baseline`.
- Run ID riêng: `policy-v3-clean-d4-baseline-colab`.
- Các module từ load dataset đến train chạy standalone, không phụ thuộc package local.
- Dataset cache được khóa theo SHA-256 của Drive URL và hỗ trợ `FORCE_DATASET_REDOWNLOAD`; thay link không còn âm thầm dùng lại manifest cũ.

### Cách chạy

1. Upload file ZIP dataset lên Google Drive.
2. Bật `Anyone with the link — Viewer` và copy link.
3. Mở notebook trên Colab, chọn GPU runtime.
4. Dán link vào `DATASET_DRIVE_URL` ở module **1. User configuration**.
5. Chạy lần lượt toàn bộ cell.

Notebook sẽ lưu `best.pt`, `last.pt`, history, TensorBoard, config và summary vào output Drive mới. Nếu link trỏ nhầm dataset v2, module validation sẽ dừng trước khi train.

### Xử lý cache dataset cũ

Phiên bản notebook trước đây bỏ qua download nếu thư mục `/content` đã có một manifest. Điều này có thể làm link v3 vẫn đọc lại manifest v2 từ cache. Notebook hiện đặt `FORCE_DATASET_REDOWNLOAD = True`, xóa đúng thư mục cache được khóa theo URL rồi tải lại. Sau khi đã tải đúng một lần, có thể đổi cờ về `False` để tái sử dụng cache trong cùng runtime.

## 6. Kết quả production run trên Colab

Run `policy-v3-clean-d4-baseline-colab` hoàn tất bằng CUDA với seed `20261109`:

| Thuộc tính | Kết quả |
|---|---:|
| Epoch đã chạy | 9 |
| Best epoch | 4 |
| Best validation loss | 1,5983 |
| Best validation top-1 | 49,98% |
| Best validation top-3 | 78,46% |
| Test loss | 1,5211 |
| Test top-1 | 51,50% |
| Test top-3 | 81,21% |
| Test samples | 4.689 |
| Thời gian | 433,51 giây |
| Số tham số | 768.537 |

Checkpoint được Colab lưu tại:

`/content/drive/MyDrive/SGU_Courses/TTNTNC_HK1_26_27/Caro_AI_Project/policy_runs/model-v3-clean-d4-baseline/best.pt`

### So sánh kiểm soát với dataset v2

| Metric tại best epoch 4 | Dataset v2 | Dataset v3 clean-D4 | Chênh lệch v3–v2 |
|---|---:|---:|---:|
| Validation loss | 1,5352 | 1,5983 | +0,0631 |
| Validation top-1 | 51,41% | 49,98% | -1,44 điểm % |
| Validation top-3 | 79,89% | 78,46% | -1,42 điểm % |
| Test loss | 1,4425 | 1,5211 | +0,0786 |
| Test top-1 | 53,22% | 51,50% | -1,72 điểm % |
| Test top-3 | 82,76% | 81,21% | -1,55 điểm % |

Toàn bộ train loss, train top-1 và train top-3 của hai run giống nhau đến độ chính xác được log ở cả 9 epoch. Đây là bằng chứng phép thử A được kiểm soát đúng: train tensors, seed, batch order, model và optimizer không thay đổi. Khác biệt held-out metric đến từ validation/test đã được purge D4 overlap.

Dataset v2 đã làm test top-1 cao hơn khoảng 1,72 điểm phần trăm và top-3 cao hơn khoảng 1,55 điểm phần trăm. Vì vậy metric v3 thấp hơn không phải model bị huấn luyện kém đi; đây là ước lượng generalization trung thực hơn.

Overfit vẫn bắt đầu sau epoch 4. Từ epoch 4 đến epoch 9, train top-1 tăng từ 59,29% lên 71,37%, trong khi validation top-1 giảm từ 49,98% xuống 46,94% và validation loss tăng từ 1,5983 lên 1,9694. Việc chọn `best.pt` ở epoch 4 tiếp tục là đúng.

### Kết luận bước A

Bước A **thành công về phương pháp đánh giá**, không nhằm tăng accuracy:

- Loại hoàn toàn D4 leakage giữa các split.
- Định lượng mức lạc quan của metric v2 khoảng 1,4–1,7 điểm phần trăm.
- Xác nhận overfit không phải do thay đổi validation/test; nguyên nhân chính vẫn nằm ở dữ liệu train, policy nhãn trộn và sức chứa model.
- Thiết lập baseline sạch để các bước B–F có thể so sánh hợp lệ.

Checkpoint v3 cần được tải về workspace và chạy tournament 666 ván trước khi kết luận leakage ảnh hưởng bao nhiêu đến sức mạnh thi đấu.

## 7. Trạng thái chạy local

Một run CPU đã được khởi động để đo baseline nhưng được dừng theo yêu cầu nhằm chuyển sang Colab. Run chưa hoàn thành epoch 1 và không tạo `best.pt`; không có metric local nào được dùng làm kết quả bước A.

Run CPU local đã được dừng trước epoch 1 theo yêu cầu và không tạo `best.pt`. Kết quả chính thức của bước A là production run Colab ở trên.

## 8. Kiểm thử

- 9 test data-pipeline không dùng fixture thư mục tạm: pass.
- Hai test dùng `tmp_path` vẫn gặp lỗi môi trường Windows `WinError 5` đã tồn tại từ trước, không phải assertion failure.
- Full build từ 2.000 raw games: pass.
- Checksum tất cả NPZ: pass trong manifest/build flow.
- Notebook JSON: hợp lệ.
- Toàn bộ code cell notebook: compile thành công.
