"""Monte Carlo Tree Search agent cho contract ``caro-v2``.

Implementation giữ toàn bộ utility của MCTS trong file này để tôn trọng
ownership của sprint W34. Mỗi simulation làm việc trên ``env.clone_env()``;
environment được truyền vào ``choose_action`` chỉ được đọc.

Semantics counter:

* ``nodes`` tính root là một node và tăng khi một child mới được expansion.
* ``simulations`` chỉ tăng sau một vòng Selection -> Expansion -> Simulation ->
  Backpropagation hoàn tất.
* ``value_sum`` luôn theo góc nhìn player đang đi tại root. Vì vậy Selection ở
  node mà đối thủ đi sẽ đảo dấu exploitation trước khi cộng exploration term.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
import time

from core.engine.interfaces import (
    Action,
    AgentDecision,
    GameEnv,
    Player,
    SearchBudget,
)

__all__ = ["MCTSAgent"]


@dataclass(slots=True)
class _MCTSNode:
    """Node nội bộ; state thật được tái dựng trên clone bằng chuỗi action."""

    parent: _MCTSNode | None
    action: Action | None
    player_to_move: Player
    untried_actions: list[Action]
    children: list[_MCTSNode] = field(default_factory=list)
    visits: int = 0
    value_sum: float = 0.0

    @property
    def mean_value(self) -> float:
        return self.value_sum / self.visits if self.visits else 0.0


def _uct_score(
    child: _MCTSNode,
    *,
    parent_visits: int,
    exploration_weight: float,
    maximize_root_value: bool,
) -> float:
    """UCT của child; node chưa thăm luôn được ưu tiên khám phá."""

    if child.visits == 0:
        return math.inf
    exploitation = child.mean_value
    if not maximize_root_value:
        exploitation = -exploitation
    exploration = exploration_weight * math.sqrt(
        math.log(max(1, parent_visits)) / child.visits
    )
    return exploitation + exploration


def _select_child(
    node: _MCTSNode,
    *,
    root_player: Player,
    exploration_weight: float,
    rng: random.Random,
) -> _MCTSNode:
    """Chọn child UCT cao nhất; RNG cục bộ xử lý tie một cách tái lập."""

    if not node.children:
        raise RuntimeError("cannot select a child from a leaf node")
    maximize = node.player_to_move == root_player
    scored = [
        (
            _uct_score(
                child,
                parent_visits=node.visits,
                exploration_weight=exploration_weight,
                maximize_root_value=maximize,
            ),
            child,
        )
        for child in node.children
    ]
    best_score = max(score for score, _ in scored)
    tied = [child for score, child in scored if score == best_score]
    return rng.choice(tied)


def _expand(node: _MCTSNode, env: GameEnv, rng: random.Random) -> _MCTSNode:
    """Mở đúng một legal child và tiến clone ``env`` tới child đó."""

    if not node.untried_actions:
        raise RuntimeError("cannot expand a fully expanded node")
    index = rng.randrange(len(node.untried_actions))
    action = node.untried_actions.pop(index)
    if action not in env.legal_actions():
        raise RuntimeError(f"tree action {action!r} is not legal in the cloned state")
    env.step(action)
    child = _MCTSNode(
        parent=node,
        action=action,
        player_to_move=env.state.current_player,
        untried_actions=env.legal_actions(),
    )
    node.children.append(child)
    return child


def _rollout(
    env: GameEnv,
    *,
    root_player: Player,
    rng: random.Random,
    deadline: float | None,
) -> float | None:
    """Rollout ngẫu nhiên; ``None`` nghĩa là time budget ngắt giữa vòng.

    Guard tối đa bằng số ô còn lại trên bàn. Với ``CaroEnv`` chuẩn, ván phải
    terminal chậm nhất khi bàn đầy. Một implementation ``GameEnv`` khác không
    terminal đúng hạn được đánh giá trung lập thay vì làm vòng lặp vô hạn.
    """

    remaining = max(0, env.config.board_size * env.config.board_size - env.state.move_count)
    for _ in range(remaining + 1):
        if env.is_terminal():
            result = env.result(root_player)
            if result is None:  # pragma: no cover - vi phạm GameEnv contract
                raise RuntimeError("terminal environment returned no result")
            return float(result)
        if deadline is not None and time.perf_counter() >= deadline:
            return None
        legal = env.legal_actions()
        if not legal:
            # Defensive handling cho mock không đánh dấu terminal khi hết action.
            return 0.0
        env.step(rng.choice(legal))
    return 0.0


def _backpropagate(node: _MCTSNode, reward: float) -> None:
    """Cập nhật toàn bộ đường từ leaf về root theo root perspective."""

    current: _MCTSNode | None = node
    while current is not None:
        current.visits += 1
        current.value_sum += reward
        current = current.parent


class MCTSAgent:
    """MCTS seeded, có simulation/node/time budget và thỏa ``Agent`` protocol."""

    def __init__(
        self,
        name: str = "mcts",
        *,
        exploration_weight: float = math.sqrt(2.0),
        default_simulations: int = 100,
        seed: int | None = None,
    ) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string")
        if (
            isinstance(exploration_weight, bool)
            or not isinstance(exploration_weight, (int, float))
            or not math.isfinite(float(exploration_weight))
            or exploration_weight < 0
        ):
            raise ValueError("exploration_weight must be a finite non-negative number")
        if (
            isinstance(default_simulations, bool)
            or not isinstance(default_simulations, int)
            or default_simulations <= 0
        ):
            raise ValueError("default_simulations must be a positive integer")
        if seed is not None and (
            isinstance(seed, bool) or not isinstance(seed, int) or seed < 0
        ):
            raise ValueError("seed must be a non-negative integer or None")

        self._name = name
        self._exploration_weight = float(exploration_weight)
        self._default_simulations = default_simulations
        self._rng = random.Random(seed)

    @property
    def name(self) -> str:
        return self._name

    def choose_action(
        self,
        env: GameEnv,
        budget: SearchBudget | None = None,
    ) -> AgentDecision:
        started = time.perf_counter()
        if env.is_terminal():
            raise RuntimeError(f"{self._name}: cannot choose an action in a terminal state")
        legal = env.legal_actions()
        if not legal:
            raise RuntimeError(f"{self._name}: no legal actions available")

        active_budget = budget or SearchBudget()
        rng = (
            random.Random(active_budget.seed)
            if active_budget.seed is not None
            else self._rng
        )
        root_player = env.state.current_player
        root = _MCTSNode(
            parent=None,
            action=None,
            player_to_move=root_player,
            untried_actions=list(legal),
        )
        nodes = 1
        completed_simulations = 0
        simulation_limit = (
            active_budget.simulations
            if active_budget.simulations is not None
            else self._default_simulations
        )
        deadline = (
            started + active_budget.time_limit_ms / 1000.0
            if active_budget.time_limit_ms is not None
            else None
        )

        while completed_simulations < simulation_limit:
            if deadline is not None and time.perf_counter() >= deadline:
                break
            if active_budget.max_nodes is not None and nodes >= active_budget.max_nodes:
                break

            simulation_env = env.clone_env()
            node = root

            # Selection: phát lại action trên clone để state khớp node trong cây.
            while (
                not simulation_env.is_terminal()
                and not node.untried_actions
                and node.children
            ):
                node = _select_child(
                    node,
                    root_player=root_player,
                    exploration_weight=self._exploration_weight,
                    rng=rng,
                )
                if node.action is None:  # pragma: no cover - invariant của tree
                    raise RuntimeError("non-root MCTS node has no action")
                simulation_env.step(node.action)
                if deadline is not None and time.perf_counter() >= deadline:
                    break

            if deadline is not None and time.perf_counter() >= deadline:
                break

            # Expansion chỉ tạo một child và không vượt max_nodes.
            if not simulation_env.is_terminal() and node.untried_actions:
                if active_budget.max_nodes is not None and nodes >= active_budget.max_nodes:
                    break
                node = _expand(node, simulation_env, rng)
                nodes += 1

            reward = _rollout(
                simulation_env,
                root_player=root_player,
                rng=rng,
                deadline=deadline,
            )
            if reward is None:
                break
            _backpropagate(node, reward)
            completed_simulations += 1

        visited = [child for child in root.children if child.visits > 0]
        if visited:
            # Robust child: visits trước, value sau, action row-major làm tie-break.
            chosen = min(
                visited,
                key=lambda child: (
                    -child.visits,
                    -child.mean_value,
                    child.action,
                ),
            )
            action = chosen.action
            score = chosen.mean_value
        else:
            # Budget có thể bằng 0 ms hoặc max_nodes=1; vẫn phải trả action legal.
            action = legal[0]
            score = 0.0

        if action is None:  # pragma: no cover - chỉ bảo vệ type invariant
            raise RuntimeError("MCTS failed to select a legal action")
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return AgentDecision(
            action=action,
            score=float(score),
            nodes=nodes,
            simulations=completed_simulations,
            elapsed_ms=elapsed_ms,
        )

    def __repr__(self) -> str:
        return (
            f"MCTSAgent(name={self._name!r}, "
            f"exploration_weight={self._exploration_weight!r}, "
            f"default_simulations={self._default_simulations!r})"
        )
