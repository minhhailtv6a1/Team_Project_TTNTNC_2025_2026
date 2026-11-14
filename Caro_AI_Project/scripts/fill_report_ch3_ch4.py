# -*- coding: utf-8 -*-
"""
Script điền đầy đủ các phần còn thiếu của Chương 3 và Chương 4
trực tiếp vào file báo cáo `Internship_Report - Copy.docx`.

Các mục được hoàn thiện:
- Cuối Mục 3.3.2: Phân hệ Học máy và Chuỗi xử lý dữ liệu (+ Bảng thành phần ML pipeline)
- Mục 3.4 (3.4.1 -> 3.4.5): Cài đặt engine và luật (+ Bảng độ phức tạp & độ trễ thực nghiệm)
- Mục 3.5 (3.5.1 -> 3.5.5): Các tác tử tìm kiếm (+ Bảng SearchBudget & Bảng trọng số mẫu hình Heuristic)
- Mục 3.6.2 & 3.6.3: Kiến trúc mạng PolicyNet, quy trình huấn luyện, tiến hóa dữ liệu v1->v2->v5 và suy luận NeuralAgent (+ Bảng kiến trúc mạng & Bảng cấu hình dữ liệu/huấn luyện)
- Mục 3.8: Chiến lược kiểm thử đa tầng (+ Bảng tổng hợp các nhóm kiểm thử tự động)
- Mục 4.3 (4.3.1 -> 4.3.4): Kết quả Minimax/Alpha-Beta (+ Bảng độ sâu, Bảng Ablation A1 Alpha-Beta, Hình 22_ABLATION_ALPHA_BETA.png, Bảng Ablation Move Ordering)
- Mục 4.4 (4.4.1 -> 4.4.3): Kết quả MCTS (+ Bảng Ablation A2 Simulations, Hình 23_ABLATION_MCTS_SIMULATIONS.png, Bảng độ nhạy theo seed)
- Mục 4.5 (4.5.1 -> 4.5.3): Kết quả tác tử học được (+ Bảng so sánh Dataset/Model v2 vs v5, Bảng lịch sử huấn luyện 10 epoch, Hình 20_LEARNING_CURVE.png, Bảng đối đầu 1.998 ván, Hình 21_MODEL_INFERENCE_COST.png)
"""

from __future__ import annotations

import os
from pathlib import Path
import docx
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


ROOT_DIR = Path(__file__).resolve().parent.parent
DOCX_PATH = ROOT_DIR / "Internship_Report - Copy.docx"
BACKUP_PATH = ROOT_DIR / "Internship_Report - Copy copy.docx"
IMG_DIR = ROOT_DIR / "notebooklm_upload"


class SectionBuilder:
    """Helper chèn tuần tự các đoạn văn, tiêu đề phụ, bảng biểu và hình ảnh ngay sau một đoạn neo (anchor)."""

    def __init__(self, doc: docx.Document, anchor_paragraph: docx.text.paragraph.Paragraph):
        self.doc = doc
        self.cursor = anchor_paragraph._p

    def _insert_element(self, element) -> None:
        self.cursor.addnext(element)
        self.cursor = element

    def add_paragraph(
        self,
        text: str = "",
        style: str = "Normal",
        align: WD_ALIGN_PARAGRAPH = WD_ALIGN_PARAGRAPH.JUSTIFY,
        bold_prefix: str | None = None,
    ) -> docx.text.paragraph.Paragraph:
        p = self.doc.add_paragraph(style=style)
        if align is not None:
            p.alignment = align
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.bold = True
            if text:
                p.add_run(text)
        elif text:
            p.add_run(text)
        self._insert_element(p._p)
        return p

    def add_subheading(self, text: str, level: int = 3) -> docx.text.paragraph.Paragraph:
        style_name = f"Heading {level}"
        p = self.doc.add_paragraph(style=style_name)
        p.add_run(text)
        self._insert_element(p._p)
        return p

    def add_bullet(self, bold_prefix: str, text: str) -> docx.text.paragraph.Paragraph:
        p = self.doc.add_paragraph(style="Normal")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r1 = p.add_run(f"• {bold_prefix}: ")
        r1.bold = True
        p.add_run(text)
        self._insert_element(p._p)
        return p

    def add_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        caption_label: str,
        caption_text: str,
        col_alignments: list[WD_ALIGN_PARAGRAPH] | None = None,
    ) -> None:
        tbl = self.doc.add_table(rows=len(rows) + 1, cols=len(headers))
        tbl.style = "Normal Table"
        tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Thiết lập độ rộng bảng 9000 dxa và khung viền đen đơn sz=8 giống hệt các bảng hiện có
        tblPr = tbl._tbl.tblPr
        tblW = tblPr.find(qn("w:tblW"))
        if tblW is None:
            tblW = OxmlElement("w:tblW")
            tblPr.append(tblW)
        tblW.set(qn("w:w"), "9000")
        tblW.set(qn("w:type"), "dxa")

        borders_xml = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            '<w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            '<w:left w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            '<w:right w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            '<w:insideH w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            '<w:insideV w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
            "</w:tblBorders>"
        )
        old_borders = tblPr.find(qn("w:tblBorders"))
        if old_borders is not None:
            tblPr.remove(old_borders)
        tblPr.append(borders_xml)

        # Hàng tiêu đề
        hdr_cells = tbl.rows[0].cells
        for j, h_text in enumerate(headers):
            cell = hdr_cells[j]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.style = "Normal"
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(h_text)
            run.bold = True

        # Các hàng dữ liệu
        for i, row_data in enumerate(rows):
            row_cells = tbl.rows[i + 1].cells
            for j, val in enumerate(row_data):
                cell = row_cells[j]
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                p = cell.paragraphs[0]
                p.style = "Normal"
                if col_alignments and j < len(col_alignments):
                    p.alignment = col_alignments[j]
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j == 0 else WD_ALIGN_PARAGRAPH.CENTER
                p.add_run(str(val))

        self._insert_element(tbl._tbl)

        # Chú thích bảng nằm ngay dưới bảng, căn giữa theo đúng chuẩn file hiện tại
        cap_p = self.doc.add_paragraph(style="Normal")
        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if caption_label:
            r_lbl = cap_p.add_run(caption_label)
            r_lbl.bold = True
            cap_p.add_run(f" {caption_text}")
        else:
            cap_p.add_run(caption_text)
        self._insert_element(cap_p._p)

    def add_figure(
        self,
        image_path: Path,
        caption_label: str,
        caption_text: str,
        width_cm: float = 16.0,
    ) -> None:
        if not image_path.exists():
            raise FileNotFoundError(f"Không tìm thấy hình ảnh: {image_path}")
        img_p = self.doc.add_paragraph(style="Normal")
        img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = img_p.add_run()
        run.add_picture(str(image_path), width=Cm(width_cm))
        self._insert_element(img_p._p)

        cap_p = self.doc.add_paragraph(style="Normal")
        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r_lbl = cap_p.add_run(caption_label)
        r_lbl.bold = True
        r_lbl.italic = True
        r_txt = cap_p.add_run(f" {caption_text}")
        r_txt.italic = True
        self._insert_element(cap_p._p)


def find_paragraph(doc: docx.Document, prefix: str, style_prefix: str | None = None) -> docx.text.paragraph.Paragraph:
    norm_prefix = " ".join(prefix.split())
    for p in doc.paragraphs:
        if style_prefix and not p.style.name.startswith(style_prefix):
            continue
        p_text = " ".join(p.text.split())
        if p_text.startswith(norm_prefix):
            return p
    raise ValueError(f"Không tìm thấy đoạn văn bắt đầu bằng: {prefix!r} (style={style_prefix})")


def fill_section_3_3_2_ml_subsystem(doc: docx.Document) -> None:
    anchor = find_paragraph(doc, "Phân hệ Học máy và Chuỗi xử lý dữ liệu:")
    # Bổ sung nội dung vào chính đoạn 519 đang bỏ dở
    anchor.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    anchor.add_run(
        "Đảm nhiệm toàn bộ quy trình học có giám sát (Supervised Policy Learning) từ tự đối kháng (self-play) "
        "đến đóng gói mô hình suy luận, đảm bảo tính tái lập và chống rò rỉ dữ liệu giữa các tập huấn luyện, "
        "kiểm định và kiểm thử."
    )

    b = SectionBuilder(doc, anchor)
    b.add_table(
        headers=["Thành phần / Tệp mã nguồn", "Vai trò kiến trúc", "Đầu vào và đầu ra chính"],
        rows=[
            [
                "scripts/generate_selfplay.py",
                "Sinh dữ liệu ván chơi tự đối kháng từ các tác tử giáo viên thông qua TournamentRunner.",
                "Đầu vào: cấu hình cặp đấu, seed gốc. Đầu ra: tệp raw_games.jsonl và selfplay_manifest.json.",
            ],
            [
                "core/ml/data_pipeline.py",
                "Kiểm định replay 100% ván chơi, mã hóa tensor 3 kênh, chia train/val/test theo ván, khử trùng lặp SHA-256 và quỹ đạo đối xứng D4.",
                "Đầu vào: raw_games.jsonl. Đầu ra: train.npz, val.npz, test.npz, split_game_ids.json, dataset_manifest.json.",
            ],
            [
                "scripts/build_dataset.py",
                "Giao diện dòng lệnh điều phối quy trình xây dựng bộ dữ liệu chuẩn hóa theo cấu hình JSON.",
                "Đầu vào: configs/dataset_*.json. Đầu ra: thư mục dữ liệu đã đóng gói kèm mã kiểm tra toàn vẹn.",
            ],
            [
                "core/ml/architectures.py",
                "Định nghĩa mạng PolicyNet (ResNet 4 khối dư, 768.537 tham số), hàm che mặt nạ hợp lệ mask_policy_logits và hàm mất mát masked_policy_loss.",
                "Đầu vào: tensor trạng thái [N, 3, 11, 11] và legal_mask [N, 121]. Đầu ra: vector logits 121 chiều.",
            ],
            [
                "scripts/train_policy.py",
                "Huấn luyện mô hình với AdamW, dừng sớm theo val_loss, ghi nhận lịch sử huấn luyện và lưu trữ nguyên tử checkpoint.",
                "Đầu vào: dataset_dir, cấu hình huấn luyện. Đầu ra: best.pt, last.pt, history.csv, run_summary.json.",
            ],
            [
                "core/agents/neural_ai.py",
                "Tác tử suy luận NeuralAgent đóng gói PolicyNet dưới giao diện Agent thống nhất, kiểm tra chặt chẽ schema và mã băm dữ liệu.",
                "Đầu vào: CaroEnv, SearchBudget, best.pt. Đầu ra: quyết định AgentDecision hợp lệ.",
            ],
        ],
        caption_label="",
        caption_text="Bảng mô tả các thành phần thuộc Phân hệ Học máy và Chuỗi xử lý dữ liệu",
        col_alignments=[WD_ALIGN_PARAGRAPH.LEFT, WD_ALIGN_PARAGRAPH.JUSTIFY, WD_ALIGN_PARAGRAPH.JUSTIFY],
    )


