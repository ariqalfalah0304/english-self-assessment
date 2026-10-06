"""
Safe Administrator Initialization Utility for English Self-Assessment.
Allows creating the initial administrator account without hardcoding
any plaintext password into the source code or repository.

Usage:
- Interactive CLI:
    python utils/admin_init.py
- Environment variable provisioning:
    ADMIN_INIT_USER="admin" ADMIN_INIT_PASS="SecretPass123!" python utils/admin_init.py
- Programmatic initialization via admin_service.init_first_admin()
"""

import sys
import os
import getpass
from pathlib import Path

# Add project root to sys.path so modules resolve correctly
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from services.admin_service import init_first_admin, has_any_admin
from database.db import init_db


def run_admin_init(db_path: str | Path | None = None) -> bool:
    """
    Run the administrator initialization routine.
    Refuses execution if an administrator account already exists.
    """
    init_db(db_path)

    if has_any_admin(db_path):
        print("ℹ️ An administrator account already exists in the database.")
        print("   Initialization is skipped to protect existing administrative credentials.")
        return False

    print("=" * 60)
    print("🔐 English Self-Assessment — Safe Initial Admin Setup")
    print("=" * 60)
    print("No administrator accounts currently exist.")
    print("This utility will initialize the first Superadmin account.\n")

    # Check environment variables first (useful for automated container deployment)
    env_user = os.environ.get("ADMIN_INIT_USER")
    env_pass = os.environ.get("ADMIN_INIT_PASS")

    if env_user and env_pass:
        print(f"Detected provisioning credentials from environment for user: {env_user}")
        username = env_user.strip()
        password = env_pass
    else:
        # Prompt interactively
        try:
            username = input("Enter Superadmin Username (min 3 chars): ").strip()
            password = getpass.getpass("Enter Superadmin Password (min 8 chars): ")
            password_confirm = getpass.getpass("Confirm Superadmin Password: ")
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Setup aborted by operator.")
            return False

        if password != password_confirm:
            print("❌ Passwords do not match. Aborting initialization.")
            return False

    success, admin, msg = init_first_admin(username, password, db_path=db_path)
    if success and admin:
        print(f"\n✅ Superadmin account '{admin.username}' created successfully!")
        print(f"   Role: {admin.role}")
        print("   Password has been securely hashed using bcrypt.")
        print("   Never share or commit administrator credentials.")
        return True
    else:
        print(f"\n❌ Initialization failed: {msg}")
        return False


if __name__ == "__main__":
    success = run_admin_init()
    sys.exit(0 if success else 1)
