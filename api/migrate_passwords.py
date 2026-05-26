"""
Password Migration Script
Migrates users from SHA256 to bcrypt hashing.
Run this ONCE after updating to the new security system.
"""

import json
import bcrypt
import os
from pathlib import Path

def migrate_passwords():
    users_file = Path(__file__).parent / "users.json"
    
    if not users_file.exists():
        print("❌ users.json not found!")
        return
    
    with open(users_file, 'r') as f:
        users = json.load(f)
    
    migrated_count = 0
    already_migrated = 0
    needs_reset = 0
    
    print("🔐 Password Migration Tool")
    print("=" * 40)
    
    for user_id, user_data in users.items():
        password = user_data.get('password', '')
        
        # Check if already using bcrypt (starts with $2b$)
        if password.startswith('$2b$'):
            already_migrated += 1
            print(f"✓ {user_data['email']} - Already migrated")
            continue
        
        # Check if it's old SHA256 format (64 hex characters)
        if len(password) == 64 and all(c in '0123456789abcdef' for c in password):
            print(f"⚠ {user_data['email']} - Old SHA256 hash detected")
            print(f"  This user will need to reset their password")
            
            # Mark for password reset by setting a flag
            user_data['password_reset_required'] = True
            
            # Optionally set a temporary bcrypt hash that forces reset
            # For now, we'll just mark them
            needs_reset += 1
        else:
            print(f"? {user_data['email']} - Unknown password format")
    
    # Save updated users.json
    with open(users_file, 'w') as f:
        json.dump(users, f, indent=2)
    
    print("\n" + "=" * 40)
    print(f"✅ Migration complete!")
    print(f"   Already migrated: {already_migrated}")
    print(f"   Need password reset: {needs_reset}")
    print(f"\n📝 Users marked for password reset will need to use")
    print(f"   the 'Forgot Password' feature on next login.")

if __name__ == "__main__":
    migrate_passwords()
