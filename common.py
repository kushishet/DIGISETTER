from pymongo import MongoClient
from .utils import sanitize
import json
import re

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["exam_paper_db"]
collection = db["questions"]
pdf_collection = db["pdfs"]
docx_collection = db["docx_files"]

# Bloom level classifier
def classify_bloom_level(question_text):
    if any(keyword in question_text.lower() for keyword in ["define", "list", "name"]):
        return "Remember"
    elif any(keyword in question_text.lower() for keyword in ["explain", "describe", "summarize"]):
        return "Understand"
    elif any(keyword in question_text.lower() for keyword in ["apply", "solve", "use"]):
        return "Apply"
    elif any(keyword in question_text.lower() for keyword in ["analyze", "compare", "contrast"]):
        return "Analyze"
    elif any(keyword in question_text.lower() for keyword in ["evaluate", "justify"]):
        return "Evaluate"
    elif any(keyword in question_text.lower() for keyword in ["create", "design", "develop"]):
        return "Create"
    else:
        return "Understand"

# Parse MCQ responses
def parse_mcq_response(response_text):
    try:
        data = json.loads(response_text)
        return data if isinstance(data, list) else []
    except Exception:
        return []

def clean_and_parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    try:
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            raise ValueError("No JSON array found in text.")
    except Exception as e:
        raise ValueError(f"Failed to parse MCQ JSON: {e}")

def clean_question_text(text):
    return re.sub(r'^\d+(\.\d+)\s', '', text.strip())

def parse_clean_questions(raw_text, default_marks=5):
    blocks = [b.strip() for b in raw_text.strip().split("\n\n") if b.strip()]
    questions = []
    for block in blocks:
        qtext = re.sub(r"(?i)[#>\-]+|question[:\-\s]|answer[:\-\s]|bloom.|difficulty.*", "", block)
        qtext = re.sub(r"\n", " ", qtext).strip()
        qtext = clean_question_text(qtext)
        if qtext:
            questions.append({
                "question_text": sanitize(qtext),
                "marks": default_marks,
                "used_in_paper": False,
                "source": "mistral-local"
            })
    return questions
import re
import re

def parse_mcq_blocks(raw_text):
    blocks = raw_text.strip().split("\n\n")
    parsed = []

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 5:
            continue

        # Detect question line and next 4 options
        q_line = lines[0]
        options = lines[1:5]

        if not q_line or not all(re.match(r"^[A-Da-d][).]?\s", opt) for opt in options):
            continue

        # Clean options
        clean_opts = [re.sub(r"^[A-Da-d][).]?\s*", "", opt).strip() for opt in options]

        parsed.append({
            "question_text": re.sub(r"^\d+[).]?\s*", "", q_line).strip(),
            "options": clean_opts
        })

    return parsed