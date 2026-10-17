# Kế hoạch chi tiết Tuần 1 - Nền tảng AI Caro

> Thời lượng: 5 ngày làm việc  
> Mục tiêu tuần: chốt luật và hợp đồng dữ liệu, tạo bộ khung engine, tạo UI dùng dữ liệu giả lập, chuẩn bị test để ba nhánh có thể phát triển độc lập từ Tuần 2.

## 1. Kết quả bắt buộc cuối tuần

Cuối Tuần 1, nhóm phải có một bản `w1-foundation` chạy được với các kết quả sau:

- Luật Caro và cách biểu diễn state/action được ghi rõ, không còn điểm mơ hồ giữa các thành viên.
- API game có chữ ký hàm, kiểu dữ liệu input/output và quy ước lỗi thống nhất.
- Engine tạo được bàn cờ, đặt quân hợp lệ và liệt kê được nước đi hợp lệ.
- Nước đi ngoài bàn, ô đã có quân hoặc đánh sai lượt đều bị từ chối.
- UI hiển thị được bàn 9x9, nhận click và chạy được bằng `MockGameEnv`.
- Có test contract và test cho các thao tác nền tảng.
- Mỗi thành viên có Pull Request riêng; không sửa trực tiếp file thuộc quyền sở hữu của người khác.

## 2. Quyết định phải chốt trước khi viết code

Ba thành viên họp tối đa 60 phút vào đầu ngày 1. M3 ghi biên bản, M2 xác nhận tính đúng của luật, M1 xác nhận dữ liệu đủ dùng cho UI.

| Hạng mục | Giá trị đề xuất cho `caro-v1` | Người xác nhận |
|---|---|---|
| Kích thước bàn | `9 x 9` | Cả nhóm |
| Giá trị ô | `0 = EMPTY`, `1 = PLAYER_X`, `-1 = PLAYER_O` | M2 + M3 |
| Action | Số nguyên `0..80`; `row = action // 9`, `col = action % 9` | M1 + M3 |
| Điều kiện thắng | Có từ 5 quân liên tiếp và không bị chặn cả hai đầu | M2 |
| Overline | Từ 6 quân trở lên vẫn được xét theo quy tắc trên | M2, hỏi lại giảng viên nếu cần |
| Luật cấm | Không áp dụng luật cấm Renju | Cả nhóm |
| Điều kiện hòa | Bàn đầy và chưa có người thắng | M2 + M3 |
| Người đi trước | `PLAYER_X = 1` | Cả nhóm |
| Tính ngẫu nhiên | Mọi module có yếu tố ngẫu nhiên phải nhận `seed` | M3 |

Nếu giảng viên yêu cầu luật khác, M3 sửa tài liệu contract và tăng `game_version` trước khi M2/M1 tiếp tục tích hợp.

## 3. Hợp đồng dữ liệu dùng chung

Đây là input/output tối thiểu mà cả ba thành viên phải dùng. Không tự ý đổi tên trường hoặc kiểu dữ liệu sau khi PR contract đã được merge.

### 3.1. `GameConfig`

```python
GameConfig(
    board_size=9,
    win_length=5,
    blocked_both_ends=True,
    first_player=1,
)
```

### 3.2. `GameState`

```python
GameState(
    board: np.ndarray,       # shape=(9, 9), dtype=np.int8
    current_player: int,     # 1 hoặc -1
    last_action: int | None,
    move_count: int,
    terminated: bool,
    winner: int | None,      # 1, -1, 0 nếu hòa, None nếu chưa kết thúc
)
```

### 3.3. API môi trường

| Hàm | Input | Output | Yêu cầu |
|---|---|---|---|
| `reset(seed=None)` | `int \| None` | `GameState` mới | Bàn rỗng, X đi trước |
| `legal_actions()` | Không | `list[int]` | Chỉ trả về ô trống; danh sách rỗng khi game kết thúc |
| `step(action)` | `int` trong `0..80` | `StepResult` | Không được sửa state nếu action không hợp lệ |
| `is_terminal()` | Không | `bool` | Đúng khi thắng hoặc hòa |
| `result(player)` | `1` hoặc `-1` | `1`, `0`, `-1` hoặc `None` | Kết quả theo góc nhìn `player` |
| `clone()` | Không | Game environment độc lập | Sửa clone không ảnh hưởng bản gốc |
| `render()` | Không | `str` hoặc dữ liệu cho UI | Không chứa logic thay đổi state |

