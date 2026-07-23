import os
import sys
import time
import subprocess
import threading
from typing import Any
import webview

# ─── RESOLVER ADVERTENCIA DE _MEIPASS ────────────────────────────────────────
# Usamos getattr de forma segura con un valor por defecto para que Pylance no chille.
if getattr(sys, 'frozen', False):
    BASE_DIR: str = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Variable global para rastrear el proceso del servidor de fondo
server_process: subprocess.Popen[bytes] | None = None

def iniciar_streamlit() -> None:
    """Ejecuta el servidor de Streamlit de forma silenciosa."""
    global server_process
    script_path = os.path.join(BASE_DIR, "main.py")
    
    env = os.environ.copy()
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
    
    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW
    else:
        creation_flags = 0

    server_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", script_path, "--server.port=8501"],
        env=env,
        creationflags=creation_flags
    )

def al_cerrar_ventana() -> None:
    """Detiene el proceso del servidor de fondo al cerrar la ventana."""
    global server_process
    if server_process is not None:
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    # 1. Iniciar Streamlit en un hilo paralelo
    t = threading.Thread(target=iniciar_streamlit, daemon=True)
    t.start()
    
    # 2. Darle un par de segundos al servidor local para inicializarse
    time.sleep(2.5)
    
    # 3. Crear la ventana nativa de escritorio
    window: Any = webview.create_window(
        title="RAV System - Gestión que impulsa tu éxito",
        url="http://localhost:8501",
        width=1280,
        height=800,
        resizable=True,
        min_size=(1024, 768)
    )
    
    # ─── RESOLVER ADVERTENCIA DE "events" is not a known attribute ───────────
    # Forzamos el tipo 'Any' en la ventana o validamos explícitamente para Pylance.
    if window is not None:
        window.events.closing += al_cerrar_ventana
    
    # Iniciar el bucle de la aplicación nativa
    webview.start()