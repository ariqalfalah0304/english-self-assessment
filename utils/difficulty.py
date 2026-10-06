"""
Rule-Based Difficulty Classification System for English Self-Assessment (Phase 13).
Evaluates linguistic and cognitive complexity heuristics WITHOUT external AI APIs.

Provides:
- Suggested Difficulty ('Easy', 'Medium', 'Hard')
- Difficulty Score (0.0 to 100.0)
- Detailed Reason / Pedagogical explanation of the heuristic determination

Rules evaluated:
1. Grammar:
   - Sentence complexity (clause count, length, conjunctions)
   - Structure type (simple vs compound vs complex)
   - Number and depth of grammar concepts (tenses, subjunctive, inversion, passives, agreement)
   - Vocabulary complexity (word length, syllable count, academic word markers)
   - Distractor similarity (length variance, shared stems)
   - Cognitive demand (negative polarity, ellipsis)

2. Reading:
   - Passage length (short, medium, long)
   - Lexical & syntactic complexity of passage
   - Question type & cognitive demand (Detail/Fact vs Main Idea vs Inference/Tone/Author's Purpose)
   - Explicit vs implicit retrieval demand

3. Listening:
   - Audio duration & pacing
   - Information density & number of distinct facts/figures
   - Dialogue vs monologue (speaker count indicators)
   - Vocabulary complexity & inference demand

Disclaimer:
This rule-based score is a pedagogical heuristic classification based on structural
and lexical rules, not an empirical psychometric item-response measurement.
Final difficulty classification remains strictly editable by the Administrator.
"""

from typing import Optional, Any
from dataclasses import dataclass
import re


@dataclass
class DifficultyResult:
    suggested_difficulty: str
    difficulty_score: float
    reason: str
    factors: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggested_difficulty": self.suggested_difficulty,
            "difficulty_score": self.difficulty_score,
            "reason": self.reason,
            "factors": self.factors,
        }


# Lexical & Syntactic Indicators
ADVANCED_VOCABULARY = {
    "furthermore", "nevertheless", "notwithstanding", "consequently", "paradoxical",
    "ubiquitous", "subterranean", "insidious", "imperative", "preceding", "preceded",
    "bioluminescence", "counter-illumination", "alluvial", "historiography", "catalyst",
    "retrospective", "juxtaposition", "synaptic", "hippocampal", "potentiation",
    "declarative", "phenomenon", "equilibrium", "disproportionately", "stifling",
    "jurisdiction", "comprehensive", "synthesize", "dichotomy", "ambiguity",
    "subversive", "indigenous", "adversary", "superfluous", "corroborate",
    "hypothetical", "subjunctive", "inversion", "necessitates", "nuance", "nuances",
}

BASIC_VOCABULARY = {
    "every", "day", "yesterday", "tomorrow", "always", "often", "sometimes", "never",
    "morning", "school", "home", "book", "table", "bicycle", "apple", "coffee", "breakfast",
    "student", "teacher", "walk", "walks", "eat", "eats", "ate", "drink", "drinks", "sleep", "sleeps",
    "look", "looks", "happy", "big", "small", "cat", "dog", "car", "bus", "friend",
}

SUBORDINATING_CONJUNCTIONS = {
    "although", "though", "even though", "whereas", "while", "unless", "provided that",
    "inasmuch as", "lest", "so that", "in order that", "since", "because", "before", "after",
    "which", "whose", "whom", "where", "when", "that", "if",
}

ADVANCED_GRAMMAR_CUES = [
    (r"\bhad\s+[a-z]+ed\b", "Past Perfect"),
    (r"\bwould\s+have\b", "Third Conditional"),
    (r"\b(?:neither|nor|either)\b.*\b(?:is|was|has)\b", "Indefinite Pronoun Agreement"),
    (r"\bnot\s+only\b.*\bbut\s+also\b", "Correlative Inversion"),
    (r"\b(?:seldom|rarely|scarcely|hardly|no\s+sooner)\b", "Negative Inversion"),
    (r"\b(?:insist|recommend|suggest|demand|require)\s+that\s+[a-z]+\s+(?:be|[a-z]+)\b", "Subjunctive Mood"),
    (r"\b(?:being|having\s+been)\s+[a-z]+ed\b", "Participle / Passive Complex"),
    (r"\b(?:subjunctive|inversion|conditional)\b", "Advanced Syntax Term"),
    (r"\b(?:hypothetical|counterfactual)\b", "Hypothetical Mood"),
]

BASIC_GRAMMAR_CUES = [
    (r"\b(?:am|is|are|was|were)\b", "Basic Copula / Continuous"),
    (r"\b(?:do|does|did)\b", "Basic Auxiliary"),
    (r"\b(?:can|will|must)\b", "Single Modal"),
    (r"\b(?:eats|walks|sleeps|plays|goes|likes|lives|works)\b", "Simple Present"),
]


