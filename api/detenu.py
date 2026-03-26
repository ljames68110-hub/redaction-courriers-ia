from fastapi import APIRouter, HTTPException, Depends
from models.pydantic_schemas import DetenuCreate, DetenuOut
from core.db import SessionLocal
from models.orm_models import Detenu
import uuid

router = APIRouter()

@router.get("/")
def list_detenu(user_id: str):
    db = SessionLocal()
    dets = db.query(Detenu).filter(Detenu.user_id == user_id).all()
    return [DetenuOut(
        id=d.id,
        nom=d.nom,
        prenom=d.prenom,
        numero_ecrou=d.numero_ecrou,
        cellule=d.cellule,
        batiment=d.batiment,
        etablissement=d.etablissement,
        date_naissance=d.date_naissance
    ) for d in dets]

@router.post("/")
def create_or_update_detenu(payload: DetenuCreate, user_id: str):
    db = SessionLocal()
    if payload.id:
        det = db.query(Detenu).filter(Detenu.id == payload.id, Detenu.user_id == user_id).first()
        if not det:
            raise HTTPException(status_code=404, detail="Detenu not found")
        for k, v in payload.dict().items():
            if v is not None and hasattr(det, k):
                setattr(det, k, v)
        db.commit()
        return {"id": det.id}
    else:
        det_id = str(uuid.uuid4())
        det = Detenu(
            id=det_id,
            user_id=user_id,
            nom=payload.nom,
            prenom=payload.prenom,
            numero_ecrou=payload.numero_ecrou,
            cellule=payload.cellule,
            batiment=payload.batiment,
            etablissement=payload.etablissement,
            date_naissance=payload.date_naissance
        )
        db.add(det)
        db.commit()
        return {"id": det_id}

@router.get("/{detenu_id}")
def get_detenu(detenu_id: str, user_id: str):
    db = SessionLocal()
    det = db.query(Detenu).filter(Detenu.id == detenu_id, Detenu.user_id == user_id).first()
    if not det:
        raise HTTPException(status_code=404, detail="Detenu not found")
    return DetenuOut(
        id=det.id,
        nom=det.nom,
        prenom=det.prenom,
        numero_ecrou=det.numero_ecrou,
        cellule=det.cellule,
        batiment=det.batiment,
        etablissement=det.etablissement,
        date_naissance=det.date_naissance
    )

@router.delete("/{detenu_id}")
def delete_detenu(detenu_id: str, user_id: str):
    db = SessionLocal()
    det = db.query(Detenu).filter(Detenu.id == detenu_id, Detenu.user_id == user_id).first()
    if not det:
        raise HTTPException(status_code=404, detail="Detenu not found")
    db.delete(det)
    db.commit()
    return {"status": "deleted"}