`StepResult` tối thiểu gồm:

```python
StepResult(
    state: GameState,
    reward: int,             # Theo góc nhìn người vừa thực hiện action
    terminated: bool,
    info: dict,
)
```

Lỗi action không hợp lệ phải phát sinh `InvalidActionError` và giữ nguyên toàn bộ state.

---

## 4. M1 - Trần Hồ Minh Hải

### Vai trò trong Tuần 1

Thiết kế trải nghiệm chơi và xây dựng UI skeleton không phụ thuộc engine đang hoàn thiện. M1 chỉ dùng contract do M3 công bố; không import trực tiếp biến nội bộ từ `board.py`.

### W1-M1-01 - Thiết kế luồng màn hình

**Công việc cụ thể**

1. Vẽ wireframe cho một màn hình chơi chính.
2. Xác định vị trí bàn cờ, trạng thái lượt, nút New Game, vùng thông báo lỗi và khu vực chọn chế độ.
3. Quy định trạng thái trực quan cho ô trống, quân X, quân O, nước vừa đi và game kết thúc.
4. Ghi lại mapping từ click `(row, col)` sang `action` dạng số nguyên.

**Input**

- Quyết định luật `caro-v1`.
- `GameState` và quy tắc mã hóa action từ M3.
- Kích thước bàn `9 x 9` từ M2/M3.

**Output**

- `docs/ui/wireframe_week1.png` hoặc `docs/ui/wireframe_week1.md`.
- Danh sách component và trạng thái giao diện.
- Bảng mapping sự kiện UI -> lời gọi API.

**Công cụ**

- Figma, Excalidraw hoặc Markdown.
- Không dùng công cụ thiết kế cũng được nếu wireframe được mô tả rõ trong Markdown.

**Tiêu chí hoàn thành**

- Người khác nhìn wireframe biết phải click ở đâu để bắt đầu và đánh một nước.
- Có trạng thái disabled sau khi game kết thúc.
- Có vị trí hiển thị lỗi khi action bị engine từ chối.

### W1-M1-02 - Tạo `MockGameEnv`

**Công việc cụ thể**

1. Tạo một adapter giả lập có cùng chữ ký với contract của M3.
2. Hỗ trợ `reset()`, `legal_actions()` và `step(action)` ở mức đủ cho UI.
3. Dùng dữ liệu giả lập; chưa cài logic thắng/thua hoàn chỉnh trong mock.
4. Đảm bảo có thể thay mock bằng engine thật mà không sửa component hiển thị bàn cờ.

**Input**

- File contract đã được merge.
- Kiểu `GameState`, `StepResult` và `InvalidActionError`.

**Output**

- `ui/mock_game_env.py`.
- Một script hoặc test nhỏ chứng minh mock tuân theo chữ ký API.

**Công cụ**

- Python.
- `dataclasses` và NumPy.
- `pytest` cho smoke test.

**Tiêu chí hoàn thành**

- Mock trả về board shape `(9, 9)` và `dtype=np.int8`.
- Click vào ô trống cập nhật được bàn cờ.
- Click lại ô đã có quân trả về lỗi rõ ràng.

### W1-M1-03 - Xây dựng UI skeleton

**Công việc cụ thể**

1. Tạo ứng dụng Streamlit tối thiểu trong `ui/app.py`.
2. Render bàn 9x9 từ `GameState.board`.
3. Chuyển click thành action và gọi `env.step(action)`.
4. Hiển thị người đang đến lượt, số nước đã đi và lỗi action.
5. Thêm nút `New Game` gọi `reset()`.

**Input**

- Wireframe W1-M1-01.
- `MockGameEnv` W1-M1-02.
- Contract API của M3.

**Output**

- `ui/app.py` chạy được bằng mock.
- Ảnh chụp màn hình trong Pull Request.
- Hướng dẫn chạy UI tối đa 3 lệnh.

**Công cụ**

- Streamlit.
- Python, NumPy.
- Trình duyệt để kiểm tra thủ công.

**Tiêu chí hoàn thành**

- Chơi thử được tối thiểu 10 nước liên tiếp bằng mock.
- Bàn cờ không mất state khi Streamlit rerun.
- UI không chứa logic xác định thắng/thua.

