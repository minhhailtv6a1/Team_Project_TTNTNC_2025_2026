# Kế hoạch chi tiết Tuần 7 và 8 - Thực nghiệm, demo và bàn giao

> **Thời lượng:** 2 tuần, 10 ngày làm việc.  
> **Phạm vi:** `caro-v2`, bàn 11x11, 5 agent: Random, Heuristic, Minimax/Alpha-Beta, MCTS và Neural/Policy.  
> **Mục tiêu:** khóa phiên bản, chạy thực nghiệm cuối, hoàn thiện demo, báo cáo, slide, poster, README và gói nộp.  
> **Nguyên tắc:** mỗi file chỉ có một owner; không sửa agent/model sau khi đã xem kết quả chính thức.

---

## 1. Baseline hiện tại và phần còn thiếu

| Hạng mục | Đã có | Cần hoàn tất trong Tuần 7-8 |
|---|---|---|
| Engine và agent | Engine, Random, Heuristic, Minimax, MCTS, NeuralAgent và test | Freeze phiên bản; chỉ sửa lỗi correctness có bằng chứng |
| Dữ liệu và model | Dataset v5, checkpoint Policy v5, báo cáo train/eval riêng | Khóa checkpoint/checksum, learning curve và failure cases |
| Đánh giá | Có kết quả Policy v5 đấu 3 agent | Round-robin đủ 5 agent, đủ 100 ván/cặp, 2 chế độ, CI và chi phí |
| Ablation | Có benchmark rời; `05_Ablation_Study.ipynb` rỗng | Alpha-Beta ON/OFF và MCTS 100/400/1000 simulations |
| UI | Có lựa chọn Human vs AI, AI vs AI nhưng chưa gọi agent | Kết nối 5 agent, demo ổn định và video |
| Báo cáo | Có khung và phân công chương | Viết bản thảo theo owner, ghép bản cuối, slide và poster |
| Tái lập | Có test, config, scripts train/self-play | Một luồng setup -> test -> evaluate -> demo; README và ZIP checksum |

**Cổng bắt đầu:** hợp nhất xong thay đổi Tuần 5-6, working tree sạch, full test không có assertion failure, ghi lại commit SHA, checkpoint SHA-256, dataset manifest SHA-256, phần cứng, phiên bản thư viện và seed. Chưa đạt cổng thì chưa chạy tournament chính thức.

---

## 2. Phạm vi không làm

- Không làm RL, PUCT, AlphaGo/AlphaZero, 9x9 hoặc luật mới.
- Không xây FastAPI vì Streamlit có thể gọi agent trực tiếp; `api/main.py` tiếp tục để trống.
- Không sinh lại dataset hoặc train lại model chỉ để cải thiện số liệu sau khi xem kết quả W7.
- Không tối ưu lại engine/search ngoài lỗi correctness chặn nghiệm thu.
- Không commit raw log, checkpoint, video, ZIP hoặc artifact lớn; chỉ commit config, script, checksum, bảng/hình nguồn nhỏ và báo cáo.

---

## 3. Phân công không conflict

| Thành viên | Task xuyên suốt | File/thư mục được sửa chính |
|---|---|---|
| **M1 - Trần Hồ Minh Hải** | `W78-M1-01` - Tích hợp UI, bằng chứng model, demo và slide | `ui/app.py`, `ui/human_controller.py`, `tests/test_ui_ai_modes.py`, `docs/report/drafts/hai_ch06_ch07.md`, `docs/report/assets/hai/`, `docs/presentation/`, `docs/demo/` |
| **M2 - Lê Thị Trúc Ly** | `W78-M2-01` - Hai ablation, phân tích chiến thuật, chương thuật toán và poster | `benchmarks/run_ablation_w78.py`, `configs/ablation_w78.json`, `notebooks/05_Ablation_Study.ipynb`, `tests/test_ablation_w78.py`, `docs/report/drafts/ly_ch02_ch04.md`, `docs/report/assets/ly/`, `docs/poster/`, `docs/review/Kiem_tra_ky_thuat_W78.md` |
| **M3 - Trương Văn Thiện** | `W78-M3-01` - Round-robin, thống kê, chương thực nghiệm, README và release | `scripts/run_tournament_w78.py`, `scripts/analyze_results_w78.py`, `configs/tournament_w78.json`, `notebooks/04_Tournament_Eval.ipynb`, `tests/test_tournament_w78.py`, `tests/test_result_analysis_w78.py`, `docs/report/drafts/thien_ch01_ch03_ch05.md`, `docs/report/assets/thien/`, `docs/results/`, `README.md`, `docs/final/`, `docs/release/` |

