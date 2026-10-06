"""
Unit tests for Phase 9: Admin Authentication & Route Protection.
Tests:
- Bcrypt password hashing, salting, and verification.
- Password and username credential format constraints.
- Admin account creation and database persistence (no plaintext passwords).
- Admin authentication (valid, invalid password, non-existent user).
- Session state management (login, active state, logout).
- Role verification (admin vs superadmin).
- Unauthorized access protection guards (require_admin_auth).
- Safe initial admin setup utility.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from database.db import init_db, get_connection
from database.models import Admin
from database import queries
from services.admin_service import (
    hash_password,
    verify_password,
    validate_admin_credentials_format,
    create_admin_account,
    authenticate_admin,
    login_admin_session,
    logout_admin_session,
    is_admin_authenticated,
    get_active_admin_session,
    check_admin_role,
    require_admin_auth,
    has_any_admin,
    init_first_admin,
    SESSION_KEY_ADMIN_ID,
    SESSION_KEY_ADMIN_AUTH,
)


class TestAdminAuthentication(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_admin.db"
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    # ---------------------------------------------
    # 1. BCRYPT HASHING & VERIFICATION TESTS
    # ---------------------------------------------
    def test_bcrypt_password_hashing_and_verification(self):
        """Test password hashing with bcrypt, salting, and verification."""
        password = "AdminSecurePassword123!"
        hashed = hash_password(password)

        # Ensure plaintext password is never preserved
        self.assertNotEqual(password, hashed)
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$"))

        # Verify correct password matches
        self.assertTrue(verify_password(password, hashed))

        # Verify wrong password fails
        self.assertFalse(verify_password("WrongPassword123!", hashed))
        self.assertFalse(verify_password("adminsecurepassword123!", hashed))

        # Verify empty password fails
        self.assertFalse(verify_password("", hashed))
        self.assertFalse(verify_password(password, ""))

        # Verify malformed hash fails gracefully without raising uncaught errors
        self.assertFalse(verify_password(password, "invalid_non_bcrypt_hash"))

    def test_empty_password_hashing_raises_error(self):
        """Hashing an empty password must raise an explicit ValueError."""
        with self.assertRaises(ValueError):
            hash_password("")

    # ---------------------------------------------
    # 2. CREDENTIAL FORMAT VALIDATION
    # ---------------------------------------------
    def test_credential_format_validation(self):
        """Test username and password formatting rules."""
        # Short username
        is_val, msg = validate_admin_credentials_format("ad", "ValidPass123!")
        self.assertFalse(is_val)
        self.assertIn("at least 3 characters", msg)

        # Invalid username characters
        is_val, msg = validate_admin_credentials_format("admin with spaces", "ValidPass123!")
        self.assertFalse(is_val)

        # Short password
        is_val, msg = validate_admin_credentials_format("admin_user", "short1!")
        self.assertFalse(is_val)
        self.assertIn("at least 8 characters", msg)

        # Password without numbers or symbols
        is_val, msg = validate_admin_credentials_format("admin_user", "alllettersonly")
        self.assertFalse(is_val)

        # Valid credentials
        is_val, msg = validate_admin_credentials_format("admin.test_123", "StrongPass2026!")
        self.assertTrue(is_val)
        self.assertEqual(msg, "")

    # ---------------------------------------------
    # 3. ACCOUNT CREATION & PERSISTENCE
    # ---------------------------------------------
    def test_create_admin_account_persistence(self):
        """Test admin creation in SQLite and ensure password is never plaintext."""
        plain_pw = "SuperSecret2026@"
        success, admin, msg = create_admin_account(
            username="head_admin",
            plain_password=plain_pw,
            role="admin",
            db_path=self.db_path,
        )

        self.assertTrue(success, f"Failed to create admin: {msg}")
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, "head_admin")
        self.assertEqual(admin.role, "admin")

        # Verify raw database content
        with get_connection(self.db_path) as conn:
            raw_admin = queries.get_admin_by_username(conn, "head_admin")
            self.assertIsNotNone(raw_admin)
            self.assertNotEqual(raw_admin.password_hash, plain_pw)
            self.assertTrue(verify_password(plain_pw, raw_admin.password_hash))

    def test_duplicate_admin_username_rejected(self):
        """Duplicate administrator usernames must be rejected."""
        create_admin_account("unique_admin", "PassOne123!", db_path=self.db_path)
        success2, admin2, msg2 = create_admin_account("unique_admin", "PassTwo123!", db_path=self.db_path)
        self.assertFalse(success2)
        self.assertIn("already exists", msg2)

    # ---------------------------------------------
    # 4. AUTHENTICATION SERVICE TESTS
    # ---------------------------------------------
    def test_authenticate_admin_success_and_failure(self):
        """Test admin authentication credentials checking."""
        username = "auth_tester"
        password = "TestingPassword456!"
        create_admin_account(username, password, db_path=self.db_path)

        # Successful authentication
        ok, admin, msg = authenticate_admin(username, password, db_path=self.db_path)
        self.assertTrue(ok)
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, username)

        # Incorrect password
        ok_wrong, admin_wrong, msg_wrong = authenticate_admin(username, "WrongPassword999!", db_path=self.db_path)
        self.assertFalse(ok_wrong)
        self.assertIsNone(admin_wrong)
        self.assertEqual(msg_wrong, "Invalid username or password.")

        # Non-existent username
        ok_ghost, admin_ghost, msg_ghost = authenticate_admin("ghost_user", password, db_path=self.db_path)
        self.assertFalse(ok_ghost)
        self.assertIsNone(admin_ghost)
        self.assertEqual(msg_ghost, "Invalid username or password.")

    # ---------------------------------------------
    # 5. SESSION MANAGEMENT & LOGOUT TESTS
    # ---------------------------------------------
    def test_session_management_and_logout(self):
        """Test admin session login, session check, and logout purging."""
        admin = Admin(id=1, username="session_admin", password_hash="hash", role="admin")

        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            self.assertFalse(is_admin_authenticated())
            self.assertIsNone(get_active_admin_session())

            # Login session
            login_admin_session(admin)
            self.assertTrue(is_admin_authenticated())

            active = get_active_admin_session()
            self.assertIsNotNone(active)
            self.assertEqual(active["username"], "session_admin")
            self.assertEqual(active["role"], "admin")

            # Logout session
            logout_admin_session()
            self.assertFalse(is_admin_authenticated())
            self.assertIsNone(get_active_admin_session())
            self.assertNotIn(SESSION_KEY_ADMIN_ID, mock_session)
            self.assertNotIn(SESSION_KEY_ADMIN_AUTH, mock_session)

    # ---------------------------------------------
    # 6. ROLE-BASED ACCESS CONTROL TESTS
    # ---------------------------------------------
    def test_role_based_access_control(self):
        """Test admin role checks (admin vs superadmin)."""
        admin_std = Admin(id=10, username="regular_admin", password_hash="hash", role="admin")
        admin_super = Admin(id=11, username="master_admin", password_hash="hash", role="superadmin")

        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            # Regular admin
            login_admin_session(admin_std)
            self.assertTrue(check_admin_role("admin"))
            self.assertFalse(check_admin_role("superadmin"))

            # Superadmin can access both admin and superadmin tasks
            mock_session.clear()
            login_admin_session(admin_super)
            self.assertTrue(check_admin_role("admin"))
            self.assertTrue(check_admin_role("superadmin"))

    # ---------------------------------------------
    # 7. ROUTE PROTECTION & UNAUTHORIZED ACCESS TESTS
    # ---------------------------------------------
    def test_unauthorized_access_protection_blocks_public_users(self):
        """Public or unauthenticated users must be halted by require_admin_auth."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session), \
             patch("streamlit.error") as mock_error, \
             patch("streamlit.markdown") as mock_markdown, \
             patch("streamlit.stop") as mock_stop:

            # Attempt admin operation without login
            require_admin_auth()
            mock_error.assert_called()
            mock_stop.assert_called_once()

    def test_authorized_admin_access_allowed(self):
        """Authenticated admin passes require_admin_auth without stopping."""
        admin = Admin(id=5, username="valid_admin", password_hash="hash", role="admin")
        mock_session = {}
        with patch("streamlit.session_state", mock_session), \
             patch("streamlit.stop") as mock_stop:

            login_admin_session(admin)
            result = require_admin_auth()
            self.assertTrue(result)
            mock_stop.assert_not_called()

    # ---------------------------------------------
    # 8. SAFE INITIAL ADMIN UTILITY
    # ---------------------------------------------
    def test_safe_initial_admin_setup_utility(self):
        """Test initializing the first administrator account."""
        self.assertFalse(has_any_admin(self.db_path))

        # First init succeeds as superadmin
        success, superadmin, msg = init_first_admin(
            username="super_init",
            plain_password="InitialPassword789!",
            db_path=self.db_path,
        )
        self.assertTrue(success)
        self.assertIsNotNone(superadmin)
        self.assertEqual(superadmin.role, "superadmin")
        self.assertTrue(has_any_admin(self.db_path))

        # Second init must be refused
        success2, admin2, msg2 = init_first_admin(
            username="another_super",
            plain_password="SecondPassword789!",
            db_path=self.db_path,
        )
        self.assertFalse(success2)
        self.assertIn("already exist", msg2)

    def test_update_admin_credentials(self):
        """Test updating administrator username and password."""
        from services.admin_service import update_admin_account_credentials

        success, admin, _ = create_admin_account(
            username="orig_admin",
            plain_password="OldPassword123!",
            db_path=self.db_path,
        )
        self.assertTrue(success)

        # Update username and password with wrong current password (should fail)
        ok, msg = update_admin_account_credentials(
            admin_id=admin.id,
            current_password="WrongOldPassword!",
            new_username="updated_admin",
            new_password="NewPassword123!",
            confirm_password="NewPassword123!",
            db_path=self.db_path,
        )
        self.assertFalse(ok)
        self.assertIn("Incorrect", msg)

        # Update username and password with correct current password (should succeed)
        ok, msg = update_admin_account_credentials(
            admin_id=admin.id,
            current_password="OldPassword123!",
            new_username="updated_admin",
            new_password="NewPassword123!",
            confirm_password="NewPassword123!",
            db_path=self.db_path,
        )
        self.assertTrue(ok)

        # Verify authentication with new credentials
        auth_ok, auth_admin, _ = authenticate_admin("updated_admin", "NewPassword123!", db_path=self.db_path)
        self.assertTrue(auth_ok)
        self.assertIsNotNone(auth_admin)


if __name__ == "__main__":
    unittest.main()
