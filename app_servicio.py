from fastapi import FastAPI, Response
import threading
from extras.servicio.camara import detectar_mejor_camara
from extras.servicio.estimador_atencion import bucle_deteccion, compartido

app = FastAPI()

# La lógica de jerarquía se ejecuta AQUÍ
fuente_final = detectar_mejor_camara()

if fuente_final is not None:
    print(f"🎯 Jerarquía decidida. Forzando apertura de: {fuente_final}")
    threading.Thread(target=bucle_deteccion, args=(fuente_final,), daemon=True).start()
else:
    print("🛑 No se encontró ninguna cámara.")

@app.get("/video")
async def get_video():
    if compartido["ultima_imagen"] is None: return Response(status_code=404)
    return Response(content=compartido["ultima_imagen"], media_type="image/jpeg")

@app.get("/datos")
async def get_datos():
    return compartido["datos_estado"]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)