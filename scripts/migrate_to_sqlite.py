#!/usr/bin/env python3
"""
Migration script to convert data.json to SQLite database
"""

import json
import os
from database import (
    init_database,
    create_or_update_user,
    start_session,
    pause_session,
    update_daily_stats,
    update_weekly_stats,
    update_monthly_stats,
    save_details_message,
    get_db
)

JSON_FILE = "data.json"
BACKUP_FILE = "data.json.backup"


def backup_json():
    """Create a backup of the JSON file"""
    if os.path.exists(JSON_FILE):
        import shutil
        shutil.copy(JSON_FILE, BACKUP_FILE)
        print(f"✅ Created backup: {BACKUP_FILE}")
    else:
        print(f"⚠️  No {JSON_FILE} found, starting fresh")


def migrate_data():
    """Migrate data from JSON to SQLite"""
    print("\n🔄 Starting migration from JSON to SQLite...")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Backup JSON first
    backup_json()

    # Initialize database
    print("\n📊 Initializing database...")
    init_database()

    # Load JSON data
    if not os.path.exists(JSON_FILE):
        print("\n✅ No existing data to migrate. Database is ready!")
        return

    print(f"\n📖 Reading {JSON_FILE}...")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Migrate users
    print("\n👥 Migrating users...")
    users_count = 0
    if 'users' in data:
        for user_id, user_data in data['users'].items():
            name = user_data.get('name', 'Unknown')
            create_or_update_user(user_id, name)

            # Migrate active session if exists
            active_session = user_data.get('active_session')
            if active_session:
                start_time = active_session.get('start_time')
                if start_time:
                    start_session(user_id, start_time)

                    paused_at = active_session.get('paused_at')
                    if paused_at:
                        pause_session(user_id, paused_at)

                    # Set paused duration
                    paused_duration = active_session.get('paused_duration', 0)
                    if paused_duration > 0:
                        with get_db() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE users
                                SET active_session_paused_duration = ?
                                WHERE user_id = ?
                            """, (paused_duration, user_id))

            users_count += 1
            print(f"  ✓ {name} ({user_id})")

    print(f"✅ Migrated {users_count} users")

    # Migrate daily stats
    print("\n📅 Migrating daily stats...")
    daily_count = 0
    if 'daily_stats' in data:
        for date, users in data['daily_stats'].items():
            for user_id, stats in users.items():
                name = stats.get('name', 'Unknown')
                total_seconds = stats.get('total_seconds', 0)
                update_daily_stats(user_id, date, name, total_seconds)
                daily_count += 1
        print(f"✅ Migrated {daily_count} daily stat entries")

    # Migrate weekly stats
    print("\n📊 Migrating weekly stats...")
    weekly_count = 0
    if 'weekly_stats' in data:
        for week_key, users in data['weekly_stats'].items():
            for user_id, stats in users.items():
                name = stats.get('name', 'Unknown')
                total_seconds = stats.get('total_seconds', 0)
                update_weekly_stats(user_id, week_key, name, total_seconds)
                weekly_count += 1
        print(f"✅ Migrated {weekly_count} weekly stat entries")

    # Migrate monthly stats
    print("\n📆 Migrating monthly stats...")
    monthly_count = 0
    if 'monthly_stats' in data:
        for month_key, users in data['monthly_stats'].items():
            for user_id, stats in users.items():
                name = stats.get('name', 'Unknown')
                total_seconds = stats.get('total_seconds', 0)
                update_monthly_stats(user_id, month_key, name, total_seconds)
                monthly_count += 1
        print(f"✅ Migrated {monthly_count} monthly stat entries")

    # Migrate details messages
    print("\n💬 Migrating details messages...")
    details_count = 0
    if 'details_message' in data:
        for date, info in data['details_message'].items():
            chat_id = info.get('chat_id')
            message_id = info.get('message_id')
            if chat_id and message_id:
                save_details_message(date, chat_id, message_id)
                details_count += 1
        print(f"✅ Migrated {details_count} details messages")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🎉 Migration completed successfully!")
    print("\n📋 Summary:")
    print(f"  • Users: {users_count}")
    print(f"  • Daily stats: {daily_count}")
    print(f"  • Weekly stats: {weekly_count}")
    print(f"  • Monthly stats: {monthly_count}")
    print(f"  • Details messages: {details_count}")
    print(f"\n💾 Backup saved as: {BACKUP_FILE}")
    print(f"🗄️  Database created: study_bot.db")
    print("\n✅ You can now run your bot with SQLite!")
    print("   The old data.json will no longer be used.")


if __name__ == "__main__":
    migrate_data()
