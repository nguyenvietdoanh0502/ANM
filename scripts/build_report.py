"""Build editable DOCX and a matching-content PDF using actual experiment data.

Run with a Python environment containing python-docx, reportlab and pandas.
The report is split into reading units; PDF pages are checked after generation.
"""
from __future__ import annotations

import json
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, Image, KeepTogether)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from docs.report_content import SECTIONS, REFERENCES
from scripts.experiment_sections import measured_sections

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/report"
OUT.mkdir(parents=True, exist_ok=True)
EXPERIMENTS, META, TESTS = measured_sections(ROOT)
CONTENT = SECTIONS + EXPERIMENTS
FIGURE_CAPTIONS = {
    "toy_curve.png": "Các điểm hữu hạn của đường cong ví dụ và một số bội của G",
    "architecture.png": "Kiến trúc và quan hệ giữa các mô-đun",
    "ui_hash.png": "Sơ đồ chức năng giao diện khám phá SHA",
    "ui_signature.png": "Sơ đồ chức năng giao diện ký và xác minh",
    "keygen.png": "Trung vị thời gian tạo khóa trong lần đo tham chiếu",
    "hash.png": "Trung vị thời gian băm theo kích thước dữ liệu",
    "sign_digest.png": "Trung vị thời gian ký digest",
    "hash_sign.png": "Trung vị thời gian băm cộng ký"
}


def picture_path(name):
    path = OUT / "figures" / name
    return path if path.exists() else ROOT / "output/reference_run" / name


ABSTRACT = [
    "Báo cáo nghiên cứu cơ sở toán học của mật mã đường cong elliptic và ứng dụng ECDSA để tạo, xác minh chữ ký số. Hai hàm băm SHA-256 và SHA-512 được khảo sát trong cùng quy trình; RSA-PSS với khóa 3072 bit được dùng để so sánh với P-256 ở mức an toàn cổ điển tham chiếu khoảng 128 bit.",
    "Sản phẩm là ứng dụng Python và Streamlit chạy trên máy cá nhân. Người dùng tạo hoặc nhập khóa, ký văn bản/tệp và xác minh chữ ký tách rời. Chương trình cho phép thử thay đổi dữ liệu, quan sát digest và đo riêng thời gian băm, ký, xác minh. Phần ứng dụng sử dụng thư viện cryptography; ví dụ trường nhỏ chỉ phục vụ giải thích toán học.",
    f"Lần đo tham chiếu có 7.240 mẫu thời gian, kèm thông tin môi trường và dữ liệu từng lượt. Bộ kiểm thử ghi nhận {TESTS} trường hợp đạt. Kết quả cho thấy ECDSA có biểu diễn khóa công khai và chữ ký nhỏ hơn RSA trong cấu hình khảo sát. Chi phí ký ECDSA thấp hơn ở các nhóm đã đo, còn tốc độ xác minh cần đọc theo từng cấu hình và xét nhiễu đo.",
    "Phạm vi kết luận giới hạn ở cấu hình và máy đã khảo sát. Ứng dụng chưa triển khai chứng thư số, dấu thời gian hay ký PDF nhúng. Chữ ký hợp lệ được hiểu là khớp với byte dữ liệu và khóa công khai được cung cấp, không tự xác nhận danh tính ngoài đời của chủ khóa.",
    "Từ khóa: ECC, ECDSA, P-256, SHA-256, SHA-512, RSA-PSS, chữ ký số, thực nghiệm."
]


def set_repeat(row):
    header = OxmlElement("w:tblHeader")
    row._tr.get_or_add_trPr().append(header)


