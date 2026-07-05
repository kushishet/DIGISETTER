import re
import unicodedata
import string
from fpdf import FPDF
import os
from datetime import datetime


DEFAULT_SOURCE = "mistral-local"

PREFIX_PAT = re.compile(r"^\s*(?:Q\d+[\.\)]|\d+[\.\)]|[\u2022\-])\s", re.IGNORECASE)
ANS_TAIL = re.compile(r"\s*(?:Answer|Ans|Explanation|Solution|Answer Key)\s*[:\-–].*", re.IGNORECASE)
PAREN_PAT = re.compile(r"\(\s*[a-dA-D]\s*\)")
BULLET_PAT = re.compile(r"[*\u2022\-→]+")


def sanitize(text: str) -> str:
    text = PREFIX_PAT.sub('', text)
    text = PAREN_PAT.sub('', text)
    text = BULLET_PAT.sub(' ', text)
    text = ANS_TAIL.sub('', text)
    return ' '.join(text.split())


PUNCT = str.maketrans('', '', string.punctuation)

def _plain(s: str) -> str:
    base = ''.join(c for c in unicodedata.normalize('NFKD', s)
                   if not unicodedata.combining(c))
    return base.translate(PUNCT).lower()

def unique_by_text(docs):
    seen, out = set(), []
    for d in docs:
        key = _plain(sanitize(d.get('question_text', '')))[:120]
        if key not in seen:
            seen.add(key)
            out.append(d)
    return out

def make_json_safe(doc):
    if isinstance(doc, list):
        for d in doc:
            if '_id' in d:
                d['_id'] = str(d['_id'])
    elif isinstance(doc, dict) and '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return doc

def split_and_clean_questions(block, marks, subject="General", topic=None, difficulty="medium"):
    lines = block.strip().split('\n')
    result = []
    for line in lines:
        if line.strip() and not line.strip().lower().startswith(('bloom', 'difficulty', '')):
            result.append({
                'question_text': sanitize(line.strip()),
                'marks': marks,
                'subject': subject,
                'topic': topic,
                'difficulty': difficulty,
                'used_in_paper': False,
                'final_selection': True,
                'source': DEFAULT_SOURCE
            })
    return result

def extract_clean_questions(raw_text):
    junk_phrases = [
        "here are", "2 mark questions", "5 mark questions",
        "10 mark questions", "additional", "note:",
        "exam style questions"
    ]

    questions = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(phrase in line.lower() for phrase in junk_phrases):
            continue
        if re.match(r"^\d+[.)]?\s*", line) or line.endswith("?"):
            questions.append(line)
    return questions

def is_valid_question(text):
    if not isinstance(text, str):
        return False
    junk_phrases = [
        "here are", "2 mark questions", "5 mark questions", "10 mark questions",
        "additional", "note:", "exam style questions"
    ]
    return not any(phrase in text.lower() for phrase in junk_phrases)

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
    return (
        text.replace("-", "-")
            .replace("—", "-")
            .replace("“", '"')
            .replace("”", '"')
            .replace("'", "'")
            .replace("'", "'")
    )