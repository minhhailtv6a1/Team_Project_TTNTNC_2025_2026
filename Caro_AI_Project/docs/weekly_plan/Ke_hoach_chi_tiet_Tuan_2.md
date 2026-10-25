# Kế hoạch chi tiết Tuần 2 - Luật đầy đủ và tích hợp Engine AI Caro

> **Cập nhật phạm vi:** 11x11 là module chính và là kích thước duy nhất được phát triển/kiểm thử. 9x9 tạm ngưng; kiến trúc vẫn tham số hóa theo `board_size` để mở rộng sau.

> Thời lượng: 5 ngày làm việc  
> Điều kiện bắt đầu: Tuần 1 đã merge, toàn bộ test xanh và có mốc `w1-foundation`.  
> Mục tiêu tuần: hoàn thiện luật thắng/hòa, terminal, clone/undo; khóa contract `caro-v1`; nối UI với engine thật; thiết lập CI với coverage lõi tối thiểu 90%.

## 1. Kết quả bắt buộc cuối tuần

Cuối Tuần 2, nhóm phải có một bản `caro-v1` chạy end-to-end với các kết quả sau:

- Engine xác định đúng thắng theo 4 hướng: ngang, dọc, chéo chính và chéo phụ.
- Các trường hợp sát biên, chặn một đầu, chặn hai đầu, overline và hòa được đặc tả và kiểm thử.
- `step()` từ chối action bất hợp lệ hoặc action sau khi game đã kết thúc mà không làm đổi state.
- `legal_actions()` trả danh sách rỗng khi game kết thúc.
- `result(player)`, `clone_env()` và `undo()` có hành vi rõ ràng, được kiểm thử.
- UI mặc định sử dụng `CaroEnv`, không dùng `MockGameEnv` trong luồng chạy production.
- Chơi hoàn chỉnh được một ván Human vs Human trên UI, có banner kết quả và nút Play Again.
- Test engine đạt tối thiểu 90% statement coverage; riêng `game_env.py` đạt tối thiểu 90%.
- CI chạy tự động trên Python 3.13 và chặn merge khi test hoặc coverage thất bại.
- Contract, code, test và UI dùng cùng một encoding state/action.
- Merge đúng thứ tự dependency và tạo tag nội bộ `caro-v1`.

## 2. Baseline sau Tuần 1 và khoảng trống cần xử lý

Kế hoạch Tuần 2 dựa trên trạng thái thực tế của repository, không giả định lại từ đầu.

| Hạng mục | Baseline hiện tại | Đích cuối Tuần 2 | Owner chính |
|---|---|---|---|
| Engine tests | 160 test engine pass | Bổ sung terminal, undo, property/regression tests | M3 |
| Coverage `core.engine` | Tổng 90% | Giữ `>=90%` | M3 |
| Coverage `game_env.py` | 77% | `>=90%` | M2 + M3 |
| Luật thắng | Đã có `RuleEngine`, cần kiểm chứng thêm | Đúng toàn bộ test vector biên | M2 |
| `result()` | Chưa cài đặt | Trả kết quả đúng theo góc nhìn player | M2 |
| `undo()` | Chưa có | Hoàn tác một nước, khôi phục đủ metadata | M2 |
| Terminal guard | Chưa khóa đầy đủ | Không cho đi tiếp sau thắng/hòa | M2 |
| Default board | Code/contract từng lệch 9x9 và 11x11 | 11x11 là module duy nhất đang hoạt động | M3 chốt |
| Action public | UI/contract dùng `(row, col)`, `Board` có action `int` nội bộ | Public dùng tuple, int chỉ là chi tiết nội bộ | M3 chốt |
| Overline | Tài liệu có chỗ ghi “đúng 5”, có chỗ ghi “từ 5” | Chốt một quy tắc duy nhất | M2 + M3 |
| UI runtime | Dùng `MockGameEnv` | Dùng `CaroEnv` thật | M1 |
| UI test | AppTest với mock | AppTest và browser smoke với engine thật | M1 + M3 |
| CI | Chưa có cổng coverage ổn định | Test + coverage tự động | M3 |

### 2.1. Việc phải kiểm tra trước khi mở nhánh Tuần 2

```powershell
git status
git pull --ff-only
python -m pytest tests -q
python -m pytest tests/test_board.py tests/test_rules.py `
  tests/test_game_env_contract.py tests/test_invalid_actions.py `
  --cov=core.engine --cov-report=term-missing
```

