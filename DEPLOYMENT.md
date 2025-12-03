# 🚀 Server Deployment Guide

Complete guide for deploying the Study Bot on a production server.

## 📋 Prerequisites

Before running `start.sh`, ensure you have:

### 1. System Requirements
- **OS**: Linux (Ubuntu 20.04+ / Debian 10+ / CentOS 8+)
- **Python**: 3.8 or higher
- **Memory**: Minimum 512MB RAM
- **Disk**: At least 100MB free space
- **Network**: Stable internet connection

### 2. Required Software

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
sudo apt install python3 python3-pip python3-venv -y

# Install git (if not installed)
sudo apt install git -y
```

### 3. Check Python Version

```bash
python3 --version
# Should be 3.8 or higher
```

## 📥 Installation Steps

### Step 1: Clone the Repository

```bash
# Navigate to your preferred directory
cd /home/your_username

# Clone the repository
git clone <your-repo-url> study-bot

# Navigate to project directory
cd study-bot
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Your prompt should now show (.venv)
```

### Step 3: Install Dependencies

```bash
# Ensure pip is up to date
pip install --upgrade pip

# Install required packages
pip install -r requirements.txt
```

**Dependencies that will be installed:**
- `python-telegram-bot==22.5` - Telegram Bot API
- `python-dotenv==1.2.1` - Environment variable management
- `pytz==2025.2` - Timezone support
- `jdatetime==5.2.0` - Persian/Jalali calendar
- And other required packages

### Step 4: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

**Required configuration in `.env`:**

```env
# Get your bot token from @BotFather on Telegram
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Your Telegram group ID (or 0 for all groups)
ALLOWED_GROUP_ID=-1001234567890

# Update interval in seconds (default: 30)
UPDATE_INTERVAL=30
```

**How to get these values:**

1. **BOT_TOKEN**:
   - Open Telegram and search for [@BotFather](https://t.me/BotFather)
   - Send `/newbot` and follow instructions
   - Copy the token provided

2. **ALLOWED_GROUP_ID**:
   - Add your bot to your Telegram group
   - Make the bot an admin in the group
   - Send any message in the group
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for `"chat":{"id":-1001234567890}` - that's your group ID
   - Or set to `0` to allow all groups

3. **UPDATE_INTERVAL**:
   - How often (in seconds) to update live statistics
   - Default: 30 seconds
   - Recommended: 30-60 seconds

### Step 5: Create Data Directory

```bash
# Create data directory for database
mkdir -p data

# Create backups directory (optional but recommended)
mkdir -p backups
```

### Step 6: Initialize Database

```bash
# Initialize the database
python3 database.py
```

**Expected output:**
```
✅ Database initialized successfully
Database setup complete!
```

### Step 7: Make Start Script Executable

```bash
# Make start.sh executable
chmod +x start.sh
```

### Step 8: Test the Bot

```bash
# Test run (press Ctrl+C to stop)
python3 bot.py
```

**Expected output:**
```
📊 Initializing database...
✅ Database initialized successfully

🤖 Bot is running...
📍 Group: -1001234567890
⏱ Update interval: 30 seconds
```

If you see this, the bot is working correctly! Press `Ctrl+C` to stop.

## 🏃 Running the Bot

### Option 1: Manual Run (for testing)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run bot
python3 bot.py
```

### Option 2: Auto-Restart Script (recommended)

```bash
# Activate virtual environment
source .venv/bin/activate

# Run with auto-restart
./start.sh
```

The `start.sh` script will:
- ✅ Automatically restart the bot if it crashes
- ✅ Show restart count and timestamps
- ✅ Wait 5 seconds between restarts
- ✅ Keep running until you press `Ctrl+C`

### Option 3: Run as Background Process

```bash
# Activate virtual environment
source .venv/bin/activate

# Run in background using nohup
nohup ./start.sh > bot.log 2>&1 &

# Check if running
ps aux | grep bot.py

# View logs
tail -f bot.log

# Stop the bot
pkill -f bot.py
```

## 🔧 Running as System Service (Recommended for Production)

For permanent deployment, set up a systemd service:

### Step 1: Create Service File

```bash
sudo nano /etc/systemd/system/study-bot.service
```

### Step 2: Add Service Configuration

