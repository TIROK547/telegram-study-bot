import os
import json
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import ApplicationBuilder
from datetime import datetime, timedelta, time

# JSON Database file
DB_FILE = "data.json"

def load_data():
    """Load data from JSON file"""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"users": {}, "daily_stats": {}}

def save_data(data):
    """Save data to JSON file"""
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def format_time(seconds):
    """Convert seconds to hours and minutes"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours} ساعت و {minutes} دقیقه"

def get_today():
    """Get today's date as string"""
    return datetime.now().strftime("%Y-%m-%d")

def build_details_message(data):
    today = get_today()

    if today not in data["daily_stats"]:
        return "📌 امروز هنوز هیچ مطالعه‌ای ثبت نشده است."

    users = data["daily_stats"][today]

    lines = []
    active = []
    finished = []

    for uid, info in users.items():
        name = info["name"]
        total = info["total_seconds"]

        # چک کن آیا در حال مطالعه هستند
        if uid in data["users"] and data["users"][uid]["active_session"]:
            sess = data["users"][uid]["active_session"]
            start = datetime.fromisoformat(sess["start_time"])
            paused = sess["paused_at"]

            if paused:
                extra = 0
            else:
                extra = (datetime.now() - start).total_seconds() - sess["paused_duration"]

            total_now = total + max(0, int(extra))
            active.append((name, total_now))
        else:
            finished.append((name, total))

    msg = f"📊 آمار لحظه‌ای امروز ({datetime.now().strftime('%H:%M')})\n\n"

    msg += "🟢 در حال مطالعه:\n"
    if active:
        for n, t in active:
            msg += f"• {n}: {format_time(t)}\n"
    else:
        msg += "هیچ‌کس در حال مطالعه نیست.\n"

    msg += "\n🔵 کسانی که امروز مطالعه کرده‌اند:\n"
    for n, t in finished:
        msg += f"• {n}: {format_time(t)}\n"

    # Top 10
    all_users = active + finished
    top = sorted(all_users, key=lambda x: x[1], reverse=True)[:10]

    msg += "\n🏆 Top 10 امروز:\n"
    for i, (n, t) in enumerate(top, 1):
        msg += f"{i}. {n} — {format_time(t)}\n"

    return msg

async def details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = get_today()

    msg_text = build_details_message(data)

    sent = await update.message.reply_text(msg_text)

    data["details_message"][today] = {
        "chat_id": sent.chat_id,
        "message_id": sent.message_id,
        "expires": "23:59"
    }
    save_data(data)

