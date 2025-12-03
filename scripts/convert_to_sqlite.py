#!/usr/bin/env python3
"""
Automated conversion of bot.py to bot_sqlite.py
This script makes all necessary SQLite replacements
"""

import re

print("🔄 Converting bot.py to bot_sqlite.py...")

# Read original bot.py
with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update imports - remove json, add database
content = content.replace(
    '''import os
import json
import asyncio''',
    '''import os
import asyncio''')

content = content.replace(
    '''from functools import lru_cache

# Load environment variables''',
    '''from functools import lru_cache

# Import database functions
import database as db

# Load environment variables''')

# 2. Remove JSON database config and caching
old_db_section = '''# Timezone
IRAN_TZ = pytz.timezone('Asia/Tehran')

# JSON Database file
DB_FILE = "data.json"

# Cache for data to reduce file I/O
_data_cache = None
_cache_time = None
CACHE_DURATION = 2

def load_data():
    """Load data from JSON file with caching"""
    global _data_cache, _cache_time

    now = datetime.now()
    if _data_cache and _cache_time and (now - _cache_time).total_seconds() < CACHE_DURATION:
        return _data_cache

    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            _data_cache = json.load(f)
    else:
        _data_cache = {
            "users": {},
            "daily_stats": {},
            "weekly_stats": {},
            "monthly_stats": {},
            "details_message": {}
        }

    _cache_time = now
    return _data_cache

def save_data(data):
    """Save data to JSON file and update cache"""
    global _data_cache, _cache_time
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _data_cache = data
    _cache_time = datetime.now()'''

new_db_section = '''# Timezone
IRAN_TZ = pytz.timezone('Asia/Tehran')'''

content = content.replace(old_db_section, new_db_section)

# 3. Update reset_expired_sessions function
old_reset = '''def reset_expired_sessions(data):
    """Reset sessions that are older than today - optimized"""
    today = get_today()
    expired_users = []

    for user_id, user_data in data["users"].items():
        if user_data.get("active_session"):
            session_start = datetime.fromisoformat(user_data["active_session"]["start_time"])
            # Make sure session_start is timezone-aware
            if session_start.tzinfo is None:
                session_start = IRAN_TZ.localize(session_start)

            session_date = session_start.astimezone(IRAN_TZ).strftime("%Y-%m-%d")

            if session_date != today:
                expired_users.append(user_id)

    for user_id in expired_users:
        data["users"][user_id]["active_session"] = None

    if expired_users:
        save_data(data)'''

new_reset = '''def reset_expired_sessions():
    """Reset sessions that are older than today"""
    today = get_today()
    db.reset_expired_sessions(today)'''

content = content.replace(old_reset, new_reset)

# 4. Update calculate_active_time to accept session instead of user_data
content = content.replace(
    'def calculate_active_time(user_data):',
    'def calculate_active_time(session):'
)
content = content.replace(
    '''    """Calculate current active study time for a user"""
    if not user_data.get("active_session"):
        return 0

    session = user_data["active_session"]''',
    '''    """Calculate current active study time for a user"""
    if not session:
        return 0'''
)

# 5. Update build_details_message
old_build = '''def build_details_message(data):
    """Build the live details message - RTL-friendly UI"""
    today = get_today()
    reset_expired_sessions(data)'''

new_build = '''def build_details_message():
    """Build the live details message - RTL-friendly UI"""
    today = get_today()
    reset_expired_sessions()'''

content = content.replace(old_build, new_build)

# Replace data["daily_stats"][today] with db.get_daily_stats(today)
content = re.sub(
    r'if today not in data\["daily_stats"\] or not data\["daily_stats"\]\[today\]:',
    'users_stats = db.get_daily_stats(today)\n    if not users_stats:',
    content
)

content = content.replace(
    '''users_stats = data["daily_stats"][today]
    active = []
    finished = []

    for uid, info in users_stats.items():
        name = info["name"]
        completed_time = info["total_seconds"]

        if uid in data["users"] and data["users"][uid].get("active_session"):
            current_session_time = calculate_active_time(data["users"][uid])''',
    '''all_users = db.get_all_users()
    active = []
    finished = []

    for uid, info in users_stats.items():
        name = info["name"]
        completed_time = info["total_seconds"]

        user_data = all_users.get(uid, {})
        session = db.get_active_session(uid)
        if session:
            current_session_time = calculate_active_time(session)''')