Nếu baseline không xanh, người làm phát hiện lỗi báo cả nhóm và sửa trên nhánh Tuần 1 trước; không trộn bugfix nền tảng vào PR tính năng Tuần 2.

## 3. Quyết định phải khóa trong Ngày 1

Ba thành viên họp tối đa 75 phút. M3 ghi biên bản và cập nhật contract; M2 xác nhận luật; M1 xác nhận UI có đủ metadata.

| Hạng mục | Giá trị đề xuất cho `caro-v1` | Người duyệt | Test bắt buộc |
|---|---|---|---|
| Bàn mặc định | `11 x 11`; kích thước khác tạm ngưng | Cả nhóm | Reset có 121 legal actions |
| Giá trị ô | `EMPTY=0`, `X=1`, `O=-1` | M2 + M3 | Dtype/miền giá trị hợp lệ |
| Public action | `Action = tuple[int, int]` dạng `(row, col)` | M1 + M3 | Biên âm, biên trên, ô đã chiếm |
| Action nội bộ Board | Có thể dùng `int`, nhưng không lộ ra UI/Agent | M2 + M3 | Round-trip int ↔ tuple |
| Luật thắng đề xuất | Có `>=5` quân liên tiếp và không bị chặn cả hai đầu | M2 | 4 hướng + blocked cases |
| Overline | Được tính thắng theo đề xuất trên | M2 + giảng viên nếu cần | Chuỗi 6/7 quân |
| Biên bàn cờ | Biên được xem là một đầu bị chặn | M2 | Chuỗi sát cả 4 biên |
| Hòa | Bàn đầy, chưa có người thắng | M2 + M3 | Full-board draw fixture |
| Step sau terminal | Raise `InvalidActionError`, state giữ nguyên | M2 + M3 | State snapshot trước/sau |
| `legal_actions()` terminal | Trả `[]` | M3 | Win và draw |
| `result(player)` | `1.0`, `0.0`, `-1.0`, hoặc `None` nếu chưa xong | M2 + M3 | X/O/draw/non-terminal |
| Reward của `step()` | Theo góc nhìn người vừa đi | M2 + M3 | Win=1, draw=0 |
| `undo()` | Hoàn tác đúng một nước; lỗi nếu history rỗng | M2 + M3 | Board/lượt/terminal khôi phục |
| State metadata | `last_action`, `move_count`, `terminated`, `winner` | M1 + M3 | Reset/step/undo/clone |
| Tính ngẫu nhiên | API có `seed` khi module dùng random | M3 | Reproducibility smoke |

Nếu nhóm hoặc giảng viên chọn “đúng 5” thay vì “từ 5 trở lên”, M3 phải cập nhật contract và fixture trước khi M2 merge luật. Không được để code và tài liệu dùng hai quy tắc khác nhau.

### 3.1. Contract public dự kiến sau khi freeze

```python
Action = tuple[int, int]

@dataclass(frozen=True)
class GameState:
    board: list[list[int]]
    current_player: Player
    last_action: Action | None = None
    move_count: int = 0
    terminated: bool = False
    winner: Player | None = None

class CaroEnv:
    def reset(self, seed: int | None = None) -> GameState: ...
    def legal_actions(self) -> list[Action]: ...
    def step(self, action: Action) -> StepResult: ...
    def is_terminal(self) -> bool: ...
    def result(self, player: Player) -> float | None: ...
    def clone_env(self) -> "CaroEnv": ...
    def undo(self) -> GameState: ...
    def render(self) -> str: ...
```

Tên field cuối cùng phải theo contract do M3 merge. Đoạn trên là mục tiêu để cả nhóm thảo luận, không phải lý do để từng nhánh tự sửa interface theo cách riêng.

---

## 4. M1 - Trần Hồ Minh Hải

### Vai trò trong Tuần 2

Thay môi trường giả lập bằng engine thật và hoàn thiện luồng chơi Human vs Human. M1 chỉ đọc public contract; không truy cập trực tiếp `Board.grid`, hàm private trong `RuleEngine` hoặc history stack nội bộ của engine.

### W2-M1-01 - Tạo adapter UI cho `CaroEnv`

**Công việc cụ thể**

1. Liệt kê tất cả thuộc tính UI đang đọc từ `MockGameEnv`.
2. Mapping chúng sang `GameState`, `StepResult` và public API đã freeze.
3. Tạo factory hoặc adapter để production khởi tạo `CaroEnv`.
4. Loại bỏ type hint và import production phụ thuộc trực tiếp `MockGameEnv`.
5. Giữ mock chỉ cho test cô lập nếu còn cần; không dùng mock khi chạy `streamlit run`.
6. Đảm bảo đổi board size tạo đúng `GameConfig` và reset session state liên quan.

