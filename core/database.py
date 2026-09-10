# core/database.py
import logging
import aiosqlite
import sqlite3
import asyncio
from config import DB_PATH

_db_conn = None

async def init_db():
    global _db_conn
    _db_conn = await aiosqlite.connect(DB_PATH)
    _db_conn.row_factory = aiosqlite.Row
    
    await _db_conn.executescript('''
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY, 
            welcome TEXT, 
            antilink BOOLEAN DEFAULT 1, 
            rules TEXT,
            is_premium BOOLEAN DEFAULT 0,
            total_messages INTEGER DEFAULT 0,
            antispam BOOLEAN DEFAULT 1,
            filter_enabled BOOLEAN DEFAULT 1,
            welcome_enabled BOOLEAN DEFAULT 1,
            lock_links BOOLEAN DEFAULT 0,
            lock_photos BOOLEAN DEFAULT 0,
            lock_videos BOOLEAN DEFAULT 0,
            lock_stickers BOOLEAN DEFAULT 0,
            lock_forward BOOLEAN DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER, 
            chat_id INTEGER, 
            is_banned BOOLEAN DEFAULT 0,
            muted_until TIMESTAMP DEFAULT 0,
            PRIMARY KEY (user_id, chat_id)
        );
        
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            chat_id INTEGER, 
            user_id INTEGER, 
            reason TEXT, 
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS filters (
            chat_id INTEGER, 
            word TEXT, 
            PRIMARY KEY (chat_id, word)
        );

        CREATE TABLE IF NOT EXISTS user_stats (
            user_id INTEGER, 
            chat_id INTEGER, 
            xp INTEGER DEFAULT 0, 
            level INTEGER DEFAULT 1, 
            last_xp_time TIMESTAMP,
            coins INTEGER DEFAULT 0,
            last_daily TIMESTAMP,
            daily_streak INTEGER DEFAULT 0,
            last_work TIMESTAMP DEFAULT 0,
            last_rob TIMESTAMP DEFAULT 0,
            username TEXT,
            PRIMARY KEY (user_id, chat_id)
        );
        
        CREATE TABLE IF NOT EXISTS user_achievements (
            user_id INTEGER, 
            chat_id INTEGER, 
            badge TEXT, 
            PRIMARY KEY (user_id, chat_id, badge)
        );
        
        CREATE TABLE IF NOT EXISTS moderation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            chat_id INTEGER, 
            admin_id INTEGER, 
            action TEXT, 
            target_id INTEGER, 
            reason TEXT, 
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS user_inventory (
            user_id INTEGER, 
            chat_id INTEGER, 
            item TEXT, 
            PRIMARY KEY (user_id, chat_id, item)
        );
        
        CREATE TABLE IF NOT EXISTS active_games (
            game_id TEXT PRIMARY KEY,
            chat_id INTEGER,
            game_type TEXT,
            data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    # اضافه کردن ستون یوزرنیم برای دیتابیس‌های قدیمی
    await _add_column_if_missing("user_stats", "username", "TEXT")
    
    await _db_conn.commit()
    logging.info("Database initialized successfully")

async def _add_column_if_missing(table, column, definition):
    """ALTER TABLE امن: اگر ستون وجود نداشت اضافه میکند."""
    try:
        await _db_conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            logging.error(f"Unexpected error adding column {column} to {table}: {e}")

async def execute_query(query, params=(), fetch=False):
    if not _db_conn: 
        await init_db()
    try:
        cursor = await _db_conn.execute(query, params)
        if fetch:
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
        await cursor.close()
        return cursor.rowcount
    except Exception as e:
        logging.error(f"DB Error on query [{query}]: {e}")
        return [] if fetch else 0

async def db_commit_task():
    while True:
        await asyncio.sleep(3)
        try:
            await _db_conn.commit()
        except Exception as e:
            logging.error(f"DB Commit Error: {e}")