from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmarks.policy_acceptance import (
    FIXTURES, build_env, evaluate, load_cases, probability_summary, smoke_matches,
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class CheckpointProbabilityReader:
    """Inspect a separate eval-mode model using the canonical encoder and mask.

    Public checkpoint metadata connects the diagnostic model to NeuralAgent;
    no private fields of the production adapter are accessed or modified.
    """

    def __init__(self, agent):
        import torch
        from core.ml.architectures import PolicyNet

        self.path = agent.checkpoint_path.resolve()
        payload = torch.load(self.path, map_location="cpu", weights_only=False)
        self.metadata = {key: payload.get(key) for key in (
            "checkpoint_schema", "contract_version", "run_id", "dataset_version",
            "dataset_manifest_sha256", "model_config", "training_seed",
            "epoch", "best_epoch", "best_val_loss", "selection_metric",
        )}
        if (payload["dataset_version"] != agent.dataset_version
                or payload["dataset_manifest_sha256"].lower() != agent.dataset_manifest_sha256
                or payload["model_config"] != agent.model_config.to_dict()):
            raise ValueError("Diagnostic checkpoint does not match the agent")
        self.model = PolicyNet(agent.model_config)
        self.model.load_state_dict(payload["model_state_dict"], strict=True)
        self.model.eval()

    def __call__(self, agent, env):
        import numpy as np
        import torch
        from core.ml.architectures import mask_policy_logits
        from core.ml.data_pipeline import encode_policy_state

        if agent.checkpoint_path.resolve() != self.path:
            raise ValueError("Probability reader belongs to another checkpoint")
        if env.is_terminal():
            raise RuntimeError("Terminal states have no policy distribution")
        x, mask = encode_policy_state(env.state, env.legal_actions(), env.config.board_size)
        with torch.inference_mode():
            logits = self.model(torch.from_numpy(np.ascontiguousarray(x)).unsqueeze(0))
            masked = mask_policy_logits(logits, torch.from_numpy(mask).unsqueeze(0))
            values = torch.softmax(masked, dim=1)[0].tolist()
        return values


def audit_fixture_overlap(agent, dataset_dir=None):
    """Check encoded states only; never use held-out labels to tune fixtures."""
    if dataset_dir is None:
        return {"status": "not_audited_dataset_unavailable", "pass": None,
                "reason": "Matching checkpoint val/test tensors were not supplied. Hand-authored provenance alone does not prove disjointness."}
    import numpy as np
    from core.ml.data_pipeline import encode_policy_state, load_dataset_split

    directory = Path(dataset_dir)
    manifest_path = directory / "dataset_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("dataset_version") != agent.dataset_version
            or sha256(manifest_path) != agent.dataset_manifest_sha256):
        raise ValueError("Overlap audit requires the exact checkpoint dataset manifest")
    fixtures = {}
    for case in load_cases():
        if case["kind"] != "terminal":
            env = build_env(case)
            x, _ = encode_policy_state(env.state, env.legal_actions(), env.config.board_size)
            fixtures[case["id"]] = np.ascontiguousarray(x).tobytes()
    overlaps = {}
    split_samples = {}
    for split in ("val", "test"):
        arrays = load_dataset_split(directory, split, verify_checksum=True)
        split_samples[split] = len(arrays["x"])
        keys = {np.ascontiguousarray(x).tobytes() for x in arrays["x"]}
        overlaps[split] = [name for name, key in fixtures.items() if key in keys]
    return {"status": "audited_exact_encoded_states", "pass": not any(overlaps.values()),
            "overlaps": overlaps, "dataset_manifest_sha256": sha256(manifest_path),
            "checked_fixture_cases": len(fixtures), "split_samples": split_samples,
            "scope": "Exact state overlap only; labels and held-out quality metrics were not used."}


def smoke_failure_examples(agent, reader, smoke):
    """Capture the final candidate decision in each lost smoke game for M1."""
    from core.engine.game_env import CaroEnv

    examples = []
    for pair in smoke["pairs"]:
        for record in pair["records"]:
            # The generic smoke runner labels this participant "candidate".
            if record["x_agent"] == "candidate":
                candidate_side = 1
            elif record["o_agent"] == "candidate":
                candidate_side = -1
            else:
                raise ValueError("Smoke record has no candidate participant")
            if record["winner"] is None or record["winner"] == candidate_side:
                continue
            env = CaroEnv()
            last = None
            history = []
            for move in record["moves"]:
                if move["player"] == candidate_side:
                    values = reader(agent, env)
                    last = {"opponent": pair["opponent"], "game_id": record["game_id"],
                            "candidate_side": candidate_side, "history_before": list(history),
                            "action": move["action"], "top5": probability_summary(values, env),
                            "legal_probabilities": values,
                            "note": "Final candidate move in a lost smoke game; a diagnostic example, not a strength estimate."}
                env.step(tuple(move["action"]))
                history.append(move["action"])
            if last is not None:
                last["opponent_winning_reply"] = record["moves"][-1]["action"]
                examples.append(last)
    return examples


