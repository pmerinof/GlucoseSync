import sys
import argparse
from datetime import datetime, timedelta
import time

from abbott import AbbottClient
from database import Database
from logger import logger

def main():
    parser = argparse.ArgumentParser(description="Descarga lecturas de LibreLinkUp y actualiza la base de datos.")
    parser.add_argument("--dry-run", action="store_true", help="No inserta en BD, sólo simula.")
    parser.add_argument("--verbose", action="store_true", help="Muestra información detallada.")
    args = parser.parse_args()

    try:
        db = Database()
        client = AbbottClient()
        client.connect()
    except Exception as e:
        logger.exception("No se pudo inicializar el cliente o la base de datos")
        sys.exit(1)

    try:
        # Descargar lecturas de las últimas ~12 horas
        datos = client.graph()
        if args.verbose:
            logger.info("Lecturas obtenidas: %d", len(datos))
        if not args.dry_run:
            db.insert_many(datos)
        try:
            ultima = client.latest()
            if ultima:
                if args.verbose:
                    logger.info("Insertando última lectura: %s", ultima)
                if not args.dry_run:
                    db.insert(ultima)
        except Exception as e:
            logger.warning("No se pudo obtener la última lectura: %s", e)

        if not args.dry_run:
            db.close()
            logger.info("Base de datos actualizada con éxito.")
        else:
            logger.info("Dry-run: no se modificó la base de datos.")
    except Exception as e:
        logger.exception("Error durante la descarga de lecturas:")
        sys.exit(1)

if __name__ == "__main__":
    main()
