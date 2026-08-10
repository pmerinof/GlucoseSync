import os

# Leer credenciales de Abbott desde variables de entorno
EMAIL = os.getenv("ABBOTT_EMAIL")
PASSWORD = os.getenv("ABBOTT_PASSWORD")

if not EMAIL or not PASSWORD:
    raise RuntimeError(
        "No se han configurado las variables de entorno ABBOTT_EMAIL y ABBOTT_PASSWORD"
    )