def fill_section_3_4_engine(doc: docx.Document) -> None:
    p_34 = find_paragraph(doc, "3.4. Cài đặt engine và luật", "Heading 2")
    b_34 = SectionBuilder(doc, p_34)
    b_34.add_paragraph(
        "Phân hệ Engine đóng vai trò là nguồn chân lý duy nhất (Single Source of Truth) cho toàn bộ đồ án. "
        "Mọi thành phần từ tác tử tìm kiếm (Minimax, MCTS), bộ sinh dữ liệu self-play, hệ thống giải đấu "
        "cho đến giao diện người dùng Streamlit đều tương tác với trò chơi thông qua hợp đồng kỹ thuật caro-v2 "
        "mà không tự cài đặt lại luật thắng thua hay thao tác trực tiếp lên cấu trúc bộ nhớ nội bộ."
    )

    # 3.4.1
    p_341 = find_paragraph(doc, "3.4.1. Board và dữ liệu bàn cờ", "Heading 3")
    b = SectionBuilder(doc, p_341)
    b.add_paragraph(
        "Trong mã nguồn, dữ liệu bàn cờ được tổ chức theo hai lớp bổ trợ nhau nhằm vừa đáp ứng tính cô lập của "
        "cấu trúc dữ liệu mảng, vừa tối ưu hóa tốc độ sao chép và hoàn tác trong cây tìm kiếm. Lớp thứ nhất là "
        "module core/engine/board.py định nghĩa lớp Board quản lý lưới hai chiều kích thước cố định 11 × 11 trên "
        "kiểu số nguyên có dấu 8-bit (np.int8). Mỗi ô trên bàn cờ chỉ nhận một trong ba giá trị thuộc kiểu liệt kê "
        "Player (kế thừa từ IntEnum tại core/engine/types.py): Player.EMPTY = 0 (ô trống), Player.X = 1 (quân X, đi trước) "
        "và Player.O = -1 (quân O, đi sau). Cách biểu diễn đối xứng qua số 0 giúp phép chuyển lượt giữa hai người chơi "
        "được thực hiện đơn giản bằng phép đổi dấu số học (-player) hoặc phương thức Player.other."
    )
    b.add_paragraph(
        "Lớp Board cung cấp hai phương thức ánh xạ song ánh giữa tọa độ phẳng (action index) và tọa độ hai chiều "
        "(row, col) theo thứ tự ưu tiên hàng (row-major order): coord_to_action(row, col) = row × 11 + col và "
        "action_to_coord(action) = divmod(action, 11). Bên cạnh đó, tại tầng môi trường core/engine/game_env.py, "
        "lớp CaroEnv duy trì cấu trúc ma trận danh sách lồng nhau của Python (_board: list[list[int]]) kết hợp cùng "
        "hai hàm tiện ích tĩnh action_to_index và index_to_action. Việc sử dụng danh sách lồng nhau thuần Python cho "
        "bàn cờ kích thước nhỏ (121 ô) giúp thao tác truy cập từng ô board[r][c] và sao chép hàng (row[:]) trong "
        "quá trình duyệt cây tìm kiếm đạt độ trễ chỉ vài micro-giây mà không chịu chi phí khởi tạo đối tượng mảng NumPy."
    )
    b.add_paragraph(
        "Để phục vụ đồng thời cho các tác tử tìm kiếm và mạng nơ-ron chính sách, trạng thái các nước đi hợp lệ được "
        "cung cấp dưới hai định dạng: danh sách tọa độ tuple list[Action] từ phương thức legal_actions() (duyệt theo "
        "thứ tự từ trên xuống dưới, từ trái sang phải) và mặt nạ nhị phân bất biến legal_action_mask(state) trả về "
        "tuple[bool, ...] gồm 121 phần tử, trong đó phần tử thứ i nhận giá trị True nếu ô (i // 11, i % 11) đang trống "
        "và ván cờ chưa kết thúc."
    )

    # 3.4.2
    p_342 = find_paragraph(doc, "3.4.2. RuleEngine, kiểm tra bốn hướng", "Heading 3")
    b = SectionBuilder(doc, p_342)
    b.add_paragraph(
        "Logic kiểm tra thắng thua được tách biệt hoàn toàn vào lớp tĩnh RuleEngine tại tệp core/engine/rules.py. "
        "Một đường thẳng trên lưới hai chiều được xác định bởi một cặp độ lệch đơn vị (dr, dc) thuộc tập bốn hướng "
        "chuẩn hóa DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1)), tương ứng với hướng ngang (trái sang phải), "
        "hướng dọc (trên xuống dưới), đường chéo chính (trên-trái xuống dưới-phải) và đường chéo phụ (trên-phải "
        "xuống dưới-trái). Việc chỉ định nghĩa một chiều dương cho mỗi trục là hoàn toàn đủ vì thuật toán luôn "
        "quét lùi về điểm đầu chuỗi trước khi đếm tiến tới điểm cuối chuỗi."
    )
    b.add_paragraph(
        "Cốt lõi của RuleEngine là phương thức tĩnh check_line(board, row, col, dr, dc, player, win_length=5, "
        "blocked_ends_rule=True). Khi người chơi vừa đặt quân tại vị trí (row, col), thuật toán thực hiện ba bước "
        "tuần tự trên từng hướng (dr, dc):"
    )
    b.add_bullet(
        "Bước 1 — Dò ngược tìm điểm bắt đầu chuỗi tối đại",
        "Từ tọa độ (row, col), con trỏ (sr, sc) lùi liên tiếp theo vector (-dr, -dc) chừng nào ô tiếp theo vẫn "
        "nằm trong biên 0 ≤ r < 11, 0 ≤ c < 11 và chứa quân của cùng người chơi player. Kết thúc bước này, (sr, sc) "
        "là đầu mút thứ nhất của chuỗi liên tiếp.",
    )
    b.add_bullet(
        "Bước 2 — Đếm toàn bộ độ dài chuỗi liên tiếp (Maximal Contiguous Run)",
        "Từ (sr, sc), con trỏ tiến theo vector (+dr, +dc) và tăng biến đếm count cho đến khi gặp ô trống, quân đối phương "
        "hoặc vượt ra ngoài biên bàn cờ. Nếu count < win_length (tức nhỏ hơn 5), phương thức lập tức trả về False. "
        "Cách đếm toàn bộ chuỗi tối đại này cho phép xử lý thống nhất cả trường hợp đúng 5 quân lẫn chuỗi dài hơn 5 quân "
        "(overline 6, 7, ... quân) mà không bị phụ thuộc vào vị trí đặt quân cuối cùng nằm ở giữa hay ở đầu chuỗi.",
    )
    b.add_bullet(
        "Bước 3 — Kiểm tra luật chặn hai đầu (Blocked-Ends Rule)",
        "Khi count ≥ 5 và cờ blocked_ends_rule=True, thuật toán xác định tọa độ hai ô ngay sát hai đầu chuỗi là "
        "h1 = (sr - dr, sc - dc) và h2 = (sr + count × dr, sc + count × dc). Theo quy ước trong RuleEngine, một đầu "
        "được đánh giá là bị chặn (blocked) nếu tọa độ đó nằm ngoài biên bàn cờ hoặc chứa quân của đối phương (-player); "
        "ngược lại, nếu ô đó nằm trong bàn cờ và đang trống (EMPTY = 0) thì đầu đó mở. Nước đi được công nhận là thắng "
        "khi và chỉ khi không đồng thời bị chặn cả hai đầu: not (blocked_head1 and blocked_head2). Như vậy, chuỗi ≥ 5 quân "
        "mở cả hai đầu hoặc chỉ bị chặn một đầu (do quân đối phương hoặc do sát mép bàn cờ) đều hợp lệ để thắng; chỉ khi "
        "cả hai đầu đều bị khóa bởi quân đối phương hoặc biên bàn cờ thì chuỗi mới bị vô hiệu hóa.",
    )
    b.add_paragraph(
        "Để tối ưu hiệu năng cho CaroEnv.step(), RuleEngine cung cấp phương thức check_winner_from_action(board, "
        "last_action, ...) chỉ kiểm tra đúng 4 hướng đi qua nước đi vừa đánh với thời gian O(n), đồng thời hỗ trợ "
        "find_winning_line_from_action trả về danh sách tọa độ của chuỗi quân chiến thắng để giao diện UI tô sáng (highlight). "
        "Trạng thái thắng luôn được xét ưu tiên trước trạng thái hòa: ở nước đi thứ 121 làm đầy bàn cờ, nếu nước đi đó "
        "tạo thành chuỗi 5 quân hợp lệ thì người vừa đánh vẫn được xử thắng; chỉ khi không có người thắng và _move_count == 121 "
        "thì ván cờ mới kết thúc hòa (winner = None)."
    )

    # 3.4.3
    p_343 = find_paragraph(doc, "3.4.3. CaroEnv và vòng đời ván chơi", "Heading 3")
    b = SectionBuilder(doc, p_343)
    b.add_paragraph(
        "Lớp CaroEnv (core/engine/game_env.py) đóng gói toàn bộ máy trạng thái hữu hạn của ván cờ theo thiết kế lấy cảm hứng "
        "từ chuẩn Gymnasium nhưng được chuyên biệt hóa cho trò chơi đối kháng hai người chơi tổng bằng không. Vòng đời "
        "của một ván cờ diễn ra qua chuỗi phương thức: khởi tạo CaroEnv(config) → đặt lại trạng thái đầu ván bằng "
        "reset(seed) → lặp quá trình truy vấn legal_actions() và thực thi step(action) cho tới khi is_terminal() == True → "
        "trích xuất kết quả chung cuộc qua winner hoặc result(player)."
    )
    b.add_paragraph(
        "Khi nhận một hành động đầu vào trong step(action), CaroEnv bắt buộc thực hiện quy trình kiểm tra tính hợp lệ "
        "theo tầng (Cascade Validation Order) trước khi thay đổi bất kỳ biến trạng thái nào. Nếu vi phạm, hệ thống ném "
        "ngoại lệ tường minh IllegalActionError kèm mã lỗi chuẩn hóa:"
    )
    b.add_bullet(
        "Tầng 1 — Trạng thái kết thúc (GAME_OVER)",
        "Nếu _terminated == True, từ chối mọi nước đi mới vì ván cờ đã khép lại.",
    )
    b.add_bullet(
        "Tầng 2 — Định dạng dữ liệu (MALFORMED)",
        "Kiểm tra action phải là một tuple gồm đúng 2 phần tử kiểu int (loại trừ kiểu bool vì trong Python bool là lớp con của int).",
    )
    b.add_bullet(
        "Tầng 3 — Phạm vi tọa độ (OUT_OF_BOUNDS)",
        "Kiểm tra điều kiện biên 0 ≤ row < 11 và 0 ≤ col < 11.",
    )
    b.add_bullet(
        "Tầng 4 — Trạng thái ô cờ (OCCUPIED)",
        "Kiểm tra ô _board[row][col] phải đang ở trạng thái Player.EMPTY (0).",
    )
    b.add_paragraph(
        "Việc kiểm tra nghiêm ngặt trước khi ghi giúp đảm bảo tính nguyên tử (atomicity): một lời gọi step() bị lỗi "
        "không bao giờ làm hỏng trạng thái bàn cờ, bộ đếm nước đi hay ngăn xếp lịch sử. Khi nước đi vượt qua cả 4 tầng "
        "kiểm tra, CaroEnv đẩy bộ ba (row, col, _last_action) vào ngăn xếp _history, ghi giá trị int(_current_player) "
        "vào _board[row][col], cập nhật _last_action = (row, col), tăng _move_count thêm 1, rồi gọi "
        "RuleEngine.check_winner_from_action. Nếu phát hiện chiến thắng, cờ _terminated được bật lên True, _winner gán bằng "
        "người chơi vừa đánh và phần thưởng tức thời reward = 1.0; nếu bàn cờ đầy (_move_count == 121) mà chưa ai thắng, "
        "_terminated = True, _winner = None và reward = 0.0; nếu ván cờ tiếp tục, _current_player được đảo sang đối phương "
        "(_current_player.other) và trả về đối tượng bất biến StepResult(state, reward, terminated, truncated=False, winner, info)."
    )

    # 3.4.4
    p_344 = find_paragraph(doc, "3.4.4. Snapshot phòng vệ, clone, history stack", "Heading 3")
    b = SectionBuilder(doc, p_344)
    b.add_paragraph(
        "Trong các giải thuật tìm kiếm trên cây như Minimax và MCTS, tác tử liên tục thử nghiệm hàng nghìn chuỗi nước đi "
        "giả định từ trạng thái gốc. Nếu tác tử vô tình sửa đổi trực tiếp ma trận bàn cờ của môi trường thật, kết quả "
        "thi đấu sẽ bị sai lệch nghiêm trọng. Để giải quyết triệt để vấn đề này, CaroEnv thiết kế ba cơ chế bảo vệ và "
        "phục hồi trạng thái:"
    )
    b.add_bullet(
        "Snapshot phòng vệ (_snapshot và GameState)",
        "Thuộc tính env.state trả về một đối tượng dataclass bất biến GameState(frozen=True). Mỗi khi tạo snapshot, "
        "phương thức _snapshot() thực hiện sao chép từng hàng của ma trận bàn cờ bằng biểu thức [row[:] for row in self._board]. "
        "Nhờ vậy, dù mã bên ngoài có cố tình thay đổi danh sách board bên trong đối tượng GameState vừa nhận, ma trận "
        "_board nội bộ của CaroEnv vẫn hoàn toàn nguyên vẹn.",
    )
    b.add_bullet(
        "Nhân bản môi trường tốc độ cao (clone_env)",
        "Thay vì sử dụng hàm copy.deepcopy() tiêu chuẩn của Python vốn có chi phí tra cứu từ điển và phản chiếu đối tượng "
        "rất lớn, phương thức clone_env() cấp phát trực tiếp một thể hiện mới bằng CaroEnv.__new__(CaroEnv) (bỏ qua __init__), "
        "gán lại tham chiếu tới đối tượng bất biến config, sao chép ma trận 11 × 11 bằng [row[:] for row in self._board] "
        "và sao chép nông danh sách lịch sử self._history[:] (vì mỗi phần tử trong _history là một tuple bất biến). "
        "Kỹ thuật này giúp thời gian nhân bản toàn bộ môi trường giảm xuống chỉ còn khoảng 1,1 – 1,4 µs.",
    )
    b.add_bullet(
        "Ngăn xếp lịch sử và hoàn tác trạng thái (History Stack & undo)",
        "Mỗi phần tử trong _history lưu trữ bộ ba (row, col, previous_last_action) kiểu tuple[int, int, Action | None]. "
        "Khi gọi phương thức undo(), môi trường lấy phần tử đỉnh ngăn xếp bằng _history.pop(), khôi phục người chơi vừa "
        "đánh thông qua giá trị quân cờ đang nằm tại ô đó (_current_player = Player(self._board[row][col])), trả ô "
        "_board[row][col] về Player.EMPTY, khôi phục _last_action = previous_last_action, giảm _move_count đi 1 và đặt lại "
        "_terminated = False, _winner = None. Cơ chế này cho phép Minimax và MCTS mở lại cả các nút lá đã kết thúc ván cờ "
        "(terminal nodes) để quay lui (backtrack) trên duy nhất một bản sao môi trường trong suốt quá trình tìm kiếm.",
    )

    # 3.4.5
    p_345 = find_paragraph(doc, "3.4.5. Độ phức tạp của step, undo, clone_env", "Heading 3")
    b = SectionBuilder(doc, p_345)
    b.add_paragraph(
        "Xét trên bàn cờ tổng quát kích thước n × n (với n = 11 cố định trong đồ án) và ván cờ đang ở lượt đi thứ m "
        "(0 ≤ m ≤ n²), độ phức tạp lý thuyết và chi phí thực nghiệm của các thao tác cốt lõi trên CaroEnv được phân tích "
        "và đo kiểm trực tiếp bằng kịch bản benchmarks/bench_clone_step.py (5.000 vòng lặp trên mỗi thao tác). "
        "Kết quả tổng hợp được trình bày tại Bảng 3.7."
    )
    b.add_table(
        headers=[
            "Thao tác Engine",
            "Độ phức tạp thời gian",
            "Độ phức tạp không gian phụ",
            "Độ trễ trung bình ± độ lệch chuẩn (µs)",
            "Độ trễ trung vị / p95 (µs)",
        ],
        rows=[
            [
                "step(action) (kèm tạo StepResult)",
                "O(n) kiểm tra thắng + O(n²) snapshot",
                "O(n²) cho bản sao bàn cờ trong StepResult",
                "13,42 ± 3,85",
                "12,90 / 16,80",
            ],
            [
                "undo() (hoàn tác 1 nước đi)",
                "O(1)",
                "O(1)",
                "4,25 ± 1,40",
                "4,10 / 5,30",
            ],
            [
                "Cặp thao tác step(action) + undo()",
                "O(n) + O(n²) snapshot",
                "O(1) sau khi thu hồi StepResult",
                "13,20 ± 4,20",
                "12,80 / 16,50",
            ],
            [
                "clone_env() (ở m = 0..60 nước đi)",
                "O(n² + m)",
                "O(n² + m)",
                "1,35 ± 0,95",
                "1,20 / 1,90",
            ],
            [
                "Truy cập thuộc tính env.state (_snapshot)",
                "O(n²)",
                "O(n²)",
                "2,60 ± 1,10",
                "2,50 / 3,40",
            ],
        ],
        caption_label="Bảng 3.7.",
        caption_text="Độ phức tạp thuật toán và độ trễ thực nghiệm của các thao tác trên CaroEnv (n = 11, 5.000 lượt đo)",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )
    b.add_paragraph(
        "Từ số liệu ở Bảng 3.7 có thể rút ra hai nhận xét quan trọng cho việc thiết kế tác tử tìm kiếm. Thứ nhất, "
        "nhờ kiểm tra thắng thua cục bộ quanh nước đi vừa đánh (check_winner_from_action), thao tác step() chỉ cần quét "
        "tối đa 4 hướng × 11 ô thay vì duyệt toàn bộ 121 ô × 4 hướng, giữ cho thời gian thực thi trung vị chỉ ở mức "
        "~12,9 µs. Thứ hai, cặp thao tác step() kết hợp undo() trên cùng một bản sao môi trường cho phép duyệt khoảng "
        "75.000 nút/giây trong Python thuần, hoàn toàn đáp ứng yêu cầu mở rộng hàng trăm đến hàng nghìn nút mỗi nước đi "
        "của Minimax và MCTS trong giới hạn thời gian thực."
    )


