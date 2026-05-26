"""
Password Migration Script
Migrates users from SHA256 to bcrypt hashing.
Run this ONCE after updating to the new security system.
"""
import json
import bcrypt
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
    needs_reset = 0
    
    print("🔐 Password Migration Tool")
    print("=" * 50)
    
    for user_id, user in users_data.get('users', {}).items():
        password_hash = user.get('password', '')
        
        # Skip if already migrated (bcrypt hashes start with $2b$)
        if password_hash.startswith('$2b$'):
            print(f"✓ {user.get('email', user_id)} - Already uses bcrypt")
            skipped_count += 1
            continue
        
        # Check if it's old SHA256 format (64 hex characters)
        if len(password_hash) == 64 and all(c in '0123456789abcdef' for c in password_hash):
            print(f"⚠ {user.get('email', user_id)} - Old SHA256 hash detected")
            print(f"  This user will need to reset their password")
            
            # Mark for password reset
            user['password_reset_required'] = True
            needs_reset += 1
        else:
            print(f"? {user.get('email', user_id)} - Unknown password format")
    
    # Save updated users.json
    with open(users_file, 'w') as f:
        json.dump(users_data, f, indent=2)
    
    print("\n" + "=" * 50)
    print(f"✅ Migration Complete!")
    print(f"   Already secure (bcrypt): {skipped_count} users")
    print(f"   Need password reset: {needs_reset} users")
    print(f"\n📝 Users marked for password reset will need to use")
    print(f"   the 'Forgot Password' feature on next login.")
    print("=" * 50)

if __name__ == "__main__":
    migrate_passwords()