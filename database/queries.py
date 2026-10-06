"""
Parameterized SQL query functions for English Self-Assessment database operations.
Prevents SQL injection by using parameterized queries exclusively.
"""

import sqlite3
from typing import Optional, Sequence, Any
from datetime import datetime, timezone

from database.models import (
    User,
    Admin,
    Category,
    Topic,
    Passage,
    Question,
    AudioFile,
    Attempt,
    AttemptQuestion,
    Answer,
    ImportHistory,
)


# ==========================================
# USERS
# ==========================================

def create_user(
    conn: sqlite3.Connection,
    name: str,
    email: str,
    institution: Optional[str] = None,
    program: Optional[str] = None,
) -> int:
    """Insert a new user and return the generated user_id."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (name, email, institution, program)
        VALUES (?, ?, ?, ?);
        """,
        (name.strip(), email.strip().lower(), institution, program),
    )
    return cursor.lastrowid  # type: ignore


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[User]:
    """Retrieve a user by primary key ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
    row = cursor.fetchone()
    return User.from_row(row) if row else None


def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[User]:
    """Retrieve the most recent user record by email address."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE email = ? ORDER BY id DESC LIMIT 1;",
        (email.strip().lower(),),
    )
    row = cursor.fetchone()
    return User.from_row(row) if row else None


def delete_user(conn: sqlite3.Connection, user_id: int) -> bool:
    """
    Permanently delete a participant user and all their associated test attempt logs and answers.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM answers WHERE attempt_id IN (
            SELECT id FROM attempts WHERE user_id = ?
        )
        """,
        (user_id,),
    )
    cursor.execute(
        """
        DELETE FROM attempt_questions WHERE attempt_id IN (
            SELECT id FROM attempts WHERE user_id = ?
        )
        """,
        (user_id,),
    )
    cursor.execute("DELETE FROM attempts WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    return cursor.rowcount > 0


def get_or_create_user(
    conn: sqlite3.Connection,
    name: str,
    email: str,
    institution: Optional[str] = None,
    program: Optional[str] = None,
) -> User:
    """Find existing user by email or create a new user record."""
    existing = get_user_by_email(conn, email)
    if existing:
        return existing
    new_id = create_user(conn, name, email, institution, program)
    created = get_user_by_id(conn, new_id)
    assert created is not None
    return created


# ==========================================
# ADMINS
# ==========================================

def create_admin(
    conn: sqlite3.Connection,
    username: str,
    password_hash: str,
    role: str = "admin",
) -> int:
    """Insert a new admin user."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO admins (username, password_hash, role)
        VALUES (?, ?, ?);
        """,
        (username.strip(), password_hash, role),
    )
    return cursor.lastrowid  # type: ignore


def get_admin_by_username(conn: sqlite3.Connection, username: str) -> Optional[Admin]:
    """Retrieve admin details by username."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE username = ?;", (username.strip(),))
    row = cursor.fetchone()
    return Admin.from_row(row) if row else None


def get_admin_by_id(conn: sqlite3.Connection, admin_id: int) -> Optional[Admin]:
    """Retrieve admin details by primary key ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE id = ?;", (admin_id,))
    row = cursor.fetchone()
    return Admin.from_row(row) if row else None


def count_admins(conn: sqlite3.Connection) -> int:
    """Return total number of registered administrator accounts."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM admins;")
    return cursor.fetchone()[0]


def update_admin_credentials(
    conn: sqlite3.Connection,
    admin_id: int,
    new_username: str,
    new_password_hash: str,
) -> bool:
    """Update an administrator's username and password hash."""
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE admins
        SET username = ?, password_hash = ?
        WHERE id = ?;
        """,
        (new_username.strip(), new_password_hash, admin_id),
    )
    conn.commit()
    return cursor.rowcount > 0


# ==========================================
# CATEGORIES & TOPICS
# ==========================================

def get_all_categories(conn: sqlite3.Connection) -> list[Category]:
    """Return all categories sorted by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY id ASC;")
    return [Category.from_row(r) for r in cursor.fetchall()]


def get_category_by_id(conn: sqlite3.Connection, category_id: int) -> Optional[Category]:
    """Retrieve category by primary key."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?;", (category_id,))
    row = cursor.fetchone()
    return Category.from_row(row) if row else None


def get_category_by_name(conn: sqlite3.Connection, name: str) -> Optional[Category]:
    """Retrieve category by case-insensitive name."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE LOWER(name) = LOWER(?);", (name.strip(),))
    row = cursor.fetchone()
    return Category.from_row(row) if row else None


def create_topic(
    conn: sqlite3.Connection,
    category_id: int,
    name: str,
    description: Optional[str] = None,
) -> int:
    """Insert a new topic for a given category."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO topics (category_id, name, description)
        VALUES (?, ?, ?);
        """,
        (category_id, name.strip(), description),
    )
    return cursor.lastrowid  # type: ignore


def get_topics_by_category(conn: sqlite3.Connection, category_id: int) -> list[Topic]:
    """Retrieve topics belonging to a category."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM topics WHERE category_id = ? ORDER BY name ASC;",
        (category_id,),
    )
    return [Topic.from_row(r) for r in cursor.fetchall()]


# ==========================================
# PASSAGES
# ==========================================

def create_passage(
    conn: sqlite3.Connection,
    passage_text: str,
    title: Optional[str] = None,
    category_id: Optional[int] = None,
) -> int:
    """Insert a reading passage."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO passages (title, passage_text, category_id)
        VALUES (?, ?, ?);
        """,
        (title, passage_text, category_id),
    )
    return cursor.lastrowid  # type: ignore


def get_passage_by_id(conn: sqlite3.Connection, passage_id: int) -> Optional[Passage]:
    """Retrieve passage by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM passages WHERE id = ?;", (passage_id,))
    row = cursor.fetchone()
    return Passage.from_row(row) if row else None


