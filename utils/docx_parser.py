"""
DOCX Question Bank Parser for English Self-Assessment (Phase 12).
Uses python-docx to extract questions, options (A-D), answer keys, and explanations
from Microsoft Word (.docx) documents.

Tolerates variations in Word formatting:
- Question labels: 'QUESTION 1', '1.', '1)', '[1]', '1 .', multi-line prompts
- Option labels: 'A.', 'A)', 'a.', 'a)', '(A)', inline or multi-line
- Answer keys: 'ANSWER: A', 'Answer: B', 'Key: C', 'Correct Answer: D', 'Ans: A'
- Explanations: 'EXPLANATION:', 'Explanation:', 'Pembahasan:'
- Topics: 'TOPIC:', 'Topic:', 'Subtopic:'
- Passages: 'PASSAGE:', 'Passage:', 'Reading Passage:'

Identifies errors and missing elements per question without silently discarding data.
"""

from typing import Optional, Any, BinaryIO
from pathlib import Path
import io
import re
import docx
from utils.difficulty import classify_difficulty


# Regex Patterns for Flexible Parsing
RE_TOPIC = re.compile(r"^(?:TOPIC|Topic|Subtopic|Subject)\s*[:=\-]?\s*(.*)$", re.IGNORECASE)
RE_PASSAGE_START = re.compile(r"^(?:PASSAGE|Passage|Reading Passage|Text)\s*[:=\-]?\s*(.*)$", re.IGNORECASE)

# Matches question beginnings:
# 'QUESTION 1', 'Question 1:', '1.', '1)', '[1]', '1 .', 'Question 1 -'
RE_QUESTION_HEADER = re.compile(
    r"^(?:QUESTION\s*(\d+)[:.\-]?|(\d+)\s*[.)\]]\s*(.*)|\[(\d+)\]\s*(.*))$",
    re.IGNORECASE,
)

# Matches an option line start: 'A.', 'A)', 'a.', 'a)', '(A)', 'A:'
RE_OPTION_LINE = re.compile(r"^[(\[]?([A-Da-d])[)\]\.:\s]\s*(.*)$")

# Matches multiple options on a single line: 'A. foo B. bar C. baz D. qux'
RE_INLINE_OPTIONS = re.compile(
    r"(?:^|\s+)[(\[]?([A-Da-d])[)\]\.:\s]\s*(.*?)(?=(?:\s+[(\[]?[A-Da-d][)\]\.:\s])|$)",
    re.IGNORECASE,
)

# Matches answer key lines:
RE_ANSWER = re.compile(
    r"^(?:ANSWER|Answer|ANS|Key|Kunci|Correct Answer)\s*[:=\-]?\s*([A-Da-d])\b",
    re.IGNORECASE,
)

# Matches explanation lines:
RE_EXPLANATION = re.compile(
    r"^(?:EXPLANATION|Explanation|Pembahasan|Explain|Note)\s*[:=\-]?\s*(.*)$",
    re.IGNORECASE,
)


def extract_paragraphs_from_docx(file_source: str | Path | BinaryIO | bytes) -> list[str]:
    """
    Extract text lines from a Word .docx document while filtering blank noise.
    Supports file path, BytesIO stream, or raw bytes.
    """
    if isinstance(file_source, bytes):
        doc_stream = io.BytesIO(file_source)
        doc = docx.Document(doc_stream)
    elif isinstance(file_source, (str, Path)):
        doc = docx.Document(str(file_source))
    else:
        # Assumed to be file-like stream (BytesIO or UploadedFile)
        doc = docx.Document(file_source)

    lines: list[str] = []
    for para in doc.paragraphs:
        txt = para.text.strip()
        if txt:
            lines.append(txt)

    # Also extract any text inside tables if present
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_txt = cell.text.strip()
                if cell_txt and cell_txt not in lines:
                    lines.append(cell_txt)

    return lines


