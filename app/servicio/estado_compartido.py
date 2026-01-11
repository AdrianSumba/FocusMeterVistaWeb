import threading

class EstadoCompartido:
    def __init__(self):
        self.frame_lock = threading.Lock()
        self.metrics_lock = threading.Lock()

        self.last_frame = None
        self.metrics = {
            "estimacion_atencion": 0,
            "estudiantes_detectados": 0,
            "aula": "",
            "docente": "",
            "materia": "",
            "carrera": "",
            "hora_inicio": "",
            "hora_fin": ""
        }

STATE = EstadoCompartido()
