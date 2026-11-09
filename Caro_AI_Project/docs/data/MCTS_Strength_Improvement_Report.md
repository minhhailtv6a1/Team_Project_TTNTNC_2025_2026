# Báo cáo cải thiện sức mạnh MCTS

## 1. Phạm vi

Báo cáo này chỉ đánh giá và cải thiện khả năng thi đấu của `MCTSAgent` trước `HeuristicAgent` và `MinimaxAgent(depth=2)`. Không chạy training, không sinh dữ liệu, không sửa pipeline dataset và không xử lý cân bằng nhãn.

## 2. Kết quả chính

Cấu hình được chọn là `MCTS-STRENGTH` với 64 simulations/nước. Mỗi cặp đấu gồm 20 ván, đổi bên X/O, dùng ba nhóm seed `707`, `808`, `909`.

| Đối thủ | Số ván | Thắng | Hòa | Thua | Tỷ lệ thắng | Score rate `(W + 0.5D) / N` | X score | O score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Heuristic | 20 | 15 | 4 | 1 | 75% | 85% | 85% | 85% |
| Minimax depth 2 | 20 | 14 | 2 | 4 | 70% | 75% | 90% | 60% |

So với kết quả legacy đã ghi nhận trước đó — MCTS 20 simulations thua toàn bộ 666 ván trước cả Heuristic và Minimax — profile mới đã chuyển sang score rate trên 50% trong cả hai cặp test. Đây không phải phép so sánh A/B có cùng số ván và cùng budget, nên chỉ được dùng để xác nhận hướng cải tiến, không dùng để suy ra mức tăng tuyệt đối trên bộ 666 ván cũ.

Artifact kết quả:

- `.benchmarks/mcts_strength/final_strength64_vs_heuristic_20.json`
- `.benchmarks/mcts_strength/final_strength64_vs_minimax_20.json`

## 3. Vì sao MCTS cũ thua nhiều

MCTS cũ có ba điểm nghẽn trực tiếp ảnh hưởng số ván thắng:

1. Không gian nước đi đầu game có thể lên tới 121 ô nhưng budget chỉ 20 simulations. Root chưa đủ lượt để thử và so sánh các nước đi có ý nghĩa; phần lớn thống kê UCT gần như là nhiễu một mẫu.
2. Expansion và rollout ngẫu nhiên không ưu tiên thắng ngay, chặn thua ngay hoặc các mẫu tấn công/phòng thủ quan trọng của Caro. Kết quả rollout vì vậy có phương sai cao và không phản ánh chất lượng nước đi ở root.
3. Rollout tới terminal tốn nhiều bước. Với budget nhỏ, phần lớn chi phí được dùng để hoàn thành các ván mô phỏng ngẫu nhiên thay vì mở rộng cây đủ sâu ở các nhánh tốt.

Heuristic có bộ chấm pattern trực tiếp, còn Minimax depth 2 có candidate filtering, alpha-beta và leaf evaluator. Hai agent này nhận tín hiệu chiến thuật rõ ràng ở mỗi lượt, trong khi MCTS cũ chỉ nhận tín hiệu thắng/thua sau rollout ngẫu nhiên dài.

## 4. Cải tiến đã áp dụng

Profile `MCTS-STRENGTH` nằm trong `configs/benchmark_mcts_v2.json`:

```json
{
  "exploration_weight": 0.7,
  "tactical_precheck": true,
  "candidate_policy": "heuristic_seeded",
  "neighbor_radius": 2,
  "progressive_widening_c": 1.5,
  "progressive_widening_alpha": 0.5,
  "rollout_policy": "epsilon_heuristic",
  "rollout_epsilon": 0.15,
  "rollout_horizon": 8,
  "leaf_evaluation": "pattern",
  "reuse_simulation_env": true
}
```

Các thay đổi tác động trực tiếp tới sức mạnh thi đấu:

