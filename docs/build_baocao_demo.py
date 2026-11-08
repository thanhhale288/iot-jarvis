#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sinh docs/baocao_demo.docx từ khung báo cáo, giữ trang bìa và bảng thành viên."""

from __future__ import annotations

import glob
import shutil
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/Users/hale/Code/IOT")
TEMPLATE = glob.glob("/Users/hale/Code/IOT-esp32-thuchanh/docs/*.docx")[0]
OUT = ROOT / "docs" / "baocao_demo.docx"
IMG = ROOT / "scratch" / "baocao_img"

_BM = 3000


def _bid() -> int:
    global _BM
    _BM += 1
    return _BM


def set_run_font(run, size=13, bold=False, italic=False):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.append(rFonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rFonts.set(qn(attr), "Times New Roman")


def bookmark(paragraph, name: str) -> None:
    tag = str(_bid())
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), tag)
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), tag)
    p = paragraph._p
    inserted = False
    for child in list(p):
        if child.tag == qn("w:r"):
            child.addprevious(start)
            inserted = True
            break
    if not inserted:
        p.append(start)
    p.append(end)


def _run_el(text, size=13, bold=False):
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    rFonts = OxmlElement("w:rFonts")
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        rFonts.set(qn(attr), "Times New Roman")
    rPr.append(rFonts)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(size * 2))
    rPr.append(sz)
    szCs = OxmlElement("w:szCs")
    szCs.set(qn("w:val"), str(size * 2))
    rPr.append(szCs)
    if bold:
        rPr.append(OxmlElement("w:b"))
    r.append(rPr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


def add_pageref(doc, label, bookmark_name, indent=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(1)
    pf.space_after = Pt(1)
    pf.line_spacing = 1.15
    pf.first_line_indent = Cm(0)
    pf.left_indent = Cm(0.6 * indent)
    pPr = p._p.get_or_add_pPr()
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "right")
    tab.set(qn("w:leader"), "dot")
    tab.set(qn("w:pos"), "9200")
    tabs.append(tab)
    pPr.append(tabs)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("w:anchor"), bookmark_name)
    hyperlink.set(qn("w:history"), "1")
    hyperlink.append(_run_el(label, size=13))
    p._p.append(hyperlink)
    run_tab = p.add_run()
    set_run_font(run_tab, size=13)
    run_tab._r.append(OxmlElement("w:tab"))
    # PAGEREF — Word cập nhật khi mở (updateFields)
    def fld(kind, text=None):
        run = p.add_run()
        set_run_font(run, size=13)
        if kind == "instr":
            node = OxmlElement("w:instrText")
            node.set(qn("xml:space"), "preserve")
            node.text = text
            run._r.append(node)
        else:
            node = OxmlElement("w:fldChar")
            node.set(qn("w:fldCharType"), kind)
            run._r.append(node)

    fld("begin")
    fld("instr", f" PAGEREF {bookmark_name} \\h ")
    fld("separate")
    run = p.add_run(" ")
    set_run_font(run, size=13)
    fld("end")
    return p


def strip_after_cover(doc: Document) -> None:
    body = doc.element.body
    children = list(body)
    start = None
    for i, child in enumerate(children):
        text = "".join(t.text or "" for t in child.iter() if t.tag.endswith("}t"))
        if text.startswith("MỤC LỤC"):
            start = i
            break
    if start is None:
        raise SystemExit("Không thấy MỤC LỤC trong khung")
    final = children[-1]
    for child in children[start:]:
        if child is final and child.tag.endswith("sectPr"):
            continue
        body.remove(child)


def enable_update_fields(doc: Document) -> None:
    settings = doc.settings.element
    for old in settings.findall(qn("w:updateFields")):
        settings.remove(old)
    uf = OxmlElement("w:updateFields")
    uf.set(qn("w:val"), "true")
    settings.append(uf)


def add_page_footer(section) -> None:
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.clear() if hasattr(p, "clear") else None
    # clear runs
    for r in list(p.runs):
        r._r.getparent().remove(r._r)

    def fld(kind, text=None):
        run = p.add_run()
        set_run_font(run, size=12)
        if kind == "instr":
            node = OxmlElement("w:instrText")
            node.set(qn("xml:space"), "preserve")
            node.text = text
            run._r.append(node)
        else:
            node = OxmlElement("w:fldChar")
            node.set(qn("w:fldCharType"), kind)
            run._r.append(node)

    fld("begin")
    fld("instr", " PAGE ")
    fld("separate")
    run = p.add_run("1")
    set_run_font(run, size=12)
    fld("end")


class R:
    def __init__(self, doc: Document):
        self.doc = doc
        self.chars = 0
        self.tables = 0
        self.figs = 0

    def _p(self, text, *, size=13, bold=False, italic=False, center=False, indent=True, before=0, after=6, page_break=False):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY
        pf = p.paragraph_format
        pf.space_before = Pt(before)
        pf.space_after = Pt(after)
        pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        if page_break:
            pf.page_break_before = True
        pf.widow_control = True
        if indent and text and not center:
            pf.first_line_indent = Cm(1.0)
        else:
            pf.first_line_indent = Cm(0)
        if text:
            run = p.add_run(text)
            set_run_font(run, size=size, bold=bold, italic=italic)
            self.chars += len(text)
        return p

    def h1(self, text, bm, *, page_break=True):
        p = self._p(text, size=14, bold=True, center=True, indent=False, before=0, after=8, page_break=page_break)
        bookmark(p, bm)
        return p

    def h2(self, text, bm):
        p = self._p(text, size=13, bold=True, center=False, indent=False, before=10, after=4)
        bookmark(p, bm)
        return p

    def h3(self, text, bm=None):
        p = self._p(text, size=13, bold=True, italic=True, center=False, indent=False, before=8, after=2)
        if bm:
            bookmark(p, bm)
        return p

    def body(self, text):
        return self._p(text)

    def bullet(self, text):
        p = self._p("–  " + text, indent=False, after=2)
        p.paragraph_format.left_indent = Cm(1.25)
        return p

    def caption(self, text, bm):
        p = self._p(text, size=12, bold=True, italic=True, center=True, indent=False, before=4, after=8)
        bookmark(p, bm)
        return p

    def table(self, headers, rows, widths):
        self.tables += 1
        table = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
        table.style = "Table Grid"
        for i, h in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(h)
            set_run_font(run, size=11, bold=True)
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            shd = OxmlElement("w:shd")
            shd.set(qn("w:fill"), "D9E2F3")
            shd.set(qn("w:val"), "clear")
            tcPr.append(shd)
        for r_i, row in enumerate(rows):
            for c_i, val in enumerate(row):
                cell = table.rows[r_i + 1].cells[c_i]
                cell.text = ""
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(str(val))
                set_run_font(run, size=11)
                self.chars += len(str(val))
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
        self._p("", indent=False, after=4)
        return table

    def picture(self, path: Path, width_cm=14.5):
        self.figs += 1
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        run = p.add_run()
        run.add_picture(str(path), width=Cm(width_cm))
        return p


def _font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
        "/Library/Fonts/Times New Roman.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def _box(draw, xy, text, font, fill="#F4F7FB"):
    draw.rounded_rectangle(xy, radius=12, fill=fill, outline="#1F4E79", width=3)
    x0, y0, x1, y1 = xy
    # wrap
    lines = text.split("\n")
    lh = 28
    total = lh * len(lines)
    y = y0 + (y1 - y0 - total) / 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text(((x0 + x1 - tw) / 2, y), line, fill="#1A1A1A", font=font)
        y += lh


def _arrow(draw, x0, y0, x1, y1):
    draw.line((x0, y0, x1, y1), fill="#1F4E79", width=3)
    # head
    if abs(x1 - x0) >= abs(y1 - y0):
        s = 1 if x1 > x0 else -1
        draw.polygon([(x1, y1), (x1 - 12 * s, y1 - 7), (x1 - 12 * s, y1 + 7)], fill="#1F4E79")
    else:
        s = 1 if y1 > y0 else -1
        draw.polygon([(x1, y1), (x1 - 7, y1 - 12 * s), (x1 + 7, y1 - 12 * s)], fill="#1F4E79")


def make_figures() -> dict[str, Path]:
    IMG.mkdir(parents=True, exist_ok=True)
    font = _font(22)
    small = _font(18)
    out = {}

    im = Image.new("RGB", (1400, 520), "white")
    d = ImageDraw.Draw(im)
    _box(d, (40, 160, 360, 360), "Tầng cảm nhận\nESP32 + Uno\nCảm biến / servo", font)
    _box(d, (520, 160, 880, 360), "Tầng kết nối\nWi-Fi HTTP\nUSB Serial 115200", font)
    _box(d, (1040, 160, 1360, 360), "Tầng ứng dụng\nHost, AI, voice\nFrontend chat", font)
    _arrow(d, 360, 260, 520, 260)
    _arrow(d, 880, 260, 1040, 260)
    d.text((430, 40), "Hình khái niệm — ba tầng chức năng Jarvis-on-Desk", fill="#1F4E79", font=font)
    p = IMG / "fig_layers.png"
    im.save(p)
    out["layers"] = p

    im = Image.new("RGB", (1400, 720), "white")
    d = ImageDraw.Draw(im)
    _box(d, (460, 30, 940, 170), "Laptop\nHost router + AI + voice + frontend", font, "#E8F0FE")
    _box(d, (80, 280, 520, 460), "ESP32 Otto\nTFT ST7789\n4 servo SG90\nPOST /cmd", font)
    _box(d, (880, 280, 1320, 460), "Arduino Uno\nDHT11, LDR, đất\nLCD, relay, bơm", font, "#EAF6EA")
    _arrow(d, 700, 170, 300, 280)
    _arrow(d, 700, 170, 1100, 280)
    d.text((250, 200), "Wi-Fi hoặc Serial", fill="#333", font=small)
    d.text((900, 200), "USB Serial", fill="#333", font=small)
    _box(d, (460, 530, 940, 680), "Người dùng\nMic / loa / trình duyệt :8787", small, "#FFF6E5")
    _arrow(d, 700, 530, 700, 170)
    p = IMG / "fig_arch.png"
    im.save(p)
    out["arch"] = p

    im = Image.new("RGB", (1400, 280), "white")
    d = ImageDraw.Draw(im)
    boxes = [
        (30, "Ghi mic\ncắt im lặng"),
        (300, "Whisper\nSTT tiếng Việt"),
        (570, "Fast path\nhoặc Qwen"),
        (840, "speak_and_act\nled + motion"),
        (1110, "edge-tts\nloa laptop"),
    ]
    for x, label in boxes:
        _box(d, (x, 70, x + 240, 220), label, small)
    for x in (270, 540, 810, 1080):
        _arrow(d, x, 145, x + 30, 145)
    p = IMG / "fig_voice.png"
    im.save(p)
    out["voice"] = p

    im = Image.new("RGB", (1400, 420), "white")
    d = ImageDraw.Draw(im)
    _box(d, (500, 20, 900, 140), "speak_and_act\ntext, emotion, motion", font)
    _box(d, (40, 240, 400, 390), "emotion → cmd led\nTFT (mặt)", small)
    _box(d, (500, 240, 900, 390), "motion → cmd motion\n4 servo Otto", small)
    _box(d, (1000, 240, 1360, 390), "text → TTS\nloa, không ra board", small, "#FFF6E5")
    _arrow(d, 620, 140, 220, 240)
    _arrow(d, 700, 140, 700, 240)
    _arrow(d, 780, 140, 1180, 240)
    p = IMG / "fig_speak.png"
    im.save(p)
    out["speak"] = p
    return out


def shade_ok():
    return None


# ---------- nội dung ----------

def write_front(r: R, toc, tables, figures):
    d = r.doc
    r.h1("MỤC LỤC", "toc_muc", page_break=False)
    for label, bm, ind in toc:
        add_pageref(d, label, bm, indent=ind)
    r.h1("DANH MỤC CÁC TỪ VIẾT TẮT", "toc_abbr")
    r.body(
        "Bảng dưới thống nhất cách gọi các từ xuất hiện nhiều lần trong báo cáo. Khi một khái niệm đã có ở đây, các chương sau dùng dạng viết tắt mà không nhắc lại lời giải nghĩa đầy đủ."
    )
    r.caption("Bảng 0.1. Danh mục từ viết tắt", "tbl_0_1")
    r.table(
        ["Từ viết tắt", "Ý nghĩa"],
        [
            ["ADC", "Bộ chuyển đổi tương tự–số (Analog to Digital Converter)"],
            ["ACK", "Tin xác nhận đã nhận và xử lý lệnh (acknowledgement)"],
            ["API", "Giao diện lập trình ứng dụng"],
            ["CSV", "Tệp giá trị tách bằng dấu phẩy"],
            ["DHT11", "Cảm biến nhiệt độ và độ ẩm không khí"],
            ["ESP32", "Vi điều khiển SoC Wi-Fi của Espressif"],
            ["GPIO", "Chân vào/ra đa năng"],
            ["HTTP", "Giao thức truyền siêu văn bản"],
            ["I2C", "Bus hai dây nối ngoại vi"],
            ["JSON", "Định dạng trao đổi dữ liệu dạng văn bản (RFC 8259)"],
            ["LCD", "Màn hình tinh thể lỏng 16×2"],
            ["LDR", "Quang trở, điện trở giảm khi sáng"],
            ["LLM", "Mô hình ngôn ngữ lớn"],
            ["NDJSON", "Mỗi dòng một object JSON"],
            ["PWM", "Điều chế độ rộng xung, dùng cho servo"],
            ["STT", "Nhận dạng tiếng nói thành chữ"],
            ["TFT", "Màn hình ST7789 240×240 trên Otto"],
            ["TTS", "Tổng hợp tiếng nói từ chữ"],
            ["UART", "Cổng nối tiếp bất đồng bộ; ở đây là USB Serial"],
        ],
        [4.2, 11.6],
    )
    r.h1("DANH MỤC BẢNG", "toc_lot")
    for label, bm in tables:
        add_pageref(d, label, bm, indent=0)
    r.h1("DANH MỤC HÌNH", "toc_lof")
    for label, bm in figures:
        add_pageref(d, label, bm, indent=0)


