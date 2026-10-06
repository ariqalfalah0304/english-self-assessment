"""
Unit tests for Phase 5: Grammar Quiz Engine Lifecycle.
Tests question selection, difficulty filtering, duplicate prevention,
answer evaluation, pointer movement, and attempt finalization.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from database.db import init_db, get_connection, create_connection
from database import queries
from services.quiz_engine import (
    start_quiz_attempt,
    submit_current_answer,
    move_to_next_question,
    complete_current_attempt,
    get_quiz_session,
    SESSION_KEY_QUESTION_INDEX,
    SESSION_KEY_CORRECT_COUNT,
    SESSION_KEY_INCORRECT_COUNT,
)


class TestGrammarQuizEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_quiz_engine.db"
        init_db(self.db_path)

        # Seed test user using get_connection context manager to ensure commit
        with get_connection(self.db_path) as conn:
            self.user_id = queries.create_user(conn, "Quiz Tester", "tester@grammar.com")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_quiz_attempt_with_difficulty_filtering_and_no_duplicates(self):
        """Test starting Grammar attempt selects matching difficulty with zero duplicate questions."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            success, attempt, questions, notice = start_quiz_attempt(
                user_id=self.user_id,
                category_name="Grammar",
                difficulty="Easy",
                num_questions=5,
                db_path=self.db_path,
            )

            self.assertTrue(success)
            self.assertIsNotNone(attempt)
            self.assertEqual(len(questions), 5)

            # Check that all questions match Grammar & Easy
            for q in questions:
                self.assertEqual(q.difficulty, "Easy")
                self.assertEqual(q.status, "Active")

            # Check for zero duplicates
            question_ids = [q.id for q in questions]
            self.assertEqual(len(question_ids), len(set(question_ids)), "Questions must not have duplicates")

            # Verify session state initialized
            state = get_quiz_session()
            self.assertIsNotNone(state)
            self.assertEqual(state["category"], "Grammar")
            self.assertEqual(state["difficulty"], "Easy")
            self.assertEqual(state["current_question_index"], 0)
            self.assertEqual(len(state["selected_questions"]), 5)

    def test_graceful_handling_when_fewer_questions_than_requested(self):
        """If fewer questions exist than requested, gracefully use available questions without crashing."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            # Request 100 questions when database sample has fewer
            success, attempt, questions, notice = start_quiz_attempt(
                user_id=self.user_id,
                category_name="Grammar",
                difficulty="Hard",
                num_questions=100,
                db_path=self.db_path,
            )

            self.assertTrue(success)
            self.assertIsNotNone(attempt)
            self.assertGreater(len(questions), 0)
            self.assertLess(len(questions), 100)
            self.assertIn("Only", notice)  # User notice provided

    def test_submit_answer_and_progression_lifecycle(self):
        """Test answer submission, evaluation, session counters, SQLite answer record, and pointer advancement."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            start_quiz_attempt(
                user_id=self.user_id,
                category_name="Grammar",
                difficulty="Easy",
                num_questions=2,
                db_path=self.db_path,
            )

            state = get_quiz_session()
            q1 = state["selected_questions"][0]
            q2 = state["selected_questions"][1]

            # 1. Submit CORRECT answer for Q1
            correct_ans = q1["correct_answer"]
            ok, feedback = submit_current_answer(correct_ans, db_path=self.db_path)
            self.assertTrue(ok)
            self.assertTrue(feedback["is_correct"])
            self.assertEqual(feedback["user_answer"], correct_ans)
            self.assertEqual(mock_session[SESSION_KEY_CORRECT_COUNT], 1)
            self.assertEqual(mock_session[SESSION_KEY_INCORRECT_COUNT], 0)

            # Move to next question
            has_next = move_to_next_question()
            self.assertTrue(has_next)
            self.assertEqual(mock_session[SESSION_KEY_QUESTION_INDEX], 1)

            # 2. Submit INCORRECT answer for Q2
            wrong_ans = "B" if q2["correct_answer"] != "B" else "C"
            ok, feedback2 = submit_current_answer(wrong_ans, db_path=self.db_path)
            self.assertTrue(ok)
            self.assertFalse(feedback2["is_correct"])
            self.assertEqual(feedback2["user_answer"], wrong_ans)
            self.assertEqual(mock_session[SESSION_KEY_CORRECT_COUNT], 1)
            self.assertEqual(mock_session[SESSION_KEY_INCORRECT_COUNT], 1)

            # 3. Final question: move_to_next_question returns False
            has_next = move_to_next_question()
            self.assertFalse(has_next)

            # 4. Finalize attempt: 1 correct out of 2 = 50.0%
            final_attempt = complete_current_attempt(db_path=self.db_path)
            self.assertIsNotNone(final_attempt)
            self.assertEqual(final_attempt.total_questions, 2)
            self.assertEqual(final_attempt.correct_answers, 1)
            self.assertEqual(final_attempt.incorrect_answers, 1)
            self.assertEqual(final_attempt.score, 50.0)

            # 5. Verify answers stored in SQLite database
            with get_connection(self.db_path) as conn:
                db_answers = queries.get_answers_by_attempt(conn, final_attempt.id)

            self.assertEqual(len(db_answers), 2)
            self.assertEqual(db_answers[0].user_answer, correct_ans)
            self.assertEqual(db_answers[0].is_correct, 1)
            self.assertEqual(db_answers[1].user_answer, wrong_ans)
            self.assertEqual(db_answers[1].is_correct, 0)


if __name__ == "__main__":
    unittest.main()
