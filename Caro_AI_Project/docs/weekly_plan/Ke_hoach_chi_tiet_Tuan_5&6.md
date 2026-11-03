# Kế hoạch chi tiết gộp Tuần 5 và Tuần 6 - Self-play, dữ liệu và PolicyNet

> **Thời lượng:** 2 tuần, tương ứng 10 ngày làm việc chính.  
> **Phạm vi hiện hành:** Contract `caro-v2`, bàn cờ 11x11, public action `(row, col)`.  
> **Mục tiêu Tuần 5:** sinh dữ liệu self-play v1 có manifest, xây encoder và PolicyNet, khóa cấu hình teacher.  
> **Mục tiêu Tuần 6:** làm sạch và chia dữ liệu theo `game_id`, huấn luyện có kiểm định, xuất checkpoint, tích hợp Neural/Policy Agent.  
> **Nguyên tắc:** mỗi thành viên sở hữu một task xuyên suốt; script/module là nguồn thực thi chuẩn, notebook chỉ dùng để trình bày và gọi lại code đã kiểm thử.

---

## 1. Nguồn lập kế hoạch và cách gộp Tuần 5-6

Kế hoạch này được xây dựng từ:

- Kế hoạch triển khai tổng thể: Giai đoạn 3 - Dữ liệu và Mạng, Tuần 5-6.
- Roadmap 8 tuần: luồng `SELF-PLAY -> CLEAN -> SPLIT -> TRAIN -> EXPORT`.
- Kế hoạch chi tiết Tuần 1, Tuần 2 và sprint gộp Tuần 3-4.
- Trạng thái thực tế của repository tại thời điểm lập kế hoạch.
- Quyền sở hữu mã nguồn trong `PhanCongVaQuyTacLamViec.md`.

### 1.1. Ánh xạ roadmap vào sprint này

| Nội dung roadmap | Tuần 5 | Tuần 6 | Owner trong kế hoạch này |
|---|---|---|---|
| Self-play và dữ liệu | Schema trajectory, self-play runner, raw JSONL và manifest | Validate, dedup, split 70/15/15 theo game, data card và checksum | M3 - Thiện |
| Teacher/search | Tối ưu agent sinh nhãn, profile throughput và khóa cấu hình | Kiểm định chiến thuật PolicyAgent, đối chiếu với teacher | M2 - Ly |
| Neural policy | Board encoder, PolicyNet, masked loss và smoke forward/backward | Train loop, TensorBoard, checkpoint và Neural/Policy Agent | M1 - Hải |

Roadmap cũ ghi M2 thực hiện `PolicyAgent adapter`. Tuy nhiên quyền sở hữu hiện tại giao `core/agents/neural_ai.py` cho M1. Vì vậy sprint này phân công như sau:

- M1 cài đặt adapter trong `neural_ai.py`.
- M2 thiết kế tactical acceptance tests và đánh giá chất lượng adapter.
- M2 không sửa trực tiếp file thuộc ownership của M1.

### 1.2. Những việc không thuộc sprint

- Không chạy round-robin chính thức tối thiểu 100 ván/cặp; nội dung đó thuộc Tuần 7.
- Không tính Elo, Wilson interval hoặc kết luận agent nào mạnh nhất.
- Không xây Reinforcement Learning, PUCT hoặc AlphaZero-inspired loop.
- Không dùng NeuralAgent chưa huấn luyện để tuyên bố đã hoàn thành tác tử học được.
- Không dùng test set để chọn learning rate, số epoch, kiến trúc hoặc checkpoint.
- Không thay đổi luật Caro, encoding action, reward hoặc contract engine.
- Không mở lại phạm vi 9x9.

---

## 2. Baseline repository và cổng bắt đầu

### 2.1. Trạng thái hiện tại

| Hạng mục | Baseline đã có | Khoảng trống Tuần 5-6 |
|---|---|---|
| Engine và contract | `caro-v2`, bàn 11x11, clone/undo, action tuple | Freeze; không sửa nếu không có blocker được cả nhóm duyệt |
| Agents | Random, Heuristic, Minimax/Alpha-Beta, MCTS đã có code và test | Khóa teacher profile; đo throughput trước khi sinh dữ liệu lớn |
| Runner/logger | Có `play_game`, `run_match`, đổi bên, seed, `GameRecord`, JSONL và manifest | Bổ sung entry point self-play, resume, shard và manifest dataset |
| Benchmark config | Có `configs/benchmark.json` cho W3-4 | Cần config riêng cho self-play và training W5-6 |
| `core/ml/architectures.py` | File rỗng | Cần encoder, PolicyNet, masked logits/loss |
| `core/ml/data_pipeline.py` | File rỗng | Cần validate, replay, encode, dedup, split và export |
| `core/agents/neural_ai.py` | File rỗng | Cần load checkpoint, legal mask và trả `AgentDecision` |
| Notebook 01-03 | Đang rỗng | Cần notebook tái lập self-play, preprocessing và training |
| Dữ liệu/checkpoint | Chỉ có `.gitkeep` | Cần raw logs, `dataset-v1`, data card và `best.pt` cục bộ |
| Dependencies | Đã khai báo NumPy, Pandas, PyTorch, TensorBoard, scikit-learn | Cần smoke import và ghi version thực tế vào manifest |

### 2.2. Kết quả audit test khi lập kế hoạch

Lần chạy full suite ghi nhận `1726 passed`, `2 skipped` và `11 errors`. Toàn bộ 11 lỗi xảy ra ở bước tạo `tmp_path` vì môi trường chạy không có quyền truy cập thư mục tạm; không có assertion sản phẩm nào bị fail trong lần chạy đó.

Điều này **không được xem là cổng xanh hoàn chỉnh**. Trước khi sinh dữ liệu production, M3 phải chạy lại suite trong CI hoặc trên máy nhóm với thư mục tạm có quyền ghi và lưu kết quả không còn setup error.

### 2.3. Điều kiện bắt đầu dữ liệu production

Chỉ chạy batch self-play lớn khi đủ tất cả điều kiện:

1. Bốn agent chạy qua cùng `TournamentRunner` và không mutation environment.
2. Test logger round-trip và agent integration xanh trong môi trường có quyền ghi temp.
3. Cấu hình teacher, seed, budget và luật đã freeze trong file config.
4. Pilot self-play ít nhất 20 ván hoàn tất, replay lại được 100% và không có action invalid.
5. M1 xác nhận encoder đọc được một fixture raw và tạo tensor đúng shape.
6. M2 xác nhận teacher vẫn vượt các tactical tests bắt buộc.

