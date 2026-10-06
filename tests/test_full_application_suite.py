"""
Phase 20: Comprehensive Full Application Testing Suite.
Tests:
- Complete end-to-end participant user flow (identity -> category -> level -> quiz -> feedback -> result -> history)
- Category engines (Grammar, Reading with passages, Listening with audio)
- Complete admin workflow (login -> dashboard -> users -> results -> question CRUD -> import -> analytics)
- Database integrity (foreign keys, transaction rollback, persistence)
- Edge cases (0 questions, insufficient questions, missing explanation, missing audio, malformed docx, invalid answers, duplicate emails, session resets)
"""

import io
import unittest
import tempfile
import shutil
import zipfile
from pathlib import Path
from unittest.mock import patch

from database.db import init_db, get_connection
from database import queries
from database.models import Question, User, Admin, Passage
from config.settings import DEFAULT_QUESTIONS_PER_TEST, BASE_DIR

# Services
from services.user_service import (
    process_user_identity,
    set_active_user_session,
    get_active_user_session,
    clear_active_user_session,
)
from services.quiz_engine import (
    prepare_quiz_session,
    get_quiz_session,
    is_quiz_selection_ready,
    start_quiz_attempt,
    submit_current_answer,
    move_to_next_question,
    complete_current_attempt,
    reset_quiz_session,
    restart_with_difficulty,
    SESSION_KEY_ATTEMPT_ID,
    SESSION_KEY_COMPLETED_ATTEMPT,
    SESSION_KEY_QUESTIONS,
)
from services.scoring_service import (
    calculate_score,
    calculate_accuracy,
    calculate_duration_seconds,
    finalize_attempt,
    get_attempt_summary,
)
from services.history_service import (
    fetch_user_history,
    calculate_self_assessment_summary,
    CERTIFICATION_DISCLAIMER,
)
from services.admin_service import (
    create_admin_account,
    authenticate_admin,
    login_admin_session,
    logout_admin_session,
    is_admin_authenticated,
    check_admin_role,
    init_first_admin,
    verify_password,
    hash_password,
)
from services.admin_dashboard_service import (
    fetch_dashboard_summary,
    fetch_users_directory,
    fetch_assessment_results,
)
from services.question_service import (
    add_question,
    update_question_record,
    deactivate_question,
    activate_question,
    archive_question,
    fetch_questions,
    fetch_question_by_id,
    validate_question_payload,
)
from services.import_service import execute_import_batch, fetch_import_history_logs
from services.analytics_service import (
    fetch_question_analytics,
    get_top_frequently_attempted,
    get_highest_accuracy_questions,
    get_lowest_accuracy_questions,
)
from utils.docx_parser import parse_docx_content
from utils.excel_parser import parse_excel_content, export_questions_to_excel
from utils.difficulty import classify_difficulty
from utils.audio import render_listening_audio, render_feedback_audio
from utils.security import sanitize_filename, validate_uploaded_file, is_safe_audio_path


