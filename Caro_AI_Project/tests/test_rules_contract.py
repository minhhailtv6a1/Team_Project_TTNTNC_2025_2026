# File: tests/test_rules_contract.py
"""Contract test C2-RULE cho ``CaroEnv`` (caro-v2, mục 3 của contract).

Luật được kiểm tra:
  * Chuỗi liên tiếp có độ dài >= 5 là ứng viên thắng (overline được tính).
  * Chuỗi không thắng nếu CẢ HAI đầu bị chặn; một đầu bị chặn khi gặp quân đối
    phương hoặc ra ngoài biên bàn cờ.
  * Bốn hướng: ngang, dọc, chéo chính, chéo phụ - cho cả X và O.
  * Hai đoạn rời nhau, chuỗi 4 quân và hai chuỗi giao nhau không thắng.
  * Bàn đầy không có người thắng là hòa.

Chỉ dùng public API. Mỗi vị trí được dựng bằng chuỗi ``step()`` xen kẽ X/O;
quân phụ của bên không thắng được đặt rải rác (cách nhau >= 2 ô, xa chuỗi) để
không tạo chuỗi hay chặn đầu ngoài ý muốn. Nước cuối của kịch bản luôn là quân
hoàn tất chuỗi, và mọi nước trước đó phải chưa kết thúc ván.

Ghi chú về W2-T10 ("nước cuối vừa thắng vừa lấp bàn"): theo luật hai đầu bị chặn,
trên bàn đầy mọi chuỗi cực đại đều bị đối phương hoặc biên chặn cả hai đầu nên
KHÔNG THỂ thắng. Kịch bản này không thể xảy ra với caro-v2; nên ghi "loại trừ có
lý do" trong ma trận thay vì viết test giả. Thứ tự "thắng trước hòa" trong
``step()`` chỉ có ý nghĩa nếu luật đổi (ví dụ bỏ điều kiện chặn hai đầu).

Trước khi PR engine của M2 merge, chạy với ``CARO_C2_XFAIL=1`` để đánh dấu cả
file là xfail (không strict). Sau khi merge, bỏ biến môi trường.
"""
from __future__ import annotations

import os

import pytest

from core.engine.game_env import CaroEnv
from core.engine.interfaces import Player, StepResult
from helpers.helpers_contract import check_state_invariants

pytestmark = pytest.mark.xfail(
    os.environ.get("CARO_C2_XFAIL") == "1",
    reason="Chờ PR engine của M2 (contract mục 11.2)",
    strict=False,
)

N = 11
Cell = tuple[int, int]

DIRECTIONS: dict[str, Cell] = {
    "horizontal": (0, 1),
    "vertical": (1, 0),
    "diagonal": (1, 1),
    "anti_diagonal": (1, -1),
}
# Chuỗi 5 giữa bàn: hai đầu nằm trong bàn và để trống.
FIVE_START: dict[str, Cell] = {
    "horizontal": (5, 3), "vertical": (3, 5), "diagonal": (3, 3), "anti_diagonal": (3, 7),
}
# Chuỗi 6 giữa bàn: hai đầu nằm trong bàn và để trống.
SIX_START: dict[str, Cell] = {
    "horizontal": (5, 2), "vertical": (2, 5), "diagonal": (2, 2), "anti_diagonal": (2, 8),
}

PLAYERS = [pytest.param(Player.X, id="X"), pytest.param(Player.O, id="O")]
DIRECTION_PARAMS = list(DIRECTIONS)

# Trạng thái chặn đầu -> có thắng không (contract mục 3, điều 5).
BLOCK_STATES = {"open": True, "left": True, "right": True, "both": False}


# ---------------------------------------------------------------------------
# Dựng vị trí
# ---------------------------------------------------------------------------
def in_bounds(cell: Cell) -> bool:
    return 0 <= cell[0] < N and 0 <= cell[1] < N


def line_cells(start: Cell, direction: str, length: int) -> list[Cell]:
    dr, dc = DIRECTIONS[direction]
    return [(start[0] + dr * i, start[1] + dc * i) for i in range(length)]


def ends_of(line: list[Cell], direction: str) -> tuple[Cell, Cell]:
    dr, dc = DIRECTIONS[direction]
    return (line[0][0] - dr, line[0][1] - dc), (line[-1][0] + dr, line[-1][1] + dc)


def blockers_for(state: str, line: list[Cell], direction: str) -> list[Cell]:
    before, after = ends_of(line, direction)
    chosen: list[Cell] = []
    if state in ("left", "both"):
        chosen.append(before)
    if state in ("right", "both"):
        chosen.append(after)
    assert all(in_bounds(c) for c in chosen), "fixture error: blocker out of bounds"
    return chosen