- Tactical pre-check: lấy nước thắng ngay hoặc nước chặn bắt buộc trước khi search, tránh lỗi chiến thuật một ply.
- Heuristic-seeded expansion: sắp xếp action theo `action_priority`, giúp các nhánh có khả năng tấn công/phòng thủ cao được mở trước.
- Progressive widening: giới hạn số child được mở theo `ceil(1.5 * (visits + 1)^0.5)`. Budget được tập trung vào các nhánh tốt thay vì dàn đều trên toàn bộ bàn.
- Epsilon-heuristic rollout: 85% chọn nước có pattern tốt, 15% khám phá ngẫu nhiên trong candidate cục bộ. Rollout giảm nhiễu nhưng vẫn giữ exploration.
- Horizon 8 và pattern leaf: dừng rollout sau 8 ply, dùng `evaluate_board` rồi chuẩn hóa bằng `tanh(raw / 5000)` về `[-1, 1]`. MCTS nhận tín hiệu trung gian có ý nghĩa thay vì phải chờ terminal.
- UCT exploration `0.7`: thấp hơn `sqrt(2)`, phù hợp với action ordering tốt và budget chỉ 64 simulations; tăng số lần tái thăm nhánh mạnh.
- Reuse simulation environment: clone một lần rồi `undo`, giảm overhead để dành thời gian cho search.

Đây là MCTS được dẫn hướng bằng heuristic, không phải pure MCTS rollout ngẫu nhiên. Nó cũng tái sử dụng evaluator hiện có của Minimax, vì mục tiêu của đợt này là tăng tỷ lệ thắng chứ không phải giữ tính độc lập giữa các thuật toán.

## 5. Chi phí và hạn chế còn lại

| Đối thủ | Mean MCTS move | P95 MCTS move | Tổng thời gian | Budget violations |
| --- | ---: | ---: | ---: | ---: |
| Heuristic | 1191.64 ms | 3161.61 ms | 777.18 s | 0 |
| Minimax depth 2 | 752.56 ms | 1415.88 ms | 357.24 s | 0 |

- Kết quả 20 ván là tín hiệu mạnh để chọn cấu hình, nhưng chưa đủ thay thế evaluation 666 ván.
- Cặp Minimax còn lệch bên: score khi đi X là 90%, khi đi O là 60%, chênh 30 điểm phần trăm. Cần tăng số ván/seed trước khi kết luận ổn định.
- Chất lượng tăng đi kèm latency cao hơn. Nếu có giới hạn thời gian nước đi, nên benchmark thêm 32/48/64 simulations thay vì tăng thẳng lên 100–400.
- Leaf evaluator dùng cùng họ pattern với Minimax/Heuristic. Kết quả chứng minh agent mạnh hơn trong repo hiện tại, không chứng minh MCTS thuần tổng quát hơn.

## 6. Kiểm thử hồi quy

Nhóm test liên quan đã chạy lại sau khi benchmark kết thúc:

```powershell
.\myenv\Scripts\python.exe -m pytest tests/test_mcts_ai.py tests/test_heuristic_ai.py tests/test_minimax_ai.py tests/test_tournament_runner.py -q -p no:cacheprovider
```

Kết quả: `197 passed in 29.37s`.

Một lần chạy trong lúc hai tournament đang chiếm CPU làm test thời gian của `BudgetEnforcer` ghi thừa một violation. Chạy riêng test đó khi tải đã kết thúc cho kết quả `1 passed in 0.07s`; chạy lại toàn bộ nhóm test sau đó đạt 197/197.

## 7. Cách tái lập tournament

```powershell
.\myenv\Scripts\python.exe benchmarks/eval_mcts_strength.py --profile MCTS-STRENGTH --simulations 64 --opponent heuristic --games 20 --seed-groups 707 808 909 --json .benchmarks/mcts_strength/final_strength64_vs_heuristic_20.json

.\myenv\Scripts\python.exe benchmarks/eval_mcts_strength.py --profile MCTS-STRENGTH --simulations 64 --opponent minimax-d2 --games 20 --seed-groups 707 808 909 --json .benchmarks/mcts_strength/final_strength64_vs_minimax_20.json
```

Để có kết luận chắc hơn, bước tiếp theo trong đúng phạm vi MCTS là chạy cùng cấu hình trên 100–200 ván/cặp, tiếp tục đổi bên và giữ nguyên seed manifest. Không cần thay đổi dataset cho bước này.
