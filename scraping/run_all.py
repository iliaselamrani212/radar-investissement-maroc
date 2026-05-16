from scrapers import (
    
  
    ammc,

    charika,
    thepulse,
    opendata_maroc,

    hcp,
    mcinet
)

from save_to_db import save_all


def safe_run(name, func):
    """
    Lance un scraper sans arrêter tout le programme si une source échoue.
    """
    try:
        print(f"\n▶️ Lancement {name}...")
        data = func()
        print(f"✅ {name} terminé : {len(data)} éléments")
        return data

    except Exception as e:
        print(f"❌ Erreur dans {name}: {e}")
        return []


def run_one_cycle():
    print("🔄 Cycle scraping entreprise + open data démarré")

    # Données investissement / entreprise / projet
    safe_run("AMMC", ammc.scrape_ammc)

    safe_run("Charika", charika.scrape_charika)
    safe_run("The Pulse", thepulse.scrape_thepulse)

    # Données contexte marché / économie / secteur
    safe_run("Open Data Maroc", opendata_maroc.scrape_opendata_maroc)

    safe_run("HCP", hcp.scrape_hcp)
    safe_run("Ministère Industrie", mcinet.scrape_mcinet)

    print("\n💾 Sauvegarde en base de données...")
    save_all()

    print("\n✅ Cycle terminé")


if __name__ == "__main__":
    run_one_cycle()
