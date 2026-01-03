import streamlit as st
import cv2
import threading
from ultralytics import YOLO
import time

# =============================
# PROCESADOR PERSISTENTE (HILO ÚNICO)
# =============================
class BackgroundMonitor:
    def __init__(self, index):
        self.cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        self.model = YOLO("app/extras/best.pt")
        self.frame = None
        self.nivel_atencion = 0
        self.is_analyzing = True # Siempre analizando
        self.lock = threading.Lock()
        
        # Iniciar el hilo inmediatamente al crear el objeto
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        while self.is_analyzing:
            start_time = time.time()
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(1) # Reintento si falla la cámara
                continue

            # --- ESTO CORRE SIEMPRE EN EL SERVIDOR ---
            results = self.model(frame, conf=0.5, verbose=False)
            
            # Lógica de atención
            boxes = results[0].boxes
            total = len(boxes)
            atentos = sum(1 for b in boxes if self.model.names[int(b.cls[0])].lower() in ["atento", "attentive"])
            
            actual_nivel = atentos / total if total > 0 else 0

            # AQUÍ IRÍA TU LÓGICA DE BASE DE DATOS (ej. MongoDB)
            # self.save_to_db(actual_nivel)

            with self.lock:
                self.nivel_atencion = actual_nivel
                # Solo procesamos la imagen si es necesario para ahorrar CPU
                # pero el cálculo del nivel ya se hizo arriba.
                self.frame = cv2.cvtColor(results[0].plot(), cv2.COLOR_BGR2RGB)

            # Control de FPS para no saturar el servidor (20 FPS)
            time.sleep(max(0, 0.05 - (time.time() - start_time)))

# =============================
# INICIALIZACIÓN (SOLO UNA VEZ)
# =============================
@st.cache_resource
def start_persistent_monitor():
    # Intentar índices 2 y 0
    for idx in [2, 0]:
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if cap.isOpened():
            cap.release()
            return BackgroundMonitor(idx)
    return None

# El monitor se inicia en cuanto arranca Streamlit, sin esperar botones
monitor = start_persistent_monitor()

# =============================
# INTERFAZ DE VISTA (STREAMLIT)
# =============================
st.title("📹 Sistema de Monitoreo Persistente")

if "show_view" not in st.session_state:
    st.session_state.show_view = False

col1, col2 = st.columns(2)

# Los botones ahora solo controlan la VISTA, no el PROCESAMIENTO
if col1.button("👁️ Ver Monitoreo"):
    st.session_state.show_view = True

if col2.button("🚫 Ocultar Vista"):
    st.session_state.show_view = False

# Espacios para la interfaz
frame_window = st.image([])
semaforo = st.empty()
info_status = st.sidebar.empty()

# Mostrar estado permanente en la barra lateral
with info_status.container():
    st.write("🛰️ **Estado del Servidor:** Ejecutando análisis")
    with monitor.lock:
        st.metric("Nivel Actual", f"{monitor.nivel_atencion:.0%}")

# --- LÓGICA DE VISUALIZACIÓN ---
if st.session_state.show_view:
    while st.session_state.show_view:
        with monitor.lock:
            img = monitor.frame
            nivel = monitor.nivel_atencion

        if img is not None:
            frame_window.image(img, use_container_width=True)
            
            if nivel >= 0.7: semaforo.success(f"🟢 Atención Alta: {nivel:.0%}")
            elif nivel >= 0.4: semaforo.warning(f"🟡 Atención Media: {nivel:.0%}")
            else: semaforo.error(f"🔴 Atención Baja: {nivel:.0%}")
        
        time.sleep(0.05) # Freno para la interfaz web
else:
    frame_window.empty()
    semaforo.info("Análisis en segundo plano activo. Presiona 'Ver Monitoreo' para visualizar.")