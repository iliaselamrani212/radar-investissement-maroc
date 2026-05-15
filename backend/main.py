from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path
from typing import Optional, Any
from urllib import request as urlrequest
import json
import csv
import io
import logging
import sys

try:
    from database import engine, get_db
    from models import Base, Project, Region
except ModuleNotFoundError:
    from .database import engine, get_db
    from .models import Base, Project, Region

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

try:
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    logger.warning("Base PostgreSQL indisponible au demarrage: %s", exc)

app = FastAPI(
    title="Radar Investissement Maroc API",
    description="API Backend pour détecter, structurer et prioriser les projets d'investissement au Maroc.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SECTORS = [
    "Industrie",
    "Énergie",
    "Agriculture",
    "Tourisme",
    "Tech",
    "Immobilier",
    "Logistique",
    "Santé",
    "Éducation",
    "Infrastructure",
    "Finance",
    "Autre"
]


class LLMDocumentInput(BaseModel):
    title: str
    content: str
    source: str = "test"
    url: Optional[str] = None
    snippet: Optional[str] = None


def _load_ai_database():
    try:
        from ai_extraction.database import init_db, get_all_projets, get_projet, save_projet

        return init_db, get_all_projets, get_projet, save_projet
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Module IA indisponible: {exc}",
        ) from exc


def _normalize_ai_project(projet: Any) -> dict:
    data = projet.model_dump(mode="json")
    score_confiance = data.get("score_confiance_extraction")

    return {
        "id": data.get("id"),
        "titre": data.get("titre"),
        "resume_ai": data.get("description") or data.get("fiche_synthetique"),
        "description": data.get("description"),
        "fiche_synthetique": data.get("fiche_synthetique"),
        "montant_mad": data.get("montant_mad"),
        "secteur": data.get("secteur"),
        "region": data.get("region"),
        "porteur": data.get("porteur"),
        "stade": data.get("stade_avancement"),
        "stade_avancement": data.get("stade_avancement"),
        "date_annonce": data.get("date_annonce"),
        "sources": data.get("sources") or [],
        "nb_sources_confirmees": data.get("nb_sources_confirmees"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
        "score_fiabilite": data.get("score_fiabilite"),
        "score_details": {
            "score_llm": round(score_confiance * 100, 1) if score_confiance is not None else None,
            "score_fiabilite": data.get("score_fiabilite"),
        },
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "llm": {
            "score_confiance_extraction": score_confiance,
            "sous_secteur": data.get("sous_secteur"),
            "type_projet": data.get("type_projet"),
            "nombre_emplois": data.get("nombre_emplois"),
            "horizon_temporel_annees": data.get("horizon_temporel_annees"),
            "tags_esg": data.get("tags_esg") or [],
            "strategies_nationales": data.get("strategies_nationales") or [],
            "ville": data.get("ville"),
            "contexte_macro": data.get("contexte_macro"),
            "anomalies": data.get("anomalies") or [],
            "source_principale": data.get("source_principale"),
            "url_source": data.get("url_source"),
        },
    }


@app.get("/")
def root():
    return {
        "message": "Radar Investissement Maroc API",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/llm/status")
def llm_status():
    try:
        from ai_extraction.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Configuration IA indisponible: {exc}",
        ) from exc

    base_url = OLLAMA_BASE_URL.rstrip("/")
    status = {
        "base_url": base_url,
        "model": OLLAMA_MODEL,
        "timeout_seconds": OLLAMA_TIMEOUT,
        "available": False,
        "model_available": False,
        "models": [],
        "message": "Ollama injoignable",
    }

    try:
        with urlrequest.urlopen(f"{base_url}/api/tags", timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))

        models = [model.get("name") for model in payload.get("models", []) if model.get("name")]
        status["available"] = True
        status["models"] = models
        status["model_available"] = any(
            OLLAMA_MODEL in model or model.startswith(OLLAMA_MODEL.split(":")[0])
            for model in models
        )
        status["message"] = "Ollama disponible" if status["model_available"] else "ModÃ¨le configurÃ© introuvable"
    except Exception as exc:
        status["message"] = str(exc)

    return status


