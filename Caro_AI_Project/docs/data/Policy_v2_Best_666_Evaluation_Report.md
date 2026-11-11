# Báo cáo đánh giá `best.pt` — 666 ván với mỗi agent

**Ngày chạy:** 2026-11-10  
**Checkpoint:** `models/checkpoints/model-v2-mcts-strength8/model-v2-mcts-strength8/best.pt`  
**Contract:** `caro-v2`, bàn cờ `11 x 11`, thắng với 5 quân liên tiếp

## 1. Kết luận

`best.pt` **chưa đủ mạnh để thay thế ba agent hiện tại**. Trên tổng cộng 1.998 ván, model thắng 471, hòa 471 và thua 1.056: **win rate 23,57%**, score rate 35,36%.

| Đối thủ | Số ván | Thắng | Hòa | Thua | Win rate | Score rate |
|---|---:|---:|---:|---:|---:|---:|
| Heuristic | 666 | 333 | 0 | 333 | **50,00%** | 50,00% |
| Minimax depth 2 | 666 | 0 | 333 | 333 | **0,00%** | 25,00% |
| MCTS strength 8 | 666 | 138 | 138 | 390 | **20,72%** | 31,08% |
| **Tổng** | **1.998** | **471** | **471** | **1.056** | **23,57%** | **35,36%** |

Trong báo cáo này:

- `win rate = số ván thắng / tổng số ván`.
- `score rate = (thắng + 0,5 x hòa) / tổng số ván`.

Kết quả 50% trước Heuristic không có nghĩa model ổn định ngang Heuristic. Toàn bộ thắng/thua phụ thuộc vào bên chơi: model thua cả 333 ván khi cầm X nhưng thắng cả 333 ván khi cầm O. Với Minimax, model cũng thua toàn bộ khi cầm X và chỉ hòa khi cầm O. Đây là dấu hiệu policy rất nhạy với opening và phía đi quân.

MCTS strength 8 là đối thủ duy nhất có ngẫu nhiên trong tìm kiếm và tạo được nhiều quỹ đạo khác nhau. Trước đối thủ này, model thua rõ rệt ở cả hai bên; score rate 31,08% thấp hơn mức cân bằng 50%.

## 2. Thiết kế đánh giá

Mỗi cặp đấu có 333 seed và đổi bên trên cùng seed:

- 333 ván model cầm X.
- 333 ván model cầm O.
- Tổng 666 ván cho mỗi đối thủ, 1.998 ván cho cả ba đối thủ.
- Base seed: `20261201`, khác seed tạo dữ liệu/train `20261109`.
- Model chạy inference CPU, legal-action masking và chọn argmax; không có search hoặc sampling.
- Chạy 4 worker, hoàn tất trong 697,62 giây (khoảng 11 phút 38 giây).
- Không có illegal action, failed game hoặc budget violation.

Ba đối thủ được khởi tạo đúng profile đã dùng cho dataset v2:

| Agent | Cấu hình |
|---|---|
| Heuristic | `HeuristicAgent` mặc định |
| Minimax | alpha-beta, `max_depth=2` |
| MCTS | 8 simulations/nước, exploration 0,7, tactical pre-check, heuristic-seeded candidates, progressive widening, epsilon-heuristic rollout 0,15, horizon 8, pattern leaf evaluation |

## 3. Kết quả theo bên chơi

| Đối thủ | Bên của model | Thắng | Hòa | Thua | Win rate | Score rate |
|---|---|---:|---:|---:|---:|---:|
| Heuristic | X | 0 | 0 | 333 | 0,00% | 0,00% |
| Heuristic | O | 333 | 0 | 0 | 100,00% | 100,00% |
| Minimax depth 2 | X | 0 | 0 | 333 | 0,00% | 0,00% |
| Minimax depth 2 | O | 0 | 333 | 0 | 0,00% | 50,00% |
| MCTS strength 8 | X | 87 | 64 | 182 | 26,13% | 35,74% |
| MCTS strength 8 | O | 51 | 74 | 208 | 15,32% | 26,43% |
| **Tổng** | **X** | **87** | **64** | **848** | **8,71%** | **11,91%** |
| **Tổng** | **O** | **384** | **407** | **208** | **38,44%** | **58,81%** |

Tổng hợp theo bên bị chi phối mạnh bởi hai đối thủ deterministic. Tuy nhiên, ngay cả riêng trước MCTS có biến thiên theo seed, model vẫn chơi tốt hơn khi cầm X (26,13% thắng) so với khi cầm O (15,32% thắng). Vì vậy không thể kết luận một cách đơn giản rằng model luôn mạnh hơn ở bên O; model đang phụ thuộc mạnh vào matchup và opening cụ thể.

## 4. Ý nghĩa của 666 ván deterministic

Heuristic, Minimax và policy argmax đều deterministic. Từ bàn cờ trống, mỗi cấu hình bên chơi luôn tạo lại cùng một ván. Vì thế:

- 333 ván model-X với Heuristic là 333 lần lặp của cùng một quỹ đạo.
- 333 ván model-O với Heuristic cũng là một quỹ đạo khác được lặp lại.
- Điều tương tự xảy ra với Minimax.

