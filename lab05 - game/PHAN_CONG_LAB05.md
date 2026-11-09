# Phân công Lab 05 - Tìm kiếm đối kháng và trò chơi

## 1. Phạm vi và quyết định chung

Nhóm hoàn thành:

- Bài 1-7: toàn bộ phần Tic-Tac-Toe bắt buộc.
- Bài mở rộng: chọn **Bài 8 - Connect 4**.
- Bảng tổng hợp, câu hỏi thảo luận, tối thiểu 3-5 nhận xét và README hướng dẫn chạy.

Lý do chọn Connect 4: notebook này bao phủ đủ môi trường trò chơi, Alpha-Beta, move ordering, heuristic với cutoff và Pure Monte Carlo; do đó có thể tái sử dụng trực tiếp kiến thức từ phần Tic-Tac-Toe. Hai notebook `assignment_mean_connect4.ipynb` và `assignment_dots_and_boxes.ipynb` không sửa, trừ khi giảng viên chỉ định một bài khác.

## 2. Hiện trạng source code

- `tictactoe.py` đã có đủ API nền: `actions`, `result`, `terminal`, `utility`, `check_board`, `random_player`, `play` và hàm hiển thị.
- Bảy notebook Tic-Tac-Toe đã có cài đặt mẫu và phần lớn có output cũ. Công việc chính là chạy lại, bổ sung đúng số thí nghiệm, chuẩn hóa bảng kết quả và viết nhận xét theo đề.
- Một số thiếu sót đáng chú ý:
  - `tictactoe_definitions.ipynb` mới chạy Random vs Random 100 ván, trong khi đề yêu cầu 1.000 ván.
  - Các notebook tìm kiếm chưa trình bày kết quả trên cùng một bộ trạng thái theo một bảng thống nhất.
  - Phần PMCS chưa đánh giá N = 10, 100, 1000 một cách hệ thống trên cùng bộ trạng thái.
  - Phần tổng hợp thời gian trung bình/nước đi và các câu hỏi thảo luận chưa có tài liệu chung.
- `assignment_connect4.ipynb` có 25 vị trí placeholder và chưa được thực thi; đây là phần cần cài đặt nhiều nhất.
- `README.md` hiện chỉ là danh sách liên kết, chưa có cách cài môi trường, cách chạy, seed và quy trình tái tạo kết quả.
- Thư mục Lab 05 hiện đang là thư mục chưa được Git theo dõi trong repository cha. Repository cha còn có thay đổi không thuộc Lab 05, vì vậy tuyệt đối không dùng `git add -A` hoặc stage từ thư mục cha.

## 3. Quy tắc chống conflict

1. **Một file chỉ có một người sở hữu.** Người khác không sửa file đó, kể cả chỉ sửa Markdown hoặc chạy lại notebook, vì Jupyter có thể thay đổi output và metadata trên toàn file.
2. `tictactoe.py` được xem là API đã đóng băng và do Hải sở hữu. Nếu Thiện hoặc Ly cần thay đổi, gửi đề xuất cho Hải; Hải là người tạo commit thay đổi API.
3. Phần Connect 4 được tách thành ba module Python. Mỗi người cài đặt và test module của mình. Chỉ Ly sửa `assignment_connect4.ipynb` để import ba module và trình bày kết quả.
4. Mỗi người ghi số liệu vào file riêng trong `results/`; không cùng sửa một CSV/Markdown tổng hợp.
5. Không format, clear output hoặc chạy notebook do người khác sở hữu.
6. Mọi agent có chữ ký thống nhất `agent(board, player=1) -> int`. Nước đi Connect 4 là chỉ số cột, đánh số từ 0.
7. Các hàm `result` phải trả bàn cờ mới, không sửa trực tiếp bàn cờ đầu vào. Giá trị ô Connect 4 là `0`, `1`, `-1`.

## 4. API Connect 4 phải chốt trước khi code

### `connect4_core.py` - Hải sở hữu

```python
empty_board(shape=(6, 7)) -> np.ndarray
actions(board) -> list[int]
result(board, player, action) -> np.ndarray
terminal(board) -> bool
utility(board, player=1) -> int | None
other(player) -> int
random_player(board, player=1) -> int
play(player1, player2, n_games=100, shape=(6, 7), seed=42) -> dict
```

Quy ước `utility`: thắng `+1`, hòa `0`, thua `-1`, trạng thái chưa kết thúc trả `None`. `result` ném `ValueError` nếu cột không hợp lệ hoặc đã đầy.

### `connect4_search.py` - Thiện sở hữu

