# Kế hoạch nâng cấp MCTS và xử lý lệch nhãn dataset

Tài liệu này dựa trên code hiện tại của repo `Caro_AI_Project`, kết quả kiểm tra
2.000 ván trong `Selfplay_2000_Recheck_Report.md`, cấu hình
`configs/benchmark.json`, `configs/selfplay_w56_dataset_v1.json` và pipeline tại
`core/ml/data_pipeline.py`.

Mục tiêu là tạo một luồng cải tiến có thể triển khai và kiểm chứng theo từng
giai đoạn, thay vì chỉ tăng số simulations rồi sinh lại dataset ngay lập tức.

## 1. Mục tiêu

1. Làm cho MCTS thực sự đi vào Selection/UCT và tái thăm các action tốt.
2. Tăng sức mạnh tactical mà vẫn giữ tính tái lập theo seed và contract
   `caro-v2`.
3. Giảm chi phí clone, `legal_actions()` và rollout không cần thiết.
4. Chỉ cho phép MCTS tham gia sinh dữ liệu sau khi vượt quality gate.
5. Cân bằng dataset theo **sample sau dedup**, không chỉ theo số game.
6. Phát hiện trạng thái có nhãn xung đột, leakage và teacher chất lượng thấp.
7. Version hóa dataset mới; không ghi đè hoặc trộn âm thầm với dataset v1.

## 2. Baseline và hạn chế hiện tại

### 2.1. Kết quả baseline

| Cặp | Kết quả hiện tại |
|---|---|
| Heuristic vs MCTS-20 | Heuristic thắng 666/666 |
| Minimax-D2 vs MCTS-20 | Minimax thắng 666/666 |
| Heuristic vs Minimax-D2 | Heuristic thắng 334, hòa 334 |

MCTS thua 1.332/1.332 ván. Ván dài nhất trong hai matchup có MCTS chỉ đạt 34
ply, tức ở mọi lượt MCTS vẫn còn ít nhất 87 action hợp lệ.

### 2.2. MCTS-20 không đi vào Selection/UCT

`core/agents/mcts_ai.py` hiện hoạt động theo thứ tự:

1. Tạo root chứa toàn bộ legal actions.
2. Mỗi simulation mở đúng một child chưa thử.
3. Chỉ Selection bằng UCT khi `untried_actions` đã rỗng.
4. Chọn robust child theo visit, mean value, rồi row-major.

Với 20 simulations nhưng luôn có hơn 20 action hợp lệ, root không bao giờ mở
hết action. Mỗi child chỉ nhận một rollout, visit count bằng nhau và UCT không
được dùng. Thuật toán thực tế trở thành:

```text
lấy mẫu 20 action khác nhau
        -> mỗi action chạy 1 rollout ngẫu nhiên
        -> chọn reward tốt nhất
        -> nếu hòa thì ưu tiên tọa độ row-major
```

Đây là nguyên nhân quan trọng nhất; tăng từ 20 lên 40 hoặc 100 simulations trên
root 121 action vẫn chưa giải quyết triệt để nếu không thay cách mở rộng.

### 2.3. Rollout có tín hiệu chiến thuật rất thấp

`_rollout()` dùng `rng.choice(legal)` trên toàn bàn, không ưu tiên:

- thắng ngay;
- chặn thua ngay;
- action gần cụm quân;
- open-three/open-four;
- center hoặc policy prior.

Reward chỉ xuất hiện khi rollout kết thúc. Một rollout ngẫu nhiên dài trên bàn
11 x 11 có phương sai cao và rất ít liên hệ với chất lượng action ở root.

### 2.4. Chi phí thực thi chưa tối ưu

- Mỗi simulation gọi `env.clone_env()` lại từ đầu.
- `_expand()` gọi `legal_actions()` để kiểm tra action rồi gọi thêm lần nữa để
  tạo child.
- Không tái sử dụng cây giữa hai ply thực tế.
- Không cache candidate/tactical information của node.
- Benchmark hiện đo end-to-end throughput nhưng chưa tách chi phí clone,
  `step`, `undo`, `legal_actions`, expansion và rollout.

### 2.5. Test và benchmark chưa đo sức mạnh

`tests/test_mcts_ai.py` kiểm tra UCT, expansion, rollout, counter, budget,
reproducibility và no-mutation. Các test này xác nhận contract, không xác nhận
MCTS chọn đúng win/block hoặc đủ mạnh trong tournament.

