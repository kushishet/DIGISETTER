import re
import json
import os

from bson import ObjectId
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from .utils import sanitize, is_valid_question, extract_clean_questions
from .common import collection, classify_bloom_level, parse_mcq_blocks
from .mcq_pdf_generator import generate_mcq_pdf
from .pdf_generator import generate_pdf_bmscw
from .llm_client import call_chatgpt
from .models import GPTQuestions
from datetime import datetime
from .views import clean_marks_suffix



def prefix_options(options):
    prefix = ['A. ', 'B. ', 'C. ', 'D. ']
    return [f"{p}{o}" for p, o in zip(prefix, options)]


def distribute_questions_by_marks_and_difficulty(marks_distribution=None, overall_difficulty='medium'):
    plan = []
    mark_levels = {2: "easy", 5: "medium", 10: "hard"}
    if marks_distribution:
        for mark, count in marks_distribution.items():
            difficulty = mark_levels.get(int(mark), overall_difficulty)
            plan.extend([{"marks": int(mark), "difficulty": difficulty}] * count)
    return plan

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_questions_from_prompt(request):
    subject = request.data.get("subject")
    topic = request.data.get("topic")
    difficulty = request.data.get("difficulty", "medium")
    course_code = request.data.get("course_code", "BCA6DSC99")
    qp_code = request.data.get("qp_code", "9999")

    if not subject or not topic:
        return Response({"error": "Subject and topic are required."}, status=400)

    def parse_questions(raw_text, marks_value):
        lines = raw_text.strip().splitlines()
        results = []
        for line in lines:
            line = line.strip()
            if not line or not line[0].isdigit() or '.' not in line:
                continue
            q_text = sanitize(line[line.find(".") + 1:].strip())
            q_text = clean_marks_suffix(q_text)
            if is_valid_question(q_text) and "####" not in q_text and not q_text.lower().startswith("question"):
                results.append({
                    "question_text": q_text,
                    "marks": marks_value,
                    "difficulty": difficulty,
                    "subject": subject,
                    "topic": topic,
                    "used_in_paper": False,
                    "final_selection": True,
                    "source": "mistral-local"
                })
        return results

    required = {2: 12, 5: 8, 10: 3}
    grouped = {2: [], 5: [], 10: []}

    prompt = (
        f"Generate 12 two-mark, 8 five-mark, and 3 ten-mark exam-style questions for the subject '{subject}' on the topic '{topic}'.\n"
        "Group them as follows:\n*Two Mark Questions:\n1. ...\nFive Mark Questions:\n1. ...\nTen Mark Questions:*\n1. ...\n"
        "Only return the questions. Do not include answers or metadata."
    )

    try:
        raw = call_chatgpt(prompt, role="examiner", max_tokens=4096)
        current_marks = None
        for line in raw.strip().splitlines():
            line = line.strip()
            if "**two mark" in line.lower():
                current_marks = 2
                continue
            elif "**five mark" in line.lower():
                current_marks = 5
                continue
            elif "**ten mark" in line.lower():
                current_marks = 10
                continue
            elif "" in line:
                current_marks = None
                continue

            if line and line[0].isdigit() and '.' in line and current_marks:
                q_text = sanitize(line[line.find(".") + 1:].strip())
                q_text = clean_marks_suffix(q_text)
                if is_valid_question(q_text) and "####" not in q_text and not q_text.lower().startswith("question"):
                    grouped[current_marks].append({
                        "question_text": q_text,
                        "marks": current_marks,
                        "difficulty": difficulty,
                        "subject": subject,
                        "topic": topic,
                        "used_in_paper": False,
                        "final_selection": True,
                        "source": "mistral-local"
                    })
    except Exception as e:
        return Response({"error": f"LLM call failed: {str(e)}"}, status=500)

    for mark, shortfall in {k: required[k] - len(grouped[k]) for k in required if len(grouped[k]) < required[k]}.items():
        if shortfall > 0:
            retry_prompt = (
                f"Generate {shortfall} {mark}-mark questions for the subject '{subject}' on the topic '{topic}'.\n"
                "Only return the questions."
            )
            raw_retry = call_chatgpt(retry_prompt, role="examiner")
            extra = parse_questions(raw_retry, mark)
            grouped[mark].extend(extra[:shortfall])

    final_check = {k: required[k] - len(grouped[k]) for k in required if len(grouped[k]) < required[k]}
    if final_check:
        return Response({"error": f"Missing required number of questions: {final_check}"}, status=500)

    all_qs = grouped[2][:12] + grouped[5][:8] + grouped[10][:3]
    for q in all_qs:
        collection.insert_one(q)
        q["_id"] = str(q["_id"])

    pdf_url = generate_pdf_bmscw(subject_title=subject, course_code=course_code, qp_code=qp_code,
                                 qs_2m=grouped[2][:12], qs_5m=grouped[5][:8], qs_10m=grouped[10][:3])

    return Response({"questions": all_qs, "pdf_url": pdf_url})






