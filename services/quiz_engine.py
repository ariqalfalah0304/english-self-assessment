"""
Quiz engine service for English Self-Assessment.
Handles question selection, randomization, attempt recording,
answer evaluation, progress advancement, and completion timing.
Supports both Grammar and Reading (with associated reading passages).
"""

from typing import Optional, Any
from pathlib import Path
from datetime import datetime, timezone
import time
import streamlit as st

from config.settings import DEFAULT_QUESTIONS_PER_TEST
from config.constants import CATEGORIES, DIFFICULTIES
from database.db import get_connection
from database.models import Question, Attempt
from database import queries
from database.seed_data import (
    seed_sample_grammar_questions_if_empty,
    seed_sample_reading_passages_and_questions_if_empty,
    seed_sample_listening_questions_if_empty,
)



from services.scoring_service import finalize_attempt
from services.question_selector import select_quiz_questions, select_final_exam_questions

# Session State Keys
SESSION_KEY_CATEGORY = "current_category"
SESSION_KEY_DIFFICULTY = "current_difficulty"
SESSION_KEY_CATEGORY_ID = "current_category_id"
SESSION_KEY_ATTEMPT_ID = "current_attempt_id"
SESSION_KEY_QUESTIONS = "selected_questions"
SESSION_KEY_QUESTION_INDEX = "current_question_index"
SESSION_KEY_QUESTION_ANSWERED = "current_question_answered"
SESSION_KEY_FEEDBACK = "current_feedback"
SESSION_KEY_CORRECT_COUNT = "correct_answers_count"
SESSION_KEY_INCORRECT_COUNT = "incorrect_answers_count"
SESSION_KEY_COMPLETED_ATTEMPT = "completed_attempt_id"
SESSION_KEY_START_TIME = "attempt_start_timestamp"


def prepare_quiz_session(
    category: str,
    difficulty: str,
    category_id: Optional[int] = None,
) -> bool:
    """Validate and initialize basic category & difficulty parameters in session state."""
    norm_cat = next((c for c in CATEGORIES if c.lower() == category.strip().lower()), None)
    norm_diff = next((d for d in DIFFICULTIES if d.lower() == difficulty.strip().lower()), None)

    if not norm_cat or not norm_diff:
        return False

    st.session_state[SESSION_KEY_CATEGORY] = norm_cat
    st.session_state[SESSION_KEY_DIFFICULTY] = norm_diff
    st.session_state[SESSION_KEY_CATEGORY_ID] = category_id
    st.session_state[SESSION_KEY_ATTEMPT_ID] = None
    st.session_state[SESSION_KEY_QUESTIONS] = []
    st.session_state[SESSION_KEY_QUESTION_INDEX] = 0
    st.session_state[SESSION_KEY_QUESTION_ANSWERED] = False
    st.session_state[SESSION_KEY_FEEDBACK] = None
    st.session_state[SESSION_KEY_CORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_INCORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_START_TIME] = None
    st.session_state.pop("is_final_exam", None)
    st.session_state.pop("quiz_skill_number", None)
    return True


def prepare_skill_quiz_session(
    category: str,
    skill_number: int,
    skill_name: str,
    category_id: Optional[int] = None,
) -> bool:
    """Pre-configure the session state before starting a skill-based quiz."""
    reset_quiz_session()
    st.session_state[SESSION_KEY_CATEGORY] = category
    st.session_state["quiz_skill_number"] = int(skill_number)
    st.session_state["quiz_skill_name"] = skill_name
    st.session_state[SESSION_KEY_DIFFICULTY] = f"Skill {skill_number}"
    st.session_state[SESSION_KEY_CATEGORY_ID] = category_id
    st.session_state[SESSION_KEY_ATTEMPT_ID] = None
    st.session_state[SESSION_KEY_QUESTIONS] = []
    st.session_state[SESSION_KEY_QUESTION_INDEX] = 0
    st.session_state[SESSION_KEY_QUESTION_ANSWERED] = False
    st.session_state[SESSION_KEY_FEEDBACK] = None
    st.session_state[SESSION_KEY_CORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_INCORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_START_TIME] = None
    st.session_state.pop("is_final_exam", None)
    return True


