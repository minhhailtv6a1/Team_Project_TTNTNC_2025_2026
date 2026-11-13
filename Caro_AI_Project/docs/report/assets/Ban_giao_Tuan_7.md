# Bàn giao tuần 7

## Phạm vi đã thực hiện

- A1: Alpha-Beta ON/OFF, cùng state, độ sâu 2, ordering và seed; 4 scenario × 30 cặp = 240 quyết định được đo.
- A2: chỉ thay ngân sách 100/400/1000 simulations; mỗi mức 30 seed × 2 vai X/O = 60 ván, tổng 180 ván hoàn chỉnh đấu Heuristic.
- Có action/score/nodes, mean/p95 latency, mức giảm node, W/D/L, score, simulations thực tế, độ nhạy theo seed và kết quả tách X/O.
- Có 2 ván thắng và 2 failure case với board snapshot trước nước MCTS đã chọn, truy ngược được game_id, ply và trajectory checksum.
- Notebook 05 chỉ đọc config/log và gọi code canonical; không chứa bản sao thuật toán.

## Đọc kết quả

[Bảng, biểu đồ, phân tích chiến thuật](Ket_qua_Ablation_W78.md).

Full regression: 1866 passed, 21 skipped, 0 failures, 0 errors.
Đã đối chiếu checksum của toàn bộ 120 raw shard và replay đủ 180 ván A2 đến terminal.

## Trạng thái freeze và giới hạn

Lần chạy hiện tại ghi `official=False`. Working tree có thay đổi chưa commit nên chưa đạt cổng chạy chính thức của kế hoạch; không gọi đây là `results-v1`.
Sau khi nhóm chốt baseline sạch và full regression, dùng `run --official --output results/w78_ablation_ly_official` để tạo lần chạy chính thức riêng. Không đổi tham số theo số liệu đã xem.
Config giữ nguyên phiên bản ablation đã tìm thấy trong commit `41df9704`; không sửa agent/engine/model frozen.
A2 dùng random rollout horizon 4 và pattern leaf evaluation đã công bố trong config; không suy rộng thành hiệu năng MCTS ở tournament.
Tactical precheck có thể dùng 0 simulations; bảng báo cả ngân sách yêu cầu và tổng simulations thực tế.
30 lần đo trên một state deterministic là phép lặp thời gian, không phải 30 vị trí độc lập. X/O là thống kê mô tả theo vai, không chứng minh lợi thế nhân quả của người đi trước.
Latency được đo khi dùng 3 worker và có full regression chạy đồng thời; chỉ phản ánh điều kiện đo này, không phải benchmark đơn tiến trình độc lập.
Poster và review bản cuối thuộc tuần 8; không nằm trong yêu cầu tuần 7 này.

## Nhận xét chiến thuật và vai đi trước

- `A2-n1000-s5-side1` (X, đi trước): nước `[8, 1]` tại ply 21. MCTS chọn nước thắng ngay hợp lệ. 
- `A2-n1000-s5-side-1` (O, đi sau): nước `[7, 2]` tại ply 18. MCTS chọn nước thắng ngay hợp lệ. 
- `A2-n1000-s0-side1` (X, đi trước): nước `[3, 4]` tại ply 33. Có nhiều hơn một nước thắng ngay của đối thủ: một nước chặn không thể giải hết threat. Các ô đối thủ có thể thắng ngay là `[[3, 5], [8, 5]]`. Thế cờ đã có ít nhất hai đe dọa thắng; không có nước thắng ngay của MCTS để kết thúc trước, nên một nước phòng thủ không đủ cứu ván. Snapshot chứng minh tình thế ở nước cuối, chưa xác định nước sai đầu tiên của cả ván.
- `A2-n1000-s0-side-1` (O, đi sau): nước `[4, 4]` tại ply 36. Có nhiều hơn một nước thắng ngay của đối thủ: một nước chặn không thể giải hết threat. Các ô đối thủ có thể thắng ngay là `[[5, 9], [10, 4]]`. Thế cờ đã có ít nhất hai đe dọa thắng; không có nước thắng ngay của MCTS để kết thúc trước, nên một nước phòng thủ không đủ cứu ván. Snapshot chứng minh tình thế ở nước cuối, chưa xác định nước sai đầu tiên của cả ván.

| Simulations | Score khi MCTS là X | Score khi MCTS là O | Chênh lệch X−O |
|---:|---:|---:|---:|
| 100 | 0.0000 | 0.0000 | +0.0000 |
| 400 | 0.0667 | 0.0833 | -0.0167 |
| 1000 | 0.1500 | 0.0333 | +0.1167 |

Mức 400 và 1000 không cho cùng xu hướng X/O. Hai case thắng được chọn gồm cả X và O; đây là minh họa chiến thuật, không phải mẫu ngẫu nhiên để ước lượng lợi thế đi trước. Phân tích dùng toàn bộ ván để tránh suy luận từ riêng những case đẹp. Tăng simulations cải thiện score trong bộ seed này nhưng phần lớn ván vẫn thua Heuristic; không che kết quả xấu hoặc tune lại profile.
