"""
Unit tests for SQLite Database Schema, Idempotency, Constraints, and Queries.
"""

import unittest
import sqlite3
import tempfile
from pathlib import Path

from database.db import create_connection, init_db, get_connection
from database.models import User, Admin, Question
from database import queries


class TestDatabaseFoundation(unittest.TestCase):
    def setUp(self):
        # Create a unique temporary database file for each test
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_assessment.db"
        init_db(self.db_path)
        self.conn = create_connection(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.temp_dir.cleanup()

    def test_schema_tables_created(self):
        """Verify all 11 required tables are created in SQLite."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row["name"] for row in cursor.fetchall()]

        expected_tables = [
            "admins",
            "answers",
            "attempt_questions",
            "attempts",
            "audio_files",
            "categories",
            "import_history",
            "passages",
            "questions",
            "topics",
            "users",
        ]
        for table in expected_tables:
            self.assertIn(table, tables, f"Expected table '{table}' not found in database.")

    def test_idempotent_initialization(self):
        """Running init_db multiple times must not crash or duplicate seeded categories."""
        # Run init_db second and third time
        init_db(self.db_path)
        init_db(self.db_path)

        categories = queries.get_all_categories(self.conn)
        self.assertEqual(len(categories), 3)
        cat_names = [c.name for c in categories]
        self.assertListEqual(cat_names, ["Grammar", "Reading", "Listening"])

    def test_user_operations(self):
        """Test user creation, retrieval, and email lookup."""
        user_id = queries.create_user(
            self.conn,
            name="Jane Doe",
            email="Jane.Doe@Example.com",
            institution="University of Excellence",
            program="English Education",
        )
        self.assertIsInstance(user_id, int)

        # Retrieve by ID
        user = queries.get_user_by_id(self.conn, user_id)
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "Jane Doe")
        self.assertEqual(user.email, "jane.doe@example.com")  # Normalized lowercase
        self.assertEqual(user.institution, "University of Excellence")

        # Retrieve by email
        by_email = queries.get_user_by_email(self.conn, "jane.doe@example.com")
        self.assertIsNotNone(by_email)
        self.assertEqual(by_email.id, user_id)

        # get_or_create_user should return existing record
        existing = queries.get_or_create_user(self.conn, "Jane Doe", "jane.doe@example.com")
        self.assertEqual(existing.id, user_id)

    def test_admin_creation_and_lookup(self):
        """Test admin creation and username uniqueness."""
        admin_id = queries.create_admin(
            self.conn,
            username="admin_test",
            password_hash="$2b$12$fakehashforunittestonly",
            role="admin",
        )
        self.assertIsInstance(admin_id, int)

        admin = queries.get_admin_by_username(self.conn, "admin_test")
        self.assertIsNotNone(admin)
        self.assertEqual(admin.username, "admin_test")

        # Duplicate username should violate UNIQUE constraint
        with self.assertRaises(sqlite3.IntegrityError):
            queries.create_admin(self.conn, "admin_test", "anotherhash")

    def test_question_constraints(self):
        """Verify constraints on correct_answer, difficulty, and status."""
        grammar = queries.get_category_by_name(self.conn, "Grammar")
        self.assertIsNotNone(grammar)

        # Valid question
        q = Question(
            category_id=grammar.id,
            question_text="The students ___ English every day.",
            option_a="study",
            option_b="studies",
            option_c="studying",
            option_d="studied",
            correct_answer="A",
            difficulty="Easy",
            status="Active",
            explanation="Students is plural.",
        )
        q_id = queries.create_question(self.conn, q)
        self.assertIsInstance(q_id, int)

        saved_q = queries.get_question_by_id(self.conn, q_id)
        self.assertIsNotNone(saved_q)
        self.assertEqual(saved_q.correct_answer, "A")
        self.assertEqual(saved_q.difficulty, "Easy")
        self.assertEqual(saved_q.status, "Active")

        # Invalid correct_answer (must be A, B, C, or D)
        invalid_q = Question(
            category_id=grammar.id,
            question_text="Test",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="E",  # Invalid
            difficulty="Easy",
            status="Active",
        )
        with self.assertRaises(sqlite3.IntegrityError):
            queries.create_question(self.conn, invalid_q)

        # Invalid difficulty
        invalid_diff = Question(
            category_id=grammar.id,
            question_text="Test",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_answer="B",
            difficulty="Extreme",  # Invalid
            status="Active",
        )
        with self.assertRaises(sqlite3.IntegrityError):
            queries.create_question(self.conn, invalid_diff)

    def test_attempt_order_and_answers_preservation(self):
        """
        Verify that attempt_questions preserves exact sequence
        and answers table preserves user answer and correctness accurately.
        """
        grammar = queries.get_category_by_name(self.conn, "Grammar")
        user_id = queries.create_user(self.conn, "Student A", "student.a@example.com")

        # Create 3 questions
        q_ids = []
        for i, ans in enumerate(["A", "B", "C"], start=1):
            q = Question(
                category_id=grammar.id,
                question_text=f"Question {i}",
                option_a="Opt 1",
                option_b="Opt 2",
                option_c="Opt 3",
                option_d="Opt 4",
                correct_answer=ans,
                difficulty="Medium",
                status="Active",
            )
            q_ids.append(queries.create_question(self.conn, q))

        # Create attempt
        attempt_id = queries.create_attempt(
            self.conn,
            user_id=user_id,
            category_id=grammar.id,
            difficulty="Medium",
            total_questions=3,
        )

        # Add questions in a specific order: [q3, q1, q2]
        custom_order = [q_ids[2], q_ids[0], q_ids[1]]
        queries.add_attempt_questions(self.conn, attempt_id, custom_order)

        # Verify preserved order
        ordered_questions = queries.get_attempt_questions(self.conn, attempt_id)
        self.assertEqual(len(ordered_questions), 3)
        retrieved_ids = [q.id for order, q in ordered_questions]
        self.assertEqual(retrieved_ids, custom_order)
        self.assertEqual([order for order, _ in ordered_questions], [1, 2, 3])

        # Record answers:
        # Q3: correct ("C")
        # Q1: user answered "B" (incorrect, correct is "A")
        # Q2: user skipped / None
        queries.record_answer(self.conn, attempt_id, custom_order[0], "C", "C", True)
        queries.record_answer(self.conn, attempt_id, custom_order[1], "B", "A", False)
        queries.record_answer(self.conn, attempt_id, custom_order[2], None, "B", False)

        answers = queries.get_answers_by_attempt(self.conn, attempt_id)
        self.assertEqual(len(answers), 3)
        self.assertEqual(answers[0].user_answer, "C")
        self.assertEqual(answers[0].is_correct, 1)

        self.assertEqual(answers[1].user_answer, "B")
        self.assertEqual(answers[1].is_correct, 0)

        self.assertIsNone(answers[2].user_answer)
        self.assertEqual(answers[2].is_correct, 0)

        # Complete attempt and calculate score: 1 correct out of 3 = 33.33%
        queries.complete_attempt(
            self.conn,
            attempt_id=attempt_id,
            correct_answers=1,
            incorrect_answers=2,
            score=33.33,
            duration_seconds=120,
        )

        completed = queries.get_attempt_by_id(self.conn, attempt_id)
        self.assertIsNotNone(completed)
        self.assertEqual(completed.correct_answers, 1)
        self.assertEqual(completed.incorrect_answers, 2)
        self.assertAlmostEqual(completed.score, 33.33, places=2)
        self.assertIsNotNone(completed.completed_at)
        self.assertEqual(completed.duration_seconds, 120)

    def test_import_history_logging(self):
        """Test recording and retrieving import history."""
        hist_id = queries.record_import(
            self.conn,
            file_name="Grammar_Test_50_Soal.docx",
            category="Grammar",
            total_detected=50,
            total_imported=48,
            total_failed=2,
            imported_by="admin",
        )
        self.assertIsInstance(hist_id, int)

        history = queries.get_import_history(self.conn)
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[0].file_name, "Grammar_Test_50_Soal.docx")
        self.assertEqual(history[0].total_imported, 48)


if __name__ == "__main__":
    unittest.main()
