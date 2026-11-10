# Báo cáo kết quả Lab 05 — Tìm kiếm đối kháng

## Phạm vi và quy ước đo

Kết quả Thiện đã được chạy lại với seed 42, `time.perf_counter()` và node counter reset ở từng search. “Tổng thời gian” là tổng các lần agent suy nghĩ; “TB/nước agent” là tổng đó chia số nước do agent thực hiện. Không suy ra TB/nước bằng cách chia cho số ván.

## Bảng sáu chiến lược Tic-Tac-Toe

|Chiến lược|Cách đánh giá|Kết quả/chi phí đã xác nhận|Nguồn|
|---|---|---|---|
|AND-OR|Kế hoạch điều kiện trước đối thủ|Chờ `results/hai_results.md` để tích hợp số liệu|Hải|
|Minimax|Utility terminal chính xác|T4: 549,946 nodes; 26.517 s|Thiện|
|Alpha-Beta|Minimax có cắt tỉa|T4: 18,297 nodes; 1.009 s|Thiện|
|Heuristic Alpha-Beta|Cutoff + heuristic|cutoff 4, T4: 283 nodes; 58.420 ms|Thiện|
|Pure Monte Carlo|Trung bình rollout|Chờ `results/ly_results.md` để tích hợp số liệu|Ly|
|UCB1/MCTS restricted|Khai thác + khám phá UCB1|Chờ `results/ly_results.md` để tích hợp số liệu|Ly|

Ba phần “chờ” được giữ rõ ràng thay vì bịa số liệu: tại thời điểm tổng hợp, hai file kết quả cá nhân của Hải/Ly chưa có trong workspace. Khi chúng được bàn giao, thay hai ô nguồn tương ứng bằng bảng W/H/L, số lượt và tổng/TB thời gian của họ.

## Kết quả Thiện

- Minimax và Alpha-Beta đã được kiểm tra cùng utility **và tập nước tối ưu** ở cả T1–T4, không chỉ cùng một chỉ số nước đi.
- Alpha-Beta giảm T4 từ 549,946 xuống 18,297 node. Ordering centre→corners→edges tiếp tục giảm T4 còn 7,275 node, nhưng làm T2 tăng 101 lên 149 node: thứ tự tĩnh là heuristic, không phải bảo đảm.
- Heuristic cutoff 2/4 đều chọn nước thuộc tập tối ưu đầy đủ ở T1–T4; cutoff 4 tốn 283 node tại T4 so với 26 node ở cutoff 2.
- Đấu Random 100 ván mỗi vai: heuristic cutoff 2 đạt X `96/4/0`, O `89/11/0`; cutoff 4 đạt X `96/4/0`, O `83/17/0` (thắng/hòa/thua từ góc nhìn agent). Chi tiết thời gian có trong `results/thien_results.md`.

## Sáu câu hỏi thảo luận

1. **Vì sao Minimax và Alpha-Beta phải cùng kết quả?** Alpha-Beta chỉ cắt nhánh không thể thay đổi lựa chọn dưới các cận hiện có; do đó utility minimax giữ nguyên. Thí nghiệm xác nhận giá trị lẫn tập nước tối ưu.
2. **Move ordering ảnh hưởng thế nào?** Nó không đổi correctness nhưng có thể đổi mạnh số node. Duyệt nước hứa hẹn trước làm cận chặt sớm; một ordering tĩnh vẫn có thể phản tác dụng ở một trạng thái như T2.
3. **Đổi cutoff đánh đổi gì?** Cutoff nông giảm thời gian rất mạnh nhưng trả về ước lượng heuristic, không phải utility thật. Cutoff sâu hơn nhìn xa hơn nhưng tăng số node theo cấp số nhân.
4. **Heuristic cần những thuộc tính nào?** Nó phải đối xứng theo người chơi, nhận terminal chính xác, thưởng cơ hội của mình, phạt đe dọa đối thủ và bị chuẩn hóa để không lấn át ±1 của terminal. Connect 4 dùng các cửa sổ 4 ô và bonus tâm bàn.
5. **Vì sao Connect 4 không full-search 6×7?** Branching factor xấp xỉ 7 và tối đa 42 lượt tạo game tree khổng lồ. Full search được giới hạn ở 4×4; bàn chuẩn dùng Alpha-Beta cutoff.
6. **Monte Carlo/UCB1 so với heuristic Alpha-Beta?** Rollout không cần handcrafted evaluation nhưng cần nhiều mô phỏng để ổn định. UCB1 phân bổ ngân sách tốt hơn PMCS; heuristic Alpha-Beta thường phản hồi chắc hơn với ngân sách thấp nếu heuristic phù hợp. Cần số liệu Ly để so sánh định lượng công bằng.

## Nhận xét tổng hợp

1. Cắt tỉa có tác động rõ nhất khi cây sâu: ở T4, Alpha-Beta giảm node khoảng 96.7% so Minimax.
2. Chất lượng nước không thể đánh giá chỉ bằng index: T1/T3/T4 có nhiều nước cùng giá trị; vì vậy báo cáo dùng tập nước tối ưu.
3. Thời gian đo một lần nhiễu hơn node count; node/value là chỉ số tái lập, thời gian chỉ dùng để đánh giá độ đáp ứng trên máy đã chạy.
4. Cutoff 4 chậm hơn cutoff 2 khoảng một bậc độ lớn trong trận đấu nhưng vẫn nhanh hơn full search trên bàn rỗng.
5. Với Connect 4 chuẩn, heuristic cửa sổ + ưu tiên tâm tạo nước đi hợp lý ở cutoff, nhưng static move ordering cần được benchmark trên nhiều vị trí thay vì giả định luôn có lợi.
