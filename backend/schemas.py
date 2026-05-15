from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date, datetime
from uuid import UUID


class SourceSchema(BaseModel):
    name: str
    url: str
    niveau: int


class ProjectSchema(BaseModel):
    id: UUID
    titre: str
    resume_ai: Optional[str] = None
    montant_mad: Optional[float] = None
    secteur: str
    region: Optional[str] = None
    porteur: Optional[str] = None
    stade: Optional[str] = None
    date_annonce: Optional[date] = None
    sources: Optional[List[SourceSchema]] = []
    nb_sources_confirmees: Optional[int] = 1
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    score_fiabilite: Optional[float] = None
    score_details: Optional[Any] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    total: int
    items: List[ProjectSchema]
    limit: int
    offset: int


class StatsResponse(BaseModel):
    total_projects: int
    total_amount_mad: float
    average_score: float
    by_sector: list
    by_region: list
    by_stade: list
    timeline: list