```python
alpha_beta_search(board, player=1, move_ordering=True) -> dict
evaluate(board, player=1) -> float
heuristic_alpha_beta_search(board, player=1, cutoff=4,
                            move_ordering=True) -> dict
AlphaBetaAgent(move_ordering=True)
HeuristicAlphaBetaAgent(cutoff=4, move_ordering=True)
```

Kết quả search thống nhất là dictionary có ít nhất `move`, `value`, `nodes`, `elapsed_s`. `evaluate` luôn nằm trong `[-1, 1]`; trạng thái thắng/thua dành riêng giá trị `+1/-1`.

### `connect4_monte_carlo.py` - Ly sở hữu

```python
playout(board, action, player=1, rng=None) -> int
pmcs(board, player=1, n_playouts=100, seed=42) -> dict
PureMonteCarloAgent(n_playouts=100, seed=42)
```

`pmcs` trả dictionary có ít nhất `move`, `value`, `playouts`, `elapsed_s`. Tổng ngân sách mô phỏng được phân bổ đều cho các hành động hợp lệ.

## 5. Phân công chi tiết

### Hải - Nền tảng trò chơi, AND-OR, tương tác và Connect 4 core

**File được phép sửa/tạo**

- `tictactoe.py`
- `tictactoe_definitions.ipynb`
- `tictactoe_and_or_tree_search.ipynb`
- `tictactoe_interactive.ipynb`
- `connect4_core.py`
- `tests/test_connect4_core.py`
- `results/hai_results.md`
- `README.md`

**Công việc Tic-Tac-Toe**

1. Bài 1:
   - Kiểm tra và giải thích state, action, transition, terminal, utility.
   - Chạy Random vs Random đúng 1.000 ván với seed cố định.
   - Ghi số ván X thắng, O thắng, hòa và nhận xét lợi thế người đi trước.
2. Bài 2:
   - Chạy đủ bốn trạng thái: sắp thắng, cần đường hòa, tình huống bất lợi, bàn rỗng.
   - Với mỗi trạng thái ghi nước đi đầu tiên và giải thích cấu trúc kế hoạch điều kiện AND-OR.
   - Cho AND-OR đấu Random tối thiểu 100 ván ở mỗi vai X và O.
3. Bài 7:
   - Chơi thử cả vai X và O.
   - Lưu lại ít nhất một biên bản ván đấu dưới dạng Markdown để người chấm đọc được mà không cần nhập tương tác.

**Công việc Connect 4**

1. Cài `connect4_core.py`: biểu diễn bàn, luật rơi quân, kiểm tra bốn quân ngang/dọc/chéo, utility, Random Agent và vòng lặp thi đấu.
2. Hỗ trợ bàn có kích thước khác nhau; Minimax sẽ dùng bàn nhỏ, heuristic/PMCS dùng bàn chuẩn 6 x 7.
3. Viết test cho:
   - Cột hợp lệ và cột đầy.
   - Quân rơi đúng hàng thấp nhất.
   - Thắng ngang, dọc, hai đường chéo.
   - Hòa và trạng thái chưa kết thúc.
   - Input board không bị mutate.
4. Viết phần ước lượng state space/game tree và kết quả Random vs Random vào `results/hai_results.md` để Ly tích hợp.
5. Cuối cùng cập nhật `README.md` với môi trường, lệnh chạy notebook/test và cấu trúc project.

**Điều kiện hoàn thành**

- Ba notebook chạy được theo thứ tự từ đầu tới cuối; riêng input tương tác được chạy thủ công.
- `tests/test_connect4_core.py` pass.
- Kết quả và nhận xét không chỉ dựa vào output cũ có sẵn.

### Thiện - Minimax/Alpha-Beta, heuristic và Connect 4 search

**File được phép sửa/tạo**

- `tictactoe_alpha_beta_tree_search.ipynb`
- `tictactoe_heuristic_alpha_beta_tree_search.ipynb`
- `connect4_search.py`
- `tests/test_connect4_search.py`
- `results/thien_results.md`
- `BAO_CAO_KET_QUA.md`

**Công việc Tic-Tac-Toe**

1. Bài 3:
   - Chạy Minimax và Alpha-Beta trên cùng bốn trạng thái chuẩn.
   - Lập bảng: trạng thái, thuật toán, nước đi, giá trị, số nút, thời gian.
   - Thêm kiểm tra khẳng định Minimax và Alpha-Beta có cùng giá trị/nước đi tối ưu. Nếu có nhiều nước tối ưu, so sánh giá trị và tập nước tối ưu thay vì bắt buộc cùng một chỉ số.
   - So sánh Alpha-Beta trước/sau move ordering bằng số nút và thời gian.
2. Bài 4:
   - Trên cùng bộ trạng thái, chạy Alpha-Beta đầy đủ, cutoff = 2 và cutoff = 4.
   - Lập đúng bảng nước đi, số nút, thời gian, nhận xét chất lượng.
   - Cho heuristic agent đấu Random ở cả hai vai, mỗi vai tối thiểu 100 ván.

