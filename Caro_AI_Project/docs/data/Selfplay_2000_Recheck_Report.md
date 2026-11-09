# Báo cáo kiểm tra lại 2.000 ván self-play

Ngày kiểm tra: 2026-11-08  
Phạm vi: Heuristic, Minimax/Alpha-Beta và MCTS trong cấu hình dataset v1.

## 1. Kết luận

Kết quả được nêu ban đầu là **đúng** với code và cấu hình hiện tại:

| Cặp agent | Số ván | Heuristic thắng | Minimax thắng | MCTS thắng | Hòa |
|---|---:|---:|---:|---:|---:|
| Heuristic vs Minimax | 668 | 334 | 0 | — | 334 |
| Heuristic vs MCTS | 666 | 666 | — | 0 | 0 |
| Minimax vs MCTS | 666 | — | 666 | 0 | 0 |

Tổng hợp theo agent:

| Agent | Thắng | Thua | Hòa |
|---|---:|---:|---:|
| Heuristic | 1.000 | 0 | 334 |
| Minimax | 666 | 334 | 334 |
| MCTS | 0 | 1.332 | 0 |

Không tìm thấy dấu hiệu đảo dấu reward, sai bên X/O hoặc agent trả nước không hợp
lệ. Kết quả bất thường chủ yếu là hậu quả của **budget MCTS không phù hợp với
branching factor**, rollout quá yếu và độ đa dạng teacher thấp. Đây là vấn đề
thiết kế thuật toán/thực nghiệm ở cấu hình hiện tại hơn là lỗi contract của game
engine.

## 2. Cấu hình được đối chiếu

Nguồn cấu hình: `configs/selfplay_w56_dataset_v1.json`.

- Bàn cờ `11 x 11`, điều kiện thắng 5 quân.
- `base_seed = 1107`.
- Đổi bên X/O sau mỗi ván; hai ván đổi bên liên tiếp dùng cùng seed.
- Số ván theo cặp: `[668, 666, 666]`.
- Minimax: Alpha-Beta, `max_depth = 2`.
- MCTS: `simulations = 20`.

Runner sinh seed cho từng ván và từng ply tại
`core/utils/tournament_runner.py:220-226` và
`core/utils/tournament_runner.py:383-384`. Vì vậy các ván có MCTS tái lập được,
trong khi seed không làm thay đổi Heuristic hoặc Minimax vì hai agent này không
dùng RNG.

## 3. Cách chạy kiểm tra

### 3.1. Kiểm tra kết quả thi đấu

- Chạy đủ 666 seed của Heuristic vs MCTS.
- Chạy đủ 666 seed của Minimax vs MCTS.
- Với Heuristic vs Minimax, chạy hai cách xếp bên duy nhất:
  - Heuristic-X / Minimax-O: hòa sau 121 ply.
  - Minimax-X / Heuristic-O: Heuristic thắng sau 34 ply.

Heuristic và Minimax đều deterministic, trạng thái đầu luôn là bàn trống, và
`CaroEnv.reset(seed)` không thêm nước khai cuộc ngẫu nhiên. Do đó 668 ván của
cặp này chỉ lặp 334 lần mỗi quỹ đạo trên; chạy lặp lại toàn bộ không tạo thêm
trường hợp kiểm thử.

Thống kê độ dài ván ở hai cặp có MCTS:

| Cặp | Min ply | Max ply | Trung bình ply | Bên thắng X/O |
|---|---:|---:|---:|---:|
| Heuristic vs MCTS | 9 | 34 | 10,584 | 333 / 333 |
| Minimax vs MCTS | 9 | 26 | 13,248 | 333 / 333 |

Kết quả cân bằng tuyệt đối theo bên thắng X/O cho thấy thất bại của MCTS không
đến từ lợi thế đi trước trong protocol đổi bên.

### 3.2. Kiểm tra unit test

Lệnh:

```powershell
.\myenv\Scripts\python.exe -m pytest `
  tests/test_heuristic_ai.py `
  tests/test_minimax_ai.py `
  tests/test_mcts_ai.py `
  -q -p no:cacheprovider
```

Kết quả: **140 passed in 4.78s**.