def fill_section_3_5_search_agents(doc: docx.Document) -> None:
    p_35 = find_paragraph(doc, "3.5. Các tác tử tìm kiếm", "Heading 2")
    b_35 = SectionBuilder(doc, p_35)
    b_35.add_paragraph(
        "Trên nền tảng CaroEnv đã chuẩn hóa, đồ án xây dựng hệ thống phân cấp gồm bốn tác tử không học (Random, Heuristic, "
        "Minimax/Alpha-Beta, MCTS) và một tác tử học sâu (NeuralAgent). Tất cả các tác tử đều kế thừa chung một giao diện "
        "lập trình nhằm bảo đảm tính hoán đổi (interchangeability) và tính công bằng khi thi đấu."
    )

    # 3.5.1
    p_351 = find_paragraph(doc, "3.5.1. Giao diện chung và ngữ nghĩa budget", "Heading 3")
    b = SectionBuilder(doc, p_351)
    b.add_paragraph(
        "Tệp core/agents/base.py định nghĩa giao thức chuẩn Agent thông qua cơ chế Structural Subtyping (typing.Protocol "
        "với đánh dấu @runtime_checkable). Mọi tác tử hợp lệ trong hệ thống bắt buộc cung cấp thuộc tính định danh "
        "name: str và phương thức quyết định duy nhất choose_action(env: CaroEnv, budget: SearchBudget | None = None) -> AgentDecision."
    )
    b.add_paragraph(
        "Hai cấu trúc dữ liệu bất biến SearchBudget và AgentDecision đóng vai trò hợp đồng đầu vào – đầu ra giữa "
        "bộ điều phối trận đấu (TournamentRunner / UI) và tác tử:"
    )
    b.add_table(
        headers=["Cấu trúc dữ liệu", "Trường thông tin", "Kiểu dữ liệu", "Ý nghĩa và quy ước vận hành"],
        rows=[
            [
                "SearchBudget (Đầu vào)",
                "time_limit_ms",
                "int | None",
                "Giới hạn thời gian suy nghĩ tối đa cho một nước đi (ms). Trong profile FAIR, mọi tác tử chịu giới hạn 150 ms.",
            ],
            [
                "SearchBudget (Đầu vào)",
                "max_depth",
                "int | None",
                "Độ sâu tìm kiếm tối đa cho giải thuật lặp sâu dần trong Minimax (mặc định bằng 2 ở cấu hình giải đấu).",
            ],
            [
                "SearchBudget (Đầu vào)",
                "max_nodes",
                "int | None",
                "Số lượng nút mở rộng tối đa cho phép trong một lượt tìm kiếm cây.",
            ],
            [
                "SearchBudget (Đầu vào)",
                "simulations",
                "int | None",
                "Ngân sách số lượt mô phỏng (rollout/playout) cho giải thuật MCTS.",
            ],
            [
                "SearchBudget (Đầu vào)",
                "seed",
                "int | None",
                "Hạt giống ngẫu nhiên cục bộ truyền vào từng ply để đảm bảo tính tái lập 100% mà không dùng RNG toàn cục.",
            ],
            [
                "AgentDecision (Đầu ra)",
                "action",
                "Action (tuple[int, int])",
                "Tọa độ nước đi (row, col) được chọn, bắt buộc thuộc tập env.legal_actions().",
            ],
            [
                "AgentDecision (Đầu ra)",
                "score",
                "float | None",
                "Điểm lượng giá hoặc xác suất tự tin của nước đi được chọn từ góc nhìn người sắp đi.",
            ],
            [
                "AgentDecision (Đầu ra)",
                "nodes, simulations",
                "int, int",
                "Số nút cây đã duyệt và số lượt mô phỏng đã thực hiện thực tế (bằng 0 với Random, Heuristic, Neural).",
            ],
            [
                "AgentDecision (Đầu ra)",
                "elapsed_ms",
                "float",
                "Thời gian thực thi thực tế đo bằng đồng hồ đơn điệu time.perf_counter() tính bằng mili-giây.",
            ],
        ],
        caption_label="Bảng 3.8.",
        caption_text="Đặc tả các trường của SearchBudget và AgentDecision trong hợp đồng tác tử",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
        ],
    )
    b.add_paragraph(
        "Giao diện chung áp đặt bốn quy tắc bất biến cho mọi tác tử: (1) Nếu env.is_terminal() là True hoặc không còn "
        "nước đi hợp lệ, tác tử phải ném ngoại lệ RuntimeError; (2) Tác tử tuyệt đối không được làm thay đổi trạng thái "
        "của đối tượng env truyền vào (mọi phép thử nước đi phải thực hiện trên bản sao env.clone_env()); (3) Mọi yếu tố "
        "ngẫu nhiên phải khởi tạo qua bộ sinh cục bộ random.Random(budget.seed); và (4) Khi chạm ngưỡng ngân sách thời gian "
        "hoặc số nút giữa chừng, tác tử phải dừng tìm kiếm an toàn và trả về nước đi tốt nhất đã tìm được ở tầng hoàn chỉnh "
        "gần nhất (graceful fallback)."
    )

    # 3.5.2
    p_352 = find_paragraph(doc, "3.5.2. Random Agent", "Heading 3")
    b = SectionBuilder(doc, p_352)
    b.add_paragraph(
        "Lớp RandomAgent (core/agents/random_ai.py) là tác tử cơ sở (lower-bound baseline) dùng để kiểm chứng đường ống "
        "thi đấu và làm mốc tham chiếu sàn cho các thuật toán thông minh hơn. Khi choose_action(env, budget) được kích hoạt, "
        "tác tử lấy danh sách nước đi hợp lệ legal = env.legal_actions(), khởi tạo bộ sinh số ngẫu nhiên cục bộ "
        "rng = random.Random(budget.seed) nếu budget có cung cấp hạt giống (hoặc sử dụng bộ sinh nội bộ của tác tử nếu không có), "
        "sau đó chọn một nước đi theo phân phối đều rời rạc thông qua rng.choice(legal)."
    )
    b.add_paragraph(
        "Do không thực hiện bất kỳ phép lượng giá bàn cờ hay tìm kiếm cây nào, RandomAgent luôn trả về AgentDecision với "
        "score = None, nodes = 0, simulations = 0 và độ phức tạp thời gian chỉ là O(n²) để quét danh sách ô trống "
        "(thời gian thực thi trung bình trong giải đấu chỉ khoảng 0,03 ms/nước). Mọi tác tử có tri thức (Heuristic, Minimax, "
        "MCTS, Neural) bắt buộc phải đạt tỷ lệ thắng xấp xỉ tuyệt đối khi đối đầu với RandomAgent."
    )

    # 3.5.3
    p_353 = find_paragraph(doc, "3.5.3. Heuristic Agent", "Heading 3")
    b = SectionBuilder(doc, p_353)
    b.add_paragraph(
        "Lớp HeuristicAgent (core/agents/heuristic_ai.py) hiện thực hóa chiến lược đánh giá mẫu hình cục bộ một bước "
        "(single-ply pattern evaluation) kết hợp thứ tự ưu tiên chiến thuật rõ ràng. Đóng vai trò cốt lõi trong module này "
        "là tập hàm lượng giá dùng chung cho cả HeuristicAgent, bộ sắp xếp nước đi (move ordering) của Minimax và hàm "
        "hướng dẫn của MCTS, bao gồm: action_priority, evaluate_board, candidate_actions và center_bonus."
    )
    b.add_paragraph(
        "Với mỗi nước đi hợp lệ a = (r, c) thuộc tập env.legal_actions(), hàm action_priority(board, action, player, win_length=5) "
        "xếp hạng nước đi theo ba tầng ưu tiên tách biệt về bậc độ lớn:"
    )
    b.add_bullet(
        "Tầng 1 — Thắng tức thời (Immediate Win)",
        "Tạm đặt quân của người chơi hiện tại (player) vào ô (r, c) và gọi RuleEngine.check_winner_from_action. "
        "Nếu tạo thành chuỗi 5 quân thắng hợp lệ, hàm lập tức trả về điểm ưu tiên tuyệt đối WIN_SCORE + center_bonus "
        "(với WIN_SCORE = 1.000.000,0).",
    )
    b.add_bullet(
        "Tầng 2 — Chặn thắng khẩn cấp của đối phương (Immediate Block)",
        "Nếu chưa thắng ngay, hàm thử đặt quân của đối phương (-player) vào chính ô (r, c). Nếu nước đi đó giúp đối phương "
        "thắng ngay, ô (r, c) là điểm chặn bắt buộc và nhận điểm BLOCK_SCORE + center_bonus (với BLOCK_SCORE = 100.000,0).",
    )
    b.add_bullet(
        "Tầng 3 — Kết hợp Công – Thủ theo mẫu hình cửa sổ trượt và ưu tiên trung tâm",
        "Nếu không thuộc hai trường hợp khẩn cấp trên, hàm tính điểm tấn công attack = _Hypothetical_action_score(board, action, player) "
        "và điểm phòng thủ defend = _Hypothetical_action_score(board, action, -player), sau đó tổng hợp theo công thức: "
        "Score(a) = attack + DEFENSE_FACTOR × defend + center_bonus(a), trong đó hệ số phòng thủ DEFENSE_FACTOR = 0,9 giúp "
        "tác tử hơi nghiêng về chủ động tạo thế công khi điểm mẫu hình hai bên ngang nhau, còn center_bonus(a) ∈ [0, 1) "
        "đóng vai trò phân định hòa (tie-breaker) ưu tiên các ô gần tâm bàn cờ (5, 5).",
    )
    b.add_paragraph(
        "Để tính điểm mẫu hình _window_Contribution trên mỗi hướng trong 4 hướng chuẩn, thuật toán xét các cửa sổ trượt "
        "độ dài win_length = 5 chứa các quân cùng màu mà không bị quân đối phương xen vào. Gọi missing là số ô còn trống "
        "trong cửa sổ 5 ô (1 ≤ missing ≤ 3) và open_ends ∈ {0, 1, 2} là số đầu mở (ô liền kề hai đầu cửa sổ nằm trong bàn cờ "
        "và đang trống). Nếu cả hai đầu cửa sổ đều bị chặn (open_ends == 0), cửa sổ đó bị loại bỏ hoàn toàn để tuân thủ "
        "luật chặn hai đầu của caro-v2. Ngược lại, điểm mẫu hình được tra cứu theo Bảng 3.9."
    )
    b.add_table(
        headers=[
            "Mẫu hình chiến thuật",
            "Số quân đã có / Số ô thiếu (missing)",
            "Số đầu mở (open_ends)",
            "Khóa tra cứu (missing, open_ends)",
            "Điểm lượng giá (_PATTERN_SCORES)",
        ],
        rows=[
            ["Thắng ngay trong 1 nước (WIN_SCORE)", "5 / 0", "≥ 1 (theo RuleEngine)", "Kiểm tra trực tiếp", "1.000.000,0"],
            ["Chặn đối thủ thắng trong 1 nước (BLOCK_SCORE)", "4 của đối thủ / 1", "≥ 1 (theo RuleEngine)", "Kiểm tra trực tiếp", "100.000,0"],
            ["Tứ mở hai đầu (Open Four)", "4 / 1", "2", "(1, 2)", "10.000,0"],
            ["Tứ bị chặn một đầu (Closed Four)", "4 / 1", "1", "(1, 1)", "2.000,0"],
            ["Tam mở hai đầu (Open Three)", "3 / 2", "2", "(2, 2)", "1.500,0"],
            ["Tam bị chặn một đầu (Closed Three)", "3 / 2", "1", "(2, 1)", "150,0"],
            ["Nhị mở hai đầu (Open Two)", "2 / 3", "2", "(3, 2)", "100,0"],
            ["Nhị bị chặn một đầu (Closed Two)", "2 / 3", "1", "(3, 1)", "10,0"],
        ],
        caption_label="Bảng 3.9.",
        caption_text="Hệ thống thang điểm ưu tiên và trọng số các mẫu hình chiến thuật trong HeuristicAgent",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )
    b.add_paragraph(
        "Tại bước chọn nước đi cuối cùng, HeuristicAgent duyệt qua toàn bộ danh sách legal_actions() theo thứ tự hàng – cột "
        "và giữ lại nước đi đầu tiên đạt giá trị điểm cao nhất (score > best_score). Nhờ quy tắc so sánh ngặt (>) kết hợp "
        "thứ tự duyệt cố định, HeuristicAgent là một tác tử hoàn toàn tất định (deterministic): cùng một trạng thái bàn cờ "
        "luôn tạo ra duy nhất một nước đi."
    )

    # 3.5.4
    p_354 = find_paragraph(doc, "3.5.4. Minimax và Alpha-Beta", "Heading 3")
    b = SectionBuilder(doc, p_354)
    b.add_paragraph(
        "Lớp MinimaxAgent (core/agents/minimax_ai.py) mở rộng khả năng nhìn trước nhiều nước đi bằng giải thuật tìm kiếm "
        "đối kháng Minimax kết hợp bốn kỹ thuật tối ưu hóa: cắt tỉa Alpha-Beta, lọc nước đi ứng viên theo lân cận Chebyshev, "
        "sắp xếp thứ tự nước đi (Move Ordering) và lặp sâu dần (Iterative Deepening)."
    )
    b.add_paragraph(
        "Thay vì nhân bản môi trường tại mỗi nút con, MinimaxAgent chỉ tạo duy nhất một bản sao sim = env.clone_env() "
        "khi bắt đầu choose_action, sau đó sử dụng cặp thao tác sim.step(action) và sim.undo() để duyệt toàn bộ cây tìm kiếm "
        "theo chiều sâu. Giá trị của mọi nút được quy chiếu nhất quán về góc nhìn của người chơi gốc (root_player): nút thuộc "
        "lượt root_player đóng vai trò cực đại hóa (Maximizing node, cập nhật α = max(α, value)), còn nút thuộc lượt đối phương "
        "đóng vai trò cực tiểu hóa (Minimizing node, cập nhật β = min(β, value)). Khi xảy ra điều kiện β ≤ α (nếu alpha_beta=True), "
        "nhánh con hiện tại bị cắt tỉa ngay lập tức."
    )
    b.add_paragraph(
        "Hàm lượng giá tại các nút lá và nút kết thúc ván cờ được thiết kế để đảm bảo tính tương thích toán học giữa "
        "điểm thắng tuyệt đối và điểm ước lượng heuristic:"
    )
    b.add_bullet(
        "Tại nút kết thúc ván cờ (Terminal Node)",
        "Nếu ván cờ kết thúc hòa, hàm trả về 0,0. Nếu có người thắng ở độ sâu ply tính từ gốc, hàm trả về +(WIN_VALUE - ply) "
        "nếu người thắng là root_player và -(WIN_VALUE - ply) nếu người thắng là đối phương (với WIN_VALUE = 1.000.000,0). "
        "Việc trừ đi ply giúp tác tử luôn ưu tiên đường thắng ngắn nhất khi đang thắng và kéo dài số nước đi tối đa khi bị dồn vào thế thua.",
    )
    b.add_bullet(
        "Tại nút lá chạm giới hạn độ sâu (depth == 0)",
        "Hàm gọi evaluate_board(sim._board, root_player, win_length=5), tính hiệu số tổng điểm mẫu hình toàn bàn giữa "
        "root_player và đối phương cộng với ưu thế vị trí trung tâm nhân hệ số POSITION_WEIGHT = 0,1. Giá trị trả về được "
        "kẹp (clamp) trong đoạn [-500.000,0; +500.000,0] để không bao giờ vượt qua ngưỡng thắng thua thật sự.",
    )
    b.add_paragraph(
        "Do bàn cờ 11 × 11 có tới 121 ô, hệ số phân nhánh (branching factor) ở đầu ván rất lớn. Để tập trung tài nguyên "
        "tính toán vào vùng chiến thuật có ý nghĩa, hàm candidate_actions(board, legal, radius=2) chỉ giữ lại các ô trống "
        "nằm trong khoảng cách Chebyshev r ≤ 2 quanh bất kỳ quân cờ nào đã đánh trên bàn (tức thỏa mãn max(|r - r₀|, |c - c₀|) ≤ 2); "
        "riêng khi bàn cờ hoàn toàn trống, hàm chỉ trả về duy nhất ô trung tâm (5, 5). Tiếp đó, nếu move_ordering=True, "
        "danh sách ứng viên được sắp xếp giảm dần theo điểm action_priority, đồng thời đưa nước đi tốt nhất của độ sâu trước "
        "(Principal Variation move — previous_best) lên vị trí đầu tiên để tối đa hóa xác suất cắt tỉa Alpha-Beta sớm."
    )
    b.add_paragraph(
        "Vòng lặp Iterative Deepening chạy tuần tự từ depth = 1 đến target_depth = budget.max_depth. Trước mỗi bước mở rộng nút, "
        "đối tượng ngữ cảnh _Context.check_limits() kiểm tra đồng thời số nút đã duyệt (nodes >= max_nodes) và thời hạn "
        "đồng hồ (perf_counter() >= deadline). Nếu vượt ngưỡng, ngoại lệ nội bộ _SearchStop được ném ra để thoát khỏi "
        "đệ quy ngay lập tức và trả về kết quả hoàn chỉnh của độ sâu trước đó (hoặc nước đi đầu tiên theo sắp xếp heuristic "
        "nếu ngay tại depth = 1 đã hết ngân sách). Ngoài ra, nếu phát hiện giá trị thắng cưỡng bức (value > 500.000,0), "
        "vòng lặp lặp sâu dần cũng dừng sớm để tiết kiệm thời gian."
    )

    # 3.5.5
    p_355 = find_paragraph(doc, "3.5.5. MCTS", "Heading 3")
    b = SectionBuilder(doc, p_355)
    b.add_paragraph(
        "Lớp MCTSAgent (core/agents/mcts_ai.py phối hợp cùng core/agents/search_utils.py) triển khai giải thuật Tìm kiếm "
        "Cây Monte Carlo (Monte Carlo Tree Search) theo kiến trúc UCT (Upper Confidence Bound applied to Trees), kết hợp "
        "các cơ chế tăng cường tri thức miền Caro nhằm khắc phục điểm yếu của mô phỏng ngẫu nhiên thuần túy trên không gian "
        "hành động lớn."
    )
    b.add_paragraph(
        "Mỗi nút trong cây tìm kiếm (_MCTSNode) lưu giữ liên kết tới nút cha (parent), nước đi dẫn tới nút (action), "
        "người chơi sắp đi tại nút đó (player_to_move), danh sách các hành động ứng viên chưa mở rộng (untried_actions), "
        "từ điển các nút con (children), số lượt viếng thăm N(v) (visits) và tổng giá trị tích lũy W(v) (value_sum) quy về "
        "góc nhìn của root_player. Trước khi bước vào vòng lặp mô phỏng, nếu cờ tactical_precheck=True được bật (mặc định "
        "trong cấu hình giải đấu), tác tử gọi immediate_tactical_action để kiểm tra xem có nước thắng ngay trong 1 bước "
        "hoặc có đúng 1 nước chặn bắt buộc duy nhất hay không; nếu có, tác tử trả về ngay nước đi đó với simulations = 0 "
        "để tránh lãng phí ngân sách mô phỏng vào các tình huống hiển nhiên."
    )
    b.add_paragraph(
        "Khi không có nước đi cưỡng bức tức thời, mỗi lượt mô phỏng (simulation) thực thi bốn pha chuẩn trên một bản sao "
        "môi trường tái sử dụng (sim = env.clone_env(), hoàn tác bằng sim.undo() sau mỗi lượt):"
    )
    b.add_bullet(
        "Pha 1 — Chọn lựa (Selection)",
        "Xuất phát từ nút gốc, thuật toán đi xuống nút con đã mở rộng chừng nào nút hiện tại chưa phải trạng thái kết thúc "
        "và không còn nhánh con nào được phép mở rộng thêm. Tại mỗi nút, nút con u được chọn sao cho cực đại hóa chỉ số UCT: "
        "UCT(u) = Q_persp(u) + c × sqrt(ln(max(1, N(v))) / N(u)), với hằng số khám phá c = exploration_constant (mặc định √2). "
        "Điểm tinh tế quan trọng trong cài đặt là việc xử lý dấu của thành phần khai thác Q_persp(u): do W(u) luôn được "
        "cộng dồn theo góc nhìn của root_player, nên nếu nút cha v thuộc lượt của root_player thì Q_persp(u) = +W(u)/N(u), "
        "nhưng nếu nút cha v thuộc lượt của đối phương thì Q_persp(u) = -W(u)/N(u). Nhờ phép đảo dấu này, đối phương trong "
        "cây MCTS luôn chủ động chọn nhánh bất lợi nhất cho root_player thay vì hợp tác.",
    )
    b.add_bullet(
        "Pha 2 — Mở rộng (Expansion) và Mở rộng lũy tiến (Progressive Widening)",
        "Danh sách ứng viên tại mỗi nút được rút gọn trong bán kính Chebyshev (candidate_radius = 2) và có thể được sắp xếp "
        "trước theo điểm chiến thuật (heuristic_seeded hoặc tactical_local_seeded). Khi bật use_progressive_widening=True, "
        "số lượng nhánh con tối đa được phép mở tại nút có N lượt thăm bị giới hạn bởi công thức k_max = max(min_children, "
        "ceil(pw_constant × (N + 1)^pw_alpha)). Cơ chế này giúp MCTS khi chạy ở ngân sách nhỏ (như 8 hoặc 64 simulations) "
        "tập trung làm sâu các nhánh hứa hẹn nhất thay vì dàn trải mỗi nhánh 1 lượt thăm.",
    )
    b.add_bullet(
        "Pha 3 — Mô phỏng (Rollout / Playout)",
        "Từ nút vừa mở rộng, tác tử chạy mô phỏng tối đa đến độ sâu rollout_horizon (mặc định 8 bước ở cấu hình giải đấu, "
        "hoặc 4 bước ở thí nghiệm ablation A2). Hệ thống hỗ trợ hai chính sách rollout: (i) random (chọn ngẫu nhiên đều "
        "trong các ô lân cận bán kính rollout_radius) và (ii) epsilon_heuristic (ưu tiên thắng/chặn ngay; với xác suất "
        "1 - ε = 0,85 chọn nước có điểm mẫu hình cao nhất trong top-k ứng viên, và với xác suất ε = 0,15 chọn ngẫu nhiên "
        "để duy trì tính khám phá). Nếu hết độ sâu rollout_horizon mà ván cờ chưa kết thúc, giá trị nút lá được ước lượng "
        "mượt về khoảng (-1, +1) bằng hàm lượng giá chuẩn hóa: v_leaf = tanh(evaluate_board(board, root_player) / 5000,0).",
    )
    b.add_bullet(
        "Pha 4 — Lan truyền ngược (Backpropagation)",
        "Giá trị thu được từ pha Rollout (1,0 nếu root_player thắng, -1,0 nếu đối phương thắng, 0,0 nếu hòa, hoặc v_leaf ∈ (-1, 1)) "
        "được truyền ngược theo đường dẫn từ nút vừa mở rộng về nút gốc: tại mỗi nút trên đường đi, tăng visits thêm 1 và "
        "cộng giá trị vào value_sum, đồng thời gọi sim.undo() tương ứng với số bước đã đi để đưa môi trường giả lập về lại "
        "trạng thái gốc.",
    )
    b.add_paragraph(
        "Kết thúc toàn bộ ngân sách mô phỏng (simulations, max_nodes hoặc time_limit_ms), MCTSAgent chọn nước đi theo "
        "tiêu chuẩn Robust Child: chọn nút con của gốc có số lượt viếng thăm visits lớn nhất; nếu có nhiều nút con cùng "
        "đạt số lượt thăm cao nhất, thuật toán phân định bằng giá trị trung bình mean_value cao hơn rồi đến thứ tự tọa độ (row, col)."
    )


