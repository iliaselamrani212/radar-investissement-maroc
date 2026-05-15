from sqlalchemy import Column, Integer, Text, Numeric, Boolean, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from database import Base
import uuid


class RawArticle(Base):
    __tablename__ = "raw_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    url = Column(Text, unique=True, nullable=False)
    source = Column(Text, nullable=False)
    niveau_source = Column(Integer, default=3)
    content = Column(Text)
    scraped_at = Column(DateTime, server_default=func.now())
    processed = Column(Boolean, default=False)


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titre = Column(Text, nullable=False)
    resume_ai = Column(Text)
    montant_mad = Column(Numeric)
    secteur = Column(Text, nullable=False)
    region = Column(Text)
    porteur = Column(Text)
    stade = Column(Text, default="annoncé")
    date_annonce = Column(Date)
    sources = Column(JSONB, default=[])
    nb_sources_confirmees = Column(Integer, default=1)
    latitude = Column(Numeric)
    longitude = Column(Numeric)
    embedding = Column(JSONB)
    score_fiabilite = Column(Numeric)
    score_details = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())


class Region(Base):
    __tablename__ = "regions"

    nom = Column(Text, primary_key=True)
    latitude = Column(Numeric)
    longitude = Column(Numeric)