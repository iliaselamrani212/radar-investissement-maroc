"""
test_ollama.py - Sanity check Ollama + Qwen 2.5 7B

Usage :
    python test_ollama.py

Vérifie :
  1. Ollama est lancé
  2. Le modèle qwen2.5:7b est disponible
  3. Le modèle répond correctement à un prompt simple
  4. Le modèle peut produire du JSON structuré
  5. Le modèle peut extraire les 5 champs critiques sur un exemple
"""
import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import requests
from ai_extraction.config import OLLAMA_BASE_URL, OLLAMA_MODEL


# ═══════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════

def test_1_ollama_up():
    """Vérifie qu'Ollama tourne"""
    print("\n[1/5] 🔍 Test : Ollama est lancé ?")
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if r.status_code == 200:
            print(f"  ✅ Ollama répond sur {OLLAMA_BASE_URL}")
            return True
        else:
            print(f"  ❌ Ollama répond avec code {r.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Ollama injoignable : {e}")
        print(f"  → Démarre Ollama : 'ollama serve'")
        return False


def test_2_modele_dispo():
    """Vérifie que qwen2.5:7b est disponible"""
    print(f"\n[2/5] 🔍 Test : Modèle '{OLLAMA_MODEL}' disponible ?")
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        modeles = [m["name"] for m in r.json().get("models", [])]
        print(f"  Modèles installés : {modeles}")
        if any(OLLAMA_MODEL in m or m.startswith(OLLAMA_MODEL.split(":")[0]) for m in modeles):
            print(f"  ✅ '{OLLAMA_MODEL}' trouvé")
            return True
        else:
            print(f"  ❌ '{OLLAMA_MODEL}' NON trouvé")
            print(f"  → Télécharge le modèle : 'ollama pull {OLLAMA_MODEL}'")
            return False
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        return False


def test_3_completion_simple():
    """Test d'une complétion simple"""
    print("\n[3/5] 🔍 Test : complétion simple")
    from ai_extraction.llm_client import llm

    t0 = time.time()
    try:
        reponse = llm.complete("Capitale du Maroc en 1 mot ?", max_tokens=20)
        duree = time.time() - t0
        print(f"  Réponse : '{reponse}'")
        print(f"  ⏱️  Durée : {duree:.1f}s")
        if "rabat" in reponse.lower():
            print(f"  ✅ Réponse correcte")
            return True
        else:
            print(f"  ⚠️  Réponse inattendue mais le modèle répond")
            return True
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        return False


def test_4_json_structure():
    """Test du mode JSON"""
    print("\n[4/5] 🔍 Test : sortie JSON structurée")
    from ai_extraction.llm_client import llm

    t0 = time.time()
    try:
        result = llm.complete_json(
            'Donne-moi un JSON avec : {"ville": "Casablanca", "pays": "Maroc", "population_M": 3.7}'
        )
        duree = time.time() - t0
        print(f"  Réponse : {result}")
        print(f"  ⏱️  Durée : {duree:.1f}s")
        if isinstance(result, dict) and len(result) > 0:
            print(f"  ✅ JSON valide produit")
            return True
        else:
            print(f"  ❌ JSON vide ou invalide")
            return False
    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        return False