def fill_section_3_6_learned_agent(doc: docx.Document) -> None:
    # 3.6.2
    p_362 = find_paragraph(doc, "3.6.2", "Heading 3")
    b = SectionBuilder(doc, p_362)
    b.add_paragraph(
        "Sự tiến hóa của các phiên bản dữ liệu huấn luyện (Dataset v1 → v2 → v5). Như đã phân tích ở Mục 3.6.1, "
        "bộ dữ liệu đầu tiên dataset-v1-three-agents-2000 xác lập thành công đường ống kỹ thuật nhưng bộc lộ hai hạn chế: "
        "tác tử giáo viên MCTS ở cấu hình cơ sở (20 simulations ngẫu nhiên) thua toàn bộ 1.332 ván, và quy trình khử trùng lặp "
        "chỉ mới xét trên trạng thái gốc trước khi nhân đối xứng D4. Để nâng cao chất lượng nhãn giám sát cho mô hình chính thức, "
        "nhóm đã phát triển tiếp hai thế hệ dữ liệu nâng cấp trên cùng hợp đồng caro-v2:"
    )
    b.add_bullet(
        "Bộ dữ liệu dataset-v2-mcts-strength8 (Phục vụ huấn luyện Policy v2)",
        "Nâng cấp giáo viên MCTS lên cấu hình có hướng dẫn chiến thuật (MCTS-STRENGTH với 8 simulations, tactical precheck, "
        "progressive widening và rollout epsilon-heuristic). Trong 2.000 ván self-play của v2, MCTS đạt 979 thắng – 57 hòa – "
        "297 thua (score rate ~75,6%), cung cấp nguồn nhãn chất lượng cao. Bộ dữ liệu v2 áp dụng cân bằng số lượng mẫu "
        "giữa 3 giáo viên trong tập train (mỗi giáo viên đóng góp đúng 75.792 mẫu sau nhân D4, tổng cộng 227.376 mẫu train, "
        "5.409 mẫu validation và 5.139 mẫu test).",
    )
    b.add_bullet(
        "Bộ dữ liệu dataset-v5-clean-d4-natural-teachers (Phục vụ huấn luyện Policy v5 — Mô hình chính thức)",
        "Khắc phục triệt để nguy cơ rò rỉ đối xứng hình học giữa các tập bằng cơ chế khử trùng lặp theo quỹ đạo chuẩn hóa D4 "
        "(canonical D4 state orbit deduplication, đảm bảo cross_split_d4_state_overlap = 0 và within_split_d4_orbit_Collisions = 0). "
        "Đồng thời, thay vì cắt giảm mẫu của giáo viên mạnh nhất để ép tỷ lệ 1:1:1 như ở v2, dataset-v5 giữ nguyên phân phối "
        "tự nhiên của các trạng thái duy nhất thu được từ ván đấu (MCTS chiếm 50,66%, Heuristic 24,82% và Minimax 24,52%), "
        "tạo ra 38.642 trạng thái duy nhất × 8 phép biến đổi D4 = 309.136 mẫu train, 4.806 mẫu validation và 4.689 mẫu test.",
    )
    b.add_table(
        headers=[
            "Phiên bản dữ liệu",
            "Cấu hình giáo viên MCTS",
            "Cơ chế khử trùng & chống rò rỉ D4",
            "Số mẫu Train (sau D4 × 8)",
            "Số mẫu Val / Test",
            "Phân phối giáo viên trong Train",
        ],
        rows=[
            [
                "dataset-v1 (Cơ sở W5-W6)",
                "MCTS cơ sở (20 sims ngẫu nhiên)",
                "Khử trùng SHA-256 trạng thái gốc theo thứ tự train→val→test",
                "70.336 (8.792 gốc × 8)",
                "1.833 / 1.573",
                "Tự nhiên theo mẫu sau khử trùng",
            ],
            [
                "dataset-v2 (MCTS-Strength8)",
                "MCTS có hướng dẫn (8 sims, thắng 979/1.333 ván)",
                "Khử trùng SHA-256 + cân bằng cứng số mẫu 3 giáo viên",
                "227.376 (28.422 gốc × 8)",
                "5.409 / 5.139",
                "Cân bằng 33,33% / 33,33% / 33,33% (75.792 mẫu/giáo viên)",
            ],
            [
                "dataset-v5 (Chính thức W7-W8)",
                "MCTS có hướng dẫn (8 sims, thắng 979/1.333 ván)",
                "Cô lập quỹ đạo đối xứng D4 xuyên tập (cross_split_d4_overlap = 0)",
                "309.136 (38.642 gốc × 8)",
                "4.806 / 4.689",
                "Tự nhiên: MCTS 50,66%, Heuristic 24,82%, Minimax 24,52%",
            ],
        ],
        caption_label="Bảng 3.D.",
        caption_text="So sánh ba thế hệ bộ dữ liệu học có giám sát trong đồ án",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
        ],
    )
    b.add_paragraph(
        "Kiến trúc mạng PolicyNet (caro-policynet-resnet-v1). Để học ánh xạ từ tensor trạng thái không gian [N, 3, 11, 11] "
        "sang phân phối xác suất trên 121 ô bàn cờ, tệp core/ml/architectures.py cài đặt mạng tích chập dư PolicyNet "
        "(lấy cảm hứng từ nhánh policy của kiến trúc AlphaZero nhưng tinh chỉnh gọn nhẹ để suy luận thời gian thực trên CPU). "
        "Cấu trúc chi tiết từng tầng và số lượng tham số khả huấn được trình bày trong Bảng 3.E."
    )
    b.add_table(
        headers=[
            "Khối chức năng",
            "Cấu trúc tầng chi tiết",
            "Kích thước Tensor đầu ra",
            "Số lượng tham số",
        ],
        rows=[
            [
                "Đầu vào (Input State)",
                "Tensor trạng thái 3 kênh góc nhìn người sắp đi (float32)",
                "[N, 3, 11, 11]",
                "0",
            ],
            [
                "Khối gốc (Stem Block)",
                "Conv2d(3 → 64, kernel 3×3, padding=1, bias=False) + BatchNorm2d(64) + ReLU",
                "[N, 64, 11, 11]",
                "1.728 + 128 = 1.856",
            ],
            [
                "Tháp dư (Residual Tower × 4 khối)",
                "Mỗi khối _ResidualBlock gồm: Conv2d(64→64, 3×3, pad=1, bias=False) + BN + ReLU + Dropout2d(p=0,10) + Conv2d(64→64, 3×3, pad=1, bias=False) + BN + Cộng nhánh tắt (Skip Connection) + ReLU",
                "[N, 64, 11, 11]",
                "4 × 73.984 = 295.936",
            ],
            [
                "Đầu chính sách — Giảm chiều kênh",
                "Conv2d(64 → 32, kernel 1×1, bias=False) + BatchNorm2d(32) + ReLU",
                "[N, 32, 11, 11]",
                "2.048 + 64 = 2.112",
            ],
            [
                "Đầu chính sách — Kết nối đầy đủ",
                "Flatten(start_dim=1) (32 × 11 × 11 = 3.872 đặc trưng) → Linear(3.872 → 121, bias=True)",
                "[N, 121]",
                "3.872 × 121 + 121 = 468.633",
            ],
            [
                "Tổng cộng toàn mạng",
                "Kiến trúc caro-policynet-resnet-v1 (channels=64, num_blocks=4, head_channels=32, dropout=0,10)",
                "[N, 121] (Raw Logits)",
                "768.537 tham số",
            ],
        ],
        caption_label="Bảng 3.E.",
        caption_text="Kiến trúc chi tiết và phân bổ 768.537 tham số của mạng PolicyNet",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )
    b.add_paragraph(
        "Cơ chế mặt nạ hợp lệ và hàm mất mát (Masked Cross-Entropy Loss). Do mạng Linear ở tầng cuối xuất ra vector logits "
        "trên toàn bộ 121 ô (bao gồm cả những ô đã có quân cờ), việc tính trực tiếp hàm Softmax thông thường sẽ phân bổ "
        "xác suất dương cho các nước đi bất hợp pháp. Do đó, hàm mask_policy_logits(logits, legal_mask) thay thế toàn bộ "
        "giá trị logit tại các ô có legal_mask == False bằng hằng số âm vô cùng khả biểu diễn nhỏ nhất của kiểu dấu phẩy động "
        "(torch.finfo(logits.dtype).min ≈ -3,40 × 10³⁸ đối với float32). Khi đưa vector logits đã che mặt nạ qua hàm "
        "F.cross_entropy trong masked_policy_loss, xác suất Softmax tại mọi ô đã có quân bằng đúng 0,0 và gradient chỉ "
        "lan truyền ngược trên tập các ô trống hợp lệ. Nếu một mẫu trong lô có toàn bộ mặt nạ bằng False hoặc nhãn mục tiêu "
        "rơi vào ô bất hợp lệ, hệ thống lập tức ném lỗi ValueError để ngăn chặn huấn luyện sai."
    )
    b.add_paragraph(
        "Quy trình huấn luyện, đóng gói checkpoint, quản lý hạt giống và tài nguyên CPU/GPU. Kịch bản huấn luyện "
        "scripts/train_policy.py được điều khiển hoàn toàn bởi tệp cấu hình JSON (configs/policy_train_v5_natural.json). "
        "Trước khi khởi tạo trọng số mạng và bộ trộn mẫu DataLoader, hàm _seed_everything(seed=20261109) khóa đồng bộ "
        "hạt giống trên cả ba thư viện random, numpy và torch (bao gồm cả torch.cuda.manual_seed_all), đồng thời truyền "
        "bộ sinh torch.Generator().manual_seed(seed) riêng cho tập train. Mô hình được tối ưu hóa bằng thuật toán AdamW "
        "với tốc độ học lr = 10⁻³, hệ số suy giảm trọng số weight_decay = 10⁻⁴, kích thước lô batch_size = 256, tối đa "
        "30 epoch và cơ chế dừng sớm (early stopping) với độ kiên nhẫn patience = 5 epoch tính trên chỉ số val_loss "
        "(ngưỡng cải thiện tối thiểu min_delta = 10⁻⁴)."
    )
    b.add_paragraph(
        "Quá trình huấn luyện chính thức được thực thi trên hạ tầng GPU đám mây Google Colab (thiết bị cuda, lưu vết tại "
        "models/checkpoints/model-v5-natural-teachers-run2/run_summary.json), trong khi khâu suy luận trong giải đấu và "
        "ứng dụng UI được thiết kế chạy hoàn toàn trên CPU tiêu chuẩn. Kết thúc mỗi epoch, kịch bản lưu nguyên tử (atomic write "
        "thông qua tệp tạm .tmp rồi gọi os.replace) hai gói checkpoint: last.pt (trạng thái epoch mới nhất để hỗ trợ "
        "khôi phục huấn luyện --resume) và best.pt (trạng thái đạt val_loss thấp nhất). Mỗi tệp checkpoint tuân thủ schema "
        "caro-policy-v1, đóng gói đầy đủ model_state_dict, optimizer_state_dict, cấu hình kiến trúc, chỉ số đánh giá, "
        "trạng thái các bộ sinh số ngẫu nhiên (rng_state) và đặc biệt là mã băm dataset_manifest_sha256 liên kết chặt chẽ "
        "mô hình với đúng phiên bản dữ liệu đã sinh ra nó."
    )

    # 3.6.3
    p_363 = find_paragraph(doc, "3.6.3", "Heading 3")
    b = SectionBuilder(doc, p_363)
    b.add_paragraph(
        "Lớp NeuralAgent (đồng danh PolicyAgent tại tệp core/agents/neural_ai.py) tích hợp mô hình học sâu PolicyNet "
        "vào hệ thống dưới cùng giao thức Agent như các tác tử tìm kiếm cổ điển. Ngay tại thời điểm khởi tạo "
        "NeuralAgent(checkpoint_path), hệ thống nạp gói checkpoint lên bộ nhớ thiết bị đích (mặc định map_location='cpu' "
        "để đảm bảo tính tương thích trên mọi máy tính không có GPU rời), chuyển mạng sang chế độ suy luận model.eval() "
        "và thực thi chuỗi kiểm tra tính toàn vẹn nghiêm ngặt:"
    )
    b.add_bullet(
        "Xác thực Schema và Hợp đồng trò chơi",
        "Kiểm tra checkpoint_schema == 'caro-policy-v1', contract_version == 'caro-v2', kích thước bàn cờ board_size == 11 "
        "và độ dài chuỗi thắng win_length == 5.",
    )
    b.add_bullet(
        "Xác thực Nguồn gốc Dữ liệu (Dataset Provenance Verification)",
        "Kiểm tra trường dataset_manifest_sha256 trong checkpoint phải là chuỗi hex SHA-256 hợp lệ dài 64 ký tự; nếu tệp "
        "dataset_manifest.json hiện diện trên đĩa, tác tử tự động băm lại tệp này và đối chiếu khớp tuyệt đối với mã băm "
        "lưu trong checkpoint nhằm ngăn chặn việc nạp nhầm mô hình huấn luyện từ bộ dữ liệu khác.",
    )
    b.add_paragraph(
        "Khi phương thức choose_action(env, budget) được gọi trong trận đấu, luồng suy luận của NeuralAgent diễn ra qua "
        "5 bước tất định mà không thực hiện bất kỳ thao tác tìm kiếm cây hay biến đổi trạng thái môi trường nào:"
    )
    b.add_bullet(
        "Bước 1 — Kiểm tra điều kiện đầu vào",
        "Xác nhận env.is_terminal() là False, kích thước bàn cờ của môi trường khớp với cấu hình mô hình (11 × 11) và "
        "tập nước đi hợp lệ legal = env.legal_actions() khác rỗng.",
    )
    b.add_bullet(
        "Bước 2 — Mã hóa trạng thái chuẩn hóa",
        "Gọi trực tiếp hàm dùng chung encode_policy_state(env.state, legal, board_size=11) từ core/ml/data_pipeline.py "
        "để biến đổi trạng thái bàn cờ hiện tại thành tensor 3 kênh góc nhìn người sắp đi, sau đó mở rộng chiều lô thành "
        "kích thước [1, 3, 11, 11] và dựng tensor mặt nạ hợp lệ [1, 121] kiểu torch.bool.",
    )
    b.add_bullet(
        "Bước 3 — Lan truyền tiến và che mặt nạ hợp lệ",
        "Trong ngữ cảnh tắt theo dõi đạo hàm torch.inference_mode(), mạng PolicyNet tính toán vector logits [1, 121], "
        "rồi áp dụng mask_policy_logits(logits, mask_tensor) để gán giá trị âm vô cùng cho toàn bộ các ô đã có quân.",
    )
    b.add_bullet(
        "Bước 4 — Chọn hành động cực đại và trích xuất độ tự tin",
        "Tác tử chọn chỉ số phẳng có giá trị logit lớn nhất thông qua phép toán tất định action_index = int(torch.argmax(masked, dim=-1).item()), "
        "đồng thời tính phân phối xác suất bằng torch.softmax(masked, dim=-1) để lấy xác suất dự đoán tại đúng ô đó làm "
        "điểm lượng giá score ∈ (0, 1].",
    )
    b.add_bullet(
        "Bước 5 — Ánh xạ tọa độ và đóng gói kết quả",
        "Chuyển đổi chỉ số phẳng action_index ∈ [0, 120] về tọa độ (row, col) bằng CaroEnv.index_to_action, kiểm tra đối chiếu "
        "một lần nữa action ∈ legal, rồi trả về đối tượng AgentDecision(action=action, score=score, nodes=0, simulations=0, elapsed_ms=...).",
    )
    b.add_paragraph(
        "Nhờ dùng chung hàm encode_policy_state và mask_policy_logits giữa pha huấn luyện và pha suy luận, hệ thống "
        "loại bỏ hoàn toàn lỗi lệch phân phối đặc trưng (training-serving skew). Đồng thời, vì chỉ thực hiện duy nhất "
        "một lượt lan truyền tiến (single forward pass) với nodes = 0 và simulations = 0, độ trễ suy luận của NeuralAgent "
        "luôn ổn định ở mức vài mili-giây bất kể độ phức tạp chiến thuật trên bàn cờ."
    )


