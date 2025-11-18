#!/usr/bin/env python3
"""
Clear Database Script
=====================
Removes all listings and drafts from the database for a fresh start.

Run with:
    python clear_database.py

WARNING: This will delete ALL listings and drafts!
"""

import sqlite3
from pathlib import Path
import shutil

def clear_database():
    """Clear all listings from database"""
    db_path = Path("data/cross_poster.db")

    if not db_path.exists():
        print("❌ Database not found!")
        return

    print("⚠️  WARNING: This will delete ALL listings and drafts!")
    confirm = input("Type 'DELETE ALL' to confirm: ")

    if confirm != "DELETE ALL":
        print("❌ Cancelled")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count before
    cursor.execute("SELECT COUNT(*) FROM listings")
    count = cursor.fetchone()[0]

    print(f"\n🗑️  Deleting {count} listing(s)...")

    # Delete all listings
    cursor.execute("DELETE FROM listings")
    cursor.execute("DELETE FROM platform_listings")
    cursor.execute("DELETE FROM sync_log")
    cursor.execute("DELETE FROM notifications")

    # Reset auto-increment
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('listings', 'platform_listings', 'sync_log', 'notifications')")

    conn.commit()
    conn.close()

    # Delete draft photos
    draft_photos = Path("data/draft_photos")
    if draft_photos.exists():
        print("🗑️  Deleting draft photos...")
        shutil.rmtree(draft_photos)
        draft_photos.mkdir()

    # Delete uploads
    uploads = Path("data/uploads")
    if uploads.exists():
        print("🗑️  Deleting uploads...")
        for file in uploads.glob("*"):
            if file.is_file():
                file.unlink()

    print("\n✅ Database cleared! Fresh start ready.")
    print("   All users will start with a clean slate.")

if __name__ == "__main__":
    clear_database()
