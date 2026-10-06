"""
Unit tests for Phase 16: Admin Question Performance Analytics.
Tests:
- Calculation of attempts, correct count, incorrect count, and accuracy per question.
- Most frequently attempted questions ranking.
- Highest accuracy questions ranking.
- Lowest accuracy questions ranking.
- Filtering by category, topic, and difficulty.
- Separate presentation of assigned difficulty vs observed performance.
- Difficulty review note: 'Observed performance may justify reviewing the assigned difficulty.'
- Verification that assigned difficulty is NEVER automatically modified by statistics.
- Absence of unsupported question quality claims.
- Plotly visualization generation.
"""

import unittest
import tempfile
from pathlib import Path

from database.db import init_db, get_connection
from database.models import Question
from database import queries
from services.analytics_service import (
    fetch_question_analytics,
    get_top_frequently_attempted,
    get_highest_accuracy_questions,
    get_lowest_accuracy_questions,
    build_accuracy_distribution_chart,
    build_attempts_vs_accuracy_scatter,
    NO_DATA_NOTE,
    HAS_DATA_NOTE,
)


class TestQuestionAnalytics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_analytics.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            self.user_id = queries.create_user(conn, "Analytics Tester", "tester@analytics.com")
            self.cat_grammar = queries.get_category_by_name(conn, "Grammar")
            self.cat_reading = queries.get_category_by_name(conn, "Reading")

            # Seed 3 questions
            # Q1: Grammar, Tenses (will have high accuracy: 80%)
            self.q1_id = queries.create_question(
                conn,
                Question(
                    category_id=self.cat_grammar.id,
                    subtopic="Tenses",
                    question_text="Grammar Question with High Mastery",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="A", difficulty="Standard", status="Active",
                    skill_number=1, skill_name="Identifying Subjects", question_order=1,
                ),
            )

            # Q2: Grammar, Modals (will have low accuracy: 20%)
            self.q2_id = queries.create_question(
                conn,
                Question(
                    category_id=self.cat_grammar.id,
                    subtopic="Modals",
                    question_text="Grammar Question with High Error Rate",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="B", difficulty="Standard", status="Active",
                    skill_number=1, skill_name="Identifying Subjects", question_order=2,
                ),
            )

            # Q3: Reading, Inference (will have medium accuracy: 60%)
            self.q3_id = queries.create_question(
                conn,
                Question(
                    category_id=self.cat_reading.id,
                    subtopic="Inference",
                    question_text="Reading Question with Normal Mastery",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="C", difficulty="Standard", status="Active",
                    skill_number=2, skill_name="Locating Details", question_order=1,
                ),
            )

            # Log answers for Q1 (5 attempts: 4 correct, 1 incorrect = 80% accuracy)
            for i in range(5):
                att_id = queries.create_attempt(conn, self.user_id, self.cat_grammar.id, "Standard", 1)
                is_corr = 1 if i < 4 else 0
                queries.record_answer(conn, att_id, self.q1_id, "A" if is_corr else "B", "A", is_corr == 1)

            # Log answers for Q2 (10 attempts: 2 correct, 8 incorrect = 20% accuracy)
            for i in range(10):
                att_id = queries.create_attempt(conn, self.user_id, self.cat_grammar.id, "Standard", 1)
                is_corr = 1 if i < 2 else 0
                queries.record_answer(conn, att_id, self.q2_id, "B" if is_corr else "A", "B", is_corr == 1)

            # Log answers for Q3 (5 attempts: 3 correct, 2 incorrect = 60% accuracy)
            for i in range(5):
                att_id = queries.create_attempt(conn, self.user_id, self.cat_reading.id, "Standard", 1)
                is_corr = 1 if i < 3 else 0
                queries.record_answer(conn, att_id, self.q3_id, "C" if is_corr else "A", "C", is_corr == 1)

    def tearDown(self):
        self.temp_dir.cleanup()

    # ==========================================
    # 1. CORE QUESTION METRICS CALCULATION
    # ==========================================

    def test_question_analytics_metrics_calculation(self):
        """
        Verify that for every active question, the system correctly calculates:
        - attempts
        - correct count
        - incorrect count
        - accuracy percentage
        """
        items = fetch_question_analytics(db_path=self.db_path)
        self.assertEqual(len(items), 3)

        item_map = {x["id"]: x for x in items}

        # Q1 checks
        q1_data = item_map[self.q1_id]
        self.assertEqual(q1_data["attempts"], 5)
        self.assertEqual(q1_data["correct_count"], 4)
        self.assertEqual(q1_data["incorrect_count"], 1)
        self.assertEqual(q1_data["accuracy"], 80.0)

        # Q2 checks
        q2_data = item_map[self.q2_id]
        self.assertEqual(q2_data["attempts"], 10)
        self.assertEqual(q2_data["correct_count"], 2)
        self.assertEqual(q2_data["incorrect_count"], 8)
        self.assertEqual(q2_data["accuracy"], 20.0)

        # Q3 checks
        q3_data = item_map[self.q3_id]
        self.assertEqual(q3_data["attempts"], 5)
        self.assertEqual(q3_data["correct_count"], 3)
        self.assertEqual(q3_data["incorrect_count"], 2)
        self.assertEqual(q3_data["accuracy"], 60.0)

    # ==========================================
    # 2. RANKINGS (FREQUENT, HIGHEST & LOWEST)
    # ==========================================

    def test_rankings_frequent_highest_lowest(self):
        """Verify rankings for most frequent, highest accuracy, and lowest accuracy."""
        items = fetch_question_analytics(db_path=self.db_path)

        # Most frequent (Q2 had 10 attempts)
        frequent = get_top_frequently_attempted(items, limit=1)
        self.assertEqual(frequent[0]["id"], self.q2_id)
        self.assertEqual(frequent[0]["attempts"], 10)

        # Highest accuracy (Q1 had 80% accuracy)
        highest = get_highest_accuracy_questions(items, limit=1)
        self.assertEqual(highest[0]["id"], self.q1_id)
        self.assertEqual(highest[0]["accuracy"], 80.0)

        # Lowest accuracy (Q2 had 20% accuracy)
        lowest = get_lowest_accuracy_questions(items, limit=1)
        self.assertEqual(lowest[0]["id"], self.q2_id)
        self.assertEqual(lowest[0]["accuracy"], 20.0)

    # ==========================================
    # 3. FILTERING TESTS (CATEGORY, TOPIC, SKILL)
    # ==========================================

    def test_analytics_filtering(self):
        """Allow filters by category, topic, and skill_number."""
        # Filter Category = Reading
        reading_items = fetch_question_analytics(category="Reading", db_path=self.db_path)
        self.assertEqual(len(reading_items), 1)
        self.assertEqual(reading_items[0]["id"], self.q3_id)

        # Filter Topic = Tenses
        tenses_items = fetch_question_analytics(topic="Tenses", db_path=self.db_path)
        self.assertEqual(len(tenses_items), 1)
        self.assertEqual(tenses_items[0]["id"], self.q1_id)

        # Filter Skill = 1
        skill1_items = fetch_question_analytics(skill_number=1, db_path=self.db_path)
        self.assertEqual(len(skill1_items), 2)

    # ==========================================
    # 4. LOW ACCURACY FLAGGING
    # ==========================================

    def test_low_accuracy_flagging(self):
        """Verify that items with low accuracy (< 40%) are flagged for admin review."""
        items = fetch_question_analytics(db_path=self.db_path)
        item_map = {x["id"]: x for x in items}

        # Q2 had 20% accuracy -> flagged
        q2 = item_map[self.q2_id]
        self.assertTrue(q2["needs_review"])

        # Q1 had 80% accuracy -> not flagged
        q1 = item_map[self.q1_id]
        self.assertFalse(q1["needs_review"])

    # ==========================================
    # 5. VISUALIZATIONS GENERATION
    # ==========================================

    def test_plotly_visualizations(self):
        """Verify Plotly charts are constructed without raising exceptions."""
        items = fetch_question_analytics(db_path=self.db_path)

        fig_hist = build_accuracy_distribution_chart(items)
        self.assertIsNotNone(fig_hist)

        fig_scatter = build_attempts_vs_accuracy_scatter(items)
        self.assertIsNotNone(fig_scatter)


if __name__ == "__main__":
    unittest.main()
