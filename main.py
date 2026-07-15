from logger import logger
from abbott import AbbottClient
from database import Database
from excel_writer import ExcelWriter

def main():
    """
    Flujo principal: descarga de lecturas y sincronizaci\u00f3n con Excel.
    """
    db = Database()
    try:
        # Descargar lecturas desde LibreLinkUp
        client = AbbottClient()
        client.connect()
        datos = client.graph()
        logger.info("Guardando %s lecturas en la base de datos...", len(datos))
        db.insert_many(datos)
        try:
            ultima = client.latest()
            logger.info("Agregando \u00faltima lectura a la base de datos.")
            db.insert(ultima)
        except Exception:
            logger.warning("No se pudo obtener la \u00faltima lectura.")

        # Sincronizar con Excel
        writer = ExcelWriter(db)
        writer.sync()

    except Exception as e:
        logger.exception("Error durante la sincronizaci\u00f3n de GlucoseSync:")
    finally:
        db.close()

if __name__ == "__main__":
    main()
