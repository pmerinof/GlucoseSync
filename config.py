from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
# Rutas de archivos
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "database" / "glucosesync.db"
CSV_PATH = BASE_DIR / "datos" / "glucose_history.csv"
EXCEL_FILE = BASE_DIR / "datos" / "glucosa.xlsx"
# Credenciales desde entorno
EMAIL = os.getenv("ABBOTT_EMAIL", "")
PASSWORD = os.getenv("ABBOTT_PASSWORD", "")
