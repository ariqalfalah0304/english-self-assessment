"""
Unit tests for Ujian Gabungan (Final Mastery Exam) Proportional Question Sampling.
"""

import unittest
import tempfile
from pathlib import Path

from database.db import init_db, get_connection
from database import queries
from database.models import Question
from services.question_selector import select_final_exam_questions
from services.quiz_engine import start_final_exam_attempt, prepare_final_exam_session
from unittest.mock import patch


class TestFinalExamSampling(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / "test_final_exam.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            self.grammar_cat = queries.get_category_by_name(conn, "Grammar")
            self.user_id = queries.create_user(conn, "Test Student", "student@example.com")

            # Seed 3 Skills with 20 questions each (60 questions total)
            for skill_num in range(1, 4):
                queries.get_or_create_skill(
                    conn,
                    self.grammar_cat.id,
                    skill_num,
                    f"Skill {skill_num}: Topic {skill_num}",
                )
                for q_idx in range(1, 21):
                    q = Question(
                        category_id=self.grammar_cat.id,
                        skill_number=skill_num,
                        skill_name=f"Skill {skill_num}: Topic {skill_num}",
                        question_text=f"Question S{skill_num}-Q{q_idx}: Choose the correct verb.",
                        option_a=f"Option A S{skill_num}-Q{q_idx}",
                        option_b=f"Option B S{skill_num}-Q{q_idx}",
                        option_c=f"Option C S{skill_num}-Q{q_idx}",
                        option_d=f"Option D S{skill_num}-Q{q_idx}",
                        correct_answer="A",
                        explanation=f"Explanation S{skill_num}-Q{q_idx}",
                        difficulty="Easy",
                        status="Active",
                    )
                    queries.create_question(conn, q)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_proportional_sampling_3_skills(self):
        """Verify that 50 questions are sampled proportionally from 3 skills (17, 17, 16)."""
        with get_connection(self.db_path) as conn:
            questions, notice = select_final_exam_questions(
                conn=conn,
                user_id=self.user_id,
                category_name="Grammar",
                category_id=self.grammar_cat.id,
                requested_count=50,
            )

            self.assertEqual(len(questions), 50)
            self.assertEqual(notice, "")

            # Count questions per skill_number
            skill_counts = {}
            for q in questions:
                snum = q.get("skill_number", 1)
                skill_counts[snum] = skill_counts.get(snum, 0) + 1

            self.assertEqual(sum(skill_counts.values()), 50)
            # Expecting 17, 17, 16 distribution
            self.assertIn(17, skill_counts.values())
            self.assertIn(16, skill_counts.values())

    def test_proportional_sampling_4_skills(self):
        """Verify that when a 4th skill is added, the system automatically adapts to sample from all 4 skills (13, 13, 12, 12)."""
        with get_connection(self.db_path) as conn:
            # Add Skill 4 with 20 questions
            queries.get_or_create_skill(conn, self.grammar_cat.id, 4, "Skill 4: Advanced Subjunctive")
            for q_idx in range(1, 21):
                q = Question(
                    category_id=self.grammar_cat.id,
                    skill_number=4,
                    skill_name="Skill 4: Advanced Subjunctive",
                    question_text=f"Question S4-Q{q_idx}: Subjunctive rule.",
                    option_a="Option A",
                    option_b="Option B",
                    option_c="Option C",
                    option_d="Option D",
                    correct_answer="A",
                    explanation="Subjunctive explanation",
                    difficulty="Hard",
                    status="Active",
                )
                queries.create_question(conn, q)

            questions, notice = select_final_exam_questions(
                conn=conn,
                user_id=self.user_id,
                category_name="Grammar",
                category_id=self.grammar_cat.id,
                requested_count=50,
            )

            self.assertEqual(len(questions), 50)
            skill_counts = {}
            for q in questions:
                snum = q.get("skill_number", 1)
                skill_counts[snum] = skill_counts.get(snum, 0) + 1

            self.assertEqual(len(skill_counts), 4)
            self.assertEqual(sum(skill_counts.values()), 50)
            # Expecting 13, 13, 12, 12 distribution
            self.assertIn(13, skill_counts.values())
            self.assertIn(12, skill_counts.values())

    def test_start_final_exam_attempt_recording(self):
        """Verify start_final_exam_attempt creates database attempt and sets session state."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            prepare_final_exam_session("Grammar", self.grammar_cat.id)
            success, attempt, questions, notice = start_final_exam_attempt(
                user_id=self.user_id,
                category_name="Grammar",
                requested_count=50,
                db_path=self.db_path,
            )

            self.assertTrue(success)
            self.assertIsNotNone(attempt)
            self.assertEqual(attempt.total_questions, 50)
            self.assertEqual(len(questions), 50)
            self.assertTrue(mock_session.get("is_final_exam"))


if __name__ == "__main__":
    unittest.main()
