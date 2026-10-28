# Kế hoạch chi tiết gộp Tuần 3 và Tuần 4 - AI cơ bản, tìm kiếm và benchmark

> **Thời lượng:** 1 tuần tăng tốc, gồm 5 ngày làm việc chính và cuối tuần dự phòng nếu còn blocker.  
> **Phạm vi hiện hành:** `caro-v2`, bàn cờ 11x11, public action `(row, col)`.  
> **Mục tiêu:** gộp công việc Tuần 3 và Tuần 4 thành một sprint; mỗi thành viên sở hữu một task xuyên suốt từ tính đúng đến tối ưu và đo lường.  
> **Nguyên tắc:** giữ nguyên cách chia M1, M2, M3; mỗi người chỉ sửa file thuộc ownership của mình; merge theo dependency, không merge theo người hoàn thành trước.

---

## 1. Nguồn và cách gộp kế hoạch

Kế hoạch này tổng hợp Giai đoạn 2 trong roadmap 8 tuần và cập nhật theo trạng thái repository hiện tại.

| Nội dung gốc | Tuần 3 | Tuần 4 | Cách giao trong sprint gộp |
|---|---|---|---|
| M1 | Khung MCTS gồm Node, UCT, expansion và rollout | Backpropagation, seed, budget, benchmark | Một task MCTS hoàn chỉnh từ correctness đến profiling |
| M2 | Heuristic theo thứ tự win, block, threat, center | Minimax, Alpha-Beta, evaluation và move ordering | Một task search agent dùng chung evaluation |
| M3 | RandomAgent, metrics schema và runner smoke | Timer, nodes, simulations và budget enforcer | Một task baseline, runner, logging và integration |

Các điểm trong roadmap cũ được chuẩn hóa như sau:

- Dùng `caro-v2`, không quay lại `caro-v1`.
- Chỉ phát triển và kiểm thử bàn 11x11; không hard-code 9x9 hoặc policy dài 81.
- Dùng `GameEnv`, `Agent`, `SearchBudget` và `AgentDecision` trong `core/engine/interfaces.py`.
- Agent chỉ dùng public API của environment. Không truy cập `Board.grid`, `_history` hoặc hàm private của `RuleEngine`.
- Benchmark Tuần 3 và 4 chỉ là smoke và sensitivity nhỏ. Giải đấu 100 ván mỗi cặp vẫn thuộc giai đoạn thực nghiệm sau.

---

## 2. Kết quả bắt buộc cuối sprint

Cuối tuần, nhóm phải có một bản `agents-v1` chạy end-to-end với các kết quả sau:

- `RandomAgent`, `HeuristicAgent`, `MinimaxAgent` có Alpha-Beta và `MCTSAgent` cùng thỏa `Agent` protocol.
- Mọi agent trả `AgentDecision.action` thuộc `env.legal_actions()` và không mutation environment thật.
- Mọi agent từ chối state terminal hoặc state không còn legal action bằng `RuntimeError`.
- Seed cho Random và MCTS tạo kết quả tái lập với cùng state và cùng budget.
- Heuristic ưu tiên thắng ngay, chặn thua ngay, threat và vị trí trung tâm theo thứ tự đã công bố.
- Minimax hỗ trợ giới hạn độ sâu, Alpha-Beta bật hoặc tắt, evaluation, move ordering và bộ đếm nodes.
- MCTS có đủ Selection, Expansion, Simulation và Backpropagation; báo nodes, simulations và elapsed time.
- Runner chạy được game tự động giữa mọi cặp agent, đổi bên X/O, nhận seed và budget từ bên ngoài.
- Logger ghi được `MoveRecord` và `GameRecord` theo schema `caro-v2`, action JSON ở dạng `[row, col]`.
- Có profile FAST 100 ms mỗi nước, FAIR 500 ms mỗi nước, MCTS 100/400/1000 simulations và Alpha-Beta depth 2/3/4.
- Có smoke tournament chứng minh các agent chạy qua cùng một runner và cùng một schema metric.
- Full regression engine và UI không bị phá vỡ.

### 2.1. Những việc không bắt buộc trong sprint này

- Không sinh hàng trăm ván self-play để train.
- Không xây PolicyNet, NeuralAgent hoặc checkpoint.
- Không chạy round-robin 100 ván mỗi cặp.
- Không tính Elo hoặc kết luận agent nào mạnh nhất.
- Không sửa luật game, encoding action hoặc ý nghĩa reward.
- Không tối ưu bằng native extension, multiprocessing hoặc GPU.
- Không mở lại module 9x9.

---

## 3. Baseline và khoảng trống hiện tại

