# 🎓 Study Bot - ربات ردیاب مطالعه

A Telegram bot for tracking study sessions in groups with Persian language support. Track your study time, compete with friends, and view detailed statistics!

## ✨ Features

- 📊 **Study Time Tracking**: Start, pause, resume, and end study sessions
- 🏆 **Leaderboards**: Daily, weekly, and monthly rankings
- 📈 **Live Updates**: Real-time study statistics that update automatically
- 👤 **Personal Stats**: View your individual study progress
- 📅 **Persian Calendar**: Full Jalali (Shamsi) calendar support
- 🔒 **User-Specific Controls**: Each user can only interact with their own commands
- 🌐 **Group Support**: Perfect for study groups and classes
- 💾 **Persistent Data**: All data stored in JSON format

## 📋 Requirements

- Python 3.8 or higher
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- A Telegram group to use the bot in

## 🚀 Installation

### 1. Clone or Download the Repository

```bash
cd /path/to/study-bot
```

### 2. Create Virtual Environment (Optional but Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# OR
.venv\Scripts\activate  # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Bot

Create a `.env` file in the project root:

```bash
cp .env.example .env  # If example exists
# OR create manually:
nano .env
```

Add the following configuration:

```env
BOT_TOKEN=your_bot_token_here
ALLOWED_GROUP_ID=your_group_id_here
UPDATE_INTERVAL=30
```

**Configuration Details:**
- `BOT_TOKEN`: Get this from [@BotFather](https://t.me/BotFather)
- `ALLOWED_GROUP_ID`: Your Telegram group ID (use 0 to allow all groups)
- `UPDATE_INTERVAL`: Seconds between live statistics updates (default: 30)

**Finding Your Group ID:**
1. Add the bot to your group
2. Send any message in the group
3. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
4. Look for `"chat":{"id":-1001234567890` - that's your group ID

## 🎮 Usage

### Running the Bot

#### Option 1: Simple Run
```bash
python3 bot.py
```

#### Option 2: Auto-Restart (Recommended)
The bot includes an auto-restart script that will automatically restart the bot if it stops:

```bash
./start.sh
```

This script:
- ✅ Runs in an infinite loop
- ✅ Automatically restarts the bot if it crashes
- ✅ Shows restart count and timestamps
- ✅ Waits 5 seconds between restarts
- ✅ Can only be stopped with Ctrl+C

### Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show main menu with all options |
| `/details` | Display live study statistics (auto-updates) |
| `/stats` | Show complete daily statistics report |

### Button Controls

When you use `/start`, you'll get an interactive menu:

- **▶️ شروع مطالعه** - Start a new study session
- **⏸ توقف موقت** - Pause your current session
- **▶️ ادامه دادن** - Resume after a pause
- **⏹ پایان و ذخیره** - End and save your session
- **📊 آمار من** - View your personal statistics
- **📈 آمار گروه** - View group statistics
- **🏆 رتبه‌بندی‌ها** - Access leaderboard menu
- **❓ راهنما** - Show help and instructions

### Leaderboard Options

- **🏆 امروز** - Today's top students
- **📅 هفتگی** - Weekly leaderboard
- **📆 ماهانه** - Monthly leaderboard

## 🔐 Security Features

- Each user can only interact with their own `/start` menu buttons
- If someone tries to use another person's buttons, they'll see an access denied message
- Group-specific access control (optional)
- No authentication required - just add users to your group!

## 📁 Project Structure

```
study-bot/
├── bot.py              # Main bot code (SQLite version)
├── database.py         # Database layer
├── start.sh           # Auto-restart script
├── requirements.txt    # Python dependencies
├── .env               # Configuration file
├── .env.example       # Configuration template
│
├── data/              # Data directory
│   └── study_bot.db   # SQLite database
│
├── backups/           # Backup files
├── scripts/           # Utility scripts
├── docs/              # Documentation
└── README.md          # This file
```

📖 See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed structure.

## 🔧 Running as a Service (Optional)

To run the bot permanently on a server, you can create a systemd service:

1. Create service file:
```bash
sudo nano /etc/systemd/system/study-bot.service
```

2. Add this configuration:
```ini
[Unit]
Description=Study Bot Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/study-bot
ExecStart=/path/to/study-bot/start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable study-bot
sudo systemctl start study-bot
sudo systemctl status study-bot
```

## 🐛 Troubleshooting

### Bot Stops Randomly
- ✅ **Fixed!** The bot now includes:
  - Error handlers to catch and log errors
  - Automatic connection retry on network issues
  - Robust timeout configurations
  - Use `./start.sh` for automatic restarts

### Bot Doesn't Respond
- Check if bot is running: `ps aux | grep bot.py`
- Verify bot token in `.env` file
- Ensure bot is admin in the group
- Check console for error messages

### Permission Errors
- Make sure `start.sh` is executable: `chmod +x start.sh`
- Check file permissions: `ls -l`

### Database Issues
- The `data.json` file is created automatically
- Backup regularly: `cp data.json data.json.backup`
- If corrupted, delete it (bot will create new one)

## 📊 Data Storage

All data is stored in **SQLite database** (`study_bot.db`) with the following structure:
- **users**: User information and active sessions
- **daily_stats**: Daily study time per user
- **weekly_stats**: Weekly statistics
- **monthly_stats**: Monthly statistics
- **details_messages**: Live message tracking

**Benefits of SQLite:**
- ✅ No data corruption
- ✅ ACID transactions (atomic, consistent, isolated, durable)
- ✅ Better performance
- ✅ Concurrent access support
- ✅ Easy backup (just copy study_bot.db)

**Backup your data regularly!**
```bash
cp data/study_bot.db backups/study_bot_$(date +%Y%m%d).db
```

## 🌟 Features in Detail

### Session Management
- Minimum session time: 1 minute
- Automatic session expiration at midnight
- Pause and resume functionality
- Real-time elapsed time calculation

### Statistics
- Live updating group dashboard
- Personal progress tracking
- Comprehensive ranking systems
- Persian calendar integration
- Average study time calculations

### Auto-Update System
- Details message updates every 30 seconds (configurable)
- Daily reports at midnight (Iran timezone)
- Automatic username synchronization

## 🤝 Contributing

Feel free to fork, modify, and improve this bot!

## 📝 License

This project is open source and available for personal and educational use.

## 🙏 Support

If you encounter issues:
1. Check the troubleshooting section
2. Review console error messages
3. Ensure all dependencies are installed
4. Verify your `.env` configuration

---

**Made with ❤️ for students who want to track their study time and compete with friends!**

🎯 Good luck with your studies! 📚✨
