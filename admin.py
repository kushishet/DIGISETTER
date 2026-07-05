# Register your models here.
from django.contrib import admin
from .models import GeneratedQuestion, GPTQuestions, PrintedPaper

admin.site.register(GeneratedQuestion)
admin.site.register(GPTQuestions)
admin.site.register(PrintedPaper)