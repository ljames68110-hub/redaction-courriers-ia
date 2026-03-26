# ia/embeddings.py
from sentence_transformers import SentenceTransformer
from core.config import settings
import os

_MODEL_NAME = "all-MiniLM-L6-v2"  # compact et efficace pour RAG
_model = None

def load_embedding_model():
    global _model
    if _model is None:
        # charge local si présent dans MODEL_DIR/embeddings/<name> sinon télécharge (offline: préinstaller)
        model_path = os.path.join(settings.MODEL_DIR, "embeddings", _MODEL_NAME)
        try:
            if os.path.exists(model_path):
                _model = SentenceTransformer(model_path)
            else:
                _model = SentenceTransformer(_MODEL_NAME)
        except Exception as e:
            raise RuntimeError(f"Impossible de charger le modèle d'embeddings: {e}")
    return _model

def embed_texts(texts):
    """
    texts: list[str] ou str
    retourne numpy array (n, dim)
    """
    model = load_embedding_model()
    if isinstance(texts, str):
        texts = [texts]
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings
