"""
Migration script to convert SHA256 hashed passwords to bcrypt hashes.
Run this ONCE after updating to the new security system.
"""
import json
import bcrypt
import hashlib
from pathlib import Path

def migrate_passwords():
    users_file = Path(__file__).parent / "users.json"
    
    if not users_file.exists():
        print("❌ users.json not found!")
        return
    
    with open(users_file, 'r') as f:
        users_data = json.load(f)
    
    migrated_count = 0
    skipped_count = 0
    
    for user_id, user in users_data.get('users', {}).items():
        password_hash = user.get('password', '')
        
        # Skip if already migrated (bcrypt hashes start with $2b$)
        if password_hash.startswith('$2b$'):
            print(f"✓ User '{user['email']}' already uses bcrypt")
            skipped_count += 1
            continue
        
        # This is a SHA256 hash - we need the original password to re-hash
        # Since we can't reverse SHA256, we'll mark these users for password reset
        print(f"⚠ User '{user['email']}' has SHA256 hash - requires password reset")
        user['password_reset_required'] = True
        # Keep the old hash temporarily but mark for reset
        user['old_hash'] = password_hash
        # Set a temporary invalid bcrypt hash
        user['password'] = '$2b$12$INVALID_HASH_NEEDS_RESET'
        migrated_count += 1
    
    # Save updated users
    with open(users_file, 'w') as f:
        json.dump(users_data, f, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Migration Complete!")
    print(f"{'='*50}")
    print(f"✓ Already secure (bcrypt): {skipped_count} users")
    print(f"⚠ Need password reset: {migrated_count} users")
    print(f"\nIMPORTANT: Users with SHA256 hashes will need to reset their passwords.")
    print(f"Their next login attempt will fail, and they should use 'Forgot Password'.")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    migrate_passwords()
