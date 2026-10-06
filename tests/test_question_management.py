"""
Unit tests for Phase 11: Admin Question Bank Management.
Tests:
- Payload validation for Grammar, Reading, and Listening questions.
- Rejection of invalid questions (missing fields, duplicate options, invalid answers).
- Question creation (add) for Grammar, Reading (with passage), Listening (with audio).
- Question retrieval and detail inspection.
- Question modification (edit/update).
- Status transitions: Active, Inactive (deactivate), Archived, Draft.
- Multi-dimensional filtering (category, difficulty, status, topic) and keyword search.
"""

import unittest
import tempfile
from pathlib import Path

from database.db import init_db, get_connection
from database import queries
from database.seed_data import (
    seed_sample_grammar_questions_if_empty,
    seed_sample_reading_passages_and_questions_if_empty,
    seed_sample_listening_questions_if_empty,
)
from services.question_service import (
    validate_question_payload,
    add_question,
    update_question_record,
    fetch_questions,
    fetch_question_by_id,
    deactivate_question,
    archive_question,
    activate_question,
    change_status,
    fetch_distinct_skill_numbers,
)


class TestQuestionBankManagement(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_qbank.db"
        init_db(self.db_path)

        with get_connection(self.db_path) as conn:
            seed_sample_grammar_questions_if_empty(conn)
            seed_sample_reading_passages_and_questions_if_empty(conn)
            seed_sample_listening_questions_if_empty(conn)

    def tearDown(self):
        self.temp_dir.cleanup()

    # ---------------------------------------------
    # 1. VALIDATION TESTS
    # ---------------------------------------------
    def test_validation_rejects_missing_or_invalid_fields(self):
        """Test that invalid payloads are strictly rejected by the validator."""
        # 1. Missing question text
        bad1 = {
            "category": "Grammar",
            "difficulty": "Easy",
            "status": "Active",
            "question_text": "",
            "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
            "correct_answer": "A",
            "explanation": "Valid explanation here.",
        }
        val1, msg1 = validate_question_payload(bad1)
        self.assertFalse(val1)
        self.assertIn("Question text", msg1)

        # 2. Duplicate options
        bad2 = {
            "category": "Grammar",
            "difficulty": "Easy",
            "status": "Active",
            "question_text": "Choose the correct verb form:",
            "option_a": "same choice",
            "option_b": "same choice",
            "option_c": "other choice",
            "option_d": "fourth choice",
            "correct_answer": "A",
            "explanation": "Valid explanation here.",
        }
        val2, msg2 = validate_question_payload(bad2)
        self.assertFalse(val2)
        self.assertIn("distinct", msg2)

        # 3. Invalid correct answer key
        bad3 = {
            "category": "Grammar",
            "difficulty": "Easy",
            "status": "Active",
            "question_text": "Choose the correct verb form:",
            "option_a": "opt1", "option_b": "opt2", "option_c": "opt3", "option_d": "opt4",
            "correct_answer": "Z",
            "explanation": "Valid explanation here.",
        }
        val3, msg3 = validate_question_payload(bad3)
        self.assertFalse(val3)
        self.assertIn("Correct answer must be one of", msg3)

        # 4. Reading question without passage
        bad_reading = {
            "category": "Reading",
            "difficulty": "Medium",
            "status": "Active",
            "question_text": "What is the primary theme of the passage?",
            "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
            "correct_answer": "A",
            "explanation": "Valid explanation.",
        }
        val_r, msg_r = validate_question_payload(bad_reading)
        self.assertFalse(val_r)
        self.assertIn("reading passage", msg_r)

        # 5. Listening question without audio file
        bad_listening = {
            "category": "Listening",
            "difficulty": "Hard",
            "status": "Active",
            "question_text": "What did the speaker mention about the flight?",
            "option_a": "A", "option_b": "B", "option_c": "C", "option_d": "D",
            "correct_answer": "B",
            "explanation": "Valid explanation.",
        }
        val_l, msg_l = validate_question_payload(bad_listening)
        self.assertFalse(val_l)
        self.assertIn("audio file", msg_l)

    # ---------------------------------------------
    # 2. CREATE (ADD) QUESTIONS ACROSS CATEGORIES
    # ---------------------------------------------
    def test_add_grammar_question(self):
        """Test creating a valid Grammar question."""
        payload = {
            "category": "Grammar",
            "difficulty": "Easy",
            "status": "Active",
            "subtopic": "Pronouns",
            "question_type": "Multiple Choice",
            "question_text": "Neither of the boys brought ___ lunch to school.",
            "option_a": "his",
            "option_b": "their",
            "option_c": "they're",
            "option_d": "its",
            "correct_answer": "A",
            "explanation": "'Neither' is a singular indefinite pronoun requiring singular pronoun 'his'.",
        }
        success, q_id, msg = add_question(payload, db_path=self.db_path)
        self.assertTrue(success, f"Failed adding grammar question: {msg}")
        self.assertIsNotNone(q_id)

        # Retrieve and verify
        q = fetch_question_by_id(q_id, db_path=self.db_path)
        self.assertIsNotNone(q)
        self.assertEqual(q["category_name"], "Grammar")
        self.assertEqual(q["correct_answer"], "A")
        self.assertEqual(q["status"], "Active")
        self.assertEqual(q["difficulty"], "Easy")

    def test_add_reading_question_with_new_passage(self):
        """Test creating a Reading question with an on-the-fly passage."""
        payload = {
            "category": "Reading",
            "difficulty": "Medium",
            "status": "Active",
            "subtopic": "Marine Science",
            "question_type": "Main Idea",
            "new_passage_title": "Hydrothermal Vent Biology",
            "new_passage_text": "Hydrothermal vents support unique deep-sea ecosystems powered by chemosynthetic bacteria rather than sunlight.",
            "question_text": "According to the passage, what powers life around hydrothermal vents?",
            "option_a": "Chemosynthetic bacteria",
            "option_b": "Solar radiation",
            "option_c": "Volcanic magma ash",
            "option_d": "Surface algae currents",
            "correct_answer": "A",
            "explanation": "The text explicitly states the ecosystems are powered by chemosynthetic bacteria.",
        }
        success, q_id, msg = add_question(payload, db_path=self.db_path)
        self.assertTrue(success, f"Failed adding reading question: {msg}")

        q = fetch_question_by_id(q_id, db_path=self.db_path)
        self.assertIsNotNone(q)
        self.assertEqual(q["category_name"], "Reading")
        self.assertIsNotNone(q["passage_id"])
        self.assertIn("Hydrothermal", q["passage_title"])

    def test_add_listening_question_with_audio_asset(self):
        """Test creating a Listening question with audio file path and transcript."""
        payload = {
            "category": "Listening",
            "difficulty": "Hard",
            "status": "Draft",
            "subtopic": "Aviation",
            "question_type": "Detail",
            "audio_file": "audio/listening/listening_test_phase11.mp3",
            "audio_transcript": "Captain: We are beginning our initial descent into Seattle Tacoma International.",
            "question_text": "What did the captain announce?",
            "option_a": "Initial descent into Seattle",
            "option_b": "A delay due to turbulence",
            "option_c": "Diversion to Portland",
            "option_d": "Emergency fuel dumping",
            "correct_answer": "A",
            "explanation": "The captain explicitly announces the beginning of initial descent into Seattle.",
        }
        success, q_id, msg = add_question(payload, db_path=self.db_path)
        self.assertTrue(success)

        q = fetch_question_by_id(q_id, db_path=self.db_path)
        self.assertIsNotNone(q)
        self.assertEqual(q["category_name"], "Listening")
        self.assertEqual(q["status"], "Draft")
        self.assertEqual(q["audio_file"], "audio/listening/listening_test_phase11.mp3")
        self.assertIn("Seattle", q["audio_transcript"])

    # ---------------------------------------------
    # 3. UPDATE (EDIT) QUESTIONS
    # ---------------------------------------------
    def test_update_existing_question(self):
        """Test modifying an existing question in the bank."""
        # Grab first question
        existing_list = fetch_questions(limit=1, db_path=self.db_path)
        self.assertTrue(len(existing_list) > 0)
        target = existing_list[0]
        q_id = target["id"]

        updated_payload = {
            "category": target["category_name"],
            "difficulty": "Hard",
            "status": "Draft",
            "subtopic": "Modified Subtopic",
            "question_type": target["question_type"],
            "question_text": "This is an edited question prompt for testing.",
            "option_a": "Edited Option Alpha",
            "option_b": "Edited Option Beta",
            "option_c": "Edited Option Gamma",
            "option_d": "Edited Option Delta",
            "correct_answer": "C",
            "explanation": "Updated explanation with clear pedagogical reasoning.",
            "passage_id": target.get("passage_id"),
            "audio_file": target.get("audio_file") or ("audio/listening/test.mp3" if target["category_name"] == "Listening" else None),
        }

        ok, msg = update_question_record(q_id, updated_payload, db_path=self.db_path)
        self.assertTrue(ok, f"Failed updating question: {msg}")

        # Verify modifications
        refetched = fetch_question_by_id(q_id, db_path=self.db_path)
        self.assertEqual(refetched["question_text"], "This is an edited question prompt for testing.")
        self.assertEqual(refetched["difficulty"], "Hard")
        self.assertEqual(refetched["status"], "Draft")
        self.assertEqual(refetched["correct_answer"], "C")

    # ---------------------------------------------
    # 4. STATUS TRANSITIONS (DEACTIVATE, ARCHIVE, ACTIVATE)
    # ---------------------------------------------
    def test_status_transitions(self):
        """Test deactivating, archiving, and reactivating a question."""
        q_list = fetch_questions(limit=1, db_path=self.db_path)
        q_id = q_list[0]["id"]

        # Deactivate
        ok_d, msg_d = deactivate_question(q_id, db_path=self.db_path)
        self.assertTrue(ok_d)
        q = fetch_question_by_id(q_id, db_path=self.db_path)
        self.assertEqual(q["status"], "Inactive")

        # Archive
        ok_a, msg_a = archive_question(q_id, db_path=self.db_path)
        self.assertTrue(ok_a)
        q = fetch_question_by_id(q_id, db_path=self.db_path)
        self.assertEqual(q["status"], "Archived")

        # Re-activate
        ok_act, msg_act = activate_question(q_id, db_path=self.db_path)
        self.assertTrue(ok_act)
        q = fetch_question_by_id(q_id, db_path=self.db_path)
        self.assertEqual(q["status"], "Active")

        # Draft
        ok_dr, msg_dr = change_status(q_id, "Draft", db_path=self.db_path)
        self.assertTrue(ok_dr)
        q = fetch_question_by_id(q_id, db_path=self.db_path)
        self.assertEqual(q["status"], "Draft")

    # ---------------------------------------------
    # 5. FILTERING AND SEARCHING
    # ---------------------------------------------
    def test_filtering_and_keyword_searching(self):
        """Test filtering by category, difficulty, status, and searching keywords."""
        # Filter by Category: Grammar
        grammar_qs = fetch_questions(category="Grammar", db_path=self.db_path)
        self.assertGreater(len(grammar_qs), 0)
        for q in grammar_qs:
            self.assertEqual(q["category_name"], "Grammar")

        # Filter by Difficulty: Easy
        easy_qs = fetch_questions(difficulty="Easy", db_path=self.db_path)
        self.assertGreater(len(easy_qs), 0)
        for q in easy_qs:
            self.assertEqual(q["difficulty"], "Easy")

        # Keyword Search
        search_res = fetch_questions(search="classroom", db_path=self.db_path)
        self.assertGreater(len(search_res), 0)

    def test_fetch_distinct_skill_numbers(self):
        """Test dynamic discovery of distinct skill numbers, including newly uploaded/created skills."""
        initial_skills = fetch_distinct_skill_numbers(db_path=self.db_path)
        self.assertIn(1, initial_skills)

        # Add a question with high skill number (e.g. Skill 27)
        payload = {
            "category": "Grammar",
            "difficulty": "Medium",
            "status": "Active",
            "subtopic": "Inversion",
            "question_type": "Multiple Choice",
            "question_text": "Not only ___ the test, but she also scored 100%.",
            "option_a": "did she pass",
            "option_b": "she passed",
            "option_c": "passed she",
            "option_d": "she did pass",
            "correct_answer": "A",
            "explanation": "Negative inversion.",
            "skill_number": 27,
            "skill_name": "Inversion with Negative Adverbials",
            "question_order": 1,
        }
        ok, q_id, msg = add_question(payload, db_path=self.db_path)
        self.assertTrue(ok, msg)

        # Verify skill 27 is immediately discovered dynamically
        updated_skills = fetch_distinct_skill_numbers(db_path=self.db_path)
        self.assertIn(27, updated_skills)

        # Also verify category-filtered retrieval
        grammar_skills = fetch_distinct_skill_numbers(category_name="Grammar", db_path=self.db_path)
        self.assertIn(27, grammar_skills)


if __name__ == "__main__":
    unittest.main()
