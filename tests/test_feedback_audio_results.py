"""
Unit tests for Phase 6: Instant Feedback, Audio Handling, and Result Lifecycle.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from database.db import init_db, get_connection, create_connection
from database import queries
from services.quiz_engine import (
    start_quiz_attempt,
    submit_current_answer,
    complete_current_attempt,
    restart_with_difficulty,
    get_quiz_session,
    SESSION_KEY_FEEDBACK,
    SESSION_KEY_QUESTION_ANSWERED,
)
from services.scoring_service import get_attempt_summary
from utils.audio import (
    get_feedback_audio_path,
    render_feedback_audio,
    AUDIO_GOOD_JOB_NAME,
    AUDIO_SORRY_TRY_AGAIN_NAME,
)


class TestFeedbackAudioAndResults(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_feedback.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            self.user_id = queries.create_user(conn, "Feedback Tester", "feedback@test.com")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_audio_paths_and_missing_asset_guard(self):
        """Audio utility must resolve correct paths and gracefully handle missing assets without crashing."""
        correct_audio = get_feedback_audio_path(True)
        self.assertTrue(str(correct_audio).endswith(AUDIO_GOOD_JOB_NAME))

        incorrect_audio = get_feedback_audio_path(False)
        self.assertTrue(str(incorrect_audio).endswith(AUDIO_SORRY_TRY_AGAIN_NAME))

        # Missing audio file test: render_feedback_audio must not raise an exception
        try:
            render_feedback_audio(True)
            render_feedback_audio(False)
        except Exception as e:
            self.fail(f"render_feedback_audio crashed when audio asset was missing: {e}")

    def test_instant_feedback_messages_and_state_preservation(self):
        """
        Verify that submitting an answer produces the exact required messages:
        'Good Job!' for correct, 'Sorry, try again.' for incorrect,
        and preserves complete quiz state without loss.
        """
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            start_quiz_attempt(
                user_id=self.user_id,
                category_name="Grammar",
                difficulty="Easy",
                num_questions=3,
                db_path=self.db_path,
            )

            state = get_quiz_session()
            self.assertEqual(len(state["selected_questions"]), 3)
            q0 = state["selected_questions"][0]

            # 1. Test CORRECT answer feedback
            correct_ans = q0["correct_answer"]
            ok, feedback = submit_current_answer(correct_ans, db_path=self.db_path)
            self.assertTrue(ok)
            self.assertTrue(feedback["is_correct"])
            self.assertEqual(feedback["message"], "Good Job!")
            self.assertEqual(feedback["correct_answer"], correct_ans)
            self.assertEqual(feedback["user_answer"], correct_ans)
            self.assertEqual(feedback["explanation"], q0["explanation"])

            # Verify state was PRESERVED after answer submission
            self.assertTrue(mock_session[SESSION_KEY_QUESTION_ANSWERED])
            self.assertIsNotNone(mock_session[SESSION_KEY_FEEDBACK])
            self.assertEqual(len(mock_session["selected_questions"]), 3)
            self.assertEqual(mock_session["current_question_index"], 0)
            self.assertIsNotNone(mock_session["current_attempt_id"])

    def test_instant_feedback_negative_message(self):
        """Test negative feedback message 'Sorry, try again.' for incorrect answer."""
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
            q0 = state["selected_questions"][0]
            wrong_ans = "B" if q0["correct_answer"] != "B" else "C"

            ok, feedback = submit_current_answer(wrong_ans, db_path=self.db_path)
            self.assertTrue(ok)
            self.assertFalse(feedback["is_correct"])
            self.assertEqual(feedback["message"], "Sorry, try again.")
            self.assertEqual(feedback["user_answer"], wrong_ans)
            self.assertEqual(feedback["correct_answer"], q0["correct_answer"])

    def test_result_page_data_and_completion_timing(self):
        """
        Verify that completing an attempt persists duration_seconds,
        calculates final score percentage, and provides full summary data.
        """
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
            q0 = state["selected_questions"][0]
            # Submit 1 correct
            submit_current_answer(q0["correct_answer"], db_path=self.db_path)

            completed = complete_current_attempt(db_path=self.db_path)
            self.assertIsNotNone(completed)
            self.assertEqual(completed.total_questions, 2)
            self.assertEqual(completed.correct_answers, 1)
            self.assertEqual(completed.score, 50.0)
            self.assertIsNotNone(completed.duration_seconds)
            self.assertGreaterEqual(completed.duration_seconds, 1)

            # Check database persistence
            with get_connection(self.db_path) as conn:
                summary = get_attempt_summary(conn, completed.id)

            self.assertIsNotNone(summary)
            self.assertEqual(summary["category"], "Grammar")
            self.assertEqual(summary["difficulty"], "Easy")
            self.assertEqual(summary["score"], 50.0)
            self.assertEqual(summary["total_questions"], 2)
            self.assertEqual(summary["correct_answers"], 1)
            self.assertEqual(summary["incorrect_answers"], 0)
            self.assertIsNotNone(summary["duration_seconds"])

    def test_restart_with_difficulty_helpers(self):
        """Verify action buttons for Try Easy, Try Medium, Try Hard."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            start_quiz_attempt(
                user_id=self.user_id,
                category_name="Grammar",
                difficulty="Medium",
                num_questions=2,
                db_path=self.db_path,
            )

            # Try Easy
            self.assertTrue(restart_with_difficulty("Easy"))
            self.assertEqual(mock_session["current_difficulty"], "Easy")
            self.assertIsNone(mock_session["current_attempt_id"])
            self.assertEqual(mock_session["selected_questions"], [])

            # Try Hard
            self.assertTrue(restart_with_difficulty("Hard"))
            self.assertEqual(mock_session["current_difficulty"], "Hard")


if __name__ == "__main__":
    unittest.main()
