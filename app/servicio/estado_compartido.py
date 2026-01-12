import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class EstadoCompartido:
    """Estado compartido entre el loop de captura/inferencia y la API.

    - last_jpeg: último frame anotado y codificado en JPEG (bytes). Se usa para streaming eficiente.
    - last_frame_ts: timestamp (time.time()) del último JPEG.
    - metrics: métricas livianas para /metrics.
    """
    frame_lock: threading.Lock = field(default_factory=threading.Lock)
    metrics_lock: threading.Lock = field(default_factory=threading.Lock)
    frame_cv: threading.Condition = field(init=False)

    last_frame: Optional[Any] = None          # frame BGR anotado (solo para depuración)
    last_jpeg: Optional[bytes] = None         # JPEG listo para enviar a clientes
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
        # extras útiles (no rompen lógica; clientes pueden ignorar)
        "fps_stream": 0.0,
        "fps_yolo": 0.0,
        "last_update": ""
    })

    def __post_init__(self):
        self.frame_cv = threading.Condition(self.frame_lock)


STATE = EstadoCompartido()
