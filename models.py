from dataclasses import dataclass
from datetime import datetime

@dataclass
class GlucoseReading:
    """
    Representa una lectura de glucosa con marca temporal.
    """
    timestamp: datetime
    glucose: int
