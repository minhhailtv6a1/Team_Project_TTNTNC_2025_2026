"""Benchmark THAM KHẢO cho clone_env / step / undo (không có ngưỡng cứng, không chạy trong CI).
Chạy (từ thư mục gốc repo):  PYTHONPATH=. python benchmarks/bench_clone_step.py
"""
import platform
import random
import statistics
import time

from core.engine.game_env import CaroEnv

REPEAT = 7


def timeit(fn, number):
    """Trả về (µs/lần trung vị, độ lệch chuẩn) qua REPEAT lượt đo."""
    samples = []
    for _ in range(REPEAT):
        t0 = time.perf_counter()
        for _ in range(number):
            fn()
        samples.append((time.perf_counter() - t0) / number * 1e6)
    return statistics.median(samples), statistics.pstdev(samples)


def env_with_moves(k, seed=0):
    rng = random.Random(seed)
    env = CaroEnv()
    while env.state.move_count < k and not env.is_terminal():
        env.step(rng.choice(env.legal_actions()))
    return env


def main():
    print(f"Python {platform.python_version()} | {platform.machine()} | {platform.system()}")
    print(f"{'phép đo':<34}{'median µs':>12}{'± std':>10}")
    for k in (0, 20, 40, 60):
        env = env_with_moves(k)
        med, sd = timeit(env.clone_env, 2000)
        print(f"{f'clone_env (đã đi {k} nước)':<34}{med:>12.1f}{sd:>10.1f}")

    # step + undo trên env có sẵn 20 nước (cặp step/undo giữ env không đổi)
    env = env_with_moves(20)
    action = env.legal_actions()[0]

    def step_undo():
        env.step(action)
        env.undo()

    med, sd = timeit(step_undo, 5000)
    print(f"{'step + undo (20 nước)':<34}{med:>12.1f}{sd:>10.1f}")

    # step riêng: clone mới mỗi lần để đo chi phí step thuần (đã trừ clone)
    base = env_with_moves(20)
    clones = [base.clone_env() for _ in range(2000)]
    t0 = time.perf_counter()
    for c in clones:
        c.step(action)
    step_us = (time.perf_counter() - t0) / len(clones) * 1e6
    print(f"{'step thuần (20 nước)':<34}{step_us:>12.1f}{'-':>10}")

    undo_us = None
    t0 = time.perf_counter()
    for c in clones:
        c.undo()
    undo_us = (time.perf_counter() - t0) / len(clones) * 1e6
    print(f"{'undo thuần':<34}{undo_us:>12.1f}{'-':>10}")

    med, _ = timeit(lambda: base.state, 5000)
    print(f"{'state (snapshot board)':<34}{med:>12.1f}{'-':>10}")

    # rollout ngẫu nhiên đến hết ván trên clone (kiểu MCTS)
    rng = random.Random(1)

    def rollout():
        sim = base.clone_env()
        while not sim.is_terminal():
            sim.step(rng.choice(sim.legal_actions()))

    med, _ = timeit(rollout, 20)
    print(f"{'rollout random tới hết ván (ms)':<34}{med / 1000:>12.2f}{'-':>10}")


if __name__ == "__main__":
    main()