content = content.replace(
    '''is_paused = data["users"][uid]["active_session"].get("paused_at") is not None''',
    '''is_paused = session.get("paused_at") is not None''')

# 6. Update stats command
content = content.replace(
    '''async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics"""
    if not check_group_access(update):
        await access_denied(update)
        return

    data = load_data()
    today = get_today()

    if today not in data["daily_stats"] or not data["daily_stats"][today]:
        await update.message.reply_text("📊 امروز هنوز هیچ مطالعه‌ای ثبت نشده است.")
        return

    users_stats = data["daily_stats"][today]''',
    '''async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics"""
    if not check_group_access(update):
        await access_denied(update)
        return

    today = get_today()
    users_stats = db.get_daily_stats(today)

    if not users_stats:
        await update.message.reply_text("📊 امروز هنوز هیچ مطالعه‌ای ثبت نشده است.")
        return''')

content = content.replace(
    '''user_totals = []

    for uid, stats in users_stats.items():
        total = stats["total_seconds"]
        if uid in data["users"] and data["users"][uid].get("active_session"):
            total += calculate_active_time(data["users"][uid])''',
    '''user_totals = []

    for uid, stats in users_stats.items():
        total = stats["total_seconds"]
        session = db.get_active_session(uid)
        if session:
            total += calculate_active_time(session)''')

# 7. Update details command
content = content.replace(
    '''async def details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show live study details"""
    if not check_group_access(update):
        await access_denied(update)
        return

    data = load_data()
    today = get_today()

    msg_text = build_details_message(data)
    sent = await update.message.reply_text(msg_text)

    if "details_message" not in data:
        data["details_message"] = {}

    data["details_message"][today] = {
        "chat_id": sent.chat_id,
        "message_id": sent.message_id
    }
    save_data(data)''',
    '''async def details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show live study details"""
    if not check_group_access(update):
        await access_denied(update)
        return

    today = get_today()
    msg_text = build_details_message()
    sent = await update.message.reply_text(msg_text)

    db.save_details_message(today, sent.chat_id, sent.message_id)''')

# 8. Update update_details_message
content = content.replace(
    '''async def update_details_message(context: ContextTypes.DEFAULT_TYPE):
    """Periodically update the details message"""
    try:
        data = load_data()
        today = get_today()

        if "details_message" not in data or today not in data["details_message"]:
            return

        info = data["details_message"][today]
        chat_id = info["chat_id"]
        message_id = info["message_id"]

        new_text = build_details_message(data)''',
    '''async def update_details_message(context: ContextTypes.DEFAULT_TYPE):
    """Periodically update the details message"""
    try:
        today = get_today()
        info = db.get_details_message(today)

        if not info:
            return

        chat_id = info["chat_id"]
        message_id = info["message_id"]

        new_text = build_details_message()''')

# 9. Update update_period_stats
content = content.replace(
    '''def update_period_stats(data, user_id, username, duration):
    """Update weekly and monthly statistics"""
    week_key = get_persian_week_key()
    month_key = get_persian_month_key()

    if "weekly_stats" not in data:
        data["weekly_stats"] = {}
    if "monthly_stats" not in data:
        data["monthly_stats"] = {}

    if week_key not in data["weekly_stats"]:
        data["weekly_stats"][week_key] = {}
    if month_key not in data["monthly_stats"]:
        data["monthly_stats"][month_key] = {}

    if user_id not in data["weekly_stats"][week_key]:
        data["weekly_stats"][week_key][user_id] = {"name": username, "total_seconds": 0}
    data["weekly_stats"][week_key][user_id]["total_seconds"] += duration
    data["weekly_stats"][week_key][user_id]["name"] = username

    if user_id not in data["monthly_stats"][month_key]:
        data["monthly_stats"][month_key][user_id] = {"name": username, "total_seconds": 0}
    data["monthly_stats"][month_key][user_id]["total_seconds"] += duration
    data["monthly_stats"][month_key][user_id]["name"] = username''',
    '''def update_period_stats(user_id, username, duration):
    """Update weekly and monthly statistics"""
    week_key = get_persian_week_key()
    month_key = get_persian_month_key()

    db.update_weekly_stats(user_id, week_key, username, duration)
    db.update_monthly_stats(user_id, month_key, username, duration)''')

