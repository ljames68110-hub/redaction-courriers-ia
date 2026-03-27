"""
CourrierIA — Lanceur principal
Double-cliquez sur CourrierIA.exe pour démarrer l'application.
"""
import sys
import os
import threading
import time
import webbrowser

# ── Ajouter le dossier du .exe au PATH Python ──
if getattr(sys, 'frozen', False):
    # Mode .exe PyInstaller
    BASE_DIR = sys._MEIPASS
    APP_DIR  = os.path.dirname(sys.executable)
else:
    # Mode développement
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR  = BASE_DIR

sys.path.insert(0, BASE_DIR)
os.chdir(APP_DIR)

# Créer les dossiers de stockage si absents
for folder in [
    "C:/CourrierIA/storage/faiss_index",
    "C:/CourrierIA/storage/model_weights",
]:
    os.makedirs(folder, exist_ok=True)

def ouvrir_navigateur():
    """Attend que le serveur démarre puis ouvre le navigateur."""
    time.sleep(3)
    webbrowser.open("http://127.0.0.1:8000/static/index.html")

def lancer_serveur():
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning"
    )

if __name__ == "__main__":
    print("=" * 50)
    print("  CourrierIA — Démarrage en cours...")
    print("  L'application s'ouvrira dans votre navigateur.")
    print("  Ne fermez pas cette fenêtre.")
    print("=" * 50)

    # Ouvrir le navigateur en arrière-plan
    threading.Thread(target=ouvrir_navigateur, daemon=True).start()

    # Lancer le serveur (bloquant)
    lancer_serveur()