`benchmarks/bench_mcts.py` đo action, elapsed time và simulations/second trên
một scenario. Script chưa đo win rate, score rate, side bias hoặc tactical
accuracy.

### 2.6. Hạn chế của dataset v1

Pipeline hiện tại:

- tạo hard target `row * 11 + col` từ mọi nước đi;
- giữ cả nước đi của bên thắng, hòa và thua;
- lưu `source_agent` trong metadata nhưng không xuất `sample_weight`;
- cân bằng game gần đều nhưng không cân bằng số sample sau dedup;
- hash dedup gồm cả state **và target**;
- chỉ báo cáo tổng sample, chưa báo cáo theo teacher/matchup/game phase;
- D4 augmentation nhân tám train sample nhưng không làm tăng thông tin độc lập.

Vì target nằm trong `_sample_hash()`, cùng một state có hai action khác nhau
không bị coi là trùng. Hai nhãn xung đột này có thể nằm ở hai split khác nhau mà
`cross_split_game_overlap = 0` vẫn không phát hiện được position leakage.

Dataset v1 đã loại khoảng 82% sample trùng. Điều này cho thấy 2.000 game không
tương đương 2.000 trajectory độc lập.

## 3. Luồng nâng cấp tổng thể

```text
Đóng băng baseline và seed
        ↓
Tactical gate: win ngay / block bắt buộc
        ↓
Candidate ranking + progressive widening
        ↓
UCT tái thăm child + rollout có hướng dẫn
        ↓
Tối ưu clone/undo/cache, sau đó mới cân nhắc tree reuse
        ↓
Unit test + tactical suite + profiler + ablation
        ↓
Tournament đổi bên với nhiều seed
        ↓
MCTS đạt quality gate?
   ├── Không: không dùng làm teacher, tiếp tục tuning
   └── Có
        ↓
Sinh pilot dataset có random opening
        ↓
Quality filter + position-level leakage guard
        ↓
Cân bằng theo source sau dedup / tạo soft target
        ↓
Validation theo teacher, phase, matchup và side
        ↓
Sinh dataset version mới + data card mới
```

Không được bỏ qua quality gate để tăng số game. Nhiều game từ teacher yếu chỉ
làm sai lệch nhãn nhanh hơn.

## 4. Thiết kế MCTS đề xuất

### 4.1. Giai đoạn A — Tactical gate

Trước khi tạo tree:

1. Nếu có action thắng ngay, trả action đó.
2. Nếu đối thủ có đúng một action thắng ngay, bắt buộc block.
3. Nếu có nhiều threat bắt buộc, đưa toàn bộ vào nhóm ưu tiên cao nhất.

Có thể tái sử dụng `cell_potential()` từ `heuristic_ai.py` ở bước đầu, nhưng nên
tách kiểm tra win/block thuần luật sang helper chung như
`core/agents/search_utils.py`. Không nên dùng toàn bộ `action_priority()` làm
quyết định cuối, vì như vậy MCTS và Heuristic tiếp tục có cùng bias.

Tactical gate phải deterministic và luôn chạy trước mọi giới hạn simulation.
Ngay cả profile UI nhỏ cũng không được bỏ qua nước thắng/chặn hiển nhiên.

### 4.2. Giai đoạn B — Candidate ordering và progressive widening

Không mở 121 action đồng đều. Xếp action thành các tầng:

1. immediate win/block;
2. action trong bán kính Chebyshev 2 quanh quân hiện có;
3. action tạo/chặn threat;
4. các legal action còn lại theo thứ tự seeded để vẫn giữ khả năng khám phá.

Áp dụng progressive widening:

```text
allowed_children(N) = min(|A|, max(1, ceil(c_pw * (N + 1)^alpha)))
```

Giá trị khởi đầu để benchmark, không phải hằng số cuối cùng:

- `c_pw = 2.0`;
- `alpha = 0.5`;
- root candidate ưu tiên tối đa ban đầu: 24–32;
- node sâu: 12–24 candidate ưu tiên.

Ví dụ với `c_pw = 2`, `alpha = 0.5`:

| Root visits | Child tối đa xấp xỉ | Visit trung bình/child |
|---:|---:|---:|
| 100 | 20 | 5 |
| 400 | 40 | 10 |
| 1.000 | 64 | 15,6 |

