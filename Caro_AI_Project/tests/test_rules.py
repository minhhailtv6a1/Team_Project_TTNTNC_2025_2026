import copy
import json
import random
from pathlib import Path

import pytest

from core.engine.interfaces import GameConfig, InvalidConfigError, Player
from core.engine.rules import RuleEngine, DIRECTIONS

N = 11
CFG = GameConfig()
FIXTURE = Path(__file__).parent / "fixtures" / "rule_vectors.json"
LEGACY = Path(__file__).parent / "fixtures" / "test_vectors.json"


def empty_board():
    return [[0] * N for _ in range(N)]


def build(stones):
    b = empty_board()
    for r, c, p in stones:
        b[r][c] = p
    return b


def place_line(b, start, d, pattern):
    for i, ch in enumerate(pattern):
        if ch != ".":
            b[start[0] + i * d[0]][start[1] + i * d[1]] = 1 if ch == "X" else -1
    return b


def as_player(v):
    return None if v is None else Player(v)


# fixture-driven
_CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))["test_cases"]


@pytest.mark.parametrize("case", _CASES, ids=[c["id"] for c in _CASES])
def test_vectors_check_winner_and_terminal(case):
    board = build(case["stones"])
    snapshot = copy.deepcopy(board)
    expected = as_player(case["expected_winner"])

    assert RuleEngine.check_winner(board, CFG) == expected
    assert RuleEngine.is_terminal(board, CFG) == (case["expected_terminated"], expected)
    assert board == snapshot, "hàm kiểm tra không được sửa board"


@pytest.mark.parametrize("case", [c for c in _CASES if c["expected_winner"] is not None],
                         ids=lambda c: c["id"])
def test_vectors_winning_cases_detected_from_any_stone_of_line(case):
    """check_winner_from_action phải ra cùng kết quả khi last_action là bất kỳ quân nào của người thắng."""
    board = build(case["stones"])
    w = case["expected_winner"]
    hits = [(r, c) for r, c, p in case["stones"] if p == w]
    found = [a for a in hits if RuleEngine.check_winner_from_action(board, a, CFG) == Player(w)]
    assert found, "không quân nào của chuỗi thắng được nhận diện"


# 4 hướng x 2 người x mọi vị trí
def _all_positions(d, length=5):
    dr, dc = d
    for r in range(N):
        for c in range(N):
            er, ec = r + (length - 1) * dr, c + (length - 1) * dc
            if 0 <= er < N and 0 <= ec < N:
                yield r, c


@pytest.mark.parametrize("d", DIRECTIONS)
@pytest.mark.parametrize("player", [Player.X, Player.O])
def test_every_position_every_direction(d, player):
    """Mọi vị trí 5 quân trên bàn: thắng đúng khi KHÔNG bị chặn cả hai đầu (đầu = quân địch hoặc biên)."""
    opp = -int(player)
    dr, dc = d
    for r, c in _all_positions(d):
        for pre in (0, opp):
            for post in (0, opp):
                b = empty_board()
                for i in range(5):
                    b[r + i * dr][c + i * dc] = int(player)
                pr, pc = r - dr, c - dc
                qr, qc = r + 5 * dr, c + 5 * dc
                pre_in = 0 <= pr < N and 0 <= pc < N
                post_in = 0 <= qr < N and 0 <= qc < N
                if pre_in:
                    b[pr][pc] = pre
                if post_in:
                    b[qr][qc] = post
                blocked1 = (not pre_in) or pre == opp
                blocked2 = (not post_in) or post == opp
                expected = None if (blocked1 and blocked2) else player
                assert RuleEngine.check_winner(b, CFG) == expected, (d, player, r, c, pre, post)
                assert RuleEngine.check_winner_from_action(b, (r + 2 * dr, c + 2 * dc), CFG) == expected


# overline mọi độ dài/hướng
@pytest.mark.parametrize("d", DIRECTIONS)
@pytest.mark.parametrize("length", [6, 7, 8])
def test_overline_follows_blocked_both_ends_rule(d, length):
    """Overline thắng trừ khi cả hai đầu bị chặn (biên hoặc O). Đường chéo ngắn đúng `length` ô => biên chặn 2 đầu."""
    dr, dc = d
    for r, c in _all_positions(d, length):
        pr, pc, qr, qc = r - dr, c - dc, r + length * dr, c + length * dc
        pre_in = 0 <= pr < N and 0 <= pc < N
        post_in = 0 <= qr < N and 0 <= qc < N
        for pre in (0, -1):
            for post in (0, -1):
                b = empty_board()
                for i in range(length):
                    b[r + i * dr][c + i * dc] = 1
                if pre_in:
                    b[pr][pc] = pre
                if post_in:
                    b[qr][qc] = post
                blocked = ((not pre_in) or pre == -1) and ((not post_in) or post == -1)
                expected = None if blocked else Player.X
                assert RuleEngine.check_winner(b, CFG) == expected, (d, length, r, c, pre, post)


