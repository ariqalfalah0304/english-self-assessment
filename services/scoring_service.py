"""
Scoring engine and evaluation service for English Self-Assessment.
Calculates percentage scores, accuracy metrics, and records completed attempts.
"""

from typing import Optional, Any
from datetime import datetime
import sqlite3

from database.models import Attempt
from database import queries


def calculate_score(correct_answers: int, total_questions: int) -> float:
    """
    Calculate standardized assessment score as a percentage (0.0 to 100.0).
    Formula: (Correct Answers / Total Questions) * 100
    """
    if total_questions <= 0:
        return 0.0
    raw_score = (correct_answers / total_questions) * 100.0
    return round(raw_score, 2)


def calculate_accuracy(correct_answers: int, total_answered: int) -> float:
    """
    Calculate accuracy rate over submitted answers.
    """
    if total_answered <= 0:
        return 0.0
    return round((correct_answers / total_answered) * 100.0, 2)


def calculate_duration_seconds(
    started_at_str: Optional[str],
    completed_at_str: Optional[str],
) -> Optional[int]:
    """Calculate elapsed duration in seconds between two timestamp strings."""
    if not started_at_str or not completed_at_str:
        return None
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        t0 = datetime.strptime(started_at_str.split(".")[0], fmt)
        t1 = datetime.strptime(completed_at_str.split(".")[0], fmt)
        return max(0, int((t1 - t0).total_seconds()))
    except Exception:
        return None


def finalize_attempt(
    conn: sqlite3.Connection,
    attempt_id: int,
    total_questions: int,
    correct_answers: int,
    incorrect_answers: int,
    duration_seconds: Optional[int] = None,
    passing_score: float = 70.0,
) -> Attempt:
    """
    Compute final scores, persist results to SQLite attempt record,
    and return the updated Attempt instance.
    """
    final_score = calculate_score(correct_answers, total_questions)

    queries.complete_attempt(
        conn=conn,
        attempt_id=attempt_id,
        correct_answers=correct_answers,
        incorrect_answers=incorrect_answers,
        score=final_score,
        duration_seconds=duration_seconds,
        passing_score=passing_score,
    )

    attempt = queries.get_attempt_by_id(conn, attempt_id)
    assert attempt is not None
    return attempt


def get_attempt_summary(conn: sqlite3.Connection, attempt_id: int) -> Optional[dict[str, Any]]:
    """Retrieve comprehensive summary data for an attempt including answers."""
    attempt = queries.get_attempt_by_id(conn, attempt_id)
    if not attempt:
        return None

    answers = queries.get_answers_by_attempt(conn, attempt_id)
    ordered_questions = queries.get_attempt_questions(conn, attempt_id)

    category = queries.get_category_by_id(conn, attempt.category_id)
    category_name = category.name if category else "Unknown"

    total = attempt.total_questions
    correct = attempt.correct_answers
    incorrect = attempt.incorrect_answers
    score = attempt.score
    accuracy = calculate_accuracy(correct, len(answers))

    return {
        "attempt_id": attempt.id,
        "user_id": attempt.user_id,
        "category": category_name,
        "difficulty": attempt.difficulty,
        "total_questions": total,
        "correct_answers": correct,
        "incorrect_answers": incorrect,
        "score": score,
        "accuracy": accuracy,
        "started_at": attempt.started_at,
        "completed_at": attempt.completed_at,
        "duration_seconds": attempt.duration_seconds,
        "skill_number": attempt.skill_number,
        "skill_name": attempt.skill_name,
        "is_passed": attempt.is_passed,
        "answers_count": len(answers),
        "questions_count": len(ordered_questions),
    }
