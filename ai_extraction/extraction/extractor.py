"""
extraction/extractor.py - Fonctionnalité 3 : EXTRACTION DES 5 CHAMPS CRITIQUES
Adapté pour Qwen 2.5 7B en local via Ollama.

Optimisations spécifiques Qwen :
  - Prompts plus directs et structurés (Qwen suit mieux les instructions étape par étape)
  - Schéma JSON simplifié inline (plus fiable que JSON Schema complet sur 7B)
  - Fallback gracieux si Qwen renvoie un JSON partiellement invalide
"""
import logging
from typing import Optional

from ..llm_client import llm
from ..models import ProjetInvestissement
from ..prompts import SYSTEM_PROMPT_EXTRACTION
from ..config import TAUX_CHANGE

logger = logging.getLogger(__name__)


# Schéma simplifié inline (Qwen 7B le suit mieux que JSON Schema complet)
SCHEMA_INLINE = """
{
  "titre": "string",
  "description": "string (1-2 phrases)",
  "montant_mad": "nombre ou null",
  "secteur": "Industrie | Énergie | Agriculture | Pêche maritime | Tourisme | Tech & Digital | Immobilier | Logistique | Santé | Éducation | Infrastructure | Mines | Finance | Commerce | BTP | Autre",
  "region": "Casablanca-Settat | Rabat-Salé-Kénitra | Tanger-Tétouan-Al Hoceïma | Fès-Meknès | Marrakech-Safi | Oriental | Béni Mellal-Khénifra | Souss-Massa | Drâa-Tafilalet | Guelmim-Oued Noun | Laâyoune-Sakia El Hamra | Dakhla-Oued Ed-Dahab | null",
  "porteur": "string ou null",
  "stade_avancement": "annonce | approuve | convention_signee | en_construction | operationnel",
  "score_confiance_extraction": "nombre entre 0 et 1",
  "devise_originale": "MAD | EUR | USD",
  "date_annonce": "YYYY-MM-DD ou null",
  "nombre_emplois": "entier ou null"
}
"""


def extraire_projet(
    titre: str,
    contenu: str,
    source: str,
    url: Optional[str] = None,
) -> Optional[ProjetInvestissement]:
    """
    Extraction principale des 5 champs critiques + métadonnées.

    Args:
        titre: titre de l'article/document
        contenu: contenu textuel complet
        source: nom de la source officielle
        url: URL d'origine

    Returns:
        ProjetInvestissement validé ou None si extraction impossible
    """
    user_prompt = f"""Analyse ce document officiel marocain et extrais les informations en JSON.

SOURCE OFFICIELLE : {source}
TITRE : {titre}

DOCUMENT :
{contenu[:4000]}

SCHÉMA JSON ATTENDU :
{SCHEMA_INLINE}

INSTRUCTIONS :
1. Lis attentivement le document
2. Pour chaque champ, cherche l'information EXPLICITEMENT dans le texte
3. Si une information n'est pas dans le texte, mets null (NE DEVINE PAS)
4. Pour le montant : convertis en MAD (1 EUR = 11 MAD, 1 USD = 10 MAD)
5. Réponds UNIQUEMENT avec le JSON, sans markdown, sans texte autour.

JSON :"""

    try:
        data = llm.complete_json(
            prompt=user_prompt,
            system=SYSTEM_PROMPT_EXTRACTION,
            temperature=0.1,
            max_tokens=1500,
        )

        if not data:
            logger.error(f"❌ Extraction vide pour '{titre[:60]}'")
            return None

        # Nettoyage / normalisation des données
        data = _nettoyer_data(data, source, url)

        # Validation Pydantic
        projet = ProjetInvestissement(**data)
        logger.info(
            f"✅ Extraction OK : {projet.titre[:60]} | "
            f"{projet.secteur} | {projet.region} | "
            f"{projet.montant_mad} MAD | conf={projet.score_confiance_extraction:.2f}"
        )
        return projet

    except Exception as e:
        logger.error(f"❌ Erreur extraction '{titre[:60]}': {e}")
        return None


