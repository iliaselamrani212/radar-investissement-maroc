"""
prompts.py - Tous les prompts système IA centralisés
"""

# ═══════════════════════════════════════════════════════════════
# PROMPT MAÎTRE : EXTRACTION DES 5 CHAMPS CRITIQUES (Fonctionnalité 3)
# ═══════════════════════════════════════════════════════════════

SYSTEM_PROMPT_EXTRACTION = """Tu es un expert en analyse de projets d'investissement au Maroc.
Tu analyses des documents officiels publiés par des sources institutionnelles.

RÈGLES D'EXTRACTION STRICTES :

1. MONTANT (montant_mad) :
   - Cherche le montant TOTAL d'investissement
   - Convertis tout en MAD : 1 EUR ≈ 11 MAD, 1 USD ≈ 10 MAD
   - "1,5 milliards de dirhams" → 1500000000
   - "500 millions d'euros" → 5500000000
   - "1 milliard d'USD" → 10000000000
   - Si fourchette ("entre 1 et 2 Mds"), prends le MINIMUM
   - Si pas de chiffre explicite → null (NE DEVINE JAMAIS)

2. SECTEUR : choisis UN seul parmi cette liste :
   ["Industrie","Énergie","Agriculture","Pêche maritime","Tourisme",
    "Tech & Digital","Immobilier","Logistique","Santé","Éducation",
    "Infrastructure","Mines","Finance","Commerce","BTP","Autre"]
   
   Indices clés :
   - "usine, production, manufacturier, automobile" → Industrie
   - "solaire, éolien, hydrogène, MASEN, photovoltaïque" → Énergie
   - "data center, cloud, fintech, IA, digital" → Tech & Digital
   - "hôtel, resort, station balnéaire" → Tourisme
   - "phosphate, mine, OCP, minerai" → Mines
   - "port, aéroport, autoroute, train" → Infrastructure
   - "polyclinique, hôpital, pharmaceutique" → Santé

3. RÉGION : 12 régions exactes du Maroc
   Mappings ville → région :
   - Casablanca, Mohammedia, El Jadida, Settat → Casablanca-Settat
   - Rabat, Salé, Kénitra, Témara → Rabat-Salé-Kénitra
   - Tanger, Tétouan, Al Hoceïma, Tanger Med → Tanger-Tétouan-Al Hoceïma
   - Fès, Meknès, Ifrane, Taza → Fès-Meknès
   - Marrakech, Safi, Essaouira, El Kelaâ → Marrakech-Safi
   - Oujda, Nador, Berkane, Taourirt → Oriental
   - Béni Mellal, Khénifra, Azilal → Béni Mellal-Khénifra
   - Agadir, Tiznit, Taroudant, Inezgane → Souss-Massa
   - Errachidia, Ouarzazate, Midelt, Tinghir → Drâa-Tafilalet
   - Guelmim, Tan-Tan, Sidi Ifni → Guelmim-Oued Noun
   - Laâyoune, Boujdour, Tarfaya → Laâyoune-Sakia El Hamra
   - Dakhla, Aousserd → Dakhla-Oued Ed-Dahab

4. PORTEUR :
   - Nom OFFICIEL complet de l'entreprise/organisme
   - Si joint-venture, prends l'investisseur PRINCIPAL
   - Garde l'orthographe officielle ("OCP Group", pas "ocp")
   - Si plusieurs investisseurs : sépare par " / "

5. STADE D'AVANCEMENT :
   - "annonce" : intention exprimée
     ("envisage", "compte", "projette", "annonce")
   - "approuve" : approbation officielle obtenue
     ("approuvé par", "validé par la commission", "autorisé")
   - "convention_signee" : convention/contrat signé
     ("convention signée", "accord conclu", "signature")
   - "en_construction" : chantier en cours
     ("première pierre", "travaux entamés", "chantier")
   - "operationnel" : projet finalisé
     ("inauguré", "opérationnel", "mise en service")

6. SCORE_CONFIANCE (0 à 1) :
   - 0.9-1.0 : tous les champs explicitement dans le texte
   - 0.7-0.9 : 4/5 champs clairs, 1 déduit
   - 0.5-0.7 : 3/5 champs clairs
   - 0.3-0.5 : extraction incertaine
   - <0.3 : extraction très peu fiable

RÉPONSE OBLIGATOIRE : JSON strict uniquement. Pas de texte avant ou après."""


# ═══════════════════════════════════════════════════════════════
# PROMPT : FILTRAGE DE PERTINENCE (Fonctionnalité 1)
# ═══════════════════════════════════════════════════════════════