| Hạng mục | Baseline hiện tại | Đích cuối sprint | Owner |
|---|---|---|---|
| Engine | `CaroEnv` có reset, step, result, clone và undo | Giữ nguyên, chỉ dùng public API | Không sửa trong sprint |
| Contract | Có `Agent`, `SearchBudget`, `AgentDecision` | Freeze trong toàn sprint | M3 kiểm soát |
| UI | Human vs Human dùng `CaroEnv` thật | Không regression | M1 smoke sau merge |
| RandomAgent | File rỗng | Baseline hợp lệ, có seed | M3 |
| HeuristicAgent | File rỗng | Win, block, threat, center | M2 |
| MinimaxAgent | File rỗng | Depth, evaluation, Alpha-Beta, ordering, nodes | M2 |
| MCTSAgent | File rỗng | UCT hoàn chỉnh, seed, budget, counters | M1 |
| Logger | File rỗng | JSONL `caro-v2`, UTF-8, không mất dữ liệu | M3 |
| Tournament runner | File rỗng | Chạy game/match, đổi bên, metrics, budget | M3 |
| Agent tests | Chưa có suite riêng | Contract, tactical, determinism, integration | M1/M2/M3 theo ownership |
| Benchmark config | Chưa có | Một file cấu hình dùng chung | M3 |

### 3.1. Điều kiện bắt đầu

Trước khi mở nhánh, cả nhóm chạy:

```powershell
git status
.\myenv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
```

Nếu baseline không xanh vì thay đổi Tuần 2 chưa merge, hoàn tất và merge Tuần 2 trước. Không trộn bugfix UI hoặc engine còn dang dở vào PR agent.

---

## 4. Quyết định kỹ thuật khóa trong sáng Ngày 1

Ba thành viên họp tối đa 60 phút. M3 ghi decision note ngắn trong mô tả PR hoặc tài liệu integration. Sau cuộc họp, các giá trị sau được xem là frozen trong sprint.

### 4.1. Agent API

```python
decision = agent.choose_action(env, budget)
```

Quy ước bắt buộc:

- `env` là `GameEnv`; agent không được sửa `env`.
- Mô phỏng phải dùng `env.clone_env()` và có thể dùng `undo()` trên clone.
- `decision.action` là tuple `(row, col)` và phải thuộc legal actions tại root.
- `decision.score` luôn theo góc nhìn player đang đi tại root.
- `decision.elapsed_ms` không âm.
- `nodes` là số state hoặc node search đã mở rộng.
- `simulations` chỉ khác 0 với MCTS hoặc agent dựa trên rollout.
- Terminal hoặc không còn legal action phải raise `RuntimeError`.

### 4.2. Budget

Nếu nhiều giới hạn cùng được truyền, agent dừng khi chạm giới hạn đầu tiên.

| Field | Ý nghĩa trong sprint |
|---|---|
| `time_limit_ms` | Wall-clock budget cho một lần `choose_action` |
| `max_depth` | Độ sâu tối đa của Minimax/Alpha-Beta |
| `max_nodes` | Số node tối đa được mở rộng |
| `simulations` | Số rollout tối đa của MCTS |
| `seed` | Seed cục bộ; không gọi `random.seed()` ở global scope |

Quy tắc triển khai:

- Minimax dùng kết quả của depth hoàn chỉnh gần nhất nếu time budget kết thúc giữa một iteration.
- MCTS chỉ tăng `simulations` sau khi hoàn tất một vòng Selection đến Backpropagation.
- Runner đo wall time độc lập để phát hiện agent không tuân budget.
- Test CI ưu tiên giới hạn depth, nodes và simulations để tránh flaky. Kiểm tra time budget dùng tolerance, không assert chính xác từng millisecond.

### 4.3. Benchmark profile

M3 tạo `configs/benchmark_w34.json` hoặc file tương đương với nội dung logic sau:

| Profile | Cấu hình | Mục đích |
|---|---|---|
| FAST | 100 ms mỗi nước | UI/demo và smoke nhanh |
| FAIR | 500 ms mỗi nước | So sánh chính ban đầu |
| MCTS-S | 100, 400, 1000 simulations | Sensitivity MCTS |
| AB-D | Depth 2, 3, 4 | Sensitivity Alpha-Beta |
| Seeds | Tối thiểu 3 seed cố định | Determinism smoke |

Absolute latency chỉ được báo cáo cùng thông tin máy chạy. Không dùng kết quả smoke để kết luận câu hỏi nghiên cứu.

---

## 5. Ownership để hạn chế conflict