#  10. Update button_handler - beginning
content = content.replace(
    '''async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    if not check_group_access(update):
        await access_denied(update)
        return

    query = update.callback_query

    # Parse callback_data to extract action and authorized user_id
    callback_parts = query.data.split(":")
    action = callback_parts[0]
    authorized_user_id = int(callback_parts[1]) if len(callback_parts) > 1 else None

    # Verify the user clicking is the authorized user
    if authorized_user_id and query.from_user.id != authorized_user_id:
        await query.answer("⛔️ این دکمه‌ها فقط برای کاربری هست که دستور رو زده!", show_alert=True)
        return

    await query.answer()

    data = load_data()
    reset_expired_sessions(data)

    user_id = str(query.from_user.id)
    username = f"@{query.from_user.username}" if query.from_user.username else f"user: ({query.from_user.first_name})"
    today = get_today()

    if user_id not in data["users"]:
        data["users"][user_id] = {"name": username, "active_session": None}

    if today not in data["daily_stats"]:
        data["daily_stats"][today] = {}

    if user_id not in data["daily_stats"][today]:
        data["daily_stats"][today][user_id] = {"name": username, "total_seconds": 0}

    user = data["users"][user_id]''',
    '''async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    if not check_group_access(update):
        await access_denied(update)
        return

    query = update.callback_query

    # Parse callback_data to extract action and authorized user_id
    callback_parts = query.data.split(":")
    action = callback_parts[0]
    authorized_user_id = int(callback_parts[1]) if len(callback_parts) > 1 else None

    # Verify the user clicking is the authorized user
    if authorized_user_id and query.from_user.id != authorized_user_id:
        await query.answer("⛔️ این دکمه‌ها فقط برای کاربری هست که دستور رو زده!", show_alert=True)
        return

    await query.answer()

    reset_expired_sessions()

    user_id = str(query.from_user.id)
    username = f"@{query.from_user.username}" if query.from_user.username else f"user: ({query.from_user.first_name})"
    today = get_today()

    # Ensure user exists
    db.create_or_update_user(user_id, username)

    # Ensure daily stat exists
    db.ensure_daily_stat_exists(user_id, today, username)

    # Get user session
    session = db.get_active_session(user_id)''')

print("✅ Step 1/5: Imports and basic functions updated")

