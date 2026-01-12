import threading
import time
import traceback
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

import cv2

from servicio.camara import open_rtsp, open_usb_or_integrated, safe_rtsp_read
from servicio.estado_compartido import STATE
from servicio.com_serial import SerialManager
from bd.mongo import insertar_registro_atencion, get_info_horario_actual
from servicio.modelo_manager import cargar_modelo, PESOS_ATENCION, nuevo_intervalo, actualizar_intervalo
from servicio.evidencias import guardar_evidencia


# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────
RECONNECT_DELAY = 1.5
STREAM_RES = (640, 480)   # (w, h)

ID_AULA = "694c11148cd1e969b0edc8a0"

YOLO_FPS = 5
YOLO_INTERVAL = 1.0 / YOLO_FPS

STREAM_FPS = 25
STREAM_INTERVAL = 1.0 / STREAM_FPS

JPEG_QUALITY = 75

SERIAL_INTERVAL_YOLO_TICKS = 5  # aprox cada 1s si YOLO_FPS=5


# ──────────────────────────────────────────────────────────────────────────────
# Runtime singleton
# ──────────────────────────────────────────────────────────────────────────────
_runtime_lock = threading.Lock()
_runtime_started = False


BoxT = Tuple[int, int, int, int, str, float]  # x1,y1,x2,y2,label,peso


