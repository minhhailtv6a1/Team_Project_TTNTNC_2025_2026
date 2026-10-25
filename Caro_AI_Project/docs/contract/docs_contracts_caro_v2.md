# Đặc tả Contract Caro AI — `caro-v2`

> Trạng thái: **DRAFT FOR TEAM REVIEW**  
> Phạm vi: Engine, UI, Agents, self-play, tournament và data pipeline  
> Python mục tiêu: **3.13+**  
> Thay thế: `docs_contracts_caro_v1.md` sau khi M1, M2 và M3 cùng duyệt

Tài liệu này là nguồn tham chiếu duy nhất cho dữ liệu và hành vi đi qua ranh giới giữa các module. Chi tiết cài đặt nội bộ có thể thay đổi, nhưng public contract trong tài liệu này không được tự ý thay đổi.

---

## 1. Kết quả rà soát `caro-v1`

### 1.1. Điểm đã làm tốt

- Thống nhất tọa độ public dạng `(row, col)`, đánh số từ `0`.
- Thống nhất mã ô `X=1`, `O=-1`, `EMPTY=0`.
- Có các thực thể nền tảng `GameConfig`, `GameState`, `StepResult`.
- Quy định action lỗi không được làm thay đổi state.
- Xác định `clone_env()` là bắt buộc cho Minimax và MCTS.
- UI không tự cài luật thắng/thua mà nhận kết quả từ engine.

### 1.2. Khoảng trống và mâu thuẫn

| Vấn đề | Hiện trạng v1/repository | Quyết định trong v2 |
|---|---|---|
| Kích thước mặc định | Contract/code/UI từng lệch giữa 9 và 11 | Mặc định và chỉ hỗ trợ chính thức `11`; 9x9 tạm ngưng |
| Overline | v1 ghi “đúng 5”; `RuleEngine` và fixture có `>=5` | `>= win_length` được tính thắng |
| Sát biên | Test engine xem biên là đầu bị chặn; fixture `TC07` ghi kết quả ngược lại | Biên là một đầu bị chặn |
| Encoding action | Public API dùng tuple; `Board` và fixture có action `int` | Public chỉ dùng tuple; `int` chỉ nội bộ/ML index |
| Metadata state | Chỉ có board và lượt | Thêm `last_action`, `move_count`, `terminated`, `winner` |
| Terminal | Chưa nói rõ đi tiếp hoặc legal actions | Đi tiếp phát sinh lỗi; legal actions là `[]` |
| `result()`/`undo()` | Thiếu hoặc chưa có hành vi | Định nghĩa đầy đủ theo góc nhìn player |
| Lỗi | Chỉ có ngoài biên và ô đã chiếm | Chuẩn hóa sai kiểu, sai shape, game over và reason code |
| Agent API | Chưa có | Thêm `Agent`, `SearchBudget`, `AgentDecision` |
| Dữ liệu thực nghiệm | Chưa có schema chung | Thêm `MoveRecord`, `GameRecord` |
| Copy semantics | Mới nói clone nhưng chưa đủ chặt | Mọi state public là defensive deep snapshot |

### 1.3. Phạm vi không thuộc contract v2

- Cách lưu board nội bộ bằng `numpy.ndarray`, list hay bitboard.
- Hàm private của `RuleEngine`, cache, transposition table và cấu trúc node tìm kiếm.
- Layout/CSS của Streamlit.
- Kiến trúc neural network và định dạng checkpoint cụ thể.
- HTTP/FastAPI endpoint. Nếu thêm API mạng, endpoint phải chỉ là lớp chuyển đổi của các kiểu public trong tài liệu này.

---

## 2. Quy ước bắt buộc

### 2.1. Hằng số, kiểu và hệ tọa độ

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Protocol, TypeAlias, runtime_checkable

CONTRACT_VERSION = "caro-v2"

Action: TypeAlias = tuple[int, int]       # (row, col)
BoardMatrix: TypeAlias = list[list[int]]  # defensive snapshot


class Player(IntEnum):
    X = 1
    O = -1
    EMPTY = 0