**Input**

- Contract `caro-v1` đã được M3 cập nhật.
- `CaroEnv` có terminal/result/clone/undo từ M2.
- UI và AppTest hoàn thành ở W1-M1-03.

**Output**

- `ui/app.py` chạy với engine thật.
- `ui/game_adapter.py` hoặc module tương đương nếu cần adapter.
- Test xác nhận runtime production không khởi tạo `MockGameEnv`.
- Bảng mapping mock field → contract field trong mô tả PR.

**Công cụ**

- Python, Streamlit.
- `typing.Protocol` hoặc type alias nếu cần.
- `streamlit.testing.v1.AppTest`.

**Tiêu chí hoàn thành**

- `streamlit run ui/app.py` khởi tạo `CaroEnv` thật.
- Render đủ 121 ô ở cấu hình mặc định.
- Click UI truyền đúng tuple `(row, col)` cho engine.
- UI không import `Board` hoặc gọi hàm private của `RuleEngine`.
- Thay đổi bên trong engine không buộc sửa component render board.

### W2-M1-02 - Hoàn thiện HumanAgent/controller và Human vs Human

**Công việc cụ thể**

1. Tạo `HumanAgent` hoặc controller mỏng nhận action từ click UI.
2. Không đặt luật thắng/thua trong controller; chỉ gọi `env.step(action)`.
3. Đồng bộ X/O, lượt chơi, move count, last action và move history từ kết quả engine.
4. Khi terminal, disable toàn bộ ô và hiện đúng winner/draw.
5. Nút New Game và Play Again phải gọi `env.reset()`.
6. Đổi mode hoặc board size phải reset sạch ván hiện tại nhưng giữ thống kê phiên theo đặc tả UI.

**Input**

- W2-M1-01.
- `StepResult.done`, `StepResult.winner` và metadata state đã freeze.
- Test vector thắng/hòa từ M2/M3.

**Output**

- `core/agents/human_agent.py` hoặc `ui/human_controller.py` theo quyết định kiến trúc.
- Luồng Human vs Human chơi được từ đầu đến kết thúc.
- Banner X thắng, O thắng và hòa lấy dữ liệu từ engine.
- Move history khớp chính xác action đã gửi.

**Công cụ**

- Streamlit, session state.
- AppTest và trình duyệt.

**Tiêu chí hoàn thành**

- Chơi được một ván có người thắng mà UI không tự kiểm tra chuỗi 5.
- Không thể click tiếp sau khi terminal.
- New Game xóa board/history/error và đưa lượt về X.
- Winner, move count và last action không lệch sau Streamlit rerun.

### W2-M1-03 - Regression test UI với engine thật

**Công việc cụ thể**

1. Chuyển test UI hiện có từ mock sang `CaroEnv` thật hoặc fixture engine theo contract.
2. Test ít nhất một chuỗi X thắng và một chuỗi O thắng.
3. Test cảnh báo ô đã chiếm và state không đổi.
4. Test terminal disable board, banner kết quả và Play Again.
5. Test cấu hình 11x11 và từ chối kích thước chưa được hỗ trợ.
6. Browser smoke ở viewport 1280x720 và viewport desktop lớn.
7. Chụp ảnh trạng thái đầu ván, giữa ván và kết thúc để đính kèm PR.

**Input**

- W2-M1-02.
- Fixtures terminal của M3.

**Output**

- `tests/test_ui_app.py` chạy với engine thật.
- Ảnh smoke test UI trong PR.
- Hướng dẫn chạy UI cập nhật trong `README.md` nếu lệnh thay đổi.

**Công cụ**

- `pytest`, AppTest.
- Trình duyệt và Streamlit.

**Tiêu chí hoàn thành**

- Test UI không monkeypatch logic thắng/thua.
- Test tái hiện được winner do engine trả về.
- Bàn 11x11 không vỡ layout; công thức kích thước ô không hard-code theo từng size.
- Toàn bộ test W1-M1-03 tiếp tục xanh.

### Nhánh và commit của M1

- Nhánh: `feature/w2-ui-engine-hai`
- Bắt đầu sau khi PR engine của M2 và contract/test của M3 đã merge.
- Commit đề xuất:
  - `refactor(ui): connect streamlit app to caro env`
  - `feat(ui): add human controller and terminal flow`
  - `test(ui): cover real-engine game flow`

---

