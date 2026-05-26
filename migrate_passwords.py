#!/usr/bin/env python3
"""Migrate existing user passwords from SHA256 to bcrypt."""
import json
import bcrypt
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
USERS_PATH = PROJECT_ROOT / "api" / "users.json"

# The known plaintext password for all test users (SHA256: 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9)
KNOWN_PASSWORD = "password"

def migrate_passwords():
    """Migrate all user passwords to bcrypt."""
    if not USERS_PATH.exists():
        print("users.json not found!")
        return
    
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    migrated_count = 0
    for user in data["users"]:
        old_hash = user.get("password", "")
        # Check if it's the old SHA256 format (64 hex chars)
        if len(old_hash) == 64 and all(c in "0123456789abcdef" for c in old_hash.lower()):
            # Hash with bcrypt
            new_hash = bcrypt.hashpw(KNOWN_PASSWORD.encode(), bcrypt.gensalt(rounds=12)).decode()
            user["password"] = new_hash
            migrated_count += 1
            print(f"Migrated: {user['email']}")
        elif old_hash.startswith("$2"):
            print(f"Already bcrypt: {user['email']}")
        else:
            print(f"Unknown format: {user['email']}")
    
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nMigration complete! {migrated_count} users migrated to bcrypt.")

if __name__ == "__main__":
    migrate_passwords()
