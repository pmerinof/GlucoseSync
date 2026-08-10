from __future__ import annotations

import sys
import argparse
from datetime import datetime, timedelta

from abbott import AbbottClient
from database import Database
from logger import logger


def seleccionar_lecturas_horarias(lecturas):
    """
    Selecciona una lectura por cada hora.

    Para cada hora del periodo disponible, selecciona la lectura real
    cuyo timestamp esté más próximo a la hora exacta.

    No se generan valores artificiales: siempre se conserva el valor
    de una lectura real obtenida de LibreLinkUp.
    """

    if not lecturas:
        return []

    # Orden cronológico
    lecturas = sorted(lecturas, key=lambda r: r.timestamp)

    seleccionadas = []
    horas_procesadas = set()

    for lectura in lecturas:
        timestamp = lectura.timestamp

        # Redondear conceptualmente la lectura a la hora más cercana.
        # Si está a 30 minutos exactos, se mantiene la hora inferior.
        hora_objetivo = timestamp.replace(
            minute=0,
            second=0,
            microsecond=0,
        )

        minutos_desde_hora = (
            timestamp - hora_objetivo
        ).total_seconds() / 60

        if minutos_desde_hora >= 30:
            hora_objetivo += timedelta(hours=1)

        # Si todavía no tenemos una lectura para esa hora,
        # la guardamos provisionalmente.
        if hora_objetivo not in horas_procesadas:
            seleccionadas.append(lectura)
            horas_procesadas.add(hora_objetivo)

        else:
            # Ya tenemos una lectura asignada a esa hora.
            # Comparamos cuál está más cerca de la hora exacta.
            anterior = seleccionadas[-1]

            distancia_anterior = abs(
                (
                    anterior.timestamp - hora_objetivo
                ).total_seconds()
            )

            distancia_actual = abs(
                (
                    lectura.timestamp - hora_objetivo
                ).total_seconds()
            )

            if distancia_actual < distancia_anterior:
                seleccionadas[-1] = lectura

    return sorted(
        seleccionadas,
        key=lambda r: r.timestamp,
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
        help="No inserta datos en la BD.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra información detallada.",
    )

    args = parser.parse_args()

    logger.info("Iniciando GlucoseSync...")

    db = None

    try:
        db = Database()
        client = AbbottClient()

        # Obtener lecturas disponibles
        lecturas = client.graph()

        if args.verbose:
            logger.info(
                "Lecturas obtenidas de LibreLinkUp: %d",
                len(lecturas),
            )

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

        # Guardar lecturas
        if not args.dry_run and lecturas_horarias:
            db.insert_many(lecturas_horarias)

        # Intentar guardar también la última lectura disponible.
        # Esto permite disponer de la lectura más reciente aunque
        # todavía no corresponda a una hora completa.
        try:
            ultima = client.latest()

            if ultima and not args.dry_run:
                db.insert(ultima)

                logger.info(
                    "Última lectura guardada: %s → %s",
                    ultima.timestamp,
                    ultima.glucose,
                )

        except Exception as e:
            logger.warning(
                "No se pudo obtener la última lectura: %s",
                e,
            )

        if args.dry_run:
            logger.info(
                "Dry-run: no se modificó la base de datos."
            )
        else:
            logger.info(
                "Base de datos actualizada correctamente."
            )

    except Exception:
        logger.exception(
            "Error al descargar o guardar el histórico."
        )
        sys.exit(1)

    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    main()
