# ia/rag.py
import os
import faiss
import numpy as np
import json
from typing import List, Dict
from core.config import settings
from ia.embeddings import embed_texts
from core.db import SessionLocal
from models.orm_models import Courrier
import joblib

# paramètres
INDEX_DIR = os.path.abspath(settings.FAISS_INDEX_DIR)
MAPPING_FILE = os.path.join(INDEX_DIR, "id_mapping.joblib")
META_FILE = os.path.join(INDEX_DIR, "meta.json")
TOP_K_DEFAULT = 5

# état en mémoire
_index = None
_id_to_meta = {}
_dim = None
_next_vector_id = 0

def _ensure_index_dir():
    os.makedirs(INDEX_DIR, exist_ok=True)

def init_faiss_index(dim: int):
    global _index, _dim, _id_to_meta, _next_vector_id
    _ensure_index_dir()
    _dim = dim
    index_path = os.path.join(INDEX_DIR, "faiss.index")
    if os.path.exists(index_path) and os.path.exists(MAPPING_FILE):
        _index = faiss.read_index(index_path)
        _id_to_meta = joblib.load(MAPPING_FILE)
        if _id_to_meta:
            _next_vector_id = max(int(k) for k in _id_to_meta.keys()) + 1
        else:
            _next_vector_id = 0
    else:
        _index = faiss.IndexFlatIP(dim)
        _id_to_meta = {}
        _next_vector_id = 0
    _save_meta()

def _save_index():
    index_path = os.path.join(INDEX_DIR, "faiss.index")
    faiss.write_index(_index, index_path)
    joblib.dump(_id_to_meta, MAPPING_FILE)
    _save_meta()

def _save_meta():
    meta = {"dim": _dim, "count": len(_id_to_meta)}
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(meta, f)

def _normalize_vectors(vectors: np.ndarray):
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms

def index_courrier(courrier_id: str, detenu_id: str, text: str):
    global _index, _next_vector_id
    if _index is None:
        emb = embed_texts("test")
        init_faiss_index(emb.shape[1])

    snippet = text[:1000]
    vec = embed_texts(snippet)
    vec = _normalize_vectors(vec)
    _index.add(vec)
    vid = str(_next_vector_id)
    _id_to_meta[vid] = {"courrier_id": courrier_id, "detenu_id": detenu_id, "snippet": snippet}
    _next_vector_id += 1
    _save_index()
    return vid

def retrieve_examples(query: str = None, top_k: int = TOP_K_DEFAULT) -> List[Dict]:
    """
    Retourne les exemples les plus proches de la query parmi TOUS les courriers indexés.
    Pas de filtre par détenu — les exemples servent à tout le monde.
    """
    global _index
    if _index is None:
        emb = embed_texts("test")
        init_faiss_index(emb.shape[1])

    if _index.ntotal == 0:
        return []

    qvec = embed_texts(query or "courrier administratif")
    qvec = _normalize_vectors(qvec)
    D, I = _index.search(qvec, min(top_k, _index.ntotal))

    results = []
    for idx in I[0]:
        if idx < 0:
            continue
        vid = str(idx)
        meta = _id_to_meta.get(vid)
        if not meta:
            continue
        results.append({
            "courrier_id": meta["courrier_id"],
            "detenu_id": meta.get("detenu_id", ""),
            "snippet": meta["snippet"]
        })
    return results

# Conserver l'ancienne fonction pour compatibilité ascendante
def retrieve_examples_for_detenu(detenu_id: str, query: str = None, top_k: int = TOP_K_DEFAULT) -> List[Dict]:
    """
    Ancienne fonction — redirige vers retrieve_examples (global).
    Les exemples s'appliquent désormais à tous les détenus.
    """
    return retrieve_examples(query=query, top_k=top_k)
