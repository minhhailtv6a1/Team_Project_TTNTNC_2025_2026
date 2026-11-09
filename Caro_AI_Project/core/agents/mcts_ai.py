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
from typing import Callable

from core.engine.interfaces import (
    Action,
    AgentDecision,
    GameEnv,
    Player,
    SearchBudget,
)
from core.agents.search_utils import (
    choose_tactical_local_action,
    normalized_line_value,
    rank_candidate_actions,
    tactical_summary,
)
from core.agents.heuristic_ai import action_priority
from core.agents.minimax_ai import candidate_actions, evaluate_board

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


def _allowed_children(
    node: _MCTSNode,
    *,
    widening_c: float | None,
    widening_alpha: float,
) -> int:
    """Number of children currently allowed by progressive widening."""

    total = len(node.children) + len(node.untried_actions)
    if widening_c is None:
        return total
    limit = max(1, math.ceil(widening_c * ((node.visits + 1) ** widening_alpha)))
    return min(total, limit)


ActionOrderer = Callable[[GameEnv, list[Action], random.Random], list[Action]]


def _rank_heuristic_actions(
    env: GameEnv,
    actions: list[Action],
    rng: random.Random,
) -> list[Action]:
    """Order the full legal set by the shared tactical pattern score."""

    state = env.state
    shuffled = list(actions)
    rng.shuffle(shuffled)
    shuffled.sort(
        key=lambda action: -action_priority(
            state.board,
            action,
            state.current_player,
            env.config.win_length,
        )
    )
    return shuffled


def _choose_heuristic_rollout_action(
    env: GameEnv,
    legal: list[Action],
    *,
    epsilon: float,
    neighbor_radius: int,
    rng: random.Random,
) -> Action:
    """Seeded epsilon-greedy rollout using tactical pattern priority."""

    state = env.state
    local = candidate_actions(state.board, legal, neighbor_radius) or legal
    tactics = tactical_summary(
        state.board,
        local,
        state.current_player,
        env.config,
    )
    if tactics.winning_actions:
        return tactics.winning_actions[0]
    if tactics.unique_forced_block is not None:
        return tactics.unique_forced_block
    if rng.random() < epsilon:
        return rng.choice(local)
    ranked = list(local)
    rng.shuffle(ranked)
    ranked.sort(
        key=lambda action: -action_priority(
            state.board,
            action,
            state.current_player,
            env.config.win_length,
        )
    )
    return ranked[0]


def _normalized_pattern_value(
    env: GameEnv,
    root_player: Player,
) -> float:
    """Map the Minimax pattern evaluator to a bounded MCTS leaf reward."""

    raw = evaluate_board(env.state.board, root_player, env.config.win_length)
    return math.tanh(raw / 5_000.0)


def _expand_ranked(
    node: _MCTSNode,
    env: GameEnv,
    rng: random.Random,
    *,
    ordered: bool,
    orderer: ActionOrderer | None,
) -> _MCTSNode:
    """Expand one action while preserving the legacy random expansion mode."""

    if not node.untried_actions:
        raise RuntimeError("cannot expand a fully expanded node")
    index = 0 if ordered else rng.randrange(len(node.untried_actions))
    action = node.untried_actions.pop(index)
    # The action came from this node's cached legal set. ``step`` remains the
    # authoritative validation and avoids a duplicate full-board legal scan.
    env.step(action)
    legal = env.legal_actions()
    if orderer is not None and legal:
        legal = orderer(env, legal, rng)
    child = _MCTSNode(
        parent=node,
        action=action,
        player_to_move=env.state.current_player,
        untried_actions=legal,
    )
    node.children.append(child)
    return child


