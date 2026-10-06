"""
Dynamic Question Selection and Repetition Control Service (Phase 14).
Implements algorithmic question selection for quiz attempts:
1. Prevents duplicate questions within any single attempt.
2. Randomizes question sequence.
3. Randomizes answer option positions (A, B, C, D) where safe while preserving correct answer.
4. Avoids recently answered questions by the same user when enough unused questions exist.
5. Gracefully reuses questions if the question bank is smaller than the requested count.
6. Strictly filters by category, difficulty, and 'Active' status (never exposes Draft, Inactive, Archived).
7. Preserves Reading passage relationships (questions sharing a passage remain contiguous).
8. Preserves Listening audio relationships (audio file path, transcript, and duration).
"""

from typing import Optional, Any
import random
import re
import sqlite3

from database.models import Question
from database import queries


# Patterns indicating answer options that depend on specific letter or position
UNSAFE_OPTION_PATTERNS = [
    r"\ball\s+of\s+the\s+above\b",
    r"\bnone\s+of\s+the\s+above\b",
    r"\bboth\s+[a-d]\s+and\s+[a-d]\b",
    r"\bneither\s+[a-d]\s+nor\s+[a-d]\b",
    r"\beither\s+[a-d]\s+or\s+[a-d]\b",
    r"\b[a-d]\s+and\s+[a-d]\s+only\b",
    r"\boptions?\s+[a-d]\b",
    r"\bchoices?\s+[a-d]\b",
    r"\bstatement\s+[a-d]\b",
]

RE_UNSAFE_OPTION = re.compile("|".join(UNSAFE_OPTION_PATTERNS), re.IGNORECASE)


def is_option_shuffling_safe(options: list[str]) -> bool:
    """
    Determine if an option list is safe to shuffle.
    Returns False if any option text references relative positions
    (e.g., 'All of the above', 'Both A and B', 'None of the above').
    """
    if not options or len(options) < 2:
        return False

    for opt in options:
        if not opt or not isinstance(opt, str):
            return False
        clean = opt.strip()
        if not clean:
            return False
        if RE_UNSAFE_OPTION.search(clean):
            return False

    return True


def shuffle_options_safely(
    q_dict: dict[str, Any],
    rng: Optional[random.Random] = None,
) -> dict[str, Any]:
    """
    Randomize answer option order (A, B, C, D) if safe, updating correct_answer
    to reflect the new position of the correct text content.
    If unsafe, options and correct_answer remain unchanged.
    """
    options = [
        q_dict.get("option_a", ""),
        q_dict.get("option_b", ""),
        q_dict.get("option_c", ""),
        q_dict.get("option_d", ""),
    ]

    if not is_option_shuffling_safe(options):
        q_dict["options_shuffled"] = False
        return q_dict

    orig_key = (q_dict.get("correct_answer") or "").strip().upper()
    key_to_idx = {"A": 0, "B": 1, "C": 2, "D": 3}
    idx_to_key = ["A", "B", "C", "D"]

    if orig_key not in key_to_idx:
        q_dict["options_shuffled"] = False
        return q_dict

    correct_text = options[key_to_idx[orig_key]]

    # Shuffle a copy of the options
    shuffled = list(options)
    if rng is not None:
        rng.shuffle(shuffled)
    else:
        random.shuffle(shuffled)

    # Reassign shuffled options
    q_dict["option_a"] = shuffled[0]
    q_dict["option_b"] = shuffled[1]
    q_dict["option_c"] = shuffled[2]
    q_dict["option_d"] = shuffled[3]

    # Map the correct answer to its new index
    new_idx = shuffled.index(correct_text)
    q_dict["correct_answer"] = idx_to_key[new_idx]
    q_dict["options_shuffled"] = True

    return q_dict