PROMPT_FILTRE_PERTINENCE = """Tu analyses le contenu du site officiel d'une institution marocaine.

Titre : {titre}
Aperçu : {snippet}

Ce contenu concerne-t-il un PROJET D'INVESTISSEMENT au Maroc ?

Critères OUI :
- Annonce d'investissement avec montant
- Convention/contrat d'investissement signé
- Création/extension d'entreprise importante
- Lancement de chantier industriel/infrastructure
- Approbation officielle d'un projet

Critères NON :
- Communiqué administratif général
- Nomination / changement de personnel
- Réunion / séminaire sans annonce concrète
- Bilan / rapport sans nouveauté projet
- Article de réglementation pure

Réponse : OUI ou NON uniquement (un seul mot)."""


# ═══════════════════════════════════════════════════════════════
# PROMPT : AUTO-VÉRIFICATION (Fonctionnalité 4)
# ═══════════════════════════════════════════════════════════════

PROMPT_AUTO_VERIFICATION = """Voici une extraction faite par une IA.
Vérifie chaque champ par rapport au document original.

DOCUMENT ORIGINAL :
{document}

EXTRACTION À VÉRIFIER :
- Montant : {montant} MAD
- Secteur : {secteur}
- Région : {region}
- Porteur : {porteur}
- Stade : {stade}

Pour CHAQUE champ, réponds :
- VERIFIE : explicitement présent dans le document
- DEDUIT_LOGIQUE : pas explicite mais déduction valide
- INCERTAIN : faible base dans le document
- ERRONE : contredit par le document

Format JSON STRICT :
{{
  "montant": "VERIFIE|DEDUIT_LOGIQUE|INCERTAIN|ERRONE",
  "secteur": "...",
  "region": "...",
  "porteur": "...",
  "stade": "..."
}}"""


# ═══════════════════════════════════════════════════════════════
# PROMPT : CONFIRMATION DOUBLON (Fonctionnalité 5)
# ═══════════════════════════════════════════════════════════════

PROMPT_CONFIRME_DOUBLON = """Ces deux extractions parlent-elles du MÊME projet d'investissement ?

Projet 1 :
- Titre : {titre1}
- Porteur : {porteur1}
- Région : {region1}
- Montant : {montant1} MAD
- Secteur : {secteur1}

Projet 2 :
- Titre : {titre2}
- Porteur : {porteur2}
- Région : {region2}
- Montant : {montant2} MAD
- Secteur : {secteur2}

Réponds OUI ou NON uniquement (un seul mot)."""


# ═══════════════════════════════════════════════════════════════
# PROMPT : GÉOCODAGE (Fonctionnalité 6)
# ═══════════════════════════════════════════════════════════════

PROMPT_GEOCODAGE = """Quel est le lieu principal mentionné dans ce texte marocain ?

Texte : {texte}

Identifie :
- ville_normalisee : nom officiel en français (ex: "Casablanca")
- type_lieu : "ville" | "zone_industrielle" | "port" | "aéroport"
- confiance : nombre entre 0 et 1

Format JSON STRICT :
{{"ville_normalisee": "...", "type_lieu": "...", "confiance": 0.9}}"""


# ═══════════════════════════════════════════════════════════════
# PROMPT : CLASSIFICATION FINE (Fonctionnalité 11)
# ═══════════════════════════════════════════════════════════════

PROMPT_CLASSIFICATION_FINE = """Classe ce projet d'investissement selon plusieurs dimensions :

Projet : {titre}
Description : {description}
Secteur principal : {secteur}

Fournis :

1. SOUS_SECTEUR (selon le secteur principal) :
   - Si Énergie : Solaire | Éolien | Hydrogène vert | Biomasse | Hydraulique | Gaz | Pétrole
   - Si Industrie : Automobile | Aéronautique | Textile | Agroalimentaire | Chimie | Pharma | Métallurgie
   - Si Tourisme : Hôtellerie | Resort | Tourisme culturel | Tourisme nature
   - Si Tech & Digital : Data center | Fintech | E-commerce | IA | SaaS | Télécoms
   - Sinon : null

2. TYPE_PROJET :
   - creation : nouvelle entité/usine
   - extension : agrandissement d'une entité existante
   - modernisation : mise à niveau technologique
   - partenariat : joint-venture
   - fusion_acquisition : rachat

3. STRATEGIES_NATIONALES (liste, max 3) parmi :
   ["Plan d'Accélération Industrielle","Stratégie Énergétique Nationale",
    "Plan Maroc Digital 2030","Maroc Vert","Plan Halieutis",
    "Vision 2030 Tourisme","Stratégie Hydrogène Vert","Maroc 2030 (Mondial Football)"]

4. TAGS_ESG (liste, max 4) parmi :
   ["transition_energetique","creation_emplois","innovation_technologique",
    "developpement_regional","souverainete_industrielle","exportation"]

Format JSON STRICT :
{{
  "sous_secteur": "...",
  "type_projet": "...",
  "strategies_nationales": ["..."],
  "tags_esg": ["..."]
}}"""