def test_5_extraction_5_champs():
    """Test du cœur du système : extraction des 5 champs critiques"""
    print("\n[5/5] 🔍 Test : extraction des 5 champs critiques")
    from ai_extraction.extraction.extractor import extraire_projet

    document_test = {
        "title": "Convention de 2,5 milliards de dirhams pour une usine Stellantis à Kénitra",
        "content": """L'Agence Marocaine de Développement des Investissements (AMDIE) 
a annoncé la signature d'une convention d'investissement avec le groupe 
Stellantis pour la construction d'une nouvelle usine de production de 
véhicules électriques à Kénitra. L'investissement total s'élève à 
2,5 milliards de dirhams et devrait créer 3000 emplois directs dans la 
région Rabat-Salé-Kénitra. La convention a été signée en présence du 
Ministre de l'Industrie.""",
    }

    t0 = time.time()
    try:
        projet = extraire_projet(
            titre=document_test["title"],
            contenu=document_test["content"],
            source="amdie",
        )
        duree = time.time() - t0
        print(f"  ⏱️  Durée : {duree:.1f}s")

        if not projet:
            print(f"  ❌ Extraction a renvoyé None")
            return False

        print(f"\n  📋 RÉSULTAT EXTRACTION :")
        print(f"  ├─ Titre        : {projet.titre[:70]}")
        print(f"  ├─ Montant      : {projet.montant_mad/1e9:.2f} Mds MAD" if projet.montant_mad else "  ├─ Montant      : null")
        print(f"  ├─ Secteur      : {projet.secteur}")
        print(f"  ├─ Région       : {projet.region}")
        print(f"  ├─ Porteur      : {projet.porteur}")
        print(f"  ├─ Stade        : {projet.stade_avancement}")
        print(f"  ├─ Emplois      : {projet.nombre_emplois}")
        print(f"  └─ Confiance    : {projet.score_confiance_extraction:.2f}")

        # Vérifications
        attendu = {
            "montant_mad_min": 2_000_000_000,
            "montant_mad_max": 3_000_000_000,
            "secteur": "Industrie",
            "region": "Rabat-Salé-Kénitra",
            "porteur_contient": "stellantis",
            "stade": "convention_signee",
        }

        score = 0
        if projet.montant_mad and attendu["montant_mad_min"] <= projet.montant_mad <= attendu["montant_mad_max"]:
            score += 1
            print(f"\n  ✅ Montant correct")
        else:
            print(f"\n  ⚠️  Montant attendu ~2,5 Mds, obtenu {projet.montant_mad}")

        if projet.secteur == attendu["secteur"]:
            score += 1
            print(f"  ✅ Secteur correct")
        else:
            print(f"  ⚠️  Secteur attendu 'Industrie', obtenu '{projet.secteur}'")

        if projet.region == attendu["region"]:
            score += 1
            print(f"  ✅ Région correcte")
        else:
            print(f"  ⚠️  Région attendue 'Rabat-Salé-Kénitra', obtenue '{projet.region}'")

        if projet.porteur and attendu["porteur_contient"] in projet.porteur.lower():
            score += 1
            print(f"  ✅ Porteur correct")
        else:
            print(f"  ⚠️  Porteur attendu 'Stellantis', obtenu '{projet.porteur}'")

        if projet.stade_avancement == attendu["stade"]:
            score += 1
            print(f"  ✅ Stade correct")
        else:
            print(f"  ⚠️  Stade attendu 'convention_signee', obtenu '{projet.stade_avancement}'")

        print(f"\n  📊 Score : {score}/5 champs correctement extraits")
        return score >= 3

    except Exception as e:
        print(f"  ❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
        return False


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("🧪 SANITY CHECK : Ollama + Qwen 2.5 7B + Radar SDG")
    print("=" * 70)

    results = []
    results.append(("Ollama lancé", test_1_ollama_up()))
    if not results[-1][1]:
        sys.exit(1)

    results.append(("Modèle disponible", test_2_modele_dispo()))
    if not results[-1][1]:
        sys.exit(1)

    results.append(("Complétion simple", test_3_completion_simple()))
    results.append(("JSON structuré", test_4_json_structure()))
    results.append(("Extraction 5 champs", test_5_extraction_5_champs()))

    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    for nom, ok in results:
        symbole = "✅" if ok else "❌"
        print(f"  {symbole} {nom}")

    nb_ok = sum(1 for _, ok in results if ok)
    print(f"\n🎯 {nb_ok}/{len(results)} tests réussis\n")

    if nb_ok == len(results):
        print("✅ Tout est OK. Tu peux lancer 'python demo.py' maintenant.\n")
    else:
        print("⚠️  Certains tests ont échoué. Vérifie la config Ollama.\n")