## 5. M2 - Lê Thị Trúc Ly

### Vai trò trong Tuần 2

Sở hữu tính đúng đắn của luật và state transition. M2 triển khai theo fixture/contract đã chốt, không sửa UI và không thay public interface nếu chưa có approval của M3.

### W2-M2-01 - Hoàn thiện luật thắng và test vector biên

**Công việc cụ thể**

1. Rà lại `RuleEngine.check_line()` và `check_winner()` theo quyết định Ngày 1.
2. Kiểm tra ngang, dọc, chéo chính và chéo phụ cho cả X/O.
3. Kiểm tra chuỗi bắt đầu/kết thúc tại biên bàn.
4. Kiểm tra không chặn, chặn một đầu, chặn hai đầu.
5. Kiểm tra overline theo luật đã freeze.
6. Đảm bảo không nhận diện thắng giả từ hai chuỗi rời nhau.
7. Tối ưu kiểm tra quanh `last_action` nếu không làm phức tạp contract; correctness ưu tiên trước.

**Input**

- Quyết định luật ở Mục 3.
- Fixtures W1 và test matrix của M3.
- `core/engine/rules.py` hiện tại.

**Output**

- `core/engine/rules.py` hoàn chỉnh.
- Test đơn vị của M2 cho từng hướng và edge case.
- Bảng test vector board/action/expected winner gửi M3.

**Công cụ**

- Python, NumPy hoặc list board theo contract.
- `pytest.mark.parametrize`.
- Profiling nhỏ nếu thay thuật toán quét.

**Tiêu chí hoàn thành**

- Tất cả trường hợp thắng hợp lệ trả đúng winner.
- Chặn hai đầu không trả winner.
- Board chưa kết thúc trả `None`.
- Kết quả nhất quán trên cấu hình 11x11.
- Không có mutation trong hàm kiểm tra thuần.

### W2-M2-02 - Hoàn thiện terminal, reward và `result()`

**Công việc cụ thể**

1. Sau `step()`, cập nhật metadata rồi kiểm tra terminal đúng một lần.
2. Tính reward theo góc nhìn người vừa đi.
3. Cài `result(player)` theo contract.
4. Khi terminal, `legal_actions()` trả `[]`.
5. `step()` sau terminal raise lỗi và giữ nguyên toàn bộ state.
6. Hòa chỉ xảy ra khi bàn đầy và chưa có winner.
7. `reset()` xóa winner, terminal, last action và move count.
8. Xóa TODO/mock code không còn sử dụng trong `game_env.py`.

**Input**

- W2-M2-01.
- Public interface do M3 freeze.
- `core/engine/game_env.py` hiện tại.

**Output**

- `CaroEnv.step`, `is_terminal`, `result`, `legal_actions`, `reset` hoàn chỉnh.
- Exception/message nhất quán cho invalid action và terminal action.
- Không còn `pass` hoặc TODO ảnh hưởng luồng production.

**Công cụ**

- Python, dataclasses.
- `pytest`.

**Tiêu chí hoàn thành**

- Win: `done=True`, winner đúng, reward người vừa đi bằng `1.0`.
- Draw: `done=True`, winner `None`, reward `0.0`.
- Non-terminal: `done=False`, winner `None`, result `None`.
- Action lỗi và action sau terminal không đổi state.
- `game_env.py` không còn nhánh mock.

### W2-M2-03 - Cài clone đầy đủ và `undo()`

**Công việc cụ thể**

1. Thiết kế history stack nội bộ đủ để undo một nước.
2. `undo()` khôi phục board, current player, last action, move count, terminal và winner.
3. Undo sau nước thắng phải mở lại game đúng cách.
4. Undo khi chưa có nước đi phải raise lỗi rõ ràng và không đổi state.
5. `clone_env()` phải sao chép độc lập board, metadata và history.
6. Thay đổi clone hoặc undo clone không ảnh hưởng môi trường gốc.
7. Ghi benchmark tham khảo cho clone/step; chưa đặt ngưỡng thời gian cứng trong CI.

**Input**

- W2-M2-02.
- Contract clone/undo đã được M3 duyệt.

**Output**

- `undo()` và `clone_env()` hoàn chỉnh.
- Unit test clone/undo do M2 viết trước khi giao M3 regression.
- Ghi chú độ phức tạp và lựa chọn copy trong docstring/PR.

**Công cụ**

- Python `copy` hoặc snapshot nhẹ.
- `pytest`, `time.perf_counter` cho benchmark tham khảo.

**Tiêu chí hoàn thành**

