import os
import re
import json
import fitz  # PyMuPDF
from io import BytesIO
from datetime import datetime
from docx import Document
from bson import ObjectId
from dotenv import load_dotenv
from pymongo import MongoClient
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .pdf_generator import generate_draft_pdf
from .pdf_generator import generate_pdf_bmscw ,generate_pdf
from datetime import datetime
from .utils import split_and_clean_questions

# Local project modules
from .models import GPTQuestions, GeneratedQuestion, PrintedPaper
from .common import (
    db, collection, pdf_collection, docx_collection,
    classify_bloom_level, parse_mcq_response, clean_and_parse_json, parse_clean_questions
)
from .llm_client import call_chatgpt
from .common import collection, parse_mcq_blocks, pdf_collection, docx_collection
from .mcq_pdf_generator import generate_mcq_pdf
from .utils import sanitize, make_json_safe, extract_clean_questions, is_valid_question

import re, os, time
# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")

pdf_collection = db["pdfs"]
docx_collection = db["docx_files"]




def home(request):
    return HttpResponse(
        "<h1>Welcome to the Exam Paper Setter API</h1>"
        "<p>Use <a href='/api/'>/api/</a> to access endpoints.</p>"
    )
# =============== Manual SIGNUP API ===============

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
import json

@csrf_exempt
@api_view(['POST'])
def signup_view(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')

        # Check for missing fields
        if not username or not password or not email:
            return JsonResponse({'error': 'Missing fields'}, status=400)

        # Check if email contains @
        if '@' not in email:
            return JsonResponse({'error': 'Invalid email: must contain "@"'}, status=400)
        
        # Validate password strength
        import re
        if not re.fullmatch(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,8}$', password):
            return JsonResponse({
                'error': 'Password must be 6-8 characters long, include letters, numbers, and special characters.'
            }, status=400)

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already registered'}, status=400)

        # Create the user
        user = User.objects.create(
            username=username,
            password=make_password(password),
            email=email
        )
        user.save()

        return JsonResponse({'message': 'User registered successfully!'}, status=201)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# =============== Manual LOGIN API ===============

@csrf_exempt
@api_view(['POST'])
def login_view(request):
    try:
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        
        # Validate password format (same as in signup)
        if not re.fullmatch(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{6,8}$', password):
            return JsonResponse({
                'error': 'Password must be 6-8 characters long, include letters, numbers, and special characters.'
            }, status=400)

        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "username": user.username,
                "email": user.email  # return email too if needed
            })
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