Các test này xác nhận action hợp lệ, không mutation environment, semantics
depth/simulation, tính tái lập theo seed, rollout/backpropagation và các tình
huống tactical cơ bản. Việc test pass không chứng minh agent mạnh; nó chỉ cho
thấy implementation tuân thủ hành vi mà test hiện tại đặc tả.

## 4. Vì sao MCTS thua toàn bộ?

### 4.1. Với 20 simulations, MCTS không đi vào Selection/UCT trong benchmark

Ở đầu ván có 121 action hợp lệ. Mỗi simulation chỉ mở một child chưa thử ở
root (`core/agents/mcts_ai.py:270-274`). Selection bằng UCT chỉ xảy ra khi
`untried_actions` của node đã rỗng (`core/agents/mcts_ai.py:248-253`).

Trong tất cả ván đã chạy, ván dài nhất chỉ có 34 ply, tức ở mọi lượt vẫn còn ít
nhất 87 ô trống. Vì `87 > 20`, sau 20 simulations root vẫn còn rất nhiều action
chưa thử. Hệ quả ở **mọi lượt MCTS của benchmark này**:

1. Mỗi simulation chọn một action root mới.
2. Mỗi child chỉ được thăm đúng một lần.
3. Nhánh Selection/UCT không được dùng để đi sâu hoặc tái thăm action tốt.
4. Thống kê visit count giữa 20 child đều bằng nhau.

Nói cách khác, cấu hình hiện tại không vận hành như MCTS nhiều tầng; nó gần với
“lấy mẫu 20 nước khác nhau, rollout ngẫu nhiên một lần cho mỗi nước”.

### 4.2. Quyết định cuối phụ thuộc vào một rollout nhiễu cao

Rollout chọn đều một action trong **toàn bộ** legal actions bằng
`rng.choice(legal)` (`core/agents/mcts_ai.py:147`), không có:

- ưu tiên thắng ngay;
- chặn nước thắng của đối thủ;
- giới hạn action quanh các quân đã có;
- pattern heuristic hoặc policy prior.

Trên bàn 11 x 11, reward thắng/thua ở cuối rollout rất thưa và có phương sai
cao. Một rollout duy nhất không đủ để ước lượng chất lượng của một nước tactical.

Sau cùng, robust-child chọn theo visit, rồi mean value, rồi tọa độ row-major
(`core/agents/mcts_ai.py:289-296`). Vì mọi child thường có một visit, visit count
không phân biệt được action; kết quả chủ yếu dựa trên reward của đúng một rollout
ngẫu nhiên. Nếu nhiều child cùng reward, tie-break row-major tạo thêm thiên lệch
tọa độ không liên quan đến chiến thuật.

### 4.3. Cây bị dựng lại ở mỗi nước đi

Mỗi lần `choose_action` tạo root mới và clone environment cho từng simulation
(`core/agents/mcts_ai.py:219-245`). Không có tree reuse giữa các ply. Toàn bộ
thông tin 20 simulations của lượt trước bị bỏ, làm budget nhỏ càng kém hiệu quả.

### 4.4. Đối thủ có kiểm tra tactical trực tiếp

Heuristic duyệt tất cả legal actions và dùng thứ tự:

`win ngay > block thua ngay > threat > center`

tại `core/agents/heuristic_ai.py:147-166` và `core/agents/heuristic_ai.py:205-206`.
Minimax depth 2 còn dùng chính `action_priority`, bảng pattern và hàm lượng giá
board của Heuristic (`core/agents/minimax_ai.py:53`, `78`, `322`, `381`).

Do đó Heuristic/Minimax luôn xử lý các đe dọa một-hai ply một cách có chủ đích,
trong khi MCTS-20 thường không nhận ra hoặc không chặn chúng. Việc MCTS thua rất
nhanh (trung bình khoảng 10,6 và 13,2 ply) phù hợp trực tiếp với cơ chế này.

## 5. Vì sao Heuristic vs Minimax chỉ cho 334 thắng + 334 hòa?

Đây không phải 668 quan sát độc lập:

- cả hai agent deterministic;
- mọi ván bắt đầu từ cùng bàn trống;
- không có random opening;
- Minimax dùng cùng bảng pattern và move-ordering với Heuristic;
- runner chỉ luân phiên bên X/O.