def prepare_final_exam_session(
    category: str,
    category_id: Optional[int] = None,
) -> bool:
    """Pre-configure session state before starting Ujian Gabungan (Final Mastery Exam)."""
    reset_quiz_session()
    st.session_state[SESSION_KEY_CATEGORY] = category
    st.session_state["is_final_exam"] = True
    st.session_state[SESSION_KEY_DIFFICULTY] = "Ujian Gabungan"
    st.session_state[SESSION_KEY_CATEGORY_ID] = category_id
    st.session_state[SESSION_KEY_ATTEMPT_ID] = None
    st.session_state[SESSION_KEY_QUESTIONS] = []
    st.session_state[SESSION_KEY_QUESTION_INDEX] = 0
    st.session_state[SESSION_KEY_QUESTION_ANSWERED] = False
    st.session_state[SESSION_KEY_FEEDBACK] = None
    st.session_state[SESSION_KEY_CORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_INCORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_START_TIME] = None
    return True


def get_quiz_session() -> Optional[dict[str, Any]]:
    """Retrieve the current quiz selection session state."""
    cat = st.session_state.get(SESSION_KEY_CATEGORY)
    diff = st.session_state.get(SESSION_KEY_DIFFICULTY)
    skill = st.session_state.get("quiz_skill_number")
    is_final = st.session_state.get("is_final_exam", False)
    if not cat or (not diff and not skill and not is_final):
        return None

    return {
        "category": cat,
        "difficulty": diff or (f"Skill {skill}" if skill else "Ujian Gabungan"),
        "skill_number": skill,
        "is_final_exam": is_final,
        "skill_name": st.session_state.get("quiz_skill_name"),
        "passing_score": st.session_state.get("quiz_passing_score", 70.0),
        "category_id": st.session_state.get(SESSION_KEY_CATEGORY_ID),
        "attempt_id": st.session_state.get(SESSION_KEY_ATTEMPT_ID),
        "selected_questions": st.session_state.get(SESSION_KEY_QUESTIONS, []),
        "current_question_index": st.session_state.get(SESSION_KEY_QUESTION_INDEX, 0),
        "question_answered": st.session_state.get(SESSION_KEY_QUESTION_ANSWERED, False),
        "feedback": st.session_state.get(SESSION_KEY_FEEDBACK),
        "correct_count": st.session_state.get(SESSION_KEY_CORRECT_COUNT, 0),
        "incorrect_count": st.session_state.get(SESSION_KEY_INCORRECT_COUNT, 0),
        "start_time": st.session_state.get(SESSION_KEY_START_TIME),
    }


def is_quiz_selection_ready() -> bool:
    """Check if category and skill or difficulty or final exam are selected."""
    cat = st.session_state.get(SESSION_KEY_CATEGORY)
    diff = st.session_state.get(SESSION_KEY_DIFFICULTY)
    skill = st.session_state.get("quiz_skill_number")
    is_final = st.session_state.get("is_final_exam", False)
    return bool(cat and (diff or skill or is_final))


def reset_quiz_session() -> None:
    """Clear quiz session state variables while preserving participant identity."""
    for key in [
        SESSION_KEY_CATEGORY,
        SESSION_KEY_DIFFICULTY,
        SESSION_KEY_CATEGORY_ID,
        SESSION_KEY_ATTEMPT_ID,
        SESSION_KEY_QUESTIONS,
        SESSION_KEY_QUESTION_INDEX,
        SESSION_KEY_QUESTION_ANSWERED,
        SESSION_KEY_FEEDBACK,
        SESSION_KEY_CORRECT_COUNT,
        SESSION_KEY_INCORRECT_COUNT,
        SESSION_KEY_START_TIME,
        "is_final_exam",
        "quiz_skill_number",
        "quiz_skill_name",
        "quiz_passing_score",
        "skill_result_passed",
        "skill_next_unlocked",
        "skill_completed_number",
        "skill_completed_name",
    ]:
        st.session_state.pop(key, None)


def restart_with_difficulty(new_difficulty: str) -> bool:
    """Prepare a new quiz attempt with a chosen difficulty level for the current category."""
    norm_diff = next((d for d in DIFFICULTIES if d.lower() == new_difficulty.strip().lower()), None)
    if not norm_diff:
        return False

    st.session_state[SESSION_KEY_DIFFICULTY] = norm_diff
    st.session_state[SESSION_KEY_ATTEMPT_ID] = None
    st.session_state[SESSION_KEY_QUESTIONS] = []
    st.session_state[SESSION_KEY_QUESTION_INDEX] = 0
    st.session_state[SESSION_KEY_QUESTION_ANSWERED] = False
    st.session_state[SESSION_KEY_FEEDBACK] = None
    st.session_state[SESSION_KEY_CORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_INCORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_START_TIME] = None
    st.session_state.pop(SESSION_KEY_COMPLETED_ATTEMPT, None)
    return True


