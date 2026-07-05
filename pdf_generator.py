# exam_app/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from textwrap import wrap
from io import BytesIO
from datetime import datetime
import os
from datetime import datetime


from django.conf import settings
from .utils import sanitize 
from reportlab.lib.units import inch
     # already in your project

# ------------------------------------------------------------------
# simple list-style PDF (unchanged)
# ------------------------------------------------------------------
from fpdf import FPDF
import os
from django.conf import settings

# exam_app/pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from textwrap import wrap
from io import BytesIO
from datetime import datetime
import os
from django.conf import settings
from .utils import sanitize
from fpdf import FPDF


def generate_pdf(django_questions, mongo_questions):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Exam Paper", ln=1, align='C')
    pdf.ln(10)

    all_questions = list(django_questions) + list(mongo_questions)

    for idx, question in enumerate(all_questions, start=1):
        q_text = question.get("question_text", "")
        pdf.multi_cell(0, 10, f"{idx}. {q_text}")
        if "options" in question:
            for opt in question["options"]:
                pdf.multi_cell(0, 8, f"   {opt}")
        pdf.ln(2)

    path = os.path.join(settings.MEDIA_ROOT, "generated_exam.pdf")
    pdf.output(path)
    return os.path.join(settings.MEDIA_URL, os.path.relpath(path, settings.MEDIA_ROOT)).replace("\\", "/")


def generate_pdf_bmscw(
        subject_title,
        course_code,
        qp_code,
        qs_2m, qs_5m, qs_10m,
        exam_sem_line="VI SEMESTER END EXAMINATION – JULY 2024",
        college="B.M.S COLLEGE FOR WOMEN",
        city="BENGALURU",
        scheme="(NEP Scheme 2021-22 onwards)",
        duration="2 ½ Hours",
        max_marks=60
):
    folder = os.path.join(settings.MEDIA_ROOT, "exam_papers")
    os.makedirs(folder, exist_ok=True)
    fname = f"StyledExam_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    path = os.path.join(folder, fname)

    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    left = 50
    y = H - 70

    c.setFont("Times-Bold", 10)
    c.drawString(left, y, "UUCMS No."); y -= 15
    c.setFont("Times-Bold", 12)
    c.drawCentredString(W / 2, y, college); y -= 15
    c.drawCentredString(W / 2, y, city); y -= 25
    c.setFont("Times-Bold", 11)
    c.drawCentredString(W / 2, y, exam_sem_line); y -= 22
    c.drawCentredString(W / 2, y, f"B.C.A. - {subject_title.upper()}"); y -= 15
    c.setFont("Times-Italic", 10)
    c.drawCentredString(W / 2, y, scheme); y -= 22

    c.setFont("Times-Roman", 11)
    c.drawString(left, y, f"Course Code: {course_code}")
    c.drawRightString(W - left, y, f"QP Code: {qp_code}"); y -= 15
    c.drawString(left, y, f"Duration: {duration}")
    c.drawRightString(W - left, y, f"Max. Marks: {max_marks}"); y -= 25

    c.setFont("Times-Bold", 11)
    c.drawString(left, y, "Instructions:")
    c.setFont("Times-Roman", 11)
    c.drawString(left + 80, y, "Answer all the sections."); y -= 25

    def section(title, desc, questions, start_no):
        nonlocal y
        c.setFont("Times-Bold", 11)
        c.drawString(left, y, title); y -= 18
        c.drawString(left, y, desc); y -= 20
        c.setFont("Times-Roman", 11)
        qno = start_no

        for q in questions:
            lines = wrap(f"{qno}. {sanitize(q['question_text'])}", 100)
            for line in lines:
                if y < 60:
                    c.showPage(); y = H - 60
                    c.setFont("Times-Roman", 11)
                c.drawString(left, y, line); y -= 15

            if "sub_questions" in q and q["sub_questions"]:
                for sq in q["sub_questions"]:
                    sq_text = f"   ({sq['label']}) {sanitize(sq['text'])}"
                    for line in wrap(sq_text, 95):
                        if y < 60:
                            c.showPage(); y = H - 60
                            c.setFont("Times-Roman", 11)
                        c.drawString(left + 20, y, line); y -= 15
                y -= 5

            qno += 1
            y -= 10

        return qno

    next_q = section("SECTION - A", "I. Answer any Ten questions. Each carries TWO marks.", qs_2m, 1)
    next_q = section("SECTION - B", "II. Answer any Six questions. Each carries FIVE marks.", qs_5m, next_q)
    section("SECTION - C", "III. Answer any One question. It carries TEN marks.", qs_10m, next_q)

    c.setFont("Times-Bold", 12)
    c.drawCentredString(W / 2, 40, "*")
    c.setFont("Times-Italic", 8)
    c.drawCentredString(W / 2, y, "*")
    c.save()

    return os.path.join(settings.MEDIA_URL, os.path.relpath(path, settings.MEDIA_ROOT)).replace("\\", "/")

