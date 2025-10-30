#!/usr/bin/env python3
"""
Database migration script for JamUpTaskMaster
Adds the 'pinned' column to existing databases
"""
import sqlite3
import sys
import os

def migrate_database(db_path):
    """Add pinned column if it doesn't exist"""
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if pinned column exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'pinned' not in columns:
            print("Adding 'pinned' column...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN pinned BOOLEAN DEFAULT 0")
            conn.commit()
            print("✓ Column added successfully!")
        else:
            print("✓ Column already exists")

        conn.close()
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    # Default path
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "tasks.db"
    )

    # Allow custom path
    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    print(f"Migrating database at: {db_path}")
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