```ini
[Unit]
Description=Study Bot - Telegram Study Time Tracker
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/study-bot
ExecStart=/home/your_username/study-bot/.venv/bin/python3 /home/your_username/study-bot/bot.py
Restart=always
RestartSec=10

# Environment
Environment="PATH=/home/your_username/study-bot/.venv/bin:/usr/bin"

# Logging
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Replace `your_username` with your actual username!**

### Step 3: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable study-bot

# Start the service
sudo systemctl start study-bot

# Check status
sudo systemctl status study-bot
```

### Step 4: Manage the Service

```bash
# Start the bot
sudo systemctl start study-bot

# Stop the bot
sudo systemctl stop study-bot

# Restart the bot
sudo systemctl restart study-bot

# Check status
sudo systemctl status study-bot

# View logs
sudo journalctl -u study-bot -f

# View last 100 lines
sudo journalctl -u study-bot -n 100
```

## 📊 Database Management

### Backup Database

```bash
# Manual backup
cp data/study_bot.db backups/study_bot_$(date +%Y%m%d).db

# Verify backup
ls -lh backups/
```

### Automated Daily Backups

```bash
# Edit crontab
crontab -e

# Add this line for daily backup at 3 AM
0 3 * * * cp /home/your_username/study-bot/data/study_bot.db /home/your_username/study-bot/backups/study_bot_$(date +\%Y\%m\%d).db
```

### Restore from Backup

```bash
# Stop the bot first
sudo systemctl stop study-bot

# Restore backup
cp backups/study_bot_20250101.db data/study_bot.db

# Start the bot
sudo systemctl start study-bot
```

## 🔒 Security Best Practices

### 1. File Permissions

```bash
# Set proper permissions
chmod 700 data/
chmod 600 .env
chmod 600 data/study_bot.db
```

### 2. Firewall (if needed)

```bash
# Allow SSH
sudo ufw allow ssh

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 3. Keep Bot Token Secret

- ✅ Never commit `.env` to git
- ✅ Keep `BOT_TOKEN` secure
- ✅ Regenerate token if exposed

## 🐛 Troubleshooting

### Bot Won't Start

```bash
# Check Python version
python3 --version

# Check if virtual environment is activated
which python3

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Database Errors

```bash
# Reinitialize database
python3 database.py

# Check database file
ls -lh data/study_bot.db
```

### Permission Denied

```bash
# Fix permissions
chmod +x start.sh
chmod -R u+w data/
```

### Service Won't Start

```bash
# Check service status
sudo systemctl status study-bot

# View detailed logs
sudo journalctl -u study-bot -n 50

# Check configuration
sudo systemctl cat study-bot
```

### Bot Not Responding in Telegram

1. Check bot is running: `ps aux | grep bot.py`
2. Verify bot token in `.env`
3. Ensure bot is admin in the group
4. Check group ID is correct
5. View logs for errors

## 📈 Monitoring

### Check Bot Status

```bash
# If using systemd service
sudo systemctl status study-bot

# If using manual process
ps aux | grep bot.py
```

### View Logs

```bash
# Systemd service logs
sudo journalctl -u study-bot -f

# Manual run logs (if using nohup)
tail -f bot.log
```

### Resource Usage

```bash
# Check memory and CPU usage
top -p $(pgrep -f bot.py)

# Disk usage
du -sh data/
```

## 🔄 Updating the Bot

```bash
# Stop the bot
sudo systemctl stop study-bot

# Backup database
cp data/study_bot.db backups/study_bot_backup_$(date +%Y%m%d).db

# Pull latest changes
git pull

# Activate virtual environment
source .venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Start the bot
sudo systemctl start study-bot

# Check status
sudo systemctl status study-bot
```

## ✅ Post-Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed
- [ ] `.env` file configured with valid tokens
- [ ] Data directory created
- [ ] Database initialized
- [ ] `start.sh` is executable
- [ ] Bot tested manually
- [ ] Systemd service configured (optional)
- [ ] Backup strategy set up
- [ ] File permissions secured
- [ ] Bot responding in Telegram group

## 🎯 Quick Start Commands Summary

```bash
# Setup (one-time)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Configure tokens
mkdir -p data backups
python3 database.py
chmod +x start.sh

# Run
./start.sh

# Or as service
sudo systemctl start study-bot
```

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review bot logs for error messages
3. Ensure all prerequisites are met
4. Verify configuration in `.env`

---

**Ready to deploy!** Follow these steps and your bot will be running smoothly on your server. 🚀
