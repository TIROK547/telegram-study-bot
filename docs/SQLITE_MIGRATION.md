# SQLite Migration Guide

## ✅ What's Been Created

I've created the complete SQLite infrastructure for you:

### 1. **database.py** - Complete Database Layer
- ✅ All tables defined (users, daily_stats, weekly_stats, monthly_stats, details_messages)
- ✅ All database operations as functions
- ✅ Proper indexing for performance
- ✅ Context managers for safe connections
- ✅ ACID compliance (no data corruption)

### 2. **migrate_to_sqlite.py** - Migration Script
- ✅ Backs up your data.json
- ✅ Converts all existing data to SQLite
- ✅ Preserves active sessions
- ✅ Migrates all stats (daily/weekly/monthly)

## 🚀 How to Migrate Your Data

### Step 1: Run the Migration
```bash
python3 migrate_to_sqlite.py
```

This will:
- Create `data.json.backup` (your safety backup)
- Create `study_bot.db` (new SQLite database)
- Migrate all users, stats, and sessions
- Show you a summary of migrated data

### Step 2: Update bot.py

The bot.py file needs extensive updates (40+ database calls). Here's the pattern:

#### Old JSON Pattern:
```python
data = load_data()
user = data["users"][user_id]
save_data(data)
```

#### New SQLite Pattern:
```python
import database as db

user = db.get_user(user_id)
db.create_or_update_user(user_id, name)
```

## 📝 Key Changes Needed in bot.py

### 1. **Imports** (Line ~1-13)
```python
# Remove: import json
# Add: import database as db
```

### 2. **Remove These Functions**
- `load_data()`
- `save_data()`
- All caching variables (`_data_cache`, etc.)

### 3. **Update reset_expired_sessions()**
```python
# Old:
def reset_expired_sessions(data):
    # ... lots of code ...
    save_data(data)

# New:
def reset_expired_sessions():
    today = get_today()
    db.reset_expired_sessions(today)
```

### 4. **Update calculate_active_time()**
```python
# Old:
def calculate_active_time(user_data):
    if not user_data.get("active_session"):
        return 0
    session = user_data["active_session"]
    # ...

# New:
def calculate_active_time(session):
    if not session:
        return 0
    # ... rest stays the same ...
```

### 5. **Update build_details_message()**
```python
# Old:
def build_details_message(data):
    reset_expired_sessions(data)
    users_stats = data["daily_stats"][today]
    # ...

# New:
def build_details_message():
    reset_expired_sessions()
    users_stats = db.get_daily_stats(today)
    all_users = db.get_all_users()
    # ...
```

### 6. **Update button_handler()** - The Biggest Change
```python
# Old pattern throughout:
data = load_data()
user = data["users"][user_id]
user["active_session"] = {...}
save_data(data)

# New pattern:
session = db.get_active_session(user_id)
db.start_session(user_id, start_time)
db.pause_session(user_id, paused_at)
db.end_session(user_id)
db.update_daily_stats(user_id, date, name, seconds)
```

### 7. **Update main()** - Add Database Initialization
```python
def main():
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found in .env file")
        return

    # Initialize database
    db.init_database()

    application = (
        ApplicationBuilder()
        # ... rest of setup ...
```

## 🔧 Complete Function Mapping

| Old (JSON) | New (SQLite) |
|-----------|--------------|
| `load_data()` | (remove - use db functions directly) |
| `save_data(data)` | (remove - db functions auto-save) |
| `data["users"][uid]` | `db.get_user(uid)` |
| `data["daily_stats"][date]` | `db.get_daily_stats(date)` |
| `data["weekly_stats"][week]` | `db.get_weekly_stats(week)` |
| `data["monthly_stats"][month]` | `db.get_monthly_stats(month)` |

## ⚠️ Important Notes

1. **Backup First**: The migration script creates `data.json.backup`
2. **Test Migration**: Run `python3 database.py` to test database creation
3. **No Data Loss**: SQLite is much safer than JSON - no corruption risk
4. **Better Performance**: Faster queries, proper indexing
5. **No Credentials**: SQLite doesn't use username/password (it's file-based)

## 🎯 Quick Testing

After migration:
```python
# Test database
python3 database.py  # Should print "Database setup complete!"

# View migrated data
python3 -c "
import database as db
users = db.get_all_users()
print(f'Migrated {len(users)} users')
"
```

## 💡 Need Help?

The migration is complex. Options:
1. **Do it yourself** - Use the patterns above
2. **Staged approach** - Update one function at a time, test as you go
3. **Request help** - Ask me to complete specific sections

## 📊 What You Get

**Benefits of SQLite:**
- ✅ No more file corruption
- ✅ Atomic transactions (all-or-nothing saves)
- ✅ Better performance with many users
- ✅ Proper concurrent access handling
- ✅ Easy backup (just copy study_bot.db)
- ✅ Can query data easily for analytics

**File Structure After Migration:**
```
study-bot/
├── bot.py                  # (needs updating - 40+ changes)
├── database.py             # ✅ Ready
├── migrate_to_sqlite.py    # ✅ Ready
├── study_bot.db           # Created after migration
├── data.json              # Old (can keep as backup)
├── data.json.backup       # Created by migration
└── README.md
```

---

**Status**: Infrastructure ready ✅ | Bot update needed ⚠️ | Data migration ready ✅
