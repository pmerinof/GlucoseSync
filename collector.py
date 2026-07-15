import sys
import argparse

from abbott import AbbottClient
from database import Database
from logger import logger


def main():
    parser = argparse.ArgumentParser(
        description="Descarga lecturas de LibreLinkUp y actualiza la base de datos."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No modifica la base de datos."
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra información adicional."
    )

    args = parser.parse_args()

    db = None

    try:
        logger.info("Iniciando sincronización...")

        db = Database()

        client = AbbottClient()

        # Descarga el histórico (~12 horas)
        lecturas = client.graph()

        logger.info(
            "Se han descargado %d lecturas.",
            len(lecturas)
        )

        if args.verbose:
            for lectura in lecturas:
                logger.info(
                    "%s -> %d",
                    lectura.timestamp,
                    lectura.glucose
                )

        if not args.dry_run:
            db.insert_many(lecturas)

        # Última lectura (por si todavía no aparece en graph)
        try:
            ultima = client.latest()

            if args.verbose:
                logger.info(
                    "Última lectura: %s -> %d",
                    ultima.timestamp,
                    ultima.glucose
                )

            if not args.dry_run:
                db.insert(ultima)

        except Exception as e:
            logger.warning(
                "No se pudo descargar la última lectura: %s",
                e
            )

        if args.dry_run:
            logger.info("Ejecución de prueba finalizada.")
        else:
            logger.info("Base de datos actualizada correctamente.")

    except Exception:
        logger.exception("Error durante la sincronización.")
        sys.exit(1)

    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    main()