LATTICE: list[Cell] = [(r, c) for r in range(0, N, 2) for c in range(0, N, 2)]


def pick_filler(count: int, keep_away: list[Cell]) -> list[Cell]:
    """Ô rải rác (cách nhau >= 2) và cách xa mọi ô trong ``keep_away`` >= 2."""
    near = {(r + a, c + b) for r, c in keep_away for a in (-1, 0, 1) for b in (-1, 0, 1)}
    cells = [cell for cell in LATTICE if cell not in near]
    assert len(cells) >= count, "fixture error: not enough filler cells"
    return cells[:count]


def interleave(x_cells: list[Cell], o_cells: list[Cell]) -> list[Cell]:
    assert len(x_cells) - len(o_cells) in (0, 1), "X must move first and alternate"
    return [
        x_cells[i // 2] if i % 2 == 0 else o_cells[i // 2]
        for i in range(len(x_cells) + len(o_cells))
    ]


def build_moves(
    player: Player,
    line: list[Cell],
    last: Cell,
    blockers: list[Cell] | tuple[Cell, ...] = (),
) -> list[Cell]:
    """Chuỗi nước đi để ``player`` đặt các ô của ``line`` với ``last`` đi sau cùng.

    Bên còn lại đặt ``blockers`` rồi quân phụ rải rác cho đủ số nước.
    """
    assert last in line
    mine = [c for c in line if c != last] + [last]
    other_count = len(mine) - 1 if player == Player.X else len(mine)
    others = list(blockers)
    assert len(others) <= other_count, "fixture error: too many blockers"
    others += pick_filler(other_count - len(others), list(line) + list(blockers))
    x_cells, o_cells = (mine, others) if player == Player.X else (others, mine)
    moves = interleave(x_cells, o_cells)
    assert len(set(moves)) == len(moves), "fixture error: duplicated cell"
    return moves


def new_env() -> CaroEnv:
    env = CaroEnv()
    env.reset()
    return env


def replay(env, moves: list[Cell]) -> StepResult:
    """Chơi hết ``moves``; mọi nước trước nước cuối phải chưa kết thúc ván."""
    result = None
    for index, move in enumerate(moves):
        result = env.step(move)
        if index < len(moves) - 1:
            assert not result.done, f"fixture ended early at ply {index + 1} ({move})"
    assert result is not None
    return result


def scenario(
    player: Player,
    line: list[Cell],
    last: Cell,
    blockers: list[Cell] | tuple[Cell, ...] = (),
):
    env = new_env()
    moves = build_moves(player, line, last, blockers)
    return env, replay(env, moves), moves


def assert_wins(env, result: StepResult, player: Player, moves: list[Cell]) -> None:
    state = env.state
    assert result.done is True
    assert result.winner == player
    assert result.reward == 1.0
    assert state.terminated is True
    assert state.winner == player
    assert state.move_count == len(moves)
    assert state.last_action == moves[-1]
    assert env.legal_actions() == []
    check_state_invariants(state)


def assert_continues(env, result: StepResult, moves: list[Cell]) -> None:
    state = env.state
    assert result.done is False
    assert result.winner is None
    assert result.reward == 0.0
    assert state.terminated is False
    assert state.winner is None
    assert state.move_count == len(moves)
    assert len(env.legal_actions()) == N * N - len(moves)
    check_state_invariants(state)


def assert_outcome(env, result, player, moves, expect_win: bool) -> None:
    if expect_win:
        assert_wins(env, result, player, moves)
    else:
        assert_continues(env, result, moves)


# ---------------------------------------------------------------------------
# Kiểm tra bộ dựng vị trí (lỗi ở đây là lỗi fixture, không phải lỗi luật)
# ---------------------------------------------------------------------------
class TestScenarioBuilder:
    @pytest.mark.parametrize("player", PLAYERS)
    def test_builder_places_exact_stones(self, player):
        line = line_cells((5, 3), "horizontal", 5)
        moves = build_moves(player, line, line[2], blockers=[(5, 2)])
        x_cells, o_cells = moves[0::2], moves[1::2]
        mine, other = (x_cells, o_cells) if player == Player.X else (o_cells, x_cells)
        assert set(mine) == set(line)
        assert moves[-1] == line[2]
        assert (5, 2) in other
        assert len(set(moves)) == len(moves)
        # quân phụ không nằm cạnh chuỗi và không sát nhau
        extras = [c for c in other if c != (5, 2)]
        for cell in extras:
            assert all(max(abs(cell[0] - r), abs(cell[1] - c)) >= 2 for r, c in line + [(5, 2)])

    def test_filler_never_touches_each_other(self):
        cells = pick_filler(5, [(5, 5)])
        for i, a in enumerate(cells):
            for b in cells[i + 1:]:
                assert max(abs(a[0] - b[0]), abs(a[1] - b[1])) >= 2


# ---------------------------------------------------------------------------
# Thắng theo bốn hướng, cho cả X và O, với mọi vị trí của quân cuối
# ---------------------------------------------------------------------------
class TestWinInEveryDirection:
    @pytest.mark.parametrize("direction", DIRECTION_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize("last_index", range(5))
    def test_five_in_a_row_wins_whichever_stone_is_last(self, direction, player, last_index):
        line = line_cells(FIVE_START[direction], direction, 5)
        env, result, moves = scenario(player, line, line[last_index])
        assert_wins(env, result, player, moves)

    @pytest.mark.parametrize("direction", DIRECTION_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    def test_four_in_a_row_is_not_a_win(self, direction, player):
        line = line_cells(FIVE_START[direction], direction, 4)
        env, result, moves = scenario(player, line, line[3])
        assert_continues(env, result, moves)


# ---------------------------------------------------------------------------
# Chặn không / một / hai đầu
# ---------------------------------------------------------------------------
class TestBlockedEnds:
    @pytest.mark.parametrize("direction", DIRECTION_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize("state", list(BLOCK_STATES))
    def test_block_states(self, direction, player, state):
        line = line_cells(FIVE_START[direction], direction, 5)
        blockers = blockers_for(state, line, direction)
        env, result, moves = scenario(player, line, line[2], blockers)
        assert_outcome(env, result, player, moves, BLOCK_STATES[state])

    @pytest.mark.parametrize("player", PLAYERS)
    def test_game_continues_after_a_double_blocked_five(self, player):
        line = line_cells((5, 3), "horizontal", 5)
        env, result, moves = scenario(player, line, line[2], blockers_for("both", line, "horizontal"))
        assert_continues(env, result, moves)
        before = env.state.move_count
        next_action = env.legal_actions()[0]
        follow_up = env.step(next_action)
        assert follow_up.next_state.move_count == before + 1
        assert follow_up.next_state.last_action == next_action
        check_state_invariants(follow_up.next_state)


# ---------------------------------------------------------------------------
# Sát biên: biên bàn cờ là một đầu bị chặn
# ---------------------------------------------------------------------------
EDGE_LINES = [
    ("left_border_horizontal", (5, 0), "horizontal"),
    ("right_border_horizontal", (5, 6), "horizontal"),
    ("top_border_vertical", (0, 5), "vertical"),
    ("bottom_border_vertical", (6, 5), "vertical"),
    ("top_left_corner_diagonal", (0, 0), "diagonal"),
    ("bottom_right_corner_diagonal", (6, 6), "diagonal"),
    ("top_right_corner_anti_diagonal", (0, 10), "anti_diagonal"),
    ("bottom_left_corner_anti_diagonal", (6, 4), "anti_diagonal"),
]
EDGE_PARAMS = [pytest.param(start, d, id=name) for name, start, d in EDGE_LINES]


def inside_end(line: list[Cell], direction: str) -> Cell:
    inside = [e for e in ends_of(line, direction) if in_bounds(e)]
    assert len(inside) == 1, "fixture error: line must touch exactly one border"
    return inside[0]


class TestBoardEdges:
    @pytest.mark.parametrize("start, direction", EDGE_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize("last_index", [0, 4])
    def test_five_touching_border_with_free_end_wins(self, start, direction, player, last_index):
        # EDGE-XXXXX_ -> thắng (một đầu bị chặn bởi biên là đủ)
        line = line_cells(start, direction, 5)
        inside_end(line, direction)
        env, result, moves = scenario(player, line, line[last_index])
        assert_wins(env, result, player, moves)

    @pytest.mark.parametrize("start, direction", EDGE_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize("last_index", [0, 4])
    def test_five_touching_border_with_opponent_on_other_end_does_not_win(
        self, start, direction, player, last_index
    ):
        # EDGE-XXXXXO -> không thắng (chính là TC07_BLOCKED_BY_O_AND_EDGE)
        line = line_cells(start, direction, 5)
        env, result, moves = scenario(player, line, line[last_index], [inside_end(line, direction)])
        assert_continues(env, result, moves)

    @pytest.mark.parametrize(
        "name, start, direction",
        [
            ("top_row", (0, 3), "horizontal"),
            ("bottom_row", (10, 3), "horizontal"),
            ("left_column", (3, 0), "vertical"),
            ("right_column", (3, 10), "vertical"),
        ],
    )
    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize("state", list(BLOCK_STATES))
    def test_line_running_along_a_border_is_not_blocked_by_it(
        self, name, start, direction, player, state
    ):
        # Chuỗi nằm DỌC theo biên: biên không phải đầu của chuỗi.
        line = line_cells(start, direction, 5)
        blockers = blockers_for(state, line, direction)
        env, result, moves = scenario(player, line, line[2], blockers)
        assert_outcome(env, result, player, moves, BLOCK_STATES[state])


# ---------------------------------------------------------------------------
# Overline (>= 6 quân) được tính thắng nếu không bị chặn hai đầu
# ---------------------------------------------------------------------------
class TestOverline:
    # Overline chỉ hình thành bằng một quân NỐI hai đoạn, mỗi đoạn < 5 quân; nếu
    # quân cuối ở đầu mút thì 5 quân trước đó đã thắng từ trước.
    @pytest.mark.parametrize(
        "length, index",
        [(length, i) for length in (6, 7) for i in range(length) if i <= 4 and length - 1 - i <= 4],
    )
    @pytest.mark.parametrize("player", PLAYERS)
    def test_overline_wins_when_the_last_stone_bridges_two_segments(self, length, index, player):
        line = line_cells((5, 2), "horizontal", length)
        env, result, moves = scenario(player, line, line[index])
        assert_wins(env, result, player, moves)

    @pytest.mark.parametrize("length", [6, 7])
    def test_overline_is_won_earlier_by_its_first_five_stones(self, length):
        # Đặt dần từ đầu mút: chuỗi 5 đầu tiên đã thắng, ván dừng ngay.
        line = line_cells((5, 2), "horizontal", length)
        env = new_env()
        moves = build_moves(Player.X, line[:5], line[4])
        assert_wins(env, replay(env, moves), Player.X, moves)

    @pytest.mark.parametrize("length", [6, 7])
    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize("state", list(BLOCK_STATES))
    def test_overline_block_states(self, length, player, state):
        line = line_cells((5, 2), "horizontal", length)
        blockers = blockers_for(state, line, "horizontal")
        env, result, moves = scenario(player, line, line[length // 2], blockers)
        assert_outcome(env, result, player, moves, BLOCK_STATES[state])

    @pytest.mark.parametrize("direction", DIRECTION_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    def test_six_in_every_direction_wins(self, direction, player):
        line = line_cells(SIX_START[direction], direction, 6)
        env, result, moves = scenario(player, line, line[2])
        assert_wins(env, result, player, moves)

    @pytest.mark.parametrize("length", [6, 7])
    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize("opponent_at_free_end", [False, True], ids=["free_end", "O_at_end"])
    def test_overline_against_border(self, length, player, opponent_at_free_end):
        line = line_cells((5, 0), "horizontal", length)  # đầu trái chạm biên
        blockers = [ends_of(line, "horizontal")[1]] if opponent_at_free_end else []
        env, result, moves = scenario(player, line, line[3], blockers)
        assert_outcome(env, result, player, moves, expect_win=not opponent_at_free_end)

    @pytest.mark.parametrize("direction", DIRECTION_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    def test_stone_filling_the_gap_creates_a_winning_overline(self, direction, player):
        # 3 quân + ô trống + 2 quân; quân lấp ô trống nối thành chuỗi 6.
        line = line_cells(SIX_START[direction], direction, 6)
        env, result, moves = scenario(player, line, line[3])
        assert_wins(env, result, player, moves)


# ---------------------------------------------------------------------------
# Không thắng giả
# ---------------------------------------------------------------------------
class TestNoFalseWin:
    @pytest.mark.parametrize("direction", DIRECTION_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize("last_index", [0, 2, 5])
    def test_three_gap_two_is_not_a_win(self, direction, player, last_index):
        # W2-T08: hai đoạn rời có tổng >= 5 không thắng.
        line = line_cells(SIX_START[direction], direction, 6)
        stones = [c for i, c in enumerate(line) if i != 3]
        assert len(stones) == 5
        env = new_env()
        moves = build_moves(player, stones, line[last_index])
        assert_continues(env, replay(env, moves), moves)

    @pytest.mark.parametrize("direction", DIRECTION_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize("last_index", [0, 5])
    def test_four_gap_one_is_not_a_win(self, direction, player, last_index):
        line = line_cells(SIX_START[direction], direction, 6)
        stones = [c for i, c in enumerate(line) if i != 4]
        env = new_env()
        moves = build_moves(player, stones, line[last_index])
        assert_continues(env, replay(env, moves), moves)

    @pytest.mark.parametrize("direction", DIRECTION_PARAMS)
    @pytest.mark.parametrize("player", PLAYERS)
    def test_gap_occupied_by_opponent_is_not_a_win(self, direction, player):
        line = line_cells(SIX_START[direction], direction, 6)
        stones = [c for i, c in enumerate(line) if i != 3]
        env = new_env()
        moves = build_moves(player, stones, line[5], blockers=[line[3]])
        assert_continues(env, replay(env, moves), moves)

    @pytest.mark.parametrize("player", PLAYERS)
    @pytest.mark.parametrize(
        "shape",
        [
            pytest.param([(5, 5), (5, 4), (5, 6), (4, 5), (6, 5)], id="plus"),
            pytest.param([(5, 5), (5, 6), (5, 7), (6, 5), (7, 5)], id="corner_L"),
        ],
    )
    def test_crossing_lines_are_not_a_win(self, player, shape):
        # 5 quân nhưng không quân nào tạo chuỗi 5 theo một hướng.
        env = new_env()
        moves = build_moves(player, shape, (5, 5))
        assert_continues(env, replay(env, moves), moves)


# ---------------------------------------------------------------------------
# Bảng ví dụ trong contract mục 3 (một hướng: hàng ngang)
# ---------------------------------------------------------------------------
CONTRACT_TABLE = [
    ("_XXXXX_", True),      # X thắng
    ("OXXXXX_", True),      # X thắng
    ("OXXXXXO", False),     # không thắng
    ("EDGE-XXXXX_", True),  # X thắng
    ("EDGE-XXXXXO", False), # không thắng (TC07)
    ("_XXXXXX_", True),     # overline: X thắng
]


class TestContractTable:
    @pytest.mark.parametrize("pattern, expect_win", CONTRACT_TABLE, ids=[p for p, _ in CONTRACT_TABLE])
    def test_row_of_the_contract_table(self, pattern, expect_win):
        at_edge = pattern.startswith("EDGE-")
        cells_text = pattern.removeprefix("EDGE-")
        # '_' ở đầu/cuối là ô trống nằm trong bàn; ký tự đầu tiên đặt ở cột 0 khi
        # chạm biên, ngược lại dịch vào để cả hai đầu nằm trong bàn.
        offset = 0 if at_edge else 2
        row = 5
        x_cells = [(row, offset + i) for i, ch in enumerate(cells_text) if ch == "X"]
        o_cells = [(row, offset + i) for i, ch in enumerate(cells_text) if ch == "O"]
        env = new_env()
        moves = build_moves(Player.X, x_cells, x_cells[len(x_cells) // 2], o_cells)
        assert_outcome(env, replay(env, moves), Player.X, moves, expect_win)


# ---------------------------------------------------------------------------
# Hòa
# ---------------------------------------------------------------------------
def _draw_moves() -> list[Cell]:
    """121 nước tạo bàn đầy không có chuỗi 5 nào (X 61 ô, O 60 ô)."""
    x_cells = [(r, c) for r in range(N) for c in range(N) if ((r + 2 * c) // 2) % 2 == 0]
    o_cells = [(r, c) for r in range(N) for c in range(N) if ((r + 2 * c) // 2) % 2 == 1]
    assert (len(x_cells), len(o_cells)) == (61, 60)
    return [x_cells[i // 2] if i % 2 == 0 else o_cells[i // 2] for i in range(N * N)]


DRAW_MOVES = _draw_moves()


class TestDraw:
    def test_full_board_without_winner_is_a_draw(self):
        env = new_env()
        result = replay(env, DRAW_MOVES)
        state = env.state
        assert result.done is True
        assert result.winner is None
        assert result.reward == 0.0
        assert state.terminated is True and state.winner is None
        assert state.move_count == N * N
        assert state.last_action == DRAW_MOVES[-1]
        assert state.current_player == Player.O  # X đi nước 121, lượt vẫn đổi
        assert env.legal_actions() == []
        check_state_invariants(state)

    def test_one_empty_cell_left_is_not_a_draw(self):
        env = new_env()
        result = replay(env, DRAW_MOVES[:-1])
        assert result.done is False
        assert env.state.terminated is False
        assert env.legal_actions() == [DRAW_MOVES[-1]]
        check_state_invariants(env.state)

    def test_draw_is_not_reported_before_the_board_is_full(self):
        env = new_env()
        for index, move in enumerate(DRAW_MOVES[:-1], start=1):
            result = env.step(move)
            assert result.done is False, f"ended early at ply {index}"