def evaluate_checkpoint(checkpoint, *, games=4, dataset_dir=None, expected=None):
    import torch
    from core.agents.neural_ai import NeuralAgent

    path = Path(checkpoint)
    digest = sha256(path)
    expected = expected or {}
    if expected.get("checkpoint_sha256") and digest != expected["checkpoint_sha256"]:
        raise ValueError("Checkpoint SHA-256 differs from the frozen acceptance config")
    if expected.get("fixture_sha256") and sha256(FIXTURES) != expected["fixture_sha256"]:
        raise ValueError("Tactical fixtures differ from the frozen acceptance config")
    agent = NeuralAgent(path, name="policy-w6-ly", device="cpu",
                        expected_dataset_version=expected.get("dataset_version"),
                        expected_dataset_manifest_sha256=expected.get("dataset_manifest_sha256"))
    reader = CheckpointProbabilityReader(agent)
    report = evaluate(agent, reader)
    report["checkpoint_load_status"] = "verified_by_NeuralAgent_strict_state_dict_load"
    report["checkpoint"] = {"path": path.as_posix(), "sha256": digest, **reader.metadata}
    report["runtime"] = {"python": platform.python_version(), "torch": torch.__version__,
                         "device": "cpu", "torch_threads": torch.get_num_threads()}
    report["seed"] = 11
    for result in report["cases"]:
        if result["kind"] == "terminal" or not result["contract_pass"]:
            continue
        case = next(c for c in load_cases() if c["id"] == result["case_id"])
        env = build_env(case)
        values = reader(agent, env)
        result["legal_probabilities"] = values
        # The independent probe must agree with the actual production adapter.
        decision = agent.choose_action(env)
        if decision.action != tuple(result["top5"][0]["action"]) or abs(decision.score - max(values)) > 1e-6:
            result["contract_errors"].append("Diagnostic probabilities disagree with NeuralAgent")
            result["contract_pass"] = False
    report["contract_pass"] = all(c["contract_pass"] for c in report["cases"])
    tactical = [c for c in report["cases"] if c["kind"] in ("win", "block")]
    report["quality_summary"] = {"tactical_cases": len(tactical),
        "action_hits": sum(c.get("quality_action_hit") is True for c in tactical),
        "topk_hits": {str(k): sum(c.get("quality_topk_hits", {}).get(str(k)) is True for c in tactical) for k in (1, 3, 5)},
        "failed_cases": [c["case_id"] for c in tactical if c.get("quality_action_hit") is not True]}
    report["fixture_independence"] = audit_fixture_overlap(agent, dataset_dir)
    report["smoke"] = smoke_matches(agent, games=games)
    report["smoke_failure_examples"] = smoke_failure_examples(agent, reader, report["smoke"])
    if sha256(path) != digest or sha256(FIXTURES) != report["fixture_sha256"]:
        raise RuntimeError("Checkpoint or tactical fixtures changed during evaluation")
    report["contract_ready_for_w7"] = report["contract_pass"] and report["smoke"]["pass"]
    report["full_w6_acceptance"] = report["contract_ready_for_w7"] and report["fixture_independence"]["pass"] is True
    return report