| Khu vực | Owner duy nhất được ghi code chính | Người khác được làm gì |
|---|---|---|
| `core/agents/mcts_ai.py` | M1 - Hải | Review API và gửi test case qua comment |
| `tests/test_mcts_ai.py` | M1 - Hải | M3 review determinism và metrics |
| `benchmarks/bench_mcts.py` | M1 - Hải | M3 gọi script, không sửa chung PR |
| `core/agents/heuristic_ai.py` | M2 - Ly | M1/M3 chỉ review |
| `core/agents/minimax_ai.py` | M2 - Ly | M1/M3 chỉ review |
| `tests/test_heuristic_ai.py`, `tests/test_minimax_ai.py` | M2 - Ly | M3 bổ sung case integration ở file riêng |
| `benchmarks/bench_minimax.py` | M2 - Ly | M3 gọi script, không sửa chung PR |
| `core/agents/random_ai.py` | M3 - Thiện | M1/M2 dùng qua `Agent` protocol |
| `core/utils/logger.py` | M3 - Thiện | M1/M2 không ghi log trực tiếp trong agent |
| `core/utils/tournament_runner.py` | M3 - Thiện | M1/M2 cung cấp agent factory qua public API |
| `tests/test_random_ai.py`, `tests/test_tournament_runner.py` | M3 - Thiện | M1/M2 review |
| `tests/test_agents_integration.py` | M3 - Thiện | M1/M2 cung cấp scenario qua comment |
| `configs/benchmark_w34.json` | M3 - Thiện | Cả nhóm duyệt giá trị |
| `core/engine/interfaces.py` | M3, chỉ khi có blocker đã được cả nhóm duyệt | M1/M2 không tự sửa |
| `core/engine/`, `ui/` | Không thuộc feature chính của sprint | Chỉ sửa bug riêng bằng PR nhỏ có owner review |

Quy tắc bổ sung:

- Không tạo một file helper chung trong `core/agents/` rồi để M1 và M2 cùng sửa trong tuần này.
- Nếu M1 cần utility riêng cho MCTS, đặt private trong `mcts_ai.py`.
- Nếu M2 cần evaluation dùng chung cho Heuristic và Minimax, M2 sở hữu helper đó trong một file của M2 hoặc giữ trong `heuristic_ai.py` với public import nội bộ rõ ràng.
- Agent không tự ghi log. Runner là nơi duy nhất tạo record và gọi logger.
- Mọi thay đổi contract phải merge trước feature code phụ thuộc vào thay đổi đó.

---

## 6. M1 - Trần Hồ Minh Hải

### W34-M1-01 - Hoàn thiện MCTS và benchmark trong một task

Đây là task duy nhất của M1 trong sprint gộp. M1 đi xuyên suốt từ khung MCTS của Tuần 3 đến budget và profiling của Tuần 4.

#### Công việc cụ thể

1. Tạo cấu trúc Node nội bộ, lưu parent, action, children, visits, value sum và untried actions.
2. Cài Selection bằng UCT, xử lý node chưa thăm mà không chia cho 0.
3. Cài Expansion từ legal actions của clone.
4. Cài Simulation bằng rollout hợp lệ đến terminal hoặc giới hạn an toàn đã công bố.
5. Cài Backpropagation với dấu score đúng theo player ở root.
6. Đảm bảo mọi mô phỏng chạy trên clone, không mutation environment nhận vào.
7. Dùng RNG cục bộ tạo từ `SearchBudget.seed`.
8. Hỗ trợ `time_limit_ms`, `max_nodes` và `simulations`; dừng khi chạm giới hạn đầu tiên.
9. Trả `AgentDecision` có action legal, score, nodes, simulations và elapsed time.
10. Cùng state, seed và simulation budget phải cho cùng action và cùng thống kê logic.
11. Viết test cho từng phase và test end-to-end trên bàn 11x11.
12. Profile 100, 400 và 1000 simulations; ghi throughput và bottleneck, không tối ưu trước khi test correctness xanh.
13. Bàn giao agent factory hoặc constructor ổn định để M3 đưa vào runner.

#### Input

- `GameEnv`, `SearchBudget`, `AgentDecision` từ contract `caro-v2`.
- `CaroEnv.clone_env()`, `undo()`, `legal_actions()` và `result(player)`.
- Benchmark profile do M3 khóa trong Ngày 1.

#### Output

- `core/agents/mcts_ai.py`.
- `tests/test_mcts_ai.py`.
- `benchmarks/bench_mcts.py` nếu cần script benchmark riêng.
- Bảng nhỏ ghi simulations, elapsed time, simulations mỗi giây và action được chọn trên scenario cố định.

#### Tiêu chí hoàn thành

- MCTS có đủ bốn phase, không phải random agent đổi tên.
- Không mutation env gốc kể cả khi timeout hoặc phát sinh lỗi.
- Action luôn legal và terminal state bị từ chối.
- Seed tái lập được.
- `simulations` trong decision bằng số simulation hoàn tất.
- 100, 400 và 1000 simulations chạy qua cùng API.
- Test không phụ thuộc vào tốc độ tuyệt đối của một máy cụ thể.

#### Nhánh và commit đề xuất