- Step → undo trả state bằng chính xác state trước step.
- N step → N undo trả board ban đầu.
- Clone không chia sẻ board/history có thể mutate.
- Undo không làm sai legal actions hoặc lượt chơi.

### Nhánh và commit của M2

- Nhánh: `feature/w2-rules-engine-ly`
- M2 mở PR code đầu tiên của Tuần 2 sau khi quyết định luật được ghi lại.
- Commit đề xuất:
  - `test(rules): add blocked-edge and overline vectors`
  - `feat(engine): complete terminal reward and result`
  - `feat(engine): add independent clone and undo`

---

## 6. M3 - Trương Văn Thiện

### Vai trò trong Tuần 2

Sở hữu contract freeze, test độc lập, coverage và CI. M3 không viết lại thuật toán luật của M2; M3 chứng minh implementation tuân theo contract và bảo vệ các invariant.

### W2-M3-01 - Đồng bộ và freeze contract `caro-v1`

**Công việc cụ thể**

1. Ghi biên bản các quyết định ở Mục 3.
2. Đồng bộ `docs/contract`, `interfaces.py` và fixtures.
3. Chốt default board, public action, metadata state, result và undo.
4. Đảm bảo field mới có default hợp lý hoặc có migration rõ ràng.
5. Ghi changelog từ `w1-foundation` sang `caro-v1`.
6. Thông báo freeze trước khi M1 bắt đầu adapter UI.

**Input**

- Kết quả họp Ngày 1.
- Nhu cầu engine từ M2 và UI từ M1.
- Yêu cầu API trong đề bài môn học.

**Output**

- Contract `caro-v1` không còn mâu thuẫn.
- `core/engine/interfaces.py` đồng bộ tài liệu.
- Fixtures JSON/JSONL cập nhật.
- Changelog hoặc mục migration ngắn.

**Công cụ**

- Markdown, Python dataclasses, JSON.
- Review chéo bằng Pull Request.

**Tiêu chí hoàn thành**

- M1 và M2 cùng approve contract.
- Không còn lệch kích thước bàn, tuple/int hoặc exact-five/overline.
- Mọi public method có input, output, lỗi và invariant rõ ràng.

### W2-M3-02 - Unit, property-style và regression tests

**Công việc cụ thể**

1. Parameterize 4 hướng thắng cho X và O.
2. Test các hoán vị chặn trái/phải, đầu/cuối và biên.
3. Test overline, gần thắng 4 quân và hai chuỗi rời.
4. Test win trước full-board draw để tránh báo hòa sai.
5. Test invalid action và terminal action giữ nguyên state.
6. Test invariant: số quân tăng đúng một sau step hợp lệ.
7. Test invariant: lượt đổi đúng, move count khớp số ô khác 0.
8. Test clone/undo độc lập và round-trip N step/N undo.
9. Test đầy đủ bàn 11x11.
10. Dùng parametrization/property-style loop; chỉ thêm Hypothesis khi nhóm duyệt dependency mới.

**Input**

- Contract W2-M3-01.
- Implementation W2-M2-01..03.
- Test vector do M2 bàn giao.

**Output**

- Test suites cho rules, terminal, result, clone và undo.
- Fixture có tên rõ, không phụ thuộc thứ tự chạy.
- Coverage report HTML hoặc terminal trong CI.

**Công cụ**

- `pytest`, `pytest-cov`.
- `pytest.mark.parametrize`.
- Seed cố định cho test property-style có random.

**Tiêu chí hoàn thành**

- `core.engine` coverage `>=90%`.
- `game_env.py` coverage `>=90%`.
- Test thất bại nếu bỏ terminal guard, clone sâu hoặc một hướng thắng.
- Test chạy lặp lại cho cùng kết quả.

### W2-M3-03 - CI, tích hợp và phát hành `caro-v1`

**Công việc cụ thể**

1. Tạo GitHub Actions chạy Python 3.13.
2. Cài từ `requirements.txt` và chạy toàn bộ test bằng một lệnh.
3. Bật coverage gate `--cov-fail-under=90` cho `core.engine`.
4. Chạy integration smoke: reset → nhiều step → terminal → result → undo/clone.
5. Sau khi PR UI merge, chạy thêm AppTest.
6. Ghi kết quả test/coverage vào PR integration.
7. Tạo tag `caro-v1` khi checklist cuối tuần đạt.

**Input**

- PR engine M2 đã merge.
- PR UI M1 sẵn sàng.
- Requirements và lệnh test chuẩn.

**Output**