def start_quiz_attempt(
    user_id: int,
    category_name: str,
    difficulty: str,
    num_questions: int = DEFAULT_QUESTIONS_PER_TEST,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, Optional[Attempt], list[Question], str]:
    """
    Select randomized active questions matching category and difficulty,
    create an attempt record, and link attempt_questions preserving sequence.
    Attaches passage data for reading questions.
    Gracefully uses available questions if fewer than requested.
    """
    with get_connection(db_path) as conn:
        # Seed sample questions if needed based on category
        if category_name.lower() == "grammar":
            seed_sample_grammar_questions_if_empty(conn)
        elif category_name.lower() == "reading":
            seed_sample_reading_passages_and_questions_if_empty(conn)
        elif category_name.lower() == "listening":
            seed_sample_listening_questions_if_empty(conn)

        category = queries.get_category_by_name(conn, category_name)
        if not category:
            return False, None, [], f"Category '{category_name}' not found."

        # Dynamic Question Selection Algorithm (Phase 14)
        serialized_questions, notice_msg = select_quiz_questions(
            conn=conn,
            user_id=user_id,
            category_name=category_name,
            category_id=category.id,  # type: ignore
            difficulty=difficulty,
            requested_count=num_questions,
        )

        total_found = len(serialized_questions)
        if total_found == 0:
            return False, None, [], f"No active questions found for {category_name} ({difficulty})."

        attempt_id = queries.create_attempt(
            conn=conn,
            user_id=user_id,
            category_id=category.id,  # type: ignore
            difficulty=difficulty,
            total_questions=total_found,
        )

        question_ids = [q["id"] for q in serialized_questions if q.get("id") is not None]
        queries.add_attempt_questions(conn, attempt_id, question_ids)
        attempt = queries.get_attempt_by_id(conn, attempt_id)

        # Question models for return signature backwards compatibility
        question_models = [Question.from_dict(qd) for qd in serialized_questions]

    st.session_state[SESSION_KEY_CATEGORY] = category_name
    st.session_state[SESSION_KEY_DIFFICULTY] = difficulty
    st.session_state[SESSION_KEY_CATEGORY_ID] = category.id
    st.session_state[SESSION_KEY_ATTEMPT_ID] = attempt_id
    st.session_state[SESSION_KEY_QUESTIONS] = serialized_questions
    st.session_state[SESSION_KEY_QUESTION_INDEX] = 0
    st.session_state[SESSION_KEY_QUESTION_ANSWERED] = False
    st.session_state[SESSION_KEY_FEEDBACK] = None
    st.session_state[SESSION_KEY_CORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_INCORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_START_TIME] = time.time()

    return True, attempt, question_models, notice_msg



def submit_current_answer(
    user_answer: str,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, dict[str, Any]]:
    """
    Evaluate user answer for the current question, store in database answers table,
    update score counters, and set feedback in session state.
    Preserves all quiz state variables.
    """
    attempt_id = st.session_state.get(SESSION_KEY_ATTEMPT_ID)
    questions = st.session_state.get(SESSION_KEY_QUESTIONS, [])
    current_idx = st.session_state.get(SESSION_KEY_QUESTION_INDEX, 0)

    if not attempt_id or not questions or current_idx >= len(questions):
        return False, {"error": "No active question found to answer."}

    q_dict = questions[current_idx]
    correct_ans = q_dict["correct_answer"].strip().upper()
    user_clean_ans = user_answer.strip().upper()
    is_correct = (user_clean_ans == correct_ans)

    with get_connection(db_path) as conn:
        queries.record_answer(
            conn=conn,
            attempt_id=attempt_id,
            question_id=q_dict["id"],
            user_answer=user_clean_ans,
            correct_answer=correct_ans,
            is_correct=is_correct,
        )

    if is_correct:
        st.session_state[SESSION_KEY_CORRECT_COUNT] = st.session_state.get(SESSION_KEY_CORRECT_COUNT, 0) + 1
    else:
        st.session_state[SESSION_KEY_INCORRECT_COUNT] = st.session_state.get(SESSION_KEY_INCORRECT_COUNT, 0) + 1

    feedback = {
        "is_correct": is_correct,
        "message": "Good Job!" if is_correct else "Sorry, try again.",
        "user_answer": user_clean_ans,
        "correct_answer": correct_ans,
        "explanation": q_dict.get("explanation", ""),
        "question_text": q_dict["question_text"],
    }

    st.session_state[SESSION_KEY_QUESTION_ANSWERED] = True
    st.session_state[SESSION_KEY_FEEDBACK] = feedback

    return True, feedback


