import sys
import csv
from pathlib import Path
from datetime import datetime

from database import Database
from logger import logger

def main():
    try:
        db = Database()
    except Exception as e:
        logger.exception("No se pudo conectar a la base de datos")
        sys.exit(1)

    try:
        readings = db.get_all()
        if not readings:
            logger.info("No hay lecturas en la base de datos para exportar.")
            return

        # Asegurar carpeta destino
        out_folder = Path("datos")
        out_folder.mkdir(exist_ok=True)
        csv_path = out_folder / "glucose_history.csv"

        # Escribir CSV
        with csv_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Timestamp", "Fecha", "Hora", "Glucosa"])
            for r in readings:
                ts = r.timestamp
                fecha = ts.strftime("%d/%m/%Y")
                hora = ts.strftime("%H:%M")
                writer.writerow([ts.isoformat(), fecha, hora, r.glucose])

        logger.info("CSV histórico guardado en %s", csv_path)
    except Exception as e:
        logger.exception("Error exportando datos a CSV:")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