- `.github/workflows/tests.yml` hoặc workflow tương đương.
- CI xanh trên commit tích hợp.
- Báo cáo coverage và smoke test.
- Tag nội bộ `caro-v1`.

**Công cụ**

- GitHub Actions.
- `pytest`, `pytest-cov`.
- Git tag/release nội bộ.

**Tiêu chí hoàn thành**

- Checkout sạch → install → test thành công.
- CI fail nếu test fail hoặc coverage dưới 90%.
- Không tag khi còn TODO production, test xfail không giải thích hoặc contract lệch code.

### Nhánh và commit của M3

- Nhánh contract: `docs/w2-caro-v1-thien`
- Nhánh test/CI: `test/w2-engine-ci-thien`
- Commit đề xuất:
  - `docs(contract): freeze caro-v1 rules and state metadata`
  - `test(engine): add terminal undo and property regressions`
  - `ci(test): enforce python 3.13 and engine coverage`
  - `chore(release): tag caro-v1 integration`

---

## 7. Thứ tự thực hiện, commit và merge

Không merge theo người hoàn thành trước. Merge theo dependency sau:

```text
0. Cả nhóm: xác nhận w1-foundation xanh
        |
1. M3: quyết định/contract draft ----+
        |                            |
2. M2: rules + terminal + undo <-----+
        |
3. M3: regression tests + coverage + CI
        |
4. M3: freeze contract caro-v1
        |
5. M1: UI adapter + Human vs Human + AppTest
        |
6. M3: integration run + coverage report
        |
7. Cả nhóm: review demo + tag caro-v1
```

### 7.1. Ai commit trước, ai làm sau

| Thứ tự | PR/commit group | Người mở | Người review bắt buộc | Điều kiện merge |
|---:|---|---|---|---|
| 1 | Contract draft + quyết định luật | M3 | M1 và M2 | Hai người xác nhận I/O và luật |
| 2 | Rules + terminal + result + undo | M2 | M3 | Test M2 xanh; không tự đổi public API |
| 3 | Regression tests + coverage gate | M3 | M2 | Engine đúng fixtures; coverage đạt ngưỡng |
| 4 | Contract freeze `caro-v1` | M3 | M1 và M2 | Docs, interfaces, fixtures đồng bộ |
| 5 | UI dùng engine thật | M1 | M3 | Không còn production dependency vào mock |
| 6 | Human vs Human + UI tests | M1 | M2 và M3 | Chơi trọn một ván; result do engine trả |
| 7 | Integration/CI/tag | M3 | M1 và M2 | Full tests + browser smoke + demo nội bộ |

### 7.2. Quy tắc tránh conflict

| Khu vực | Owner ghi code chính | Người khác được làm gì |
|---|---|---|
| `core/engine/rules.py`, `game_env.py` | M2 | M3 chỉ thêm test/review; không sửa thuật toán trong cùng PR |
| `core/engine/interfaces.py`, contract docs | M3 | M1/M2 comment và approve trước merge |
| `ui/`, UI tests | M1 | M3 cung cấp fixture/review contract |
| `.github/workflows/`, coverage config | M3 | M1/M2 review lệnh chạy trên máy cá nhân |

Mỗi commit phải chạy được test liên quan. Không gom code engine, UI và CI vào một commit lớn.

## 8. Lịch làm việc gợi ý trong 5 ngày

| Ngày | M1 - Hải | M2 - Ly | M3 - Thiện | Điểm đồng bộ |
|---|---|---|---|---|
| Ngày 1 | Audit mock dependency, đề xuất adapter | Chốt exact-five/overline và edge rules | Ghi contract draft + test matrix | Họp 75 phút; khóa quyết định luật |
| Ngày 2 | Chuẩn bị factory/controller theo contract draft | Hoàn thiện rules + terminal/result | Viết fixtures và regression tests độc lập | M2 mở PR cuối ngày |
| Ngày 3 | Chờ engine merge; viết test adapter | Hoàn thiện undo/clone, fix review | Merge engine, chạy coverage, hoàn thiện CI | Engine + test phải xanh trước UI integration |
| Ngày 4 | Nối UI với `CaroEnv`, Human vs Human | Hỗ trợ fix bug engine từ integration | Freeze contract, review UI I/O | Không còn production import mock |
| Ngày 5 | AppTest + browser smoke + ảnh PR | Review chuỗi thắng/hòa trên UI | Full suite, coverage report, integration | Demo nội bộ, tag `caro-v1`, retrospective |

### 8.1. Điểm dừng bắt buộc mỗi ngày

