from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    consent_finetune = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    detenus = relationship("Detenu", back_populates="owner")
    courriers = relationship("Courrier", back_populates="owner")

class Detenu(Base):
    __tablename__ = "detenus"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    numero_ecrou = Column(String, nullable=False)
    cellule = Column(String, nullable=False)
    batiment = Column(String, nullable=False)
    etablissement = Column(String, nullable=True)
    date_naissance = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="detenus")
    courriers = relationship("Courrier", back_populates="detenu")

class Courrier(Base):
    __tablename__ = "courriers"
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"))
    detenu_id = Column(String, ForeignKey("detenus.id"), nullable=True)
    type = Column(String, nullable=False)
    motif = Column(String, nullable=True)
    contenu_chiffre = Column(Text, nullable=False)  # stocké chiffré
    tags = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="courriers")
    detenu = relationship("Detenu", back_populates="courriers")