def doc_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = ([5.3,10.7] if len(headers)==2 else [16/len(headers)]*len(headers))
    for column, width in zip(table.columns, widths):
        column.width = Cm(width)
    for cell, text, width in zip(table.rows[0].cells, headers, widths):
        cell.text = text; cell.width = Cm(width)
        shd = OxmlElement("w:shd"); shd.set(qn("w:fill"), "DDEAF1"); cell._tc.get_or_add_tcPr().append(shd)
        for run in cell.paragraphs[0].runs: run.bold = True
    set_repeat(table.rows[0])
    for row in rows:
        cells = table.add_row().cells
        for cell, text, width in zip(cells, row, widths):
            cell.text = str(text); cell.width = Cm(width)
    for row_index, row in enumerate(table.rows):
        cant_split = OxmlElement("w:cantSplit")
        row._tr.get_or_add_trPr().append(cant_split)
        for cell in row.cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr = cell._tc.get_or_add_tcPr()
            borders = OxmlElement("w:tcBorders")
            for side in ("top","left","bottom","right"):
                e = OxmlElement("w:"+side); e.set(qn("w:val"),"single"); e.set(qn("w:sz"),"4"); e.set(qn("w:color"),"D9D9D9"); borders.append(e)
            tcpr.append(borders)
            margins = OxmlElement("w:tcMar")
            for side in ("top","left","bottom","right"):
                e = OxmlElement("w:"+side); e.set(qn("w:w"),"90"); e.set(qn("w:type"),"dxa"); margins.append(e)
            tcpr.append(margins)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(3); p.paragraph_format.line_spacing = 1.1
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.keep_with_next = row_index < len(table.rows) - 1
                for run in p.runs: run.font.size = Pt(10.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(0)


def build_docx():
    doc = Document()
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21)
    sec.top_margin, sec.bottom_margin = Cm(2), Cm(2)
    sec.left_margin, sec.right_margin = Cm(3), Cm(2)
    for name in ("Normal","Title","Subtitle","Heading 1","Heading 2","Caption"):
        style = doc.styles[name]
        style.font.name = "Times New Roman"; style.font.color.rgb = RGBColor(0,0,0)
    normal = doc.styles["Normal"]
    normal.font.size = Pt(13)
    normal.paragraph_format.line_spacing = 1.35
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.widow_control = True
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name, size in (("Title",22),("Heading 1",16),("Heading 2",14),("Caption",10.5)):
        doc.styles[name].font.size = Pt(size)
    doc.styles["Heading 2"].paragraph_format.space_before = Pt(12)
    doc.styles["Caption"].paragraph_format.line_spacing = 1.1
    # Remove built-in theme overrides and title borders from the base template.
    for root in (doc.styles.element, doc.element):
        for fonts in root.iter(qn("w:rFonts")):
            for attr in list(fonts.attrib):
                if "theme" in attr.lower():
                    del fonts.attrib[attr]
        for border in list(root.iter(qn("w:pBdr"))):
            border.getparent().remove(border)
    footer = sec.footer.paragraphs[0]; footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement("w:fldSimple"); field.set(qn("w:instr"),"PAGE"); footer._p.append(field)
    doc.core_properties.title = "Nghiên cứu hệ mật đường cong elliptic và ứng dụng tạo chữ ký số"
    doc.core_properties.subject = "Bài tập lớn An ninh mạng"
    doc.core_properties.author = ""
    for text in ("TRƯỜNG ................................................", "KHOA ..................................................."):
        p=doc.add_paragraph(text); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("\n")
    p=doc.add_paragraph("BÀI TẬP LỚN\nMÔN AN NINH MẠNG",style="Title"); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p=doc.add_paragraph("Nghiên cứu hệ mật đường cong elliptic\nvà ứng dụng tạo chữ ký số",style="Title"); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p=doc.add_paragraph("ECC và SHA256 SHA512\nSo sánh ECDSA với RSAPSS",style="Subtitle"); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("\n")
    for text in ("Giảng viên hướng dẫn: ........................................", "Sinh viên thực hiện: ............................................", "Mã sinh viên: .......................................................", "Lớp: ..................................................................."):
        doc.add_paragraph(text)
    p=doc.add_paragraph("Tháng 11 năm 2026"); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break(); doc.add_heading("Tóm tắt",level=1)
    for text in ABSTRACT: doc.add_paragraph(text)
    doc.add_heading("Ký hiệu và chữ viết tắt",level=2)
    doc_table(doc,["Ký hiệu", "Ý nghĩa"], [["p / n","Modulo tọa độ / bậc điểm sinh"],["G / O","Điểm sinh / điểm vô cực"],["d / Q / k","Khóa bí mật / khóa công khai / nonce"],["DER / PEM","Định dạng nhị phân / biểu diễn văn bản"],["KiB / MiB","1.024 byte / 1.048.576 byte"]])
    doc.add_page_break(); doc.add_heading("Mục lục",level=1)
    toc_p = doc.add_paragraph()
    run = toc_p.add_run()
    start = OxmlElement("w:fldChar"); start.set(qn("w:fldCharType"), "begin"); run._r.append(start)
    instruction = OxmlElement("w:instrText"); instruction.set(qn("xml:space"), "preserve")
    instruction.text = ' TOC \\o "1-2" \\h \\z \\u '; run._r.append(instruction)
    separator = OxmlElement("w:fldChar"); separator.set(qn("w:fldCharType"), "separate"); run._r.append(separator)
    toc_p.add_run("\n".join("Chương " + c for c in dict.fromkeys(s["chapter"] for s in CONTENT)))
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end"); toc_p.add_run()._r.append(end)
    previous=None; figure_number=0; table_number=0
    for item in CONTENT:
        if item["chapter"] != previous:
            doc.add_page_break()
            doc.add_heading("Chương " + item["chapter"],level=1); previous=item["chapter"]
        doc.add_heading(item["title"],level=2)
        for text in item["paragraphs"]: doc.add_paragraph(text)
        equations = item.get("equations") or []
        for eq_index, equation in enumerate(equations):
            p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = eq_index < len(equations)-1
            math=OxmlElement("m:oMath"); run=OxmlElement("m:r"); t=OxmlElement("m:t"); t.text=equation; run.append(t); math.append(run); p._p.append(math)
        if item.get("code"):
            for line in item["code"].splitlines():
                p=doc.add_paragraph(); p.paragraph_format.line_spacing=1; p.paragraph_format.space_after=Pt(2)
                r=p.add_run(line); r.font.name="Consolas"; r.font.size=Pt(10)
        if item.get("table"):
            table_number+=1
            caption=doc.add_paragraph(f"Bảng {table_number}  {item['title'].split(' ',1)[1]}",style="Caption")
            caption.paragraph_format.keep_with_next = True
            doc_table(doc,*item["table"])
        if item.get("figure"):
            figure_number+=1; path=picture_path(item["figure"])
            p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next=True
            p.add_run().add_picture(str(path),width=Cm(15.5))
            doc.add_paragraph(f"Hình {figure_number}  {FIGURE_CAPTIONS[item['figure']]}",style="Caption")
    doc.add_page_break(); doc.add_heading("Tài liệu tham khảo",level=1)
    for tag,desc,url in REFERENCES:
        p = doc.add_paragraph(f"{tag} {desc}\n{url}")
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.add_paragraph("Các tài liệu trực tuyến được đối chiếu ngày 15 tháng 11 năm 2026. Số liệu thực nghiệm do chương trình của đề tài sinh ra, lưu cùng mã nguồn.")
    doc.add_page_break(); doc.add_heading("Phụ lục hướng dẫn tái lập",level=1)
    for text in APPENDIX: doc.add_paragraph(text)
    settings=doc.settings.element
    update=OxmlElement("w:updateFields"); update.set(qn("w:val"),"true"); settings.append(update)
    path=OUT/"Bao_cao_ECC_Chu_ky_so.docx"; doc.save(path)
    return path


