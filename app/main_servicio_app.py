import threading
import cv2
import time
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse

from servicio.estado_compartido import STATE
from servicio.monitoreo import start_model_loop


app = FastAPI()


@app.on_event("startup")
def startup():
    threading.Thread(target=start_model_loop, daemon=True).start()


def frame_generator():
    while True:
        with STATE.frame_lock:
            frame = STATE.last_frame

        if frame is None:
            time.sleep(0.01)
            continue

        ret, jpeg = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        )
        if not ret:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + jpeg.tobytes()
            + b"\r\n"
        )

        time.sleep(0.02)


@app.get("/stream")
def stream():
    return StreamingResponse(
        frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


@app.get("/metrics")
def metrics():
    with STATE.metrics_lock:
        data = STATE.metrics.copy()
    return JSONResponse(content=data)