def score_to_difficulty(score: float) -> str:
    """Map numeric score (0-100) to Easy, Medium, or Hard."""
    if score < 42.0:
        return "Easy"
    elif score < 68.0:
        return "Medium"
    else:
        return "Hard"


# ==========================================
# 1. GRAMMAR DIFFICULTY EVALUATION
# ==========================================

def evaluate_grammar_difficulty(
    question_text: str,
    options: Optional[list[str]] = None,
    explanation: str = "",
) -> DifficultyResult:
    """
    Evaluate Grammar question difficulty based on sentence length, syntactic
    clauses, advanced grammar patterns, lexical complexity, and distractor similarity.
    """
    clean_text = question_text.strip()
    words = re.findall(r"\b[A-Za-z'-]+\b", clean_text)
    word_count = len(words)

    # 1. Sentence length & clause score (0 - 25 pts)
    clause_count = 1 + len(re.findall(r"[,;]|(?:\b(?:and|but|nor|yet|so)\b)", clean_text.lower()))
    sub_count = sum(1 for c in SUBORDINATING_CONJUNCTIONS if re.search(rf"\b{re.escape(c)}\b", clean_text.lower()))

    length_score = min(25.0, (word_count * 0.9) + (clause_count * 2.5) + (sub_count * 4.0))

    # 2. Grammar concept complexity (0 - 30 pts)
    grammar_score = 10.0  # baseline
    detected_concepts = []

    for pattern, name in ADVANCED_GRAMMAR_CUES:
        if re.search(pattern, clean_text, re.IGNORECASE):
            grammar_score += 9.0
            detected_concepts.append(name)

    if not detected_concepts:
        for pattern, name in BASIC_GRAMMAR_CUES:
            if re.search(pattern, clean_text, re.IGNORECASE):
                grammar_score = 4.0
                detected_concepts.append(name)
                break

    grammar_score = min(30.0, grammar_score)

    # 3. Vocabulary complexity (0 - 20 pts)
    avg_word_len = sum(len(w) for w in words) / max(1, word_count)
    adv_vocab_matches = [w.lower() for w in words if w.lower() in ADVANCED_VOCABULARY]
    basic_vocab_matches = [w.lower() for w in words if w.lower() in BASIC_VOCABULARY]

    vocab_score = (avg_word_len * 2.0) + (len(adv_vocab_matches) * 5.0) - (len(basic_vocab_matches) * 2.0)
    vocab_score = max(3.0, min(20.0, vocab_score))

    # 4. Distractor similarity (0 - 15 pts)
    # High similarity between options increases cognitive discrimination difficulty
    distractor_score = 5.0
    if options and len(options) >= 2:
        lengths = [len(opt.strip()) for opt in options if opt.strip()]
        word_counts = [len(opt.split()) for opt in options if opt.strip()]
        is_multiword = any(wc > 1 for wc in word_counts)
        if lengths:
            variance = max(lengths) - min(lengths)
            if is_multiword:
                if variance <= 4:
                    distractor_score = 14.0  # subtle phrase discrimination
                elif variance <= 10:
                    distractor_score = 10.0
                else:
                    distractor_score = 5.0
            else:
                if variance <= 3 and max(lengths) >= 8:
                    distractor_score = 10.0  # long complex vocabulary words
                elif variance <= 3:
                    distractor_score = 5.0  # basic word choices
                else:
                    distractor_score = 4.0

    # 5. Cognitive demand (0 - 10 pts)
    cognitive_score = 2.0
    if re.search(r"\bnot\b|\bneither\b|\bnever\b|\bexcept\b", clean_text.lower()):
        cognitive_score += 4.0
    if sub_count >= 2 or clause_count >= 3:
        cognitive_score += 4.0
    elif len(adv_vocab_matches) >= 3:
        cognitive_score += 4.0
    cognitive_score = min(10.0, cognitive_score)

    # Total Score Calculation (0 - 100)
    total_score = round(min(100.0, max(5.0, length_score + grammar_score + vocab_score + distractor_score + cognitive_score)), 1)
    diff = score_to_difficulty(total_score)

    # Reason narrative
    reasons = []
    if sub_count > 0:
        reasons.append(f"complex structure with {sub_count} subordinating clause(s)")
    elif clause_count > 1:
        reasons.append(f"compound structure with {clause_count} clauses")
    else:
        reasons.append("simple direct sentence structure")

    if detected_concepts:
        reasons.append(f"features {', '.join(detected_concepts[:2])}")
    if adv_vocab_matches:
        reasons.append(f"advanced terms ({', '.join(adv_vocab_matches[:2])})")
    elif basic_vocab_matches:
        reasons.append("familiar foundational vocabulary")

    if distractor_score >= 12.0:
        reasons.append("subtle distractor similarity requiring precise discrimination")

    reason_text = f"Grammar Heuristic ({diff} — Score {total_score}/100): " + "; ".join(reasons) + "."

    return DifficultyResult(
        suggested_difficulty=diff,
        difficulty_score=total_score,
        reason=reason_text,
        factors={
            "length_score": round(length_score, 1),
            "grammar_score": round(grammar_score, 1),
            "vocab_score": round(vocab_score, 1),
            "distractor_score": round(distractor_score, 1),
            "cognitive_score": round(cognitive_score, 1),
            "word_count": word_count,
            "detected_concepts": detected_concepts,
        },
    )