# ==========================================
# QUESTIONS
# ==========================================

def create_question(conn: sqlite3.Connection, q: Question) -> int:
    """Insert a question record."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO questions (
            category_id, topic_id, passage_id, subtopic, question_type,
            question_text, option_a, option_b, option_c, option_d,
            correct_answer, explanation, difficulty, status, source_file,
            skill_number, skill_name, question_order
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            q.category_id,
            q.topic_id,
            q.passage_id,
            q.subtopic,
            q.question_type,
            q.question_text,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.correct_answer.upper(),
            q.explanation,
            getattr(q, "difficulty", "Standard") or "Standard",
            q.status,
            q.source_file,
            getattr(q, "skill_number", 1) or 1,
            getattr(q, "skill_name", None),
            getattr(q, "question_order", 1) or 1,
        ),
    )
    return cursor.lastrowid  # type: ignore


def get_question_by_id(conn: sqlite3.Connection, question_id: int) -> Optional[Question]:
    """Retrieve question by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE id = ?;", (question_id,))
    row = cursor.fetchone()
    return Question.from_row(row) if row else None


def get_random_questions(
    conn: sqlite3.Connection,
    category_id: int,
    difficulty: str,
    limit: int = 20,
    exclude_ids: Optional[Sequence[int]] = None,
) -> list[Question]:
    """
    Select randomized active questions matching category and difficulty.
    Optionally excludes specified question IDs to avoid repeats.
    """
    cursor = conn.cursor()
    params: list[object] = [category_id, difficulty.capitalize(), "Active"]

    query = """
        SELECT * FROM questions
        WHERE category_id = ?
          AND LOWER(difficulty) = LOWER(?)
          AND status = ?
    """

    if exclude_ids:
        placeholders = ",".join("?" for _ in exclude_ids)
        query += f" AND id NOT IN ({placeholders})"
        params.extend(exclude_ids)

    query += " ORDER BY RANDOM() LIMIT ?;"
    params.append(limit)

    cursor.execute(query, params)
    return [Question.from_row(r) for r in cursor.fetchall()]


def count_active_questions(
    conn: sqlite3.Connection,
    category_id: Optional[int] = None,
    difficulty: Optional[str] = None,
) -> int:
    """Count active questions with optional category and difficulty filters."""
    cursor = conn.cursor()
    query = "SELECT COUNT(*) FROM questions WHERE status = 'Active'"
    params: list[object] = []

    if category_id is not None:
        query += " AND category_id = ?"
        params.append(category_id)

    if difficulty is not None:
        query += " AND LOWER(difficulty) = LOWER(?)"
        params.append(difficulty)

    cursor.execute(query, params)
    return cursor.fetchone()[0]


def get_user_recent_question_ids(
    conn: sqlite3.Connection,
    user_id: int,
    category_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> list[int]:
    """
    Retrieve question IDs previously answered/attempted by this user,
    ordered from most recent to oldest.
    """
    cursor = conn.cursor()
    query = """
        SELECT aq.question_id
        FROM attempt_questions aq
        JOIN attempts a ON aq.attempt_id = a.id
        WHERE a.user_id = ?
    """
    params: list[Any] = [user_id]
    if category_id is not None:
        query += " AND a.category_id = ?"
        params.append(category_id)

    query += " ORDER BY a.started_at DESC, a.id DESC"
    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)
    # Deduplicate while preserving recency order
    seen: set[int] = set()
    result: list[int] = []
    for r in cursor.fetchall():
        qid = r[0]
        if qid not in seen:
            seen.add(qid)
            result.append(qid)
    return result


def get_active_questions_by_category_difficulty(
    conn: sqlite3.Connection,
    category_id: int,
    difficulty: str,
) -> list[Question]:
    """
    Retrieve all Active questions for a given category and difficulty.
    Excludes Draft, Inactive, and Archived questions strictly.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM questions
        WHERE category_id = ?
          AND LOWER(difficulty) = LOWER(?)
          AND status = 'Active'
        ORDER BY id ASC;
        """,
        (category_id, difficulty),
    )
    return [Question.from_row(r) for r in cursor.fetchall()]


# ==========================================
# AUDIO FILES
# ==========================================

def create_audio_file(
    conn: sqlite3.Connection,
    question_id: int,
    file_path: str,
    transcript: Optional[str] = None,
    duration: Optional[float] = None,
) -> int:
    """Link an audio file to a question."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO audio_files (question_id, file_path, transcript, duration)
        VALUES (?, ?, ?, ?);
        """,
        (question_id, file_path, transcript, duration),
    )
    return cursor.lastrowid  # type: ignore


def get_audio_file_by_question_id(conn: sqlite3.Connection, question_id: int) -> Optional[AudioFile]:
    """Retrieve audio file record for a given question."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audio_files WHERE question_id = ?;", (question_id,))
    row = cursor.fetchone()
    return AudioFile.from_row(row) if row else None


# ==========================================
# ATTEMPTS & ATTEMPT QUESTIONS
# ==========================================

def create_attempt(
    conn: sqlite3.Connection,
    user_id: int,
    category_id: int,
    difficulty: str,
    total_questions: int = 0,
) -> int:
    """Create a new quiz attempt record."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO attempts (user_id, category_id, difficulty, total_questions)
        VALUES (?, ?, ?, ?);
        """,
        (user_id, category_id, difficulty, total_questions),
    )
    return cursor.lastrowid  # type: ignore


def get_attempt_by_id(conn: sqlite3.Connection, attempt_id: int) -> Optional[Attempt]:
    """Retrieve attempt by ID."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM attempts WHERE id = ?;", (attempt_id,))
    row = cursor.fetchone()
    return Attempt.from_row(row) if row else None


