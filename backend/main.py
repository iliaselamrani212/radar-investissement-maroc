from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import csv
import io

from database import engine, get_db
from models import Base, Project, Region

Base.metadata.create_all(bind=engine)

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