# ==========================================
# 2. READING DIFFICULTY EVALUATION
# ==========================================

def evaluate_reading_difficulty(
    question_text: str,
    passage_text: str = "",
    question_type: str = "",
    options: Optional[list[str]] = None,
    explanation: str = "",
) -> DifficultyResult:
    """
    Evaluate Reading question difficulty based on passage length, question cognitive
    demand (detail vs inference vs tone), vocabulary load, and sentence structure.
    """
    clean_passage = passage_text.strip()
    passage_words = re.findall(r"\b[A-Za-z'-]+\b", clean_passage)
    passage_word_count = len(passage_words)

    # 1. Passage Length (0 - 30 pts)
    # < 80 words = Easy (5-10), 80-200 words = Medium (11-20), > 200 words = Hard (21-30)
    if passage_word_count == 0:
        length_score = 15.0  # fallback if passage absent
    elif passage_word_count < 80:
        length_score = 8.0 + (passage_word_count * 0.05)
    elif passage_word_count <= 220:
        length_score = 14.0 + ((passage_word_count - 80) * 0.07)
    else:
        length_score = min(30.0, 24.0 + ((passage_word_count - 220) * 0.04))

    # 2. Question Type Cognitive Demand (0 - 30 pts)
    # Detail / Fact = Explicit (Low: 8-12)
    # Main Idea / Vocab = Moderate (14-20)
    # Inference / Purpose / Tone / Assumption = Implicit (High: 22-30)
    q_lower = (question_text + " " + question_type).lower()
    if any(w in q_lower for w in ["infer", "implies", "inferred", "author's attitude", "tone", "assumption", "implicit"]):
        qtype_score = 28.0
        qtype_desc = "High inference & implicit cognitive demand"
    elif any(w in q_lower for w in ["main idea", "primarily concerned", "purpose", "best title"]):
        qtype_score = 20.0
        qtype_desc = "Moderate global synthesis demand"
    elif any(w in q_lower for w in ["meaning", "vocabulary", "closest in meaning"]):
        qtype_score = 17.0
        qtype_desc = "Contextual lexical identification"
    else:
        qtype_score = 10.0
        qtype_desc = "Direct factual retrieval"

    # 3. Vocabulary & Sentence Density in Passage (0 - 25 pts)
    if passage_words:
        avg_pass_len = sum(len(w) for w in passage_words) / passage_word_count
        adv_count = sum(1 for w in passage_words if w.lower() in ADVANCED_VOCABULARY)
        vocab_score = min(25.0, (avg_pass_len * 2.8) + (adv_count * 2.5))
    else:
        q_words = re.findall(r"\b[A-Za-z'-]+\b", question_text)
        vocab_score = 12.0

    # 4. Distractor plausibility & explanation depth (0 - 15 pts)
    options_score = 8.0
    if options and len(options) >= 4:
        opt_words = sum(len(opt.split()) for opt in options)
        if opt_words >= 16:  # Long multi-sentence options
            options_score = 14.0

    total_score = round(min(100.0, max(5.0, length_score + qtype_score + vocab_score + options_score)), 1)
    diff = score_to_difficulty(total_score)

    reason_parts = [
        f"Reading Heuristic ({diff} — Score {total_score}/100): {qtype_desc}",
        f"passage length {passage_word_count} words",
    ]
    if passage_word_count >= 200:
        reason_parts.append("extended text requiring sustained comprehension")
    elif passage_word_count <= 80 and passage_word_count > 0:
        reason_parts.append("concise passage with explicit facts")

    reason_text = "; ".join(reason_parts) + "."

    return DifficultyResult(
        suggested_difficulty=diff,
        difficulty_score=total_score,
        reason=reason_text,
        factors={
            "length_score": round(length_score, 1),
            "qtype_score": round(qtype_score, 1),
            "vocab_score": round(vocab_score, 1),
            "options_score": round(options_score, 1),
            "passage_word_count": passage_word_count,
        },
    )


# ==========================================
# 3. LISTENING DIFFICULTY EVALUATION
# ==========================================