def complete_attempt(
    conn: sqlite3.Connection,
    attempt_id: int,
    correct_answers: int,
    incorrect_answers: int,
    score: float,
    duration_seconds: Optional[int] = None,
    passing_score: float = 70.0,
) -> None:
    """Mark an attempt as completed with final scores, is_passed status, and timestamp."""
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    is_passed_val = 1 if score >= passing_score else 0
    cursor.execute(
        """
        UPDATE attempts
        SET correct_answers = ?,
            incorrect_answers = ?,
            score = ?,
            is_passed = ?,
            completed_at = ?,
            duration_seconds = ?
        WHERE id = ?;
        """,
        (correct_answers, incorrect_answers, score, is_passed_val, now_str, duration_seconds, attempt_id),
    )


def get_attempts_by_user(conn: sqlite3.Connection, user_id: int) -> list[Attempt]:
    """Retrieve all attempts for a user sorted by most recent first."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM attempts WHERE user_id = ? ORDER BY started_at DESC, id DESC;",
        (user_id,),
    )
    return [Attempt.from_row(r) for r in cursor.fetchall()]


def add_attempt_questions(
    conn: sqlite3.Connection,
    attempt_id: int,
    question_ids: Sequence[int],
) -> None:
    """
    Preserve question order in attempt_questions table.
    Ensures question_order index starts at 1.
    """
    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT INTO attempt_questions (attempt_id, question_id, question_order)
        VALUES (?, ?, ?);
        """,
        [(attempt_id, q_id, order) for order, q_id in enumerate(question_ids, start=1)],
    )


def get_attempt_questions(conn: sqlite3.Connection, attempt_id: int) -> list[tuple[int, Question]]:
    """
    Retrieve questions for an attempt ordered by original sequence (question_order ASC).
    Returns list of (question_order, Question).
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT aq.question_order, q.*
        FROM attempt_questions aq
        JOIN questions q ON aq.question_id = q.id
        WHERE aq.attempt_id = ?
        ORDER BY aq.question_order ASC;
        """,
        (attempt_id,),
    )
    results: list[tuple[int, Question]] = []
    for row in cursor.fetchall():
        order = row["question_order"]
        q = Question.from_row(row)
        results.append((order, q))
    return results


# ==========================================
# ANSWERS
# ==========================================

def record_answer(
    conn: sqlite3.Connection,
    attempt_id: int,
    question_id: int,
    user_answer: Optional[str],
    correct_answer: str,
    is_correct: bool,
) -> int:
    """
    Record user response to a question in an attempt.
    Preserves actual user answer (even if None or empty).
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO answers (attempt_id, question_id, user_answer, correct_answer, is_correct)
        VALUES (?, ?, ?, ?, ?);
        """,
        (
            attempt_id,
            question_id,
            user_answer,
            correct_answer.upper(),
            1 if is_correct else 0,
        ),
    )
    return cursor.lastrowid  # type: ignore


def get_answers_by_attempt(conn: sqlite3.Connection, attempt_id: int) -> list[Answer]:
    """Retrieve all submitted answers for an attempt."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM answers WHERE attempt_id = ? ORDER BY id ASC;",
        (attempt_id,),
    )
    return [Answer.from_row(r) for r in cursor.fetchall()]


# ==========================================
# IMPORT HISTORY
# ==========================================

def record_import(
    conn: sqlite3.Connection,
    file_name: str,
    category: str,
    total_detected: int = 0,
    total_imported: int = 0,
    total_failed: int = 0,
    imported_by: Optional[str] = None,
) -> int:
    """Log an import batch execution into import_history."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO import_history (
            file_name, category, total_detected, total_imported, total_failed, imported_by
        ) VALUES (?, ?, ?, ?, ?, ?);
        """,
        (file_name, category, total_detected, total_imported, total_failed, imported_by),
    )
    return cursor.lastrowid  # type: ignore


def get_import_history(conn: sqlite3.Connection, limit: int = 50) -> list[ImportHistory]:
    """Retrieve recent import history logs."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM import_history ORDER BY imported_at DESC, id DESC LIMIT ?;",
        (limit,),
    )
    return [ImportHistory.from_row(r) for r in cursor.fetchall()]


# ==========================================
# ADMIN DASHBOARD & ANALYTICS QUERIES (PHASE 10)
# ==========================================

def get_dashboard_metrics(conn: sqlite3.Connection) -> dict[str, Any]:
    """
    Retrieve aggregated metrics for Admin Dashboard:
    - total users
    - total assessment attempts
    - total questions
    - active questions
    - attempts per category (Grammar, Reading, Listening)
    - difficulty breakdown
    - average score
    """
    cursor = conn.cursor()

    # Total users
    cursor.execute("SELECT COUNT(*) FROM users;")
    total_users = cursor.fetchone()[0]

    # Total attempts
    cursor.execute("SELECT COUNT(*) FROM attempts;")
    total_attempts = cursor.fetchone()[0]

    # Total and active questions
    cursor.execute("SELECT COUNT(*) FROM questions;")
    total_questions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM questions WHERE LOWER(status) = 'active';")
    active_questions = cursor.fetchone()[0]

    # Category attempts breakdown
    cursor.execute(
        """
        SELECT c.name, COUNT(a.id) as attempt_count
        FROM categories c
        LEFT JOIN attempts a ON c.id = a.category_id
        GROUP BY c.name;
        """
    )
    category_counts = {row[0]: row[1] for row in cursor.fetchall()}

    grammar_attempts = category_counts.get("Grammar", 0)
    reading_attempts = category_counts.get("Reading", 0)
    listening_attempts = category_counts.get("Listening", 0)

    # Difficulty attempts breakdown
    cursor.execute(
        """
        SELECT difficulty, COUNT(id)
        FROM attempts
        GROUP BY difficulty;
        """
    )
    difficulty_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # Completed attempts and average score
    cursor.execute("SELECT AVG(score) FROM attempts WHERE completed_at IS NOT NULL;")
    avg_score_row = cursor.fetchone()[0]
    avg_score = round(float(avg_score_row), 1) if avg_score_row is not None else 0.0

    return {
        "total_users": total_users,
        "total_attempts": total_attempts,
        "total_questions": total_questions,
        "active_questions": active_questions,
        "grammar_attempts": grammar_attempts,
        "reading_attempts": reading_attempts,
        "listening_attempts": listening_attempts,
        "category_counts": category_counts,
        "difficulty_counts": difficulty_counts,
        "average_score": avg_score,
    }