Nếu chưa đạt cổng này, chỉ được chạy pilot để debug; không gắn nhãn `dataset-v1`.

---

## 3. Kết quả bắt buộc cuối Tuần 6

Cuối sprint, nhóm phải có một bản `model-v1` có thể tái lập với các kết quả sau:

- Tối thiểu 200 ván Heuristic vs MCTS hợp lệ, đổi bên cân bằng; mục tiêu 300 ván nếu thời gian cho phép.
- Không chọn riêng ván thắng. Mọi ván hợp lệ trong batch đã khai báo đều được giữ hoặc có lý do loại minh bạch trong manifest.
- Raw log dùng `GameRecord`/JSONL `caro-v2`, có manifest chứa config, seed, budget, agent, hardware, version thư viện và checksum.
- Mỗi game replay được từ board rỗng đến terminal; action, player, winner và số ply khớp log.
- Dataset được chia `70/15/15` theo `game_id`, không chia ngẫu nhiên từng state.
- Symmetry augmentation chỉ áp dụng cho tập train sau khi split; val/test không được phình bằng augmentation.
- Có báo cáo dedup và kiểm tra leakage giữa ba split.
- Có `dataset-v1` với checksum, thống kê số game/số sample/phân phối X-O/hòa/source agent và data card.
- PolicyNet nhận tensor `[N, 3, 11, 11]`, xuất logits `[N, 121]`.
- Loss và suy luận đều mask action bất hợp lệ trước khi chọn action hoặc tính phân phối.
- Train loop có seed, mini-batch, validation mỗi epoch, early stopping, TensorBoard/CSV history và checkpoint tốt nhất.
- Checkpoint chứa model state, model config, contract version, dataset checksum, training seed, epoch và validation metric.
- NeuralAgent tải được checkpoint, trả action legal, không mutation environment và chạy qua `TournamentRunner`.
- Có smoke training CPU trên fixture nhỏ và một production training run trên `dataset-v1`.
- Test hiện có của engine, UI và bốn agent cũ không bị regression.
- Tạo tag nội bộ `model-v1` chỉ sau khi checklist cuối sprint được cả nhóm xác nhận.

---

## 4. Quyết định kỹ thuật phải khóa trong Ngày 1

Ba thành viên họp tối đa 90 phút. M3 ghi decision note; M1 xác nhận model/loss; M2 xác nhận teacher profile và tactical acceptance.

### 4.1. Mục tiêu học

- Bài toán chính là **supervised policy learning** từ nước đi do Heuristic/MCTS sinh ra.
- Một sample biểu diễn trạng thái **trước nước đi** và nhãn là action thực tế của người đang đi.
- Baseline giữ toàn bộ nước đi hợp lệ từ cả hai teacher, có trường `source_agent` để phân tích.
- Không lọc chỉ các nước của bên thắng và không loại ván thua chỉ để làm metric đẹp hơn.
- Test set chỉ được mở để báo cáo một lần sau khi kiến trúc và checkpoint selection đã freeze bằng validation set.

### 4.2. State, label và legal mask

Encoder chuẩn cho bàn 11x11:

```text
x.shape = [3, 11, 11], dtype=float32

channel 0: quân của player đang đi
channel 1: quân của đối thủ
channel 2: ô trống/legal tại state hiện tại

legal_mask.shape = [121], dtype=bool
target = row * 11 + col, dtype=int64
```

Quy ước:

- Board luôn được chuẩn hóa theo góc nhìn player đang đi; model không phải đoán X hay O từ dấu số.
- `target` phải nằm trong `legal_mask`; sample vi phạm bị từ chối và ghi lỗi, không tự sửa nhãn.
- Chuyển đổi index chỉ dùng helper `action_to_index`/`index_to_action` của contract.
- Không hard-code 81 hoặc shape 9x9.

### 4.3. Model tối thiểu

- `PolicyNet` dạng CNN nhẹ, có 3-5 convolution blocks và policy head.
- Output là 121 logits thô; không đặt `softmax` trong `forward()`.
- Mask illegal logits bằng giá trị âm lớn trước `CrossEntropyLoss`/argmax.
- Kiến trúc và số channel được lưu trong config/checkpoint; không chỉ lưu `state_dict` rời.
- Production model phải chạy được trên CPU; GPU là tùy chọn tăng tốc, không phải điều kiện duy nhất để tái lập.

### 4.4. Self-play batch

| Hạng mục | Giá trị khóa |
|---|---|
| Cặp sinh dữ liệu | `HeuristicAgent` vs `MCTSAgent` |
| Pilot | 20 ván, đổi bên, dùng để kiểm schema và throughput |
| Production tối thiểu | 200 ván hợp lệ |
| Production mục tiêu | 300 ván nếu runtime đáp ứng |
| Đổi bên | Bắt buộc 50/50 X-O theo từng cặp seed |
| Seed | Danh sách cố định trong config; mỗi cặp đổi bên dùng cùng seed gốc |
| Budget | Teacher profile do M2 đề xuất và cả nhóm freeze sau pilot |
| Dữ liệu giữ lại | Toàn bộ game hợp lệ trong batch; không chọn theo winner |
| Lỗi/timeout | Ghi failed-game manifest; không âm thầm chạy lại bằng budget khác |

Nếu MCTS quá chậm, nhóm giảm **số game mục tiêu về mức tối thiểu 200** hoặc giảm budget bằng một thay đổi config có version. Không được âm thầm thay đổi budget giữa các shard.

### 4.5. Split, dedup và augmentation

- Dùng seed split cố định.
- Split danh sách `game_id` theo tỷ lệ 70% train, 15% validation và 15% test.
- Mọi state của một game chỉ thuộc đúng một split.
- D4 symmetry gồm quay 0/90/180/270 độ và phản chiếu; action/legal mask phải biến đổi cùng board.
- Chỉ augment train sau khi split.
- Dedup bằng hash của `(encoded_state, legal_mask, target)`; báo cáo số sample bị loại.
- Chạy cross-split leakage audit. Nếu cùng sample xuất hiện ở nhiều game khác split, ưu tiên train, loại bản sao khỏi val/test và ghi số lượng vào data card; không di chuyển từng state sang split khác.

### 4.6. Training và checkpoint selection

