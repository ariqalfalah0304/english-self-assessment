"""
Unit tests for Phase 7: Reading Module.
Tests passage creation and retrieval, multiple questions per passage,
reading question selection across all difficulties (Easy, Medium, Hard),
scoring, and SQLite attempt saving.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from database.db import init_db, get_connection, create_connection
from database.models import Passage, Question
from database import queries
from services.quiz_engine import (
    start_quiz_attempt,
    submit_current_answer,
    complete_current_attempt,
    get_quiz_session,
)
from services.scoring_service import get_attempt_summary


class TestReadingModule(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_reading.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            self.user_id = queries.create_user(conn, "Reading Student", "reader@example.com")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_passage_creation_and_retrieval(self):
        """Test inserting and retrieving a reading passage from SQLite."""
        with get_connection(self.db_path) as conn:
            reading_cat = queries.get_category_by_name(conn, "Reading")
            self.assertIsNotNone(reading_cat)

            passage_id = queries.create_passage(
                conn=conn,
                title="The Great Coral Reef Ecosystem",
                passage_text="Coral reefs are diverse underwater ecosystems held together by calcium carbonate structures.",
                category_id=reading_cat.id,
            )
            self.assertIsInstance(passage_id, int)

            retrieved = queries.get_passage_by_id(conn, passage_id)
            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.title, "The Great Coral Reef Ecosystem")
            self.assertIn("underwater ecosystems", retrieved.passage_text)
            self.assertEqual(retrieved.category_id, reading_cat.id)

    def test_multiple_questions_associated_with_single_passage(self):
        """Verify multiple questions of different types can be linked to a single passage."""
        with get_connection(self.db_path) as conn:
            reading_cat = queries.get_category_by_name(conn, "Reading")

            passage_id = queries.create_passage(
                conn=conn,
                title="Microplastic Pollution",
                passage_text="Microplastics are tiny plastic particles less than five millimeters in diameter.",
                category_id=reading_cat.id,
            )

            # Insert questions with various types
            question_types = ["Main Idea", "Detail", "Vocabulary", "Inference", "Author's Purpose"]
            created_ids = []

            for q_type in question_types:
                q = Question(
                    category_id=reading_cat.id,
                    passage_id=passage_id,
                    subtopic="Environmental Science",
                    question_type=q_type,
                    question_text=f"Sample question testing {q_type}",
                    option_a="Choice A",
                    option_b="Choice B",
                    option_c="Choice C",
                    option_d="Choice D",
                    correct_answer="A",
                    explanation=f"Explanation for {q_type}",
                    difficulty="Medium",
                    status="Active",
                )
                qid = queries.create_question(conn, q)
                created_ids.append(qid)

            self.assertEqual(len(created_ids), 5)

            # Verify all questions point to the same passage
            for qid in created_ids:
                saved_q = queries.get_question_by_id(conn, qid)
                self.assertIsNotNone(saved_q)
                self.assertEqual(saved_q.passage_id, passage_id)
                self.assertIn(saved_q.question_type, question_types)

    def test_reading_question_selection_across_all_difficulties(self):
        """
        Verify Reading + Easy, Reading + Medium, and Reading + Hard selection,
        and confirm passage text/title is attached to questions in session state.
        """
        for diff in ["Easy", "Medium", "Hard"]:
            mock_session = {}
            with patch("streamlit.session_state", mock_session):
                success, attempt, questions, notice = start_quiz_attempt(
                    user_id=self.user_id,
                    category_name="Reading",
                    difficulty=diff,
                    num_questions=10,
                    db_path=self.db_path,
                )

                self.assertTrue(success, f"Reading + {diff} failed to initialize")
                self.assertIsNotNone(attempt)
                self.assertGreater(len(questions), 0)

                # Verify each question belongs to Reading and matches the requested difficulty
                for q in questions:
                    self.assertEqual(q.difficulty, diff)
                    self.assertIsNotNone(q.passage_id, "Reading question must have an associated passage_id")

                # Verify session state has attached passage title and body
                state = get_quiz_session()
                self.assertIsNotNone(state)
                self.assertEqual(state["category"], "Reading")
                self.assertEqual(state["difficulty"], diff)

                first_q = state["selected_questions"][0]
                self.assertIn("passage_title", first_q)
                self.assertIn("passage_text", first_q)
                self.assertTrue(len(first_q["passage_text"]) > 50)

    def test_reading_scoring_and_attempt_saving(self):
        """Test full assessment workflow for Reading including answer submission, scoring, and SQLite persistence."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            start_quiz_attempt(
                user_id=self.user_id,
                category_name="Reading",
                difficulty="Easy",
                num_questions=4,
                db_path=self.db_path,
            )

            state = get_quiz_session()
            questions = state["selected_questions"]
            total_count = len(questions)

            # Submit 3 correct answers and 1 wrong answer (if total >= 4)
            for idx, q in enumerate(questions):
                if idx < 3:
                    submit_current_answer(q["correct_answer"], db_path=self.db_path)
                else:
                    wrong = "B" if q["correct_answer"] != "B" else "C"
                    submit_current_answer(wrong, db_path=self.db_path)

            completed = complete_current_attempt(db_path=self.db_path)
            self.assertIsNotNone(completed)
            self.assertEqual(completed.category_id, 2)  # Reading ID = 2
            self.assertEqual(completed.difficulty, "Easy")
            self.assertEqual(completed.total_questions, total_count)
            self.assertGreaterEqual(completed.correct_answers, 1)

            # Check database persistence
            with get_connection(self.db_path) as conn:
                summary = get_attempt_summary(conn, completed.id)

            self.assertIsNotNone(summary)
            self.assertEqual(summary["category"], "Reading")
            self.assertEqual(summary["difficulty"], "Easy")
            self.assertIsNotNone(summary["completed_at"])
            self.assertEqual(summary["answers_count"], total_count)


if __name__ == "__main__":
    unittest.main()