- Nhánh: `feature/w34-mcts-hai`
- Commit:
  - `feat(mcts): add node uct expansion and rollout`
  - `feat(mcts): add backpropagation seed and search budgets`
  - `test(mcts): cover legality determinism and no mutation`
  - `perf(mcts): add simulation benchmark profiles`

---

## 7. M2 - Lê Thị Trúc Ly

### W34-M2-01 - Hoàn thiện Heuristic và Minimax/Alpha-Beta trong một task

Đây là task duy nhất của M2 trong sprint gộp. Evaluation và move ordering được thiết kế một lần để phục vụ cả Heuristic lẫn Minimax, tránh hai implementation lệch nhau.

#### Công việc cụ thể

1. Xây thứ tự Heuristic công khai: thắng ngay, chặn thua ngay, tạo hoặc chặn threat, ưu tiên vị trí trung tâm.
2. Định nghĩa tie-break deterministic, ví dụ row-major sau khi score bằng nhau.
3. Chỉ đọc `GameState.board` và public API; không gọi private rule method.
4. Trả `AgentDecision` với action legal, score và số candidate đã đánh giá trong `nodes`.
5. Cài Minimax giới hạn độ sâu với score theo player ở root.
6. Cài Alpha-Beta có tùy chọn bật hoặc tắt để phục vụ ablation sau này.
7. Dùng evaluation chung gồm tactical pattern, terminal score và ưu tiên vị trí.
8. Thêm move ordering để xét win, block và move score cao trước.
9. Hỗ trợ `max_depth`, `max_nodes` và `time_limit_ms`.
10. Nếu timeout giữa iteration, trả action từ depth đã hoàn tất gần nhất.
11. Đếm nodes nhất quán cho cả chế độ pruning bật và tắt.
12. So sánh pruning bật/tắt trên cùng state: action hoặc score phải tương thích; nodes có pruning không được tăng vô lý.
13. Profile depth 2, 3 và 4 trên scenario cố định 11x11.
14. Bàn giao constructor hoặc factory rõ ràng cho M3.

#### Input

- Public contract `caro-v2`.
- Engine clone/undo đã kiểm thử.
- Các tactical scenario do M2 tự tạo trong test riêng.
- Benchmark profile do M3 khóa.

#### Output

- `core/agents/heuristic_ai.py`.
- `core/agents/minimax_ai.py`.
- `tests/test_heuristic_ai.py`.
- `tests/test_minimax_ai.py`.
- `benchmarks/bench_minimax.py` nếu cần.
- Bảng depth, pruning on/off, nodes, elapsed time và selected action.

#### Tiêu chí hoàn thành

- Heuristic chọn nước thắng ngay trước mọi ưu tiên khác.
- Heuristic chặn được nước thắng ngay của đối thủ khi không có nước thắng cho mình.
- Minimax không mutation env gốc.
- Alpha-Beta bật/tắt qua cấu hình, không tách thành hai codebase.
- Move ordering không làm thay đổi legal action hoặc kết quả terminal.
- Depth 2, 3 và 4 chạy qua cùng API; nếu depth cao chạm time budget phải dừng an toàn.
- Test có X/O, biên bàn và ít nhất một scenario nhiều candidate.

#### Nhánh và commit đề xuất

- Nhánh: `feature/w34-search-ly`
- Commit:
  - `feat(heuristic): add win block threat and center policy`
  - `feat(search): add depth limited minimax evaluation`
  - `feat(search): add alpha beta move ordering and budgets`
  - `test(search): cover tactics pruning counters and no mutation`
  - `perf(search): add depth benchmark profiles`

---

## 8. M3 - Trương Văn Thiện

### W34-M3-01 - Random baseline, metrics, runner và integration trong một task

Đây là task duy nhất của M3 trong sprint gộp. M3 sở hữu toàn bộ đường đi từ baseline đến record và smoke tournament, nhờ đó M1/M2 không phải cùng sửa runner hoặc logger.

#### Công việc cụ thể

1. Cài `RandomAgent` chọn đều trong legal actions bằng RNG cục bộ.
2. Seed phải tái lập, terminal hoặc legal actions rỗng phải raise `RuntimeError`.
3. Trả `AgentDecision`; Random có `nodes=0` và `simulations=0`.
4. Xây runner chạy một game từ reset đến terminal bằng hai object thỏa `Agent`.
5. Chuyển budget từ profile vào mỗi lần `choose_action`.
6. Đo wall time độc lập và đối chiếu với `decision.elapsed_ms`.
7. Validate action agent trả về trước khi gọi `env.step()`; lỗi agent phải có thông báo gồm agent, ply và action.
8. Ghi `MoveRecord` cho từng ply và `GameRecord` cho toàn game.
9. Logger serialize action thành `[row, col]`, player thành số và file UTF-8.
10. Chạy match nhiều game, đổi bên X/O và phân phối seed xác định.
11. Tổng hợp smoke metrics: W/D/L, số move, mean move time, p95 move time, total nodes và simulations.
12. Tạo budget enforcer: ghi vi phạm và có chế độ fail-fast cho test.
13. Viết common contract tests áp cho Random, Heuristic, Minimax và MCTS mà không sửa file test riêng của M1/M2.
14. Tạo file benchmark config duy nhất; không để mỗi agent hard-code budget riêng.
15. Sau khi M1/M2 merge, rebase và chạy smoke tournament qua tất cả agent.
16. Ghi report integration ngắn gồm seed, profile, số game và đường dẫn log.