def get_users_with_stats(
    conn: sqlite3.Connection,
    search_query: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve users list along with their assessment stats (total attempts, average score).
    Supports keyword search across name, email, institution, and program.
    """
    cursor = conn.cursor()
    params: list[Any] = []

    sql = """
    SELECT 
        u.id,
        u.name,
        u.email,
        u.institution,
        u.program,
        u.created_at,
        COUNT(a.id) AS total_attempts,
        AVG(CASE WHEN a.completed_at IS NOT NULL THEN a.score ELSE NULL END) AS average_score,
        MAX(a.started_at) AS last_attempt_at
    FROM users u
    LEFT JOIN attempts a ON u.id = a.user_id
    """

    if search_query and search_query.strip():
        term = f"%{search_query.strip().lower()}%"
        sql += """
        WHERE LOWER(u.name) LIKE ? 
           OR LOWER(u.email) LIKE ? 
           OR LOWER(COALESCE(u.institution, '')) LIKE ? 
           OR LOWER(COALESCE(u.program, '')) LIKE ?
        """
        params.extend([term, term, term, term])

    sql += """
    GROUP BY u.id
    ORDER BY u.created_at DESC, u.id DESC;
    """

    cursor.execute(sql, params)
    results = []
    for r in cursor.fetchall():
        avg_score = round(float(r[7]), 1) if r[7] is not None else None
        results.append({
            "id": r[0],
            "name": r[1],
            "email": r[2],
            "institution": r[3] or "-",
            "program": r[4] or "-",
            "created_at": r[5],
            "total_attempts": r[6],
            "average_score": avg_score,
            "last_attempt_at": r[8],
        })
    return results


def get_user_assessment_history(
    conn: sqlite3.Connection,
    user_id: int,
) -> list[dict[str, Any]]:
    """
    Retrieve detailed assessment attempt history for a specific user.
    """
    cursor = conn.cursor()
    sql = """
    SELECT 
        a.id,
        a.user_id,
        c.name AS category,
        a.difficulty,
        a.total_questions,
        a.correct_answers,
        a.incorrect_answers,
        a.score,
        a.started_at,
        a.completed_at,
        a.duration_seconds
    FROM attempts a
    JOIN categories c ON a.category_id = c.id
    WHERE a.user_id = ?
    ORDER BY a.started_at DESC, a.id DESC;
    """
    cursor.execute(sql, (user_id,))
    rows = cursor.fetchall()
    history = []
    for r in rows:
        history.append({
            "id": r[0],
            "user_id": r[1],
            "category": r[2],
            "difficulty": r[3],
            "total_questions": r[4] or 0,
            "correct_answers": r[5] if r[5] is not None else 0,
            "incorrect_answers": r[6] if r[6] is not None else 0,
            "score": round(float(r[7]), 1) if r[7] is not None else 0.0,
            "started_at": r[8],
            "completed_at": r[9],
            "duration_seconds": r[10],
        })
    return history


def get_filtered_attempts(
    conn: sqlite3.Connection,
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """
    Retrieve assessment attempts with flexible filters:
    - category (Grammar, Reading, Listening)
    - difficulty (Easy, Medium, Hard)
    - date range (start_date, end_date)
    Read-only view; does not allow direct score modifications.
    """
    cursor = conn.cursor()
    params: list[Any] = []
    conditions = ["1=1"]

    if category and category.strip().lower() != "all":
        conditions.append("LOWER(c.name) = ?")
        params.append(category.strip().lower())

    if difficulty and difficulty.strip().lower() != "all":
        conditions.append("LOWER(a.difficulty) = ?")
        params.append(difficulty.strip().lower())

    if start_date and start_date.strip():
        conditions.append("DATE(a.started_at) >= DATE(?)")
        params.append(start_date.strip())

    if end_date and end_date.strip():
        conditions.append("DATE(a.started_at) <= DATE(?)")
        params.append(end_date.strip())

    sql = f"""
    SELECT 
        a.id,
        u.name AS user_name,
        u.email AS user_email,
        u.institution,
        c.name AS category,
        a.difficulty,
        a.total_questions,
        a.correct_answers,
        a.incorrect_answers,
        a.score,
        a.started_at,
        a.completed_at,
        a.duration_seconds
    FROM attempts a
    JOIN users u ON a.user_id = u.id
    JOIN categories c ON a.category_id = c.id
    WHERE {' AND '.join(conditions)}
    ORDER BY a.started_at DESC, a.id DESC
    LIMIT ?;
    """
    params.append(limit)
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    attempts = []
    for r in rows:
        attempts.append({
            "id": r[0],
            "user_name": r[1],
            "user_email": r[2],
            "institution": r[3] or "-",
            "category": r[4],
            "difficulty": r[5],
            "total_questions": r[6],
            "correct_answers": r[7],
            "incorrect_answers": r[8],
            "score": round(float(r[9]), 1),
            "started_at": r[10],
            "completed_at": r[11],
            "duration_seconds": r[12],
        })
    return attempts


# ==========================================
# QUESTION BANK MANAGEMENT QUERIES (PHASE 11)
# ==========================================

def update_question(
    conn: sqlite3.Connection,
    question_id: int,
    category_id: int,
    question_text: str,
    option_a: str,
    option_b: str,
    option_c: str,
    option_d: str,
    correct_answer: str,
    difficulty: str,
    explanation: Optional[str] = None,
    status: str = "Active",
    subtopic: Optional[str] = None,
    question_type: Optional[str] = None,
    passage_id: Optional[int] = None,
    skill_number: Optional[int] = None,
    skill_name: Optional[str] = None,
    question_order: Optional[int] = None,
) -> bool:
    """Update fields of an existing question record."""
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        UPDATE questions
        SET category_id = ?,
            question_text = ?,
            option_a = ?,
            option_b = ?,
            option_c = ?,
            option_d = ?,
            correct_answer = ?,
            difficulty = ?,
            explanation = ?,
            status = ?,
            subtopic = ?,
            question_type = ?,
            passage_id = ?,
            skill_number = ?,
            skill_name = ?,
            question_order = ?,
            updated_at = ?
        WHERE id = ?;
        """,
        (
            category_id,
            question_text.strip(),
            option_a.strip(),
            option_b.strip(),
            option_c.strip(),
            option_d.strip(),
            correct_answer.strip().upper(),
            difficulty.strip(),
            explanation.strip() if explanation else None,
            status.strip(),
            subtopic.strip() if subtopic else None,
            question_type.strip() if question_type else None,
            passage_id,
            skill_number,
            skill_name.strip() if skill_name else None,
            question_order,
            now_str,
            question_id,
        ),
    )
    return cursor.rowcount > 0


