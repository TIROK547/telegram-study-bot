import os
import asyncio
from datetime import datetime, timedelta, time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters, ConversationHandler
from telegram.ext import ApplicationBuilder
import pytz
import jdatetime
from dotenv import load_dotenv
from functools import lru_cache

# Import database functions
import database as db

# Load environment variables
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ALLOWED_GROUP_ID = int(os.getenv("ALLOWED_GROUP_ID", "0"))
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "30"))

# Timezone
IRAN_TZ = pytz.timezone('Asia/Tehran')

# Profile setup states
FIELD_SELECTION, GRADE_INPUT = range(2)

# Field options
FIELD_OPTIONS = {
    "daneshgah": "دانشگاه",
    "riazi": "ریاضی",
    "ensani": "انسانی",
    "tajrobi": "تجربی",
    "honarestan": "هنرستان"
}

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

async def check_group_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is a member of the allowed group"""
    if ALLOWED_GROUP_ID == 0:
        return True

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # If message is in the allowed group, allow it
    if chat_id == ALLOWED_GROUP_ID:
        return True

    # If it's a private chat, check if user is a member of the allowed group
    if chat_id == user_id:  # Private chat
        try:
            member = await context.bot.get_chat_member(ALLOWED_GROUP_ID, user_id)
            # Allow if user is member, administrator, or creator
            return member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            print(f"Error checking group membership: {e}")
            return False

    return False

async def access_denied(update: Update):
    """Send access denied message"""
    message = (
        "⛔️ دسترسی محدود شده است.\n\n"
        "برای استفاده از این ربات، ابتدا باید عضو گروه مجاز باشید.\n"
        "بعد از عضویت در گروه، می‌توانید از ربات در پیام خصوصی استفاده کنید."
    )
    if update.message:
        await update.message.reply_text(message)
    elif update.callback_query:
        await update.callback_query.answer(message, show_alert=True)

def reset_expired_sessions():
    """Reset sessions that are older than today - optimized"""
    today = get_today()
    all_users = db.get_all_users()
    expired_users = []

    for user_id, user_data in all_users.items():
        session = db.get_active_session(user_id)
        if session:
            session_start = datetime.fromisoformat(session["start_time"])
            # Make sure session_start is timezone-aware
            if session_start.tzinfo is None:
                session_start = IRAN_TZ.localize(session_start)

            session_date = session_start.astimezone(IRAN_TZ).strftime("%Y-%m-%d")

            if session_date != today:
                expired_users.append(user_id)

    for user_id in expired_users:
        db.end_session(user_id)

def calculate_active_time(session):
    """Calculate current active study time for a session"""
    if not session:
        return 0

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

def get_main_menu_keyboard(user_id):
    """Get main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("▶️ شروع مطالعه", callback_data=f"start_study:{user_id}")],
        [
            InlineKeyboardButton("⏸ توقف موقت", callback_data=f"pause_study:{user_id}"),
            InlineKeyboardButton("▶️ ادامه دادن", callback_data=f"resume_study:{user_id}")
        ],
        [InlineKeyboardButton("⏹ پایان و ذخیره", callback_data=f"end_study:{user_id}")],
        [
            InlineKeyboardButton("📊 آمار من", callback_data=f"my_stats:{user_id}"),
            InlineKeyboardButton("📈 آمار گروه", callback_data=f"group_stats:{user_id}")
        ],
        [
            InlineKeyboardButton("🏆 رتبه‌بندی‌ها", callback_data=f"leaderboard_menu:{user_id}"),
            InlineKeyboardButton("❓ راهنما", callback_data=f"help:{user_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_leaderboard_menu_keyboard(user_id):
    """Get leaderboard menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("🏆 امروز", callback_data=f"top_students:{user_id}")],
        [InlineKeyboardButton("📅 هفتگی", callback_data=f"weekly_stats:{user_id}")],
        [InlineKeyboardButton("📆 ماهانه", callback_data=f"monthly_stats:{user_id}")],
        [InlineKeyboardButton("🔙 بازگشت به منو", callback_data=f"back_main:{user_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button(user_id):
    """Get back button keyboard"""
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منو", callback_data=f"back_main:{user_id}")]]
    return InlineKeyboardMarkup(keyboard)

def build_details_message():
    """Build the live details message - RTL-friendly UI"""
    today = get_today()
    reset_expired_sessions()

    now = get_iran_now()
    time_fa = format_time_hms(now)
    
    users_stats = db.get_daily_stats(today)
    if not users_stats:
        return (
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📊 آمار زنده امروز\n"
            f"🕐 ساعت: {time_fa}\n"
            f"━━━━━━━━━━━━━━━━━━━\n\n"
            f"💤 هنوز کسی امروز شروع نکرده!\n\n"
            f"🎯 اولین نفر باش و شروع کن! 💪"
        )

    all_users = db.get_all_users()
    active = []
    finished = []

    for uid, info in users_stats.items():
        name = info["name"]
        completed_time = info["total_seconds"]

        user_data = all_users.get(uid, {})
        session = db.get_active_session(uid)
        if session:
            current_session_time = calculate_active_time(session)
            total_time = completed_time + current_session_time
            is_paused = session.get("paused_at") is not None
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
    if not await check_group_access(update, context):
        await access_denied(update)
        return

    today = get_today()
    users_stats = db.get_daily_stats(today)

    if not users_stats:
        await update.message.reply_text("📊 امروز هنوز هیچ مطالعه‌ای ثبت نشده است.")
        return

    user_totals = []

    for uid, stats in users_stats.items():
        total = stats["total_seconds"]
        session = db.get_active_session(uid)
        if session:
            total += calculate_active_time(session)
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
    if not await check_group_access(update, context):
        await access_denied(update)
        return

    today = get_today()
    msg_text = build_details_message()
    sent = await update.message.reply_text(msg_text)

    db.save_details_message(today, sent.chat_id, sent.message_id)

async def update_details_message(context: ContextTypes.DEFAULT_TYPE):
    """Periodically update the details message"""
    try:
        today = get_today()
        info = db.get_details_message(today)

        if not info:
            return

        chat_id = info["chat_id"]
        message_id = info["message_id"]

        new_text = build_details_message()

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=new_text
        )
    except Exception as e:
        # Message was deleted or not found, or network error - just continue
        print(f"⚠️ Warning updating details message: {e}")
        pass

async def start_profile_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start profile setup process"""
    message = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 تکمیل پروفایل\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"سلام! 👋\n\n"
        f"برای استفاده از ربات، لطفاً اول\n"
        f"پروفایلت رو کامل کن.\n\n"
        f"🎓 رشته یا مقطع تحصیلی خودت رو انتخاب کن:"
    )

    keyboard = [
        [InlineKeyboardButton("🎓 دانشگاه", callback_data="field:daneshgah")],
        [InlineKeyboardButton("📐 ریاضی", callback_data="field:riazi")],
        [InlineKeyboardButton("📚 انسانی", callback_data="field:ensani")],
        [InlineKeyboardButton("🔬 تجربی", callback_data="field:tajrobi")],
        [InlineKeyboardButton("🎨 هنرستان", callback_data="field:honarestan")]
    ]

    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    return FIELD_SELECTION


async def handle_field_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle field selection"""
    query = update.callback_query
    await query.answer()

    # Extract field from callback data
    field = query.data.split(":")[1]
    context.user_data['field'] = field

    # Determine grade range based on field
    if field == "daneshgah":
        grade_message = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📚 ترم تحصیلی\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ رشته انتخاب شد: دانشگاه\n\n"
            f"لطفاً شماره ترم خودت رو وارد کن\n"
            f"(عدد بین ۱ تا ۲۲):\n\n"
            f"مثال: 5"
        )
        context.user_data['min_grade'] = 1
        context.user_data['max_grade'] = 22
    elif field == "honarestan":
        grade_message = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🎨 رشته هنرستان\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ مقطع انتخاب شد: هنرستان\n\n"
            f"لطفاً رشته دقیق خودت رو بنویس:\n\n"
            f"مثال: گرافیک"
        )
        context.user_data['honarestan_custom'] = True
    else:
        field_name = FIELD_OPTIONS[field]
        grade_message = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📖 پایه تحصیلی\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ رشته انتخاب شد: {field_name}\n\n"
            f"لطفاً پایه تحصیلی خودت رو وارد کن\n"
            f"(عدد بین ۶ تا ۱۲):\n\n"
            f"مثال: 11"
        )
        context.user_data['min_grade'] = 6
        context.user_data['max_grade'] = 12

    await query.edit_message_text(grade_message)
    return GRADE_INPUT


async def handle_grade_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle grade/term input"""
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()
    field = context.user_data.get('field')

    # Handle honarestan custom field
    if context.user_data.get('honarestan_custom'):
        # Save custom field for honarestan
        custom_field = f"honarestan:{text}"
        db.update_user_profile(user_id, custom_field, 0)  # 0 for honarestan as grade is the field name

        message = (
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ پروفایل تکمیل شد!\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎉 عالی!\n\n"
            f"🎓 رشته: هنرستان - {text}\n\n"
            f"حالا می‌تونی از ربات استفاده کنی!\n\n"
            f"برای شروع: /start"
        )
        await update.message.reply_text(message)
        return ConversationHandler.END

    # Validate grade is a number
    try:
        grade = int(text)
    except ValueError:
        await update.message.reply_text(
            f"⚠️ لطفاً فقط عدد وارد کن!\n\nمثال: 11"
        )
        return GRADE_INPUT

    # Validate grade range
    min_grade = context.user_data.get('min_grade', 1)
    max_grade = context.user_data.get('max_grade', 22)

    if grade < min_grade or grade > max_grade:
        min_fa = to_farsi_number(min_grade)
        max_fa = to_farsi_number(max_grade)
        await update.message.reply_text(
            f"⚠️ عدد باید بین {min_fa} تا {max_fa} باشه!\n\nدوباره امتحان کن:"
        )
        return GRADE_INPUT

    # Save profile
    db.update_user_profile(user_id, field, grade)

    field_name = FIELD_OPTIONS[field]
    grade_fa = to_farsi_number(grade)

    if field == "daneshgah":
        grade_label = f"ترم {grade_fa}"
    else:
        grade_label = f"پایه {grade_fa}"

    message = (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ پروفایل تکمیل شد!\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎉 عالی!\n\n"
        f"🎓 رشته: {field_name}\n"
        f"📚 {grade_label}\n\n"
        f"حالا می‌تونی از ربات استفاده کنی!\n\n"
        f"برای شروع: /start"
    )

    await update.message.reply_text(message)
    return ConversationHandler.END


async def cancel_profile_setup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel profile setup"""
    await update.message.reply_text(
        f"❌ تکمیل پروفایل لغو شد.\n\n"
        f"برای شروع دوباره: /start"
    )
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    if not await check_group_access(update, context):
        await access_denied(update)
        return

    user_id = str(update.effective_user.id)
    username = f"@{update.effective_user.username}" if update.effective_user.username else f"user: ({update.effective_user.first_name})"

    # Create or update user
    db.create_or_update_user(user_id, username)

    # Check if profile is completed
    if not db.is_profile_completed(user_id):
        # Start profile setup
        return await start_profile_setup(update, context)

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

    await update.message.reply_text(message, reply_markup=get_main_menu_keyboard(update.effective_user.id))

def update_period_stats(user_id, username, duration):
    """Update weekly and monthly statistics"""
    week_key = get_persian_week_key()
    month_key = get_persian_month_key()

    # Update weekly stats
    db.update_weekly_stats(user_id, week_key, username, duration)

    # Update monthly stats
    db.update_monthly_stats(user_id, month_key, username, duration)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    if not await check_group_access(update, context):
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

    # Ensure user exists in database
    db.create_or_update_user(user_id, username)

    # Ensure daily stat exists
    db.ensure_daily_stat_exists(user_id, today, username)

    # Get active session if any
    session = db.get_active_session(user_id)

    # Navigation
    if action == "back_main":
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
        await query.edit_message_text(message, reply_markup=get_main_menu_keyboard(query.from_user.id))
        return

    elif action == "leaderboard_menu":
        message = (
            f"━━━━━━━━━━━━━━━━━\n"
            f"🏆 رتبه‌بندی‌ها\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"کدوم رتبه‌بندی رو می‌خوای ببینی؟ 👀"
        )
        await query.edit_message_text(message, reply_markup=get_leaderboard_menu_keyboard(query.from_user.id))
        return

    elif action == "help":
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
        await query.edit_message_text(message, reply_markup=get_back_button(query.from_user.id))
        return

    elif action == "group_stats":
        users_stats = db.get_daily_stats(today)
        if not users_stats:
            message = (
                f"━━━━━━━━━━━━━━━\n"
                f"📈 آمار گروه\n"
                f"━━━━━━━━━━━━━━━\n\n"
                f"💤 امروز هنوز کسی شروع نکرده!"
            )
            await query.edit_message_text(message, reply_markup=get_back_button(query.from_user.id))
            return

        user_totals = []

        for uid, stats in users_stats.items():
            total = stats["total_seconds"]
            user_session = db.get_active_session(uid)
            if user_session:
                total += calculate_active_time(user_session)
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

        await query.edit_message_text(message, reply_markup=get_back_button(query.from_user.id))
        return

    # Study controls
    elif action == "start_study":
        if session:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ توجه!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"قبلاً یه جلسه شروع کردی! 😊\n\n"
                f"اول باید اون رو تموم کنی.\n"
                f"روی 'پایان و ذخیره' کلیک کن. ✅",
                reply_markup=get_back_button(query.from_user.id)
            )
        else:
            now = get_iran_now()
            db.start_session(user_id, now.isoformat())
            
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
            await query.edit_message_text(message, reply_markup=get_back_button(query.from_user.id))

    elif action == "pause_study":
        if not session:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ خطا!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"هیچ جلسه فعالی نداری! 😕\n\n"
                f"اول باید مطالعه رو شروع کنی. ▶️",
                reply_markup=get_back_button(query.from_user.id)
            )
        elif session.get("paused_at"):
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ توجه!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"قبلاً متوقف کردی! ⏸\n\n"
                f"برای ادامه روی 'ادامه دادن' کلیک کن.",
                reply_markup=get_back_button(query.from_user.id)
            )
        else:
            now = get_iran_now()
            db.pause_session(user_id, now.isoformat())

            # Refresh session to get updated data
            session = db.get_active_session(user_id)
            current_time = calculate_active_time(session)
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
            await query.edit_message_text(message, reply_markup=get_back_button(query.from_user.id))

    elif action == "resume_study":
        if not session:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ خطا!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"هیچ جلسه فعالی نداری! 😕",
                reply_markup=get_back_button(query.from_user.id)
            )
        elif not session.get("paused_at"):
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ توجه!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"جلسه‌ت متوقف نشده! 🤔\n\n"
                f"الان داری مطالعه می‌کنی. ▶️",
                reply_markup=get_back_button(query.from_user.id)
            )
        else:
            paused_at = datetime.fromisoformat(session["paused_at"])
            # Make sure paused_at is timezone-aware
            if paused_at.tzinfo is None:
                paused_at = IRAN_TZ.localize(paused_at)

            pause_duration = (get_iran_now() - paused_at).total_seconds()
            db.resume_session(user_id, pause_duration)
            
            message = (
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"▶️ ادامه داد!\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎉 آفرین {username}!\n"
                f"بریم که وقت طلاست! ⏰\n\n"
                f"موفق باشی! 📚💪✨"
            )
            await query.edit_message_text(message, reply_markup=get_back_button(query.from_user.id))

    elif action == "end_study":
        if not session:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ خطا!\n"
                f"━━━━━━━━━━━━━━━━━\n\n"
                f"هیچ جلسه فعالی نداری! 😕",
                reply_markup=get_back_button(query.from_user.id)
            )
        else:
            session_duration = calculate_active_time(session)

            if session_duration < 60:
                await query.edit_message_text(
                    f"━━━━━━━━━━━━━━━━━\n"
                    f"⚠️ توجه!\n"
                    f"━━━━━━━━━━━━━━━━━\n\n"
                    f"مدت جلسه خیلی کمه! ⏱\n"
                    f"(کمتر از ۱ دقیقه)\n\n"
                    f"حداقل ۱ دقیقه مطالعه کن. 📚",
                    reply_markup=get_back_button(query.from_user.id)
                )
                return

            # Update daily stats
            db.update_daily_stats(user_id, today, username, session_duration)

            # Update period stats (weekly/monthly)
            update_period_stats(user_id, username, session_duration)

            # End the session
            db.end_session(user_id)

            # Get updated total for today
            daily_stats = db.get_daily_stats(today)
            total_today = daily_stats.get(user_id, {}).get("total_seconds", 0)
            
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
            await query.edit_message_text(message, reply_markup=get_back_button(query.from_user.id))

    elif action == "my_stats":
        # Get daily stats
        daily_stats = db.get_daily_stats(today)
        completed_time = daily_stats.get(user_id, {}).get("total_seconds", 0)

        if session:
            current_session_time = calculate_active_time(session)
            total_time = completed_time + current_session_time
            if session.get("paused_at"):
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
        
        await query.edit_message_text(message, reply_markup=get_back_button(query.from_user.id))

    elif action == "top_students":
        users_stats = db.get_daily_stats(today)
        if not users_stats:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🏆 برترین‌ها\n"
                f"━━━━━━━━━━━━━━━━━━━━\n\n"
                f"💤 هنوز کسی شروع نکرده!\n\n"
                f"اولین نفر باش! 🚀",
                reply_markup=get_leaderboard_menu_keyboard(query.from_user.id)
            )
            return

        user_totals = []
        for uid, stats in users_stats.items():
            total = stats["total_seconds"]
            user_session = db.get_active_session(uid)
            if user_session:
                total += calculate_active_time(user_session)
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
        
        await query.edit_message_text(message, reply_markup=get_leaderboard_menu_keyboard(query.from_user.id))

    elif action == "weekly_stats":
        week_key = get_persian_week_key()
        week_stats = db.get_weekly_stats(week_key)

        if not week_stats:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📅 آمار هفتگی\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"💤 این هفته هنوز کسی شروع نکرده!",
                reply_markup=get_leaderboard_menu_keyboard(query.from_user.id)
            )
            return

        sorted_users = sorted(
            week_stats.items(),
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
        
        await query.edit_message_text(message, reply_markup=get_leaderboard_menu_keyboard(query.from_user.id))

    elif action == "monthly_stats":
        month_key = get_persian_month_key()
        month_stats = db.get_monthly_stats(month_key)

        if not month_stats:
            await query.edit_message_text(
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📆 آمار ماهانه\n"
                f"━━━━━━━━━━━━━━━━━━━\n\n"
                f"💤 این ماه هنوز کسی شروع نکرده!",
                reply_markup=get_leaderboard_menu_keyboard(query.from_user.id)
            )
            return

        sorted_users = sorted(
            month_stats.items(),
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
        
        await query.edit_message_text(message, reply_markup=get_leaderboard_menu_keyboard(query.from_user.id))

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Send daily report at midnight"""
    yesterday_dt = get_iran_now() - timedelta(days=1)
    yesterday = yesterday_dt.strftime("%Y-%m-%d")

    daily_stats = db.get_daily_stats(yesterday)

    if daily_stats:
        sorted_users = sorted(
            daily_stats.items(),
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
    all_users = db.get_all_users()
    
    needs_save = False
    updated_count = 0
    failed_count = 0
    
    # Go through all users and fetch their current Telegram info
    for user_id_str, user_data in all_users.items():
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
                    db.create_or_update_user(user_id_str, new_name)
                    needs_save = True
                    updated_count += 1
                    print(f"  ✅ Updated user {user_id_str}: {current_name} -> {new_name}")
                
            except Exception as e:
                # User not accessible (blocked bot, deleted account, etc.)
                if not current_name.startswith("@") and not current_name.startswith("user: "):
                    # Fix format for inaccessible users
                    new_name = f"user: ({current_name})"
                    db.create_or_update_user(user_id_str, new_name)
                    needs_save = True
                    failed_count += 1
                    print(f"  ⚠️ Cannot access user {user_id_str}, kept as: {user_data['name']}")
                
        except Exception as e:
            print(f"  ❌ Error processing user {user_id_str}: {e}")
            failed_count += 1
    
    # Print migration results
    if needs_save:
        print(f"\n✅ Migration completed!")
        print(f"   📊 Updated: {updated_count} users")
        if failed_count > 0:
            print(f"   ⚠️ Inaccessible: {failed_count} users")
    else:
        print("✅ No updates needed, all usernames are current!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors to prevent bot from stopping"""
    print(f"❌ Error occurred: {context.error}")
    # Don't let errors stop the bot
    return

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found in .env file")
        return

    # Initialize database
    print("📊 Initializing database...")
    db.init_database()

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .pool_timeout(30.0)
        .build()
    )

    # Skip startup migration - usernames will be updated as users interact with bot
    # Note: startup_migration can be manually run if needed to refresh all usernames

    # Add error handler first
    application.add_error_handler(error_handler)

    # Profile setup conversation handler
    profile_conv_handler = ConversationHandler(
        entry_points=[],  # Entry is handled by /start command
        states={
            FIELD_SELECTION: [CallbackQueryHandler(handle_field_selection, pattern="^field:")],
            GRADE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_grade_input)]
        },
        fallbacks=[CommandHandler("cancel", cancel_profile_setup)],
        allow_reentry=True
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(profile_conv_handler)
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

    # Run with robust polling settings
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        close_loop=False
    )

if __name__ == "__main__":
    main()