from .pdf_generator import safe_unicode
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_mcq(request):
    subject = request.data.get("subject")
    prompt = request.data.get("prompt")
    num_questions = int(request.data.get("num_questions", 10))
    difficulty = request.data.get("difficulty", "medium")

    raw_prompt = (
        f"Generate exactly {num_questions} multiple-choice questions (MCQs) on the topic '{prompt}' "
        f"related to the subject '{subject}'.\n\n"
        "Each MCQ must have:\n"
        "- A clear question statement\n"
        "- Exactly four options labeled A, B, C, and D\n"
        "- No answers should be included.\n\n"
        "Format each MCQ as:\n"
        "Question: ...\n"
        "A. ...\n"
        "B. ...\n"
        "C. ...\n"
        "D. ...\n\n"
        "Ensure each question block is clearly separated.\n"
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


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def regenerate_question(request):
#     question_id = request.data.get("id")
#     if not question_id:
#         return Response({"error": "Question ID is required"}, status=400)

#     question = collection.find_one({"_id": ObjectId(question_id)})
#     if not question:
#         return Response({"error": "Question not found"}, status=404)

#     subject = question.get("subject", "General")
#     topic = question.get("topic", "")
#     difficulty = question.get("difficulty", "medium")
#     marks = question.get("marks", 5)

#     try:
#         prompt = f"Generate a {difficulty} {marks}-mark exam-style question in {subject} on the topic '{topic}'. No answers or explanations."
#         q_text = call_chatgpt(prompt, role="examiner")
#         new_text = sanitize(q_text.strip())
#         collection.update_one({"_id": ObjectId(question_id)}, {"$set": {"question_text": new_text}})

#         current = list(collection.find({"used_in_paper": True}))
#         from .pdf_generator import generate_draft_pdf
#         pdf_path = generate_draft_pdf(current)

#         return Response({
#             "message": "Question regenerated.",
#             "updated_question": {"_id": str(question_id), "question_text": new_text},
#             "pdf_url": pdf_path.replace(settings.MEDIA_ROOT, settings.MEDIA_URL).replace("\\", "/")
#         })

#     except Exception as e:
#         return Response({"error": str(e)}, status=500)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def regenerate_mcqs(request):
#     subject = request.data.get("subject")
#     topic = request.data.get("topic", subject)
#     total_questions = int(request.data.get("total_questions", 5))

#     if not subject:
#         return Response({"error": "Subject is required."}, status=400)

#     try:
#         prompt = (
#             f"Generate exactly {total_questions} multiple choice questions for the subject '{subject}' "
#             f"based on the topic '{topic}'. Each must have four options (A–D), no answers or explanations."
#         )
#         raw_text = call_chatgpt(prompt, role="mcq")
#         parsed_mcqs = parse_mcq_blocks(raw_text)

#         questions = []
#         for q in parsed_mcqs:
#             if q["question_text"] and len(q["options"]) >= 4:
#                 questions.append({
#                     "question_text": sanitize(q["question_text"]),
#                     "options": q["options"],
#                     "marks": 1,
#                     "used_in_paper": False,
#                     "source": "openai"
#                 })

#         return Response({"questions": questions})

#     except Exception as e:
#         return Response({"error": str(e)}, status=500)


# def regenerate_mcqs_by_metadata(subject, total_questions=5, topic=None):
#     syllabus = topic or subject
#     prompt = (
#         f"Generate exactly {total_questions} multiple choice questions for the subject '{subject}' "
#         f"based on the topic '{syllabus}'. Format: question followed by 4 options A–D. No answers or explanations."
#     )
#     raw_text = call_chatgpt(prompt, role="mcq")
#     return parse_mcq_blocks(raw_text)


# def regenerate_question_by_metadata(subject, topic, difficulty, marks):
#     try:
#         prompt = f"Generate a {difficulty} {marks}-mark exam-style question in {subject} on the topic '{topic}'. No answers or explanations."
#         text = call_chatgpt(prompt, role="examiner")
#         return {
#             "question_text": sanitize(text.strip()),
#             "marks": marks,
#             "difficulty": difficulty,
#             "topic": topic,
#             "subject": subject,
#             "used_in_paper": False,
#             "source": "openai"
#         }
#     except Exception as e:
#         return {"error": str(e)}