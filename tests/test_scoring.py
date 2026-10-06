"""
Unit tests for Phase 5: Scoring Service & Evaluation.
"""

import unittest
import tempfile
from pathlib import Path

from database.db import init_db, create_connection
from database import queries
from services.scoring_service import (
    calculate_score,
    calculate_accuracy,
    calculate_duration_seconds,
    finalize_attempt,
    get_attempt_summary,
)


class TestScoringService(unittest.TestCase):
    def test_calculate_score(self):
        """Test percentage score calculations."""
        # 17 out of 20 = 85.0%
        self.assertEqual(calculate_score(17, 20), 85.0)

        # 20 out of 20 = 100.0%
        self.assertEqual(calculate_score(20, 20), 100.0)

        # 0 out of 20 = 0.0%
        self.assertEqual(calculate_score(0, 20), 0.0)

        # 1 out of 3 = 33.33%
        self.assertEqual(calculate_score(1, 3), 33.33)

        # Zero total questions safety
        self.assertEqual(calculate_score(0, 0), 0.0)

    def test_calculate_accuracy(self):
        """Test accuracy calculation over answered items."""
        self.assertEqual(calculate_accuracy(8, 10), 80.0)
        self.assertEqual(calculate_accuracy(0, 5), 0.0)
        self.assertEqual(calculate_accuracy(0, 0), 0.0)

    def test_calculate_duration_seconds(self):
        """Test calculation of duration between timestamps."""
        t0 = "2026-09-28 10:00:00"
        t1 = "2026-09-28 10:05:30"
        self.assertEqual(calculate_duration_seconds(t0, t1), 330)

        # None values handling
        self.assertIsNone(calculate_duration_seconds(None, t1))
        self.assertIsNone(calculate_duration_seconds(t0, None))

    def test_finalize_attempt_in_database(self):
        """Test persisting finalized attempt score to SQLite."""
        temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(temp_dir.name) / "test_score.db"
        init_db(db_path)
        conn = create_connection(db_path)

        user_id = queries.create_user(conn, "Test Student", "student@test.com")
        grammar_cat = queries.get_category_by_name(conn, "Grammar")
        attempt_id = queries.create_attempt(
            conn=conn,
            user_id=user_id,
            category_id=grammar_cat.id,
            difficulty="Medium",
            total_questions=20,
        )

        # Finalize attempt with 16 correct answers
        finalized = finalize_attempt(
            conn=conn,
            attempt_id=attempt_id,
            total_questions=20,
            correct_answers=16,
            incorrect_answers=4,
            duration_seconds=300,
        )

        self.assertEqual(finalized.score, 80.0)
        self.assertEqual(finalized.correct_answers, 16)
        self.assertEqual(finalized.incorrect_answers, 4)
        self.assertEqual(finalized.duration_seconds, 300)
        self.assertIsNotNone(finalized.completed_at)

        # Verify summary
        summary = get_attempt_summary(conn, attempt_id)
        self.assertIsNotNone(summary)
        self.assertEqual(summary["score"], 80.0)
        self.assertEqual(summary["total_questions"], 20)

        conn.close()
        temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
