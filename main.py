from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.db import init_db
from api import auth, detenu, courriers, ia as ia_api

app = FastAPI(title="CourrierIA - Serveur Local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=settings.SERVER_PORT)