| Hạng mục | Giá trị mặc định |
|---|---|
| Loss | Masked cross entropy |
| Optimizer | Adam hoặc AdamW, giá trị cuối ghi trong config |
| Epoch tối đa | 30 |
| Early stopping | Patience 5 theo validation loss |
| Training seeds | `11`, `22`, `33` nếu tài nguyên cho phép; tối thiểu một production seed phải hoàn tất |
| Metric | Train/val loss, top-1, top-3 legal accuracy, learning rate, epoch time |
| Chọn checkpoint | Validation loss thấp nhất; không dựa vào test |
| Test evaluation | Chạy một lần sau khi chọn config/checkpoint |

---

## 5. Ownership để hạn chế conflict

| Khu vực | Owner ghi code chính | Người khác được làm gì |
|---|---|---|
| `core/ml/architectures.py` | M1 - Hải | M2 review shape/mask; M3 dùng public encoder contract |
| `core/agents/neural_ai.py` | M1 - Hải | M2 viết acceptance test ở file riêng; không sửa adapter |
| `scripts/train_policy.py` | M1 - Hải | M3 cung cấp dataset path/schema |
| `notebooks/03_Train_Model.ipynb` | M1 - Hải | Cả nhóm review output, không sửa trực tiếp |
| `tests/test_architectures.py`, `tests/test_neural_ai.py` | M1 - Hải | M2 bổ sung tactical acceptance trong file riêng |
| `core/agents/heuristic_ai.py`, `core/agents/minimax_ai.py` | M2 - Ly | Chỉ tối ưu có benchmark và không đổi contract |
| `benchmarks/bench_teacher_generation.py` | M2 - Ly | M3 gọi benchmark để chọn config |
| `configs/teacher_w56.json` | M2 - Ly | M1/M3 review và xác nhận trước production |
| `tests/test_policy_tactical.py` | M2 - Ly | M1 cung cấp factory/checkpoint fixture |
| `core/ml/data_pipeline.py` | M3 - Thiện | M1/M2 chỉ dùng public functions và review schema |
| `scripts/generate_selfplay.py`, `scripts/build_dataset.py` | M3 - Thiện | M2 cung cấp teacher config; M1 cung cấp encoder contract |
| `notebooks/01_SelfPlay_DataGen.ipynb`, `02_Data_Preprocessing.ipynb` | M3 - Thiện | Cả nhóm review số liệu |
| `configs/selfplay_w56.json`, `configs/train_w56.json` | M3 quản lý bản tích hợp | M2 đề xuất teacher fields; M1 đề xuất training fields |
| `tests/test_data_pipeline.py`, `tests/test_selfplay_generation.py` | M3 - Thiện | M1/M2 cung cấp fixture qua review |
| `core/utils/logger.py`, `tournament_runner.py` | M3 - Thiện, chỉ khi có blocker dữ liệu | M1/M2 không sửa trong feature PR |

Quy tắc bổ sung:

- M1 và M3 thống nhất encoder schema bằng test fixture trước khi viết hai implementation độc lập.
- Encoder logic chỉ có một nguồn trong `core/ml`; notebook không copy lại logic.
- M2 không tối ưu `mcts_ai.py`. Nếu profile phát hiện blocker trong MCTS, M1 sửa bằng PR bugfix nhỏ trước khi training.
- Không commit raw logs, tensors, checkpoints hoặc TensorBoard runs vì đã được `.gitignore` loại trừ.
- Chỉ commit config, schema, data card, checksum text, fixture nhỏ và code tái tạo artifact.

---

## 6. M1 - Trần Hồ Minh Hải

### W56-M1-01 - PolicyNet, huấn luyện và NeuralAgent trong một task

M1 sở hữu toàn bộ đường đi từ tensor đã chuẩn hóa đến checkpoint và agent suy luận. M1 không tự đọc JSONL theo schema riêng; dữ liệu đầu vào phải đi qua API của M3.

#### Công việc Tuần 5 - Encoder contract và PolicyNet

1. Cùng M3 viết fixture state/action và expected tensor cho encoder 3 channel.
2. Cài `PolicyNet` trong `core/ml/architectures.py` với board size/model config rõ ràng.
3. Kiểm tra forward shape `[N, 3, 11, 11] -> [N, 121]` cho batch 1 và batch nhiều sample.
4. Cài helper mask illegal logits; không cho softmax/argmax chọn ô đã có quân.
5. Cài masked cross-entropy và assert target là action legal.
6. Viết smoke forward/backward trên CPU; loss hữu hạn và gradient không NaN/Inf.
7. Tạo model config có số channel, số block, dropout nếu dùng và version kiến trúc.
8. Viết unit test cho shape, dtype, legal mask, loss và save/load state dict.
9. Chuẩn bị `notebooks/03_Train_Model.ipynb` ở mức import module, đọc dataset fixture và chạy một mini-batch; chưa train production khi dataset chưa freeze.

#### Công việc Tuần 6 - Train, checkpoint và adapter

1. Tạo `scripts/train_policy.py` nhận config, dataset directory, output directory, device và seed từ CLI.
2. Seed Python/NumPy/PyTorch; ghi rõ giới hạn determinism nếu dùng GPU.
3. Tạo DataLoader train/val/test; shuffle chỉ train.
4. Ghi train/val loss, top-1, top-3 legal accuracy, learning rate và epoch time ra TensorBoard và CSV/JSON.
5. Cài early stopping theo validation loss và lưu `last.pt`, `best.pt`.
6. Checkpoint phải chứa model config, state dict, optimizer state nếu cần resume, epoch, metric, contract version, dataset checksum và training seed.
7. Resume từ checkpoint phải tiếp tục đúng epoch/config; từ chối checkpoint sai board size, model version hoặc dataset checksum khi chạy production.
8. Chọn `best.pt` chỉ bằng validation loss; sau khi khóa mới chạy test evaluation một lần.
9. Cài `NeuralAgent`/`PolicyAgent` trong `core/agents/neural_ai.py`.
10. Adapter encode state theo góc nhìn current player, áp legal mask, chọn argmax deterministic và trả `AgentDecision`.
11. Agent phải chạy CPU, không mutation env, raise `RuntimeError` ở terminal và từ chối checkpoint không tương thích.
12. Bàn giao factory/constructor ổn định để M3 đưa vào runner Tuần 7.
13. Hoàn thiện notebook 03 với learning curve, config, dataset checksum và kết quả test cuối; notebook gọi code module/script, không chứa train loop thứ hai.

#### Input

- Schema tensor và `dataset-v1` do M3 bàn giao.
- `teacher_w56.json` và tactical fixtures do M2 bàn giao.
- Contract `Agent`, `AgentDecision`, `SearchBudget` hiện tại.
- PyTorch và TensorBoard trong `requirements.txt`.

#### Output

