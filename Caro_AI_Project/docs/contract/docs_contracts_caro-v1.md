# Đặc tả Hợp đồng API Trò chơi Caro (Gomoku) - Phiên bản 1 (`caro-v1`)

> **Trạng thái: DRAFT – ĐỀ XUẤT NGÀY 1 TUẦN 2, CHƯA FREEZE**  
> **Người tổng hợp:** M3  
> **Cần duyệt:** M1 (UI), M2 (Engine/rules), M3 (Contract/tests)  
> **Nguồn chỉnh sửa:** Contract hiện có của nhóm và *Kế hoạch chi tiết Tuần 2*.  
> Các giá trị ghi **[ĐỀ XUẤT]** chưa phải quyết định đã được nhóm hoặc giảng viên phê duyệt. Chưa sửa public interface trong code trước khi thống nhất.

Tài liệu này định nghĩa các cấu trúc dữ liệu và giao diện API cốt lõi (Contract) cho trò chơi Caro. Contract này đóng vai trò là "nguồn sự thật duy nhất" (Single Source of Truth) giúp các nhóm làm Giao diện (UI) và Thuật toán AI (Engine/Agents) làm việc độc lập mà không cần phải đoán ý nhau.

## 1. Quy ước chung

- **Không gian trạng thái:** Bàn cờ là ma trận 2 chiều; tọa độ `(row, col)` bắt đầu từ chỉ số 0, dòng từ trên xuống và cột từ trái sang phải.
- **Kích thước bàn cờ [ĐỀ XUẤT]:** Mặc định **9×9**, tùy chọn **11×11**, cấu hình qua `GameConfig`. Điều này làm rõ chỗ contract cũ ghi “9×9 hoặc 11×11” nhưng `GameConfig.board_size` lại là 11.
- **Giá trị ô:** `Player.EMPTY = 0`, `Player.X = 1`, `Player.O = -1`; X đi trước.
- **Action public [ĐỀ XUẤT]:** `Action = tuple[int, int]` theo `(row, col)`. Nếu `Board` sử dụng số nguyên làm action nội bộ thì phải chuyển đổi trước khi trả về UI/Agent; không lộ `int` ra API public.
- **Luật thắng [ĐỀ XUẤT – CẦN M2 CHỐT]:** Có **từ 5 quân liên tiếp trở lên** theo ngang, dọc, chéo chính hoặc chéo phụ và **không bị chặn cả hai đầu**. Biên bàn cờ được xem là một đầu bị chặn; chặn một đầu vẫn có thể thắng.
- **Overline [ĐỀ XUẤT – CẦN M2/GIẢNG VIÊN CHỐT]:** Chuỗi 6 hoặc 7 quân được xét thắng nếu đáp ứng quy tắc chặn hai đầu. **Khác với contract cũ ghi “đúng 5”**; nếu nhóm chọn exact-five, phải đổi lại mục này, tests và fixtures đồng thời **trước khi merge luật của M2**.
- **Hòa [ĐỀ XUẤT]:** Bàn đầy và không có người thắng. Nếu nước cuối vừa tạo thắng vừa làm đầy bàn thì ưu tiên thắng, không báo hòa.
- **Tính đúng đắn của luật:** Engine nội bộ chịu trách nhiệm xác định kết quả; UI đọc `StepResult`, không tự tính thắng/thua.

## 2. Định nghĩa các thực thể (Entities)

### 2.1. Người chơi (`Player`)

Sử dụng Enum `Player` để đại diện cho ô và lượt chơi:

- `Player.X = 1`: người chơi đi trước, ký hiệu X.
- `Player.O = -1`: người chơi đi sau, ký hiệu O.
- `Player.EMPTY = 0`: ô trống.

### 2.2. Cấu hình trò chơi (`GameConfig`)

