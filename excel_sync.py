import sys

from database import Database
from excel_writer import ExcelWriter
from logger import logger

def main():
    try:
        db = Database()
        writer = ExcelWriter(db)
        writer.sync()
    except Exception as e:
        logger.exception("Error en la sincronización del Excel:")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
