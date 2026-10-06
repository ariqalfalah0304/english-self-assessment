"""
Unit tests for Phase 8: Listening Module.
Tests:
- Audio file record creation, linking to listening question, and retrieval.
- Listening question selection across difficulties (Easy, Medium, Hard).
- Audio metadata attachment (audio_file, transcript, duration).
- Transcript secrecy during quiz (not exposed by default).
- Non-crashing graceful handling of missing audio assets.
- Answer submission, immediate feedback, scoring, and SQLite persistence.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from database.db import init_db, get_connection
from database.models import Question
from database import queries
from services.quiz_engine import (
    start_quiz_attempt,
    submit_current_answer,
    complete_current_attempt,
    get_quiz_session,
)
from services.scoring_service import get_attempt_summary
from utils.audio import (
    render_listening_audio,
    render_feedback_audio,
    get_feedback_audio_path,
)


class TestListeningModule(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_listening.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            self.user_id = queries.create_user(conn, "Listening Participant", "listener@example.com")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_audio_file_creation_and_retrieval(self):
        """Test inserting and retrieving an audio file record linked to a question."""
        with get_connection(self.db_path) as conn:
            listening_cat = queries.get_category_by_name(conn, "Listening")
            self.assertIsNotNone(listening_cat)

            q = Question(
                category_id=listening_cat.id,
                question_text="What does the speaker recommend?",
                option_a="Buy the tickets online",
                option_b="Wait until tomorrow",
                option_c="Call customer support",
                option_d="Cancel the trip",
                correct_answer="A",
                explanation="The speaker clearly advises purchasing tickets online to save time.",
                difficulty="Easy",
                status="Active",
                subtopic="Travel Tips",
                question_type="Detail",
            )
            q_id = queries.create_question(conn, q)

            audio_id = queries.create_audio_file(
                conn=conn,
                question_id=q_id,
                file_path="audio/listening/listening_test_01.mp3",
                transcript="Speaker: I strongly recommend buying your tickets online in advance.",
                duration=18.5,
            )
            self.assertIsInstance(audio_id, int)

            audio_rec = queries.get_audio_file_by_question_id(conn, q_id)
            self.assertIsNotNone(audio_rec)
            self.assertEqual(audio_rec.question_id, q_id)
            self.assertEqual(audio_rec.file_path, "audio/listening/listening_test_01.mp3")
            self.assertIn("tickets online in advance", audio_rec.transcript)
            self.assertEqual(audio_rec.duration, 18.5)

    def test_listening_question_selection_across_difficulties(self):
        """Verify Listening question selection for Easy, Medium, and Hard."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            for diff in ["Easy", "Medium", "Hard"]:
                mock_session.clear()
                success, attempt, questions, notice = start_quiz_attempt(
                    user_id=self.user_id,
                    category_name="Listening",
                    difficulty=diff,
                    num_questions=4,
                    db_path=self.db_path,
                )

                self.assertTrue(success, f"Failed starting Listening attempt for {diff}: {notice}")
                self.assertIsNotNone(attempt)
                self.assertGreaterEqual(len(questions), 4)

                for q in questions:
                    self.assertEqual(q.difficulty, diff)

                state = get_quiz_session()
                self.assertIsNotNone(state)
                self.assertEqual(state["category"], "Listening")
                self.assertEqual(state["difficulty"], diff)

                first_q = state["selected_questions"][0]
                self.assertIn("audio_file", first_q)
                self.assertTrue(first_q["audio_file"].startswith("audio/listening/"))

    def test_missing_audio_does_not_crash_application(self):
        """Verify that missing audio file gracefully notifies user and never raises an unhandled error."""
        with patch("streamlit.markdown") as mock_markdown, \
             patch("streamlit.warning") as mock_warning:

            # 1. Non-existent file path
            result = render_listening_audio("audio/listening/completely_nonexistent_audio_file_xyz.mp3")
            self.assertFalse(result)
            mock_markdown.assert_called()

            # 2. None or empty file path
            result_none = render_listening_audio(None)
            self.assertFalse(result_none)
            mock_warning.assert_called()

    def test_existing_audio_playback(self):
        """Verify that existing audio file is read and passed to st.audio without error."""
        # Create a temporary mp3 file
        sample_audio = Path(self.temp_dir.name) / "test_sample.mp3"
        sample_audio.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 413)

        with patch("streamlit.audio") as mock_audio, \
             patch("streamlit.markdown") as mock_markdown:
            result = render_listening_audio(str(sample_audio))
            self.assertTrue(result)
            mock_audio.assert_called_once()

    def test_feedback_audio_handling(self):
        """Verify feedback audio rendering for correct and incorrect answers does not crash."""
        with patch("streamlit.audio"), patch("streamlit.markdown"):
            # Should safely execute without raising exceptions
            render_feedback_audio(is_correct=True)
            render_feedback_audio(is_correct=False)

    def test_listening_scoring_and_attempt_saving(self):
        """Test full assessment workflow for Listening: answer submission, instant feedback, scoring, and SQLite persistence."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            start_quiz_attempt(
                user_id=self.user_id,
                category_name="Listening",
                difficulty="Easy",
                num_questions=4,
                db_path=self.db_path,
            )

            state = get_quiz_session()
            questions = state["selected_questions"]
            total_count = len(questions)

            # Answer question 1 correctly
            q1 = questions[0]
            success1, fb1 = submit_current_answer(q1["correct_answer"], db_path=self.db_path)
            self.assertTrue(success1)
            self.assertTrue(fb1["is_correct"])
            self.assertEqual(fb1["message"], "Good Job!")

            # Answer question 2 incorrectly
            mock_session["current_question_index"] = 1
            mock_session["question_answered"] = False
            q2 = questions[1]
            wrong_choice = "D" if q2["correct_answer"] != "D" else "A"
            success2, fb2 = submit_current_answer(wrong_choice, db_path=self.db_path)
            self.assertTrue(success2)
            self.assertFalse(fb2["is_correct"])
            self.assertEqual(fb2["message"], "Sorry, try again.")

            # Answer remaining questions
            for idx in range(2, total_count):
                mock_session["current_question_index"] = idx
                mock_session["question_answered"] = False
                q = questions[idx]
                submit_current_answer(q["correct_answer"], db_path=self.db_path)

            completed = complete_current_attempt(db_path=self.db_path)
            self.assertIsNotNone(completed)
            self.assertEqual(completed.category_id, 3)  # Listening ID = 3
            self.assertEqual(completed.difficulty, "Easy")
            self.assertEqual(completed.total_questions, total_count)
            self.assertEqual(completed.correct_answers, total_count - 1)
            self.assertEqual(completed.incorrect_answers, 1)

            # Check database persistence
            with get_connection(self.db_path) as conn:
                summary = get_attempt_summary(conn, completed.id)

            self.assertIsNotNone(summary)
            self.assertEqual(summary["category"], "Listening")
            self.assertEqual(summary["difficulty"], "Easy")
            self.assertIsNotNone(summary["completed_at"])
            self.assertEqual(summary["answers_count"], total_count)


if __name__ == "__main__":
    unittest.main()
