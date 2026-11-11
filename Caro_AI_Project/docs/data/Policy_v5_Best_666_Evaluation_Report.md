# Kết quả model v5 — 666 ván với mỗi agent

**Checkpoint:** `models/checkpoints/model-v5-natural-teachers-run2/best.pt`  
**Seed:** `20261201`  
**Thiết kế:** 333 seed/đối thủ, đổi bên tại cùng seed; 333 ván cầm X và 333 ván cầm O

## Kết quả chính

| Đối thủ | Thắng | Hòa | Thua | Win rate | Draw rate | Loss rate | Score rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| Heuristic | 333 | 333 | 0 | 50,00% | 50,00% | 0,00% | 75,00% |
| Minimax depth 2 | 333 | 0 | 333 | 50,00% | 0,00% | 50,00% | 50,00% |
| MCTS strength 8 | 154 | 160 | 352 | 23,12% | 24,02% | 52,85% | 35,14% |
| **Tổng** | **820** | **493** | **685** | **41,04%** | **24,67%** | **34,28%** | **53,38%** |

`Score rate = (thắng + 0,5 × hòa) / tổng số ván`.

## Kết quả theo bên

| Đối thủ | Bên model | Thắng | Hòa | Thua | Win rate | Score rate |
|---|---|---:|---:|---:|---:|---:|
| Heuristic | X | 333 | 0 | 0 | 100,00% | 100,00% |
| Heuristic | O | 0 | 333 | 0 | 0,00% | 50,00% |
| Minimax depth 2 | X | 0 | 0 | 333 | 0,00% | 0,00% |
| Minimax depth 2 | O | 333 | 0 | 0 | 100,00% | 100,00% |
| MCTS strength 8 | X | 105 | 72 | 156 | 31,53% | 42,34% |
| MCTS strength 8 | O | 49 | 88 | 196 | 14,71% | 27,93% |

## So sánh với model v2

| Đối thủ | v2 W/D/L | v5 W/D/L | V2 score | V5 score | Thay đổi |
|---|---:|---:|---:|---:|---:|
| Heuristic | 333/0/333 | 333/333/0 | 50,00% | 75,00% | +25,00 điểm % |
| Minimax depth 2 | 0/333/333 | 333/0/333 | 25,00% | 50,00% | +25,00 điểm % |
| MCTS strength 8 | 138/138/390 | 154/160/352 | 31,08% | 35,14% | +4,05 điểm % |
| **Tổng** | **471/471/1.056** | **820/493/685** | **35,36%** | **53,38%** | **+18,02 điểm %** |

Trước MCTS — matchup có biến thiên theo seed — v5 tăng 16 trận thắng, tăng 22 trận hòa và giảm 38 trận thua so với v2. Win rate tăng từ 20,72% lên 23,12%; score rate tăng từ 31,08% lên 35,14%.

## Kết luận

- V5 cải thiện rõ so với v2 ở cả ba matchup và đạt score tổng hợp trên 50%.
- V5 không thua Heuristic trong cấu hình deterministic hiện tại.
- V5 đã thắng được Minimax khi cầm O, nhưng vẫn thua toàn bộ khi cầm X.
- MCTS strength 8 vẫn mạnh hơn v5: model thua 352/666 ván và score rate chỉ 35,14%.
- Điểm yếu lớn nhất còn lại là MCTS và chênh lệch theo phía đi quân.

Heuristic, Minimax và policy argmax đều deterministic; 333 ván mỗi bên lặp lại cùng một quỹ đạo, nên hai matchup này xác nhận tính tái lập chứ không phải 333 mẫu độc lập. Kết quả MCTS có giá trị thống kê thực tế hơn vì rollout có ngẫu nhiên.

## Tính hợp lệ

- Tổng số ván: 1.998.
- Mỗi đối thủ: 666 ván, cân bằng X/O.
- Budget violations: 0.
- JSON gốc: `results/policy_v5_best_666.json`.
- Thời gian chạy: 1.353,48 giây, khoảng 22 phút 33 giây.
