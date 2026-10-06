"""
SQLite Database Backup Utility for English Self-Assessment.
Creates an atomic, consistent online snapshot of the SQLite database
even while the application is actively serving users.

Usage:
    python utils/backup_db.py
    python utils/backup_db.py --dest /path/to/custom_backup_dir/
"""

import sys
import os
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import DATABASE_PATH, DATA_DIR


def backup_database(
    source_db: Path | str | None = None,
    backup_dir: Path | str | None = None,
) -> Path:
    """
    Perform an atomic online backup of the SQLite database.
    Returns the Path to the generated backup file.
    """
    src_path = Path(source_db or DATABASE_PATH).resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"Source database file not found at: {src_path}")

    target_dir = Path(backup_dir or (DATA_DIR / "backups")).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        target_dir.chmod(0o700)
    except OSError:
        pass

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"english_assessment_backup_{timestamp}.db"
    dest_path = target_dir / backup_filename

    # Perform atomic online backup using SQLite's backup API
    src_conn = sqlite3.connect(src_path)
    dest_conn = sqlite3.connect(dest_path)

    try:
        with dest_conn:
            src_conn.backup(dest_conn, pages=100)
    finally:
        src_conn.close()
        dest_conn.close()

    # Restrict permissions on backup file (owner read/write only)
    try:
        dest_path.chmod(0o600)
    except OSError:
        pass

    # Integrity verification on backup
    verify_conn = sqlite3.connect(dest_path)
    try:
        cursor = verify_conn.cursor()
        cursor.execute("PRAGMA quick_check;")
        result = cursor.fetchone()[0]
        if result != "ok":
            raise RuntimeError(f"Backup integrity check failed: {result}")
    finally:
        verify_conn.close()

    return dest_path


def main():
    parser = argparse.ArgumentParser(description="Backup SQLite database for English Self-Assessment.")
    parser.add_argument("--src", type=str, default=None, help="Source SQLite database path.")
    parser.add_argument("--dest", type=str, default=None, help="Target directory for backup file.")
    args = parser.parse_args()

    print("=" * 60)
    print("📦 English Self-Assessment — SQLite Online Backup Utility")
    print("=" * 60)

    try:
        dest_path = backup_database(source_db=args.src, backup_dir=args.dest)
        size_kb = dest_path.stat().st_size / 1024.0
        print("✅ Database backup completed successfully!")
        print(f"   Backup Path : {dest_path}")
        print(f"   Backup Size : {size_kb:.2f} KB")
        print("   Integrity   : Verified (PRAGMA quick_check OK)")
        print("   Permissions : Restrictive (0600)")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Backup failed: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
