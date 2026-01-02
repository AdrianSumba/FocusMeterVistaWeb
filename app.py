import streamlit as st
import cv2
from ultralytics import YOLO

st.title("📹 Monitoreo en Servidor Ubuntu")

# =============================
# LÓGICA DE DETECCIÓN LINUX
# =============================
def encontrar_camara_linux():
    # Probamos los dispositivos detectados en tu comando ls: 2 y 0
    # Usamos CAP_V4L2 que es el driver nativo de Linux
    for index in [2, 0]: 
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
    return YOLO("app/extras/best.pt")

model = load_model()

# =============================
# INTERFAZ Y CONTROL
# =============================
col1, col2 = st.columns(2)
start = col1.button("▶️ Iniciar")
stop = col2.button("⏹️ Detener")

frame_window = st.image([])
status_text = st.empty()

if start:
    cap, idx = encontrar_camara_linux()
    
    if cap is None:
        st.error("❌ No se pudo abrir /dev/video0 ni /dev/video2. Revisa los permisos.")
        st.code("Ejecuta: sudo usermod -aG video $USER (y reinicia sesión)")
        st.stop()
    
    status_text.success(f"🎥 Conectado a: /dev/video{idx}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Inferencia rápida
        results = model(frame, conf=0.5, verbose=False)
        
        # Dibujar resultados automáticamente
        annotated_frame = results[0].plot()

        # Mostrar en Streamlit
        frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        frame_window.image(frame_rgb)

        if stop:
            break

    cap.release()
    status_text.info("⏹️ Monitoreo detenido.")