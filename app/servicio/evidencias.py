import cv2
import os


EVIDENCIAS_PATH = "extras/evidencias"
os.makedirs(EVIDENCIAS_PATH, exist_ok=True)


def guardar_evidencia(frame, texto, timestamp):
    cv2.putText(frame, texto, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    cv2.imwrite(
        os.path.join(EVIDENCIAS_PATH, f"evidencia_{timestamp}.jpg"),
        frame
    )