**Công việc Connect 4**

1. Cài `connect4_search.py`: Alpha-Beta, đếm node, move ordering ưu tiên cột trung tâm, heuristic và depth cutoff.
2. Dùng full Alpha-Beta trên bàn nhỏ; không cố duyệt hết bàn chuẩn 6 x 7.
3. Heuristic nên tính các cửa sổ bốn ô, thưởng chuỗi của mình, phạt chuỗi đối thủ và ưu tiên trung tâm; chuẩn hóa về `[-1, 1]`.
4. Viết tối thiểu năm trạng thái test thủ công: thắng ngay, chặn thua, thắng ngang, thắng dọc, thắng chéo/ưu tiên trung tâm.
5. Đo move ordering on/off và cutoff khác nhau; ghi số liệu, giải thích vào `results/thien_results.md`.
6. Sau khi nhận ba file kết quả cá nhân, tổng hợp `BAO_CAO_KET_QUA.md`, gồm:
   - Bảng sáu chiến lược Tic-Tac-Toe.
   - Sáu câu hỏi thảo luận của đề.
   - Tối thiểu 3-5 nhận xét về chất lượng nước đi, số nút, thời gian và khả năng mở rộng.

**Điều kiện hoàn thành**

- Hai notebook chạy từ đầu tới cuối và có bảng so sánh theo cùng protocol.
- `tests/test_connect4_search.py` pass cùng core của Hải.
- Báo cáo phân biệt rõ thời gian tổng và thời gian trung bình/nước đi.

### Ly - Monte Carlo/UCB1 và notebook Connect 4 tích hợp

**File được phép sửa/tạo**

- `tictactoe_pure_monte_carlo_search.ipynb`
- `tictactoe_monte_carlo_tree_search_restricted.ipynb`
- `connect4_monte_carlo.py`
- `tests/test_connect4_monte_carlo.py`
- `results/ly_results.md`
- `assignment_connect4.ipynb`

**Công việc Tic-Tac-Toe**

1. Bài 5:
   - Chạy PMCS với N = 10, 100, 1000 trên cùng bốn trạng thái chuẩn.
   - Mỗi cấu hình lặp nhiều lần để đo độ ổn định; đề xuất 30 lần/trạng thái và báo tỷ lệ chọn nước đi phổ biến nhất.
   - Cho PMCS-10 và PMCS-100 đấu Random ở cả hai vai, mỗi vai tối thiểu 100 ván. Nếu thời gian cho phép, thêm PMCS-1000 để hoàn thiện bảng so sánh ngân sách.
   - Báo thắng/hòa/thua và thời gian trung bình/nước đi.
2. Bài 6:
   - Chạy UCB1-10 và UCB1-100 trên cùng bộ trạng thái và khi đấu Random ở cả hai vai.
   - Giải thích exploration term, exploitation term và ảnh hưởng của số mô phỏng đến độ ổn định.
   - Sửa tiêu đề/nhận xét trong notebook nếu còn ghi nhầm thành Pure Monte Carlo.

**Công việc Connect 4**

1. Cài `connect4_monte_carlo.py` và test tính hợp lệ của playout, seed, ngân sách mô phỏng, nước thắng ngay.
2. Là người duy nhất chỉnh `assignment_connect4.ipynb`:
   - Import `connect4_core`, `connect4_search`, `connect4_monte_carlo` thay vì sao chép ba bản thuật toán vào notebook.
   - Điền toàn bộ Task 1-5 và mọi placeholder bắt buộc.
   - Tích hợp nội dung/số liệu do Hải và Thiện bàn giao.
   - Chạy Random vs Random 1.000 ván, Alpha-Beta vs Random trên bàn 4 x 4, hai heuristic cutoff đấu nhau, PMCS trên các trạng thái test.
   - Ghi thời gian theo kích thước bàn và giải thích vì sao full Minimax không khả thi trên 6 x 7.
   - Không làm phần Graduate/bonus nếu các phần bắt buộc chưa hoàn chỉnh.
3. Ghi kết quả Monte Carlo và UCB1 vào `results/ly_results.md` để Thiện tổng hợp.

**Điều kiện hoàn thành**

- Hai notebook Tic-Tac-Toe và notebook Connect 4 chạy từ đầu tới cuối không lỗi.
- `tests/test_connect4_monte_carlo.py` pass cùng core của Hải.
- Notebook Connect 4 có code, output, bảng/biểu đồ và nhận xét ngay sau từng thí nghiệm.

## 6. Bộ thí nghiệm chung

Tất cả notebook Tic-Tac-Toe dùng cùng bốn trạng thái đã có trong source:

