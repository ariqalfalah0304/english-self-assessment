"""
Question Bank Management Service for English Self-Assessment (Phase 11).
Handles:
- Validation rules for question creation & modification across all categories
- CRUD operations for Grammar, Reading (with passages), and Listening (with audio files)
- Status transitions: Draft, Active, Inactive, Archived
- Topic and passage management helpers
- Filtering and keyword searching
"""

from typing import Optional, Any
from pathlib import Path

from database.db import get_connection
from database.models import Question, Passage
from database import queries
from config.settings import BASE_DIR
from utils.security import is_safe_audio_path


VALID_CATEGORIES = ["Grammar", "Reading", "Listening"]
VALID_DIFFICULTIES = ["Easy", "Medium", "Hard"]
VALID_STATUSES = ["Draft", "Active", "Inactive", "Archived"]
VALID_ANSWERS = ["A", "B", "C", "D"]


def validate_question_payload(data: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate all fields before adding or updating a question.
    Ensures invalid or incomplete questions cannot be created.
    """
    # 1. Category check
    category = data.get("category", "").strip()
    if category not in VALID_CATEGORIES:
        return False, f"Invalid category '{category}'. Must be one of: {', '.join(VALID_CATEGORIES)}"

    # 2. Difficulty check
    difficulty = data.get("difficulty", "").strip()
    if difficulty not in VALID_DIFFICULTIES:
        return False, f"Invalid difficulty '{difficulty}'. Must be one of: {', '.join(VALID_DIFFICULTIES)}"

    # 3. Status check
    status = data.get("status", "Active").strip()
    if status not in VALID_STATUSES:
        return False, f"Invalid status '{status}'. Must be one of: {', '.join(VALID_STATUSES)}"

    # 4. Question text check
    q_text = data.get("question_text", "").strip()
    if not q_text or len(q_text) < 5:
        return False, "Question text must be at least 5 characters long."

    # 5. Options A, B, C, D checks
    opt_a = data.get("option_a", "").strip()
    opt_b = data.get("option_b", "").strip()
    opt_c = data.get("option_c", "").strip()
    opt_d = data.get("option_d", "").strip()

    if not opt_a or not opt_b or not opt_c or not opt_d:
        return False, "All four options (A, B, C, and D) are required and cannot be empty."

    # Ensure options are distinct (avoid duplicate options)
    options_set = {opt_a.lower(), opt_b.lower(), opt_c.lower(), opt_d.lower()}
    if len(options_set) < 4:
        return False, "All four options must be distinct from one another."

    # 6. Correct answer check
    correct = data.get("correct_answer", "").strip().upper()
    if correct not in VALID_ANSWERS:
        return False, f"Correct answer must be one of: {', '.join(VALID_ANSWERS)}"

    # 7. Category-specific requirements
    if category == "Reading":
        # Reading question must be linked to a passage
        has_passage_id = data.get("passage_id") is not None and int(data.get("passage_id", 0)) > 0
        has_new_passage = bool(data.get("new_passage_text", "").strip())
        if not (has_passage_id or has_new_passage):
            return False, "Reading questions must be associated with a reading passage."

    elif category == "Listening":
        # Listening question must be linked to a safe audio file
        audio_file = data.get("audio_file", "").strip()
        if not audio_file:
            return False, "Listening questions must include an audio file path (e.g. audio/listening/file.mp3)."
        is_safe, _, sec_err = is_safe_audio_path(audio_file, BASE_DIR)
        if not is_safe:
            return False, f"Invalid audio file reference: {sec_err}"

    # 8. Explanation check
    explanation = data.get("explanation", "").strip()
    if not explanation or len(explanation) < 5:
        return False, "An informative explanation is required (at least 5 characters)."

    return True, ""


# ==========================================
# CRUD OPERATIONS
# ==========================================

def fetch_questions(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    status: Optional[str] = None,
    topic: Optional[str] = None,
    search: Optional[str] = None,
    skill_number: Optional[int] = None,
    limit: int = 200,
    offset: int = 0,
    db_path: Optional[str | Path] = None,
) -> list[dict[str, Any]]:
    """Retrieve filtered list of questions."""
    with get_connection(db_path) as conn:
        cat_id = None
        if category and category.strip().lower() != "all":
            c_row = queries.get_category_by_name(conn, category.strip())
            if c_row:
                cat_id = c_row.id

        return queries.get_questions_filtered(
            conn=conn,
            category_id=cat_id,
            difficulty=difficulty,
            status=status,
            topic=topic,
            search_query=search,
            skill_number=skill_number,
            limit=limit,
            offset=offset,
        )


def fetch_question_by_id(
    question_id: int,
    db_path: Optional[str | Path] = None,
) -> Optional[dict[str, Any]]:
    """Retrieve a single question by primary key with linked passage and audio info."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 
                q.id, q.category_id, c.name, q.difficulty, q.status, q.subtopic, q.question_type,
                q.question_text, q.option_a, q.option_b, q.option_c, q.option_d, q.correct_answer,
                q.explanation, q.passage_id, p.title, p.passage_text, af.file_path, af.transcript,
                q.created_at, q.updated_at, q.skill_number, q.skill_name, q.question_order
            FROM questions q
            JOIN categories c ON q.category_id = c.id
            LEFT JOIN passages p ON q.passage_id = p.id
            LEFT JOIN audio_files af ON q.id = af.question_id
            WHERE q.id = ?;
            """,
            (question_id,),
        )
        r = cursor.fetchone()
        if not r:
            return None

        return {
            "id": r[0],
            "category_id": r[1],
            "category_name": r[2],
            "difficulty": r[3],
            "status": r[4],
            "subtopic": r[5] or "General",
            "question_type": r[6] or "Multiple Choice",
            "question_text": r[7],
            "option_a": r[8],
            "option_b": r[9],
            "option_c": r[10],
            "option_d": r[11],
            "correct_answer": r[12],
            "explanation": r[13] or "",
            "passage_id": r[14],
            "passage_title": r[15],
            "passage_text": r[16],
            "audio_file": r[17],
            "audio_transcript": r[18],
            "created_at": r[19],
            "updated_at": r[20],
            "skill_number": r[21],
            "skill_name": r[22] or (f"Skill {r[21]}" if r[21] is not None else None),
            "question_order": r[23],
        }


def add_question(
    data: dict[str, Any],
    db_path: Optional[str | Path] = None,
) -> tuple[bool, Optional[int], str]:
    """
    Validate and add a new question to the database.
    Creates passage or audio records if applicable.
    """
    is_valid, err_msg = validate_question_payload(data)
    if not is_valid:
        return False, None, err_msg

    with get_connection(db_path) as conn:
        cat_row = queries.get_category_by_name(conn, data["category"].strip())
        if not cat_row:
            return False, None, f"Category '{data['category']}' not found in database."

        s_num = data.get("skill_number")
        s_name = data.get("skill_name")
        if s_num:
            try:
                s_num = int(s_num)
                if not s_name:
                    s_name = f"Skill {s_num}"
                queries.get_or_create_skill(conn, cat_row.id, s_num, s_name)
            except Exception:
                s_num = None

        passage_id = data.get("passage_id")
        # If Reading and creating a new passage on-the-fly
        if data["category"] == "Reading":
            if not passage_id and data.get("new_passage_text"):
                passage_id = queries.create_passage(
                    conn=conn,
                    title=data.get("new_passage_title", "Untitled Passage").strip(),
                    passage_text=data.get("new_passage_text", "").strip(),
                    category_id=cat_row.id,
                )

        q = Question(
            category_id=cat_row.id,
            passage_id=passage_id,
            subtopic=data.get("subtopic", "General").strip(),
            question_type=data.get("question_type", "Multiple Choice").strip(),
            question_text=data["question_text"].strip(),
            option_a=data["option_a"].strip(),
            option_b=data["option_b"].strip(),
            option_c=data["option_c"].strip(),
            option_d=data["option_d"].strip(),
            correct_answer=data["correct_answer"].strip().upper(),
            explanation=data.get("explanation", "").strip(),
            difficulty=data.get("difficulty", "Standard").strip(),
            status=data.get("status", "Active").strip(),
            source_file="manual_admin_entry",
            skill_number=s_num,
            skill_name=s_name,
            question_order=data.get("question_order"),
        )

        q_id = queries.create_question(conn, q)

        # If Listening, create audio_files record
        if data["category"] == "Listening" and data.get("audio_file"):
            queries.create_audio_file(
                conn=conn,
                question_id=q_id,
                file_path=data.get("audio_file", "").strip(),
                transcript=data.get("audio_transcript", "").strip() or None,
            )

        return True, q_id, f"Question #{q_id} created successfully."


def update_question_record(
    question_id: int,
    data: dict[str, Any],
    db_path: Optional[str | Path] = None,
) -> tuple[bool, str]:
    """
    Validate and update an existing question record.
    """
    is_valid, err_msg = validate_question_payload(data)
    if not is_valid:
        return False, err_msg

    with get_connection(db_path) as conn:
        cat_row = queries.get_category_by_name(conn, data["category"].strip())
        if not cat_row:
            return False, f"Category '{data['category']}' not found in database."

        s_num = data.get("skill_number")
        s_name = data.get("skill_name")
        if s_num:
            try:
                s_num = int(s_num)
                if not s_name:
                    s_name = f"Skill {s_num}"
                queries.get_or_create_skill(conn, cat_row.id, s_num, s_name)
            except Exception:
                s_num = None

        passage_id = data.get("passage_id")
        if data["category"] == "Reading" and not passage_id and data.get("new_passage_text"):
            passage_id = queries.create_passage(
                conn=conn,
                title=data.get("new_passage_title", "Untitled Passage").strip(),
                passage_text=data.get("new_passage_text", "").strip(),
                category_id=cat_row.id,
            )

        updated = queries.update_question(
            conn=conn,
            question_id=question_id,
            category_id=cat_row.id,
            question_text=data["question_text"],
            option_a=data["option_a"],
            option_b=data["option_b"],
            option_c=data["option_c"],
            option_d=data["option_d"],
            correct_answer=data["correct_answer"],
            difficulty=data.get("difficulty", "Standard"),
            explanation=data.get("explanation"),
            status=data.get("status", "Active"),
            subtopic=data.get("subtopic"),
            question_type=data.get("question_type"),
            passage_id=passage_id,
            skill_number=s_num,
            skill_name=s_name,
            question_order=data.get("question_order"),
        )

        if not updated:
            return False, f"Question #{question_id} could not be updated."

        # Update audio file if Listening
        if data["category"] == "Listening" and data.get("audio_file"):
            queries.update_or_create_audio_file(
                conn=conn,
                question_id=question_id,
                file_path=data.get("audio_file", "").strip(),
                transcript=data.get("audio_transcript", "").strip() or None,
            )

        return True, f"Question #{question_id} updated successfully."


def change_status(
    question_id: int,
    new_status: str,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, str]:
    """Change the operational status of a question."""
    norm_status = new_status.strip().capitalize()
    if norm_status not in VALID_STATUSES:
        return False, f"Invalid status '{new_status}'. Allowed: {', '.join(VALID_STATUSES)}"

    with get_connection(db_path) as conn:
        success = queries.update_question_status(conn, question_id, norm_status)
        if success:
            return True, f"Question #{question_id} status changed to '{norm_status}'."
        return False, f"Could not update status for Question #{question_id}."


def deactivate_question(question_id: int, db_path: Optional[str | Path] = None) -> tuple[bool, str]:
    """Mark question as Inactive (hidden from quiz)."""
    return change_status(question_id, "Inactive", db_path=db_path)


def archive_question(question_id: int, db_path: Optional[str | Path] = None) -> tuple[bool, str]:
    """Mark question as Archived."""
    return change_status(question_id, "Archived", db_path=db_path)


def activate_question(question_id: int, db_path: Optional[str | Path] = None) -> tuple[bool, str]:
    """Mark question as Active."""
    return change_status(question_id, "Active", db_path=db_path)


def fetch_passages_list(db_path: Optional[str | Path] = None) -> list[Passage]:
    """Fetch all available reading passages."""
    with get_connection(db_path) as conn:
        return queries.get_all_passages(conn)


def fetch_distinct_topics_list(db_path: Optional[str | Path] = None) -> list[str]:
    """Fetch unique topics across questions."""
    with get_connection(db_path) as conn:
        return queries.get_distinct_topics(conn)


def fetch_distinct_skill_numbers(
    category_name: Optional[str] = None,
    db_path: Optional[str | Path] = None,
) -> list[int]:
    """
    Fetch all unique skill numbers present across questions and configured skills.
    Optionally filtered by category_name.
    """
    with get_connection(db_path) as conn:
        cat_id = None
        if category_name and category_name != "All":
            cat = queries.get_category_by_name(conn, category_name)
            if cat:
                cat_id = cat.id

        cursor = conn.cursor()
        query = """
            SELECT DISTINCT skill_number
            FROM (
                SELECT skill_number, category_id FROM questions WHERE skill_number IS NOT NULL
                UNION
                SELECT skill_number, category_id FROM skills WHERE skill_number IS NOT NULL
            )
            WHERE (? IS NULL OR category_id = ?)
            ORDER BY skill_number ASC;
        """
        cursor.execute(query, (cat_id, cat_id))
        return [row[0] for row in cursor.fetchall() if row[0] is not None]


def delete_question_record(question_id: int, db_path: Optional[str | Path] = None) -> tuple[bool, str]:
    """Permanently delete a question from the database if not referenced by completed attempts."""
    try:
        with get_connection(db_path) as conn:
            success = queries.delete_question(conn, question_id)
            if success:
                return True, f"Question #{question_id} was successfully deleted."
            return False, f"Question #{question_id} was not found."
    except ValueError as ve:
        return False, str(ve)
    except Exception as e:
        return False, f"Error deleting question: {str(e)}"


def delete_questions_bulk(question_ids: list[int], db_path: Optional[str | Path] = None) -> tuple[int, int]:
    """Bulk delete multiple questions. Returns (deleted_count, skipped_count)."""
    with get_connection(db_path) as conn:
        return queries.delete_questions_by_ids(conn, question_ids)


def activate_questions_bulk(question_ids: list[int], db_path: Optional[str | Path] = None) -> tuple[bool, str]:
    """Bulk activate a list of questions."""
    return update_questions_status_bulk(question_ids, "Active", db_path=db_path)


def update_questions_status_bulk(
    question_ids: list[int],
    new_status: str,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, str]:
    """Bulk change status (Active, Inactive, Archived, Draft) for multiple questions."""
    if not question_ids:
        return False, "Tidak ada soal yang dipilih."
    try:
        with get_connection(db_path) as conn:
            updated_count = queries.update_questions_status_by_ids(conn, question_ids, new_status)
            return True, f"Berhasil memperbarui {updated_count} soal menjadi status '{new_status}'!"
    except Exception as e:
        return False, f"Gagal memperbarui status soal: {str(e)}"


def fetch_category_question_limits(db_path: Optional[str | Path] = None) -> list[dict[str, Any]]:
    """Fetch categories with their configured question limits and available question counts."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(categories);")
        cols = [r["name"] for r in cursor.fetchall()]
        if "question_limit" not in cols:
            cursor.execute("ALTER TABLE categories ADD COLUMN question_limit INTEGER DEFAULT 20;")
            conn.commit()
        return queries.get_all_categories_with_limits(conn)


