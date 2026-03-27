from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVER_PORT: int = 8000
    JWT_SECRET: str = "change_this_secret_in_prod"
    JWT_ALGORITHM: str = "HS256"
    SQLCIPHER_DB_PATH: str = "C:/CourrierIA/storage/sqlcipher.db"
    SQLCIPHER_KEY: str = "change_this_db_key_in_prod"
    MODEL_DIR: str = "C:/CourrierIA/storage/model_weights"
    FAISS_INDEX_DIR: str = "C:/CourrierIA/storage/faiss_index"

settings = Settings()