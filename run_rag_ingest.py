"""
run_rag_ingest.py - Alimente le système RAG.

Usage :
    python run_rag_ingest.py                 # datasets finance + projets
    python run_rag_ingest.py --finance       # uniquement data.gov.ma finance
    python run_rag_ingest.py --projets       # uniquement les projets en base
    python run_rag_ingest.py --stats         # affiche l'état de l'index
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

from ai_extraction.rag import ingerer_datasets_finance, ingerer_projets, rag_store
from ai_extraction.database import get_all_projets


def main():
    parser = argparse.ArgumentParser(description="Ingestion RAG")
    parser.add_argument("--finance", action="store_true", help="Datasets data.gov.ma finance uniquement")
    parser.add_argument("--projets", action="store_true", help="Projets en base uniquement")
    parser.add_argument("--stats", action="store_true", help="Afficher l'état de l'index RAG")
    args = parser.parse_args()

    rag_store.init()

    if args.stats:
        print("=" * 60)
        print("ÉTAT DE L'INDEX RAG")
        print("=" * 60)
        print(rag_store.stats())
        return

    tout = not (args.finance or args.projets)

    if args.finance or tout:
        print("\n>>> Ingestion datasets finance data.gov.ma ...")
        stats = ingerer_datasets_finance(reset=True)
        print(f"    Ressources : {stats['ressources']} | Chunks : {stats['chunks']} | Erreurs : {stats['erreurs']}")

    if args.projets or tout:
        print("\n>>> Ingestion des projets en base ...")
        projets = get_all_projets(limit=1000)
        stats = ingerer_projets(projets, reset=True)
        print(f"    Projets indexés : {stats['projets_indexes']}")

    print("\n" + "=" * 60)
    print("ÉTAT FINAL :", rag_store.stats())
    print("=" * 60)


if __name__ == "__main__":
    main()