APPENDIX = [
    "Cài Python và tạo môi trường ảo trong thư mục dự án bằng python -m venv .venv. Cài thư viện từ requirements.txt. Trên Windows dùng .venv\\Scripts\\python.exe cho các lệnh dưới đây; trên Linux/macOS dùng .venv/bin/python.",
    "Mở ứng dụng: python -m streamlit run app.py. Truy cập http://127.0.0.1:8501. Tạo khóa trong Quản lý khóa rồi chuyển sang Ký và xác minh. Tệp samples/message.txt cùng samples/ecdsa_public.pem và samples/ecdsa_sha-256.json cho một phép kiểm tra hợp lệ; thay bằng message_tampered.txt để kiểm tra thất bại.",
    "Kiểm thử: python -m pytest -q --junitxml=output/test-results.xml. Chương trình kiểm thử cần quyền ghi thư mục tạm. Nếu môi trường hạn chế thư mục tạm hệ thống, chọn một thư mục tạm mới trong workspace bằng --basetemp và bảo đảm thư mục cha đã tồn tại.",
    "Thực nghiệm đầy đủ: python -m ecc_lab.benchmark --output output/experiments. Không thêm --quick khi cần số liệu theo cấu hình báo cáo. Giữ kết quả tham chiếu ban đầu để đối chiếu; mỗi lần chạy mới nên có thư mục riêng.",
    "Kiểm tra raw.csv có 7.240 dòng dữ liệu cho cấu hình đầy đủ, summary.csv có count đúng từng nhóm và metadata.json có môi trường thực tế. Đơn vị time_ms là mili giây. std_ms dùng độ lệch chuẩn mẫu. Đối chiếu các bảng trong báo cáo với CSV trước khi trình bày.",
    "Nguồn nội dung nằm trong docs/report_content.py và scripts/experiment_sections.py. Chạy python -m scripts.make_figures trước, sau đó dùng môi trường có python-docx, reportlab, pandas để chạy python -m scripts.build_report. Phần đầu báo cáo có chỗ điền trường, khoa, giảng viên, họ tên, mã sinh viên và lớp.",
    "Kịch bản trình bày đầy đủ và câu hỏi ôn tập nằm trong docs/DEMO.md. Khi trình bày, nêu rõ hình giao diện trong báo cáo là sơ đồ mô tả. Có thể trình diễn trực tiếp sản phẩm để bổ sung bằng chứng về bố cục và tương tác thực tế."
]