@app.get("/llm/projects")
def list_llm_projects(
    secteur: Optional[str] = None,
    region: Optional[str] = None,
    stade: Optional[str] = None,
    montant_min: Optional[float] = None,
    score_min: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    init_db, get_all_projets, _, _ = _load_ai_database()
    init_db()

    projets = get_all_projets(
        limit=1000,
        secteur=secteur,
        region=region,
        stade=stade,
        montant_min=montant_min,
    )

    if score_min is not None:
        projets = [p for p in projets if (p.score_fiabilite or 0) >= score_min]

    if search:
        needle = search.lower()
        projets = [
            p for p in projets
            if needle in " ".join([
                p.titre or "",
                p.description or "",
                p.porteur or "",
                p.secteur or "",
                p.region or "",
            ]).lower()
        ]

    total = len(projets)
    items = projets[offset:offset + limit]

    return {
        "total": total,
        "items": [_normalize_ai_project(projet) for projet in items],
        "limit": limit,
        "offset": offset,
    }


@app.get("/llm/projects/{project_id}/similar")
def list_llm_similar_projects(
    project_id: str,
    top_n: int = Query(5, ge=1, le=20),
):
    init_db, get_all_projets, get_projet, _ = _load_ai_database()
    init_db()

    projet = get_projet(project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet IA introuvable")

    try:
        from ai_extraction.veille.recommandations import recommander_similaires
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Recommandations IA indisponibles: {exc}",
        ) from exc

    projets = get_all_projets(limit=500)
    return {
        "items": recommander_similaires(projet, projets, top_n=top_n),
    }


@app.get("/llm/projects/{project_id}")
def get_llm_project(project_id: str):
    init_db, _, get_projet, _ = _load_ai_database()
    init_db()

    projet = get_projet(project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet IA introuvable")

    return _normalize_ai_project(projet)


@app.get("/llm/veille/hebdo")
def llm_weekly_watch(limit: int = Query(200, ge=1, le=1000)):
    init_db, get_all_projets, _, _ = _load_ai_database()
    init_db()

    try:
        from ai_extraction.veille.tendances import (
            calculer_chiffres_cles,
            generer_rapport_veille_hebdo,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Veille IA indisponible: {exc}",
        ) from exc

    projets = get_all_projets(limit=limit)
    return {
        "nb_projets_analyses": len(projets),
        "chiffres_cles": calculer_chiffres_cles(projets),
        "rapport_markdown": generer_rapport_veille_hebdo(projets),
    }


@app.post("/llm/extract")
def extract_with_llm(document: LLMDocumentInput):
    init_db, get_all_projets, _, save_projet = _load_ai_database()
    init_db()

    try:
        from ai_extraction.pipeline import traiter_nouveau_document
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Pipeline IA indisponible: {exc}",
        ) from exc

    projets_existants = get_all_projets(limit=500)
    projet = traiter_nouveau_document(
        document=document.model_dump(exclude_none=True),
        source=document.source,
        projets_existants=projets_existants,
    )

    if not projet:
        return {
            "status": "rejected",
            "reason": "Document non pertinent, contenu trop court ou extraction impossible",
        }

    save_projet(projet)
    return {
        "status": "ok",
        "project": _normalize_ai_project(projet),
    }


@app.get("/projects")
def list_projects(
    secteur: Optional[str] = None,
    region: Optional[str] = None,
    montant_min: Optional[float] = None,
    montant_max: Optional[float] = None,
    stade: Optional[str] = None,
    score_min: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: str = Query(
        "score_fiabilite",
        pattern="^(score_fiabilite|montant_mad|date_annonce|created_at)$"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = "SELECT * FROM projects WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM projects WHERE 1=1"
    params = {}

    if secteur:
        query += " AND secteur = :secteur"
        count_query += " AND secteur = :secteur"
        params["secteur"] = secteur

    if region:
        query += " AND region = :region"
        count_query += " AND region = :region"
        params["region"] = region

    if montant_min is not None:
        query += " AND montant_mad >= :montant_min"
        count_query += " AND montant_mad >= :montant_min"
        params["montant_min"] = montant_min

    if montant_max is not None:
        query += " AND montant_mad <= :montant_max"
        count_query += " AND montant_mad <= :montant_max"
        params["montant_max"] = montant_max

    if stade:
        query += " AND stade = :stade"
        count_query += " AND stade = :stade"
        params["stade"] = stade

    if score_min is not None:
        query += " AND score_fiabilite >= :score_min"
        count_query += " AND score_fiabilite >= :score_min"
        params["score_min"] = score_min

    if search:
        query += """
        AND (
            titre ILIKE :search
            OR resume_ai ILIKE :search
            OR porteur ILIKE :search
            OR secteur ILIKE :search
            OR region ILIKE :search
        )
        """
        count_query += """
        AND (
            titre ILIKE :search
            OR resume_ai ILIKE :search
            OR porteur ILIKE :search
            OR secteur ILIKE :search
            OR region ILIKE :search
        )
        """
        params["search"] = f"%{search}%"

    query += f" ORDER BY {sort_by} DESC NULLS LAST LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    total = db.execute(
        text(count_query),
        {k: v for k, v in params.items() if k not in ["limit", "offset"]}
    ).scalar()

    result = db.execute(text(query), params).fetchall()
    items = [dict(row._mapping) for row in result]

    return {
        "total": total,
        "items": items,
        "limit": limit,
        "offset": offset
    }


@app.get("/projects/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text("SELECT * FROM projects WHERE id = :id"),
        {"id": project_id}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    return dict(result._mapping)


@app.get("/projects/{project_id}/sources")
def get_project_sources(project_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        text("SELECT titre, sources FROM projects WHERE id = :id"),
        {"id": project_id}
    ).fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    row = dict(result._mapping)

    return {
        "project": row["titre"],
        "sources": row["sources"]
    }


@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.execute(text("SELECT COUNT(*) FROM projects")).scalar()

    total_amount = db.execute(
        text("SELECT COALESCE(SUM(montant_mad), 0) FROM projects")
    ).scalar()

    avg_score = db.execute(
        text("SELECT COALESCE(AVG(score_fiabilite), 0) FROM projects")
    ).scalar()

    by_sector = db.execute(text("""
        SELECT 
            secteur,
            COUNT(*) AS count,
            COALESCE(SUM(montant_mad), 0) AS total
        FROM projects
        GROUP BY secteur
        ORDER BY count DESC
    """)).fetchall()

    by_region = db.execute(text("""
        SELECT 
            region,
            COUNT(*) AS count,
            COALESCE(SUM(montant_mad), 0) AS total
        FROM projects
        WHERE region IS NOT NULL
        GROUP BY region
        ORDER BY count DESC
    """)).fetchall()

    by_stade = db.execute(text("""
        SELECT 
            stade,
            COUNT(*) AS count
        FROM projects
        GROUP BY stade
        ORDER BY count DESC
    """)).fetchall()

    timeline = db.execute(text("""
        SELECT 
            DATE_TRUNC('month', created_at) AS mois,
            COUNT(*) AS count
        FROM projects
        GROUP BY mois
        ORDER BY mois
    """)).fetchall()

    return {
        "total_projects": total,
        "total_amount_mad": float(total_amount),
        "average_score": round(float(avg_score), 1),
        "by_sector": [dict(row._mapping) for row in by_sector],
        "by_region": [dict(row._mapping) for row in by_region],
        "by_stade": [dict(row._mapping) for row in by_stade],
        "timeline": [dict(row._mapping) for row in timeline]
    }


@app.get("/regions")
def get_regions(db: Session = Depends(get_db)):
    regions = db.query(Region).all()

    return [
        {
            "nom": region.nom,
            "latitude": float(region.latitude),
            "longitude": float(region.longitude)
        }
        for region in regions
    ]


@app.get("/sectors")
def get_sectors():
    return SECTORS


@app.get("/alerts/recent")
def recent_alerts(
    score_min: float = 80,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    result = db.execute(text("""
        SELECT *
        FROM projects
        WHERE score_fiabilite >= :score_min
        ORDER BY created_at DESC
        LIMIT :limit
    """), {
        "score_min": score_min,
        "limit": limit
    }).fetchall()

    return {
        "score_min": score_min,
        "items": [dict(row._mapping) for row in result]
    }


@app.get("/export/csv")
def export_csv(
    secteur: Optional[str] = None,
    region: Optional[str] = None,
    score_min: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = """
    SELECT 
        titre,
        secteur,
        region,
        porteur,
        montant_mad,
        stade,
        score_fiabilite,
        nb_sources_confirmees
    FROM projects
    WHERE 1=1
    """

    params = {}

    if secteur:
        query += " AND secteur = :secteur"
        params["secteur"] = secteur

    if region:
        query += " AND region = :region"
        params["region"] = region

    if score_min is not None:
        query += " AND score_fiabilite >= :score_min"
        params["score_min"] = score_min

    query += " ORDER BY score_fiabilite DESC NULLS LAST"

    rows = db.execute(text(query), params).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Titre",
        "Secteur",
        "Région",
        "Porteur",
        "Montant MAD",
        "Stade",
        "Score Fiabilité",
        "Nombre Sources"
    ])

    for row in rows:
        writer.writerow(row)

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=projets_investissement.csv"
        }
    )
