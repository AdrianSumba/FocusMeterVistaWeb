import time
import cv2
import os
from ultralytics import YOLO

MODEL_PATH = "extras/servicio/best.pt"
model = YOLO(MODEL_PATH)

compartido = {
    "ultima_imagen": None,
    "datos_estado": {"nivel": 0, "total": 0, "camara": "Iniciando..."}
}

def bucle_deteccion(source):
    global compartido

    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG) if isinstance(source, str) else cv2.VideoCapture(source)
    compartido["datos_estado"]["camara"] = f"ID:{source}"

    while True:
        ret, frame = cap.read()
        
        if not ret:
            print(f"🚨 Error en fuente {source}. Reintentando estrictamente...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG) if isinstance(source, str) else cv2.VideoCapture(source)
            continue

        results = model(frame, conf=0.5, verbose=False, imgsz=640)
        boxes = results[0].boxes
        atentos = sum(1 for b in boxes if "atent" in model.names[int(b.cls[0])].lower())
        total = len(boxes)

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = model.names[int(box.cls[0])]
            color = (0, 255, 0) if "atent" in label.lower() else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        compartido["datos_estado"].update({"nivel": atentos/total if total>0 else 0, "total": total})
        _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        compartido["ultima_imagen"] = buffer.tobytes()