#### Input

- `Agent`, `SearchBudget`, `AgentDecision`, `MoveRecord`, `GameRecord`.
- `CaroEnv` factory.
- Agent factory do M1 và M2 bàn giao.
- Profile FAST, FAIR, MCTS-S và AB-D.

#### Output

- `core/agents/random_ai.py`.
- `core/utils/logger.py`.
- `core/utils/tournament_runner.py`.
- `tests/test_random_ai.py`.
- `tests/test_tournament_runner.py`.
- `tests/test_agents_integration.py`.
- `configs/benchmark_w34.json`.
- Log smoke trong thư mục artifact được `.gitignore` đúng quy định; chỉ commit fixture nhỏ khi cần.

#### Tiêu chí hoàn thành

- RandomAgent deterministic theo seed và không mutation env.
- Runner không import private implementation của từng agent.
- Cùng config và seed tạo cùng chuỗi action khi các agent deterministic.
- Mỗi game đổi đúng player theo state, dừng đúng terminal và record đủ ply.
- JSONL round-trip không mất action, player, reward hoặc metric.
- Đổi X/O hoạt động và không gộp nhầm thống kê hai bên.
- Budget violation có thể quan sát, không bị bỏ qua im lặng.
- Smoke tournament chạy được Random, Heuristic, Minimax/Alpha-Beta và MCTS.

#### Nhánh và commit đề xuất

- Nhánh baseline: `feature/w34-runner-thien`
- Nhánh integration sau khi agent merge: `integration/w34-agents-thien`
- Commit:
  - `feat(agent): add seeded random baseline`
  - `feat(eval): add game runner metrics and caro v2 logging`
  - `feat(eval): add budget enforcement and side balancing`
  - `test(eval): add agent contract and runner integration`
  - `chore(config): freeze week 34 benchmark profiles`

---

## 9. Dependency và thứ tự merge

Ba feature implementation có thể làm song song vì file ownership tách biệt. Integration không được merge trước agent.

```text
0. Cả nhóm: baseline Tuần 2 xanh, Agent contract được xác nhận
        |
        +-------------------+-------------------+
        |                   |                   |
1A. M1: MCTS          1B. M2: Heuristic   1C. M3: RandomAgent
    correctness           + Minimax             + runner skeleton
        |                   |                   |
2A. M1: budget        2B. M2: Alpha-Beta   2C. M3: logger + metrics
    + profiling            + profiling          + budget enforcer
        |                   |                   |
        +-------------------+-------------------+
                            |
3. Merge M3 Random baseline -> M2 Search -> M1 MCTS
                            |
4. M3 rebase integration, nối tất cả agent vào runner
                            |
5. Full regression + smoke benchmark + review chéo
                            |
6. Cả nhóm xác nhận tag nội bộ agents-v1
```

### 9.1. Bảng merge cụ thể

| Thứ tự | PR | Người mở | Reviewer bắt buộc | Điều kiện merge |
|---:|---|---|---|---|
| 1 | RandomAgent và contract smoke nhỏ | M3 | M1, M2 | Legal, seed, no mutation xanh |
| 2 | Heuristic và Minimax/Alpha-Beta | M2 | M3, M1 | Tactical tests và pruning tests xanh |
| 3 | MCTS hoàn chỉnh | M1 | M3, M2 | Four phases, seed, budget và no mutation xanh |
| 4 | Runner, logger, config, integration | M3 | M1, M2 | Tất cả agent chạy chung runner |
| 5 | Integration fix nhỏ nếu có | Đúng owner file lỗi | Hai owner còn lại | Không đổi contract âm thầm |
| 6 | Tag `agents-v1` | M3 | Cả nhóm | Full test xanh và report smoke có đủ seed/config |

### 9.2. Quy tắc rebase và xử lý conflict