- `core/ml/architectures.py`.
- `core/agents/neural_ai.py`.
- `scripts/train_policy.py`.
- `notebooks/03_Train_Model.ipynb`.
- `tests/test_architectures.py`.
- `tests/test_neural_ai.py`.
- `configs/model_w56.json` hoặc phần model trong config tích hợp.
- `models/checkpoints/model-v1/best.pt` ở máy chạy, không commit Git.
- `runs/model-v1/` và training history ở máy chạy, không commit Git.
- Báo cáo ngắn về số tham số, device, thời gian train, best epoch, val/test metrics.

#### Tiêu chí hoàn thành

- Forward output đúng `[N, 121]` và không có NaN/Inf.
- Illegal action có xác suất chọn bằng 0 sau mask.
- Smoke training trên fixture nhỏ làm loss giảm hoặc chứng minh optimizer cập nhật tham số.
- Cùng checkpoint/state cho cùng action.
- NeuralAgent trả action thuộc `env.legal_actions()` và không mutation env.
- Checkpoint load lại cho logits/action giống trước khi save trong tolerance đã công bố.
- Training history và TensorBoard event có đủ train/val metrics.
- Test set không được đọc trong vòng lặp chọn kiến trúc/checkpoint.

#### Nhánh và commit đề xuất

- Nhánh Tuần 5: `feature/w56-policynet-hai`.
- Nhánh Tuần 6: tiếp tục cùng nhánh hoặc `feature/w56-train-neural-hai` sau khi architecture merge.
- Commit:
  - `feat(ml): add perspective board encoder contract and policy net`
  - `feat(ml): add legal masked policy loss`
  - `test(ml): cover policy shapes masks gradients and serialization`
  - `feat(train): add seeded supervised training and early stopping`
  - `feat(agent): add checkpoint backed neural policy agent`
  - `docs(notebook): add reproducible policy training workflow`

---

## 7. M2 - Lê Thị Trúc Ly

### W56-M2-01 - Tối ưu teacher, khóa cấu hình và kiểm định PolicyAgent

M2 bảo đảm dữ liệu được sinh bởi teacher đúng chiến thuật và đủ throughput, sau đó đóng vai trò acceptance owner cho NeuralAgent. M2 không sửa data pipeline hoặc neural adapter.

#### Công việc Tuần 5 - Teacher profiling và tối ưu an toàn

1. Chạy lại tactical suite của Heuristic, Minimax và MCTS trên cùng fixtures W3-4.
2. Đo throughput sinh nước và thời gian một ván cho Heuristic vs MCTS ở các simulation budget ứng viên.
3. Lập bảng so sánh tối thiểu các profile MCTS 50/100/200 simulations hoặc các mức khả thi từ pilot; ghi hardware và seed.
4. Xác định profile có cân bằng giữa chất lượng nhãn và thời gian để hoàn thành tối thiểu 200 ván.
5. Profile Heuristic; tối ưu evaluation/candidate cache thuộc file M2 nếu có bottleneck rõ.
6. Mọi cache phải dùng key bất biến từ state, không giữ tham chiếu mutable đến board và không làm kết quả phụ thuộc thứ tự game.
7. Chạy correctness trước/sau tối ưu: action legal, win/block priority, deterministic tie-break và no-mutation.
8. Không sửa MCTS; nếu MCTS là bottleneck, gửi profile cho M1 xử lý bằng PR riêng.
9. Ghi `configs/teacher_w56.json` gồm tên agent, constructor options, budget, seed policy và lý do chọn.
10. Bàn giao cấu hình teacher đã freeze cho M3 trước production self-play.

#### Công việc Tuần 6 - Tactical acceptance cho PolicyAgent

1. Xây bộ state tactical không trùng trực tiếp với sample test dùng để chọn model.
2. Kiểm tra NeuralAgent luôn trả action legal ở opening, midgame, gần full-board và state có forced win/block.
3. Phân biệt hai mức nghiệm thu:
   - **Bắt buộc:** legal, deterministic, terminal guard, no-mutation, load checkpoint đúng.
   - **Chất lượng tham khảo:** top-k có chứa win/block hoặc action teacher trên tactical boards.
4. Không yêu cầu NeuralAgent phải thắng mọi tactical case nếu dữ liệu chưa đủ; ghi failure case thay vì sửa expected cho pass.
5. Chạy mini match smoke NeuralAgent vs Random và NeuralAgent vs Heuristic, 2-4 ván mỗi cặp, chỉ để kiểm pipeline.
6. Ghi các ván lỗi điển hình, prediction top-5 và legal probabilities để M1 phân tích.
7. Xác nhận agent đủ điều kiện tham gia round-robin Tuần 7 về mặt contract, không tuyên bố sức mạnh từ smoke match.

#### Input

- Bốn agent và benchmark config của sprint W3-4.
- Runner/logger của M3.
- NeuralAgent factory và `best.pt` của M1.
- Hardware profile của máy sinh dữ liệu.

#### Output

- `benchmarks/bench_teacher_generation.py`.
- `configs/teacher_w56.json`.
- `tests/test_policy_tactical.py`.
- Báo cáo throughput trước/sau, simulations/second, game/hour và profile được chọn.
- Báo cáo tactical sanity gồm expected, top-k prediction, action thực tế và failure notes.

#### Tiêu chí hoàn thành

- Cấu hình teacher tái lập, không dùng global RNG.
- Không có correctness test W3-4 bị vỡ sau tối ưu.
- Profile cuối có ước lượng thời gian hoàn thành 200 và 300 game.
- Heuristic/MCTS vẫn không mutation env và trả action legal.
- Tactical acceptance không phụ thuộc vào đường dẫn checkpoint hard-code trên một máy.
- Smoke match NeuralAgent hoàn tất qua runner và tạo record hợp lệ.
- Mọi failure chất lượng được ghi trung thực; không thay fixture để che lỗi model.

#### Nhánh và commit đề xuất

- Nhánh: `perf/w56-teacher-policy-ly`.
- Commit:
  - `perf(search): profile self play teacher throughput`
  - `perf(heuristic): add safe evaluation cache if justified`
  - `chore(config): freeze week 56 teacher profile`
  - `test(neural): add legal and tactical policy acceptance`
  - `docs(eval): record teacher and policy sanity results`

---

## 8. M3 - Trương Văn Thiện

### W56-M3-01 - Self-play, data pipeline và dataset-v1 trong một task

M3 sở hữu đường dữ liệu từ runner đến raw log, tensor split và data card. M3 không tự cài PolicyNet hoặc sửa logic teacher.

#### Công việc Tuần 5 - Schema, self-play và raw data