Quy tắc chống conflict:

1. Mỗi người chỉ sửa các file trong dòng của mình; test mới phải có tên riêng như bảng trên.
2. `core/engine/`, `core/agents/`, `core/ml/`, `core/utils/` và checkpoint được freeze trước W7.
3. M1/M2 viết bản thảo riêng; chỉ M3 ghép vào báo cáo cuối sau khi nhận bản đã khóa.
4. Chỉ M3 sửa `README.md`, tạo release manifest và đóng ZIP.
5. M1 sở hữu slide/video; M2 sở hữu poster; M3 chỉ kiểm tra link và đưa vào gói nộp.
6. Nếu lỗi nằm trong file đã freeze, tạo issue cho đúng owner cũ sửa bằng PR hotfix riêng. Sau hotfix phải tăng version và chạy lại toàn bộ kết quả bị ảnh hưởng.

---

## 4. M1 - Trần Hồ Minh Hải

### W78-M1-01 - UI, bằng chứng PolicyNet, demo và slide

#### Tuần 7

- Kết nối chế độ Human vs AI và AI vs AI với 5 agent qua public `choose_action()`; không copy logic agent vào UI.
- Cho phép chọn bên X/O, cấp AI và checkpoint Neural; khóa bàn khi AI đang suy luận hoặc game terminal.
- Hiển thị thời gian nước đi, nodes/simulations khi agent có trả metric; xử lý lỗi checkpoint bằng thông báo rõ ràng.
- Viết test UI riêng cho đổi mode, nước AI hợp lệ, terminal guard, reset và checkpoint lỗi.
- Từ training history và raw log đã khóa, tạo learning curve, biểu đồ chi phí model và 4 thế cờ: 2 thành công, 2 thất bại.

#### Tuần 8

- Viết trọn Chương 6 và 7 trong `hai_ch06_ch07.md`; không sửa chương của M2/M3.
- Chụp ảnh demo, chuẩn bị slide thuyết trình và quay video ngắn: Human vs AI, AI vs AI, chọn đủ cấp độ.
- Chạy fresh demo smoke theo README do M3 cung cấp; báo lỗi để M3 sửa README, không tự sửa.

#### Definition of Done

- 5 agent đều chọn được action legal trên UI; Neural dùng checkpoint đã huấn luyện.
- Human vs AI và AI vs AI hoàn tất ít nhất một ván, reset được, không mutation/đi hai nước.
- Test UI mới và test UI cũ xanh.
- Learning curve/4 case board sinh từ artifact thật, có run id và nguồn log.
- Slide và video demo không chứa số liệu khác với `results-v1`.

**Nhánh:** `feature/w78-demo-hai`

---

## 5. M2 - Lê Thị Trúc Ly

### W78-M2-01 - Ablation, phân tích chiến thuật và poster

#### Tuần 7

- Khóa `ablation_w78.json` rồi chạy đúng hai phân tích bắt buộc:
  - **A1:** Minimax cùng độ sâu và scenario, Alpha-Beta ON so với OFF; báo action/score, nodes, mean/p95 latency và mức giảm node.
  - **A2:** MCTS cùng rollout policy/seed, lần lượt 100/400/1000 simulations; báo W/D/L, score, mean/p95 latency, simulations và độ nhạy theo seed.