# =============== TEST Protected View ===============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return JsonResponse({'message': f'Hello {request.user.username}, you are authenticated!'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def insert_question(request):
    try:
        collection.insert_one(request.data)
        return JsonResponse({"message": "Question added successfully!"}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_questions(request):
    questions = list(collection.find({}, {"_id": 0}))
    return JsonResponse({"questions": questions}, safe=False)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_question(request, question_id):
    try:
        if not ObjectId.is_valid(question_id):
            return JsonResponse({"error": "Invalid ObjectId format"}, status=400)

        result = collection.update_one(
            {"_id": ObjectId(question_id)},
            {"$set": request.data}
        )
        if result.matched_count == 0:
            return JsonResponse({"error": "Question not found"}, status=404)
        return JsonResponse({"message": "Question updated successfully!"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_question(request, question_id):
    try:
        if not ObjectId.is_valid(question_id):
            return JsonResponse({"error": "Invalid ObjectId format"}, status=400)

        if not request.user.is_staff:
            return JsonResponse({"error": "Only admins can delete questions"}, status=403)

        result = collection.delete_one({"_id": ObjectId(question_id)})
        if result.deleted_count == 0:
            return JsonResponse({"error": "Question not found"}, status=404)
        return JsonResponse({"message": "Question deleted successfully!"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_pdf(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        username = request.user.username
        pdf_file = request.FILES['file']
        file_path = default_storage.save(f"pdfs/{pdf_file.name}", ContentFile(pdf_file.read()))

        doc = fitz.open(f"media/{file_path}")
        text = "\n".join(page.get_text("text") for page in doc)

        pdf_record = {
            "username": request.user.username, 
            "filename": pdf_file.name,
            "extracted_text": text,
            "uploaded_by": username
        }
        pdf_collection.insert_one(pdf_record)

        return JsonResponse({
            "message": "PDF uploaded successfully!",
            "filename": pdf_file.name,
            "extracted_text": text
        }, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_extracted_pdfs(request):
    try:
        # Assuming you store `username` in each PDF record in MongoDB
        username = request.user.username  
        pdfs = list(pdf_collection.find({"username": username}, {"_id": 0, "filename": 1}))
        return JsonResponse({"pdfs": pdfs}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_docx(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        docx_file = request.FILES['file']
        file_path = default_storage.save(f"docs/{docx_file.name}", ContentFile(docx_file.read()))

        doc = Document(f"media/{file_path}")
        text = "\n".join([para.text for para in doc.paragraphs])

        docx_data = {"filename": docx_file.name, "extracted_text": text}
        docx_collection.insert_one(docx_data)

        return JsonResponse({"message": "DOCX uploaded successfully!", "extracted_text": text}, status=201)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_extracted_docx(request):
    try:
        docx_files = list(docx_collection.find({}, {"_id": 0}))
        return JsonResponse({"docx_files": docx_files}, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_extracted_text_by_filename(request, filetype, filename):
    if filetype not in ("pdf", "docx"):
        return JsonResponse({"error": "Invalid file type. Must be 'pdf' or 'docx'."}, status=400)

    target_collection = pdf_collection if filetype == "pdf" else docx_collection
    record = target_collection.find_one({"filename": filename}, {"_id": 0})

    if not record:
        return JsonResponse({"error": f"{filetype.upper()} file not found: {filename}"}, status=404)

    return JsonResponse({
        "filename": filename,
        "extracted_text": record.get("extracted_text", "")
    }, safe=False)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unused_questions(request):
    subject = request.GET.get('subject')
    difficulty = request.GET.get('difficulty')

    query = {"used_in_paper": {"$ne": True}}
    if subject:
        query["subject"] = subject
    if difficulty:
        query["difficulty"] = difficulty

    questions = list(collection.find(query))
    for q in questions:
        q['_id'] = str(q['_id'])
    return JsonResponse({"unused_questions": questions}, safe=False)


class GenerateExamPaperPDFView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        question_ids = request.data.get('question_ids', [])
        mongo_question_ids = request.data.get('mongo_question_ids', [])

        django_questions = GeneratedQuestion.objects.filter(id__in=question_ids)

        mongo_questions = []
        if mongo_question_ids:
            mongo_questions = list(collection.find({"_id": {"$in": [ObjectId(qid) for qid in mongo_question_ids]}}))
            collection.update_many(
                {"_id": {"$in": [ObjectId(qid) for qid in mongo_question_ids]}},
                {"$set": {"used_in_paper": True}}
            )

        pdf_path = generate_pdf(django_questions, mongo_questions)
        return Response({'message': 'PDF generated', 'pdf_file': pdf_path}, status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def select_questions_from_extracted_text(request):
    try:
        questions = request.data.get("selected_questions") or request.data.get("questions")
        filetype = request.data.get("filetype")
        filename = request.data.get("filename")

        if not questions:
            return JsonResponse({"error": "No questions provided"}, status=400)

        inserted_count = 0
        for question in questions:
            if not all([question.get("question_text"), question.get("marks"), question.get("subject"), question.get("difficulty")]):
                continue

            doc = {
                "question_text": question["question_text"],
                "marks": question["marks"],
                "subject": question["subject"],
                "difficulty": question["difficulty"],
                "topic": question.get("topic"),
                "chapter": question.get("chapter"),
                "used_in_paper": False,
            }

            if filetype and filename:
                doc["source_file"] = filename
                doc["source_type"] = filetype

            collection.insert_one(doc)
            inserted_count += 1

        return JsonResponse({"message": f"{inserted_count} questions inserted successfully"}, status=201)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def store_gpt_questions(request):
    try:
        data = request.data.get("questions", [])

        if not data or not isinstance(data, list):
            return JsonResponse({"error": "Invalid or empty questions list"}, status=400)

        saved = []
        for q in data:
            question = GPTQuestions.objects.create(
                question_text=q.get("question_text"),
                options=q.get("options", []),
                answer=q.get("answer"),
                marks=q.get("marks", 1),
                subject=q.get("subject"),
                chapter=q.get("chapter"),
                topic=q.get("topic"),
                difficulty=q.get("difficulty", "medium")
            )
            saved.append(str(question.id))

        return JsonResponse({"status": "success", "saved_ids": saved})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_modified_questions(request):
    questions = request.data.get("questions", [])

    if not questions:
        return Response({"error": "No questions provided"}, status=400)

    inserted_count = 0
    for q in questions:
        if not all([q.get("question_text"), q.get("marks"), q.get("subject"), q.get("difficulty")]):
            continue

        bloom_level = q.get("bloom_level") or classify_bloom_level(q.get("question_text", ""))

        doc = {
            "question_text": q["question_text"],
            "marks": q["marks"],
            "subject": q["subject"],
            "difficulty": q["difficulty"],
            "topic": q.get("topic"),
            "chapter": q.get("chapter"),
            "bloom_level": bloom_level,
            "learning_outcome": q.get("learning_outcome"),
            "used_in_paper": False,
            "source": q.get("source", "cohere")  
        }

        if q.get("options"):
            doc["options"] = q["options"]
            doc["answer"] = q.get("answer")

        collection.insert_one(doc)
        inserted_count += 1

    return Response({"message": f"{inserted_count} questions saved successfully!"}, status=201)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_levels_from_file(request):
    filename = request.GET.get("filename")
    filetype = request.GET.get("filetype", "pdf")
    level = request.GET.get("level", "module").lower()

    if not filename or not level:
        return JsonResponse({"error": "Filename and level are required."}, status=400)

    # Choose correct collection
    target_collection = pdf_collection if filetype == "pdf" else docx_collection
    record = target_collection.find_one({"filename": filename})

    if not record:
        return JsonResponse({"error": f"{filetype.upper()} file not found"}, status=404)

    text = record.get("extracted_text", "")
    lines = text.splitlines()

    # Match patterns like:
    # Module-1, MODULE – 2, Unit 3, UNIT-4, Chapter: 5, etc.
    pattern = re.compile(rf"{level}\s*[-–: ]?\s*\d+", re.IGNORECASE)

    matches = set()
    for line in lines:
        if pattern.search(line.strip()):
            matches.add(line.strip())

    return JsonResponse({"options": sorted(matches)}, status=200)
from .utils import sanitize
from .pdf_generator import generate_styled_exam_pdf


def clean_marks_suffix(text):
    return re.sub(r"\s*\(\d+\s*mark[s]?\)\s*$", "", text.strip(), flags=re.IGNORECASE)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_questions_from_file(request):
    filename = request.data.get("filename")
    filetype = request.data.get("filetype", "pdf")
    subject = request.data.get("subject")
    difficulty = request.data.get("difficulty", "medium")
    course_code = request.data.get("course_code", "BCA6DSC99")
    qp_code = request.data.get("qp_code", "9999")

    if not subject or not filename:
        return Response({"error": "Filename and subject are required."}, status=400)

    collection_source = pdf_collection if filetype == "pdf" else docx_collection
    record = collection_source.find_one({"filename": filename})

    if not record or "extracted_text" not in record:
        return Response({"error": f"{filetype.upper()} file not found or missing text."}, status=404)

    text = record["extracted_text"][:6000]

    def parse_questions(raw_text, marks_value):
        all_qs = split_and_clean_questions(raw_text, marks_value, subject, "auto-generated", difficulty)
        cleaned = []
        for q in all_qs:
            q_text = clean_marks_suffix(q["question_text"])
            if "####" not in q_text and not q_text.lower().startswith("question"):
                q["question_text"] = q_text
                cleaned.append(q)
        return cleaned

    required = {2: 12, 5: 8, 10: 3}
    grouped = {2: [], 5: [], 10: []}

    for mark, count in required.items():
        prompt = f"Generate {count} {mark}-mark questions on '{subject}' based on the following content:\n\n{text}"
        raw = call_chatgpt(prompt, role="examiner")
        parsed = parse_questions(raw, mark)
        grouped[mark].extend(parsed[:count])

    missing = {k: required[k] - len(grouped[k]) for k in required if len(grouped[k]) < required[k]}
    if missing:
        return Response({"error": f"Missing required number of questions: {missing}"}, status=500)

    final_qs = grouped[2][:12] + grouped[5][:8] + grouped[10][:3]
    for q in final_qs:
        collection.insert_one(q)
        q["_id"] = str(q["_id"])

    pdf_url = generate_pdf_bmscw(subject_title=subject, course_code=course_code, qp_code=qp_code,
                                 qs_2m=grouped[2][:12], qs_5m=grouped[5][:8], qs_10m=grouped[10][:3])

    return Response({"questions": final_qs, "pdf_url": pdf_url})



from .pdf_generator import safe_unicode
import logging

logger = logging.getLogger(__name__)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_mcq_from_file(request):
    filename = request.data.get("filename")
    filetype = request.data.get("filetype", "pdf")
    subject = request.data.get("subject")
    num_questions = int(request.data.get("num_questions", 10))
    difficulty = request.data.get("difficulty", "medium")

    collection_source = pdf_collection if filetype == "pdf" else docx_collection
    record = collection_source.find_one({"filename": filename})

    if not record or "extracted_text" not in record:
        return Response({"error": f"{filetype.upper()} file not found or missing text."}, status=404)

    # Trim non-academic parts if needed
    text = record["extracted_text"]
    if "Unit" in text:
        text = text[text.index("Unit"):]

    text = text[:6000]  # Trim for model input limit

    raw_prompt = (
        f"You are an exam setter. Based on the following syllabus text, generate exactly {num_questions} multiple-choice questions (MCQs).\n\n"
        f"Syllabus:\n{text}\n\n"
        "Instructions:\n"
        "- Each MCQ must have a clear and concise question.\n"
        "- Provide exactly four options labeled A, B, C, and D.\n"
        "- Do not include answers.\n"
        "- Separate each MCQ clearly.\n\n"
        "Format:\n"
        "Question: ...\n"
        "A. ...\n"
        "B. ...\n"
        "C. ...\n"
        "D. ...\n\n"
        f"Ensure you return exactly {num_questions} complete MCQs following the format."
    )

    raw = call_chatgpt(raw_prompt, role="mcq")
    parsed_mcqs = parse_mcq_blocks(raw)

    parsed_mcqs = [
        q for q in parsed_mcqs
        if isinstance(q, dict)
        and "question_text" in q
        and isinstance(q["question_text"], str)
        and "####" not in q["question_text"]
        and not q["question_text"].lower().startswith("question")
        and "options" in q
        and isinstance(q["options"], list)
        and len(q["options"]) == 4
    ][:num_questions]

    if not parsed_mcqs:
        return Response({"error": "No valid MCQs parsed."}, status=500)

    cleaned_output = []
    for q in parsed_mcqs:
        q_text = safe_unicode(q["question_text"])
        options = [safe_unicode(opt) for opt in q["options"]]

        GPTQuestions.objects.create(
            question_text=q_text,
            options=options,
            marks=1,
            difficulty=difficulty,
            used_in_paper=False,
            subject=subject,
            final_selection=True,
            source="mistral-local"
        )

        cleaned_output.append({
            "question": q_text,
            "options": options
        })

    try:
        pdf_url = generate_mcq_pdf({"questions": cleaned_output})
    except Exception as e:
        return Response({"error": f"PDF generation failed: {str(e)}"}, status=500)

    return Response({"questions": cleaned_output, "pdf_url": str(pdf_url)})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_mcq_questions(request):
    mcqs = request.data.get("questions", [])

    if not mcqs:
        return Response({"error": "No MCQs provided"}, status=400)

    inserted_count = 0
    for q in mcqs:
        if not all([q.get("question_text"), q.get("options"), q.get("subject")]):
            continue

        doc = {
            "question_text": q["question_text"],
            "options": q["options"],
            "answer": q.get("answer"),
            "subject": q["subject"],
            "difficulty": q.get("difficulty", "medium"),
            "topic": q.get("topic"),
            "chapter": q.get("chapter"),
            "bloom_level": q.get("bloom_level") or classify_bloom_level(q.get("question_text", "")),
            "used_in_paper": False,
            "source": q.get("source", "mistral-local")  #  updated
        }

        collection.insert_one(doc)
        inserted_count += 1

    return Response({"message": f"{inserted_count} MCQs saved successfully!"}, status=201)

def classify_bloom_level(question_text):
    text = question_text.lower()

    if any(w in text for w in ['define', 'list', 'name', 'identify', 'state']):
        return 'Remember'
    elif any(w in text for w in ['explain', 'describe', 'summarize', 'classify']):
        return 'Understand'
    elif any(w in text for w in ['apply', 'solve', 'use', 'demonstrate']):
        return 'Apply'
    elif any(w in text for w in ['analyze', 'compare', 'contrast', 'differentiate']):
        return 'Analyze'
    elif any(w in text for w in ['evaluate', 'justify', 'assess', 'argue']):
        return 'Evaluate'
    elif any(w in text for w in ['design', 'create', 'develop', 'formulate']):
        return 'Create'
    return 'Uncategorized'

def parse_mcq_response(text):
    mcqs = []
    blocks = text.strip().split("\n\n")
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) >= 5:
            question = lines[0]
            options = lines[1:5]
            answer = None
            for line in lines[5:]:
                if line.lower().startswith("answer"):
                    answer = line.split(":")[-1].strip()
            mcqs.append({
                "question_text": question,
                "options": options,
                "answer": answer
            })
    return mcqs

SUBJECT_CORRECTIONS = {
    "maths": "Mathematics",
    "math": "Mathematics",
    "eng": "English",
    "cs": "Computer Science",
    "ca": "Computer Applications",
    "ai": "Artificial Intelligence",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "cv": "Computer Vision",
    "iot": "Internet of Things",
    "dsa": "Data Structures and Algorithms",
    "os": "Operating Systems",
    "dbms": "Database Management Systems",
    "rdbms": "Relational Database Management Systems",
    "se": "Software Engineering",
    "cn": "Computer Networks",
    "oop": "Object Oriented Programming",
    "oops": "Object Oriented Programming",
    "java": "Java Programming",
    "python": "Python Programming",
    "c": "C Programming",
    "c++": "C++ Programming",
    "wt": "Web Technologies",
    "wtl": "Web Technology Lab",
    "html": "HTML and Web Design",
    "css": "CSS and Styling",
    "js": "JavaScript",
    "php": "PHP Programming",
    "net": ".NET Framework",
    "ds": "Data Science",
    "bda": "Big Data Analytics",
    "daa": "Design and Analysis of Algorithms",
    "fl": "Formal Languages and Automata",
    "coa": "Computer Organization and Architecture",
    "toc": "Theory of Computation",
    "daa": "Design and Analysis of Algorithms",
    "is": "Information Security",
    "cyber": "Cybersecurity",
    "cloud": "Cloud Computing",
    "blockchain": "Blockchain Technology",
    "ui": "User Interface Design",
    "ux": "User Experience",
    "android": "Android Application Development",
    "mobile": "Mobile Application Development",
    "dm": "Discrete Mathematics",
    "am": "Applied Mathematics",
    "stat": "Statistics",
    "eco": "Economics",
    "acct": "Accounting",
    "bce": "Business Communication in English",
    "it": "Information Technology"
}


def format_subject(subject):
    subject = subject.strip().lower()
    return SUBJECT_CORRECTIONS.get(subject, subject.title())  # default title case if not found

def format_semester(sem):
    sem = sem.strip().upper()
    if 'V' in sem and 'I' not in sem:
        return 'V Semester'
    elif 'VI' in sem:
        return 'VI Semester'
    elif 'IV' in sem:
        return 'IV Semester'
    elif 'III' in sem:
        return 'III Semester'
    elif 'II' in sem:
        return 'II Semester'
    elif 'I' in sem:
        return 'I Semester'
    return sem

def format_duration(duration):
    duration = duration.strip()
    if duration in ["2.5", "2.5 hours", "2 1/2", "2½"]:
        return "2 1/2 Hrs"
    elif duration in ["3", "3 hours"]:
        return "3 Hrs"
    elif duration in ["1.5", "1 1/2", "1½"]:
        return "1 1/2 Hrs"
    return duration.title()


def format_exam_month_year(month_year):
    month_year = month_year.strip().lower()
    if 'jan' in month_year:
        return month_year.replace('jan', 'Jan/Feb').capitalize()
    return month_year.capitalize()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_custom_exam_paper(request):
    """
    Build a full paper (Parts I-III) by randomly sampling unused
    2-, 5- and 10-mark questions from Mongo, deduplicating and sanitising
    them, then piping everything to pdf_generator.generate_pdf_custom().
    """
    try:
        # ---------- 1. read POST body ----------
        course_name      = request.data.get('course_name', '').strip()
        subject_name     = request.data.get('subject_name', '').strip()
        semester         = request.data.get('semester', '').strip()
        exam_month_year  = request.data.get('exam_month_year', '').strip()
        duration         = request.data.get('duration', '').strip()
        total_marks      = int(request.data.get('total_marks', 60))
        num_2marks       = int(request.data.get('num_2marks', 10))
        num_5marks       = int(request.data.get('num_5marks', 6))
        num_10marks      = int(request.data.get('num_10marks', 1))

        # ---------- 2. beautify heading ----------
        heading = (
            f"{course_name} - {format_subject(subject_name)}\n"
            f"{format_semester(semester)} END EXAMINATION – "
            f"{format_exam_month_year(exam_month_year)}\n\n"
            f"Duration: {format_duration(duration)}           "
            f"Max. Marks: {total_marks}"
        )

        # ---------- 3. pull from Mongo ----------
        def grab(mark, n):
            return list(collection.aggregate([
                {"$match": {"marks": mark, "used_in_paper": {"$ne": True}}},
                {"$sample": {"size": n}}
            ]))

        questions_2m  = unique_by_text(grab(2,  num_2marks))
        questions_5m  = unique_by_text(grab(5,  num_5marks))
        questions_10m = unique_by_text(grab(10, num_10marks))

        # ---------- 4. PDF ----------
        pdf_path = generate_pdf_custom(
            heading,
            questions_2m,
            questions_5m,
            questions_10m
        )
        

        # ---------- 5. flag as used ----------
        used_ids = [q['_id'] for q in (questions_2m + questions_5m + questions_10m)]
        if used_ids:
            collection.update_many({'_id': {'$in': used_ids}}, {'$set': {'used_in_paper': True}})

        return Response(
            {'message': 'Custom exam paper generated successfully!', 'pdf_file': pdf_path},
            status=201
        )

    except Exception as exc:
        return Response({'error': str(exc)}, status=500)
 
def generate_pdf_parts(questions):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - 60, "B.C.A - Machine Learning")
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 80, "VI Semester END EXAMINATION – Jan/Feb 2025")
    c.drawCentredString(width / 2, height - 100, "Duration: 2 1/2 Hrs                Max. Marks: 60")

    y = height - 140
    c.setFont("Helvetica-Bold", 12)

    # PART I - 2 Mark Questions
    c.drawString(50, y, "PART - I: Answer any TEN questions. (10 x 2 = 20 Marks)")
    y -= 20
    count = 1
    for q in questions:
        if q['marks'] == 2:
            lines = split_text(f"{count}. {q['question_text']}", max_chars=100)
            for line in lines:
                c.drawString(50, y, line)
                y -= 20
                if y < 80:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = height - 50
            count += 1
    y -= 20

    # PART II - 5 Mark Questions
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "PART - II: Answer any SIX questions. (6 x 5 = 30 Marks)")
    y -= 20
    count = 1
    for q in questions:
        if q['marks'] == 5:
            lines = split_text(f"{count}. {q['question_text']}", max_chars=100)
            for line in lines:
                c.drawString(50, y, line)
                y -= 20
                if y < 80:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = height - 50
            count += 1
    y -= 20

    # PART III - 10 Mark Question
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "PART - III: Answer any ONE question. (1 x 10 = 10 Marks)")
    y -= 20
    count = 1
    for q in questions:
        if q['marks'] == 10:
            lines = split_text(f"{count}. {q['question_text']}", max_chars=100)
            for line in lines:
                c.drawString(50, y, line)
                y -= 20
                if y < 80:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = height - 50
            count += 1

    c.save()
    buffer.seek(0)

    # Save to disk (media folder)
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ExamPaper_{now}.pdf"
    filepath = os.path.join("media", "exam_papers", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        f.write(buffer.read())

    return f"/media/exam_papers/{filename}"

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

# 1. Save selected + edited questions for final PDF generation
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_final_questions_for_pdf(request):
    final_questions = request.data.get("questions", [])
    if not final_questions:
        return Response({"error": "No questions provided."}, status=400)

    saved_ids = []
    for q in final_questions:
        if not all([q.get("question_text"), q.get("marks"), q.get("subject")]):
            continue
        doc = {
            "question_text": q["question_text"],
            "marks": int(q["marks"]),
            "subject": q["subject"],
            "difficulty": q.get("difficulty", "medium"),
            "topic": q.get("topic"),
            "chapter": q.get("chapter"),
            "bloom_level": q.get("bloom_level") or classify_bloom_level(q["question_text"]),
            "learning_outcome": q.get("learning_outcome"),
            "used_in_paper": False,
            "source": q.get("source", "manual"),
            "final_selection": True
        }
        inserted = collection.insert_one(doc)
        saved_ids.append(str(inserted.inserted_id))

    return Response({"message": f"{len(saved_ids)} final questions saved.", "saved_ids": saved_ids}, status=201)

# 2. Generate PDF from only final-selected questions
# views.py
from .utils import sanitize, unique_by_text

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_pdf_from_final_selection(request):
    """
    Lay out a PDF from the questions previously marked final_selection=True.
    Text is sanitized and duplicates stripped.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from io import BytesIO
    import os
    from datetime import datetime

    # ---------- 1. user header ----------
    heading  = request.data.get("heading", "END SEMESTER EXAMINATION")
    duration = request.data.get("duration", "3 Hrs")
    max_marks= request.data.get("max_marks", 60)

    # ---------- 2. pull selection ----------
    docs = list(collection.find({
        "final_selection": True,
        "used_in_paper":  {"$ne": True}
    }))

    if not docs:
        return Response({"error": "No selected questions found."}, status=404)

    # dedup on the way out
    docs = unique_by_text(docs)

    # ---------- 3. split by marks ----------
    part1 = [d for d in docs if d['marks'] == 2][:10]
    part2 = [d for d in docs if d['marks'] == 5][:6]
    part3 = [d for d in docs if d['marks'] == 10][:1]

    # mark "used"
    ids = [d['_id'] for d in (part1 + part2 + part3)]
    if ids:
        collection.update_many({'_id': {'$in': ids}}, {'$set': {'used_in_paper': True}})

    # ---------- 4. PDF ----------
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4

    # heading
    c.setFont("Helvetica-Bold", 14)
    for i, line in enumerate(heading.splitlines()):
        c.drawCentredString(W / 2, H - 60 - i*20, line)
    c.setFont("Helvetica", 12)
    c.drawCentredString(W / 2, H - 100, f"Duration: {duration}            Max. Marks: {max_marks}")

    y = H - 140
    c.setFont("Helvetica-Bold", 12)

    # helper
    def block(title, items, start_no):
        nonlocal y
        c.drawString(50, y, title)
        y -= 20
        c.setFont("Helvetica", 11)
        qno = start_no
        for d in items:
            txt = sanitize(d["question_text"])
            if y < 80:
                c.showPage()
                y = H - 60
                c.setFont("Helvetica", 11)
            c.drawString(60, y, f"{qno}. {txt}")
            y -= 20
            qno += 1
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        return qno

    next_no = block("PART – I: Answer any TEN questions. (10 × 2 = 20 Marks)", part1, 1)
    next_no = block("PART – II: Answer any SIX questions. (6 × 5 = 30 Marks)",  part2, next_no)
    block    ("PART – III: Answer any ONE question. (1 × 10 = 10 Marks)",     part3, next_no)

    c.save()
    buffer.seek(0)

    # ---------- 5. persist ----------
    now  = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"FinalExamPaper_{now}.pdf"
    folder = os.path.join("media", "exam_papers")
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, name)
    with open(file_path, "wb") as f:
        f.write(buffer.read())

    return Response({
        "message": "Custom final exam PDF generated successfully.",
        "pdf_file": f"/media/exam_papers/{name}"
    }, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_bmscw_paper(request):
    """
    Accepts JSON like:
    {
      "subject_title": "MOBILE APPLICATION DEVELOPMENT",
      "course_code":   "BCA6DSC17",
      "qp_code":       "6046",
      "duration":      "2 ½ Hours",
      "max_marks":     60,
      "exam_sem_line": "VI SEMESTER END EXAMINATION – MAY-2025",
      "num_2": 10,
      "num_5": 6,
      "num_10": 1
    }
    """
    # ---------- user-provided header fields ----------
    subj        = request.data.get("subject_title",  "SUBJECT NAME")
    course_code = request.data.get("course_code",    "")
    qp_code     = request.data.get("qp_code",        "")
    duration    = request.data.get("duration",       "3 Hours")
    max_marks   = int(request.data.get("max_marks",  60))
    sem_line    = request.data.get("exam_sem_line",
                                   "VI SEMESTER END EXAMINATION – 2025")

    # ---------- how many questions ----------
    n2  = int(request.data.get("num_2",  10))
    n5  = int(request.data.get("num_5",   6))
    n10 = int(request.data.get("num_10",  1))

    qs2  = unique_by_text(list(collection.aggregate([{"$match":{"marks":2}},  {"$sample":{"size":n2}}])))
    qs5  = unique_by_text(list(collection.aggregate([{"$match":{"marks":5}},  {"$sample":{"size":n5}}])))
    qs10 = unique_by_text(list(collection.aggregate([{"$match":{"marks":10}}, {"$sample":{"size":n10}}])))

    pdf_url = generate_pdf_bmscw(
        subject_title = subj,
        course_code   = course_code,
        qp_code       = qp_code,
        duration      = duration,
        max_marks     = max_marks,
        exam_sem_line = sem_line,
        qs_2m         = qs2,
        qs_5m         = qs5,
        qs_10m        = qs10
    )
    return Response({"pdf_file": pdf_url}, status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def preview_paper(request):
    """
    Body:
    {
      "subject_title": "MOBILE APPLICATION DEVELOPMENT",
      "course_code":   "BCA6DSC17",
      "qp_code":       "6046",
      "duration":      "2 ½ Hours",
      "max_marks":     60,
      "questions": [ { "question_text":"...", "marks":2 }, … ],
      "save": true     // optional
    }
    """
    header  = request.data
    qlist   = header["questions"]

    # split by marks
    qs2  = [q for q in qlist if q.get("marks",2)  == 2][:10]
    qs5  = [q for q in qlist if q.get("marks",5)  == 5][:6]
    qs10 = [q for q in qlist if q.get("marks",10) == 10][:1]

    pdf_url = generate_pdf_bmscw(
        subject_title = header["subject_title"],
        course_code   = header["course_code"],
        qp_code       = header["qp_code"],
        duration      = header["duration"],
        max_marks     = int(header["max_marks"]),
        qs_2m = qs2, qs_5m = qs5, qs_10m = qs10
    )

    # ⬇ persist if requested
    if header.get("save"):
        PrintedPaper.objects.create(
            user          = request.user,
            subject_title = header["subject_title"],
            course_code   = header["course_code"],
            qp_code       = header["qp_code"],
            duration      = header["duration"],
            max_marks     = int(header["max_marks"]),
            pdf_url       = pdf_url,
            questions     = qlist
        )

    # ⬇ e-mail link to user
    absolute_link = request.build_absolute_uri(pdf_url)
    send_mail(
        subject       = "Your exam paper is ready",
        message       = (
            f"Hi {request.user.get_full_name() or request.user.username},\n\n"
            f"Download your paper here:\n{absolute_link}\n\nRegards,\nExam-Setter Bot"
        ),
        from_email    = settings.DEFAULT_FROM_EMAIL,
        recipient_list= [request.user.email],
        fail_silently = True
    )

    return Response({"preview_pdf": pdf_url}, status=201)


from .pdf_generator import generate_styled_exam_pdf
def _finalize_and_respond(cleaned_questions, subject, course_code, qp_code, duration, max_marks, source="mistral-local"):
    from .models import Question
    import re

    def clean_text(q):
        text = re.sub(r"\\.?\\*", "", q["question_text"])
        return re.sub(r"\n+", " ", text).strip()

    final_questions = []
    for q in cleaned_questions:
        if not q["question_text"].strip().lower().endswith("questions:"):
            final_questions.append({
                "question_text": clean_text(q),
                "marks": q["marks"],
                "subject": subject,
                "final_selection": True,
                "used_in_paper": False,
                "source": source  #  updated default
            })

    Question.objects.insert_many(final_questions)

def clear_previous_final_selection(user_id):
    collection.update_many(
        {"final_selection": True, "user_id": str(user_id)},
        {"$unset": {"final_selection": ""}}
    )
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_pdf_from_final_selection(request):
    """
    Generate PDF from questions marked as final_selection=True.
    Skips section headers and only includes valid questions.
    """
    try:
        collection = db["questions"]
        docs = list(collection.find({
            "final_selection": True,
            "used_in_paper": {"$ne": True}
        }))

        # Filter out header texts like "2 Mark Questions:", etc.
        skip_headers = ["2 mark questions:", "5 mark questions:", "10 mark questions:"]
        cleaned_docs = [d for d in docs if d["question_text"].strip().lower() not in skip_headers]

        # Separate by marks
       # Updated mark-wise distribution
        part1 = [d for d in cleaned_docs if d['marks'] == 2][:12]
        part2 = [d for d in cleaned_docs if d['marks'] == 5][:8]
        part3 = [d for d in cleaned_docs if d['marks'] == 10][:3]


        # Combine and mark as used
        selected_questions = part1 + part2 + part3
        ids = [q["_id"] for q in selected_questions]
        collection.update_many({"_id": {"$in": ids}}, {"$set": {"used_in_paper": True}})

        # Generate PDF
        pdf_path = generate_pdf(part1, part2, part3)

        return Response({
            "pdf_url": pdf_path,
            "questions": selected_questions
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_bmscw_pdf(request):
    subject_title = request.GET.get("subject_title", "Operating Systems")
    course_code   = request.GET.get("course_code", "BCA6DSC17")
    qp_code       = request.GET.get("qp_code", "6046")

    questions = list(collection.find({"used_in_paper": True, "final_selection": True}))

    qs_2m  = [q for q in questions if q["marks"] == 2]
    qs_5m  = [q for q in questions if q["marks"] == 5]
    qs_10m = [q for q in questions if q["marks"] == 10]

    pdf_url = generate_pdf_bmscw(subject_title, course_code, qp_code, qs_2m, qs_5m, qs_10m)
    return Response({"pdf_url": pdf_url})

from django.http import JsonResponse
from django.conf import settings
import os
from datetime import datetime
 # Assuming you have a PDF generator function

def generate_pdf_view(request):
    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"StyledExam_{timestamp}.pdf"
    relative_path = f"exam_papers/{filename}"
    absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)

    # Your custom logic to generate the PDF and save it
    generate_pdf(absolute_path)  # e.g., using ReportLab, WeasyPrint, etc.

    # Return relative media URL so frontend can use it
    file_url = f"/media/{relative_path}"
    return JsonResponse({"pdf_url": file_url})
