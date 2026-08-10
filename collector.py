#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collector.py: Extrae datos de glucosa desde Abbott LibreLinkUp,
los filtra para conservar solo lecturas nuevas y los inserta en la base SQLite.
"""

import os
from abbott import AbbottClient
import os
import sys

# Importar clases del proyecto
from config import ABBOTT_EMAIL, ABBOTT_PASSWORD
from abbott import Abbott
from database import Database

def main():
    # Configuración básica del logger
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    # Inicializar conexión a la base de datos
    try:
        db = Database()
    except Exception as e:
        logging.error(f"Error al conectar con la base de datos: {e}")
        sys.exit(1)
    db.initialize_db()  # Asegura que existe la tabla (si aplica)

    # Obtener la última fecha registrada en la base de datos
    last_ts = None
    try:
        # Asumimos que Database tiene un método get_last_timestamp() que devuelve un datetime o similar
        last_ts = db.get_last_timestamp()
    except AttributeError:
        # Si no existe, intentamos otros métodos alternativos
        try:
            last_ts = db.get_last_reading_timestamp()
        except Exception:
            # Fallback: consulta manual SQL suponiendo tabla 'readings' con campo 'timestamp'
            try:
                conn = db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(timestamp) FROM readings;")
                row = cursor.fetchone()
                if row:
                    last_ts = row[0]
            except Exception as e:
                logging.warning("No fue posible determinar la última fecha desde la DB: %s", e)
                last_ts = None

    # Normalizar el tipo de last_ts a datetime si es necesario
    if isinstance(last_ts, (int, float)):
        last_ts = datetime.fromtimestamp(last_ts)
    elif isinstance(last_ts, str):
        try:
            last_ts = datetime.fromisoformat(last_ts)
        except ValueError:
            logging.warning("Formato de fecha desconocido para last_ts: %s", last_ts)
            last_ts = None

    if last_ts is None:
        # Si no hay datos previos, asignar una fecha muy antigua
        last_ts = datetime(1970, 1, 1)
        logging.info("No hay lecturas anteriores. Se tomarán todas las lecturas disponibles.")

    # Conectar al servicio de Abbott LibreLinkUp
    try:
        email = os.getenv("ABBOTT_EMAIL")
        password = os.getenv("ABBOTT_PASSWORD")
        client = AbbottClient(email, password)
    except Exception as e:
        logging.error(f"Error al iniciar sesión en LibreLinkUp: {e}")
        sys.exit(1)

    # Obtener el historial completo de lecturas (graph) y la lectura más reciente (latest)
    try:
        readings = abbott.graph()
    except Exception as e:
        logging.error(f"Error al obtener lecturas (graph): {e}")
        readings = []

    try:
        latest_reading = abbott.latest()
    except Exception as e:
        logging.error(f"Error al obtener la última lectura (latest): {e}")
        latest_reading = None

    # Filtrar solo las lecturas posteriores a la última fecha en la base de datos
    nuevas = []
    for r in readings:
        # Extraer timestamp de la lectura (depende del objeto retornado)
        ts = None
        if hasattr(r, 'timestamp'):
            ts = r.timestamp
        elif hasattr(r, 'unix_timestamp'):
            ts = r.unix_timestamp
        elif isinstance(r, dict):
            ts = r.get('timestamp') or r.get('unix_timestamp')
        
        # Convertir ts a datetime
        ts_dt = None
        if isinstance(ts, (int, float)):
            ts_dt = datetime.fromtimestamp(ts)
        elif isinstance(ts, str):
            try:
                ts_dt = datetime.fromisoformat(ts)
            except Exception:
                logging.debug("No se pudo parsear la fecha: %s", ts)
        elif isinstance(ts, datetime):
            ts_dt = ts

        # Si la lectura es más reciente, incluirla
        if ts_dt and ts_dt > last_ts:
            nuevas.append(r)

    # Insertar nuevas lecturas en la base de datos
    if nuevas:
        logging.info(f"Insertando {len(nuevas)} lecturas nuevas.")
        try:
            db.insert_many(nuevas)  # Asumimos que Database soporta insert_many(objetos)
        except AttributeError:
            # Si no existe insert_many, insertar individualmente
            for r in nuevas:
                try:
                    db.insert(r)
                except Exception as e:
                    logging.error(f"Error insertando lectura {r}: {e}")
    else:
        logging.info("No hay nuevas lecturas del historial (graph).")

    # Procesar la lectura "latest": puede ser más reciente que todas las anteriores
    if latest_reading:
        # Misma lógica para obtener ts de latest_reading
        ts = None
        if hasattr(latest_reading, 'timestamp'):
            ts = latest_reading.timestamp
        elif hasattr(latest_reading, 'unix_timestamp'):
            ts = latest_reading.unix_timestamp
        elif isinstance(latest_reading, dict):
            ts = latest_reading.get('timestamp') or latest_reading.get('unix_timestamp')
        
        ts_dt = None
        if isinstance(ts, (int, float)):
            ts_dt = datetime.fromtimestamp(ts)
        elif isinstance(ts, str):
            try:
                ts_dt = datetime.fromisoformat(ts)
            except Exception:
                ts_dt = None
        elif isinstance(ts, datetime):
            ts_dt = ts

        if ts_dt and ts_dt > last_ts:
            logging.info("Insertando lectura más reciente (latest).")
            try:
                db.insert(latest_reading)
            except Exception:
                # Fallback si solo hay insert_many
                try:
                    db.insert_many([latest_reading])
                except Exception as e:
                    logging.error(f"Error insertando la última lectura: {e}")
        else:
            logging.info("La lectura 'latest' no es más reciente que los datos existentes.")

    # Cerrar la base de datos (si hace falta)
    try:
        db.close()
    except Exception:
        pass

if __name__ == "__main__":
    main()
