import streamlit as st
import cv2
from ultralytics import YOLO

st.title("📹 Monitoreo en Tiempo Real")

st.markdown(
    """
    Visualización en tiempo real del nivel de atención estudiantil utilizando
    directamente las predicciones del modelo entrenado.
    """
)

# =============================
# CONFIGURACIÓN
# =============================
MODEL_PATH = "models/best.pt"
CAMERA_INDEX = 0

# =============================
# CARGAR MODELO
# =============================
@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)

model = load_model()
class_names = model.names  # ← CLASES DEL MODELO

# =============================
# CONTROLES
# =============================
start = st.button("▶️ Iniciar monitoreo")
stop = st.button("⏹️ Detener monitoreo")

frame_window = st.image([])
semaforo = st.empty()

# =============================
# SEMÁFORO
# =============================
def mostrar_semaforo(nivel):
    if nivel >= 0.7:
        semaforo.success("🟢 Atención Alta")
    elif nivel >= 0.4:
        semaforo.warning("🟡 Atención Media")
    else:
        semaforo.error("🔴 Atención Baja")

# =============================
# MONITOREO
# =============================
if start:
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        st.error("❌ No se pudo acceder a la cámara")
        st.stop()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # ===== INFERENCIA YOLO =====
        results = model(frame, conf=0.5)
        boxes = results[0].boxes

        atentos = 0
        total = len(boxes)

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            etiqueta = class_names[cls_id]  # ← DEL MODELO

            # Color según clase (AJUSTA nombres si es necesario)
            if etiqueta.lower() in ["atento", "attentive"]:
                color = (0, 255, 0)
                atentos += 1
            else:
                color = (0, 0, 255)

            # ===== DIBUJAR CUADRO =====
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

        # ===== NIVEL DE ATENCIÓN (MODELO) =====
        nivel_atencion = atentos / total if total > 0 else 0

        mostrar_semaforo(nivel_atencion)

        # ===== MOSTRAR VIDEO =====
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_window.image(frame_rgb)

        if stop:
            break

    cap.release()
    st.info("⏹️ Monitoreo detenido")