def markdown_report(report):
    """Render measured results without treating advisory quality as a gate."""
    checkpoint = report["checkpoint"]
    quality = report["quality_summary"]
    passed = sum(case["contract_pass"] for case in report["cases"])
    path = Path(checkpoint["path"])
    display_path = path.relative_to(ROOT).as_posix() if path.is_absolute() and path.is_relative_to(ROOT) else path.as_posix()
    lines = [
        "# Nghiệm thu PolicyAgent tuần 6 — Ly", "",
        f"Checkpoint: `{display_path}`; dataset `{checkpoint['dataset_version']}`; best epoch {checkpoint['best_epoch']}.", "",
        "## Kết quả chính", "",
        f"- Contract: **{passed}/{len(report['cases'])} trạng thái đạt** (opening X/O, midgame, thắng/chặn, gần đầy bàn, terminal thắng/hòa).",
        "- Kiểm tra bắt buộc: nạp state dict nghiêm ngặt, action legal và deterministic, không sửa environment, terminal guard trả RuntimeError.",
        "- Xác suất được đọc bằng model chẩn đoán riêng, dùng encoder/mask chuẩn; top-1 và score khớp NeuralAgent. Ô bất hợp lệ có xác suất 0; tổng xác suất bằng 1 trong sai số 1e-6.",
        f"- Chất lượng tham khảo: action đúng **{quality['action_hits']}/{quality['tactical_cases']}**; expected xuất hiện trong top-1/top-3/top-5 lần lượt **{quality['topk_hits']['1']}/{quality['topk_hits']['3']}/{quality['topk_hits']['5']}** trên {quality['tactical_cases']} thế.",
        "- Không thay trọng số, fixture hoặc expected actions sau khi xem kết quả; không huấn luyện lại hay chọn model bằng kết quả nghiệm thu.", "",
        "## Các thế chiến thuật", "",
        "Tọa độ `(hàng, cột)` bắt đầu từ 0. Top-5 ghi xác suất sau legal mask.", "",
        "| Trạng thái | Expected | Action | Top-5: action (xác suất) |",
        "|---|---|---|---|",
    ]
    for case in report["cases"]:
        if case["kind"] not in ("win", "block"):
            continue
        expected = ", ".join(str(tuple(a)) for a in case["expected_actions"])
        top = "; ".join(f"{tuple(row['action'])} ({row['probability']:.2%})" for row in case["top5"] or [])
        lines.append(f"| {case['case_id']} | {expected} | {tuple(case['action']) if 'action' in case else 'lỗi'} | {top} |")
    lines.extend(["", "## Smoke match qua runner", "",
                  "Mỗi cặp 4 ván nếu dùng cấu hình mặc định; đổi vai theo cùng seed gốc 11. W/D/L tính theo PolicyAgent.", "",
                  "| Đối thủ | Số ván | Thắng | Hòa | Thua | Record và replay |", "|---|---:|---:|---:|---:|---|"])
    for pair in report["smoke"]["pairs"]:
        wins = draws = losses = 0
        for record in pair["records"]:
            side = 1 if record["x_agent"] == "candidate" else -1
            if record["winner"] is None:
                draws += 1
            elif record["winner"] == side:
                wins += 1
            else:
                losses += 1
        lines.append(f"| {pair['opponent']} | {len(pair['records'])} | {wins} | {draws} | {losses} | {'Đạt' if pair['pass'] else 'Lỗi'} |")
    lines.extend(["", "Các ván smoke chỉ xác nhận pipeline, không dùng để kết luận sức mạnh hoặc thay giải đấu tuần 7.", "",
                  "## Lỗi và bàn giao", "",
                  f"- Tactical miss: {', '.join(quality['failed_cases']) or 'không ghi nhận trên bộ fixture này'}.",
                  f"- Ván smoke thua cần phân tích: {len(report['smoke_failure_examples'])}. Nếu có, JSON lưu lịch sử trước nước đi cuối của candidate, top-5 và toàn bộ legal probabilities.",
                  "- Kết quả đầy đủ: `results/policy_acceptance_w6_ly.json`, gồm 16 case, phân phối 121 ô ở mỗi state chưa terminal và biên bản các ván smoke.", "",
                  "## Điều kiện chuyển tuần 7", "",
                  f"- Đủ contract để tích hợp runner: **{'Đạt' if report['contract_ready_for_w7'] else 'Chưa đạt'}**."])
    audit = report["fixture_independence"]
    if audit["pass"] is None:
        lines.append("- Đối chiếu trùng state với val/test: **chưa xác nhận**. Fixture được viết tay và giữ nguyên từ trước lần đánh giá; hiện máy chỉ có dataset v2, còn checkpoint dùng v5. Không thể dùng v2 để chứng minh không trùng v5.")
    else:
        lines.append(f"- Đối chiếu exact state với val/test: **{'Không trùng' if audit['pass'] else 'Có trùng'}**. Đã kiểm tra {audit['checked_fixture_cases']} fixture chưa terminal với {audit['split_samples']['val']} state validation và {audit['split_samples']['test']} state test; manifest và checksum tensor khớp bản v5 của checkpoint.")
    lines.extend([
        f"- Nghiệm thu đầy đủ tuần 6: **{'Đạt' if report['full_w6_acceptance'] else 'Chưa chốt (xem các điều kiện ở trên)'}**. Đây là xác nhận riêng phần Ly; không tự đóng checklist hoặc gắn tag model của cả nhóm.", "",
        "## Định danh bản đánh giá", "",
        f"- Checkpoint SHA-256: `{checkpoint['sha256']}`.",
        f"- Dataset manifest SHA-256: `{checkpoint['dataset_manifest_sha256']}`.",
        f"- Fixture SHA-256: `{report['fixture_sha256']}`.",
        f"- Môi trường: Python {report['runtime']['python']}, PyTorch {report['runtime']['torch']}, CPU, {report['runtime']['torch_threads']} thread.",
    ])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/policy_acceptance_neural_w6.json")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--dataset", type=Path, help="Exact checkpoint dataset, for val/test state-overlap audit")
    parser.add_argument("--games", type=int, choices=(2, 4), default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "results/policy_acceptance_w6_ly.json")
    parser.add_argument("--report", type=Path, default=ROOT / "docs/data/Policy_W6_Ly_Acceptance_Report.md")
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text(encoding="utf-8"))
    checkpoint = args.checkpoint or ROOT / config["checkpoint"]
    dataset = args.dataset
    if dataset is None and config.get("dataset"):
        dataset = ROOT / config["dataset"]
    import torch
    torch.set_num_threads(1)
    report = evaluate_checkpoint(checkpoint, games=args.games, dataset_dir=dataset, expected=config)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "contract_pass", "quality_summary", "fixture_independence", "contract_ready_for_w7", "full_w6_acceptance")}, ensure_ascii=False, indent=2))
    print(f"Full records and legal probabilities: {args.output}")
    return 0 if report["contract_ready_for_w7"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