1. Freeze raw schema dựa trên `GameRecord` `caro-v2`; state được tái dựng bằng replay action từ board rỗng.
2. Định nghĩa manifest gồm run id, thời điểm, contract, game config, agent config, budgets, seeds, hardware, package versions, số game yêu cầu/thành công/thất bại và checksum từng shard.
3. Tạo `scripts/generate_selfplay.py` gọi runner/logger public; không copy game loop riêng vào notebook.
4. Hỗ trợ pilot, production, output shard, resume và dry-run config validation.
5. Nếu dùng multiprocessing trên Windows, worker phải spawn-safe, seed không trùng và mỗi worker ghi shard riêng; tiến trình chính merge/manifest sau khi validate.
6. Game ID phải unique và ổn định từ run id, seed, side assignment và game index.
7. Chạy pilot 20 game, replay 100%, kiểm cân bằng side, winner distribution và budget violation.
8. Sau khi M2 freeze teacher config, chạy production tối thiểu 200 game; không thay config giữa shard.
9. Log failed games riêng với loại lỗi; failed game không được chèn nửa dòng vào raw JSONL.
10. Hoàn thiện `notebooks/01_SelfPlay_DataGen.ipynb` để đọc config, gọi script/module, hiển thị thống kê và đường dẫn artifact.

#### Công việc Tuần 6 - Validate, split, dedup và export

1. Cài loader streaming JSONL, validate `contract_version`, schema và checksum.
2. Replay từng game qua `CaroEnv`, đối chiếu player/action/terminal/winner và tạo sample trước mỗi move.
3. Encode sample theo contract Mục 4.2 và giữ metadata `game_id`, `ply`, `player`, `source_agent`, `winner`, `seed`.
4. Split theo danh sách `game_id` 70/15/15 bằng seed cố định; assert ba tập game rời nhau.
5. Chạy dedup, cross-split leakage audit và ghi số sample loại theo lý do.
6. Áp D4 augmentation cho train; biến đổi đồng bộ board, target và legal mask.
7. Export tensor và metadata theo định dạng ổn định, ví dụ `.npz`/`.pt` cho tensor và JSON/Parquet cho index; M1 không phải parse raw JSONL trong train loop.
8. Tính SHA-256 cho raw manifest, split files, tensor files và config.
9. Tạo data card mô tả nguồn, số game/sample, split, label policy, preprocessing, dedup, augmentation, hạn chế và nguy cơ học lại teacher.
10. Hoàn thiện `notebooks/02_Data_Preprocessing.ipynb` để hiển thị validation report, phân phối split và sample decode; không copy pipeline.
11. Bàn giao `dataset-v1` path, checksum và public loader API cho M1.
12. Viết integration test raw fixture -> replay -> split -> load batch.

#### Input

- Agent/runner/logger `agents-v1`.
- `teacher_w56.json` của M2.
- Encoder/sample contract đã thống nhất với M1.
- `configs/selfplay_w56.json` và split seed.

#### Output

- `core/ml/data_pipeline.py`.
- `scripts/generate_selfplay.py`.
- `scripts/build_dataset.py`.
- `notebooks/01_SelfPlay_DataGen.ipynb`.
- `notebooks/02_Data_Preprocessing.ipynb`.
- `configs/selfplay_w56.json` và `configs/train_w56.json` bản tích hợp.
- `tests/test_selfplay_generation.py`.
- `tests/test_data_pipeline.py`.
- `docs/data/Dataset_v1_Data_Card.md`.
- Raw data trong `data/raw_logs/w56_selfplay_v1/`, không commit Git.
- Processed data trong `data/processed_tensors/dataset_v1/`, không commit Git.
- Manifest và checksum bàn giao cùng artifact, chỉ commit bản data card không chứa dữ liệu lớn.

#### Tiêu chí hoàn thành

- Pilot và production đều có manifest đầy đủ, checksum khớp.
- 100% game được nhận vào dataset replay đến terminal và khớp winner.
- Không có action invalid, duplicate game ID hoặc game nằm ở nhiều split.
- Mỗi target thuộc legal mask của sample tương ứng.
- Split theo game đúng 70/15/15 trong sai số làm tròn đã công bố.
- Augmentation biến đổi action/mask đúng và chỉ áp lên train.
- Loader trả batch đúng dtype/shape và deterministic với cùng seed.
- Data card có số liệu thật, không để placeholder.

#### Nhánh và commit đề xuất

- Nhánh Tuần 5: `feature/w56-selfplay-thien`.
- Nhánh Tuần 6: `feature/w56-dataset-thien` sau khi raw schema merge.
- Commit:
  - `feat(data): add versioned self play generation and manifests`
  - `test(data): cover deterministic shards replay and resume`
  - `feat(data): add game grouped split dedup and symmetry`
  - `feat(data): export dataset v1 tensors metadata and checksums`
  - `test(data): cover leakage masks and replay invariants`
  - `docs(data): add dataset v1 data card and notebooks`

---

## 9. Dependency và thứ tự merge

Ba task có thể khởi động song song ở mức fixture/prototype, nhưng production phải theo dependency sau:

```text
0. Cả nhóm: W3-4 regression xanh trong môi trường có temp ghi được
        |
1. M3: raw/sample schema draft + fixture một game
        |
        +----------------------+----------------------+
        |                      |                      |
2A. M1: encoder + PolicyNet   2B. M2: teacher profile  2C. M3: pilot generator
        |                      |                      |
        +----------------------+----------------------+
                               |
3. M2 freeze teacher_w56 -> M3 chạy pilot 20 game và validate
                               |
4. M3 chạy production self-play -> build/freeze dataset-v1
                               |
5. M1 train smoke -> train production -> chọn best.pt bằng validation
                               |
6. M1 merge NeuralAgent -> M2 chạy tactical acceptance/smoke match
                               |
7. M3 chạy integration raw-to-agent + cả nhóm review data card/model card
                               |
8. Full regression -> freeze config/checksum -> tag model-v1
```

### 9.1. Bảng merge cụ thể