def update_question_status(
    conn: sqlite3.Connection,
    question_id: int,
    new_status: str,
) -> bool:
    """Update only the status of a question (e.g. Active, Inactive, Archived, Draft)."""
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        UPDATE questions
        SET status = ?, updated_at = ?
        WHERE id = ?;
        """,
        (new_status.strip(), now_str, question_id),
    )
    return cursor.rowcount > 0


def delete_question(
    conn: sqlite3.Connection,
    question_id: int,
) -> bool:
    """
    Permanently delete a question and its answer/attempt/audio references.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM answers WHERE question_id = ?", (question_id,))
    cursor.execute("DELETE FROM attempt_questions WHERE question_id = ?", (question_id,))
    cursor.execute("DELETE FROM audio_files WHERE question_id = ?", (question_id,))
    cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
    conn.commit()
    return cursor.rowcount > 0


def delete_questions_by_ids(
    conn: sqlite3.Connection,
    question_ids: list[int],
) -> tuple[int, int]:
    """
    Batch delete multiple questions and their answer/attempt/audio references.
    Returns (deleted_count, 0).
    """
    if not question_ids:
        return 0, 0
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in question_ids)
    cursor.execute(f"DELETE FROM answers WHERE question_id IN ({placeholders})", list(question_ids))
    cursor.execute(f"DELETE FROM attempt_questions WHERE question_id IN ({placeholders})", list(question_ids))
    cursor.execute(f"DELETE FROM audio_files WHERE question_id IN ({placeholders})", list(question_ids))
    cursor.execute(f"DELETE FROM questions WHERE id IN ({placeholders})", list(question_ids))
    deleted = cursor.rowcount
    conn.commit()
    return deleted, 0


def update_questions_status_by_ids(
    conn: sqlite3.Connection,
    question_ids: list[int],
    new_status: str,
) -> int:
    """
    Batch update status for multiple questions (e.g. bulk activate drafts).
    Returns count of updated rows.
    """
    if not question_ids:
        return 0
    cursor = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    placeholders = ",".join("?" for _ in question_ids)
    cursor.execute(
        f"""
        UPDATE questions
        SET status = ?, updated_at = ?
        WHERE id IN ({placeholders});
        """,
        [new_status.strip(), now_str] + list(question_ids),
    )
    conn.commit()
    return cursor.rowcount


