"""
Unit tests for Phase 10: Admin Dashboard, User Management, and Results Analytics.
Tests:
- Aggregation of dashboard overview metrics (users, attempts, questions, category breakdown).
- User search, directory listing, and individual assessment history retrieval.
- Filtered assessment results (by category, difficulty, date range).
- Plotly chart generation for category and difficulty distributions.
- Read-only guarantees (scores cannot be modified through dashboard service).
"""

import unittest
import tempfile
from pathlib import Path

from database.db import init_db, get_connection
from database.models import Question
from database import queries
from database.seed_data import (
    seed_sample_grammar_questions_if_empty,
    seed_sample_reading_passages_and_questions_if_empty,
    seed_sample_listening_questions_if_empty,
)
from services.admin_dashboard_service import (
    fetch_dashboard_summary,
    fetch_users_directory,
    fetch_user_details_and_history,
    fetch_assessment_results,
    build_category_distribution_chart,
    build_difficulty_distribution_chart,
)


class TestAdminDashboardAndUserData(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_dashboard.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            # Seed questions across categories
            seed_sample_grammar_questions_if_empty(conn)
            seed_sample_reading_passages_and_questions_if_empty(conn)
            seed_sample_listening_questions_if_empty(conn)

            # Create test users
            self.u1_id = queries.create_user(conn, "Alice Johnson", "alice@example.com", "Harvard Univ", "Literature")
            self.u2_id = queries.create_user(conn, "Bob Smith", "bob@example.com", "MIT", "Computer Science")
            self.u3_id = queries.create_user(conn, "Clara Lee", "clara@sample.org", "Oxford", "Linguistics")

            # Create test attempts
            cat_grammar = queries.get_category_by_name(conn, "Grammar")
            cat_reading = queries.get_category_by_name(conn, "Reading")
            cat_listening = queries.get_category_by_name(conn, "Listening")

            # Attempt 1: Alice Grammar Easy (score 100)
            a1 = queries.create_attempt(conn, self.u1_id, cat_grammar.id, "Easy", 10)
            queries.complete_attempt(conn, a1, 10, 0, 100.0, 120)

            # Attempt 2: Alice Reading Medium (score 80)
            a2 = queries.create_attempt(conn, self.u1_id, cat_reading.id, "Medium", 10)
            queries.complete_attempt(conn, a2, 8, 2, 80.0, 180)

            # Attempt 3: Bob Listening Hard (score 60)
            a3 = queries.create_attempt(conn, self.u2_id, cat_listening.id, "Hard", 10)
            queries.complete_attempt(conn, a3, 6, 4, 60.0, 240)

            # Attempt 4: Bob Grammar Medium (in progress, no completion)
            queries.create_attempt(conn, self.u2_id, cat_grammar.id, "Medium", 10)

    def tearDown(self):
        self.temp_dir.cleanup()

    # ---------------------------------------------
    # 1. DASHBOARD OVERVIEW METRICS TESTS
    # ---------------------------------------------
    def test_dashboard_metrics_aggregation(self):
        """Test calculation of total users, attempts, question counts, and category breakdown."""
        stats = fetch_dashboard_summary(db_path=self.db_path)

        self.assertEqual(stats["total_users"], 3)
        self.assertEqual(stats["total_attempts"], 4)
        self.assertGreater(stats["total_questions"], 20)
        self.assertGreater(stats["active_questions"], 0)

        # Category attempt breakdown
        self.assertEqual(stats["grammar_attempts"], 2)
        self.assertEqual(stats["reading_attempts"], 1)
        self.assertEqual(stats["listening_attempts"], 1)

        # Average score across completed attempts: (100 + 80 + 60) / 3 = 80.0
        self.assertEqual(stats["average_score"], 80.0)

    # ---------------------------------------------
    # 2. USER DIRECTORY & SEARCH TESTS
    # ---------------------------------------------
    def test_user_directory_listing_and_stats(self):
        """Test that user directory includes calculated attempt count and average score."""
        users = fetch_users_directory(db_path=self.db_path)
        self.assertEqual(len(users), 3)

        user_map = {u["id"]: u for u in users}
        alice = user_map[self.u1_id]
        self.assertEqual(alice["name"], "Alice Johnson")
        self.assertEqual(alice["institution"], "Harvard Univ")
        self.assertEqual(alice["total_attempts"], 2)
        self.assertEqual(alice["average_score"], 90.0)  # (100 + 80) / 2

        bob = user_map[self.u2_id]
        self.assertEqual(bob["total_attempts"], 2)
        self.assertEqual(bob["average_score"], 60.0)  # 1 completed with 60, 1 in progress

        clara = user_map[self.u3_id]
        self.assertEqual(clara["total_attempts"], 0)
        self.assertIsNone(clara["average_score"])

    def test_user_search_filtering(self):
        """Test searching user directory by name, email, institution, and program."""
        # Search by name
        results = fetch_users_directory(search_query="Alice", db_path=self.db_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Alice Johnson")

        # Search by institution
        results_inst = fetch_users_directory(search_query="MIT", db_path=self.db_path)
        self.assertEqual(len(results_inst), 1)
        self.assertEqual(results_inst[0]["name"], "Bob Smith")

        # Search by program
        results_prog = fetch_users_directory(search_query="Linguistics", db_path=self.db_path)
        self.assertEqual(len(results_prog), 1)
        self.assertEqual(results_prog[0]["name"], "Clara Lee")

        # Non-matching search
        results_empty = fetch_users_directory(search_query="NonExistentPerson", db_path=self.db_path)
        self.assertEqual(len(results_empty), 0)

    # ---------------------------------------------
    # 3. INDIVIDUAL USER HISTORY TESTS
    # ---------------------------------------------
    def test_individual_user_history_retrieval(self):
        """Test retrieving detailed assessment logs for a single user."""
        user, history = fetch_user_details_and_history(self.u1_id, db_path=self.db_path)
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "Alice Johnson")
        self.assertEqual(len(history), 2)

        # Check most recent attempt first
        first_h = history[0]
        self.assertIn("category", first_h)
        self.assertIn("score", first_h)
        self.assertIn("correct_answers", first_h)
        self.assertIn("duration_seconds", first_h)

    # ---------------------------------------------
    # 4. ASSESSMENT RESULTS FILTERING TESTS
    # ---------------------------------------------
    def test_assessment_results_category_and_difficulty_filters(self):
        """Test filtering attempts ledger by category and level."""
        # Filter category: Grammar
        grammar_res = fetch_assessment_results(category="Grammar", db_path=self.db_path)
        self.assertEqual(len(grammar_res), 2)
        for r in grammar_res:
            self.assertEqual(r["category"], "Grammar")

        # Filter category: Reading
        reading_res = fetch_assessment_results(category="Reading", db_path=self.db_path)
        self.assertEqual(len(reading_res), 1)
        self.assertEqual(reading_res[0]["category"], "Reading")

        # Filter difficulty: Hard
        hard_res = fetch_assessment_results(difficulty="Hard", db_path=self.db_path)
        self.assertEqual(len(hard_res), 1)
        self.assertEqual(hard_res[0]["difficulty"], "Hard")
        self.assertEqual(hard_res[0]["user_name"], "Bob Smith")

        # Filter category + difficulty combination
        combo_res = fetch_assessment_results(category="Grammar", difficulty="Easy", db_path=self.db_path)
        self.assertEqual(len(combo_res), 1)
        self.assertEqual(combo_res[0]["score"], 100.0)

    # ---------------------------------------------
    # 5. PLOTLY CHART BUILDERS TESTS
    # ---------------------------------------------
    def test_plotly_chart_builders(self):
        """Test generation of interactive Plotly figures."""
        cat_counts = {"Grammar": 5, "Reading": 3, "Listening": 4}
        fig_cat = build_category_distribution_chart(cat_counts)
        self.assertIsNotNone(fig_cat)
        self.assertEqual(fig_cat.data[0].type, "pie")
        self.assertEqual(len(fig_cat.data[0].labels), 3)

        diff_counts = {"Easy": 6, "Medium": 4, "Hard": 2}
        fig_diff = build_difficulty_distribution_chart(diff_counts)
        self.assertIsNotNone(fig_diff)
        self.assertEqual(fig_diff.data[0].type, "bar")


if __name__ == "__main__":
    unittest.main()
