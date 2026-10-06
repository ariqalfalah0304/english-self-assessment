"""
Unit tests for Phase 14: Dynamic Question Selection and Repetition Control.
Tests:
- Category filtering: strictly returns questions matching requested category.
- Difficulty filtering: strictly returns questions matching requested difficulty.
- Active status enforcement: strictly excludes Draft, Inactive, and Archived questions.
- Duplicate prevention: zero duplicate question IDs within any single attempt.
- History exclusion: excludes recently seen questions when enough unused questions exist.
- Insufficient question bank: gracefully reuses questions and provides clear notice when bank < requested.
- Question order randomization: varies question sequence across attempts.
- Safe option shuffling: shuffles options when safe while strictly preserving the correct answer content.
- Unsafe option preservation: preserves original option order when choices contain 'All of the above', etc.
- Reading passage relationship: maintains contiguous grouping of passage-linked questions.
- Listening audio relationship: attaches and preserves audio metadata on selected items.
"""

import unittest
import tempfile
import random
from pathlib import Path
from unittest.mock import patch

from database.db import init_db, get_connection
from database.models import Question, Passage, AudioFile
from database import queries
from services.question_selector import (
    select_quiz_questions,
    is_option_shuffling_safe,
    shuffle_options_safely,
)
from services.quiz_engine import start_quiz_attempt


