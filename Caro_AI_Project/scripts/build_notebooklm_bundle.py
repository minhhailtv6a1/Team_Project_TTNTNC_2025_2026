"""Build a flat, NotebookLM-compatible source bundle for the Caro AI project."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooklm_upload"


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def write_text(name: str, content: str) -> None:
    (OUTPUT / name).write_text(content.rstrip() + "\n", encoding="utf-8")


def combine_markdown(name: str, title: str, sources: list[str], note: str | None = None) -> None:
    sections = [
        f"# {title}",
        "",
        "> Tài liệu tổng hợp tự động từ các nguồn trong repository. "
        "Mỗi phần ghi rõ đường dẫn nguồn để đối chiếu.",
    ]
    if note:
        sections.extend(["", f"> **Lưu ý trạng thái:** {note}"])
    for source in sources:
        sections.extend(
            [
                "",
                "---",
                "",
                f"## Nguồn: `{source}`",
                "",
                read_text(source),
            ]
        )
    write_text(name, "\n".join(sections))


def combine_code(name: str, title: str, sources: list[str]) -> None:
    sections = [
        f"# {title}",
        "",
        "Các file nguồn được đóng gói thành Markdown vì NotebookLM không nhận trực tiếp file `.py`.",
    ]
    for source in sources:
        language = "json" if source.endswith(".json") else "python"
        sections.extend(
            [
                "",
                "---",
                "",
                f"## `{source}`",
                "",
                f"```{language}",
                read_text(source).rstrip(),
                "```",
            ]
        )
    write_text(name, "\n".join(sections))


def export_notebooks() -> None:
    sources = sorted((ROOT / "notebooks").glob("*.ipynb"))
    sections = [
        "# Notebook thí nghiệm",
        "",
        "Nội dung dưới đây chỉ lấy Markdown và source code của từng cell; output nặng đã được bỏ qua.",
    ]
    for path in sources:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        sections.extend(["", "---", "", f"## `notebooks/{path.name}`"])
        for index, cell in enumerate(notebook.get("cells", []), start=1):
            cell_type = cell.get("cell_type", "unknown")
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            source = source.rstrip()
            if not source:
                continue
            sections.extend(["", f"### Cell {index} — {cell_type}", ""])
            if cell_type == "code":
                sections.extend(["```python", source, "```"])
            else:
                sections.append(source)
    write_text("17_NOTEBOOKS.md", "\n".join(sections))


def export_json_evidence() -> None:
    sources = [
        "results/policy_v5_best_666.json",
        "docs/report/assets/ablation_summary.json",
        "docs/report/assets/tactical_cases.json",
        "models/checkpoints/model-v5-natural-teachers-run2/run_summary.json",
    ]
    combine_code("18_RAW_RESULTS.md", "Kết quả thô dùng làm bằng chứng", sources)


def export_policy_csv() -> None:
    result = json.loads(read_text("results/policy_v5_best_666.json"))
    fields = [
        "opponent",
        "games",
        "wins",
        "draws",
        "losses",
        "win_rate",
        "draw_rate",
        "loss_rate",
        "score_rate",
        "mean_game_plies",
        "neural_mean_move_ms",
        "neural_p95_move_ms",
    ]
    with (OUTPUT / "33_POLICY_V5_RESULTS.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for opponent, metrics in result["opponents"].items():
            writer.writerow({"opponent": opponent, **{key: metrics[key] for key in fields[1:]}})
        combined = result["combined"]
        writer.writerow({"opponent": "combined", **{key: combined[key] for key in fields[1:]}})


def save_learning_curve() -> None:
    path = ROOT / "models/checkpoints/model-v5-natural-teachers-run2/history.csv"
    with path.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    epochs = [int(row["epoch"]) for row in rows]
    train_top1 = [float(row["train_top1"]) * 100 for row in rows]
    val_top1 = [float(row["val_top1"]) * 100 for row in rows]
    train_loss = [float(row["train_loss"]) for row in rows]
    val_loss = [float(row["val_loss"]) for row in rows]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].plot(epochs, train_loss, marker="o", label="Train")
    axes[0].plot(epochs, val_loss, marker="o", label="Validation")
    axes[0].set(title="Policy v5 — Loss", xlabel="Epoch", ylabel="Cross-entropy loss")
    axes[1].plot(epochs, train_top1, marker="o", label="Train")
    axes[1].plot(epochs, val_top1, marker="o", label="Validation")
    axes[1].set(title="Policy v5 — Top-1 accuracy", xlabel="Epoch", ylabel="Accuracy (%)")
    for axis in axes:
        axis.grid(alpha=0.25)
        axis.legend()
    fig.suptitle("Learning curve — model-v5-natural-teachers-run2")
    fig.tight_layout()
    fig.savefig(OUTPUT / "20_LEARNING_CURVE.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_inference_cost() -> None:
    result = json.loads(read_text("results/policy_v5_best_666.json"))
    labels = list(result["opponents"])
    means = [result["opponents"][label]["neural_mean_move_ms"] for label in labels]
    p95s = [result["opponents"][label]["neural_p95_move_ms"] for label in labels]
    x = list(range(len(labels)))

    fig, axis = plt.subplots(figsize=(8.5, 5))
    width = 0.36
    axis.bar([value - width / 2 for value in x], means, width, label="Mean")
    axis.bar([value + width / 2 for value in x], p95s, width, label="P95")
    axis.set_xticks(x, labels)
    axis.set(title="Policy v5 — Neural inference cost", ylabel="Milliseconds / move")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT / "21_MODEL_INFERENCE_COST.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_alpha_beta_chart() -> None:
    with (ROOT / "docs/report/assets/ablation_a1.csv").open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    scenarios = list(dict.fromkeys(row["scenario"] for row in rows))
    off = {row["scenario"]: float(row["nodes_mean"]) for row in rows if row["alpha_beta"] == "False"}
    on = {row["scenario"]: float(row["nodes_mean"]) for row in rows if row["alpha_beta"] == "True"}
    x = list(range(len(scenarios)))

    fig, axis = plt.subplots(figsize=(10, 5.2))
    width = 0.36
    axis.bar([value - width / 2 for value in x], [off[item] for item in scenarios], width, label="Không cắt tỉa")
    axis.bar([value + width / 2 for value in x], [on[item] for item in scenarios], width, label="Alpha-beta")
    axis.set_xticks(x, scenarios, rotation=15, ha="right")
    axis.set(title="Ablation A1 — Số node Minimax", ylabel="Mean nodes (log scale)")
    axis.set_yscale("log")
    axis.grid(axis="y", alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(OUTPUT / "22_ABLATION_ALPHA_BETA.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_mcts_chart() -> None:
    with (ROOT / "docs/report/assets/ablation_a2.csv").open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    simulations = [int(row["simulations"]) for row in rows]
    scores = [float(row["score_rate"]) * 100 for row in rows]
    mean_ms = [float(row["mean_ms"]) for row in rows]

    fig, axis_score = plt.subplots(figsize=(9, 5.2))
    axis_time = axis_score.twinx()
    score_line = axis_score.plot(simulations, scores, color="#1565c0", marker="o", label="Score rate")
    time_line = axis_time.plot(simulations, mean_ms, color="#ef6c00", marker="s", label="Mean time")
    axis_score.set(xlabel="MCTS simulations / move", ylabel="Score rate (%)", title="Ablation A2 — Chất lượng và chi phí MCTS")
    axis_time.set_ylabel("Mean milliseconds / move")
    axis_score.grid(alpha=0.25)
    axis_score.legend(score_line + time_line, [line.get_label() for line in score_line + time_line], loc="upper left")
    fig.tight_layout()
    fig.savefig(OUTPUT / "23_ABLATION_MCTS_SIMULATIONS.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def save_tactical_boards() -> None:
    cases = json.loads(read_text("docs/report/assets/tactical_cases.json"))
    for index, case in enumerate(cases, start=1):
        board = case["board_before"]
        size = len(board)
        action = tuple(case["action"])
        fig, axis = plt.subplots(figsize=(7, 7))
        axis.set_facecolor("#e8bd75")
        for line in range(size):
            axis.axhline(line, color="#5d4037", linewidth=0.7)
            axis.axvline(line, color="#5d4037", linewidth=0.7)
        for row_index, row in enumerate(board):
            for col_index, value in enumerate(row):
                if value == 1:
                    axis.text(col_index, row_index, "X", ha="center", va="center", fontsize=17, weight="bold", color="#0d47a1")
                elif value == -1:
                    axis.text(col_index, row_index, "O", ha="center", va="center", fontsize=17, weight="bold", color="#b71c1c")
        action_row, action_col = action
        axis.scatter(action_col, action_row, s=420, facecolors="none", edgecolors="#ffeb3b", linewidths=3, zorder=5)
        axis.set_xlim(-0.5, size - 0.5)
        axis.set_ylim(size - 0.5, -0.5)
        axis.set_xticks(range(size))
        axis.set_yticks(range(size))
        axis.set_aspect("equal")
        status = "WIN" if case["kind"] == "win" else "FAILURE"
        axis.set_title(f"Tactical case {index} — {status}\nGame {case['game_id']} | chosen action {action}")
        fig.tight_layout()
        fig.savefig(OUTPUT / f"{23 + index:02d}_CASE_{index}_{case['kind'].upper()}.png", dpi=180, bbox_inches="tight")
        plt.close(fig)


def copy_binary_sources() -> None:
    copies = {
        "ui/Caro_AI_Project.png": "28_UI_REFERENCE.png",
        "docs/presentation/Caro_AI_W78_Hai_v2.pptx": "29_CURRENT_SLIDE_REFERENCE.pptx",
        "docs/report/assets/ablation_a1.csv": "30_ABLATION_ALPHA_BETA.csv",
        "docs/report/assets/ablation_a2.csv": "31_ABLATION_MCTS.csv",
        "docs/report/assets/ablation_sensitivity.csv": "32_ABLATION_SENSITIVITY.csv",
        "requirements.txt": "19_REQUIREMENTS.txt",
    }
    for source, destination in copies.items():
        shutil.copy2(ROOT / source, OUTPUT / destination)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest() -> None:
    purpose = {
        "00_UPLOAD_GUIDE.md": "Hướng dẫn chọn nguồn và đưa lên NotebookLM",
        "01_PROJECT_CONTEXT.md": "Bối cảnh, phân công và trạng thái dự án",
        "02_SYSTEM_CONTRACT_CARO_V2.md": "Luật và hợp đồng hệ thống chuẩn hiện hành",
        "03_REPORT_STRUCTURE.md": "Cấu trúc báo cáo và phân công viết",
        "04_WEEKLY_PLAN_W78.md": "Yêu cầu tuần 7-8",
        "05_CHAPTERS_6_7.md": "Bản thảo chương thực nghiệm và kết luận",
        "06_DATASET_AND_TRAINING.md": "Nguồn dữ liệu, MCTS và huấn luyện Policy v5",
        "07_POLICY_V5_EVALUATION.md": "Đánh giá 1.998 ván của Policy v5",
        "08_ABLATION_RESULTS.md": "Kết quả ablation tuần 7-8",
        "09_DEMO_AND_UI_GUIDE.md": "Kịch bản demo cùng trạng thái UI mới nhất",
        "10_SOURCE_ENGINE.md": "Source code bàn cờ, luật và môi trường",
        "11_SOURCE_AGENTS.md": "Source code các AI agent",
        "12_SOURCE_ML_PIPELINE.md": "Source code mô hình và pipeline dữ liệu",
        "13_SOURCE_EXPERIMENTS.md": "Source code giải đấu, phân tích và ablation",
        "14_SOURCE_UI.md": "Source code giao diện Streamlit",
        "15_TESTS_AND_VALIDATION.md": "Các test tiêu biểu làm bằng chứng kiểm chứng",
        "16_CONFIGS.md": "Cấu hình thí nghiệm chính",
        "17_NOTEBOOKS.md": "Markdown và code từ các notebook",
        "18_RAW_RESULTS.md": "JSON kết quả thô ở dạng Markdown",
        "19_REQUIREMENTS.txt": "Thư viện Python cần thiết",
        "20_LEARNING_CURVE.png": "Biểu đồ quá trình huấn luyện",
        "21_MODEL_INFERENCE_COST.png": "Biểu đồ chi phí suy luận",
        "22_ABLATION_ALPHA_BETA.png": "Biểu đồ alpha-beta",
        "23_ABLATION_MCTS_SIMULATIONS.png": "Biểu đồ ngân sách MCTS",
        "24_CASE_1_WIN.png": "Bàn cờ tình huống thắng 1",
        "25_CASE_2_WIN.png": "Bàn cờ tình huống thắng 2",
        "26_CASE_3_FAILURE.png": "Bàn cờ tình huống thất bại 1",
        "27_CASE_4_FAILURE.png": "Bàn cờ tình huống thất bại 2",
        "28_UI_REFERENCE.png": "Ảnh tham chiếu giao diện",
        "29_CURRENT_SLIDE_REFERENCE.pptx": "Slide hiện có để NotebookLM tham chiếu",
        "30_ABLATION_ALPHA_BETA.csv": "Dữ liệu ablation alpha-beta",
        "31_ABLATION_MCTS.csv": "Dữ liệu ablation MCTS",
        "32_ABLATION_SENSITIVITY.csv": "Dữ liệu độ nhạy seed",
        "33_POLICY_V5_RESULTS.csv": "Bảng tóm tắt đánh giá Policy v5",
    }
    with (OUTPUT / "99_MANIFEST.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["file", "extension", "bytes", "sha256", "purpose"])
        writer.writeheader()
        for path in sorted(OUTPUT.iterdir()):
            if path.name == "99_MANIFEST.csv":
                continue
            writer.writerow(
                {
                    "file": path.name,
                    "extension": path.suffix.lower(),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                    "purpose": purpose[path.name],
                }
            )


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"Output already exists: {OUTPUT}. Rename or remove it before rebuilding.")
    OUTPUT.mkdir()

    write_text(
        "00_UPLOAD_GUIDE.md",
        """# Hướng dẫn dùng bộ nguồn với NotebookLM

