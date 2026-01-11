import cv2
import time
import traceback
import sys
from datetime import datetime

from servicio.camara import open_rtsp, open_usb_or_integrated, safe_rtsp_read
from servicio.estado_compartido import STATE
from servicio.com_serial import SerialManager
from bd.mongo import insertar_registro_atencion, get_info_horario_actual
from servicio.modelo_manager import cargar_modelo, procesar_detecciones, nuevo_intervalo, actualizar_intervalo
from servicio.evidencias import guardar_evidencia


RECONNECT_DELAY = 1.5
STREAM_RES = (640, 480)
ID_AULA = "694c11148cd1e969b0edc8a0"

YOLO_FPS = 5
YOLO_INTERVAL = 1.0 / YOLO_FPS
SERIAL_INTERVAL_FRAMES = 5

info_horario_actual = None
hora_nueva_clase = None


def start_model_loop():
    global info_horario_actual, hora_nueva_clase

    print("[INIT] Iniciando monitoreo de cámara")

    ahora_dt = datetime.now()
    hora_nueva_clase = ahora_dt.strftime("%H:00")
    info_horario_actual = get_info_horario_actual(ID_AULA)

    # ───── Métricas iniciales ─────
    if info_horario_actual:
        with STATE.metrics_lock:
            STATE.metrics.update({
                "aula": info_horario_actual.get("aula", ""),
                "docente": info_horario_actual.get("docente", ""),
                "materia": info_horario_actual.get("materia", ""),
                "carrera": info_horario_actual.get("carrera", ""),
                "hora_inicio": info_horario_actual.get("hora_inicio", ""),
                "hora_fin": info_horario_actual.get("hora_fin", "")
            })

    model, class_names = cargar_modelo()
    if model is None:
        return

    print("[INIT] Modelo YOLO cargado")

    cap = None
    serial_mgr = SerialManager()
    frame_count = 0
    last_yolo_time = time.time()
    camera_mode = None  # "RTSP" o "USB"

    start_time_interval = time.time()
    interval_data = nuevo_intervalo(
        ahora_dt.strftime("%Y-%m-%d"),
        ahora_dt.strftime("%H:%M:%S")
    )

    while True:
        try:
            ahora_dt = datetime.now()
            hora_actual_str = ahora_dt.strftime("%H:00")

            # ───── Cambio de clase ─────
            if hora_actual_str != hora_nueva_clase:
                info_horario_actual = get_info_horario_actual(ID_AULA)
                hora_nueva_clase = hora_actual_str

                if info_horario_actual:
                    with STATE.metrics_lock:
                        STATE.metrics.update({
                            "aula": info_horario_actual.get("aula", ""),
                            "docente": info_horario_actual.get("docente", ""),
                            "materia": info_horario_actual.get("materia", ""),
                            "carrera": info_horario_actual.get("carrera", ""),
                            "hora_inicio": info_horario_actual.get("hora_inicio", ""),
                            "hora_fin": info_horario_actual.get("hora_fin", "")
                        })

            # ───── Conectar cámara ─────
            if cap is None:
                if camera_mode is None: 
                    try:
                        print("[CAMARA] Intentando RTSP...")
                        cap = open_rtsp()
                        camera_mode = "RTSP"
                        print("[CAMARA] RTSP conectado")
                    except Exception:
                        print("[CAMARA] RTSP no disponible, usando USB/integrada...")
                        cap = open_usb_or_integrated()
                        camera_mode = "USB"
                        print("[CAMARA] Cámara USB/integrada conectada")
                else:  
                    if camera_mode == "RTSP":
                        cap = open_rtsp()
                        print("[CAMARA] Reconectando RTSP")
                    else:
                        cap = open_usb_or_integrated()
                        print("[CAMARA] Reconectando cámara USB/integrada")

                interval_data["inicio_fecha"] = ahora_dt.strftime("%Y-%m-%d")
                interval_data["inicio_hora"] = ahora_dt.strftime("%H:%M:%S")

            # ───── Leer frame ─────
            ret, frame = safe_rtsp_read(cap)
            if not ret:
                print("[CAMARA] Timeout, reconectando...")
                cap.release()
                cap = None
                time.sleep(RECONNECT_DELAY)
                continue

            # ───── Actualizar último frame para streaming ─────
            with STATE.frame_lock:
                STATE.last_frame = cv2.resize(frame, STREAM_RES)

            # ───── YOLO (solo cada YOLO_INTERVAL segundos) ─────
            if time.time() - last_yolo_time >= YOLO_INTERVAL:
                results = model(frame, conf=0.5, verbose=False)
                boxes = results[0].boxes

                estimacion_iap, total_detectados, conteo_frame = procesar_detecciones(
                    boxes, class_names, frame
                )

                actualizar_intervalo(
                    interval_data,
                    total_detectados,
                    estimacion_iap,
                    conteo_frame
                )

                # ───── Estado compartido (métricas) ─────
                with STATE.metrics_lock:
                    STATE.metrics["estimacion_atencion"] = round(estimacion_iap, 2)
                    STATE.metrics["estudiantes_detectados"] = total_detectados

                # ───── Serial cada SERIAL_INTERVAL_FRAMES ─────
                if frame_count % SERIAL_INTERVAL_FRAMES == 0:
                    serial_mgr.send(estimacion_iap)

                last_yolo_time = time.time()

            # ───── Cierre de intervalo (60s) ─────
            if time.time() - start_time_interval >= 60:
                timestamp = ahora_dt.strftime("%Y%m%d_%H%M%S")

                guardar_evidencia(
                    frame,
                    f"Atencion: {STATE.metrics.get('estimacion_atencion', 0)}% | Estudiantes: {STATE.metrics.get('estudiantes_detectados', 0)}",
                    timestamp
                )

                atencion_prom = sum(interval_data["atencion_list"]) / len(interval_data["atencion_list"])
                num_est_max = max(interval_data["estudiantes_list"])
                res_num_det = {
                    k: max(v) for k, v in interval_data["etiquetas_conteos"].items()
                }

                documento = {
                    "num_estudiantes_detectados": num_est_max,
                    "porcentaje_estimado_atencion": round(atencion_prom, 2),
                    "num_deteccion_etiquetas": res_num_det,
                    "fecha_deteccion": interval_data["inicio_fecha"],
                    "hora_detecccion": interval_data["inicio_hora"],
                    "id_horario": info_horario_actual["id_horario"] if info_horario_actual else ""
                }

                insertar_registro_atencion(documento)

                start_time_interval = time.time()
                interval_data = nuevo_intervalo(
                    ahora_dt.strftime("%Y-%m-%d"),
                    ahora_dt.strftime("%H:%M:%S")
                )

                sys.stdout.write("\033[H\033[J")

            frame_count += 1
            time.sleep(0.01)

        except Exception:
            traceback.print_exc()
            if cap:
                cap.release()
            cap = None
            time.sleep(RECONNECT_DELAY)
