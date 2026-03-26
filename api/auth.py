from fastapi import APIRouter, HTTPException, Depends
from models.pydantic_schemas import UserCreate, UserOut
from core.db import SessionLocal
from models.orm_models import User
from passlib.context import CryptContext
from jose import jwt
from core.config import settings
import uuid

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    token = jwt.encode(data, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

@router.post("/login")
def login(email: str, password: str):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user or not pwd_context.verify(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.id})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/register")
def register(payload: UserCreate):
    db = SessionLocal()
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email exists")
    user = User(
        id=payload.id or str(uuid.uuid4()),
        nom=payload.nom,
        email=payload.email,
        password_hash=pwd_context.hash(payload.password),
        role="user"
    )
    db.add(user)
    db.commit()
    return {"id": user.id, "email": user.email}