Vì vậy chỉ tồn tại hai trajectory cho cặp này. Khi Heuristic là X, trajectory
đi đến hòa; khi Heuristic là O, trajectory kết thúc bằng Heuristic thắng. Mỗi
cách xếp bên xuất hiện 334 lần nên kết quả bắt buộc là 334 thắng và 334 hòa.

Kết quả này không nên được diễn giải như win rate ước lượng từ 668 mẫu độc lập.
Nó chủ yếu đo hai đường đi deterministic của hai policy có chung nền tảng đánh
giá.

## 6. Tác động lên dataset

Nhận xét “dataset thiên về Heuristic” là đúng về **chất lượng và kiểu policy**,
nhưng cần diễn đạt chính xác hơn về số lượng:

- Số ván có mặt của các agent gần cân bằng: Heuristic 1.334, Minimax 1.334,
  MCTS 1.332.
- Pipeline tạo sample trước **mọi** nước đi và lưu `source_agent`
  (`core/ml/data_pipeline.py:150-169`); không chỉ lấy nước của bên thắng.
- Vì vậy các nước yếu của MCTS trong 1.332 ván thua vẫn trở thành nhãn policy.
- Heuristic và Minimax không phải hai teacher độc lập hoàn toàn vì dùng chung
  pattern/evaluation; dữ liệu dễ khuếch đại cùng một inductive bias.
- 668 ván Heuristic-Minimax chỉ gồm hai trajectory lặp lại, gây duplication rất
  lớn trước bước dedup.

Data card hiện tại đã cho thấy 67.642 sample trước dedup nhưng loại 55.444
duplicate (xấp xỉ **82%**). Đây là bằng chứng định lượng rằng diversity thực tế
thấp hơn nhiều so với con số 2.000 ván.

Rủi ro chính không chỉ là model “học quá nhiều Heuristic”, mà là model học hỗn
hợp nhãn có chất lượng không đồng đều: pattern bias tương quan mạnh từ
Heuristic/Minimax cộng với nhiều quyết định MCTS gần-random.

## 7. Khuyến nghị

1. **Không dùng MCTS-20 làm teacher chính** cho dataset huấn luyện tiếp theo.
2. Benchmark MCTS ở ít nhất 100/400/1.000 simulations như profile dự kiến của
   repo. Lưu ý 100 vẫn nhỏ hơn 121 action ở root; chỉ tăng budget chưa chắc đủ.
3. Thêm tactical pre-check `win/block`, candidate filtering hoặc progressive
   widening để budget tập trung vào action có liên quan.
4. Dùng heuristic/policy-guided rollout hoặc value estimate thay rollout đều
   toàn bàn; cân nhắc tree reuse giữa các ply.
5. Thêm random opening hợp lệ hoặc tập vị trí khởi đầu đa dạng; không lặp hàng
   trăm lần cùng một cặp deterministic từ bàn trống.
6. Theo dõi phân bố sample theo `source_agent`, tỷ lệ thắng và độ trùng; cân
   nhắc weighting/filtering theo chất lượng teacher thay vì chỉ cân bằng số ván.
7. Sau khi thay MCTS/config, sinh lại raw logs và data card; không trộn âm thầm
   dataset cũ và mới dưới cùng version.

## 8. Kết luận cuối

Kết quả ban đầu được tái lập đúng. MCTS không yếu vì lỗi đổi bên hay lỗi reward
đã quan sát được; nó yếu vì với 20 simulations trên bàn 11 x 11, code chưa bao
giờ đi qua giai đoạn mở hết root trong các ván này, nên UCT không tham gia vào
quyết định. Kết hợp rollout ngẫu nhiên, không tactical prior và không
tree reuse khiến MCTS hoạt động gần như một policy lấy mẫu nhiễu, trong khi hai
đối thủ có rule/pattern cụ thể.

Dataset v1 vì thế phù hợp để smoke-test pipeline, nhưng không phải nguồn teacher
cân bằng để kết luận chất lượng policy. Data card cần tiếp tục ghi rõ hạn chế
này; phiên bản dữ liệu kế tiếp nên tăng chất lượng và độ đa dạng teacher trước
khi tăng số lượng game.