### Nhánh và commit của M1

- Nhánh: `feature/w1-ui-hai`
- Commit đề xuất:
  - `docs(ui): add week-1 game screen wireframe`
  - `feat(ui): add contract-compatible mock environment`
  - `feat(ui): add interactive 9x9 board skeleton`

---

## 5. M2 - Lê Thị Trúc Ly

### Vai trò trong Tuần 1

Xây dựng cấu trúc bàn cờ và thao tác state nền tảng. Tuần 1 chưa cần hoàn thiện toàn bộ thuật toán kiểm tra thắng; mục tiêu là cung cấp engine skeleton đúng contract để Tuần 2 bổ sung luật đầy đủ.

### W1-M2-01 - Xác nhận luật và test vector biên

**Công việc cụ thể**

1. Kiểm tra các quyết định luật ở Mục 2.
2. Mô tả ví dụ hàng ngang, dọc và hai đường chéo.
3. Đưa ra ví dụ chuỗi 5 quân bị chặn hai đầu và chuỗi không bị chặn hai đầu.
4. Xác định rõ cách xử lý overline và các vị trí sát biên.

**Input**

- Yêu cầu đề tài Game AI.
- Biên bản chốt luật đầu tuần.

**Output**

- Phần luật đã xác nhận trong contract.
- Tối thiểu 8 test vector dạng board/action/expected-result gửi M3.

**Công cụ**

- Markdown hoặc JSON.
- Có thể dùng NumPy để tạo fixture.

**Tiêu chí hoàn thành**

- Có test vector cho 4 hướng thắng.
- Có trường hợp sát biên, bị chặn hai đầu, bàn chưa kết thúc và bàn hòa.
- Không còn câu hỏi mở về cách xác định thắng trong `caro-v1`.

### W1-M2-02 - Cài đặt cấu trúc `Board`

**Công việc cụ thể**

1. Tạo board NumPy `9 x 9`, `dtype=np.int8`.
2. Cài đặt chuyển đổi `action <-> (row, col)`.
3. Cài đặt kiểm tra action trong biên và ô trống.
4. Cài thao tác đặt quân nội bộ có kiểm tra hợp lệ.
5. Cung cấp bản sao độc lập của board để tránh thay đổi ngoài ý muốn.

**Input**

- `GameConfig` và encoding action từ contract của M3.
- Các quy tắc đã xác nhận ở W1-M2-01.

**Output**

- `core/engine/board.py`.
- Các hàm chuyển đổi action/coordinate.
- Unit test riêng cho board nếu M2 cần kiểm tra trước khi giao M3.

**Công cụ**

- Python, NumPy.
- `pytest`.

**Tiêu chí hoàn thành**

- Board mới luôn có 81 ô trống.
- `action_to_coord()` và `coord_to_action()` đảo ngược chính xác cho toàn bộ 81 ô.
- Action `< 0`, `> 80` và ô đã có quân đều bị từ chối.
- Trả board ra ngoài không cho phép vô tình sửa state nội bộ.

### W1-M2-03 - Cài đặt state transition cơ bản

**Công việc cụ thể**

1. Tạo state ban đầu: board rỗng, X đi trước, `move_count=0`.
2. Sau nước đi hợp lệ, cập nhật board, `last_action`, `move_count` và đổi lượt.
3. Đảm bảo nước đi lỗi không làm đổi bất kỳ trường nào của state.
4. Chuẩn bị hook `check_terminal()` để Tuần 2 bổ sung luật thắng đầy đủ.

**Input**

- `Board` từ W1-M2-02.
- `GameState`, `StepResult` và lỗi chuẩn từ contract.

**Output**

- `core/engine/rules.py` với chữ ký hàm kiểm tra.
- Phần xử lý state cơ bản trong module engine được nhóm thống nhất.
- Bản demo terminal nhỏ: reset -> step -> in state.

**Công cụ**

- Python, NumPy.
- `pytest`.

**Tiêu chí hoàn thành**

- Sau một action hợp lệ, đúng một ô thay đổi.
- Người chơi được đổi từ `1` sang `-1` hoặc ngược lại.
- `move_count` tăng đúng một.
- State không bị sửa nếu action không hợp lệ.

### Nhánh và commit của M2