def write_body(r: R, figs: dict[str, Path]) -> None:
    # ===== MỞ ĐẦU =====
    r.h1("MỞ ĐẦU", "toc_intro")
    r.h2("1. Lý do chọn đề tài", "toc_intro_1")
    r.body(
        "Người ngồi làm việc tại bàn phải liên tục rời tay khỏi việc chính để bật đèn, xem nhiệt độ, tưới cây hoặc kiểm tra xem thiết bị còn sống hay không. Mỗi thao tác riêng lẻ thì nhỏ, nhưng cộng lại chúng làm đứt mạch suy nghĩ. Đề tài Jarvis-on-Desk đặt một trợ lý có hình thể ngay trên bàn: robot Otto nhìn được trạng thái hội thoại trên màn TFT, tay chân servo phản hồi cảm xúc, trong khi cụm Arduino Uno theo dõi nhiệt, ẩm, ánh sáng và độ ẩm đất rồi chấp hành đèn, quạt và bơm."
    )
    r.body(
        "Môn Mạng kết nối vạn vật yêu cầu sinh viên không dừng ở việc nháy một đèn. Hệ thống phải có cảm biến, có kênh truyền, có phần mềm điều phối và có phản hồi cho người dùng. Jarvis-on-Desk gom các yêu cầu đó vào một nguyên mẫu duy nhất: hai vi điều khiển không nối tiếp nhau thành một chuỗi, mà cùng nói chuyện với laptop bằng hợp đồng JSON một dòng. Laptop phát điểm truy cập Wi-Fi cho ESP32, mở một cổng USB Serial cho Uno, rồi chạy mô hình ngôn ngữ và giọng nói."
    )
    r.body(
        "Lý do thứ hai là tính tách biệt. Nếu mỗi người trong nhóm tự nghĩ một câu lệnh riêng, bản demo sẽ vỡ ngay khi ghép. Vì vậy hợp đồng được viết trước trong tài liệu PROTOCOL: phong bì JSON, tên lệnh, kiểu dữ liệu, mã lỗi. Phần cứng chỉ được làm những việc đã có trong kế hoạch linh kiện. Những món có trong hộp kit nhưng không có nhiệm vụ — mưa, keypad, NeoPixel, đồng hồ thời gian thực — được ghi rõ là ngoài phạm vi, để khỏi bị kéo vào “cho đủ đồ”."
    )
    r.h2("2. Mục tiêu", "toc_intro_2")
    r.body(
        "Mục tiêu tổng quát là xây dựng nguyên mẫu trợ lý bàn làm việc: nghe hoặc nhận chữ tiếng Việt, đọc môi trường, điều khiển đèn, quạt và bơm có giới hạn thời gian, đồng thời đổi mặt và cử chỉ của Otto cho khớp nội dung câu nói."
    )
    r.body("Các mục tiêu cụ thể của bản đang mô tả trong báo cáo này gồm:")
    r.bullet("Chuẩn hóa mọi lệnh thành một object JSON, UTF-8, một dòng, tối đa 256 byte, có trường phiên bản v bằng 1.")
    r.bullet("ESP32 nhận ping, led và motion; vẽ mặt trên TFT ST7789; chạy bốn servo SG90; mở thêm cổng HTTP POST /cmd khi đã vào Wi-Fi hotspot của laptop.")
    r.bullet("Arduino Uno đọc DHT11, quang trở và cảm biến đất; hiện LCD 16×2; đóng relay đèn và quạt; bơm trong 1–5 giây rồi nghỉ 5 giây nếu bị gọi lại.")
    r.bullet("Cầu nối serial_bridge mở cổng một lần, hạ DTR và RTS để hạn chế reset Uno, chờ khoảng hai giây rồi mới gửi lệnh.")
    r.bullet("Host router đọc trường to và gửi đúng đường: uno qua Serial, esp32 qua Serial hoặc HTTP, host thì tách speak_and_act.")
    r.bullet("Khối AI gọi công cụ get_environment, set_relay, set_pump, otto_act; có đường nhanh không cần mô hình cho câu lệnh rõ; có nhà cung cấp Ollama hoặc DeepSeek.")
    r.bullet("Khối voice ghi âm đến khi im lặng, nhận dạng bằng Faster-Whisper, đọc câu bằng edge-tts; pipeline đo thời gian tới tiếng nói đầu tiên.")
    r.bullet("Cửa sổ chat tại cổng 8787 hiện bong bóng hội thoại và phát đúng câu đang hiện.")
    r.bullet("Bộ kiểm thử tự động khóa enum, cooldown bơm, việc không ghi JSON của ESP32 xuống Serial của Uno, và các API chat.")
    r.h2("3. Đối tượng và phạm vi", "toc_intro_3")
    r.body(
        "Đối tượng nghiên cứu là phần mềm và hợp đồng dữ liệu của nguyên mẫu, cùng cách phần mềm đó bám vào pin map đã chốt. Báo cáo đi hết các thư mục esp32, uno, serial_bridge, host, ai, voice, frontend, tests và docs. Đây là báo cáo hệ thống đầy đủ của đồ án, không phải báo cáo thực hành riêng về Bluetooth hay MQTT."
    )
    r.body(
        "Phạm vi có chủ ý loại một số hướng. Không có broker MQTT trong mã hiện tại. Không có ứng dụng Bluetooth điều khiển Otto làm nền. Không có dáng đi liên tục kiểu gait; các lệnh turn_left, turn_right và step_forward nằm trong enum để khóa tên, còn mức hoàn thiện servo thuộc mốc tuần 5. Sự kiện vỗ tay, siêu âm và remote hồng ngoại đã có chỗ trong hợp đồng (cmd event) nhưng plan phần mềm ghi nhận chúng là việc sau MVP, nên báo cáo mô tả hợp đồng và chân cắm, không mô tả như thể firmware đã phát sự kiện đó trên bàn demo."
    )
    r.body(
        "Nguồn chấp hành là tải thấp. Servo và siêu âm dùng nguồn 5 V ngoài từ 3 A trở lên, chung mass với ESP32. Bơm có trần thời gian. Báo cáo không đánh giá định lượng trên mẫu thống kê lớn; các con số thời gian là tham số thiết kế (im lặng 600 ms, trần ghi âm 8 giây, cooldown bơm 5 giây), còn độ trễ hội thoại được theo dõi bằng chỉ số time-to-first-speech khi chạy máy thật."
    )
    r.h2("4. Phương pháp thực hiện", "toc_intro_4")
    r.body(
        "Nhóm viết hợp đồng trước, rồi mới code. Mỗi lệnh có ví dụ gửi và ví dụ trả. Thiếu tầng phần cứng thì mock trả đúng phong bì, không bịa thêm trường. Việc làm được khi không cắm board được liệt kê thành nhóm A trong plan-soft: mock, router, tool, prompt, STT, TTS, speak_and_act, unit test. Việc cần board là nhóm B: firmware Wi-Fi, firmware Uno, cầu nối, đổi transport, sự kiện, kịch bản nói end-to-end, luật tưới. Nhóm C (hồng ngoại, vòng nhắc 60 giây, từ đánh thức, bước đi, tự nối lại Wi-Fi) chỉ mở sau khi A và B ổn."
    )
    r.body(
        "Kiểm thử đi từ trong ra ngoài. Mock board kiểm tra phong bì và mã lỗi. Router kiểm tra hai transport không trộn. Tool AI kiểm tra không cần cổng Serial khi backend là mock. Frontend kiểm tra API bằng máy chủ thử. Trên bàn, từng khối phần cứng được smoke riêng (TFT, từng cặp servo, get_env) trước khi ghép pipeline giọng nói."
    )
    r.h2("5. Bố cục báo cáo", "toc_intro_5")
    r.body(
        "Chương 1 trình bày bài toán và cơ sở lý thuyết: mô hình ba tầng, hai vi điều khiển, cảm biến, JSON, giọng nói và gọi công cụ. Chương 2 là yêu cầu và thiết kế: vai trò thư mục, hợp đồng lệnh, sơ đồ khối, ánh xạ cảm xúc–cử chỉ, lựa chọn đường truyền. Chương 3 mô tả cách xây từng khối và cách chúng ghép lại. Chương 4 là kiểm thử, kịch bản sử dụng và đánh giá. Kết luận nêu kết quả, hạn chế và hướng tiếp. Phụ lục chép lại bảng lệnh, pin và biến môi trường để tra cứu khi demo."
    )

    # ===== CHƯƠNG 1 =====
    r.h1("CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI VÀ CƠ SỞ LÝ THUYẾT", "toc_c1")
    r.h2("1.1. Bài toán trợ lý bàn làm việc", "toc_c1_1")
    r.body(
        "Jarvis-on-Desk là trợ lý có mặt tại chỗ, không phải ứng dụng chỉ sống trên điện thoại. Người dùng nói hoặc gõ. Hệ thống trả lời bằng tiếng Việt qua loa laptop, đồng thời Otto đổi mặt và làm một cử chỉ ngắn. Nếu câu nói đụng tới đèn, quạt, nước hoặc thời tiết trên bàn, laptop phát lệnh xuống Uno. Nếu câu nói đụng tới tâm trạng hoặc cử chỉ, laptop phát lệnh xuống ESP32. Hai hướng này dùng chung một phong bì nhưng không dùng chung một sợi cáp."
    )
    r.body(
        "Sự phân vai đó tránh một lớp lỗi hay gặp khi học IoT: nối mọi cảm biến vào một board “cho tiện” rồi để board kia chỉ display. Ở đây Uno giữ việc đo và đóng tải vì các chân tương tự, relay và driver bơm nằm trên cụm đó, và vì Uno vẫn có thể chạy luật cục bộ khi laptop rút cáp — đó là yêu cầu của mốc diễn tập, dù luật tự tưới đầy đủ còn ở bước B8. ESP32 giữ việc vô tuyến, màn hình màu và servo vì các ngoại vi đó đã đấu trên robot Otto."
    )
    r.body(
        "Hệ thống vừa có nhánh hội thoại vừa có nhánh quy tắc. Nhánh hội thoại đi qua mô hình ngôn ngữ khi câu nói mơ hồ. Nhánh quy tắc, gọi là fast path, bắt các câu mẫu như “bật đèn”, “tắt quạt”, “tưới 2 giây” hoặc câu hỏi nhiệt ẩm, rồi gọi thẳng công cụ. Cách này giảm độ trễ và giảm rủi ro mô hình bịa số cảm biến. Khi fast path không khớp, câu mới rơi xuống Qwen hoặc DeepSeek cùng danh sách tool đã khai báo."
    )
    r.picture(figs["layers"])
    r.caption("Hình 1.1. Ba tầng chức năng: cảm nhận, kết nối, ứng dụng", "fig_1_1")
    r.body(
        "Hình 1.1 không gắn mỗi tầng với một cái hộp sắt. Laptop vừa là tầng ứng dụng vừa là đầu kia của tầng kết nối. ESP32 vừa cảm nhận (và sẽ phát sự kiện) vừa chấp hành. Cách vẽ theo chức năng giúp thảo luận “mất laptop thì còn gì chạy” mà không bị rối bởi tên thư mục."
    )

    r.h2("1.2. Mô hình phân tầng cho IoT học tập", "toc_c1_2")
    r.body(
        "Khuyến nghị ITU-T Y.4000 (trước là Y.2060) mô tả IoT như hạ tầng kết nối vật thể với ứng dụng thông tin. Với một đồ án một học kỳ, báo cáo dùng lược đồ ba tầng đủ để phân công: tầng thiết bị, tầng mạng, tầng ứng dụng. Tầng thiết bị gồm cảm biến, vi điều khiển và cơ cấu chấp hành. Tầng mạng ở đề tài này là Wi-Fi cục bộ do laptop phát và cáp USB Serial, chưa phải mạng diện rộng. Tầng ứng dụng là router, mô hình ngôn ngữ, giọng nói và trang chat."
    )
    r.body(
        "Phân tầng không có nghĩa mọi quyết định đều lên mây. Xử lý tại biên đặt giới hạn nguy hiểm gần tải: bơm tự tắt sau số giây đã hẹn, cooldown từ chối lần bơm kế tiếp, servo không lấy điện từ chân 5 V của ESP32. Những quy tắc này nằm trong firmware và trong mock, nên chúng còn đúng cả khi người demo tắt mô hình ngôn ngữ."
    )
    r.body(
        "Hệ quả thiết kế là hợp đồng phải nhỏ. Một dòng JSON dưới 256 byte vừa đủ cho bộ đệm Arduino, vừa buộc người viết không nhét cả trạng thái hội thoại xuống board. Board không cần biết câu người dùng vừa nói. Board chỉ cần biết cmd, các đối số đã kiểm, và id để echo lại."
    )

    r.h2("1.3. ESP32, Arduino Uno và lý do có hai board", "toc_c1_3")
    r.body(
        "ESP32 là hệ thống trên một chip, có Wi-Fi IEEE 802.11 b/g/n, nhiều GPIO, SPI cho màn hình, LEDC hoặc PWM cho servo. Trong đồ án, ESP32 đóng vai Otto: vẽ cảm xúc và cử động. Firmware chính nằm ở esp32/otto_motion. Sketch vừa đọc dòng JSON trên UART 115200 vừa, khi đã cấu hình wifi_config.h, gia nhập hotspot và mở WebServer cổng 80 tại đường dẫn /cmd. Một POST mang đúng một object JSON; phản hồi là một object JSON. GET /cmd chỉ trả lời một dòng nhắc, để người kiểm tra nhầm phương thức vẫn thấy server sống."
    )
    r.body(
        "Arduino Uno R3 dùng ATmega328P, giao tiếp máy tính bằng USB Serial. Nó không có Wi-Fi. Việc đó là có chủ đích: nhánh môi trường đi cáp, ổn định khi phòng thực hành nhiễu vô tuyến, và dễ debug bằng máy theo dõi cổng nối tiếp. Firmware uno/get_env đọc cảm biến, cập nhật LCD, chấp hành relay và bơm. Baud 115200, 8N1, khớp quy định C của PROTOCOL."
    )
    r.body(
        "Hai board không nói chuyện trực tiếp với nhau trong thiết kế hiện tại. Laptop là điểm hội tụ. Quy tắc cứng: JSON có to bằng esp32 không bao giờ được ghi vào cổng Serial của Uno. Kiểm thử test_esp32_never_writes_serial và test_esp32_still_not_on_uno_serial khóa hành vi này, vì trộn cáp là lỗi vừa sai điện vừa sai ngữ nghĩa — Uno sẽ cố hiểu lệnh motion hoặc sẽ vỡ bộ đệm."
    )
    r.caption("Bảng 1.1. Phân vai hai vi điều khiển", "tbl_1_1")
    r.table(
        ["Hạng mục", "ESP32 (Otto)", "Arduino Uno"],
        [
            ["Kết nối tới laptop", "Wi-Fi POST /cmd hoặc USB Serial", "USB Serial 115200"],
            ["Việc chính", "Mặt TFT, cử chỉ servo, ping", "Môi trường, đèn, quạt, bơm, LCD"],
            ["Lệnh nhận", "ping, led, motion", "get_env, relay, pump"],
            ["Sự kiện dự kiến", "clap, proximity (hợp đồng, sau MVP)", "ir (hợp đồng, tuần 4)"],
            ["Nguồn tải", "5 V ngoài ≥ 3 A, chung GND", "Bơm có nguồn riêng, chung GND"],
            ["Khi mất laptop", "Mất lệnh từ xa; không tự tưới", "Firmware vẫn tắt bơm theo giờ đã hẹn"],
        ],
        [4.0, 6.0, 5.8],
    )

    r.h2("1.4. Cảm biến và cơ cấu chấp hành", "toc_c1_4")
    r.body(
        "DHT11 đo nhiệt độ theo độ C và độ ẩm tương đối. Chân OUT vào D2 của Uno. Giá trị temp làm tròn một chữ số thập phân, hum theo phần trăm. Khi cảm biến lỗi, firmware trả ok false và error bằng sensor, đồng thời LCD báo lỗi dây D2 thay vì giữ số cũ giả vờ còn tốt."
    )
    r.body(
        "Quang trở MS-CDS05 đọc ADC 0–1023 tại A0. Trên module của kit, số thấp nghĩa là sáng hơn — ngược với thói quen “số lớn là sáng” nếu người lập trình không đọc ghi chú đo ngày 15/09. Cảm biến đất tại A1 cũng là ADC; trên module này số lớn nghĩa là khô hơn. Hai quy ước này được ghi vào mô tả tool get_environment để mô hình ngôn ngữ không đảo chiều khi diễn giải."
    )
    r.body(
        "Nếu chân chưa gắn, get_env được phép trả light hoặc soil bằng −1. Quy tắc này quan trọng hơn vẻ đẹp của số liệu: một demo tuần 1 chỉ có DHT11 vẫn hợp lệ, miễn là không bịa lux hay phần trăm đất. LCD I2C 16×2 (SDA A4, SCL A5) hiện nhiệt ẩm ở dòng trên và ánh sáng cùng đất ở dòng dưới, để người đứng cạnh bàn đối chiếu mà không cần mở terminal."
    )
    r.body(
        "Relay một kênh, chân IN vào D7, là đèn (id light). Quạt ở giai đoạn này là LED có điện trở vào D8 (id fan), vì chưa gắn động cơ quạt thật; tên lệnh vẫn là fan để khi thay tải không đổi hợp đồng. Bơm đi qua driver L298, IN1 vào D9. Tham số seconds là số nguyên từ 1 đến 5, thiếu thì mặc định 2. Hết giờ, firmware tự đưa on về false. Trong 5 giây sau khi tắt, lệnh bật mới bị từ chối với error busy. Lệnh tắt luôn được nhận. Đang chạy mà bật lần nữa cũng busy. Ba quy tắc này chống tưới vô hạn và chống dội lệnh khi người dùng nói hai lần."
    )
    r.body(
        "Phía Otto, bốn servo SG90 tạo cử chỉ ngắn, không phải bước đi đường dài. Chân PWM theo pin map hiện hành là D16, D13, D26 và D14. Nguồn 5 V ngoài, mass chung với ESP32. Thiếu mass chung thì servo giật và board reset — đây là sự cố nguồn, không phải sự cố JSON. Màn ST7789 nối SPI: CS D22, DC D21, MOSI D23, SCK D18, RST D27, nuôi 3V3. Trạng thái mặt là idle, listening, thinking, speaking, happy, alert. NeoPixel bị loại; cmd led vẽ TFT chứ không đếm pixel."
    )
    r.body(
        "Cảm biến âm thanh KY-037 dự kiến lấy xung số vào D35 để sau này phát event clap. Siêu âm HC-SR04 dự kiến TRIG D4 và ECHO D5 qua level shifter, nguồn 5 V ngoài, để phát event proximity. Cả hai chân đã có trong pin map. Buzzer 5 V không gắn ESP32; nó cắm Uno D6, kêu cục bộ, không có cmd JSON riêng. Remote hồng ngoại là event ir kèm code, thuộc mốc tuần 4."
    )

    r.h2("1.5. Wi-Fi cục bộ và USB Serial", "toc_c1_5")
    r.body(
        "Quy định A: laptop phát hotspot, ESP32 vào mạng đó. Không dùng Wi-Fi của trường vì cổng đăng nhập (captive portal) làm board không có đường ra Internet và cũng không có đường tới laptop một cách ổn định. SSID và mật khẩu nằm trong wifi_config.h, bản example được commit, bản thật không đưa vào báo cáo và không commit. Khi nối được, Serial in dòng dạng WiFi OK cùng URL http://địa-chỉ/cmd. Host đặt ESP32_TRANSPORT=http và ESP32_URL trỏ về gốc địa chỉ đó."
    )
    r.body(
        "HTTP ở đây là kênh trong phòng, không phải API công cộng. Không có xác thực vì điểm truy cập đã là ranh giới vật lý. Body là JSON thô, không bọc thêm lớp. Phản hồi cũng là JSON một object. Nếu transport để auto, host chọn theo biến môi trường đang có: có URL thì HTTP, có cổng Serial thì UART, không có thì mock."
    )
    r.body(
        "USB Serial của Uno dễ mất dòng đầu vì nhiều hệ điều hành kéo DTR khi mở cổng, và DTR trên Uno thường nối chân reset. serial_bridge mở cổng với DTR và RTS ở mức false, rồi delay khoảng hai giây. Cổng được giữ suốt phiên, không mở đóng mỗi lệnh. Host không gửi lệnh mới khi chưa có dòng trả lời hoặc khi đã hết thời gian chờ. Chế độ --allow-reset và biến UNO_PREVENT_RESET=0 chỉ dùng khi đang soi lỗi phần cứng, không dùng khi demo."
    )

    r.h2("1.6. JSON một dòng làm hợp đồng", "toc_c1_6")
    r.body(
        "RFC 8259 định nghĩa JSON là văn bản độc lập ngôn ngữ. Đề tài siết thêm bốn luật cục bộ. Một tin là một object. Một tin là một dòng (NDJSON), cấm pretty-print trên Serial vì dấu xuống dòng giữa chừng bị firmware hiểu là hết tin. Số không được để trong chuỗi: temp, on, seconds là number hoặc boolean. Không hiểu cmd thì phải trả ok false, không được im lặng — im lặng làm timeout phía host không phân biệt được đứt cáp với lệnh lạ."
    )
    r.body(
        "Phong bì gửi gồm v, id, to, cmd và các đối số. Phong bì trả gồm v, id echo lại, from, ok, và error khi thất bại. Mã lỗi khép kín: unknown_cmd, bad_args, busy, timeout, sensor. id tuần 1 được phép bỏ với thử nghiệm LED; từ tuần 2 mọi lệnh nên có id do host sinh, thường là chuỗi hex ngắn. Đổi tên trường hoặc đổi đơn vị soil và light đòi họp lại. Thêm lệnh mới ở mục dành sẵn không bắt buộc tăng v. Phá trường cũ thì mới là v bằng 2."
    )
    r.caption("Bảng 1.2. Mã lỗi trong phong bì trả lời", "tbl_1_2")
    r.table(
        ["error", "Khi nào", "Ví dụ"],
        [
            ["unknown_cmd", "cmd không có trong firmware board đó", "Uno nhận motion"],
            ["bad_args", "Đối số sai kiểu hoặc ngoài enum", "led state=neon; pump seconds=9"],
            ["busy", "Bơm đang chạy hoặc còn cooldown", "Bật bơm lần hai trong 5 giây"],
            ["timeout", "Host không kịp thấy dòng trả", "Cáp rời, sai baud"],
            ["sensor", "Đọc DHT hoặc ADC thất bại", "DHT11 đứt D2"],
        ],
        [3.5, 6.5, 5.8],
    )

    r.h2("1.7. Giọng nói: ghi, nhận dạng, đọc", "toc_c1_7")
    r.body(
        "Chuỗi giọng nói của đồ án cố ý không dùng nhận dạng trực tiếp từng từ (live STT). Đường đã chọn là: ghi đến khi im lặng, nhận dạng cả đoạn bằng Faster-Whisper, sinh câu trả lời, rồi tổng hợp tiếng. Cách này đơn giản hơn streaming mic hai chiều và đủ cho câu lệnh bàn làm việc dài vài giây."
    )
    r.body(
        "Ghi âm dừng sau STT_SILENCE_MS mili giây im, mặc định 600, và không dài quá STT_MAX_SECONDS, mặc định 8. Ngôn ngữ khóa vi. Model mặc định trong tài liệu voice có thể là base hoặc small tùy chỗ cấu hình; beam càng cao càng chậm và càng đúng. Người demo cần biết đánh đổi này: tiny cho máy yếu, small khi cần câu tiếng Việt có dấu khó."
    )
    r.body(
        "TTS dùng edge-tts, giọng vi-VN-HoaiMyNeural, tốc độ mặc định hơi nhanh (+10%). Hàm for_speech chỉnh chữ cho dễ đọc (đơn vị, số). Chế độ TTS_MODE=full đọc một lần đúng chuỗi đang hiện trên giao diện; chế độ chunk chồng tiếng lên lúc mô hình còn đang sinh — đó là nâng cấp A6b, phụ thuộc luồng token. Chỉ số cần nhìn khi tối ưu là time-to-first-speech, không phải tổng thời gian cả câu, vì người nghe cảm thấy hệ thống “chết” chủ yếu ở khoảng im trước tiếng đầu."
    )
    r.body(
        "Từ đánh thức “Hey Jarvis” nằm ở nhóm C, chưa là cổng vào bắt buộc. Bản hiện tại bắt đầu một lượt khi người dùng bấm nút nghe trên trang chat hoặc khi chạy pipeline có mic. Tách từ đánh thức khỏi nhận dạng cả câu là đúng về mặt kỹ thuật: một mô hình nhỏ chỉ cần phát hiện cụm từ, rồi mô hình lớn mới chạy. Việc đó chưa được đóng trong mã đang báo cáo."
    )

    r.h2("1.8. Mô hình ngôn ngữ và gọi công cụ", "toc_c1_8")
    r.body(
        "Mô hình ngôn ngữ nhận chữ và có thể yêu cầu gọi hàm. Đề tài không để mô hình tự bịa nhiệt độ. Tool get_environment không có tham số; kết quả là temp, hum, light, soil. Tool set_relay nhận name trong {light, fan} và on kiểu boolean. Tool set_pump nhận on và seconds từ 1 đến 5. Tool otto_act nhận emotion và/hoặc motion trong enum đã khóa. Mô tả tool viết bằng tiếng Việt, kèm chiều của số ADC, vì mô hình dùng phần mô tả này để quyết định có gọi hay không."
    )
    r.body(
        "Nhà cung cấp mặc định là Ollama tại 127.0.0.1:11434, model qwen2.5:7b. Máy trường, khi mạng cho phép, có thể trỏ research.neu.edu.vn với qwen3:8b. Nhà cung cấp deepseek đi API tương thích OpenAI, cần DEEPSEEK_API_KEY, model deepseek-chat. Biến LLM_PROVIDER chọn nhánh. Khóa API không ghi vào báo cáo, không commit. System prompt mặc định chỉnh giọng Jarvis: tiếng Việt, ngắn khi đang điều khiển, không bịa số; có thể thay cả prompt bằng AI_SYSTEM_PROMPT."
    )
    r.body(
        "Sau khi tool trả về, mô hình viết câu nói. Với đường streaming, token được cắt thành câu rồi đẩy sang TTS. Một lượt chat của frontend là một câu độc lập: máy chủ không gửi lịch sử cũ lên mô hình. Lịch sử người dùng thấy nằm trong localStorage của trình duyệt, chỉ để đọc lại, không phải bộ nhớ của mô hình. Đây là giới hạn có chủ đích ở giai đoạn demo, tránh prompt phình và tránh mô hình “nhớ” một lệnh bơm cũ."
    )

    r.h2("1.9. Phản hồi cảm xúc và an toàn chấp hành", "toc_c1_9")
    r.body(
        "Otto cần một bảng ánh xạ ổn định giữa câu chữ và cơ thể. emotion dùng cùng enum với led.state. Nếu người gọi không chỉ motion, host chọn mặc định: idle và listening đứng yên, thinking thì jitter, speaking thì gật, happy thì đung đưa, alert thì lắc nhanh. Hàm infer_emotion quét vài từ khóa tiếng Việt (cảnh báo, khô, vui, nghĩ, nghe) để gán cảm xúc khi câu không mang enum tường minh. Từ khóa “khô” map sang alert vì trong kịch bản bàn, đất khô là tình huống cần người chú ý, không phải là nụ cười."
    )
    r.body(
        "An toàn chấp hành tách khỏi cảm xúc. Dù câu nói có kích động đến đâu, bơm vẫn bị trần 5 giây và cooldown. Relay chỉ có hai tên. Motion lạ bị bad_args, servo không chạy góc tự do do mô hình nghĩ ra. Firmware từ chối trước khi PWM đổi. Mock từ chối y hệt, nên bài test không cần điện vẫn chứng minh được hàng rào này."
    )

    # ===== CHƯƠNG 2 =====
    r.h1("CHƯƠNG 2. PHÂN TÍCH YÊU CẦU VÀ THIẾT KẾ", "toc_c2")
    r.h2("2.1. Vai trò theo thư mục", "toc_c2_1")
    r.body(
        "Kho mã chia theo việc, không chia theo tuần. esp32 thuộc phần robot và Wi-Fi. uno và serial_bridge thuộc phần môi trường và cáp. host là bộ định tuyến. ai là mô hình và tool. voice là mic, loa và pipeline. frontend là cửa sổ chat. docs giữ PROTOCOL, CONTEXT, pin map cảm xúc và plan-soft. tests là kiểm thử không cần board. Quy ước làm việc: đổi schema phải có người phụ trách ESP32 và người phụ trách Uno cùng biết; một người không sửa trường JSON một mình."
    )
    r.caption("Bảng 2.1. Thư mục và sản phẩm tương ứng", "tbl_2_1")
    r.table(
        ["Thư mục", "Sản phẩm", "Xong khi"],
        [
            ["docs/", "PROTOCOL, CONTEXT, plan-soft", "Lệnh và pin không mâu thuẫn nhau"],
            ["esp32/otto_motion", "Firmware TFT + servo + /cmd", "ping, led, motion ACK"],
            ["uno/get_env", "Firmware cảm biến và tải", "get_env, relay, pump, LCD"],
            ["serial_bridge/", "Giữ cổng, chống reset", "Không mất dòng JSON đầu"],
            ["host/", "Router và speak_and_act", "to đúng đường"],
            ["ai/", "Tool + prompt + stream", "Câu môi trường ra số thật hoặc mock"],
            ["voice/", "STT, TTS, pipeline", "Một câu tiếng Việt ra loa"],
            ["frontend/", "Chat cổng 8787", "Bong bóng và TTS cùng một chuỗi"],
            ["tests/", "unittest theo hợp đồng", "Enum, cooldown, không trộn cáp"],
        ],
        [4.2, 6.2, 5.4],
    )

    r.h2("2.2. Yêu cầu chức năng", "toc_c2_2")
    r.body(
        "Yêu cầu được viết lại thành danh sách kiểm được, bám plan-soft. Nhóm A làm offline. A1: mock Uno và ESP32 nhận một dòng JSON, trả một dòng đúng phong bì, gồm get_env mẫu (temp 28.4, hum 61, light 420, soil 610), ACK led và motion, lỗi unknown_cmd. A2: router tách to. A3: tool gọi mock, không mở Serial. A4: prompt Jarvis, cần Ollama hoặc DeepSeek sống. A5: STT một câu từ mic laptop. A6: TTS từ text; việc clone giọng là thay backend, không đổi PROTOCOL. A6b: cắt câu trong lúc model còn sinh. A7: speak_and_act tách ba ngả. A8: test enum và cooldown. A9: checklist năm bước smoke của PROTOCOL, phần AI đánh dấu riêng nếu model chết."
    )
    r.body(
        "Nhóm B cần board. B1: firmware ESP32 qua Wi-Fi, đã có POST /cmd trong otto_motion; còn phụ thuộc hotspot lúc demo. B2: Uno đủ get_env, relay, pump. B3: cầu nối. B4: host đổi từ mock sang cáp hoặc HTTP mà API dispatch không đổi. B5: tool AI trỏ backend serial. B6: sự kiện clap và proximity — chưa đóng. B7: nói một câu rồi Otto cử động, đường Serial đã đi được trong trạng thái plan. B8: đọc soil rồi tưới có hạn — chưa đóng thành luật tự động, dù lệnh pump đã có."
    )
    r.body(
        "Nhóm C bị khóa cho đến khi demo MVP chắc: hồng ngoại, vòng 60 giây nhắc ngưỡng, Hey Jarvis, ba motion di chuyển, Wi-Fi tự nối lại và Uno vẫn tưới khi rút laptop. Báo cáo kể tên chúng để phạm vi không bị hiểu nhầm là “đã làm hết hộp kit”."
    )
    r.h3("2.2.1. Yêu cầu người dùng nhìn thấy")
    r.body(
        "Người dùng mở trình duyệt tại 127.0.0.1:8787. Ô soạn ở dưới, câu của người dùng nằm bên phải, câu của Jarvis bên trái. Bấm gửi thì máy chủ chạy một lượt: fast path hoặc mô hình, rồi TTS. Bấm nghe thì máy chủ ghi mic của chính máy đang chạy server — không phải mic của điện thoại khách — đến khi im khoảng 0,6 giây. Bấm nghe lại một câu thì chỉ TTS, không gọi mô hình. Trang sức khỏe /api/health trả nhà cung cấp, tên model và giọng."
    )
    r.body(
        "Song song, người đứng cạnh robot nhìn TFT và servo. Khi OTTO_ACT bật, pipeline và chat gửi cảm xúc cùng cử chỉ. Khi tắt, hệ thống vẫn nói nhưng không đụng board. Cờ này cho phép tập giọng trên máy không cắm USB."
    )
    r.h3("2.2.2. Yêu cầu người vận hành")
    r.body(
        "Người vận hành cần một tệp .env: UNO_PORT, ESP32_PORT hoặc ESP32_URL, ESP32_TRANSPORT, AI_BACKEND, LLM_PROVIDER, và các khóa nếu dùng đám mây. Cổng Serial chỉ một chương trình được giữ. Trước khi chạy bridge phải tắt màn hình Serial của Arduino IDE. Đang cắm hoặc rút dây thì rút USB. Thứ tự cắm Uno đi từ nguồn breadboard, rồi DHT11, ánh sáng, đất, LCD, relay, LED quạt, cuối cùng mới L298 và bơm."
    )

    r.h2("2.3. Kiến trúc lúc chạy", "toc_c2_3")
    r.picture(figs["arch"])
    r.caption("Hình 2.1. Sơ đồ khối: laptop hội tụ, hai board không nối chéo", "fig_2_1")
    r.body(
        "Hình 2.1 là kiến trúc triển khai, khác hình 1.1 ở chỗ gọi tên thiết bị. Mọi mũi tên điều khiển đi qua laptop. Người dùng có thể nhập ở terminal (python -m ai, python -m voice.pipeline) hoặc ở trang 8787. Cả hai đều xuống cùng lớp ask và cùng router. Vì vậy sửa enum một nơi thì cả CLI lẫn web đi theo, miễn là không có bản sao hợp đồng nằm trong JavaScript."
    )
    r.body(
        "Router có ba transport. MockUnoTransport và MockEsp32Transport nói với đối tượng trong bộ nhớ. UnoSerialTransport ghi một dòng rồi đọc một dòng. Esp32SerialTransport làm tương tự trên cổng Otto. Esp32HttpTransport POST tới URL/cmd. HostRouter.dispatch nhìn to. Giá trị uno chọn transport Uno. Giá trị esp32 chọn transport ESP32. Giá trị host với cmd speak_and_act thì không xuống board nguyên khối, mà tách lệnh. Giá trị to lạ bị từ chối tại host, có test riêng."
    )
    r.body(
        "Chế độ sống chọn trong make_router và make_live_router. make_mock_router dùng khi test và khi AI_BACKEND=mock. Bản live đọc ESP32_TRANSPORT: serial, http, mock hoặc auto. Thiết kế này thỏa B4: cùng một lời gọi dispatch, đổi dây mà không đổi tool."
    )

    r.h2("2.4. Thiết kế hợp đồng lệnh", "toc_c2_4")
    r.h3("2.4.1. Lệnh ESP32")
    r.body(
        "ping không đối số, trả ok true, dùng để biết Wi-Fi và firmware còn sống trước khi diễn. led mang state thuộc sáu giá trị đã nêu; echo lại state. motion mang name. Tuần 1 firmware phải nhận và ACK đủ enum kể cả khi servo thật gắn sau; bản otto_motion hiện đã gắn tên motion với hàm cử chỉ: idle về home, nod nghiêng, shake lắc chân, think rung hông, happy đung đưa kèm nhón, alert lắc nhanh, turn_left và turn_right quay, step_forward đi ngắn. Không dùng playGesture vì hàm đó của thư viện Otto cần ma trận LED đã bị loại."
    )
    r.h3("2.4.2. Lệnh Uno")
    r.body(
        "get_env không đối số. relay dùng id light hoặc fan — trong firmware và CLI, tên tham số bề mặt đôi khi hiện là name cho dễ đọc, nhưng giá trị chỉ được hai chuỗi đó. pump dùng on và seconds. LCD không có lệnh; nó là hiệu ứng phụ của vòng lặp firmware, làm mới theo kỳ lcdNextRefresh. Buzzer không có lệnh; nó là đầu ra cục bộ."
    )
    r.h3("2.4.3. Lệnh host và sự kiện")
    r.body(
        "speak_and_act gửi tới host, gồm text tiếng Việt, emotion, motion. Host sinh id nếu thiếu, chuẩn hóa enum, bỏ giá trị lạ. Nếu ESP32_LED_FACE_ONLY khác 0, host gửi led trước (chỉ mặt) rồi gửi motion. Mặc định biến này tắt: một lệnh motion đã làm firmware đổi cả mặt lẫn servo, ổn định hơn khi liên kết TFT nằm trong act(). text đi vào speak_fn nếu có; pipeline thường để speak_fn rỗng và tự TTS để không đọc hai lần."
    )
    r.body(
        "Sự kiện đi ngược chiều, từ board lên host, không có to bắt buộc theo cùng kiểu lệnh. ESP32: name clap hoặc proximity. Uno: name ir và code ví dụ FFA25D. Host là nơi quyết định có nói hay có tưới hay không. Firmware mắt không gọi mô hình và không bật bơm. Quy tắc này giữ biên nhỏ khi siêu âm nhiễu."
    )
    r.caption("Bảng 2.2. Enum led.state và motion mặc định", "tbl_2_2")
    r.table(
        ["emotion / state", "Mặt TFT", "motion mặc định", "Ý nghĩa với người xem"],
        [
            ["idle", "IDLE", "idle", "Đứng, chờ"],
            ["listening", "LISTEN", "idle", "Đang nghe mic"],
            ["thinking", "THINK", "think", "Đang đợi mô hình"],
            ["speaking", "SPEAK", "nod", "Đang nói"],
            ["happy", "HAPPY", "happy", "Câu vui, cảm ơn"],
            ["alert", "ALERT", "alert", "Cảnh báo, đất khô, lỗi"],
        ],
        [3.6, 2.8, 3.6, 5.8],
    )

    r.h2("2.5. Thiết kế pipeline giọng và độ trễ", "toc_c2_5")
    r.picture(figs["voice"])
    r.caption("Hình 2.2. Một lượt nói: ghi, nhận dạng, quyết định, Otto, loa", "fig_2_2")
    r.body(
        "Hình 2.2 là thứ tự một lượt. Ghi âm và Whisper chạy trước khi có chữ. Khi đã có chữ, fast path thử khớp biểu thức chính quy. Khớp thì gọi tool và trả câu mẫu (“Đã bật đèn.”, “Đã tưới 2 giây.”, “Nhiệt độ … độ C, độ ẩm … phần trăm.”). Không khớp thì mới mở kết nối mô hình. otto_act hoặc infer_emotion chạy trong cùng lượt để TFT không đứng ở idle trong lúc loa đã nói."
    )
    r.body(
        "Fast path đang tắt theo mặc định trong mã (cờ AI_FAST_PATH). Khi bật, các mẫu đèn, quạt, tưới và từ khóa môi trường không đụng Ollama. Bộ nhớ đệm get_environment giảm việc đọc DHT lặp trong một cụm câu. Câu môi trường được viết dạng dễ đọc, rồi for_speech có thể chỉnh thêm. Người chỉnh demo nên bật fast path khi mạng tới Ollama không ổn, và tắt khi muốn nghe mô hình diễn đạt tự do."
    )
    r.body(
        "Giao diện voice.ui trên cổng 7860 là công cụ đo, không phải sản phẩm người dùng cuối. Nó có lối mic, lối nhập chữ, lối chỉ STT và lối chỉ TTS. Sản phẩm nhìn thấy trong buổi demo là frontend. Tách hai cổng để khỏi trộn nút thí nghiệm vào trang chat."
    )

    r.h2("2.6. Thiết kế an toàn, nguồn và những thứ cố ý không làm", "toc_c2_6")
    r.picture(figs["speak"])
    r.caption("Hình 2.3. Tách speak_and_act thành mặt, cử chỉ và tiếng", "fig_2_3")
    r.body(
        "Hình 2.3 nhắc một lỗi dễ mắc: gửi nguyên cả text xuống ESP32. Board không có loa tiếng Việt và không nên nhận câu dài. Tiếng ở lại laptop. Chỉ enum ngắn qua cáp hoặc Wi-Fi. Nhờ vậy bộ đệm 256 byte không bị một câu trả lời của mô hình làm tràn."
    )
    r.body(
        "Nguồn được coi là một yêu cầu chức năng. Servo đói dòng lúc khởi động. Nếu lấy 5 V từ chân của ESP32 hoặc từ USB yếu, điện áp sụt, chip reset giữa cử chỉ, demo trông như lỗi phần mềm. Quy định B bắt nguồn ngoài và mass chung. Bơm cũng không ăn điện từ chân Uno; driver có nguồn riêng, mass chung, seconds có trần."
    )
    r.body(
        "CONTEXT liệt kê món không làm: DS1307, rung SW-420, cảm biến mưa, NE555, 74HC595, NeoPixel, LED 7 đoạn, ma trận 8×8, động cơ bước 28BYJ-48, pin 9 V nuôi servo, keypad 4×4, nút nhấn, chiết áp chỉnh ngưỡng. Ngưỡng nếu có sẽ nằm trong mã, không phải biến trở. Hiển thị số là LCD, hiển thị cảm xúc là TFT. Tưới theo đất, không theo mưa. Otto không dùng động cơ bước."
    )
    r.caption("Bảng 2.3. Trong plan và ngoài plan (rút gọn)", "tbl_2_3")
    r.table(
        ["Trong plan", "Ngoài plan", "Lý do để ngoài"],
        [
            ["DHT11, LDR, đất, LCD", "Đồng hồ DS1307", "Không có nhiệm vụ log thời gian"],
            ["Relay đèn, LED quạt, bơm", "Cảm biến mưa", "Tưới theo đất"],
            ["TFT + 4 servo", "NeoPixel, ma trận LED", "Cảm xúc đã là TFT"],
            ["KY-037, HC-SR04 (chân, sự kiện sau)", "Động cơ bước", "Otto dùng servo"],
            ["IR remote (tuần 4)", "Keypad, nút, biến trở", "Điều khiển bằng giọng và IR"],
        ],
        [5.6, 4.6, 5.6],
    )

    # ===== CHƯƠNG 3 =====
    r.h1("CHƯƠNG 3. XÂY DỰNG VÀ TÍCH HỢP", "toc_c3")
    r.h2("3.1. Firmware ESP32", "toc_c3_1")
    r.body(
        "Thư mục esp32 chứa nhiều sketch smoke trước khi có firmware đủ lệnh: tft_test và tft_eyes kiểm tra SPI và mặt; servo_smoke, ct_bt_smoke, cp_bp_smoke, bp_smoke, bp_diag, d26_smoke, d17_d26_smoke, all4_smoke, otto_smoke kiểm tra từng nhóm chân servo vì một chân chết (đặc biệt D26 và bàn chân) làm cả robot có vẻ hỏng. bt_smoke là bản dò kênh, không phải sản phẩm Bluetooth của đồ án. Firmware nộp cho hệ thống là otto_motion."
    )
    r.body(
        "otto_motion.ino khai báo WebServer cổng 80, nối Wi-Fi từ wifi_config.h, in URL khi thành công, đăng ký POST /cmd vào hàm handleHttpCmd và vẫn đọc Serial trong loop. Cùng một bộ phân tích JSON phục vụ cả hai cửa. Lệnh hợp lệ đi vào hàm chấp hành đổi TFT và servo theo MOTION_EMOTION_MAP. Lệnh lạ trả bad_args hoặc unknown_cmd tùy chỗ sai. Người nạp board mở Serial 115200, thấy dòng ready, rồi mới cho host kết nối."
    )
    r.body(
        "File wifi_config.example.h là mẫu. Bản wifi_config.h có mật khẩu thì nằm máy người nạp, đã được đưa vào diện không commit cùng .gitignore khi có bí mật. Báo cáo không chép SSID. Khi demo trong phòng, người phụ trách hotspot điền bảng mạng ở README (SSID, IP ESP32) tại chỗ, không ghi vào tệp phát hành."
    )
    r.body(
        "Map cử chỉ dùng đơn vị độ servo. Bàn chân để FOOT_H khoảng 30 độ vì khớp cơ khí lỏng hơn thiết kế Otto gốc. happy là swing cộng tiptoeSwing. alert là swing nhanh cộng shakeLeg. think là jitter. nod là bend. Các hàm này nằm trong sketch, không nằm trong PROTOCOL — PROTOCOL chỉ giữ tên. Nhờ vậy cơ khí có thể chỉnh góc mà không họp lại schema."
    )

    r.h2("3.2. Firmware Uno", "toc_c3_2")
    r.body(
        "uno/get_env/get_env.ino là firmware môi trường. Vòng lặp vừa đọc Serial không chặn lâu, vừa kiểm tra pumpOffAt để tắt bơm đúng hạn, vừa làm mới LCD. Biến pumpOn, pumpOffAt và pumpCooldownUntil hiện thực đúng bảng cooldown. Hàm pumpInCooldown so millis có xét tràn số vì phép trừ unsigned. Khi từ chối, trả về vẫn là một dòng JSON có id echo, không phải một chuỗi text tự do — CLI serial_bridge phụ thuộc điều đó."
    )
    r.body(
        "Đọc DHT lỗi thì LCD in “DHT error” và “check D2 wiring”, đồng thời lệnh get_env thất bại với error sensor. Ánh sáng và đất đọc analogRead. Chiều giải thích không đảo trong firmware: firmware trả số thô, chiều “thấp là sáng” và “lớn là khô” thuộc tài liệu và thuộc mô tả tool. Nếu đảo trong firmware mà quên đảo trong prompt, mô hình sẽ tưới khi đất đang ướt. Tách số thô khỏi lời nói giảm loại lỗi này."
    )
    r.body(
        "Relay và quạt là digitalWrite lên D7 và D8. Bơm là D9 qua L298. Tài liệu uno/README.md đi từng bước breadboard: ray dương và ray mass chạy dọc hai mép, mỗi hàng năm lỗ thông nhau, rãnh giữa không thông. Mẹo tiết kiệm dây: 5 V và GND của Uno chỉ cắm một lần vào ray, module lấy nguồn từ ray, chỉ dây tín hiệu chạy tới D2, A0, A1, A4, A5, D6, D7, D8, D9. Mỗi bước rút USB, cắm, cắm lại USB, chạy một lệnh kiểm, rồi mới sang bước sau."
    )
    r.body(
        "Sketch uno/power_check là bước soi nguồn trước khi gắn bơm. Thư mục test-5ex chứa bài tập linh kiện rời (LED đơn, LED RGB, keypad, servo sweep, nhiệt) dùng để làm quen kit, không nằm trên đường đi của router. Báo cáo nhắc chúng để người đọc không tưởng năm file .ino đó là năm dịch vụ của Jarvis."
    )

    r.h2("3.3. Cầu nối Serial", "toc_c3_3")
    r.body(
        "Gói serial_bridge chạy bằng python -m serial_bridge. Không tham số thì mở phiên tương tác theo kiểu lệnh đã định. Có --cmd relay --name light --on, --cmd pump --on --seconds 2, và --test-cooldown để thấy lần bật thứ hai ra busy. Chế độ --text nhận các câu ngắn kiểu “light on”, “fan off”, “env”, “quit” để người chưa thuộc JSON vẫn thử được phần cứng; bên trong vẫn sinh đúng object."
    )
    r.body(
        "Cổng lấy từ UNO_PORT, ví dụ /dev/cu.usbserial-2110 trên macOS hoặc COM3 trên Windows. Bridge là tiến trình duy nhất được giữ cổng. Host khi chạy live dùng cùng chính sách mở cổng. Nếu cả bridge lẫn IDE cùng mở, hệ điều hành từ chối hoặc hai bên đọc xen kẽ và JSON gãy. Tài liệu ghi rõ phải đóng monitor trước."
    )

    r.h2("3.4. Host router và mock", "toc_c3_4")
    r.body(
        "host/mock_boards.py định nghĩa LED_STATES, MOTION_NAMES, RELAY_IDS và SAMPLE_ENV. MockEsp32 xử lý ping, led, motion. MockUno xử lý get_env, relay, pump với cooldown 5 giây tính bằng đồng hồ thời gian thực của process, để test_cooldown_second_on_is_busy không cần phần cứng. Lệnh lạ ra unknown_cmd. Đối số lạ ra bad_args. Mỗi trả lời là một dòng, không pretty-print — test_ndjson_one_line_no_pretty khóa định dạng."
    )
    r.body(
        "host/router.py định nghĩa giao thức Transport với phương thức send. Các lớp bọc ghi lại đường đi trong test: RecordingTransport đếm lời gọi, FakeSerial ghi lại chuỗi đã viết. Nhờ vậy test chứng minh esp32 không đụng bộ đệm của Uno mà không cần hai cáp. make_mock_router nhận speak_fn tùy chọn để test TTS không phát loa thật."
    )
    r.body(
        "host/uno_serial.py, esp32_serial.py và esp32_http.py là ba cửa thật. HTTP đặt Content-Type application/json, body là đúng object, đọc object trả về. Serial ghi một dòng kết thúc bằng ký tự xuống dòng rồi đọc đến dòng kế. id thiếu thì transport hoặc speak_and_act sinh uuid cắt còn tám ký tự hex."
    )
    r.body(
        "host/speak_act.py là A7. normalize_emotion và normalize_motion trả None nếu chuỗi không thuộc enum, và lớp trên đổi thành lỗi thay vì gửi xuống board. infer_motion ưu tiên motion tường minh. EMOTION_DEFAULT_MOTION là bảng đã nêu ở chương 2. handle_host_speak_and_act là điểm router gọi khi to bằng host. Kết quả trả về cho người gọi gồm trạng thái đã gửi và phần text, để pipeline ghi log."
    )

    r.h2("3.5. Khối AI", "toc_c3_5")
    r.body(
        "ai/chat_env.py giữ TOOLS, system prompt, vòng gọi mô hình và run_tool. run_tool ánh xạ tên tool sang lệnh PROTOCOL thông qua backend. MockBoardBackend không mở cổng. Backend serial dùng bridge và router sống. make_backend đọc AI_BACKEND; mặc định mock, đúng test_make_backend_default_is_mock. Tool lạ bị từ chối, có test_unknown_tool."
    )
    r.body(
        "_chat_ollama và _chat_deepseek gửi danh sách tools khi use_tools đúng. Vòng _run_tool_round thực thi từng lời gọi rồi đưa kết quả trở lại mô hình để viết câu cuối. ask là API đồng bộ một chuỗi. ask_sentences và iter_sentences_from_tokens phục vụ A6b: mô hình stream token, bộ cắt câu phát từng câu hoàn chỉnh. Dấu chấm, dấu hỏi và dấu xuống dòng là mốc cắt chính, đủ cho tiếng Việt có dấu câu."
    )
    r.body(
        "ai/fast_path.py là lớp trước mô hình. try_fast_reply trả None nếu cờ tắt hoặc câu không khớp, để caller rơi xuống ask. Mẫu đèn và quạt nhận “bật”, “mở”, “tắt”. Mẫu tưới lấy số giây nếu có, kẹp vào đoạn 1–5, không có số thì 2 giây. Mẫu môi trường nhìn các từ nhiệt, ẩm, đất, sáng. get_environment_cached tránh đọc lặp. Câu trả lời mẫu cố định giúp TTS ổn định khi demo hội trường ồn và không muốn chờ model."
    )
    r.body(
        "Điểm vào python -m ai nhận một câu trên dòng lệnh, in nhà cung cấp và in câu trả lời. Với AI_BACKEND=serial và cổng Uno mở, câu “Bật đèn” làm relay thật. Với mock, cùng câu chỉ đổi trạng thái trong bộ nhớ và vẫn trả “Đã bật đèn.” khi fast path bật, hoặc một câu của mô hình khi fast path tắt. Người chấm có thể chạy mock trước để xem hợp đồng, rồi mới cắm cáp."
    )

    r.h2("3.6. Khối voice", "toc_c3_6")
    r.body(
        "voice/record.py có record_seconds cho đoạn cố định và record_until_silence cho đường demo. voice/stt.py bọc FasterWhisperSTT, khóa ngôn ngữ, chọn model và beam từ môi trường. voice/tts.py có synthesize ra tệp, play_file, speak tiện lợi, và StreamingSpeaker cho chế độ chồng tiếng. for_speech là cửa duy nhất nên đi qua trước khi đọc, để số và đơn vị không bị phát từng chữ cái."
    )
    r.body(
        "voice/pipeline.py là B7 ở mức phần mềm. run_voice_turn nhận text có sẵn (bỏ qua STT) hoặc tự ghi mic. Nó gọi fast path hoặc ask, suy ra emotion, gọi router khi OTTO_ACT bật, rồi TTS trừ khi --no-tts. PipelineTimings ghi các mốc để tính time-to-first-speech. Lệnh ví dụ: python -m voice.pipeline \"Otto vui lên\" và python -m voice.pipeline \"Gật đầu\" --no-tts khi chỉ muốn xem servo."
    )
    r.body(
        "voice/ui.py dựng giao diện Gradio cổng 7860. Có làm nóng model (warmup) để lần đo đầu không bị cộng thời gian nạp Whisper. Bốn lối vào tương ứng bốn câu hỏi thí nghiệm: mic đầy đủ, chữ đầy đủ, chỉ STT, chỉ TTS. voice/__main__.py là lối STT/TTS ngắn không kéo cả Otto."
    )

    r.h2("3.7. Frontend chat", "toc_c3_7")
    r.body(
        "frontend/server.py phục vụ trang tĩnh và ba API POST cùng một API GET. /api/chat nhận {\"text\": \"...\"}. Chuỗi rỗng bị từ chối. Chuỗi hợp lệ chạy execute_turn, trả về phần user và assistant, rồi speak_text trên câu assistant. /api/listen không cần text; nó ghi mic server và đi cùng pipeline. /api/replay nhận text và chỉ đọc. /api/health phục vụ người debug. FRONTEND_HOST mặc định 127.0.0.1, FRONTEND_PORT mặc định 8787, nên máy khác trong phòng không vào được trừ khi người chạy đổi host một cách có chủ đích."
    )
    r.body(
        "Giao diện để lịch sử trong localStorage. Tải lại trang không làm mất bong bóng, nhưng cũng không gửi lịch sử đó cho mô hình. Kiểm thử test_frontend_chat dựng máy chủ thật trên cổng tạm, thay execute_turn và speak bằng hàm giả, rồi POST. test_index_has_composer kiểm tra ô soạn có trên HTML. test_chat_returns_text_then_speaks kiểm tra thứ tự: có chữ trả về và hàm nói được gọi. test_empty_chat_rejected và test_listen_uses_mic_turn khóa hai biên. test_unknown_path_not_a_file tránh biến server thành máy phát nhầm tệp ngoài thư mục tĩnh."
    )
    r.body(
        "Quyết định “một lượt một câu” làm demo dễ giải thích: người xem thấy một nguyên nhân và một kết quả. Nhược điểm là không có đại từ nối (“tắt cái đó”). Muốn tắt đèn phải nói đủ từ đèn. Fast path cũng cần từ đầy đủ. Đây là đánh đổi có ghi trong README frontend, không phải lỗi bỏ quên."
    )

    r.h2("3.8. Cấu hình và thứ tự ghép", "toc_c3_8")
    r.body(
        "Thứ tự ghép an toàn bám plan-soft: mock và test trước (A1 đến A8), sau đó firmware ESP32 và Uno độc lập, rồi bridge, rồi trỏ host sang cáp, rồi trỏ AI sang backend serial, rồi mới bật mic. Nhảy cóc — cắm bơm trước khi get_env ra số — làm lỗi nguồn và lỗi JSON chồng lên nhau, không biết đang sửa gì."
    )
    r.body(
        "Biến môi trường then chốt được gom ở phụ lục C. Nguyên tắc đặt tên: thứ gì là bí mật thì ở .env và .env.example chỉ có chìa khóa trống. .env.example trong kho là danh sách biến, không phải mật khẩu thật. Báo cáo này cũng không điền mật khẩu."
    )
    r.body(
        "Khi ESP32_TRANSPORT=http, người demo cần thấy IP in ra Serial trước khi đặt ESP32_URL. curl một ping là bài smoke ngắn nhất của B1, trước khi mở trang chat. Khi transport=serial, cổng ESP32_PORT là cổng của Otto, khác UNO_PORT. Nhầm hai cổng là cách nhanh nhất để vi phạm quy tắc không trộn JSON; test tự động không bắt được nhầm cổng ngoài đời, nên bảng mạng trong README phải điền tay lúc dựng bàn."
    )

    r.h2("3.9. Những chức năng dừng ở mức hợp đồng", "toc_c3_9")
    r.body(
        "clap và proximity có tên trong PROTOCOL mục 7 và có chân trong esp32/README.md, nhưng plan-soft ghi B6 là việc sau. Firmware otto_motion hiện tập trung led, motion và HTTP. Báo cáo không kèm sơ đồ xung KY-037 như thể đã hiệu chỉnh ngưỡng vỗ tay trên bàn. Khi làm tiếp, firmware chỉ nên gửi event; host mới quyết định nói hoặc đổi mặt alert. Không thêm trường cm vào get_env, vì khoảng cách không phải môi trường của Uno."
    )
    r.body(
        "Luật “đất khô thì tưới” (B8, task T15) cần ngưỡng soil đã hiệu chỉnh trên đúng module, rồi mới gọi pump với seconds có hạn. Chưa có vòng đó trong host. Người dùng vẫn tưới được bằng câu nói, tức là quyết định nằm ở người, không nằm ở ngưỡng. Vòng Uno 60 giây nhắc vượt ngưỡng thuộc C2, cũng chưa chạy."
    )
    r.body(
        "Hey Jarvis (C3) và ba motion di chuyển (C4) có tên trong tài liệu để enum không phải thêm sau. Firmware đã có nhánh turn và step_forward trong map cử chỉ ở mức hàm Otto, nhưng nhóm C vẫn đánh dấu khóa cho buổi demo nếu gait chưa chắc. Người vận hành demo nên dùng nod, shake, think, happy, alert — các cử chỉ tại chỗ, ít rủi ro ngã robot trên bàn."
    )

    # ===== CHƯƠNG 4 =====
    r.h1("CHƯƠNG 4. KIỂM THỬ, KỊCH BẢN VÀ ĐÁNH GIÁ", "toc_c4")
    r.h2("4.1. Chiến lược kiểm thử", "toc_c4_1")
    r.body(
        "Kiểm thử chia ba lớp. Lớp hợp đồng chạy bằng unittest, không điện, không mic, không Ollama. Lớp khói trên bàn dùng một lệnh một lần: curl ping, serial_bridge get_env, một motion trên Serial Otto. Lớp hội thoại là pipeline hoặc trang 8787, chỉ chạy sau khi hai lớp kia xanh. PROTOCOL mục 6 còn một kịch bản năm bước dành cho buổi thứ Sáu: nói ra chữ, gửi motion hoặc led và thấy ACK, hỏi môi trường và thấy get_env, nhận câu trả kèm emotion, nghe TTS và thấy mặt đổi. Thiếu tầng nào thì mock đúng schema, không bịa trường cho đủ slide."
    )
    r.body(
        "Lớp hợp đồng là hàng rào chống tụt. Một người sửa enum trên firmware mà quên mock sẽ fail test_led_enum_matches_protocol hoặc test_motion_enum_matches_protocol. Một người thêm pretty-print cho dễ đọc sẽ fail test NDJSON. Một người “tiện tay” ghi lệnh ESP32 ra cùng cổng Uno sẽ fail test router. Những bài này rẻ, chạy được trên máy không có driver USB, nên chúng nên chạy trước khi commit phần host và ai."
    )

    r.h2("4.2. Kết quả lớp hợp đồng", "toc_c4_2")
    r.caption("Bảng 4.1. Nhóm kiểm thử tự động và việc chúng khóa", "tbl_4_1")
    r.table(
        ["Mô-đun", "Ví dụ bài test", "Khóa điều gì"],
        [
            ["test_mock_boards", "test_get_env_envelope, test_led_ack", "Phong bì và số mẫu"],
            ["test_mock_boards", "test_unknown_cmd_uno / esp32", "Cấm im lặng khi lạ lệnh"],
            ["test_host_router", "test_uno_and_esp32_use_different_transports", "Tách đường"],
            ["test_host_router", "test_esp32_never_writes_serial", "Cấm trộn cáp"],
            ["test_host_router", "test_bad_to_rejected_by_host", "to lạ không được gửi"],
            ["test_protocol_a8", "test_seconds_out_of_range", "seconds chỉ 1–5"],
            ["test_protocol_a8", "test_cooldown_second_on_is_busy", "busy sau khi bơm"],
            ["test_speak_and_act", "test_splits_emotion_motion_and_tts", "Ba ngả của A7"],
            ["test_speak_and_act", "test_bad_emotion_rejected", "Enum cảm xúc"],
            ["test_speak_and_act", "test_infer_alert", "Từ khóa cảnh báo"],
            ["test_ai_tools_mock", "test_get_environment_no_serial", "Tool không cần cáp"],
            ["test_frontend_chat", "test_chat_returns_text_then_speaks", "API và thứ tự TTS"],
        ],
        [4.0, 6.6, 5.2],
    )
    r.body(
        "Bảng 4.1 không thay cho nhật ký một buổi chạy trên bàn. Nó chứng minh phần mềm tôn trọng hợp đồng khi dữ liệu đi trong bộ nhớ. Cooldown trong mock dùng đồng hồ process; firmware dùng millis. Cả hai cùng quy tắc 5 giây nhưng không dùng chung một hàm, nên khi sửa một bên phải sửa bên kia và sửa test. Đó là hệ quả của việc firmware Arduino không import được mô-đun Python. Tài liệu PROTOCOL là bản thứ ba phải khớp."
    )
    r.body(
        "test_face_only_sends_led_then_motion kiểm tra cờ ESP32_LED_FACE_ONLY: bật thì có cả led lẫn motion, đúng thứ tự. Mặc định demo để tắt cờ nếu một lệnh motion đã cập nhật mặt, tránh hai lệnh liên tiếp làm servo giật hai nhịp. Người tích hợp đọc MOTION_EMOTION_MAP trước khi bật cờ."
    )

    r.h2("4.3. Kịch bản trên bàn", "toc_c4_3")
    r.h3("4.3.1. Hỏi môi trường")
    r.body(
        "Người dùng gõ “Nhiệt độ và độ ẩm hiện tại?”. Nếu fast path bật và câu chứa từ khóa, hệ thống gọi get_environment, nhận temp và hum, nói câu mẫu có đơn vị. Nếu fast path tắt, mô hình phải gọi đúng tool vì prompt cấm bịa số; rồi mới diễn đạt. Trên LCD, cùng lúc hiện số để đối chiếu. Nếu DHT lỗi, người dùng nghe thông báo thất bại và thấy LCD báo kiểm D2, thay vì một nhiệt độ cũ."
    )
    r.h3("4.3.2. Bật đèn và quạt")
    r.body(
        "“Bật đèn” thành relay id light, on true, chân D7. “Tắt quạt” thành id fan, on false, chân D8. Hai tên không hoán đổi: light không phải là LED trên D8. Kịch bản ghép “Bật đèn và tưới 2 giây” cần mô hình gọi hai tool trong một lượt, hoặc người dùng nói hai câu. Fast path hiện khớp một ý mỗi lần; câu ghép là việc của mô hình. Đây là ranh giới có chủ đích giữa đường nhanh và đường thông minh."
    )
    r.h3("4.3.3. Tưới có hạn")
    r.body(
        "“Tưới 2 giây” đặt seconds bằng 2. Bơm chạy rồi tự tắt. Nói lại ngay lập tức, lần hai nhận busy. Đợi hơn 5 giây, lần ba được phép. Nói “tưới 9 giây” không được hiểu là 9; tầng kiểm tra kẹp hoặc từ chối theo bad_args tùy cửa (fast path kẹp 1–5, firmware và mock từ chối ngoài khoảng khi đối số đi thẳng từ JSON). Người demo nên nói số trong khoảng để cả hai cửa cùng một hành vi dễ kể."
    )
    r.h3("4.3.4. Otto vui và Otto cảnh báo")
    r.body(
        "“Otto vui lên đi” đi vào infer hoặc otto_act, emotion happy, motion happy, TFT HAPPY, servo đung đưa. Câu có “cảnh báo” hoặc “khô” kéo alert. Câu cảm ơn kéo happy theo từ khóa. Trong lúc mô hình đang nghĩ, trạng thái thinking là lựa chọn đúng nếu pipeline gửi led trước khi có chữ; bản ghép tối thiểu có thể chỉ gửi một lần khi đã có câu cuối, chấp nhận mặt đổi muộn hơn một nhịp. Đo time-to-first-speech sẽ cho thấy nhịp nào đang tốn thời gian: Whisper, model, hay tổng hợp tiếng."
    )
    r.h3("4.3.5. Mất cáp và sai lệnh")
    r.body(
        "Rút USB Uno giữa chừng: host hết timeout, không được gửi tiếp một loạt lệnh dồn. Cắm lại phải mở lại bridge vì cổng đã chết. Gửi cmd không có trong bảng: board trả unknown_cmd, host không thử lại bằng cách đổi tên trường. Gửi state lạ cho led: bad_args, mặt TFT giữ nguyên. Các phản ứng này là yêu cầu, không phải tùy chọn lịch sự."
    )

    r.h2("4.4. Đánh giá mức đạt", "toc_c4_4")
    r.caption("Bảng 4.2. Đối chiếu mục tiêu với hiện trạng mã", "tbl_4_2")
    r.table(
        ["Mục tiêu", "Hiện trạng", "Bằng chứng trong kho"],
        [
            ["Hợp đồng JSON một dòng", "Đã khóa bằng test", "tests/test_mock_boards.py"],
            ["Otto nhận led và motion", "Firmware otto_motion", "esp32/otto_motion/otto_motion.ino"],
            ["Wi-Fi POST /cmd", "Đã có trong sketch", "Cần hotspot lúc chạy"],
            ["Uno đo và chấp hành", "get_env, relay, pump, LCD", "uno/get_env/get_env.ino"],
            ["Chống reset Serial", "DTR/RTS false, delay", "serial_bridge"],
            ["Router không trộn cáp", "Test tự động", "tests/test_host_router.py"],
            ["speak_and_act", "Tách led, motion, TTS", "host/speak_act.py"],
            ["Tool mô hình", "4 tool, 2 nhà cung cấp", "ai/chat_env.py"],
            ["Giọng một lượt", "Whisper + edge-tts", "voice/pipeline.py"],
            ["Cửa sổ chat", "Cổng 8787", "frontend/server.py"],
            ["Vỗ tay, siêu âm, tự tưới", "Mới ở hợp đồng / pin", "plan-soft B6, B8"],
            ["Hey Jarvis, IR, gait", "Khóa nhóm C", "docs/plan-soft.md"],
        ],
        [4.8, 5.4, 5.6],
    )
    r.body(
        "Nhìn bảng 4.2, phần lõi điều khiển và hội thoại đã có mặt trong mã: nói hoặc gõ, ra chữ, ra tiếng, ra lệnh đúng board, có hàng rào thời gian cho bơm, có hàng rào enum cho Otto. Phần còn lại là cảm biến sự kiện và luật tự trị khi vắng người. Đồ án không xem các mục đó là thất bại của kiến trúc; chúng được xếp sau vì làm sớm sẽ đụng GPIO và schema trước khi đường nói ổn định."
    )
    r.body(
        "Điểm mạnh của cách làm là mock và board chia sẻ tên lệnh. Người viết AI không cần đợi nạp firmware mới thử prompt. Điểm yếu là ba nơi phải khớp tay: PROTOCOL, mock, firmware. Không có một tệp schema sinh ra cả hai ngôn ngữ. Trong phạm vi một học kỳ, tài liệu cộng test là cách rẻ. Nếu đề tài kéo dài, bước tiếp theo hợp lý là sinh bảng enum từ một nguồn, không phải thêm tính năng."
    )
    r.body(
        "Độ trễ là hạn chế cảm nhận rõ nhất. Whisper trên máy laptop, mô hình 7 tỷ tham số và TTS mạng (edge-tts cần ra Internet) cộng lại dễ vượt một giây trước tiếng đầu. Fast path và TTS local là hai nút giảm. Streaming câu giảm cảm giác chờ nhưng không giảm thời gian Whisper. Hotspot yếu làm HTTP /cmd chậm hoặc rớt; lúc đó transport serial của chính ESP32 vẫn là đường dự phòng vì otto_motion nghe cả hai cửa."
    )
    r.body(
        "An toàn điện là hạn chế vận hành, không phải hạn chế của JSON. Demo servo mà thiếu nguồn 3 A sẽ reset giữa happy và bị ghi nhầm thành lỗi firmware. Demo bơm mà lấy nguồn từ cổng USB sẽ sụt áp Uno và gãy dòng JSON. Bảng kiểm trước buổi diễn phải có mục nguồn riêng, đứng trước mục phần mềm."
    )

    r.h2("4.5. So sánh với các kênh không dùng trong bản này", "toc_c4_5")
    r.body(
        "Một bài thực hành khác của cùng môn học có thể đi Bluetooth Classic, SoftAP và MQTT trên một ESP32. Bản Jarvis-on-Desk không đi con đường đó. Bluetooth không phải cửa điều khiển của router. ESP32 có Wi-Fi nhưng ở chế độ station vào hotspot laptop, không phát SoftAP cho điện thoại. Không có địa chỉ broker MQTT trong kho. Nếu so sánh trên giấy, Bluetooth gần và không cần IP nhưng khó đưa vào pipeline Python sẵn có; MQTT hợp Internet nhưng thêm một dịch vụ phải sống đúng lúc demo; HTTP POST trên hotspot đủ cho một máy laptop và một board trong phòng, lại trùng kỹ năng đã dùng cho API chat."
    )
    r.body(
        "USB Serial của Uno đánh đổi khoảng cách lấy tính xác định. Người chấm nhìn thấy cổng, thấy baud, thấy dòng JSON. Khi sự cố, rút cáp là tái hiện được. Wi-Fi của Otto đánh đổi tính xác định lấy việc robot không bị một sợi cáp kéo nghiêng. Giữ cả hai trong cùng router là cách để mỗi tải đi đúng loại dây của nó, thay vì ép một giao thức cho mọi thứ."
    )

    # ===== KẾT =====
    r.h1("KẾT LUẬN", "toc_kl")
    r.h2("1. Kết quả đạt được", "toc_kl_1")
    r.body(
        "Đồ án đã dựng một nguyên mẫu trợ lý bàn làm việc có hợp đồng rõ. Laptop điều phối. ESP32 là Otto: mặt TFT, cử chỉ servo, nhận lệnh bằng Serial và bằng HTTP POST /cmd khi đã vào hotspot. Uno là bàn: nhiệt, ẩm, ánh sáng, đất, LCD, đèn, quạt, bơm có giờ và có cooldown. Giọng nói đi một lượt từ mic tới Whisper, tới mô hình hoặc fast path, tới loa edge-tts. Trang chat cổng 8787 cho người xem thấy chữ đúng với tiếng. Bộ test khóa những lỗi kiến trúc đắt nhất: trộn cáp, im lặng khi lệnh lạ, bơm không chịu dừng, enum cảm xúc trôi."
    )
    r.body(
        "Về mặt môn học, nhóm vận dụng được mô hình phân tầng, xử lý tại biên, và sự khác nhau giữa số đo thô với câu nói. Quy ước “số thấp là sáng” và “số lớn là khô” là ví dụ cụ thể cho thấy đặc tả cảm biến phải đi cùng mã, nếu không mô hình ngôn ngữ sẽ hành động ngược."
    )
    r.h2("2. Hạn chế", "toc_kl_2")
    r.body(
        "Chưa có sự kiện vỗ tay và siêu âm trên firmware đang chạy, chưa có luật tự tưới theo ngưỡng, chưa có từ đánh thức, chưa có remote hồng ngoại, chưa có bộ nhớ hội thoại nhiều lượt. Độ trễ phụ thuộc máy chạy Whisper và việc edge-tts ra mạng. Nguồn servo và bơm vẫn là điều kiện vật lý dễ làm hỏng một buổi demo dù phần mềm đúng. Schema còn nằm ở ba nơi viết tay."
    )
    r.h2("3. Hướng phát triển", "toc_kl_3")
    r.body(
        "Thứ tự nên giữ như plan-soft: đóng B6 và B8 trước khi mở nhóm C. B6 chỉ thêm event, không thêm tưới trong firmware mắt. B8 đặt ngưỡng soil sau khi đo ướt và khô trên đúng module, rồi gọi pump sẵn có. Tiếp theo mới tới Hey Jarvis, IR, và các motion di chuyển khi cơ khí đã đứng vững. Song song, có thể đổi TTS sang máy cục bộ để buổi demo không phụ thuộc mạng, và sinh enum từ một tệp dùng chung cho Python và phần chú thích firmware."
    )

    r.h1("TÀI LIỆU THAM KHẢO", "toc_tl")
    r.body("Tài liệu được liệt kê theo cách trình bày kiểu IEEE, đúng phần hướng dẫn của khung báo cáo.")
    refs = [
        "[1] ITU-T, “Overview of the Internet of things,” Recommendation Y.4000/Y.2060, 2012.",
        "[2] Espressif Systems, “ESP32 Series Datasheet,” phiên bản tài liệu kỹ thuật của nhà sản xuất, tra cứu tại tài liệu Espressif.",
        "[3] Espressif Systems, “ESP32 Arduino core,” tài liệu Wi-Fi station và WebServer trong gói Arduino-ESP32.",
        "[4] Arduino, “Arduino Uno Rev3,” tài liệu sản phẩm và sơ đồ chân ATmega328P.",
        "[5] T. Bray, Ed., “The JavaScript Object Notation (JSON) Data Interchange Format,” RFC 8259, IETF, 2017.",
        "[6] OASIS, “MQTT Version 3.1.1,” OASIS Standard, 2014. (Tài liệu đối chiếu kênh; bản hệ thống này không triển khai broker.)",
        "[7] G. Bradski và cộng sự, Faster-Whisper / CTranslate2, tài liệu nhận dạng tiếng nói chạy tại máy.",
        "[8] Microsoft, “Azure Neural TTS voices,” giọng vi-VN-HoaiMyNeural qua thư viện edge-tts.",
        "[9] Ollama, tài liệu API cục bộ tại cổng 11434 và cơ chế tool calling.",
        "[10] DeepSeek, tài liệu API chat tương thích giao diện OpenAI, model deepseek-chat.",
        "[11] Nhóm đồ án, “PROTOCOL — hợp đồng JSON Jarvis-on-Desk,” tài liệu nội bộ docs/PROTOCOL.md, 2026.",
        "[12] Nhóm đồ án, “CONTEXT — mỗi linh kiện làm gì,” tài liệu nội bộ docs/CONTEXT.md, 2026.",
        "[13] Nhóm đồ án, “Plan phần mềm (plan-soft),” tài liệu nội bộ docs/plan-soft.md, 2026.",
        "[14] Nhóm đồ án, “Map emotion / motion → TFT + Otto servo,” docs/MOTION_EMOTION_MAP.md, 2026.",
    ]
    for ref in refs:
        r.body(ref)

    # ===== PHỤ LỤC =====
    r.h1("PHỤ LỤC", "toc_pl")
    r.h2("Phụ lục A. Các lệnh JSON tra cứu", "toc_pla")
    r.body(
        "Phụ lục này chép lại dạng lệnh để khi demo không phải lật chương 2. Mọi dòng là một tin. id là ví dụ."
    )
    r.caption("Bảng A.1. Lệnh gửi và ý nghĩa", "tbl_a_1")
    r.table(
        ["Lệnh", "Đích", "Đối số", "Kết quả đúng"],
        [
            ["ping", "esp32", "không", "ok true"],
            ["led", "esp32", "state: 6 giá trị", "echo state, đổi TFT"],
            ["motion", "esp32", "name trong enum", "echo name, chạy servo"],
            ["get_env", "uno", "không", "temp, hum, light, soil"],
            ["relay", "uno", "id light|fan, on", "đóng hoặc mở tải"],
            ["pump", "uno", "on, seconds 1–5", "chạy rồi tự tắt; hoặc busy"],
            ["speak_and_act", "host", "text, emotion, motion", "tách ba ngả"],
            ["event clap / proximity", "từ esp32", "name", "host quyết định sau"],
            ["event ir", "từ uno", "name, code", "dành cho tuần 4"],
        ],
        [3.6, 2.4, 4.6, 5.2],
    )
    r.body(
        "Ví dụ ping: {\"v\":1,\"id\":\"0\",\"to\":\"esp32\",\"cmd\":\"ping\"}. Ví dụ led: state listening. Ví dụ motion: name nod. Ví dụ get_env trả temp 28.4 và hum 61.0 khi dùng mock; trên bàn, số là số đo. Ví dụ relay đèn: {\"v\":1,\"id\":\"4\",\"to\":\"uno\",\"cmd\":\"relay\",\"id\":\"light\",\"on\":true}. Ví dụ bơm: seconds 2. Ví dụ speak_and_act: text tiếng Việt, emotion alert, motion nod. Ví dụ lỗi: ok false, error unknown_cmd."
    )
    r.body(
        "Trường from trên đường về là esp32, uno hoặc host. Host echo id. Thiếu id ở lệnh đời sau vẫn nên được board chấp nhận nếu firmware đã nới, nhưng công cụ mới phải luôn gửi id để đối chiếu log. Không gửi hai object trên một dòng. Không chèn khoảng trắng xuống dòng giữa các trường khi đi Serial."
    )

    r.h2("Phụ lục B. Pin map rút gọn", "toc_plb")
    r.caption("Bảng B.1. Uno", "tbl_b_1")
    r.table(
        ["Thiết bị", "Chân", "Ghi chú"],
        [
            ["DHT11", "D2", "OUT"],
            ["LDR MS-CDS05", "A0", "Số thấp = sáng hơn"],
            ["Độ ẩm đất", "A1", "Số lớn = khô hơn"],
            ["LCD I2C", "A4, A5", "SDA, SCL"],
            ["Buzzer", "D6", "Không có cmd JSON"],
            ["Relay đèn", "D7", "id light"],
            ["LED quạt", "D8", "id fan"],
            ["Bơm qua L298", "D9", "IN1, nguồn riêng"],
        ],
        [4.5, 3.5, 7.8],
    )
    r.caption("Bảng B.2. ESP32 Otto", "tbl_b_2")
    r.table(
        ["Thiết bị", "GPIO", "Ghi chú"],
        [
            ["TFT CS, DC, MOSI, SCK, RST", "22, 21, 23, 18, 27", "VCC 3V3"],
            ["Servo", "16, 13, 26, 14", "5 V ngoài, chung GND"],
            ["HC-SR04 TRIG, ECHO", "4, 5", "Level shifter, sự kiện sau"],
            ["KY-037 D0", "35", "Sự kiện clap sau"],
            ["ESP32", "USB", "Nuôi board"],
        ],
        [6.5, 4.0, 5.3],
    )
    r.body(
        "Khi đang rút hoặc cắm các chân trên, ngắt USB của board đó. Servo không lấy 5 V từ chân của ESP32. Buzzer không quay lại ESP32. NeoPixel không gắn lại “cho vui” vì cmd led đã được định nghĩa là vẽ TFT; gắn thêm đèn sẽ khiến người xem hiểu nhầm trạng thái."
    )

    r.h2("Phụ lục C. Biến môi trường", "toc_plc")
    r.caption("Bảng C.1. Biến hay dùng khi demo", "tbl_c_1")
    r.table(
        ["Biến", "Ví dụ ý nghĩa", "Khối"],
        [
            ["UNO_PORT", "Cổng Serial Uno", "bridge, host"],
            ["ESP32_PORT", "Cổng Serial Otto", "host"],
            ["ESP32_URL", "http://địa-chỉ-ip", "host HTTP"],
            ["ESP32_TRANSPORT", "serial | http | mock | auto", "host"],
            ["ESP32_LED_FACE_ONLY", "0 hoặc 1", "speak_and_act"],
            ["OTTO_ACT", "1 thì pipeline đụng robot", "voice, frontend"],
            ["AI_BACKEND", "mock hoặc serial", "ai"],
            ["AI_FAST_PATH", "1 thì câu mẫu không gọi model", "ai"],
            ["AI_SYSTEM_PROMPT", "Đè prompt Jarvis", "ai"],
            ["LLM_PROVIDER", "ollama hoặc deepseek", "ai"],
            ["DEEPSEEK_API_KEY", "Khóa, không ghi vào báo cáo", "ai"],
            ["STT_MODEL, STT_BEAM", "Độ chính xác Whisper", "voice"],
            ["STT_SILENCE_MS", "600", "voice"],
            ["STT_MAX_SECONDS", "8", "voice"],
            ["TTS_VOICE, TTS_RATE", "HoaiMyNeural, +10%", "voice"],
            ["FRONTEND_PORT", "8787", "frontend"],
        ],
        [4.6, 6.6, 4.6],
    )

    r.h2("Phụ lục D. Thứ tự một buổi demo 15 phút", "toc_pld")
    r.body(
        "Phút 0–2: nguồn 5 V servo đã chung mass, USB hai board, hotspot bật, không mở Serial IDE. Phút 2–4: curl ping hoặc một lệnh Serial ping, thấy ok true. Phút 4–6: python -m serial_bridge đọc get_env, đối chiếu LCD. Phút 6–8: bật đèn, tắt đèn, tưới 2 giây, thử tưới ngay lần hai để thấy busy. Phút 8–12: mở http://127.0.0.1:8787, gõ một câu môi trường và một câu nhờ Otto vui. Phút 12–15: rút tình huống dự phòng — nếu Wi-Fi rớt thì đổi ESP32_TRANSPORT sang serial; nếu Ollama chết thì bật AI_FAST_PATH hoặc chỉ demo tool mock và phần cứng qua bridge."
    )
    r.body(
        "Câu nên chuẩn bị sẵn, viết ra giấy, vì mic hội trường kém: “Nhiệt độ và độ ẩm hiện tại?”, “Bật đèn”, “Tắt đèn”, “Tưới 2 giây”, “Otto vui lên đi”. Câu không nên dùng ở phút cuối: câu ghép nhiều ý, câu cần nhớ lượt trước, câu yêu cầu bước đi dài. Những câu đó thuộc phần hạn chế đã nêu ở kết luận, không phải phần chứng minh."
    )
    r.body(
        "Nếu phải giải thích trong một câu cho người xem không học IoT: laptop là người phiên dịch, Uno là đôi tay với đèn và bình nước, Otto là khuôn mặt. Chúng nói với nhau bằng những tờ giấy JSON một dòng, và tờ giấy của Otto không bao giờ bỏ nhầm vào túi của Uno."
    )