```

- Gốc tọa độ ở góc trên trái.
- `row` tăng từ trên xuống; `col` tăng từ trái sang phải.
- Action hợp lệ thỏa `0 <= row, col < board_size`.
- `bool` không được xem là tọa độ nguyên dù `bool` là subclass của `int` trong Python.
- Public API không nhận action dạng số nguyên phẳng.

### 2.2. Public và internal action

`Board` có thể dùng index phẳng để tối ưu nội bộ, nhưng không được để kiểu này lọt sang UI hoặc `GameEnv`.

```python
def action_to_index(action: Action, board_size: int) -> int:
    row, col = action
    return row * board_size + col


def index_to_action(index: int, board_size: int) -> Action:
    return divmod(index, board_size)
```

Quy tắc này cũng là thứ tự policy của neural agent: index `i` ứng với ô `divmod(i, board_size)`.

---

## 3. Luật Caro chuẩn của dự án

1. X đi trước; hai bên luân phiên đúng một nước.
2. Một nước đặt đúng một quân vào một ô trống.
3. Xét bốn hướng: ngang `(0, 1)`, dọc `(1, 0)`, chéo chính `(1, 1)`, chéo phụ `(1, -1)`.
4. Một chuỗi liên tiếp có độ dài **lớn hơn hoặc bằng** `win_length` là ứng viên thắng.
5. Chuỗi không thắng nếu **cả hai đầu** đều bị chặn. Một đầu bị chặn khi gặp quân đối phương hoặc đi ra ngoài biên bàn cờ.
6. Overline (6, 7, ... quân) được tính thắng nếu không bị chặn cả hai đầu.
7. Sau khi kiểm tra thắng, nếu bàn đầy mà chưa có người thắng thì ván đấu hòa.
8. Ván đấu dừng ngay sau nước tạo trạng thái thắng hoặc hòa.

Ví dụ với chuỗi `XXXXX`:

| Mẫu theo một hướng | Kết quả |
|---|---|
| `_XXXXX_` | X thắng |
| `OXXXXX_` | X thắng |
| `OXXXXXO` | Không thắng |
| `EDGE-XXXXX_` | X thắng |
| `EDGE-XXXXXO` | Không thắng |
| `_XXXXXX_` | X thắng (overline) |

> Theo quy tắc trên, fixture `TC07_BLOCKED_BY_O_AND_EDGE` hiện tại phải có `expected_winner = null` và `terminated = false`. Description/expected value cũ phải được sửa cùng PR triển khai v2.

---

## 4. Các thực thể public

### 4.1. `GameConfig`

```python
class InvalidConfigError(ValueError):
    """Cấu hình không thuộc miền được caro-v2 hỗ trợ."""


@dataclass(frozen=True, slots=True)
class GameConfig:
    board_size: int = 11
    win_length: int = 5

    def __post_init__(self) -> None:
        if isinstance(self.board_size, bool) or self.board_size not in (11,):
            raise InvalidConfigError("caro-v2 currently requires board_size=11")
        if isinstance(self.win_length, bool) or self.win_length != 5:
            raise InvalidConfigError("caro-v2 requires win_length=5")
```

Quy ước:

- `GameConfig()` luôn tạo bàn 11x11.
- 11x11 là module duy nhất được phát triển và kiểm thử chính thức ở phiên bản hiện tại.
- 9x9 tạm ngưng. Khi mở lại hoặc thêm kích thước khác, cập nhật danh sách hỗ trợ tập trung và chạy lại toàn bộ contract test.
- Config bất biến và clone có thể dùng chung một instance config an toàn.

### 4.2. `GameState`

```python
@dataclass(frozen=True, slots=True)
class GameState:
    board: BoardMatrix
    current_player: Player
    last_action: Action | None = None
    move_count: int = 0
    terminated: bool = False
    winner: Player | None = None