def _nettoyer_data(data: dict, source: str, url: Optional[str]) -> dict:
    """
    Nettoie et normalise les données retournées par Qwen.
    Qwen 7B peut parfois renvoyer des valeurs non-conformes — on robustifie.
    """
    # === Source et URL ===
    data["source_principale"] = source
    if url:
        data["url_source"] = url

    # === Montant : conversion devise ===
    montant = data.get("montant_mad")
    devise = data.get("devise_originale", "MAD")
    if montant is not None and devise and devise != "MAD":
        taux = TAUX_CHANGE.get(devise, 1.0)
        try:
            data["montant_mad"] = float(montant) * taux
        except (ValueError, TypeError):
            data["montant_mad"] = None

    # Conversion str -> float si nécessaire
    if isinstance(data.get("montant_mad"), str):
        try:
            # Retire les espaces, virgules, etc.
            montant_str = data["montant_mad"].replace(" ", "").replace(",", ".")
            data["montant_mad"] = float(montant_str)
        except (ValueError, AttributeError):
            data["montant_mad"] = None

    # === Score de confiance ===
    score = data.get("score_confiance_extraction")
    if isinstance(score, str):
        try:
            data["score_confiance_extraction"] = float(score)
        except ValueError:
            data["score_confiance_extraction"] = 0.5
    elif score is None:
        data["score_confiance_extraction"] = 0.5

    # Bornage 0-1
    data["score_confiance_extraction"] = max(
        0.0, min(1.0, float(data.get("score_confiance_extraction", 0.5)))
    )

    # === Secteur : fallback si valeur invalide ===
    secteurs_valides = [
        "Industrie", "Énergie", "Agriculture", "Pêche maritime",
        "Tourisme", "Tech & Digital", "Immobilier", "Logistique",
        "Santé", "Éducation", "Infrastructure", "Mines",
        "Finance", "Commerce", "BTP", "Autre"
    ]
    if data.get("secteur") not in secteurs_valides:
        # Tente un mapping
        secteur_brut = (data.get("secteur") or "").lower()
        if "tech" in secteur_brut or "digital" in secteur_brut or "ia" in secteur_brut:
            data["secteur"] = "Tech & Digital"
        elif "énergie" in secteur_brut or "energie" in secteur_brut or "solaire" in secteur_brut:
            data["secteur"] = "Énergie"
        elif "pêche" in secteur_brut or "peche" in secteur_brut:
            data["secteur"] = "Pêche maritime"
        else:
            data["secteur"] = "Autre"

    # === Région : invalide → null ===
    regions_valides = [
        "Casablanca-Settat", "Rabat-Salé-Kénitra",
        "Tanger-Tétouan-Al Hoceïma", "Fès-Meknès",
        "Marrakech-Safi", "Oriental", "Béni Mellal-Khénifra",
        "Souss-Massa", "Drâa-Tafilalet", "Guelmim-Oued Noun",
        "Laâyoune-Sakia El Hamra", "Dakhla-Oued Ed-Dahab"
    ]
    if data.get("region") not in regions_valides:
        data["region"] = None

    # === Stade : fallback ===
    stades_valides = ["annonce", "approuve", "convention_signee",
                      "en_construction", "operationnel"]
    if data.get("stade_avancement") not in stades_valides:
        data["stade_avancement"] = "annonce"

    # === Champs vides ===
    if not data.get("titre"):
        data["titre"] = "Sans titre"
    if not data.get("description"):
        data["description"] = "Description non extraite"

    return data


def extraire_batch(documents: list) -> list:
    """Extraction en lot avec gestion d'erreurs par document"""
    projets = []
    for doc in documents:
        projet = extraire_projet(
            titre=doc.get("title", ""),
            contenu=doc.get("content", ""),
            source=doc.get("source", "inconnue"),
            url=doc.get("url"),
        )
        if projet:
            projets.append(projet)
    logger.info(f"Extraction batch : {len(projets)}/{len(documents)} réussies")
    return projets