Do đó các con số 333/333 ở hai matchup này xác nhận tính tái lập nhưng **không phải 333 mẫu thống kê độc lập**. Không nên dùng chúng để tính khoảng tin cậy hoặc tuyên bố model thắng 50% Heuristic trên nhiều opening khác nhau. Muốn đo độ mạnh tổng quát, cần bổ sung opening book ngẫu nhiên/hợp lệ hoặc randomize một số nước đầu rồi mới tiếp tục đấu.

Với MCTS, rollout có ngẫu nhiên nên 666 ván tạo biến thiên thực tế hơn. Đây là matchup có giá trị đánh giá sức mạnh cao nhất trong lượt test hiện tại.

## 5. Đối chiếu với kết quả training

Checkpoint `best.pt` là checkpoint tốt nhất theo validation loss, không phải checkpoint được chọn bằng tournament:

| Thuộc tính | Kết quả |
|---|---:|
| Best epoch | 4 |
| Best validation loss | 1,5352 |
| Test loss | 1,4425 |
| Test top-1 | 53,22% |
| Test top-3 | 82,76% |
| Test samples | 5.139 |
| Số tham số | 768.537 |

Từ epoch 4 đến epoch 9, train loss giảm từ 1,2019 xuống 0,8127 nhưng validation loss tăng từ 1,5352 lên 1,8698. Đây là dấu hiệu overfit; việc giữ epoch 4 làm `best.pt` là đúng.

Top-1 53,22% chỉ cho biết model bắt chước đúng nước đi teacher trên test split ở khoảng một nửa số state. Nó không đảm bảo sức mạnh thi đấu tương đương teacher. Khi chơi tự do, một nước sai làm model đi vào state ngoài phân phối train; lỗi tiếp tục tích lũy qua nhiều ply. Ngoài ra model là policy argmax một bước, không có tactical pre-check hay search như Minimax/MCTS.

Dataset đã cân bằng số policy sample của Heuristic, Minimax và MCTS. Vì vậy model học một policy trộn từ ba teacher có phong cách và độ mạnh khác nhau, thay vì tối ưu trực tiếp tỷ lệ thắng hoặc chỉ bắt chước teacher mạnh nhất.

## 6. So sánh với sức mạnh teacher trong dataset v2

Trong lượt sinh dataset v2 trước đó:

- MCTS strength 8 đạt score rate 75,3% trước Heuristic.
- MCTS strength 8 đạt score rate 71,2% trước Minimax depth 2.

Trong lượt đánh giá hiện tại, `best.pt` chỉ đạt score rate 31,08% trước chính MCTS strength 8. Model do đó **chưa kế thừa được sức mạnh tìm kiếm của MCTS**, dù MCTS đóng góp một phần ba số nhãn sau cân bằng.

Xếp hạng thực dụng từ kết quả hiện có:

1. MCTS strength 8 mạnh hơn `best.pt` rõ rệt.
2. Minimax depth 2 mạnh hơn `best.pt`; model không thắng ván nào.
3. Matchup với Heuristic phụ thuộc hoàn toàn vào phía đi quân, chưa đủ để xếp hai agent ngang nhau.

## 7. Tốc độ inference

| Đối thủ | Model mean ms/nước | Model p95 ms/nước | Đối thủ mean ms/nước |
|---|---:|---:|---:|
| Heuristic | 2,31 | 3,34 | 0,69 |
| Minimax depth 2 | 3,00 | 3,58 | 50,66 |
| MCTS strength 8 | 5,10 | 21,93 | 63,70 |
| **Tổng** | **3,40** | **3,96** | **38,85** |

Điểm mạnh rõ nhất của model là tốc độ: trung bình 3,40 ms/nước trên CPU, nhanh hơn nhiều so với Minimax và MCTS. Đổi lại, sức mạnh thi đấu hiện tại thấp hơn hai search agent.

## 8. Khuyến nghị

Ưu tiên theo thứ tự:

1. Thêm tournament validation vào quy trình chọn checkpoint; không chỉ chọn theo validation loss.
2. Đánh giá lại Heuristic/Minimax bằng opening suite đa dạng để tránh lặp cùng một ván 333 lần.
3. Train riêng từ teacher mạnh hoặc tăng trọng số mẫu MCTS thay vì trộn đều ba teacher.
4. Bổ sung tactical safety layer hoặc policy-guided search khi inference.
5. Nếu tiếp tục supervised learning, theo dõi win/score rate theo epoch để phát hiện checkpoint có top-1 thấp hơn nhẹ nhưng chơi mạnh hơn.

Với checkpoint hiện tại, nên xem `best.pt` là baseline policy nhanh để thử nghiệm, chưa phải agent mạnh nhất của dự án.

## 9. Artifact và tái lập

- Kết quả máy đọc: `results/policy_v2_best_666.json`.
- Benchmark script: `benchmarks/eval_policy_v2_666.py`.
- Training summary: `models/checkpoints/model-v2-mcts-strength8/model-v2-mcts-strength8/run_summary.json`.
- Training history: `models/checkpoints/model-v2-mcts-strength8/model-v2-mcts-strength8/history.csv`.

Lệnh tái lập:

```powershell
.\myenv\Scripts\python.exe benchmarks/eval_policy_v2_666.py `
  --checkpoint models/checkpoints/model-v2-mcts-strength8/model-v2-mcts-strength8/best.pt `
  --games 666 `
  --workers 4 `
  --base-seed 20261201 `
  --json results/policy_v2_best_666.json
```

Benchmark chỉ đọc checkpoint và chạy game; không sửa model, agent, dataset hoặc training pipeline.
