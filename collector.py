#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
import logging
import sys

from abbott import AbbottClient
from database import (
    get_last_timestamp,
    initialize_db,
    insert_many,
    insert,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)

logger = logging.getLogger("GlucoseSync")


def main():
    logger.info("Iniciando GlucoseSync...")

    try:
        initialize_db()
    except Exception:
        logger.exception("No se pudo inicializar la base de datos.")
        sys.exit(1)

    try:
        last_timestamp = get_last_timestamp()

        if last_timestamp is None:
            logger.info(
                "No hay lecturas anteriores en la base de datos."
            )
        else:
            logger.info(
                "Última lectura almacenada: %s",
                last_timestamp.isoformat(),
            )

    except Exception:
        logger.exception(
            "No se pudo obtener la última lectura almacenada."
        )
        sys.exit(1)

    try:
        client = AbbottClient()
    except Exception:
        logger.exception(
            "No se pudo inicializar el cliente de Abbott."
        )
        sys.exit(1)

    try:
        readings = client.graph()

        if last_timestamp is None:
            nuevas = readings
        else:
            nuevas = [
                reading
                for reading in readings
                if reading.timestamp > last_timestamp
            ]

        if nuevas:
            logger.info(
                "Se han encontrado %d lecturas nuevas.",
                len(nuevas),
            )
            insert_many(nuevas)
        else:
            logger.info(
                "No se han encontrado lecturas nuevas en graph()."
            )

    except Exception:
        logger.exception(
            "Error al descargar o guardar el histórico."
        )
        sys.exit(1)

    try:
        latest = client.latest()

        if last_timestamp is None or latest.timestamp > last_timestamp:
            # Evitar volver a insertar una lectura que ya haya
            # sido introducida mediante graph().
            if not any(
                reading.timestamp == latest.timestamp
                for reading in nuevas
            ):
                logger.info(
                    "Guardando la última lectura: %s",
                    latest.timestamp.isoformat(),
                )
                insert(latest)

    except Exception:
        logger.exception(
            "No se pudo obtener la última lectura."
        )
        sys.exit(1)

    logger.info("GlucoseSync finalizado correctamente.")


# Compatibilidad con main.py
run = main


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
