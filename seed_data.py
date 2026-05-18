"""
seed_data.py - Injecte 20+ projets réalistes directement en base (sans Ollama).
Permet de tester le dashboard immédiatement.

Usage : python seed_data.py
"""
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from ai_extraction.database import init_db, save_projet
from ai_extraction.models import ProjetInvestissement

PROJETS = [
    {
        "titre": "Centrale solaire Noor Midelt II — 800 MW",
        "description": "MASEN lance l'appel d'offres pour la centrale solaire Noor Midelt II d'une capacité de 800 MW, combinant technologies photovoltaïque et thermique à concentration.",
        "montant_mad": 8_800_000_000,
        "secteur": "Énergie",
        "sous_secteur": "Solaire",
        "region": "Drâa-Tafilalet",
        "ville": "Midelt",
        "porteur": "MASEN",
        "stade_avancement": "convention_signee",
        "source_principale": "masen",
        "score_confiance_extraction": 0.95,
        "score_fiabilite": 92,
        "nb_sources_confirmees": 3,
        "latitude": 32.6852,
        "longitude": -4.7333,
        "nombre_emplois": 2000,
        "tags_esg": ["transition_energetique", "creation_emplois", "exportation"],
        "strategies_nationales": ["Stratégie Énergétique Nationale"],
        "fiche_synthetique": """**CENTRALE SOLAIRE NOOR MIDELT II — 800 MW**
Porteur : MASEN | Région : Drâa-Tafilalet | Montant : 8,8 Mds MAD

**Contexte stratégique**
La centrale Noor Midelt II s'inscrit dans le programme national Noor, flagship de la stratégie énergétique du Maroc visant 52 % d'énergies renouvelables d'ici 2030. Située dans la province de Midelt, cette centrale hybride PV + CSP constitue la deuxième tranche d'un complexe solaire de 800 MW total.

**Description du projet**
Combinant technologie photovoltaïque (PV) et thermique à concentration (CSP avec stockage), Noor Midelt II offre une production continue jour et nuit, résolvant le problème d'intermittence solaire. La capacité installée de 800 MW permettra d'alimenter environ 2 millions de foyers marocains.

**Impact économique et social**
- 2 000 emplois directs durant la phase de construction
- 500 emplois permanents d'exploitation
- Réduction de la facture énergétique nationale estimée à 1,2 Md MAD/an
- Économie de 800 000 tonnes de CO₂ par an

**Alignement stratégique**
✓ Stratégie Énergétique Nationale 2030
✓ Plan Climatique National (NDC Maroc)
✓ Programme NOOR MASEN

**Score de fiabilité : 92/100** — Données confirmées par 3 sources institutionnelles (MASEN, MEF, AMDIE)""",
    },
    {
        "titre": "Usine Stellantis — Production véhicules électriques Kénitra",
        "description": "Signature d'une convention d'investissement avec Stellantis pour la construction d'une nouvelle usine de production de véhicules électriques à Kénitra.",
        "montant_mad": 2_500_000_000,
        "secteur": "Industrie",
        "sous_secteur": "Automobile",
        "region": "Rabat-Salé-Kénitra",
        "ville": "Kénitra",
        "porteur": "Stellantis",
        "stade_avancement": "convention_signee",
        "source_principale": "amdie",
        "score_confiance_extraction": 0.93,
        "score_fiabilite": 90,
        "nb_sources_confirmees": 2,
        "latitude": 34.2610,
        "longitude": -6.5802,
        "nombre_emplois": 3000,
        "tags_esg": ["creation_emplois", "souverainete_industrielle"],
        "strategies_nationales": ["Plan d'Accélération Industrielle"],
        "fiche_synthetique": """**USINE STELLANTIS — VÉHICULES ÉLECTRIQUES KÉNITRA**
Porteur : Stellantis | Région : Rabat-Salé-Kénitra | Montant : 2,5 Mds MAD

**Contexte stratégique**
Stellantis renforce sa présence industrielle au Maroc avec une deuxième usine à Kénitra, dédiée exclusivement aux véhicules électriques. Cette décision confirme le positionnement du Maroc comme hub automobile de référence pour l'Afrique et l'Europe du Sud.

**Description du projet**
L'usine couvrira 120 000 m² dans la zone industrielle de Kénitra et produira initialement 100 000 véhicules/an (modèles électriques des marques Citroën, Peugeot et Fiat). La ligne de production intègre une chaîne d'assemblage de batteries et un atelier de peinture last-gen.

**Impact économique et social**
- 3 000 emplois directs hautement qualifiés
- 8 000 emplois indirects dans l'écosystème sous-traitant
- Exportations estimées à 5 Mds MAD/an vers l'Europe
- Transfert de technologie VE (formation de 1 200 ingénieurs)

**Alignement stratégique**
✓ Plan d'Accélération Industrielle (PAI)
✓ Stratégie Automobile Maroc 2025
✓ Objectif 1 million de véhicules produits/an à l'horizon 2030

**Score de fiabilité : 90/100** — Convention signée et validée par AMDIE et CRI Kénitra""",
    },
    {
        "titre": "OCP Group — Programme d'investissement vert 130 Mds MAD",
        "description": "OCP Group annonce un programme d'investissement vert de 130 milliards de dirhams sur 2023-2027 couvrant hydrogène vert, ammoniac vert et extension des capacités.",
        "montant_mad": 130_000_000_000,
        "secteur": "Mines",
        "sous_secteur": "Phosphate",
        "region": "Béni Mellal-Khénifra",
        "ville": "Khouribga",
        "porteur": "OCP Group",
        "stade_avancement": "en_construction",
        "source_principale": "ocp_group",
        "score_confiance_extraction": 0.97,
        "score_fiabilite": 96,
        "nb_sources_confirmees": 4,
        "latitude": 32.8811,
        "longitude": -6.9063,
        "nombre_emplois": 25000,
        "tags_esg": ["transition_energetique", "creation_emplois", "exportation", "innovation_technologique"],
        "strategies_nationales": ["Stratégie Hydrogène Vert", "Plan d'Accélération Industrielle"],
        "fiche_synthetique": """**OCP GROUP — PROGRAMME D'INVESTISSEMENT VERT 130 Mds MAD**
Porteur : OCP Group | Région : Béni Mellal-Khénifra | Montant : 130 Mds MAD (2023–2027)

**Contexte stratégique**
Le plus grand programme d'investissement industriel de l'histoire du Maroc. OCP Group, leader mondial des phosphates avec 70 % des réserves mondiales, engage une transformation profonde de sa chaîne de valeur pour atteindre la neutralité carbone d'ici 2040.

**Description du projet**
Le programme couvre 5 axes majeurs :
1. Production d'hydrogène vert (1 Mt/an d'ici 2027) via électrolyse alimentée par EnR
2. Production d'ammoniac vert (3 Mt/an) pour engrais décarbonés
3. Extension des capacités d'extraction à Khouribga et Gantour (+30 %)
4. Dessalement de l'eau industrielle (200 000 m³/j)
5. Déploiement de 3 GW d'énergie solaire et éolienne en propre

**Impact économique et social**
- 25 000 emplois directs créés ou maintenus
- 60 000 emplois indirects dans l'écosystème fournisseurs
- Économies de 8 Mds MAD/an sur la facture énergétique
- Recettes d'exportation additionnelles estimées à 15 Mds MAD/an

**Alignement stratégique**
✓ Stratégie Nationale Hydrogène Vert
✓ Plan d'Accélération Industrielle (PAI)
✓ Objectifs Climatiques NDC Maroc 2030
✓ Feuille de route OCP 2030

**Score de fiabilité : 96/100** — Données vérifiées par 4 sources (OCP, MEF, AMDIE, Bourse Casablanca)""",
    },
    {
        "titre": "Terminal TC4 Tanger Med — Extension port",
        "description": "Inauguration du nouveau terminal à conteneurs TC4 portant la capacité totale du port à 9 millions d'EVP par an. Investissement de 1,3 Mds MAD.",
        "montant_mad": 1_300_000_000,
        "secteur": "Logistique",
        "sous_secteur": "Port",
        "region": "Tanger-Tétouan-Al Hoceïma",
        "ville": "Tanger Med",
        "porteur": "Tanger Med Port Authority",
        "stade_avancement": "operationnel",
        "source_principale": "tangermed",
        "score_confiance_extraction": 0.96,
        "score_fiabilite": 94,
        "nb_sources_confirmees": 3,
        "latitude": 35.8967,
        "longitude": -5.5078,
        "nombre_emplois": 850,
        "tags_esg": ["exportation", "developpement_regional"],
        "strategies_nationales": ["Plan d'Accélération Industrielle"],
        "fiche_synthetique": """**TERMINAL TC4 — TANGER MED**
Porteur : Tanger Med Port Authority | Région : Tanger-Tétouan | Montant : 1,3 Md MAD

**Contexte stratégique**
Tanger Med s'impose comme le 1er port africain et méditerranéen. Le terminal TC4, mis en service en 2024, porte la capacité totale du complexe à 9 millions d'EVP/an, consolidant sa position face aux grands hubs européens (Algésiras, Valence, Barcelone).

**Description du projet**
TC4 est un terminal de nouvelle génération équipé de grues STS dernière génération, d'un système de gestion automatisé des conteneurs (AGV), et d'une connexion directe au complexe ferroviaire et autoroutier. Le quai de 600 m peut accueillir les plus grands porte-conteneurs du monde (classe Ultra Large Container Vessels).

**Impact économique et social**
- 850 emplois directs hautement qualifiés
- Augmentation du trafic de transit estimée à +2 M EVP/an
- Recettes supplémentaires de 800 M MAD/an pour l'économie nationale
- Réduction des délais logistiques Europe-Afrique de 3 à 1,5 jours

**Alignement stratégique**
✓ Plan d'Accélération Industrielle (PAI)
✓ Stratégie Nationale Logistique 2030
✓ Positionnement Maroc hub continental Afrique-Europe

**Score de fiabilité : 94/100** — Projet opérationnel, données confirmées par Tanger Med SA et MEF""",
    },
    {
        "titre": "Data Center Maroc Datacenter — Bouskoura Casablanca",
        "description": "Projet de data center hyperscale approuvé par le CRI Casablanca-Settat dans la zone de Bouskoura. Capacité de 20 MW IT.",
        "montant_mad": 450_000_000,
        "secteur": "Tech & Digital",
        "sous_secteur": "Data center",
        "region": "Casablanca-Settat",
        "ville": "Casablanca",
        "porteur": "Maroc Datacenter",
        "stade_avancement": "approuve",
        "source_principale": "cri_casablanca",
        "score_confiance_extraction": 0.88,
        "score_fiabilite": 82,
        "nb_sources_confirmees": 2,
        "latitude": 33.5731,
        "longitude": -7.5898,
        "nombre_emplois": 120,
        "tags_esg": ["innovation_technologique", "souverainete_industrielle"],
        "strategies_nationales": ["Plan Maroc Digital 2030"],
        "fiche_synthetique": """**DATA CENTER BOUSKOURA — CASABLANCA**
Porteur : Maroc Datacenter | Région : Casablanca-Settat | Montant : 450 M MAD

**Contexte stratégique**
Dans un contexte de croissance exponentielle des besoins cloud et IA en Afrique, ce data center hyperscale répond à la demande des entreprises marocaines et régionales. Il positionne Casablanca comme hub numérique continental, dans le cadre de la stratégie Maroc Digital 2030.

**Description du projet**
Le campus de Bouskoura comprend 2 bâtiments data center avec une capacité IT de 20 MW, extensible à 50 MW à terme. Infrastructure Tier III certifiée, refroidissement adiabatique (PUE < 1,4), alimentation 100 % énergie renouvelable (PPAs solaires). Connexion aux câbles sous-marins AAE-1 et SMW-5.

**Impact économique et social**
- 120 emplois directs spécialisés (ingénieurs systèmes, cybersécurité)
- 400 emplois indirects (maintenance, services)
- Hébergement de 300+ entreprises clientes
- Réduction de la latence cloud pour les marchés africains de 40 ms

**Alignement stratégique**
✓ Plan Maroc Digital 2030
✓ Stratégie Nationale de Cybersécurité
✓ Attractivité des investissements tech internationaux (AWS, Azure)

**Score de fiabilité : 82/100** — Approuvé par CRI Casablanca-Settat, en attente de permis de construire""",
    },
    {
        "titre": "Parc éolien Taza — 120 MW",
        "description": "Convention signée pour la construction d'un parc éolien de 120 MW dans la région de Taza. Investissement porté par Nareva Holding.",
        "montant_mad": 1_800_000_000,
        "secteur": "Énergie",
        "sous_secteur": "Éolien",
        "region": "Fès-Meknès",
        "ville": "Taza",
        "porteur": "Nareva Holding",
        "stade_avancement": "convention_signee",
        "source_principale": "masen",
        "score_confiance_extraction": 0.90,
        "score_fiabilite": 86,
        "nb_sources_confirmees": 2,
        "latitude": 34.2098,
        "longitude": -4.0087,
        "nombre_emplois": 400,
        "tags_esg": ["transition_energetique", "developpement_regional"],
        "strategies_nationales": ["Stratégie Énergétique Nationale"],
        "fiche_synthetique": """**PARC ÉOLIEN TAZA — 120 MW**
Porteur : Nareva Holding | Région : Fès-Meknès | Montant : 1,8 Md MAD

**Contexte stratégique**
Nareva Holding (filiale Royale), premier opérateur éolien privé du Maroc, étend son parc de production dans le couloir éolien de Taza, l'un des gisements les plus ventés du pays (vitesse moyenne 9,5 m/s). Ce projet porte le parc Taza à 300 MW au total.

**Description du projet**
50 éoliennes Vestas de 2,4 MW chacune, sur une superficie de 3 500 ha dans les monts du Rif oriental. Durée de construction : 24 mois. Raccordement au réseau national ONEE via une ligne 225 kV de 45 km. Facteur de charge estimé : 45 %, soit ~475 GWh/an.

**Impact économique et social**
- 400 emplois en phase de construction (ouvriers, techniciens)
- 80 emplois permanents d'exploitation et maintenance
- Alimentation de 380 000 foyers en électricité verte
- Économies de 600 000 tonnes de CO₂/an

**Alignement stratégique**
✓ Stratégie Énergétique Nationale 2030 (cible 52 % EnR)
✓ Plan Maroc Éolien ONEE-MASEN
✓ Programme Loi 13-09 sur les énergies renouvelables

**Score de fiabilité : 86/100** — Convention signée avec MASEN, financement en cours de bouclage""",
    },
    {
        "titre": "Cité Mohammed VI Tanger Tech — Zone industrielle",
        "description": "Lancement de la phase 2 de la cité Mohammed VI Tanger Tech, zone industrielle intégrée de 2000 hectares dédiée aux industries du futur.",
        "montant_mad": 10_000_000_000,
        "secteur": "Industrie",
        "sous_secteur": "Zone industrielle",
        "region": "Tanger-Tétouan-Al Hoceïma",
        "ville": "Tanger",
        "porteur": "CDG Développement",
        "stade_avancement": "en_construction",
        "source_principale": "amdie",
        "score_confiance_extraction": 0.91,
        "score_fiabilite": 88,
        "nb_sources_confirmees": 3,
        "latitude": 35.7595,
        "longitude": -5.8340,
        "nombre_emplois": 50000,
        "tags_esg": ["creation_emplois", "souverainete_industrielle", "developpement_regional"],
        "strategies_nationales": ["Plan d'Accélération Industrielle"],
        "fiche_synthetique": """**CITÉ MOHAMMED VI TANGER TECH — PHASE 2**
Porteur : CDG Développement | Région : Tanger-Tétouan | Montant : 10 Mds MAD

**Contexte stratégique**
Tanger Tech est la plus grande zone industrielle intégrée jamais créée au Maroc : 2 000 ha dédiés aux industries du futur (IA, électronique, véhicule électrique, énergies propres). La phase 2 double la superficie et attire des investisseurs asiatiques et européens de premier rang.

**Description du projet**
Infrastructure clé en main : parcs industriels thématiques (électronique, automobile, chimie verte), zone résidentielle pour 300 000 habitants, campus universitaire, hôpital, centres de formation technique. Connexion directe au port Tanger Med et à l'autoroute A4.

**Impact économique et social**
- 50 000 emplois directs à terme (phase 1 + 2)
- 100 000 emplois indirects dans la région
- Attraction de 8 Mds USD d'IDE étrangers projetés
- Doublement du PIB régional de Tanger-Tétouan d'ici 2030

**Alignement stratégique**
✓ Plan d'Accélération Industrielle (PAI 2023-2026)
✓ Vision Royale industrie du futur
✓ Accord de partenariat Maroc-Chine (CCPIT)

**Score de fiabilité : 88/100** — En cours de construction, données AMDIE et CDG confirmées""",
    },
    {
        "titre": "Station balnéaire Taghazout Bay — Extension hôtelière",
        "description": "Signature d'une convention pour l'extension de la station Taghazout Bay avec 3 nouveaux hôtels 5 étoiles et un golf.",
        "montant_mad": 900_000_000,
        "secteur": "Tourisme",
        "sous_secteur": "Resort",
        "region": "Souss-Massa",
        "ville": "Agadir",
        "porteur": "Société d'Aménagement de Taghazout",
        "stade_avancement": "convention_signee",
        "source_principale": "amdie",
        "score_confiance_extraction": 0.87,
        "score_fiabilite": 80,
        "nb_sources_confirmees": 2,
        "latitude": 30.4278,
        "longitude": -9.5981,
        "nombre_emplois": 1500,
        "tags_esg": ["creation_emplois", "developpement_regional"],
        "strategies_nationales": ["Vision 2030 Tourisme"],
        "fiche_synthetique": """**TAGHAZOUT BAY — EXTENSION HÔTELIÈRE**
Porteur : SAT (Société d'Aménagement de Taghazout) | Région : Souss-Massa | Montant : 900 M MAD

**Contexte stratégique**
Taghazout Bay est la vitrine de la stratégie touristique nationale : station balnéaire premium de 615 ha sur la côte atlantique. L'extension répond à une demande croissante pour le tourisme de luxe et de surf, positionnant Agadir face à Dubaï et Marrakech.

**Description du projet**
Phase d'extension comprenant 3 hôtels 5 étoiles (1 200 chambres supplémentaires), un parcours de golf 18 trous signé Nicklaus Design, un centre de thalassothérapie international, et 80 villas de luxe en front de mer. Ouverture prévue : 2026.

**Impact économique et social**
- 1 500 emplois directs dans l'hôtellerie et services
- 4 000 emplois saisonniers dans la région d'Agadir
- Capacité d'accueil portée à 15 000 touristes/an supplémentaires
- Revenus touristiques additionnels estimés à 600 M MAD/an

**Alignement stratégique**
✓ Vision 2030 Tourisme (30 millions de touristes)
✓ Programme stations Plan Azur
✓ Préparation Coupe du Monde 2030 (ville de Marrakech)

**Score de fiabilité : 80/100** — Convention signée, études techniques en cours""",
    },
    {
        "titre": "Usine de dessalement Casablanca — 300 000 m³/j",
        "description": "Lancement du projet de dessalement d'eau de mer de grande capacité à Casablanca pour répondre aux besoins en eau potable de la région.",
        "montant_mad": 4_500_000_000,
        "secteur": "Infrastructure",
        "sous_secteur": "Eau",
        "region": "Casablanca-Settat",
        "ville": "Casablanca",
        "porteur": "ONEP",
        "stade_avancement": "approuve",
        "source_principale": "mef",
        "score_confiance_extraction": 0.89,
        "score_fiabilite": 85,
        "nb_sources_confirmees": 2,
        "latitude": 33.5731,
        "longitude": -7.5898,
        "nombre_emplois": 300,
        "tags_esg": ["transition_energetique", "developpement_regional"],
        "strategies_nationales": ["Plan National de l'Eau"],
        "fiche_synthetique": """**USINE DE DESSALEMENT CASABLANCA — 300 000 m³/j**
Porteur : ONEP (Office National de l'Eau Potable) | Région : Casablanca-Settat | Montant : 4,5 Mds MAD

**Contexte stratégique**
Face au stress hydrique croissant (sécheresses répétées, croissance démographique), le Maroc lance son plus grand projet de dessalement pour sécuriser l'alimentation en eau potable de 6 millions d'habitants de la métropole casablancaise. Priorité nationale inscrite au Programme National d'Approvisionnement en Eau Potable 2020-2027.

**Description du projet**
Usine SWRO (Osmose inverse eau de mer) de 300 000 m³/jour, extensible à 500 000 m³/j, sur le littoral atlantique à Ain Diab. Technologie dernier cri : membranes haute pression, récupération d'énergie (ERD), alimentation par parc solaire dédié de 150 MW.

**Impact économique et social**
- 300 emplois permanents d'exploitation
- Sécurisation hydrique de 6 millions d'habitants
- Réduction de la dépendance aux barrages (actuellement à 28 % de capacité)
- Coût de production : 6,5 MAD/m³ (compétitif avec l'eau conventionnelle)

**Alignement stratégique**
✓ Plan National de l'Eau 2020-2027
✓ Programme National d'Approvisionnement en Eau
✓ Objectifs Climatiques NDC Maroc (adaptation)

**Score de fiabilité : 85/100** — Approuvé par le Conseil des Ministres, appel d'offres en cours""",
    },
    {
        "titre": "Plateforme logistique Zenata — Phase 3",
        "description": "Extension de la plateforme logistique Zenata avec 150 000 m² d'entrepôts supplémentaires et une connexion ferroviaire.",
        "montant_mad": 650_000_000,
        "secteur": "Logistique",
        "sous_secteur": "Entrepôt",
        "region": "Casablanca-Settat",
        "ville": "Casablanca",
        "porteur": "Medlog",
        "stade_avancement": "en_construction",
        "source_principale": "cri_casablanca",
        "score_confiance_extraction": 0.86,
        "score_fiabilite": 79,
        "nb_sources_confirmees": 2,
        "latitude": 33.6167,
        "longitude": -7.4667,
        "nombre_emplois": 600,
        "tags_esg": ["creation_emplois", "exportation"],
        "strategies_nationales": ["Plan d'Accélération Industrielle"],
        "fiche_synthetique": """**PLATEFORME LOGISTIQUE ZENATA — PHASE 3**
Porteur : Medlog | Région : Casablanca-Settat | Montant : 650 M MAD

**Contexte stratégique**
Zenata est la principale plateforme logistique de la métropole casablancaise. La phase 3 répond à la saturation des capacités existantes, portée par le boom du e-commerce et la croissance des flux d'import-export marocains.

**Description du projet**
150 000 m² d'entrepôts nouvelle génération (classe A+) avec : racks haute densité 12 m, systèmes WMS intelligents, quais de chargement niveau 0,90 m et sol, connexion directe à la ligne ferroviaire de fret Casa-Port. Certification logistique ISO 9001 et normes douanières BADR.

**Impact économique et social**
- 600 emplois directs (logisticiens, caristes, douaniers)
- Réduction des coûts logistiques régionaux de 15 %
- Capacité de stockage de 800 000 palettes supplémentaires
- Délai de livraison J+1 pour l'ensemble du Grand Casablanca

**Alignement stratégique**
✓ Plan d'Accélération Industrielle (PAI)
✓ Stratégie Nationale Logistique 2030
✓ Développement corridor Casablanca-Tanger

**Score de fiabilité : 79/100** — En construction, données CRI confirmées""",
    },
    {
        "titre": "Hôpital Universitaire Mohammed VI Marrakech — Extension",
        "description": "Extension de l'hôpital universitaire Mohammed VI de Marrakech avec 500 lits supplémentaires et un centre de recherche oncologique.",
        "montant_mad": 1_200_000_000,
        "secteur": "Santé",
        "sous_secteur": "Hôpital",
        "region": "Marrakech-Safi",
        "ville": "Marrakech",
        "porteur": "Ministère de la Santé",
        "stade_avancement": "approuve",
        "source_principale": "mef",
        "score_confiance_extraction": 0.92,
        "score_fiabilite": 87,
        "nb_sources_confirmees": 2,
        "latitude": 31.6295,
        "longitude": -7.9811,
        "nombre_emplois": 800,
        "tags_esg": ["developpement_regional", "creation_emplois"],
        "strategies_nationales": [],
        "fiche_synthetique": """**CHU MOHAMMED VI MARRAKECH — EXTENSION**
Porteur : Ministère de la Santé | Région : Marrakech-Safi | Montant : 1,2 Md MAD

**Contexte stratégique**
Le CHU Mohammed VI de Marrakech est l'hôpital de référence pour les régions du Sud marocain (Marrakech-Safi, Béni Mellal, Souss). L'extension répond à la pression post-séisme 2023 sur les infrastructures sanitaires régionales et au manque criant de lits hospitaliers.

**Description du projet**
Extension du bâtiment principal : 500 lits supplémentaires (dont 80 en réanimation), nouveau bâtiment de 15 000 m² dédié à l'oncologie (imagerie PET-Scan, accélérateurs linéaires, unité d'hématologie), plateau technique de chirurgie robotique, et unité de télémédecine pour les provinces rurales.

**Impact économique et social**
- 800 emplois directs (médecins spécialistes, infirmiers, techniciens)
- Couverture sanitaire améliorée pour 4 millions d'habitants
- Réduction des évacuations médicales vers Casablanca (-60 % estimé)
- Formation de 200 résidents/an en spécialités rares

**Alignement stratégique**
✓ Plan Santé Maroc 2025 (couverture sanitaire universelle)
✓ Plan de Reconstruction post-séisme Al Haouz
✓ Objectifs ODD 3 (Santé et bien-être)

**Score de fiabilité : 87/100** — Budget approuvé par MEF, marché en cours de passation""",
    },
    {
        "titre": "Parc industriel Aéronef Casablanca — Phase 2",
        "description": "Lancement de la phase 2 du parc industriel dédié à l'aéronautique à Casablanca, avec 30 nouveaux hangars pour sous-traitants.",
        "montant_mad": 780_000_000,
        "secteur": "Industrie",
        "sous_secteur": "Aéronautique",
        "region": "Casablanca-Settat",
        "ville": "Casablanca",
        "porteur": "GIMAS",
        "stade_avancement": "convention_signee",
        "source_principale": "amdie",
        "score_confiance_extraction": 0.88,
        "score_fiabilite": 83,
        "nb_sources_confirmees": 2,
        "latitude": 33.3675,
        "longitude": -7.5898,
        "nombre_emplois": 2500,
        "tags_esg": ["souverainete_industrielle", "exportation", "creation_emplois"],
        "strategies_nationales": ["Plan d'Accélération Industrielle"],
        "fiche_synthetique": """**PARC AÉRONAUTIQUE CASABLANCA — PHASE 2**
Porteur : GIMAS (Groupement des Industriels Marocains de l'Aéronautique) | Région : Casablanca-Settat | Montant : 780 M MAD

**Contexte stratégique**
Le Maroc est le 3ème exportateur mondial de câblages aéronautiques et ambitionne de devenir dans le Top 20 mondial de la maintenance aéronautique. La phase 2 du parc Midparc Airport répond à l'afflux de nouveaux sous-traitants attirés par les donneurs d'ordre (Boeing, Airbus, Safran, Bombardier).

**Description du projet**
30 nouveaux hangars industriels de 2 000 à 8 000 m² chacun, adaptés aux normes aéronautiques (NADCAP, EN9100), avec ateliers de traitement de surface, zone de test climatique, et centre de formation aux métiers aéronautiques. Infrastructure certifiée par DGAC et FAA.

**Impact économique et social**
- 2 500 emplois directs qualifiés (ingénieurs, techniciens PART-66)
- 6 000 emplois indirects dans la filière
- Exportations additionnelles de 1,2 Md MAD/an
- Formation de 800 techniciens/an via OFPPT Aéro

**Alignement stratégique**
✓ Plan d'Accélération Industrielle — Filière Aéronautique
✓ Plan Maroc Export Plus
✓ Convention cadre GIMAS-Gouvernement 2023-2026

**Score de fiabilité : 83/100** — Convention signée GIMAS-AMDIE, financement en cours""",
    },
    {
        "titre": "Mine Khénifra — Extension capacité extraction cuivre",
        "description": "ONHYM et partenaires annoncent l'extension des opérations minières à Khénifra pour doubler la capacité d'extraction de cuivre.",
        "montant_mad": 2_100_000_000,
        "secteur": "Mines",
        "sous_secteur": "Cuivre",
        "region": "Béni Mellal-Khénifra",
        "ville": "Khénifra",
        "porteur": "ONHYM",
        "stade_avancement": "approuve",
        "source_principale": "onhym",
        "score_confiance_extraction": 0.85,
        "score_fiabilite": 81,
        "nb_sources_confirmees": 2,
        "latitude": 32.9333,
        "longitude": -5.6667,
        "nombre_emplois": 1200,
        "tags_esg": ["developpement_regional", "creation_emplois"],
        "strategies_nationales": [],
        "fiche_synthetique": """**MINE KHÉNIFRA — EXTENSION CUIVRE**
Porteur : ONHYM + Partenaires | Région : Béni Mellal-Khénifra | Montant : 2,1 Mds MAD

**Contexte stratégique**
Le cuivre est un métal stratégique de la transition énergétique (câbles électriques, VE, éoliennes). L'extension de la mine de Khénifra, l'une des plus importantes d'Afrique du Nord, double la capacité d'extraction et positionne le Maroc comme fournisseur clé pour l'industrie européenne du VE.

**Description du projet**
Extension en profondeur de la mine existante : galeries à -800 m, nouvelle station de pompage, enrichisseur flottation moderne, pipeline de concentré de 120 km vers le port de Casablanca. Capacité cible : 80 000 tonnes de cuivre raffiné/an.

**Impact économique et social**
- 1 200 emplois directs dans la mine et l'enrichissement
- 3 000 emplois indirects (transport, maintenance, services)
- Revenus d'exportation additionnels : 3,5 Mds MAD/an
- Développement socio-économique de la province de Khénifra

**Alignement stratégique**
✓ Stratégie Nationale des Ressources Minières
✓ Souveraineté sur les métaux critiques
✓ Exportation vers l'Union Européenne (Critical Raw Materials Act)

**Score de fiabilité : 81/100** — Approuvé par ONHYM, étude d'impact environnemental validée""",
    },
    {
        "titre": "Agropole Meknès — Centre agro-industriel",
        "description": "Inauguration de la première phase de l'agropole de Meknès, plateforme intégrée pour la transformation agroalimentaire.",
        "montant_mad": 560_000_000,
        "secteur": "Agriculture",
        "sous_secteur": "Agroalimentaire",
        "region": "Fès-Meknès",
        "ville": "Meknès",
        "porteur": "ADA",
        "stade_avancement": "operationnel",
        "source_principale": "mef",
        "score_confiance_extraction": 0.90,
        "score_fiabilite": 84,
        "nb_sources_confirmees": 2,
        "latitude": 33.8935,
        "longitude": -5.5547,
        "nombre_emplois": 900,
        "tags_esg": ["developpement_regional", "creation_emplois", "exportation"],
        "strategies_nationales": ["Maroc Vert"],
        "fiche_synthetique": """**AGROPOLE MEKNÈS — PLATEFORME AGRO-INDUSTRIELLE**
Porteur : ADA (Agence pour le Développement Agricole) | Région : Fès-Meknès | Montant : 560 M MAD

**Contexte stratégique**
Meknès, capitale agricole du Maroc, accueille la première agropole nationale : un pôle intégré combinant production, transformation, stockage et export de produits agroalimentaires. Pilier du Plan Maroc Vert, il vise à réduire les pertes post-récolte (actuellement 30 %) et à augmenter la valeur ajoutée exportée.

**Description du projet**
Plateforme de 300 ha comprenant : unités de transformation (conserverie, surgélation, conditionnement fruits & légumes), entrepôts frigorifiques (80 000 m³), laboratoire de contrôle qualité certifié HACCP, centre de formation OFPPT Agro, et guichet unique douanier pour les exportations.

**Impact économique et social**
- 900 emplois directs permanents
- 5 000 emplois saisonniers dans la région
- Réduction des pertes post-récolte de 30 % à 8 %
- Augmentation des exportations agricoles régionales de +40 %

**Alignement stratégique**
✓ Plan Maroc Vert — Pilier II (Petite et Moyenne Agriculture)
✓ Génération Green 2020-2030
✓ Plan Maroc Export (objectif 50 Mds MAD export agricole)

**Score de fiabilité : 84/100** — Projet opérationnel, données ADA et MEF confirmées""",
    },
    {
        "titre": "Ligne ferroviaire à Grande Vitesse Marrakech-Agadir",
        "description": "Annonce du projet de ligne LGV Marrakech-Agadir de 230 km. Convention signée entre l'ONCF et le gouvernement.",
        "montant_mad": 35_000_000_000,
        "secteur": "Infrastructure",
        "sous_secteur": "Ferroviaire",
        "region": "Souss-Massa",
        "ville": "Agadir",
        "porteur": "ONCF",
        "stade_avancement": "convention_signee",
        "source_principale": "mef",
        "score_confiance_extraction": 0.94,
        "score_fiabilite": 91,
        "nb_sources_confirmees": 3,
        "latitude": 30.4278,
        "longitude": -9.5981,
        "nombre_emplois": 10000,
        "tags_esg": ["developpement_regional", "creation_emplois", "transition_energetique"],
        "strategies_nationales": ["Vision 2030 Tourisme", "Maroc 2030 (Mondial Football)"],
        "fiche_synthetique": """**LGV MARRAKECH-AGADIR — 230 KM**
Porteur : ONCF | Région : Souss-Massa | Montant : 35 Mds MAD

**Contexte stratégique**
Deuxième ligne LGV marocaine après Casablanca-Tanger (Al Boraq), la LGV Marrakech-Agadir est une infrastructure structurante pour l'économie du sud du Maroc. Inscrite dans la préparation de la Coupe du Monde 2030 (Maroc co-organisateur), elle réduira le trajet Marrakech-Agadir de 3h à 1h15.

**Description du projet**
230 km de ligne nouvelle à grande vitesse (320 km/h), 5 gares dont Ouarzazate (desserte touristique), 8 tunnels et 15 viaducs dans le massif du Haut Atlas, dépôt de maintenance à Agadir. Matériel roulant : 12 rames Alstom Avelia Horizon. Alimentation 25 kV / 50 Hz.

**Impact économique et social**
- 10 000 emplois directs en phase de construction (BTP, génie civil)
- 2 000 emplois permanents d'exploitation
- Désenclavement de 3 millions d'habitants du sud du Maroc
- Impact touristique : +2 millions de touristes/an pour la région Souss

**Alignement stratégique**
✓ Vision 2030 Tourisme (30 millions de visiteurs)
✓ Maroc 2030 — Coupe du Monde FIFA
✓ Plan de mobilité durable ONCF 2035
✓ Développement régional Souss-Massa

**Score de fiabilité : 91/100** — Convention signée, études d'ingénierie avancées, financement BEI confirmé""",
    },
    {
        "titre": "Complexe pétrochimique Jorf Lasfar",
        "description": "OCP Group et partenaires internationaux lancent un complexe pétrochimique intégré à Jorf Lasfar pour la production d'engrais spéciaux.",
        "montant_mad": 8_000_000_000,
        "secteur": "Mines",
        "sous_secteur": "Pétrochimie",
        "region": "Casablanca-Settat",
        "ville": "El Jadida",
        "porteur": "OCP Group",
        "stade_avancement": "en_construction",
        "source_principale": "ocp_group",
        "score_confiance_extraction": 0.93,
        "score_fiabilite": 89,
        "nb_sources_confirmees": 3,
        "latitude": 33.2316,
        "longitude": -8.5077,
        "nombre_emplois": 3500,
        "tags_esg": ["exportation", "innovation_technologique", "creation_emplois"],
        "strategies_nationales": ["Plan d'Accélération Industrielle"],
        "fiche_synthetique": """**COMPLEXE PÉTROCHIMIQUE JORF LASFAR**
Porteur : OCP Group | Région : Casablanca-Settat (El Jadida) | Montant : 8 Mds MAD

**Contexte stratégique**
Jorf Lasfar est le plus grand hub industriel phosphatier au monde. Ce nouveau complexe pétrochimique intégré permet à OCP de monter en gamme : passer des engrais DAP/MAP standard à des fertilisants spéciaux à haute valeur ajoutée (engrais liquides, engrais de précision, spécialités crop nutrition).

**Description du projet**
Unités de production : acide phosphorique purifié (200 000 t/an), engrais spéciaux NPS/NPKS (500 000 t/an), sulfate d'ammonium, unité de granulation avancée. Intégration avec la centrale thermique existante, terminal portuaire dédié pour exportation directe.

**Impact économique et social**
- 3 500 emplois directs (ingénieurs chimistes, opérateurs, logisticiens)
- 8 000 emplois indirects dans la région d'El Jadida
- Revenus d'exportation additionnels : 5 Mds MAD/an
- Valeur ajoutée multiplié par 3 vs engrais conventionnels

**Alignement stratégique**
✓ Plan d'Accélération Industrielle — Chimie et Para-chimie
✓ Stratégie OCP 2030 (montée en gamme)
✓ Programme d'approvisionnement alimentaire africain (FAFFA)

**Score de fiabilité : 89/100** — En construction, données OCP et MEF confirmées par 3 sources""",
    },
    {
        "titre": "Cité Financière Mohammed VI Casablanca",
        "description": "Extension de la Casablanca Finance City avec 3 nouvelles tours de bureaux et un hôtel d'affaires 5 étoiles.",
        "montant_mad": 3_200_000_000,
        "secteur": "Finance",
        "sous_secteur": "Immobilier de bureau",
        "region": "Casablanca-Settat",
        "ville": "Casablanca",
        "porteur": "Casablanca Finance City",
        "stade_avancement": "en_construction",
        "source_principale": "ammc",
        "score_confiance_extraction": 0.89,
        "score_fiabilite": 84,
        "nb_sources_confirmees": 2,
        "latitude": 33.5731,
        "longitude": -7.5898,
        "nombre_emplois": 2000,
        "tags_esg": ["developpement_regional", "innovation_technologique"],
        "strategies_nationales": [],
        "fiche_synthetique": """**CASABLANCA FINANCE CITY — EXTENSION**
Porteur : CFC Authority | Région : Casablanca-Settat | Montant : 3,2 Mds MAD

**Contexte stratégique**
Casablanca Finance City est le 1er centre financier africain (classement GFCI 2024). L'extension répond à la demande croissante des multinationales pour installer leurs sièges régionaux Afrique à Casablanca, face à la concurrence de Nairobi et Johannesburg.

**Description du projet**
3 tours de bureaux de classe A+ (respectivement 25, 30 et 35 étages), un hôtel Hyatt Regency 5 étoiles de 350 chambres, un centre de conférences international (3 000 places), galerie commerciale premium, et infrastructure digitale fibré 100 Gb/s. Certification LEED Gold pour les 3 tours.

**Impact économique et social**
- 2 000 emplois directs dans le secteur financier et services
- Accueil de 150 entreprises multinationales supplémentaires
- Recettes fiscales additionnelles : 500 M MAD/an
- Renforcement du statut de hub financier africain

**Alignement stratégique**
✓ Stratégie d'attractivité des investissements étrangers
✓ Positionnement Casablanca hub financier africain
✓ Programme CFC 2030 (objectif 500 entreprises membres)

**Score de fiabilité : 84/100** — En construction, permis accordés, AMMC informée""",
    },
    {
        "titre": "Campus Université Mohammed VI Polytechnique — Ben Guerir",
        "description": "Extension du campus UM6P avec 5 nouveaux instituts de recherche appliquée et un centre d'innovation.",
        "montant_mad": 1_500_000_000,
        "secteur": "Éducation",
        "sous_secteur": "Université",
        "region": "Marrakech-Safi",
        "ville": "Ben Guerir",
        "porteur": "OCP Group / UM6P",
        "stade_avancement": "en_construction",
        "source_principale": "ocp_group",
        "score_confiance_extraction": 0.91,
        "score_fiabilite": 86,
        "nb_sources_confirmees": 2,
        "latitude": 32.2333,
        "longitude": -7.9500,
        "nombre_emplois": 500,
        "tags_esg": ["innovation_technologique", "creation_emplois"],
        "strategies_nationales": ["Plan Maroc Digital 2030"],
        "fiche_synthetique": """**UM6P BEN GUERIR — EXTENSION CAMPUS R&D**
Porteur : OCP Group / Université Mohammed VI Polytechnique | Région : Marrakech-Safi | Montant : 1,5 Md MAD

**Contexte stratégique**
L'UM6P est l'université panafricaine de référence pour les sciences appliquées et l'innovation. Classée Top 5 africaine, elle positionne le Maroc comme hub intellectuel et technologique continental. Cette extension double sa capacité de recherche dans des domaines stratégiques (IA, AgriTech, CleanTech, Minéralurgie).

**Description du projet**
5 nouveaux instituts : African Institute for Mathematical Sciences (AIMS-Maroc), Institut d'IA et Data Science (partenariat MIT Media Lab), Centre de Biotechnologies Agricoles, Institut CleanTech & Hydrogène, Centre de Minéralurgie Avancée. Capacité : 3 000 étudiants supplémentaires, 200 chercheurs internationaux.

**Impact économique et social**
- 500 emplois directs (professeurs, chercheurs, personnels)
- Formation de 3 000 ingénieurs/doctorants/an supplémentaires
- 40 startups deep tech lancées par an (via UM6P Ventures)
- Attraction de 30 M USD de fonds de recherche internationaux/an

**Alignement stratégique**
✓ Plan Maroc Digital 2030 (100 000 ingénieurs numériques)
✓ Stratégie Nationale de la Recherche 2030
✓ Partenariats MIT, UC Berkeley, Paris Sciences et Lettres

**Score de fiabilité : 86/100** — En construction, financement OCP Group et fonds souverains confirmés""",
    },
    {
        "titre": "Port de Dakhla Atlantique — Nouvelle infrastructure",
        "description": "Démarrage des travaux du nouveau port de Dakhla Atlantique, première grande infrastructure portuaire du sud du Maroc.",
        "montant_mad": 6_000_000_000,
        "secteur": "Infrastructure",
        "sous_secteur": "Port",
        "region": "Dakhla-Oued Ed-Dahab",
        "ville": "Dakhla",
        "porteur": "ANP",
        "stade_avancement": "en_construction",
        "source_principale": "mef",
        "score_confiance_extraction": 0.92,
        "score_fiabilite": 88,
        "nb_sources_confirmees": 3,
        "latitude": 23.7128,
        "longitude": -15.9341,
        "nombre_emplois": 4000,
        "tags_esg": ["developpement_regional", "exportation", "creation_emplois"],
        "strategies_nationales": ["Plan d'Accélération Industrielle"],
        "fiche_synthetique": """**PORT DE DAKHLA ATLANTIQUE**
Porteur : ANP (Agence Nationale des Ports) | Région : Dakhla-Oued Ed-Dahab | Montant : 6 Mds MAD

**Contexte stratégique**
Le Port de Dakhla Atlantique est l'infrastructure la plus stratégique du développement du Sahara marocain. Première grande infrastructure portuaire de l'Atlantique sud-marocain, il ouvre le Maroc sur l'Afrique sub-saharienne et réduit la dépendance aux ports du nord (Tanger, Casablanca) pour les échanges avec l'Afrique de l'Ouest.

**Description du projet**
Port en eaux profondes (-16 m), digue de protection de 3,2 km, terminal à conteneurs (500 000 EVP/an), terminal halieutique (1ère zone de pêche mondiale au poulpe), quai minéralier et énergies renouvelables, zone industrielle franche de 200 ha adjacente.

**Impact économique et social**
- 4 000 emplois directs dans le port et la zone franche
- 15 000 emplois indirects dans l'économie régionale
- Développement de la pêche industrielle : +500 M MAD de recettes/an
- Plateforme pour les exportations vers 16 pays d'Afrique de l'Ouest

**Alignement stratégique**
✓ Plan d'Accélération Industrielle — Développement Sahara
✓ Initiative Royale pour l'Atlantique (accès mer Sahel)
✓ Stratégie Nationale Portuaire 2030

**Score de fiabilité : 88/100** — En construction, travaux démarrés, financement BEI et MEF confirmés""",
    },
    {
        "titre": "Projet hydrogène vert Guelmim — 200 MW électrolyseurs",
        "description": "Convention signée pour la construction d'une unité de production d'hydrogène vert de 200 MW dans la région de Guelmim.",
        "montant_mad": 5_500_000_000,
        "secteur": "Énergie",
        "sous_secteur": "Hydrogène vert",
        "region": "Guelmim-Oued Noun",
        "ville": "Guelmim",
        "porteur": "ACWA Power Maroc",
        "stade_avancement": "convention_signee",
        "source_principale": "masen",
        "score_confiance_extraction": 0.90,
        "score_fiabilite": 85,
        "nb_sources_confirmees": 2,
        "latitude": 28.9887,
        "longitude": -10.0572,
        "nombre_emplois": 800,
        "tags_esg": ["transition_energetique", "exportation", "innovation_technologique"],
        "strategies_nationales": ["Stratégie Hydrogène Vert"],
        "fiche_synthetique": """**HYDROGÈNE VERT GUELMIM — 200 MW**
Porteur : ACWA Power Maroc | Région : Guelmim-Oued Noun | Montant : 5,5 Mds MAD

**Contexte stratégique**
Le Maroc dispose d'atouts exceptionnels pour l'hydrogène vert : irradiation solaire parmi les meilleures au monde, vent côtier puissant, côte atlantique pour l'export. Ce projet, premier de grande taille au Maroc, est un prototype pour la future filière H2V nationale visant 4 millions de tonnes/an d'ici 2050.

**Description du projet**
Parc solaire de 400 MW dédié + 200 MW d'électrolyseurs PEM (Proton Exchange Membrane), unité de compression et stockage H2, terminal export vers l'Europe via pipeline sous-marin (convention avec l'Espagne). Capacité : 80 000 tonnes H2/an, équivalent à 7 000 tonnes/an d'ammoniac vert.

**Impact économique et social**
- 800 emplois qualifiés (ingénieurs électrochimie, opérateurs H2)
- Formation d'une filière H2 marocaine (100 experts formés/an)
- Recettes d'exportation vers l'UE : 2 Mds MAD/an à terme
- Émissions évitées : 700 000 tonnes CO₂/an

**Alignement stratégique**
✓ Stratégie Nationale Hydrogène Vert (Feuille de Route 2030)
✓ Partenariat Maroc-Allemagne (H2 Global)
✓ Accord Maroc-UE sur l'énergie verte (REPowerEU)
✓ Plan Maroc Offshoring H2 (objectif exportateur net)

**Score de fiabilité : 85/100** — Convention signée MASEN-ACWA Power, études FEED en cours""",
    },
]


def generer_id(projet: dict) -> str:
    base = f"{projet['titre']}-{projet.get('porteur', '')}-{projet.get('region', '')}"
    return hashlib.md5(base.encode()).hexdigest()[:12]


def main():
    print("=" * 60)
    print("SEED DATA — Radar Investissement Maroc")
    print("=" * 60)

    init_db()
    print(f"\n✅ Base initialisée\n")

    saved = 0
    for i, data in enumerate(PROJETS):
        try:
            projet = ProjetInvestissement(
                id=generer_id(data),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                **data,
            )
            save_projet(projet)
            print(f"  [{i+1:02d}] ✅ {data['titre'][:55]}")
            saved += 1
        except Exception as e:
            print(f"  [{i+1:02d}] ❌ {data['titre'][:40]} — {e}")

    print(f"\n{'='*60}")
    print(f"✅ {saved}/{len(PROJETS)} projets insérés en base")
    print(f"📂 Base : data/radar_sdg.db")
    print(f"\n→ Ouvrir http://localhost:3000 pour voir le dashboard")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