#------------------------------------------------------------------
#  QUICK “draft preview” PDF  (plain list, no headers)
# ------------------------------------------------------------------
# exam_app/pdf_generator.py
def generate_styled_exam_pdf(header, questions_2m, questions_5m, questions_10m):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from textwrap import wrap
    from datetime import datetime
    import os
    from django.conf import settings
    from .utils import sanitize

    folder = os.path.join(settings.MEDIA_ROOT, "exam_papers")
    os.makedirs(folder, exist_ok=True)
    filename = f"StyledExam_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    path = os.path.join(folder, filename)

    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    y = height - inch

    # Top header
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 50, y, "UCMS No.")
    y -= 15
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, "B.M.S COLLEGE FOR WOMEN")
    y -= 15
    c.drawCentredString(width / 2, y, "BENGALURU")
    y -= 15
    c.drawCentredString(width / 2, y, "VI SEMESTER END EXAMINATION - JULY 2024")
    y -= 15
    c.drawCentredString(width / 2, y, f"B.C.A. - {header['subject_title'].upper()}")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, y, "(NEP Scheme 2021-22 onwards)")
    y -= 20

    c.drawString(50, y, f"Course Code: {header['course_code']}")
    c.drawString(200, y, f"Duration: {header['duration']}")
    c.drawString(width - 200, y, f"QP Code: {header['qp_code']}")
    c.drawString(width - 90, y, f"Max. Marks: {header['max_marks']}")
    y -= 25

    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Instructions:")
    c.setFont("Helvetica", 10)
    c.drawString(120, y, "Answer all the sections.")
    y -= 20

    def write_section(title, subtitle, questions, start_no):
        nonlocal y
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, title)
        y -= 15
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, subtitle)
        y -= 20
        c.setFont("Helvetica", 10)
        qno = start_no
        for q in questions:
            clean = sanitize(q.get("question_text", ""))
            for line in wrap(f"{qno}. {clean}", 100):
                if y < 60:
                    c.showPage()
                    y = height - inch
                    c.setFont("Helvetica", 10)
                c.drawString(60, y, line)
                y -= 15
            qno += 1
            y -= 5
        return qno

    next_no = write_section("SECTION - A", "I. Answer any TEN questions. Each carries TWO marks.", questions_2m, 1)
    next_no = write_section("SECTION - B", "II. Answer any SIX questions. Each carries FIVE marks.", questions_5m, next_no)
    write_section("SECTION - C", "III. Answer any ONE question. It carries TEN marks.", questions_10m, next_no)

    c.drawCentredString(width / 2, y - 30, "*")
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2, 30, "*")
    c.save()

    return os.path.join(settings.MEDIA_URL, os.path.relpath(path, settings.MEDIA_ROOT)).replace("\\", "/")

def safe_unicode(text):
    try:
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="replace")
        return (
            str(text)
            .replace("-", "-")
            .replace("—", "-")
            .replace("“", '"')
            .replace("”", '"')
            .replace("'", "'")
            .replace("'", "'")
            .replace("…", "...")
        )
    except Exception as e:
        return "Bad text"

# ------------------------------------------------------------------
# university-style PDF (Part I / II / III)
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# university-style PDF  (Part I / II / III)
def generate_pdf_custom(heading, questions_2m, questions_5m, questions_10m):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from textwrap import wrap
    from datetime import datetime
    import os
    from django.conf import settings
    from .utils import sanitize

    folder = os.path.join(settings.MEDIA_ROOT, "exam_papers")
    os.makedirs(folder, exist_ok=True)
    filename = f"ExamPaper_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    path = os.path.join(folder, filename)

    c = canvas.Canvas(path, pagesize=A4)
    W, H = A4
    y = H - inch

    # Heading
    c.setFont("Helvetica-Bold", 14)
    for line in heading.splitlines():
        c.drawCentredString(W / 2, y, line.strip())
        y -= 20
    y -= 20

    def draw_block(title, docs, start_no):
        nonlocal y
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, title)
        y -= 25
        c.setFont("Helvetica", 11)
        qno = start_no

        for d in docs:
            txt = sanitize(d.get("question_text", ""))
            for line in wrap(f"{qno}. {txt}", 110):
                if y < 80:
                    c.showPage()
                    y = H - 60
                    c.setFont("Helvetica", 11)
                c.drawString(55, y, line)
                y -= 15
            qno += 1
            y -= 6
        y -= 10
        return qno

    next_no = draw_block("PART - I: Answer any Ten questions. Each carries 2 marks", questions_2m, 1)
    next_no = draw_block("PART - II: Answer any Six questions. Each carries 5 marks ", questions_5m, next_no)
    draw_block("PART - III: Answer any One question.Each carries 10 marks ", questions_10m, next_no)

    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(W / 2, 3, "*")
    c.save()

    return os.path.join(settings.MEDIA_URL, os.path.relpath(path, settings.MEDIA_ROOT)).replace("\\", "/")

from fpdf import FPDF
import os
from django.conf import settings
def generate_draft_pdf(questions):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Draft Exam Paper (MCQs)", ln=1, align='C')
    pdf.ln(10)

    for idx, question in enumerate(questions, 1):
        pdf.multi_cell(0, 10, f"{idx}. {question['question_text']}")
        for option in question.get("options", []):
            pdf.multi_cell(0, 8, f"   {option}")
        pdf.ln(2)

    file_path = os.path.join(settings.MEDIA_ROOT, "draft_exam_mcqs.pdf")
    pdf.output(file_path)
    return file_path

def split_text(text, max_chars=100):

    words = text.split()
    lines = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > max_chars:
            lines.append(current)
            current = word
        else:
            current += " " + word if current else word
    if current:
        lines.append(current)
    return lines

def safe_unicode(text):
    # Replace common problematic characters with ASCII equivalents
    return (
        text.replace("-", "-")
            .replace("—", "-")
            .replace("“", '"')
            .replace("”", '"')
            .replace("'", "'")
            .replace("'", "'")
    )