def get_questions_filtered(
    conn: sqlite3.Connection,
    category_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    status: Optional[str] = None,
    topic: Optional[str] = None,
    search_query: Optional[str] = None,
    skill_number: Optional[int] = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Retrieve questions matching filter criteria with joined category, passage, and audio data.
    """
    cursor = conn.cursor()
    conditions = ["1=1"]
    params: list[Any] = []

    if category_id is not None:
        conditions.append("q.category_id = ?")
        params.append(category_id)

    if skill_number is not None:
        conditions.append("q.skill_number = ?")
        params.append(skill_number)

    if difficulty and difficulty.strip().lower() != "all":
        conditions.append("LOWER(q.difficulty) = ?")
        params.append(difficulty.strip().lower())

    if status and status.strip().lower() != "all":
        conditions.append("LOWER(q.status) = ?")
        params.append(status.strip().lower())

    if topic and topic.strip().lower() != "all":
        conditions.append("LOWER(q.subtopic) = ?")
        params.append(topic.strip().lower())

    if search_query and search_query.strip():
        term = f"%{search_query.strip().lower()}%"
        conditions.append("(LOWER(q.question_text) LIKE ? OR LOWER(COALESCE(q.explanation, '')) LIKE ? OR LOWER(COALESCE(q.subtopic, '')) LIKE ?)")
        params.extend([term, term, term])

    sql = f"""
    SELECT 
        q.id,
        q.category_id,
        c.name AS category_name,
        q.difficulty,
        q.status,
        q.subtopic,
        q.question_type,
        q.question_text,
        q.option_a,
        q.option_b,
        q.option_c,
        q.option_d,
        q.correct_answer,
        q.explanation,
        q.passage_id,
        p.title AS passage_title,
        p.passage_text,
        af.file_path AS audio_file,
        af.transcript AS audio_transcript,
        q.created_at,
        q.updated_at,
        q.skill_number,
        q.skill_name,
        q.question_order
    FROM questions q
    JOIN categories c ON q.category_id = c.id
    LEFT JOIN passages p ON q.passage_id = p.id
    LEFT JOIN audio_files af ON q.id = af.question_id
    WHERE {' AND '.join(conditions)}
    ORDER BY COALESCE(q.skill_number, 0) ASC, COALESCE(q.question_order, q.id) ASC, q.id DESC
    LIMIT ? OFFSET ?;
    """
    params.extend([limit, offset])
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "category_id": r[1],
            "category_name": r[2],
            "difficulty": r[3],
            "status": r[4],
            "subtopic": r[5] or "General",
            "question_type": r[6] or "Multiple Choice",
            "question_text": r[7],
            "option_a": r[8],
            "option_b": r[9],
            "option_c": r[10],
            "option_d": r[11],
            "correct_answer": r[12],
            "explanation": r[13] or "",
            "passage_id": r[14],
            "passage_title": r[15],
            "passage_text": r[16],
            "audio_file": r[17],
            "audio_transcript": r[18],
            "created_at": r[19],
            "updated_at": r[20],
            "skill_number": r[21],
            "skill_name": r[22] or (f"Skill {r[21]}" if r[21] is not None else None),
            "question_order": r[23],
        })
    return results


def count_questions_filtered(
    conn: sqlite3.Connection,
    category_id: Optional[int] = None,
    difficulty: Optional[str] = None,
    status: Optional[str] = None,
    topic: Optional[str] = None,
    search_query: Optional[str] = None,
    skill_number: Optional[int] = None,
) -> int:
    """Count total questions matching filter criteria."""
    cursor = conn.cursor()
    conditions = ["1=1"]
    params: list[Any] = []

    if category_id is not None:
        conditions.append("category_id = ?")
        params.append(category_id)

    if skill_number is not None:
        conditions.append("skill_number = ?")
        params.append(skill_number)

    if difficulty and difficulty.strip().lower() != "all":
        conditions.append("LOWER(difficulty) = ?")
        params.append(difficulty.strip().lower())

    if status and status.strip().lower() != "all":
        conditions.append("LOWER(status) = ?")
        params.append(status.strip().lower())

    if topic and topic.strip().lower() != "all":
        conditions.append("LOWER(subtopic) = ?")
        params.append(topic.strip().lower())

    if search_query and search_query.strip():
        term = f"%{search_query.strip().lower()}%"
        conditions.append("(LOWER(question_text) LIKE ? OR LOWER(COALESCE(explanation, '')) LIKE ?)")
        params.extend([term, term])

    sql = f"SELECT COUNT(*) FROM questions WHERE {' AND '.join(conditions)};"
    cursor.execute(sql, params)
    return cursor.fetchone()[0]


def get_all_passages(
    conn: sqlite3.Connection,
    category_id: Optional[int] = None,
) -> list[Passage]:
    """Retrieve all passages available for reading questions."""
    cursor = conn.cursor()
    if category_id is not None:
        cursor.execute("SELECT * FROM passages WHERE category_id = ? ORDER BY id DESC;", (category_id,))
    else:
        cursor.execute("SELECT * FROM passages ORDER BY id DESC;")
    return [Passage.from_row(r) for r in cursor.fetchall()]


def update_or_create_audio_file(
    conn: sqlite3.Connection,
    question_id: int,
    file_path: str,
    transcript: Optional[str] = None,
    duration: Optional[float] = None,
) -> int:
    """Create or update linked audio file record for a listening question."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM audio_files WHERE question_id = ?;", (question_id,))
    row = cursor.fetchone()
    if row:
        audio_id = row[0]
        cursor.execute(
            """
            UPDATE audio_files
            SET file_path = ?, transcript = ?, duration = ?
            WHERE id = ?;
            """,
            (file_path.strip(), transcript.strip() if transcript else None, duration, audio_id),
        )
        return audio_id
    else:
        return create_audio_file(conn, question_id, file_path, transcript, duration)


def get_distinct_topics(conn: sqlite3.Connection) -> list[str]:
    """Retrieve unique non-null subtopic/topic names across questions."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT DISTINCT subtopic FROM questions 
        WHERE subtopic IS NOT NULL AND TRIM(subtopic) != ''
        ORDER BY subtopic ASC;
        """
    )
    return [r[0] for r in cursor.fetchall()]


# ==========================================
# QUESTION PERFORMANCE ANALYTICS (PHASE 16)
# ==========================================

