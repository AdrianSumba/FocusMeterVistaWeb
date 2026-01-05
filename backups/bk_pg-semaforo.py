import streamlit as st
import cv2
from ultralytics import YOLO
import serial
import time


st.title("🚦 Semáforo")


PUERTO_SEMAFORO = "/dev/ttyACM0"
BAUDIOS = 115200
comunicacion_serial = None

MODEL_PATH = "modelo/best.pt"

RTSP_URL = "rtsp://admin:Novat3ch@192.168.137.35:554/Streaming/Channels/101"
CAMERA_INDEX = 0


@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)

def open_camera():
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(CAMERA_INDEX)
    return cap if cap.isOpened() else None

def mostrar_semaforo(nivel):
    if nivel >= 0.7:
        semaforo.success("Atención Alta")
    elif nivel >= 0.4:
        semaforo.warning("Atención Media")
    else:
        semaforo.error("Atención Baja")

model = load_model()
class_names = model.names


if "running" not in st.session_state:
    st.session_state.running = False
    st.session_state.cap = None

if st.button("Iniciar monitoreo"):
    st.session_state.running = True
    if st.session_state.cap is None:
        st.session_state.cap = open_camera()

if st.button("Detener monitoreo"):
    st.session_state.running = False
    if st.session_state.cap:
        st.session_state.cap.release()
        st.session_state.cap = None

frame_window = st.image([])
semaforo = st.empty()

while st.session_state.running:
    cap = st.session_state.cap

    if cap is None:
        st.error("No se pudo acceder a la cámara")
        st.stop()

    ret, frame = cap.read()
    if not ret:
        st.error("Error al leer frame")
        st.stop()

    results = model(frame, conf=0.5)
    boxes = results[0].boxes

    atentos = 0
    total = len(boxes)

    for box in boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        etiqueta = class_names[cls_id]

        if etiqueta.lower() in ["atento", "attentive"]:
            atentos += 1
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f"{etiqueta} ({conf:.2f})",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    nivel_atencion = atentos / total if total else 0

    if comunicacion_serial is None:
        try:
            comunicacion_serial = serial.Serial(PUERTO_SEMAFORO, BAUDIOS, timeout=1)
            time.sleep(2)
        except serial.SerialException:
            comunicacion_serial = None
            time.sleep(1)
            continue

    if "ultimo_envio" not in st.session_state:
        st.session_state.ultimo_envio = 0.0

    try:
        ahora = time.time()

        if ahora - st.session_state.ultimo_envio >= 4:
            mensaje = f"<{nivel_atencion}>\n"
            comunicacion_serial.write(mensaje.encode())
            print(f"Enviado a Arduino: {nivel_atencion}")
            st.session_state.ultimo_envio = ahora
    except serial.SerialException:
        try:
            comunicacion_serial.close()
        except Exception:
            pass
        comunicacion_serial = None

    mostrar_semaforo(nivel_atencion)
    frame_window.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))