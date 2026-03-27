from typing import Tuple, Optional
from ia import rag
from datetime import datetime

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

OLLAMA_MODEL = "mistral"

def _assemble_prompt(
    detenu: Optional[dict],
    detenu_id: Optional[str],
    type_courrier: str,
    motif: Optional[str],
    ton: str
) -> str:

    # Date du jour en français
    mois = ["janvier","février","mars","avril","mai","juin",
            "juillet","août","septembre","octobre","novembre","décembre"]
    now = datetime.now()
    date_fr = f"{now.day} {mois[now.month-1]} {now.year}"

    # Récupérer exemples RAG si disponible
    rag_context = ""
    try:
        examples = rag.retrieve_examples_for_detenu(
            detenu_id=str(detenu_id) if detenu_id else "",
            query=motif or "",
            top_k=3
        )
        for ex in examples:
            rag_context += f"Exemple de courrier similaire :\n{ex.get('snippet','')}\n---\n"
    except Exception:
        pass

    # Infos détenu
    nom = ""
    prenom = ""
    ecrou = ""
    cellule = ""
    batiment = ""
    etablissement = ""
    date_naissance = ""

    if detenu:
        nom = detenu.get('nom', '')
        prenom = detenu.get('prenom', '')
        ecrou = detenu.get('numero_ecrou', '')
        cellule = detenu.get('cellule', '')
        batiment = detenu.get('batiment', '')
        etablissement = detenu.get('etablissement', '') or ''
        date_naissance = detenu.get('date_naissance', '') or ''

    detenu_info = (
        f"- Nom : {nom}\n"
        f"- Prénom : {prenom}\n"
        f"- Numéro d'écrou : {ecrou}\n"
        f"- Cellule : {cellule}, Bâtiment : {batiment}\n"
    )
    if etablissement:
        detenu_info += f"- Établissement : {etablissement}\n"
    if date_naissance:
        detenu_info += f"- Date de naissance : {date_naissance}\n"

    destinataire = _get_destinataire(type_courrier)
    exemples_section = ("EXEMPLES POUR INSPIRATION :\n" + rag_context) if rag_context else ""
    motif_str = motif or "Non précisé"
    adresse_etablissement = etablissement if etablissement else "l'établissement pénitentiaire"

    prompt = f"""Tu es un juriste expert en droit pénitentiaire français, spécialisé dans la rédaction de courriers officiels pour détenus.

CONSIGNES STRICTES :
- Rédige UNIQUEMENT le courrier, rien d'autre avant ni après
- La date du jour est : {date_fr} — utilise cette date exacte, pas une autre
- Le destinataire exact est : {destinataire} — adresse le courrier uniquement à cette personne
- N'invente AUCUN fait qui n'est pas mentionné dans le motif
- Utilise le vouvoiement strict et le registre administratif formel
- La formule de politesse finale doit être sobre et professionnelle
- Le courrier doit être complet et prêt à envoyer

STRUCTURE OBLIGATOIRE :
1. En-tête expéditeur (nom, prénom, numéro d'écrou, cellule, établissement)
2. En-tête destinataire ({destinataire})
3. Lieu et date : {adresse_etablissement}, le {date_fr}
4. Objet : {type_courrier}
5. Formule d'appel : Monsieur / Madame (selon le destinataire)
6. Corps du courrier structuré en paragraphes clairs
7. Formule de politesse finale formelle et complète
8. Signature : {nom} {prenom}, numéro d'écrou {ecrou}

INFORMATIONS DU DÉTENU :
{detenu_info}

TYPE DE COURRIER : {type_courrier}
TON : {ton}
MOTIF ET CONTEXTE : {motif_str}

{exemples_section}

COURRIER :"""

    return prompt

    return prompt


def _get_destinataire(type_courrier: str) -> str:
    type_lower = type_courrier.lower()
    if "greffe" in type_lower:
        return "Monsieur/Madame le/la Chef(fe) du Greffe"
    elif "direction" in type_lower:
        return "Monsieur/Madame le/la Directeur/Directrice de l'établissement pénitentiaire"
    elif "parloir" in type_lower:
        return "Monsieur/Madame le/la Chef(fe) du service des Parloirs"
    elif "médical" in type_lower or "ucsa" in type_lower:
        return "Monsieur/Madame le/la Médecin-Chef de l'UCSA"
    elif "spip" in type_lower:
        return "Monsieur/Madame le/la Directeur/Directrice du SPIP"
    elif "juge" in type_lower or "jap" in type_lower or "application" in type_lower:
        return "Monsieur/Madame le/la Juge de l'Application des Peines"
    elif "comptabilité" in type_lower or "pécule" in type_lower:
        return "Monsieur/Madame le/la Responsable du service Comptabilité"
    elif "transfert" in type_lower:
        return "Monsieur/Madame le/la Directeur/Directrice Interrégional(e) des Services Pénitentiaires"
    elif "discipline" in type_lower:
        return "Monsieur/Madame le/la Président(e) de la Commission de Discipline"
    elif "uvf" in type_lower or "familiale" in type_lower:
        return "Monsieur/Madame le/la Responsable des Unités de Vie Familiale"
    elif "préfecture" in type_lower:
        return "Monsieur/Madame le/la Préfet(e)"
    else:
        return "Monsieur/Madame le/la Directeur/Directrice de l'établissement"


def generate_courrier_text(
    detenu: Optional[dict],
    detenu_id: Optional[str],
    type_courrier: str,
    motif: Optional[str],
    ton: str
) -> Tuple[str, dict]:
    """
    Génère un courrier via Ollama/Mistral.
    Fallback sur texte stub si Ollama non disponible.
    """

    if not OLLAMA_AVAILABLE:
        return _fallback(detenu, type_courrier, motif), {"model_version": "stub", "used_examples": 0}

    # Vérifier qu'Ollama tourne
    try:
        ollama.list()
    except Exception:
        return _fallback(detenu, type_courrier, motif), {"model_version": "stub (ollama non démarré)", "used_examples": 0}

    prompt = _assemble_prompt(
        detenu=detenu,
        detenu_id=detenu_id,
        type_courrier=type_courrier,
        motif=motif,
        ton=ton
    )

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.4,
                "top_p": 0.9,
                "num_predict": 1024,
            }
        )
        generated = response["message"]["content"].strip()

        # Compter les exemples RAG utilisés
        used_examples = 0
        try:
            used_examples = len(rag.retrieve_examples_for_detenu(
                detenu_id=str(detenu_id) if detenu_id else "",
                query=motif or "",
                top_k=3
            ))
        except Exception:
            pass

        return generated, {"model_version": f"ollama/{OLLAMA_MODEL}", "used_examples": used_examples}

    except Exception as e:
        return _fallback(detenu, type_courrier, motif), {"model_version": f"stub (erreur: {str(e)})", "used_examples": 0}


def _fallback(detenu, type_courrier, motif):
    nom = detenu.get("nom", "NOM") if detenu else "NOM"
    prenom = detenu.get("prenom", "PRÉNOM") if detenu else "PRÉNOM"
    num = detenu.get("numero_ecrou", "XXXXX") if detenu else "XXXXX"
    return (
        f"Objet : {type_courrier}\n\n"
        f"Je soussigné(e) {nom} {prenom}, numéro d'écrou {num}, "
        f"sollicite par la présente votre attention concernant : {motif or 'le motif non précisé'}.\n\n"
        "⚠️ Mode démo — Installez Ollama et Mistral pour une génération IA complète.\n"
        "Voir instructions dans la conversation."
    )


# Pas de chargement au démarrage nécessaire avec Ollama
def load_model():
    pass

load_model()