```

Invariant bắt buộc:

- `board` có đúng `board_size` hàng và mỗi hàng có đúng `board_size` ô.
- Mọi ô chỉ chứa `-1`, `0`, `1` hoặc `Player` tương ứng.
- `move_count` bằng số ô khác `EMPTY`.
- `last_action is None` khi và chỉ khi `move_count == 0`.
- X đi trước: lượt tiếp theo là X khi `move_count` chẵn, O khi `move_count` lẻ.
- Sau một step hợp lệ, `current_player` luôn là người dự kiến đi tiếp, kể cả khi state vừa terminal. Consumer không được yêu cầu nước đi khi `terminated=True`.
- `winner` chỉ có thể là `Player.X`, `Player.O` hoặc `None`; không bao giờ là `Player.EMPTY`.
- `terminated=False` kéo theo `winner=None`.
- `terminated=True, winner=None` biểu diễn hòa.
- `terminated=True, winner in (X, O)` biểu diễn có người thắng.

`frozen=True` không làm đóng băng list lồng nhau. Vì vậy engine **phải deep-copy board** trước khi trả state; consumer xem `board` là read-only và không được sửa nó.

### 4.3. `StepResult`

```python
@dataclass(frozen=True, slots=True)
class StepResult:
    next_state: GameState
    reward: float
    done: bool
    winner: Player | None = None
```

Invariant:

```python
result.done == result.next_state.terminated
result.winner == result.next_state.winner
```

Reward theo góc nhìn người vừa thực hiện action:

| Trạng thái sau step | `reward` |
|---|---:|
| Chưa kết thúc | `0.0` |
| Hòa | `0.0` |
| Người vừa đi thắng | `1.0` |

`-1.0` được dành cho adapter/môi trường mở rộng; `CaroEnv` chuẩn không tạo `-1.0` từ một state hợp lệ vì người vừa đi không thể làm đối thủ thắng.

### 4.4. Lỗi public

```python
class InvalidActionReason(str, Enum):
    MALFORMED = "malformed"
    OUT_OF_BOUNDS = "out_of_bounds"
    OCCUPIED = "occupied"
    GAME_OVER = "game_over"


class InvalidActionError(ValueError):
    def __init__(
        self,
        reason: InvalidActionReason,
        action: object,
        message: str,
    ) -> None:
        super().__init__(message)
        self.reason = reason
        self.action = action


class UndoError(RuntimeError):
    """Không thể undo vì history của environment đang rỗng."""
```

Mọi validation action phải hoàn tất trước khi mutation. Nếu phát sinh `InvalidActionError`, board, lượt, metadata, terminal state và history phải giữ nguyên từng giá trị.

Thứ tự validation chuẩn:

1. Game đã terminal → `GAME_OVER`.
2. Action không phải tuple dài 2 hoặc tọa độ không phải integer thực → `MALFORMED`.
3. Tọa độ ngoài biên → `OUT_OF_BOUNDS`.
4. Ô đã có quân → `OCCUPIED`.

---

## 5. `GameEnv` API

### 5.1. Protocol chuẩn

```python
@runtime_checkable
class GameEnv(Protocol):
    @property
    def config(self) -> GameConfig: ...

    @property
    def state(self) -> GameState: ...

    def reset(self, seed: int | None = None) -> GameState: ...

    def legal_actions(self) -> list[Action]: ...

    def step(self, action: Action) -> StepResult: ...

    def is_terminal(self) -> bool: ...

    def result(self, player: Player) -> float | None: ...

    def clone_env(self) -> GameEnv: ...

    def undo(self) -> GameState: ...

    def render(self) -> str: ...
```

`CaroEnv` và mock dùng trong test phải cùng thỏa protocol này. UI chỉ type-hint theo `GameEnv`, không phụ thuộc `MockGameEnv`, `Board`, `_history` hoặc hàm private của `RuleEngine`.

### 5.2. Hành vi từng API

#### `reset(seed=None) -> GameState`

- Tạo board rỗng, X đi trước, `move_count=0` và toàn bộ metadata terminal rỗng.
- Xóa history dùng cho undo.
- Trả defensive snapshot.
- Engine hiện không ngẫu nhiên nhưng vẫn nhận `seed` để thống nhất runner; cùng seed phải không làm thay đổi hành vi xác định.

#### `legal_actions() -> list[Action]`

- Khi game đang chạy: trả toàn bộ ô trống theo thứ tự row-major.
- Khi game terminal: trả `[]`.
- List trả về là object mới; sửa list này không được ảnh hưởng environment.

#### `step(action) -> StepResult`

Thứ tự chuyển trạng thái nguyên tử:

```python
def step(action: Action) -> StepResult:
    validate_game_is_active()
    row, col = validate_action(action)
    acting_player = state.current_player
    save_history_snapshot()
    place_stone(row, col, acting_player)
    update_last_action_and_move_count()
    evaluate_win_before_draw()
    switch_current_player()
    return independent_step_result()