| Mã | Trạng thái | Mục đích |
|---|---|---|
| T1 | X sắp thắng | Kiểm tra tìm nước thắng ngay |
| T2 | X chỉ có thể bảo đảm hòa | Kiểm tra chiến lược phòng thủ |
| T3 | Tình huống bất lợi | Kiểm tra giá trị thua/khả năng trì hoãn |
| T4 | Bàn rỗng | Kiểm tra độ lớn cây và tính mở rộng |

Protocol chung:

- Seed mặc định: `42`; với thí nghiệm độ ổn định dùng danh sách seed `0..29`.
- Random vs Random: 1.000 ván.
- Mỗi agent khác vs Random: 100 ván làm X và 100 ván làm O. Khi gộp kết quả, thắng/thua luôn tính từ góc nhìn agent đang đánh giá.
- Thời gian dùng `time.perf_counter()`; báo `elapsed_s / số_nước_agent_đã_đi`, không chia đơn giản cho tổng số ván.
- Tắt `DEBUG` khi benchmark và reset node counter ở mỗi lần search.
- Chạy warm-up một lần trước khi đo; không trộn thời gian render Matplotlib vào thời gian chọn nước đi.

## 7. Trình tự làm và merge

### Giai đoạn 0 - Tạo baseline

Một người tạo commit baseline chỉ chứa Lab 05 trước khi chia nhánh. Stage file bằng đường dẫn cụ thể, không stage toàn repository cha. Nếu Git báo `dubious ownership`, xử lý `safe.directory` trước khi tạo nhánh.

### Giai đoạn 1 - Làm song song

- Hải: `feature/hai-core-andor`
- Thiện: `feature/thien-search`
- Ly: `feature/ly-montecarlo-integration`

Trong giai đoạn này, Ly có thể tạo khung notebook nhưng chỉ chạy tích hợp sau khi API core/search ổn định.

### Giai đoạn 2 - Bàn giao module

1. Merge Hải trước để chốt `connect4_core.py`.
2. Thiện rebase/merge main, chạy test search với core thật rồi merge.
3. Ly rebase/merge main, chạy test Monte Carlo và hoàn thiện notebook Connect 4.
4. Mỗi người push file `results/<ten>_results.md` của mình.

### Giai đoạn 3 - Tổng hợp

- Thiện tổng hợp `BAO_CAO_KET_QUA.md` từ ba file kết quả, không sửa notebook của Hải/Ly.
- Hải cập nhật `README.md` từ các lệnh chạy đã được xác nhận.
- Ly chạy lại `assignment_connect4.ipynb` sau khi hai module phụ thuộc đã merge.

## 8. Quy ước commit và pull request

Commit nhỏ, mỗi commit chỉ có một mục đích. Ví dụ:

```text
feat(tictactoe): add AND-OR benchmark and analysis
feat(connect4-core): implement board rules and random agent
feat(connect4-search): add alpha-beta cutoff and move ordering
feat(connect4-mc): add pure Monte Carlo agent
docs(report): summarize adversarial-search experiments
test(connect4): cover terminal and utility cases
```

Trước khi push:

1. `git status --short` và xác nhận không có file của người khác.
2. Stage bằng danh sách file thuộc quyền sở hữu.
3. Chạy test module của mình.
4. Chạy lại notebook mình sở hữu từ kernel mới.
5. Kiểm tra notebook không chứa traceback, output debug quá dài hoặc đường dẫn máy cá nhân.

## 9. Checklist nộp bài

- [ ] Bài 1-7 có code, output và nhận xét ngay dưới thí nghiệm.
- [ ] Random vs Random đủ 1.000 ván.
- [ ] Mỗi chiến lược vs Random đủ tối thiểu 100 ván; nhóm dùng 100 ván cho mỗi vai.
- [ ] Bảng tổng hợp có Thắng/Hòa/Thua và thời gian trung bình/nước đi.
- [ ] Minimax và Alpha-Beta được xác nhận không thay đổi giá trị tối ưu.
- [ ] Có so sánh move ordering trước/sau.
- [ ] Heuristic Alpha-Beta có cutoff 2, 4 và full search.
- [ ] PMCS có N = 10, 100, 1000; UCB1 có N = 10, 100.
- [ ] Có ít nhất một ván tương tác được ghi lại.
- [ ] `assignment_connect4.ipynb` hoàn thành Task 1-5 và chạy được.
- [ ] Ba file test Connect 4 pass.
- [ ] Có đủ sáu câu trả lời thảo luận và tối thiểu 3-5 nhận xét tổng hợp.
- [ ] README có hướng dẫn cài đặt và chạy.
- [ ] Không sửa/nộp các notebook mở rộng không được chọn.

