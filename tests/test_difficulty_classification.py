"""
Unit tests for Phase 13: Rule-Based Difficulty Classification.
Tests:
- Grammar rule evaluation across Easy, Medium, and Hard samples.
- Reading rule evaluation across Easy, Medium, and Hard samples.
- Listening rule evaluation across Easy, Medium, and Hard samples.
- Factor extraction, scoring bounds (0-100), and pedagogical explanations.
- Docx parser integration providing suggested difficulty, score, and reason.
- Admin Override verification: Admin's chosen final difficulty overrides rule-based
  suggestion and is strictly persisted in the SQLite database.
"""

import unittest
import tempfile
from pathlib import Path

from database.db import init_db, get_connection
from database import queries
from utils.difficulty import (
    classify_difficulty,
    evaluate_grammar_difficulty,
    evaluate_reading_difficulty,
    evaluate_listening_difficulty,
    DifficultyResult,
    score_to_difficulty,
)
from services.import_service import execute_import_batch


class TestDifficultyClassification(unittest.TestCase):
    """Test suite for linguistic rule-based difficulty categorization."""

    def test_score_to_difficulty_thresholds(self):
        """Verify score mapping aligns with predefined difficulty thresholds."""
        self.assertEqual(score_to_difficulty(10.0), "Easy")
        self.assertEqual(score_to_difficulty(41.9), "Easy")
        self.assertEqual(score_to_difficulty(42.0), "Medium")
        self.assertEqual(score_to_difficulty(55.0), "Medium")
        self.assertEqual(score_to_difficulty(67.9), "Medium")
        self.assertEqual(score_to_difficulty(68.0), "Hard")
        self.assertEqual(score_to_difficulty(95.0), "Hard")

    # ==========================================
    # 1. GRAMMAR DIFFICULTY EVALUATION TESTS
    # ==========================================

    def test_grammar_easy_example(self):
        """Simple direct sentence, foundational vocabulary, basic auxiliary."""
        question_text = "She eats an apple every day for breakfast."
        options = ["eats", "ate", "eating", "eat"]
        result = evaluate_grammar_difficulty(question_text=question_text, options=options)

        self.assertIsInstance(result, DifficultyResult)
        self.assertEqual(result.suggested_difficulty, "Easy")
        self.assertLess(result.difficulty_score, 42.0)
        self.assertIn("Grammar Heuristic (Easy", result.reason)
        self.assertIn("simple direct sentence structure", result.reason)

    def test_grammar_medium_example(self):
        """Compound sentence with coordinate conjunction, moderate length."""
        question_text = "The committee reviewed the proposal yesterday, but they requested several revisions before approval."
        options = ["requested", "were requesting", "would request", "had been requesting"]
        result = evaluate_grammar_difficulty(question_text=question_text, options=options)

        self.assertIsInstance(result, DifficultyResult)
        self.assertEqual(result.suggested_difficulty, "Medium")
        self.assertGreaterEqual(result.difficulty_score, 42.0)
        self.assertLess(result.difficulty_score, 68.0)
        self.assertIn("Grammar Heuristic (Medium", result.reason)

    def test_grammar_hard_example(self):
        """
        Complex multi-clause structure with subordinating conjunctions,
        advanced grammar cues (negative inversion / subjunctive / third conditional),
        and academic vocabulary.
        """
        question_text = (
            "Not only had the board insisted that the executive director resign immediately, "
            "but furthermore, neither of the legal advisors was able to synthesize the contradictory evidence, "
            "which consequently led to ubiquitous controversy."
        )
        options = ["resign", "resigns", "resigned", "resigning"]
        result = evaluate_grammar_difficulty(question_text=question_text, options=options)

        self.assertIsInstance(result, DifficultyResult)
        self.assertEqual(result.suggested_difficulty, "Hard")
        self.assertGreaterEqual(result.difficulty_score, 68.0)
        self.assertIn("Grammar Heuristic (Hard", result.reason)
        self.assertIn("complex structure", result.reason)

    # ==========================================
    # 2. READING DIFFICULTY EVALUATION TESTS
    # ==========================================

    def test_reading_easy_example(self):
        """Short passage (< 80 words) and direct factual detail question."""
        passage = (
            "The library is open every morning from eight o'clock until noon. "
            "Students can borrow up to three books at a time. "
            "The librarians are always happy to help children find books."
        )
        question_text = "According to the passage, what time does the library open?"
        question_type = "Detail"
        options = ["At 8:00 AM", "At 9:00 AM", "At 12:00 PM", "At 3:00 PM"]

        result = evaluate_reading_difficulty(
            question_text=question_text,
            passage_text=passage,
            question_type=question_type,
            options=options,
        )

        self.assertEqual(result.suggested_difficulty, "Easy")
        self.assertLess(result.difficulty_score, 42.0)
        self.assertIn("Direct factual retrieval", result.reason)
        self.assertIn("passage length", result.reason)

    def test_reading_medium_example(self):
        """Moderate passage (100-180 words) and main idea question."""
        passage = (
            "Solar power technology has advanced dramatically over the past two decades. "
            "Photovoltaic panels are now significantly more efficient and less expensive to manufacture than "
            "their early predecessors. Many municipal governments have begun installing solar arrays on public "
            "buildings, reducing municipal electricity expenses while cutting carbon emissions. However, the storage "
            "of surplus energy during overcast days remains a technological hurdle that engineers continue to address."
        )
        question_text = "What is the main idea of the passage?"
        question_type = "Main Idea"
        options = [
            "Solar energy has made great progress despite ongoing storage challenges.",
            "Municipal governments spend too much money on electricity.",
            "Solar panels cannot function during cloudy or overcast days.",
            "Engineers have completely solved all renewable energy issues.",
        ]

        result = evaluate_reading_difficulty(
            question_text=question_text,
            passage_text=passage,
            question_type=question_type,
            options=options,
        )

        self.assertEqual(result.suggested_difficulty, "Medium")
        self.assertGreaterEqual(result.difficulty_score, 42.0)
        self.assertLess(result.difficulty_score, 68.0)
        self.assertIn("Moderate global synthesis demand", result.reason)

    def test_reading_hard_example(self):
        """
        Long academic passage (> 220 words) with advanced vocabulary and
        implicit inference question demand.
        """
        passage = (
            "In deep subterranean oceanic trenches, organisms exhibit remarkable physiological adaptations "
            "to survive under crushing hydrostatic pressures and total darkness. One prominent adaptation is "
            "bioluminescence, produced by specialized light-emitting photophores. Marine biologists note that "
            "counter-illumination allows certain species to match the intensity of downwelling ambient light, "
            "rendering them virtually imperceptible to predators hunting from below. The ubiquitous presence of "
            "such mechanisms suggests an evolutionary arms race driven by visual predation in the twilight zone. "
            "Furthermore, paradoxical enzymatic activities in abyssal fauna corroborate the hypothesis that metabolic "
            "rates are disproportionately influenced by ecological niches rather than ambient water temperature alone. "
            "Historiography of marine exploration demonstrates how early assumptions regarding abiotic deep oceans "
            "were fundamentally flawed, as contemporary submersibles synthesize vast biodiversity data."
        )
        question_text = "What can be inferred regarding the evolutionary advantage of counter-illumination?"
        question_type = "Inference"
        options = [
            "It affords selective camouflage by negating predatory silhouette recognition from beneath.",
            "It permanently elevates the organism's ambient metabolic equilibrium.",
            "It generates subterranean heat to counteract freezing water temperatures.",
            "It attracts prey organisms directly into the photophore apertures.",
        ]

        result = evaluate_reading_difficulty(
            question_text=question_text,
            passage_text=passage,
            question_type=question_type,
            options=options,
        )

        self.assertEqual(result.suggested_difficulty, "Hard")
        self.assertGreaterEqual(result.difficulty_score, 68.0)
        self.assertIn("High inference & implicit cognitive demand", result.reason)

    # ==========================================
    # 3. LISTENING DIFFICULTY EVALUATION TESTS
    # ==========================================

    def test_listening_easy_example(self):
        """Short audio (< 12 seconds), single-speaker public announcement, explicit fact."""
        transcript = "Attention passengers. Flight 204 to Boston is now boarding at Gate 12."
        question_text = "Which gate is Flight 204 boarding at?"
        result = evaluate_listening_difficulty(
            question_text=question_text,
            duration=9.5,
            transcript=transcript,
        )

        self.assertEqual(result.suggested_difficulty, "Easy")
        self.assertLess(result.difficulty_score, 42.0)
        self.assertIn("single-speaker monologue/announcement", result.reason)
        self.assertIn("explicit factual detail recall", result.reason)

    def test_listening_medium_example(self):
        """Moderate audio (20 seconds), two-speaker dialogue, factual schedule."""
        transcript = (
            "Speaker A: Do you know what time the library closes on Friday?\n"
            "Speaker B: Usually at 8 pm, but this Friday it closes at 5 pm for renovations."
        )
        question_text = "Why is the library closing early this Friday?"
        result = evaluate_listening_difficulty(
            question_text=question_text,
            duration=19.0,
            transcript=transcript,
        )

        self.assertEqual(result.suggested_difficulty, "Medium")
        self.assertGreaterEqual(result.difficulty_score, 42.0)
        self.assertLess(result.difficulty_score, 68.0)
        self.assertIn("two-speaker dialogue", result.reason)

    def test_listening_hard_example(self):
        """Extended audio (> 28s), multi-turn conversation, high density, speaker attitude inference."""
        transcript = (
            "Professor: Your research proposal on hippocampal synaptic potentiation shows promise, but your methodology lacks control variables.\n"
            "Student: I intended to synthesize the retrospective clinical trials from 2018.\n"
            "Professor: That won't suffice; you must corroborate declarative memory results with empirical biological data."
        )
        question_text = "What is the professor's attitude toward the student's current research methodology?"
        result = evaluate_listening_difficulty(
            question_text=question_text,
            duration=32.0,
            transcript=transcript,
        )

        self.assertEqual(result.suggested_difficulty, "Hard")
        self.assertGreaterEqual(result.difficulty_score, 68.0)
        self.assertIn("multi-turn conversational dialogue", result.reason)
        self.assertIn("implicit speaker attitude", result.reason)

    # ==========================================
    # 4. UNIFIED DISPATCHER TESTS
    # ==========================================

    def test_classify_difficulty_dispatcher(self):
        """Verify classify_difficulty correctly routes based on category name."""
        res_g = classify_difficulty("Grammar", question_text="He walks to school.")
        self.assertIn("Grammar Heuristic", res_g.reason)

        res_r = classify_difficulty("Reading", question_text="What is inferred?", passage_text="Short text.")
        self.assertIn("Reading Heuristic", res_r.reason)

        res_l = classify_difficulty("Listening", question_text="What did she say?", transcript="Hello there.")
        self.assertIn("Listening Heuristic", res_l.reason)

    # ==========================================
    # 5. ADMIN OVERRIDE PERSISTENCE TEST
    # ==========================================

    def test_admin_difficulty_override_persistence(self):
        """
        Critical Requirement: The rule-based system recommends a difficulty,
        but the Admin has editorial authority to override it (e.g. from Easy to Hard).
        The final chosen level MUST be stored in the database.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test_override.db"
            init_db(db_path)

            # Question where rule heuristic suggests 'Easy'
            parsed_easy_q = {
                "question_text": "The cat sleeps on the mat.",
                "option_a": "sleeps",
                "option_b": "sleep",
                "option_c": "slept",
                "option_d": "sleeping",
                "correct_answer": "A",
                "explanation": "Simple present agreement.",
                "topic": "Basic Verbs",
                "is_valid": True,
                "suggested_difficulty": "Easy",
                "difficulty_score": 24.5,
                "reason": "Grammar Heuristic (Easy): simple direct sentence structure.",
                # Admin overrides to 'Hard' during Admin Review
                "final_difficulty": "Hard",
            }

            # Question where rule heuristic suggests 'Hard'
            parsed_hard_q = {
                "question_text": "Had they realized the insidious consequences, they would have acted.",
                "option_a": "acted",
                "option_b": "act",
                "option_c": "acting",
                "option_d": "acts",
                "correct_answer": "A",
                "explanation": "Inversion and conditional.",
                "topic": "Inversion",
                "is_valid": True,
                "suggested_difficulty": "Hard",
                "difficulty_score": 82.0,
                "reason": "Grammar Heuristic (Hard): complex structure.",
                # Admin overrides to 'Medium' during Admin Review
                "final_difficulty": "Medium",
            }

            questions_to_import = [parsed_easy_q, parsed_hard_q]

            # Execute batch import
            detected, imported, failed = execute_import_batch(
                file_name="admin_override_test.docx",
                questions=questions_to_import,
                category_name="Grammar",
                default_status="Draft",
                imported_by="lead_admin",
                db_path=db_path,
            )

            self.assertEqual(detected, 2)
            self.assertEqual(imported, 2)
            self.assertEqual(failed, 0)

            # Verify in SQLite database that the final chosen levels were stored
            with get_connection(db_path) as conn:
                imported_rows = queries.get_questions_filtered(conn, limit=10)
                self.assertEqual(len(imported_rows), 2)

                q_map = {q["question_text"]: q["difficulty"] for q in imported_rows}

                # Assert that Q1 has 'Hard' (Admin's override, NOT 'Easy')
                self.assertEqual(q_map["The cat sleeps on the mat."], "Hard")

                # Assert that Q2 has 'Medium' (Admin's override, NOT 'Hard')
                self.assertEqual(
                    q_map["Had they realized the insidious consequences, they would have acted."],
                    "Medium",
                )


if __name__ == "__main__":
    unittest.main()
