# core/database.py
import logging
import aiosqlite
import sqlite3
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
            rules TEXT
        );
        
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER, 
            chat_id INTEGER, 
            is_banned BOOLEAN DEFAULT 0, 
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
            PRIMARY KEY (user_id, chat_id)
        );
    ''')
    # اضافه کردن ستون‌های جدید به صورت امن (اگر از قبل وجود نداشته باشند)
    await _add_column_if_missing("groups", "is_premium", "BOOLEAN DEFAULT 0")
    await _add_column_if_missing("groups", "total_messages", "INTEGER DEFAULT 0")
    await _db_conn.commit()
        # اضافه کردن ستون‌های اقتصاد به صورت امن
    await _add_column_if_missing("user_stats", "coins", "INTEGER DEFAULT 0")
    await _add_column_if_missing("user_stats", "last_daily", "TIMESTAMP")


async def _add_column_if_missing(table, column, definition):
    """ALTER TABLE امن: فقط خطای 'duplicate column' را نادیده می‌گیرد، نه هر خطایی را."""
    try:
        await _db_conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            logging.error(f"Unexpected error adding column {column} to {table}: {e}")
            raise

async def execute_query(query, params=(), fetch=False):
    if not _db_conn:
        await init_db()
        
    try:
        cursor = await _db_conn.execute(query, params)
        if fetch:
            rows = await cursor.fetchall()
            await cursor.close()
            return rows
        await _db_conn.commit()
        await cursor.close()
        return cursor.rowcount
    except Exception as e:
        logging.error(f"DB Error on query [{query}]: {e}")
        return [] if fetch else 0