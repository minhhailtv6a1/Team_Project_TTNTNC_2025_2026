"""Test RandomAgent: W34-T05 (legal) và W34-T06 (seed tái lập), kèm contract chung.

``StubEnv`` là ``GameEnv`` tối giản chỉ phục vụ test agent: nó cho phép dựng
state bất kỳ và *từ chối* mọi thao tác ghi, nên nếu agent cố ``step``/``undo``/
``reset`` thì test sẽ lỗi ngay. Test tích hợp với ``CaroEnv`` thật nằm ở
``tests/test_agents_integration.py``.
"""

from __future__ import annotations

import inspect
import random
import re
from collections import Counter

import pytest

from core.agents import random_ai
from core.agents.random_ai import RandomAgent
from core.engine.interfaces import (
    Action,
    Agent,
    AgentDecision,
    GameConfig,
    GameState,
    Player,
    SearchBudget,
)

N = GameConfig().board_size


class StubEnv:
    """Môi trường chỉ đọc: state dựng từ danh sách ô đã chiếm."""

    def __init__(self, occupied: list[Action] | None = None, terminated: bool = False):
        self._occupied = list(occupied or [])
        self._terminated = terminated
        self._cfg = GameConfig()

    @property
    def config(self) -> GameConfig:
        return self._cfg

    @property
    def state(self) -> GameState:
        board = [[0] * N for _ in range(N)]
        for index, (row, col) in enumerate(self._occupied):
            board[row][col] = 1 if index % 2 == 0 else -1
        count = len(self._occupied)
        return GameState(
            board=board,
            current_player=Player.X if count % 2 == 0 else Player.O,
            last_action=self._occupied[-1] if self._occupied else None,
            move_count=count,
            terminated=self._terminated,
            winner=None,
        )

    def is_terminal(self) -> bool:
        return self._terminated

    def legal_actions(self) -> list[Action]:
        if self._terminated:
            return []
        taken = set(self._occupied)
        return [(r, c) for r in range(N) for c in range(N) if (r, c) not in taken]

    def clone_env(self) -> StubEnv:
        return StubEnv(self._occupied, self._terminated)

    def step(self, action):  # pragma: no cover - chỉ chạy khi agent vi phạm
        raise AssertionError("agent must not call step() on the real env")

    def undo(self):  # pragma: no cover
        raise AssertionError("agent must not call undo() on the real env")

    def reset(self, seed=None):  # pragma: no cover
        raise AssertionError("agent must not call reset() on the real env")


def all_cells() -> list[Action]:
    return [(r, c) for r in range(N) for c in range(N)]


def board_with_free(free: list[Action]) -> StubEnv:
    """Bàn đầy trừ các ô trong ``free`` (không terminal)."""
    return StubEnv([cell for cell in all_cells() if cell not in set(free)])


SCENARIOS = {
    "empty": StubEnv(),
    "two_plies": StubEnv([(5, 5), (5, 6)]),
    "midgame": StubEnv([(5, 5), (4, 4), (5, 6), (6, 6), (3, 3), (7, 7)]),
    "corner_and_edges": StubEnv([(0, 0), (0, N - 1), (N - 1, 0), (N - 1, N - 1)]),
    "almost_full": board_with_free([(2, 3), (7, 8), (10, 0)]),
}


# ---------------------------------------------------------------------------
# Protocol và hình dạng decision
# ---------------------------------------------------------------------------
def test_satisfies_agent_protocol_and_has_name():
    agent = RandomAgent()
    assert isinstance(agent, Agent)
    assert agent.name == "random"
    assert RandomAgent(name="baseline").name == "baseline"


@pytest.mark.parametrize("bad_name", ["", None, 3])
def test_rejects_invalid_name(bad_name):
    with pytest.raises(ValueError):
        RandomAgent(name=bad_name)


def test_decision_shape():
    decision = RandomAgent().choose_action(StubEnv(), SearchBudget(seed=1))
    assert isinstance(decision, AgentDecision)
    assert decision.nodes == 0 and decision.simulations == 0
    assert decision.score is None
    assert isinstance(decision.elapsed_ms, float) and decision.elapsed_ms >= 0.0
    row, col = decision.action
    assert type(row) is int and type(col) is int  # tuple (row, col), không phải bool/index


def test_works_without_budget():
    env = StubEnv([(5, 5)])
    decision = RandomAgent(seed=3).choose_action(env)
    assert decision.action in env.legal_actions()


def test_other_budget_fields_are_ignored():
    budget = SearchBudget(time_limit_ms=1, max_depth=2, max_nodes=3, simulations=4, seed=5)
    decision = RandomAgent().choose_action(StubEnv(), budget)
    assert decision.nodes == 0 and decision.simulations == 0


# ---------------------------------------------------------------------------
# W34-T05: không bao giờ trả action không hợp lệ
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_t05_action_always_legal_across_seeds(scenario):
    env = SCENARIOS[scenario]
    legal = set(env.legal_actions())
    agent = RandomAgent()
    for seed in range(200):
        decision = agent.choose_action(env, SearchBudget(seed=seed))
        assert decision.action in legal, (scenario, seed, decision.action)


