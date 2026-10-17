from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT_DIR = os.path.join(ROOT, "output", "pdf")
TMP_DIR = os.path.join(ROOT, "tmp", "pdfs")
OUT_FILE = os.path.join(OUT_DIR, "Roadmap_Tong_quan_AI_Caro_8_Tuan.pdf")

PAGE_W, PAGE_H = landscape(A4)

# Palette
NAVY = colors.HexColor("#11263D")
INK = colors.HexColor("#203247")
MUTED = colors.HexColor("#66788A")
BG = colors.HexColor("#F4F7FA")
WHITE = colors.white
LINE = colors.HexColor("#DCE5ED")
CYAN = colors.HexColor("#00A7A5")
CYAN_LIGHT = colors.HexColor("#E7F7F6")
PURPLE = colors.HexColor("#6D5BD0")
PURPLE_LIGHT = colors.HexColor("#F0EDFC")
ORANGE = colors.HexColor("#F08A4B")
ORANGE_LIGHT = colors.HexColor("#FFF0E7")
GREEN = colors.HexColor("#2DA66F")
GREEN_LIGHT = colors.HexColor("#E8F6EF")
RED = colors.HexColor("#D55353")
RED_LIGHT = colors.HexColor("#FCECEC")
YELLOW = colors.HexColor("#F2C14E")
YELLOW_LIGHT = colors.HexColor("#FFF7DD")


def register_fonts() -> None:
    font_dir = r"C:\Windows\Fonts"
    fonts = {
        "UI": "arial.ttf",
        "UI-Bold": "arialbd.ttf",
        "UI-Italic": "ariali.ttf",
    }
    for name, filename in fonts.items():
        pdfmetrics.registerFont(TTFont(name, os.path.join(font_dir, filename)))


register_fonts()


def para(c: canvas.Canvas, text: str, x: float, y_top: float, w: float, h: float,
         size: float = 9, color=INK, font: str = "UI", leading: float | None = None,
         align: int = TA_LEFT) -> float:
    style = ParagraphStyle(
        name="p",
        fontName=font,
        fontSize=size,
        leading=leading or size * 1.28,
        textColor=color,
        alignment=align,
        spaceAfter=0,
        allowWidows=0,
        allowOrphans=0,
    )
    p = Paragraph(text, style)
    _, ph = p.wrap(w, h)
    p.drawOn(c, x, y_top - ph)
    return ph


def round_rect(c: canvas.Canvas, x: float, y: float, w: float, h: float,
               fill, stroke=LINE, radius: float = 4 * mm, line_width: float = 0.7) -> None:
    c.setLineWidth(line_width)
    c.setStrokeColor(stroke)
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def chip(c: canvas.Canvas, text: str, x: float, y: float, fill, color=INK,
         min_w: float = 0, height: float = 6.2 * mm, font_size: float = 7.4) -> float:
    w = max(min_w, c.stringWidth(text, "UI-Bold", font_size) + 5.5 * mm)
    c.setFillColor(fill)
    c.roundRect(x, y, w, height, height / 2, fill=1, stroke=0)
    c.setFillColor(color)
    c.setFont("UI-Bold", font_size)
    c.drawCentredString(x + w / 2, y + 1.8 * mm, text)
    return w


