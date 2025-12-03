import sqlite3
import json
import os
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, Dict, List, Tuple

# Database file location
DB_FILE = os.path.join("data", "study_bot.db")


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """Initialize the database with tables"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                active_session_start TEXT,
                active_session_paused_at TEXT,
                active_session_paused_duration INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Daily stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                name TEXT NOT NULL,
                total_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, date),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Weekly stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                week_key TEXT NOT NULL,
                name TEXT NOT NULL,
                total_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, week_key),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Monthly stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                month_key TEXT NOT NULL,
                name TEXT NOT NULL,
                total_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, month_key),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Details messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS details_messages (
                date TEXT PRIMARY KEY,
                chat_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_stats(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weekly_week ON weekly_stats(week_key)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_monthly_month ON monthly_stats(month_key)")

        conn.commit()
        print("✅ Database initialized successfully")


# USER OPERATIONS

def get_user(user_id: str) -> Optional[Dict]:
    """Get user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def create_or_update_user(user_id: str, name: str) -> None:
    """Create or update user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, name, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                name = excluded.name,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, name))


def get_active_session(user_id: str) -> Optional[Dict]:
    """Get user's active session"""
    user = get_user(user_id)
    if not user or not user['active_session_start']:
        return None

    return {
        "start_time": user['active_session_start'],
        "paused_at": user['active_session_paused_at'],
        "paused_duration": user['active_session_paused_duration'] or 0
    }


def start_session(user_id: str, start_time: str) -> None:
    """Start a study session"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET active_session_start = ?,
                active_session_paused_at = NULL,
                active_session_paused_duration = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (start_time, user_id))


def pause_session(user_id: str, paused_at: str) -> None:
    """Pause a study session"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET active_session_paused_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (paused_at, user_id))


def resume_session(user_id: str, pause_duration: int) -> None:
    """Resume a paused session"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET active_session_paused_at = NULL,
                active_session_paused_duration = active_session_paused_duration + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (pause_duration, user_id))


def end_session(user_id: str) -> None:
    """End a study session"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET active_session_start = NULL,
                active_session_paused_at = NULL,
                active_session_paused_duration = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (user_id,))


def reset_expired_sessions(today: str) -> None:
    """Reset sessions that are not from today"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET active_session_start = NULL,
                active_session_paused_at = NULL,
                active_session_paused_duration = 0,
                updated_at = CURRENT_TIMESTAMP
            WHERE active_session_start IS NOT NULL
                AND date(active_session_start) != ?
        """, (today,))


def get_all_users() -> Dict[str, Dict]:
    """Get all users"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return {row['user_id']: dict(row) for row in rows}


# DAILY STATS OPERATIONS

def get_daily_stats(date: str) -> Dict[str, Dict]:
    """Get daily stats for a specific date"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name, total_seconds
            FROM daily_stats
            WHERE date = ?
        """, (date,))
        rows = cursor.fetchall()
        return {row['user_id']: {"name": row['name'], "total_seconds": row['total_seconds']} for row in rows}


def update_daily_stats(user_id: str, date: str, name: str, seconds: int) -> None:
    """Update daily stats for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_stats (user_id, date, name, total_seconds)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET
                total_seconds = total_seconds + excluded.total_seconds,
                name = excluded.name
        """, (user_id, date, name, seconds))


def ensure_daily_stat_exists(user_id: str, date: str, name: str) -> None:
    """Ensure a daily stat entry exists for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO daily_stats (user_id, date, name, total_seconds)
            VALUES (?, ?, ?, 0)
        """, (user_id, date, name))


# WEEKLY STATS OPERATIONS

def get_weekly_stats(week_key: str) -> Dict[str, Dict]:
    """Get weekly stats"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name, total_seconds
            FROM weekly_stats
            WHERE week_key = ?
        """, (week_key,))
        rows = cursor.fetchall()
        return {row['user_id']: {"name": row['name'], "total_seconds": row['total_seconds']} for row in rows}


def update_weekly_stats(user_id: str, week_key: str, name: str, seconds: int) -> None:
    """Update weekly stats"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO weekly_stats (user_id, week_key, name, total_seconds)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, week_key) DO UPDATE SET
                total_seconds = total_seconds + excluded.total_seconds,
                name = excluded.name
        """, (user_id, week_key, name, seconds))


# MONTHLY STATS OPERATIONS

def get_monthly_stats(month_key: str) -> Dict[str, Dict]:
    """Get monthly stats"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name, total_seconds
            FROM monthly_stats
            WHERE month_key = ?
        """, (month_key,))
        rows = cursor.fetchall()
        return {row['user_id']: {"name": row['name'], "total_seconds": row['total_seconds']} for row in rows}


def update_monthly_stats(user_id: str, month_key: str, name: str, seconds: int) -> None:
    """Update monthly stats"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO monthly_stats (user_id, month_key, name, total_seconds)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, month_key) DO UPDATE SET
                total_seconds = total_seconds + excluded.total_seconds,
                name = excluded.name
        """, (user_id, month_key, name, seconds))


# DETAILS MESSAGE OPERATIONS

def get_details_message(date: str) -> Optional[Dict]:
    """Get details message for a date"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chat_id, message_id
            FROM details_messages
            WHERE date = ?
        """, (date,))
        row = cursor.fetchone()
        if row:
            return {"chat_id": row['chat_id'], "message_id": row['message_id']}
        return None


def save_details_message(date: str, chat_id: int, message_id: int) -> None:
    """Save details message info"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO details_messages (date, chat_id, message_id)
            VALUES (?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                chat_id = excluded.chat_id,
                message_id = excluded.message_id
        """, (date, chat_id, message_id))


# UTILITY FUNCTIONS

def get_all_daily_stats() -> Dict[str, Dict]:
    """Get all daily stats"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT date, user_id, name, total_seconds FROM daily_stats ORDER BY date DESC")
        rows = cursor.fetchall()

        result = {}
        for row in rows:
            date = row['date']
            if date not in result:
                result[date] = {}
            result[date][row['user_id']] = {
                "name": row['name'],
                "total_seconds": row['total_seconds']
            }
        return result


def get_all_weekly_stats() -> Dict[str, Dict]:
    """Get all weekly stats"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT week_key, user_id, name, total_seconds FROM weekly_stats ORDER BY week_key DESC")
        rows = cursor.fetchall()

        result = {}
        for row in rows:
            week = row['week_key']
            if week not in result:
                result[week] = {}
            result[week][row['user_id']] = {
                "name": row['name'],
                "total_seconds": row['total_seconds']
            }
        return result


def get_all_monthly_stats() -> Dict[str, Dict]:
    """Get all monthly stats"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT month_key, user_id, name, total_seconds FROM monthly_stats ORDER BY month_key DESC")
        rows = cursor.fetchall()

        result = {}
        for row in rows:
            month = row['month_key']
            if month not in result:
                result[month] = {}
            result[month][row['user_id']] = {
                "name": row['name'],
                "total_seconds": row['total_seconds']
            }
        return result


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    print("Database setup complete!")
