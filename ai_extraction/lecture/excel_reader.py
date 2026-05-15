"""
lecture/excel_reader.py - Fonctionnalité 2 : Lecture Excel avec IA
data.gov.ma publie des datasets Excel avec structure variable.
"""
import json
import logging
from typing import List, Dict

from ..llm_client import llm

logger = logging.getLogger(__name__)


def lire_excel_intelligemment(xlsx_path: str) -> List[Dict]:
    """
    Lit un fichier Excel avec structure variable.
    L'IA identifie automatiquement les colonnes pertinentes.
    """
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas non installé. pip install pandas openpyxl")
        return []

    resultats = []
    try:
        xl = pd.ExcelFile(xlsx_path)
        for sheet_name in xl.sheet_names:
            df = xl.parse(sheet_name)
            if df.empty:
                continue

            mapping = _identifier_colonnes_via_llm(df)
            structures = _structurer_df(df, mapping)
            resultats.extend(structures)

    except Exception as e:
        logger.error(f"Erreur lecture Excel {xlsx_path}: {e}")

    return resultats


def _identifier_colonnes_via_llm(df) -> Dict[str, str]:
    """L'IA identifie quelles colonnes correspondent aux 5 champs critiques"""
    prompt = f"""Voici les colonnes d'un fichier Excel officiel marocain :
{list(df.columns)}

Échantillon de 3 lignes :
{df.head(3).to_string()}

Identifie quelles colonnes correspondent à :
- montant : colonne contenant le montant d'investissement
- secteur : colonne du secteur d'activité
- region : colonne de la région
- porteur : colonne du nom du porteur de projet
- date : colonne de la date
- stade : colonne du stade d'avancement

Réponse JSON STRICT (mets null si une colonne n'existe pas) :
{{"montant": "nom_colonne", "secteur": "...", "region": "...", "porteur": "...", "date": "...", "stade": "..."}}"""

    try:
        return llm.complete_json(prompt)
    except Exception as e:
        logger.error(f"Erreur identification colonnes: {e}")
        return {}


def _structurer_df(df, mapping: Dict[str, str]) -> List[Dict]:
    """Transforme le DataFrame en liste de projets structurés"""
    projets = []
    for _, row in df.iterrows():
        projet = {}
        for champ, colonne in mapping.items():
            if colonne and colonne in df.columns:
                valeur = row.get(colonne)
                if valeur is not None and str(valeur).strip():
                    projet[champ] = valeur
        if projet:
            projets.append(projet)
    return projets
