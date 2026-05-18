"""
api.py - API FastAPI servant le Dashboard interactif (LIVRABLE 1)

Endpoints exposés :
  GET  /api/projets              → liste des projets (avec filtres)
  GET  /api/projets/{id}         → détail d'un projet + fiche
  GET  /api/projets/{id}/similaires → recommandations
  GET  /api/stats                → statistiques pour dashboard
  GET  /api/veille/hebdo         → rapport de veille
  POST /api/projets/extraire     → extraction à la volée (test)
  GET  /api/alertes/{user_id}    → alertes d'un utilisateur
"""
import logging
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .database import (
    init_db, get_all_projets, get_projet, save_projet,
    stats_globales, get_alertes_user,
)
from .pipeline import traiter_nouveau_document
from .veille.tendances import generer_rapport_veille_hebdo
from .veille.recommandations import recommander_similaires

logger = logging.getLogger(__name__)

app = FastAPI(
    title="InvestiGator 43 - API",
    description="API du radar des projets d'investissement au Maroc",
    version="1.0.0",
)

# CORS pour permettre au frontend de consommer l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


# ═══════════════════════════════════════════════════════════════
# ENDPOINT : LISTE DES PROJETS (avec filtres - LIVRABLE 4)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/projets")
def liste_projets(
    secteur: Optional[str] = None,
    region: Optional[str] = None,
    stade: Optional[str] = None,
    montant_min: Optional[float] = None,
    limit: int = Query(default=100, le=1000),
):
    """Liste des projets avec filtres multiples"""
    projets = get_all_projets(
        limit=limit, secteur=secteur, region=region,
        stade=stade, montant_min=montant_min,
    )
    return {
        "count": len(projets),
        "projets": [p.model_dump() for p in projets],
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT : DÉTAIL D'UN PROJET (avec fiche synthétique)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/projets/{projet_id}")
def detail_projet(projet_id: str):
    """Détail complet d'un projet avec sa fiche synthétique"""
    projet = get_projet(projet_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return projet.model_dump()


# ═══════════════════════════════════════════════════════════════
# ENDPOINT : PROJETS SIMILAIRES
# ═══════════════════════════════════════════════════════════════

@app.get("/api/projets/{projet_id}/similaires")
def projets_similaires(projet_id: str, top_n: int = 5):
    """Recommandations de projets similaires"""
    projet = get_projet(projet_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    tous = get_all_projets(limit=500)
    recommendations = recommander_similaires(projet, tous, top_n=top_n)
    return {"recommendations": recommendations}


# ═══════════════════════════════════════════════════════════════
# ENDPOINT : STATISTIQUES (pour Dashboard - LIVRABLE 1)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/stats")
def stats():
    """Statistiques globales pour le dashboard"""
    return stats_globales()


# ═══════════════════════════════════════════════════════════════
# ENDPOINT : VEILLE STRATÉGIQUE
# ═══════════════════════════════════════════════════════════════

@app.get("/api/veille/hebdo")
def veille_hebdo():
    """Génère le rapport de veille hebdomadaire"""
    projets = get_all_projets(limit=200)
    rapport = generer_rapport_veille_hebdo(projets)
    return {
        "rapport_markdown": rapport,
        "nb_projets_analyses": len(projets),
    }


# ═══════════════════════════════════════════════════════════════
# ENDPOINT : ALERTES UTILISATEUR
# ═══════════════════════════════════════════════════════════════

@app.get("/api/alertes/{user_id}")
def alertes(user_id: str, non_lues: bool = False):
    """Alertes personnalisées d'un utilisateur"""
    return {"alertes": get_alertes_user(user_id, non_lues_seulement=non_lues)}


# ═══════════════════════════════════════════════════════════════
# ENDPOINT : EXTRACTION À LA VOLÉE (test/démo)
# ═══════════════════════════════════════════════════════════════

class DocumentInput(BaseModel):
    title: str
    content: str
    source: str = "test"
    url: Optional[str] = None


@app.post("/api/projets/extraire")
def extraire(document: DocumentInput):
    """Extraction à la volée (test/démo)"""
    projets_existants = get_all_projets(limit=500)
    projet = traiter_nouveau_document(
        document=document.model_dump(),
        source=document.source,
        projets_existants=projets_existants,
    )
    if not projet:
        return {"status": "rejeté", "raison": "Document non pertinent ou extraction échouée"}

    save_projet(projet)
    return {"status": "ok", "projet": projet.model_dump()}


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

@app.get("/")
def root():
    return {
        "service": "InvestiGator 43",
        "version": "1.0.0",
        "status": "online",
        "endpoints": [
            "/api/projets",
            "/api/projets/{id}",
            "/api/projets/{id}/similaires",
            "/api/stats",
            "/api/veille/hebdo",
            "/api/alertes/{user_id}",
            "/api/projets/extraire (POST)",
        ],
    }


# Run avec : uvicorn ai_extraction.api:app --reload --port 8000