- Dùng tối thiểu 30 paired runs/profile hoặc số lớn hơn nếu pilot cho phép; cùng input/seed giữa các biến thể.
- Chọn từ raw log 2 ván thắng và 2 failure case có board snapshot; giải thích chiến thuật và first-player effect.
- Notebook 05 chỉ đọc config/log và gọi code canonical; không chứa bản sao thuật toán.

#### Tuần 8

- Viết trọn Chương 2 và 4 trong `ly_ch02_ch04.md`; nhận mô tả MCTS/Neural từ M1 và contract/metric từ M3.
- Làm poster tóm tắt bài toán, 5 agent, pipeline, kết quả chính, 2 ablation và hạn chế.
- Review kỹ thuật bản cuối: luật, thuật ngữ, công thức UCT/Alpha-Beta, ngân sách, số liệu và trích dẫn.

#### Definition of Done

- Hai ablation dùng agent frozen và config versioned; không đổi tham số giữa chừng.
- Alpha-Beta ON/OFF so sánh trên cùng state/depth; MCTS chỉ thay simulations.
- Mọi bảng/hình tái sinh được từ raw output, không nhập số thủ công.
- Notebook 05 chạy end-to-end; báo cả kết quả xấu và giới hạn độc lập mẫu.
- Poster khớp hoàn toàn với `results-v1` và báo cáo cuối.

**Nhánh:** `feature/w78-ablation-ly`

---

## 6. M3 - Trương Văn Thiện

### W78-M3-01 - Tournament, thống kê, báo cáo thực nghiệm và release

#### Tuần 7

- Khóa `tournament_w78.json`: commit SHA, 5 agent, checkpoint checksum, hardware, seeds, budgets và hai profile `DEFAULT`/`FAIR`.
- Chạy round-robin đủ 10 cặp, **tối thiểu 100 ván/cặp/profile**, đổi bên X/O 50/50. Seed của hai ván đổi bên phải ghép cặp; không bỏ ván thua.
- `DEFAULT` dùng cấu hình công bố của từng agent. `FAIR` dùng cùng giới hạn thời gian/nước hoặc budget chung đã pilot và khóa trước khi chạy.
- Lưu raw JSONL + manifest + checksum trong `results/w78/` cục bộ; script phải hỗ trợ resume mà không trùng `game_id`.
- Phân tích W/D/L, score, ma trận đối đầu, tách X/O, Wilson 95% CI, mean/p95 move time, nodes, simulations, RAM/VRAM nếu phù hợp, budget violations và seed sensitivity.
- Với cặp deterministic lặp cùng trajectory, ghi rõ CI không đại diện cho 100 quan sát độc lập.
- Khóa `results-v1` sau kiểm tra checksum; sau thời điểm này không được tune agent/model theo kết quả.

#### Tuần 8

- Viết trọn Chương 1, 3 và 5 trong `thien_ch01_ch03_ch05.md`.
- Sau khi M1/M2 bàn giao bản khóa, ghép báo cáo cuối; không viết lại nội dung chuyên môn của họ nếu chưa review.
- Cập nhật README với setup, test, train hoặc tải checkpoint, evaluate và demo.
- Kiểm tra fresh install, full test, link/artifact, đóng gói ZIP đúng tên và tạo SHA-256.
- Gắn tag `results-v1` sau W7 và `v1.0` chỉ khi pre-flight cuối đạt.

#### Definition of Done

- Đủ 5 agent, 10 cặp, >=100 ván/cặp/profile, cân bằng X/O và không thiếu raw log.
- Một lệnh tái sinh được toàn bộ bảng/hình từ raw logs; notebook 04 chỉ gọi script canonical.
- Báo cáo trả lời câu hỏi nghiên cứu bằng số liệu, có hạn chế và failure analysis.
- README chạy được trên checkout sạch; ZIP có code, config, test, checkpoint/đường tải, log, notebook, report, slide và poster.
- Release manifest có commit SHA, checksum và danh sách file; không chứa cache, virtualenv hoặc secret.

