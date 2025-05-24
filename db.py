# db.py
import aiosqlite

# Initialize DB
async def init_db():
    async with aiosqlite.connect("workhours.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INTEGER PRIMARY KEY,
            hourly_rate REAL,
            transport_bonus REAL,
            credit_points REAL,
            language TEXT DEFAULT 'en'
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS WorkSessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
        """)
        await db.commit()

# User registration
async def register_user(user_id):
    async with aiosqlite.connect("workhours.db") as db:
        await db.execute("INSERT OR IGNORE INTO Users (user_id) VALUES (?)", (user_id,))
        await db.commit()

# Update settings
async def update_rate(user_id, rate):
    async with aiosqlite.connect("workhours.db") as db:
        await db.execute("UPDATE Users SET hourly_rate = ? WHERE user_id = ?", (rate, user_id))
        await db.commit()

async def update_bonus(user_id, bonus):
    async with aiosqlite.connect("workhours.db") as db:
        await db.execute("UPDATE Users SET transport_bonus = ? WHERE user_id = ?", (bonus, user_id))
        await db.commit()

async def update_credit_points(user_id, points):
    async with aiosqlite.connect("workhours.db") as db:
        await db.execute("UPDATE Users SET credit_points = ? WHERE user_id = ?", (points, user_id))
        await db.commit()

async def update_language(user_id, lang):
    async with aiosqlite.connect("workhours.db") as db:
        await db.execute("UPDATE Users SET language = ? WHERE user_id = ?", (lang, user_id))
        await db.commit()

# Retrieve user settings
async def get_user_language(user_id):
    async with aiosqlite.connect("workhours.db") as db:
        async with db.execute("SELECT language FROM Users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 'en'

async def get_user_settings(user_id):
    async with aiosqlite.connect("workhours.db") as db:
        async with db.execute(
            "SELECT hourly_rate, transport_bonus, credit_points, language FROM Users WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return {
                "hourly_rate": row[0] or 0,
                "transport_bonus": row[1] or 0,
                "credit_points": row[2] or 0,
                "language": row[3] or 'en'
            }

# Work session recording
async def start_session(user_id, start_time):
    async with aiosqlite.connect("workhours.db") as db:
        await db.execute("INSERT INTO WorkSessions (user_id, start_time) VALUES (?, ?)", (user_id, start_time))
        await db.commit()

async def stop_session(user_id, end_time):
    async with aiosqlite.connect("workhours.db") as db:
        async with db.execute("""
            SELECT id FROM WorkSessions
            WHERE user_id = ? AND end_time IS NULL
            ORDER BY start_time DESC LIMIT 1
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                session_id = row[0]
                await db.execute("UPDATE WorkSessions SET end_time = ? WHERE id = ?", (end_time, session_id))
                await db.commit()

# Manual session insertion
async def save_manual_session(user_id, start_time, end_time):
    async with aiosqlite.connect("workhours.db") as db:
        await db.execute(
            "INSERT INTO WorkSessions (user_id, start_time, end_time) VALUES (?, ?, ?)",
            (user_id, start_time, end_time)
        )
        await db.commit()

# Queries
async def get_sessions_by_month(user_id, year, month):
    async with aiosqlite.connect("workhours.db") as db:
        async with db.execute("""
            SELECT start_time, end_time FROM WorkSessions
            WHERE user_id = ?
              AND strftime('%Y', start_time) = ?
              AND strftime('%m', start_time) = ?
              AND end_time IS NOT NULL
        """, (user_id, str(year), f"{month:02d}")) as cursor:
            return await cursor.fetchall()

async def get_sessions_by_day(user_id, day):
    async with aiosqlite.connect("workhours.db") as db:
        async with db.execute("""
            SELECT start_time, end_time FROM WorkSessions
            WHERE user_id = ? AND date(start_time) = ? AND end_time IS NOT NULL
            ORDER BY start_time
        """, (user_id, day)) as cursor:
            return await cursor.fetchall()

async def get_user_active_months(user_id):
    async with aiosqlite.connect("workhours.db") as db:
        async with db.execute("""
            SELECT DISTINCT 
                strftime('%Y', start_time) AS year, 
                strftime('%m', start_time) AS month
            FROM WorkSessions
            WHERE user_id = ? AND end_time IS NOT NULL
            ORDER BY year DESC, month DESC
        """, (user_id,)) as cursor:
            return [(int(row[0]), int(row[1])) async for row in cursor]

async def get_all_users():
    async with aiosqlite.connect("workhours.db") as db:
        async with db.execute("SELECT user_id FROM Users") as cursor:
            return [row[0] async for row in cursor]
