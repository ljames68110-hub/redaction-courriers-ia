from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.db import init_db
from api import auth, detenu, courriers, ia as ia_api, exemples

app = FastAPI(title="CourrierIA - Serveur Local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# initialisation DB (création tables si besoin)
init_db()

# inclure routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(detenu.router, prefix="/detenus", tags=["detenus"])
app.include_router(courriers.router, prefix="/courriers", tags=["courriers"])
app.include_router(ia_api.router, prefix="/ia", tags=["ia"])
app.include_router(exemples.router, prefix="/exemples", tags=["exemples"])

# servir l'interface HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=settings.SERVER_PORT)