- `board_size: int = 9` **[ĐỀ XUẤT]**; hỗ trợ `11` như cấu hình tùy chọn.
- `win_length: int = 5`: số quân liên tiếp tối thiểu để xét thắng theo luật đề xuất tại Mục 1.
- `reset()` với 9×9 có 81 nước đi hợp lệ, với 11×11 có 121 nước đi hợp lệ.

### 2.3. Trạng thái ván đấu (`GameState`)

Các trường đang có:

- `board: list[list[int]]`: ma trận `board_size × board_size`, chỉ nhận giá trị `0`, `1`, `-1`.
- `current_player: Player`: lượt đi tiếp theo theo quy ước của Engine.

**Metadata cần bổ sung [ĐỀ XUẤT]:**

- `last_action: Action | None = None`: tọa độ nước đi gần nhất; `None` khi chưa đi.
- `move_count: int = 0`: tổng nước đi hợp lệ đã thực hiện.
- `terminated: bool = False`: ván đã kết thúc hay chưa.
- `winner: Player | None = None`: X/O nếu thắng; `None` khi hòa hoặc chưa kết thúc.

Mẫu cấu trúc mục tiêu **để thảo luận, không dán đè code hiện có**:

```python
from dataclasses import dataclass

Action = tuple[int, int]

@dataclass(frozen=True)
class GameState:
    board: list[list[int]]
    current_player: Player
    last_action: Action | None = None
    move_count: int = 0
    terminated: bool = False
    winner: Player | None = None
```

Lưu ý: `frozen=True` không tự bảo vệ danh sách lồng nhau trong `board` khỏi mutation. Cần đối chiếu cách Engine trả snapshot và quản lý tham chiếu với M2.

### 2.4. Kết quả của một nước đi (`StepResult`)

**Giữ các field hiện có** (không tự ý đổi tên):

- `next_state: GameState`: trạng thái sau khi đi, là bản sao/snapshot độc lập theo contract hiện có, tránh chia sẻ tham chiếu có thể bị thay đổi.
- `reward: float`: theo góc nhìn **người vừa đi**. **[ĐỀ XUẤT]** Win = `1.0`; draw = `0.0`; chưa kết thúc = `0.0`. Contract cũ cũng liệt kê `-1.0` cho thua; cần M2/M3 xác nhận liệu `step()` có tình huống nào trả giá trị này và ghi rõ quy tắc.
- `done: bool`: `True` khi thắng/hòa; ngược lại `False`.
- `winner: Player | None`: X/O nếu thắng, `None` nếu hòa/chưa kết thúc.

**Bất biến [ĐỀ XUẤT]:** `StepResult.done` thống nhất với `next_state.terminated`, `StepResult.winner` thống nhất với `next_state.winner`; state của action không hợp lệ không bị thay đổi.

### 2.5. Xử lý lỗi (`InvalidActionError`)

`step()` raise `InvalidActionError` khi:

- Tọa độ âm/vượt ngoài `board_size - 1`.
- Đánh vào ô đã chiếm.
- **[ĐỀ XUẤT]** Thực hiện nước đi khi ván đã terminal.
- **[CẦN XÁC NHẬN]** Action có sai kiểu/cấu trúc có dùng chính exception này hay `TypeError`/`ValueError`.

**Bất biến:** khi bị từ chối, toàn bộ `board`, `current_player`, `last_action`, `move_count`, `terminated`, `winner` và history giữ nguyên.

## 3. Giao diện Môi trường (`GameEnv API`)

`CaroEnv` cung cấp các phương thức public sau. Chữ ký sau đây là **bản đề xuất cần đối chiếu `core/engine/interfaces.py` trước khi freeze**.

