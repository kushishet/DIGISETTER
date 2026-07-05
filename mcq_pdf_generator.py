#  mcq_pdf_generator.py
from fpdf import FPDF
import os
from django.conf import settings
import re  
from datetime import datetime


class MCQPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "MCQ Question Paper", ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def add_question(self, q_text, options, index):
        self.set_font("Arial", "", 12)
        self.multi_cell(0, 10, f"{index}. {q_text}")
        for i, opt in enumerate(options):
            self.multi_cell(0, 10, f"    ({chr(65+i)}) {opt}")
        self.ln(3)
from fpdf import FPDF
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import os
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def generate_mcq_pdf(data):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 50, "Multiple Choice Questions")
    c.setFont("Helvetica", 11)

    y = height - 100
    count = 1
    for item in data["questions"]:
        question = item.get("question", "").strip()
        options = item.get("options", [])

        c.drawString(50, y, f"{count}. {question}")
        y -= 20
        for i, opt in enumerate(options):
            c.drawString(70, y, f"{chr(65 + i)}. {opt}")
            y -= 20
        y -= 10
        count += 1

        if y < 100:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 11)

    c.save()
    buffer.seek(0)

    # Save to disk
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"mcq_{now}.pdf"
    folder = os.path.join("media", "mcq_papers")
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, filename)

    with open(file_path, "wb") as f:
        f.write(buffer.read())

    return f"/media/mcq_papers/{filename}"