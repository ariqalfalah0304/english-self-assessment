"""
Data models representing SQLite entities for English Self-Assessment.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Any
import sqlite3


@dataclass
class User:
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    institution: Optional[str] = None
    program: Optional[str] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Admin:
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    role: str = "admin"
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Admin":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Category:
    id: Optional[int] = None
    name: str = ""
    description: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Category":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Topic:
    id: Optional[int] = None
    category_id: int = 0
    name: str = ""
    description: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Topic":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Passage:
    id: Optional[int] = None
    title: Optional[str] = None
    passage_text: str = ""
    category_id: Optional[int] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Passage":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Question:
    id: Optional[int] = None
    category_id: int = 0
    topic_id: Optional[int] = None
    passage_id: Optional[int] = None
    subtopic: Optional[str] = None
    question_type: Optional[str] = None
    question_text: str = ""
    option_a: str = ""
    option_b: str = ""
    option_c: str = ""
    option_d: str = ""
    correct_answer: str = "A"
    explanation: Optional[str] = None
    difficulty: str = "Easy"
    status: str = "Active"
    source_file: Optional[str] = None
    skill_number: int = 1
    skill_name: Optional[str] = None
    question_order: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Question":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Question":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: data[k] for k in data if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)



@dataclass
class AudioFile:
    id: Optional[int] = None
    question_id: int = 0
    file_path: str = ""
    transcript: Optional[str] = None
    duration: Optional[float] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AudioFile":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Attempt:
    id: Optional[int] = None
    user_id: int = 0
    category_id: int = 0
    difficulty: str = "Standard"
    skill_number: Optional[int] = None
    skill_name: Optional[str] = None
    is_passed: int = 0
    total_questions: int = 0
    correct_answers: int = 0
    incorrect_answers: int = 0
    score: float = 0.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Attempt":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AttemptQuestion:
    id: Optional[int] = None
    attempt_id: int = 0
    question_id: int = 0
    question_order: int = 1

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "AttemptQuestion":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Answer:
    id: Optional[int] = None
    attempt_id: int = 0
    question_id: int = 0
    user_answer: Optional[str] = None
    correct_answer: str = ""
    is_correct: int = 0
    answered_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Answer":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ImportHistory:
    id: Optional[int] = None
    file_name: str = ""
    category: str = ""
    total_detected: int = 0
    total_imported: int = 0
    total_failed: int = 0
    imported_by: Optional[str] = None
    imported_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "ImportHistory":
        fields = cls.__dataclass_fields__.keys()
        return cls(**{k: row[k] for k in row.keys() if k in fields})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
