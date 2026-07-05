from django.urls import path, include
from .views import (
    home, login_view, insert_question, get_questions, 
    upload_pdf, upload_docx,  
    get_extracted_pdfs, get_extracted_docx,  
    update_question, delete_question,
    GenerateExamPaperPDFView, 
    get_extracted_text_by_filename,
    select_questions_from_extracted_text,
    save_modified_questions,
    get_levels_from_file,generate_mcq_from_file, save_mcq_questions,
    generate_custom_exam_paper, generate_questions_from_file, save_final_questions_for_pdf,
    generate_pdf_from_final_selection,
    signup_view, protected_view,preview_paper,export_bmscw_pdf,

    #generate_draft_paper,finalize_paper
)

from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static
from .question_generation import generate_mcq , generate_questions_from_prompt


urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('protected/', protected_view, name='protected'),
    path('oauth/', include('social_django.urls', namespace='social')),

    path('insert/', insert_question, name='insert_question'),
    path('questions/', get_questions, name='get_questions'),
    path('update/<str:question_id>/', update_question, name='update_question'),
    path('delete/<str:question_id>/', delete_question, name='delete_question'),

    path('upload-pdf/', upload_pdf, name='upload_pdf'),
    path('pdfs/', get_extracted_pdfs, name='get_extracted_pdfs'),
    path('upload-docx/', upload_docx, name='upload_docx'),
    path('get_extracted_docx/', get_extracted_docx, name='get_extracted_docx'),
    path('get_extracted_text/<str:filetype>/<str:filename>/', get_extracted_text_by_filename),

    path('select_questions_from_extracted_text/', select_questions_from_extracted_text),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path("save-gemini-questions/", save_modified_questions, name="save_gemini_questions"),
    path("get_levels_from_file/", get_levels_from_file, name="get_levels_from_file"),
    path('auto_generate_from_syllabus/', generate_questions_from_file, name='auto_generate_from_syllabus'),
    path('generate-mcq-from-syllabus/', generate_mcq_from_file, name='generate_mcq_from_syllabus'),
    path('save-mcq-questions/', save_mcq_questions, name='save_mcq_questions'),
    path('generate-custom-exam-paper/', generate_custom_exam_paper, name='generate_custom_exam_paper'),

    #  Core question generators
    path('generate-prompt/', generate_questions_from_prompt),
    path('generate-mcqs/', generate_mcq),

    path("save-final-questions-for-pdf/", save_final_questions_for_pdf, name="save_final_questions_for_pdf"),
    path('generate-final-pdf/', generate_pdf_from_final_selection, name='generate_final_pdf'),
    path('generate-exam-paper/', GenerateExamPaperPDFView.as_view(), name='generate_exam_paper'),



    # path('regenerate-question/', regenerate_question),
    # path("regenerate-mcq/", regenerate_mcqs, name="regenerate_mcq_question"),
  
    path("preview-paper/", preview_paper),
    path("api/export_bmscw_pdf/", export_bmscw_pdf),




] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)