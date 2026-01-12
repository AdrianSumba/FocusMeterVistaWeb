import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from servicio.estado_compartido import STATE
from servicio.monitoreo import start_model_loop


app = FastAPI(title="FocusMeter Servicio", version="2.0")

# Permite que cualquier cliente (Streamlit, HTML, móvil, etc.) consulte /metrics sin bloquearse por CORS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    # Un solo loop de captura/inferencia en background.
    start_model_loop()


def mjpeg_generator():
    """Genera un stream MJPEG usando el último JPEG precodificado.

    Importante: NO re-codifica por cliente; solo reutiliza bytes compartidos.
    """
    last_sent_ts = 0.0
    while True:
        with STATE.frame_cv:
            # Espera a que haya un JPEG nuevo o a que exista uno inicial.
            STATE.frame_cv.wait_for(lambda: STATE.last_jpeg is not None and STATE.last_frame_ts != last_sent_ts, timeout=1.0)
            jpeg = STATE.last_jpeg
            ts = STATE.last_frame_ts

        if jpeg is None:
            time.sleep(0.01)
            continue

        last_sent_ts = ts
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n"
               b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" +
               jpeg + b"\r\n")


@app.get("/stream")
def stream():
    # Stream MJPEG estándar para <img src=".../stream">
    return StreamingResponse(
        mjpeg_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/frame")
def frame():
    """Devuelve un frame único (snapshot) para clientes que no soportan MJPEG."""
    with STATE.frame_lock:
        jpeg = STATE.last_jpeg
    if jpeg is None:
        return Response(status_code=204)
    return Response(content=jpeg, media_type="image/jpeg", headers={"Cache-Control": "no-cache"})


@app.get("/metrics")
def metrics():
    # Respuesta ultra-liviana: copia bajo lock y retorna JSON.
    with STATE.metrics_lock:
        data = dict(STATE.metrics)
    return JSONResponse(content=data, headers={"Cache-Control": "no-cache"})
