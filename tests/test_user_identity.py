"""
Unit tests for Phase 3: User Identity, Email Validation, SQLite Storage, and Session State.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from database.db import init_db, create_connection
from database.models import User
from utils.validators import (
    validate_name,
    validate_email_address,
    validate_identity_form,
)
from services.user_service import (
    process_user_identity,
    set_active_user_session,
    get_active_user_session,
    is_user_authenticated,
    clear_active_user_session,
    SESSION_KEY_USER_ID,
    SESSION_KEY_USER_NAME,
    SESSION_KEY_USER_EMAIL,
)


class TestUserIdentityAndValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_identity.db"
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    # 1. Valid Identity
    def test_valid_identity(self):
        """Test validation of correct name and email."""
        is_valid, errors, norm_email = validate_identity_form("Sarah Connor", "sarah@cyberdyne.org")
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertEqual(norm_email, "sarah@cyberdyne.org")

    # 2. Missing Name
    def test_missing_name(self):
        """Test rejection of empty or whitespace-only name."""
        # Empty string
        valid, msg = validate_name("")
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())

        # Whitespace
        valid, msg = validate_name("   ")
        self.assertFalse(valid)
        self.assertIn("required", msg.lower())

        # Single character
        valid, msg = validate_name("A")
        self.assertFalse(valid)
        self.assertIn("at least 2 characters", msg.lower())

        # In full form
        is_valid, errors, _ = validate_identity_form("", "valid@example.com")
        self.assertFalse(is_valid)
        self.assertIn("name", errors)

    # 3. Invalid Email
    def test_invalid_email(self):
        """Test rejection of malformed email addresses using email-validator."""
        invalid_emails = [
            "",
            "plainaddress",
            "@missinguser.com",
            "missingdomain@",
            "user@.com",
            "user@domain..com",
            "spaces in@domain.com",
        ]
        for bad_email in invalid_emails:
            valid, msg, norm = validate_email_address(bad_email)
            self.assertFalse(valid, f"Email '{bad_email}' should be marked invalid")
            self.assertTrue(len(msg) > 0)
            self.assertIsNone(norm)

            is_valid, errors, _ = validate_identity_form("Valid Name", bad_email)
            self.assertFalse(is_valid)
            self.assertIn("email", errors)

    # 4. Successful SQLite Insertion
    def test_successful_sqlite_insertion(self):
        """Test that valid identity submission inserts and retrieves user from SQLite."""
        success, user, errors = process_user_identity(
            name="Alice Smith",
            email="Alice.Smith@University.edu",
            institution="Oxford University",
            program="Linguistics",
            db_path=self.db_path,
        )
        self.assertTrue(success)
        self.assertEqual(len(errors), 0)
        self.assertIsNotNone(user)
        self.assertIsInstance(user.id, int)
        self.assertEqual(user.name, "Alice Smith")
        self.assertEqual(user.email, "alice.smith@university.edu")  # Normalized lowercase
        self.assertEqual(user.institution, "Oxford University")
        self.assertEqual(user.program, "Linguistics")

        # Verify directly in SQLite connection
        conn = create_connection(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?;", (user.id,))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Alice Smith")
        self.assertEqual(row["email"], "alice.smith@university.edu")

    # 5. Handling Existing / Repeated Email Gracefully
    def test_reused_email_handled_safely(self):
        """Submitting with an existing email should retrieve the existing user without duplicates."""
        success1, user1, _ = process_user_identity(
            name="Bob Brown",
            email="bob@example.com",
            db_path=self.db_path,
        )
        self.assertTrue(success1)

        # Same email entered again
        success2, user2, _ = process_user_identity(
            name="Bob Brown",
            email="bob@example.com",
            db_path=self.db_path,
        )
        self.assertTrue(success2)
        self.assertEqual(user1.id, user2.id)

    # 6. Session State Behavior
    def test_session_state_behavior(self):
        """Test session state helpers for storing, retrieving, and clearing active user."""
        test_session_dict = {}

        with patch("streamlit.session_state", test_session_dict):
            # Initially not authenticated
            self.assertFalse(is_user_authenticated())
            self.assertIsNone(get_active_user_session())

            # Store user in session
            mock_user = User(
                id=42,
                name="David Clark",
                email="david@example.com",
                institution="Tech Institute",
                program="Computer Science",
            )
            set_active_user_session(mock_user)

            # Verify session state values
            self.assertTrue(is_user_authenticated())
            session_data = get_active_user_session()
            self.assertIsNotNone(session_data)
            self.assertEqual(session_data["id"], 42)
            self.assertEqual(session_data["name"], "David Clark")
            self.assertEqual(session_data["email"], "david@example.com")
            self.assertEqual(session_data["institution"], "Tech Institute")
            self.assertEqual(session_data["program"], "Computer Science")

            # Clear session
            clear_active_user_session()
            self.assertFalse(is_user_authenticated())
            self.assertIsNone(get_active_user_session())

    def test_delete_user_account(self):
        """Test deleting a participant user account permanently from SQLite."""
        from services.admin_dashboard_service import delete_user_account
        from database.queries import get_user_by_id

        success, user, _ = process_user_identity(
            name="Delete Me",
            email="deleteme@example.com",
            db_path=self.db_path,
        )
        self.assertTrue(success)
        self.assertIsNotNone(user)

        del_ok = delete_user_account(user.id, db_path=self.db_path)
        self.assertTrue(del_ok)

        conn = create_connection(self.db_path)
        u_check = get_user_by_id(conn, user.id)
        conn.close()
        self.assertIsNone(u_check)


if __name__ == "__main__":
    unittest.main()
