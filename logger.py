import logging
from pathlib import Path

# Crear directorio de logs si no existe
Path("logs").mkdir(exist_ok=True)

def create_logger():
    """
    Configura y devuelve un logger que escribe en pantalla y en archivo.
    """
    logger = logging.getLogger("GlucoseSync")
    logger.setLevel(logging.INFO)

    # Formato de log
    formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")

    # Handler para archivo
    fh = logging.FileHandler("logs/glucosesync.log", encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Handler para consola
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

# Instancia de logger compartida
logger = create_logger()
