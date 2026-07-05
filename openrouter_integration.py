from .llm_client import call_chatgpt
from .utils import sanitize
from .common import parse_mcq_blocks
import re
import json
from datetime import datetime



def generate_exam_questions(subject, marks, difficulty, prompt):
    user_prompt = (
        f"Generate a {marks}-mark exam-style question in the subject '{subject}' "
        f"based on the topic: {prompt}.\n"
        "If the mark is 5 or 10, include subparts like (a), (b), etc.\n"
        "Exclude explanations and answers."
    )

    raw_text = call_chatgpt(user_prompt, role="examiner")
    if not raw_text.strip():
        return [{"error": "LLM returned no content"}]

    question_blocks = raw_text.strip().split("\n\n")
    questions = []

    for block in question_blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue

        q_text = []
        sub_qs = []

        for line in lines:
            match = re.match(r"^\(?([a-dA-D])[\.\)]\s*(.+)", line.strip())
            if match:
                sub_qs.append({"label": match.group(1), "text": sanitize(match.group(2))})
            else:
                q_text.append(line.strip())

        full_question = sanitize(" ".join(q_text))
        questions.append({
            "question_text": full_question,
            "sub_questions": sub_qs if sub_qs else None,
            "marks": marks,
            "difficulty": difficulty,
            "topic": prompt,
            "subject": subject,
            "source": "mistral-local"
        })

    return questions


def clean_question_text(text):
    return re.sub(r'^\d+[\.\)]\s*', '', text.strip())


def generate_mcqs_from_text(text, subject, marks_distribution=None, difficulty=None):
    prompt = (
        f"Generate 5 multiple choice questions for the subject '{subject}' on the topic '{text}'.\n"
        "Each question must be followed by exactly four options labeled A, B, C, D.\n"
        "Do not include answers, explanations, or numbering beyond what's needed for the MCQs."
    )

    try:
        raw_text = call_chatgpt(prompt, role="mcq")
        if not raw_text.strip():
            return [{"error": "LLM returned no content"}]

        parsed_mcqs = parse_mcq_blocks(raw_text)

        cleaned = []
        for q in parsed_mcqs:
            options = [sanitize(opt) for opt in q["options"]]
            if all(not opt[:2].upper().startswith(("A.", "B.", "C.", "D.")) for opt in options):
                options = [f"{label}. {opt}" for label, opt in zip("ABCD", options)]

            cleaned.append({
                "question_text": sanitize(q["question_text"]),
                "options": options,
                "marks": 1,
                "used_in_paper": False,
                "source": "mistral-local",
                "subject": subject,
                "difficulty": difficulty or "medium"
            })

        return cleaned

    except Exception as e:
        return [{"error": str(e)}]


def generate_exam_questions_text_response(subject, syllabus_text):
    prompt = (
        f"Subject: {subject}\n"
        f"Syllabus: {syllabus_text}\n"
        "Generate exam-style questions. Use this format:\n"
        "Q1. Main question text\n"
        "(a) Sub-question 1\n"
        "(b) Sub-question 2\n"
        "\nQ2. Another question or sub-parts...\n"
        "Do NOT include answers or explanations."
    )

    raw = call_chatgpt(prompt, role="examiner")
    if not raw.strip():
        return [{"error": "LLM returned no content"}]

    question_blocks = re.split(r"\n{2,}", raw.strip())
    questions = []

    for block in question_blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue

        q_match = re.match(r"^(Q\d+[\.\)]?)\s*(.*)", lines[0])
        if q_match:
            main_text = q_match.group(2).strip()
            sub_questions = []
            for line in lines[1:]:
                sub_match = re.match(r"^\(?([a-dA-D])\)?[\.\)]?\s+(.*)", line.strip())
                if sub_match:
                    sub_questions.append({
                        "label": sub_match.group(1),
                        "text": sanitize(sub_match.group(2))
                    })
            questions.append({
                "question_text": sanitize(main_text),
                "sub_questions": sub_questions if sub_questions else None,
                "source": "mistral-local"
            })
        else:
            questions.append({
                "question_text": sanitize(" ".join(lines)),
                "sub_questions": None,
                "source": "mistral-local"
            })

    return questions