def collect_lists():
    toc = [
        ("MỞ ĐẦU", "toc_intro", 0),
        ("1. Lý do chọn đề tài", "toc_intro_1", 1),
        ("2. Mục tiêu", "toc_intro_2", 1),
        ("3. Đối tượng và phạm vi", "toc_intro_3", 1),
        ("4. Phương pháp thực hiện", "toc_intro_4", 1),
        ("5. Bố cục báo cáo", "toc_intro_5", 1),
        ("CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI VÀ CƠ SỞ LÝ THUYẾT", "toc_c1", 0),
        ("1.1. Bài toán trợ lý bàn làm việc", "toc_c1_1", 1),
        ("1.2. Mô hình phân tầng cho IoT học tập", "toc_c1_2", 1),
        ("1.3. ESP32, Arduino Uno và lý do có hai board", "toc_c1_3", 1),
        ("1.4. Cảm biến và cơ cấu chấp hành", "toc_c1_4", 1),
        ("1.5. Wi-Fi cục bộ và USB Serial", "toc_c1_5", 1),
        ("1.6. JSON một dòng làm hợp đồng", "toc_c1_6", 1),
        ("1.7. Giọng nói: ghi, nhận dạng, đọc", "toc_c1_7", 1),
        ("1.8. Mô hình ngôn ngữ và gọi công cụ", "toc_c1_8", 1),
        ("1.9. Phản hồi cảm xúc và an toàn chấp hành", "toc_c1_9", 1),
        ("CHƯƠNG 2. PHÂN TÍCH YÊU CẦU VÀ THIẾT KẾ", "toc_c2", 0),
        ("2.1. Vai trò theo thư mục", "toc_c2_1", 1),
        ("2.2. Yêu cầu chức năng", "toc_c2_2", 1),
        ("2.3. Kiến trúc lúc chạy", "toc_c2_3", 1),
        ("2.4. Thiết kế hợp đồng lệnh", "toc_c2_4", 1),
        ("2.5. Thiết kế pipeline giọng và độ trễ", "toc_c2_5", 1),
        ("2.6. Thiết kế an toàn, nguồn và những thứ cố ý không làm", "toc_c2_6", 1),
        ("CHƯƠNG 3. XÂY DỰNG VÀ TÍCH HỢP", "toc_c3", 0),
        ("3.1. Firmware ESP32", "toc_c3_1", 1),
        ("3.2. Firmware Uno", "toc_c3_2", 1),
        ("3.3. Cầu nối Serial", "toc_c3_3", 1),
        ("3.4. Host router và mock", "toc_c3_4", 1),
        ("3.5. Khối AI", "toc_c3_5", 1),
        ("3.6. Khối voice", "toc_c3_6", 1),
        ("3.7. Frontend chat", "toc_c3_7", 1),
        ("3.8. Cấu hình và thứ tự ghép", "toc_c3_8", 1),
        ("3.9. Những chức năng dừng ở mức hợp đồng", "toc_c3_9", 1),
        ("CHƯƠNG 4. KIỂM THỬ, KỊCH BẢN VÀ ĐÁNH GIÁ", "toc_c4", 0),
        ("4.1. Chiến lược kiểm thử", "toc_c4_1", 1),
        ("4.2. Kết quả lớp hợp đồng", "toc_c4_2", 1),
        ("4.3. Kịch bản trên bàn", "toc_c4_3", 1),
        ("4.4. Đánh giá mức đạt", "toc_c4_4", 1),
        ("4.5. So sánh với các kênh không dùng trong bản này", "toc_c4_5", 1),
        ("KẾT LUẬN", "toc_kl", 0),
        ("TÀI LIỆU THAM KHẢO", "toc_tl", 0),
        ("PHỤ LỤC", "toc_pl", 0),
    ]
    tables = [
        ("Bảng 0.1. Danh mục từ viết tắt", "tbl_0_1"),
        ("Bảng 1.1. Phân vai hai vi điều khiển", "tbl_1_1"),
        ("Bảng 1.2. Mã lỗi trong phong bì trả lời", "tbl_1_2"),
        ("Bảng 2.1. Thư mục và sản phẩm tương ứng", "tbl_2_1"),
        ("Bảng 2.2. Enum led.state và motion mặc định", "tbl_2_2"),
        ("Bảng 2.3. Trong plan và ngoài plan (rút gọn)", "tbl_2_3"),
        ("Bảng 4.1. Nhóm kiểm thử tự động và việc chúng khóa", "tbl_4_1"),
        ("Bảng 4.2. Đối chiếu mục tiêu với hiện trạng mã", "tbl_4_2"),
        ("Bảng A.1. Lệnh gửi và ý nghĩa", "tbl_a_1"),
        ("Bảng B.1. Uno", "tbl_b_1"),
        ("Bảng B.2. ESP32 Otto", "tbl_b_2"),
        ("Bảng C.1. Biến môi trường hay dùng khi demo", "tbl_c_1"),
    ]
    figures = [
        ("Hình 1.1. Ba tầng chức năng", "fig_1_1"),
        ("Hình 2.1. Sơ đồ khối hệ thống", "fig_2_1"),
        ("Hình 2.2. Pipeline một lượt nói", "fig_2_2"),
        ("Hình 2.3. Tách speak_and_act", "fig_2_3"),
    ]
    return toc, tables, figures