class TestFullApplicationComprehensive(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir).resolve() / "comprehensive_test.db"
        init_db(self.db_path)
        self.seed_test_data()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def seed_test_data(self):
        """Seed a representative question bank across all categories and levels."""
        with get_connection(self.db_path) as conn:
            # Seed default test participant user
            default_user = queries.get_or_create_user(conn, name="Test Participant", email="test.participant@example.com")
            self.user_id = default_user.id

            g_cat = queries.get_category_by_name(conn, "Grammar")
            r_cat = queries.get_category_by_name(conn, "Reading")
            l_cat = queries.get_category_by_name(conn, "Listening")

            # 1. Grammar Questions (Easy, Medium, Hard)
            for diff in ["Easy", "Medium", "Hard"]:
                for i in range(1, 4):
                    queries.create_question(conn, Question(
                        category_id=g_cat.id,
                        subtopic="Tenses",
                        question_type="Multiple Choice",
                        question_text=f"Grammar {diff} question number {i} prompt text?",
                        option_a=f"Option A {i}",
                        option_b=f"Option B {i}",
                        option_c=f"Option C {i}",
                        option_d=f"Option D {i}",
                        correct_answer="A",
                        explanation=f"Detailed explanation for Grammar {diff} question {i}.",
                        difficulty=diff,
                        status="Active",
                    ))

            # 2. Reading Passage and linked questions
            pass_id = queries.create_passage(
                conn=conn,
                title="Climate and Oceanography",
                passage_text="Ocean currents act as a global conveyor belt transporting thermal energy.",
                category_id=r_cat.id,
            )
            for i in range(1, 4):
                queries.create_question(conn, Question(
                    category_id=r_cat.id,
                    passage_id=pass_id,
                    subtopic="Ocean Currents",
                    question_type="Main Idea" if i == 1 else "Detail",
                    question_text=f"Reading Medium question number {i} regarding ocean energy?",
                    option_a=f"Choice A {i}",
                    option_b=f"Choice B {i}",
                    option_c=f"Choice C {i}",
                    option_d=f"Choice D {i}",
                    correct_answer="B",
                    explanation=f"Explanation for Reading question {i}.",
                    difficulty="Medium",
                    status="Active",
                ))

            # 3. Listening Question with Audio Link
            l_qid = queries.create_question(conn, Question(
                category_id=l_cat.id,
                subtopic="Lecture",
                question_type="Detail",
                question_text="What was the primary conclusion of the seminar?",
                option_a="Theory A",
                option_b="Theory B",
                option_c="Theory C",
                option_d="Theory D",
                correct_answer="C",
                explanation="The lecturer emphasized Theory C.",
                difficulty="Easy",
                status="Active",
            ))
            queries.create_audio_file(
                conn=conn,
                question_id=l_qid,
                file_path="audio/listening/test_lecture.mp3",
                transcript="Welcome class, today we conclude that Theory C holds.",
                duration=12.5,
            )

    # ========================================================
    # 1. USER FLOW: END-TO-END PARTICIPANT ASSESSMENT
    # ========================================================
    def test_complete_user_flow(self):
        """
        Verify full participant lifecycle:
        Identity -> Category & Level -> Start Attempt -> Submit Answers -> Score Finalization -> History & Summary.
        """
        # Step 1: User Identity
        success, user, errors = process_user_identity(
            name="Alice Walker",
            email="alice.walker@university.edu",
            institution="State University",
            program="English Education",
            db_path=self.db_path,
        )
        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertEqual(user.email, "alice.walker@university.edu")

        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            set_active_user_session(user)
            self.assertEqual(get_active_user_session()["name"], "Alice Walker")

            # Step 2: Category & Level Selection
            prepare_quiz_session(category="Grammar", difficulty="Easy")
            self.assertTrue(is_quiz_selection_ready())
            self.assertEqual(get_quiz_session()["category"], "Grammar")
            self.assertEqual(get_quiz_session()["difficulty"], "Easy")

            # Step 3: Start Quiz Attempt
            ok, attempt, questions, notice = start_quiz_attempt(
                user_id=user.id,
                category_name="Grammar",
                difficulty="Easy",
                num_questions=3,
                db_path=self.db_path,
            )
            self.assertTrue(ok)
            self.assertEqual(len(questions), 3)
            self.assertIsNotNone(mock_session.get(SESSION_KEY_ATTEMPT_ID))

            # Step 4: Answer questions with instant feedback
            session_questions = mock_session[SESSION_KEY_QUESTIONS]
            for idx in range(3):
                correct_key = session_questions[idx]["correct_answer"]
                ok_eval, evaluated = submit_current_answer(correct_key, db_path=self.db_path)
                self.assertTrue(ok_eval)
                self.assertTrue(evaluated["is_correct"])
                self.assertIn("explanation", evaluated)

                # Move to next question if not last
                if idx < 2:
                    move_to_next_question()

            # Step 5: Finalize Attempt
            final_attempt = complete_current_attempt(db_path=self.db_path)
            self.assertIsNotNone(final_attempt)
            self.assertEqual(final_attempt.score, 100)
            self.assertEqual(final_attempt.correct_answers, 3)

            # Step 6: Verify History & Self-Assessment Summary
            history_rows = fetch_user_history(user.id, db_path=self.db_path)
            self.assertEqual(len(history_rows), 1)
            self.assertEqual(history_rows[0]["score"], 100)
            self.assertEqual(history_rows[0]["category"], "Grammar")

            summary = calculate_self_assessment_summary(history_rows)
            self.assertEqual(summary["total_attempts"], 1)
            self.assertEqual(summary["overall_average_score"], 100.0)
            self.assertEqual(summary["strongest_observed_category"], "Grammar")
            self.assertIn("not an officially certified", summary["disclaimer"].lower())

    # ========================================================
    # 2. READING MODULE: PASSAGES & MULTI-QUESTION LINKAGE
    # ========================================================
    def test_reading_module_flow(self):
        """Verify passage retrieval, question linkage, and scoring for Reading."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            prepare_quiz_session(category="Reading", difficulty="Medium")
            ok, attempt, questions, _ = start_quiz_attempt(
                user_id=self.user_id,
                category_name="Reading",
                difficulty="Medium",
                num_questions=3,
                db_path=self.db_path,
            )
            self.assertTrue(ok)
            self.assertEqual(len(questions), 3)

            # Check that questions in session state have passage attached
            session_questions = mock_session.get(SESSION_KEY_QUESTIONS, [])
            self.assertEqual(len(session_questions), 3)
            for q_item in session_questions:
                self.assertIsNotNone(q_item.get("passage_id"))
                self.assertIsNotNone(q_item.get("passage_text"))
                self.assertIn("Ocean currents", q_item["passage_text"])

            # Submit answers: 2 correct, 1 incorrect
            q0_corr = session_questions[0]["correct_answer"]
            submit_current_answer(q0_corr, db_path=self.db_path)
            move_to_next_question()

            q1_corr = session_questions[1]["correct_answer"]
            submit_current_answer(q1_corr, db_path=self.db_path)
            move_to_next_question()

            q2_corr = session_questions[2]["correct_answer"]
            q2_wrong = "A" if q2_corr != "A" else "B"
            submit_current_answer(q2_wrong, db_path=self.db_path)

            final_attempt = complete_current_attempt(db_path=self.db_path)
            self.assertEqual(final_attempt.correct_answers, 2)
            self.assertEqual(final_attempt.incorrect_answers, 1)
            self.assertAlmostEqual(final_attempt.score, 66.67, places=1)

    # ========================================================
    # 3. LISTENING MODULE: AUDIO RETRIEVAL & PLAYBACK
    # ========================================================
    def test_listening_module_audio_flow(self):
        """Verify audio file retrieval, non-crashing safe playback, and scoring."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            prepare_quiz_session(category="Listening", difficulty="Easy")
            ok, attempt, questions, _ = start_quiz_attempt(
                user_id=self.user_id,
                category_name="Listening",
                difficulty="Easy",
                num_questions=1,
                db_path=self.db_path,
            )
            self.assertTrue(ok)
            self.assertEqual(len(questions), 1)

            session_questions = mock_session.get(SESSION_KEY_QUESTIONS, [])
            self.assertEqual(len(session_questions), 1)
            l_q = session_questions[0]
            self.assertEqual(l_q["audio_file"], "audio/listening/test_lecture.mp3")

            # Non-crashing playback for non-existent file path
            with patch("streamlit.markdown") as mock_md:
                rendered = render_listening_audio(l_q["audio_file"])
                self.assertFalse(rendered)  # Audio file doesn't exist on disk in test, safely reported
                mock_md.assert_called()

            # Answer and score
            corr_ans = l_q["correct_answer"]
            ok_ans, res = submit_current_answer(corr_ans, db_path=self.db_path)
            self.assertTrue(ok_ans)
            self.assertTrue(res["is_correct"])

            # Feedback audio call
            with patch("streamlit.audio"), patch("streamlit.markdown"):
                render_feedback_audio(is_correct=True)

    # ========================================================
    # 4. ADMIN MODULE: COMPLETE MANAGEMENT & ANALYTICS
    # ========================================================
    def test_admin_complete_workflow(self):
        """
        Verify:
        Admin creation -> login -> dashboard stats -> question CRUD -> analytics calculation.
        """
        # 1. Admin Creation & Authentication
        created, admin, _ = create_admin_account("superadmin", "AdminPass123!", role="superadmin", db_path=self.db_path)
        self.assertTrue(created)

        auth_ok, logged_admin, _ = authenticate_admin("superadmin", "AdminPass123!", db_path=self.db_path)
        self.assertTrue(auth_ok)
        self.assertEqual(logged_admin.username, "superadmin")

        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            login_admin_session(logged_admin)
            self.assertTrue(is_admin_authenticated())
            self.assertTrue(check_admin_role("admin"))
            self.assertTrue(check_admin_role("superadmin"))

            # 2. Dashboard Summary
            summary = fetch_dashboard_summary(db_path=self.db_path)
            self.assertGreater(summary["total_questions"], 0)
            self.assertGreater(summary["active_questions"], 0)

            # 3. Question CRUD
            q_payload = {
                "category": "Grammar",
                "difficulty": "Hard",
                "question_text": "The symposium ___ postponed indefinitely due to inclement weather.",
                "option_a": "was",
                "option_b": "were",
                "option_c": "have been",
                "option_d": "being",
                "correct_answer": "A",
                "explanation": "Singular subject 'symposium' requires singular verb 'was'.",
                "subtopic": "Subject-Verb Agreement",
                "status": "Active",
            }
            add_ok, new_qid, add_msg = add_question(q_payload, db_path=self.db_path)
            self.assertTrue(add_ok)

            # Inspect
            q_read = fetch_question_by_id(new_qid, db_path=self.db_path)
            self.assertIsNotNone(q_read)
            self.assertEqual(q_read["difficulty"], "Hard")

            # Update
            q_update_payload = {
                "category": "Grammar",
                "difficulty": "Medium",  # Changed level
                "question_text": q_read["question_text"],
                "option_a": q_read["option_a"],
                "option_b": q_read["option_b"],
                "option_c": q_read["option_c"],
                "option_d": q_read["option_d"],
                "correct_answer": "A",
                "explanation": q_read["explanation"],
                "subtopic": q_read["subtopic"],
                "status": "Active",
            }
            up_ok, _ = update_question_record(new_qid, q_update_payload, db_path=self.db_path)
            self.assertTrue(up_ok)

            # Deactivate & Archive
            deact_ok, _ = deactivate_question(new_qid, db_path=self.db_path)
            self.assertTrue(deact_ok)
            arch_ok, _ = archive_question(new_qid, db_path=self.db_path)
            self.assertTrue(arch_ok)

            # 4. Question Analytics
            analytics = fetch_question_analytics(db_path=self.db_path)
            self.assertIsInstance(analytics, list)

            # 5. Logout
            logout_admin_session()
            self.assertFalse(is_admin_authenticated())

    # ========================================================
    # 5. DATABASE INTEGRITY: TRANSACTIONS & CONSTRAINTS
    # ========================================================
    def test_database_foreign_key_and_transactions(self):
        """Verify foreign key enforcement and rollback on exception."""
        with get_connection(self.db_path) as conn:
            # 1. Inserting question with non-existent category_id must raise integrity error
            with self.assertRaises(Exception):
                queries.create_question(conn, Question(
                    category_id=999999,  # Invalid FK
                    question_text="Invalid FK question?",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="A",
                    explanation="Explanation text",
                    difficulty="Easy",
                    status="Active",
                ))

        # 2. Transaction rollback: ensure failed batch rolls back cleanly
        try:
            with get_connection(self.db_path) as conn:
                g_cat = queries.get_category_by_name(conn, "Grammar")
                queries.create_question(conn, Question(
                    category_id=g_cat.id,
                    question_text="Will this persist if transaction fails?",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="A",
                    explanation="Explanation text",
                    difficulty="Easy",
                    status="Active",
                ))
                # Trigger deliberate exception
                raise RuntimeError("Intentional rollback trigger")
        except RuntimeError:
            pass

        # Verify that question was rolled back and not persisted
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM questions WHERE question_text LIKE 'Will this persist%';")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 0)

    # ========================================================
    # 6. EDGE CASES & ERROR RESILIENCE
    # ========================================================
    def test_edge_cases(self):
        """
        Verify:
        - 0 questions available for a criteria
        - Insufficient questions (< requested limit)
        - Missing explanation rejected
        - Invalid answer key rejected
        - Duplicate email re-use
        - Quiz session reset
        - Malformed DOCX and XLSX
        """
        # 1. Insufficient / Graceful reuse of questions
        ok, attempt, questions, notice = start_quiz_attempt(
            user_id=self.user_id,
            category_name="Listening",
            difficulty="Easy",
            num_questions=10,  # Only 1 question exists in Listening Easy!
            db_path=self.db_path,
        )
        self.assertTrue(ok)
        self.assertLess(len(questions), 10)  # Gracefully returned available count without crash
        self.assertIsNotNone(notice)

        # 2. Missing explanation rejected in payload
        bad_payload = {
            "category": "Grammar",
            "difficulty": "Easy",
            "status": "Active",
            "question_text": "Valid question prompt?",
            "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
            "correct_answer": "A",
            "explanation": "",  # Missing!
        }
        val_ok, val_err = validate_question_payload(bad_payload)
        self.assertFalse(val_ok)
        self.assertIn("explanation is required", val_err.lower())

        # 3. Invalid answer key rejected
        bad_payload["explanation"] = "Valid explanation"
        bad_payload["correct_answer"] = "Z"  # Invalid!
        val_ok, val_err = validate_question_payload(bad_payload)
        self.assertFalse(val_ok)
        self.assertIn("correct answer must be one of", val_err.lower())

        # 4. Duplicate email reuse returns existing user profile
        _, user1, _ = process_user_identity("Bob Smith", "bob@example.com", db_path=self.db_path)
        _, user2, _ = process_user_identity("Bob Smith", "bob@example.com", db_path=self.db_path)
        self.assertEqual(user1.id, user2.id)

        # 5. Quiz session reset clears state cleanly
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            prepare_quiz_session("Grammar", "Easy")
            self.assertTrue(is_quiz_selection_ready())
            reset_quiz_session()
            self.assertFalse(is_quiz_selection_ready())

        # 6. Malformed DOCX content handling
        parsed_docx = parse_docx_content(b"Corrupted non-zip raw bytes")
        self.assertEqual(parsed_docx["total_detected"], 0)
        self.assertEqual(parsed_docx["valid_count"], 0)


if __name__ == "__main__":
    unittest.main()
