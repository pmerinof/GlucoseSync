import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

EMAIL = os.getenv("ABBOTT_EMAIL", "")
PASSWORD = os.getenv("ABBOTT_PASSWORD", "")
# Ruta del archivo Excel (por defecto 'datos/glucosa.xlsx')
EXCEL_FILE = Path(os.getenv("EXCEL_FILE", "datos/glucosa.xlsx"))

if not EMAIL or not PASSWORD:
    raise ValueError(
        "Debe especificarse ABBOTT_EMAIL y ABBOTT_PASSWORD en el archivo .env"
    )
