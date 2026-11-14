# -*- coding: utf-8 -*-
"""
Script hoàn thiện toàn bộ Chương 5 (Xây dựng ứng dụng minh họa),
Chương 6 (Kết luận và hướng phát triển) và Tài liệu tham khảo
trực tiếp vào file báo cáo `Internship_Report - Copy.docx`.

Script tự động xóa các dòng gợi ý dàn ý ngắn (placeholder) nằm dưới các tiêu đề
của Chương 5 và Chương 6, sau đó chèn nội dung học thuật hoàn chỉnh, các bảng
tổng hợp và hình ảnh chụp giao diện Streamlit thực tế.
"""

from __future__ import annotations

from pathlib import Path
import docx
from docx.shared import Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


ROOT_DIR = Path(__file__).resolve().parent.parent
DOCX_PATH = ROOT_DIR / "Internship_Report - Copy.docx"
IMG_UI_LIVE = ROOT_DIR / "tmp" / "pptx_rework_assets" / "ui-live.png"
IMG_UI_AI_VS_AI = ROOT_DIR / "tmp" / "pptx_rework_assets" / "ui-ai-vs-ai.png"
IMG_UI_REF = ROOT_DIR / "notebooklm_upload" / "28_UI_REFERENCE.png"


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

        hdr_cells = tbl.rows[0].cells
        for j, h_text in enumerate(headers):
            cell = hdr_cells[j]
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.style = "Normal"
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(h_text)
            run.bold = True

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


def clear_normal_paragraphs_after_heading(doc: docx.Document, heading_p: docx.text.paragraph.Paragraph) -> None:
    """Xóa các đoạn văn Normal (dàn ý nháp) nằm ngay sau một Heading cho đến trước Heading kế tiếp."""
    nxt = heading_p._p.getnext()
    while nxt is not None:
        # Nếu là bảng cũ thuộc phần nháp (nếu có) hoặc đoạn văn Normal thì kiểm tra
        tag = nxt.tag.split("}")[-1]
        if tag == "p":
            # Tìm đối tượng Paragraph tương ứng để kiểm tra style
            p_obj = docx.text.paragraph.Paragraph(nxt, doc)
            if p_obj.style.name.startswith("Heading"):
                break
            to_remove = nxt
            nxt = nxt.getnext()
            to_remove.getparent().remove(to_remove)
        elif tag == "tbl":
            to_remove = nxt
            nxt = nxt.getnext()
            to_remove.getparent().remove(to_remove)
        else:
            break


