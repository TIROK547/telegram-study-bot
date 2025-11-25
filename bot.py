import os
import json
import asyncio
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import ApplicationBuilder
import pytz
import jdatetime
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_GROUP_ID = int(os.getenv("ALLOWED_GROUP_ID", "0"))
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "30"))

# Timezone
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
    _cache_time = datetime.now()

def to_farsi_number(num):
    """Convert English/Arabic numbers to Farsi"""
    english_to_farsi = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    return ''.join(english_to_farsi.get(c, c) for c in str(num))

def format_time(seconds):
    """Convert seconds to readable Farsi format"""
    if seconds < 60:
        return "کمتر از یک دقیقه"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    hours_fa = to_farsi_number(hours)
    minutes_fa = to_farsi_number(minutes)
    
    if hours == 0:
        return f"{minutes_fa} دقیقه"
    elif minutes == 0:
        return f"{hours_fa} ساعت"
    else:
        return f"{hours_fa} ساعت و {minutes_fa} دقیقه"

def format_time_hms(dt):
    """Format datetime to Farsi HH:MM:SS"""
    time_str = dt.strftime('%H:%M:%S')
    return to_farsi_number(time_str)

def format_date_farsi(dt):
    """Format date to Farsi"""
    date_str = dt.strftime('%Y/%m/%d')
    return to_farsi_number(date_str)

def get_iran_now():
    """Get current time in Iran timezone"""
    return datetime.now(IRAN_TZ)

def get_today():
    """Get today's date as string"""
    return get_iran_now().strftime("%Y-%m-%d")

@lru_cache(maxsize=10)
def get_persian_date_cached(date_str):
    """Cached Persian date calculation"""
    now = datetime.strptime(date_str, "%Y-%m-%d")
    now = IRAN_TZ.localize(now)
    j_date = jdatetime.datetime.fromgregorian(datetime=now)
    return {
        "year": j_date.year,
        "month": j_date.month,
        "day": j_date.day,
        "week": j_date.isocalendar()[1],
        "date_str": j_date.strftime("%Y-%m-%d")
    }

def get_persian_date():
    """Get today's Persian date"""
    return get_persian_date_cached(get_today())

def get_persian_week_key():
    """Get Persian week identifier"""
    p_date = get_persian_date()
    return f"{p_date['year']}-W{p_date['week']:02d}"

def get_persian_month_key():
    """Get Persian month identifier"""
    p_date = get_persian_date()
    return f"{p_date['year']}-{p_date['month']:02d}"

def format_persian_date_display(p_date):
    """Format Persian date with Farsi numbers"""
    year = to_farsi_number(p_date['year'])
    month = to_farsi_number(f"{p_date['month']:02d}")
    day = to_farsi_number(f"{p_date['day']:02d}")
    return f"{year}/{month}/{day}"

def check_group_access(update: Update) -> bool:
    """Check if the update is from the allowed group"""
    if ALLOWED_GROUP_ID == 0:
        return True
    
    chat_id = update.effective_chat.id
    return chat_id == ALLOWED_GROUP_ID

async def access_denied(update: Update):
    """Send access denied message"""
    message = "⛔️ این ربات فقط در گروه مجاز فعال است."
    if update.message:
        await update.message.reply_text(message)
    elif update.callback_query:
        await update.callback_query.answer(message, show_alert=True)

def reset_expired_sessions(data):
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
        save_data(data)

def calculate_active_time(user_data):
    """Calculate current active study time for a user"""
    if not user_data.get("active_session"):
        return 0
    
    session = user_data["active_session"]
    start_time = datetime.fromisoformat(session["start_time"])
    
    # Make sure start_time is timezone-aware
    if start_time.tzinfo is None:
        start_time = IRAN_TZ.localize(start_time)
    
    paused_duration = session.get("paused_duration", 0)
    
    if session.get("paused_at"):
        paused_at = datetime.fromisoformat(session["paused_at"])
        # Make sure paused_at is timezone-aware
        if paused_at.tzinfo is None:
            paused_at = IRAN_TZ.localize(paused_at)
        total_time = (paused_at - start_time).total_seconds() - paused_duration
    else:
        total_time = (get_iran_now() - start_time).total_seconds() - paused_duration
    
    return max(0, int(total_time))

