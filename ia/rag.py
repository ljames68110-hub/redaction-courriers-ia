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
_id_to_meta = {}   # mapping vector_id -> {courrier_id, detenu_id, snippet}
_dim = None
_next_vector_id = 0

def _ensure_index_dir():
    os.makedirs(INDEX_DIR, exist_ok=True)

def init_faiss_index(dim: int):
    global _index, _dim, _id_to_meta, _next_vector_id
    _ensure_index_dir()
    _dim = dim
    # si index existant sur disque, charger
    index_path = os.path.join(INDEX_DIR, "faiss.index")
    if os.path.exists(index_path) and os.path.exists(MAPPING_FILE):
        _index = faiss.read_index(index_path)
        _id_to_meta = joblib.load(MAPPING_FILE)
        # compute next id
        if _id_to_meta:
            _next_vector_id = max(int(k) for k in _id_to_meta.keys()) + 1
        else:
            _next_vector_id = 0
    else:
        # index plat (IndexFlatIP) + normalization pour cos sim
        _index = faiss.IndexFlatIP(dim)
        _id_to_meta = {}
        _next_vector_id = 0
    # save meta file for debugging
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
    # pour IndexFlatIP on normalise pour sim cosinus
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms

def index_courrier(courrier_id: str, detenu_id: str, text: str):
    """
    Extrait un ou plusieurs passages (ici on indexe le texte complet et un snippet),
    calcule embedding(s) et ajoute à FAISS. Stocke mapping vector_id -> meta.
    """
    global _index, _next_vector_id
    if _index is None:
        # lazy init: determine dim from embedding model
        emb = embed_texts("test")
        init_faiss_index(emb.shape[1])

    # on peut découper en passages si long ; ici on indexe 1 vecteur par courrier (snippet)
    snippet = text[:1000]  # limiter la taille
    vec = embed_texts(snippet)  # shape (1, dim)
    vec = _normalize_vectors(vec)
    # add to index
    _index.add(vec)
    vid = str(_next_vector_id)
    _id_to_meta[vid] = {"courrier_id": courrier_id, "detenu_id": detenu_id, "snippet": snippet}
    _next_vector_id += 1
    _save_index()
    return vid

def rebuild_index_from_db():
    """
    Reconstruit l'index FAISS à partir de la base de données (utile si tu as déjà des courriers).
    """
    global _index, _id_to_meta, _next_vector_id, _dim
    db = SessionLocal()
    courriers = db.query(Courrier).all()
    texts = []
    metas = []
    for c in courriers:
        # déchiffrer contenu si nécessaire : ici on suppose contenu_chiffre contient texte brut ou token
        try:
            content = c.contenu_chiffre
            # si chiffré, il faut le déchiffrer ici avant d'indexer
        except Exception:
            content = ""
        snippet = (content[:1000]) if content else ""
        if snippet:
            texts.append(snippet)
            metas.append({"courrier_id": c.id, "detenu_id": c.detenu_id, "snippet": snippet})
    if not texts:
        # init empty index with dim from embedding model
        emb = embed_texts("test")
        init_faiss_index(emb.shape[1])
        return

    vecs = embed_texts(texts)
    vecs = _normalize_vectors(vecs)
    _dim = vecs.shape[1]
    _index = faiss.IndexFlatIP(_dim)
    _index.add(vecs)
    _id_to_meta = {}
    for i, m in enumerate(metas):
        _id_to_meta[str(i)] = m
    _next_vector_id = len(metas)
    _save_index()

def retrieve_examples_for_detenu(detenu_id: str, query: str = None, top_k: int = TOP_K_DEFAULT) -> List[Dict]:
    """
    Retourne une liste d'extraits pertinents (snippet + meta) pour un détenu donné.
    Si query fourni, on combine retrieval par query + filtrage par detenu_id.
    """
    global _index
    if _index is None:
        # lazy init
        emb = embed_texts("test")
        init_faiss_index(emb.shape[1])

    # si pas d'éléments indexés, retourne vide
    if _index.ntotal == 0:
        return []

    # si query fourni, on embed la query et recherche top_k*2
    if query:
        qvec = embed_texts(query)
    else:
        # si pas de query, on utilise un vecteur neutre (ex: embedding du mot "lettre")
        qvec = embed_texts("lettre")
    qvec = _normalize_vectors(qvec)
    D, I = _index.search(qvec, min(top_k * 3, _index.ntotal))
    results = []
    for idx in I[0]:
        if idx < 0:
            continue
        vid = str(idx)
        meta = _id_to_meta.get(vid)
        if not meta:
            continue
        # filtrer par detenu_id
        if meta.get("detenu_id") == detenu_id:
            results.append({"courrier_id": meta["courrier_id"], "snippet": meta["snippet"]})
            if len(results) >= top_k:
                break
    return results