def fill_chapter_5(doc: docx.Document) -> None:
    # Xóa các dòng dàn ý nháp trong Chương 5 trước khi ghi nội dung chính thức
    ch5_headings = [
        ("CHƯƠNG 5. XÂY DỰNG ỨNG DỤNG MINH HỌA", "Heading 1"),
        ("5.1. Mục tiêu ứng dụng", "Heading 2"),
        ("5.2. Công nghệ sử dụng", "Heading 2"),
        ("5.3. Thiết kế giao diện và trải nghiệm", "Heading 2"),
        ("5.4. Tích hợp UI với engine", "Heading 2"),
        ("5.5. Các chức năng đã hoàn thành", "Heading 2"),
        ("5.6. Kiểm thử ứng dụng", "Heading 2"),
    ]
    for prefix, style in ch5_headings:
        hp = find_paragraph(doc, prefix, style)
        clear_normal_paragraphs_after_heading(doc, hp)

    # Mở đầu Chương 5
    p_ch5 = find_paragraph(doc, "CHƯƠNG 5. XÂY DỰNG ỨNG DỤNG MINH HỌA", "Heading 1")
    b_ch5 = SectionBuilder(doc, p_ch5)
    b_ch5.add_paragraph(
        "Bên cạnh hệ thống đánh giá định lượng qua dòng lệnh (CLI) và nhật ký JSONL ở Chương 4, đồ án xây dựng "
        "một ứng dụng web tương tác hoàn chỉnh tại phân hệ ui/ nhằm trực quan hóa môi trường Caro 11 × 11 và toàn bộ "
        "năm tác tử trí tuệ nhân tạo. Chương này trình bày mục tiêu thiết kế, công nghệ nền tảng, kiến trúc trải nghiệm "
        "người dùng, cơ chế tích hợp không rò rỉ luật với CaroEnv, các tính năng đã hoàn thiện và bộ kiểm thử tự động "
        "của ứng dụng."
    )

    # 5.1. Mục tiêu ứng dụng
    p_51 = find_paragraph(doc, "5.1. Mục tiêu ứng dụng", "Heading 2")
    b = SectionBuilder(doc, p_51)
    b.add_paragraph(
        "Ứng dụng minh họa được phát triển nhằm giải quyết đồng thời hai mục tiêu học thuật và kỹ thuật phần mềm:"
    )
    b.add_bullet(
        "Trực quan hóa hành vi chiến thuật và chi phí suy luận của các tác tử AI trong thời gian thực",
        "Cung cấp một môi trường trực quan nơi giảng viên, sinh viên và người dùng có thể trực tiếp thi đấu hoặc "
        "quan sát năm thuật toán (Random, Heuristic, Minimax/Alpha-Beta, MCTS và Neural Network) đối đầu với nhau trên "
        "bàn cờ 11 × 11. Qua từng nước đi, giao diện phản hồi tức thời trạng thái bàn cờ, lượt người chơi hiện tại, "
        "lịch sử tọa độ (row, col), kết quả thắng/hòa/thua cùng các chỉ số đo lường nội tại của thuật toán gồm thời gian "
        "suy nghĩ (elapsed_ms), số nút cây mở rộng (nodes) và số lượt mô phỏng (simulations).",
    )
    b.add_bullet(
        "Thực thi nghiêm ngặt nguyên lý tách biệt giao diện và lõi nghiệp vụ (Strict Separation of Concerns)",
        "Giao diện người dùng đóng vai trò thuần túy là tầng trình diễn (Presentation Layer) và điều phối sự kiện "
        "mỏng. Ứng dụng tuyệt đối không cài đặt lại bất kỳ logic kiểm tra hợp lệ, luật thắng 5 quân chặn hai đầu hay "
        "thuật toán tìm kiếm nào bên trong mã nguồn UI; toàn bộ trạng thái ván cờ do CaroEnv quản lý và mọi quyết định "
        "của AI đều đi qua phương thức chuẩn Agent.choose_action(env, budget) theo đúng hợp đồng caro-v2.",
    )

    # 5.2. Công nghệ sử dụng
    p_52 = find_paragraph(doc, "5.2. Công nghệ sử dụng", "Heading 2")
    b = SectionBuilder(doc, p_52)
    b.add_paragraph(
        "Toàn bộ phân hệ giao diện được xây dựng bằng ngôn ngữ Python 3.13 kết hợp với khung ứng dụng web hướng dữ liệu "
        "Streamlit (phiên bản 1.x), khởi chạy trực tiếp từ thư mục gốc của dự án bằng lệnh chuẩn python -m streamlit run ui/app.py. "
        "Việc lựa chọn Streamlit cho đồ án Trí tuệ nhân tạo nâng cao dựa trên bốn lý do kỹ thuật cốt lõi:"
    )
    b.add_bullet(
        "Tích hợp trực tiếp trong cùng không gian tiến trình Python (Zero-Serialization Overhead)",
        "Do CaroEnv, các tác tử tìm kiếm cây (Minimax, MCTS) và mô hình mạng nơ-ron PyTorch (NeuralAgent) đều được viết "
        "bằng Python, việc sử dụng Streamlit cho phép tầng giao diện gọi trực tiếp các đối tượng trong bộ nhớ mà không cần "
        "xây dựng thêm tầng REST API trung gian hay tuần tự hóa/giải tuần tự hóa ma trận bàn cờ qua giao thức mạng sau mỗi nước đi.",
    )
    b.add_bullet(
        "Mô hình thực thi phản ứng (Reactive Rerun Model) và quản lý trạng thái phiên (st.session_state)",
        "Cơ chế tự động chạy lại kịch bản từ trên xuống dưới mỗi khi có tương tác người dùng kết hợp cùng từ điển bền vững "
        "st.session_state giúp đồng bộ hóa hoàn toàn giao diện hiển thị với đối tượng bất biến env.state: tại bất kỳ thời điểm nào, "
        "bàn cờ trên màn hình luôn là ảnh chiếu một-một của ma trận CaroEnv._board.",
    )
    b.add_bullet(
        "Khả năng tùy biến giao diện sâu bằng CSS động (_inject_styles và _build_dynamic_cell_css)",
        "Mặc dù sử dụng các thành phần nút bấm chuẩn (st.button) để bắt sự kiện nhấp chuột theo tọa độ khóa "
        "cell_11_{row}_{col}, ứng dụng tiêm trực tiếp bảng kiểu CSS động theo trạng thái ván cờ để định hình lưới bàn cờ "
        "vuông vức, phân biệt màu quân X/O, đóng khung cam nước đi vừa đánh và tô đỏ toàn bộ chuỗi 5 quân chiến thắng.",
    )
    b.add_bullet(
        "Hỗ trợ khung kiểm thử giao diện tự động không cần trình duyệt (Headless AppTest)",
        "Mô-đun streamlit.testing.v1.AppTest cho phép giả lập thao tác chọn menu, nhập đường dẫn checkpoint, nhấp chuột "
        "lên từng ô bàn cờ và kiểm tra trực tiếp trạng thái DOM cũng như session_state ngay trong pytest, giúp tích hợp "
        "kiểm thử UI vào cùng đường ống hồi quy với Engine và Agent.",
    )
    b.add_paragraph(
        "Cấu trúc các tệp mã nguồn thuộc phân hệ giao diện và kiểm thử giao diện được tổng hợp trong Bảng 5.1."
    )
    b.add_table(
        headers=["Tệp mã nguồn", "Số dòng mã", "Trách nhiệm kiến trúc trong phân hệ UI"],
        rows=[
            [
                "ui/app.py",
                "~510 dòng",
                "Điểm nhập chính của ứng dụng Streamlit: quản lý st.session_state, khởi tạo và lưu đệm (cache) 5 tác tử AI, điều phối 3 chế độ chơi, sinh CSS động tô sáng nước đi/chuỗi thắng và kết xuất bố cục bàn cờ + thanh bên.",
            ],
            [
                "ui/human_controller.py",
                "~35 dòng",
                "Lớp điều khiển mỏng (Thin Controller) tại biên giao diện: định nghĩa cấu trúc bất biến HumanMove và hàm submit_human_action(env, action) chuyển thao tác nhấp chuột thành lời gọi env.step(action).",
            ],
            [
                "ui/mock_game_env.py",
                "~250 dòng",
                "Môi trường giả lập độc lập (Test Double) tuân thủ giao thức caro-v2, dùng để kiểm thử cô lập giao diện ở giai đoạn phát triển song song trước khi ghép nối với CaroEnv thật.",
            ],
            [
                "tests/test_ui_app.py",
                "~270 dòng",
                "Bộ kiểm thử tích hợp giao diện cơ sở với CaroEnv thật: kiểm tra khởi tạo bàn 11×11, tính nguyên tử khi nhấp ô đã có quân, thắng X, thắng O, hòa 121 nước, bảo toàn thống kê khi Reset/Play Again.",
            ],
            [
                "tests/test_ui_ai_modes.py",
                "~146 dòng",
                "Bộ kiểm thử chuyên biệt cho các chế độ AI (Human vs AI chọn X/O, AI vs AI tự động chạy hết ván, kiểm tra cả 5 tác tử không làm biến đổi môi trường, bắt lỗi nguyên tử khi thiếu tệp checkpoint Neural và tô sáng đúng 5 ô thắng).",
            ],
        ],
        caption_label="Bảng 5.1.",
        caption_text="Cấu trúc các tệp mã nguồn thuộc phân hệ giao diện và kiểm thử giao diện Streamlit",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
        ],
    )

    # 5.3. Thiết kế giao diện và trải nghiệm
    p_53 = find_paragraph(doc, "5.3. Thiết kế giao diện và trải nghiệm", "Heading 2")
    b = SectionBuilder(doc, p_53)
    b.add_paragraph(
        "Giao diện ứng dụng được thiết kế theo phong cách tối giản học thuật (Clean Academic Dashboard), bố cục chia "
        "thành hai vùng rõ rệt để toàn bộ bàn cờ 11 × 11 luôn hiển thị trọn vẹn trong một khung nhìn màn hình máy tính "
        "xách tay phổ thông (kể cả độ phân giải 1280 × 720 nhờ quy tắc phản hồi @media (max-height: 820px) tự động thu gọn "
        "kích thước ô từ 44px xuống 36px):"
    )
    b.add_bullet(
        "Thanh điều khiển và thống kê bên trái (Sidebar — rộng cố định 300px, hàm _render_sidebar)",
        "Phần trên của thanh bên bố trí các hộp chọn cấu hình trận đấu: chế độ chơi (Game Mode gồm Human vs Human, "
        "Human vs AI, AI vs AI), thuật toán AI (AI Algorithm trong chế độ đấu với máy, hoặc hai hộp chọn độc lập "
        "Player X AI và Player O AI trong chế độ máy đấu máy), bên cầm quân của người chơi (Human Side: X đi trước hoặc O đi sau), "
        "ô nhập đường dẫn tệp trọng số mạng nơ-ron (Neural Checkpoint — chỉ hiển thị động khi có ít nhất một bên chọn "
        "Neural Network, mặc định trỏ tới models/checkpoints/model-v5-natural-teachers-run2/best.pt), kích thước bàn cờ "
        "(khóa ở 11 × 11 theo hợp đồng caro-v2), nút tạo ván mới (↻ New Game) và nút kích hoạt chạy tự động (▶ Run AI Game "
        "khi ở chế độ AI vs AI). Phần dưới của thanh bên hiển thị bảng thống kê phiên làm việc (Statistics) chia 3 cột "
        "(X wins màu xanh dương, O wins màu đỏ, Draws màu xám) và khung lịch sử nước đi thu gọn được (Move History) ghi rõ "
        "số thứ tự nước, người chơi, tọa độ (row, col), tên thuật toán và độ trễ suy luận.",
    )
    b.add_bullet(
        "Khung bàn cờ trung tâm (Main Game Panel — rộng tối đa 590px, hàm _render_status, _render_board, _render_result)",
        "Phía trên bàn cờ là thanh trạng thái hiển thị đèn báo lượt đi hiện tại (Player X's turn / Player O's turn / Game complete), "
        "bộ đếm tiến độ số nước đã đánh trên tổng số ô (Moves: m / 121) và dòng thông tin chi tiết về quyết định vừa thực hiện "
        "của AI (Last AI move: tên thuật toán, thời gian ms, số nút duyệt và số lượt simulation). Chính giữa là lưới bàn cờ "
        "11 × 11 gồm 121 nút tương tác được căn lề khít nhau (khoảng cách 2px). Phía dưới bàn cờ là chú giải màu sắc (Legend), "
        "dòng hướng dẫn ngữ cảnh và biểu ngữ thông báo kết quả trận đấu (Result Banner) đi kèm nút ↻ Play Again khi ván cờ khép lại.",
    )
    b.add_paragraph(
        "Để người dùng theo dõi trực quan diễn biến chiến thuật trên bàn cờ, hàm _build_dynamic_cell_css(env) kết hợp cùng "
        "hàm _winning_cells(env) tự động sinh các quy tắc CSS gắn trực tiếp vào từng khóa phần tử .st-key-cell_11_{row}_{col} button "
        "dựa trên trạng thái của CaroEnv. Hệ thống trạng thái hiển thị ô cờ và bảng mã màu ngữ nghĩa được tóm tắt trong Bảng 5.2, "
        "cùng ảnh chụp giao diện thực tế tại Hình 5.1 và bản thiết kế thành phần tại Hình 5.2."
    )
    b.add_table(
        headers=[
            "Trạng thái ô / Thành phần UI",
            "Điều kiện kích hoạt từ GameState",
            "Mã màu chữ / Viền / Nền (Hex CSS)",
            "Ý nghĩa trải nghiệm người dùng",
        ],
        rows=[
            [
                "Ô trống hợp lệ (Empty Cell)",
                "board[r][c] == 0 và chưa khóa bàn",
                "Chữ #343A43, Viền 1px #E0E0E0, Nền #FFFFFF (Hover: #F7F8FA)",
                "Cho phép người chơi nhấp chuột đặt quân ở lượt của mình.",
            ],
            [
                "Ô chứa quân X (Player X)",
                "board[r][c] == Player.X (1)",
                "Chữ đậm #1E88E5 (Xanh dương), Nền #EAF4FE",
                "Nhận diện trực quan các quân của người đi trước (X).",
            ],
            [
                "Ô chứa quân O (Player O)",
                "board[r][c] == Player.O (-1)",
                "Chữ đậm #E53935 (Đỏ), Nền #FDEEEE",
                "Nhận diện trực quan các quân của người đi sau (O).",
            ],
            [
                "Nước đi vừa đánh (Last Move)",
                "state.last_action == (r, col)",
                "Viền 2px solid #FFA726 (Cam nổi bật)",
                "Giúp người chơi nhận biết ngay lập tức vị trí AI hoặc đối thủ vừa đặt quân.",
            ],
            [
                "Chuỗi quân chiến thắng (Winning Line)",
                "(r, col) ∈ _winning_cells(env) khi state.winner ≠ None",
                "Chữ #B71C1C, Viền 3px solid #E53935, Nền #FFE3E3, Bóng mờ đỏ",
                "Tô sáng toàn bộ chuỗi ≥ 5 quân liên tiếp đi qua nước cuối mang lại chiến thắng.",
            ],
            [
                "Trạng thái khóa bàn cờ (Board Locked)",
                "state.terminated hoặc _is_ai_turn(env) hoặc ai_thinking",
                "Thuộc tính disabled=True, Độ mờ opacity: 0.5",
                "Ngăn người dùng nhấp đúp khi AI đang suy nghĩ hoặc khi ván đấu đã kết thúc.",
            ],
        ],
        caption_label="Bảng 5.2.",
        caption_text="Hệ thống mã màu ngữ nghĩa và quy tắc hiển thị trạng thái ô cờ trong ui/app.py",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
        ],
    )
    b.add_figure(
        image_path=IMG_UI_LIVE,
        caption_label="Hình 5.1.",
        caption_text="Giao diện chính của ứng dụng Caro AI 11×11 trên nền tảng Streamlit khi bắt đầu ván đấu mới",
        width_cm=16.0,
    )
    b.add_figure(
        image_path=IMG_UI_REF,
        caption_label="Hình 5.2.",
        caption_text="Đặc tả thiết kế các thành phần giao diện (Component Sheet), trạng thái ô cờ, thông báo và bảng màu ngữ nghĩa",
        width_cm=15.0,
    )

    # 5.4. Tích hợp UI với engine
    p_54 = find_paragraph(doc, "5.4. Tích hợp UI với engine", "Heading 2")
    b = SectionBuilder(doc, p_54)
    b.add_paragraph(
        "Điểm cốt lõi trong kiến trúc của ui/app.py là việc tuân thủ tuyệt đối ranh giới hợp đồng caro-v2: giao diện "
        "không bao giờ ghi trực tiếp vào mảng bàn cờ mà chỉ đọc dữ liệu từ snapshot bất biến env.state và ủy quyền mọi "
        "thao tác biến đổi trạng thái cho CaroEnv. Luồng tích hợp giữa giao diện, bộ điều khiển người chơi và các tác tử AI "
        "được tổ chức qua bốn cơ chế kỹ thuật:"
    )
    b.add_bullet(
        "1. Luồng xử lý nước đi của người chơi qua Thin Controller (ui/human_controller.py)",
        "Khi người dùng nhấp vào một ô tại dòng row, cột col trên lưới nút bấm, hàm callback _play_move(row, col) được kích hoạt. "
        "Nếu đang là lượt của AI (_is_ai_turn(env) == True), giao diện lập tức từ chối thao tác và hiển thị cảnh báo yêu cầu "
        "đợi AI hoàn tất. Ngược lại, hàm gọi submit_human_action(env, (row, col)) để chuyển tọa độ tuple (row, col) thẳng vào "
        "env.step(action). Nếu người dùng nhấp vào ô đã có quân cờ, CaroEnv ném ngoại lệ InvalidActionError(OCCUPIED); giao diện "
        "bắt ngoại lệ này, gán thông điệp vào st.session_state.error_message để hiển thị hộp cảnh báo st.warning('Cell (r, c) is already occupied') "
        "mà không làm thay đổi trạng thái bàn cờ, lượt đi hay lịch sử nước đi. Nếu hợp lệ, đối tượng HumanMove(action, player, result) "
        "được ghi vào move_history; tiếp đó, nếu đang ở chế độ Human vs AI và ván cờ chưa kết thúc (not result.done), hàm tự động "
        "gọi tiếp _play_ai_turn() để máy phản hồi đúng một nước.",
    )
    b.add_bullet(
        "2. Luồng quyết định và áp dụng nước đi nguyên tử của AI (_play_ai_turn và _apply_ai_decision)",
        "Trong một lượt đi của AI, giao diện xác định người chơi hiện tại player = env.state.current_player, bật cờ khóa "
        "ai_thinking = True, lấy đối tượng tác tử từ bộ nhớ đệm thông qua _get_agent(algorithm), và gọi phương thức công khai "
        "decision = agent.choose_action(env, SearchBudget(seed=20261113 + env.state.move_count)). Nhờ truyền hạt giống tăng dần "
        "theo số nước đã đi (move_count), hành vi của các tác tử có yếu tố ngẫu nhiên như Random và MCTS trên UI vừa đa dạng "
        "giữa các lượt vừa hoàn toàn tái lập được. Sau khi nhận AgentDecision, hàm _apply_ai_decision kiểm tra một lần nữa "
        "decision.action ∈ env.legal_actions() rồi mới gọi env.step(decision.action) đúng một lần duy nhất, cập nhật lịch sử "
        "kèm các chỉ số elapsed_ms, nodes, simulations. Việc tách bạch rõ ràng giữa bước xin quyết định (choose_action) và bước "
        "thực thi (env.step) giúp ngăn chặn triệt để lỗi AI tự ý đánh hai nước hoặc làm hỏng trạng thái môi trường.",
    )
    b.add_bullet(
        "3. Cơ chế lưu đệm tác tử (Session Agent Caching) và bảo vệ nguyên tử khi lỗi Checkpoint",
        "Hàm _get_agent(algorithm) lưu trữ các thể hiện tác tử đã khởi tạo vào từ điển st.session_state.agent_cache theo khóa "
        "(algorithm, checkpoint_path). Cơ chế này đặc biệt quan trọng đối với NeuralAgent: tệp trọng số best.pt (768.537 tham số) "
        "chỉ cần nạp và kiểm tra mã băm SHA-256 đúng một lần khi người dùng chọn chế độ, giúp các nước đi tiếp theo đạt tốc độ "
        "phản hồi ~3 – 5 ms mà không phải đọc lại ổ đĩa. Trong trường hợp người dùng nhập đường dẫn checkpoint không tồn tại "
        "hoặc không khớp schema caro-policy-v1, khối try...except (FileNotFoundError, RuntimeError, ValueError) trong _play_ai_turn "
        "bắt lỗi an toàn, tắt cờ auto_play, hiển thị nguyên nhân lỗi rõ ràng trên giao diện và giữ nguyên trạng thái bàn cờ "
        "ở đúng lượt của AI mà không làm sập ứng dụng.",
    )
    b.add_bullet(
        "4. Vòng đời làm mới ván đấu (_start_new_game) và duy trì trạng thái qua Streamlit Rerun",
        "Khi người dùng nhấn nút ↻ New Game, ↻ Play Again hoặc chuyển đổi chế độ chơi trên thanh bên, hàm _start_new_game() "
        "gọi trực tiếp phương thức công khai current_env.reset(), xóa danh sách move_history, đặt lại các cờ ai_thinking = False, "
        "auto_play = False, last_ai_decision = None nhưng vẫn bảo toàn nguyên vẹn từ điển thống kê st.session_state.stats "
        "(x_wins, o_wins, draws) trong suốt phiên làm việc của trình duyệt.",
    )

    # 5.5. Các chức năng đã hoàn thành
    p_55 = find_paragraph(doc, "5.5. Các chức năng đã hoàn thành", "Heading 2")
    b = SectionBuilder(doc, p_55)
    b.add_paragraph(
        "Tại thời điểm hoàn thành đồ án, ứng dụng Streamlit không chỉ dừng lại ở mức giao diện khung cho hai người chơi "
        "mà đã kết nối thực tế và đầy đủ cả 3 chế độ chơi với toàn bộ 5 tác tử AI theo đúng cấu hình đã khóa ở Chương 4. "
        "Bảng 5.3 tổng hợp cấu hình kỹ thuật của 5 tác tử khi vận hành trên UI."
    )
    b.add_table(
        headers=[
            "Tên hiển thị trên UI",
            "Lớp cài đặt (core/agents/)",
            "Tham số cấu hình khóa trong ui/app.py",
            "Thông số hiển thị sau mỗi nước đi",
        ],
        rows=[
            [
                "Random",
                "RandomAgent",
                "seed = 20261113 (kết hợp SearchBudget.seed theo ply)",
                "Thời gian thực thi (elapsed_ms)",
            ],
            [
                "Heuristic",
                "HeuristicAgent",
                "Đánh giá mẫu hình 1 bước (WIN_SCORE, BLOCK_SCORE, _PATTERN_SCORES)",
                "Thời gian thực thi (elapsed_ms)",
            ],
            [
                "Minimax (Alpha-Beta)",
                "MinimaxAgent",
                "default_depth = 2, alpha_beta = True, move_ordering = True, radius = 2",
                "Thời gian (elapsed_ms) và Số nút duyệt (nodes)",
            ],
            [
                "MCTS",
                "MCTSAgent",
                "default_simulations = 8, c = 0.7, tactical_precheck = True, heuristic_seeded, progressive_widening_c = 1.5, rollout = epsilon_heuristic (horizon = 8)",
                "Thời gian (elapsed_ms), Số nút (nodes) và Số mô phỏng (simulations)",
            ],
            [
                "Neural Network",
                "NeuralAgent (PolicyNet)",
                "Checkpoint mặc định: models/checkpoints/model-v5-natural-teachers-run2/best.pt (cho phép đổi đường dẫn trực tiếp trên Sidebar)",
                "Thời gian suy luận mạng (elapsed_ms)",
            ],
        ],
        caption_label="Bảng 5.3.",
        caption_text="Cấu hình 5 tác tử AI được tích hợp thực tế vào ứng dụng giao diện ui/app.py",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
            WD_ALIGN_PARAGRAPH.LEFT,
        ],
    )
    b.add_paragraph(
        "Các nhóm chức năng hoàn thiện của ứng dụng bao gồm:"
    )
    b.add_bullet(
        "Chế độ Người đấu với Người (Human vs Human)",
        "Hai người chơi luân phiên nhấp chuột đặt quân X và O trên bàn cờ 11 × 11. Hệ thống tự động kiểm tra nước đi hợp lệ, "
        "cập nhật lịch sử tọa độ, phát hiện chiến thắng theo luật chặn hai đầu hoặc hòa khi đầy 121 ô.",
    )
    b.add_bullet(
        "Chế độ Người đấu với Máy (Human vs AI — hỗ trợ chọn cầm X hoặc cầm O)",
        "Người chơi có thể chọn đối đầu với bất kỳ tác tử nào trong 5 cấp độ AI. Khi người chơi chọn cầm quân X (đi trước), "
        "ngay sau mỗi cú nhấp chuột hợp lệ vào ô trống, AI sẽ tự động suy luận và đánh trả 1 nước. Đặc biệt, khi người chơi "
        "chọn cầm quân O (đi sau), ngay khi khởi tạo ván mới (move_count == 0), giao diện tự động nhận diện lượt đi đầu tiên "
        "thuộc về AI (quân X) và kích hoạt _play_ai_turn() để máy mở màn ván đấu trước khi mở khóa bàn cờ cho người chơi.",
    )
    b.add_bullet(
        "Chế độ Máy đấu với Máy trực tiếp từng bước (AI vs AI Step-by-Step Auto-Play)",
        "Người dùng có thể ghép cặp bất kỳ hai thuật toán nào (ví dụ: MCTS cầm X đấu với Neural Network cầm O, hoặc Random "
        "đấu với Heuristic) và nhấn nút ▶ Run AI Game. Thay vì chạy ngầm toàn bộ ván cờ trong một vòng lặp chặn đứng giao diện "
        "rồi chỉ hiện kết quả cuối cùng, ứng dụng sử dụng cờ st.session_state.auto_play kết hợp độ trễ ngắn AI_MOVE_DELAY_SECONDS = 0,12s "
        "và lệnh st.rerun() sau mỗi nước đi đơn lẻ. Nhờ cơ chế này, bàn cờ được vẽ lại trực tiếp sau từng ply, giúp người xem "
        "quan sát rõ ràng từng bước dàn trận, chặn đường và thời gian suy nghĩ của mỗi tác tử cho tới khi ván cờ kết thúc (Hình 5.3).",
    )
    b.add_figure(
        image_path=IMG_UI_AI_VS_AI,
        caption_label="Hình 5.3.",
        caption_text="Giao diện chế độ AI vs AI sau khi hoàn tất ván đấu: hiển thị thông số suy luận của nước cuối và tô đỏ toàn bộ chuỗi 5 quân chiến thắng",
        width_cm=16.0,
    )

    # 5.6. Kiểm thử ứng dụng
    p_56 = find_paragraph(doc, "5.6. Kiểm thử ứng dụng", "Heading 2")
    b = SectionBuilder(doc, p_56)
    b.add_paragraph(
        "Để đảm bảo giao diện hoạt động chính xác, không chứa bản sao ẩn của luật chơi và kết nối an toàn với cả 5 tác tử AI, "
        "nhóm xây dựng bộ kiểm thử tích hợp tự động sử dụng khung streamlit.testing.v1.AppTest tại hai tệp tests/test_ui_app.py "
        "(9 kịch bản kiểm thử luồng cơ sở) và tests/test_ui_ai_modes.py (6 kịch bản kiểm thử chuyên sâu cho các chế độ AI, "
        "trong đó kịch bản kiểm tra hợp đồng tác tử duyệt qua toàn bộ 5 thuật toán). Toàn bộ 15 hàm kiểm thử AppTest (tương ứng "
        "17 phép kiểm chứng kịch bản UI và controller) đều vượt qua 100% khi chạy với CaroEnv thật. Bảng 5.4 liệt kê chi tiết "
        "các kịch bản kiểm thử này."
    )
    b.add_table(
        headers=[
            "Tệp kiểm thử",
            "Tên hàm kiểm thử (pytest)",
            "Mục tiêu và điều kiện nghiệm thu được xác nhận",
        ],
        rows=[
            [
                "tests/test_ui_app.py",
                "test_app_uses_real_caro_env_and_renders_default_11x11_board",
                "Xác nhận st.session_state.env là thể hiện thật của CaroEnv, bàn cờ 11×11 gồm đúng 121 nút bấm và 121 nước hợp lệ ban đầu.",
            ],
            [
                "tests/test_ui_app.py",
                "test_click_uses_tuple_action_and_occupied_error_is_atomic",
                "Xác nhận nhấp chuột truyền đúng tuple (5, 5); nhấp lại vào đúng ô (5, 5) hiện cảnh báo 'already occupied' và giữ nguyên trạng thái bàn cờ cùng lịch sử (tính nguyên tử).",
            ],
            [
                "tests/test_ui_app.py",
                "test_new_game_resets_public_state_and_preserves_statistics",
                "Xác nhận nút New Game đưa move_count về 0, xóa lịch sử nước đi nhưng bảo toàn nguyên vẹn bộ đếm thống kê x_wins.",
            ],
            [
                "tests/test_ui_app.py",
                "test_board_size_selector_is_fixed_to_caro_v2_config",
                "Xác nhận hộp chọn kích thước bàn cờ khóa cố định ở tùy chọn '11×11' theo đúng hợp đồng caro-v2.",
            ],
            [
                "tests/test_ui_app.py",
                "test_moves_and_contract_metadata_survive_streamlit_rerun",
                "Xác nhận sau chuỗi 10 nước đi liên tiếp và gọi app.run() (rerun), toàn bộ trạng thái bàn cờ và lịch sử được giữ nguyên.",
            ],
            [
                "tests/test_ui_app.py",
                "test_changing_mode_resets_game_and_toggles_ai_control",
                "Xác nhận khi chuyển giữa Human vs Human và Human vs AI, ván cờ tự động reset và hộp chọn AI Algorithm bật/tắt tương ứng.",
            ],
            [
                "tests/test_ui_app.py",
                "test_x_win_comes_from_engine_disables_board_and_play_again_resets",
                "Giả lập 9 nước đi để X thắng: xác nhận banner 'Player X wins!', toàn bộ 121 ô bị khóa (disabled), stats['x_wins'] tăng lên 1 và nút Play Again khôi phục bàn mới.",
            ],
            [
                "tests/test_ui_app.py",
                "test_o_win_banner_and_history_match_engine_result",
                "Giả lập 10 nước đi để O thắng: xác nhận banner 'Player O wins!', lịch sử khớp tuyệt đối với 10 nước đi và bàn cờ khóa hoàn toàn.",
            ],
            [
                "tests/test_ui_app.py",
                "test_draw_banner_uses_engine_terminal_metadata",
                "Điền kín 121 ô không có chuỗi 5 quân thắng: xác nhận state.winner == None, stats['draws'] == 1 và hiển thị banner hòa.",
            ],
            [
                "tests/test_ui_ai_modes.py",
                "test_all_five_ui_agents_choose_legal_action_without_mutation",
                "Khởi tạo cả 5 tác tử từ factory _create_agent của UI: xác nhận mọi tác tử trả về nước đi hợp lệ và env.state trước/sau choose_action giống hệt nhau.",
            ],
            [
                "tests/test_ui_ai_modes.py",
                "test_human_vs_ai_applies_exactly_one_ai_reply",
                "Trong chế độ Human vs AI, sau khi người chơi nhấp (5, 5), xác nhận move_count == 2 (1 nước người + đúng 1 nước AI đáp trả) và lưu đủ telemetry.",
            ],
            [
                "tests/test_ui_ai_modes.py",
                "test_human_can_choose_o_and_ai_opens_as_x",
                "Khi người chơi chọn cầm quân O, xác nhận AI tự động đánh nước mở màn đầu tiên với tư cách quân X (move_count == 1, lượt kế tiếp là O).",
            ],
            [
                "tests/test_ui_ai_modes.py",
                "test_neural_checkpoint_error_is_clear_and_atomic_for_ai_turn",
                "Khi nhập đường dẫn checkpoint giả không tồn tại, xác nhận UI hiện cảnh báo 'policy checkpoint not found' và giữ nguyên bàn cờ sau nước đi của người chơi.",
            ],
            [
                "tests/test_ui_ai_modes.py",
                "test_terminal_win_highlights_the_complete_winning_line",
                "Xác nhận hàm _winning_cells(env) và _build_dynamic_cell_css(env) tìm đúng 5 tọa độ chiến thắng (5, 1)..(5, 5) và sinh đúng 5 quy tắc tô nền đỏ #FFE3E3.",
            ],
            [
                "tests/test_ui_ai_modes.py",
                "test_ai_vs_ai_finishes_one_game_and_reset_is_clean",
                "Chạy trọn vẹn một ván AI vs AI từ nút Run AI Game đến khi kết thúc: xác nhận ván cờ hoàn tất hợp lệ, thống kê tăng đúng 1 ván và Reset làm sạch hoàn toàn.",
            ],
        ],
        caption_label="Bảng 5.4.",
        caption_text="Tổng hợp các kịch bản kiểm thử tự động giao diện Streamlit bằng AppTest",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
        ],
    )