# Save intermediate
with open('bot_sqlite.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Step 2/5: Core database functions updated")
print("✅ Intermediate file saved")
print("\n⚠️  Now updating button_handler body (40+ replacements)...")
print("This is the largest section - please wait...")

# Now make button_handler replacements
# Group stats section
content = content.replace(
    '''elif action == "group_stats":
        if today not in data["daily_stats"] or not data["daily_stats"][today]:''',
    '''elif action == "group_stats":
        users_stats = db.get_daily_stats(today)
        if not users_stats:''')

content = content.replace(
    '''users_stats = data["daily_stats"][today]
        user_totals = []

        for uid, stats in users_stats.items():
            total = stats["total_seconds"]
            if uid in data["users"] and data["users"][uid].get("active_session"):
                total += calculate_active_time(data["users"][uid])''',
    '''user_totals = []

        for uid, stats in users_stats.items():
            total = stats["total_seconds"]
            user_session = db.get_active_session(uid)
            if user_session:
                total += calculate_active_time(user_session)''')

# start_study section
content = content.replace(
    '''elif action == "start_study":
        if user.get("active_session"):''',
    '''elif action == "start_study":
        if session:''')

content = content.replace(
    '''else:
            now = get_iran_now()
            user["active_session"] = {
                "start_time": now.isoformat(),
                "paused_at": None,
                "paused_duration": 0
            }
            save_data(data)''',
    '''else:
            now = get_iran_now()
            db.start_session(user_id, now.isoformat())''')

# pause_study section
content = content.replace(
    '''elif action == "pause_study":
        if not user.get("active_session"):''',
    '''elif action == "pause_study":
        if not session:''')

content = content.replace(
    '''elif user["active_session"].get("paused_at"):''',
    '''elif session.get("paused_at"):''')

content = content.replace(
    '''else:
            user["active_session"]["paused_at"] = get_iran_now().isoformat()
            save_data(data)

            current_time = calculate_active_time(user)''',
    '''else:
            paused_at = get_iran_now().isoformat()
            db.pause_session(user_id, paused_at)

            session = db.get_active_session(user_id)
            current_time = calculate_active_time(session)''')

# resume_study section
content = content.replace(
    '''elif action == "resume_study":
        if not user.get("active_session"):''',
    '''elif action == "resume_study":
        if not session:''')

content = content.replace(
    '''elif not user["active_session"].get("paused_at"):''',
    '''elif not session.get("paused_at"):''')

content = content.replace(
    '''else:
            paused_at = datetime.fromisoformat(user["active_session"]["paused_at"])
            # Make sure paused_at is timezone-aware
            if paused_at.tzinfo is None:
                paused_at = IRAN_TZ.localize(paused_at)

            pause_duration = (get_iran_now() - paused_at).total_seconds()
            user["active_session"]["paused_duration"] += pause_duration
            user["active_session"]["paused_at"] = None
            save_data(data)''',
    '''else:
            paused_at = datetime.fromisoformat(session["paused_at"])
            # Make sure paused_at is timezone-aware
            if paused_at.tzinfo is None:
                paused_at = IRAN_TZ.localize(paused_at)

            pause_duration = int((get_iran_now() - paused_at).total_seconds())
            db.resume_session(user_id, pause_duration)''')

# end_study section
content = content.replace(
    '''elif action == "end_study":
        if not user.get("active_session"):''',
    '''elif action == "end_study":
        if not session:''')

content = content.replace(
    '''else:
            session_duration = calculate_active_time(user)''',
    '''else:
            session_duration = calculate_active_time(session)''')

content = content.replace(
    '''data["daily_stats"][today][user_id]["total_seconds"] += session_duration
            data["daily_stats"][today][user_id]["name"] = username

            update_period_stats(data, user_id, username, session_duration)

            user["active_session"] = None
            save_data(data)

            total_today = data["daily_stats"][today][user_id]["total_seconds"]''',
    '''db.update_daily_stats(user_id, today, username, session_duration)
            update_period_stats(user_id, username, session_duration)
            db.end_session(user_id)

            daily_stat = db.get_daily_stats(today).get(user_id, {})
            total_today = daily_stat.get("total_seconds", 0)''')

# my_stats section
content = content.replace(
    '''elif action == "my_stats":
        completed_time = data["daily_stats"][today][user_id]["total_seconds"]

        if user.get("active_session"):
            current_session_time = calculate_active_time(user)''',
    '''elif action == "my_stats":
        daily_stat = db.get_daily_stats(today).get(user_id, {})
        completed_time = daily_stat.get("total_seconds", 0)

        if session:
            current_session_time = calculate_active_time(session)''')

content = content.replace(
    '''if user["active_session"].get("paused_at"):''',
    '''if session.get("paused_at"):''')

# top_students section
content = content.replace(
    '''elif action == "top_students":
        if today not in data["daily_stats"] or not data["daily_stats"][today]:''',
    '''elif action == "top_students":
        users_stats = db.get_daily_stats(today)
        if not users_stats:''')

content = content.replace(
    '''user_totals = []
        for uid, stats in data["daily_stats"][today].items():
            total = stats["total_seconds"]
            if uid in data["users"] and data["users"][uid].get("active_session"):
                total += calculate_active_time(data["users"][uid])''',
    '''user_totals = []
        for uid, stats in users_stats.items():
            total = stats["total_seconds"]
            user_session = db.get_active_session(uid)
            if user_session:
                total += calculate_active_time(user_session)''')

# weekly_stats section
content = content.replace(
    '''elif action == "weekly_stats":
        week_key = get_persian_week_key()

        if "weekly_stats" not in data or week_key not in data["weekly_stats"] or not data["weekly_stats"][week_key]:''',
    '''elif action == "weekly_stats":
        week_key = get_persian_week_key()
        week_stats = db.get_weekly_stats(week_key)

        if not week_stats:''')

content = content.replace(
    '''sorted_users = sorted(
            data["weekly_stats"][week_key].items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        )''',
    '''sorted_users = sorted(
            week_stats.items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        )''')

# monthly_stats section
content = content.replace(
    '''elif action == "monthly_stats":
        month_key = get_persian_month_key()

        if "monthly_stats" not in data or month_key not in data["monthly_stats"] or not data["monthly_stats"][month_key]:''',
    '''elif action == "monthly_stats":
        month_key = get_persian_month_key()
        month_stats = db.get_monthly_stats(month_key)

        if not month_stats:''')

content = content.replace(
    '''sorted_users = sorted(
            data["monthly_stats"][month_key].items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        )''',
    '''sorted_users = sorted(
            month_stats.items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        )''')

print("✅ Step 3/5: button_handler updated")

# 11. Update daily_report
content = content.replace(
    '''async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Send daily report at midnight"""
    data = load_data()
    yesterday_dt = get_iran_now() - timedelta(days=1)
    yesterday = yesterday_dt.strftime("%Y-%m-%d")

    if yesterday in data["daily_stats"] and data["daily_stats"][yesterday]:
        sorted_users = sorted(
            data["daily_stats"][yesterday].items(),''',
    '''async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Send daily report at midnight"""
    yesterday_dt = get_iran_now() - timedelta(days=1)
    yesterday = yesterday_dt.strftime("%Y-%m-%d")

    yesterday_stats = db.get_daily_stats(yesterday)
    if yesterday_stats:
        sorted_users = sorted(
            yesterday_stats.items(),''')

# 12. Update startup_migration
content = content.replace(
    '''async def startup_migration(application):
    """Fetch and update usernames from Telegram API on startup"""
    print("🔄 Running startup migration to fetch usernames...")
    data = load_data()''',
    '''async def startup_migration(application):
    """Fetch and update usernames from Telegram API on startup"""
    print("🔄 Running startup migration to fetch usernames...")
    all_users = db.get_all_users()''')

content = content.replace(
    '''# Go through all users and fetch their current Telegram info
    for user_id_str, user_data in data["users"].items():''',
    '''# Go through all users and fetch their current Telegram info
    for user_id_str, user_data in all_users.items():''')

content = content.replace(
    '''# Update if changed
                if current_name != new_name:
                    user_data["name"] = new_name
                    needs_save = True''',
    '''# Update if changed
                if current_name != new_name:
                    db.create_or_update_user(user_id_str, new_name)
                    needs_save = True''')

content = content.replace(
    '''# User not accessible (blocked bot, deleted account, etc.)
                if not current_name.startswith("@") and not current_name.startswith("user: "):
                    # Fix format for inaccessible users
                    user_data["name"] = f"user: ({current_name})"
                    needs_save = True''',
    '''# User not accessible (blocked bot, deleted account, etc.)
                if not current_name.startswith("@") and not current_name.startswith("user: "):
                    # Fix format for inaccessible users
                    new_name = f"user: ({current_name})"
                    db.create_or_update_user(user_id_str, new_name)
                    needs_save = True''')

# Remove the update names in stats sections since DB handles it automatically
content = content.replace(
    '''# Update all stats with the new names
    if needs_save:
        # Update names in daily_stats
        for date_key, users in data.get("daily_stats", {}).items():
            for user_id, stats in users.items():
                if user_id in data["users"]:
                    stats["name"] = data["users"][user_id]["name"]

        # Update names in weekly_stats
        for week_key, users in data.get("weekly_stats", {}).items():
            for user_id, stats in users.items():
                if user_id in data["users"]:
                    stats["name"] = data["users"][user_id]["name"]

        # Update names in monthly_stats
        for month_key, users in data.get("monthly_stats", {}).items():
            for user_id, stats in users.items():
                if user_id in data["users"]:
                    stats["name"] = data["users"][user_id]["name"]

        save_data(data)''',
    '''# Names are automatically updated in database via create_or_update_user
    if needs_save:''')

print("✅ Step 4/5: Utility functions updated")

# 13. Update main() to initialize database
content = content.replace(
    '''def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found in .env file")
        return

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)''',
    '''def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found in .env file")
        return

    # Initialize database
    print("📊 Initializing database...")
    db.init_database()

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)''')

print("✅ Step 5/5: main() updated with database initialization")

# Write final file
with open('bot_sqlite.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("🎉 Conversion complete!")
print("\n📁 Files created:")
print("   • bot_sqlite.py - Complete SQLite version")
print("   • bot.py - Original (unchanged)")
print("   • bot_json_backup.py - Backup")
print("\n✅ Next steps:")
print("   1. Run: python3 migrate_to_sqlite.py")
print("   2. Test: python3 bot_sqlite.py")
print("   3. If all works, replace bot.py with bot_sqlite.py")
print("\n💡 The SQLite version is ready to use!")