def fill_section_3_8_testing_strategy(doc: docx.Document) -> None:
    p_38 = find_paragraph(doc, "3.8 Chiến lược kiểm thử", "Heading 2")
    b = SectionBuilder(doc, p_38)
    b.add_paragraph(
        "Để đảm bảo tính đúng đắn kỹ thuật của toàn bộ hệ thống trước khi tiến hành các thực nghiệm quy mô lớn ở Chương 4, "
        "đồ án áp dụng chiến lược kiểm thử tự động đa tầng bằng khung kiểm thử pytest. Thay vì chỉ kiểm tra các trường hợp "
        "đơn lẻ thủ công, bộ kiểm thử kết hợp kiểm thử đơn vị (Unit Testing), kiểm thử hợp đồng giao diện (Contract Testing), "
        "kiểm thử bất biến dựa trên thuộc tính ngẫu nhiên có hạt giống (Property-based & Oracle Testing) và kiểm thử tích hợp "
        "đường ống đầu-cuối (End-to-End Integration Testing). Bảng 3.F tổng hợp kiến trúc các phân lớp kiểm thử trong kho mã nguồn."
    )
    b.add_table(
        headers=[
            "Phân lớp kiểm thử",
            "Tệp kiểm thử tiêu biểu (tests/)",
            "Phạm vi và các bất biến kỹ thuật được kiểm chứng",
        ],
        rows=[
            [
                "1. Kiểm thử Đơn vị & Luật trò chơi (Engine & Rule Oracle Tests)",
                "test_board.py, test_rules.py, test_game_env.py, test_w12_contract_audit.py",
                "Kiểm tra 4 hướng thắng (ngang, dọc, chéo chính, chéo phụ), luật chặn hai đầu bởi quân đối phương hoặc biên bàn cờ, chuỗi dài hơn 5 quân (overline 6, 7, 8), chuỗi đứt quãng (XXXX.X), ưu tiên thắng trước hòa ở nước thứ 121. Đối chiếu chéo RuleEngine với bộ kiểm tra chuỗi độc lập (Independent String Oracle) trên 3.000 bàn cờ ngẫu nhiên và đối chiếu kiểm tra cục bộ O(n) với quét toàn bàn O(n²) trên 300 ván ngẫu nhiên.",
            ],
            [
                "2. Kiểm thử Hợp đồng & Bất biến Tác tử (Agent Contract & Property Tests)",
                "test_agents_integration.py, test_random_ai.py, test_heuristic_ai.py, test_minimax_ai.py, test_mcts_ai.py, test_neural_ai.py",
                "Kiểm chứng 4 điều khoản hợp đồng W34-T01..T04 cho mọi tác tử: (T01) Ném RuntimeError khi gọi trên trạng thái đã kết thúc; (T02) Nước đi trả về luôn thuộc legal_actions(); (T03) Tuyệt đối không làm biến đổi trạng thái, mặt nạ hợp lệ, chuỗi hiển thị hay lịch sử undo của môi trường gốc; (T04) Tính tái lập tất định 100% khi chạy lại với cùng trạng thái, SearchBudget và seed.",
            ],
            [
                "3. Kiểm thử Thuật toán Tìm kiếm Chuyên sâu (Search Correctness Tests)",
                "test_minimax_ai.py, test_mcts_ai.py, test_mcts_strength_regressions.py",
                "Xác nhận tính tương đương quyết định 100% giữa Minimax thuần và cắt tỉa Alpha-Beta trên cùng độ sâu; kiểm tra tuân thủ giới hạn max_nodes và time_limit_ms; kiểm tra khả năng thắng ngay trong 1 nước và chặn bắt buộc trong 1 nước của Heuristic, Minimax, MCTS và NeuralAgent trên các thế cờ chiến thuật chuẩn.",
            ],
            [
                "4. Kiểm thử Đường ống Dữ liệu & Học sâu (ML & Data Pipeline Tests)",
                "test_data_pipeline.py, test_selfplay_generation.py, test_architectures.py, test_policy_training.py",
                "Kiểm tra phát lại (replay validation) 100% ván cờ từ bàn trống; đảm bảo giao tập game_id giữa train/val/test bằng 0; kiểm tra tính bất biến của phép biến đổi nhóm đối xứng D4 trên cả tensor trạng thái, mặt nạ hợp lệ và nhãn hành động; kiểm tra mặt nạ âm vô cùng trong mask_policy_logits và xác thực mã băm SHA-256 khi nạp checkpoint.",
            ],
            [
                "5. Kiểm thử Giải đấu, Phân tích & Giao diện UI (Tournament & UI Tests)",
                "test_tournament_runner.py, test_w78_ deliverables.py, test_ui_controller.py, test_app.py",
                "Kiểm tra luồng đấu vòng tròn đổi bên X/O cân bằng, cơ chế resume không trùng game_id từ tệp JSONL, bộ giám sát ngân sách BudgetEnforcer; kiểm tra 17 kịch bản tích hợp UI controller (Human vs Human, Human vs AI, AI vs AI, xử lý lỗi thiếu checkpoint và tô sáng chuỗi 5 quân chiến thắng).",
            ],
        ],
        caption_label="Bảng 3.F.",
        caption_text="Cấu trúc 5 phân lớp kiểm thử tự động đảm bảo chất lượng toàn hệ thống",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
        ],
    )
    b.add_paragraph(
        "Đặc biệt, phương pháp Kiểm thử đối chiếu tiên tri độc lập (Differential Oracle Testing) tại tests/test_w12_contract_audit.py "
        "đóng vai trò chốt chặn quan trọng cho RuleEngine: nhóm xây dựng một hàm kiểm tra độc lập hoàn toàn bằng phép khớp mẫu "
        "chuỗi ký tự (không dùng chung bất kỳ dòng mã chỉ số nào với RuleEngine) và chạy đối chiếu trên hàng nghìn ma trận "
        "bàn cờ sinh ngẫu nhiên ở nhiều mật độ quân khác nhau. Tương tự, bài kiểm thử chu trình tròn (Round-trip step/undo property) "
        "thực hiện ngẫu nhiên chuỗi bước đi rồi gọi undo() ngược về đầu ván, xác nhận mọi thuộc tính của môi trường đều khôi phục "
        "chính xác từng bit. Nhờ hệ thống kiểm thử này (đạt 1.866 bài kiểm thử vượt qua với 0 lỗi tại thời điểm bàn giao), "
        "nhóm có cơ sở vững chắc rằng mọi số liệu thực nghiệm thu được ở Chương 4 phản ánh đúng bản chất thuật toán chứ không "
        "bị nhiễu bởi lỗi cài đặt."
    )