def select_quiz_questions(
    conn: sqlite3.Connection,
    user_id: int,
    category_name: str,
    category_id: int,
    difficulty: str,
    requested_count: int,
    rng: Optional[random.Random] = None,
) -> tuple[list[dict[str, Any]], str]:
    """
    Core Dynamic Question Selection Algorithm (Phase 14):
    1. Filter candidates strictly by Active status, category, and difficulty.
    2. Exclude recent user history when enough unused questions exist.
    3. Gracefully reuse questions when the bank is small.
    4. Group and preserve Reading passage relationships contiguously.
    5. Attach and preserve Listening audio metadata.
    6. Randomize question order.
    7. Randomize option order where safe.
    8. Enforce zero duplicate questions within an attempt.

    Returns:
    (selected_question_dicts, notice_message)
    """
    _rng = rng or random.Random()

    # 1. Fetch strictly Active questions for this category and difficulty
    candidates = queries.get_active_questions_by_category_difficulty(
        conn=conn,
        category_id=category_id,
        difficulty=difficulty,
    )

    if not candidates:
        return [], f"No active questions found for {category_name} ({difficulty})."

    # 2. Retrieve question IDs previously answered/attempted by this user
    recent_seen_ids = queries.get_user_recent_question_ids(
        conn=conn,
        user_id=user_id,
        category_id=category_id,
    )
    recent_seen_set = set(recent_seen_ids)

    selected_questions: list[Question] = []
    is_reading = (category_name.strip().lower() == "reading")

    # ==========================================
    # A. READING CATEGORY: PASSAGE GROUPING
    # ==========================================
    if is_reading:
        # Group questions by passage_id
        passage_groups: dict[Optional[int], list[Question]] = {}
        for q in candidates:
            pid = q.passage_id
            if pid not in passage_groups:
                passage_groups[pid] = []
            passage_groups[pid].append(q)

        # Categorize passage groups into unseen vs seen
        unseen_groups: list[list[Question]] = []
        seen_groups: list[list[Question]] = []

        for pid, q_list in passage_groups.items():
            # If no question in this passage group was recently seen, it's unseen
            if any(q.id in recent_seen_set for q in q_list if q.id is not None):
                seen_groups.append(q_list)
            else:
                unseen_groups.append(q_list)

        _rng.shuffle(unseen_groups)
        # Order seen groups by oldest seen (least recently used)
        seen_groups.sort(
            key=lambda grp: min(
                (recent_seen_ids.index(q.id) for q in grp if q.id in recent_seen_set),
                default=-1,
            ),
            reverse=True,
        )

        # Prioritize unseen passages; fallback gracefully to seen passages
        ordered_groups = unseen_groups + seen_groups

        for grp in ordered_groups:
            if len(selected_questions) >= requested_count:
                break
            # Add all questions of this passage together to preserve passage relationship
            for q in grp:
                if q not in selected_questions:
                    selected_questions.append(q)
                if len(selected_questions) >= requested_count:
                    break

    # ==========================================
    # B. GRAMMAR & LISTENING CATEGORIES
    # ==========================================
    else:
        unseen = [q for q in candidates if q.id not in recent_seen_set]
        seen = [q for q in candidates if q.id in recent_seen_set]

        # Order seen questions from oldest seen (least recent) to most recent
        seen.sort(
            key=lambda q: recent_seen_ids.index(q.id) if q.id in recent_seen_set else -1,
            reverse=True,
        )

        if len(unseen) >= requested_count:
            # Enough fresh questions exist: pick exclusively from unseen
            _rng.shuffle(unseen)
            selected_questions = unseen[:requested_count]
        else:
            # Gracefully reuse questions: take all unseen, then oldest seen
            selected_questions = list(unseen)
            needed = requested_count - len(selected_questions)
            selected_questions.extend(seen[:needed])

        # Randomize question order (Requirement 2)
        _rng.shuffle(selected_questions)

    # 3. Enforce zero duplicate questions within the attempt (Requirement 1)
    seen_check: set[int] = set()
    deduped_questions: list[Question] = []
    for q in selected_questions:
        if q.id is not None and q.id not in seen_check:
            seen_check.add(q.id)
            deduped_questions.append(q)

    total_found = len(deduped_questions)
    notice_msg = ""
    if total_found < requested_count:
        notice_msg = f"Note: Only {total_found} questions are currently available for this level."

    # 4. Serialize to dicts, attach relationships & randomize options safely
    serialized_questions: list[dict[str, Any]] = []

    for q in deduped_questions:
        q_dict = q.to_dict()

        # Preserve reading passage relationship (Requirement 8)
        if q.passage_id is not None:
            passage = queries.get_passage_by_id(conn, q.passage_id)
            if passage:
                q_dict["passage_title"] = passage.title
                q_dict["passage_text"] = passage.passage_text

        # Preserve listening audio relationship (Requirement 9)
        if q.id is not None:
            audio_file = queries.get_audio_file_by_question_id(conn, q.id)
            if audio_file:
                q_dict["audio_file"] = audio_file.file_path
                q_dict["transcript"] = audio_file.transcript
                q_dict["duration"] = audio_file.duration

        # Randomize answer options order where safe (Requirement 3)
        q_dict = shuffle_options_safely(q_dict, rng=_rng)
        serialized_questions.append(q_dict)

    return serialized_questions, notice_msg


