import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

Base = declarative_base()
DB_PATH = os.path.abspath(settings.SQLCIPHER_DB_PATH)

# connection string sqlite file
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# create engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# For SQLCipher we attempt to set PRAGMA key on each connection if supported.
@event.listens_for(engine, "connect")
def set_sqlcipher_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        # If SQLCipher is available, this will set the key; otherwise it will raise and be ignored.
        cursor.execute(f"PRAGMA key = '{settings.SQLCIPHER_KEY}';")
        cursor.close()
    except Exception:
        # SQLCipher not available or PRAGMA failed: continue with plain SQLite for dev.
        pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from models.orm_models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)