def save_category_question_limits(category_limits: dict[str, int], db_path: Optional[str | Path] = None) -> tuple[bool, str]:
    """Save question limits for categories."""
    try:
        with get_connection(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(categories);")
            cols = [r["name"] for r in cursor.fetchall()]
            if "question_limit" not in cols:
                cursor.execute("ALTER TABLE categories ADD COLUMN question_limit INTEGER DEFAULT 20;")
                conn.commit()

            for cat_name, limit in category_limits.items():
                queries.update_category_question_limit(conn, cat_name, limit)
        return True, "Berhasil menyimpan pengaturan jumlah soal untuk setiap kategori!"
    except Exception as e:
        return False, f"Gagal menyimpan pengaturan: {str(e)}"


def get_category_question_limit_setting(category_name: str, db_path: Optional[str | Path] = None) -> int:
    """Get the question limit for a specific category."""
    with get_connection(db_path) as conn:
        return queries.get_category_question_limit(conn, category_name)


def fetch_skills_for_category(category_name: str, db_path: Optional[str | Path] = None) -> list[dict[str, Any]]:
    """Fetch all skills configured for a category."""
    with get_connection(db_path) as conn:
        c = queries.get_category_by_name(conn, category_name)
        if not c:
            return []
        return queries.get_skills_by_category(conn, c.id)  # type: ignore


def update_skill_passing_grade(
    skill_id: int,
    skill_name: str,
    passing_score: float,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, str]:
    """Update skill name and passing grade."""
    try:
        with get_connection(db_path) as conn:
            ok = queries.update_skill_config(conn, skill_id, skill_name, passing_score)
            if ok:
                return True, "Berhasil memperbarui konfigurasi skill!"
            return False, "Skill tidak ditemukan."
    except Exception as e:
        return False, f"Gagal memperbarui skill: {str(e)}"




