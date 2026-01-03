import os
import cv2
import time

RTSP_URL = "rtsp://admin:Novat3ch@192.168.1.5:554/Streaming/Channels/102"

def detectar_mejor_camara():
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
    cap = cv2.VideoCapture(RTSP_URL, cv2.CAP_FFMPEG)
    if cap.isOpened():
        ret, _ = cap.read()
        if ret:
            print("\n\nRTSP Detectada.\n\n")
            cap.release()
            return RTSP_URL
    if cap: cap.release()

    os.environ.pop("OPENCV_FFMPEG_CAPTURE_OPTIONS", None)
    for idx in range(1, 11):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            time.sleep(0.8) 
            ret, _ = cap.read()
            if ret:
                print(f"\n\nUSB Detectada en índice {idx}.\n\n")
                cap.release()
                return idx
            cap.release()

    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        print(f"\n\nCamara integrada detectada.\n\n")
        cap.release()
        return 0

    print(f"\n\nNo se detecto una camara disponible.\n\n")
    return None