import os
import cv2


RTSP_URL = os.getenv(
    "FOCUSMETER_RTSP_URL",
    "rtsp://admin:Novat3ch@192.168.137.159:554/Streaming/Channels/101",
)


def _set_low_latency_options(cap: cv2.VideoCapture) -> None:
    try:
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    except Exception:
        pass


def _try_open_capture(source, api_preference=None) -> cv2.VideoCapture | None:

    try:
        cap = cv2.VideoCapture(source, api_preference) if api_preference is not None else cv2.VideoCapture(source)
    except Exception:
        return None

    _set_low_latency_options(cap)

    if not cap.isOpened():
        try:
            cap.release()
        except Exception:
            pass
        return None

    ret, frame = cap.read()
    if not ret or frame is None:
        try:
            cap.release()
        except Exception:
            pass
        return None

    return cap


def open_rtsp():
    cap = _try_open_capture(RTSP_URL, cv2.CAP_FFMPEG)
    if cap is not None:
        return cap

    for idx in (1, 2, 3):
        cap = _try_open_capture(idx)
        if cap is not None:
            print(f"[CAM] RTSP no disponible. Usando webcam externa (index={idx}).")
            return cap

    # 3) Cámara integrada
    cap = _try_open_capture(0)
    if cap is not None:
        print("[CAM] RTSP no disponible. Usando cámara integrada (index=0).")
        return cap

    raise RuntimeError("No se pudo abrir RTSP ni webcams (externa/integrada)")