# check_line độc lập vị trí truyền vào
@pytest.mark.parametrize("d", DIRECTIONS)
def test_check_line_is_independent_of_entry_cell(d):
    dr, dc = d
    b = empty_board()
    start = (3, 4) if d != (1, -1) else (3, 6)
    for i in range(6):
        b[start[0] + i * dr][start[1] + i * dc] = 1
    for i in range(6):
        assert RuleEngine.check_line(b, start[0] + i * dr, start[1] + i * dc, dr, dc, 1, N, 5)
    # chặn cả hai đầu -> mọi ô vào đều trả False
    b[start[0] - dr][start[1] - dc] = -1
    b[start[0] + 6 * dr][start[1] + 6 * dc] = -1
    for i in range(6):
        assert not RuleEngine.check_line(b, start[0] + i * dr, start[1] + i * dc, dr, dc, 1, N, 5)


def test_check_line_guards():
    b = empty_board()
    assert not RuleEngine.check_line(b, 0, 0, 0, 1, 0, N, 5)    # EMPTY player
    assert not RuleEngine.check_line(b, 5, 5, 0, 1, 1, N, 5)    # ô không phải quân của player
    assert not RuleEngine.check_line(b, -1, 0, 0, 1, 1, N, 5)   # ngoài biên
    assert not RuleEngine.check_line(b, 0, N, 0, 1, 1, N, 5)


# tách bạch chuỗi rời nhau
@pytest.mark.parametrize("d", DIRECTIONS)
@pytest.mark.parametrize("pattern", ["XXXX.X", "XXX.XX", "XX.XXX", "X.XXXX", "XXXXOXXXX", "XXXX.XXXX"])
def test_disjoint_chains_never_fake_a_win(d, pattern):
    start = {(0, 1): (5, 0), (1, 0): (0, 5), (1, 1): (0, 0), (1, -1): (0, 10)}[d]
    b = place_line(empty_board(), start, d, pattern)
    assert RuleEngine.check_winner(b, CFG) is None
    assert RuleEngine.is_terminal(b, CFG) == (False, None)