- Mỗi nhánh tạo từ cùng commit baseline đã được nhóm ghi lại.
- Trước khi mở PR, rebase lên branch tích hợp mới nhất; không merge branch tích hợp ngược vào feature branch.
- Nếu conflict nằm trong file của người khác, dừng và gọi đúng owner giải quyết.
- Không dùng `git checkout --theirs` hoặc `--ours` cho contract, test hoặc config nếu chưa review từng thay đổi.
- Integration fix phải nằm trong commit riêng, không amend vào commit feature đã review.
- Không format hàng loạt file ngoài ownership trong cùng PR.

---

## 10. Lịch tăng tốc trong một tuần

| Ngày | M1 - Hải | M2 - Ly | M3 - Thiện | Gate cuối ngày |
|---|---|---|---|---|
| Ngày 1 | Node, UCT, Selection, Expansion | Heuristic win/block và tie-break | Freeze API/budget, RandomAgent, runner interface | Tất cả agent skeleton import được; không đổi contract |
| Ngày 2 | Rollout, Backpropagation, no-mutation tests | Threat/center, evaluation, Minimax depth-limited | Single-game runner, validation, MoveRecord | Random/Heuristic/MCTS basic smoke xanh |
| Ngày 3 | Seed, simulations/max_nodes/time budget | Alpha-Beta, move ordering, counters | Logger JSONL, metrics, đổi bên, budget enforcer | M1/M2 mở draft PR; M3 runner test xanh với dummy agents |
| Ngày 4 | Profile 100/400/1000 simulations, fix review | Profile depth 2/3/4, pruning on/off, fix review | Merge Random baseline, review M1/M2, khóa config | Ba agent PR đủ test và benchmark output nhỏ |
| Ngày 5 | Review runner và smoke MCTS | Review runner và smoke search agents | Rebase integration, smoke tournament, full tests, report | Full regression xanh; cả nhóm ký checklist |
| Cuối tuần dự phòng | Chỉ sửa blocker/bug | Chỉ sửa blocker/bug | CI, tài liệu integration | Không thêm thuật toán hoặc scope mới |

### 10.1. Điểm đồng bộ bắt buộc

- **Sáng Ngày 1:** họp 60 phút khóa API, semantics score/nodes/simulations và budget precedence.
- **Cuối Ngày 2:** demo mỗi agent chọn một action legal trên cùng fixture 11x11.
- **Cuối Ngày 3:** review chéo no-mutation và deterministic seed.
- **Cuối Ngày 4:** không còn thay đổi public API; feature PR chuyển sang review/fix.
- **Chiều Ngày 5:** chạy integration từ checkout sạch, lưu command và kết quả.

---

## 11. Ma trận test bắt buộc

| ID | Nhóm | Kịch bản | Expected | Owner |
|---|---|---|---|---|
| W34-T01 | Common | Agent nhận terminal env | Raise `RuntimeError` | M3 |
| W34-T02 | Common | Agent nhận env đang chơi | Action thuộc legal actions | M3 |
| W34-T03 | Common | Snapshot trước/sau choose_action | Env bằng nhau | M3 |
| W34-T04 | Common | Cùng state, budget, seed | Kết quả tái lập với agent stochastic | M3 |
| W34-T05 | Random | Nhiều seed trên legal actions | Không trả action invalid | M3 |
| W34-T06 | Random | Cùng seed | Cùng action | M3 |
| W34-T07 | Heuristic | Có nước thắng ngay | Chọn thắng | M2 |
| W34-T08 | Heuristic | Không thắng, đối thủ sắp thắng | Chọn block | M2 |
| W34-T09 | Heuristic | Nhiều move cùng tactical score | Tie-break deterministic | M2 |
| W34-T10 | Heuristic | Scenario threat và center | Đúng thứ tự ưu tiên công bố | M2 |
| W34-T11 | Minimax | Terminal leaf X/O/draw | Score đúng góc nhìn root | M2 |
| W34-T12 | Minimax | Pruning on/off cùng state | Action/score tương thích | M2 |
| W34-T13 | Minimax | `max_depth=2/3/4` | Không vượt depth | M2 |
| W34-T14 | Minimax | Giới hạn nodes/time | Dừng an toàn, action legal | M2 |
| W34-T15 | MCTS | UCT node chưa thăm | Không chia 0, ưu tiên explore | M1 |
| W34-T16 | MCTS | Expansion | Chỉ tạo child legal, không trùng | M1 |
| W34-T17 | MCTS | Rollout | Kết thúc ở terminal hoặc guard hợp lệ | M1 |
| W34-T18 | MCTS | Backpropagation | Visits/value cập nhật đúng đường đi | M1 |
| W34-T19 | MCTS | 100/400/1000 simulations | Counter đúng số hoàn tất | M1 |
| W34-T20 | MCTS | Cùng seed và simulation budget | Cùng action | M1 |
| W34-T21 | Runner | Một game hai agent | Dừng terminal, record đủ ply | M3 |
| W34-T22 | Runner | Agent trả action invalid | Lỗi rõ agent, ply, action | M3 |
| W34-T23 | Runner | Hai game đổi bên | X/O được hoán đổi đúng | M3 |
| W34-T24 | Logger | JSONL UTF-8 round-trip | Không mất field | M3 |
| W34-T25 | Metrics | Decision có nodes/simulations | Tổng hợp đúng | M3 |
| W34-T26 | Budget | Agent vượt tolerance | Runner ghi/fail theo mode | M3 |
| W34-T27 | Integration | Random, Heuristic, Minimax, MCTS | Cùng chạy qua một runner | M3 |
| W34-T28 | Regression | Engine và UI suite | Không có test cũ bị vỡ | Cả nhóm |
| W34-T29 | Scope | Tìm literal 9 hoặc 81 trong agent | Không hard-code phạm vi cũ | M3 |
| W34-T30 | Contract | Public action từ agent | Luôn là tuple `(row, col)` | Cả nhóm |