def move_to_next_question() -> bool:
    """
    Advance question pointer by 1 and reset current feedback state.
    Returns True if another question is available, or False if all questions are completed.
    """
    questions = st.session_state.get(SESSION_KEY_QUESTIONS, [])
    current_idx = st.session_state.get(SESSION_KEY_QUESTION_INDEX, 0)

    next_idx = current_idx + 1
    if next_idx < len(questions):
        st.session_state[SESSION_KEY_QUESTION_INDEX] = next_idx
        st.session_state[SESSION_KEY_QUESTION_ANSWERED] = False
        st.session_state[SESSION_KEY_FEEDBACK] = None
        return True
    return False


def start_skill_quiz_attempt(
    user_id: int,
    category_name: str,
    skill_number: int,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, Optional[Attempt], list[dict[str, Any]], str]:
    """
    Start a quiz attempt for a specific skill:
    - Questions are fetched in exact sequential order
    - All available active questions for this skill are loaded
    """
    with get_connection(db_path) as conn:
        if category_name.lower() == "grammar":
            seed_sample_grammar_questions_if_empty(conn)
        elif category_name.lower() == "reading":
            seed_sample_reading_passages_and_questions_if_empty(conn)
        elif category_name.lower() == "listening":
            seed_sample_listening_questions_if_empty(conn)

        category = queries.get_category_by_name(conn, category_name)
        if not category:
            return False, None, [], f"Category '{category_name}' not found."

        raw_questions = queries.get_questions_by_skill_sequential(
            conn=conn,
            category_id=category.id,  # type: ignore
            skill_number=skill_number,
            status="Active",
        )

        if not raw_questions:
            return False, None, [], f"Belum ada soal aktif untuk {category_name} - Skill {skill_number}."

        first_sname = raw_questions[0].get("skill_name") or f"Skill {skill_number}"
        skill_info = queries.get_or_create_skill(
            conn,
            category.id,  # type: ignore
            skill_number,
            first_sname,
        )

        total_questions = len(raw_questions)

        cursor = conn.cursor()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute(
                """
                INSERT INTO attempts (user_id, category_id, difficulty, skill_number, skill_name, total_questions, started_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (user_id, category.id, f"Skill {skill_number}", skill_number, skill_info["skill_name"], total_questions, now_str),
            )
        except sqlite3.IntegrityError:
            # Fallback for unmigrated database with legacy CHECK(difficulty IN ('Easy', 'Medium', 'Hard'))
            cursor.execute(
                """
                INSERT INTO attempts (user_id, category_id, difficulty, skill_number, skill_name, total_questions, started_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (user_id, category.id, "Medium", skill_number, skill_info["skill_name"], total_questions, now_str),
            )
        attempt_id = cursor.lastrowid

        question_ids = [q["id"] for q in raw_questions]
        queries.add_attempt_questions(conn, attempt_id, question_ids)
        attempt = queries.get_attempt_by_id(conn, attempt_id)

    st.session_state[SESSION_KEY_CATEGORY] = category_name
    st.session_state["quiz_skill_number"] = int(skill_number)
    st.session_state["quiz_skill_name"] = skill_info["skill_name"]
    st.session_state["quiz_passing_score"] = float(skill_info.get("passing_score", 70.0))
    st.session_state[SESSION_KEY_DIFFICULTY] = f"Skill {skill_number}"
    st.session_state[SESSION_KEY_ATTEMPT_ID] = attempt_id
    st.session_state[SESSION_KEY_QUESTIONS] = raw_questions
    st.session_state[SESSION_KEY_QUESTION_INDEX] = 0
    st.session_state[SESSION_KEY_QUESTION_ANSWERED] = False
    st.session_state[SESSION_KEY_FEEDBACK] = None
    st.session_state[SESSION_KEY_CORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_INCORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_START_TIME] = time.time()
    st.session_state.pop(SESSION_KEY_COMPLETED_ATTEMPT, None)

    return True, attempt, raw_questions, ""


def complete_current_attempt(db_path: Optional[str | Path] = None) -> Optional[Attempt]:
    """Finalize the current attempt by calculating final score, duration, and saving to SQLite."""
    attempt_id = st.session_state.get(SESSION_KEY_ATTEMPT_ID)
    questions = st.session_state.get(SESSION_KEY_QUESTIONS, [])
    correct = st.session_state.get(SESSION_KEY_CORRECT_COUNT, 0)
    incorrect = st.session_state.get(SESSION_KEY_INCORRECT_COUNT, 0)
    start_ts = st.session_state.get(SESSION_KEY_START_TIME)

    if not attempt_id:
        return None

    duration_sec: Optional[int] = None
    if start_ts is not None:
        duration_sec = max(1, int(time.time() - start_ts))

    passing_score = float(st.session_state.get("quiz_passing_score", 70.0))

    with get_connection(db_path) as conn:
        attempt = finalize_attempt(
            conn=conn,
            attempt_id=attempt_id,
            total_questions=len(questions),
            correct_answers=correct,
            incorrect_answers=incorrect,
            duration_seconds=duration_sec,
            passing_score=passing_score,
        )
        if attempt and "quiz_skill_number" in st.session_state:
            s_num = int(st.session_state["quiz_skill_number"])
            is_passed, next_unlocked = queries.record_user_skill_attempt(
                conn=conn,
                user_id=attempt.user_id,
                category_id=attempt.category_id,
                skill_number=s_num,
                score=attempt.score,
                passing_score=passing_score,
            )
            st.session_state["skill_result_passed"] = is_passed
            st.session_state["skill_next_unlocked"] = next_unlocked
            st.session_state["skill_completed_number"] = s_num
            st.session_state["skill_completed_name"] = st.session_state.get("quiz_skill_name", f"Skill {s_num}")

    st.session_state[SESSION_KEY_COMPLETED_ATTEMPT] = attempt_id
    return attempt


def start_final_exam_attempt(
    user_id: int,
    category_name: str,
    requested_count: int = 50,
    db_path: Optional[str | Path] = None,
) -> tuple[bool, Optional[Attempt], list[dict[str, Any]], str]:
    """
    Start an Ujian Gabungan (Final Mastery Exam) attempt:
    1. Samples questions proportionally across all active skills of the category.
    2. Shuffles questions & answer options randomly.
    3. Records attempt in database as Ujian Gabungan.
    """
    with get_connection(db_path) as conn:
        if category_name.lower() == "grammar":
            seed_sample_grammar_questions_if_empty(conn)
        elif category_name.lower() == "reading":
            seed_sample_reading_passages_and_questions_if_empty(conn)
        elif category_name.lower() == "listening":
            seed_sample_listening_questions_if_empty(conn)

        category = queries.get_category_by_name(conn, category_name)
        if not category:
            return False, None, [], f"Category '{category_name}' not found."

        raw_questions, notice_msg = select_final_exam_questions(
            conn=conn,
            user_id=user_id,
            category_name=category_name,
            category_id=category.id,  # type: ignore
            requested_count=requested_count,
        )

        if not raw_questions:
            return False, None, [], f"Belum ada soal aktif untuk Ujian Gabungan {category_name}."

        total_questions = len(raw_questions)

        cursor = conn.cursor()
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor.execute(
                """
                INSERT INTO attempts (user_id, category_id, difficulty, skill_name, total_questions, started_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (user_id, category.id, "Ujian Gabungan", "Ujian Gabungan (Final Mastery)", total_questions, now_str),
            )
        except sqlite3.IntegrityError:
            cursor.execute(
                """
                INSERT INTO attempts (user_id, category_id, difficulty, skill_name, total_questions, started_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (user_id, category.id, "Hard", "Ujian Gabungan (Final Mastery)", total_questions, now_str),
            )
        attempt_id = cursor.lastrowid

        question_ids = [q["id"] for q in raw_questions if q.get("id")]
        queries.add_attempt_questions(conn, attempt_id, question_ids)
        attempt = queries.get_attempt_by_id(conn, attempt_id)

    st.session_state[SESSION_KEY_CATEGORY] = category_name
    st.session_state["is_final_exam"] = True
    st.session_state[SESSION_KEY_DIFFICULTY] = "Ujian Gabungan"
    st.session_state[SESSION_KEY_CATEGORY_ID] = category.id
    st.session_state[SESSION_KEY_ATTEMPT_ID] = attempt_id
    st.session_state[SESSION_KEY_QUESTIONS] = raw_questions
    st.session_state[SESSION_KEY_QUESTION_INDEX] = 0
    st.session_state[SESSION_KEY_QUESTION_ANSWERED] = False
    st.session_state[SESSION_KEY_FEEDBACK] = None
    st.session_state[SESSION_KEY_CORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_INCORRECT_COUNT] = 0
    st.session_state[SESSION_KEY_START_TIME] = time.time()
    st.session_state.pop(SESSION_KEY_COMPLETED_ATTEMPT, None)

    return True, attempt, raw_questions, notice_msg