```

- Mỗi lần gọi thành công tăng `move_count` đúng 1.
- Không phát sinh mutation quan sát được nếu bất kỳ validation nào thất bại.
- `next_state` không chia sẻ mutable board với environment hoặc state đã trả trước đó.

#### `is_terminal() -> bool`

- Tương đương `env.state.terminated`.
- Không mutation và không có side effect.

#### `result(player) -> float | None`

```python
def result(player: Player) -> float | None:
    """
    None : game chưa kết thúc
     0.0 : hòa
     1.0 : player thắng
    -1.0 : đối thủ của player thắng
    """
```

- Chỉ chấp nhận `Player.X` hoặc `Player.O`; `Player.EMPTY`/sai kiểu phát sinh `ValueError`.
- Không được trả `StepResult`; đây là utility theo góc nhìn một player.

#### `clone_env() -> GameEnv`

- Clone có cùng config, state, terminal metadata và undo history.
- Board và history của clone hoàn toàn độc lập.
- Step/undo/reset trên clone không ảnh hưởng environment gốc và ngược lại.
- Agent nhận environment thật chỉ được mô phỏng trên clone.

#### `undo() -> GameState`

- Hoàn tác đúng một `step()` thành công gần nhất.
- Khôi phục board, `current_player`, `last_action`, `move_count`, `terminated` và `winner`.
- Undo được phép sau state thắng/hòa để quay lại state đang chơi.
- History rỗng phát sinh `UndoError` và state giữ nguyên.
- Trả defensive snapshot của state sau undo.

#### `render() -> str`

- Trả biểu diễn text của board và lượt hiện tại; không mutation.
- Có thể in chính chuỗi trả về ở chế độ debug, nhưng test chỉ được phụ thuộc vào giá trị trả về.

---

## 6. Agent contract

Mọi AI từ Random, Heuristic, Minimax, MCTS đến Neural dùng cùng một interface. Agent không được sửa environment nhận vào.

### 6.1. Budget và kết quả quyết định

```python
@dataclass(frozen=True, slots=True)
class SearchBudget:
    time_limit_ms: int | None = None
    max_depth: int | None = None
    max_nodes: int | None = None
    simulations: int | None = None
    seed: int | None = None


@dataclass(frozen=True, slots=True)
class AgentDecision:
    action: Action
    score: float | None = None
    nodes: int = 0
    simulations: int = 0
    elapsed_ms: float = 0.0
```

- Giá trị budget không `None` phải không âm; giới hạn đếm (`max_depth`, `max_nodes`, `simulations`) phải lớn hơn 0.
- Field không áp dụng với một agent được để `None` hoặc `0` tương ứng.
- `action` phải thuộc `env.legal_actions()` tại thời điểm trả về.
- `elapsed_ms`, `nodes`, `simulations` phục vụ benchmark và không ảnh hưởng luật game.

### 6.2. Protocol chung

```python
@runtime_checkable
class Agent(Protocol):
    @property
    def name(self) -> str: ...

    def choose_action(
        self,
        env: GameEnv,
        budget: SearchBudget | None = None,
    ) -> AgentDecision: ...
