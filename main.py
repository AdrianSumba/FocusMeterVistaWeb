import os
import sys
import time
import signal
import subprocess
import threading
from pathlib import Path


ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
STREAMING_DIR = APP_DIR / "vista" / "streaming"

FASTAPI_HOST = os.getenv("FOCUSMETER_FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FOCUSMETER_FASTAPI_PORT", "8000"))
STREAMING_PORT = int(os.getenv("FOCUSMETER_STREAMING_PORT", "5500"))

DELAY_AFTER_FASTAPI = float(os.getenv("FOCUSMETER_DELAY_FASTAPI", "3.0"))
DELAY_AFTER_STREAMING = float(os.getenv("FOCUSMETER_DELAY_STREAMING", "1.5"))

NEW_CONSOLE = os.getenv("FOCUSMETER_NEW_CONSOLE", "0") == "1"


def _stream_output(prefix: str, proc: subprocess.Popen):
    try:
        for line in iter(proc.stdout.readline, ""):
            if not line:
                break
            print(f"[{prefix}] {line}", end="")
    except Exception:
        pass


def start_service(name: str, cmd: list[str], cwd: Path) -> subprocess.Popen:
    if not cwd.exists():
        raise FileNotFoundError(f"No existe el directorio requerido: {cwd}")

    creationflags = 0
    if os.name == "nt" and NEW_CONSOLE:
        creationflags = subprocess.CREATE_NEW_CONSOLE

    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        stdout=None if (os.name == "nt" and NEW_CONSOLE) else subprocess.PIPE,
        stderr=None if (os.name == "nt" and NEW_CONSOLE) else subprocess.STDOUT,
        text=True,
        bufsize=1,
        creationflags=creationflags,
    )

    if proc.stdout is not None:
        t = threading.Thread(target=_stream_output, args=(name, proc), daemon=True)
        t.start()

    print(f"✅ {name} iniciado (PID={proc.pid}) -> {' '.join(cmd)}")
    return proc


def main():
    procs: list[subprocess.Popen] = []

    def shutdown(*_):
        print("\n🛑 Cerrando servicios...")
        for p in procs:
            try:
                if p.poll() is None:
                    p.terminate()
            except Exception:
                pass

        time.sleep(2.0)
        for p in procs:
            try:
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass

        print("✅ Servicios cerrados.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if os.name == "nt":
        try:
            signal.signal(signal.SIGTERM, shutdown)
        except Exception:
            pass

    fastapi_cmd = [
        sys.executable, "-m", "uvicorn",
        "main_servicio_app:app",
        "--host", FASTAPI_HOST,
        "--port", str(FASTAPI_PORT),
    ]
    procs.append(start_service("FASTAPI", fastapi_cmd, APP_DIR))
    time.sleep(DELAY_AFTER_FASTAPI)

    streaming_cmd = [
        sys.executable, "-m", "http.server",
        str(STREAMING_PORT),
    ]
    procs.append(start_service("HTML", streaming_cmd, STREAMING_DIR))
    time.sleep(DELAY_AFTER_STREAMING)

    streamlit_cmd = [
        sys.executable, "-m", "streamlit",
        "run", "main_streamlit_app.py",
    ]
    procs.append(start_service("STREAMLIT", streamlit_cmd, APP_DIR))

    print("\n🚀 Todo levantado.")
    print(f"   - FastAPI:    http://{FASTAPI_HOST}:{FASTAPI_PORT}")
    print(f"   - HTML/JS:    http://localhost:{STREAMING_PORT}")
    print("   - Streamlit:  revisa la URL que imprime Streamlit en consola\n")


    try:
        while True:
            for p in procs:
                if p.poll() is not None:
                    print(f"⚠️ Un servicio terminó (PID={p.pid}, code={p.returncode}).")
                    procs.remove(p)
            if not procs:
                print("⚠️ No quedan servicios corriendo. Saliendo.")
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()