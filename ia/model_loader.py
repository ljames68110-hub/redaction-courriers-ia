from typing import Tuple, Optional
from core.config import settings
import os

# Attempt to load a local transformer model; fallback to dummy generator
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    MODEL_AVAILABLE = True
except Exception:
    MODEL_AVAILABLE = False

# Import RAG retrieval
from ia import rag

_model = None
_tokenizer = None
_generator = None

def load_model():
    global _model, _tokenizer, _generator
    if not MODEL_AVAILABLE:
        return
    model_dir = settings.MODEL_DIR
    if os.path.exists(model_dir):
        _tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        _model = AutoModelForCausalLM.from_pretrained(model_dir, local_files_only=True)
        # device=-1 forces CPU; si GPU disponible, adapter device param
        _generator = pipeline("text-generation", model=_model, tokenizer=_tokenizer, device=-1)
    else:
        # model not present locally
        pass

def _assemble_prompt(detenu: Optional[dict], detenu_id: Optional[str], type_courrier: str, motif: Optional[str], ton: str) -> str:
    # récupérer exemples RAG si possible
    rag_context = ""
    try:
        if detenu_id:
            examples = rag.retrieve_examples_for_detenu(detenu_id=str(detenu_id), query=motif or "", top_k=3)
        else:
            # si pas d'id, tenter retrieval par motif
            examples = rag.retrieve_examples_for_detenu(detenu_id="", query=motif or "", top_k=3)
    except Exception:
        examples = []

    for ex in examples:
        snippet = ex.get("snippet", "")
        rag_context += f"Exemple précédent:\n{snippet}\n---\n"

    detenu_info = ""
    if detenu:
        # afficher uniquement les champs utiles (éviter d'exposer trop d'infos dans le prompt si anonymisation souhaitée)
        detenu_info = (
            f"Nom: {detenu.get('nom','')}\n"
            f"Prénom: {detenu.get('prenom','')}\n"
            f"Numéro d'écrou: {detenu.get('numero_ecrou','')}\n"
            f"Cellule: {detenu.get('cellule','')}\n"
            f"Bâtiment: {detenu.get('batiment','')}\n"
        )

    prompt = (
        "System: Tu es un assistant qui rédige des courriers administratifs pour détenus. "
        "Respecte le ton demandé et inclue les mentions pénitentiaires obligatoires.\n\n"
        f"{'Context: ' + rag_context if rag_context else ''}\n"
        f"Detenu:\n{detenu_info}\n"
        f"Instruction: Rédige un courrier de type {type_courrier} pour le motif: {motif or '---'} en ton {ton}.\n\n"
        "Rédige le texte complet, avec en‑tête et formule de politesse finale.\n\nTexte:"
    )
    return prompt

def generate_courrier_text(detenu: Optional[dict], detenu_id: Optional[str], type_courrier: str, motif: Optional[str], ton: str) -> Tuple[str, dict]:
    """
    Retourne (texte, metadata)
    """
    # Si pas de modèle disponible, fallback demo text
    if _generator is None:
        nom = detenu.get("nom") if detenu else "NOM"
        num = detenu.get("numero_ecrou") if detenu else "NUM"
        text = (
            f"Objet : {type_courrier}\n\n"
            f"Je soussigné(e) {nom}, numéro d'écrou {num}, sollicite par la présente {motif or 'votre attention'}.\n\n"
            "Texte généré en mode démo. Remplacer par un modèle local pour production."
        )
        return text, {"model_version": "stub", "used_examples": 0}

    # assembler prompt en incluant contexte RAG
    prompt = _assemble_prompt(detenu=detenu, detenu_id=detenu_id, type_courrier=type_courrier, motif=motif, ton=ton)

    # génération via pipeline
    out = _generator(prompt, max_length=512, do_sample=False)
    generated = out[0].get("generated_text", "")
    # si le générateur renvoie le prompt + texte, on peut nettoyer le prompt si nécessaire
    if generated.startswith(prompt):
        generated = generated[len(prompt):].strip()

    return generated, {"model_version": "local", "used_examples": len(rag.retrieve_examples_for_detenu(detenu_id=str(detenu_id), query=motif or "", top_k=3)) if detenu_id else 0}

# charger modèle au démarrage si possible
load_model()
