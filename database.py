import sqlite3
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def initialize_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS glucose(
            timestamp TEXT PRIMARY KEY,
            glucose INTEGER
        )
    """)
    conn.commit()
    conn.close()
