import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data")).resolve()
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", DATA_DIR / "english_assessment.db")).resolve()

AUDIO_DIR = BASE_DIR / "audio"
FEEDBACK_AUDIO_DIR = AUDIO_DIR / "feedback"
LISTENING_AUDIO_DIR = AUDIO_DIR / "listening"

UPLOADS_DIR = Path(os.environ.get("UPLOADS_DIR", BASE_DIR / "uploads")).resolve()
DOCX_UPLOADS_DIR = UPLOADS_DIR / "imported_docs"
EXCEL_UPLOADS_DIR = UPLOADS_DIR / "imported_excel"

ASSETS_DIR = BASE_DIR / "assets"

# App Settings
APP_NAME = "English Self-Assessment Quiz"
APP_TAGLINE = "Test. Practice. Understand. Improve."
DEFAULT_QUESTIONS_PER_TEST = int(os.environ.get("DEFAULT_QUESTIONS_PER_TEST", 20))


def ensure_directories() -> None:
    """Ensure all required runtime application directories exist."""
    for directory in [
        DATA_DIR,
        AUDIO_DIR,
        FEEDBACK_AUDIO_DIR,
        LISTENING_AUDIO_DIR,
        UPLOADS_DIR,
        DOCX_UPLOADS_DIR,
        EXCEL_UPLOADS_DIR,
        ASSETS_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)


# Guarantee runtime directory readiness upon configuration import
ensure_directories()