| API | Đầu vào | Đầu ra | Hành vi đề xuất |
|---|---|---|---|
| `reset(seed: int | None = None)` | Seed tùy chọn | `GameState` | Bàn trống, lượt X, `move_count=0`, `last_action=None`, `terminated=False`, `winner=None`; seed phục vụ khả năng tái lập nếu có randomness. |
| `legal_actions()` | Không | `list[Action]` | Danh sách ô trống nếu chưa kết thúc, **`[]` sau thắng/hòa**. |
| `step(action: Action)` | `(row, col)` | `StepResult` | Kiểm tra action, cập nhật state/metadata, tính win trước draw, reward theo người vừa đi; lỗi không đổi state. |
| `clone_env()` | Không | `CaroEnv` | Deep/independent clone của board, metadata và history; thay đổi clone không ảnh hưởng gốc. |
| `is_terminal()` | Không | `bool` | Cho biết ván đã thắng hoặc hòa. |
| `result(player: Player)` **[MỚI]** | X hoặc O | `float | None` | `1.0` nếu player thắng, `-1.0` nếu thua, `0.0` nếu hòa, `None` nếu chưa kết thúc. |
| `undo()` **[MỚI]** | Không | `GameState` | Hoàn tác đúng một nước, khôi phục board/lượt/last_action/move_count/terminated/winner; undo sau thắng mở lại ván; history rỗng báo lỗi **[cần chốt loại exception]**. |
| `render()` | Không | `str` **[ĐỀ XUẤT]** | Trả về biểu diễn bàn cờ cho debug; contract cũ chưa ghi rõ kiểu trả về nên cần kiểm tra implementation. |

### 3.1. Quy tắc chuyển trạng thái [ĐỀ XUẤT]

1. `reset()` đưa về state ban đầu, X đi trước, không còn metadata/history của ván cũ.
2. Mỗi `step()` hợp lệ tăng đúng một ô khác 0 và tăng `move_count` đúng 1.
3. Nước đi bất hợp lệ hoặc sau terminal bị từ chối, không mutate state.
4. Sau khi đi, Engine kiểm tra người thắng trước khi kết luận hòa.
5. Khi thắng/hòa, `is_terminal() == True` và `legal_actions() == []`.
6. `undo()` sau terminal khôi phục game chưa kết thúc nếu nước vừa bỏ là nước kết thúc; undo nhiều nước liên tiếp khôi phục trạng thái trước đó chính xác.
7. `clone_env()` phải độc lập cả board và history có thể mutate.
8. **[CẦN M2 CHỐT]** `current_player` biểu diễn ai khi state đã terminal (vẫn đổi lượt hay giữ người vừa đi); test và UI phải dùng cùng một cách hiểu.

### 3.2. Ví dụ chữ ký API đích