- Nhánh: `feature/w1-engine-ly`
- Commit đề xuất:
  - `docs(rules): confirm caro-v1 edge cases`
  - `feat(engine): add board and action encoding`
  - `feat(engine): add basic state transitions`

---

## 6. M3 - Trương Văn Thiện

### Vai trò trong Tuần 1

Sở hữu contract API, fixture và test tích hợp. M3 merge trước để M1/M2 có một nguồn sự thật duy nhất về input/output.

### W1-M3-01 - Viết đặc tả `caro-v1`

**Công việc cụ thể**

1. Ghi lại toàn bộ quyết định luật của cuộc họp đầu tuần.
2. Định nghĩa `GameConfig`, `GameState`, `StepResult` và `InvalidActionError`.
3. Định nghĩa chính xác input/output của từng API.
4. Ghi rõ reward/result theo góc nhìn người chơi.
5. Đưa ví dụ JSON hoặc Python cho một state hợp lệ.

**Input**

- Yêu cầu đồ án.
- Biên bản chốt luật của cả nhóm.
- Test vector luật do M2 cung cấp.
- Nhu cầu hiển thị state/action do M1 cung cấp.

**Output**

- `docs/contracts/caro_v1.md`.
- `core/engine/interfaces.py` hoặc module kiểu dữ liệu tương đương.
- `tests/fixtures/caro_v1_cases.json`.

**Công cụ**

- Markdown, Python `dataclasses` hoặc `typing`.
- JSON.

**Tiêu chí hoàn thành**

- M1 có thể viết mock mà không hỏi thêm cấu trúc dữ liệu.
- M2 có thể viết board/state mà không tự đặt thêm quy ước.
- Mọi trường dữ liệu đều có kiểu, miền giá trị và ý nghĩa.

### W1-M3-02 - Tạo skeleton `GameEnv`

**Công việc cụ thể**

1. Tạo lớp hoặc protocol cho API môi trường.
2. Khai báo các hàm `reset`, `legal_actions`, `step`, `is_terminal`, `result`, `clone`, `render`.
3. Kết nối với `Board` của M2 sau khi PR M2 sẵn sàng.
4. Không cài luật thắng trùng với phần sở hữu của M2.

**Input**

- Contract W1-M3-01.
- `Board` và state transition của M2.

**Output**

- `core/engine/game_env.py`.
- Một ví dụ chạy reset -> legal actions -> step.

**Công cụ**

- Python.
- `typing.Protocol` hoặc abstract base class nếu cần.

**Tiêu chí hoàn thành**

- `reset()` trả state hợp lệ.
- Ban đầu `legal_actions()` có đúng 81 action.
- Sau một nước hợp lệ còn 80 action.
- API không làm lộ biến nội bộ có thể sửa trực tiếp.

### W1-M3-03 - Viết contract tests và CI tối thiểu

**Công việc cụ thể**

1. Test reset và kích thước/kiểu board.
2. Test danh sách nước đi hợp lệ trước và sau một action.
3. Test action ngoài biên.
4. Test đánh vào ô đã có quân.
5. Test state không đổi sau action lỗi.
6. Test clone độc lập.
7. Thiết lập lệnh test dùng chung cho nhóm.

**Input**

- `GameEnv` skeleton.
- Test vector từ M2.
- Contract đã merge.

**Output**

- `tests/test_game_env_contract.py`.
- `tests/test_invalid_actions.py`.
- Cấu hình CI hoặc lệnh `pytest` được ghi trong README.
- Báo cáo test pass trong Pull Request.

**Công cụ**

- `pytest`, `pytest-cov`.
- GitHub Actions nếu repository đã kết nối GitHub.

**Tiêu chí hoàn thành**

- Tất cả test Tuần 1 chạy xanh.
- Test lỗi xác nhận cả loại exception và việc state không đổi.
- Test chạy được bằng một lệnh trên máy thành viên khác.

### Nhánh và commit của M3

- Nhánh contract: `docs/w1-contract-thien`
- Nhánh test/integration: `test/w1-engine-contract-thien`
- Commit đề xuất:
  - `docs(contract): define caro-v1 state action and API`
  - `feat(engine): add game environment interface`
  - `test(engine): add API and invalid-action contract tests`
  - `ci(test): run week-1 engine tests`

---

## 7. Thứ tự thực hiện và merge

