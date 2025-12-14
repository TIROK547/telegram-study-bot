# Quick Start Guide

## 🚀 Running the Complete System

### Step 1: Start Backend Services

Open a terminal and run:

```bash
cd /home/tirok547/Code/study-bot
./start.sh
```

This will start:
- ✅ Telegram Bot (listens for messages)
- ✅ FastAPI Backend (http://localhost:8000)

**Alternative:** Run them separately in different terminals:
```bash
# Terminal 1
source .venv/bin/activate
python bot.py

# Terminal 2
source .venv/bin/activate
python api.py
```

### Step 2: Start Frontend (Choose One)

#### Option A: Next.js Frontend (Recommended) 🌟

Open a **new terminal**:

```bash
cd /home/tirok547/Code/study-bot/web-panel
npm run dev
```

Access at:
- **Farsi:** http://localhost:3000
- **English:** http://localhost:3000/en

#### Option B: Vanilla HTML Frontend

No additional setup needed! Already served by FastAPI.

Access at: http://localhost:8000

---

## 🎯 Testing the System

### 1. Test the Bot

1. Open Telegram
2. Go to your bot (use the token in `.env`)
3. Send `/start`
4. **First Time Users:**
   - You'll be asked to complete your profile
   - Select your field (دانشگاه, ریاضی, etc.)
   - Enter your grade/term
5. **After Profile Setup:**
   - Use the inline buttons to:
     - ▶️ Start studying
     - ⏸ Pause
     - ⏹ End and save

### 2. Test the Web Panel

#### Search Feature:
1. Open web panel (http://localhost:3000 or http://localhost:8000)
2. Enter your username: `@tirok547`
3. Click "جستجو" (Search)
4. View your profile and stats

#### Statistics:
- Click **روزانه** (Daily) - Today's leaderboard
- Click **هفتگی** (Weekly) - This week's leaderboard
- Click **ماهانه** (Monthly) - This month's leaderboard

#### Theme & Language:
- Click **🌙** to toggle dark mode
- Click **EN/FA** to switch language

---

## 📱 Bot Access Control

### How It Works Now:

✅ **Group Members Can Use Bot in DM**

1. User must be a member of `ALLOWED_GROUP_ID` (set in `.env`)
2. Once they're a member, they can:
   - Use bot in the group
   - Use bot in private DM

❌ **Non-Members Cannot Use Bot**

If someone tries to use the bot without being in the group:
```
⛔️ دسترسی محدود شده است.

برای استفاده از این ربات، ابتدا باید عضو گروه مجاز باشید.
بعد از عضویت در گروه، می‌توانید از ربات در پیام خصوصی استفاده کنید.
```

---

## 🎨 Next.js Frontend Features

### Dark & Light Theme
- Click the moon/sun button (🌙/☀️) in the header
- Preference is saved automatically
- Works in both Farsi and English

### Language Switching
- Click **EN** (when in Farsi) or **FA** (when in English)
- Full RTL support for Farsi
- LTR support for English
- All UI text translates

### User Search
- Type `@username` (e.g., `@tirok547`)
- Press Enter or click "جستجو"
- See user's:
  - Field (رشته)
  - Grade (پایه)
  - Daily time
  - Weekly time
  - Monthly time
  - Total time

### Statistics Leaderboards
- **Top 3 get medals:** 🥇 🥈 🥉
- **Special styling** for top 3 ranks
- **Click 🔄** to refresh data
- **Real-time updates** from FastAPI

---

## 🔧 Troubleshooting

### Bot Not Responding

1. Check if bot is running:
   ```bash
   ps aux | grep bot.py
   ```

2. Check `.env` file has correct `BOT_TOKEN`

3. Restart bot:
   ```bash
   pkill -f bot.py
   python bot.py
   ```

### Web Panel Not Loading

1. Check if API is running:
   ```bash
   curl http://localhost:8000/api/stats/daily
   ```

2. Check if Next.js is running:
   ```bash
   curl http://localhost:3000
   ```

3. Check browser console for errors (F12)

### "Access Denied" in Bot

1. Make sure `ALLOWED_GROUP_ID` is set in `.env`
2. Verify user is a member of that group
3. Check bot has permission to see group members

### Next.js Build Errors

```bash
cd web-panel
rm -rf .next node_modules package-lock.json
npm install
npm run dev
```

---

## 📊 Monitoring

### Check Active Users
```bash
sqlite3 data/study_bot.db "SELECT name, field, grade FROM users WHERE profile_completed = 1"
```

### Check Today's Stats
```bash
curl http://localhost:8000/api/stats/daily | jq
```

### Check API Health
```bash
curl http://localhost:8000/docs
```

---

## 🛑 Stopping Services

### Stop All Services (if using start.sh)
Press `Ctrl+C` in the terminal where `start.sh` is running

### Stop Individual Services

**Bot:**
```bash
pkill -f bot.py
```

**API:**
```bash
pkill -f api.py
```

**Next.js:**
```bash
# In the web-panel terminal, press Ctrl+C
```

---

## 🌟 Production Deployment

### Next.js Production Build

```bash
cd web-panel
npm run build
npm start
```

This will:
- Optimize all components
- Generate static pages where possible
- Start production server on port 3000

### Environment Variables

Create `web-panel/.env.production.local`:
```env
NEXT_PUBLIC_API_URL=https://your-domain.com/api
```

---

## 📚 More Documentation

- **Complete System Docs:** `WEB_PANEL_README.md`
- **Next.js Specific:** `web-panel/README.md`
- **Bot Code:** `bot.py`
- **API Code:** `api.py`
- **Database Schema:** `database.py`

---

## 💡 Tips

1. **Use Next.js frontend** for better performance and SEO
2. **Set ALLOWED_GROUP_ID** to enable access control
3. **Users must complete profiles** before using the bot
4. **Check API docs** at http://localhost:8000/docs
5. **Use Dark Mode** for night studying 🌙

---

## 🆘 Support

Created by: [@tirok547](https://t.me/tirok547)

If you encounter issues:
1. Check this guide first
2. Read the full documentation
3. Contact @tirok547 on Telegram