Như vậy UCT có cơ hội tái thăm action tốt thay vì dùng toàn bộ budget để mở
action mới. Tập action đầy đủ vẫn được giữ để progressive widening có thể mở
rộng dần; không xóa vĩnh viễn action ngoài vùng lân cận.

### 4.3. Giai đoạn C — Rollout policy có hướng dẫn

Đề xuất rollout epsilon-greedy:

```text
nếu có win ngay     -> chọn win
ngược lại có block  -> chọn block
ngược lại với xác suất 1 - epsilon
                     -> chọn action local/threat tốt
ngược lại            -> chọn legal action ngẫu nhiên
```

Giá trị thử nghiệm:

- `rollout_epsilon = 0.15` cho teacher;
- `rollout_epsilon = 0.25` cho evaluation diversity;
- ưu tiên action trong radius 2;
- vẫn dùng RNG cục bộ nhận từ `SearchBudget.seed`.

Không nên cắt rollout ở một horizon tùy ý rồi trả reward 0. Nếu cần rollout
ngắn để tăng throughput, phải có hàm leaf evaluation được chuẩn hóa về `[-1,1]`
và benchmark riêng ảnh hưởng bias. Việc dùng nguyên hàm evaluation của Minimax
sẽ làm ba teacher càng tương quan; cần ablation giữa random, tactical-local và
heuristic-evaluated rollout.

### 4.4. Giai đoạn D — Chọn action cuối

Giữ robust-child theo visit là hợp lý khi mỗi child đã được tái thăm. Bổ sung:

- `root_max_visits`;
- visit distribution;
- selected visit ratio;
- policy entropy;
- max tree depth;
- số tactical override.

Trong evaluation chọn action có visit cao nhất. Khi sinh nhãn soft policy, dùng
toàn bộ root visit distribution thay vì chỉ action cuối.

### 4.5. Giai đoạn E — Tối ưu hiệu suất

Thứ tự tối ưu đề xuất:

1. Profile để đo tỷ lệ thời gian của clone, legal action, rollout và rule check.
2. Clone một simulation environment rồi dùng `step()/undo()` để quay về root,
   thay vì clone lại toàn bộ ở mọi simulation.
3. Trong `_expand()`, lấy legal actions một lần và tái sử dụng.
4. Cache candidate ordering trong node.
5. Chỉ sau đó mới thêm tree reuse giữa các ply.

Tree reuse phải giữ contract reproducibility. Test hiện tại yêu cầu gọi lại
cùng state, seed và budget trên cùng agent cho cùng kết quả. Cách an toàn:

- nếu `move_count` và state key không tiến lên, reset tree và chạy lại từ seed;
- chỉ reuse khi state mới đúng là hậu duệ của root trước qua nước agent và nước
  đối thủ đã quan sát;
- nếu không khớp, bỏ cache;
- profile dataset/evaluation có thể đặt `reuse_tree = false` để kết quả không
  phụ thuộc lịch sử process;
- profile UI có thể bật reuse sau khi test đầy đủ.

## 5. Config đề xuất

### 5.1. Lưu ý tương thích

`MCTSAgent.__init__()` hiện chỉ nhận `name`, `exploration_weight`,
`default_simulations` và `seed`. Các key bên dưới là **config mục tiêu**, chỉ
được thêm vào JSON sau khi constructor và validation đã được cài đặt. Nếu thêm
config trước, `_build_participant()` sẽ báo `TypeError`.

### 5.2. Profile đề xuất

| Profile | Mục đích | Simulations | Candidate/expansion | Rollout | Time limit |
|---|---|---:|---|---|---|
| `MCTS-SMOKE` | unit/integration nhanh | 64 | PW, local priority | tactical-local | Không |
| `MCTS-UI` | tương tác | 100–200 | PW, root 16–24 | tactical-local | 150–300 ms |
| `MCTS-EVAL-400` | ablation chuẩn | 400 | PW, root 24–40 | tactical-local | Không |
| `MCTS-EVAL-1000` | strength benchmark | 1.000 | PW, root 32–64 | tactical-local | Không |
| `MCTS-TEACHER` | sinh dữ liệu | 1.000, tăng 2.000 nếu cần | PW | epsilon 0,15 | Không |

Dataset phải dùng simulation/node budget, không dùng time budget. Time budget
phụ thuộc phần cứng và có thể làm số simulation/nhãn khác nhau giữa hai lần
chạy.