def select_final_exam_questions(
    conn: sqlite3.Connection,
    user_id: int,
    category_name: str,
    category_id: int,
    requested_count: int = 50,
    rng: Optional[random.Random] = None,
) -> tuple[list[dict[str, Any]], str]:
    """
    Dynamic Proportional Question Sampling Algorithm for Ujian Gabungan (Final Mastery Exam):
    1. Detects all active skills for the specified category.
    2. Calculates proportional quota per skill (e.g. ~33.3% for 3 skills, ~25% for 4 skills).
    3. Randomly samples questions without replacement from each skill.
    4. Interleaves and shuffles all sampled questions into a randomized final 50-question paper.
    5. Shuffles options (A, B, C, D) safely.
    6. Attaches reading passages and listening audio metadata.
    """
    _rng = rng or random.Random()

    # Get all active skills for this category
    skills = queries.get_skills_by_category(conn, category_id)
    if not skills:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT COALESCE(skill_number, 1) as snum
            FROM questions
            WHERE category_id = ? AND status = 'Active'
            ORDER BY snum ASC;
            """,
            (category_id,),
        )
        skill_numbers = [r[0] for r in cursor.fetchall()]
    else:
        skill_numbers = [s["skill_number"] for s in skills]

    if not skill_numbers:
        skill_numbers = [1]

    num_skills = len(skill_numbers)
    base_quota = requested_count // num_skills
    remainder = requested_count % num_skills

    # Calculate quota per skill
    skill_quotas = {}
    for i, snum in enumerate(skill_numbers):
        quota = base_quota + (1 if i < remainder else 0)
        skill_quotas[snum] = quota

    # Fetch active questions for each skill
    selected_questions: list[dict[str, Any]] = []
    shortfall = 0

    for snum in skill_numbers:
        quota = skill_quotas[snum]
        q_list = queries.get_questions_by_skill_sequential(
            conn=conn,
            category_id=category_id,
            skill_number=snum,
            status="Active",
        )
        active_qs = [q for q in q_list if q.get("status", "Active").capitalize() == "Active"]
        if not active_qs:
            shortfall += quota
            continue

        _rng.shuffle(active_qs)
        taken = active_qs[:quota]
        selected_questions.extend(taken)
        if len(taken) < quota:
            shortfall += (quota - len(taken))

    # If any skill had fewer questions than its quota, pool remaining active questions from category
    if shortfall > 0:
        taken_ids = {q["id"] for q in selected_questions if q.get("id")}
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id FROM questions
            WHERE category_id = ? AND status = 'Active'
            """,
            (category_id,),
        )
        all_active_ids = [r[0] for r in cursor.fetchall() if r[0] not in taken_ids]
        _rng.shuffle(all_active_ids)
        extra_ids = all_active_ids[:shortfall]

        for qid in extra_ids:
            q_obj = queries.get_question_by_id(conn, qid)
            if q_obj:
                selected_questions.append(q_obj.to_dict())

    # Randomize final sequence across all skills so questions from different skills are interleaved
    _rng.shuffle(selected_questions)

    # Serialize & attach relationships (passages, audio) and shuffle options safely
    serialized_questions: list[dict[str, Any]] = []
    seen_check: set[int] = set()

    for q_dict in selected_questions:
        qid = q_dict.get("id")
        if qid in seen_check:
            continue
        if qid:
            seen_check.add(qid)

        # Attach reading passage
        pid = q_dict.get("passage_id")
        if pid:
            passage = queries.get_passage_by_id(conn, pid)
            if passage:
                q_dict["passage_title"] = passage.title
                q_dict["passage_text"] = passage.passage_text

        # Attach listening audio
        if qid:
            audio_file = queries.get_audio_file_by_question_id(conn, qid)
            if audio_file:
                q_dict["audio_file"] = audio_file.file_path
                q_dict["transcript"] = audio_file.transcript
                q_dict["duration"] = audio_file.duration

        # Randomize options safely
        q_dict = shuffle_options_safely(q_dict, rng=_rng)
        serialized_questions.append(q_dict)

    total_found = len(serialized_questions)
    notice_msg = ""
    if total_found < requested_count:
        notice_msg = f"Catatan: Tersedia {total_found} soal gabungan dari {num_skills} skill."

    return serialized_questions, notice_msg
