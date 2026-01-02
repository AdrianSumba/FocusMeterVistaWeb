import streamlit as st
import cv2
from ultralytics import YOLO

st.title("📹 Monitoreo en el Servidor")

# =============================
# CONFIGURACIÓN UBUNTU
# =============================
MODEL_PATH = "app/extras/best.pt"

def iniciar_camara_linux():
    # En Linux/Ubuntu, los índices suelen ser 0 (integrada) y 2, 4 o 6 (USB externa)
    # debido a que cada cámara crea múltiples archivos de dispositivo.
    
    for index in [0, 2, 4, 1]: # Orden de prueba
        # CAP_V4L2 es el estándar para Linux
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                return cap, index
            cap.release()
    return None, None

# =============================
# CARGAR MODELO
# =============================
@st.cache_resource
def load_model():
    return YOLO(MODEL_PATH)

model = load_model()
class_names = model.names

# =============================
# INTERFAZ
# =============================
col1, col2 = st.columns(2)
with col1:
    start = st.button("▶️ Iniciar")
with col2:
    stop = st.button("⏹️ Detener")

frame_window = st.image([])
semaforo = st.empty()

# =============================
# BUCLE DE VIDEO
# =============================
if start:
    cap, selected_index = iniciar_camara_linux()

    if cap is None:
        st.error("❌ No se detectó ninguna cámara en el servidor Ubuntu.")
        st.info("Nota: Asegúrate de que el usuario que corre Streamlit tenga permisos sobre /dev/video*")
        st.stop()
    
    st.success(f"🎥 Cámara detectada en índice: {selected_index}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            st.warning("Se perdió la señal de la cámara.")
            break

        # Inferencia YOLO
        results = model(frame, conf=0.5, verbose=False)
        atentos = 0
        total = len(results[0].boxes)

        # Dibujar resultados
        annotated_frame = results[0].plot()

        # Conteo manual para el semáforo
        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            if class_names[cls_id].lower() in ["atento", "attentive"]:
                atentos += 1

        # Lógica de Semáforo
        nivel = atentos / total if total > 0 else 0
        if nivel >= 0.7:
            semaforo.success(f"🟢 Nivel de Atención: {nivel:.0%}")
        elif nivel >= 0.4:
            semaforo.warning(f"🟡 Nivel de Atención: {nivel:.0%}")
        else:
            semaforo.error(f"🔴 Nivel de Atención: {nivel:.0%}")

        # Mostrar en Streamlit
        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        frame_window.image(frame_rgb)

        if stop:
            break

    cap.release()
    st.info("Monitoreo detenido.")