async def update_details_message(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    today = get_today()

    if today not in data["details_message"]:
        return

    info = data["details_message"][today]
    print("run")
    now = datetime.now().strftime("%H:%M")
    if now >= "23:59":
        return  # deactivate

    chat_id = info["chat_id"]
    message_id = info["message_id"]

    new_text = build_details_message(data)

    try:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=new_text
        )
    except:
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    keyboard = [
        [InlineKeyboardButton("▶️ شروع مطالعه", callback_data="start_study")],
        [InlineKeyboardButton("⏸️ توقف موقت", callback_data="pause_study"),
         InlineKeyboardButton("▶️ ادامه", callback_data="resume_study")],
        [InlineKeyboardButton("⏹️ پایان مطالعه", callback_data="end_study")],
        [InlineKeyboardButton("📊 آمار امروز من", callback_data="my_stats"),
         InlineKeyboardButton("🏆 برترین‌ها", callback_data="top_students")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎓 به ربات ردیاب مطالعه خوش آمدید!\n\n"
        "از دکمه‌های زیر برای شروع استفاده کنید:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = str(query.from_user.id)
    username = query.from_user.first_name
    today = get_today()
    
    # Initialize user if not exists
    if user_id not in data["users"]:
        data["users"][user_id] = {
            "name": username,
            "active_session": None,
            "paused_time": 0
        }
    
    # Initialize today's stats if not exists
    if today not in data["daily_stats"]:
        data["daily_stats"][today] = {}
    
    if user_id not in data["daily_stats"][today]:
        data["daily_stats"][today][user_id] = {
            "name": username,
            "total_seconds": 0
        }
    
    user = data["users"][user_id]
    
    if query.data == "start_study":
        if user["active_session"]:
            await query.edit_message_text("⚠️ شما در حال حاضر یک جلسه مطالعه فعال دارید!")
        else:
            user["active_session"] = {
                "start_time": datetime.now().isoformat(),
                "paused_at": None,
                "paused_duration": 0
            }
            save_data(data)
            await query.edit_message_text(
                f"✅ {username} عزیز، مطالعه شما شروع شد!\n"
                f"⏰ زمان شروع: {datetime.now().strftime('%H:%M:%S')}\n\n"
                "موفق باشید! 📚"
            )
    
    elif query.data == "pause_study":
        if not user["active_session"]:
            await query.edit_message_text("⚠️ شما جلسه مطالعه فعالی ندارید!")
        elif user["active_session"]["paused_at"]:
            await query.edit_message_text("⚠️ مطالعه شما از قبل متوقف شده است!")
        else:
            user["active_session"]["paused_at"] = datetime.now().isoformat()
            save_data(data)
            await query.edit_message_text(
                f"⏸️ {username} عزیز، مطالعه شما موقتاً متوقف شد.\n"
                "برای ادامه از دکمه 'ادامه' استفاده کنید."
            )
    
    elif query.data == "resume_study":
        if not user["active_session"]:
            await query.edit_message_text("⚠️ شما جلسه مطالعه فعالی ندارید!")
        elif not user["active_session"]["paused_at"]:
            await query.edit_message_text("⚠️ مطالعه شما متوقف نشده است!")
        else:
            paused_at = datetime.fromisoformat(user["active_session"]["paused_at"])
            pause_duration = (datetime.now() - paused_at).total_seconds()
            user["active_session"]["paused_duration"] += pause_duration
            user["active_session"]["paused_at"] = None
            save_data(data)
            await query.edit_message_text(
                f"▶️ {username} عزیز، مطالعه شما از سر گرفته شد!\n"
                "موفق باشید! 📚"
            )
    
    elif query.data == "end_study":
        if not user["active_session"]:
            await query.edit_message_text("⚠️ شما جلسه مطالعه فعالی ندارید!")
        else:
            start_time = datetime.fromisoformat(user["active_session"]["start_time"])
            
            # Calculate total study time
            total_duration = (datetime.now() - start_time).total_seconds()
            total_duration -= user["active_session"]["paused_duration"]
            
            # If currently paused, don't count paused time
            if user["active_session"]["paused_at"]:
                paused_at = datetime.fromisoformat(user["active_session"]["paused_at"])
                total_duration -= (datetime.now() - paused_at).total_seconds()
            
            total_duration = max(0, int(total_duration))
            
            # Update daily stats
            data["daily_stats"][today][user_id]["total_seconds"] += total_duration
            data["daily_stats"][today][user_id]["name"] = username
            
            # Clear active session
            user["active_session"] = None
            save_data(data)
            
            # Get total time for today
            total_today = data["daily_stats"][today][user_id]["total_seconds"]
            
            await query.edit_message_text(
                f"🎉 {username} عزیز، مطالعه شما به پایان رسید!\n\n"
                f"⏱️ مدت این جلسه: {format_time(total_duration)}\n"
                f"📊 مجموع مطالعه امروز: {format_time(total_today)}\n\n"
                "آفرین! ادامه بده! 💪"
            )
    
    elif query.data == "my_stats":
        if user_id in data["daily_stats"].get(today, {}):
            total_seconds = data["daily_stats"][today][user_id]["total_seconds"]
            await query.edit_message_text(
                f"📊 آمار امروز {username}:\n\n"
                f"⏱️ مجموع مطالعه: {format_time(total_seconds)}\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y/%m/%d')}"
            )
        else:
            await query.edit_message_text(
                f"📊 {username} عزیز، شما امروز هنوز مطالعه‌ای ثبت نکرده‌اید!"
            )
    
    elif query.data == "top_students":
        if today in data["daily_stats"] and data["daily_stats"][today]:
            # Sort users by study time
            sorted_users = sorted(
                data["daily_stats"][today].items(),
                key=lambda x: x[1]["total_seconds"],
                reverse=True
            )
            
            message = f"🏆 برترین دانشجویان امروز ({datetime.now().strftime('%Y/%m/%d')}):\n\n"
            
            medals = ["🥇", "🥈", "🥉"]
            for i, (uid, stats) in enumerate(sorted_users[:10], 1):
                medal = medals[i-1] if i <= 3 else f"{i}."
                message += f"{medal} {stats['name']}: {format_time(stats['total_seconds'])}\n"
            
            await query.edit_message_text(message)
        else:
            await query.edit_message_text(
                "📊 هنوز کسی امروز مطالعه‌ای ثبت نکرده است!"
            )

async def daily_report(context: ContextTypes.DEFAULT_TYPE):
    """Send daily report at midnight"""
    data = load_data()
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if yesterday in data["daily_stats"] and data["daily_stats"][yesterday]:
        sorted_users = sorted(
            data["daily_stats"][yesterday].items(),
            key=lambda x: x[1]["total_seconds"],
            reverse=True
        )
        
        message = f"📊 گزارش روز {yesterday}:\n\n"
        message += "🏆 برترین دانشجویان:\n\n"
        
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, stats) in enumerate(sorted_users[:10], 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            message += f"{medal} {stats['name']}: {format_time(stats['total_seconds'])}\n"
        
        # Send to all groups/users (you need to store chat IDs)
        # For now, this would need to be triggered manually or you store chat IDs
        print(message)  # Replace with actual sending logic

def main():
    """Start the bot"""
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token from @BotFather
    TOKEN = "8083782221:AAGy7C6X8tc_ddMbnuQLNn6NByU9h65ph7k"
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("details", details))
    application.job_queue.run_repeating(update_details_message, interval=5, first=10)

    # Schedule daily report at midnight (optional - requires additional setup)
    job_queue = application.job_queue
    job_queue.run_daily(daily_report, time=time(hour=0, minute=0))

    
    print("🤖 Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()