- **Cuối Ngày 1:** có biên bản luật và contract draft.
- **Cuối Ngày 2:** PR M2 có test cục bộ xanh.
- **Cuối Ngày 3:** engine regression xanh, coverage đạt ngưỡng hoặc có danh sách dòng thiếu cụ thể.
- **Cuối Ngày 4:** UI chạy bằng engine thật và chơi được đến terminal.
- **Cuối Ngày 5:** CI xanh trên nhánh integration và cả nhóm xem demo.

## 9. Ma trận test bắt buộc Tuần 2

| ID | Nhóm test | Kịch bản | Expected | Owner |
|---|---|---|---|---|
| W2-T01 | Rule | X thắng ngang | Winner X | M2/M3 |
| W2-T02 | Rule | O thắng dọc | Winner O | M2/M3 |
| W2-T03 | Rule | Chéo chính sát biên | Winner đúng | M2/M3 |
| W2-T04 | Rule | Chéo phụ sát biên | Winner đúng | M2/M3 |
| W2-T05 | Rule | Chuỗi 5 bị chặn một đầu | Thắng | M2/M3 |
| W2-T06 | Rule | Chuỗi 5 bị chặn hai đầu | Không thắng | M2/M3 |
| W2-T07 | Rule | Overline 6/7 quân | Theo quyết định contract | M2/M3 |
| W2-T08 | Rule | Hai chuỗi ngắt quãng tổng >=5 | Không thắng | M3 |
| W2-T09 | Draw | Bàn đầy không winner | Done, winner None | M2/M3 |
| W2-T10 | Precedence | Nước cuối vừa tạo win vừa lấp bàn | Win, không báo draw | M3 |
| W2-T11 | Invalid | Action ngoài biên | Raise, state không đổi | M3 |
| W2-T12 | Invalid | Ô đã chiếm | Raise, state không đổi | M3 |
| W2-T13 | Terminal | Step sau khi game kết thúc | Raise, state không đổi | M2/M3 |
| W2-T14 | Terminal | Legal actions sau terminal | `[]` | M3 |
| W2-T15 | Result | `result(X/O)` cho X win, O win, draw | `1/0/-1` đúng góc nhìn | M2/M3 |
| W2-T16 | Undo | Step rồi undo | State ban đầu | M2/M3 |
| W2-T17 | Undo | Undo sau terminal | Game mở lại đúng | M2/M3 |
| W2-T18 | Undo | Undo history rỗng | Raise, state không đổi | M3 |
| W2-T19 | Clone | Mutate clone | Gốc không đổi | M2/M3 |
| W2-T20 | Invariant | N step hợp lệ | Move count và số quân cùng tăng N | M3 |
| W2-T21 | UI | Chuỗi X thắng | Banner X, board disabled | M1 |
| W2-T22 | UI | Chuỗi O thắng | Banner O, board disabled | M1 |
| W2-T23 | UI | Click ô đã chiếm | Warning, UI state giữ nguyên | M1 |
| W2-T24 | UI | Play Again | Reset về X, board rỗng | M1 |
| W2-T25 | UI | Khởi tạo module 11x11 | 121 ô, không vỡ layout | M1 |

## 10. Lệnh kiểm thử và cổng chất lượng

### 10.1. Test nhanh theo module

```powershell
python -m pytest tests/test_rules.py -q
python -m pytest tests/test_game_env_contract.py tests/test_invalid_actions.py -q
python -m pytest tests/test_ui_app.py -q
```

### 10.2. Coverage engine

```powershell
python -m pytest `
  tests/test_board.py `
  tests/test_rules.py `
  tests/test_game_env_contract.py `
  tests/test_invalid_actions.py `
  --cov=core.engine `
  --cov-report=term-missing `
  --cov-fail-under=90