**Nhánh:** `feature/w78-eval-release-thien`

---

## 7. Thứ tự thực hiện và merge

```text
Ngày 1: Cả nhóm dọn baseline -> full test -> freeze code/model/config
        |
        +-- M1: UI + model evidence
        +-- M2: ablation + tactical cases
        +-- M3: tournament runner + analysis
        |
Ngày 2-4: pilot nhỏ -> khóa config -> chạy chính thức
        |
Ngày 5: M3 kiểm raw log/checksum -> khóa results-v1
        |
Ngày 6-7: ba người viết đúng draft riêng; M1 làm slide, M2 làm poster
        |
Ngày 8: M3 ghép báo cáo + README; M1 fresh demo; M2 review kỹ thuật
        |
Ngày 9: sửa blocker theo đúng owner, full regression, pre-flight 100 điểm
        |
Ngày 10: M3 đóng ZIP + checksum -> tag v1.0 -> nộp
```

Thứ tự merge đề xuất:

1. M3 merge runner/analyzer/config sau khi test bằng pilot nhỏ.
2. M2 merge ablation code/config/notebook và bản thảo đã khóa.
3. M1 merge UI/test/demo assets và bản thảo đã khóa.
4. M3 rebase một lần, ghép báo cáo/README/release trong PR cuối; M1 và M2 cùng review.

Không merge notebook output hoặc binary lớn nếu không cần thiết. Không resolve conflict bằng cách chọn toàn bộ `ours/theirs` cho config, báo cáo hoặc kết quả.

---

## 8. Cổng kiểm thử và nghiệm thu cuối

```powershell
# Full regression
.\myenv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider

# M1
.\myenv\Scripts\python.exe -m pytest tests/test_ui_app.py tests/test_ui_ai_modes.py -q -p no:cacheprovider

# M2
.\myenv\Scripts\python.exe -m pytest tests/test_ablation_w78.py -q -p no:cacheprovider

# M3
.\myenv\Scripts\python.exe -m pytest `
  tests/test_tournament_runner.py tests/test_tournament_w78.py `
  tests/test_result_analysis_w78.py -q -p no:cacheprovider

git diff --check
```

Checklist cuối:

- [ ] Code/model/config đã freeze trước tournament chính thức.
- [ ] Round-robin đủ 5 agent, hai profile, >=100 ván/cặp/profile, cân bằng X/O.
- [ ] Có raw logs, manifest, checksum, matrix, CI, latency p95, nodes/sims và cost.
- [ ] Có đúng hai ablation: Alpha-Beta ON/OFF và MCTS 100/400/1000.
- [ ] Có learning curve và 4 case board: 2 thành công, 2 thất bại.
- [ ] UI chạy Human vs AI và AI vs AI với 5 agent.
- [ ] Full test xanh; không còn setup error hoặc budget violation chưa giải thích.
- [ ] Báo cáo, slide, poster, video và README dùng cùng số liệu `results-v1`.
- [ ] Báo cáo nêu rõ dữ liệu tự sinh, split, teacher, seed, checkpoint, phần cứng và hạn chế.
- [ ] Fresh install chạy được luồng setup -> test -> evaluate -> demo.
- [ ] ZIP đúng quy ước tên, không chứa file rác/secret, có SHA-256 và tag `v1.0`.

---

## 9. Sản phẩm bàn giao theo người

| Người | Bàn giao bắt buộc |
|---|---|
| **Hải** | UI tích hợp 5 agent, test UI, learning/cost figures, 4 case boards, Chương 6-7, slide, video demo |
| **Ly** | Hai ablation, notebook 05, tactical analysis, Chương 2-4, poster, checklist review kỹ thuật |
| **Thiện** | Round-robin và analyzer, notebook 04, results-v1/checksum, Chương 1-3-5, báo cáo ghép, README, release manifest và ZIP |

Hoàn thành Tuần 7-8 khi toàn bộ checklist đạt và mỗi artifact cuối truy ngược được về config, seed, commit và raw log tương ứng.