## Mục tiêu

Thư mục này là bộ nguồn phẳng, đã loại bỏ định dạng NotebookLM không nhận trực tiếp như `.py`, `.json`, `.ipynb` và `.svg`. Nội dung tương ứng đã được chuyển sang Markdown hoặc PNG. Không cần tải file nén lên NotebookLM.

## Cách tải lên

1. Tạo một notebook mới trong NotebookLM.
2. Chọn **Add sources / Upload** rồi chọn toàn bộ file trong thư mục này.
3. Nếu tài khoản bị giới hạn số nguồn, ưu tiên các file `01` đến `09`, `20` đến `29`, `33` và `99`.
4. Dùng `99_MANIFEST.csv` để kiểm tra đủ file và truy nguyên mục đích.

## Thứ tự ưu tiên khi tạo slide

- Bối cảnh và yêu cầu: `01`–`05`.
- Dữ liệu, kết quả và bằng chứng: `06`–`09`, `18`, `20`–`27`, `30`–`33`.
- Kiến trúc và hiện thực: `10`–`17`.
- Slide/UI tham chiếu: `28`–`29`.

## Lưu ý về độ tin cậy

- Hợp đồng chuẩn hiện hành là Caro v2 trong file `02`; không dùng tài liệu contract v1 cũ.
- Báo cáo ablation có cờ `official=False`; khi viết slide phải gọi đúng là kết quả thử nghiệm/khám phá, không nâng thành kết luận chính thức.
- `09_DEMO_AND_UI_GUIDE.md` phản ánh trạng thái UI mới hơn README gốc: các agent đã được nối thật, có đánh dấu đường thắng và AI-vs-AI chạy tuần tự đến hết ván.

