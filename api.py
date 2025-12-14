from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import database as db
import pytz
import jdatetime
import uvicorn

app = FastAPI(title="Study Bot API", version="1.0.0")

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Timezone
IRAN_TZ = pytz.timezone('Asia/Tehran')

# Field name mappings
FIELD_NAMES = {
    "daneshgah": {"fa": "دانشگاه", "en": "University"},
    "riazi": {"fa": "ریاضی", "en": "Mathematics"},
    "ensani": {"fa": "انسانی", "en": "Humanities"},
    "tajrobi": {"fa": "تجربی", "en": "Experimental"},
    "honarestan": {"fa": "هنرستان", "en": "Art School"}
}


def get_iran_now():
    """Get current time in Iran timezone"""
    return datetime.now(IRAN_TZ)


def get_today():
    """Get today's date as string"""
    return get_iran_now().strftime("%Y-%m-%d")


def get_persian_date_cached(date_str):
    """Get Persian date from Gregorian date string"""
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


def get_persian_week_key():
    """Get Persian week identifier"""
    p_date = get_persian_date_cached(get_today())
    return f"{p_date['year']}-W{p_date['week']:02d}"


def get_persian_month_key():
    """Get Persian month identifier"""
    p_date = get_persian_date_cached(get_today())
    return f"{p_date['year']}-{p_date['month']:02d}"


def format_user_data(user_data: Dict) -> Dict:
    """Format user data for API response"""
    field = user_data.get('field', '')
    grade = user_data.get('grade', 0)

    # Handle honarestan custom field
    if field and field.startswith('honarestan:'):
        field_key = 'honarestan'
        custom_field = field.split(':', 1)[1]
        field_display = {
            "fa": f"هنرستان - {custom_field}",
            "en": f"Art School - {custom_field}"
        }
        grade_display = {"fa": custom_field, "en": custom_field}
    elif field in FIELD_NAMES:
        field_key = field
        field_display = FIELD_NAMES[field]
        if field == "daneshgah":
            grade_display = {"fa": f"ترم {grade}", "en": f"Term {grade}"}
        else:
            grade_display = {"fa": f"پایه {grade}", "en": f"Grade {grade}"}
    else:
        field_key = field or "unknown"
        field_display = {"fa": field or "نامشخص", "en": field or "Unknown"}
        grade_display = {"fa": str(grade), "en": str(grade)}

    return {
        "user_id": user_data.get('user_id'),
        "name": user_data.get('name'),
        "field": field_key,
        "field_display": field_display,
        "grade": grade,
        "grade_display": grade_display,
        "profile_completed": user_data.get('profile_completed', 0) == 1
    }


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    db.init_database()
    print("✅ API Server started successfully")


@app.get("/")
async def root():
    """Redirect to frontend"""
    return FileResponse("frontend/index.html")


@app.get("/api/users")
async def get_users():
    """Get all users with their profiles"""
    users = db.get_all_users()
    formatted_users = []

    for user_id, user_data in users.items():
        formatted_users.append(format_user_data(user_data))

    return {"users": formatted_users}


@app.get("/api/user/{username}")
async def get_user_by_username(username: str):
    """Get user stats by username"""
    # Remove @ if present
    username = username.strip()
    if not username.startswith('@'):
        username = '@' + username

    # Find user by username
    users = db.get_all_users()
    user_id = None
    user_data = None

    for uid, data in users.items():
        if data.get('name', '').lower() == username.lower():
            user_id = uid
            user_data = data
            break

    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")

    # Get stats
    today = get_today()
    week_key = get_persian_week_key()
    month_key = get_persian_month_key()

    daily_stats = db.get_daily_stats(today)
    weekly_stats = db.get_weekly_stats(week_key)
    monthly_stats = db.get_monthly_stats(month_key)

    # Calculate total time from all daily stats
    all_daily_stats = db.get_all_daily_stats()
    total_time = sum(
        day_data.get(user_id, {}).get('total_seconds', 0)
        for day_data in all_daily_stats.values()
    )

    return {
        "user": format_user_data(user_data),
        "stats": {
            "daily": daily_stats.get(user_id, {}).get('total_seconds', 0),
            "weekly": weekly_stats.get(user_id, {}).get('total_seconds', 0),
            "monthly": monthly_stats.get(user_id, {}).get('total_seconds', 0),
            "total": total_time
        }
    }


@app.get("/api/stats/daily")
async def get_daily_stats():
    """Get daily stats for all users"""
    today = get_today()
    stats = db.get_daily_stats(today)
    users = db.get_all_users()

    result = []
    for user_id, user_stats in stats.items():
        user_data = users.get(user_id, {})
        result.append({
            "user": format_user_data(user_data),
            "total_seconds": user_stats.get('total_seconds', 0)
        })

    # Sort by total_seconds descending
    result.sort(key=lambda x: x['total_seconds'], reverse=True)

    return {
        "date": today,
        "stats": result
    }


@app.get("/api/stats/weekly")
async def get_weekly_stats():
    """Get weekly stats for all users"""
    week_key = get_persian_week_key()
    stats = db.get_weekly_stats(week_key)
    users = db.get_all_users()

    result = []
    for user_id, user_stats in stats.items():
        user_data = users.get(user_id, {})
        result.append({
            "user": format_user_data(user_data),
            "total_seconds": user_stats.get('total_seconds', 0)
        })

    # Sort by total_seconds descending
    result.sort(key=lambda x: x['total_seconds'], reverse=True)

    return {
        "week_key": week_key,
        "stats": result
    }


@app.get("/api/stats/monthly")
async def get_monthly_stats():
    """Get monthly stats for all users"""
    month_key = get_persian_month_key()
    stats = db.get_monthly_stats(month_key)
    users = db.get_all_users()

    result = []
    for user_id, user_stats in stats.items():
        user_data = users.get(user_id, {})
        result.append({
            "user": format_user_data(user_data),
            "total_seconds": user_stats.get('total_seconds', 0)
        })

    # Sort by total_seconds descending
    result.sort(key=lambda x: x['total_seconds'], reverse=True)

    return {
        "month_key": month_key,
        "stats": result
    }


@app.get("/api/search/{query}")
async def search_users(query: str):
    """Search users by username"""
    query = query.lower().strip()
    if query.startswith('@'):
        query = query[1:]

    users = db.get_all_users()
    results = []

    for user_id, user_data in users.items():
        name = user_data.get('name', '').lower()
        if query in name or f"@{query}" in name:
            results.append(format_user_data(user_data))

    return {"results": results}


# Mount static files (frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
