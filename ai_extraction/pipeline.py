"""
pipeline.py - ORCHESTRATEUR PRINCIPAL
Enchaîne les 13 étapes de traitement d'un document officiel.

Pipeline aligné avec les 4 livrables du brief SDG :
  - LIVRABLE 1 : Dashboard interactif (consomme les données structurées)
  - LIVRABLE 2 : Base de données structurée (output de ce pipeline)
  - LIVRABLE 3 : Fiches projets synthétiques (étape 12)
  - LIVRABLE 4 : Outils de filtrage et priorisation (via score_fiabilite)
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict

from .models import ProjetInvestissement, SourceArticle
from .filtres.pertinence import llm_filtre_pertinence
from .lecture.pdf_reader import extraire_texte_pdf
from .lecture.excel_reader import lire_excel_intelligemment
from .lecture.docx_reader import extraire_texte_docx
from .extraction.extractor import extraire_projet
from .extraction.verifier import auto_verifier
from .dedup.embeddings_dedup import dedup_service, fusionner_projets
from .enrichissement.geocoder import geocoder_intelligent
from .enrichissement.macro_context import enrichir_avec_macro
from .enrichissement.classifier_fin import classifier_finement, appliquer_classification
from .validation.anomalies import detecter_anomalies
from .validation.triangulation import trianguler, calculer_score_fiabilite
from .synthese.fiche_generator import generer_fiche_projet
from .veille.alertes import notifier_utilisateurs_pertinents
from .config import SEUIL_CONFIANCE_MIN

logger = logging.getLogger(__name__)


def traiter_nouveau_document(
    document: Dict,
    source: str,
    projets_existants: List[ProjetInvestissement] = None,
    articles_bruts: List[SourceArticle] = None,
    profils_utilisateurs: List[Dict] = None,
) -> Optional[ProjetInvestissement]:
    """
    PIPELINE COMPLET sur 1 document officiel.

    Args:
        document: dict avec keys 'title', 'content', 'url', 'path' (optionnel)
        source: nom de la source officielle
        projets_existants: base actuelle pour déduplication
        articles_bruts: articles bruts pour triangulation
        profils_utilisateurs: profils pour alertes personnalisées

    Returns:
        ProjetInvestissement enrichi, OU None si rejeté
    """
    projets_existants = projets_existants or []
    articles_bruts = articles_bruts or []
    profils_utilisateurs = profils_utilisateurs or []

    titre = document.get("title", "")
    logger.info(f"\n{'='*70}\nPipeline ▶ '{titre[:60]}' (source: {source})\n{'='*70}")

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 1 : FILTRAGE IA DE PERTINENCE (Fonctionnalité 1)
    # ═══════════════════════════════════════════════════════════
    logger.info("[1/13] Filtrage de pertinence...")
    if not llm_filtre_pertinence(titre, document.get("snippet", "") or document.get("content", "")[:500]):
        logger.info("❌ REJETÉ : non pertinent")
        return None

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 2 : LECTURE INTELLIGENTE (Fonctionnalité 2)
    # ═══════════════════════════════════════════════════════════
    logger.info("[2/13] Lecture du contenu...")
    contenu = _lire_contenu(document)
    if not contenu or len(contenu) < 100:
        logger.info("❌ REJETÉ : contenu trop court")
        return None

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 3 : EXTRACTION DES 5 CHAMPS CRITIQUES (Fonctionnalité 3)
    # ═══════════════════════════════════════════════════════════
    logger.info("[3/13] Extraction des 5 champs critiques...")
    projet = extraire_projet(
        titre=titre,
        contenu=contenu,
        source=source,
        url=document.get("url"),
    )
    if not projet:
        logger.info("❌ REJETÉ : extraction échouée")
        return None

    if projet.score_confiance_extraction < SEUIL_CONFIANCE_MIN:
        logger.info(f"❌ REJETÉ : confiance trop basse ({projet.score_confiance_extraction:.2f})")
        return None

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 4 : AUTO-VÉRIFICATION (Fonctionnalité 4)
    # ═══════════════════════════════════════════════════════════
    logger.info("[4/13] Auto-vérification...")
    projet, verification = auto_verifier(contenu, projet)

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 5 : GÉOCODAGE (Fonctionnalité 6)
    # ═══════════════════════════════════════════════════════════
    logger.info("[5/13] Géocodage...")
    texte_pour_geocoding = f"{titre} {contenu[:500]}"
    geo = geocoder_intelligent(texte_pour_geocoding, region_connue=projet.region)
    if geo:
        projet.latitude = geo.get("lat")
        projet.longitude = geo.get("lng")
        projet.ville = geo.get("ville")
        if not projet.region and geo.get("region"):
            projet.region = geo["region"]

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 6 : DÉDUPLICATION (Fonctionnalité 5)
    # ═══════════════════════════════════════════════════════════
    logger.info("[6/13] Déduplication...")
    doublon = dedup_service.detecter_doublon(projet, projets_existants)
    if doublon:
        projet_existant, sim = doublon
        logger.info(f"🔗 DOUBLON DÉTECTÉ (sim={sim:.2f}) → fusion")
        projet_fusionne = fusionner_projets(projet_existant, projet)
        return projet_fusionne

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 7 : ENRICHISSEMENT MACRO (Fonctionnalité 7)
    # ═══════════════════════════════════════════════════════════
    logger.info("[7/13] Enrichissement macroéconomique...")
    enrichissement = enrichir_avec_macro(projet)
    projet.contexte_macro = enrichissement

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 8 : CLASSIFICATION FINE (Fonctionnalité 11)
    # ═══════════════════════════════════════════════════════════
    logger.info("[8/13] Classification fine...")
    classification = classifier_finement(projet)
    projet = appliquer_classification(projet, classification)

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 9 : DÉTECTION D'ANOMALIES (Fonctionnalité 8)
    # ═══════════════════════════════════════════════════════════
    logger.info("[9/13] Détection d'anomalies...")
    anomalies = detecter_anomalies(projet, enrichissement)
    projet.anomalies = [a.model_dump() for a in anomalies]
    if anomalies:
        logger.warning(f"⚠️  {len(anomalies)} anomalie(s) détectée(s)")

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 10 : TRIANGULATION (Fonctionnalité 9)
    # ═══════════════════════════════════════════════════════════
    logger.info("[10/13] Triangulation entre sources...")
    if articles_bruts:
        sources_confirmees = trianguler(projet, articles_bruts)
        projet.sources = sources_confirmees
        projet.nb_sources_confirmees = len(sources_confirmees) + 1

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 11 : CALCUL DU SCORE DE FIABILITÉ
    # ═══════════════════════════════════════════════════════════
    logger.info("[11/13] Calcul du score de fiabilité...")
    projet.score_fiabilite = calculer_score_fiabilite(projet)
    logger.info(f"📊 Score fiabilité : {projet.score_fiabilite}/100")

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 12 : GÉNÉRATION DE FICHE (Fonctionnalité 10 - LIVRABLE 3)
    # ═══════════════════════════════════════════════════════════
    logger.info("[12/13] Génération de la fiche synthétique...")
    projet.fiche_synthetique = generer_fiche_projet(
        projet, enrichissement, projet.sources,
    )

    # ═══════════════════════════════════════════════════════════
    # ÉTAPE 13 : ALERTES PERSONNALISÉES (Fonctionnalité 12-B)
    # ═══════════════════════════════════════════════════════════
    logger.info("[13/13] Évaluation des alertes...")
    if profils_utilisateurs:
        alertes = notifier_utilisateurs_pertinents(projet, profils_utilisateurs)
        if alertes:
            logger.info(f"🔔 {len(alertes)} alerte(s) générée(s)")

    logger.info(f"✅ PIPELINE TERMINÉ : '{projet.titre[:60]}'\n")
    return projet


def _lire_contenu(document: Dict) -> str:
    """Lit le contenu selon le type de document"""
    # Priorité au contenu déjà fourni
    if document.get("content"):
        return document["content"]

    path = document.get("path")
    if not path:
        return ""

    path_lower = path.lower()
    if path_lower.endswith(".pdf"):
        return extraire_texte_pdf(path)
    elif path_lower.endswith((".xlsx", ".xls")):
        # Pour Excel, on convertit en string les projets extraits
        projets_excel = lire_excel_intelligemment(path)
        return str(projets_excel)
    elif path_lower.endswith(".docx"):
        return extraire_texte_docx(path)
    else:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Erreur lecture fichier : {e}")
            return ""


def traiter_batch(
    documents: List[Dict],
    source: str = "inconnue",
    projets_existants: List[ProjetInvestissement] = None,
) -> List[ProjetInvestissement]:
    """Traitement en lot avec déduplication progressive"""
    projets_existants = projets_existants or []
    nouveaux_projets = []

    for i, doc in enumerate(documents):
        logger.info(f"\n📄 Document {i+1}/{len(documents)}")
        try:
            projet = traiter_nouveau_document(
                document=doc,
                source=doc.get("source", source),
                projets_existants=projets_existants + nouveaux_projets,
            )
            if projet:
                nouveaux_projets.append(projet)
        except Exception as e:
            logger.error(f"❌ Erreur sur document {i+1}: {e}")
            continue

    logger.info(
        f"\n{'='*70}\n"
        f"📊 BATCH TERMINÉ : {len(nouveaux_projets)}/{len(documents)} "
        f"projets retenus\n{'='*70}"
    )
    return nouveaux_projets
