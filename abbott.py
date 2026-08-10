from __future__ import annotations
import time
from typing import Callable, TypeVar

from pylibrelinkup import PyLibreLinkUp
from config import EMAIL, PASSWORD
from models import GlucoseReading
from logger import logger

class AbbottClient:
    """
    Cliente para la API de LibreLinkUp.
    """

    def __init__(self):
        self.client = PyLibreLinkUp(EMAIL, PASSWORD)
        self.patient = None

    def connect(self) -> None:
        """
        Autentica en LibreLinkUp y selecciona el primer paciente disponible.
        """
        logger.info("Autenticando con LibreLinkUp...")
        self.client.authenticate()
        patients = self.client.get_patients()
        if not patients:
            raise RuntimeError("No se encontró ningún paciente en LibreLinkUp.")
        self.patient = patients[0]
        logger.info(
            "Paciente seleccionado: %s %s",
            self.patient.first_name, self.patient.last_name
        )

    from typing import Callable, TypeVar

    T = TypeVar("T")

    def _execute(self, func: Callable[[], T]) -> T:
        """
        Ejecuta una operación con reintentos automáticos en caso de error temporal.
        """
        if self.patient is None:
            self.connect()

        ultimo_error = None

        for segundos in (0, 10, 30):
            if segundos:
                logger.warning("Reintentando en %s segundos...", segundos)
                time.sleep(segundos)
            try:
                return func()
            except Exception as e:
                ultimo_error = e
                logger.exception("Error de red/LibreLinkUp:")
        raise ultimo_error

    def latest(self) -> GlucoseReading:
        """
        Obtiene la última lectura de glucosa disponible.
        """
        def tarea():
            data = self.client.latest(self.patient)
            return GlucoseReading(timestamp=data.timestamp, glucose=int(round(data.value)))
        return self._execute(tarea)

    def graph(self) -> list[GlucoseReading]:
        """
        Descarga el historial reciente (~12 horas) desde LibreLinkUp.
        Si hay error de red, propaga la excepción para manejarlo en caller.
        """
        def tarea():
            datos = self.client.graph(self.patient)
            resultado = [
                GlucoseReading(timestamp=d.timestamp, glucose=int(round(d.value)))
                for d in datos
            ]
            # Ordenar cronológicamente (de menor a mayor timestamp)
            resultado.sort(key=lambda r: r.timestamp)
            logger.info("Descargadas %s lecturas del hist\u00f3rico.", len(resultado))
            return resultado
        return self._execute(tarea)
