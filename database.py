import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

from models import GlucoseReading
from logger import logger

# Crear carpeta de la base de datos si no existe
DB_FOLDER = Path("database")
DB_FOLDER.mkdir(exist_ok=True)
DB_FILE = DB_FOLDER / "glucosesync.db"

class Database:
    """
    Base de datos SQLite local para GlucoseSync.
    Tablas:
      - glucose(timestamp TEXT PRIMARY KEY, glucose INTEGER)
      - sync_state(key TEXT PRIMARY KEY, value TEXT)
    """
    def __init__(self):
        # Conexión a la base de datos (crea el archivo si no existe).
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

    def insert(self, reading: GlucoseReading) -> None:
        """
        Inserta una lectura en la tabla glucose. Si ya existe (timestamp duplicado), se ignora.
        """
        try:
            self.conn.execute(
                "INSERT OR IGNORE INTO glucose (timestamp, glucose) VALUES (?, ?)",
                (reading.timestamp.isoformat(), reading.glucose)
            )
        except Exception as e:
            logger.error("Error insertando lectura %s: %s", reading, e)
        # No hacemos commit aquí para poder agrupar múltiples inserciones.

    def insert_many(self, readings: list[GlucoseReading]) -> None:
        """
        Inserta múltiples lecturas en una sola transacción.
        """
        try:
            cur = self.conn.cursor()
            data = [(r.timestamp.isoformat(), r.glucose) for r in readings]
            cur.executemany("INSERT OR IGNORE INTO glucose (timestamp, glucose) VALUES (?, ?)", data)
        except Exception as e:
            logger.error("Error insertando lecturas masivas: %s", e)

    def get_all(self) -> list[GlucoseReading]:
        """
        Devuelve todas las lecturas ordenadas por timestamp ascendente.
        """
        cur = self.conn.execute("SELECT timestamp, glucose FROM glucose ORDER BY timestamp")
        rows = cur.fetchall()
        return [GlucoseReading(datetime.fromisoformat(row["timestamp"]), row["glucose"]) for row in rows]

    def get_between(self, start: datetime, end: datetime) -> list[GlucoseReading]:
        """
        Devuelve lecturas entre fechas (inclusive).
        """
        cur = self.conn.execute(
            "SELECT timestamp, glucose FROM glucose WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
            (start.isoformat(), end.isoformat())
        )
        rows = cur.fetchall()
        return [GlucoseReading(datetime.fromisoformat(row["timestamp"]), row["glucose"]) for row in rows]

    def get_last_before(self, when: datetime) -> Optional[GlucoseReading]:
        """
        Devuelve la última lectura antes de 'when', o None si no hay.
        """
        cur = self.conn.execute(
            "SELECT timestamp, glucose FROM glucose WHERE timestamp < ? ORDER BY timestamp DESC LIMIT 1",
            (when.isoformat(),)
        )
        row = cur.fetchone()
        if row:
            return GlucoseReading(datetime.fromisoformat(row["timestamp"]), row["glucose"])
        return None

    def count(self) -> int:
        """Número total de lecturas en la base de datos."""
        cur = self.conn.execute("SELECT COUNT(*) AS cnt FROM glucose")
        row = cur.fetchone()
        return row["cnt"] if row else 0

    def clear(self) -> None:
        """Elimina todas las lecturas (tabla glucose)."""
        self.conn.execute("DELETE FROM glucose")
        self.conn.commit()

    def set_state(self, key: str, value: str) -> None:
        """
        Guarda un par llave-valor en sync_state (p.ej. última fecha de sync Excel).
        """
        self.conn.execute("INSERT OR REPLACE INTO sync_state (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_state(self, key: str) -> Optional[str]:
        """
        Recupera el valor almacenado para 'key' en sync_state, o None si no existe.
        """
        cur = self.conn.execute("SELECT value FROM sync_state WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None

    def last_excel_sync(self) -> Optional[datetime]:
        """
        Obtiene la última fecha de sincronización con Excel (guardada como ISO).
        """
        val = self.get_state("last_excel_sync")
        if val:
            return datetime.fromisoformat(val)
        return None

    def update_last_excel_sync(self, timestamp: datetime) -> None:
        """Actualiza la fecha de última sincronización en sync_state."""
        self.set_state("last_excel_sync", timestamp.isoformat())

    def close(self) -> None:
        """Commit y cierra la conexión."""
        self.conn.commit()
        self.conn.close()
