from fastapi import APIRouter, HTTPException
from core.db import SessionLocal
from models.orm_models import User
from core.config import settings

router = APIRouter()

@router.post("/fine_tune")
def fine_tune_request(admin_user_id: str):
    # stub: vérifier rôle admin, lancer pipeline finetune asynchrone
    db = SessionLocal()
    user = db.query(User).filter(User.id == admin_user_id).first()
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    # lancer tâche asynchrone (à implémenter)
    return {"status": "fine_tune_started"}
