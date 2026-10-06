"""
SQLite database schema definitions and initialization logic.
Fully idempotent: uses CREATE TABLE IF NOT EXISTS and INSERT OR IGNORE for initial seeds.
"""

PRAGMA_FOREIGN_KEYS = "PRAGMA foreign_keys = ON;"

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    institution TEXT,
    program TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_ADMINS_TABLE = """
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_CATEGORIES_TABLE = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    question_limit INTEGER DEFAULT 20
);
"""

CREATE_TOPICS_TABLE = """
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT
);
"""

CREATE_PASSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS passages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    passage_text TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_QUESTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
    passage_id INTEGER REFERENCES passages(id) ON DELETE SET NULL,
    subtopic TEXT,
    question_type TEXT,
    question_text TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL CHECK(correct_answer IN ('A', 'B', 'C', 'D')),
    explanation TEXT,
    difficulty TEXT NOT NULL DEFAULT 'Standard' CHECK(difficulty IN ('Easy', 'Medium', 'Hard', 'Standard', 'easy', 'medium', 'hard', 'standard')),
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Draft', 'Active', 'Inactive', 'Archived', 'draft', 'active', 'inactive', 'archived')),
    source_file TEXT,
    skill_number INTEGER,
    skill_name TEXT,
    question_order INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_AUDIO_FILES_TABLE = """
CREATE TABLE IF NOT EXISTS audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    transcript TEXT,
    duration REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_ATTEMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    difficulty TEXT NOT NULL DEFAULT 'Standard',
    skill_number INTEGER,
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
"""

CREATE_ATTEMPT_QUESTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS attempt_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    question_order INTEGER NOT NULL,
    UNIQUE(attempt_id, question_order),
    UNIQUE(attempt_id, question_id)
);
"""

CREATE_ANSWERS_TABLE = """
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE RESTRICT,
    user_answer TEXT,
    correct_answer TEXT NOT NULL,
    is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_IMPORT_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    category TEXT NOT NULL,
    total_detected INTEGER NOT NULL DEFAULT 0,
    total_imported INTEGER NOT NULL DEFAULT 0,
    total_failed INTEGER NOT NULL DEFAULT 0,
    imported_by TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_SKILLS_TABLE = """
CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    skill_number INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    description TEXT,
    passing_score REAL DEFAULT 70.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category_id, skill_number)
);
"""

CREATE_USER_SKILL_PROGRESS_TABLE = """
CREATE TABLE IF NOT EXISTS user_skill_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    skill_number INTEGER NOT NULL,
    is_unlocked INTEGER NOT NULL DEFAULT 0,
    is_passed INTEGER NOT NULL DEFAULT 0,
    highest_score REAL DEFAULT 0.0,
    attempts_count INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    UNIQUE(user_id, category_id, skill_number)
);
"""

# Performance & search indexes
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
    "CREATE INDEX IF NOT EXISTS idx_questions_lookup ON questions(category_id, difficulty, status);",
    "CREATE INDEX IF NOT EXISTS idx_questions_skill ON questions(category_id, skill_number);",
    "CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic_id);",
    "CREATE INDEX IF NOT EXISTS idx_questions_passage ON questions(passage_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempts_user ON attempts(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempts_category ON attempts(category_id);",
    "CREATE INDEX IF NOT EXISTS idx_attempt_questions_order ON attempt_questions(attempt_id, question_order);",
    "CREATE INDEX IF NOT EXISTS idx_answers_attempt ON answers(attempt_id);",
    "CREATE INDEX IF NOT EXISTS idx_audio_files_question ON audio_files(question_id);",
    "CREATE INDEX IF NOT EXISTS idx_skill_progress_user ON user_skill_progress(user_id, category_id);",
]

# Initial Seed Data for categories (Section 35 PRD)
SEED_CATEGORIES = [
    (1, "Grammar", "Measures understanding of English grammar structures and rules."),
    (2, "Reading", "Measures reading comprehension and text analysis skills."),
    (3, "Listening", "Measures listening comprehension from authentic audio materials."),
]

ALL_TABLE_STATEMENTS = [
    CREATE_USERS_TABLE,
    CREATE_ADMINS_TABLE,
    CREATE_CATEGORIES_TABLE,
    CREATE_TOPICS_TABLE,
    CREATE_PASSAGES_TABLE,
    CREATE_QUESTIONS_TABLE,
    CREATE_AUDIO_FILES_TABLE,
    CREATE_ATTEMPTS_TABLE,
    CREATE_ATTEMPT_QUESTIONS_TABLE,
    CREATE_ANSWERS_TABLE,
    CREATE_IMPORT_HISTORY_TABLE,
    CREATE_SKILLS_TABLE,
    CREATE_USER_SKILL_PROGRESS_TABLE,
]