def evaluate_listening_difficulty(
    question_text: str,
    duration: Optional[float] = None,
    transcript: str = "",
    question_type: str = "",
    options: Optional[list[str]] = None,
    explanation: str = "",
) -> DifficultyResult:
    """
    Evaluate Listening question difficulty based on audio duration, speech density,
    speaker count, and inference vs direct factual identification.
    """
    clean_transcript = transcript.strip()
    words = re.findall(r"\b[A-Za-z'-]+\b", clean_transcript)
    word_count = len(words)

    # 1. Duration & Audio Exposure Score (0 - 30 pts)
    # < 14s = Easy (4-10), 14-25s = Medium (11-20), > 25s = Hard (21-30)
    dur = duration or (word_count / 2.3 if word_count > 0 else 18.0)  # ~140 wpm estimate
    if dur < 14.0:
        duration_score = 4.0 + (dur * 0.4)
        dur_desc = f"short duration ({dur:.1f}s)"
    elif dur <= 25.0:
        duration_score = 11.0 + ((dur - 14.0) * 0.7)
        dur_desc = f"moderate duration ({dur:.1f}s)"
    else:
        duration_score = min(30.0, 20.0 + ((dur - 25.0) * 0.5))
        dur_desc = f"extended audio duration ({dur:.1f}s)"

    # 2. Information Density & Speaking Speed (0 - 25 pts)
    # Detect dates, times, numerical data, platforms, specialized facts
    numbers = re.findall(r"\b(?:\d+|pm|am|percent|dollars|platform|flight)\b", clean_transcript.lower())
    density_score = min(25.0, 4.0 + (len(numbers) * 2.0) + (min(15, word_count * 0.12)))

    # 3. Speaker Interaction & Dialogue Complexity (0 - 20 pts)
    # Single speaker announcement vs rapid multi-speaker dialogue
    speaker_markers = re.findall(r"^[A-Za-z\s]+:", clean_transcript, re.MULTILINE)
    if len(speaker_markers) >= 3:
        speaker_score = 18.0
        speaker_desc = "multi-turn conversational dialogue"
    elif len(speaker_markers) >= 2:
        speaker_score = 13.0
        speaker_desc = "two-speaker dialogue"
    else:
        speaker_score = 5.0
        speaker_desc = "single-speaker monologue/announcement"

    # 4. Cognitive Inference Demand (0 - 25 pts)
    combined_q = (question_text + " " + question_type).lower()
    if any(w in combined_q for w in ["attitude", "infer", "feel", "purpose", "why did the speaker"]):
        inference_score = 22.0
        inf_desc = "implicit speaker attitude or purpose inference"
    else:
        inference_score = 6.0
        inf_desc = "explicit factual detail recall"

    total_score = round(min(100.0, max(5.0, duration_score + density_score + speaker_score + inference_score)), 1)
    diff = score_to_difficulty(total_score)

    reason_parts = [
        f"Listening Heuristic ({diff} — Score {total_score}/100): {speaker_desc}",
        dur_desc,
        inf_desc,
    ]
    reason_text = "; ".join(reason_parts) + "."

    return DifficultyResult(
        suggested_difficulty=diff,
        difficulty_score=total_score,
        reason=reason_text,
        factors={
            "duration_score": round(duration_score, 1),
            "density_score": round(density_score, 1),
            "speaker_score": round(speaker_score, 1),
            "inference_score": round(inference_score, 1),
            "effective_duration_sec": round(dur, 1),
            "word_count": word_count,
        },
    )


# ==========================================
# 4. UNIFIED DISPATCHER FUNCTION
# ==========================================

def classify_difficulty(
    category: str,
    question_text: str,
    options: Optional[list[str]] = None,
    passage_text: str = "",
    audio_file: str = "",
    duration: Optional[float] = None,
    transcript: str = "",
    question_type: str = "",
    explanation: str = "",
) -> DifficultyResult:
    """
    Unified entry point for rule-based difficulty suggestion across any category.
    Returns DifficultyResult containing suggested_difficulty, difficulty_score, and reason.
    """
    cat_clean = category.strip().capitalize()

    if cat_clean == "Grammar":
        return evaluate_grammar_difficulty(
            question_text=question_text,
            options=options,
            explanation=explanation,
        )
    elif cat_clean == "Reading":
        return evaluate_reading_difficulty(
            question_text=question_text,
            passage_text=passage_text,
            question_type=question_type,
            options=options,
            explanation=explanation,
        )
    elif cat_clean == "Listening":
        return evaluate_listening_difficulty(
            question_text=question_text,
            duration=duration,
            transcript=transcript,
            question_type=question_type,
            options=options,
            explanation=explanation,
        )
    else:
        # Default fallback to Grammar evaluation
        return evaluate_grammar_difficulty(
            question_text=question_text,
            options=options,
            explanation=explanation,
        )