class TestQuestionSelectionAndRepetition(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_selection.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            # Users
            self.user1_id = queries.create_user(conn, "Alice User", "alice@test.com")
            self.user2_id = queries.create_user(conn, "Bob User", "bob@test.com")

            # Categories (1=Grammar, 2=Reading, 3=Listening from seed)
            self.cat_grammar = queries.get_category_by_name(conn, "Grammar")
            self.cat_reading = queries.get_category_by_name(conn, "Reading")
            self.cat_listening = queries.get_category_by_name(conn, "Listening")

    def tearDown(self):
        self.temp_dir.cleanup()

    # ==========================================
    # 1. CATEGORY & DIFFICULTY FILTERING TESTS
    # ==========================================

    def test_category_filtering(self):
        """Ensure selection strictly isolates questions belonging to the requested category."""
        with get_connection(self.db_path) as conn:
            # Insert 3 Grammar questions
            for i in range(3):
                queries.create_question(
                    conn,
                    Question(
                        category_id=self.cat_grammar.id,
                        question_text=f"Grammar Q{i+1}",
                        option_a="A", option_b="B", option_c="C", option_d="D",
                        correct_answer="A", difficulty="Medium", status="Active",
                    ),
                )
            # Insert 3 Reading questions
            for i in range(3):
                queries.create_question(
                    conn,
                    Question(
                        category_id=self.cat_reading.id,
                        question_text=f"Reading Q{i+1}",
                        option_a="A", option_b="B", option_c="C", option_d="D",
                        correct_answer="A", difficulty="Medium", status="Active",
                    ),
                )

            selected_g, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Grammar",
                category_id=self.cat_grammar.id,
                difficulty="Medium",
                requested_count=5,
            )

            self.assertEqual(len(selected_g), 3)
            for q in selected_g:
                self.assertEqual(q["category_id"], self.cat_grammar.id)
                self.assertTrue(q["question_text"].startswith("Grammar"))

    def test_difficulty_filtering(self):
        """Ensure selection strictly matches requested difficulty level."""
        with get_connection(self.db_path) as conn:
            # Insert Easy and Hard Grammar questions
            for i in range(4):
                queries.create_question(
                    conn,
                    Question(
                        category_id=self.cat_grammar.id,
                        question_text=f"Easy Q{i+1}",
                        option_a="A", option_b="B", option_c="C", option_d="D",
                        correct_answer="A", difficulty="Easy", status="Active",
                    ),
                )
            for i in range(3):
                queries.create_question(
                    conn,
                    Question(
                        category_id=self.cat_grammar.id,
                        question_text=f"Hard Q{i+1}",
                        option_a="A", option_b="B", option_c="C", option_d="D",
                        correct_answer="A", difficulty="Hard", status="Active",
                    ),
                )

            selected_easy, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Grammar",
                category_id=self.cat_grammar.id,
                difficulty="Easy",
                requested_count=10,
            )

            self.assertEqual(len(selected_easy), 4)
            for q in selected_easy:
                self.assertEqual(q["difficulty"], "Easy")

    # ==========================================
    # 2. ACTIVE STATUS ENFORCEMENT
    # ==========================================

    def test_active_status_enforcement(self):
        """Public quiz must NEVER expose questions in Draft, Inactive, or Archived status."""
        with get_connection(self.db_path) as conn:
            statuses = ["Active", "Draft", "Inactive", "Archived"]
            for idx, st in enumerate(statuses):
                queries.create_question(
                    conn,
                    Question(
                        category_id=self.cat_grammar.id,
                        question_text=f"Status Question {st}",
                        option_a="A", option_b="B", option_c="C", option_d="D",
                        correct_answer="A", difficulty="Easy", status=st,
                    ),
                )

            selected, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Grammar",
                category_id=self.cat_grammar.id,
                difficulty="Easy",
                requested_count=10,
            )

            # Only the single 'Active' question should be selected
            self.assertEqual(len(selected), 1)
            self.assertEqual(selected[0]["status"], "Active")
            self.assertEqual(selected[0]["question_text"], "Status Question Active")

    # ==========================================
    # 3. DUPLICATE PREVENTION & RANDOMIZATION
    # ==========================================

    def test_duplicate_prevention(self):
        """Zero duplicate questions within any single attempt."""
        with get_connection(self.db_path) as conn:
            for i in range(12):
                queries.create_question(
                    conn,
                    Question(
                        category_id=self.cat_grammar.id,
                        question_text=f"Unique Question {i+1}",
                        option_a="A", option_b="B", option_c="C", option_d="D",
                        correct_answer="A", difficulty="Medium", status="Active",
                    ),
                )

            selected, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Grammar",
                category_id=self.cat_grammar.id,
                difficulty="Medium",
                requested_count=8,
            )

            self.assertEqual(len(selected), 8)
            selected_ids = [q["id"] for q in selected]
            self.assertEqual(len(selected_ids), len(set(selected_ids)), "Duplicate question IDs detected in attempt!")

    def test_question_order_randomization(self):
        """Question order is randomized across distinct attempts."""
        with get_connection(self.db_path) as conn:
            for i in range(15):
                queries.create_question(
                    conn,
                    Question(
                        category_id=self.cat_grammar.id,
                        question_text=f"Random Q {i+1}",
                        option_a="A", option_b="B", option_c="C", option_d="D",
                        correct_answer="A", difficulty="Medium", status="Active",
                    ),
                )

            # Run with two distinct random seeds
            res1, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Grammar",
                category_id=self.cat_grammar.id,
                difficulty="Medium",
                requested_count=10,
                rng=random.Random(42),
            )
            res2, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Grammar",
                category_id=self.cat_grammar.id,
                difficulty="Medium",
                requested_count=10,
                rng=random.Random(999),
            )

            ids1 = [q["id"] for q in res1]
            ids2 = [q["id"] for q in res2]
            self.assertNotEqual(ids1, ids2, "Question orders across different seeds should vary!")

    # ==========================================
    # 4. HISTORY EXCLUSION & GRACEFUL REUSE
    # ==========================================

    def test_history_exclusion_when_enough_unused_exist(self):
        """Avoid recently used questions by the same user when enough unused questions exist."""
        with get_connection(self.db_path) as conn:
            # Seed 10 questions
            created_ids = []
            for i in range(10):
                qid = queries.create_question(
                    conn,
                    Question(
                        category_id=self.cat_grammar.id,
                        question_text=f"Grammar Item {i+1}",
                        option_a="A", option_b="B", option_c="C", option_d="D",
                        correct_answer="A", difficulty="Hard", status="Active",
                    ),
                )
                created_ids.append(qid)

            # Record a past attempt for user1 using the first 5 questions (created_ids[0..4])
            att_id = queries.create_attempt(
                conn=conn,
                user_id=self.user1_id,
                category_id=self.cat_grammar.id,
                difficulty="Hard",
                total_questions=5,
            )
            queries.add_attempt_questions(conn, att_id, created_ids[:5])

            # Now User1 starts a new quiz for 5 questions
            new_selection, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Grammar",
                category_id=self.cat_grammar.id,
                difficulty="Hard",
                requested_count=5,
            )

            new_ids = set(q["id"] for q in new_selection)
            history_ids = set(created_ids[:5])

            # Zero overlap: new selection must draw exclusively from the 5 unused questions!
            overlap = new_ids.intersection(history_ids)
            self.assertEqual(len(overlap), 0, f"History exclusion failed: {overlap} were reused despite unused items existing.")

    def test_insufficient_question_bank_graceful_reuse(self):
        """If question bank is too small, gracefully reuse available questions without crashing."""
        with get_connection(self.db_path) as conn:
            # Only 3 active questions exist in total
            for i in range(3):
                queries.create_question(
                    conn,
                    Question(
                        category_id=self.cat_grammar.id,
                        question_text=f"Small Bank Q{i+1}",
                        option_a="A", option_b="B", option_c="C", option_d="D",
                        correct_answer="A", difficulty="Easy", status="Active",
                    ),
                )

            # Request 5 questions
            selected, notice = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Grammar",
                category_id=self.cat_grammar.id,
                difficulty="Easy",
                requested_count=5,
            )

            # Must return all 3 available without error
            self.assertEqual(len(selected), 3)
            self.assertIn("Only 3 questions are currently available", notice)

            # Record attempt so user has now seen all 3 questions
            att_id = queries.create_attempt(
                conn=conn,
                user_id=self.user1_id,
                category_id=self.cat_grammar.id,
                difficulty="Easy",
                total_questions=3,
            )
            queries.add_attempt_questions(conn, att_id, [q["id"] for q in selected])

            # Request again: since all 3 were seen, it gracefully reuses them
            second_attempt_qs, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Grammar",
                category_id=self.cat_grammar.id,
                difficulty="Easy",
                requested_count=3,
            )
            self.assertEqual(len(second_attempt_qs), 3)

    # ==========================================
    # 5. SAFE OPTION SHUFFLING & PRESERVATION
    # ==========================================

    def test_safe_option_shuffling_preserves_correct_answer(self):
        """Randomize answer option order where safe, strictly preserving the correct answer."""
        q_dict = {
            "option_a": "Paris",
            "option_b": "London",
            "option_c": "Rome",
            "option_d": "Berlin",
            "correct_answer": "B",  # London
        }

        # Shuffle with controlled RNG
        shuffled = shuffle_options_safely(dict(q_dict), rng=random.Random(12345))

        self.assertTrue(shuffled["options_shuffled"])
        new_key = shuffled["correct_answer"]
        key_map = {"A": shuffled["option_a"], "B": shuffled["option_b"], "C": shuffled["option_c"], "D": shuffled["option_d"]}

        # London MUST still be the correct answer content!
        self.assertEqual(key_map[new_key], "London")

    def test_unsafe_options_are_never_shuffled(self):
        """Options with 'All of the above', 'Both A and B', etc. must NOT be shuffled."""
        unsafe_cases = [
            ["Option 1", "Option 2", "Option 3", "All of the above"],
            ["None of the above", "Option 2", "Option 3", "Option 4"],
            ["Option A", "Option B", "Both A and B", "Neither"],
            ["Choice A", "Choice B", "Neither A nor B", "Other"],
        ]

        for opts in unsafe_cases:
            self.assertFalse(is_option_shuffling_safe(opts))
            q_dict = {
                "option_a": opts[0],
                "option_b": opts[1],
                "option_c": opts[2],
                "option_d": opts[3],
                "correct_answer": "D",
            }
            res = shuffle_options_safely(dict(q_dict))
            self.assertFalse(res["options_shuffled"])
            self.assertEqual(res["option_d"], opts[3])
            self.assertEqual(res["correct_answer"], "D")

    # ==========================================
    # 6. PASSAGE & AUDIO RELATIONSHIP PRESERVATION
    # ==========================================

    def test_reading_passage_relationship_preserved(self):
        """Preserve reading passage relationships: questions for a passage remain contiguous."""
        with get_connection(self.db_path) as conn:
            # Create Passage 1 with 2 questions
            p1_id = queries.create_passage(conn, "Passage One", "Text of passage one.", self.cat_reading.id)
            q1 = queries.create_question(
                conn,
                Question(
                    category_id=self.cat_reading.id, passage_id=p1_id,
                    question_text="Passage 1 Question 1",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="A", difficulty="Medium", status="Active",
                ),
            )
            q2 = queries.create_question(
                conn,
                Question(
                    category_id=self.cat_reading.id, passage_id=p1_id,
                    question_text="Passage 1 Question 2",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="B", difficulty="Medium", status="Active",
                ),
            )

            # Create Passage 2 with 2 questions
            p2_id = queries.create_passage(conn, "Passage Two", "Text of passage two.", self.cat_reading.id)
            q3 = queries.create_question(
                conn,
                Question(
                    category_id=self.cat_reading.id, passage_id=p2_id,
                    question_text="Passage 2 Question 1",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="C", difficulty="Medium", status="Active",
                ),
            )
            q4 = queries.create_question(
                conn,
                Question(
                    category_id=self.cat_reading.id, passage_id=p2_id,
                    question_text="Passage 2 Question 2",
                    option_a="A", option_b="B", option_c="C", option_d="D",
                    correct_answer="D", difficulty="Medium", status="Active",
                ),
            )

            selected, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Reading",
                category_id=self.cat_reading.id,
                difficulty="Medium",
                requested_count=4,
            )

            self.assertEqual(len(selected), 4)

            # Verify passage details are attached to each question
            for q in selected:
                self.assertIn("passage_title", q)
                self.assertIn("passage_text", q)
                self.assertTrue(len(q["passage_text"]) > 0)

            # Verify contiguous grouping: questions of same passage are adjacent
            p_ids = [q["passage_id"] for q in selected]
            # Must be [P1, P1, P2, P2] or [P2, P2, P1, P1], never interleaved [P1, P2, P1, P2]
            self.assertEqual(p_ids[0], p_ids[1])
            self.assertEqual(p_ids[2], p_ids[3])
            self.assertNotEqual(p_ids[0], p_ids[2])

    def test_listening_audio_relationship_preserved(self):
        """Preserve listening audio relationships: audio_file, transcript, and duration attached."""
        with get_connection(self.db_path) as conn:
            qid = queries.create_question(
                conn,
                Question(
                    category_id=self.cat_listening.id,
                    question_text="What did the announcer say?",
                    option_a="Flight A", option_b="Flight B", option_c="Flight C", option_d="Flight D",
                    correct_answer="A", difficulty="Easy", status="Active",
                ),
            )
            queries.create_audio_file(
                conn=conn,
                question_id=qid,
                file_path="audio/listening/test_announcement.mp3",
                transcript="Attention passengers, flight 101 now boarding.",
                duration=12.5,
            )

            selected, _ = select_quiz_questions(
                conn=conn,
                user_id=self.user1_id,
                category_name="Listening",
                category_id=self.cat_listening.id,
                difficulty="Easy",
                requested_count=1,
            )

            self.assertEqual(len(selected), 1)
            q = selected[0]
            self.assertEqual(q["audio_file"], "audio/listening/test_announcement.mp3")
            self.assertEqual(q["transcript"], "Attention passengers, flight 101 now boarding.")
            self.assertEqual(q["duration"], 12.5)

    # ==========================================
    # 7. INTEGRATION WITH START_QUIZ_ATTEMPT
    # ==========================================

    def test_start_quiz_attempt_integration(self):
        """Verify full engine integration with session state and question models."""
        mock_session = {}
        with patch("streamlit.session_state", mock_session):
            with get_connection(self.db_path) as conn:
                for i in range(4):
                    queries.create_question(
                        conn,
                        Question(
                            category_id=self.cat_grammar.id,
                            question_text=f"Integration Grammar Q{i+1}",
                            option_a="A", option_b="B", option_c="C", option_d="D",
                            correct_answer="A", difficulty="Easy", status="Active",
                        ),
                    )

            success, attempt, questions, notice = start_quiz_attempt(
                user_id=self.user1_id,
                category_name="Grammar",
                difficulty="Easy",
                num_questions=4,
                db_path=self.db_path,
            )

            self.assertTrue(success)
            self.assertIsNotNone(attempt)
            self.assertEqual(len(questions), 4)
            for q in questions:
                self.assertEqual(q.difficulty, "Easy")
                self.assertEqual(q.status, "Active")


if __name__ == "__main__":
    unittest.main()