def build_pdf():
    font_dir=Path("C:/Windows/Fonts")
    for name,filename in (("TNR","times.ttf"),("TNR-Bold","timesbd.ttf"),("TNR-Italic","timesi.ttf"),("SymbolText","arial.ttf")):
        pdfmetrics.registerFont(TTFont(name,str(font_dir/filename)))
    pdfmetrics.registerFontFamily("TNR",normal="TNR",bold="TNR-Bold",italic="TNR-Italic",boldItalic="TNR-Bold")
    styles={
        "body":ParagraphStyle("body",fontName="TNR",fontSize=13,leading=17.55,spaceAfter=6,alignment=TA_JUSTIFY),
        "reference":ParagraphStyle("reference",fontName="TNR",fontSize=13,leading=17.55,spaceAfter=6),
        "h1":ParagraphStyle("h1",fontName="TNR-Bold",fontSize=16,leading=21,spaceAfter=12),
        "h2":ParagraphStyle("h2",fontName="TNR-Bold",fontSize=14,leading=19,spaceAfter=10),
        "title":ParagraphStyle("title",fontName="TNR-Bold",fontSize=22,leading=29,alignment=TA_CENTER,spaceAfter=20),
        "center":ParagraphStyle("center",fontName="TNR",fontSize=13,leading=18,alignment=TA_CENTER,spaceAfter=12),
        "caption":ParagraphStyle("caption",fontName="TNR-Italic",fontSize=10.5,leading=14,spaceAfter=7),
        "cell":ParagraphStyle("cell",fontName="TNR",fontSize=10.5,leading=13),
        "equation":ParagraphStyle("equation",fontName="SymbolText",fontSize=11,leading=17,alignment=TA_CENTER,spaceAfter=5),
    }
    def p(text,style="body"):
        return Paragraph(escape(str(text)).replace("\n","<br/>"),styles[style])
    story=[]
    story += [p("TRƯỜNG ................................................","center"),p("KHOA ...................................................","center"),Spacer(1,70),p("BÀI TẬP LỚN<br/>MÔN AN NINH MẠNG".replace("<br/>","\n"),"title"),p("Nghiên cứu hệ mật đường cong elliptic\nvà ứng dụng tạo chữ ký số","title"),p("ECC và SHA256 SHA512\nSo sánh ECDSA với RSAPSS","center"),Spacer(1,60)]
    for text in ("Giảng viên hướng dẫn: ........................................", "Sinh viên thực hiện: ............................................", "Mã sinh viên: .......................................................", "Lớp: ..................................................................."):
        story.append(p(text))
    story += [Spacer(1,40),p("Tháng 11 năm 2026","center"),PageBreak(),p("Tóm tắt","h1")]
    story += [p(text) for text in ABSTRACT]
    story += [p("Ký hiệu và chữ viết tắt","h2")]
    def add_table(headers, rows):
        widths=[150,303] if len(headers)==2 else [453/len(headers)]*len(headers)
        data=[[p(x,"cell") for x in row] for row in [headers]+rows]
        table=Table(data,colWidths=widths,repeatRows=1,hAlign="LEFT")
        table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#DDEAF1")),("GRID",(0,0),(-1,-1),.4,colors.HexColor("#D9D9D9")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        story.extend([table,Spacer(1,8)])
    add_table(["Ký hiệu","Ý nghĩa"],[["p / n","Modulo tọa độ / bậc điểm sinh"],["G / O","Điểm sinh / điểm vô cực"],["d / Q / k","Khóa bí mật / khóa công khai / nonce"],["DER / PEM","Nhị phân / văn bản"],["KiB / MiB","1.024 / 1.048.576 byte"]])
    story += [PageBreak(),p("Mục lục nội dung","h1")]
    for chapter in dict.fromkeys(s["chapter"] for s in CONTENT):
        story.append(p("Chương "+chapter,"h2"))
        story.append(p(" · ".join(s["title"] for s in CONTENT if s["chapter"]==chapter)))
    story.extend([p("Tài liệu tham khảo","h2"),p("Phụ lục hướng dẫn tái lập","h2")])
    previous=None; fnum=0; tnum=0
    for item in CONTENT:
        if item["chapter"] != previous:
            story.append(PageBreak())
            story.append(p("Chương "+item["chapter"],"h1")); previous=item["chapter"]
        story.append(p(item["title"],"h2"))
        story.extend(p(text) for text in item["paragraphs"])
        story.extend(p(eq,"equation") for eq in item.get("equations") or [])
        if item.get("code"):
            story.append(p(item["code"],"equation"))
        if item.get("table"):
            tnum+=1; story.append(p(f"Bảng {tnum}  {item['title'].split(' ',1)[1]}","caption")); add_table(*item["table"])
        if item.get("figure"):
            fnum+=1; path=picture_path(item["figure"])
            image=Image(str(path)); image.drawHeight*=440/image.drawWidth; image.drawWidth=440
            story.append(KeepTogether([image,p(f"Hình {fnum}  {FIGURE_CAPTIONS[item['figure']]}","caption")]))
    story += [PageBreak(),p("Tài liệu tham khảo","h1")]
    for tag,desc,url in REFERENCES:
        story.append(p(f"{tag} {desc}\n{url}","reference"))
    story.append(p("Tài liệu trực tuyến được đối chiếu ngày 15 tháng 11 năm 2026. Số liệu thực nghiệm lưu cùng mã nguồn."))
    story += [PageBreak(),p("Phụ lục hướng dẫn tái lập","h1")]+[p(text) for text in APPENDIX]
    def footer(canvas,doc):
        canvas.saveState(); canvas.setFont("TNR",10); canvas.drawCentredString(A4[0]/2,28,str(doc.page)); canvas.restoreState()
    path=OUT/"Bao_cao_ECC_Chu_ky_so.pdf"
    SimpleDocTemplate(str(path),pagesize=A4,leftMargin=85,rightMargin=57,topMargin=50,bottomMargin=48,title="Nghiên cứu ECC và chữ ký số",author="").build(story,onFirstPage=footer,onLaterPages=footer)
    return path


if __name__=="__main__":
    print(build_docx())
    print(build_pdf())
