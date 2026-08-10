from __future__ import annotations

import sys
import argparse
from datetime import timedelta

from abbott import AbbottClient
import database
from logger import logger


def seleccionar_lecturas_horarias(lecturas):
    """
    Selecciona una única lectura para cada hora.

    Para cada hora representada en las lecturas obtenidas,
    se selecciona la lectura real cuyo timestamp está más
    próximo a la hora exacta.

    No se generan valores artificiales: siempre se utiliza
    una lectura real procedente de LibreLinkUp.
    """

    if not lecturas:
        return []

    lecturas = sorted(
        lecturas,
        key=lambda r: r.timestamp
    )

    grupos = {}

    for lectura in lecturas:
        timestamp = lectura.timestamp

        # Hora exacta inmediatamente anterior
        hora_base = timestamp.replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        # Distancia respecto a la hora en punto
        distancia_base = abs(
            timestamp - hora_base
        )

        # Distancia respecto a la hora siguiente
        hora_siguiente = hora_base + timedelta(hours=1)

        distancia_siguiente = abs(
            timestamp - hora_siguiente
        )

        # Elegimos la hora en punto más cercana
        if distancia_siguiente < distancia_base:
            hora_objetivo = hora_siguiente
        else:
            hora_objetivo = hora_base

        # Si todavía no hay lectura para esa hora,
        # la guardamos.
        if hora_objetivo not in grupos:
            grupos[hora_objetivo] = lectura
        else:
            # Si ya existe una lectura para esa hora,
            # conservamos la que esté más cerca.
            anterior = grupos[hora_objetivo]

            distancia_anterior = abs(
                anterior.timestamp - hora_objetivo
            )

            distancia_actual = abs(
                lectura.timestamp - hora_objetivo
            )

            if distancia_actual < distancia_anterior:
                grupos[hora_objetivo] = lectura

    return sorted(
        grupos.values(),
        key=lambda r: r.timestamp
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Descarga lecturas de LibreLinkUp y "
            "guarda una lectura por cada hora."
        )
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="No modifica la base de datos.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra información detallada.",
    )

    args = parser.parse_args()

    logger.info("Iniciando GlucoseSync...")

    try:
        # Inicializar la base de datos
        database.initialize_db()

        # Crear cliente de LibreLinkUp
        client = AbbottClient()

        # Descargar histórico disponible
        lecturas = client.graph()

        logger.info(
            "Lecturas obtenidas de LibreLinkUp: %d",
            len(lecturas),
        )

        if not lecturas:
            logger.warning(
                "LibreLinkUp no ha devuelto ninguna lectura."
            )
            return

        # Seleccionar una lectura por hora
        lecturas_horarias = seleccionar_lecturas_horarias(
            lecturas
        )

        logger.info(
            "Lecturas horarias seleccionadas: %d",
            len(lecturas_horarias),
        )

        if args.verbose:
            for lectura in lecturas_horarias:
                logger.info(
                    "Seleccionada: %s → %s",
                    lectura.timestamp,
                    lectura.glucose,
                )

        # Guardar las lecturas seleccionadas
        if not args.dry_run:
            database.insert_many(lecturas_horarias)

            logger.info(
                "Base de datos actualizada correctamente."
            )
        else:
            logger.info(
                "Dry-run: no se modificó la base de datos."
            )

    except Exception:
        logger.exception(
            "Error al descargar o guardar el histórico."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
