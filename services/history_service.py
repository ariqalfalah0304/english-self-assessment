"""
User Assessment History and Self-Assessment Summary Service (Phase 15).
Computes performance metrics, category breakdowns, score progression trends,
and descriptive feedback without formal proficiency certification claims.
"""

from typing import Optional, Any
from pathlib import Path
from datetime import datetime

from database.db import get_connection
from database import queries
from config.constants import CATEGORIES


CERTIFICATION_DISCLAIMER = (
    "This self-assessment summary reflects observed practice scores across completed test attempts. "
    "It is not an officially certified English proficiency credential or standardized diagnostic score (such as TOEFL, IELTS, or CEFR)."
)


def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds to a human-readable string (e.g., '1m 24s')."""
    if seconds is None or seconds <= 0:
        return "-"
    mins = seconds // 60
    secs = seconds % 60
    if mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"


def fetch_user_history(
    user_id: int,
    db_path: Optional[str | Path] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve formatted assessment history for a specific user.
    Ordered by date (most recent first).
    """
    with get_connection(db_path) as conn:
        raw_history = queries.get_user_assessment_history(conn, user_id)

    formatted: list[dict[str, Any]] = []
    for item in raw_history:
        date_raw = item.get("completed_at") or item.get("started_at") or ""
        date_str = date_raw[:16] if len(date_raw) >= 16 else date_raw

        tot = item.get("total_questions", 0)
        corr = item.get("correct_answers", 0)
        inc = item.get("incorrect_answers", 0)
        score = item.get("score", 0.0)
        acc = round((corr / tot) * 100.0, 1) if tot > 0 else 0.0

        formatted.append({
            "attempt_id": item.get("id"),
            "date": date_str,
            "raw_timestamp": date_raw,
            "category": item.get("category", "Grammar"),
            "difficulty": item.get("difficulty", "Easy"),
            "score": score,
            "correct": corr,
            "incorrect": inc,
            "number_of_questions": tot,
            "accuracy": acc,
            "duration": format_duration(item.get("duration_seconds")),
            "duration_seconds": item.get("duration_seconds"),
            "is_completed": item.get("completed_at") is not None,
        })

    return formatted


