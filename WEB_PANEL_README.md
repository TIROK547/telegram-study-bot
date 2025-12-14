# Study Bot - Web Panel Documentation

## Overview

This system includes:
1. **Telegram Bot** - Tracks study time with user profiles (field & grade)
2. **Web API** - FastAPI backend serving statistics
3. **Web Panel** - Two frontend options available:
   - **Next.js App** (Recommended) - Modern React framework with SSR
   - **Vanilla HTML/CSS/JS** - Simple static frontend

## Features

### Bot Features (Farsi)
- ✅ User profile completion on first /start
- ✅ Field selection: دانشگاه, ریاضی, انسانی, تجربی, هنرستان
- ✅ Grade/Term input (6-12 for school, 1-22 for university)
- ✅ Custom field for هنرستان students
- ✅ **Group member verification** - Users must be members of the allowed group
- ✅ **Private DM support** - Group members can use the bot in private messages
- ✅ Study session tracking
- ✅ Daily, weekly, monthly statistics

### Web Panel Features
- ✅ No login required (public dashboard)
- ✅ Dark & Light theme toggle
- ✅ Farsi & English language support
- ✅ User search by username (@username)
- ✅ Daily, weekly, monthly leaderboards
- ✅ User profile display (field, grade)
- ✅ Total study time per user
- ✅ Responsive design
- ✅ Footer with creator info (@tirok547)

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup .env file:**
   ```bash
   BOT_TOKEN=your_telegram_bot_token
   ALLOWED_GROUP_ID=your_group_id  # Optional
   UPDATE_INTERVAL=30  # Seconds
   ```

3. **Initialize database:**
   ```bash
   python database.py
   ```

## Running the System

### Backend Services

**Option 1: Run All Services Together**
```bash
./start.sh
```

This will start:
- Telegram Bot
- Web API on http://localhost:8000

**Option 2: Run Services Separately**

**Terminal 1 - Bot:**
```bash
python bot.py
```

**Terminal 2 - API:**
```bash
python api.py
```

### Frontend Options

#### Option 1: Next.js Frontend (Recommended)

**Development:**
```bash
cd web-panel
npm install
npm run dev
```

Access at: http://localhost:3000

**Production:**
```bash
cd web-panel
npm run build
npm start
```

**Features:**
- Server-Side Rendering (SSR)
- Better SEO
- Optimized performance
- TypeScript support
- Modern React features

#### Option 2: Vanilla HTML Frontend

The FastAPI backend serves the vanilla frontend automatically.

Access at: http://localhost:8000

**Features:**
- No build step required
- Simple and lightweight
- Served directly by FastAPI
- Good for simple deployments

## API Endpoints

### Get all users
```
GET /api/users
```

### Get user by username
```
GET /api/user/{username}
```
Example: `/api/user/@tirok547`

### Get daily stats
```
GET /api/stats/daily
```

### Get weekly stats
```
GET /api/stats/weekly
```

### Get monthly stats
```
GET /api/stats/monthly
```

### Search users
```
GET /api/search/{query}
```

## Database Schema

### Users Table
- `user_id` (TEXT, PRIMARY KEY)
- `name` (TEXT) - Username (@username or "user: (Name)")
- `field` (TEXT) - Field of study
- `grade` (INTEGER) - Grade/Term
- `profile_completed` (INTEGER) - 0 or 1
- `active_session_start` (TEXT)
- `active_session_paused_at` (TEXT)
- `active_session_paused_duration` (INTEGER)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Daily/Weekly/Monthly Stats Tables
- `user_id` (TEXT)
- `date/week_key/month_key` (TEXT)
- `name` (TEXT)
- `total_seconds` (INTEGER)

## User Profile Fields

### Fields (رشته)
1. **دانشگاه (University)** - Term 1-22
2. **ریاضی (Mathematics)** - Grade 6-12
3. **انسانی (Humanities)** - Grade 6-12
4. **تجربی (Experimental)** - Grade 6-12
5. **هنرستان (Art School)** - Custom field name

## Web Panel Usage

### Theme Toggle
Click the moon/sun icon (🌙/☀️) to switch between dark and light themes.

### Language Toggle
Click "EN/FA" button to switch between English and Farsi.

### Search User
1. Enter username in the format `@username`
2. Click "جستجو" (Search)
3. View user's profile and all-time statistics

### View Statistics
- **Daily Tab**: Today's study time leaderboard
- **Weekly Tab**: This week's study time leaderboard
- **Monthly Tab**: This month's study time leaderboard

### Refresh Stats
Click the 🔄 button next to each tab title to refresh the data.

## Development

### Project Structure
```
study-bot/
├── bot.py              # Telegram bot
├── database.py         # Database operations
├── api.py              # FastAPI backend
├── frontend/           # Web panel
│   ├── index.html     # Main HTML
│   ├── style.css      # Styles
│   └── app.js         # JavaScript logic
├── data/              # SQLite database
│   └── study_bot.db
├── start.sh           # Startup script
└── requirements.txt   # Python dependencies
```

### Adding New Features

**Backend (api.py):**
```python
@app.get("/api/your-endpoint")
async def your_function():
    # Your code here
    return {"data": result}
```

**Frontend (app.js):**
```javascript
async function fetchYourData() {
    const response = await fetch(`${API_URL}/your-endpoint`);
    return await response.json();
}
```

## Production Deployment

### Using Nginx as Reverse Proxy

1. **Install Nginx:**
   ```bash
   sudo apt install nginx
   ```

2. **Configure Nginx:**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Run with systemd:**
   Create `/etc/systemd/system/study-bot.service`:
   ```ini
   [Unit]
   Description=Study Bot
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/study-bot
   ExecStart=/path/to/study-bot/.venv/bin/python bot.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   Create `/etc/systemd/system/study-api.service` for the API similarly.

## Troubleshooting

### Bot not responding
- Check if BOT_TOKEN is correct in .env
- Verify bot is running: `ps aux | grep bot.py`
- Check bot logs

### Web panel not loading
- Verify API is running on port 8000
- Check firewall settings
- Inspect browser console for errors

### Database errors
- Ensure `data/` directory exists
- Run `python database.py` to reinitialize
- Check file permissions

### Stats not updating
- Verify users have completed their profiles
- Check if bot is tracking sessions correctly
- Refresh the page or click 🔄 button

## Credits

**Developer & Support:** [@tirok547](https://t.me/tirok547)

## License

This project is created for educational purposes.
