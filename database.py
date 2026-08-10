from datetime import datetime
import sqlite3

from config import DB_PATH
from models import GlucoseReading


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_db():
    conn = get_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS glucose(
            timestamp TEXT PRIMARY KEY,
            glucose INTEGER
        )
        """
    )

    conn.commit()
    conn.close()


def get_last_timestamp():
    initialize_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT MAX(timestamp) FROM glucose"
    )

    row = cursor.fetchone()

    conn.close()

    if not row or row[0] is None:
        return None

    return datetime.fromisoformat(row[0])


def insert(reading: GlucoseReading):
    initialize_db()

    conn = get_connection()

    conn.execute(
        """
        INSERT OR IGNORE INTO glucose(timestamp, glucose)
        VALUES (?, ?)
        """,
        (
            reading.timestamp.isoformat(),
            reading.glucose,
        ),
    )

    conn.commit()
    conn.close()


def insert_many(readings):
    if not readings:
        return

    initialize_db()

    conn = get_connection()

    conn.executemany(
        """
        INSERT OR IGNORE INTO glucose(timestamp, glucose)
        VALUES (?, ?)
        """,
        [
            (
                reading.timestamp.isoformat(),
                reading.glucose,
            )
            for reading in readings
        ],
    )

    conn.commit()
    conn.close()


def get_all():
    initialize_db()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT timestamp, glucose
        FROM glucose
        ORDER BY timestamp
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return [
        GlucoseReading(
            timestamp=datetime.fromisoformat(timestamp),
            glucose=glucose,
        )
        for timestamp, glucose in rows
    ]
