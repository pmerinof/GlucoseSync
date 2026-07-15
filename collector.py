import json, datetime
from config import EMAIL, PASSWORD
from database import get_connection, initialize_db
# Importar el cliente de LibreLinkUp
from libre_link_up import LibreLinkUpClient

def fetch_glucose_data():
    client = LibreLinkUpClient(
        username=EMAIL,
        password=PASSWORD,
        # La URL por región; usar la correcta según Abbott
        url="https://api-eu2.libreview.io",
        version="4.16.0"
    )
    client.login()
    # Obtener múltiples lecturas (por ejemplo, últimas 1-2 semanas)
    data = client.get_reading_history()  # Supongamos que devuelve lista
    return data

def run():
    # Inicializar DB y leer datos
    initialize_db()
    readings = fetch_glucose_data()
    conn = get_connection()
    cur = conn.cursor()
    count = 0
    for entry in readings:
        ts = datetime.datetime.fromtimestamp(entry["unix_timestamp"])
        ts_str = ts.isoformat(sep=' ')
        glucose = int(round(entry["value_in_mg_per_dl"]))
        try:
            cur.execute("INSERT INTO glucose(timestamp, glucose) VALUES (?, ?)", (ts_str, glucose))
            count += 1
        except sqlite3.IntegrityError:
            continue  # ya existía
    conn.commit()
    conn.close()
    print(f"Se agregaron {count} lecturas nuevas.")
    
if __name__ == "__main__":
    run()