| Thứ tự | PR | Người mở | Reviewer bắt buộc | Điều kiện merge |
|---:|---|---|---|---|
| 1 | Schema sample/raw + fixture | M3 | M1, M2 | Replay được; tensor expectation được M1 xác nhận |
| 2 | PolicyNet + mask/loss tests | M1 | M2, M3 | Shape, gradient, illegal mask và serialization xanh |
| 3 | Teacher profile/config | M2 | M1, M3 | Tactical regression xanh; có throughput và ETA |
| 4 | Self-play pilot/generator | M3 | M1, M2 | 20 game replay 100%, manifest/checksum hợp lệ |
| 5 | Data pipeline + dataset-v1 | M3 | M1, M2 | Split theo game, leakage audit và loader xanh |
| 6 | Train loop + best checkpoint | M1 | M2, M3 | Smoke train xanh; config/checksum ghi đủ |
| 7 | NeuralAgent | M1 | M2, M3 | Agent contract, legal mask và no-mutation xanh |
| 8 | Tactical acceptance | M2 | M1, M3 | Smoke match chạy qua runner; failure report đầy đủ |
| 9 | Integration/tag `model-v1` | M3 | Cả nhóm | Full regression, data card, checkpoint metadata và checksum được duyệt |

### 9.2. Quy tắc xử lý thay đổi sau freeze

- Thay teacher budget sau production bắt buộc tạo run id/dataset version mới.
- Thay encoder channel/order bắt buộc tăng dataset/model schema version và build lại dataset.
- Thay split seed bắt buộc tạo split manifest mới; không ghi đè `dataset-v1` im lặng.
- Thay model config sau khi xem test metric không được dùng cùng test result để báo cáo chính.
- Integration fix nằm trong commit riêng và do đúng owner file thực hiện.

---

## 10. Lịch làm việc 10 ngày

| Ngày | M1 - Hải | M2 - Ly | M3 - Thiện | Gate cuối ngày |
|---|---|---|---|---|
| W5-D1 | Chốt tensor/model contract | Chốt candidate teacher budgets | Chốt raw/sample schema, manifest và run id | Decision note được cả ba duyệt |
| W5-D2 | PolicyNet forward + shape tests | Tactical regression + benchmark harness | Self-play CLI + deterministic game IDs | Fixture raw -> tensor expectation thống nhất |
| W5-D3 | Legal mask + loss + backward smoke | Profile teacher budgets, ETA 200/300 game | Pilot generator, shard/resume | Chọn được 1-2 profile khả thi |
| W5-D4 | Serialization + notebook smoke | Tối ưu Heuristic/cache nếu có bằng chứng | Chạy pilot 20 game, replay/manifest audit | Pilot 100% replay hoặc dừng sửa blocker |
| W5-D5 | Review pilot tensor, chuẩn bị train script | Freeze `teacher_w56.json` | Merge pilot PR, bắt đầu production | Teacher config freeze; không đổi âm thầm |
| W6-D1 | DataLoader/train loop + metrics | Chuẩn bị tactical acceptance fixtures | Hoàn tất production self-play | Đủ >=200 valid games và raw checksum |
| W6-D2 | Early stop/checkpoint/resume | Review data distribution/teacher source | Split, dedup, leakage audit, augmentation | `dataset-v1` candidate và data card draft |
| W6-D3 | Smoke train rồi production train | Viết policy contract/tactical tests | Freeze dataset checksum, loader integration | M1 train đúng checksum đã freeze |
| W6-D4 | NeuralAgent + best checkpoint test | Chạy tactical sanity và smoke match | Integration runner/logger/dataset checks | NeuralAgent chạy qua runner |
| W6-D5 | Learning curves + notebook/report | Failure analysis và acceptance report | Full regression, manifest tổng, chuẩn bị tag | Cả nhóm duyệt model-v1 hoặc ghi blocker |

### 10.1. Điểm đồng bộ bắt buộc

- **Sáng W5-D1:** họp 90 phút khóa schema, label policy, split và teacher candidates.
- **Cuối W5-D3:** xem benchmark teacher và ước lượng thời gian batch.
- **Cuối W5-D4:** xem pilot replay report; nếu có một game không replay được thì dừng production.
- **Cuối W5-D5:** freeze teacher config và production run id.
- **Cuối W6-D2:** freeze dataset checksum/split manifest trước khi production train.
- **Cuối W6-D3:** xác nhận test set chưa được dùng để chọn checkpoint.
- **Chiều W6-D5:** demo raw log -> dataset loader -> checkpoint -> NeuralAgent action -> runner.

---

## 11. Dataset contract chi tiết

### 11.1. Raw artifact

```text
data/raw_logs/w56_selfplay_v1/
├── run_manifest.json
├── shard_000.jsonl
├── shard_001.jsonl
├── ...
├── failed_games.jsonl
└── checksums.sha256
```

Mỗi dòng shard là một `GameRecord` hoàn chỉnh. Không ghi state tensor trực tiếp vào raw log vì có thể tái dựng từ action và giúp schema raw đơn giản hơn.

### 11.2. Processed artifact

```text
data/processed_tensors/dataset_v1/
├── dataset_manifest.json
├── train.npz hoặc train.pt
├── val.npz hoặc val.pt
├── test.npz hoặc test.pt
├── train_metadata.parquet hoặc jsonl
├── val_metadata.parquet hoặc jsonl
├── test_metadata.parquet hoặc jsonl
├── split_game_ids.json
├── validation_report.json
└── checksums.sha256
```

Định dạng `.npz` hay `.pt` được chốt ở W5-D1. Không duy trì hai định dạng production song song nếu không có lý do rõ ràng.

### 11.3. Manifest tối thiểu

- `dataset_version`, `contract_version`, `board_size`, `win_length`.
- Raw run id và raw checksums.
- Teacher agents, budgets, seed policy và side balancing.
- Số game yêu cầu/thành công/thất bại, winner distribution.
- Số sample trước/sau validate, dedup và augmentation.
- Danh sách game id theo train/val/test và split seed.
- Encoder version, channel order, dtype, target mapping.
- Số duplicate/leakage bị loại theo từng split.
- Checksums của tensor, metadata và config.

### 11.4. Data card tối thiểu

- Mục đích và phạm vi sử dụng.
- Nguồn dữ liệu tự sinh và teacher configuration.
- Quy tắc luật Caro 11x11, chặn hai đầu và overline.
- Quy trình thu thập, validate, replay, split, dedup và augmentation.
- Phân phối game/sample/winner/source agent.
- Giới hạn: dữ liệu bắt chước Heuristic/MCTS, không phải expert con người; nguy cơ kế thừa bias teacher.
- Tuyên bố không chọn lọc ván thắng và không dùng test set để chọn siêu tham số.
- Hướng dẫn tái tạo cùng command, config, seed và checksum.

---

## 12. Ma trận test bắt buộc

