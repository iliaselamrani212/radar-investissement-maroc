"""
synthese/fiche_generator.py - Fonctionnalité 10 : Génération de fiches projets
Aligné avec LIVRABLE 3 du brief SDG :
"Fiches projets synthétiques avec informations clés détectées automatiquement"
"""
import logging
import re
from typing import Dict, Any, List

from ..llm_client import llm
from ..models import ProjetInvestissement
from ..prompts import PROMPT_FICHE_PROJET

logger = logging.getLogger(__name__)


def nettoyer_fiche_publique(fiche: str) -> str:
    """Retire les mentions internes avant affichage ou export."""
    text = fiche or ""
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


def generer_fiche_projet(
    projet: ProjetInvestissement,
    enrichissement: Dict[str, Any] = None,
    sources_confirmees: List[Dict] = None,
) -> str:
    """
    Génère une fiche projet professionnelle en Markdown.
    Format consommable par le Dashboard ou exportable en PDF.
    """
    enrichissement = enrichissement or {}
    sources_confirmees = sources_confirmees or []

    # Format compact pour le LLM
    donnees_projet = _format_donnees_pour_llm(projet)
    contexte = _format_contexte_pour_llm(enrichissement)
    sources_str = _format_sources_pour_llm(sources_confirmees, projet)

    prompt = PROMPT_FICHE_PROJET.format(
        donnees_projet=donnees_projet,
        contexte=contexte,
        sources=sources_str,
        titre_projet=projet.titre,
        sous_secteur=projet.sous_secteur or "",
    )

    try:
        fiche = llm.complete(prompt, max_tokens=1500, temperature=0.2)
        return nettoyer_fiche_publique(fiche)
    except Exception as e:
        logger.error(f"Erreur génération fiche: {e}")
        return _fiche_fallback(projet, enrichissement, sources_confirmees)


def _format_donnees_pour_llm(projet: ProjetInvestissement) -> str:
    """Format compact des données projet"""
    montant_str = (
        f"{projet.montant_mad/1e9:.2f} Mds MAD"
        if projet.montant_mad and projet.montant_mad >= 1e9
        else f"{projet.montant_mad/1e6:.0f} M MAD"
        if projet.montant_mad
        else "Non précisé"
    )
    return f"""- Titre : {projet.titre}
- Description : {projet.description}
- Montant : {montant_str}
- Secteur : {projet.secteur}
- Sous-secteur : {projet.sous_secteur or 'Non précisé'}
- Région : {projet.region or 'Non précisée'}
- Ville : {projet.ville or 'Non précisée'}
- Porteur : {projet.porteur or 'Non précisé'}
- Stade : {projet.stade_avancement}
- Type : {projet.type_projet or 'Non précisé'}
- Emplois : {projet.nombre_emplois or 'Non précisé'}
- Date annonce : {projet.date_annonce or 'Non précisée'}
- Score fiabilité : {projet.score_fiabilite or 'N/A'}/100"""


def _format_contexte_pour_llm(enrichissement: Dict) -> str:
    """Format compact du contexte macro"""
    if not enrichissement:
        return "Aucun contexte disponible"

    parties = []
    if enrichissement.get("contexte_secteur"):
        cs = enrichissement["contexte_secteur"]
        parties.append(
            f"Secteur représente {cs.get('pib_pct')}% du PIB national, "
            f"investissement moyen sectoriel : {cs.get('investissement_moyen', 0)/1e6:.0f} M MAD, "
            f"croissance annuelle : {cs.get('croissance_annuelle')}%"
        )
    if enrichissement.get("contexte_region"):
        cr = enrichissement["contexte_region"]
        parties.append(
            f"Région : budget public {cr.get('budget_public', 0)/1e9:.1f} Mds MAD, "
            f"{cr.get('pib_regional_pct')}% du PIB régional, "
            f"secteurs dominants : {', '.join(cr.get('secteurs_dominants', []))}"
        )
    return ". ".join(parties)


def _format_sources_pour_llm(sources: List[Dict], projet: ProjetInvestissement) -> str:
    """Format compact des sources"""
    all_sources = [
        {
            "source": projet.source_principale,
            "url": projet.url_source,
            "niveau": 5,
        }
    ] + sources

    lignes = []
    for s in all_sources:
        if s.get("source"):
            lignes.append(
                f"- {s.get('nom_source', s['source'])} "
                f"(niveau {s.get('niveau_fiabilite', s.get('niveau', 5))}/5)"
            )
    return "\n".join(lignes) if lignes else "Aucune source"


def _fiche_fallback(
    projet: ProjetInvestissement,
    enrichissement: Dict,
    sources: List[Dict],
) -> str:
    """Fiche statique de secours si LLM échoue"""
    montant = (
        f"{projet.montant_mad/1e9:.2f} Mds MAD"
        if projet.montant_mad else "Non précisé"
    )
    return f"""# {projet.titre}

## Résumé exécutif
{projet.description}

## Points clés
- **Montant** : {montant}
- **Secteur** : {projet.secteur} {f'({projet.sous_secteur})' if projet.sous_secteur else ''}
- **Localisation** : {projet.region or 'N/A'} {f'- {projet.ville}' if projet.ville else ''}
- **Porteur** : {projet.porteur or 'Non précisé'}
- **Stade d'avancement** : {projet.stade_avancement}

## Analyse contextuelle
{enrichissement.get('analyse_contextuelle', 'Analyse contextuelle indisponible.')}

"""


def exporter_fiche_pdf(projet: ProjetInvestissement, output_path: str) -> str:
    """
    Exporte la fiche en PDF.
    Nécessite : pip install markdown weasyprint OU reportlab
    """
    fiche_md = nettoyer_fiche_publique(projet.fiche_synthetique or generer_fiche_projet(projet))

    try:
        import markdown
        from weasyprint import HTML
        html_content = markdown.markdown(fiche_md, extensions=["tables"])
        html_full = f"""
        <html><head><style>
        body {{ font-family: 'Helvetica', sans-serif; padding: 30px; }}
        h1 {{ color: #1a472a; border-bottom: 2px solid #1a472a; }}
        h2 {{ color: #2d5f3f; margin-top: 25px; }}
        ul {{ line-height: 1.6; }}
        </style></head><body>{html_content}</body></html>
        """
        HTML(string=html_full).write_pdf(output_path)
        logger.info(f"Fiche PDF générée : {output_path}")
        return output_path
    except ImportError:
        logger.warning("weasyprint non installé - export PDF impossible")
        # Fallback : sauvegarde markdown
        md_path = output_path.replace(".pdf", ".md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(fiche_md)
        return md_path
