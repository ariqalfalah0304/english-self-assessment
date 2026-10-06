"""
SQLite database connection management and idempotent initialization.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Generator

from config.settings import DATABASE_PATH
from database.schema import (
    PRAGMA_FOREIGN_KEYS,
    ALL_TABLE_STATEMENTS,
    CREATE_INDEXES,
    SEED_CATEGORIES,
)


def get_db_path(custom_path: Optional[str | Path] = None) -> Path | str:
    """Return the resolved Path or string for the SQLite database."""
    if custom_path is not None:
        if str(custom_path) == ":memory:":
            return ":memory:"
        return Path(custom_path).resolve()
    return DATABASE_PATH.resolve()


def create_connection(db_path: Optional[str | Path] = None) -> sqlite3.Connection:
    """Create and return a configured sqlite3 Connection with restrictive file permissions."""
    resolved_path = get_db_path(db_path)
    if resolved_path != ":memory:":
        db_file = Path(resolved_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            db_file.parent.chmod(0o700)
        except OSError:
            pass

    conn = sqlite3.connect(resolved_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute(PRAGMA_FOREIGN_KEYS)
    if resolved_path != ":memory:":
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except sqlite3.OperationalError:
            pass

    if resolved_path != ":memory:":
        try:
            Path(resolved_path).chmod(0o600)
        except OSError:
            pass

    return conn


@contextmanager
def get_connection(db_path: Optional[str | Path] = None) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite database transactions."""
    conn = create_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[str | Path] = None) -> None:
    """
    Initialize SQLite database schema and seed initial data.
    Idempotent: safe to run multiple times without altering existing records.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Create all tables
        for statement in ALL_TABLE_STATEMENTS:
            cursor.execute(statement)

        # Ensure question_limit column exists in categories table
        cursor.execute("PRAGMA table_info(categories);")
        col_names = [r["name"] for r in cursor.fetchall()]
        if "question_limit" not in col_names:
            cursor.execute("ALTER TABLE categories ADD COLUMN question_limit INTEGER DEFAULT 20;")

        # Ensure skill columns exist in questions table
        cursor.execute("PRAGMA table_info(questions);")
        q_cols = [r["name"] for r in cursor.fetchall()]
        if "skill_number" not in q_cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN skill_number INTEGER DEFAULT 1;")
        if "skill_name" not in q_cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN skill_name TEXT;")
        if "question_order" not in q_cols:
            cursor.execute("ALTER TABLE questions ADD COLUMN question_order INTEGER DEFAULT 1;")

        # Ensure skill columns exist in attempts table
        cursor.execute("PRAGMA table_info(attempts);")
        att_cols = [r["name"] for r in cursor.fetchall()]
        if "skill_number" not in att_cols:
            cursor.execute("ALTER TABLE attempts ADD COLUMN skill_number INTEGER DEFAULT 1;")
        if "skill_name" not in att_cols:
            cursor.execute("ALTER TABLE attempts ADD COLUMN skill_name TEXT;")
        if "is_passed" not in att_cols:
            cursor.execute("ALTER TABLE attempts ADD COLUMN is_passed INTEGER DEFAULT 0;")

        # Migrate attempts table if legacy CHECK(difficulty IN ...) constraint is present
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='attempts';")
        attempts_sql_row = cursor.fetchone()
        if attempts_sql_row and "CHECK" in attempts_sql_row[0] and "difficulty" in attempts_sql_row[0]:
            cursor.execute("PRAGMA foreign_keys=OFF;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attempts_migrated (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                    difficulty TEXT NOT NULL DEFAULT 'Standard',
                    skill_number INTEGER DEFAULT 1,
                    skill_name TEXT,
                    is_passed INTEGER DEFAULT 0,
                    total_questions INTEGER NOT NULL DEFAULT 0,
                    correct_answers INTEGER NOT NULL DEFAULT 0,
                    incorrect_answers INTEGER NOT NULL DEFAULT 0,
                    score REAL NOT NULL DEFAULT 0.0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds INTEGER
                );
            """)
            cursor.execute("""
                INSERT INTO attempts_migrated (id, user_id, category_id, difficulty, skill_number, skill_name, is_passed, total_questions, correct_answers, incorrect_answers, score, started_at, completed_at, duration_seconds)
                SELECT id, user_id, category_id, difficulty,
                       COALESCE(skill_number, 1), skill_name, COALESCE(is_passed, 0),
                       total_questions, correct_answers, incorrect_answers, score, started_at, completed_at, duration_seconds
                FROM attempts;
            """)
            cursor.execute("DROP TABLE attempts;")
            cursor.execute("ALTER TABLE attempts_migrated RENAME TO attempts;")
            cursor.execute("PRAGMA foreign_keys=ON;")

        # Create all indexes
        for index_statement in CREATE_INDEXES:
            cursor.execute(index_statement)

        # Seed default categories if not already present
        for cat_id, name, desc in SEED_CATEGORIES:
            cursor.execute(
                """
                INSERT OR IGNORE INTO categories (id, name, description)
                VALUES (?, ?, ?);
                """,
                (cat_id, name, desc),
            )