Không merge theo thời điểm ai làm xong trước. Merge theo dependency sau:

```text
1. M3: contract + interfaces
        |
        +--> 2A. M2: Board + state transition
        |
        +--> 2B. M1: MockGameEnv + UI skeleton
                    |
3. M3: nối GameEnv với Board + bật contract tests
                    |
4. M1: smoke test UI với engine thật nếu API đã ổn định
                    |
5. Cả nhóm: review + merge integration + tag w1-foundation
```

| Thứ tự | PR | Người mở | Người review bắt buộc | Điều kiện merge |
|---:|---|---|---|---|
| 1 | Contract `caro-v1` | M3 | M1 và M2 | Hai người approve; không còn comment về I/O |
| 2 | Board/state skeleton | M2 | M3 | Unit test board xanh; đúng contract |
| 3 | UI + mock | M1 | M3 | Mock đúng contract; UI chạy được |
| 4 | GameEnv + contract tests | M3 | M2 | Test API và invalid action xanh |
| 5 | Integration Week 1 | M3 | M1 và M2 | Cả test và UI smoke test đều đạt |

## 8. Lịch làm việc gợi ý trong 5 ngày

| Ngày | M1 - Hải | M2 - Ly | M3 - Thiện | Điểm đồng bộ |
|---|---|---|---|---|
| Ngày 1 | Nêu yêu cầu dữ liệu UI, vẽ wireframe | Chốt luật và edge cases | Ghi contract, kiểu dữ liệu | Họp chốt D0 và API |
| Ngày 2 | Tạo mock theo contract | Cài `Board` và action encoding | Merge contract, tạo fixtures | Contract phải merge trước cuối ngày |
| Ngày 3 | Xây UI skeleton | Cài state transition | Tạo `GameEnv` skeleton | M3 kiểm tra hai nhánh không lệch API |
| Ngày 4 | Hoàn thiện state UI và lỗi | Fix theo contract tests | Viết test API/invalid action | Chạy test chéo trên máy khác |
| Ngày 5 | Thử UI với engine thật | Review luật/state | Tích hợp và CI | Demo nội bộ, retrospective 30 phút |

## 9. Checklist nghiệm thu Tuần 1

### Contract

- [ ] Luật `caro-v1` đã được cả nhóm duyệt.
- [ ] Board, player, action và winner có encoding rõ ràng.
- [ ] Input/output của mọi API có kiểu dữ liệu cụ thể.
- [ ] Có quy ước lỗi và cam kết state không đổi khi action sai.

### Engine

- [ ] Reset tạo board rỗng 9x9.
- [ ] Có đúng 81 legal actions khi bắt đầu.
- [ ] Đặt quân hợp lệ làm giảm legal actions còn 80.
- [ ] Action ngoài biên và ô đã có quân bị từ chối.
- [ ] Clone không chia sẻ board có thể thay đổi với bản gốc.

### UI

- [ ] Render đủ 81 ô.
- [ ] Click được và chuyển đúng sang action.
- [ ] Hiển thị lượt chơi và lỗi.
- [ ] Nút New Game hoạt động.
- [ ] UI không chứa logic luật game.

### Git và tích hợp

- [ ] Mỗi người làm trên nhánh riêng.
- [ ] Mỗi PR chỉ thay đổi phần thuộc phạm vi đã phân công.
- [ ] Tất cả test Tuần 1 chạy xanh.
- [ ] Có ảnh hoặc video demo ngắn trong PR tích hợp.
- [ ] Tạo tag hoặc release nội bộ `w1-foundation`.

## 10. Những việc chưa làm trong Tuần 1

Để tránh vượt phạm vi, các mục sau chuyển sang tuần sau:

- Hoàn thiện mọi trường hợp thắng/hòa và luật chặn hai đầu.
- Random, Heuristic, Alpha-Beta, MCTS hoặc Neural Network.
- Backend FastAPI nếu Streamlit có thể gọi trực tiếp Python.
- Self-play, huấn luyện, tournament và biểu đồ.
- Tối ưu hiệu năng hoặc thay đổi kích thước bàn linh hoạt.

Tuần 1 chỉ được xem là hoàn thành khi contract ổn định, engine skeleton đúng, test xanh và UI có thể thay mock bằng engine mà không đổi cách biểu diễn state/action.
