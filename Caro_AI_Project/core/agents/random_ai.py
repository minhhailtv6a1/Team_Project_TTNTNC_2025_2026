"""RandomAgent: baseline chọn đều trong các legal action, theo contract ``caro-v2``.

Hành vi:
- Chọn đều ngẫu nhiên trong ``env.legal_actions()`` bằng ``random.Random`` cục bộ;
  không bao giờ đụng vào RNG toàn cục của ``random``.
- Seed lấy từ ``budget.seed`` (runner cấp). Cùng state, budget và seed thì cùng
  action vì ``legal_actions()`` luôn có thứ tự row-major xác định.
- Không mutation ``env``: chỉ đọc ``is_terminal()`` và ``legal_actions()``.
- Terminal hoặc không còn legal action thì ``RuntimeError``.
- ``nodes=0`` và ``simulations=0``; ``score=None`` vì agent không đánh giá thế cờ.
"""

from __future__ import annotations

import random
import time

from core.engine.interfaces import AgentDecision, GameEnv, SearchBudget

__all__ = ["RandomAgent"]


class RandomAgent:
    """Agent ngẫu nhiên có seed, thỏa ``Agent`` protocol.

    Thứ tự chọn nguồn seed cho mỗi lần ``choose_action``:

    1. ``budget.seed`` nếu có (cách runner dùng, tái lập tuyệt đối theo state).
    2. Ngược lại dùng RNG riêng của instance, tạo từ ``seed`` ở constructor.
       RNG này tiến lên theo từng lần gọi, nên chuỗi nước đi tái lập được khi
       gọi theo cùng thứ tự. Nếu ``seed=None`` thì lấy entropy của hệ điều hành.
    """

    def __init__(self, name: str = "random", seed: int | None = None) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string")
        self._name = name
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

        if budget is not None and budget.seed is not None:
            rng = random.Random(budget.seed)
        else:
            rng = self._rng
        action = rng.choice(legal)

        return AgentDecision(
            action=action,
            score=None,
            nodes=0,
            simulations=0,
            elapsed_ms=(time.perf_counter() - started) * 1000.0,
        )

    def __repr__(self) -> str:
        return f"RandomAgent(name={self._name!r})"