| ID | Nhóm | Kịch bản | Expected | Owner |
|---|---|---|---|---|
| W56-T01 | Baseline | Full W3-4 suite với temp ghi được | Không setup error, không regression | M3 |
| W56-T02 | Raw | Một `GameRecord` hợp lệ | Validate và replay thành công | M3 |
| W56-T03 | Raw | Sai `contract_version` | Từ chối rõ lỗi | M3 |
| W56-T04 | Raw | Action/player/winner không khớp replay | Từ chối, ghi game id/ply | M3 |
| W56-T05 | Raw | Cùng config và seed | Cùng game IDs, side assignment và log logic | M3 |
| W56-T06 | Raw | Resume sau shard hoàn tất | Không sinh duplicate game ID | M3 |
| W56-T07 | Manifest | Shard bị sửa sau khi ghi | Checksum fail | M3 |
| W56-T08 | Encoder | State X và O đối xứng góc nhìn | Channel current/opponent đúng | M1/M3 |
| W56-T09 | Encoder | State 11x11 | Tensor `[3,11,11]`, float32 | M1 |
| W56-T10 | Label | Action `(row,col)` | Target index đúng và round-trip | M1/M3 |
| W56-T11 | Label | Target nằm trên ô đã chiếm | Pipeline từ chối | M3 |
| W56-T12 | Split | Nhiều sample cùng `game_id` | Chỉ thuộc một split | M3 |
| W56-T13 | Split | Cùng split seed | Cùng danh sách game IDs | M3 |
| W56-T14 | Leakage | Duplicate sample giữa split | Phát hiện và loại theo policy | M3 |
| W56-T15 | Symmetry | 8 phép D4 | Board/action/mask biến đổi đồng bộ | M3 |
| W56-T16 | Symmetry | Validation và test | Không augmentation | M3 |
| W56-T17 | Loader | Load một batch train | Shape/dtype/metadata đúng | M1/M3 |
| W56-T18 | Model | Batch 1 và batch >1 | Logits `[N,121]` | M1 |
| W56-T19 | Model | Forward/backward | Loss/gradient hữu hạn | M1 |
| W56-T20 | Mask | Highest raw logit là illegal | Action illegal không được chọn | M1 |
| W56-T21 | Loss | Target legal/illegal | Legal chạy; illegal bị từ chối | M1 |
| W56-T22 | Checkpoint | Save rồi load | Logits/action khớp trong tolerance | M1 |
| W56-T23 | Checkpoint | Sai board/model/dataset version | Từ chối rõ lỗi | M1 |
| W56-T24 | Train | Smoke dataset nhỏ | Có metric và tham số được cập nhật | M1 |
| W56-T25 | Train | Early stopping | Dừng theo validation, lưu best epoch | M1 |
| W56-T26 | Train | Resume checkpoint | Tiếp tục epoch/config đúng | M1 |
| W56-T27 | Neural | Env terminal | Raise `RuntimeError` | M1/M2 |
| W56-T28 | Neural | Env đang chơi | Action legal, `AgentDecision` hợp lệ | M1/M2 |
| W56-T29 | Neural | Snapshot trước/sau inference | Env không đổi | M1/M2 |
| W56-T30 | Neural | Cùng checkpoint/state | Cùng action | M1/M2 |
| W56-T31 | Teacher | Win/block fixtures W3-4 | Không regression | M2 |
| W56-T32 | Teacher | Cache bật/tắt cùng state | Action/score tương thích | M2 |
| W56-T33 | Teacher | Profile nhiều budget | Có throughput, ETA và hardware | M2 |
| W56-T34 | Tactical | Forced win/block board | Báo top-k/action trung thực | M2 |
| W56-T35 | Integration | Raw -> dataset -> train -> checkpoint | Hoàn tất trên fixture nhỏ | Cả nhóm |
| W56-T36 | Integration | Neural vs Random/Heuristic smoke | Runner/logger hoàn tất game | M2/M3 |
| W56-T37 | Regression | Engine, UI và agents cũ | Không test cũ bị vỡ | Cả nhóm |
| W56-T38 | Scope | Tìm literal 9/81 trong ML code | Không hard-code phạm vi cũ | M3 |

---

## 13. Lệnh thực thi và cổng chất lượng

Các CLI dưới đây là contract đầu ra mong muốn của sprint. Nếu tên option cuối cùng thay đổi, README và notebook phải cập nhật cùng PR.

### 13.1. Baseline và test theo owner

```powershell
# Full baseline; chọn basetemp có quyền ghi trên máy nhóm
.\myenv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider

# M1
.\myenv\Scripts\python.exe -m pytest `
  tests/test_architectures.py tests/test_neural_ai.py `
  -q -p no:cacheprovider

# M2
.\myenv\Scripts\python.exe -m pytest `
  tests/test_heuristic_ai.py tests/test_minimax_ai.py `
  tests/test_mcts_ai.py tests/test_policy_tactical.py `
  -q -p no:cacheprovider

# M3
.\myenv\Scripts\python.exe -m pytest `
  tests/test_selfplay_generation.py tests/test_data_pipeline.py `
  tests/test_tournament_runner.py tests/test_agents_integration.py `
  -q -p no:cacheprovider
```

### 13.2. Self-play và build dataset

```powershell
# Pilot
.\myenv\Scripts\python.exe scripts/generate_selfplay.py `
  --config configs/selfplay_w56.json `
  --games 20 `
  --output data/raw_logs/w56_selfplay_pilot

# Production
.\myenv\Scripts\python.exe scripts/generate_selfplay.py `
  --config configs/selfplay_w56.json `
  --games 200 `
  --output data/raw_logs/w56_selfplay_v1 `
  --resume

# Build dataset-v1
.\myenv\Scripts\python.exe scripts/build_dataset.py `
  --input data/raw_logs/w56_selfplay_v1 `
  --output data/processed_tensors/dataset_v1 `
  --config configs/train_w56.json
```

### 13.3. Train và smoke agent

```powershell
# Smoke CPU
.\myenv\Scripts\python.exe scripts/train_policy.py `
  --config configs/train_w56.json `
  --dataset data/processed_tensors/dataset_v1 `
  --output models/checkpoints/model-v1 `
  --device cpu `
  --smoke

# Production
.\myenv\Scripts\python.exe scripts/train_policy.py `
  --config configs/train_w56.json `
  --dataset data/processed_tensors/dataset_v1 `
  --output models/checkpoints/model-v1
```

### 13.4. Coverage và Definition of Done

Cổng đề xuất:

