from openpyxl import load_workbook
from config import EXCEL_FILE
import csv

def run():
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    with open('datos/glucose_history.csv', newline='') as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)  # saltar encabezados
        data = list(reader)
    for row in data:
        # Asignar fila por timestamp/hora o similar
        pass
    wb.save(EXCEL_FILE)

if __name__ == "__main__":
    run()
