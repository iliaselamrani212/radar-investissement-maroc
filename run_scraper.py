"""
run_scraper.py - Lance la collecte automatique depuis les sources officielles.

Usage :
    # Toutes les sources
    python run_scraper.py

    # Sources spécifiques
    python run_scraper.py --source amdie --source masen

    # Liste des sources disponibles
    python run_scraper.py --list
"""
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from ai_extraction.config import SOURCES_CONFIG
from ai_extraction.scraper import lancer_scraping


def main():
    parser = argparse.ArgumentParser(description="Radar Investissement Maroc — Scraper")
    parser.add_argument(
        "--source", action="append", dest="sources",
        help="Source à scraper (répétable). Ex: --source amdie --source masen"
    )
    parser.add_argument(
        "--list", action="store_true",
        help="Affiche toutes les sources disponibles"
    )
    args = parser.parse_args()

    if args.list:
        print("\nSources disponibles :\n")
        for sid, cfg in SOURCES_CONFIG.items():
            print(f"  {sid:25} — {cfg['nom']}")
            print(f"  {'':25}   {cfg['url']}\n")
        return

    sources = args.sources or None
    if sources:
        invalides = [s for s in sources if s not in SOURCES_CONFIG]
        if invalides:
            print(f"Sources inconnues : {invalides}")
            print(f"Lancez --list pour voir les sources disponibles.")
            sys.exit(1)

    stats = lancer_scraping(sources)

    print(f"\n{'='*50}")
    print(f"Résultat : {stats['projets_detectes']} projet(s) ajouté(s) en base")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