Trang định dạng nguồn NotebookLM chính thức: https://support.google.com/gemininotebook/answer/16215270
""",
    )

    combine_markdown(
        "01_PROJECT_CONTEXT.md",
        "Bối cảnh, phân công và trạng thái dự án",
        ["README.md", "PhanCongVaQuyTacLamViec.md", "docs/Phan_cong_thanh_vien.md"],
        note=(
            "README có ghi chú UI chưa nối agent tại thời điểm viết. Trạng thái hiện hành nằm trong "
            "`09_DEMO_AND_UI_GUIDE.md`: UI đã nối agent thật, đánh dấu đường thắng và chế độ AI-vs-AI "
            "tự chạy tuần tự đến hết ván. Khi hai nguồn mâu thuẫn, dùng trạng thái hiện hành này."
        ),
    )
    combine_markdown("02_SYSTEM_CONTRACT_CARO_V2.md", "System contract Caro v2", ["docs/contract/docs_contracts_caro_v2.md"])
    combine_markdown(
        "03_REPORT_STRUCTURE.md",
        "Cấu trúc báo cáo và phân công viết",
        ["docs/Cau_truc_bao_cao_do_an_AI_Caro.md", "docs/Phan_cong_viet_bao_cao.md"],
    )
    combine_markdown("04_WEEKLY_PLAN_W78.md", "Kế hoạch chi tiết tuần 7-8", ["docs/weekly_plan/Ke_hoach_chi_tiet_Tuan_7&8.md"])
    combine_markdown("05_CHAPTERS_6_7.md", "Chương 6 và 7 — thực nghiệm, kết luận", ["docs/report/drafts/hai_ch06_ch07.md"])
    combine_markdown(
        "06_DATASET_AND_TRAINING.md",
        "Dữ liệu, MCTS và quá trình huấn luyện",
        [
            "docs/data/Dataset_v5_Natural_Teachers_Report.md",
            "docs/data/Task56_Hai_Execution_Report.md",
            "docs/data/MCTS_Strength_Improvement_Report.md",
            "docs/data/MCTS_Upgrade_Execution_Report.md",
        ],
    )
    combine_markdown("07_POLICY_V5_EVALUATION.md", "Đánh giá Policy v5", ["docs/data/Policy_v5_Best_666_Evaluation_Report.md"])
    combine_markdown(
        "08_ABLATION_RESULTS.md",
        "Kết quả ablation tuần 7-8",
        ["docs/report/assets/Ket_qua_Ablation_W78.md", "docs/report/assets/Ban_giao_Tuan_7.md"],
    )
    combine_markdown(
        "09_DEMO_AND_UI_GUIDE.md",
        "Hướng dẫn demo và trạng thái UI",
        ["docs/demo/fresh_demo_report.md", "docs/demo/hai_demo_script.md"],
    )
    combine_code(
        "10_SOURCE_ENGINE.md",
        "Source code — engine",
        ["core/engine/board.py", "core/engine/rules.py", "core/engine/game_env.py", "core/engine/interfaces.py"],
    )
    combine_code(
        "11_SOURCE_AGENTS.md",
        "Source code — AI agents",
        [
            "core/agents/random_ai.py",
            "core/agents/heuristic_ai.py",
            "core/agents/minimax_ai.py",
            "core/agents/mcts_ai.py",
            "core/agents/neural_ai.py",
            "core/agents/search_utils.py",
        ],
    )
    combine_code(
        "12_SOURCE_ML_PIPELINE.md",
        "Source code — mô hình và pipeline dữ liệu",
        ["core/ml/architectures.py", "core/ml/data_pipeline.py", "scripts/build_dataset.py", "scripts/train_policy.py"],
    )
    combine_code(
        "13_SOURCE_EXPERIMENTS.md",
        "Source code — giải đấu và thí nghiệm",
        [
            "core/utils/logger.py",
            "core/utils/tournament_runner.py",
            "scripts/run_tournament_w78.py",
            "scripts/analyze_results_w78.py",
            "benchmarks/run_ablation_w78.py",
        ],
    )
    combine_code("14_SOURCE_UI.md", "Source code — giao diện", ["ui/app.py", "ui/human_controller.py", "ui/mock_game_env.py"])
    combine_code(
        "15_TESTS_AND_VALIDATION.md",
        "Tests và bằng chứng kiểm chứng",
        [
            "tests/test_board.py",
            "tests/test_rules.py",
            "tests/test_agents_integration.py",
            "tests/test_ui_ai_modes.py",
            "tests/test_tournament_w78.py",
            "tests/test_ablation_w78.py",
            "tests/test_result_analysis_w78.py",
        ],
    )
    combine_code(
        "16_CONFIGS.md",
        "Cấu hình thí nghiệm chính",
        [
            "configs/tournament_w78.json",
            "configs/ablation_w78.json",
            "configs/policy_train_v5_natural.json",
            "configs/train_w56_v5_natural.json",
            "configs/selfplay_w56_dataset_v2_mcts_strength.json",
            "configs/teacher_w56.json",
        ],
    )
    export_notebooks()
    export_json_evidence()
    copy_binary_sources()
    save_learning_curve()
    save_inference_cost()
    save_alpha_beta_chart()
    save_mcts_chart()
    save_tactical_boards()
    export_policy_csv()
    write_manifest()
    print(f"Created {len(list(OUTPUT.iterdir()))} NotebookLM-compatible files in {OUTPUT}")


if __name__ == "__main__":
    main()
