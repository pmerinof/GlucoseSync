import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EMAIL = os.getenv("ABBOTT_EMAIL")
PASSWORD = os.getenv("ABBOTT_PASSWORD")

if not EMAIL or not PASSWORD:
    raise RuntimeError(
        "No se han configurado las variables de entorno "
        "ABBOTT_EMAIL y ABBOTT_PASSWORD."
    )

DB_PATH = BASE_DIR / "database" / "glucosesync.db"
CSV_PATH = BASE_DIR / "datos" / "glucose_history.csv"
EXCEL_FILE = BASE_DIR / "datos" / "Glucosa.xlsx"
