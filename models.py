# exam_app/models.py
from django.db import models
from django.conf import settings
from datetime import datetime



# ------------------------------------------------------------------
# 1. Generated (subjective / theory) questions you save manually
# ------------------------------------------------------------------
class GeneratedQuestion(models.Model):
    question_text = models.TextField()
    marks         = models.IntegerField()
    difficulty    = models.CharField(max_length=20)
    subject       = models.CharField(max_length=100)
    created_at    = models.DateTimeField(auto_now_add=True)
    final_selection = models.BooleanField(default=False)
    used_in_paper = models.BooleanField(default=False)

    def _str_(self):
        # show first 60 chars in admin list
        return self.question_text[:60] + ("…" if len(self.question_text) > 60 else "")


# ------------------------------------------------------------------
# 2. GPT-based MCQ bank (stem + options + answer)
# ------------------------------------------------------------------
class GPTQuestions(models.Model):
    question_text = models.TextField()
    options       = models.JSONField(blank=True, null=True)
    answer        = models.TextField(blank=True, null=True)
    marks         = models.IntegerField(default=1)
    subject       = models.CharField(max_length=255)
    chapter       = models.CharField(max_length=255, blank=True, null=True)
    topic         = models.CharField(max_length=255, blank=True, null=True)
    difficulty    = models.CharField(max_length=100, default="medium")
    final_selection = models.BooleanField(default=False)
    used_in_paper = models.BooleanField(default=False)
    source        = models.CharField(max_length=100, default="mistral-local")  # ✅ Add this

    def _str_(self):
        return self.question_text[:60] + ("…" if len(self.question_text) > 60 else "")

    def get_option_list(self):
        return self.options if self.options else []

    def correct_answer(self):
        return self.answer or "Not Provided"


# ------------------------------------------------------------------
# 3. Archive for every PDF the user prints
# ------------------------------------------------------------------
class PrintedPaper(models.Model):
    user          = models.ForeignKey(settings.AUTH_USER_MODEL,
                                      on_delete=models.CASCADE)
    subject_title = models.CharField(max_length=120)
    course_code   = models.CharField(max_length=30)
    qp_code       = models.CharField(max_length=30)
    duration      = models.CharField(max_length=30)
    max_marks     = models.PositiveSmallIntegerField()
    pdf_url       = models.CharField(max_length=255)
    questions     = models.JSONField()               # full edited list
    created_at    = models.DateTimeField(auto_now_add=True)

    def _str_(self):
        return f"{self.subject_title} – {self.user.username} – {self.created_at:%Y-%m-%d}"
    def generate_filename(self):
        base = f"{self.subject_title}{self.qp_code}{self.created_at:%Y%m%d}"
        return f"{base}.pdf"