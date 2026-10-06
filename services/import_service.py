"""
Import Service for English Self-Assessment (Phase 12).
Orchestrates batch import of questions parsed from Word (.docx) documents.
Features:
- Never publishes questions automatically (default status = 'Draft')
- Sets source_file tracking for origin auditing
- Records batch executions in import_history table
- Preserves admin-assigned Final Level
- Provides import audit history
"""

from typing import Optional, Any
from pathlib import Path

from database.db import get_connection
from database.models import Question, ImportHistory
from database import queries
from config.settings import BASE_DIR, LISTENING_AUDIO_DIR
from utils.security import sanitize_filename, is_safe_audio_path


def execute_import_batch(
    file_name: str,
    questions: list[dict[str, Any]],
    category_name: str,
    default_status: str = "Draft",
    imported_by: Optional[str] = None,
    db_path: Optional[str | Path] = None,
) -> tuple[int, int, int]:
    """
    Commit parsed questions into SQLite database under the designated category.
    Sets status to 'Draft' so questions are not published automatically.
    Creates an entry in import_history.

    Returns:
    (total_detected, total_imported, total_failed)
    """
    total_detected = len(questions)
    total_imported = 0
    total_failed = 0
    safe_filename = sanitize_filename(file_name)

    with get_connection(db_path) as conn:
        cat_cache: dict[str, Any] = {}
        passage_cache: dict[str, int] = {}

        for q_data in questions:
            # Skip questions flagged as invalid
            if not q_data.get("is_valid", False):
                total_failed += 1
                continue

            # Determine item category (row-level or fallback)
            item_cat_name = (q_data.get("category") or category_name).strip()
            if item_cat_name not in cat_cache:
                cat_row = queries.get_category_by_name(conn, item_cat_name)
                if not cat_row:
                    cat_row = queries.get_category_by_name(conn, category_name)
                cat_cache[item_cat_name] = cat_row

            active_cat = cat_cache.get(item_cat_name)
            if not active_cat:
                total_failed += 1
                continue

            # Passage handling for Reading
            passage_id = None
            if active_cat.name == "Reading" and q_data.get("passage_text"):
                pass_text = q_data["passage_text"].strip()
                if pass_text in passage_cache:
                    passage_id = passage_cache[pass_text]
                else:
                    passage_id = queries.create_passage(
                        conn=conn,
                        title=q_data.get("passage_title") or "Imported Passage",
                        passage_text=pass_text,
                        category_id=active_cat.id,
                    )
                    passage_cache[pass_text] = passage_id

            # Determine final level
            final_difficulty = q_data.get("final_difficulty") or q_data.get("difficulty") or q_data.get("suggested_difficulty") or "Medium"

            # Determine item status - preserve Draft safety
            item_status = q_data.get("status") or default_status
            if item_status not in ["Draft", "Active", "Inactive", "Archived"]:
                item_status = "Draft"

            # Resolve skill number, skill name, and sequential order
            raw_snum = q_data.get("skill_number") or q_data.get("skill") or 1
            try:
                s_num = int(raw_snum)
            except (ValueError, TypeError):
                s_num = 1

            s_name = str(q_data.get("skill_name") or q_data.get("topic") or f"Skill {s_num}").strip()

            raw_qorder = q_data.get("question_order") or q_data.get("question_number") or (total_imported + 1)
            try:
                q_order = int(raw_qorder)
            except (ValueError, TypeError):
                q_order = total_imported + 1

            # Auto-register skill in category's skill list
            queries.get_or_create_skill(conn, active_cat.id, s_num, s_name)

            try:
                q_model = Question(
                    category_id=active_cat.id,
                    passage_id=passage_id,
                    subtopic=s_name,
                    question_type=q_data.get("question_type", "Multiple Choice"),
                    question_text=q_data["question_text"].strip(),
                    option_a=q_data["option_a"].strip(),
                    option_b=q_data["option_b"].strip(),
                    option_c=q_data["option_c"].strip(),
                    option_d=q_data["option_d"].strip(),
                    correct_answer=q_data["correct_answer"].strip().upper(),
                    explanation=q_data.get("explanation", "").strip(),
                    difficulty=final_difficulty,
                    status=item_status,
                    source_file=safe_filename,
                    skill_number=s_num,
                    skill_name=s_name,
                    question_order=q_order,
                )
                new_qid = queries.create_question(conn, q_model)

                # Link audio file for Listening questions if provided
                if active_cat.name == "Listening":
                    final_audio_path = None
                    if q_data.get("uploaded_audio_bytes") and q_data.get("uploaded_audio_name"):
                        audio_filename = sanitize_filename(f"q_{new_qid}_{q_data['uploaded_audio_name']}")
                        LISTENING_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
                        save_dest = LISTENING_AUDIO_DIR / audio_filename
                        with open(save_dest, "wb") as f_aud:
                            f_aud.write(q_data["uploaded_audio_bytes"])
                        final_audio_path = f"audio/listening/{audio_filename}"
                    elif q_data.get("audio_file"):
                        raw_audio_str = str(q_data["audio_file"]).strip()
                        is_safe_audio, _, _ = is_safe_audio_path(raw_audio_str, BASE_DIR)
                        if is_safe_audio:
                            final_audio_path = raw_audio_str

                    if final_audio_path:
                        queries.create_audio_file(
                            conn=conn,
                            question_id=new_qid,
                            file_path=final_audio_path,
                            transcript=str(q_data.get("transcript", "")).strip() or None,
                            duration=float(q_data["duration"]) if q_data.get("duration") is not None and isinstance(q_data.get("duration"), (int, float)) else None,
                        )

                total_imported += 1
            except Exception:
                total_failed += 1

        # Record import batch in import_history
        queries.record_import(
            conn=conn,
            file_name=safe_filename,
            category=category_name,
            total_detected=total_detected,
            total_imported=total_imported,
            total_failed=total_failed,
            imported_by=imported_by or "admin",
        )

    return total_detected, total_imported, total_failed


def fetch_import_history_logs(
    limit: int = 50,
    db_path: Optional[str | Path] = None,
) -> list[ImportHistory]:
    """Retrieve historical import batch execution logs."""
    with get_connection(db_path) as conn:
        return queries.get_import_history(conn, limit=limit)
