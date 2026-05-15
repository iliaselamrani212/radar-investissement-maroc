"""
models.py - Schémas Pydantic pour la base de données structurée des projets
Aligné avec le LIVRABLE 2 : "Base de données structurée des projets"
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, List, Dict, Any
from datetime import date, datetime
from enum import Enum


# === ENUMS SECTEURS / RÉGIONS / STADES ===

SECTEURS = Literal[
    "Industrie", "Énergie", "Agriculture", "Pêche maritime",
    "Tourisme", "Tech & Digital", "Immobilier", "Logistique",
    "Santé", "Éducation", "Infrastructure", "Mines",
    "Finance", "Commerce", "BTP", "Autre"
]

REGIONS = Literal[
    "Casablanca-Settat", "Rabat-Salé-Kénitra",
    "Tanger-Tétouan-Al Hoceïma", "Fès-Meknès",
    "Marrakech-Safi", "Oriental", "Béni Mellal-Khénifra",
    "Souss-Massa", "Drâa-Tafilalet", "Guelmim-Oued Noun",
    "Laâyoune-Sakia El Hamra", "Dakhla-Oued Ed-Dahab"
]

STADES = Literal[
    "annonce", "approuve", "convention_signee",
    "en_construction", "operationnel"
]

TYPES_PROJET = Literal[
    "creation", "extension", "modernisation",
    "partenariat", "fusion_acquisition"
]


# === MODÈLE PRINCIPAL : PROJET D'INVESTISSEMENT ===

class ProjetInvestissement(BaseModel):
    """
    Modèle central du projet d'investissement.
    Contient les 5 CHAMPS CRITIQUES du brief + métadonnées + enrichissements.
    """

    # === IDENTIFIANT ===
    id: Optional[str] = None

    # === 5 CHAMPS CRITIQUES DU BRIEF SDG ===
    montant_mad: Optional[float] = Field(
        None, description="Montant total de l'investissement converti en MAD"
    )
    secteur: SECTEURS = Field(..., description="Secteur d'activité principal")
    region: Optional[REGIONS] = Field(None, description="Région marocaine")
    porteur: Optional[str] = Field(None, description="Entreprise/organisme porteur")
    stade_avancement: STADES = Field("annonce", description="Stade d'avancement")

    # === MÉTADONNÉES DE BASE ===
    titre: str
    description: str
    date_annonce: Optional[date] = None
    devise_originale: Optional[Literal["MAD", "EUR", "USD"]] = "MAD"

    # === ENRICHISSEMENTS IA ===
    sous_secteur: Optional[str] = None
    type_projet: Optional[TYPES_PROJET] = None
    nombre_emplois: Optional[int] = None
    horizon_temporel_annees: Optional[int] = None
    tags_esg: List[str] = Field(default_factory=list)
    strategies_nationales: List[str] = Field(default_factory=list)

    # === GÉOCODAGE ===
    ville: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # === FIABILITÉ & SOURCES ===
    score_confiance_extraction: float = Field(0.5, ge=0, le=1)
    score_fiabilite: Optional[float] = Field(None, ge=0, le=100)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    nb_sources_confirmees: int = 1
    source_principale: Optional[str] = None
    url_source: Optional[str] = None

    # === CONTEXTE & ANALYSE ===
    contexte_macro: Optional[Dict[str, Any]] = None
    fiche_synthetique: Optional[str] = None
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)

    # === HORODATAGE ===
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @field_validator("montant_mad")
    @classmethod
    def montant_positif(cls, v):
        if v is not None and v < 0:
            raise ValueError("Le montant doit être positif")
        return v


# === MODÈLES AUXILIAIRES ===

class SourceArticle(BaseModel):
    """Article brut collecté avant extraction"""
    id: Optional[str] = None
    source: str
    url: str
    title: str
    content: str
    snippet: Optional[str] = None
    type_document: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.now)
    processed: bool = False
    niveau_fiabilite: int = Field(5, ge=1, le=5)


class Anomalie(BaseModel):
    type: str
    severite: Literal["faible", "moyenne", "elevee"]
    message: str
    impact_fiabilite: int = 0


class AlertePersonnalisee(BaseModel):
    projet_id: str
    user_id: str
    pertinence_score: int = Field(ge=0, le=100)
    urgence: Literal["faible", "moyenne", "elevee"]
    raison_alerte: str
    actions_suggerees: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