def fill_chapter_6_and_references(doc: docx.Document) -> None:
    ch6_headings = [
        ("CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", "Heading 1"),
        ("6.1. Kết luận", "Heading 2"),
        ("6.2. Hạn chế", "Heading 2"),
        ("6.3. Hướng phát triển", "Heading 2"),
        ("TÀI LIỆU THAM KHẢO", "Heading 1"),
    ]
    for prefix, style in ch6_headings:
        hp = find_paragraph(doc, prefix, style)
        clear_normal_paragraphs_after_heading(doc, hp)

    # Mở đầu Chương 6
    p_ch6 = find_paragraph(doc, "CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", "Heading 1")
    b_ch6 = SectionBuilder(doc, p_ch6)
    b_ch6.add_paragraph(
        "Chương cuối cùng tổng kết toàn bộ kết quả nghiên cứu, thiết kế và thực nghiệm của đồ án “Xây dựng và đánh giá "
        "các thuật toán trí tuệ nhân tạo cho trò chơi Caro 11 × 11”, đối chiếu tường minh từng mục tiêu đã đặt ra ở "
        "Chương 1 với các bằng chứng định lượng thu được, đồng thời phân tích thẳng thắn những hạn chế hiện tại và đề xuất "
        "lộ trình phát triển tiếp theo."
    )

    # 6.1. Kết luận
    p_61 = find_paragraph(doc, "6.1. Kết luận", "Heading 2")
    b = SectionBuilder(doc, p_61)
    b.add_paragraph(
        "Xuất phát từ bài toán xây dựng tác tử thông minh cho trò chơi đối kháng hai người chơi tổng bằng không có thông tin "
        "hoàn hảo (Zero-Sum Perfect-Information Game) với hệ số phân nhánh lớn trên bàn cờ Caro 11 × 11 (121 ô, thắng khi tạo "
        "chuỗi ≥ 5 quân liên tiếp không bị chặn cả hai đầu), đồ án đã hoàn thành trọn vẹn một nền tảng thực nghiệm Game AI "
        "chuẩn hóa, khép kín từ lõi môi trường, các giải thuật tìm kiếm cổ điển, mô hình học sâu có giám sát cho đến hạ tầng "
        "tổ chức giải đấu tự động và ứng dụng web tương tác."
    )
    b.add_paragraph(
        "Về mặt thực nghiệm khoa học, qua 2.000 ván đấu vòng tròn chính thức của giải đấu W78 (1.000 ván ở profile DEFAULT "
        "và 1.000 ván ở profile FAIR giới hạn 150 ms/nước), các thí nghiệm khảo sát chuyên sâu (Ablation A1, A2) và 1.998 ván "
        "đánh giá mô hình học sâu, đồ án rút ra bốn phát hiện cốt lõi:"
    )
    b.add_bullet(
        "1. Phân hóa sức mạnh rõ rệt nhưng phi tuyến giữa các họ thuật toán",
        "Trong cấu hình giải đấu công bố, MCTS có hướng dẫn chiến thuật (8 simulations kết hợp tactical precheck, mở rộng lũy tiến "
        "heuristic_seeded và rollout ε-heuristic) đạt sức mạnh tổng thể cao nhất với tỷ lệ điểm 81,25% (thắng 306, hòa 38, thua 56 "
        "trên 400 ván). Đứng thứ hai là tác tử học sâu NeuralAgent (Policy v5) với tỷ lệ điểm 64,62% (thắng 205, hòa 107, thua 88), "
        "vượt qua cả HeuristicAgent (54,00%) và MinimaxAgent độ sâu 2 (49,62%), trong khi RandomAgent đứng cuối (0,50%).",
    )
    b.add_bullet(
        "2. Vai trò quyết định của cắt tỉa Alpha-Beta kết hợp sắp xếp nước đi (Move Ordering)",
        "Thực nghiệm Ablation A1 và khảo sát độ sâu chứng minh rằng cắt tỉa Alpha-Beta bảo toàn 100% quyết định của Minimax "
        "nhưng giảm tới 89,07% – 89,60% số nút mở rộng ở giai đoạn trung cuộc tại độ sâu d = 2 (rút ngắn thời gian 3,85 – 4,14 lần). "
        "Khi tăng lên độ sâu d = 3, sự cộng hưởng giữa Alpha-Beta và hàm sắp xếp nước đi action_priority giúp cắt giảm tới 97,52% "
        "số nút so với Alpha-Beta không sắp xếp và 99,48% số nút so với Minimax thuần (từ 94.319 nút xuống 494 nút).",
    )
    b.add_bullet(
        "3. Sự cần thiết của tri thức miền trong MCTS trên không gian hành động lớn",
        "Thí nghiệm Ablation A2 chỉ ra rằng nếu chỉ dùng chính sách mô phỏng ngẫu nhiên thuần túy độ sâu ngắn, việc tăng ngân sách "
        "từ 100 lên 1.000 simulations/nước chỉ giúp MCTS nâng tỷ lệ điểm trước Heuristic từ 0,00% lên 9,17% với chi phí độ trễ "
        "lên tới 345,05 ms/nước. Ngược lại, khi tích hợp tri thức mẫu hình vào bước chọn nhánh ưu tiên và pha rollout ε-greedy, "
        "MCTS đạt tới 74,50% điểm trước Heuristic chỉ với 8 simulations (30,79 ms/nước) và đạt 85,00% điểm ở 64 simulations.",
    )
    b.add_bullet(
        "4. Hiệu quả chưng cất tri thức và ưu thế tốc độ suy luận thời gian thực của mạng PolicyNet",
        "Việc làm sạch rò rỉ đối xứng D4 xuyên tập và giữ phân phối giáo viên tự nhiên (dataset-v5 với 309.136 mẫu train, "
        "trong đó giáo viên mạnh nhất MCTS chiếm 50,66%) giúp mạng PolicyNet (768.537 tham số) tăng +18,02 điểm phần trăm "
        "tỷ lệ điểm đối kháng so với bản cân bằng cứng v2 (từ 35,36% lên 53,38% trên 1.998 ván; đặc biệt bất bại 666/666 ván "
        "trước Heuristic với 75,00% điểm và hòa 50,00% trước Minimax-D2). Hơn thế nữa, một lượt suy luận tiến của NeuralAgent "
        "trên CPU chỉ mất trung bình 3,66 ms (p95 = 5,13 ms) — nhanh hơn 8,4 lần so với MCTS và 10,2 lần so với Minimax, chứng minh "
        "khả năng chuyển giao thành công chi phí tìm kiếm sang pha huấn luyện ngoại tuyến.",
    )
    b.add_paragraph(
        "Để đánh giá toàn diện mức độ hoàn thành đề tài, Bảng 6.1 đối chiếu trực tiếp từng mục tiêu cụ thể đã đề ra tại "
        "Mục 1.2 của Chương 1 với các sản phẩm mã nguồn và bằng chứng nghiệm thu thực tế."
    )
    b.add_table(
        headers=[
            "Mục tiêu đề ra tại Chương 1",
            "Trạng thái",
            "Sản phẩm hiện thực và Bằng chứng nghiệm thu đạt được",
        ],
        rows=[
            [
                "1. Chuẩn hóa luật chơi, trạng thái, hành động và kết quả qua Contract rõ ràng",
                "Hoàn thành 100%",
                "Hợp đồng caro-v2 được khóa tại core/engine/types.py & interfaces.py: bàn cờ 11×11, thắng ≥ 5 quân không bị chặn cả hai đầu, ưu tiên thắng trước hòa ở nước 121, kiểm tra hợp lệ 4 tầng nguyên tử.",
            ],
            [
                "2. Xây dựng Game Engine hỗ trợ reset, step, legal_actions, clone_env, undo tối ưu",
                "Hoàn thành 100%",
                "CaroEnv & RuleEngine đạt độ trễ trung vị step 12,9 µs (kiểm tra cục bộ 4 hướng O(n)), undo 4,1 µs (O(1)) và clone_env 1,2 µs; vượt qua kiểm thử đối chiếu String Oracle trên 3.000 bàn cờ ngẫu nhiên.",
            ],
            [
                "3. Cài đặt các nhóm tác tử AI tuân thủ giao diện chung, không biến đổi môi trường thật và tuân thủ SearchBudget",
                "Hoàn thành 100%",
                "5 tác tử (Random, Heuristic, Minimax/Alpha-Beta, MCTS, NeuralAgent) thực thi đúng giao thức Agent.choose_action, vượt qua 100% kiểm thử hợp đồng W34-T01..T04 và ghi nhận budget_violations = 0 trên cả 2.000 ván giải đấu.",
            ],
            [
                "4. Xây dựng hệ thống giải đấu tự động đổi bên X/O, quản trị seed tái lập 100% và xuất log JSONL",
                "Hoàn thành 100%",
                "TournamentRunner và scripts/run_tournament_w78.py điều phối 10 cặp đấu × 100 ván/profile, ghép cặp hạt giống derive_seed(base_seed=20261111), hỗ trợ resume an toàn và xuất manifest SHA-256.",
            ],
            [
                "5. Xây dựng đường ống dữ liệu self-play và mạng nơ-ron học sâu theo phong cách AlphaZero Policy",
                "Hoàn thành 100%",
                "Pipeline core/ml/data_pipeline.py kiểm định replay 100% của 2.000 ván self-play, cô lập quỹ đạo D4 xuyên tập (dataset-v5: 309.136 mẫu train); mạng PolicyNet ResNet 4 khối (768.537 tham số) đạt Test Top-1 = 52,68%, Top-3 = 81,49%, giải đúng 9/9 thế cờ chiến thuật.",
            ],
            [
                "6. Thực nghiệm kiểm chứng khoa học trả lời các câu hỏi nghiên cứu về sức mạnh và chi phí tính toán",
                "Hoàn thành 100%",
                "Hoàn thành trọn vẹn 2.000 ván giải đấu W78 (DEFAULT & FAIR), 240 quyết định Ablation A1, 180 ván Ablation A2 và 1.998 ván đánh giá PolicyNet; toàn bộ bảng biểu và đồ thị được tái sinh tự động từ raw log.",
            ],
            [
                "7. Xây dựng ứng dụng giao diện web Streamlit trực quan hóa bàn cờ và minh họa thuật toán",
                "Hoàn thành 100%",
                "Ứng dụng ui/app.py hỗ trợ đầy đủ 3 chế độ (Human vs Human, Human vs AI chọn X/O, AI vs AI chạy tự động từng bước), tích hợp cả 5 tác tử thật, tô sáng chuỗi 5 quân thắng và vượt qua 15/15 bài kiểm thử AppTest.",
            ],
        ],
        caption_label="Bảng 6.1.",
        caption_text="Bảng đối chiếu các mục tiêu đề ra ở Chương 1 với kết quả và bằng chứng nghiệm thu thực tế của đồ án",
        col_alignments=[
            WD_ALIGN_PARAGRAPH.LEFT,
            WD_ALIGN_PARAGRAPH.CENTER,
            WD_ALIGN_PARAGRAPH.JUSTIFY,
        ],
    )

    # 6.2. Hạn chế
    p_62 = find_paragraph(doc, "6.2. Hạn chế", "Heading 2")
    b = SectionBuilder(doc, p_62)
    b.add_paragraph(
        "Bên cạnh những kết quả đã đạt được, việc phân tích nghiêm túc các số liệu thực nghiệm cũng giúp nhóm nhận diện rõ "
        "bốn hạn chế kỹ thuật và phương pháp luận của hệ thống hiện tại:"
    )
    b.add_bullet(
        "1. Giới hạn độ sâu của Minimax và thiếu vắng bảng băm chuyển vị (Transposition Table)",
        "Do được cài đặt bằng Python thuần và phải tuân thủ ngân sách thời gian phản hồi nhanh (150 ms/nước trong profile FAIR), "
        "MinimaxAgent trong giải đấu chính chỉ dừng ở độ sâu max_depth = 2. Ở độ sâu này, tác tử chỉ nhìn thấy một cặp nước đi – "
        "đáp trả nên dễ rơi vào hiệu ứng chân trời (horizon effect) trước các đòn phối hợp đa bước của MCTS hoặc bị khai thác "
        "khi cầm quân X đi trước. Đồng thời, cây tìm kiếm hiện tại chưa tích hợp bảng băm Zobrist (Transposition Table) nên vẫn "
        "phải lượng giá lại các trạng thái bàn cờ trùng nhau sinh ra do hoán vị thứ tự nước đi.",
    )
    b.add_bullet(
        "2. Trần năng lực của học có giám sát thuần túy (Behavioral Cloning) ở NeuralAgent",
        "Mạng PolicyNet hiện được huấn luyện hoàn toàn bằng học có giám sát (bắt chước nhãn nước đi của ba tác tử giáo viên "
        "Heuristic, Minimax-D2 và MCTS-S8) mà chưa có nhánh ước lượng giá trị trạng thái (Value Head) hay vòng lặp tự cải thiện "
        "bằng học tăng cường (Reinforcement Learning). Do đó, dù chiến thắng thuyết phục trước Heuristic (75,00%) và cân bằng "
        "với Minimax-D2 (50,00%), NeuralAgent vẫn chịu trần chất lượng của dữ liệu giáo viên và chỉ đạt tỷ lệ điểm 35,14% "
        "(trong bộ 666 ván) đến 36,50% (trong giải đấu W78) khi đối đầu trực tiếp với giáo viên mạnh nhất là MCTS.",
    )
    b.add_bullet(
        "3. Hiện tượng lặp lại quỹ đạo (Trajectory Duplication) giữa các cặp tác tử tất định",
        "Vì cả ba tác tử HeuristicAgent, MinimaxAgent và NeuralAgent đều lựa chọn nước đi theo quy tắc cực đại tất định (argmax) "
        "mà không lấy mẫu theo nhiệt độ xác suất (temperature sampling) ở các nước khai cuộc, nên trong các cặp đấu chỉ gồm hai "
        "tác tử tất định, việc thay đổi hạt giống ngẫu nhiên (paired seeds) vẫn dẫn tới cùng một biên bản ván cờ cho mỗi vai X/O. "
        "Điều này làm giảm số lượng quan sát độc lập thống kê trong các cặp đấu tất định so với các cặp đấu có sự tham gia của "
        "MCTS hoặc Random.",
    )
    b.add_bullet(
        "4. Giới hạn trong phân tích truy vết nước sai đầu tiên (First-Error Attribution)",
        "Các hình chụp thế cờ thất bại (failure snapshots trong thí nghiệm A2) mới chỉ chứng minh được trạng thái tuyệt vọng ở "
        "nước đi cuối cùng — khi đối phương đã hoàn thành đe dọa kép (Double Four hoặc Four-Three) không thể cứu vãn bằng một "
        "nước chặn đơn lẻ — nhưng chưa có công cụ tự động rà soát ngược biên bản ván đấu để chỉ ra chính xác nước đi sai lầm "
        "chiến thuật đầu tiên (root blunder) đã dẫn tới thế thua đó.",
    )

    # 6.3. Hướng phát triển
    p_63 = find_paragraph(doc, "6.3. Hướng phát triển", "Heading 2")
    b = SectionBuilder(doc, p_63)
    b.add_paragraph(
        "Từ nền tảng kiến trúc mô-đun và hợp đồng caro-v2 đã được chuẩn hóa vững chắc, đồ án mở ra bốn hướng nghiên cứu "
        "và phát triển nâng cao rất giàu tiềm năng cho các giai đoạn tiếp theo:"
    )
    b.add_bullet(
        "1. Phát triển mạng kép Policy–Value (Dual-ResNet) kết hợp tìm kiếm cây PUCT theo chuẩn AlphaZero",
        "Bổ sung thêm một nhánh đầu ra giá trị (Value Head: Conv2d 1×1 → Linear → tanh ∈ [-1, +1]) song song với nhánh Policy Head "
        "hiện có trên cùng thân ResNet 4 khối. Khi đó, thay vì sử dụng hàm lượng giá mẫu hình thủ công và rollout ε-heuristic, "
        "MCTS có thể sử dụng trực tiếp phân phối xác suất của Policy Head làm xác suất tiên nghiệm P(s, a) trong công thức PUCT "
        "và dùng Value Head để lượng giá trực tiếp nút lá, tiến tới huấn luyện tự đối kháng lặp (Iterative Self-Play Reinforcement Learning).",
    )
    b.add_bullet(
        "2. Tối ưu hóa chiều sâu tìm kiếm bằng Bảng chuyển vị Zobrist, Tìm kiếm không gian đe dọa (VCF/VCT) và Bitboard",
        "Tích hợp mã băm Zobrist 64-bit cùng bảng chuyển vị (Transposition Table) để lưu đệm kết quả lượng giá các trạng thái "
        "đã thăm qua các tầng Iterative Deepening; đồng thời bổ sung bộ giải chuyên biệt Tìm kiếm Chiến thắng bằng Chuỗi Tứ liên tục "
        "(VCF — Victory by Continuous Four) và Chuỗi Tam liên tục (VCT), kết hợp biểu diễn bàn cờ bằng Bitboard hoặc biên dịch "
        "các hàm quét mẫu hình sang Cython/Rust để đưa độ sâu khả thi của Minimax lên d = 5..6 trong cùng ngân sách 150 ms.",
    )
    b.add_bullet(
        "3. Khai cuộc ngẫu nhiên hóa có kiểm soát (Opening Book / Temperature Sampling) và Công cụ truy vết lỗi tự động",
        "Bổ sung chế độ lấy mẫu Softmax có nhiệt độ τ > 0 trong 2 – 4 nước đi đầu tiên hoặc áp dụng bộ mẫu khai cuộc cân bằng "
        "(Opening Suite / luật mở màn Swap2) trong TournamentRunner để mọi cặp đấu giữa các tác tử tất định đều sinh ra các quỹ đạo "
        "độc lập phong phú. Song song đó, xây dựng kịch bản hậu kiểm (post-game blunder analyzer) chạy tìm kiếm sâu ngược từ cuối "
        "ván về đầu ván để tự động đánh dấu nước đi đầu tiên làm sụt giảm mạnh xác suất thắng.",
    )
    b.add_bullet(
        "4. Mở rộng tính năng trực quan hóa giải thích AI (Explainable AI UI) và đa biến thể luật",
        "Nâng cấp ứng dụng Streamlit với tính năng phát lại biên bản ván đấu (Game Replay) từ tệp JSONL, hiển thị bản đồ nhiệt "
        "(Heatmap) phân phối xác suất Top-k của mạng PolicyNet và tỷ lệ phần trăm số lượt thăm của MCTS ngay trên từng ô bàn cờ, "
        "cùng tùy chọn mở rộng sang bàn cờ 15 × 15 và luật Renju quốc tế thông qua tham số cấu hình GameConfig.",
    )

    # TÀI LIỆU THAM KHẢO
    p_ref = find_paragraph(doc, "TÀI LIỆU THAM KHẢO", "Heading 1")
    b_ref = SectionBuilder(doc, p_ref)
    references = [
        (
            "[1] ",
            "Stuart Russell and Peter Norvig (2020), Artificial Intelligence: A Modern Approach (4th Edition), "
            "Pearson, Chapter 5: Adversarial Search and Games, pp. 146–189.",
        ),
        (
            "[2] ",
            "Cameron B. Browne, Edward Powley, Daniel Whitehouse, Simon M. Lucas, Peter I. Cowling, Philipp Rohlfshagen, "
            "Stephen Tavener, Diego Perez, Spyridon Samothrakis, and Simon Colton (2012), “A Survey of Monte Carlo Tree Search Methods”, "
            "IEEE Transactions on Computational Intelligence and AI in Games, Vol. 4, No. 1, pp. 1–43.",
        ),
        (
            "[3] ",
            "David Silver, Aja Huang, Chris J. Maddison, Arthur Guez, Laurent Sifre, George van den Driessche, "
            "Julian Schrittwieser et al. (2016), “Mastering the game of Go with deep neural networks and tree search”, "
            "Nature, Vol. 529, pp. 484–489.",
        ),
        (
            "[4] ",
            "David Silver, Thomas Hubert, Julian Schrittwieser, Ioannis Antonoglou, Matthew Lai, Arthur Guez, "
            "Marc Lanctot et al. (2018), “A general reinforcement learning algorithm that masters chess, shogi, and Go through self-play”, "
            "Science, Vol. 362, Issue 6419, pp. 1140–1144.",
        ),
        (
            "[5] ",
            "L. Victor Allis, H. J. van den Herik, and M. P. H. Huntjens (1996), “Go-Moku Solved by New Search Techniques”, "
            "Computational Intelligence, Vol. 12, No. 1, pp. 7–23.",
        ),
        (
            "[6] ",
            "Donald E. Knuth and Ronald W. Moore (1975), “An Analysis of Alpha-Beta Pruning”, "
            "Artificial Intelligence, Vol. 6, No. 4, pp. 293–326.",
        ),
        (
            "[7] ",
            "Levente Kocsis and Csaba Szepesvári (2006), “Bandit Based Monte-Carlo Planning”, "
            "Proceedings of the 17th European Conference on Machine Learning (ECML 2006), Lecture Notes in Computer Science, Vol. 4212, pp. 282–293.",
        ),
        (
            "[8] ",
            "Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun (2016), “Deep Residual Learning for Image Recognition”, "
            "Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), pp. 770–778.",
        ),
        (
            "[9] ",
            "Ilya Loshchilov and Frank Hutter (2019), “Decoupled Weight Decay Regularization (AdamW)”, "
            "International Conference on Learning Representations (ICLR 2019).",
        ),
        (
            "[10] ",
            "Edwin B. Wilson (1927), “Probable Inference, the Law of Succession, and Statistical Inference”, "
            "Journal of the American Statistical Association, Vol. 22, No. 158, pp. 209–212.",
        ),
    ]
    for label, ref_text in references:
        b_ref.add_paragraph(ref_text, bold_prefix=label)


