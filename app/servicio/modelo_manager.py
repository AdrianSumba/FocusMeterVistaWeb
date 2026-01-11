import traceback
import cv2
from ultralytics import YOLO


MODEL_PATH = "servicio/modelo/best.pt"
PESOS_ATENCION = {
    "attentive": 1.0,
    "hand_rising": 1.0,
    "human": 0.5,
    "daydreaming": 0.3,
    "distracted": 0.0,
    "sleepy": 0.0,
    "bullying": 0.0,
    "phone_use": 0.0
}


def cargar_modelo():
    try:
        model = YOLO(MODEL_PATH)
        return model, model.names
    except Exception:
        traceback.print_exc()
        return None, None


def procesar_detecciones(boxes, class_names, frame):
    total = len(boxes)
    suma = 0.0
    conteo = {}

    for box in boxes:
        cls = int(box.cls[0])
        label = class_names[cls].lower()
        conteo[label] = conteo.get(label, 0) + 1

        peso = PESOS_ATENCION.get(label, 0.0)
        suma += peso

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        color = (0, 255, 0) if peso >= 0.7 else (255, 255, 0) if peso >= 0.3 else (0, 0, 255)

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    estimacion = (suma / total * 100) if total > 0 else 0
    return estimacion, total, conteo


def nuevo_intervalo(fecha, hora):
    return {
        "estudiantes_list": [],
        "atencion_list": [],
        "etiquetas_conteos": {},
        "inicio_fecha": fecha,
        "inicio_hora": hora
    }


def actualizar_intervalo(intervalo, total, atencion, conteo):
    intervalo["estudiantes_list"].append(total)
    intervalo["atencion_list"].append(atencion)

    for k, v in conteo.items():
        intervalo["etiquetas_conteos"].setdefault(k, []).append(v)
