"""
rag/engine.py - Moteur RAG : récupération + génération ancrée.

1. Embedding de la question
2. Récupération des passages les plus pertinents (datasets finance + projets)
3. Génération de la réponse par Ollama, STRICTEMENT basée sur les passages
   (anti-hallucination : interdiction d'inventer, citation des sources)
"""
import logging
from typing import Dict, List, Optional

from .store import rag_store
from ..llm_client import llm

logger = logging.getLogger(__name__)

SYSTEM_RAG = (
    "Tu es un assistant analyste pour un radar des projets d'investissement au Maroc. "
    "Tu réponds UNIQUEMENT à partir des EXTRAITS fournis (données officielles "
    "et projets détectés). "
    "Si l'information n'est pas dans les extraits, dis explicitement : "
    "\"Cette information n'est pas disponible dans l'index.\" "
    "N'invente JAMAIS de chiffre. Ne mentionne pas les sources techniques ni leurs URL. "
    "Réponds en français, de façon factuelle et concise."
)

PROMPT_TEMPLATE = """CONTEXTE PROJET :
{contexte_projet}

EXTRAITS DE DONNÉES OFFICIELLES (numérotés) :
{extraits}

QUESTION :
{question}

Consignes :
- Réponds uniquement avec les faits présents dans les extraits ci-dessus.
- Ne cite pas les sources techniques et n'affiche pas d'URL.
- Si les extraits ne permettent pas de répondre, dis-le clairement.
- Pas d'emoji, ton professionnel."""


def _formater_extraits(passages: List[Dict]) -> str:
    blocs = []
    for i, p in enumerate(passages, 1):
        origine = p.get("titre") or p.get("source") or "source"
        blocs.append(f"[{i}] ({origine})\n{p['contenu'][:700]}")
    return "\n\n".join(blocs) if blocs else "(aucun extrait pertinent trouvé)"


def poser_question(
    question: str,
    top_k: int = 5,
    doc_type: Optional[str] = None,
    contexte_projet: str = "",
) -> Dict:
    """
    Pose une question au RAG. Retourne la réponse + les sources utilisées.
    """
    rag_store.init()

    passages = rag_store.rechercher(question, top_k=top_k, doc_type=doc_type)

    if not passages:
        return {
            "reponse": "Aucune donnée indexée pour le moment. Lancez l'ingestion "
            "puis réessayez.",
            "sources": [],
            "contexte_trouve": False,
        }

    prompt = PROMPT_TEMPLATE.format(
        contexte_projet=contexte_projet or "(question générale, pas de projet ciblé)",
        extraits=_formater_extraits(passages),
        question=question,
    )

    try:
        reponse = llm.complete(prompt, system=SYSTEM_RAG, temperature=0.1, max_tokens=500)
    except Exception as e:
        logger.error(f"Erreur génération RAG : {e}")
        reponse = "Le modèle local (Ollama) est indisponible. Vérifiez qu'Ollama tourne."

    return {
        "reponse": reponse,
        "sources": [
            {
                "n": i + 1,
                "titre": p.get("titre"),
                "source": p.get("source"),
                "url": p.get("url"),
                "doc_type": p.get("doc_type"),
                "score": p.get("score"),
                "extrait": p["contenu"][:300],
            }
            for i, p in enumerate(passages)
        ],
        "contexte_trouve": True,
    }


def ask_about_project(projet, question: str, top_k: int = 5) -> Dict:
    """
    Question ancrée sur un projet précis : on combine
    - le contexte du projet (toujours)
    - les passages finance/projets les plus pertinents
    """
    d = projet.model_dump() if hasattr(projet, "model_dump") else dict(projet)

    montant = d.get("montant_mad")
    montant_str = (
        f"{montant/1e9:.2f} Mds MAD"
        if montant and montant >= 1e9
        else (f"{montant/1e6:.0f} M MAD" if montant else "Non précisé")
    )

    contexte_projet = (
        f"Titre : {d.get('titre', '')}\n"
        f"Secteur : {d.get('secteur', '')} / {d.get('sous_secteur') or 'N/A'}\n"
        f"Région : {d.get('region') or 'N/A'} - Ville : {d.get('ville') or 'N/A'}\n"
        f"Porteur : {d.get('porteur') or 'N/A'}\n"
        f"Montant : {montant_str}\n"
        f"Stade : {d.get('stade_avancement') or 'N/A'}\n"
        f"Description : {d.get('description') or ''}"
    )

    projet_id = str(d.get("id", ""))
    requete = f"{d.get('titre', '')} {d.get('secteur', '')} {question}"

    # Une SEULE recherche (cache mémoire + 1 seul embedding requête).
    # On élargit puis on priorise les sources liées à CE projet.
    bruts = rag_store.rechercher(requete, top_k=max(top_k * 3, 12))
    lies = [p for p in bruts if projet_id and p.get("ref_id") == projet_id]
    autres = [p for p in bruts if not (projet_id and p.get("ref_id") == projet_id)]
    passages = (lies + autres)[: max(top_k, 5)]

    if not passages:
        # Pas d'index finance → on répond avec le seul contexte projet
        prompt = (
            f"CONTEXTE PROJET :\n{contexte_projet}\n\n"
            f"QUESTION : {question}\n\n"
            "Réponds uniquement à partir du contexte projet ci-dessus. "
            "Si l'info manque, dis-le."
        )
        try:
            reponse = llm.complete(prompt, system=SYSTEM_RAG, temperature=0.1, max_tokens=700)
        except Exception:
            reponse = "Ollama indisponible."
        return {"reponse": reponse, "sources": [], "contexte_trouve": False}

    prompt = PROMPT_TEMPLATE.format(
        contexte_projet=contexte_projet,
        extraits=_formater_extraits(passages),
        question=question,
    )
    try:
        reponse = llm.complete(prompt, system=SYSTEM_RAG, temperature=0.1, max_tokens=500)
    except Exception as e:
        logger.error(f"Erreur RAG projet : {e}")
        reponse = "Ollama indisponible. Vérifiez 'ollama serve'."

    return {
        "reponse": reponse,
        "sources": [
            {
                "n": i + 1,
                "titre": p.get("titre"),
                "source": p.get("source"),
                "url": p.get("url"),
                "doc_type": p.get("doc_type"),
                "score": p.get("score"),
                "extrait": p["contenu"][:300],
            }
            for i, p in enumerate(passages)
        ],
        "contexte_trouve": True,
    }
