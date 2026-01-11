import cv2
import time


RTSP_URL = "rtsp://admin:Novat3ch@192.168.137.159:554/Streaming/Channels/101"
RTSP_READ_TIMEOUT = 2.0


def open_rtsp():
    cap = cv2.VideoCapture(RTSP_URL)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir RTSP")
    return cap


def safe_rtsp_read(cap, timeout=RTSP_READ_TIMEOUT):
    start = time.time()
    while time.time() - start < timeout:
        ret, frame = cap.read()
        if ret and frame is not None:
            return True, frame
        time.sleep(0.01)
    return False, None


def open_usb_or_integrated(max_usb_index=5):

    for i in range(1, max_usb_index + 1):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"[CAMARA] Cámara USB encontrada en índice {i}")
            return cap
        else:
            cap.release()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir ninguna cámara (USB ni integrada)")
    print("[CAMARA] Usando cámara integrada del computador (índice 0)")
    return cap
