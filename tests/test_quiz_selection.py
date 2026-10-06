"""
Unit tests for Phase 4: Test Category and Difficulty Selection Flow.
"""

import unittest
from unittest.mock import patch

from services.quiz_engine import (
    prepare_quiz_session,
    get_quiz_session,
    is_quiz_selection_ready,
    reset_quiz_session,
    SESSION_KEY_CATEGORY,
    SESSION_KEY_DIFFICULTY,
    SESSION_KEY_ATTEMPT_ID,
    SESSION_KEY_QUESTIONS,
    SESSION_KEY_QUESTION_INDEX,
)
from services.user_service import (
    is_user_authenticated,
    set_active_user_session,
    clear_active_user_session,
)
from database.models import User
from config.constants import CATEGORIES, DIFFICULTIES


class TestQuizSelectionFlow(unittest.TestCase):
    def test_categories_and_difficulties_constants(self):
        """Verify the 3 standard categories and 3 levels are defined."""
        self.assertListEqual(CATEGORIES, ["Grammar", "Reading", "Listening"])
        self.assertListEqual(DIFFICULTIES, ["Easy", "Medium", "Hard"])

    def test_unauthenticated_identity_guard(self):
        """Verify unauthenticated user cannot start test selection."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            self.assertFalse(is_user_authenticated())

            # Setting active user authenticates the session
            user = User(id=1, name="John Doe", email="john@example.com")
            set_active_user_session(user)
            self.assertTrue(is_user_authenticated())

            # Clearing resets authentication
            clear_active_user_session()
            self.assertFalse(is_user_authenticated())

    def test_prepare_quiz_session_for_any_category_first(self):
        """Verify user is free to select any category first (e.g. Listening first, then Reading, then Grammar)."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            # 1. User picks Listening with Hard
            success = prepare_quiz_session("Listening", "Hard", category_id=3)
            self.assertTrue(success)
            self.assertTrue(is_quiz_selection_ready())

            state = get_quiz_session()
            self.assertIsNotNone(state)
            self.assertEqual(state["category"], "Listening")
            self.assertEqual(state["difficulty"], "Hard")
            self.assertEqual(state["category_id"], 3)
            self.assertIsNone(state["attempt_id"])
            self.assertEqual(state["selected_questions"], [])
            self.assertEqual(state["current_question_index"], 0)

            # 2. User switches to Reading with Easy
            success = prepare_quiz_session("Reading", "Easy", category_id=2)
            self.assertTrue(success)
            state = get_quiz_session()
            self.assertEqual(state["category"], "Reading")
            self.assertEqual(state["difficulty"], "Easy")

            # 3. User switches to Grammar with Medium
            success = prepare_quiz_session("Grammar", "Medium", category_id=1)
            self.assertTrue(success)
            state = get_quiz_session()
            self.assertEqual(state["category"], "Grammar")
            self.assertEqual(state["difficulty"], "Medium")

    def test_invalid_category_or_difficulty_rejected(self):
        """Invalid categories or difficulties must return False and not set state."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            self.assertFalse(prepare_quiz_session("Speaking", "Easy"))
            self.assertFalse(prepare_quiz_session("Grammar", "UltraHard"))
            self.assertFalse(is_quiz_selection_ready())
            self.assertIsNone(get_quiz_session())

    def test_reset_quiz_session(self):
        """Resetting quiz selection clears category and difficulty state."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            prepare_quiz_session("Grammar", "Easy")
            self.assertTrue(is_quiz_selection_ready())

            reset_quiz_session()
            self.assertFalse(is_quiz_selection_ready())
            self.assertIsNone(get_quiz_session())


if __name__ == "__main__":
    unittest.main()