# hòa / thắng trước hòa
def _draw_board():
    return [[1 if (r // 2 + c) % 2 == 0 else -1 for c in range(N)] for r in range(N)]


def test_full_board_without_win_is_draw():
    b = _draw_board()
    assert RuleEngine.is_board_full(b, N)
    assert RuleEngine.is_terminal(b, CFG) == (True, None)


def test_any_full_board_is_draw_under_blocked_both_ends_rule():
    """Bàn đầy => không còn ô trống nên mọi chuỗi bị chặn cả 2 đầu => luôn hòa (không bao giờ có winner)."""
    rng = random.Random(99)
    for _ in range(200):
        b = [[rng.choice([-1, 1]) for _ in range(N)] for _ in range(N)]
        assert RuleEngine.is_terminal(b, CFG) == (True, None)


def test_win_is_reported_before_draw_check():
    """Còn ô trống + chuỗi thắng hợp lệ => (True, winner); thứ tự check_winner trước is_board_full."""
    b = _draw_board()
    b[5] = [-1, 1, 1, 1, 1, 1, 0] + b[5][7:]
    b[5][0] = -1
    assert RuleEngine.is_terminal(b, CFG) == (True, Player.X)


def test_board_not_full_without_win_is_not_terminal():
    b = _draw_board()
    b[10][10] = 0
    assert RuleEngine.is_terminal(b, CFG) == (False, None)


# pure / không mutation
def test_functions_do_not_mutate_board():
    rng = random.Random(7)
    for _ in range(50):
        b = [[rng.choice([-1, 0, 1]) for _ in range(N)] for _ in range(N)]
        snap = copy.deepcopy(b)
        RuleEngine.check_winner(b, CFG)
        RuleEngine.is_terminal(b, CFG)
        RuleEngine.is_board_full(b, N)
        RuleEngine.check_winner_from_action(b, (5, 5), CFG)
        assert b == snap


# đối chiếu oracle độc lập (chuỗi ký tự)
def oracle_winner(board):
    """Cài đặt khác hẳn engine: duyệt từng đường thành chuỗi, '#' = biên."""
    lines = []
    for r in range(N):
        lines.append([board[r][c] for c in range(N)])
    for c in range(N):
        lines.append([board[r][c] for r in range(N)])
    for k in range(-(N - 1), N):
        lines.append([board[i][i - k] for i in range(N) if 0 <= i - k < N])
    for k in range(0, 2 * N - 1):
        lines.append([board[i][k - i] for i in range(N) if 0 <= k - i < N])
    winners = set()
    for ln in lines:
        seq = ["#"] + ln + ["#"]
        i = 1
        while i < len(seq) - 1:
            if seq[i] in (1, -1):
                j = i
                while seq[j + 1] == seq[i]:
                    j += 1
                p = seq[i]
                if j - i + 1 >= 5:
                    bl = lambda v: v == "#" or v == -p
                    if not (bl(seq[i - 1]) and bl(seq[j + 1])):
                        winners.add(p)
                i = j + 1
            else:
                i += 1
    return winners


def _random_board(rng):
    b = [[rng.choice([0, 0, 0, 1, -1]) for _ in range(N)] for _ in range(N)]
    for _ in range(rng.randint(1, 3)):  # cấy chuỗi dài 3..8 để có nhiều ca biên
        d = rng.choice(DIRECTIONS)
        ln = rng.randint(3, 8)
        r, c = rng.randrange(N), rng.randrange(N)
        p = rng.choice([1, -1])
        for i in range(ln):
            rr, cc = r + i * d[0], c + i * d[1]
            if 0 <= rr < N and 0 <= cc < N:
                b[rr][cc] = p
        for rr, cc in ((r - d[0], c - d[1]), (r + ln * d[0], c + ln * d[1])):
            if 0 <= rr < N and 0 <= cc < N and rng.random() < 0.5:
                b[rr][cc] = -p
    return b


def test_matches_independent_oracle_on_random_boards():
    rng = random.Random(20260101)
    wins = 0
    for _ in range(3000):
        b = _random_board(rng)
        ws = oracle_winner(b)
        got = RuleEngine.check_winner(b, CFG)
        if len(ws) == 1:
            assert got == Player(next(iter(ws)))
            wins += 1
        elif not ws:
            assert got is None
        else:  # hai người cùng có chuỗi thắng: trạng thái không đạt được trong ván thật
            assert got in (Player.X, Player.O)
    assert wins > 100, "tập random phải chứa đủ ca thắng để test có ý nghĩa"


def test_incremental_check_equals_full_scan_in_random_games():
    """Mô phỏng ván thật: sau mỗi nước, kiểm tra quanh last_action == quét toàn bàn."""
    rng = random.Random(42)
    finished_by_win = 0
    for _ in range(300):
        b = empty_board()
        cells = [(r, c) for r in range(N) for c in range(N)]
        rng.shuffle(cells)
        player = 1
        for (r, c) in cells:
            b[r][c] = player
            full = RuleEngine.check_winner(b, CFG)
            inc = RuleEngine.check_winner_from_action(b, (r, c), CFG)
            assert inc == full
            if full is not None:
                finished_by_win += 1
                break
            player = -player
    assert finished_by_win > 0


# fixture nhóm (test_vectors.json, caro-v2)
_LEGACY = json.loads(LEGACY.read_text(encoding="utf-8"))
_LEGACY_CASES = _LEGACY["test_cases"]


def test_team_fixture_header_matches_contract_v2():
    assert _LEGACY["game_version"] == "caro-v2"
    assert _LEGACY["board_size"] == N == CFG.board_size
    assert _LEGACY["win_length"] == CFG.win_length
    assert _LEGACY["blocked_both_ends_rule"] is True


def test_team_fixture_ids_unique_and_actions_are_tuples():
    ids = [tc["id"] for tc in _LEGACY_CASES]
    assert len(ids) == len(set(ids))
    for tc in _LEGACY_CASES:
        for m in tc.get("board_moves", []):
            r, c = m["action"]  # public action = [row, col], không phải int phẳng
            assert isinstance(r, int) and isinstance(c, int) and not isinstance(r, bool)
            assert 0 <= r < N and 0 <= c < N
            assert m["player"] in (1, -1)


@pytest.mark.parametrize("tc", _LEGACY_CASES, ids=[t["id"] for t in _LEGACY_CASES])
def test_team_fixture(tc):
    """board_moves là chuỗi chơi được: X đi trước, luân phiên, ván chỉ kết thúc ở nước cuối (nếu có)."""
    moves = tc["board_moves"]
    b = empty_board()
    for i, m in enumerate(moves):
        assert m["player"] == (1 if i % 2 == 0 else -1), f"{tc['id']}: nước {i} sai lượt"
        r, c = m["action"]
        assert b[r][c] == 0, f"{tc['id']}: nước {i} đặt vào ô đã có quân"
        b[r][c] = m["player"]
        done, _ = RuleEngine.is_terminal(b, CFG)
        if i < len(moves) - 1:
            assert not done, f"{tc['id']}: ván kết thúc sớm ở nước {i} (trước nước cuối)"

    expected = as_player(tc["expected_winner"])
    assert RuleEngine.check_winner(b, CFG) == expected, tc["id"]
    assert RuleEngine.is_terminal(b, CFG) == (tc["terminated"], expected), tc["id"]
    # nước cuối phải là nước hoàn tất chuỗi (nếu có người thắng)
    if expected is not None:
        last = tuple(moves[-1]["action"])
        assert RuleEngine.check_winner_from_action(b, last, CFG) == expected


def test_check_winner_from_action_ignores_invalid_or_empty_cell():
    b = place_line(empty_board(), (5, 2), (0, 1), "XXXXX")
    assert RuleEngine.check_winner_from_action(b, (-1, 0), CFG) is None
    assert RuleEngine.check_winner_from_action(b, (0, N), CFG) is None
    assert RuleEngine.check_winner_from_action(b, (0, 0), CFG) is None  # ô trống

# ================================================================== W2-M2-02: terminal / hòa
@pytest.mark.parametrize("filled, has_win, expected", [
    ("full", False, (True, None)),                 # đầy + không thắng  -> hòa
    ("almost_full", False, (False, None)),         # còn 1 ô trống      -> chưa xong
    ("almost_full", True, (True, Player.X)),       # còn ô trống + thắng -> X thắng
    ("empty", False, (False, None)),
])
def test_draw_only_when_full_and_no_winner(filled, has_win, expected):
    if filled == "empty":
        b = empty_board()
    else:
        b = _draw_board()
        if filled == "almost_full":
            b[10][10] = 0
    if has_win:
        b[5] = [-1, 1, 1, 1, 1, 1, 0] + b[5][7:]
        b[5][0] = -1
    assert RuleEngine.is_terminal(b, CFG) == expected


def test_is_terminal_is_idempotent_and_pure():
    rng = random.Random(11)
    for _ in range(100):
        b = _random_board(rng)
        snap = copy.deepcopy(b)
        first = RuleEngine.is_terminal(b, CFG)
        assert RuleEngine.is_terminal(b, CFG) == first and b == snap


def test_check_winner_from_action_equals_full_scan_on_every_prefix():
    """Env dùng kiểm tra quanh last_action: phải bằng quét toàn bàn tại MỌI nước của mọi ván fixture."""
    for tc in _LEGACY_CASES:
        b = empty_board()
        for m in tc["board_moves"]:
            r, c = m["action"]
            b[r][c] = m["player"]
            assert RuleEngine.check_winner_from_action(b, (r, c), CFG) == RuleEngine.check_winner(b, CFG), tc["id"]


# ================================================================== W2-M2-03: nền cho undo
def test_removing_last_move_reopens_every_won_fixture_game():
    """Undo nước thắng => bàn trước đó phải được engine coi là CHƯA kết thúc (khớp env.undo)."""
    checked = 0
    for tc in _LEGACY_CASES:
        if tc["expected_winner"] is None:
            continue
        b = empty_board()
        for m in tc["board_moves"]:
            r, c = m["action"]
            b[r][c] = m["player"]
        assert RuleEngine.is_terminal(b, CFG)[0] is True
        r, c = tc["board_moves"][-1]["action"]
        b[r][c] = 0
        assert RuleEngine.is_terminal(b, CFG) == (False, None), tc["id"]
        checked += 1
    assert checked >= 6


def test_rules_follow_config_board_size():
    """Kết quả nhất quán trên cấu hình 11x11; kích thước khác bị contract từ chối."""
    assert CFG.board_size == 11 and CFG.win_length == 5
    b = place_line(empty_board(), (5, 2), (0, 1), "XXXXX")
    assert RuleEngine.check_winner(b, GameConfig()) == RuleEngine.check_winner(b, GameConfig(11, 5)) == Player.X
    with pytest.raises(InvalidConfigError):
        GameConfig(board_size=9)
    with pytest.raises(InvalidConfigError):
        GameConfig(win_length=4)