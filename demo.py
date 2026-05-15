"""
demo.py - Script de démo end-to-end du Radar SDG Capital

Usage :
    python demo.py

Simule un cycle complet :
  1. Charge des documents officiels d'exemple
  2. Pipeline complet sur chacun (13 étapes)
  3. Sauvegarde en BDD
  4. Affiche les statistiques
  5. Génère le rapport de veille
"""
import logging
import sys
from pathlib import Path

# Permet d'exécuter sans installer en package
sys.path.insert(0, str(Path(__file__).parent))

from ai_extraction.pipeline import traiter_nouveau_document
from ai_extraction.database import (
    init_db, save_projet, get_all_projets, stats_globales,
)
from ai_extraction.veille.tendances import generer_rapport_veille_hebdo

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("demo")


# ═══════════════════════════════════════════════════════════════
# DOCUMENTS DE DÉMO (extraits de sources officielles)
# ═══════════════════════════════════════════════════════════════

DOCUMENTS_DEMO = [
    {
        "source": "amdie",
        "url": "https://www.amdie.gov.ma/fr/actualites/exemple-1",
        "title": "Signature d'une convention d'investissement de 2,5 milliards de dirhams "
                 "pour une usine automobile à Kénitra",
        "content": """L'Agence Marocaine de Développement des Investissements (AMDIE) 
        a annoncé la signature d'une convention d'investissement avec le groupe 
        Stellantis pour la construction d'une nouvelle usine de production de 
        véhicules électriques à Kénitra. 
        
        L'investissement total s'élève à 2,5 milliards de dirhams et devrait 
        créer 3000 emplois directs dans la région Rabat-Salé-Kénitra. 
        
        La convention a été signée en présence du Ministre de l'Industrie et 
        s'inscrit dans le cadre du Plan d'Accélération Industrielle. Le démarrage 
        des travaux est prévu pour le premier trimestre 2026 et la production 
        opérationnelle pour 2028.""",
    },
    {
        "source": "masen",
        "url": "https://www.masen.ma/fr/actualites/exemple-2",
        "title": "MASEN lance l'appel d'offres pour la centrale solaire Noor Midelt II "
                 "de 800 MW",
        "content": """L'Agence Marocaine pour l'Énergie Durable (MASEN) a officialisé 
        le lancement de l'appel d'offres pour la centrale solaire Noor Midelt II 
        d'une capacité de 800 MW. 
        
        Le projet, estimé à 800 millions d'euros, sera développé dans la région 
        Drâa-Tafilalet, à proximité de Midelt. Il combinera technologies 
        photovoltaïque et thermique à concentration. 
        
        Cette initiative s'inscrit dans la Stratégie Énergétique Nationale visant 
        52% d'énergies renouvelables dans le mix énergétique d'ici 2030. 
        Le démarrage des travaux est prévu en 2026.""",
    },
    {
        "source": "tangermed",
        "url": "https://www.tangermed.ma/communique/exemple-3",
        "title": "Inauguration du nouveau terminal à conteneurs TC4 à Tanger Med",
        "content": """L'Autorité Portuaire Tanger Med a inauguré ce mardi le nouveau 
        terminal à conteneurs TC4, portant la capacité totale du port à 9 millions 
        d'EVP par an. 
        
        L'investissement, réalisé par TM2 SA, filiale de l'Autorité Portuaire, 
        s'élève à 1,3 milliards de dirhams. Le terminal est opérationnel 
        depuis le 1er mai 2026 et emploie directement 850 personnes. 
        
        Cette extension renforce le positionnement de Tanger Med comme premier 
        hub logistique d'Afrique et de Méditerranée.""",
    },
    {
        "source": "ocp_group",
        "url": "https://www.ocpgroup.ma/communique/exemple-4",
        "title": "OCP Group annonce un programme d'investissement vert de 130 milliards "
                 "de dirhams",
        "content": """OCP Group, leader mondial du phosphate, a annoncé un programme 
        d'investissement vert de 130 milliards de dirhams sur la période 2023-2027. 
        
        Le programme couvre la production d'hydrogène vert, d'ammoniac vert et 
        l'extension des capacités à Khouribga, Béni Mellal-Khénifra. Les principaux 
        projets incluent une usine de dessalement et la généralisation de l'énergie 
        solaire pour alimenter les installations. 
        
        Ce plan stratégique s'inscrit dans la Stratégie Hydrogène Vert du Royaume 
        et créera environ 25 000 emplois directs et indirects.""",
    },
    {
        "source": "cri_casablanca",
        "url": "https://www.casainvest.ma/exemple-5",
        "title": "Approbation d'un projet de data center à Casablanca",
        "content": """Le Centre Régional d'Investissement Casablanca-Settat a approuvé 
        le projet de data center hyperscale porté par Maroc Datacenter dans la zone 
        de Bouskoura, Casablanca. 
        
        Le projet représente un investissement de 450 millions de dirhams et 
        devrait créer 120 emplois qualifiés. Le data center, d'une capacité de 
        20 MW IT, alimentera les besoins du Cloud Maroc et des entreprises 
        régionales. La mise en service est prévue mi-2027.""",
    },
]


# ═══════════════════════════════════════════════════════════════
# EXÉCUTION DE LA DÉMO
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n" + "=" * 70)
    print("🚀 RADAR SDG CAPITAL - DÉMO END-TO-END")
    print("=" * 70 + "\n")

    # === Étape 1 : Initialisation BDD ===
    logger.info("📦 Initialisation de la base de données...")
    init_db()

    # === Étape 2 : Traitement de chaque document ===
    projets_traites = []
    for i, doc in enumerate(DOCUMENTS_DEMO):
        print(f"\n{'─' * 70}\nDOCUMENT {i+1}/{len(DOCUMENTS_DEMO)}\n{'─' * 70}")
        try:
            projet = traiter_nouveau_document(
                document=doc,
                source=doc["source"],
                projets_existants=projets_traites,
            )
            if projet:
                save_projet(projet)
                projets_traites.append(projet)
        except Exception as e:
            logger.error(f"❌ Erreur sur document {i+1}: {e}", exc_info=True)
            continue

    # === Étape 3 : Statistiques ===
    print("\n" + "=" * 70)
    print("📊 STATISTIQUES GLOBALES")
    print("=" * 70)
    stats = stats_globales()
    print(f"\nNombre total de projets : {stats['total_projets']}")
    print(f"Investissement total : {stats['total_investissement_mds']} Mds MAD")
    print("\nPar secteur :")
    for s in stats["par_secteur"]:
        print(f"  - {s['secteur']:25} : {s['nb']} projets, {s['total_mad']/1e9:.2f} Mds MAD")
    print("\nPar région :")
    for r in stats["par_region"]:
        print(f"  - {r['region']:30} : {r['nb']} projets, {r['total_mad']/1e9:.2f} Mds MAD")

    # === Étape 4 : Rapport de veille ===
    print("\n" + "=" * 70)
    print("📰 RAPPORT DE VEILLE HEBDOMADAIRE")
    print("=" * 70)
    rapport = generer_rapport_veille_hebdo(get_all_projets())
    print(f"\n{rapport}\n")

    # === Étape 5 : Affichage d'une fiche projet ===
    print("\n" + "=" * 70)
    print("📋 EXEMPLE DE FICHE PROJET SYNTHÉTIQUE")
    print("=" * 70)
    if projets_traites:
        premier_projet = projets_traites[0]
        print(f"\n{premier_projet.fiche_synthetique}\n")

    print("\n✅ Démo terminée avec succès.\n")


if __name__ == "__main__":
    main()
