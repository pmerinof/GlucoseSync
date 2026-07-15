"""
Gestión de la caché local.
"""

import json
from pathlib import Path
from datetime import datetime

from models import GlucoseReading


CACHE_FOLDER = Path("cache")
CACHE_FOLDER.mkdir(exist_ok=True)

CACHE_FILE = CACHE_FOLDER / "history.json"


def save_cache(readings):

    datos = []

    for r in readings:

        datos.append(
            {
                "timestamp": r.timestamp.isoformat(),
                "glucose": r.glucose
            }
        )

    with open(CACHE_FILE, "w", encoding="utf8") as f:

        json.dump(datos, f, indent=4)


def load_cache():

    if not CACHE_FILE.exists():
        return []

    with open(CACHE_FILE, encoding="utf8") as f:

        datos = json.load(f)

    resultado = []

    for d in datos:

        resultado.append(

            GlucoseReading(

                timestamp=datetime.fromisoformat(
                    d["timestamp"]
                ),

                glucose=d["glucose"]
            )

        )

    return resultado