def get_main_menu_keyboard():
    """Get main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("▶️ شروع مطالعه", callback_data="start_study")],
        [
            InlineKeyboardButton("⏸ توقف موقت", callback_data="pause_study"),
            InlineKeyboardButton("▶️ ادامه دادن", callback_data="resume_study")
        ],
        [InlineKeyboardButton("⏹ پایان و ذخیره", callback_data="end_study")],
        [
            InlineKeyboardButton("📊 آمار من", callback_data="my_stats"),
            InlineKeyboardButton("📈 آمار گروه", callback_data="group_stats")
        ],
        [
            InlineKeyboardButton("🏆 رتبه‌بندی‌ها", callback_data="leaderboard_menu"),
            InlineKeyboardButton("❓ راهنما", callback_data="help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_leaderboard_menu_keyboard():
    """Get leaderboard menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🏆 امروز", callback_data="top_students")],
        [InlineKeyboardButton("📅 هفتگی", callback_data="weekly_stats")],
        [InlineKeyboardButton("📆 ماهانه", callback_data="monthly_stats")],
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button():
    """Get back button keyboard"""
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data="back_main")]]
    return InlineKeyboardMarkup(keyboard)

def build_details_message(data):
    """Build the live details message - RTL-friendly UI"""
    today = get_today()
    reset_expired_sessions(data)

    now = get_iran_now()
    time_fa = format_time_hms(now)
    
    if today not in data["daily_stats"] or not data["daily_stats"][today]:
        return (
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 آمار زنده امروز\n"
            f"🕐 ساعت: {time_fa}\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"💤 هنوز کسی امروز شروع نکرده!\n\n"
            f"🎯 اولین نفر باش و شروع کن! 💪"
        )

    users_stats = data["daily_stats"][today]
    active = []
    finished = []

    for uid, info in users_stats.items():
        name = info["name"]
        completed_time = info["total_seconds"]

        if uid in data["users"] and data["users"][uid].get("active_session"):
            current_session_time = calculate_active_time(data["users"][uid])
            total_time = completed_time + current_session_time
            is_paused = data["users"][uid]["active_session"].get("paused_at") is not None
            active.append((name, total_time, is_paused))
        else:
            if completed_time > 0:
                finished.append((name, completed_time))

    msg = f"━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📊 آمار زنده امروز\n"
    msg += f"🕐 ساعت: {time_fa}\n"
    msg += f"━━━━━━━━━━━━━━━━━━━\n\n"

    # Active students
    if active:
        msg += "🔥 در حال مطالعه:\n\n"
        for n, t, is_paused in sorted(active, key=lambda x: x[1], reverse=True):
            status = "⏸" if is_paused else "▶️"
            msg += f"{status} {n}\n"
            msg += f"     ⏱ {format_time(t)}\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

    # Finished students
    if finished:
        msg += "✅ امروز مطالعه کردند:\n\n"
        for n, t in sorted(finished, key=lambda x: x[1], reverse=True)[:5]:
            msg += f"👤 {n}\n"
            msg += f"     ⏱ {format_time(t)}\n\n"
        msg += "━━━━━━━━━━━━━━━━━━━\n\n"

    # Top 5
    all_users = [(n, t) for n, t, _ in active] + finished
    if all_users:
        top = sorted(all_users, key=lambda x: x[1], reverse=True)[:5]
        
        msg += "🏆 برترین‌های امروز:\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, (n, t) in enumerate(top):
            msg += f"{medals[i]} {n}\n"
            msg += f"     ⏱ {format_time(t)}\n\n"

    msg += "💡 برای جزئیات بیشتر: /stats"
    
    return msg

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics"""
    if not check_group_access(update):
        await access_denied(update)
        return
    
    data = load_data()
    today = get_today()

    if today not in data["daily_stats"] or not data["daily_stats"][today]:
        await update.message.reply_text("📊 امروز هنوز هیچ مطالعه‌ای ثبت نشده است.")
        return

    users_stats = data["daily_stats"][today]
    user_totals = []
    
    for uid, stats in users_stats.items():
        total = stats["total_seconds"]
        if uid in data["users"] and data["users"][uid].get("active_session"):
            total += calculate_active_time(data["users"][uid])
        if total > 0:
            user_totals.append((stats["name"], total))
    
    sorted_users = sorted(user_totals, key=lambda x: x[1], reverse=True)
    
    now = get_iran_now()
    p_date = get_persian_date()
    
    date_fa = format_date_farsi(now)
    p_date_fa = format_persian_date_display(p_date)
    total_students_fa = to_farsi_number(len(sorted_users))
    
    message = f"━━━━━━━━━━━━━━━━━━━━━\n"
    message += f"📊 گزارش کامل امروز\n"
    message += f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"📅 تاریخ: {date_fa}\n"
    message += f"📆 شمسی: {p_date_fa}\n\n"
    
    total_study_time = sum(t for _, t in sorted_users)
    total_students = len(sorted_users)
    
    message += f"📈 آمار کلی:\n\n"
    message += f"👥 تعداد دانشجو: {total_students_fa} نفر\n"
    message += f"⏱ مجموع مطالعه: {format_time(total_study_time)}\n"
    
    if total_students > 0:
        avg_time = total_study_time // total_students
        message += f"📊 میانگین: {format_time(avg_time)}\n"
    
    message += f"\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"🏅 رتبه‌بندی کامل:\n\n"
    
    for i, (name, total) in enumerate(sorted_users, 1):
        if i <= 3:
            medals = ["🥇", "🥈", "🥉"]
            message += f"{medals[i-1]} {name}\n"
        else:
            rank_fa = to_farsi_number(i)
            message += f"{rank_fa}. {name}\n"
        message += f"     ⏱ {format_time(total)}\n\n"
    
    await update.message.reply_text(message)

async def details(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    save_data(data)

async def update_details_message(context: ContextTypes.DEFAULT_TYPE):
    """Periodically update the details message"""
    data = load_data()
    today = get_today()

    if "details_message" not in data or today not in data["details_message"]:
        return

    info = data["details_message"][today]
    chat_id = info["chat_id"]
    message_id = info["message_id"]

    new_text = build_details_message(data)

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=new_text
        )
    except Exception:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    if not check_group_access(update):
        await access_denied(update)
        return
    
    now = get_iran_now()
    p_date = get_persian_date()
    
    time_fa = format_time_hms(now)
    p_date_fa = format_persian_date_display(p_date)
    
    message = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎓 ربات ردیاب مطالعه\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"سلام! 👋 خوش اومدی!\n\n"
        f"با این ربات می‌تونی زمان مطالعه‌ت رو ثبت کنی\n"
        f"و با دوستات رقابت کنی! 🏆\n\n"
        f"📅 امروز:\n"
        f"🕐 ساعت: {time_fa}\n"
        f"📆 تاریخ شمسی: {p_date_fa}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👇 از دکمه‌های زیر استفاده کن:"
    )
    
    await update.message.reply_text(message, reply_markup=get_main_menu_keyboard())

def update_period_stats(data, user_id, username, duration):
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
    data["monthly_stats"][month_key][user_id]["name"] = username

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    if not check_group_access(update):
        await access_denied(update)
        return
    
    query = update.callback_query
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
    
    user = data["users"][user_id]
    
    # Navigation
    if query.data == "back_main":
        now = get_iran_now()
        p_date = get_persian_date()
        
        time_fa = format_time_hms(now)
        p_date_fa = format_persian_date_display(p_date)
        
        message = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎓 منوی اصلی\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📅 {time_fa} - {p_date_fa}\n\n"
            f"👇 یکی از گزینه‌ها رو انتخاب کن:"
        )
        await query.edit_message_text(message, reply_markup=get_main_menu_keyboard())
        return
    
    elif query.data == "leaderboard_menu":
        message = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"🏆 رتبه‌بندی‌ها\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"کدوم رتبه‌بندی رو می‌خوای ببینی؟ 👀"
        )
        await query.edit_message_text(message, reply_markup=get_leaderboard_menu_keyboard())
        return
    
    elif query.data == "help":
        message = (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"❓ راهنمای کامل\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📖 دستورات:\n\n"
            f"▶️ شروع مطالعه:\n"
            f"     برای شروع جلسه جدید\n\n"
            f"⏸ توقف موقت:\n"
            f"     برای استراحت کوتاه\n\n"
            f"▶️ ادامه دادن:\n"
            f"     ادامه بعد از استراحت\n\n"
            f"⏹ پایان و ذخیره:\n"
            f"     برای ذخیره زمان مطالعه\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"📊 دستورات خط:\n\n"
            f"/details - آمار زنده (خودکار)\n"
            f"/stats - آمار کامل امروز\n\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 نکته مهم:\n"
            f"حتماً بعد از تموم شدن مطالعه،\n"
            f"روی 'پایان و ذخیره' کلیک کن! ✅"
        )
        await query.edit_message_text(message, reply_markup=get_back_button())
        return
    
    elif query.data == "group_stats":
        if today not in data["daily_stats"] or not data["daily_stats"][today]:
            message = (
                f"━━━━━━━━━━━━━━━\n"
                f"📈 آمار گروه\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"💤 امروز هنوز کسی شروع نکرده!"
            )
            await query.edit_message_text(message, reply_markup=get_back_button())
            return
        
        users_stats = data["daily_stats"][today]
        user_totals = []
        
        for uid, stats in users_stats.items():
            total = stats["total_seconds"]
            if uid in data["users"] and data["users"][uid].get("active_session"):
                total += calculate_active_time(data["users"][uid])
            if total > 0:
                user_totals.append((stats["name"], total))
        
        total_study = sum(t for _, t in user_totals)
        total_students = len(user_totals)
        
        now = get_iran_now()
        p_date = get_persian_date()
        p_date_fa = format_persian_date_display(p_date)
        students_fa = to_farsi_number(total_students)
        
        message = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"📈 آمار گروه\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📅 {p_date_fa}\n\n"
            f"📊 خلاصه:\n\n"
            f"👥 افراد فعال: {students_fa} نفر\n"
            f"⏱ مجموع مطالعه: {format_time(total_study)}\n"
        )
        
        if total_students > 0:
            avg = total_study // total_students
            message += f"📊 میانگین: {format_time(avg)}\n"
        
        message += f"\n🔥 بریم بالاتر! 💪"
        
        await query.edit_message_text(message, reply_markup=get_back_button())
        return
    
    # Study controls
    elif query.data == "start_study":
        if user.get("active_session"):
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ توجه!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"قبلاً یه جلسه شروع کردی! 😊\n\n"
                f"اول باید اون رو تموم کنی.\n"
                f"روی 'پایان و ذخیره' کلیک کن. ✅",
                reply_markup=get_back_button()
            )
        else:
            now = get_iran_now()
            user["active_session"] = {
                "start_time": now.isoformat(),
                "paused_at": None,
                "paused_duration": 0
            }
            save_data(data)
            
            time_fa = format_time_hms(now)
            
            message = (
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ شروع موفق!\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎉 عالیه {username}!\n"
                f"مطالعه‌ت شروع شد.\n\n"
                f"⏰ زمان شروع: {time_fa}\n\n"
                f"موفق باشی! 📚💪✨"
            )
            await query.edit_message_text(message, reply_markup=get_back_button())
    
    elif query.data == "pause_study":
        if not user.get("active_session"):
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ خطا!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"هیچ جلسه فعالی نداری! 😕\n\n"
                f"اول باید مطالعه رو شروع کنی. ▶️",
                reply_markup=get_back_button()
            )
        elif user["active_session"].get("paused_at"):
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ توجه!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"قبلاً متوقف کردی! ⏸\n\n"
                f"برای ادامه روی 'ادامه دادن' کلیک کن.",
                reply_markup=get_back_button()
            )
        else:
            user["active_session"]["paused_at"] = get_iran_now().isoformat()
            save_data(data)
            
            current_time = calculate_active_time(user)
            message = (
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"⏸ متوقف شد\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"🤚 {username} عزیز،\n"
                f"مطالعه‌ت متوقف شد.\n\n"
                f"⏱ زمان تا الان: {format_time(current_time)}\n\n"
                f"برای ادامه:\n"
                f"'ادامه دادن' رو بزن. ▶️"
            )
            await query.edit_message_text(message, reply_markup=get_back_button())
    
    elif query.data == "resume_study":
        if not user.get("active_session"):
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ خطا!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"هیچ جلسه فعالی نداری! 😕",
                reply_markup=get_back_button()
            )
        elif not user["active_session"].get("paused_at"):
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ توجه!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"جلسه‌ت متوقف نشده! 🤔\n\n"
                f"الان داری مطالعه می‌کنی. ▶️",
                reply_markup=get_back_button()
            )
        else:
            paused_at = datetime.fromisoformat(user["active_session"]["paused_at"])
            # Make sure paused_at is timezone-aware
            if paused_at.tzinfo is None:
                paused_at = IRAN_TZ.localize(paused_at)
            
            pause_duration = (get_iran_now() - paused_at).total_seconds()
            user["active_session"]["paused_duration"] += pause_duration
            user["active_session"]["paused_at"] = None
            save_data(data)
            
            message = (
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"▶️ ادامه داد!\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎉 آفرین {username}!\n"
                f"بریم که وقت طلاست! ⏰\n\n"
                f"موفق باشی! 📚💪✨"
            )
            await query.edit_message_text(message, reply_markup=get_back_button())
    
    elif query.data == "end_study":
        if not user.get("active_session"):
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ خطا!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"هیچ جلسه فعالی نداری! 😕",
                reply_markup=get_back_button()
            )
        else:
            session_duration = calculate_active_time(user)
            
            if session_duration < 60:
                await query.edit_message_text(
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ توجه!\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"مدت جلسه خیلی کمه! ⏱\n"
                    f"(کمتر از ۱ دقیقه)\n\n"
                    f"حداقل ۱ دقیقه مطالعه کن. 📚",
                    reply_markup=get_back_button()
                )
                return
            
            data["daily_stats"][today][user_id]["total_seconds"] += session_duration
            data["daily_stats"][today][user_id]["name"] = username
            
            update_period_stats(data, user_id, username, session_duration)
            
            user["active_session"] = None
            save_data(data)
            
            total_today = data["daily_stats"][today][user_id]["total_seconds"]
            
            message = (
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎉 تموم شد!\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"👏 آفرین {username}!\n"
                f"جلسه‌ت با موفقیت ذخیره شد. ✅\n\n"
                f"⏱ این جلسه: {format_time(session_duration)}\n"
                f"📊 مجموع امروز: {format_time(total_today)}\n\n"
                f"ادامه بده! 💪🔥✨"
            )
            await query.edit_message_text(message, reply_markup=get_back_button())
    
    elif query.data == "my_stats":
        completed_time = data["daily_stats"][today][user_id]["total_seconds"]
        
        if user.get("active_session"):
            current_session_time = calculate_active_time(user)
            total_time = completed_time + current_session_time
            if user["active_session"].get("paused_at"):
                status = "⏸ متوقف شده"
                status_emoji = "⏸"
            else:
                status = "▶️ در حال مطالعه"
                status_emoji = "🔥"
        else:
            total_time = completed_time
            status = "⚪️ بدون جلسه فعال"
            status_emoji = "💤"
        
        now = get_iran_now()
        p_date = get_persian_date()
        p_date_fa = format_persian_date_display(p_date)
        
        message = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 آمار شخصی من\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 {username}\n"
            f"📅 تاریخ: {p_date_fa}\n\n"
            f"⏱ مجموع مطالعه:\n"
            f"     {format_time(total_time)}\n\n"
            f"{status_emoji} وضعیت:\n"
            f"     {status}\n\n"
        )
        
        if total_time > 0:
            message += f"🌟 آفرین! ادامه بده! 💪"
        else:
            message += f"💡 هنوز شروع نکردی!\nبزن بریم! 🚀"
        
        await query.edit_message_text(message, reply_markup=get_back_button())
    
    elif query.data == "top_students":
        if today not in data["daily_stats"] or not data["daily_stats"][today]:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 برترین‌ها\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💤 هنوز کسی شروع نکرده!\n\n"
                f"اولین نفر باش! 🚀",
                reply_markup=get_leaderboard_menu_keyboard()
            )
            return
        
        user_totals = []
        for uid, stats in data["daily_stats"][today].items():
            total = stats["total_seconds"]
            if uid in data["users"] and data["users"][uid].get("active_session"):
                total += calculate_active_time(data["users"][uid])
            if total > 0:
                user_totals.append((stats["name"], total))
        
        sorted_users = sorted(user_totals, key=lambda x: x[1], reverse=True)
        
        now = get_iran_now()
        p_date = get_persian_date()
        p_date_fa = format_persian_date_display(p_date)
        
        message = (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏆 برترین‌های امروز\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📅 {p_date_fa}\n\n"
            f"🏅 رتبه‌بندی:\n\n"
        )
        
        medals = ["🥇", "🥈", "🥉"]
        for i, (name, total) in enumerate(sorted_users[:10], 1):
            if i <= 3:
                message += f"{medals[i-1]} {name}\n"
            else:
                rank_fa = to_farsi_number(i)
                message += f"{rank_fa}. {name}\n"
            message += f"     ⏱ {format_time(total)}\n\n"
        
        await query.edit_message_text(message, reply_markup=get_leaderboard_menu_keyboard())
    
    elif query.data == "weekly_stats":
        week_key = get_persian_week_key()
        
        if "weekly_stats" not in data or week_key not in data["weekly_stats"] or not data["weekly_stats"][week_key]:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📅 آمار هفتگی\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"💤 این هفته هنوز کسی شروع نکرده!",
                reply_markup=get_leaderboard_menu_keyboard()
            )
            return
        
        sorted_users = sorted(
            data["weekly_stats"][week_key].items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        )
        
        message = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 برترین‌های هفته\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🗓 هفته {week_key}\n\n"
            f"🏅 رتبه‌بندی:\n\n"
        )
        
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, stats) in enumerate(sorted_users[:10], 1):
            if i <= 3:
                message += f"{medals[i-1]} {stats['name']}\n"
            else:
                rank_fa = to_farsi_number(i)
                message += f"{rank_fa}. {stats['name']}\n"
            message += f"     ⏱ {format_time(stats['total_seconds'])}\n\n"
        
        await query.edit_message_text(message, reply_markup=get_leaderboard_menu_keyboard())
    
    elif query.data == "monthly_stats":
        month_key = get_persian_month_key()
        
        if "monthly_stats" not in data or month_key not in data["monthly_stats"] or not data["monthly_stats"][month_key]:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📆 آمار ماهانه\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"💤 این ماه هنوز کسی شروع نکرده!",
                reply_markup=get_leaderboard_menu_keyboard()
            )
            return
        
        sorted_users = sorted(
            data["monthly_stats"][month_key].items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        )
        
        p_date = get_persian_date()
        persian_months = ["", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
                         "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
        month_name = persian_months[p_date["month"]]
        year_fa = to_farsi_number(p_date['year'])
        
        message = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📆 برترین‌های ماه\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🗓 {month_name} {year_fa}\n\n"
            f"🏅 رتبه‌بندی:\n\n"
        )
        
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, stats) in enumerate(sorted_users[:10], 1):
            if i <= 3:
                message += f"{medals[i-1]} {stats['name']}\n"
            else:
                rank_fa = to_farsi_number(i)
                message += f"{rank_fa}. {stats['name']}\n"
            message += f"     ⏱ {format_time(stats['total_seconds'])}\n\n"
        
        await query.edit_message_text(message, reply_markup=get_leaderboard_menu_keyboard())

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Send daily report at midnight"""
    data = load_data()
    yesterday_dt = get_iran_now() - timedelta(days=1)
    yesterday = yesterday_dt.strftime("%Y-%m-%d")
    
    if yesterday in data["daily_stats"] and data["daily_stats"][yesterday]:
        sorted_users = sorted(
            data["daily_stats"][yesterday].items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        )
        
        message = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"📊 گزارش روز\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📅 {yesterday}\n\n"
            f"🏆 برترین دانشجویان:\n\n"
        )
        
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, stats) in enumerate(sorted_users[:10], 1):
            if i <= 3:
                message += f"{medals[i-1]} {stats['name']}\n"
            else:
                rank_fa = to_farsi_number(i)
                message += f"{rank_fa}. {stats['name']}\n"
            message += f"     ⏱ {format_time(stats['total_seconds'])}\n\n"
        
        print(message)

