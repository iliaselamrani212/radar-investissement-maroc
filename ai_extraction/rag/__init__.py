"""
Module RAG — Retrieval-Augmented Generation.

Permet d'interroger les datasets finance de data.gov.ma et le contexte
projet en langage naturel, avec réponses générées par Ollama Qwen 2.5
ancrées sur des données réelles (anti-hallucination via citations).
"""
from .store import RagStore, rag_store
from .engine import poser_question, ask_about_project
from .ingestion import (
    ingerer_datasets_finance,
    ingerer_projets,
    ingerer_source_scrapee,
)

__all__ = [
    "RagStore",
    "rag_store",
    "poser_question",
    "ask_about_project",
    "ingerer_datasets_finance",
    "ingerer_projets",
    "ingerer_source_scrapee",
]
