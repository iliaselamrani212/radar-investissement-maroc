"""
llm_client.py - Client Ollama LOCAL pour Qwen 2.5 7B
Aucune dépendance externe / aucune clé API requise.

Prérequis :
  1. Ollama installé : https://ollama.com/download
  2. Modèle téléchargé : ollama pull qwen2.5:7b
  3. Serveur lancé : ollama serve (auto-lancé sur Linux/Mac)
"""
import json
import logging
import re
from typing import Optional, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client Ollama local pour Qwen 2.5 7B.

    Compatible avec l'interface attendue par le reste du système :
      - complete(prompt, system) -> str
      - complete_json(prompt, system) -> dict
      - binaire(prompt) -> bool
    """

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        timeout: int = OLLAMA_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._check_ollama_ready()

    def _check_ollama_ready(self):
        """Vérifie qu'Ollama tourne et que le modèle est disponible"""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                modeles = [m["name"] for m in r.json().get("models", [])]
                modele_trouve = any(
                    self.model in m or m.startswith(self.model.split(":")[0])
                    for m in modeles
                )
                if modele_trouve:
                    logger.info(f"✅ Ollama prêt - modèle '{self.model}' disponible")
                else:
                    logger.warning(
                        f"⚠️  Modèle '{self.model}' introuvable. "
                        f"Modèles disponibles : {modeles}\n"
                        f"   → Lance : ollama pull {self.model}"
                    )
        except Exception as e:
            logger.warning(
                f"⚠️  Ollama injoignable sur {self.base_url}\n"
                f"   → Démarre Ollama : 'ollama serve'\n"
                f"   Erreur : {e}"
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> str:
        """Appel texte simple via l'API chat d'Ollama"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": 0.9,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"].strip()
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  Timeout Ollama après {self.timeout}s")
            raise
        except Exception as e:
            logger.error(f"❌ Erreur Ollama : {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def complete_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """
        Appel forcé en JSON structuré.
        Ollama supporte le mode JSON via format="json" (très fiable avec Qwen 2.5).
        """
        messages = []
        system_avec_json = (
            (system or "")
            + "\n\nIMPORTANT : Réponds UNIQUEMENT avec un JSON valide, "
              "sans aucun texte avant ou après, sans markdown, sans ```."
        )
        messages.append({"role": "system", "content": system_avec_json.strip()})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "format": "json",  # Mode JSON natif d'Ollama
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            content = data["message"]["content"].strip()
            return self._parse_json_robust(content)
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  Timeout Ollama après {self.timeout}s")
            return {}
        except Exception as e:
            logger.error(f"❌ Erreur Ollama JSON : {e}")
            return {}

    def _parse_json_robust(self, content: str) -> Dict[str, Any]:
        """Parse JSON avec plusieurs stratégies de fallback"""
        # Stratégie 1 : parse direct
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Stratégie 2 : retirer markdown ```json ... ```
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.MULTILINE)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Stratégie 3 : extraire le premier bloc { ... }
        match = re.search(r"\{[\s\S]*\}", content)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        logger.error(f"❌ Impossible de parser le JSON : {content[:200]}")
        return {}

    def binaire(self, prompt: str) -> bool:
        """Réponse binaire OUI/NON (économique en tokens)"""
        try:
            response = self.complete(prompt, temperature=0.0, max_tokens=10)
            return response.strip().upper().startswith("OUI")
        except Exception as e:
            logger.error(f"Erreur binaire LLM : {e}")
            return False

    def embed(self, text: str) -> list:
        """
        Embeddings via Ollama (optionnel - on garde sentence-transformers
        en parallèle car plus rapide pour la déduplication massive).
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("embedding", [])
        except Exception as e:
            logger.error(f"Erreur embeddings Ollama : {e}")
            return []


# Instance globale partagée
llm = OllamaClient()