- Code mới trong `core.ml`, `neural_ai.py` và data pipeline đạt tối thiểu 85% statement coverage.
- Các invariant replay, split, legal mask, no-mutation và checkpoint version phải có test hành vi; coverage không thay thế các test này.
- Notebook 01-03 mở và chạy được từ kernel project; cell đầu ghi rõ config/run id.
- `git diff --check` không báo lỗi.
- Không commit dữ liệu lớn, checkpoint, event TensorBoard, cache hoặc artifact tạm.
- Config và manifest không chứa đường dẫn tuyệt đối phụ thuộc một máy.
- PR mô tả command, seed, checksum và artifact đã tạo.
- Không ghi metric giả hoặc placeholder vào data card/model report.

---

## 14. Rủi ro và phương án xử lý

| Rủi ro | Dấu hiệu | Cách xử lý | Owner |
|---|---|---|---|
| W3-4 chưa thật sự xanh | Setup error hoặc integration test không chạy | Sửa môi trường temp/CI, xác nhận cổng trước production | M3 |
| MCTS quá chậm để đủ 200 game | ETA vượt thời gian sprint | Profile pilot; freeze budget thấp hơn có version; không đổi giữa shard | M1, M2, M3 |
| Multiprocessing tạo seed/game trùng | Duplicate game ID/checksum | Seed derivation tập trung, shard ranges cố định, test resume | M3 |
| Raw game không replay được | Player/action/winner lệch | Dừng production, sửa nguồn; không “làm sạch” bằng đoán state | M3 |
| Leakage do split từng state | Cùng game xuất hiện ở train/test | Split danh sách game IDs trước mọi augmentation | M3 |
| Duplicate opening giữa game khác split | Hash state-target trùng | Cross-split audit; ưu tiên train và ghi số loại khỏi val/test | M3 |
| Symmetry biến đổi sai action | Board hợp lý nhưng target lệch | Unit test 8 phép và inverse transform | M3 |
| Model chọn illegal move | Mask áp sau argmax hoặc sai flatten order | Mask logits trước argmax/loss; test forced illegal max | M1 |
| Model overfit teacher | Train tốt, val/test thấp | Early stopping, report gap, không tune trên test | M1 |
| Checkpoint không tái lập | Thiếu config/dataset checksum | Checkpoint bundle bắt buộc metadata/version | M1 |
| M2/M1 cùng sửa NeuralAgent | Conflict ownership | M1 code adapter, M2 chỉ viết acceptance file riêng | M1, M2 |
| Cache làm sai search | Action thay đổi theo thứ tự game | Immutable key, cache on/off equivalence tests | M2 |
| Notebook chạy được nhưng script không chạy | Logic bị copy vào cell | Script/module là canonical; notebook chỉ gọi API | Cả nhóm |
| Data/checkpoint làm đầy Git | File lớn xuất hiện trong status | Giữ `.gitignore`, commit data card/checksum/config thôi | M3 |
| Test metric bị dùng để tune | Nhiều lần sửa config sau xem test | Ghi access log; khóa config trước test evaluation | M1, M3 |

---

## 15. Checklist nghiệm thu Tuần 5-6

### Baseline và config

- [ ] Full W3-4 regression xanh trong môi trường có quyền ghi temp.
- [ ] `caro-v2`, 11x11 và action tuple được giữ nguyên.
- [ ] Teacher config, seeds, budgets và production run id đã freeze.
- [ ] Encoder/model/dataset schema có version rõ.

### M1 - PolicyNet và NeuralAgent

- [ ] Encoder 3 channel đúng góc nhìn current player.
- [ ] PolicyNet xuất 121 logits.
- [ ] Mask và loss từ chối illegal target/action.
- [ ] Forward/backward smoke xanh trên CPU.
- [ ] Train loop có seed, val, early stopping và history.
- [ ] Best checkpoint chứa đủ config/version/checksum/metrics.
- [ ] NeuralAgent legal, deterministic, no-mutation và terminal guard đúng.
- [ ] Notebook 03 tái lập được training workflow.

### M2 - Teacher và acceptance

- [ ] Tactical regression của Heuristic/MCTS xanh.
- [ ] Có benchmark throughput và ETA 200/300 game.
- [ ] Mọi tối ưu/cache có equivalence test.
- [ ] `teacher_w56.json` được cả nhóm duyệt.
- [ ] Tactical acceptance của NeuralAgent chạy trên fixtures độc lập.
- [ ] Smoke match qua runner hoàn tất và không bị dùng để kết luận sức mạnh.
- [ ] Failure cases được lưu trung thực.

### M3 - Self-play và dataset

- [ ] Pilot 20 game replay 100%.
- [ ] Production có tối thiểu 200 game hợp lệ, đổi bên cân bằng.
- [ ] Không chọn lọc ván thắng.
- [ ] Raw manifest có config, seed, budget, hardware và checksum.
- [ ] Split 70/15/15 theo game id.
- [ ] Dedup/leakage audit và D4 train-only đúng.
- [ ] Mỗi target nằm trong legal mask.
- [ ] `dataset-v1` có loader, manifest, checksums và data card.
- [ ] Notebook 01-02 gọi code canonical và hiển thị số liệu thật.

### Integration và Git

- [ ] Ma trận W56-T01 đến W56-T38 được cover hoặc có lý do loại trừ.
- [ ] Raw fixture -> dataset -> smoke train -> checkpoint -> NeuralAgent chạy end-to-end.
- [ ] Engine/UI/bốn agent cũ không regression.
- [ ] Không commit raw logs, tensor, checkpoint hoặc TensorBoard run.
- [ ] PR merge đúng thứ tự ở Mục 9.
- [ ] Config, data card, model report và checksum được cả nhóm review.
- [ ] Chỉ tạo tag `model-v1` sau khi full checklist đạt.

---

## 16. Điều kiện chuyển sang Tuần 7

Nhóm chỉ bắt đầu giải đấu chính thức và ablation khi:

1. `agents-v1`, `dataset-v1` và `model-v1` có config/checksum cố định.
2. NeuralAgent thực sự tải checkpoint đã huấn luyện, không phải mạng random.
3. Raw data, split manifest, data card và training history đủ để tái lập.
4. Test set chưa bị dùng để chọn siêu tham số.
5. NeuralAgent chạy qua cùng runner/logger với Random, Heuristic, Minimax và MCTS.
6. Full regression xanh và không còn setup error môi trường.
7. M2 đã ghi tactical failure cases; M1 đã ghi learning curve; M3 đã ghi dataset statistics.

Sau khi freeze, Tuần 7 không được chỉnh agent hoặc model dựa trên kết quả round-robin chính thức. Nếu bắt buộc sửa lỗi correctness, phải tăng version, chạy lại các kết quả bị ảnh hưởng và ghi rõ thay đổi trong báo cáo.