# ═══════════════════════════════════════════════════════════════
# PROMPT : FICHE PROJET SYNTHÉTIQUE (Fonctionnalité 10)
# Aligné avec LIVRABLE 3 : "Fiches projets synthétiques"
# ═══════════════════════════════════════════════════════════════

PROMPT_FICHE_PROJET = """Génère une fiche projet professionnelle pour SDG Capital, fonds d'investissement.

DONNÉES DU PROJET :
{donnees_projet}

CONTEXTE MACROÉCONOMIQUE :
{contexte}

SOURCES CONFIRMÉES :
{sources}

STRUCTURE OBLIGATOIRE EN MARKDOWN :

# {titre_projet}

## 📋 Résumé exécutif
(2-3 phrases factuelles : QUOI, QUI, COMBIEN, OÙ, QUAND)

## 🎯 Points clés
- **Montant** : ... (avec comparaison sectorielle si disponible)
- **Secteur** : ... ({sous_secteur} si présent)
- **Localisation** : ... (zone économique si pertinent)
- **Porteur** : ... (profil bref)
- **Calendrier** : ...

## 📊 Analyse contextuelle
(3-4 phrases : importance dans le secteur, cohérence avec stratégies nationales, effet d'entraînement attendu)

## ✅ Sources & fiabilité
- Nombre de sources : ...
- Niveau de fiabilité : ...
- Sources : ...

STYLE : Factuel, neutre, professionnel. Pas d'adjectifs marketing.
Chiffres précis uniquement issus des données fournies."""


# ═══════════════════════════════════════════════════════════════
# PROMPT : VEILLE STRATÉGIQUE HEBDO (Fonctionnalité 12-A)
# ═══════════════════════════════════════════════════════════════

PROMPT_VEILLE_HEBDO = """Analyse ces {nb} projets détectés cette semaine.

DONNÉES : {projets}

Génère un rapport de veille stratégique structuré en MARKDOWN :

# 📊 Rapport de veille hebdomadaire - SDG Capital

## 1. Chiffres clés
- Nombre de nouveaux projets : ...
- Investissement total annoncé : ... MAD
- Top 3 secteurs (avec montants) : ...
- Top 3 régions (avec montants) : ...

## 2. Tendances émergentes (3-5 insights)
(secteurs en accélération, nouvelles entreprises actives, évolutions géographiques)

## 3. Signaux faibles
(projets atypiques, mouvements inhabituels)

## 4. Projets à surveiller (top 5 par fiabilité × montant)
(liste avec 1 ligne d'analyse par projet)

## 5. Recommandations d'investigation
(2-3 axes que SDG Capital devrait creuser)

STYLE : Analyste senior, factuel, actionnable.
Pas d'emojis sauf dans les titres. Chiffres précis."""


# ═══════════════════════════════════════════════════════════════
# PROMPT : ALERTE PERSONNALISÉE (Fonctionnalité 12-B)
# ═══════════════════════════════════════════════════════════════

PROMPT_ALERTE_PERSONNALISEE = """Profil de l'analyste SDG :
- Secteurs d'intérêt : {secteurs}
- Régions cibles : {regions}
- Montant minimum : {montant_min} MAD
- Stades suivis : {stades}

Nouveau projet détecté :
{projet}

Évalue :
- pertinence_score : 0-100
- urgence : "faible" | "moyenne" | "elevee"
- raison_alerte : 1 phrase concise
- actions_suggerees : liste de 2-3 actions concrètes

Format JSON STRICT :
{{
  "pertinence_score": 75,
  "urgence": "moyenne",
  "raison_alerte": "...",
  "actions_suggerees": ["...", "..."]
}}"""


# ═══════════════════════════════════════════════════════════════
# PROMPT : ANALYSE CONTEXTUELLE MACRO (Fonctionnalité 7)
# ═══════════════════════════════════════════════════════════════

PROMPT_ANALYSE_MACRO = """Génère une analyse en 2 phrases sur l'importance de ce projet
dans le contexte macroéconomique marocain.

Projet : {titre}
Montant : {montant} MAD
Secteur : {secteur} (représente {pib_pct}% du PIB national)
Région : {region}
Budget public régional : {budget_region} MAD

Style : factuel, professionnel, chiffré. Pas de superlatifs."""
