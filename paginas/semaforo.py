import streamlit as st
import cv2
from ultralytics import YOLO

MODEL_PATH = "modelo/best.pt"
RTSP_URL = "rtsp://admin:Novat3ch@192.168.1.5:554/Streaming/Channels/101"
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

st.title("Semáforo")

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
    mostrar_semaforo(nivel_atencion)

    frame_window.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))





"""import streamlit as st
import cv2
from ultralytics import YOLO

st.title("🚦 Semáforo")

MODEL_PATH = "modelo/best.pt"

@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)

model = load_model()
class_names = model.names 

start = st.button("▶️ Iniciar monitoreo")
stop = st.button("⏹️ Detener monitoreo")

frame_window = st.image([])
semaforo = st.empty()

def mostrar_semaforo(nivel):
    if nivel >= 0.7:
        semaforo.success("🟢 Atención Alta")
    elif nivel >= 0.4:
        semaforo.warning("🟡 Atención Media")
    else:
        semaforo.error("🔴 Atención Baja")


rtsp_url = "rtsp://admin:Novat3ch@192.168.1.5:554/Streaming/Channels/102"
CAMERA_INDEX = 0

if start:

    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        st.error("❌ No se pudo acceder a la cámara")
        st.stop()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

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
                color = (0, 255, 0)
                atentos += 1
            else:
                color = (0, 0, 255)

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(
                frame,
                f"{etiqueta} ({conf:.2f})",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        nivel_atencion = atentos / total if total > 0 else 0

        mostrar_semaforo(nivel_atencion)

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_window.image(frame_rgb)

        if stop:
            break

    cap.release()
    st.info("⏹️ Monitoreo detenido")"""