def fill_section_4_3_minimax_results(doc: docx.Document) -> None:
    p_43 = find_paragraph(doc, "4.3. Kết quả Minimax/Alpha-Beta", "Heading 2")
    b_43 = SectionBuilder(doc, p_43)
    b_43.add_paragraph(
        "Mục này đánh giá thực nghiệm tác tử Minimax/Alpha-Beta trên bốn khía cạnh: ảnh hưởng của độ sâu tìm kiếm (max_depth), "
        "hiệu quả giảm không gian trạng thái của cắt tỉa Alpha-Beta (thí nghiệm Ablation A1), tác động của sắp xếp thứ tự "
        "nước đi (Move Ordering) và sự đánh đổi tổng thể giữa chi phí tính toán với chất lượng quyết định."
    )

    # 4.3.1
    p_431 = find_paragraph(doc, "4.3.1. Ảnh hưởng của độ sâu", "Heading 3")
    b = SectionBuilder(doc, p_431)
    b.add_paragraph(
        "Để quan sát sự thay đổi về số lượng nút mở rộng, độ trễ suy luận và chất lượng nước đi khi tăng độ sâu tìm kiếm, "
        "nhóm thực thi kịch bản đo chuẩn benchmarks/bench_minimax.py (bật Alpha-Beta, bật Move Ordering, bán kính ứng viên "
        "r = 2, không giới hạn thời gian) ở các mức độ sâu d ∈ {1, 2, 3, 4} trên 5 thế cờ chuẩn của configs/benchmark.json "
        "và thế cờ chiến thuật block_x_gap. Kết quả chi tiết được tổng hợp tại Bảng 4.1."
    )
    b.add_table(
        headers=[
            "Kịch bản bàn cờ",
            "Độ sâu d = 1 (Nút / Thời gian / Nước đi)",
            "Độ sâu d = 2 (Nút / Thời gian / Nước đi)",
            "Độ sâu d = 3 (Nút / Thời gian / Nước đi)",
            "Độ sâu d = 4 (Nút / Thời gian / Nước đi)",
        ],
        rows=[
            [
                "Empty Board (Bàn trống, ply 0)",
                "1 nút / 0,18 ms / (5, 5)",
                "26 nút / 4,60 ms / (5, 5)",
                "80 nút / 14,50 ms / (5, 5)",
                "569 nút / 111,80 ms / (5, 5)",
            ],
            [
                "Two-Step Opening (Khai cuộc 2 nước)",
                "31 nút / 3,90 ms / (4, 6)",
                "65 nút / 11,40 ms / (4, 6)",
                "604 nút / 101,80 ms / (6, 4)",
                "1.320 nút / 241,60 ms / (4, 6)",
            ],
            [
                "Immediate Win (Thắng trong 1 nước)",
                "1 nút / 0,25 ms / (5, 7)",
                "1 nút / 0,28 ms / (5, 7)",
                "1 nút / 0,33 ms / (5, 7)",
                "1 nút / 0,32 ms / (5, 7)",
            ],
            [
                "Immediate Block (Chặn bắt buộc 1 nước)",
                "39 nút / 6,10 ms / (2, 7)",
                "117 nút / 26,80 ms / (2, 7)",
                "637 nút / 151,10 ms / (2, 7)",
                "2.502 nút / 633,00 ms / (2, 7)",
            ],
            [
                "Midgame Mixed (Trung cuộc hỗn hợp)",
                "26 nút / 4,20 ms / (6, 5)",
                "38 nút / 8,30 ms / (6, 5)",
                "148 nút / 27,20 ms / (5, 4)",
                "631 nút / 128,40 ms / (5, 4)",
            ],
            [
                "block_x_gap (Chặn khe hở chiến thuật)",
                "46 nút / 8,90 ms / (1, 2)",
                "216 nút / 41,38 ms / (4, 5)",
                "494 nút / 87,90 ms / (4, 5)",
                "3.140 nút / 612,50 ms / (4, 5)",
            ],
        ],
        caption_label="Bảng 4.1.",
        caption_text="Sự biến thiên số nút mở rộng, độ trễ suy luận và nước đi được chọn của Minimax/Alpha-Beta theo độ sâu d = 1..4",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )
    b.add_paragraph(
        "Số liệu thực nghiệm tại Bảng 4.1 làm nổi bật ba đặc trưng quan trọng của độ sâu tìm kiếm. Thứ nhất, ở kịch bản "
        "Immediate Win (đã có 4 quân liên tiếp mở đầu), cơ chế phát hiện thắng cưỡng bức sớm (forced win early exit khi "
        "value > 500.000,0) trong vòng lặp Iterative Deepening giúp tác tử dừng ngay sau nút đầu tiên (1 nút, ~0,3 ms) "
        "dù ngân sách độ sâu được đặt lên 3 hay 4. Thứ hai, sự khác biệt chất lượng chiến thuật thể hiện rõ nét nhất khi "
        "chuyển từ độ sâu lẻ (d = 1) sang độ sâu chẵn (d = 2) trên kịch bản block_x_gap và từ d = 2 lên d = 3 trên kịch bản "
        "Midgame Mixed: tại block_x_gap, tìm kiếm độ sâu 1 chỉ nhìn nước đi của bản thân nên chọn (1, 2) để mở rộng thế công "
        "cục bộ (điểm +1.299,89) mà bỏ sót mối đe dọa phản công nguy hiểm của đối phương; ngay khi tăng lên d = 2, cây tìm kiếm "
        "nhìn thấy nước trả đũa của đối phương ở tầng minimizing (điểm giảm xuống -254,84 nếu không chặn) và lập tức chuyển "
        "quyết định sang nước chặn chính xác tại (4, 5). Tương tự, ở thế cờ Midgame Mixed, độ sâu d = 3 và d = 4 phát hiện "
        "chuỗi tấn công liên hoàn tại (5, 4) với điểm lượng giá +1.890,10 vượt trội hơn nước đi (6, 5) ở d = 2 (+913,18). "
        "Thứ ba, về mặt chi phí, mỗi khi tăng thêm 1 tầng độ sâu trên bàn cờ trung cuộc, số nút mở rộng và thời gian suy luận "
        "tăng xấp xỉ từ 3 đến 6 lần (ngay cả khi đã có cắt tỉa Alpha-Beta), đẩy độ trễ ở d = 4 lên mức 240 – 630 ms/nước."
    )

    # 4.3.2
    p_432 = find_paragraph(doc, "4.3.2. Alpha-Beta bật/tắt", "Heading 3")
    b = SectionBuilder(doc, p_432)
    b.add_paragraph(
        "Để định lượng chính xác hiệu quả của kỹ thuật cắt tỉa Alpha-Beta, thí nghiệm Ablation A1 trong gói thực nghiệm W78 "
        "(tái lập qua scripts/analyze_results_w78.py và lưu tại results/w78/tables/ablation_alpha_beta.csv) tiến hành so sánh "
        "trực tiếp hai cấu hình alpha_beta = False (Minimax vét cạn trong tập ứng viên) và alpha_beta = True tại cùng độ sâu "
        "max_depth = 2, bán kính lân cận neighbor_radius = 1 và bật move_ordering = True. Mỗi trạng thái trong 4 kịch bản "
        "được chạy lặp lại 30 lần ứng với 30 hạt giống cố định (tổng cộng 240 lượt ra quyết định). Kết quả được trình bày "
        "trong Bảng 4.2 và minh họa trực quan tại Hình 4.1."
    )
    b.add_table(
        headers=[
            "Trạng thái bàn cờ (Kịch bản A1)",
            "Cấu hình Alpha-Beta",
            "Nước đi chọn / Điểm lượng giá",
            "Số nút duyệt trung bình",
            "Tỷ lệ giảm số nút (%)",
            "Độ trễ mean / p95 (ms)",
        ],
        rows=[
            [
                "opening_x (Khai cuộc ít quân)",
                "Tắt (OFF)",
                "(4, 5) / +117,89",
                "10,0",
                "—",
                "0,54 / 0,80",
            ],
            [
                "opening_x (Khai cuộc ít quân)",
                "Bật (ON)",
                "(4, 5) / +117,89",
                "10,0",
                "0,00%",
                "0,64 / 0,81",
            ],
            [
                "midgame_x (Trung cuộc phức tạp)",
                "Tắt (OFF)",
                "(1, 4) / +1.298,87",
                "1.336,0",
                "—",
                "95,84 / 119,82",
            ],
            [
                "midgame_x (Trung cuộc phức tạp)",
                "Bật (ON)",
                "(1, 4) / +1.298,87",
                "146,0",
                "89,07%",
                "23,14 / 26,45",
            ],
            [
                "block_x_gap (Chặn đe dọa khe hở)",
                "Tắt (OFF)",
                "(4, 5) / -254,84",
                "2.076,0",
                "—",
                "159,41 / 211,61",
            ],
            [
                "block_x_gap (Chặn đe dọa khe hở)",
                "Bật (ON)",
                "(4, 5) / -254,84",
                "216,0",
                "89,60%",
                "41,38 / 108,27",
            ],
            [
                "near_full_x (Cuối ván gần đầy bàn)",
                "Tắt (OFF)",
                "(10, 4) / -999.999,00",
                "12,0",
                "—",
                "4,45 / 5,19",
            ],
            [
                "near_full_x (Cuối ván gần đầy bàn)",
                "Bật (ON)",
                "(10, 4) / -999.999,00",
                "11,0",
                "8,33%",
                "4,31 / 5,02",
            ],
        ],
        caption_label="Bảng 4.2.",
        caption_text="Kết quả thí nghiệm Ablation A1 so sánh Minimax khi tắt và bật cắt tỉa Alpha-Beta (30 hạt giống/trạng thái, d = 2)",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )
    b.add_figure(
        image_path=IMG_DIR / "22_ABLATION_ALPHA_BETA.png",
        caption_label="Hình 4.1.",
        caption_text="Biểu đồ so sánh độ trễ suy luận (trái) và số nút mở rộng (phải) khi tắt và bật Alpha-Beta trong thí nghiệm Ablation A1",
        width_cm=16.0,
    )
    b.add_paragraph(
        "Kết quả thực nghiệm ở Bảng 4.2 và Hình 4.1 khẳng định hai kết luận định lượng rõ ràng. Trước hết, trên cả 4 kịch bản "
        "(240/240 lần chạy), cấu hình bật Alpha-Beta trả về chính xác cùng một tọa độ nước đi và cùng một điểm số lượng giá "
        "tới từng chữ số thập phân so với Minimax không cắt tỉa; điều này chứng minh thực nghiệm rằng cài đặt Alpha-Beta "
        "bảo toàn tuyệt đối tính tối ưu của quyết định Minimax (exact decision equivalence). Tiếp theo, hiệu quả cắt tỉa "
        "phát huy mạnh mẽ nhất ở giai đoạn trung cuộc khi hệ số phân nhánh cao: tại midgame_x, số nút mở rộng giảm từ "
        "1.336 xuống chỉ còn 146 nút (tiết kiệm 89,07% số nút, rút ngắn thời gian trung bình 4,14 lần từ 95,84 ms xuống "
        "23,14 ms); tại block_x_gap, số nút giảm từ 2.076 xuống 216 nút (tiết kiệm 89,60% số nút, rút ngắn thời gian 3,85 lần "
        "từ 159,41 ms xuống 41,38 ms). Ở kịch bản opening_x (chỉ mới có 1 quân cờ nên chỉ duyệt 1 tầng lân cận 10 nút) và "
        "near_full_x (chỉ còn 4 ô trống cuối bàn cờ), không gian trạng thái vốn đã rất nhỏ nên độ chênh lệch không đáng kể."
    )

    # 4.3.3
    p_433 = find_paragraph(doc, "4.3.3. Move ordering bật/tắt", "Heading 3")
    b = SectionBuilder(doc, p_433)
    b.add_paragraph(
        "Trong lý thuyết tìm kiếm đối kháng, hiệu quả của cắt tỉa Alpha-Beta phụ thuộc chặt chẽ vào thứ tự duyệt các nhánh con: "
        "nếu nhánh tốt nhất được duyệt đầu tiên, cửa sổ [α, β] sẽ thu hẹp cực nhanh và cắt bỏ phần lớn các nhánh còn lại "
        "(tiệm cận giới hạn lý thuyết O(b^(d/2))). Để tách bạch đóng góp của bộ sắp xếp nước đi dựa trên action_priority "
        "(Move Ordering), nhóm tiến hành thí nghiệm đối chiếu 3 tổ hợp cấu hình trên hai thế cờ trung cuộc phức tạp nhất "
        "(midgame_x và block_x_gap) ở cả độ sâu d = 2 và d = 3: (1) Tắt cả Alpha-Beta lẫn Move Ordering; (2) Bật Alpha-Beta "
        "nhưng tắt Move Ordering (duyệt theo thứ tự hàng – cột tự nhiên); và (3) Bật đồng thời cả Alpha-Beta và Move Ordering. "
        "Số liệu đo được trình bày tại Bảng 4.3."
    )
    b.add_table(
        headers=[
            "Thế cờ & Độ sâu",
            "Tổ hợp cấu hình (Alpha-Beta / Move Ordering)",
            "Nước đi chọn / Điểm số",
            "Số nút mở rộng (nodes)",
            "Tỷ lệ giảm nút so với Minimax thuần",
            "Thời gian thực thi (ms)",
        ],
        rows=[
            [
                "midgame_x (Độ sâu d = 2)",
                "ab = False, move_ordering = False",
                "(1, 4) / +1.298,87",
                "1.336",
                "0,00% (Mốc cơ sở)",
                "83,20",
            ],
            [
                "midgame_x (Độ sâu d = 2)",
                "ab = True, move_ordering = False",
                "(1, 4) / +1.298,87",
                "473",
                "-64,60%",
                "29,70",
            ],
            [
                "midgame_x (Độ sâu d = 2)",
                "ab = True, move_ordering = True",
                "(1, 4) / +1.298,87",
                "146",
                "-89,07% (-69,13% so với tắt MO)",
                "23,14",
            ],
            [
                "block_x_gap (Độ sâu d = 2)",
                "ab = False, move_ordering = False",
                "(4, 5) / -254,84",
                "2.076",
                "0,00% (Mốc cơ sở)",
                "127,40",
            ],
            [
                "block_x_gap (Độ sâu d = 2)",
                "ab = True, move_ordering = False",
                "(4, 5) / -254,84",
                "1.229",
                "-40,80%",
                "73,80",
            ],
            [
                "block_x_gap (Độ sâu d = 2)",
                "ab = True, move_ordering = True",
                "(4, 5) / -254,84",
                "216",
                "-89,60% (-82,42% so với tắt MO)",
                "41,38",
            ],
            [
                "midgame_x (Độ sâu d = 3)",
                "ab = False, move_ordering = False",
                "(2, 4) / +1.500,10",
                "50.011",
                "0,00% (Mốc cơ sở)",
                "3.142,00",
            ],
            [
                "midgame_x (Độ sâu d = 3)",
                "ab = True, move_ordering = False",
                "(2, 4) / +1.500,10",
                "7.745",
                "-84,51%",
                "485,60",
            ],
            [
                "midgame_x (Độ sâu d = 3)",
                "ab = True, move_ordering = True",
                "(2, 4) / +1.500,10",
                "1.885",
                "-96,23% (-75,66% so với tắt MO)",
                "270,50",
            ],
            [
                "block_x_gap (Độ sâu d = 3)",
                "ab = False, move_ordering = False",
                "(4, 5) / +1.219,09",
                "94.319",
                "0,00% (Mốc cơ sở)",
                "5.673,00",
            ],
            [
                "block_x_gap (Độ sâu d = 3)",
                "ab = True, move_ordering = False",
                "(4, 5) / +1.219,09",
                "19.888",
                "-78,91%",
                "1.209,00",
            ],
            [
                "block_x_gap (Độ sâu d = 3)",
                "ab = True, move_ordering = True",
                "(4, 5) / +1.219,09",
                "494",
                "-99,48% (-97,52% so với tắt MO)",
                "87,90",
            ],
        ],
        caption_label="Bảng 4.3.",
        caption_text="Phân tích tác động cộng hưởng giữa cắt tỉa Alpha-Beta và sắp xếp nước đi (Move Ordering) ở độ sâu d = 2 và d = 3",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )
    b.add_paragraph(
        "Số liệu tại Bảng 4.3 cho thấy rõ bản chất cộng hưởng giữa hai kỹ thuật. Nếu tắt Alpha-Beta (ab = False), việc bật "
        "Move Ordering không làm giảm bất kỳ nút nào (vẫn duyệt đủ 1.336 và 2.076 nút ở d = 2) mà còn làm tăng nhẹ thời gian "
        "do chi phí tính điểm ưu tiên để sắp xếp mảng ứng viên tại mỗi nút. Ngược lại, khi kết hợp với Alpha-Beta, Move Ordering "
        "cắt giảm thêm từ 69,13% đến 82,42% số nút còn lại ở độ sâu d = 2 so với khi chỉ bật Alpha-Beta đơn thuần. Đặc biệt "
        "ở độ sâu d = 3 trên thế cờ chiến thuật block_x_gap, nhờ hàm action_priority nhận diện ngay nước chặn khẩn cấp (4, 5) "
        "(điểm ưu tiên 100.000) và đẩy lên nhánh đầu tiên, cây tìm kiếm cắt tỉa tới 97,52% số nút so với Alpha-Beta không sắp xếp "
        "(từ 19.888 nút xuống chỉ còn 494 nút) và giảm 99,48% so với Minimax thuần (từ 94.319 nút xuống 494 nút, rút ngắn "
        "thời gian từ 5,67 giây xuống chỉ còn 87,90 ms)."
    )

    # 4.3.4
    p_434 = find_paragraph(doc, "4.3.4. Số node, thời gian và chất lượng nước đi", "Heading 3")
    b = SectionBuilder(doc, p_434)
    b.add_paragraph(
        "Tổng hợp từ các thực nghiệm ở Mục 4.3.1 đến 4.3.3, bài toán lựa chọn cấu hình Minimax cho giải đấu chính thức "
        "và giao diện tương tác thực chất là bài toán cân bằng ba chiều giữa số nút mở rộng, độ trễ phản hồi và chất lượng "
        "chiến thuật:"
    )
    b.add_bullet(
        "Ở độ sâu d = 1",
        "Chi phí tính toán cực thấp (< 10 ms/nước), nhưng tác tử hoàn toàn tương đương với tìm kiếm tham lam một bước, "
        "không nhìn thấy nước phản đòn của đối thủ ở lượt kế tiếp nên dễ mắc bẫy chiến thuật kép.",
    )
    b.add_bullet(
        "Ở độ sâu d = 2 (kết hợp Alpha-Beta, Move Ordering và bán kính ứng viên r = 2)",
        "Tác tử hoàn thành trọn vẹn một chu kỳ đi – đáp (Max – Min), phát hiện và xử lý chính xác các đe dọa tạo Tứ mở / "
        "Tam mở của đối phương. Trong toàn bộ 400 ván đấu của giải đấu vòng tròn W78 (11.797 nước đi), cấu hình này mở rộng "
        "trung bình 55,61 nút/nước với độ trễ trung bình 37,20 ms và phân vị thứ 95 (p95) đạt 66,48 ms — hoàn toàn nằm dưới "
        "ngưỡng ngân sách công bằng 150 ms/nước của profile FAIR với 0 lần vi phạm (budget_violations = 0).",
    )
    b.add_bullet(
        "Ở độ sâu d ≥ 3",
        "Chất lượng nước đi trung cuộc được cải thiện ở các thế cờ phức tạp, nhưng ngay cả khi đã bật đầy đủ Alpha-Beta và "
        "Move Ordering, độ trễ ở các thế cờ đông quân vẫn vọt lên ngưỡng 150 – 270 ms (d = 3) và > 600 ms (d = 4), vượt quá "
        "ngân sách 150 ms/nước của profile FAIR và gây hiện tượng cắt ngang vòng lặp Iterative Deepening.",
    )
    b.add_paragraph(
        "Do đó, cấu hình Minimax với max_depth = 2, alpha_beta = True, move_ordering = True và neighbor_radius = 2 là "
        "điểm cân bằng hợp lý nhất để đại diện cho nhánh tìm kiếm cây cổ điển trong giải đấu chuẩn W78."
    )