async def startup_migration(application):
    """Fetch and update usernames from Telegram API on startup"""
    print("🔄 Running startup migration to fetch usernames...")
    data = load_data()
    
    needs_save = False
    updated_count = 0
    failed_count = 0
    
    # Go through all users and fetch their current Telegram info
    for user_id_str, user_data in data["users"].items():
        try:
            user_id_int = int(user_id_str)
            current_name = user_data.get("name", "")
            
            # Try to get user info from Telegram
            try:
                # Get user info using the bot's get_chat method
                chat = await application.bot.get_chat(user_id_int)
                
                # Determine the display name
                if chat.username:
                    new_name = f"@{chat.username}"
                else:
                    # Use first name as fallback
                    first_name = chat.first_name or "Unknown"
                    new_name = f"user: ({first_name})"
                
                # Update if changed
                if current_name != new_name:
                    user_data["name"] = new_name
                    needs_save = True
                    updated_count += 1
                    print(f"  ✅ Updated user {user_id_str}: {current_name} -> {new_name}")
                
            except Exception as e:
                # User not accessible (blocked bot, deleted account, etc.)
                if not current_name.startswith("@") and not current_name.startswith("user: "):
                    # Fix format for inaccessible users
                    user_data["name"] = f"user: ({current_name})"
                    needs_save = True
                    failed_count += 1
                    print(f"  ⚠️ Cannot access user {user_id_str}, kept as: {user_data['name']}")
                
        except Exception as e:
            print(f"  ❌ Error processing user {user_id_str}: {e}")
            failed_count += 1
    
    # Update all stats with the new names
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
        
        save_data(data)
        print(f"\n✅ Migration completed!")
        print(f"   📊 Updated: {updated_count} users")
        if failed_count > 0:
            print(f"   ⚠️ Inaccessible: {failed_count} users")
    else:
        print("✅ No updates needed, all usernames are current!")

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found in .env file")
        return
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Run startup migration to fetch usernames
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(startup_migration(application))
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("details", details))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.job_queue.run_repeating(
        update_details_message, 
        interval=UPDATE_INTERVAL, 
        first=UPDATE_INTERVAL
    )

    midnight_iran = time(hour=0, minute=0, tzinfo=IRAN_TZ)
    application.job_queue.run_daily(daily_report, time=midnight_iran)
    
    print("\n🤖 Bot is running...")
    print(f"📍 Group: {ALLOWED_GROUP_ID if ALLOWED_GROUP_ID != 0 else 'All'}")
    print(f"⏱ Update interval: {UPDATE_INTERVAL} seconds")
    application.run_polling()

if __name__ == "__main__":
    main()