### 5.3. Constructor options mục tiêu

```json
{
  "exploration_weight": 1.41421356237,
  "default_simulations": 1000,
  "tactical_precheck": true,
  "candidate_policy": "tactical_local_seeded",
  "neighbor_radius": 2,
  "progressive_widening_c": 2.0,
  "progressive_widening_alpha": 0.5,
  "rollout_policy": "epsilon_tactical_local",
  "rollout_epsilon": 0.15,
  "reuse_tree": false
}
```

Không tune tất cả tham số cùng lúc. Thứ tự ablation:

1. MCTS hiện tại 20/100/400/1.000.
2. Thêm tactical gate.
3. Thêm progressive widening.
4. Thêm guided rollout.
5. Tối ưu clone/undo nhưng giữ logic giống bước 4.
6. Cuối cùng mới tune exploration weight và tree reuse.

### 5.4. Self-play config mục tiêu

Tạo file mới, ví dụ `configs/selfplay_dataset_v2.json`; không sửa version của
dataset v1 tại chỗ.

```json
{
  "contract_version": "caro-v2",
  "run_id": "dataset-v2-mcts-quality-gated",
  "game_config": {"board_size": 11, "win_length": 5},
  "base_seed": 20261201,
  "swap_sides": true,
  "random_opening": {
    "enabled": true,
    "plies": [2, 4, 6],
    "radius_from_center": 3,
    "reject_terminal_or_forced_win": true
  },
  "agents": {
    "heuristic": {"factory": "core.agents.heuristic_ai:HeuristicAgent"},
    "minimax": {
      "factory": "core.agents.minimax_ai:MinimaxAgent",
      "options": {"alpha_beta": true, "default_depth": 2},
      "budget": {"max_depth": 2}
    },
    "mcts": {
      "factory": "core.agents.mcts_ai:MCTSAgent",
      "options": {
        "default_simulations": 1000,
        "tactical_precheck": true,
        "candidate_policy": "tactical_local_seeded",
        "progressive_widening_c": 2.0,
        "progressive_widening_alpha": 0.5,
        "rollout_policy": "epsilon_tactical_local",
        "rollout_epsilon": 0.15,
        "reuse_tree": false
      },
      "budget": {"simulations": 1000}
    }
  }
}
```

`random_opening` chưa tồn tại trong loader hiện tại. Khi cài đặt, opening phải
được sinh từ seed, replay được, ghi vào manifest và không tạo state terminal hay
forced win quá sớm. Các nước opening phải nằm trong raw move prefix để replay
đúng, nhưng phải có `opening_plies`/metadata riêng và bị loại khỏi teacher target;
nếu không, pipeline hiện tại sẽ gán nhầm các nước random đó cho agent X/O.

## 6. Benchmark và quality gate cho MCTS

### 6.1. Correctness gate

Phải pass trước mọi tournament:

- 100% chọn win-in-one trên tactical suite;
- 100% block forced loss-in-one;
- action luôn legal;
- không mutation environment;
- cùng state/seed/config cho cùng decision;
- counter simulations/nodes chính xác;
- root có child visit > 1 và tree depth >= 2 ở opening/midgame khi budget cho
  phép;
- rollout và progressive widening không vượt budget.

### 6.2. Efficiency gate

Mở rộng `benchmarks/bench_mcts.py` để xuất:

- median và p95 elapsed;
- simulations/second;
- tỷ lệ thời gian clone, legal action, selection, expansion, rollout;
- mean/max tree depth;
- root children và visits/child;
- peak memory nếu có profiler phù hợp.

Tối ưu chỉ được chấp nhận khi action/visit statistics giống nhau với cùng seed
hoặc khác biệt đã được giải thích bởi thay đổi thuật toán, không phải mutation.

### 6.3. Strength gate

Thêm tournament strength benchmark dùng `run_match()`:

- ít nhất 200 game/matchup ở pilot, đổi bên và ghép cùng seed;
- báo cáo win/draw/loss, score rate `(win + 0.5 * draw) / games`;
- báo cáo riêng as-X/as-O và chênh lệch hai bên;
- so sánh MCTS mới với MCTS-20, Heuristic và Minimax-D2;
- chạy các budget 100/400/1.000 để có learning curve theo compute.

Ngưỡng khởi đầu đề xuất:

| Gate | Điều kiện |
|---|---|
| So với MCTS-20 | MCTS mới thắng hoặc đạt score rate >= 70% trên 200 game |
| Tactical | Win/block accuracy = 100% |
| Side balance | Chênh score rate X/O <= 10 điểm phần trăm |
| Teacher eligibility | Score rate >= 35% trước **từng** Heuristic và Minimax-D2 |
| Stability | Kết luận giữ nguyên trên ít nhất 3 nhóm seed |

Ngưỡng 35% là gate pilot, không phải tuyên bố MCTS đã mạnh. Nếu không đạt thì
MCTS chưa được dùng làm teacher, dù throughput cao.

### 6.4. Ablation bắt buộc

| Biến thể | Mục đích |
|---|---|
| Baseline MCTS-20 | Mốc lỗi hiện tại |
| Sims 100/400/1.000, code cũ | Tách ảnh hưởng chỉ tăng compute |
| + tactical gate | Đo khả năng ngăn thua nhanh |
| + progressive widening | Chứng minh UCT được dùng |
| + guided rollout | Đo chất lượng reward estimate |
| + clone/undo optimization | Đo tốc độ với logic giữ nguyên |
| + tree reuse | Đo thêm lợi ích và rủi ro reproducibility |

## 7. Luồng xử lý lệch nhãn

### 7.1. Không cân bằng bằng số game đơn thuần

Một game 121 ply tạo nhiều sample hơn game 9 ply. Vì vậy 666 game mỗi cặp
không đồng nghĩa mỗi teacher đóng góp số nhãn bằng nhau. Cần báo cáo và cân bằng
theo sample tại các thời điểm:

1. raw moves;
2. sau quality filter;
3. sau dedup/aggregation;
4. sau split;
5. sau augmentation.

Mỗi báo cáo phải có breakdown theo:

- `source_agent`;
- matchup;
- win/draw/loss từ góc nhìn người đi;
- X/O;
- opening/midgame/endgame;
- tactical override/normal search;
- budget/profile/version của agent.

### 7.2. Quality filter trước cân bằng

Không nên oversample nhãn MCTS yếu chỉ để đủ 1/3. Trước hết loại hoặc giảm trọng
số các sample vi phạm tactical consistency:

- bỏ/downweight action bỏ lỡ nước thắng ngay;
- bỏ/downweight action không block forced loss;
- đánh dấu game có budget violation;
- từ chối game không replay được;
- không dùng run chưa đạt strength gate.

Không nên chỉ giữ nước của bên thắng. Cách đó tạo survivorship bias và loại các
state phòng thủ hữu ích. Outcome chỉ nên là một thành phần trọng số có giới hạn.

### 7.3. Position hash không chứa target

Tạo hai hash riêng:

```text
position_hash = hash(encoded_state, legal_mask)
label_hash    = hash(position_hash, target)
```

- `position_hash` dùng để phát hiện leakage và nhãn xung đột.
- `label_hash` dùng để đếm duplicate hoàn toàn.
- cùng `position_hash`, khác target phải được ghi nhận là conflict, không coi là
  hai sample độc lập không liên quan.

Để tránh leakage, validation/test phải loại hoặc group mọi position đã xuất hiện
ở train, bất kể target có giống nhau hay không. Tốt hơn nữa, group các game có
chung position vào cùng split; nếu chưa triển khai graph grouping, ít nhất dùng
train-priority position hash và báo cáo số position bị loại khỏi val/test.

### 7.4. Hai mức nâng cấp dataset

#### Mức 1 — Dataset v1.1 tương thích hard target

Giữ `target: int64`, bổ sung:

- `sample_weight: float32`;
- `position_hash` trong metadata;
- source-balanced sampler hoặc source weight;
- tactical quality flag;
- báo cáo conflict và leakage theo position;
- stratified split theo matchup/outcome/side ở cấp game.

Trọng số khởi đầu để thử nghiệm:

```text
sample_weight = source_weight
              * outcome_weight
              * tactical_quality_weight
```

Candidate weights, phải tune bằng validation:

| Thành phần | Giá trị ban đầu |
|---|---:|
| thắng | 1,00 |
| hòa | 0,75 |
| thua nhưng không tactical blunder | 0,50 |
| tactical blunder | 0,10 hoặc loại |
| source weight | target share / observed share, clip [0,5; 2,0] |
| weight cuối | clip [0,25; 4,0] |