def get_question_analytics_data(
    conn: sqlite3.Connection,
    category: Optional[str] = None,
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    skill_number: Optional[int] = None,
    status: str = "Active",
) -> list[dict[str, Any]]:
    """
    Calculate performance metrics (attempts, correct count, incorrect count,
    accuracy percentage) for questions based on stored attempts/answers.
    Supports filtering by category, topic, difficulty, and skill_number.
    """
    cursor = conn.cursor()
    sql = """
    SELECT 
        q.id,
        q.question_text,
        c.name AS category,
        COALESCE(q.subtopic, 'General') AS topic,
        q.difficulty AS assigned_difficulty,
        q.status,
        COALESCE(q.skill_number, 1) AS skill_number,
        COALESCE(q.skill_name, '') AS skill_name,
        COALESCE(q.question_order, 1) AS question_order,
        COUNT(ans.id) AS attempts,
        COALESCE(SUM(CASE WHEN ans.is_correct = 1 THEN 1 ELSE 0 END), 0) AS correct_count,
        COALESCE(SUM(CASE WHEN ans.is_correct = 0 THEN 1 ELSE 0 END), 0) AS incorrect_count
    FROM questions q
    JOIN categories c ON q.category_id = c.id
    LEFT JOIN answers ans ON q.id = ans.question_id
    WHERE 1=1
    """
    params: list[Any] = []

    if status and status.lower() != "all":
        sql += " AND LOWER(q.status) = LOWER(?)"
        params.append(status)

    if category and category.lower() != "all":
        sql += " AND LOWER(c.name) = LOWER(?)"
        params.append(category)

    if topic and topic.lower() != "all":
        sql += " AND LOWER(COALESCE(q.subtopic, 'General')) = LOWER(?)"
        params.append(topic)

    if difficulty and difficulty.lower() != "all":
        sql += " AND LOWER(q.difficulty) = LOWER(?)"
        params.append(difficulty)

    if skill_number is not None:
        sql += " AND q.skill_number = ?"
        params.append(skill_number)

    sql += """
    GROUP BY q.id, q.question_text, c.name, q.subtopic, q.difficulty, q.status, q.skill_number, q.skill_name, q.question_order
    ORDER BY attempts DESC, q.id ASC;
    """

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    results = []

    for r in rows:
        attempts = r[9]
        correct = r[10]
        incorrect = r[11]
        accuracy = round((correct / attempts) * 100.0, 1) if attempts > 0 else 0.0

        results.append({
            "id": r[0],
            "question_text": r[1],
            "category": r[2],
            "topic": r[3],
            "assigned_difficulty": r[4],
            "status": r[5],
            "skill_number": r[6],
            "skill_name": r[7] or f"Skill {r[6]}",
            "question_order": r[8],
            "attempts": attempts,
            "correct_count": correct,
            "incorrect_count": incorrect,
            "accuracy": accuracy,
        })

    return results


def get_category_question_limit(conn: sqlite3.Connection, category_name: str) -> int:
    """Retrieve configured question limit for a given category name (default 20)."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT question_limit FROM categories WHERE name = ? COLLATE NOCASE;",
            (category_name.strip(),),
        )
        row = cursor.fetchone()
        if row and row[0] is not None:
            return max(1, int(row[0]))
    except Exception:
        pass
    return 20


def update_category_question_limit(conn: sqlite3.Connection, category_name: str, limit: int) -> bool:
    """Update configured question limit for a given category name."""
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE categories
        SET question_limit = ?
        WHERE name = ? COLLATE NOCASE;
        """,
        (max(1, limit), category_name.strip()),
    )
    conn.commit()
    return cursor.rowcount > 0


