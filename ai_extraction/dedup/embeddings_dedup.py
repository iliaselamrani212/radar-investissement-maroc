"""
dedup/embeddings_dedup.py - Fonctionnalité 5 : Déduplication sémantique
Le même projet peut être annoncé par AMDIE + Bulletin Officiel + Charika.
On le détecte par similarité d'embeddings.
"""
import logging
from typing import List, Optional, Tuple
import numpy as np

from ..llm_client import llm
from ..models import ProjetInvestissement
from ..prompts import PROMPT_CONFIRME_DOUBLON
from ..config import SEUIL_DEDUPLICATION, EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class DeduplicationService:
    """Service de déduplication sémantique avec cache du modèle d'embeddings"""

    def __init__(self):
        self._model = None

    @property
    def model(self):
        """Lazy loading du modèle (lourd)"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(EMBEDDING_MODEL)
                logger.info(f"Modèle embeddings chargé : {EMBEDDING_MODEL}")
            except ImportError:
                logger.error("sentence-transformers non installé")
                raise
        return self._model

    def signature(self, projet: ProjetInvestissement) -> str:
        """Crée une signature textuelle pour l'embedding"""
        return (
            f"{projet.titre} | "
            f"porteur:{projet.porteur or '?'} | "
            f"region:{projet.region or '?'} | "
            f"secteur:{projet.secteur}"
        )

    def embed(self, projet: ProjetInvestissement) -> np.ndarray:
        """Calcule l'embedding d'un projet"""
        return self.model.encode(self.signature(projet))

    def cosine_similarity(self, e1: np.ndarray, e2: np.ndarray) -> float:
        """Similarité cosine entre deux embeddings"""
        norm = np.linalg.norm(e1) * np.linalg.norm(e2)
        if norm == 0:
            return 0.0
        return float(np.dot(e1, e2) / norm)

    def detecter_doublon(
        self,
        nouveau: ProjetInvestissement,
        existants: List[ProjetInvestissement],
        seuil: float = SEUIL_DEDUPLICATION,
    ) -> Optional[Tuple[ProjetInvestissement, float]]:
        """
        Détecte si `nouveau` est un doublon d'un projet existant.

        Returns:
            Tuple (projet_existant, similarité) si doublon, None sinon
        """
        if not existants:
            return None

        emb_new = self.embed(nouveau)
        candidats = []

        for existant in existants:
            emb_old = self.embed(existant)
            sim = self.cosine_similarity(emb_new, emb_old)
            if sim > seuil:
                candidats.append((existant, sim))

        # Tri par similarité décroissante
        candidats.sort(key=lambda x: x[1], reverse=True)

        # Validation LLM du meilleur candidat
        for existant, sim in candidats[:3]:  # max 3 candidats à vérifier
            if self._llm_confirme_doublon(nouveau, existant):
                logger.info(
                    f"🔗 Doublon détecté : '{nouveau.titre[:40]}' ≈ "
                    f"'{existant.titre[:40]}' (sim={sim:.2f})"
                )
                return (existant, sim)

        return None

    def _llm_confirme_doublon(
        self,
        p1: ProjetInvestissement,
        p2: ProjetInvestissement,
    ) -> bool:
        """Confirmation finale par LLM"""
        prompt = PROMPT_CONFIRME_DOUBLON.format(
            titre1=p1.titre, porteur1=p1.porteur, region1=p1.region,
            montant1=p1.montant_mad, secteur1=p1.secteur,
            titre2=p2.titre, porteur2=p2.porteur, region2=p2.region,
            montant2=p2.montant_mad, secteur2=p2.secteur,
        )
        try:
            return llm.binaire(prompt)
        except Exception as e:
            logger.error(f"Erreur confirmation doublon: {e}")
            return False


# Instance globale
dedup_service = DeduplicationService()


def fusionner_projets(
    principal: ProjetInvestissement,
    doublon: ProjetInvestissement,
) -> ProjetInvestissement:
    """
    Fusionne un doublon dans le projet principal.
    Garde les meilleures données + ajoute la nouvelle source.
    """
    # Complète les champs manquants
    if not principal.montant_mad and doublon.montant_mad:
        principal.montant_mad = doublon.montant_mad
    if not principal.region and doublon.region:
        principal.region = doublon.region
    if not principal.porteur and doublon.porteur:
        principal.porteur = doublon.porteur
    if not principal.nombre_emplois and doublon.nombre_emplois:
        principal.nombre_emplois = doublon.nombre_emplois

    # Ajoute la source si nouvelle
    sources_existantes = {s.get("source") for s in principal.sources}
    if doublon.source_principale and doublon.source_principale not in sources_existantes:
        principal.sources.append({
            "source": doublon.source_principale,
            "url": doublon.url_source,
        })
        principal.nb_sources_confirmees = len(principal.sources) + 1

    # Garde le stade le plus avancé
    ordre_stades = [
        "annonce", "approuve", "convention_signee",
        "en_construction", "operationnel"
    ]
    idx_principal = ordre_stades.index(principal.stade_avancement)
    idx_doublon = ordre_stades.index(doublon.stade_avancement)
    if idx_doublon > idx_principal:
        principal.stade_avancement = doublon.stade_avancement

    return principal