Không đặt MCTS weight cao nếu MCTS chưa đạt quality gate. Cân bằng source chỉ
được thực hiện **sau** quality filtering.

#### Mức 2 — Dataset v2 dùng soft policy target

Đây là hướng khuyến nghị dài hạn. Với MCTS, nhãn nên là root visit distribution:

```text
pi(a) = N(a)^(1 / temperature) / sum_b N(b)^(1 / temperature)
```

- temperature cao hơn ở opening để giữ diversity;
- temperature thấp dần ở late game;
- action illegal có xác suất 0;
- lưu `policy_target: float32[121]` thay cho một hard action duy nhất.

Với cùng `position_hash`, aggregate các teacher distribution sau khi áp dụng
quality/source weights. Heuristic và Minimax có thể đóng góp one-hot target;
MCTS đóng góp visit distribution. Kết quả là một soft target phản ánh mức đồng
thuận/xung đột thay vì ghi nhiều hard label mâu thuẫn.

Pipeline hiện không lưu root visits trong `MoveRecord`; `AgentDecision.score`
cũng không được runner ghi xuống raw log. Có hai lựa chọn:

1. thêm sidecar `search_stats.jsonl` khóa bởi `(game_id, ply)`, giữ nguyên
   `caro-v2`; hoặc
2. nâng contract/schema để `MoveRecord` có optional policy statistics.

Sidecar ít phá vỡ tương thích hơn trong giai đoạn thử nghiệm. Manifest phải ghi
checksum và schema của sidecar.

### 7.5. Config dataset v1.1 đề xuất

```json
{
  "dataset_version": "dataset-v1.1-quality-weighted",
  "split_seed": 20261201,
  "dedup_key": "position_and_target",
  "leakage_key": "position_only",
  "train_d4_augmentation": true,
  "quality_filter": {
    "reject_budget_violation": true,
    "reject_missed_immediate_win": true,
    "missed_forced_block_weight": 0.1
  },
  "weights": {
    "win": 1.0,
    "draw": 0.75,
    "loss": 0.5,
    "source_balance": true,
    "source_weight_clip": [0.5, 2.0],
    "final_weight_clip": [0.25, 4.0]
  },
  "reports": {
    "by_source": true,
    "by_matchup": true,
    "by_phase": true,
    "label_conflicts": true,
    "position_leakage": true
  }
}
```

Các key này chưa được `build_dataset()` hỗ trợ; cần thêm validation trước khi
dùng config.

### 7.6. Acceptance criteria cho dataset mới

| Tiêu chí | Gate đề xuất |
|---|---|
| Replay/schema/checksum | 100% pass |
| Cross-split game overlap | 0 |
| Cross-split position overlap | 0 |
| Illegal target | 0 |
| Tactical blunder không được đánh dấu | 0 |
| Source share sau dedup, trước D4 | mỗi teacher mục tiêu 25–40%, hoặc giải thích rõ |
| Duplicate rate | mục tiêu < 30%; nếu cao hơn phải dừng và phân tích opening |
| Side imbalance | chênh sample X/O <= 10 điểm phần trăm |
| Báo cáo conflict | bắt buộc có count, entropy và top position |
| Validation | báo cáo overall và riêng theo source/matchup/phase |

Khoảng source share 25–40% chỉ áp dụng khi cả ba teacher đã qua quality gate.
Nếu MCTS chưa đạt gate, dataset nên dùng hai teacher tốt hơn hoặc giảm tỷ trọng
MCTS và ghi rõ trong data card, thay vì ép cân bằng giả tạo.

## 8. Thay đổi code theo file

| File | Thay đổi dự kiến |
|---|---|
| `core/agents/mcts_ai.py` | tactical gate, progressive widening, guided rollout, metrics, clone/undo optimization |
| `core/agents/search_utils.py` | helper win/block/candidate dùng chung, không chứa quyết định policy cuối |
| `tests/test_mcts_ai.py` | test tactical, root revisit, depth, PW, rollout policy, reuse/reset và deterministic seed |
| `benchmarks/bench_mcts.py` | profiler breakdown và tree statistics |
| `benchmarks/eval_mcts_strength.py` | tournament strength, side split, seed groups và ablation |
| `configs/benchmark.json` | profile mới, giữ profile cũ làm baseline |
| `scripts/generate_selfplay.py` | random opening seeded, agent version/profile trong manifest, optional search sidecar |
| `configs/selfplay_dataset_v2.json` | run mới; không sửa config v1 |
| `core/ml/data_pipeline.py` | position hash, quality flags, weights, source reports; sau đó soft policy target |
| `tests/test_data_pipeline.py` | position leakage, conflict, weight, source balance, soft target và checksum |
| `configs/train_dataset_v2.json` | quality/weight/split config có validation |
| `docs/data/Dataset_v2_Data_Card.md` | provenance, gates, distribution, limitations và checksums |