---

## 12. Benchmark và smoke tournament

### 12.1. Scenario benchmark

M3 tạo tối thiểu ba state cố định bằng chuỗi action public:

1. **Opening:** bàn trống hoặc 2 nước đầu, dùng để đo branching lớn.
2. **Midgame tactical:** có win hoặc block trong 1 đến 2 ply.
3. **Midgame mixed:** nhiều candidate, chưa có thắng ngay.

Không dựng state bằng cách sửa board nội bộ. Fixture phải tạo qua `CaroEnv.step()` hoặc helper public.

### 12.2. Output benchmark tối thiểu

| Agent | Profile | Seed | Action | Score | Elapsed ms | Nodes | Simulations |
|---|---|---:|---|---:|---:|---:|---:|
| Random | FAST | ... | ... | ... | ... | 0 | 0 |
| Heuristic | FAST | ... | ... | ... | ... | ... | 0 |
| Minimax | AB-D | ... | ... | ... | ... | ... | 0 |
| MCTS | MCTS-S | ... | ... | ... | ... | ... | ... |

### 12.3. Smoke tournament

- Chỉ cần số game nhỏ để kiểm tra pipeline, ví dụ 2 đến 4 game mỗi cặp.
- Mỗi cặp phải đổi bên ít nhất một lần.
- Dùng seed cố định và lưu config cùng log.
- Không dùng smoke W/D/L để tuyên bố agent mạnh hơn.
- Nếu chạy quá lâu, giảm số game trước; không âm thầm giảm budget hoặc đổi luật.

---

## 13. Lệnh kiểm thử và cổng chất lượng

### 13.1. Test theo owner

```powershell
# M1
.\myenv\Scripts\python.exe -m pytest tests/test_mcts_ai.py -q -p no:cacheprovider

# M2
.\myenv\Scripts\python.exe -m pytest tests/test_heuristic_ai.py tests/test_minimax_ai.py -q -p no:cacheprovider

# M3
.\myenv\Scripts\python.exe -m pytest tests/test_random_ai.py tests/test_tournament_runner.py tests/test_agents_integration.py -q -p no:cacheprovider
```

### 13.2. Full regression

```powershell
.\myenv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
git diff --check
```

### 13.3. Coverage gợi ý cho code mới

```powershell
.\myenv\Scripts\python.exe -m pytest `
  tests/test_random_ai.py `
  tests/test_heuristic_ai.py `
  tests/test_minimax_ai.py `
  tests/test_mcts_ai.py `
  tests/test_tournament_runner.py `
  tests/test_agents_integration.py `
  --cov=core.agents `
  --cov=core.utils `
  --cov-report=term-missing
