"""
Unit tests for Phase 15: User History and Self-Assessment Summary.
Tests:
- Detailed attempt history retrieval with required fields (date, category, difficulty, score, correct, incorrect, questions).
- Self-assessment summary calculations:
  * Category breakdown (Grammar, Reading, Listening)
  * Average score, number of attempts, latest score, best score, accuracy
  * Identification of strongest observed category and lower observed category
  * Progress over time trajectory detection
  * Descriptive feedback wording (non-certification compliance)
  * Non-certification disclaimer inclusion
- Graceful handling of empty assessment history without division by zero.
"""

import unittest
import tempfile
from pathlib import Path

from database.db import init_db, get_connection
from database.models import Question
from database import queries
from services.history_service import (
    fetch_user_history,
    calculate_self_assessment_summary,
    CERTIFICATION_DISCLAIMER,
)


class TestUserHistoryAndSummary(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_history.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            self.user_id = queries.create_user(conn, "Jane Doe", "jane@historytest.com")
            self.cat_grammar = queries.get_category_by_name(conn, "Grammar")
            self.cat_reading = queries.get_category_by_name(conn, "Reading")
            self.cat_listening = queries.get_category_by_name(conn, "Listening")

    def tearDown(self):
        self.temp_dir.cleanup()

    # ==========================================
    # 1. USER ASSESSMENT HISTORY FIELDS TEST
    # ==========================================

    def test_fetch_user_history_fields(self):
        """Verify fetch_user_history returns all required data fields."""
        with get_connection(self.db_path) as conn:
            # Create completed attempt
            att_id = queries.create_attempt(
                conn=conn,
                user_id=self.user_id,
                category_id=self.cat_grammar.id,
                difficulty="Easy",
                total_questions=10,
            )
            queries.complete_attempt(
                conn=conn,
                attempt_id=att_id,
                correct_answers=9,
                incorrect_answers=1,
                score=90.0,
                duration_seconds=125,
            )

        history = fetch_user_history(self.user_id, db_path=self.db_path)
        self.assertEqual(len(history), 1)

        item = history[0]
        # Required fields according to Phase 15 prompt:
        self.assertIn("date", item)
        self.assertEqual(item["category"], "Grammar")
        self.assertEqual(item["difficulty"], "Easy")
        self.assertEqual(item["score"], 90.0)
        self.assertEqual(item["correct"], 9)
        self.assertEqual(item["incorrect"], 1)
        self.assertEqual(item["number_of_questions"], 10)
        self.assertEqual(item["accuracy"], 90.0)
        self.assertEqual(item["duration"], "2m 5s")
        self.assertTrue(item["is_completed"])

    # ==========================================
    # 2. CATEGORY BREAKDOWN & METRICS TEST
    # ==========================================

    def test_self_assessment_summary_category_breakdown(self):
        """
        Verify calculation of:
        - average score
        - number of attempts
        - latest score
        - best score
        - accuracy
        across Grammar, Reading, and Listening.
        """
        with get_connection(self.db_path) as conn:
            # Grammar Attempt 1: 80%
            att_g1 = queries.create_attempt(conn, self.user_id, self.cat_grammar.id, "Easy", 10)
            queries.complete_attempt(conn, att_g1, 8, 2, 80.0, 100)

            # Grammar Attempt 2: 100% (Latest Grammar)
            att_g2 = queries.create_attempt(conn, self.user_id, self.cat_grammar.id, "Medium", 10)
            queries.complete_attempt(conn, att_g2, 10, 0, 100.0, 150)

            # Reading Attempt 1: 70%
            att_r1 = queries.create_attempt(conn, self.user_id, self.cat_reading.id, "Medium", 10)
            queries.complete_attempt(conn, att_r1, 7, 3, 70.0, 200)

            # Listening Attempt 1: 85%
            att_l1 = queries.create_attempt(conn, self.user_id, self.cat_listening.id, "Easy", 10)
            queries.complete_attempt(conn, att_l1, 8, 2, 80.0, 90)

        history = fetch_user_history(self.user_id, db_path=self.db_path)
        summary = calculate_self_assessment_summary(history)

        self.assertEqual(summary["total_attempts"], 4)

        # Check Grammar Performance Breakdown
        g_data = summary["categories"]["Grammar"]
        self.assertEqual(g_data["number_of_attempts"], 2)
        self.assertEqual(g_data["average_score"], 90.0)  # (80 + 100) / 2
        self.assertEqual(g_data["best_score"], 100.0)
        self.assertEqual(g_data["latest_score"], 100.0)
        self.assertEqual(g_data["accuracy"], 90.0)  # 18/20 = 90%

        # Check Reading Performance Breakdown
        r_data = summary["categories"]["Reading"]
        self.assertEqual(r_data["number_of_attempts"], 1)
        self.assertEqual(r_data["average_score"], 70.0)
        self.assertEqual(r_data["best_score"], 70.0)
        self.assertEqual(r_data["latest_score"], 70.0)
        self.assertEqual(r_data["accuracy"], 70.0)

        # Check Listening Performance Breakdown
        l_data = summary["categories"]["Listening"]
        self.assertEqual(l_data["number_of_attempts"], 1)
        self.assertEqual(l_data["average_score"], 80.0)
        self.assertEqual(l_data["best_score"], 80.0)
        self.assertEqual(l_data["latest_score"], 80.0)

        # Overall summary
        self.assertEqual(summary["overall_best_score"], 100.0)
        self.assertEqual(summary["overall_average_score"], 82.5)  # (80+100+70+80) / 4

    # ==========================================
    # 3. STRONGEST & LOWER OBSERVED CATEGORIES
    # ==========================================

    def test_strongest_and_lower_observed_categories(self):
        """Identify strongest observed category and lower observed category."""
        history_mock = [
            {"category": "Grammar", "score": 92.0, "correct": 9, "number_of_questions": 10, "is_completed": True},
            {"category": "Reading", "score": 68.0, "correct": 7, "number_of_questions": 10, "is_completed": True},
            {"category": "Listening", "score": 84.0, "correct": 8, "number_of_questions": 10, "is_completed": True},
        ]

        summary = calculate_self_assessment_summary(history_mock)
        self.assertEqual(summary["strongest_observed_category"], "Grammar")
        self.assertEqual(summary["lower_observed_category"], "Reading")

    # ==========================================
    # 4. DESCRIPTIVE FEEDBACK & DISCLAIMER
    # ==========================================

    def test_descriptive_feedback_language_and_disclaimer(self):
        """
        Verify descriptive feedback language:
        - Uses 'Your recent score in...'
        - Does NOT make formal proficiency certification claims
        - Strictly includes non-certification disclaimer
        """
        history_mock = [
            {
                "category": "Grammar",
                "difficulty": "Medium",
                "score": 88.0,
                "correct": 9,
                "number_of_questions": 10,
                "is_completed": True,
            },
        ]

        summary = calculate_self_assessment_summary(history_mock)
        feedback = summary["descriptive_feedback"]

        # Check descriptive wording
        found_recent_mention = any("Your recent score in Grammar was 88.0%" in f for f in feedback)
        self.assertTrue(found_recent_mention, "Expected descriptive phrasing 'Your recent score in Grammar was...'")

        # Verify disclaimer
        self.assertIn("not an officially certified", summary["disclaimer"])
        self.assertEqual(summary["disclaimer"], CERTIFICATION_DISCLAIMER)

    # ==========================================
    # 5. PROGRESS OVER TIME TRAJECTORY
    # ==========================================

    def test_progress_over_time_trend(self):
        """Verify progress trend evaluation across multiple attempts."""
        history_mock = [
            {"category": "Grammar", "score": 95.0, "correct": 10, "number_of_questions": 10, "is_completed": True},
            {"category": "Grammar", "score": 90.0, "correct": 9, "number_of_questions": 10, "is_completed": True},
            {"category": "Grammar", "score": 75.0, "correct": 7, "number_of_questions": 10, "is_completed": True},
            {"category": "Grammar", "score": 70.0, "correct": 7, "number_of_questions": 10, "is_completed": True},
        ]

        summary = calculate_self_assessment_summary(history_mock)
        self.assertIn("Upward trajectory observed", summary["progress_trend"])

    # ==========================================
    # 6. EMPTY HISTORY HANDLING
    # ==========================================

    def test_empty_history_handling(self):
        """New participant with zero attempts must receive safe defaults without crashing."""
        summary = calculate_self_assessment_summary([])
        self.assertEqual(summary["total_attempts"], 0)
        self.assertEqual(summary["overall_average_score"], 0.0)
        self.assertEqual(summary["overall_best_score"], 0.0)
        self.assertIsNone(summary["overall_latest_score"])
        self.assertIsNone(summary["strongest_observed_category"])
        self.assertIsNone(summary["lower_observed_category"])
        self.assertEqual(len(summary["categories"]), 3)
        for cat in ["Grammar", "Reading", "Listening"]:
            self.assertEqual(summary["categories"][cat]["number_of_attempts"], 0)


if __name__ == "__main__":
    unittest.main()