def stamp_page_numbers(path: Path) -> int:
    """Ghi số trang tĩnh cho mục lục. Word tính PAGEREF thành 1 cho mọi mục."""
    doc = Document(str(path))
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    cap = 30
    page = 1
    lines = 0.0
    bm_page: dict[str, int] = {}

    def newpage() -> None:
        nonlocal page, lines
        page += 1
        lines = 0.0

    for child in list(doc.element.body):
        tag = child.tag.split("}")[-1]
        if tag == "sectPr":
            continue
        if tag == "tbl":
            rows = child.findall(W + "tr")
            need = len(rows) * 0.85 + 0.5
            if lines + need > cap and lines > 0:
                newpage()
            lines += need
            continue
        if tag != "p":
            continue
        pPr = child.find(W + "pPr")
        if pPr is not None and pPr.find(W + "sectPr") is not None:
            page += 1
            lines = 0.0
        pb = pPr.find(W + "pageBreakBefore") if pPr is not None else None
        if pb is not None and pb.get(qn("w:val")) not in ("0", "false"):
            newpage()
        text = "".join(t.text or "" for t in child.iter(W + "t"))
        if child.find(".//" + W + "drawing") is not None:
            need = 14.0
        else:
            need = 0.35 if not text.strip() else max(1.0, len(text) / 82)
        if lines + need > cap and lines > 2:
            newpage()
        lines += need
        for b in child.findall(W + "bookmarkStart"):
            name = b.get(qn("w:name"))
            if name:
                bm_page[name] = page

    for p in doc.element.body.iter(W + "p"):
        instrs = [t for t in p.iter(W + "instrText") if t.text and "PAGEREF" in t.text]
        if not instrs:
            continue
        name = instrs[0].text.strip().split()[1]
        num = str(bm_page.get(name, ""))
        for el in list(p):
            if el.tag != W + "r":
                continue
            if el.find(W + "fldChar") is not None or el.find(W + "instrText") is not None:
                p.remove(el)
                continue
            texts = list(el.iter(W + "t"))
            if texts and (texts[0].text or "").strip() in {"", "1"} and el.find(W + "tab") is None:
                texts[0].text = num

    sect = doc.element.body[-1]
    pg = sect.find(W + "pgNumType")
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        sect.append(pg)
    pg.set(qn("w:start"), "4")
    settings = doc.settings.element
    for old in settings.findall(qn("w:updateFields")):
        settings.remove(old)
    doc.save(str(path))
    return page


def main() -> None:
    shutil.copy2(TEMPLATE, OUT)
    doc = Document(str(OUT))
    strip_after_cover(doc)
    enable_update_fields(doc)
    add_page_footer(doc.sections[-1])
    figs = make_figures()
    r = R(doc)
    toc, tables, figures = collect_lists()
    write_front(r, toc, tables, figures)
    write_body(r, figs)
    cp = doc.core_properties
    cp.title = "Báo cáo Jarvis-on-Desk"
    cp.subject = "Mạng kết nối vạn vật — hệ thống trợ lý bàn làm việc"
    cp.category = "Báo cáo nhóm"
    doc.save(str(OUT))
    last = stamp_page_numbers(OUT)
    print(f"wrote {OUT}")
    print(f"chars={r.chars} tables={r.tables} figs={r.figs} stamped_pages={last}")


if __name__ == "__main__":
    main()