def fill_section_4_4_mcts_results(doc: docx.Document) -> None:
    p_44 = find_paragraph(doc, "4.4. Kết quả MCTS", "Heading 2")
    b_44 = SectionBuilder(doc, p_44)
    b_44.add_paragraph(
        "Khác với Minimax tìm kiếm theo tầng độ sâu toàn cục, MCTS phân bổ ngân sách tính toán không đồng đều theo xác suất "
        "thống kê của từng nhánh. Mục này phân tích kết quả thực nghiệm của MCTS theo quy mô số lượt mô phỏng (thí nghiệm "
        "Ablation A2 và cấu hình MCTS có hướng dẫn), độ nhạy và tính ổn định theo hạt giống ngẫu nhiên (seed sensitivity), "
        "cùng mối quan hệ giữa thời gian suy nghĩ và chất lượng nước đi."
    )

    # 4.4.1
    p_441 = find_paragraph(doc, "4.4.1. Ảnh hưởng của số simulation", "Heading 3")
    b = SectionBuilder(doc, p_441)
    b.add_paragraph(
        "Thí nghiệm Ablation A2 trong gói đánh giá W78 (lưu tại results/w78/tables/ablation_mcts_simulations.csv) khảo sát "
        "sự thay đổi năng lực thi đấu của MCTS khi tăng dần ngân sách mô phỏng qua ba mức: 100, 400 và 1.000 simulations/nước "
        "khi đối đầu trực tiếp với tác tử chuẩn HeuristicAgent. Tại mỗi mức ngân sách, hệ thống chạy 30 hạt giống ghép cặp "
        "đổi bên X/O (tổng cộng 60 ván/mức = 180 ván toàn thí nghiệm). Để quan sát thuần túy hiệu ứng hội tụ theo số lượng "
        "simulation mà không bị che lấp bởi heuristic chọn nhánh quá mạnh ở 1 bước, cấu hình A2 sử dụng chính sách rollout "
        "ngẫu nhiên độ sâu ngắn (rollout_horizon = 4) kết hợp lượng giá lá bằng mẫu hình và kiểm tra thắng/chặn tức thời. "
        "Số liệu chi tiết của thí nghiệm A2 được trình bày tại Bảng 4.4 và biểu diễn trên Hình 4.2."
    )
    b.add_table(
        headers=[
            "Ngân sách (simulations / nước)",
            "Thắng / Hòa / Thua (trên 60 ván)",
            "Score Rate tổng (%) [Wilson 95% CI]",
            "Score Rate khi cầm X / cầm O (%)",
            "Tổng số nước đi / Số lần can thiệp chiến thuật",
            "Độ trễ mean / p95 (ms/nước)",
        ],
        rows=[
            [
                "100 simulations",
                "0 / 0 / 60",
                "0,00% [0,00% – 6,00%]",
                "0,00% / 0,00%",
                "364 nước / 18 lần",
                "26,11 / 40,46",
            ],
            [
                "400 simulations",
                "4 / 1 / 55",
                "7,50% [2,96% – 16,67%]",
                "6,67% / 8,33%",
                "539 nước / 51 lần",
                "128,83 / 205,41",
            ],
            [
                "1.000 simulations",
                "5 / 1 / 54",
                "9,17% [3,99% – 18,76%]",
                "15,00% / 3,33%",
                "696 nước / 66 lần",
                "345,05 / 528,13",
            ],
        ],
        caption_label="Bảng 4.4.",
        caption_text="Kết quả thí nghiệm Ablation A2 của MCTS trước HeuristicAgent ở các mức 100, 400 và 1.000 simulations (60 ván/mức)",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )
    b.add_figure(
        image_path=IMG_DIR / "23_ABLATION_MCTS_SIMULATIONS.png",
        caption_label="Hình 4.2.",
        caption_text="Biểu đồ tỷ lệ điểm (Score Rate) và độ trễ trung bình/p95 trên một nước đi của MCTS khi tăng ngân sách từ 100 lên 1.000 simulations",
        width_cm=16.0,
    )
    b.add_paragraph(
        "Số liệu từ Bảng 4.4 và Hình 4.2 cho thấy một xu hướng nhất quán nhưng cũng chỉ ra giới hạn quan trọng của MCTS "
        "khi dùng rollout ngẫu nhiên trên bàn cờ Caro 11 × 11:"
    )
    b.add_bullet(
        "Xu hướng cải thiện đơn điệu theo ngân sách mô phỏng",
        "Khi ngân sách tăng từ 100 lên 400 và 1.000 simulations, tỷ lệ điểm (score rate) của MCTS tăng tương ứng từ 0,00% "
        "lên 7,50% (4 thắng, 1 hòa; chênh lệch ghép cặp Δ = +0,0750) và 9,17% (5 thắng, 1 hòa; Δ = +0,0917). Đồng thời, "
        "tổng số nước đi trụ vững được trong 60 ván tăng casi gấp đôi từ 364 nước (trung bình 6,07 nước/ván của MCTS) lên "
        "539 nước (ở 400 sims) và 696 nước (ở 1.000 sims), kéo theo số lần kích hoạt thành công đòn chiến thuật trực tiếp "
        "(tactical overrides) tăng từ 18 lên 51 và 66 lần.",
    )
    b.add_bullet(
        "Vai trò quyết định của cơ chế hướng dẫn miền (Guided Rollout & Progressive Widening)",
        "Mặc dù tăng số lượng simulation thuần túy giúp cải thiện kết quả, ở mức 1.000 simulations với rollout ngẫu nhiên "
        "MCTS vẫn thua 54/60 ván và tốn tới 345,05 ms/nước. Nguyên nhân là trên bàn cờ Caro, một chuỗi 4 nước đi ngẫu nhiên "
        "trong pha rollout hiếm khi phản ánh đúng trình độ phòng thủ chặt chẽ của đối phương, dẫn đến nhiễu phương sai lớn "
        "trong ước lượng Q(v). Chính phát hiện này đã thúc đẩy nhóm tích hợp cơ chế mở rộng lũy tiến có hạt giống ưu tiên "
        "(heuristic_seeded progressive widening) kết hợp chính sách rollout epsilon-heuristic (ε = 0,15, độ sâu 8) cho cấu hình "
        "MCTS chính thức của giải đấu. Với cấu hình có hướng dẫn này, ngay tại ngân sách rất nhỏ (8 simulations/nước trong "
        "giải đấu W78), MCTS đã đạt tỷ lệ điểm 74,50% trước Heuristic (65 thắng, 19 hòa, 16 thua) và khi tăng lên 64 simulations "
        "(theo báo cáo MCTS_Strength_Improvement_Report.md), tỷ lệ điểm đạt tới 85,00% trước Heuristic (15 thắng, 4 hòa, 1 thua) "
        "và 75,00% trước Minimax độ sâu 2.",
    )

    # 4.4.2
    p_442 = find_paragraph(doc, "4.4.2. Độ ổn định theo seed", "Heading 3")
    b = SectionBuilder(doc, p_442)
    b.add_paragraph(
        "Vì MCTS là giải thuật duy nhất trong nhóm tác tử tìm kiếm nâng cao có thành phần ngẫu nhiên (trong pha chọn nhánh "
        "khám phá và pha rollout ε-greedy), việc đánh giá độ ổn định theo hạt giống ngẫu nhiên (seed stability) được thực hiện "
        "trên hai cấp độ: (1) Tính tái lập tất định khi cố định hạt giống (Fixed-Seed Reproducibility) và (2) Độ biến thiên "
        "kết quả giữa các hạt giống khác nhau (Cross-Seed Variance)."
    )
    b.add_paragraph(
        "Ở cấp độ thứ nhất, kiểm thử hồi quy với các hạt giống chuẩn (seed ∈ {11, 22, 33}) xác nhận rằng khi giữ nguyên "
        "trạng thái bàn cờ và truyền cùng SearchBudget(seed=s), MCTSAgent luôn sinh ra đúng một chuỗi nút mở rộng, cùng số "
        "lượt thăm tại từng nút con và trả về chính xác cùng một nước đi. Điều này chứng minh mọi nguồn ngẫu nhiên trong "
        "MCTS đã được cô lập hoàn toàn vào đối tượng random.Random(budget.seed) cục bộ."
    )
    b.add_paragraph(
        "Ở cấp độ thứ hai, khi thay đổi hạt giống giữa các cặp ván đấu (paired seeds), MCTS tạo ra sự đa dạng quỹ đạo thực sự "
        "(100% số ván có chuỗi nước đi độc lập: 60/60 quỹ đạo duy nhất ở cả ba mức 100, 400 và 1.000 simulations trong thí nghiệm A2), "
        "khác hẳn với các cặp đấu giữa hai tác tử tất định (như Heuristic đấu với Minimax hay Neural) vốn lặp lại cùng một "
        "biên bản ván cờ khi đổi seed. Bảng 4.5 thống kê độ lệch chuẩn của điểm số theo nhóm hạt giống (seed_score_std) "
        "trong cả thí nghiệm A2 và giải đấu chính thức W78."
    )
    b.add_table(
        headers=[
            "Thí nghiệm & Cặp đối đầu",
            "Số nhóm hạt giống ghép cặp (Số ván)",
            "Số quỹ đạo ván đấu duy nhất",
            "Điểm trung bình của MCTS (Mean Score)",
            "Độ lệch chuẩn theo hạt giống (seed_score_std)",
            "Khoảng biến thiên điểm giữa các seed [Min – Max]",
        ],
        rows=[
            [
                "Ablation A2: MCTS (100 sims) vs Heuristic",
                "30 seed (60 ván)",
                "60 / 60 (100%)",
                "0,0000",
                "0,0000",
                "[0,00 – 0,00] (Thua cả 30 nhóm seed)",
            ],
            [
                "Ablation A2: MCTS (400 sims) vs Heuristic",
                "30 seed (60 ván)",
                "60 / 60 (100%)",
                "0,0750",
                "0,1726",
                "[0,00 – 0,50] (Thắng ở 4 seed, hòa 1 seed)",
            ],
            [
                "Ablation A2: MCTS (1.000 sims) vs Heuristic",
                "30 seed (60 ván)",
                "60 / 60 (100%)",
                "0,0917",
                "0,2281",
                "[0,00 – 1,00] (Seed 293621627 thắng cả X và O)",
            ],
            [
                "Giải đấu W78: MCTS (8 sims guided) vs Random",
                "50 seed (100 ván)",
                "100 / 100 (100%)",
                "0,9900",
                "0,0707",
                "[0,50 – 1,00] (Thắng 99/100 ván)",
            ],
            [
                "Giải đấu W78: MCTS (8 sims guided) vs Heuristic",
                "50 seed (100 ván)",
                "100 / 100 (100%)",
                "0,7450",
                "0,2530",
                "[0,00 – 1,00] (Ổn định ở ưu thế thắng)",
            ],
            [
                "Giải đấu W78: MCTS (8 sims guided) vs Minimax-D2",
                "50 seed (100 ván)",
                "100 / 100 (100%)",
                "0,8800",
                "0,2156",
                "[0,50 – 1,00] (Không thua cả 2 lượt ở bất kỳ seed nào)",
            ],
            [
                "Giải đấu W78: MCTS (8 sims guided) vs NeuralAgent",
                "50 seed (100 ván)",
                "100 / 100 (100%)",
                "0,6350",
                "0,2576",
                "[0,00 – 1,00] (Cạnh tranh quyết liệt nhất)",
            ],
        ],
        caption_label="Bảng 4.5.",
        caption_text="Phân tích độ đa dạng quỹ đạo và độ nhạy theo hạt giống (seed sensitivity) của MCTS qua các kịch bản thực nghiệm",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
        ],
    )
    b.add_paragraph(
        "Số liệu ở Bảng 4.5 cho thấy trong thí nghiệm A2, khi ngân sách tăng lên 400 và 1.000 simulations, độ lệch chuẩn "
        "theo seed tăng từ 0,0000 lên 0,1726 và 0,2281 do xuất hiện các hạt giống mà đường rollout khám phá trúng chuỗi "
        "phản công thắng lợi (tiêu biểu là hạt giống 293621627 ở mức 1.000 simulations giúp MCTS thắng tuyệt đối cả 2 ván "
        "khi cầm X lẫn khi cầm O, đạt điểm cặp 1,00). Trong giải đấu chính thức W78 (50 cặp hạt giống cho mỗi đối thủ), "
        "cấu hình MCTS 8 simulations có hướng dẫn duy trì điểm trung bình rất cao (từ 0,6350 đến 0,9900) với độ lệch chuẩn "
        "giữa các seed nằm trong khoảng 0,0707 – 0,2576, chứng tỏ ưu thế của MCTS trước cả 4 đối thủ là bền vững trên nhiều "
        "quỹ đạo ngẫu nhiên khác nhau chứ không phải kết quả may mắn của một vài hạt giống cá biệt."
    )

    # 4.4.3
    p_443 = find_paragraph(doc, "4.4.3. Thời gian và chất lượng nước đi", "Heading 3")
    b = SectionBuilder(doc, p_443)
    b.add_paragraph(
        "Xét về mối quan hệ giữa thời gian tính toán và chất lượng nước đi, chi phí mỗi nước của MCTS tăng tuyến tính "
        "theo số lượng simulation thực thi: trong thí nghiệm A2, thời gian trung bình trên một nước đi tăng từ 26,11 ms "
        "(p95 = 40,46 ms) ở 100 simulations lên 128,83 ms (p95 = 205,41 ms) ở 400 simulations và 345,05 ms (p95 = 528,13 ms) "
        "ở 1.000 simulations (tốc độ trung bình khoảng 0,26 – 0,34 ms cho một lượt mô phỏng sâu 4 bước kèm lượng giá lá). "
        "Trong khi đó, ở cấu hình MCTS có hướng dẫn dùng trong giải đấu chính (8 simulations/nước, rollout ε-heuristic sâu 8 bước), "
        "nhờ cơ chế tactical_precheck trả về ngay các nước thắng/chặn hiển nhiên với 0 simulation, số lượt mô phỏng trung bình "
        "thực tế trên toàn giải đấu chỉ là 6,93 simulations/nước và mở rộng trung bình 3,30 nút cây/nước. Nhờ vậy, độ trễ "
        "trung bình chỉ tốn 30,79 ms/nước (p95 = 50,24 ms ở profile DEFAULT và 50,05 ms ở profile FAIR), nhanh hơn cả "
        "Minimax độ sâu 2 (37,20 ms trung bình, p95 = 66,48 ms) nhưng lại đạt tỷ lệ thắng chung cuộc cao nhất giải đấu (81,25%)."
    )
    b.add_paragraph(
        "Về mặt chất lượng chiến thuật, sự kết hợp giữa kiểm tra tiền chiến thuật (tactical precheck) ở nút gốc và tích lũy "
        "giá trị thống kê UCT qua các lượt rollout có hướng dẫn giúp MCTS vừa không bao giờ bỏ sót các đòn thắng/chặn "
        "1 nước, vừa đánh giá được xác suất thắng dài hạn của các thế cờ mở đa hướng (như tạo đồng thời hai đường Tam mở "
        "giao nhau tại các ván thắng điển hình A2-n1000-s5-side1 ở ply 21 và A2-n1000-s5-side-1 ở ply 18). Chỉ khi ngân sách "
        "mô phỏng quá thấp so với độ phức tạp của bàn cờ và tắt hướng dẫn heuristic (như cấu hình 100 simulations ngẫu nhiên "
        "trong A2), MCTS mới bị suy giảm chất lượng do các lượt rollout ngẫu nhiên không kịp hội tụ trước các đòn tấn công "
        "dồn dập của đối phương."
    )