```

Hành vi bắt buộc:

- Nếu `env.is_terminal()` hoặc không có legal action, phát sinh `RuntimeError`.
- Không mutation `env`; Minimax/MCTS phải dùng `clone_env()` và có thể dùng `undo()` trên clone.
- Cùng state, config, budget và seed phải cho kết quả tái lập với agent có yếu tố ngẫu nhiên.
- Human click thuộc UI/controller, không bắt buộc triển khai `Agent` đồng bộ này.

---

## 7. Neural policy và legal mask

Policy vector có độ dài `board_size ** 2`, dùng row-major mapping ở mục 2.2.

```python
def legal_action_mask(
    legal_actions: list[Action],
    board_size: int,
) -> list[bool]:
    mask = [False] * (board_size * board_size)
    for action in legal_actions:
        mask[action_to_index(action, board_size)] = True
    return mask
```

- Logit của action không hợp lệ phải bị mask trước argmax/sampling.
- Neural agent phải đổi index được chọn về `Action` tuple trước khi trả `AgentDecision`.
- Input tensor là chi tiết của ML module; giá trị nguồn phải giữ đúng ý nghĩa `X=1`, `O=-1`, `EMPTY=0` hoặc ghi rõ phép biến đổi trong data pipeline.

---

## 8. Contract dữ liệu self-play và tournament

### 8.1. Record trong Python

```python
@dataclass(frozen=True, slots=True)
class MoveRecord:
    ply: int                 # bắt đầu từ 1
    player: Player
    action: Action
    reward: float
    elapsed_ms: float = 0.0
    nodes: int = 0
    simulations: int = 0


@dataclass(frozen=True, slots=True)
class GameRecord:
    contract_version: str
    game_id: str
    config: GameConfig
    seed: int | None
    x_agent: str
    o_agent: str
    moves: list[MoveRecord] = field(default_factory=list)
    terminated: bool = False
    winner: Player | None = None
```

Invariant:

- `ply` liên tục từ 1 và bằng vị trí trong danh sách `moves`.
- Player luân phiên X/O; action không trùng nhau.
- Record hoàn chỉnh phải có `terminated=True`.
- `winner=None` với record hoàn chỉnh nghĩa là hòa.
- `contract_version` bắt buộc là `"caro-v2"` để data pipeline từ chối dữ liệu khác version thay vì đoán schema.

### 8.2. JSON encoding

JSON không có tuple/enum nên dùng mapping duy nhất:

```python
def action_to_json(action: Action) -> list[int]:
    return [action[0], action[1]]


def player_to_json(player: Player | None) -> int | None:
    return None if player is None else int(player)
```

- Action JSON: `[row, col]`, không dùng index phẳng.
- Player JSON: `1`, `-1`, `0`; winner chỉ nhận `1`, `-1`, `null`.
- Board JSON: mảng hai chiều số nguyên.
- File JSON/JSONL phải lưu UTF-8.

---

## 9. Ranh giới module

| Module | Được dùng | Không được phụ thuộc |
|---|---|---|
| `ui/` | `GameEnv`, `GameState`, `StepResult`, public errors | `Board.grid`, `_history`, private rule methods |
| `core/agents/` | `Agent`, clone public, legal actions, result | Mutable state của UI/engine thật |
| `core/ml/` | `GameRecord`, action-index mapping, board values | CSS/UI session state |
| `core/utils/` | `Agent`, `GameEnv`, record schema | Cấu trúc node riêng của từng AI |
| `api/` | Serialize/deserialize public entities | Tái cài luật thắng/thua |

`board_array`, NumPy dtype, cached winner, node tree và history stack là implementation detail. Nếu UI/test cần chúng, hãy thêm helper/adapter ngoài contract thay vì ép engine công khai nội bộ.

---

## 10. Test chấp nhận contract

Một implementation chỉ được gắn nhãn `caro-v2 compliant` khi toàn bộ nhóm test sau xanh:

| ID | Nhóm test | Điều kiện tối thiểu |
|---|---|---|
| C2-CONFIG | Config | Default 11; phạm vi hiện tại chỉ nhận 11 và `win_length=5` |
| C2-STATE | Invariant | Shape, cell domain, count, turn, metadata đúng |
| C2-ACTION | Validation | Sai shape/type, bool, ngoài biên, occupied, game over |
| C2-ATOMIC | Atomicity | Mọi lỗi giữ nguyên state và history |
| C2-RULE | Luật | 4 hướng, một/hai đầu chặn, 4 biên, overline, draw |
| C2-TERM | Terminal | `legal_actions()==[]`; step tiếp theo lỗi |
| C2-RESULT | Result | X/O thắng, thua, hòa, non-terminal |
| C2-CLONE | Clone | State và history độc lập hai chiều |
| C2-UNDO | Undo | Round-trip step/undo và undo terminal |
| C2-AGENT | Agent | Action legal, không mutation, seed tái lập |
| C2-DATA | Record | JSON round-trip không mất thông tin |
| C2-UI | Integration | UI chạy bằng `CaroEnv`, không tự xét luật |

Property quan trọng:

```python
before = env.state
result = env.step(action)
after_undo = env.undo()