```

### 10.3. Full regression

```powershell
python -m pytest tests -q
python -m streamlit run ui/app.py
```

### 10.4. Definition of Done cho mỗi PR

- Test liên quan chạy xanh trên máy người viết.
- `git diff --check` không có lỗi.
- Không commit cache, secrets, virtual environment hoặc artifact tạm.
- Public API mới có type hint và docstring.
- PR mô tả input, output, test đã chạy và ảnh hưởng đến module khác.
- Reviewer kiểm tra state không bị mutation ngoài ý muốn.
- Không giảm coverage mà không có giải thích và approval.

## 11. Rủi ro và phương án xử lý

| Rủi ro | Dấu hiệu | Cách xử lý | Owner |
|---|---|---|---|
| Luật overline chưa thống nhất | Fixture M2/M3 cho expected khác nhau | Dừng merge, hỏi giảng viên hoặc chốt biên bản | M2 + M3 |
| Contract đổi khi UI đang tích hợp | M1 phải sửa nhiều field | Freeze trước PR UI; thay đổi sau freeze cần cả 3 approve | M3 |
| UI đọc nội bộ engine | Import `Board`, `_history`, `RuleEngine._...` | Bắt buộc qua `GameState`/public API | M1 reviewer: M3 |
| Clone shallow copy | Simulation làm đổi game chính | Test mutate clone ở board và history | M2 + M3 |
| Undo thiếu metadata | Board đúng nhưng lượt/winner sai | Snapshot đủ metadata; test undo terminal | M2 |
| Coverage 90% nhưng bỏ sót invariant | Nhiều line chạy nhưng assertion yếu | Mutation-oriented review: bỏ guard phải làm test fail | M3 |
| CI khác máy local | Dependency hoặc path Windows | Cài từ requirements; không hard-code path | M3 |
| UI result khác engine | UI tự suy luận winner | Xóa mọi win logic khỏi UI; dùng StepResult | M1 |

## 12. Checklist nghiệm thu Tuần 2

### Contract

- [ ] Default board và board tùy chọn đã thống nhất.
- [ ] Public action tuple và action int nội bộ được phân biệt rõ.
- [ ] Exact-five/overline và blocked-edge đã chốt.
- [ ] GameState metadata và StepResult đồng bộ code/docs.
- [ ] `result`, `clone_env`, `undo`, terminal error có chữ ký rõ.

### Rules và Engine

- [ ] 4 hướng thắng đúng cho X và O.
- [ ] Chặn hai đầu, một đầu, biên và overline đúng contract.
- [ ] Hòa chỉ báo khi bàn đầy và không winner.
- [ ] Step sau terminal bị từ chối và state không đổi.
- [ ] Legal actions terminal là danh sách rỗng.
- [ ] Reward/result đúng góc nhìn player.
- [ ] Reset xóa toàn bộ metadata ván trước.
- [ ] Clone độc lập cả board và history.
- [ ] Undo khôi phục đủ board/lượt/terminal/winner.

### Test và CI

- [ ] Ma trận W2-T01..W2-T25 được cover hoặc có lý do loại trừ.
- [ ] Coverage `core.engine >=90%`.
- [ ] Coverage `game_env.py >=90%`.
- [ ] Full regression Tuần 1 vẫn xanh.
- [ ] CI chạy Python 3.13 từ checkout sạch.
- [ ] CI fail khi test fail hoặc coverage dưới ngưỡng.

### UI

- [ ] Production UI khởi tạo `CaroEnv`, không khởi tạo mock.
- [ ] Human vs Human chơi được đến thắng/hòa.
- [ ] Status, move history và last move lấy từ engine/result.
- [ ] Terminal disable bàn và hiện đúng banner.
- [ ] New Game/Play Again gọi reset.
- [ ] 11x11 không vỡ layout.
- [ ] Không có logic thắng/thua trong `ui/`.

### Git và bàn giao

- [ ] PR merge đúng thứ tự ở Mục 7.
- [ ] Mỗi người có commit đúng phạm vi sở hữu.
- [ ] Có ảnh/video demo một ván hoàn chỉnh.
- [ ] README có lệnh test và chạy UI.
- [ ] Cả nhóm review demo cuối tuần.
- [ ] Tag `caro-v1` chỉ tạo sau khi CI xanh.

## 13. Những việc chưa làm trong Tuần 2

Để không vượt phạm vi, các hạng mục sau chuyển sang Tuần 3 trở đi:

- RandomAgent và schema metric/tournament runner chính thức.
- Heuristic Agent với thứ tự ưu tiên thắng/chặn/threat/center.
- Minimax, Alpha-Beta hoặc move ordering.
- MCTS Selection/Expansion/Simulation/Backpropagation.
- Neural Network, self-play, dataset hoặc training.
- Tournament 100+ ván/cặp và Elo.
- Tối ưu hiệu năng sâu hoặc cache tìm kiếm.
- Backend FastAPI nếu Streamlit gọi trực tiếp Python đã đủ.

Tuần 2 chỉ hoàn thành khi engine đúng luật, contract đã freeze, test/CI chứng minh được các invariant và UI chơi trọn một ván bằng engine thật. Đây là cổng bắt buộc trước khi ba thành viên bắt đầu xây các agent ở Tuần 3.
