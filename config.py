import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (local) o desde GitHub Secrets en CI.
load_dotenv()

# Credenciales de Abbott LibreLinkUp (definidas en .env o como secrets).
EMAIL = os.getenv("ABBOTT_EMAIL", "")
PASSWORD = os.getenv("ABBOTT_PASSWORD", "")

# Ruta al archivo de Excel (plantilla). Puede pasarse por EXCEL_FILE en .env.
EXCEL_FILE = Path(os.getenv("EXCEL_FILE", "datos/glucosa.xlsx"))

if not EMAIL or not PASSWORD:
    raise ValueError("Debe especificarse ABBOTT_EMAIL y ABBOTT_PASSWORD en el archivo de configuración")