```

Cổng đề xuất:

- Overall code mới trong `core.agents` và `core.utils` đạt tối thiểu 85% statement coverage.
- `random_ai.py`, `heuristic_ai.py`, `logger.py` và `tournament_runner.py` hướng tới tối thiểu 90%.
- Không dùng coverage để thay thế test tactical, no-mutation và determinism.

### 13.4. Definition of Done cho mỗi PR

- Test thuộc ownership xanh.
- Full regression liên quan không bị vỡ.
- `git diff --check` không báo lỗi.
- Agent không mutation env gốc.
- Action trả về legal và đúng tuple public.
- Không hard-code 9x9 hoặc index 0 đến 80.
- Không thêm dependency mới nếu chưa được cả nhóm duyệt.
- PR ghi rõ budget, seed, scenario và lệnh test đã chạy.
- Benchmark artifact nhỏ; không commit log hoặc profile dung lượng lớn.
- Reviewer thuộc module downstream đã approve.

---

## 14. Rủi ro và phương án xử lý

| Rủi ro | Dấu hiệu | Cách xử lý | Owner |
|---|---|---|---|
| Branching 11x11 làm search quá chậm | Depth 2 hoặc 100 simulations đã vượt budget | Profile; move ordering/candidate ranking nội bộ; không sửa legal actions | M1, M2 |
| Score sai góc nhìn player | Agent chọn nước giúp đối thủ | Test X/O đối xứng và terminal leaf | M1, M2 |
| Mô phỏng làm đổi env thật | State khác sau choose_action | Clone-only và common no-mutation test | Cả nhóm |
| Time test flaky | CI lúc pass lúc fail | Test bằng node/simulation budget; time dùng tolerance | M3 |
| RNG global gây test phụ thuộc thứ tự | Cùng seed nhưng kết quả khác | `random.Random(seed)` cục bộ | M1, M3 |
| M1/M2 cùng tạo helper evaluation | Conflict hoặc hai semantics | M2 sở hữu evaluation search; MCTS giữ rollout private | M1, M2 |
| Mỗi agent tự log khác schema | JSON không ghép được | Agent chỉ trả decision; runner/logger do M3 sở hữu | M3 |
| Runner phụ thuộc class cụ thể | Thêm agent mới phải sửa nhiều nhánh | Chỉ nhận `Agent` protocol hoặc factory | M3 |
| Budget semantics không thống nhất | Nodes/sims không so sánh được | Khóa định nghĩa ở Ngày 1 và ghi trong config | M3 |
| Tối ưu làm sai thuật toán | Benchmark nhanh nhưng tactical test fail | Correctness gate trước profiling | Owner agent |
| PR quá lớn cuối tuần | Không đủ thời gian review | Commit theo phase; draft PR từ Ngày 2 | Cả nhóm |
| Contract đổi giữa sprint | Ba nhánh cùng phải sửa | M3 mở PR contract nhỏ trước feature, cả nhóm approve | M3 |

---

## 15. Checklist nghiệm thu sprint gộp

### Contract và kiến trúc

- [ ] Dùng `caro-v2` và 11x11 xuyên suốt.
- [ ] Không có public action dạng index phẳng.
- [ ] Mọi agent thỏa `Agent` protocol.
- [ ] Score, nodes, simulations và elapsed time có semantics thống nhất.
- [ ] Budget precedence đã được ghi và test.
- [ ] Agent không import private engine internals.

### M1 - MCTS

- [ ] Có Selection, Expansion, Simulation và Backpropagation.
- [ ] UCT xử lý đúng unvisited child.
- [ ] Seed tái lập.
- [ ] Time, nodes và simulation budget hoạt động.
- [ ] Decision có counters đúng.
- [ ] Profile 100/400/1000 simulations đã chạy.

### M2 - Heuristic và Alpha-Beta

- [ ] Heuristic thắng ngay trước block, threat và center.
- [ ] Tie-break deterministic.
- [ ] Minimax depth-limited đúng góc nhìn root.
- [ ] Alpha-Beta bật/tắt được.
- [ ] Move ordering và nodes counter hoạt động.
- [ ] Profile depth 2/3/4 đã chạy hoặc có ghi rõ giới hạn thực tế.

### M3 - Baseline và runner

- [ ] RandomAgent legal, seeded và no-mutation.
- [ ] Runner chạy đến terminal và đổi bên.
- [ ] Logger JSONL theo `caro-v2`.
- [ ] Metrics tổng hợp timer, nodes và simulations.
- [ ] Budget violation quan sát được.
- [ ] Config benchmark chỉ có một nguồn sự thật.
- [ ] Smoke tournament chạy tất cả agent.

### Test, Git và bàn giao

- [ ] Ma trận W34-T01 đến W34-T30 được cover hoặc ghi lý do loại trừ.
- [ ] Test mới đạt coverage gate đã thống nhất.
- [ ] Full engine/UI regression xanh.
- [ ] Merge đúng thứ tự ở Mục 9.
- [ ] Không có commit format hàng loạt file ngoài ownership.
- [ ] Có report smoke ghi seed, profile, số game và hardware.
- [ ] Cả ba thành viên review config và output.
- [ ] Chỉ tạo tag `agents-v1` sau khi integration xanh.

---

## 16. Điều kiện chuyển sang Tuần 5

Nhóm chỉ bắt đầu self-play và dữ liệu khi:

1. Bốn automated agent Random, Heuristic, Minimax/Alpha-Beta và MCTS chạy qua cùng runner.
2. Log game có schema ổn định và round-trip được.
3. Seed và budget được lưu cùng record hoặc manifest.
4. Không còn mutation env hoặc action invalid trong integration test.
5. Benchmark config đã freeze và có ít nhất một smoke run tái lập.

Nếu chưa đạt các điều kiện trên, không dùng output của runner để sinh dataset vì lỗi agent hoặc schema sẽ lan sang toàn bộ pipeline train ở Tuần 5 và Tuần 6.
