# Nghiệm thu PolicyAgent tuần 6 — Ly

Checkpoint: `models/checkpoints/model-v5-natural-teachers-run2-20261112T051727Z-1-001/model-v5-natural-teachers-run2/best.pt`; dataset `dataset-v5-clean-d4-natural-teachers`; best epoch 5.

## Kết quả chính

- Contract: **16/16 trạng thái đạt** (opening X/O, midgame, thắng/chặn, gần đầy bàn, terminal thắng/hòa).
- Kiểm tra bắt buộc: nạp state dict nghiêm ngặt, action legal và deterministic, không sửa environment, terminal guard trả RuntimeError.
- Xác suất được đọc bằng model chẩn đoán riêng, dùng encoder/mask chuẩn; top-1 và score khớp NeuralAgent. Ô bất hợp lệ có xác suất 0; tổng xác suất bằng 1 trong sai số 1e-6.
- Chất lượng tham khảo: action đúng **9/9**; expected xuất hiện trong top-1/top-3/top-5 lần lượt **9/9/9** trên 9 thế.
- Không thay trọng số, fixture hoặc expected actions sau khi xem kết quả; không huấn luyện lại hay chọn model bằng kết quả nghiệm thu.

## Các thế chiến thuật

Tọa độ `(hàng, cột)` bắt đầu từ 0. Top-5 ghi xác suất sau legal mask.

| Trạng thái | Expected | Action | Top-5: action (xác suất) |
|---|---|---|---|
| win_x_gap | (6, 4) | (6, 4) | (6, 4) (78.21%); (5, 5) (20.16%); (6, 7) (1.27%); (6, 1) (0.14%); (1, 2) (0.10%) |
| block_o_gap | (6, 4) | (6, 4) | (6, 4) (86.41%); (5, 5) (11.87%); (6, 7) (1.34%); (6, 1) (0.26%); (1, 2) (0.06%) |
| block_x_gap | (4, 5) | (4, 5) | (4, 5) (98.78%); (4, 2) (0.88%); (1, 2) (0.13%); (4, 8) (0.11%); (5, 5) (0.08%) |
| win_o_gap | (4, 5) | (4, 5) | (4, 5) (94.67%); (4, 2) (3.67%); (1, 2) (0.72%); (5, 5) (0.46%); (4, 8) (0.31%) |
| win_before_block | (3, 1), (3, 6) | (3, 6) | (3, 6) (93.30%); (8, 6) (4.07%); (3, 1) (2.35%); (3, 0) (0.13%); (5, 5) (0.04%) |
| win_edge | (0, 5), (0, 10) | (0, 5) | (0, 5) (93.07%); (0, 10) (4.64%); (6, 3) (1.31%); (7, 2) (0.50%); (5, 2) (0.15%) |
| win_vertical | (4, 6) | (4, 6) | (4, 6) (98.77%); (5, 5) (0.93%); (1, 6) (0.17%); (7, 6) (0.12%); (4, 5) (0.00%) |
| win_diagonal | (4, 4) | (4, 4) | (4, 4) (98.14%); (7, 7) (1.64%); (1, 1) (0.14%); (6, 5) (0.01%); (4, 5) (0.01%) |
| win_antidiagonal | (4, 6) | (4, 6) | (4, 6) (99.37%); (1, 9) (0.50%); (7, 3) (0.07%); (2, 7) (0.02%); (6, 5) (0.02%) |

## Smoke match qua runner

Mỗi cặp 4 ván nếu dùng cấu hình mặc định; đổi vai theo cùng seed gốc 11. W/D/L tính theo PolicyAgent.

| Đối thủ | Số ván | Thắng | Hòa | Thua | Record và replay |
|---|---:|---:|---:|---:|---|
| random | 4 | 4 | 0 | 0 | Đạt |
| heuristic | 4 | 2 | 2 | 0 | Đạt |

Các ván smoke chỉ xác nhận pipeline, không dùng để kết luận sức mạnh hoặc thay giải đấu tuần 7.

## Lỗi và bàn giao

- Tactical miss: không ghi nhận trên bộ fixture này.
- Ván smoke thua cần phân tích: 0. Nếu có, JSON lưu lịch sử trước nước đi cuối của candidate, top-5 và toàn bộ legal probabilities.
- Kết quả đầy đủ: `results/policy_acceptance_w6_ly.json`, gồm 16 case, phân phối 121 ô ở mỗi state chưa terminal và biên bản các ván smoke.

## Điều kiện chuyển tuần 7

- Đủ contract để tích hợp runner: **Đạt**.
- Đối chiếu exact state với val/test: **Không trùng**. Đã kiểm tra 14 fixture chưa terminal với 4806 state validation và 4689 state test; manifest và checksum tensor khớp bản v5 của checkpoint.
- Nghiệm thu đầy đủ tuần 6: **Đạt**. Đây là xác nhận riêng phần Ly; không tự đóng checklist hoặc gắn tag model của cả nhóm.

## Định danh bản đánh giá

- Checkpoint SHA-256: `d3bf4023055d63108ffc977d792841af49ac38d92252dcf900bbf5c740e238bb`.
- Dataset manifest SHA-256: `2515e17c3037a4c632ce96d8f95ee3b9197c939f18464d14cd8c22c8a266fc72`.
- Fixture SHA-256: `f1f6f184ce9ccbde69ff47d8ca7718411f8f794703effa45deaaaf95de9ad68f`.
- Môi trường: Python 3.13.5, PyTorch 2.15.0+cpu, CPU, 1 thread.
