from pydantic import BaseModel, Field
from typing import Optional, List

class UserCreate(BaseModel):
    id: str
    nom: str
    email: str
    password: str

class UserOut(BaseModel):
    id: str
    nom: str
    email: str
    role: str
    consent_finetune: bool

class DetenuBase(BaseModel):
    nom: str
    prenom: str
    numero_ecrou: str
    cellule: str
    batiment: str
    etablissement: Optional[str] = None
    date_naissance: Optional[str] = None

class DetenuCreate(DetenuBase):
    id: Optional[str] = None
    save_detenu: Optional[bool] = False

class DetenuOut(DetenuBase):
    id: str

class CourrierGenerate(BaseModel):
    user_id: str
    detenu_id: Optional[str] = None
    detenu_temp: Optional[DetenuCreate] = None
    type_courrier: str
    motif: Optional[str] = None
    ton: Optional[str] = "neutre"
    save_detenu: Optional[bool] = False

class CourrierOut(BaseModel):
    courrier_id: str
    contenu: str
    metadata: dict
