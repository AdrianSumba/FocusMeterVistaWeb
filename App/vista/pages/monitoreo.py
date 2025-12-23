import streamlit as st
import requests
import cv2
import numpy as np

API_URL = "http://localhost:8000"

st.title("Monitoreo en Tiempo Real")

start = st.button("Iniciar monitoreo")
stop = st.button("Detener monitoreo")

frame_window = st.image([])
semaforo = st.empty()

def mostrar_semaforo(nivel):
    if nivel >= 0.7:
        semaforo.success("Atención Alta")
    elif nivel >= 0.4:
        semaforo.warning("Atención Media")
    else:
        semaforo.error("Atención Baja")

if start:
    while True:
        nivel = requests.get(f"{API_URL}/estimacion_atencion").json()["estimacion_atencion"]
        mostrar_semaforo(nivel)

        resp = requests.get(f"{API_URL}/frame")
        if resp.content:
            frame = np.frombuffer(resp.content, np.uint8)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_window.image(frame)

        if stop:
            break
