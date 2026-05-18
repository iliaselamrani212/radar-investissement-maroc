# InvestiGator 43 - Module IA (100% LOCAL)

Système d'extraction et d'enrichissement automatique des projets d'investissement au Maroc, propulsé par **Qwen 2.5 7B via Ollama** en LOCAL.

> 🔒 **Zéro clé API. Zéro coût. Zéro envoi de données externes.**
> Tout tourne sur ta machine.

---

## ⚡ Démarrage rapide

### 1. Prérequis Ollama (déjà fait chez toi)

```bash
# Vérifier qu'Ollama est lancé
ollama serve

# Vérifier que le modèle est bien là
ollama list
# Doit afficher : qwen2.5:7b

# Si manquant :
ollama pull qwen2.5:7b
```

### 2. Installer les dépendances Python

```bash
cd radar_sdg
pip install -r requirements.txt
```

### 3. Tester qu'Ollama répond bien

```bash
python test_ollama.py
```

Ce script vérifie 5 choses :
- ✅ Ollama est lancé
- ✅ Le modèle qwen2.5:7b est dispo
- ✅ Le modèle répond à une question simple
- ✅ Le modèle produit du JSON valide
- ✅ Le modèle extrait correctement les 5 champs critiques

### 4. Lancer la démo complète

```bash
python demo.py
```

Pipeline end-to-end sur 5 documents officiels d'exemple.

### 5. Démarrer l'API pour le dashboard

```bash
uvicorn ai_extraction.api:app --reload --port 8000
```

API doc : http://localhost:8000/docs

---

## 🎯 Architecture LLM

```
┌────────────────────────────────────────┐
│  Ton frontend (Dashboard)              │
└────────────┬───────────────────────────┘
             │ HTTP
             ▼
┌────────────────────────────────────────┐
│  FastAPI (ai_extraction/api.py)        │
│  → Routes /api/projets, /api/stats...  │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  Pipeline IA (13 étapes)               │
│  → 12 fonctionnalités IA               │
└────────────┬───────────────────────────┘
             │ HTTP localhost:11434
             ▼
┌────────────────────────────────────────┐
│  OLLAMA (local)                        │
│  → Qwen 2.5 7B                         │
│  → Tourne sur GPU ou CPU               │
└────────────────────────────────────────┘
```

---

## 📦 Configuration

### Fichier `.env`

```bash
cp .env.example .env
```

Variables :
```bash
OLLAMA_BASE_URL=http://localhost:11434    # Défaut local
OLLAMA_MODEL=qwen2.5:7b                   # Modèle à utiliser
OLLAMA_TIMEOUT=180                        # 180s si CPU, 60s si GPU
```

### Choix du modèle Qwen

| Modèle | RAM/VRAM | Vitesse (CPU) | Qualité | Recommandation |
|--------|----------|---------------|---------|----------------|
| `qwen2.5:3b` | ~3 Go | ~5-15s | ⭐⭐⭐ | Test rapide |
| `qwen2.5:7b` | ~5 Go | ~15-45s | ⭐⭐⭐⭐ | **Recommandé** |
| `qwen2.5:14b` | ~10 Go | ~45-120s | ⭐⭐⭐⭐⭐ | Production / GPU |

Tu as déjà `qwen2.5:7b` → laisse cette config par défaut.

---

## Les 4 livrables

| # | Livrable | Module |
|---|----------|--------|
| 1 | **Dashboard interactif** | `api.py` (FastAPI) |
| 2 | **Base de données structurée** | `database.py` + `models.py` |
| 3 | **Fiches projets synthétiques** | `synthese/fiche_generator.py` |
| 4 | **Outils filtrage/priorisation** | `database.py` + `veille/recommandations.py` |

## ⚙️ Les 12 fonctionnalités IA

| # | Fonctionnalité | Fichier |
|---|----------------|---------|
| 1 | Filtrage de pertinence | `filtres/pertinence.py` |
| 2 | Lecture PDF/XLSX/DOCX | `lecture/*.py` |
| 3 | **Extraction des 5 champs critiques** | `extraction/extractor.py` |
| 4 | Auto-vérification | `extraction/verifier.py` |
| 5 | Déduplication sémantique | `dedup/embeddings_dedup.py` |
| 6 | Géocodage intelligent | `enrichissement/geocoder.py` |
| 7 | Enrichissement macroéconomique | `enrichissement/macro_context.py` |
| 8 | Détection d'anomalies | `validation/anomalies.py` |
| 9 | Triangulation entre sources | `validation/triangulation.py` |
| 10 | Génération de fiches | `synthese/fiche_generator.py` |
| 11 | Classification fine | `enrichissement/classifier_fin.py` |
| 12 | Veille stratégique | `veille/*.py` |

---

## 🐛 Dépannage

### Erreur "Ollama injoignable"

```bash
# Vérifie qu'Ollama tourne
ollama serve

# Sur Mac/Linux : lance dans un autre terminal
# Sur Windows : Ollama démarre automatiquement
```

### Extraction trop lente

Tu es probablement sur CPU. Options :
1. Utiliser un modèle plus petit : `OLLAMA_MODEL=qwen2.5:3b`
2. Augmenter le timeout : `OLLAMA_TIMEOUT=300`
3. Activer le GPU si tu en as un (CUDA / Metal)

### JSON invalide retourné par Qwen

Le client a 3 stratégies de fallback automatiques. Si ça plante quand même :
1. Baisser `temperature` à 0.0 dans `llm_client.py`
2. Augmenter `max_tokens` à 3000

### Score de confiance trop bas

Normal pour des documents très courts. Ajuste `SEUIL_CONFIANCE_MIN` dans `config.py` (défaut 0.3, peux baisser à 0.2 pour le MVP).

---

## Collecte institutionnelle

La collecte reste limitée à des contenus publics et institutionnels. Les références techniques ne sont pas affichées dans l'interface utilisateur.

---

## Phrase clé pour le jury

> Notre système IA accomplit **12 fonctionnalités distinctes** alignées avec le brief, avec un LLM 100% local (Qwen 2.5 7B via Ollama). **Zéro dépendance externe, zéro coût, souveraineté complète des données.**