## 9. Lộ trình triển khai và điểm dừng

### Phase 0 — Baseline

- Lưu kết quả MCTS-20 và throughput hiện tại.
- Giữ các seed 11/22/33 và thêm tập seed tournament cố định.
- Không thay dataset v1.

**Done:** baseline tái lập được và có JSON report.

### Phase 1 — Tactical + progressive widening

- Cài tactical gate.
- Cài candidate tiers và PW.
- Thêm test root child được revisit và tree depth >= 2.

**Done:** correctness gate pass; MCTS không còn chỉ mở child root một lần.

### Phase 2 — Rollout + hiệu suất

- Cài epsilon tactical-local rollout.
- Profile và chuyển sang clone-once + undo nếu giữ nguyên logic.
- Chạy ablation 100/400/1.000 simulations.

**Done:** throughput không giảm ngoài ngưỡng đã chấp nhận và strength tăng có ý
nghĩa trên ba nhóm seed.

### Phase 3 — Strength tournament

- Chạy ít nhất 200 game/matchup ở pilot.
- Đổi bên, paired seeds, báo cáo score rate và p95 latency.

**Điểm dừng:** nếu không đạt teacher eligibility, không sinh dataset lớn.

### Phase 4 — Pilot data 300–600 game

- Bật random opening seeded.
- Sinh search sidecar nếu dùng soft target.
- Chạy full validation và báo cáo source/conflict/leakage.

**Điểm dừng:** duplicate rate, source share hoặc leakage không đạt thì sửa
pipeline/opening trước khi tăng game.

### Phase 5 — Dataset v2 đầy đủ

- Khóa code, config, seed policy và agent version.
- Sinh raw logs mới.
- Build tensor, checksum, data card và validation report.
- Chỉ sau đó mới huấn luyện và mở test split một lần theo quy trình.

## 10. Rủi ro và trade-off

| Rủi ro | Cách kiểm soát |
|---|---|
| Guided rollout làm MCTS giống Heuristic | ablation random/local/heuristic, chỉ dùng tactical bắt buộc ở gate |
| Candidate filter bỏ nước xa | progressive widening giữ full legal set |
| Tăng simulations làm sinh data quá chậm | profile clone/undo, chạy pilot, chọn budget theo strength/compute curve |
| Tree reuse phá reproducibility | state-key reset, test gọi lặp cùng state, tắt reuse ở teacher profile |
| Outcome weighting tạo survivorship bias | không loại toàn bộ nước thua, clip weight, validation theo outcome |
| Ép source balance làm phóng đại teacher yếu | quality gate trước source balancing |
| Random opening tạo position không tự nhiên | giới hạn vùng trung tâm, replay validation, loại terminal/forced-win opening |
| Soft label đổi format train | version schema, loader hỗ trợ song song hard/soft target, test checksum/shape |

## 11. Kết luận

Nút thắt hiện tại không chỉ là `simulations = 20`, mà là quan hệ giữa budget,
121 legal actions và chiến lược expansion. Nếu chỉ tăng game hoặc tăng nhẹ
simulations mà không làm root child được tái thăm, MCTS vẫn tạo nhãn nhiễu.

Thứ tự đúng là:

1. bảo đảm tactical correctness;
2. làm UCT thực sự hoạt động bằng progressive widening;
3. cải thiện rollout và hiệu suất;
4. chứng minh strength qua tournament;
5. mới cho MCTS qua quality gate để sinh dữ liệu;
6. xử lý nhãn theo position, source và confidence sau dedup;
7. chuyển sang soft visit-policy khi raw schema hỗ trợ.

Theo luồng này, dataset mới không chỉ “cân bằng số lượng”, mà cân bằng cả chất
lượng teacher, độ đa dạng trạng thái và mức tin cậy của nhãn.
