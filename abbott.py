from __future__ import annotations

import time
from typing import Callable

from pylibrelinkup import PyLibreLinkUp
from pylibrelinkup.api_url import APIUrl

from config import EMAIL, PASSWORD
from models import GlucoseReading
from logger import logger


class AbbottClient:
    """
    Cliente para la API de LibreLinkUp.
    """

    def __init__(self):
        # España utiliza la API europea de LibreLinkUp.
        self.client = PyLibreLinkUp(
            EMAIL,
            PASSWORD,
            api_url=APIUrl.EU,
        )
        self.patient = None

    def connect(self) -> None:
        """
        Autentica en LibreLinkUp y selecciona el primer paciente disponible.
        """
        logger.info("Autenticando con LibreLinkUp...")

        self.client.authenticate()

        patients = self.client.get_patients()

        if not patients:
            raise RuntimeError(
                "No se encontró ningún paciente en LibreLinkUp."
            )

        self.patient = patients[0]

        logger.info(
            "Paciente seleccionado: %s %s",
            self.patient.first_name,
            self.patient.last_name,
        )

    def _execute(self, func: Callable):
        """
        Ejecuta una operación con reintentos automáticos
        en caso de error temporal.
        """
        ultimo_error = None

        for segundos in (0, 10, 30):
            if segundos:
                logger.warning(
                    "Reintentando en %s segundos...",
                    segundos,
                )
                time.sleep(segundos)

            try:
                self.connect()
                return func()

            except Exception as e:
                ultimo_error = e
                logger.exception(
                    "Error de red/LibreLinkUp:"
                )

        raise ultimo_error

    def latest(self) -> GlucoseReading:
        """
        Obtiene la última lectura de glucosa disponible.
        """

        def tarea():
            data = self.client.latest(self.patient)

            return GlucoseReading(
                timestamp=data.timestamp,
                glucose=int(round(data.value)),
            )

        return self._execute(tarea)

    def graph(self) -> list[GlucoseReading]:
        """
        Descarga el historial reciente (~12 horas)
        desde LibreLinkUp.
        """

        def tarea():
            datos = self.client.graph(self.patient)

            resultado = [
                GlucoseReading(
                    timestamp=d.timestamp,
                    glucose=int(round(d.value)),
                )
                for d in datos
            ]

            resultado.sort(
                key=lambda r: r.timestamp
            )

            logger.info(
                "Descargadas %s lecturas del histórico.",
                len(resultado),
            )

            return resultado

        return self._execute(tarea)
