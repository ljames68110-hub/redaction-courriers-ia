from fastapi import APIRouter, HTTPException
from models.pydantic_schemas import CourrierGenerate, CourrierOut
from core.db import SessionLocal
from models.orm_models import Courrier, Detenu
from ia.model_loader import generate_courrier_text
from ia import rag
import uuid
from core.config import settings
from cryptography.fernet import Fernet
import base64
import os

router = APIRouter()

# Simple symmetric encryption for contenu_chiffre (demo). In prod, use robust key management.
def _get_fernet():
    # derive key from settings.SQLCIPHER_KEY (demo only)
    key = base64.urlsafe_b64encode(settings.SQLCIPHER_KEY.encode("utf-8").ljust(32, b"\0"))
    return Fernet(key)

@router.post("/generer", response_model=CourrierOut)
def generer_courrier(payload: CourrierGenerate):
    db = SessionLocal()
    detenu_data = None
    detenu_id = payload.detenu_id

    # Chargement du détenu enregistré si fourni
    if payload.detenu_id:
        det = db.query(Detenu).filter(Detenu.id == payload.detenu_id).first()
        if not det:
            raise HTTPException(status_code=404, detail="Detenu introuvable")
        detenu_data = {
            "id": det.id,
            "nom": det.nom,
            "prenom": det.prenom,
            "numero_ecrou": det.numero_ecrou,
            "cellule": det.cellule,
            "batiment": det.batiment,
            "etablissement": det.etablissement,
            "date_naissance": det.date_naissance
        }

    # Cas detenu temporaire (nouveau)
    elif payload.detenu_temp:
        detenu_data = payload.detenu_temp.dict()
        # si on demande de sauvegarder le détenu, on le crée et on récupère son id
        if payload.save_detenu:
            new_id = str(uuid.uuid4())
            det = Detenu(
                id=new_id,
                user_id=payload.user_id,
                nom=detenu_data["nom"],
                prenom=detenu_data["prenom"],
                numero_ecrou=detenu_data["numero_ecrou"],
                cellule=detenu_data["cellule"],
                batiment=detenu_data["batiment"],
                etablissement=detenu_data.get("etablissement"),
                date_naissance=detenu_data.get("date_naissance")
            )
            db.add(det)
            db.commit()
            detenu_id = new_id
            # ajouter l'id au dict detenu_data pour que le générateur et RAG puissent l'utiliser
            detenu_data["id"] = new_id

    # Appel du générateur IA (le générateur utilisera RAG si disponible)
    generated_text, metadata = generate_courrier_text(
        detenu=detenu_data,
        detenu_id=detenu_id or (detenu_data.get("id") if detenu_data else None),
        type_courrier=payload.type_courrier,
        motif=payload.motif,
        ton=payload.ton
    )

    # encrypt contenu
    f = _get_fernet()
    token = f.encrypt(generated_text.encode("utf-8"))

    courrier_id = str(uuid.uuid4())
    courrier = Courrier(
        id=courrier_id,
        user_id=payload.user_id,
        detenu_id=detenu_id,
        type=payload.type_courrier,
        motif=payload.motif,
        contenu_chiffre=token.decode("utf-8"),
        tags=None
    )
    db.add(courrier)
    db.commit()

    # Indexer le courrier dans FAISS pour RAG (snippet)
    try:
        # on indexe le texte clair (ou un snippet anonymisé si tu préfères)
        rag.index_courrier(courrier_id=courrier_id, detenu_id=detenu_id or (detenu_data.get("id") if detenu_data else None), text=generated_text)
    except Exception as e:
        # ne pas bloquer la réponse si l'indexation échoue ; log minimal
        print("Erreur indexation RAG:", e)

    return CourrierOut(courrier_id=courrier_id, contenu=generated_text, metadata=metadata)