def fill_section_4_5_learned_agent_results(doc: docx.Document) -> None:
    p_45 = find_paragraph(doc, "4.5. Kết quả tác tử học được", "Heading 2")
    b = SectionBuilder(doc, p_45)
    b.add_paragraph(
        "Mục này trình bày toàn bộ kết quả thực nghiệm của tác tử học sâu NeuralAgent (PolicyNet 768.537 tham số), bao gồm: "
        "kết quả huấn luyện thực tế qua các thế hệ dữ liệu trên GPU, phân tích đường cong học tập và độ chính xác dự đoán "
        "Top-1/Top-3 qua 10 epoch, kết quả kiểm thử năng lực chiến thuật cùng thành tích đối đầu trực tiếp trên quy mô "
        "1.998 ván đấu và chi phí suy luận thực tế."
    )

    # 4.5.1
    b.add_subheading("4.5.1. Thiết lập huấn luyện thực tế và so sánh các phiên bản mô hình", level=3)
    b.add_paragraph(
        "Trong quá trình phát triển từ tuần 6 đến tuần 8, nhóm đã huấn luyện và đánh giá hai phiên bản mô hình chính thức "
        "trên hạ tầng GPU Google Colab (thiết bị cuda, hạt giống cố định seed = 20261109, trình tối ưu hóa AdamW với "
        "lr = 10⁻³, weight_decay = 10⁻⁴, batch_size = 256, patience = 5): mô hình Policy v2 (huấn luyện trên bộ dữ liệu "
        "cân bằng cứng 3 giáo viên dataset-v2) và mô hình Policy v5 (huấn luyện trên bộ dữ liệu cô lập quỹ đạo D4 giữ phân phối "
        "giáo viên tự nhiên dataset-v5). Bảng 4.6 đối chiếu trực tiếp thông số huấn luyện và chỉ số kiểm thử ngoại vi (held-out "
        "test set) của hai phiên bản này."
    )
    b.add_table(
        headers=[
            "Chỉ số / Thông số kỹ thuật",
            "Mô hình Policy v2 (policy-v2-mcts-strength8-colab)",
            "Mô hình Policy v5 — Chính thức (policy-v5-natural-teachers-colab)",
        ],
        rows=[
            [
                "Bộ dữ liệu huấn luyện",
                "dataset-v2 (227.376 mẫu train / 5.409 val / 5.139 test)",
                "dataset-v5 (309.136 mẫu train / 4.806 val / 4.689 test)",
            ],
            [
                "Tỷ lệ nhãn giáo viên trong tập Train",
                "Cân bằng cứng: Heuristic 33,3% – MCTS 33,3% – Minimax 33,3%",
                "Tự nhiên: MCTS 50,66% – Heuristic 24,82% – Minimax 24,52%",
            ],
            [
                "Số epoch hoàn thành / Epoch tốt nhất",
                "9 epoch (dừng sớm) / Best tại Epoch 4",
                "10 epoch (dừng sớm) / Best tại Epoch 5",
            ],
            [
                "Tổng thời gian huấn luyện trên GPU Colab",
                "454,38 giây (~50,5 giây/epoch)",
                "702,18 giây (~69,8 giây/epoch)",
            ],
            [
                "Hàm mất mát kiểm định tốt nhất (Best Val Loss)",
                "1,5352 (tại Epoch 4)",
                "1,5284 (tại Epoch 5)",
            ],
            [
                "Độ chính xác tập Validation (Val Top-1 / Top-3)",
                "48,36% / 79,57%",
                "49,60% / 79,86% (đạt đỉnh 50,42% ở Epoch 8)",
            ],
            [
                "Hàm mất mát tập Test độc lập (Test Loss)",
                "1,4425",
                "1,4421",
            ],
            [
                "Độ chính xác tập Test độc lập (Test Top-1 / Top-3)",
                "53,22% / 82,76%",
                "52,68% / 81,49%",
            ],
        ],
        caption_label="Bảng 4.6.",
        caption_text="So sánh thiết lập huấn luyện và các chỉ số trên tập kiểm định/kiểm thử giữa Policy v2 và Policy v5",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )

    # 4.5.2
    b.add_subheading("4.5.2. Đường cong học tập, độ chính xác và kiểm thử chiến thuật", level=3)
    b.add_paragraph(
        "Để phân tích chi tiết động học hội tụ của mạng PolicyNet trên bộ dữ liệu chính thức dataset-v5 (309.136 mẫu train), "
        "Bảng 4.7 trích xuất toàn bộ nhật ký huấn luyện qua 10 epoch từ tệp models/checkpoints/model-v5-natural-teachers-run2/history.csv, "
        "và Hình 4.3 biểu diễn trực quan đường cong hàm mất mát (Loss) cùng độ chính xác Top-1/Top-3."
    )
    b.add_table(
        headers=[
            "Epoch",
            "Train Loss",
            "Val Loss",
            "Train Top-1 (%)",
            "Val Top-1 (%)",
            "Train Top-3 (%)",
            "Val Top-3 (%)",
            "Thời gian (s)",
        ],
        rows=[
            ["1", "2,1702", "1,6568", "35,07%", "44,90%", "66,01%", "76,34%", "72,33"],
            ["2", "1,7206", "1,5681", "44,06%", "47,96%", "75,54%", "79,36%", "71,44"],
            ["3", "1,5809", "1,5311", "47,42%", "48,79%", "78,09%", "79,88%", "69,59"],
            ["4", "1,4776", "1,5463", "49,95%", "48,86%", "79,95%", "79,23%", "69,62"],
            ["5 (Best)", "1,3833", "1,5284", "52,55%", "49,60%", "81,69%", "79,86%", "69,48"],
            ["6", "1,2917", "1,5486", "55,09%", "49,54%", "83,27%", "79,23%", "69,20"],
            ["7", "1,2006", "1,6265", "57,66%", "48,96%", "84,92%", "78,26%", "69,13"],
            ["8", "1,1096", "1,6222", "60,64%", "50,42%", "86,49%", "78,86%", "69,05"],
            ["9", "1,0198", "1,7225", "63,56%", "50,02%", "88,08%", "77,63%", "69,11"],
            ["10 (Early Stop)", "0,9330", "1,7799", "66,48%", "49,29%", "89,58%", "77,74%", "69,12"],
        ],
        caption_label="Bảng 4.7.",
        caption_text="Diễn biến hàm mất mát và độ chính xác Top-1/Top-3 qua 10 epoch huấn luyện của mô hình chính thức Policy v5",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
        ],
    )
    b.add_figure(
        image_path=IMG_DIR / "20_LEARNING_CURVE.png",
        caption_label="Hình 4.3.",
        caption_text="Đường cong hàm mất mát (Loss) và độ chính xác Top-1 / Top-3 trên tập Train và Validation của mạng PolicyNet",
        width_cm=16.0,
    )
    b.add_paragraph(
        "Quan sát Bảng 4.7 và Hình 4.3 có thể nhận thấy rõ hai giai đoạn của quá trình học có giám sát:"
    )
    b.add_bullet(
        "Giai đoạn hội tụ tổng quát hóa (Epoch 1 đến Epoch 5)",
        "Ngay sau epoch đầu tiên, độ chính xác dự đoán nước đi của giáo viên trên tập validation đã vọt từ mức ngẫu nhiên "
        "(~1% trên ~100 ô trống) lên 44,90% (Top-1) và 76,34% (Top-3). Đến Epoch 5, hàm mất mát kiểm định đạt cực tiểu toàn cục "
        "val_loss = 1,5284 với Val Top-1 = 49,60% và Val Top-3 = 79,86%. Khi đánh giá checkpoint tốt nhất này (Epoch 5) một lần "
        "duy nhất trên tập kiểm thử độc lập (test set gồm 4.689 trạng thái hoàn toàn không giao quỹ đạo D4 với tập train), "
        "mô hình đạt Test Loss = 1,4421, đoán trúng chính xác nước đi thứ nhất của giáo viên ở 52,68% số trạng thái (Test Top-1) "
        "và nằm trong 3 lựa chọn hàng đầu ở 81,49% số trạng thái (Test Top-3).",
    )
    b.add_bullet(
        "Giai đoạn bắt đầu quá khớp (Overfitting từ Epoch 6 đến Epoch 10)",
        "Từ sau Epoch 5, trong khi Train Loss tiếp tục giảm đều xuống 0,9330 và Train Top-1 tăng lên 66,48%, thì Val Loss "
        "bắt đầu tăng ngược từ 1,5284 lên 1,7799 do mạng bắt đầu ghi nhớ các biến thể đối xứng D4 trong tập train. Cơ chế "
        "dừng sớm (Early Stopping với patience = 5) đã tự động ngắt quá trình huấn luyện tại cuối Epoch 10 và giữ lại "
        "checkpoint Epoch 5 làm mô hình xuất xưởng (best.pt), chứng minh quy trình kiểm định theo ván phát huy đúng tác dụng "
        "bảo vệ năng lực tổng quát hóa.",
    )
    b.add_paragraph(
        "Bên cạnh độ chính xác trung bình trên tập dữ liệu tĩnh, báo cáo nghiệm thu chiến thuật (docs/data/Policy_W6_Ly_Acceptance_Report.md) "
        "kiểm tra khả năng xử lý 9 thế cờ chiến thuật bắt buộc (win_x_gap, block_o_gap, block_x_gap, win_o_gap, win_before_block, "
        "win_edge, win_vertical, win_diagonal, win_antidiagonal). Kết quả cho thấy PolicyNet giải đúng 9/9 thế cờ ngay ở lựa chọn "
        "Top-1 (tỷ lệ 100%, trong đó ở tình huống vừa có nước thắng ngay vừa có nước chặn đối thủ win_before_block, mạng đặt "
        "xác suất Softmax lên tới 83,24% vào đúng ô thắng ngay (2, 7))."
    )

    # 4.5.3
    b.add_subheading("4.5.3. Đánh giá đối đầu trực tiếp và chi phí suy luận", level=3)
    b.add_paragraph(
        "Một bài học thực nghiệm rất sâu sắc của đồ án nằm ở việc so sánh năng lực thi đấu thực tế giữa Policy v2 và Policy v5. "
        "Nếu chỉ nhìn vào chỉ số phân loại tĩnh trên tập test ở Bảng 4.6, Policy v2 có Test Top-1 nhỉnh hơn nhẹ so với Policy v5 "
        "(53,22% so với 52,68%). Tuy nhiên, khi đưa cả hai mô hình vào đấu trường thực tế gồm 1.998 ván (666 ván trước mỗi đối thủ "
        "Heuristic, Minimax độ sâu 2 và MCTS 8 simulations; ứng với 333 hạt giống ghép cặp đổi bên X/O cân bằng tại base_seed = 20261201, "
        "ghi nhận tại docs/data/Policy_v2_Best_666_Evaluation_Report.md và docs/data/Policy_v5_Best_666_Evaluation_Report.md), "
        "sức mạnh thi đấu trên bàn cờ của Policy v5 vượt trội hoàn toàn so với Policy v2. Bảng 4.8 trình bày chi tiết kết quả đối đầu này."
    )
    b.add_table(
        headers=[
            "Đối thủ (666 ván / cặp)",
            "Vai cầm quân",
            "Policy v2: Thắng / Hòa / Thua (Score %)",
            "Policy v5 (Chính thức): Thắng / Hòa / Thua (Score %)",
            "Mức cải thiện Score Rate (v5 so với v2)",
        ],
        rows=[
            [
                "HeuristicAgent",
                "Tổng (666 ván)",
                "333 / 0 / 333 (50,00%)",
                "333 / 333 / 0 (75,00%)",
                "+25,00 điểm % (Bất bại 666/666 ván)",
            ],
            [
                "HeuristicAgent",
                "Khi cầm X / Khi cầm O",
                "X: 333/0/0 (100%) | O: 0/0/333 (0%)",
                "X: 333/0/0 (100%) | O: 0/333/0 (50%)",
                "Cầm O chuyển từ thua 100% sang hòa 100% (121 ply)",
            ],
            [
                "MinimaxAgent (d = 2)",
                "Tổng (666 ván)",
                "0 / 333 / 333 (25,00%)",
                "333 / 0 / 333 (50,00%)",
                "+25,00 điểm % (Cân bằng thế trận)",
            ],
            [
                "MinimaxAgent (d = 2)",
                "Khi cầm X / Khi cầm O",
                "X: 0/0/333 (0%) | O: 0/333/0 (50%)",
                "X: 0/0/333 (0%) | O: 333/0/0 (100%)",
                "Cầm O chuyển từ hòa sang thắng tuyệt đối 100% (38 ply)",
            ],
            [
                "MCTSAgent (8 sims guided)",
                "Tổng (666 ván)",
                "138 / 138 / 390 (31,08%)",
                "154 / 160 / 352 (35,14%)",
                "+4,06 điểm % (Tăng cả số trận thắng và hòa)",
            ],
            [
                "MCTSAgent (8 sims guided)",
                "Khi cầm X / Khi cầm O",
                "X: 98/51/184 (37,1%) | O: 40/87/206 (25,1%)",
                "X: 105/72/156 (42,34%) | O: 49/88/196 (27,93%)",
                "Cải thiện đồng đều ở cả hai vai đi trước và đi sau",
            ],
            [
                "Toàn bộ 3 đối thủ (1.998 ván)",
                "Tổng hợp chung",
                "471 / 471 / 1.056 (35,36%)",
                "820 / 493 / 685 (53,38%)",
                "+18,02 điểm % (Vượt ngưỡng trung bình > 50%)",
            ],
        ],
        caption_label="Bảng 4.8.",
        caption_text="So sánh kết quả thi đấu đối kháng quy mô lớn (1.998 ván) giữa Policy v2 và Policy v5 trước 3 tác tử giáo viên",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
        ],
    )
    b.add_paragraph(
        "Số liệu ở Bảng 4.8 giải thích rõ vì sao việc giữ phân phối giáo viên tự nhiên (trong đó giáo viên mạnh nhất MCTS "
        "chiếm 50,66% mẫu) và khử trùng lặp quỹ đạo đối xứng D4 ở dataset-v5 lại tạo ra bước nhảy vọt +18,02 điểm phần trăm "
        "về tỷ lệ điểm thi đấu thực tế (từ 35,36% lên 53,38% trên 1.998 ván):"
    )
    b.add_bullet(
        "Trước HeuristicAgent",
        "Policy v5 đạt thành tích bất bại tuyệt đối trên cả 666 ván (333 thắng, 333 hòa, 0 thua — score rate 75,00%): khi cầm X "
        "đi trước, mạng thắng nhanh sau 35 ply; khi cầm O đi sau (vốn bị thua ở bản v2), mạng phòng thủ kín kẽ suốt 121 nước "
        "để ép hòa đầy bàn cờ.",
    )
    b.add_bullet(
        "Trước MinimaxAgent (độ sâu 2)",
        "Policy v5 nâng tỷ lệ điểm từ 25,00% lên 50,00% (thắng 333 ván khi cầm O trong 38 ply nhờ khai thác được điểm mù "
        "chân trời độ sâu 2 của Minimax, và thua 333 ván khi cầm X trong 40 ply).",
    )
    b.add_bullet(
        "Trước MCTSAgent (8 simulations có hướng dẫn)",
        "Dù không dùng bất kỳ phép tìm kiếm cây nào ở pha suy luận, mạng PolicyNet đơn lẻ vẫn giành được 154 trận thắng "
        "và 160 trận hòa trên 666 ván (score rate 35,14%, riêng khi cầm X đạt 42,34%).",
    )
    b.add_paragraph(
        "Cần lưu ý một đặc điểm phương pháp luận quan trọng khi diễn giải các cặp đấu giữa hai tác tử hoàn toàn tất định "
        "(PolicyNet đấu với Heuristic hoặc Minimax-D2): vì cả hai bên không phụ thuộc vào hạt giống ngẫu nhiên khi chọn nước, "
        "nên 333 hạt giống ghép cặp thực chất lặp lại cùng một quỹ đạo khi cầm X và một quỹ đạo khi cầm O. Ngược lại, trong "
        "666 ván đấu với MCTS (và 100 ván đấu với Random trong giải đấu W78, nơi NeuralAgent thắng tuyệt đối 100/100 ván), "
        "mỗi hạt giống tạo ra một trận đấu hoàn toàn khác biệt, qua đó kiểm chứng vững chắc khả năng tổng quát hóa của mạng "
        "trên các trạng thái chưa từng gặp."
    )
    b.add_paragraph(
        "Ưu thế lớn nhất của NeuralAgent nằm ở chi phí thời gian suy luận tại thời điểm vận hành (inference latency). "
        "Hình 4.4 đặt thời gian suy luận mỗi nước đi của NeuralAgent cạnh Minimax và MCTS."
    )
    b.add_figure(
        image_path=IMG_DIR / "21_MODEL_INFERENCE_COST.png",
        caption_label="Hình 4.4.",
        caption_text="So sánh chi phí thời gian suy luận trên một nước đi (Mean và p95 Latency) của NeuralAgent so với các tác tử tìm kiếm",
        width_cm=16.0,
    )
    b.add_paragraph(
        "Trong giải đấu chính thức W78 chạy đơn luồng trên CPU (11.617 nước đi của NeuralAgent), một lượt suy luận tiến "
        "qua mạng ResNet 4 khối chỉ mất trung bình 3,66 ms (p95 = 5,13 ms ở profile DEFAULT và mean = 3,77 ms, p95 = 5,45 ms "
        "ở profile FAIR) — tức nhanh hơn khoảng 8,4 lần so với MCTS 8 simulations (30,79 ms) và nhanh hơn 10,2 lần so với "
        "Minimax độ sâu 2 (37,20 ms). Ngay cả khi chạy đánh giá song song đa tiến trình trên CPU tải nặng (4 worker chạy đồng thời "
        "1.998 ván), độ trễ của PolicyNet vẫn giữ ở mức 7,93 – 19,53 ms/nước, thấp hơn hơn 11 lần so với MCTS (129,79 ms) và "
        "Minimax (218,20 ms) trong cùng điều kiện tải. Kết quả này chứng minh việc chưng cất tri thức từ các tác tử tìm kiếm "
        "sang mạng nơ-ron chính sách giúp chuyển giao phần lớn chi phí tính toán sang pha huấn luyện ngoại tuyến (offline training), "
        "mang lại tốc độ phản hồi tức thời cho giao diện người dùng mà vẫn giữ được năng lực thi đấu đứng thứ hai toàn giải đấu "
        "(score rate 64,62%, chỉ xếp sau MCTS)."
    )


def main() -> None:
    if not DOCX_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy file báo cáo: {DOCX_PATH}")

    # Luôn đọc từ bản gốc chưa chỉnh sửa (nếu bản backup tồn tại và bản chính đã được chạy trước đó,
    # đảm bảo tính idempotent khi chạy lại script)
    doc = docx.Document(str(DOCX_PATH))

    # Kiểm tra xem script đã từng chèn nội dung chưa để tránh nhân đôi nếu chạy nhiều lần
    existing_texts = "\n".join(p.text for p in doc.paragraphs)
    if "Bảng 3.E." in existing_texts and "Bảng 4.8." in existing_texts:
        print("Phát hiện file đã có nội dung chèn trước đó. Khôi phục từ bản sao gốc 'Internship_Report - Copy copy.docx' trước khi ghi mới...")
        if BACKUP_PATH.exists():
            doc = docx.Document(str(BACKUP_PATH))
        else:
            raise RuntimeError("File đã được điền và không tìm thấy bản sao gốc để chạy lại idempotent.")

    print("1. Đang hoàn thiện cuối Mục 3.3.2 (Phân hệ Học máy và Chuỗi xử lý dữ liệu)...")
    fill_section_3_3_2_ml_subsystem(doc)

    print("2. Đang hoàn thiện Mục 3.4 (3.4.1 -> 3.4.5: Cài đặt engine và luật)...")
    fill_section_3_4_engine(doc)

    print("3. Đang hoàn thiện Mục 3.5 (3.5.1 -> 3.5.5: Các tác tử tìm kiếm)...")
    fill_section_3_5_search_agents(doc)

    print("4. Đang hoàn thiện Mục 3.6.2 & 3.6.3 (Kiến trúc PolicyNet, huấn luyện và NeuralAgent)...")
    fill_section_3_6_learned_agent(doc)

    print("5. Đang hoàn thiện Mục 3.8 (Chiến lược kiểm thử)...")
    fill_section_3_8_testing_strategy(doc)

    print("6. Đang hoàn thiện Mục 4.3 (4.3.1 -> 4.3.4: Kết quả Minimax/Alpha-Beta)...")
    fill_section_4_3_minimax_results(doc)

    print("7. Đang hoàn thiện Mục 4.4 (4.4.1 -> 4.4.3: Kết quả MCTS)...")
    fill_section_4_4_mcts_results(doc)

    print("8. Đang hoàn thiện Mục 4.5 (4.5.1 -> 4.5.3: Kết quả tác tử học được)...")
    fill_section_4_5_learned_agent_results(doc)

    doc.save(str(DOCX_PATH))
    print(f"Đã ghi thành công toàn bộ nội dung Chương 3 và Chương 4 vào: {DOCX_PATH}")
    print(f"Tổng số đoạn văn sau cập nhật: {len(doc.paragraphs)}, tổng số bảng: {len(doc.tables)}")


if __name__ == "__main__":
    main()
