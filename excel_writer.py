from __future__ import annotations
from datetime import datetime, timedelta
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from config import EXCEL_FILE
from database import Database
from logger import logger

class ExcelWriter:
    """
    Maneja la actualización del archivo Excel con lecturas horarias.
    """
    def __init__(self, db: Database):
        self.db = db
        if not Path(EXCEL_FILE).is_file():
            raise FileNotFoundError(f"No se encontró el archivo Excel: {EXCEL_FILE}")
        self.wb = load_workbook(EXCEL_FILE)
        self.sheet = self.wb.active

        # Columna de hora (en el Excel actual se asume que la hora está en la primera columna).
        # Ajustar si es necesario:
        self.time_col = 1

    def sync(self) -> None:
        """
        Sincroniza el Excel agregando filas faltantes por hora.
        Usa last_excel_sync para continuar donde quedó la última vez.
        """
        last_sync = self.db.last_excel_sync()
        all_readings = self.db.get_all()
        if not all_readings:
            logger.info("No hay lecturas en la base de datos para sincronizar.")
            return

        # Determinar hora de inicio
        if last_sync:
            start_time = last_sync + timedelta(hours=1)
        else:
            # Usar la primera lectura disponible como inicio
            start_time = all_readings[0].timestamp.replace(minute=0, second=0, microsecond=0)
        now = datetime.now()
        # Rellenar hasta la hora actual (no completa)
        while start_time <= now:
            # Obtener la lectura más reciente antes o en esta hora
            lectura = self.db.get_last_before(start_time + timedelta(hours=1))
            if lectura:
                # Escribir en Excel: buscar fila correspondiente a start_time
                found = False
                for row in range(2, self.sheet.max_row + 1):
                    cell = self.sheet.cell(row=row, column=self.time_col).value
                    if isinstance(cell, datetime) and cell == start_time:
                        # Asumimos que la glucosa va en columna 2 (B)
                        self.sheet.cell(row=row, column=2, value=lectura.glucose)
                        found = True
                        break
                if not found:
                    # Si la hora no existe en Excel, crear nueva fila al final
                    new_row = self.sheet.max_row + 1
                    self.sheet.cell(row=new_row, column=self.time_col, value=start_time)
                    self.sheet.cell(row=new_row, column=2, value=lectura.glucose)
            start_time += timedelta(hours=1)

        # Guardar y actualizar estado
        self.wb.save(EXCEL_FILE)
        self.db.update_last_excel_sync(datetime.now())
        logger.info("Archivo Excel sincronizado correctamente.")