def calculate_self_assessment_summary(
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compute self-assessment performance summary:
    - Category breakdowns (Grammar, Reading, Listening)
    - Average score, number of attempts, latest score, best score, accuracy
    - Strongest observed category & category with lower observed score
    - Descriptive feedback and non-certification disclaimer
    """
    completed_items = [h for h in history if h.get("is_completed")]
    total_attempts = len(completed_items)

    category_summaries: dict[str, dict[str, Any]] = {}
    standard_categories = ["Grammar", "Reading", "Listening"]

    for cat in standard_categories:
        cat_items = [h for h in completed_items if h.get("category", "").lower() == cat.lower()]
        count = len(cat_items)

        if count > 0:
            scores = [h["score"] for h in cat_items]
            avg_score = round(sum(scores) / count, 1)
            best_score = round(max(scores), 1)
            latest_score = round(cat_items[0]["score"], 1)  # history is sorted DESC

            tot_corr = sum(h["correct"] for h in cat_items)
            tot_q = sum(h["number_of_questions"] for h in cat_items)
            accuracy = round((tot_corr / tot_q) * 100.0, 1) if tot_q > 0 else 0.0
        else:
            avg_score = 0.0
            best_score = 0.0
            latest_score = None
            accuracy = 0.0
            tot_corr = 0
            tot_q = 0

        category_summaries[cat] = {
            "category": cat,
            "number_of_attempts": count,
            "average_score": avg_score,
            "best_score": best_score,
            "latest_score": latest_score,
            "accuracy": accuracy,
            "total_correct": tot_corr,
            "total_questions": tot_q,
        }

    # Overall Metrics
    if total_attempts > 0:
        all_scores = [h["score"] for h in completed_items]
        overall_avg = round(sum(all_scores) / total_attempts, 1)
        overall_best = round(max(all_scores), 1)
        overall_latest = round(completed_items[0]["score"], 1)
        all_corr = sum(h["correct"] for h in completed_items)
        all_q = sum(h["number_of_questions"] for h in completed_items)
        overall_acc = round((all_corr / all_q) * 100.0, 1) if all_q > 0 else 0.0
    else:
        overall_avg = 0.0
        overall_best = 0.0
        overall_latest = None
        overall_acc = 0.0

    # Determine Strongest & Lower Observed Categories (only from attempted categories)
    attempted_cats = [
        cat for cat, data in category_summaries.items()
        if data["number_of_attempts"] > 0
    ]

    strongest_cat: Optional[str] = None
    lowest_cat: Optional[str] = None

    if attempted_cats:
        strongest_cat = max(attempted_cats, key=lambda c: category_summaries[c]["average_score"])
        if len(attempted_cats) > 1:
            lowest_cat = min(attempted_cats, key=lambda c: category_summaries[c]["average_score"])
            # If lowest is identical score to strongest, only report if there is actual variance
            if category_summaries[lowest_cat]["average_score"] == category_summaries[strongest_cat]["average_score"]:
                lowest_cat = None
        else:
            lowest_cat = None

    # Chronological progression (oldest to newest for charts & progress analysis)
    chronological = list(reversed(completed_items))

    # Evaluate Progress Trend
    progress_trend = "Initial assessment baseline established."
    if len(chronological) >= 3:
        first_half = chronological[:len(chronological)//2]
        second_half = chronological[len(chronological)//2:]
        avg1 = sum(h["score"] for h in first_half) / len(first_half)
        avg2 = sum(h["score"] for h in second_half) / len(second_half)
        diff = avg2 - avg1

        if diff >= 5.0:
            progress_trend = f"Upward trajectory observed (recent average score improved by {diff:.1f}% compared to earlier attempts)."
        elif diff <= -5.0:
            progress_trend = f"Recent attempts show higher difficulty or variance (score shift of {diff:.1f}%)."
        else:
            progress_trend = "Consistent score stability maintained across recent assessment attempts."
    elif len(chronological) == 2:
        diff = chronological[1]["score"] - chronological[0]["score"]
        if diff > 0:
            progress_trend = f"Improvement observed (+{diff:.1f}% compared to previous attempt)."
        elif diff < 0:
            progress_trend = f"Score variance observed ({diff:.1f}% compared to previous attempt)."
        else:
            progress_trend = "Identical score maintained across attempts."

    # Build Descriptive Feedback Messages (Strictly non-evaluative / descriptive)
    feedback_points: list[str] = []

    if completed_items:
        latest = completed_items[0]
        diff_suffix = f" on {latest.get('difficulty')} level" if latest.get("difficulty") else ""
        feedback_points.append(
            f"Your recent score in {latest.get('category', 'English')} was {latest.get('score', 0)}%{diff_suffix}."
        )

    if strongest_cat:
        s_data = category_summaries[strongest_cat]
        feedback_points.append(
            f"Your strongest observed category is {strongest_cat}, with an average score of {s_data['average_score']}% across {s_data['number_of_attempts']} attempt(s)."
        )

    if lowest_cat:
        l_data = category_summaries[lowest_cat]
        feedback_points.append(
            f"Your performance in {lowest_cat} indicates an opportunity for further targeted practice, with an observed average of {l_data['average_score']}%."
        )

    unattempted_cats = [c for c in standard_categories if category_summaries[c]["number_of_attempts"] == 0]
    if unattempted_cats:
        feedback_points.append(
            f"You have not yet attempted the {', '.join(unattempted_cats)} category. Practicing all three categories provides a more balanced self-assessment profile."
        )

    feedback_points.append(f"Progress over time: {progress_trend}")

    return {
        "total_attempts": total_attempts,
        "overall_average_score": overall_avg,
        "overall_best_score": overall_best,
        "overall_latest_score": overall_latest,
        "overall_accuracy": overall_acc,
        "categories": category_summaries,
        "strongest_observed_category": strongest_cat,
        "lower_observed_category": lowest_cat,
        "progress_trend": progress_trend,
        "chronological_attempts": chronological,
        "descriptive_feedback": feedback_points,
        "disclaimer": CERTIFICATION_DISCLAIMER,
    }