class FocusMeterRuntime:
    def __init__(self):
        self.stop_event = threading.Event()

        self.cap = None  # cv2.VideoCapture

        self.latest_lock = threading.Lock()
        self.latest_frame = None  # BGR frame raw (puede ser alta resolución)
        self.latest_frame_ts = 0.0

        self.det_lock = threading.Lock()
        self.last_boxes: List[BoxT] = []
        self.last_attention: float = 0.0
        self.last_total: int = 0
        self.last_counts: Dict[str, int] = {}
        self.last_yolo_ts: float = 0.0

        self.model = None
        self.class_names = None

        self.serial_mgr = SerialManager()

        # Intervalo de 60s para almacenamiento
        now = datetime.now()
        self.interval_start_ts = time.time()
        self.interval_data = nuevo_intervalo(now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))
        self.info_horario_actual: Optional[Dict[str, Any]] = None
        self._last_hora_slot = now.strftime("%H:00")

        # FPS internos
        self._stream_frames = 0
        self._stream_fps_ts = time.time()
        self._yolo_ticks = 0
        self._yolo_fps_ts = time.time()

    # ────────────── lifecycle ──────────────
    def start(self):
        print("[INIT] Iniciando FocusMeterRuntime optimizado")

        self.model, self.class_names = cargar_modelo()
        if self.model is None:
            raise RuntimeError("No se pudo cargar el modelo YOLO")

        print("[INIT] Modelo YOLO cargado")

        # Serial (si no existe, el proyecto igual funciona)
        try:
            self.serial_mgr.connect()
        except Exception:
            pass

        # Horario inicial (se usa para enriquecer metrics y para id_horario)
        self._refresh_horario(force=True)

        # Hilos
        threading.Thread(target=self._capture_loop, daemon=True).start()
        threading.Thread(target=self._yolo_loop, daemon=True).start()
        threading.Thread(target=self._encode_stream_loop, daemon=True).start()

    # ────────────── helpers ──────────────
    def _open_camera(self):
        """Intenta RTSP primero; si falla, usa cámara USB/integrada."""
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        self.cap = None

        try:
            print("[CAMARA] Intentando RTSP...")
            cap = open_rtsp()
            print("[CAMARA] RTSP conectado")
            self.cap = cap
            return
        except Exception:
            print("[CAMARA] RTSP no disponible, usando USB/integrada...")

        cap = open_usb_or_integrated()
        self.cap = cap
        print("[CAMARA] Cámara USB/integrada conectada")

        # Intentar fijar resolución para evitar resize costoso (si el driver lo permite)
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, STREAM_RES[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, STREAM_RES[1])
        except Exception:
            pass

    def _refresh_horario(self, force: bool = False):
        now = datetime.now()
        hora_slot = now.strftime("%H:00")
        if (not force) and (hora_slot == self._last_hora_slot):
            return

        self._last_hora_slot = hora_slot
        info = get_info_horario_actual(ID_AULA)
        self.info_horario_actual = info

        if info:
            with STATE.metrics_lock:
                STATE.metrics.update({
                    "aula": info.get("aula", ""),
                    "docente": info.get("docente", ""),
                    "materia": info.get("materia", ""),
                    "carrera": info.get("carrera", ""),
                    "hora_inicio": info.get("hora_inicio", ""),
                    "hora_fin": info.get("hora_fin", ""),
                })

    # ────────────── loops ──────────────
    def _capture_loop(self):
        """Captura frames lo más rápido posible y guarda solo el más reciente."""
        while not self.stop_event.is_set():
            try:
                if self.cap is None or not self.cap.isOpened():
                    self._open_camera()

                if self.cap is None:
                    time.sleep(RECONNECT_DELAY)
                    continue

                # Intento de lectura con timeout (sirve para RTSP y para USB también)
                ok, frame = safe_rtsp_read(self.cap)
                if not ok or frame is None:
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                    self.cap = None
                    time.sleep(RECONNECT_DELAY)
                    continue

                with self.latest_lock:
                    self.latest_frame = frame
                    self.latest_frame_ts = time.time()

            except Exception:
                traceback.print_exc()
                try:
                    if self.cap:
                        self.cap.release()
                except Exception:
                    pass
                self.cap = None
                time.sleep(RECONNECT_DELAY)

    def _yolo_loop(self):
        """Ejecuta YOLO a YOLO_FPS sobre un frame redimensionado (STREAM_RES)."""
        yolo_tick = 0
        while not self.stop_event.is_set():
            t0 = time.time()
            try:
                self._refresh_horario()

                with self.latest_lock:
                    frame = None if self.latest_frame is None else self.latest_frame.copy()

                if frame is None:
                    time.sleep(0.01)
                    continue

                frame_rs = cv2.resize(frame, STREAM_RES)

                results = self.model(frame_rs, conf=0.5, verbose=False)
                boxes = results[0].boxes

                total = len(boxes)
                suma = 0.0
                conteo: Dict[str, int] = {}
                box_list: List[BoxT] = []

                for box in boxes:
                    cls = int(box.cls[0])
                    label = self.class_names[cls].lower()
                    conteo[label] = conteo.get(label, 0) + 1
                    peso = float(PESOS_ATENCION.get(label, 0.0))
                    suma += peso

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    box_list.append((x1, y1, x2, y2, label, peso))

                estimacion = (suma / total * 100) if total > 0 else 0.0

                with self.det_lock:
                    self.last_boxes = box_list
                    self.last_attention = float(estimacion)
                    self.last_total = int(total)
                    self.last_counts = conteo
                    self.last_yolo_ts = time.time()

                actualizar_intervalo(self.interval_data, total, estimacion, conteo)

                with STATE.metrics_lock:
                    STATE.metrics["estimacion_atencion"] = round(estimacion, 2)
                    STATE.metrics["estudiantes_detectados"] = int(total)
                    STATE.metrics["last_update"] = datetime.now().isoformat(timespec="seconds")

                yolo_tick += 1
                if yolo_tick % SERIAL_INTERVAL_YOLO_TICKS == 0:
                    try:
                        self.serial_mgr.send(estimacion)
                    except Exception:
                        pass

                if time.time() - self.interval_start_ts >= 60:
                    self._close_interval(frame_rs)

                # FPS yolo
                self._yolo_ticks += 1
                now = time.time()
                if now - self._yolo_fps_ts >= 2.0:
                    fps = self._yolo_ticks / (now - self._yolo_fps_ts)
                    with STATE.metrics_lock:
                        STATE.metrics["fps_yolo"] = round(fps, 2)
                    self._yolo_ticks = 0
                    self._yolo_fps_ts = now

            except Exception:
                traceback.print_exc()

            dt = time.time() - t0
            sleep = YOLO_INTERVAL - dt
            if sleep > 0:
                time.sleep(sleep)

    def _close_interval(self, frame_for_evidence):
        """Calcula agregados del último minuto y guarda evidencia + Mongo."""
        try:
            now = datetime.now()
            timestamp = now.strftime("%Y%m%d_%H%M%S")

            with STATE.metrics_lock:
                att = STATE.metrics.get("estimacion_atencion", 0)
                det = STATE.metrics.get("estudiantes_detectados", 0)

            try:
                guardar_evidencia(
                    frame_for_evidence.copy(),
                    f"Atencion: {att}%  |  Estudiantes: {det}",
                    timestamp
                )
            except Exception:
                pass

            if self.interval_data["atencion_list"]:
                atencion_prom = sum(self.interval_data["atencion_list"]) / len(self.interval_data["atencion_list"])
            else:
                atencion_prom = 0.0
            num_est_max = max(self.interval_data["estudiantes_list"]) if self.interval_data["estudiantes_list"] else 0
            res_num_det = {k: (max(v) if v else 0) for k, v in self.interval_data["etiquetas_conteos"].items()}

            doc = {
                "num_estudiantes_detectados": int(num_est_max),
                "porcentaje_estimado_atencion": round(float(atencion_prom), 2),
                "num_deteccion_etiquetas": res_num_det,
                "fecha_deteccion": self.interval_data["inicio_fecha"],
                "hora_detecccion": self.interval_data["inicio_hora"],
                "id_horario": (self.info_horario_actual.get("id_horario") if self.info_horario_actual else "")
            }

            try:
                insertar_registro_atencion(doc)
            except Exception:
                pass

        finally:
            self.interval_start_ts = time.time()
            now = datetime.now()
            self.interval_data = nuevo_intervalo(now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S"))

    def _encode_stream_loop(self):
        """Construye el frame anotado + JPEG una sola vez y lo comparte con todos los clientes."""
        while not self.stop_event.is_set():
            t0 = time.time()
            try:
                with self.latest_lock:
                    frame = None if self.latest_frame is None else self.latest_frame.copy()

                if frame is None:
                    time.sleep(0.01)
                    continue

                frame_rs = cv2.resize(frame, STREAM_RES)

                with self.det_lock:
                    boxes = list(self.last_boxes)
                    att = float(self.last_attention)
                    total = int(self.last_total)

                for (x1, y1, x2, y2, label, peso) in boxes:
                    color = (0, 255, 0) if peso >= 0.7 else (255, 255, 0) if peso >= 0.3 else (0, 0, 255)
                    cv2.rectangle(frame_rs, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame_rs, label, (x1, max(15, y1 - 5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

                cv2.putText(frame_rs, f"Atencion: {att:.1f}%  Estudiantes: {total}",
                            (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                ok, buf = cv2.imencode(".jpg", frame_rs, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                if ok:
                    jpeg = buf.tobytes()
                    with STATE.frame_cv:
                        STATE.last_frame = frame_rs
                        STATE.last_jpeg = jpeg
                        STATE.last_frame_ts = time.time()
                        STATE.frame_cv.notify_all()

                    self._stream_frames += 1
                    now = time.time()
                    if now - self._stream_fps_ts >= 2.0:
                        fps = self._stream_frames / (now - self._stream_fps_ts)
                        with STATE.metrics_lock:
                            STATE.metrics["fps_stream"] = round(fps, 2)
                        self._stream_frames = 0
                        self._stream_fps_ts = now

            except Exception:
                traceback.print_exc()

            dt = time.time() - t0
            sleep = STREAM_INTERVAL - dt
            if sleep > 0:
                time.sleep(sleep)


def start_model_loop():
    """Arranca el runtime una sola vez (idempotente)."""
    global _runtime_started
    with _runtime_lock:
        if _runtime_started:
            return
        _runtime_started = True

    runtime = FocusMeterRuntime()
    runtime.start()
