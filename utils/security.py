"""
Security utilities and hardening for English Self-Assessment (Phase 19).
Handles:
- Uploaded file size limits and extension verification
- ZIP archive integrity and zip-bomb mitigation for DOCX and XLSX
- Path traversal prevention for audio assets and file imports
- Filename sanitization to prevent filesystem overwrites
- Text input sanitization
"""

import io
import re
import zipfile
from pathlib import Path
from typing import Optional


MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
MAX_ZIP_UNCOMPRESSED_BYTES = 50 * 1024 * 1024  # 50 MB uncompressed limit
ALLOWED_UPLOAD_EXTENSIONS = {".docx", ".xlsx"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a"}
ZIP_MAGIC_HEADER = b"PK\x03\x04"


def sanitize_filename(filename: str, max_length: int = 120) -> str:
    r"""
    Sanitize an uploaded or user-provided filename to prevent path traversal
    and filesystem overwriting.
    - Strips directory components (/, \)
    - Strips null bytes and control characters
    - Keeps only safe alphanumeric, underscore, dot, hyphen, space
    - Truncates to max_length
    """
    if not filename:
        return "unnamed_file"

    # Take only the base name (strip any leading directory paths)
    base = Path(filename).name

    # Remove null bytes and control characters
    cleaned = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", base)

    # Remove path traversal tokens
    cleaned = cleaned.replace("..", "").replace("/", "").replace("\\", "")

    # Retain safe characters
    cleaned = re.sub(r"[^a-zA-Z0-9._\-\s]", "_", cleaned).strip()

    # Prevent hidden files
    cleaned = cleaned.lstrip(".")

    if not cleaned:
        return "unnamed_file"

    return cleaned[:max_length]


def validate_uploaded_file(
    filename: str,
    file_bytes: bytes,
    max_size_bytes: int = MAX_UPLOAD_SIZE_BYTES,
    allowed_extensions: Optional[set[str]] = None,
) -> tuple[bool, str]:
    """
    Validate uploaded file integrity before parsing.
    Checks:
    - Empty file rejection
    - File size ceiling
    - Allowed extension
    - ZIP magic bytes for OpenXML (.docx and .xlsx)
    - Valid ZIP archive structure without decompression bomb
    """
    if not file_bytes:
        return False, "Uploaded file is empty (0 bytes)."

    if len(file_bytes) > max_size_bytes:
        size_mb = len(file_bytes) / (1024 * 1024)
        max_mb = max_size_bytes / (1024 * 1024)
        return False, f"File size ({size_mb:.1f} MB) exceeds maximum allowed limit of {max_mb:.0f} MB."

    exts = allowed_extensions or ALLOWED_UPLOAD_EXTENSIONS
    ext = Path(filename).suffix.lower()
    if ext not in exts:
        return False, f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(exts))}"

    # Verify OpenXML ZIP header
    if not file_bytes.startswith(ZIP_MAGIC_HEADER):
        return False, f"Invalid file content: '{filename}' does not appear to be a valid {ext.upper()} document."

    # Verify ZIP structure and guard against zip bombs
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            # Check for bad zip CRC
            bad_file = zf.testzip()
            if bad_file:
                return False, f"Corrupted file: internal archive entry '{bad_file}' failed checksum test."

            # Guard against zip bombs (excessive uncompressed size)
            total_uncompressed = sum(info.file_size for info in zf.infolist())
            if total_uncompressed > MAX_ZIP_UNCOMPRESSED_BYTES:
                return False, "File rejected: uncompressed contents exceed safe processing limits."
    except zipfile.BadZipFile:
        return False, f"Corrupted or invalid {ext.upper()} archive."
    except Exception as e:
        return False, f"Failed to verify archive integrity: {str(e)}"

    return True, ""


def is_safe_audio_path(
    file_path: Optional[str],
    base_dir: Path,
) -> tuple[bool, Optional[Path], str]:
    """
    Validate and resolve an audio file reference safely.
    Prevents path traversal and arbitrary non-audio file access.
    Checks:
    - Non-empty path
    - Strictly forbids '..' path traversal components
    - Strictly forbids null bytes
    - Extension within allowed audio formats (.mp3, .wav, .ogg, .m4a)
    - Relative paths must strictly reside within base_dir
    """
    if not file_path or not str(file_path).strip():
        return False, None, "Audio path is empty."

    raw_str = str(file_path).strip()

    # Reject null bytes
    if "\x00" in raw_str:
        return False, None, "Path contains invalid null byte character."

    # Strictly reject path traversal sequences
    if ".." in raw_str:
        return False, None, "Path traversal detected: directory traversal '..' is forbidden."

    # Check extension
    ext = Path(raw_str).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return False, None, f"Invalid audio extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"

    raw_path = Path(raw_str)

    if raw_path.is_absolute():
        resolved = raw_path.resolve()
        if resolved.suffix.lower() not in ALLOWED_AUDIO_EXTENSIONS:
            return False, None, "Invalid audio file."
        return True, resolved, ""

    # Resolve relative path against base_dir
    base_resolved = base_dir.resolve()
    target_resolved = (base_dir / raw_path).resolve()

    # Check that target is inside base_resolved
    try:
        target_resolved.relative_to(base_resolved)
    except ValueError:
        return False, None, "Path traversal detected: audio file must reside within application directory."

    return True, target_resolved, ""


def sanitize_text(text: Optional[str], max_length: Optional[int] = None) -> str:
    """Sanitize general text input to strip null bytes and normalize whitespace."""
    if not text:
        return ""
    cleaned = text.replace("\x00", "").strip()
    if max_length and len(cleaned) > max_length:
        return cleaned[:max_length]
    return cleaned
