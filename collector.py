#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
from datetime import datetime
import sqlite3

from abbott import AbbottClient
from database import initialize_db, get_connection
from logger import logger

def main():
    parser = argparse.ArgumentParser(
        description="Descarga lecturas de LibreLinkUp y actualiza la base de datos."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="No modifica la base de datos.")
    parser.add_argument("--verbose", action="store_true",
                        help="Muestra información adicional.")
    args = parser.parse_args()

    logger.info("Iniciando sincronización...")

    try:
        # Inicializar BD y obtener conexión
        initialize_db()
        conn = get_connection()
        cur = conn.cursor()

        # Obtener la última marca temporal en la BD (como datetime)
        cur.execute("SELECT MAX(timestamp) FROM glucose")
        result = cur.fetchone()[0]
        ultima_bd = None
        if result:
            try:
                ultima_bd = datetime.fromisoformat(result)
            except ValueError:
                # Si falla el parseo, ignorar
                ultima_bd = None

        # Conectar al API de LibreLinkUp
        client = AbbottClient()

        # Descargar histórico reciente (~12 horas)
        lecturas = client.graph()
        logger.info("Se han descargado %d lecturas del histórico.", len(lecturas))

        if args.verbose:
            for lec in lecturas:
                logger.info("%s -> %d", lec.timestamp.isoformat(sep=' '), lec.glucose)

        # Filtrar lecturas posteriores a la última fecha registrada
        lecturas_nuevas = []
        for lec in lecturas:
            lec_ts = lec.timestamp
            if ultima_bd is None or lec_ts > ultima_bd:
                lecturas_nuevas.append(lec)

        if lecturas_nuevas:
            logger.info("Insertando %d lecturas nuevas en la BD.", len(lecturas_nuevas))
            if not args.dry_run:
                sql = "INSERT OR IGNORE INTO glucose(timestamp, glucose) VALUES (?,?)"
                for lec in lecturas_nuevas:
                    cur.execute(sql, (lec.timestamp.isoformat(), lec.glucose))
        else:
            logger.info("No hay lecturas nuevas para insertar.")

        # Consultar la última lectura puntual (para no perder la más reciente)
        try:
            ultima = client.latest()
            if ultima:
                if args.verbose:
                    logger.info("Última lectura: %s -> %d",
                                ultima.timestamp.isoformat(sep=' '), ultima.glucose)
                # Insertar la última lectura si es posterior
                if (ultima_bd is None or ultima.timestamp > ultima_bd) and not args.dry_run:
                    cur.execute("INSERT OR IGNORE INTO glucose(timestamp, glucose) VALUES (?,?)",
                                (ultima.timestamp.isoformat(), ultima.glucose))
        except Exception as e:
            logger.warning("No se pudo descargar la última lectura: %s", e)

        # Cerrar la BD (commit automático en caso de modificación)
        if not args.dry_run:
            conn.commit()
            logger.info("Base de datos actualizada correctamente.")
        else:
            logger.info("Ejecución de prueba (dry-run) finalizada: no se modificó la base de datos.")

    except Exception as e:
        logger.exception("Error durante la sincronización.")
        sys.exit(1)
    finally:
        # Asegurar cierre de conexión
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    main()
