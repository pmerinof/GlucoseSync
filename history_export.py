import csv
import datetime
from config import CSV_PATH
from database import get_connection

def run():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT timestamp, glucose FROM glucose ORDER BY timestamp")
    rows = cur.fetchall()
    conn.close()
    with open(CSV_PATH, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["Timestamp","Fecha","Hora","Glucosa"])
        for ts_str, glucose in rows:
            ts = datetime.datetime.fromisoformat(ts_str)
            fecha = ts.strftime("%d/%m/%Y")
            hora = ts.strftime("%H:%M")
            writer.writerow([ts_str, fecha, hora, glucose])

if __name__ == "__main__":
    run()
