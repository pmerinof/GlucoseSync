from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

from models import GlucoseReading
from logger import logger

# Crear carpeta para la BD si no existe
DB_FOLDER = Path("database")
DB_FOLDER.mkdir(exist_ok=True)
DB_FILE = DB_FOLDER / "glucosesync.db"

class Database:
    """
    Base de datos SQLite local para GlucoseSync.
    Contiene dos tablas:
      - glucose(timestamp TEXT PRIMARY KEY, glucose INTEGER)
      - sync_state(key TEXT PRIMARY KEY, value TEXT)
    """

    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS glucose (
                timestamp TEXT PRIMARY KEY,
                glucose INTEGER NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sync_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.conn.commit()

    def insert(self, reading: GlucoseReading):
        """
        Inserta una lectura (ignorando duplicados por PRIMARY KEY).
        """
        self.conn.execute(
            "INSERT OR IGNORE INTO glucose(timestamp, glucose) VALUES (?, ?)",
            (reading.timestamp.isoformat(), reading.glucose)
        )

    def insert_many(self, readings: list[GlucoseReading]):
        """
        Inserta varias lecturas de golpe.
        """
        if not readings:
            return
        data = [(r.timestamp.isoformat(), r.glucose) for r in readings]
        self.conn.executemany(
            "INSERT OR IGNORE INTO glucose(timestamp, glucose) VALUES (?, ?)",
            data
        )
        self.conn.commit()

    def get_all(self) -> list[GlucoseReading]:
        """
        Devuelve todas las lecturas ordenadas por timestamp.
        """
        cur = self.conn.execute(
            "SELECT timestamp, glucose FROM glucose ORDER BY timestamp"
        )
        results = []
        for row in cur.fetchall():
            results.append(
                GlucoseReading(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    glucose=row["glucose"]
                )
            )
        return results

    def get_between(self, start: datetime, end: datetime) -> list[GlucoseReading]:
        """
        Devuelve lecturas con timestamp en [start, end].
        """
        cur = self.conn.execute(
            """
            SELECT timestamp, glucose FROM glucose
            WHERE timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp
            """,
            (start.isoformat(), end.isoformat())
        )
        results = []
        for row in cur.fetchall():
            results.append(
                GlucoseReading(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    glucose=row["glucose"]
                )
            )
        return results

    def get_last_before(self, when: datetime) -> Optional[GlucoseReading]:
        """
        Devuelve la última lectura con timestamp <= 'when', o None si no hay.
        """
        cur = self.conn.execute(
            """
            SELECT timestamp, glucose FROM glucose
            WHERE timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (when.isoformat(),)
        )
        row = cur.fetchone()
        if row:
            return GlucoseReading(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                glucose=row["glucose"]
            )
        return None

    def count(self) -> int:
        """
        Devuelve el número de registros en glucose.
        """
        cur = self.conn.execute("SELECT COUNT(*) FROM glucose")
        return cur.fetchone()[0]

    def clear(self):
        """
        Borra todas las lecturas (no elimina la tabla).
        """
        self.conn.execute("DELETE FROM glucose")
        self.conn.commit()

    # ---- Estado de sincronización ----

    def set_state(self, key: str, value: str):
        """
        Inserta o actualiza el estado de sincronización.
        """
        self.conn.execute(
            """
            INSERT INTO sync_state(key, value) VALUES(?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
            """,
            (key, value)
        )
        self.conn.commit()

    def get_state(self, key: str) -> Optional[str]:
        """
        Obtiene el valor del estado por clave, o None si no existe.
        """
        cur = self.conn.execute(
            "SELECT value FROM sync_state WHERE key = ?", (key,)
        )
        row = cur.fetchone()
        return row["value"] if row else None

    def last_excel_sync(self) -> Optional[datetime]:
        """
        Devuelve el último timestamp sincronizado en Excel (key 'last_excel_sync').
        """
        ts = self.get_state("last_excel_sync")
        return datetime.fromisoformat(ts) if ts else None

    def update_last_excel_sync(self, timestamp: datetime):
        """
        Actualiza el estado 'last_excel_sync' con el timestamp dado.
        """
        self.set_state("last_excel_sync", timestamp.isoformat())

    def close(self):
        """
        Cierra la conexión con la base de datos.
        """
        self.conn.commit()
        self.conn.close()