def title_band(c: canvas.Canvas, kicker: str, title: str, subtitle: str, page_no: int) -> None:
    c.setFillColor(NAVY)
    c.rect(0, PAGE_H - 29 * mm, PAGE_W, 29 * mm, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, PAGE_H - 29 * mm, 7 * mm, 29 * mm, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#8DE1DF"))
    c.setFont("UI-Bold", 7.5)
    c.drawString(15 * mm, PAGE_H - 8.5 * mm, kicker.upper())
    c.setFillColor(WHITE)
    c.setFont("UI-Bold", 20)
    c.drawString(15 * mm, PAGE_H - 17 * mm, title)
    c.setFillColor(colors.HexColor("#BFD0DE"))
    c.setFont("UI", 8.4)
    c.drawString(15 * mm, PAGE_H - 23.5 * mm, subtitle)
    c.setFillColor(colors.HexColor("#BFD0DE"))
    c.setFont("UI-Bold", 8)
    c.drawRightString(PAGE_W - 12 * mm, PAGE_H - 15.5 * mm, f"{page_no:02d}")


def footer(c: canvas.Canvas, page_no: int, label: str = "AI CARO - ROADMAP 8 TUẦN") -> None:
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(12 * mm, 10.5 * mm, PAGE_W - 12 * mm, 10.5 * mm)
    c.setFillColor(MUTED)
    c.setFont("UI", 6.8)
    c.drawString(12 * mm, 6.3 * mm, label)
    c.drawRightString(PAGE_W - 12 * mm, 6.3 * mm, f"Trang {page_no}/8")


def bullet_lines(items: Iterable[str]) -> str:
    return "<br/>".join(f"<font color='#00A7A5'>●</font> {item}" for item in items)


def arrow(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, color=CYAN,
          width: float = 2.0) -> None:
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    l = 3.2 * mm
    for d in (2.6, -2.6):
        c.line(x2, y2, x2 - l * math.cos(ang + d), y2 - l * math.sin(ang + d))


def section_label(c: canvas.Canvas, text: str, x: float, y: float, color=CYAN) -> None:
    c.setFillColor(color)
    c.roundRect(x, y - 1.5 * mm, 3 * mm, 3 * mm, 1.5 * mm, fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont("UI-Bold", 9)
    c.drawString(x + 5 * mm, y - 1.1 * mm, text)


def page_cover(c: canvas.Canvas) -> None:
    c.setFillColor(BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.rect(0, 0, 97 * mm, PAGE_H, fill=1, stroke=0)
    c.setFillColor(CYAN)
    c.rect(0, PAGE_H - 8 * mm, 97 * mm, 8 * mm, fill=1, stroke=0)

    c.setFillColor(colors.HexColor("#8DE1DF"))
    c.setFont("UI-Bold", 9)
    c.drawString(13 * mm, PAGE_H - 25 * mm, "ĐỒ ÁN TRÍ TUỆ NHÂN TẠO NÂNG CAO")
    para(c, "ROADMAP<br/>AI CARO", 13 * mm, PAGE_H - 41 * mm, 72 * mm, 48 * mm,
         size=28, color=WHITE, font="UI-Bold", leading=31)
    para(c, "Từ engine đúng luật đến giải đấu tái lập", 13 * mm, PAGE_H - 103 * mm,
         66 * mm, 20 * mm, size=12, color=colors.HexColor("#BFD0DE"), font="UI")

    # Simple gomoku motif
    gx, gy, step = 16 * mm, 26 * mm, 8 * mm
    c.setStrokeColor(colors.HexColor("#36526C"))
    c.setLineWidth(0.7)
    for i in range(8):
        c.line(gx, gy + i * step, gx + 7 * step, gy + i * step)
        c.line(gx + i * step, gy, gx + i * step, gy + 7 * step)
    for i in range(5):
        c.setFillColor(CYAN if i % 2 == 0 else WHITE)
        c.circle(gx + (i + 1) * step, gy + (i + 1) * step, 2.6 * mm, fill=1, stroke=0)

    # Right hand summary
    x0 = 112 * mm
    c.setFillColor(INK)
    c.setFont("UI-Bold", 21)
    c.drawString(x0, PAGE_H - 28 * mm, "8 tuần · 3 người · 5 tác tử")
    para(c, "Một kế hoạch thực thi có dependency, input/output, công cụ, thứ tự commit và cổng nghiệm thu.",
         x0, PAGE_H - 38 * mm, 163 * mm, 18 * mm, size=10, color=MUTED)

    metrics = [
        ("05", "agent bắt buộc", "Random · Heuristic · Alpha-Beta · MCTS · PolicyNet", CYAN_LIGHT, CYAN),
        ("100+", "ván / cặp", "Round-robin · cân bằng lượt · nhiều seed", PURPLE_LIGHT, PURPLE),
        ("02", "ablation tối thiểu", "Cắt tỉa · ngân sách MCTS / policy-guided", ORANGE_LIGHT, ORANGE),
        ("01", "bản demo", "Người-máy · máy-máy · chọn cấp độ", GREEN_LIGHT, GREEN),
    ]
    y = PAGE_H - 70 * mm
    for num, label, desc, fill, accent in metrics:
        round_rect(c, x0, y - 25 * mm, 163 * mm, 21 * mm, fill, stroke=fill, radius=4 * mm)
        c.setFillColor(accent)
        c.setFont("UI-Bold", 19)
        c.drawString(x0 + 6 * mm, y - 15 * mm, num)
        c.setFillColor(INK)
        c.setFont("UI-Bold", 9.2)
        c.drawString(x0 + 30 * mm, y - 10.5 * mm, label)
        c.setFillColor(MUTED)
        c.setFont("UI", 7.8)
        c.drawString(x0 + 30 * mm, y - 16.2 * mm, desc)
        y -= 27 * mm

    # Owner legend
    y0 = 24 * mm
    chip(c, "M1 · Hải · UI + MCTS + NN", x0, y0, CYAN_LIGHT, CYAN, 49 * mm)
    chip(c, "M2 · Ly · Engine + Search", x0 + 53 * mm, y0, PURPLE_LIGHT, PURPLE, 47 * mm)
    chip(c, "M3 · Thiện · Data + Eval", x0 + 104 * mm, y0, ORANGE_LIGHT, ORANGE, 50 * mm)
    c.setFillColor(MUTED)
    c.setFont("UI", 7)
    c.drawRightString(PAGE_W - 12 * mm, 9 * mm, "Phiên bản 1.0 · 17/10/2026")
    c.showPage()


def page_scope(c: canvas.Canvas) -> None:
    c.setFillColor(BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    title_band(c, "01 · CHỐT PHẠM VI", "Đích đến & tiêu chuẩn thành công",
               "Giữ scope vừa đủ để có số liệu thật, demo ổn định và kết quả tái lập.", 2)

    # Decision card
    round_rect(c, 12 * mm, 119 * mm, 80 * mm, 54 * mm, WHITE)
    chip(c, "GATE D0 · CHỐT VỚI GIẢNG VIÊN", 17 * mm, 163 * mm, YELLOW_LIGHT, colors.HexColor("#9B7200"), 66 * mm)
    para(c, "Luật đề xuất", 17 * mm, 155 * mm, 64 * mm, 9 * mm, size=11, font="UI-Bold")
    para(c, bullet_lines([
        "Bàn 9×9, hai người, thông tin đầy đủ",
        "Thắng: ≥5 liên tiếp, không bị chặn cả hai đầu",
        "Không luật cấm; hòa khi hết ô; seed cố định",
        "Game version: <b>caro-v1</b> (đóng băng từ W2)",
    ]), 17 * mm, 144 * mm, 68 * mm, 32 * mm, size=8.2, leading=11)

    # Research cards
    round_rect(c, 99 * mm, 119 * mm, 89 * mm, 54 * mm, CYAN_LIGHT, stroke=CYAN_LIGHT)
    chip(c, "RQ1 · SEARCH", 104 * mm, 163 * mm, WHITE, CYAN, 30 * mm)
    para(c, "Cùng ngân sách thời gian/nước, MCTS có cải thiện score so với Alpha-Beta không?",
         104 * mm, 153 * mm, 76 * mm, 22 * mm, size=11, font="UI-Bold", leading=14)
    para(c, "Đo: W/D/L · score · p95 latency · nodes/simulations", 104 * mm, 130 * mm,
         76 * mm, 9 * mm, size=7.8, color=MUTED)

    round_rect(c, 195 * mm, 119 * mm, 89 * mm, 54 * mm, PURPLE_LIGHT, stroke=PURPLE_LIGHT)
    chip(c, "RQ2 · LEARNING", 200 * mm, 163 * mm, WHITE, PURPLE, 33 * mm)
    para(c, "PolicyNet học từ self-play có vượt Heuristic và cải thiện MCTS khi dẫn hướng không?",
         200 * mm, 153 * mm, 76 * mm, 22 * mm, size=11, font="UI-Bold", leading=14)
    para(c, "Đo: accuracy · learning curve · score · ablation policy-only", 200 * mm, 130 * mm,
         76 * mm, 9 * mm, size=7.8, color=MUTED)

    # Definition of done bands
    section_label(c, "4 lớp sản phẩm phải đồng thời hoàn tất", 12 * mm, 108 * mm)
    cards = [
        ("01", "ENGINE", "API chuẩn · luật đúng · clone/undo · test biên", CYAN, CYAN_LIGHT),
        ("02", "AGENTS", "4 search/baseline + 1 agent học có checkpoint", PURPLE, PURPLE_LIGHT),
        ("03", "EVIDENCE", "100+ ván/cặp · 2 ablation · CI · raw logs", ORANGE, ORANGE_LIGHT),
        ("04", "DELIVERY", "Demo · report · slide · poster · README · ZIP", GREEN, GREEN_LIGHT),
    ]
    x = 12 * mm
    for num, name, body, accent, fill in cards:
        round_rect(c, x, 62 * mm, 64 * mm, 38 * mm, fill, stroke=fill)
        c.setFillColor(accent); c.setFont("UI-Bold", 17); c.drawString(x + 5 * mm, 88 * mm, num)
        c.setFillColor(INK); c.setFont("UI-Bold", 10); c.drawString(x + 17 * mm, 89 * mm, name)
        para(c, body, x + 5 * mm, 80 * mm, 54 * mm, 16 * mm, size=8.2, color=MUTED)
        x += 69 * mm

    # Tool stack
    section_label(c, "Stack tối giản", 12 * mm, 51 * mm, PURPLE)
    tool_groups = [
        ("Core", "Python · NumPy · pytest"),
        ("Search", "dataclass · time · cProfile"),
        ("Learn", "PyTorch · TensorBoard"),
        ("Data", "Pandas · Parquet/CSV"),
        ("Eval", "SciPy · psutil · Matplotlib"),
        ("Demo/CI", "Streamlit · GitHub Actions"),
    ]
    x = 12 * mm
    for head, tools in tool_groups:
        round_rect(c, x, 20 * mm, 43 * mm, 24 * mm, WHITE, radius=3 * mm)
        c.setFillColor(INK); c.setFont("UI-Bold", 8.2); c.drawString(x + 4 * mm, 36 * mm, head)
        para(c, tools, x + 4 * mm, 31 * mm, 35 * mm, 9 * mm, size=7, color=MUTED)
        x += 46 * mm
    footer(c, 2)
    c.showPage()


def page_architecture(c: canvas.Canvas) -> None:
    c.setFillColor(BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    title_band(c, "02 · KIẾN TRÚC", "Một hợp đồng - nhiều tác tử - một pipeline đánh giá",
               "Mọi module chỉ giao tiếp qua GameState, Action và Agent.choose_action().", 3)

    # Central flow
    boxes = [
        (15, 131, 46, 31, "GAME ENGINE", "state · rules · terminal", CYAN, CYAN_LIGHT),
        (78, 131, 46, 31, "AGENT API", "choose_action(state, budget)", PURPLE, PURPLE_LIGHT),
        (141, 131, 46, 31, "SELF-PLAY", "trajectory · label · seed", ORANGE, ORANGE_LIGHT),
        (204, 131, 46, 31, "TRAIN", "policy · checkpoint · config", GREEN, GREEN_LIGHT),
    ]
    for x, y, w, h, head, sub, accent, fill in boxes:
        round_rect(c, x * mm, y * mm, w * mm, h * mm, fill, stroke=fill)
        c.setFillColor(accent); c.roundRect((x + 5) * mm, (y + 20) * mm, 7 * mm, 7 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont("UI-Bold", 9.2); c.drawString((x + 16) * mm, (y + 23) * mm, head)
        para(c, sub, (x + 5) * mm, (y + 17) * mm, (w - 10) * mm, 9 * mm, size=7.2, color=MUTED, align=TA_CENTER)
    for x1, x2 in [(61, 78), (124, 141), (187, 204)]:
        arrow(c, x1 * mm, 146.5 * mm, (x2 - 3) * mm, 146.5 * mm, CYAN)
    # feedback
    c.setStrokeColor(PURPLE); c.setLineWidth(1.6); c.setDash(3, 2)
    c.line(227 * mm, 129 * mm, 227 * mm, 119 * mm)
    c.line(227 * mm, 119 * mm, 101 * mm, 119 * mm)
    c.line(101 * mm, 119 * mm, 101 * mm, 128 * mm)
    c.setDash()
    para(c, "checkpoint -> PolicyAgent / policy-guided MCTS", 133 * mm, 117 * mm, 80 * mm, 8 * mm,
         size=7.2, color=PURPLE, font="UI-Bold", align=TA_CENTER)

    # Agent fan-out
    section_label(c, "Agent implementations", 15 * mm, 106 * mm, PURPLE)
    agents = [
        ("RANDOM", "uniform legal", ORANGE_LIGHT, ORANGE),
        ("HEURISTIC", "win · block · position", PURPLE_LIGHT, PURPLE),
        ("ALPHA-BETA", "depth · eval · prune", CYAN_LIGHT, CYAN),
        ("MCTS", "UCT · rollout · budget", GREEN_LIGHT, GREEN),
        ("POLICYNET", "board tensor -> policy", YELLOW_LIGHT, colors.HexColor("#A87800")),
    ]
    x = 15 * mm
    for name, sub, fill, accent in agents:
        round_rect(c, x, 77 * mm, 49 * mm, 22 * mm, fill, stroke=fill, radius=3 * mm)
        c.setFillColor(accent); c.setFont("UI-Bold", 8); c.drawCentredString(x + 24.5 * mm, 91 * mm, name)
        c.setFillColor(MUTED); c.setFont("UI", 6.7); c.drawCentredString(x + 24.5 * mm, 83 * mm, sub)
        x += 53 * mm

    # contracts table-like cards
    section_label(c, "Hợp đồng dữ liệu đóng băng ở cuối W2", 15 * mm, 66 * mm, CYAN)
    contracts = [
        ("STATE", "board[int8, 9,9]\ncurrent_player · last_move", CYAN),
        ("ACTION", "int 0..80 <-> (row,col)\nlegal mask[81]", PURPLE),
        ("STEP", "next_state · reward · done\nreject illegal action", ORANGE),
        ("TRACE", "game_id · ply · seed · agent\nmove_ms · nodes/sims · result", GREEN),
    ]
    x = 15 * mm
    for head, body, accent in contracts:
        round_rect(c, x, 25 * mm, 62 * mm, 32 * mm, WHITE, radius=3 * mm)
        c.setFillColor(accent); c.setFont("UI-Bold", 8.4); c.drawString(x + 4 * mm, 48 * mm, head)
        para(c, body.replace("\n", "<br/>"), x + 4 * mm, 43 * mm, 54 * mm, 15 * mm, size=7.1, color=MUTED)
        x += 66 * mm

    footer(c, 3)
    c.showPage()


@dataclass
class Task:
    owner: str
    title: str
    inp: str
    out: str
    tools: str
    accent: colors.Color
    fill: colors.Color


def owner_card(c: canvas.Canvas, t: Task, x: float, y: float, w: float, h: float) -> None:
    round_rect(c, x, y, w, h, WHITE, radius=3.5 * mm)
    c.setFillColor(t.accent)
    c.roundRect(x, y + h - 12 * mm, w, 12 * mm, 3.5 * mm, fill=1, stroke=0)
    c.rect(x, y + h - 12 * mm, w, 6 * mm, fill=1, stroke=0)
    c.setFillColor(WHITE); c.setFont("UI-Bold", 9)
    c.drawString(x + 5 * mm, y + h - 8 * mm, t.owner)
    para(c, t.title, x + 5 * mm, y + h - 16 * mm, w - 10 * mm, 15 * mm, size=9.1, font="UI-Bold", leading=11)
    labels = [("IN", t.inp), ("OUT", t.out), ("TOOL", t.tools)]
    yy = y + h - 34 * mm
    for label, value in labels:
        c.setFillColor(t.fill)
        c.roundRect(x + 5 * mm, yy - 3.5 * mm, 12 * mm, 6 * mm, 2 * mm, fill=1, stroke=0)
        c.setFillColor(t.accent); c.setFont("UI-Bold", 6.6)
        c.drawCentredString(x + 11 * mm, yy - 1.5 * mm, label)
        para(c, value, x + 20 * mm, yy + 2.1 * mm, w - 25 * mm, 10 * mm, size=6.9, color=MUTED, leading=8.2)
        yy -= 12.5 * mm


def week_page(c: canvas.Canvas, page_no: int, week: int, phase: str, objective: str,
              tasks: list[Task], inputs: str, outputs: str, order: list[str],
              gate: str, risk: str, top_tools: str) -> None:
    c.setFillColor(BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    title_band(c, f"TUẦN {week:02d} · {phase}", f"W{week} — {objective}",
               f"Input chung: {inputs}   |   Output chung: {outputs}", page_no)
    # dependency and sprint banner
    round_rect(c, 12 * mm, 155 * mm, 272 * mm, 17 * mm, NAVY, stroke=NAVY, radius=3 * mm)
    c.setFillColor(colors.HexColor("#8DE1DF")); c.setFont("UI-Bold", 7.6)
    c.drawString(17 * mm, 165 * mm, "SPRINT STACK")
    c.setFillColor(WHITE); c.setFont("UI", 8)
    c.drawString(48 * mm, 165 * mm, top_tools)

    xs = [12 * mm, 104 * mm, 196 * mm]
    for t, x in zip(tasks, xs):
        owner_card(c, t, x, 80 * mm, 88 * mm, 68 * mm)

    # commit train
    section_label(c, "Thứ tự commit / merge", 12 * mm, 70 * mm, CYAN)
    n = len(order)
    x0, total_w = 12 * mm, 272 * mm
    gap = 4 * mm
    bw = (total_w - gap * (n - 1)) / n
    palette = [(CYAN, CYAN_LIGHT), (PURPLE, PURPLE_LIGHT), (ORANGE, ORANGE_LIGHT), (GREEN, GREEN_LIGHT), (NAVY, colors.HexColor("#E9EEF3"))]
    for i, item in enumerate(order):
        accent, fill = palette[i % len(palette)]
        x = x0 + i * (bw + gap)
        round_rect(c, x, 42 * mm, bw, 20 * mm, fill, stroke=fill, radius=3 * mm)
        c.setFillColor(accent); c.setFont("UI-Bold", 8)
        c.drawString(x + 4 * mm, 55 * mm, f"{i+1:02d}")
        para(c, item, x + 13 * mm, 57 * mm, bw - 16 * mm, 13 * mm, size=6.8, color=INK, font="UI-Bold", leading=8)
        if i < n - 1:
            arrow(c, x + bw + 0.8 * mm, 52 * mm, x + bw + gap - 0.8 * mm, 52 * mm, accent, 1.1)

    # gate and risk
    round_rect(c, 12 * mm, 16 * mm, 181 * mm, 19 * mm, GREEN_LIGHT, stroke=GREEN_LIGHT, radius=3 * mm)
    c.setFillColor(GREEN); c.setFont("UI-Bold", 7.5); c.drawString(17 * mm, 28 * mm, "GATE / DONE")
    para(c, gate, 46 * mm, 30.3 * mm, 140 * mm, 12 * mm, size=7.1, color=INK, font="UI-Bold", leading=8.2)
    round_rect(c, 198 * mm, 16 * mm, 86 * mm, 19 * mm, RED_LIGHT, stroke=RED_LIGHT, radius=3 * mm)
    c.setFillColor(RED); c.setFont("UI-Bold", 7.5); c.drawString(203 * mm, 28 * mm, "RỦI RO")
    para(c, risk, 220 * mm, 30.3 * mm, 58 * mm, 12 * mm, size=6.8, color=INK, leading=8)
    footer(c, page_no)
    c.showPage()


def page_weeks_1_2(c: canvas.Canvas) -> None:
    # This pair is handled as one foundation page to keep the PDF concise.
    c.setFillColor(BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    title_band(c, "GIAI ĐOẠN 1 · W1-W2", "Nền tảng: chốt luật, khóa API, chứng minh engine đúng",
               "Nguyên tắc: tests/spec đi trước; UI và agents không đọc trực tiếp cấu trúc nội bộ của engine.", 4)

    # Timeline rail
    for x, week, title, accent in [(12, "W1", "CONTRACT + SKELETON", CYAN), (151, "W2", "RULES + INTEGRATION", PURPLE)]:
        c.setFillColor(accent); c.roundRect(x * mm, 158 * mm, 128 * mm, 12 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("UI-Bold", 9); c.drawString((x + 5) * mm, 162 * mm, f"{week}  ·  {title}")

    def mini_task(x, y, owner, title, io, tools, accent, fill):
        round_rect(c, x, y, 128 * mm, 31 * mm, WHITE, radius=3 * mm)
        c.setFillColor(accent); c.roundRect(x, y, 26 * mm, 31 * mm, 3 * mm, fill=1, stroke=0)
        c.rect(x + 13 * mm, y, 13 * mm, 31 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("UI-Bold", 8.2); c.drawCentredString(x + 13 * mm, y + 17 * mm, owner)
        para(c, title, x + 31 * mm, y + 26 * mm, 91 * mm, 9 * mm, size=8.3, font="UI-Bold")
        para(c, f"<font color='#66788A'>{io}</font><br/><font color='#66788A'><b>Tool:</b> {tools}</font>",
             x + 31 * mm, y + 17 * mm, 91 * mm, 14 * mm, size=6.7, leading=8)

    # W1
    mini_task(12 * mm, 118 * mm, "M3", "Đặc tả API + test vector",
              "IN: đề bài, luật nháp  |  OUT: interfaces.py, cases JSON", "pytest · dataclass", ORANGE, ORANGE_LIGHT)
    mini_task(12 * mm, 81 * mm, "M2", "Board/state + legal move skeleton",
              "IN: contract M3  |  OUT: reset/step/clone khung", "Python · NumPy", PURPLE, PURPLE_LIGHT)
    mini_task(12 * mm, 44 * mm, "M1", "Wireframe UI + adapter mock",
              "IN: state/action schema  |  OUT: bàn cờ click được", "Streamlit · Figma tùy chọn", CYAN, CYAN_LIGHT)
    # W2
    mini_task(151 * mm, 118 * mm, "M2", "Luật thắng/hòa + terminal + undo",
              "IN: test vector  |  OUT: caro-v1 engine", "NumPy · profiling", PURPLE, PURPLE_LIGHT)
    mini_task(151 * mm, 81 * mm, "M3", "Unit + property tests + CI",
              "IN: caro-v1  |  OUT: ≥90% core coverage, CI xanh", "pytest · coverage · Actions", ORANGE, ORANGE_LIGHT)
    mini_task(151 * mm, 44 * mm, "M1", "UI nối engine thật + HumanAgent",
              "IN: API đóng băng  |  OUT: người-người chạy được", "Streamlit · session_state", CYAN, CYAN_LIGHT)

    # Bottom commit flow
    section_label(c, "Merge train & cổng chất lượng", 12 * mm, 35 * mm, GREEN)
    flow = ["M3 spec/tests", "M2 engine", "M3 CI/regression", "M1 UI adapter", "tag caro-v1"]
    x = 12 * mm
    widths = [39, 38, 44, 41, 38]
    for i, (s, w) in enumerate(zip(flow, widths)):
        fill = [ORANGE_LIGHT, PURPLE_LIGHT, ORANGE_LIGHT, CYAN_LIGHT, GREEN_LIGHT][i]
        accent = [ORANGE, PURPLE, ORANGE, CYAN, GREEN][i]
        chip(c, f"{i+1} · {s}", x, 16 * mm, fill, accent, w * mm, 7 * mm, 7)
        x += (w + 4) * mm
    para(c, "DONE: 0 nước đi bất hợp lệ · 6 hướng thắng/biên được test · clone/undo không đổi state · UI hoàn tất 1 ván.",
         12 * mm, 14 * mm, 272 * mm, 7 * mm, size=7.1, color=MUTED, align=TA_CENTER)
    footer(c, 4)
    c.showPage()


def page_weeks_3_4(c: canvas.Canvas) -> None:
    c.setFillColor(BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    title_band(c, "GIAI ĐOẠN 2 · W3-W4", "AI cơ bản: baseline -> chiến thuật -> tìm kiếm",
               "Cùng Agent API; budget được truyền từ runner để so sánh công bằng.", 5)

    # Column headers
    for x, label, sub, accent in [
        (12, "W3 · ĐÚNG TRƯỚC", "agent logic + smoke tournament", CYAN),
        (151, "W4 · NHANH & ĐO ĐƯỢC", "optimization + instrumentation", PURPLE),
    ]:
        c.setFillColor(accent); c.roundRect(x * mm, 158 * mm, 128 * mm, 12 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("UI-Bold", 9); c.drawString((x + 5) * mm, 162 * mm, label)
        c.setFont("UI", 6.7); c.drawRightString((x + 123) * mm, 162 * mm, sub)

    # Matrix per owner
    rows = [
        ("M1", "MCTS khung: Node, UCT, expand, rollout", "IN: caro-v1 · OUT: MCTS + tests · Tool: NumPy/pytest",
         "MCTS hoàn chỉnh: backprop, seed, budget", "OUT: config + benchmark · Tool: cProfile/time", CYAN, CYAN_LIGHT),
        ("M2", "Heuristic: win > block > threat > center", "IN: caro-v1 · OUT: agent + tests · Tool: NumPy/pytest",
         "Alpha-Beta + eval + move ordering", "OUT: agent + counters · Tool: cProfile/cache", PURPLE, PURPLE_LIGHT),
        ("M3", "RandomAgent + metrics schema + runner smoke", "IN: Agent API · OUT: runner smoke · Tool: pytest/JSONL",
         "timer/nodes/sims + budget enforcer", "OUT: budget runner · Tool: psutil/time", ORANGE, ORANGE_LIGHT),
    ]
    y = 119 * mm
    for owner, left, left_meta, right, right_meta, accent, fill in rows:
        # owner badge
        c.setFillColor(accent); c.roundRect(12 * mm, y, 17 * mm, 31 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("UI-Bold", 9); c.drawCentredString(20.5 * mm, y + 16 * mm, owner)
        round_rect(c, 32 * mm, y, 108 * mm, 31 * mm, WHITE, radius=3 * mm)
        para(c, left, 38 * mm, y + 25 * mm, 96 * mm, 13 * mm, size=8.2, font="UI-Bold")
        para(c, left_meta, 38 * mm, y + 10 * mm, 96 * mm, 7 * mm, size=6.4, color=MUTED)
        c.setFillColor(accent); c.roundRect(151 * mm, y, 17 * mm, 31 * mm, 3 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("UI-Bold", 9); c.drawCentredString(159.5 * mm, y + 16 * mm, owner)
        round_rect(c, 171 * mm, y, 108 * mm, 31 * mm, WHITE, radius=3 * mm)
        para(c, right, 177 * mm, y + 25 * mm, 96 * mm, 13 * mm, size=8.2, font="UI-Bold")
        para(c, right_meta, 177 * mm, y + 10 * mm, 96 * mm, 7 * mm, size=6.4, color=MUTED)
        y -= 37 * mm

    # Budgets and ablation preview
    section_label(c, "Cấu hình benchmark khóa ở cuối W4", 12 * mm, 44 * mm, GREEN)
    configs = [
        ("FAST", "100 ms/nước", "UI/demo"),
        ("FAIR", "500 ms/nước", "RQ1 chính"),
        ("MCTS-S", "100/400/1000 sims", "sensitivity"),
        ("AB-D", "depth 2/3/4", "sensitivity"),
    ]
    x = 12 * mm
    for name, val, use in configs:
        round_rect(c, x, 17 * mm, 51 * mm, 21 * mm, WHITE, radius=3 * mm)
        c.setFillColor(INK); c.setFont("UI-Bold", 7.6); c.drawString(x + 4 * mm, 31 * mm, name)
        c.setFillColor(CYAN); c.setFont("UI-Bold", 8.5); c.drawRightString(x + 47 * mm, 31 * mm, val)
        c.setFillColor(MUTED); c.setFont("UI", 6.7); c.drawString(x + 4 * mm, 22 * mm, use)
        x += 56 * mm
    round_rect(c, 238 * mm, 17 * mm, 46 * mm, 21 * mm, GREEN_LIGHT, stroke=GREEN_LIGHT, radius=3 * mm)
    para(c, "DONE<br/><b>5 agents chạy qua cùng runner; seed lặp lại cho cùng chuỗi.</b>", 242 * mm, 34 * mm,
         38 * mm, 16 * mm, size=6.9, color=GREEN, align=TA_CENTER)
    footer(c, 5)
    c.showPage()


def page_weeks_5_6(c: canvas.Canvas) -> None:
    c.setFillColor(BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    title_band(c, "GIAI ĐOẠN 3 · W5-W6", "Dữ liệu & PolicyNet: từ self-play đến checkpoint dùng được",
               "Tách theo game_id, không theo từng trạng thái; test set không dùng để chọn siêu tham số.", 6)

    # Pipeline
    pipe = [
        ("SELF-PLAY", "Heuristic ↔ MCTS", ORANGE, ORANGE_LIGHT),
        ("CLEAN", "dedup · symmetry · validate", CYAN, CYAN_LIGHT),
        ("SPLIT", "70/15/15 by game", PURPLE, PURPLE_LIGHT),
        ("TRAIN", "CE loss · early stop", GREEN, GREEN_LIGHT),
        ("EXPORT", "best.pt + config", NAVY, colors.HexColor("#E9EEF3")),
    ]
    x = 12 * mm
    for i, (head, sub, accent, fill) in enumerate(pipe):
        round_rect(c, x, 143 * mm, 47 * mm, 25 * mm, fill, stroke=fill, radius=3 * mm)
        c.setFillColor(accent); c.setFont("UI-Bold", 8.2); c.drawCentredString(x + 23.5 * mm, 158 * mm, head)
        c.setFillColor(MUTED); c.setFont("UI", 6.6); c.drawCentredString(x + 23.5 * mm, 150 * mm, sub)
        if i < len(pipe) - 1:
            arrow(c, x + 48 * mm, 155.5 * mm, x + 52 * mm, 155.5 * mm, accent, 1.1)
        x += 55 * mm

    # Week two-column cards
    section_label(c, "W5 · Sinh dữ liệu v1", 12 * mm, 132 * mm, ORANGE)
    section_label(c, "W6 · Train, kiểm định, tích hợp", 151 * mm, 132 * mm, GREEN)
    items = [
        (12, 97, "M3", "Schema trajectory + self-play runner", "IN: agents-v1 · OUT: raw JSONL + manifest · Tool: multiprocessing", ORANGE, ORANGE_LIGHT),
        (12, 64, "M2", "Tối ưu agent sinh nhãn + cache", "IN: profiler W4 · OUT: throughput/config · Tool: cProfile", PURPLE, PURPLE_LIGHT),
        (12, 31, "M1", "Board encoder + PolicyNet + loss", "IN: state/mask schema · OUT: model + smoke · Tool: PyTorch", CYAN, CYAN_LIGHT),
        (151, 97, "M3", "Dedup + split theo game + data card", "IN: raw JSONL · OUT: dataset-v1/checksum · Tool: Pandas", ORANGE, ORANGE_LIGHT),
        (151, 64, "M1", "Train loop + TensorBoard + checkpoint", "IN: dataset-v1 · OUT: best.pt/curves · Tool: PyTorch/TB", CYAN, CYAN_LIGHT),
        (151, 31, "M2", "PolicyAgent adapter + tactical sanity", "IN: best.pt · OUT: legal-mask agent · Tool: pytest/benchmark", PURPLE, PURPLE_LIGHT),
    ]
    for x_mm, y_mm, owner, title, out, accent, fill in items:
        round_rect(c, x_mm * mm, y_mm * mm, 128 * mm, 27 * mm, WHITE, radius=3 * mm)
        chip(c, owner, (x_mm + 5) * mm, (y_mm + 15.5) * mm, fill, accent, 14 * mm, 6 * mm, 7)
        para(c, title, (x_mm + 23) * mm, (y_mm + 23) * mm, 97 * mm, 9 * mm, size=8.1, font="UI-Bold")
        para(c, out, (x_mm + 23) * mm, (y_mm + 11) * mm, 97 * mm, 8 * mm, size=6.2, color=MUTED)

    # Merge order and gate
    round_rect(c, 12 * mm, 14 * mm, 272 * mm, 12 * mm, NAVY, stroke=NAVY, radius=3 * mm)
    para(c, "MERGE:  1 M3 schema  →  2 M2 export/config  →  3 M3 dataset-v1  →  4 M1 train  →  5 M2 PolicyAgent  →  6 tag model-v1",
         18 * mm, 22 * mm, 260 * mm, 8 * mm, size=7.4, color=WHITE, font="UI-Bold", align=TA_CENTER)
    footer(c, 6)
    c.showPage()


def page_week_7(c: canvas.Canvas) -> None:
    c.setFillColor(BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    title_band(c, "GIAI ĐOẠN 4 · W7", "Thực nghiệm: freeze trước, chạy sau, phân tích cuối",
               "Không chỉnh agent sau khi xem kết quả test cuối; mọi biểu đồ phải sinh lại từ raw logs.", 7)

    # 3-step flow
    steps = [
        ("1", "FREEZE", "caro-v1 · agents-v1 · model-v1\nconfig + hardware + seeds", CYAN, CYAN_LIGHT),
        ("2", "RUN", "round-robin ≥100 ván/cặp\n50% đi trước · nhiều seed", PURPLE, PURPLE_LIGHT),
        ("3", "ANALYZE", "matrix · CI · latency p95\nlearning curve · failure cases", ORANGE, ORANGE_LIGHT),
    ]
    x = 12 * mm
    for i, (num, head, body, accent, fill) in enumerate(steps):
        round_rect(c, x, 133 * mm, 82 * mm, 35 * mm, fill, stroke=fill, radius=4 * mm)
        c.setFillColor(accent); c.circle(x + 10 * mm, 156 * mm, 5 * mm, fill=1, stroke=0)
        c.setFillColor(WHITE); c.setFont("UI-Bold", 9); c.drawCentredString(x + 10 * mm, 153.5 * mm, num)
        c.setFillColor(INK); c.setFont("UI-Bold", 10); c.drawString(x + 20 * mm, 157 * mm, head)
        para(c, body.replace("\n", "<br/>"), x + 8 * mm, 148 * mm, 66 * mm, 16 * mm, size=7.4, color=MUTED, align=TA_CENTER)
        if i < 2:
            arrow(c, x + 84 * mm, 150.5 * mm, x + 91 * mm, 150.5 * mm, accent, 1.5)
        x += 95 * mm

    # Responsibility cards
    section_label(c, "Ai làm gì", 12 * mm, 121 * mm, CYAN)
    resp = [
        ("M3 · OWNER RUNNER", "IN: tags/config/seeds. OUT: raw log + matrix + CI.<br/><b>Tool:</b> tournament.py · Pandas · SciPy", ORANGE, ORANGE_LIGHT),
        ("M2 · OWNER ABLATION", "IN: frozen agents. OUT: A1 pruning ON/OFF; A2 100/400/1000 sims.<br/><b>Tool:</b> runner · cProfile", PURPLE, PURPLE_LIGHT),
        ("M1 · OWNER MODEL/UI", "IN: best.pt + logs. OUT: curves, cost chart, 4 case boards.<br/><b>Tool:</b> TensorBoard · psutil · Matplotlib", CYAN, CYAN_LIGHT),
    ]
    x = 12 * mm
    for head, body, accent, fill in resp:
        round_rect(c, x, 78 * mm, 86 * mm, 35 * mm, WHITE, radius=3 * mm)
        chip(c, head, x + 5 * mm, 101 * mm, fill, accent, 58 * mm, 6.5 * mm, 6.8)
        para(c, body, x + 5 * mm, 96 * mm, 76 * mm, 18 * mm, size=6.8, color=MUTED, leading=8.2)
        x += 92 * mm

    # Result matrix schematic
    section_label(c, "Gói bằng chứng phải có", 12 * mm, 68 * mm, GREEN)
    evidence = [
        ("RAW", "games.jsonl\nmoves.parquet", CYAN_LIGHT, CYAN),
        ("MATRIX", "W/D/L + score\nfirst-player split", PURPLE_LIGHT, PURPLE),
        ("COST", "mean/p95 ms\nnodes · sims · RAM", ORANGE_LIGHT, ORANGE),
        ("STATS", "Wilson 95% CI\nseed sensitivity", GREEN_LIGHT, GREEN),
        ("CASES", "2 thắng · 2 lỗi\nboard snapshots", YELLOW_LIGHT, colors.HexColor("#A87800")),
    ]
    x = 12 * mm
    for head, body, fill, accent in evidence:
        round_rect(c, x, 35 * mm, 49 * mm, 25 * mm, fill, stroke=fill, radius=3 * mm)
        c.setFillColor(accent); c.setFont("UI-Bold", 8); c.drawCentredString(x + 24.5 * mm, 51 * mm, head)
        para(c, body.replace("\n", "<br/>"), x + 4 * mm, 46 * mm, 41 * mm, 12 * mm, size=6.8, color=MUTED, align=TA_CENTER)
        x += 54 * mm
    round_rect(c, 12 * mm, 15 * mm, 272 * mm, 13 * mm, GREEN_LIGHT, stroke=GREEN_LIGHT, radius=3 * mm)
    para(c, "DONE: một lệnh tái chạy được bảng/hình từ log; kết luận RQ1/RQ2 có số liệu và nêu giới hạn.",
         18 * mm, 24 * mm, 260 * mm, 8 * mm, size=7.5, color=GREEN, font="UI-Bold", align=TA_CENTER)
    footer(c, 7)
    c.showPage()


def page_week8_git(c: canvas.Canvas) -> None:
    c.setFillColor(BG); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    title_band(c, "GIAI ĐOẠN 5 · W8", "Đóng gói: kể đúng câu chuyện, giao đúng bằng chứng",
               "Chỉ dùng số liệu đã khóa ở W7; release candidate phải cài và chạy được trên máy sạch.", 8)

    # Workstream cards
    streams = [
        ("M1 · HẢI", "IN: model/results-v1\nOUT: Ch.3 + demo + video\nTool: Streamlit · OBS", CYAN, CYAN_LIGHT),
        ("M2 · LY", "IN: search logs/cases\nOUT: Ch.2/3 + tactical analysis\nTool: Markdown/Word · review", PURPLE, PURPLE_LIGHT),
        ("M3 · THIỆN", "IN: locked raw logs\nOUT: Ch.4 + README + ZIP\nTool: Pandas · GitHub · checksum", ORANGE, ORANGE_LIGHT),
    ]
    x = 12 * mm
    for head, body, accent, fill in streams:
        round_rect(c, x, 130 * mm, 86 * mm, 38 * mm, WHITE, radius=4 * mm)
        chip(c, head, x + 5 * mm, 157 * mm, fill, accent, 31 * mm, 7 * mm, 7.5)
        para(c, body.replace("\n", "<br/>"), x + 6 * mm, 151 * mm, 74 * mm, 22 * mm,
             size=7.7, color=MUTED, leading=9.5)
        x += 92 * mm

    # Git integration rail
    section_label(c, "Workflow Git - ai commit trước, ai merge sau", 12 * mm, 119 * mm, CYAN)
    flow = [
        ("A", "M3 khóa results", "tag results-v1", ORANGE, ORANGE_LIGHT),
        ("B", "M1/M2 viết phần", "PR nhỏ + hình nguồn", CYAN, CYAN_LIGHT),
        ("C", "M3 tích hợp", "resolve + link assets", PURPLE, PURPLE_LIGHT),
        ("D", "M1 chạy demo", "fresh install smoke", GREEN, GREEN_LIGHT),
        ("E", "M2 review kỹ thuật", "rules/search/numbers", NAVY, colors.HexColor("#E9EEF3")),
        ("F", "M3 release", "v1.0 + ZIP checksum", ORANGE, ORANGE_LIGHT),
    ]
    x = 12 * mm
    for i, (letter, head, sub, accent, fill) in enumerate(flow):
        round_rect(c, x, 82 * mm, 40 * mm, 27 * mm, fill, stroke=fill, radius=3 * mm)
        c.setFillColor(accent); c.setFont("UI-Bold", 12); c.drawCentredString(x + 7 * mm, 96 * mm, letter)
        para(c, head, x + 14 * mm, 103 * mm, 22 * mm, 10 * mm, size=6.8, font="UI-Bold", leading=7.8)
        para(c, sub, x + 4 * mm, 91 * mm, 32 * mm, 8 * mm, size=6.2, color=MUTED, align=TA_CENTER)
        if i < 5:
            arrow(c, x + 41 * mm, 95 * mm, x + 45 * mm, 95 * mm, accent, 1.0)
        x += 46 * mm

    # Rubric checklist
    section_label(c, "Pre-flight 100 điểm", 12 * mm, 70 * mm, GREEN)
    rubrics = [
        ("10", "Game", "luật · I/O · RQ"),
        ("15", "System", "API · UI · tests"),
        ("20", "Search", "4 agents đúng"),
        ("15", "Learn", "train · ckpt"),
        ("15", "Eval", "fair · 2 ablation"),
        ("10", "Discuss", "CI · failures"),
        ("10", "Present", "report · demo"),
        ("05", "Reproduce", "seed · logs"),
    ]
    x = 12 * mm
    for pts, head, sub in rubrics:
        round_rect(c, x, 39 * mm, 30 * mm, 24 * mm, WHITE, radius=3 * mm)
        c.setFillColor(CYAN); c.setFont("UI-Bold", 11); c.drawCentredString(x + 15 * mm, 54 * mm, pts)
        c.setFillColor(INK); c.setFont("UI-Bold", 6.8); c.drawCentredString(x + 15 * mm, 47 * mm, head)
        c.setFillColor(MUTED); c.setFont("UI", 5.8); c.drawCentredString(x + 15 * mm, 42 * mm, sub)
        x += 34 * mm

    round_rect(c, 12 * mm, 15 * mm, 272 * mm, 17 * mm, NAVY, stroke=NAVY, radius=3 * mm)
    para(c, "FINAL COMMAND:  setup → test → train (hoặc tải checkpoint) → evaluate → demo   |   PACKAGE: code + config + weights + logs + notebook + README + report/slide/poster",
         18 * mm, 27 * mm, 260 * mm, 11 * mm, size=7.2, color=WHITE, font="UI-Bold", align=TA_CENTER)
    footer(c, 8, "AI CARO - ROADMAP 8 TUẦN · Nguồn: Đề tài Game AI + Kế hoạch AI Caro")
    c.showPage()


def build() -> str:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(TMP_DIR, exist_ok=True)
    c = canvas.Canvas(OUT_FILE, pagesize=(PAGE_W, PAGE_H), pageCompression=1)
    c.setTitle("Roadmap tổng quan AI Caro 8 tuần")
    c.setAuthor("Nhóm đồ án AI Caro")
    c.setSubject("Roadmap module, input/output, công cụ, dependency và workflow commit")
    page_cover(c)
    page_scope(c)
    page_architecture(c)
    page_weeks_1_2(c)
    page_weeks_3_4(c)
    page_weeks_5_6(c)
    page_week_7(c)
    page_week8_git(c)
    c.save()
    return OUT_FILE


if __name__ == "__main__":
    print(build())