```python
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

## 4. Test matrix dự kiến cho `caro-v1`

| Mã | Tình huống | Kết quả kỳ vọng | Người phụ trách |
|---|---|---|---|
| W2-T01..T04 | 4 hướng thắng, cả X/O | Đúng winner | M2/M3 |
| W2-T05..T06 | Chặn một đầu / hai đầu | Thắng / không thắng | M2/M3 |
| W2-T07 | Overline 6/7 | Theo quyết định đã freeze | M2/M3 |
| W2-T08 | Hai chuỗi rời tổng ≥5 | Không thắng | M3 |
| W2-T09..T10 | Bàn đầy hòa / thắng cùng nước cuối | Draw / ưu tiên win | M2/M3 |
| W2-T11..T14 | Action invalid, sau terminal, legal actions | Raise không mutate / `[]` | M2/M3 |
| W2-T15 | Result X/O/thắng/thua/hòa/chưa kết thúc | `1/-1/0/None` | M2/M3 |
| W2-T16..T19 | Undo, undo terminal, empty history, clone | State khôi phục / độc lập | M2/M3 |
| W2-T20 | N nước hợp lệ | `move_count` = số ô khác 0 | M3 |
| W2-T21..T25 | UI thắng/hòa, invalid click, reset, board size | UI đọc engine thật | M1 (M3 review) |

**Coverage đích cuối Tuần 2:** `core.engine >= 90%` và riêng `game_env.py >= 90%`; CI chạy Python 3.13. Đây **không** phải yêu cầu phải đạt ngay cuối Ngày 1.

## 5. Phạm vi trách nhiệm và tích hợp

- **M1 (UI):** dùng contract public và `StepResult`; cần các metadata để hiển thị lượt chơi, nước cuối, move count, winner và trạng thái kết thúc. Có thể dùng fixture `tests/fixtures/caro_v1_cases.json` để làm mock trước khi engine hoàn chỉnh, nếu file có trong repository.
- **M2 (Engine):** xác nhận và hiện thực luật thắng, terminal/reward/result, `clone_env()` và `undo()`; ưu tiên tính đúng đắn, không đổi public interface khi chưa được M3 duyệt.
- **M3 (Contract/Tests/CI):** ghi biên bản, đồng bộ docs/interface/fixtures theo kết quả họp; bổ sung regression/property-style tests, coverage và CI.

## 6. Các quyết định cần nhóm chốt trước khi freeze

| # | Vấn đề | Đề xuất hiện tại | Người duyệt | Trạng thái |
|---|---|---|---|---|
| 1 | Bàn mặc định | 9×9; 11×11 tùy chọn | M1 + M2 + M3 | ☐ Chưa duyệt |
| 2 | Giá trị ô | EMPTY=0, X=1, O=-1 | M2 + M3 | ☐ Chưa duyệt |
| 3 | Public action | Tuple `(row, col)`; `int` chỉ nội bộ | M1 + M3; M2 review | ☐ Chưa duyệt |
| 4 | Luật thắng | ≥5, không chặn cả hai đầu | M2; cả nhóm xác nhận | ☐ Chưa duyệt |
| 5 | Overline | Chuỗi 6/7 tính thắng nếu không bị chặn hai đầu | M2 + giảng viên nếu cần | ☐ Chưa duyệt |
| 6 | Sát biên | Biên tính là đầu bị chặn | M2 | ☐ Chưa duyệt |
| 7 | Hòa và terminal guard | Win trước draw; sau terminal raise, state không đổi | M2 + M3 | ☐ Chưa duyệt |
| 8 | `legal_actions()` | Trả `[]` khi terminal | M3 + M2 | ☐ Chưa duyệt |
| 9 | `result(player)` | `1/-1/0/None` theo player | M2 + M3 | ☐ Chưa duyệt |
| 10 | `step().reward` | Win=1, draw/nonterminal=0; làm rõ -1 | M2 + M3 | ☐ Chưa duyệt |
| 11 | `undo()` | Hoàn tác 1 nước, lỗi history rỗng | M2 + M3 | ☐ Chưa duyệt |
| 12 | `GameState` metadata | last_action, move_count, terminated, winner | M1 + M3; M2 review | ☐ Chưa duyệt |
| 13 | `reset(seed)` | API có seed khi có randomness | M3 | ☐ Chưa duyệt |
| 14 | Kiểu lỗi/return phụ | Undo empty history, render, terminal current_player, invalid type | M1 + M2 + M3 | ☐ Chưa duyệt |

**Điều kiện chuyển `DRAFT` → `FROZEN`:** M1 và M2 xác nhận, M3 tổng hợp quyết định cuối cùng; `docs/contract`, `core/engine/interfaces.py`, fixture và implementation dùng cùng API/luật. Chưa freeze nếu còn mâu thuẫn exact-five/overline hoặc 9×9/11×11.

### Biên bản xác nhận

- Ngày họp: `________________`
- M1: `☐ Đồng ý / ☐ Yêu cầu sửa` — Ghi chú: `________________`
- M2: `☐ Đồng ý / ☐ Yêu cầu sửa` — Ghi chú: `________________`
- M3: `☐ Đã cập nhật contract` — Ghi chú: `________________`

---

*Bản bổ sung này là đề xuất để nhóm review; không thể hiện rằng các giá trị đã được chính thức thông qua.*