def parse_docx_content(file_source: str | Path | BinaryIO | bytes) -> dict[str, Any]:
    """
    Parse a Word document into structured questions and validation logs.
    Returns:
    {
        "total_detected": int,
        "valid_count": int,
        "invalid_count": int,
        "global_topic": Optional[str],
        "questions": list[dict],
    }
    """
    try:
        lines = extract_paragraphs_from_docx(file_source)
    except Exception as e:
        return {
            "total_detected": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "global_topic": None,
            "questions": [],
            "error": f"Failed to extract document contents: {str(e)}",
        }

    global_topic: Optional[str] = None
    current_passage: Optional[str] = None
    questions_raw: list[dict[str, Any]] = []

    # Current question collector state
    current_q: Optional[dict[str, Any]] = None
    current_section: Optional[str] = None  # 'question', 'option_a', ..., 'explanation', 'passage'

    def finalize_current_question():
        nonlocal current_q
        if current_q:
            # Validate question completeness
            errors = []
            q_text = current_q.get("question_text", "").strip()
            if not q_text:
                errors.append("Question text prompt is empty.")

            opt_a = current_q.get("option_a", "").strip()
            opt_b = current_q.get("option_b", "").strip()
            opt_c = current_q.get("option_c", "").strip()
            opt_d = current_q.get("option_d", "").strip()

            missing_opts = []
            if not opt_a: missing_opts.append("A")
            if not opt_b: missing_opts.append("B")
            if not opt_c: missing_opts.append("C")
            if not opt_d: missing_opts.append("D")

            if missing_opts:
                errors.append(f"Missing option(s): {', '.join(missing_opts)} ({len(missing_opts)} of 4 missing)")

            if opt_a and opt_b and opt_c and opt_d:
                opts_set = {opt_a.lower(), opt_b.lower(), opt_c.lower(), opt_d.lower()}
                if len(opts_set) < 4:
                    errors.append("Duplicate choices detected among options A, B, C, D.")

            correct = current_q.get("correct_answer")
            if not correct:
                errors.append("Answer key missing (expected 'Answer: X').")
            elif correct.upper() not in ["A", "B", "C", "D"]:
                errors.append(f"Invalid answer key '{correct}'. Must be A, B, C, or D.")

            if not current_q.get("explanation"):
                # Missing explanation is flagged but can be tolerated with a default
                current_q["explanation"] = "No explanation provided in source document."

            current_q["is_valid"] = (len(errors) == 0)
            current_q["validation_errors"] = errors

            # Assign topic and passage if present
            if not current_q.get("topic") and global_topic:
                current_q["topic"] = global_topic
            if not current_q.get("passage_text") and current_passage:
                current_q["passage_text"] = current_passage

            # Rule-based difficulty classification (Phase 13)
            opts = [opt_a, opt_b, opt_c, opt_d]
            category = "Reading" if current_q.get("passage_text") else "Grammar"
            diff_res = classify_difficulty(
                category=category,
                question_text=q_text,
                options=opts,
                passage_text=current_q.get("passage_text", ""),
                explanation=current_q.get("explanation", ""),
            )
            current_q["suggested_difficulty"] = diff_res.suggested_difficulty
            current_q["difficulty_score"] = diff_res.difficulty_score
            current_q["reason"] = diff_res.reason
            current_q["difficulty_reason"] = diff_res.reason
            current_q["difficulty_factors"] = diff_res.factors
            current_q["final_difficulty"] = diff_res.suggested_difficulty

            questions_raw.append(current_q)
            current_q = None

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # 1. Check for Topic Header
        topic_match = RE_TOPIC.match(line_clean)
        if topic_match:
            global_topic = topic_match.group(1).strip()
            if current_q:
                current_q["topic"] = global_topic
            continue

        # 2. Check for Passage Header
        passage_match = RE_PASSAGE_START.match(line_clean)
        if passage_match:
            current_passage = passage_match.group(1).strip()
            current_section = "passage"
            continue

        # 3. Check for Question Header / Start
        q_match = RE_QUESTION_HEADER.match(line_clean)
        if q_match:
            finalize_current_question()

            # Extract number and possible prompt text on the same line
            q_num_str = q_match.group(1) or q_match.group(2) or q_match.group(4) or str(len(questions_raw) + 1)
            same_line_prompt = (q_match.group(3) or q_match.group(5) or "").strip()

            current_q = {
                "question_number": int(q_num_str) if q_num_str.isdigit() else q_num_str,
                "question_text": same_line_prompt,
                "option_a": "",
                "option_b": "",
                "option_c": "",
                "option_d": "",
                "correct_answer": None,
                "explanation": "",
                "topic": global_topic,
                "passage_text": current_passage,
            }
            current_section = "question"
            continue

        # 4. Check for Answer Key
        ans_match = RE_ANSWER.match(line_clean)
        if ans_match and current_q:
            current_q["correct_answer"] = ans_match.group(1).strip().upper()
            current_section = "answer"
            continue

        # 5. Check for Explanation
        exp_match = RE_EXPLANATION.match(line_clean)
        if exp_match and current_q:
            current_q["explanation"] = exp_match.group(1).strip()
            current_section = "explanation"
            continue

        # 6. Check for Options A, B, C, D
        opt_match = RE_OPTION_LINE.match(line_clean)
        if opt_match and current_q:
            key = opt_match.group(1).upper()
            opt_text = opt_match.group(2).strip()

            # Check if multiple options exist on this single line
            multi_matches = list(RE_INLINE_OPTIONS.finditer(line_clean))
            if len(multi_matches) >= 2:
                for m in multi_matches:
                    m_key = m.group(1).upper()
                    m_val = m.group(2).strip()
                    if m_key in ["A", "B", "C", "D"]:
                        current_q[f"option_{m_key.lower()}"] = m_val
                current_section = None
                continue
            else:
                if key in ["A", "B", "C", "D"]:
                    current_q[f"option_{key.lower()}"] = opt_text
                    current_section = f"option_{key.lower()}"
                    continue

        # 7. Multi-line Continuation Handling
        if current_q:
            if current_section == "question":
                if current_q["question_text"]:
                    current_q["question_text"] += " " + line_clean
                else:
                    current_q["question_text"] = line_clean
            elif current_section in ["option_a", "option_b", "option_c", "option_d"]:
                current_q[current_section] += " " + line_clean
            elif current_section == "explanation":
                if current_q["explanation"]:
                    current_q["explanation"] += "\n" + line_clean
                else:
                    current_q["explanation"] = line_clean
            elif current_section == "passage" and current_passage:
                current_passage += "\n" + line_clean

    # Finalize last question in document
    finalize_current_question()

    valid_questions = [q for q in questions_raw if q["is_valid"]]
    invalid_questions = [q for q in questions_raw if not q["is_valid"]]

    return {
        "total_detected": len(questions_raw),
        "valid_count": len(valid_questions),
        "invalid_count": len(invalid_questions),
        "global_topic": global_topic or "General",
        "questions": questions_raw,
    }


def infer_suggested_difficulty(question_text: str, explanation: str) -> str:
    """
    Heuristic rule to suggest starting difficulty (Easy, Medium, Hard).
    Admin has full authority to alter or approve the final level.
    """
    res = classify_difficulty("Grammar", question_text=question_text, explanation=explanation)
    return res.suggested_difficulty