def get_all_categories_with_limits(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Retrieve all categories with their configured limits and current question counts."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            c.id, 
            c.name, 
            c.description, 
            COALESCE(c.question_limit, 20) as question_limit,
            COUNT(CASE WHEN q.status = 'Active' THEN q.id END) as active_question_count,
            COUNT(q.id) as total_question_count
        FROM categories c
        LEFT JOIN questions q ON q.category_id = c.id
        GROUP BY c.id, c.name, c.description, c.question_limit
        ORDER BY c.id ASC;
        """
    )
    results = []
    for row in cursor.fetchall():
        results.append({
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "question_limit": row["question_limit"],
            "active_question_count": row["active_question_count"],
            "total_question_count": row["total_question_count"],
        })
    return results


def get_or_create_skill(
    conn: sqlite3.Connection,
    category_id: int,
    skill_number: int,
    skill_name: str,
    passing_score: float = 70.0,
) -> dict[str, Any]:
    """Retrieve existing skill or create a new one."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, category_id, skill_number, skill_name, passing_score
        FROM skills
        WHERE category_id = ? AND skill_number = ?;
        """,
        (category_id, skill_number),
    )
    row = cursor.fetchone()
    if row:
        if skill_name and row["skill_name"] != skill_name:
            cursor.execute(
                "UPDATE skills SET skill_name = ? WHERE id = ?;",
                (skill_name.strip(), row["id"]),
            )
            conn.commit()
        return dict(row)

    cursor.execute(
        """
        INSERT INTO skills (category_id, skill_number, skill_name, passing_score)
        VALUES (?, ?, ?, ?);
        """,
        (category_id, skill_number, skill_name.strip(), passing_score),
    )
    conn.commit()
    return {
        "id": cursor.lastrowid,
        "category_id": category_id,
        "skill_number": skill_number,
        "skill_name": skill_name.strip(),
        "passing_score": passing_score,
    }


def get_skills_by_category(conn: sqlite3.Connection, category_id: int) -> list[dict[str, Any]]:
    """Retrieve all skills defined in a category with total and active question counts."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            s.id,
            s.category_id,
            s.skill_number,
            s.skill_name,
            s.description,
            s.passing_score,
            COUNT(CASE WHEN q.status = 'Active' THEN q.id END) as active_question_count,
            COUNT(q.id) as total_question_count
        FROM skills s
        LEFT JOIN questions q ON q.category_id = s.category_id AND q.skill_number = s.skill_number
        WHERE s.category_id = ?
        GROUP BY s.id, s.category_id, s.skill_number, s.skill_name, s.description, s.passing_score
        ORDER BY s.skill_number ASC;
        """,
        (category_id,),
    )
    return [dict(r) for r in cursor.fetchall()]


def update_skill_config(
    conn: sqlite3.Connection,
    skill_id: int,
    skill_name: str,
    passing_score: float,
) -> bool:
    """Update skill name and passing score threshold."""
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE skills
        SET skill_name = ?, passing_score = ?
        WHERE id = ?;
        """,
        (skill_name.strip(), float(passing_score), skill_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def get_user_skills_status(
    conn: sqlite3.Connection,
    user_id: int,
    category_id: int,
) -> list[dict[str, Any]]:
    """
    Get all skills for a category along with the user's unlock/passed status:
    - is_unlocked (Skill 1 is always unlocked)
    - is_passed
    - highest_score
    - attempts_count
    """
    skills = get_skills_by_category(conn, category_id)
    if not skills:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT COALESCE(skill_number, 1) as snum, COALESCE(skill_name, 'Skill ' || COALESCE(skill_number, 1)) as sname
            FROM questions
            WHERE category_id = ?
            ORDER BY snum ASC;
            """,
            (category_id,),
        )
        for r in cursor.fetchall():
            get_or_create_skill(conn, category_id, r["snum"], r["sname"])
        skills = get_skills_by_category(conn, category_id)

    if not skills:
        get_or_create_skill(conn, category_id, 1, "Skill 1: Basic Structure")
        skills = get_skills_by_category(conn, category_id)

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT skill_number, is_unlocked, is_passed, highest_score, attempts_count
        FROM user_skill_progress
        WHERE user_id = ? AND category_id = ?;
        """,
        (user_id, category_id),
    )
    progress_map = {r["skill_number"]: dict(r) for r in cursor.fetchall()}

    results = []
    prev_passed = True

    for s in skills:
        s_num = s["skill_number"]
        prog = progress_map.get(s_num)

        if s_num == 1:
            unlocked = True
        elif prog and prog["is_unlocked"]:
            unlocked = True
        elif prev_passed:
            unlocked = True
        else:
            unlocked = False

        passed = bool(prog["is_passed"]) if prog else False
        highest_score = float(prog["highest_score"]) if prog else 0.0
        attempts_count = int(prog["attempts_count"]) if prog else 0

        prev_passed = passed

        results.append({
            "skill_number": s_num,
            "skill_name": s["skill_name"],
            "passing_score": s["passing_score"],
            "active_question_count": s["active_question_count"],
            "total_question_count": s["total_question_count"],
            "is_unlocked": unlocked,
            "is_passed": passed,
            "highest_score": highest_score,
            "attempts_count": attempts_count,
        })

    return results


def record_user_skill_attempt(
    conn: sqlite3.Connection,
    user_id: int,
    category_id: int,
    skill_number: int,
    score: float,
    passing_score: float = 70.0,
) -> tuple[bool, bool]:
    """Update progress when a user completes a skill quiz. Returns (is_passed, next_skill_unlocked)."""
    cursor = conn.cursor()
    is_passed = score >= passing_score
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        SELECT is_passed, highest_score, attempts_count
        FROM user_skill_progress
        WHERE user_id = ? AND category_id = ? AND skill_number = ?;
        """,
        (user_id, category_id, skill_number),
    )
    row = cursor.fetchone()

    if row:
        new_passed = 1 if (row["is_passed"] or is_passed) else 0
        new_highest = max(float(row["highest_score"]), float(score))
        new_attempts = row["attempts_count"] + 1
        cursor.execute(
            """
            UPDATE user_skill_progress
            SET is_passed = ?, highest_score = ?, attempts_count = ?, last_attempt_at = ?
            WHERE user_id = ? AND category_id = ? AND skill_number = ?;
            """,
            (new_passed, new_highest, new_attempts, now_str, user_id, category_id, skill_number),
        )
    else:
        cursor.execute(
            """
            INSERT INTO user_skill_progress 
            (user_id, category_id, skill_number, is_unlocked, is_passed, highest_score, attempts_count, last_attempt_at)
            VALUES (?, ?, ?, 1, ?, ?, 1, ?);
            """,
            (user_id, category_id, skill_number, 1 if is_passed else 0, score, now_str),
        )

    next_unlocked = False
    if is_passed:
        next_num = skill_number + 1
        cursor.execute(
            """
            INSERT INTO user_skill_progress
            (user_id, category_id, skill_number, is_unlocked, is_passed, highest_score, attempts_count)
            VALUES (?, ?, ?, 1, 0, 0.0, 0)
            ON CONFLICT(user_id, category_id, skill_number)
            DO UPDATE SET is_unlocked = 1;
            """,
            (user_id, category_id, next_num),
        )
        next_unlocked = True

    conn.commit()
    return is_passed, next_unlocked


def get_questions_by_skill_sequential(
    conn: sqlite3.Connection,
    category_id: int,
    skill_number: int,
    status: str = "Active",
) -> list[dict[str, Any]]:
    """Retrieve all questions for a given skill ordered sequentially."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            q.id,
            q.category_id,
            COALESCE(q.skill_number, 1) as skill_number,
            COALESCE(q.skill_name, 'Skill ' || COALESCE(q.skill_number, 1)) as skill_name,
            COALESCE(q.question_order, q.id) as question_order,
            q.question_type,
            q.question_text,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.correct_answer,
            q.explanation,
            q.status,
            c.name as category_name,
            p.id as passage_id,
            p.title as passage_title,
            p.passage_text as passage_text,
            af.file_path as audio_file,
            af.transcript as audio_transcript,
            af.duration as audio_duration
        FROM questions q
        JOIN categories c ON c.id = q.category_id
        LEFT JOIN passages p ON p.id = q.passage_id
        LEFT JOIN audio_files af ON af.question_id = q.id
        WHERE q.category_id = ? 
          AND (q.skill_number = ? OR (q.skill_number IS NULL AND ? = 1))
          AND q.status = ?
        ORDER BY COALESCE(q.question_order, q.id) ASC, q.id ASC;
        """,
        (category_id, skill_number, skill_number, status),
    )
    return [dict(r) for r in cursor.fetchall()]




