from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path
from typing import Optional, Any
from urllib import request as urlrequest
import json
import csv
import io
import logging
import os
import re
import sys
import threading
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

logger = logging.getLogger(__name__)

# Initialise la base IA au démarrage
try:
    from ai_extraction.database import init_db
    init_db()
    logger.info("Base IA initialisée")
except Exception as exc:
    logger.warning("Base IA indisponible au démarrage: %s", exc)

app = FastAPI(
    title="InvestiGator 43 API",
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


class RagQuestionInput(BaseModel):
    question: str
    top_k: int = 5


class ScoringConfigInput(BaseModel):
    poids_source: float
    poids_triangulation: float
    poids_precision: float
    poids_fraicheur: float
    poids_llm: float


def _load_ai_database():
    try:
        from ai_extraction.database import init_db, get_all_projets, get_projet, save_projet

        return init_db, get_all_projets, get_projet, save_projet
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Module IA indisponible: {exc}",
        ) from exc


def _clean_public_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    text = re.sub(r"SDG\s+Capital", "", text, flags=re.IGNORECASE)
    text = re.sub(r"data\.gov\.ma", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?##\s+Sources\s*&\s*fiabilit\S*[\s\S]*$", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"(?im)^\s*[-*]?\s*(Nombre de sources|Sources confirmees?|Source principale)\s*:.*$",
        "",
        text,
    )
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _normalize_ai_project(projet: Any) -> dict:
    data = projet.model_dump(mode="json")
    score_confiance = data.get("score_confiance_extraction")

    return {
        "id": data.get("id"),
        "titre": data.get("titre"),
        "resume_ai": _clean_public_text(data.get("description") or data.get("fiche_synthetique")),
        "description": _clean_public_text(data.get("description")),
        "fiche_synthetique": _clean_public_text(data.get("fiche_synthetique")),
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
        "score_details": data.get("score_details") or {
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


def _pdf_escape(value: Any) -> str:
    text = str(value if value is not None else "")
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("latin-1", "replace").decode("latin-1")


def _simple_pdf(title: str, lines: list[str]) -> bytes:
    """Genere un PDF minimal sans dependance externe."""
    safe_lines = [_pdf_escape(title[:90])] + [_pdf_escape(line[:110]) for line in lines]
    y = 800
    commands = ["BT", "/F1 16 Tf", f"50 {y} Td", f"({safe_lines[0]}) Tj"]
    commands += ["/F1 10 Tf"]
    for line in safe_lines[1:]:
        y_step = -16
        commands.append(f"0 {y_step} Td")
        commands.append(f"({line}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = [b"%PDF-1.4\n"]
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in pdf))
        pdf.append(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = sum(len(part) for part in pdf)
    pdf.append(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.append(f"{offset:010d} 00000 n \n".encode())
    pdf.append(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    )
    return b"".join(pdf)


def _run_veille_job() -> None:
    try:
        from ai_extraction.database import (
            get_all_projets,
            init_db,
            save_veille_run,
        )
        from ai_extraction.veille.tendances import generer_rapport_veille_hebdo

        init_db()
        projets = get_all_projets(limit=1000)
        rapport = generer_rapport_veille_hebdo(projets)
        save_veille_run("ok", nb_projets=len(projets), rapport_markdown=rapport)
        logger.info("Veille automatique executee (%s projets)", len(projets))
    except Exception as exc:
        logger.warning("Veille automatique KO: %s", exc)
        try:
            from ai_extraction.database import save_veille_run

            save_veille_run("error", error=str(exc))
        except Exception:
            pass


def _start_veille_scheduler() -> None:
    if os.getenv("VEILLE_SCHEDULER_DISABLED", "0") == "1":
        return

    interval_hours = float(os.getenv("VEILLE_INTERVAL_HOURS", "168"))
    interval_seconds = max(60, int(interval_hours * 3600))

    def loop() -> None:
        # Premiere execution differee pour ne pas ralentir le demarrage API.
        time.sleep(5)
        while True:
            _run_veille_job()
            time.sleep(interval_seconds)

    thread = threading.Thread(target=loop, name="veille-scheduler", daemon=True)
    thread.start()


@app.on_event("startup")
def startup_scheduler():
    _start_veille_scheduler()


@app.get("/")
def root():
    return {
        "message": "InvestiGator 43 API",
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
        status["message"] = "Ollama disponible" if status["model_available"] else "Modele configure introuvable"
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
    sort_by: str = Query("score_fiabilite", pattern="^(score_fiabilite|montant_mad|date_annonce|created_at)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    from ai_extraction.database import get_all_projets, init_db
    init_db()

    projets = get_all_projets(
        limit=1000,
        secteur=secteur,
        region=region,
        stade=stade,
        montant_min=montant_min,
    )

    if montant_max is not None:
        projets = [p for p in projets if p.montant_mad is None or p.montant_mad <= montant_max]
    if score_min is not None:
        projets = [p for p in projets if (p.score_fiabilite or 0) >= score_min]
    if search:
        needle = search.lower()
        projets = [
            p for p in projets
            if needle in " ".join([p.titre or "", p.description or "", p.porteur or "", p.secteur or "", p.region or ""]).lower()
        ]

    total = len(projets)
    items = [_normalize_ai_project(p) for p in projets[offset:offset + limit]]

    return {"total": total, "items": items, "limit": limit, "offset": offset}


@app.get("/projects/{project_id}")
def get_project(project_id: str):
    from ai_extraction.database import get_projet, init_db
    init_db()
    projet = get_projet(project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return _normalize_ai_project(projet)


@app.get("/projects/{project_id}/sources")
def get_project_sources(project_id: str):
    from ai_extraction.database import get_projet, init_db
    init_db()
    projet = get_projet(project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return {"project": projet.titre, "sources": projet.sources or []}


@app.get("/stats")
def get_stats():
    try:
        import sqlite3
        from pathlib import Path
        db_path = Path(__file__).parent.parent / "data" / "radar_sdg.db"
        if not db_path.exists():
            return {
                "total_projects": 0, "total_amount_mad": 0.0, "average_score": 0.0,
                "by_sector": [], "by_region": [], "by_stade": [], "timeline": []
            }
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        total = cur.execute("SELECT COUNT(*) FROM projets").fetchone()[0]
        total_amount = cur.execute("SELECT COALESCE(SUM(montant_mad),0) FROM projets").fetchone()[0]
        avg_score = cur.execute("SELECT COALESCE(AVG(score_fiabilite),0) FROM projets").fetchone()[0]

        by_sector = [
            {"secteur": r["secteur"], "count": r["nb"], "total": r["total_mad"]}
            for r in cur.execute("""
                SELECT secteur, COUNT(*) nb, COALESCE(SUM(montant_mad),0) total_mad
                FROM projets GROUP BY secteur ORDER BY nb DESC
            """).fetchall()
        ]
        by_region = [
            {"region": r["region"], "count": r["nb"], "total": r["total_mad"]}
            for r in cur.execute("""
                SELECT region, COUNT(*) nb, COALESCE(SUM(montant_mad),0) total_mad
                FROM projets WHERE region IS NOT NULL GROUP BY region ORDER BY nb DESC
            """).fetchall()
        ]
        by_stade = [
            {"stade": r["stade_avancement"], "count": r["nb"]}
            for r in cur.execute("""
                SELECT stade_avancement, COUNT(*) nb FROM projets
                GROUP BY stade_avancement ORDER BY nb DESC
            """).fetchall()
        ]
        timeline = [
            {"mois": r["mois"], "count": r["nb"]}
            for r in cur.execute("""
                SELECT substr(created_at,1,7) mois, COUNT(*) nb
                FROM projets GROUP BY mois ORDER BY mois
            """).fetchall()
        ]
        conn.close()
        return {
            "total_projects": total,
            "total_amount_mad": float(total_amount),
            "average_score": round(float(avg_score), 1),
            "by_sector": by_sector,
            "by_region": by_region,
            "by_stade": by_stade,
            "timeline": timeline,
        }
    except Exception as exc:
        logger.warning("Stats IA indisponibles: %s", exc)
        return {
            "total_projects": 0, "total_amount_mad": 0.0, "average_score": 0.0,
            "by_sector": [], "by_region": [], "by_stade": [], "timeline": []
        }


@app.get("/regions")
def get_regions():
    from ai_extraction.enrichissement.geocoder import CENTRES_REGIONS
    return [
        {"nom": region, "latitude": coords["lat"], "longitude": coords["lng"]}
        for region, coords in CENTRES_REGIONS.items()
    ]


@app.get("/sectors")
def get_sectors():
    return SECTORS


@app.get("/alerts/recent")
def recent_alerts(
    score_min: float = 80,
    limit: int = Query(10, ge=1, le=50),
):
    try:
        from ai_extraction.database import get_all_projets, init_db
        init_db()
        projets = get_all_projets(limit=limit)
        items = [
            _normalize_ai_project(p)
            for p in projets
            if (p.score_fiabilite or 0) >= score_min
        ][:limit]
        return {"score_min": score_min, "items": items}
    except Exception as exc:
        logger.warning("Alertes IA indisponibles: %s", exc)
        return {"score_min": score_min, "items": []}


@app.get("/config/scoring")
def get_scoring_config_endpoint():
    from ai_extraction.database import get_scoring_config

    return get_scoring_config()


@app.put("/config/scoring")
def update_scoring_config_endpoint(payload: ScoringConfigInput):
    from ai_extraction.database import (
        get_all_projets,
        save_projet,
        update_scoring_config,
    )
    from ai_extraction.validation.triangulation import calculer_score_fiabilite

    try:
        config = update_scoring_config(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    recalcules = 0
    for projet in get_all_projets(limit=5000):
        projet.score_fiabilite = calculer_score_fiabilite(projet)
        save_projet(projet)
        recalcules += 1

    return {"status": "ok", "config": config, "projets_recalcules": recalcules}


@app.post("/config/scoring/recalculate")
def recalculate_scoring_endpoint():
    from ai_extraction.database import get_all_projets, save_projet
    from ai_extraction.validation.triangulation import calculer_score_fiabilite

    recalcules = 0
    for projet in get_all_projets(limit=5000):
        projet.score_fiabilite = calculer_score_fiabilite(projet)
        save_projet(projet)
        recalcules += 1
    return {"status": "ok", "projets_recalcules": recalcules}


@app.get("/veille/scheduler/status")
def veille_scheduler_status():
    from ai_extraction.database import get_last_veille_run

    return {
        "enabled": os.getenv("VEILLE_SCHEDULER_DISABLED", "0") != "1",
        "interval_hours": float(os.getenv("VEILLE_INTERVAL_HOURS", "168")),
        "last_run": get_last_veille_run(),
    }


@app.post("/veille/run")
def veille_run_now():
    _run_veille_job()
    return veille_scheduler_status()


@app.get("/export/csv")
def export_csv(
    secteur: Optional[str] = None,
    region: Optional[str] = None,
    score_min: Optional[float] = None,
):
    from ai_extraction.database import get_all_projets, init_db
    init_db()
    projets = get_all_projets(limit=1000, secteur=secteur, region=region)
    if score_min is not None:
        projets = [p for p in projets if (p.score_fiabilite or 0) >= score_min]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Titre", "Secteur", "Region", "Porteur", "Montant MAD", "Stade", "Score Fiabilite"])
    for p in projets:
        writer.writerow([p.titre, p.secteur, p.region, p.porteur, p.montant_mad, p.stade_avancement, p.score_fiabilite])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=projets_investissement.csv"}
    )


@app.get("/export/pdf")
def export_pdf(
    secteur: Optional[str] = None,
    region: Optional[str] = None,
    score_min: Optional[float] = None,
):
    from ai_extraction.database import get_all_projets, init_db

    init_db()
    projets = get_all_projets(limit=1000, secteur=secteur, region=region)
    if score_min is not None:
        projets = [p for p in projets if (p.score_fiabilite or 0) >= score_min]

    total = sum(p.montant_mad or 0 for p in projets)
    lines = [
        f"Nombre de projets: {len(projets)}",
        f"Investissement total MAD: {total:,.0f}",
        "",
    ]
    for p in projets[:45]:
        lines.append(
            f"- {p.titre} | {p.secteur} | {p.region or 'N/A'} | "
            f"{p.montant_mad or 0:,.0f} MAD | score {p.score_fiabilite or 0}/100"
        )

    pdf = _simple_pdf("InvestiGator 43 - Export projets", lines)
    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=projets_investissement.pdf"},
    )


@app.get("/projects/{project_id}/export/pdf")
def export_project_pdf(project_id: str):
    from ai_extraction.database import get_projet, init_db

    init_db()
    projet = get_projet(project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    lines = [
        f"Secteur: {projet.secteur}",
        f"Region: {projet.region or 'N/A'}",
        f"Porteur: {projet.porteur or 'N/A'}",
        f"Montant MAD: {projet.montant_mad or 0:,.0f}",
        f"Stade: {projet.stade_avancement}",
        f"Score: {projet.score_fiabilite or 0}/100",
        "",
        _clean_public_text(projet.description) or "",
        "",
        (_clean_public_text(projet.fiche_synthetique) or "")[:2500],
    ]
    pdf = _simple_pdf(projet.titre, lines)
    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=projet_{project_id}.pdf"},
    )


# ═══════════════════════════════════════════════════════════════
# RAG — Interrogation des contenus indexes
# ═══════════════════════════════════════════════════════════════

def _load_rag():
    try:
        from ai_extraction.rag import (
            poser_question,
            ask_about_project,
            ingerer_datasets_finance,
            ingerer_projets,
            rag_store,
        )
        return poser_question, ask_about_project, ingerer_datasets_finance, ingerer_projets, rag_store
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Module RAG indisponible: {exc}") from exc


@app.get("/rag/status")
def rag_status():
    """État de l'index RAG (nombre de chunks, sources)."""
    try:
        *_, rag_store = _load_rag()
        rag_store.init()
        return {"ok": True, **rag_store.stats()}
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("RAG status indisponible: %s", exc)
        return {"ok": False, "total_chunks": 0, "par_source": []}


@app.post("/rag/ingest")
def rag_ingest(finance: bool = True, projets: bool = True):
    """
    Lance l'ingestion : contenus finance et/ou projets en base.
    Opération longue (téléchargement + embeddings).
    """
    poser, ask_proj, ingerer_finance, ingerer_proj, rag_store = _load_rag()
    rag_store.init()
    resultat = {}

    if finance:
        resultat["finance"] = ingerer_finance(reset=True)
    if projets:
        from ai_extraction.database import get_all_projets, init_db
        init_db()
        resultat["projets"] = ingerer_proj(get_all_projets(limit=1000), reset=True)

    return {"status": "ok", "details": resultat, **rag_store.stats()}


@app.post("/rag/ask")
def rag_ask(payload: RagQuestionInput):
    """Question générale au RAG sur l'ensemble des données indexées."""
    poser, *_ = _load_rag()
    return poser(payload.question, top_k=payload.top_k)


@app.post("/projects/{project_id}/ask")
def rag_ask_project(project_id: str, payload: RagQuestionInput):
    """Question RAG ancrée sur un projet précis + croisement données finance."""
    poser, ask_proj, *_ = _load_rag()
    from ai_extraction.database import get_projet, init_db
    init_db()
    projet = get_projet(project_id)
    if not projet:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    return ask_proj(projet, payload.question, top_k=payload.top_k)
