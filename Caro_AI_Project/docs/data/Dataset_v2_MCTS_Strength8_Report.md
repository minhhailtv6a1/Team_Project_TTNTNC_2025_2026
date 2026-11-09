# Dataset v2 — MCTS Strength-8, 2.000 ván

## Kết luận

Dataset đã được sinh và xuất tensors để chuẩn bị train. Không có quá trình train nào được chạy.

Dataset cuối dùng ba teacher với số policy samples bằng nhau trong từng split. MCTS dùng implementation mới gồm tactical pre-check, heuristic-seeded expansion, progressive widening, epsilon-heuristic rollout, horizon 8 và pattern leaf evaluation; budget được khóa ở 8 simulations/nước.

## Đường dẫn

- Raw run: `data/raw_logs/w56_dataset_v2_mcts_strength8_2000`
- Processed dataset dùng để train: `data/processed_tensors/w56_dataset_v2_mcts_strength8_2000_balanced`
- Dataset manifest: `data/processed_tensors/w56_dataset_v2_mcts_strength8_2000_balanced/dataset_manifest.json`
- Balance report: `data/processed_tensors/w56_dataset_v2_mcts_strength8_2000_balanced/balance_report.json`
- Self-play config: `configs/selfplay_w56_dataset_v2_mcts_strength.json`
- Dataset config: `configs/train_w56_v2_mcts_strength.json`

Bản processed trung gian không cân bằng đã được xóa sau khi đối chiếu để tránh dùng nhầm khi train.

## Cấu hình sinh dữ liệu

| Thuộc tính | Giá trị |
| --- | ---: |
| Tổng số ván | 2.000 |
| Heuristic–Minimax | 668 |
| Heuristic–MCTS | 666 |
| Minimax–MCTS | 666 |
| Swap X/O | Có |
| Board | 11×11 |
| Win length | 5 |
| MCTS simulations | 8 |
| Process shards | 16 |
| Failed games | 0 |

Raw run có 16 shard, tổng 118.429 nước đi và kích thước khoảng 13,55 MB. Tất cả shard có checksum trong manifest và từng ván đã được replay theo engine trước khi manifest con được ghi.

## Kết quả thi đấu thực tế

| Cặp | MCTS thắng | Đối thủ thắng | Hòa | MCTS score rate |
| --- | ---: | ---: | ---: | ---: |
| MCTS–Heuristic | 452 | 115 | 99 | 75,3% |
| MCTS–Minimax depth 2 | 422 | 139 | 105 | 71,2% |
| Heuristic–Minimax depth 2 | — | Heuristic 334, Minimax 0 | 334 | — |

Mẫu hiệu chỉnh 6 ván trước khi sinh chỉ dùng để chọn budget có chi phí phù hợp. Kết quả 666 ván cho thấy MCTS strength-8 vẫn mạnh hơn rõ rệt; không được diễn giải rằng ba agent có sức mạnh ngang nhau.

Tổng hợp theo agent trong raw run:

| Agent | Số ván tham gia | X | O | Thắng | Hòa | Thua | Raw move labels |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Heuristic | 1.334 | 667 | 667 | 449 | 433 | 452 | 42.708 |
| MCTS | 1.332 | 666 | 666 | 874 | 204 | 254 | 33.492 |
| Minimax | 1.334 | 667 | 667 | 139 | 439 | 756 | 42.229 |

## Vì sao cần cân bằng sau dedup

Pipeline tạo một policy sample trước mọi nước đi của cả bên thắng và bên thua. Sau split theo game, các state–action trùng nhau được loại để tránh lặp và leakage.

Trước bước cân bằng, teacher source trong train sau dedup là:

| Source agent | Samples trước D4 | Tỷ lệ |
| --- | ---: | ---: |
| Heuristic | 9.589 | 24,8% |
| MCTS | 19.579 | 50,7% |
| Minimax | 9.474 | 24,5% |

MCTS mới tạo nhiều state–action duy nhất hơn, trong khi các opening tất định giống nhau của Heuristic/Minimax bị dedup nhiều. Vì vậy lịch số ván cân bằng chưa đủ để giữ tỷ trọng teacher sau xử lý.

Pipeline được bổ sung `balance_source_agents: true`. Trong mỗi split, nó downsample xác định bằng `split_seed` về source nhỏ nhất sau dedup và trước D4 augmentation. Split theo game vẫn được giữ nguyên, nên không tạo cross-split leakage.

## Dataset cuối

| Split | Games | Tổng samples | Heuristic | MCTS | Minimax |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Train | 1.400 | 227.376 | 75.792 | 75.792 | 75.792 |
| Validation | 300 | 5.409 | 1.803 | 1.803 | 1.803 |
| Test | 300 | 5.139 | 1.713 | 1.713 | 1.713 |

Train có 9.474 samples/source trước D4 và 75.792 samples/source sau 8 phép biến đổi D4.

Phân phối action target:

| Split | Nhãn được phủ | Normalized entropy | Tỷ lệ nhãn lớn nhất |
| --- | ---: | ---: | ---: |
| Train | 121/121 | 0,9852 | 1,37% |
| Validation | 120/121 | 0,9883 | 1,48% |
| Test | 120/121 | 0,9868 | 1,67% |

Train phủ đủ toàn bộ 121 action classes. Entropy gần 1 và tỷ lệ class lớn nhất thấp cho thấy không có hiện tượng một ô duy nhất chi phối policy labels. Việc thiếu một class trong val/test nhỏ hơn không ảnh hưởng legality và có thể xảy ra sau dedup/downsample.

Processed dataset cuối có kích thước khoảng 76,92 MB. Loader đã xác nhận checksum, dtype, tensor shape, legal mask và legality của mọi target ở cả ba split.

## Cảnh báo thời gian

Raw manifest ghi 4 `elapsed_mismatch` ở mức 55–77 ms trong lúc chạy 16 process. Đây là chênh lệch giữa elapsed time agent tự báo và wall-clock do tranh CPU; không có vi phạm simulations, max depth, illegal action hay failed game. Các ván liên quan vẫn replay đúng engine và được giữ lại.

## Kiểm thử

Các nhóm test data pipeline, self-play, MCTS và tournament đã chạy lại:

```text
105 passed in 7.01s
```

Dataset có thể được đưa vào bước train thông qua `dataset_manifest.json` trong thư mục processed `_balanced`. Không cần chạy lại self-play trừ khi thay đổi teacher config hoặc muốn tăng quy mô dữ liệu.
