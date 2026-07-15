from logger import logger
from collector import main as run_collector
from history_export import main as run_export

def main():
    """
    Flujo principal para entornos locales: descarga datos y exporta CSV.
    """
    try:
        run_collector()
        run_export()
    except Exception:
        logger.exception("Error en el flujo principal de GlucoseSync 2.0")

if __name__ == "__main__":
    main()