def _rollout(
    env: GameEnv,
    *,
    root_player: Player,
    rng: random.Random,
    deadline: float | None,
    policy: str = "random",
    epsilon: float = 0.15,
    neighbor_radius: int = 2,
    horizon: int | None = None,
    leaf_evaluation: str = "line",
) -> float | None:
    """Rollout ngẫu nhiên; ``None`` nghĩa là time budget ngắt giữa vòng.

    Guard tối đa bằng số ô còn lại trên bàn. Với ``CaroEnv`` chuẩn, ván phải
    terminal chậm nhất khi bàn đầy. Một implementation ``GameEnv`` khác không
    terminal đúng hạn được đánh giá trung lập thay vì làm vòng lặp vô hạn.
    """

    remaining = max(0, env.config.board_size * env.config.board_size - env.state.move_count)
    for rollout_ply in range(remaining + 1):
        if env.is_terminal():
            result = env.result(root_player)
            if result is None:  # pragma: no cover - vi phạm GameEnv contract
                raise RuntimeError("terminal environment returned no result")
            return float(result)
        if horizon is not None and rollout_ply >= horizon:
            if leaf_evaluation == "pattern":
                return _normalized_pattern_value(env, root_player)
            return normalized_line_value(
                env.state.board,
                root_player,
                env.config.win_length,
            )
        if deadline is not None and time.perf_counter() >= deadline:
            return None
        legal = env.legal_actions()
        if not legal:
            # Defensive handling cho mock không đánh dấu terminal khi hết action.
            return 0.0
        if policy == "epsilon_tactical_local":
            state = env.state
            action = choose_tactical_local_action(
                state.board,
                legal,
                state.current_player,
                env.config,
                neighbor_radius=neighbor_radius,
                epsilon=epsilon,
                rng=rng,
            )
        elif policy == "epsilon_heuristic":
            action = _choose_heuristic_rollout_action(
                env,
                legal,
                epsilon=epsilon,
                neighbor_radius=neighbor_radius,
                rng=rng,
            )
        else:
            action = rng.choice(legal)
        env.step(action)
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
        tactical_precheck: bool = False,
        candidate_policy: str = "legacy_random",
        neighbor_radius: int = 2,
        progressive_widening_c: float | None = None,
        progressive_widening_alpha: float = 0.5,
        rollout_policy: str = "random",
        rollout_epsilon: float = 0.15,
        reuse_simulation_env: bool = False,
        rollout_horizon: int | None = None,
        leaf_evaluation: str = "line",
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
        if not isinstance(tactical_precheck, bool):
            raise ValueError("tactical_precheck must be a bool")
        if candidate_policy not in {
            "legacy_random",
            "tactical_local_seeded",
            "heuristic_seeded",
        }:
            raise ValueError(
                "candidate_policy must be 'legacy_random', "
                "'tactical_local_seeded', or 'heuristic_seeded'"
            )
        if (
            isinstance(neighbor_radius, bool)
            or not isinstance(neighbor_radius, int)
            or neighbor_radius <= 0
        ):
            raise ValueError("neighbor_radius must be a positive integer")
        if progressive_widening_c is not None and (
            isinstance(progressive_widening_c, bool)
            or not isinstance(progressive_widening_c, (int, float))
            or not math.isfinite(float(progressive_widening_c))
            or progressive_widening_c <= 0
        ):
            raise ValueError("progressive_widening_c must be positive and finite or None")
        if (
            isinstance(progressive_widening_alpha, bool)
            or not isinstance(progressive_widening_alpha, (int, float))
            or not math.isfinite(float(progressive_widening_alpha))
            or not 0 < progressive_widening_alpha <= 1
        ):
            raise ValueError("progressive_widening_alpha must be in (0, 1]")
        if rollout_policy not in {
            "random",
            "epsilon_tactical_local",
            "epsilon_heuristic",
        }:
            raise ValueError(
                "rollout_policy must be 'random', 'epsilon_tactical_local', "
                "or 'epsilon_heuristic'"
            )
        if (
            isinstance(rollout_epsilon, bool)
            or not isinstance(rollout_epsilon, (int, float))
            or not math.isfinite(float(rollout_epsilon))
            or not 0 <= rollout_epsilon <= 1
        ):
            raise ValueError("rollout_epsilon must be in [0, 1]")
        if not isinstance(reuse_simulation_env, bool):
            raise ValueError("reuse_simulation_env must be a bool")
        if rollout_horizon is not None and (
            isinstance(rollout_horizon, bool)
            or not isinstance(rollout_horizon, int)
            or rollout_horizon <= 0
        ):
            raise ValueError("rollout_horizon must be a positive integer or None")
        if leaf_evaluation not in {"line", "pattern"}:
            raise ValueError("leaf_evaluation must be 'line' or 'pattern'")

        self._name = name
        self._exploration_weight = float(exploration_weight)
        self._default_simulations = default_simulations
        self._rng = random.Random(seed)
        self._tactical_precheck = tactical_precheck
        self._candidate_policy = candidate_policy
        self._neighbor_radius = neighbor_radius
        self._widening_c = (
            None if progressive_widening_c is None else float(progressive_widening_c)
        )
        self._widening_alpha = float(progressive_widening_alpha)
        self._rollout_policy = rollout_policy
        self._rollout_epsilon = float(rollout_epsilon)
        self._reuse_simulation_env = reuse_simulation_env
        self._rollout_horizon = rollout_horizon
        self._leaf_evaluation = leaf_evaluation
        self.last_search_stats: dict[str, object] = {}

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
        root_state = env.state
        if self._tactical_precheck:
            tactics = tactical_summary(root_state.board, legal, root_player, env.config)
            override: tuple[Action, str, float] | None = None
            if tactics.winning_actions:
                override = (tactics.winning_actions[0], "win", 1.0)
            elif tactics.unique_forced_block is not None:
                override = (tactics.unique_forced_block, "block", 0.0)
            if override is not None:
                action, kind, score = override
                elapsed_ms = (time.perf_counter() - started) * 1000.0
                self.last_search_stats = {
                    "tactical_override": kind,
                    "legal_actions": len(legal),
                    "root_children": 0,
                    "root_max_visits": 0,
                    "root_mean_visits": 0.0,
                    "max_tree_depth": 0,
                    "simulations": 0,
                }
                return AgentDecision(
                    action=action,
                    score=score,
                    nodes=1,
                    simulations=0,
                    elapsed_ms=elapsed_ms,
                )

        ordered = self._candidate_policy != "legacy_random"

        def orderer(
            target_env: GameEnv,
            actions: list[Action],
            local_rng: random.Random,
        ) -> list[Action]:
            if self._candidate_policy == "heuristic_seeded":
                return _rank_heuristic_actions(target_env, actions, local_rng)
            state = target_env.state
            return rank_candidate_actions(
                state.board,
                actions,
                state.current_player,
                target_env.config,
                neighbor_radius=self._neighbor_radius,
                rng=local_rng,
            )

        root_actions = orderer(env, list(legal), rng) if ordered else list(legal)
        root = _MCTSNode(
            parent=None,
            action=None,
            player_to_move=root_player,
            untried_actions=root_actions,
        )
        nodes = 1
        completed_simulations = 0
        max_tree_depth = 0
        simulation_depths: list[int] = []
        timing = {
            "clone": 0.0,
            "selection": 0.0,
            "expansion": 0.0,
            "rollout": 0.0,
        }
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

        shared_env: GameEnv | None = None
        root_move_count = root_state.move_count
        if self._reuse_simulation_env:
            clone_started = time.perf_counter()
            shared_env = env.clone_env()
            timing["clone"] += time.perf_counter() - clone_started

        def rewind_shared() -> None:
            if shared_env is None:
                return
            while shared_env.state.move_count > root_move_count:
                shared_env.undo()

        while completed_simulations < simulation_limit:
            if deadline is not None and time.perf_counter() >= deadline:
                break
            if active_budget.max_nodes is not None and nodes >= active_budget.max_nodes:
                break

            if shared_env is None:
                clone_started = time.perf_counter()
                simulation_env = env.clone_env()
                timing["clone"] += time.perf_counter() - clone_started
            else:
                simulation_env = shared_env
            node = root

            depth = 0
            # Selection continues until this node is allowed to expand under
            # progressive widening, or a terminal/leaf node is reached.
            selection_started = time.perf_counter()
            while not simulation_env.is_terminal():
                allowed = _allowed_children(
                    node,
                    widening_c=self._widening_c,
                    widening_alpha=self._widening_alpha,
                )
                if node.untried_actions and len(node.children) < allowed:
                    break
                if not node.children:
                    break
                node = _select_child(
                    node,
                    root_player=root_player,
                    exploration_weight=self._exploration_weight,
                    rng=rng,
                )
                if node.action is None:  # pragma: no cover - invariant của tree
                    raise RuntimeError("non-root MCTS node has no action")
                simulation_env.step(node.action)
                depth += 1
                max_tree_depth = max(max_tree_depth, depth)
                if deadline is not None and time.perf_counter() >= deadline:
                    break
            timing["selection"] += time.perf_counter() - selection_started

            if deadline is not None and time.perf_counter() >= deadline:
                rewind_shared()
                break

            # Expansion chỉ tạo một child và không vượt max_nodes.
            allowed = _allowed_children(
                node,
                widening_c=self._widening_c,
                widening_alpha=self._widening_alpha,
            )
            if (
                not simulation_env.is_terminal()
                and node.untried_actions
                and len(node.children) < allowed
            ):
                if active_budget.max_nodes is not None and nodes >= active_budget.max_nodes:
                    break
                expansion_started = time.perf_counter()
                node = _expand_ranked(
                    node,
                    simulation_env,
                    rng,
                    ordered=ordered,
                    orderer=orderer if ordered else None,
                )
                nodes += 1
                depth += 1
                max_tree_depth = max(max_tree_depth, depth)
                timing["expansion"] += time.perf_counter() - expansion_started

            rollout_started = time.perf_counter()
            reward = _rollout(
                simulation_env,
                root_player=root_player,
                rng=rng,
                deadline=deadline,
                policy=self._rollout_policy,
                epsilon=self._rollout_epsilon,
                neighbor_radius=self._neighbor_radius,
                horizon=self._rollout_horizon,
                leaf_evaluation=self._leaf_evaluation,
            )
            timing["rollout"] += time.perf_counter() - rollout_started
            if reward is None:
                rewind_shared()
                break
            _backpropagate(node, reward)
            completed_simulations += 1
            simulation_depths.append(depth)
            rewind_shared()

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
        visits = [child.visits for child in root.children]
        self.last_search_stats = {
            "tactical_override": None,
            "legal_actions": len(legal),
            "root_children": len(root.children),
            "root_max_visits": max(visits, default=0),
            "root_mean_visits": sum(visits) / len(visits) if visits else 0.0,
            "max_tree_depth": max_tree_depth,
            "mean_tree_depth": (
                sum(simulation_depths) / len(simulation_depths)
                if simulation_depths
                else 0.0
            ),
            "simulations": completed_simulations,
            "timing_ms": {
                key: value * 1000.0 for key, value in timing.items()
            },
            "root_visits": [
                {
                    "action": child.action,
                    "visits": child.visits,
                    "mean_value": child.mean_value,
                }
                for child in sorted(root.children, key=lambda item: item.action)
            ],
        }
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
            f"default_simulations={self._default_simulations!r}, "
            f"tactical_precheck={self._tactical_precheck!r}, "
            f"candidate_policy={self._candidate_policy!r}, "
            f"progressive_widening_c={self._widening_c!r}, "
            f"progressive_widening_alpha={self._widening_alpha!r}, "
            f"rollout_policy={self._rollout_policy!r}, "
            f"rollout_epsilon={self._rollout_epsilon!r}, "
            f"reuse_simulation_env={self._reuse_simulation_env!r}, "
            f"rollout_horizon={self._rollout_horizon!r}, "
            f"leaf_evaluation={self._leaf_evaluation!r})"
        )
