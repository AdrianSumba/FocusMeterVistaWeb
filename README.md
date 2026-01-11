# PROYECTO FINAL CICLO 4: FOCUS METER

- Entorno python: focusmeterv2 con python 3.10.19

- Ejecutar servicio:
    - cd app
    - uvicorn main_servicio_app:app --host 0.0.0.0 --port 8000

- Ejecutar streaming auxiliar:
    - cd app/vista/streaming
    - python -m http.server 5500

- Ejecutar app web de streamlit:
    - cd app
    - streamlit run main_streamlit_app.py