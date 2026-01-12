import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class EstadoCompartido:
    frame_lock: threading.Lock = field(default_factory=threading.Lock)
    metrics_lock: threading.Lock = field(default_factory=threading.Lock)
    frame_cv: threading.Condition = field(init=False)

    last_frame: Optional[Any] = None
    last_jpeg: Optional[bytes] = None
    last_frame_ts: float = 0.0

    metrics: Dict[str, Any] = field(default_factory=lambda: {
        "estimacion_atencion": 0,
        "estudiantes_detectados": 0,
        "aula": "",
        "docente": "",
        "materia": "",
        "carrera": "",
        "hora_inicio": "",
        "hora_fin": "",
    })

    def __post_init__(self):
        self.frame_cv = threading.Condition(self.frame_lock)


STATE = EstadoCompartido()