def main() -> None:
    if not DOCX_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy file báo cáo: {DOCX_PATH}")

    doc = docx.Document(str(DOCX_PATH))

    print("1. Đang hoàn thiện toàn bộ Chương 5 (Mục 5.1 -> 5.6 + Bảng 5.1..5.4 + Hình 5.1..5.3)...")
    fill_chapter_5(doc)

    print("2. Đang hoàn thiện toàn bộ Chương 6 (Mục 6.1 -> 6.3 + Bảng 6.1) và Tài liệu tham khảo...")
    fill_chapter_6_and_references(doc)

    try:
        doc.save(str(DOCX_PATH))
        print(f"Đã ghi thành công toàn bộ Chương 5, Chương 6 và Tài liệu tham khảo trực tiếp vào: {DOCX_PATH}")
    except PermissionError:
        fallback_path = ROOT_DIR / "Internship_Report - Completed.docx"
        doc.save(str(fallback_path))
        print(
            f"Lưu ý: File '{DOCX_PATH.name}' đang được mở trong Microsoft Word nên bị khóa ghi (PermissionError).\n"
            f"Script đã xuất bản đầy đủ (Chương 1 -> Chương 6 + Tài liệu tham khảo) ra file: {fallback_path}\n"
            f"Sau khi đóng Microsoft Word, bạn có thể chạy lại `python scripts/fill_report_ch5_ch6.py` để ghi đè trực tiếp vào '{DOCX_PATH.name}'."
        )
    print(f"Tổng số đoạn văn sau cập nhật: {len(doc.paragraphs)}, tổng số bảng: {len(doc.tables)}")


if __name__ == "__main__":
    main()