assert after_undo == before
assert result.next_state.move_count == before.move_count + 1
```

```python
clone = env.clone_env()
clone.step(clone.legal_actions()[0])

assert env.state != clone.state
assert env.state == state_before_clone_move
```

---

## 11. Migration từ v1 sang v2

### 11.1. Thay đổi breaking

- Khóa `GameConfig.board_size=11`; 9x9 rời khỏi phạm vi hỗ trợ hiện tại.
- `GameState` thêm bốn field metadata.
- `result()` đổi thành `result(player) -> float | None`.
- `reset()` nhận `seed` tùy chọn.
- `render()` phải trả `str`.
- Thêm `undo()` và terminal guard.
- `InvalidActionError` có `reason` và `action`.
- Mock và engine thật phải cùng thỏa `GameEnv` protocol.
- Fixture public phải dùng `[row, col]`, không dùng action index phẳng.

### 11.2. Thứ tự migration/commit

1. **M3 — Contract/tests:** merge tài liệu v2, shared interface skeleton và contract tests đang `xfail` hoặc test branch riêng.
2. **M2 — Rules/engine:** cập nhật entities, rule edge/overline, terminal, result, clone và undo; sửa fixture `TC07`.
3. **M3 — Verification:** bỏ `xfail`, chạy toàn bộ contract/regression tests và duyệt implementation.
4. **M1 — UI/agents adapter:** chuyển UI từ `MockGameEnv` sang `GameEnv`/`CaroEnv`; dùng metadata trong state.
5. **M3 — Integration:** merge cuối, chạy UI smoke, agent smoke, coverage và gắn tag sau khi ba thành viên ký duyệt.

Không merge UI/agent tự định nghĩa field mới trước commit interface của M3. Không sửa đồng thời contract từ nhiều branch.

### 11.3. Các file phải đồng bộ

- `core/engine/interfaces.py`
- `core/engine/game_env.py`
- `core/engine/rules.py`
- `ui/mock_game_env.py` và `ui/app.py`
- `tests/test_game_env_contract.py`
- `tests/test_invalid_actions.py`
- `tests/test_rules.py`
- `tests/fixtures/test_vectors.json`
- `tests/fixtures/caro_v1_case.jsonl` → fixture v2 mới
- Agent base/shared interface, logger và tournament runner khi bắt đầu triển khai

---

## 12. Quy tắc thay đổi contract

1. Mọi thay đổi public phải có issue/decision note nêu lý do và module bị ảnh hưởng.
2. M1 duyệt ảnh hưởng UI/API; M2 duyệt luật/engine; M3 duyệt test/data/integration.
3. Breaking change phải tạo `caro-v3`; không sửa âm thầm ý nghĩa field của v2.
4. Thay đổi không breaking vẫn phải cập nhật docs, type hints, fixture và test trong cùng PR.
5. Chỉ ghi trạng thái **FROZEN** khi cả ba thành viên xác nhận checklist dưới đây.

### Checklist ký duyệt

- [ ] M1 xác nhận đủ dữ liệu cho UI và agent integration.
- [ ] M2 xác nhận rule edge, blocked ends và overline.
- [ ] M3 xác nhận fixture, exception, clone/undo và data schema.
- [ ] Contract tests xanh trên Python 3.13.
- [ ] Không còn consumer dùng action index phẳng ở public boundary.
- [ ] `docs_contracts_caro_v2.md`, code và fixture không còn mâu thuẫn.

