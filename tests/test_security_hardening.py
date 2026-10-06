"""
Security Hardening Tests for English Self-Assessment (Phase 19).
Verifies:
- Filename sanitization against path traversal and overwrites
- Uploaded file validation (size limits, extensions, ZIP magic bytes, archive integrity)
- Audio path traversal mitigation and format restrictions
- Database query parameterization safety against SQL injection
- Secure bcrypt password verification and malformed hash resilience
- Question payload validation rejecting insecure audio references
"""

import io
import unittest
import tempfile
import shutil
import zipfile
from pathlib import Path

from database.db import init_db, get_connection
from database import queries
from database.models import User
from utils.security import (
    sanitize_filename,
    validate_uploaded_file,
    is_safe_audio_path,
    MAX_UPLOAD_SIZE_BYTES,
)
from services.admin_service import verify_password, hash_password
from services.question_service import validate_question_payload
from utils.audio import render_listening_audio


class TestSecurityHardening(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_sec.db"
        init_db(self.db_path)
        self.base_dir = Path(self.temp_dir).resolve()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # --------------------------------------------------------
    # 1. FILENAME SANITIZATION & PATH TRAVERSAL
    # --------------------------------------------------------
    def test_sanitize_filename_traversal_prevention(self):
        """Ensure filenames with directory traversal tokens are stripped to safe basenames."""
        cases = [
            ("../../etc/passwd", "etc_passwd"),
            ("..\\..\\windows\\system32\\cmd.exe", "cmd.exe"),
            ("folder/subfolder/test_bank.xlsx", "test_bank.xlsx"),
            ("question\x00bank.docx", "questionbank.docx"),
            ("../../../secret.key", "secret.key"),
            ("", "unnamed_file"),
            ("...", "unnamed_file"),
            ("normal_file.xlsx", "normal_file.xlsx"),
        ]
        for raw, expected in cases:
            cleaned = sanitize_filename(raw)
            self.assertNotIn("..", cleaned)
            self.assertNotIn("/", cleaned)
            self.assertNotIn("\\", cleaned)
            self.assertNotIn("\x00", cleaned)
            self.assertTrue(len(cleaned) > 0)

    # --------------------------------------------------------
    # 2. UPLOADED FILE VALIDATION
    # --------------------------------------------------------
    def test_validate_uploaded_file_rejection(self):
        """Ensure invalid, oversized, or malicious files are rejected."""
        # 1. Empty file
        valid, err = validate_uploaded_file("empty.docx", b"")
        self.assertFalse(valid)
        self.assertIn("empty", err.lower())

        # 2. Oversized file (>10MB)
        oversized_bytes = b"PK\x03\x04" + b"X" * (MAX_UPLOAD_SIZE_BYTES + 100)
        valid, err = validate_uploaded_file("big.docx", oversized_bytes)
        self.assertFalse(valid)
        self.assertIn("exceeds", err.lower())

        # 3. Disallowed extension
        valid, err = validate_uploaded_file("payload.py", b"print('hack')")
        self.assertFalse(valid)
        self.assertIn("unsupported", err.lower())

        # 4. Bad magic bytes (e.g. text file renamed to .docx)
        fake_docx = b"This is just plaintext pretending to be Word"
        valid, err = validate_uploaded_file("fake.docx", fake_docx)
        self.assertFalse(valid)
        self.assertIn("does not appear to be a valid", err.lower())

    def test_validate_uploaded_file_valid_zip(self):
        """Ensure valid OpenXML zip archive passes validation."""
        bio = io.BytesIO()
        with zipfile.ZipFile(bio, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types></Types>")
        valid_bytes = bio.getvalue()

        valid, err = validate_uploaded_file("test.docx", valid_bytes)
        self.assertTrue(valid)
        self.assertEqual(err, "")

    # --------------------------------------------------------
    # 3. AUDIO PATH TRAVERSAL MITIGATION
    # --------------------------------------------------------
    def test_is_safe_audio_path_traversal(self):
        """Ensure absolute paths and directory traversal are rejected for audio files."""
        # Path traversal breakout with ..
        valid, path, err = is_safe_audio_path("../../outside.mp3", self.base_dir)
        self.assertFalse(valid)
        self.assertIn("traversal", err.lower())

        # Path traversal with absolute path containing ..
        valid, path, err = is_safe_audio_path("/var/log/../../etc/passwd.mp3", self.base_dir)
        self.assertFalse(valid)
        self.assertIn("traversal", err.lower())

        # Invalid extension
        valid, path, err = is_safe_audio_path("audio/listening/script.sh", self.base_dir)
        self.assertFalse(valid)
        self.assertIn("invalid audio extension", err.lower())

        # Non-audio file without extension
        valid, path, err = is_safe_audio_path("/etc/passwd", self.base_dir)
        self.assertFalse(valid)
        self.assertIn("invalid audio extension", err.lower())

        # Valid relative audio path
        valid, path, err = is_safe_audio_path("audio/listening/lesson1.mp3", self.base_dir)
        self.assertTrue(valid)
        self.assertIsNotNone(path)
        self.assertTrue(path.is_relative_to(self.base_dir))

    # --------------------------------------------------------
    # 4. QUESTION VALIDATION AUDIO SECURITY
    # --------------------------------------------------------
    def test_question_payload_rejects_unsafe_audio(self):
        """Ensure manual Listening question creation rejects traversing audio files."""
        payload = {
            "category": "Listening",
            "difficulty": "Easy",
            "status": "Active",
            "question_text": "What is the speaker discussing?",
            "option_a": "Option A",
            "option_b": "Option B",
            "option_c": "Option C",
            "option_d": "Option D",
            "correct_answer": "A",
            "explanation": "Because speaker mentioned Option A in the dialog.",
            "audio_file": "../../etc/shadow",  # Insecure traversal
        }
        is_valid, msg = validate_question_payload(payload)
        self.assertFalse(is_valid)
        self.assertIn("invalid audio", msg.lower())

    # --------------------------------------------------------
    # 5. SQL INJECTION & PARAMETERIZATION SAFETY
    # --------------------------------------------------------
    def test_sql_parameterization_safety(self):
        """Ensure malicious SQL injection strings in queries are safely escaped via parameters."""
        with get_connection(self.db_path) as conn:
            # 1. Attempt injection in user name/email
            sqli_payload = "'; DROP TABLE users; --"
            user = queries.get_or_create_user(
                conn=conn,
                name=f"Attacker {sqli_payload}",
                email="attacker@safe.org",
            )
            self.assertIsNotNone(user.id)

            # Check that users table still exists and data was parameterized
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM users WHERE id = ?;", (user.id,))
            row = cursor.fetchone()
            self.assertEqual(row[0], f"Attacker {sqli_payload}")

            # 2. Attempt injection in get_questions_filtered search
            results = queries.get_questions_filtered(
                conn=conn,
                search_query="' OR '1'='1' --",
            )
            # Query executes safely without syntax error
            self.assertIsInstance(results, list)

    # --------------------------------------------------------
    # 6. BCRYPT RESILIENCE & ADMIN AUTHENTICATION
    # --------------------------------------------------------
    def test_bcrypt_verification_resilience(self):
        """Ensure password verification handles edge cases and malformed hashes safely."""
        # Valid hash verification
        pw = "CorrectHorseBattery99!"
        h = hash_password(pw)
        self.assertTrue(verify_password(pw, h))
        self.assertFalse(verify_password("WrongPassword123!", h))

        # Malformed or garbage hashes must return False without crashing
        self.assertFalse(verify_password(pw, "not_a_bcrypt_hash"))
        self.assertFalse(verify_password(pw, ""))
        self.assertFalse(verify_password("", h))
        self.assertFalse(verify_password("", ""))


if __name__ == "__main__":
    unittest.main()
