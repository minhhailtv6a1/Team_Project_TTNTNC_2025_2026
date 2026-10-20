import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engine.game_env import CaroEnv
from core.engine.interfaces import GameConfig, Player


def run_demo():
    print("==================================================")
    print("   DEMO ENGINE CARO-V1: RESET -> STEP -> RENDER   ")
    print("==================================================\n")

    # 1. Khởi tạo môi trường ván đấu (Khởi tạo GameConfig)
    config = GameConfig(board_size=11, win_length=5)
    env = CaroEnv(config=config)

    # 2. Gọi RESET - Đưa bàn cờ về trạng thái ban đầu
    state = env.reset()
    print("[1] Bàn cờ sau khi RESET (Trống hoàn toàn, lượt Player X):")
    env.render()
    print("-" * 50)

    # 3. Gọi STEP 1 - Player X đánh vào vị trí giữa bàn (5, 5)
    action_x = (5, 5)
    result_1 = env.step(action_x)
    print(f"\n[2] Nước đi 1: Player X đánh vào {action_x}")
    env.render()
    print(f"-> Done: {result_1.done} | Winner: {result_1.winner} | Reward: {result_1.reward}")
    print("-" * 50)

    # 4. Gọi STEP 2 - Player O đánh vào ô bên cạnh (5, 6)
    action_o = (5, 6)
    result_2 = env.step(action_o)
    print(f"\n[3] Nước đi 2: Player O đánh vào {action_o}")
    env.render()
    print(f"-> Done: {result_2.done} | Winner: {result_2.winner} | Reward: {result_2.reward}")
    print("-" * 50)


if __name__ == "__main__":
    run_demo()