def test_t05_single_legal_action_is_returned():
    env = board_with_free([(4, 7)])
    for seed in range(20):
        assert RandomAgent().choose_action(env, SearchBudget(seed=seed)).action == (4, 7)


def test_t05_never_picks_occupied_cells_with_instance_rng():
    env = SCENARIOS["midgame"]
    legal = set(env.legal_actions())
    agent = RandomAgent(seed=123)
    for _ in range(300):
        assert agent.choose_action(env).action in legal


def test_choice_is_roughly_uniform():
    free = [(1, 1), (3, 5), (6, 2), (9, 8)]
    env = board_with_free(free)
    counts = Counter(
        RandomAgent().choose_action(env, SearchBudget(seed=s)).action for s in range(2000)
    )
    assert set(counts) == set(free)
    # kỳ vọng 500 mỗi ô; seed cố định nên kết quả xác định, không flaky
    assert all(400 <= n <= 600 for n in counts.values()), counts


# ---------------------------------------------------------------------------
# W34-T06: cùng seed thì cùng action
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_t06_same_seed_same_action(scenario):
    env = SCENARIOS[scenario]
    for seed in (0, 1, 7, 12345):
        budget = SearchBudget(seed=seed)
        a = RandomAgent().choose_action(env, budget).action
        b = RandomAgent().choose_action(env, budget).action
        c = RandomAgent(name="other", seed=999).choose_action(env, budget).action
        assert a == b == c  # không phụ thuộc instance hay seed của constructor


def test_t06_repeated_calls_with_same_budget_seed_are_stable():
    env = SCENARIOS["midgame"]
    agent = RandomAgent()
    budget = SearchBudget(seed=42)
    first = agent.choose_action(env, budget).action
    assert all(agent.choose_action(env, budget).action == first for _ in range(20))


def test_t06_different_seeds_give_variety():
    env = StubEnv()
    actions = {RandomAgent().choose_action(env, SearchBudget(seed=s)).action for s in range(100)}
    assert len(actions) > 20


def test_instance_seed_gives_reproducible_sequence():
    env = SCENARIOS["two_plies"]
    one, two = RandomAgent(seed=8), RandomAgent(seed=8)
    seq_one = [one.choose_action(env).action for _ in range(30)]
    seq_two = [two.choose_action(env).action for _ in range(30)]
    assert seq_one == seq_two
    assert len(set(seq_one)) > 1  # RNG tiến lên giữa các lần gọi


def test_budget_seed_overrides_instance_seed():
    env = SCENARIOS["midgame"]
    budget = SearchBudget(seed=31)
    expected = RandomAgent().choose_action(env, budget).action
    assert RandomAgent(seed=1).choose_action(env, budget).action == expected
    assert RandomAgent(seed=2).choose_action(env, budget).action == expected


# ---------------------------------------------------------------------------
# Không dùng RNG toàn cục
# ---------------------------------------------------------------------------
def test_does_not_touch_global_random_state():
    env = SCENARIOS["midgame"]
    random.seed(1234)
    before = random.getstate()
    RandomAgent().choose_action(env, SearchBudget(seed=5))
    RandomAgent(seed=5).choose_action(env)
    RandomAgent().choose_action(env)
    assert random.getstate() == before


def test_result_independent_of_global_seed():
    env = SCENARIOS["midgame"]
    budget = SearchBudget(seed=77)
    random.seed(1)
    a = RandomAgent().choose_action(env, budget).action
    random.seed(2)
    b = RandomAgent().choose_action(env, budget).action
    assert a == b


# ---------------------------------------------------------------------------
# Không mutation env
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("scenario", SCENARIOS)
def test_does_not_mutate_env(scenario):
    env = SCENARIOS[scenario]
    before = env.state
    legal_before = env.legal_actions()
    for seed in range(25):
        RandomAgent().choose_action(env, SearchBudget(seed=seed))
    assert env.state == before
    assert env.legal_actions() == legal_before
    # StubEnv.step/undo/reset ném AssertionError nên chưa có gọi nào xảy ra.


# ---------------------------------------------------------------------------
# Terminal và hết nước đi
# ---------------------------------------------------------------------------
def test_terminal_env_raises_runtime_error():
    with pytest.raises(RuntimeError):
        RandomAgent().choose_action(StubEnv([(0, 0), (1, 1)], terminated=True))


def test_terminal_env_raises_with_budget_too():
    with pytest.raises(RuntimeError):
        RandomAgent().choose_action(StubEnv(terminated=True), SearchBudget(seed=1))


def test_no_legal_actions_raises_runtime_error():
    full = StubEnv(all_cells())  # bàn đầy nhưng cờ terminal chưa được bật
    assert full.legal_actions() == []
    with pytest.raises(RuntimeError):
        RandomAgent().choose_action(full, SearchBudget(seed=1))


# ---------------------------------------------------------------------------
# W34-T29: không hard-code phạm vi bàn cờ cũ
# ---------------------------------------------------------------------------
def test_t29_no_hardcoded_old_board_literals():
    source = inspect.getsource(random_ai)
    assert not re.search(r"\b(9|81)\b", source)
