import logging
import os

import requests

from app.services.validation import safe_selection

LOG = logging.getLogger(__name__)
SYSTEM_PROMPT = (
    "Je bent MinorMatch. Selecteer uitsluitend IDs uit ALLOWED_MINORS. "
    "Verzin nooit een minor of eigenschap. Antwoord uitsluitend als JSON: "
    '{"recommended_ids":["id"]}. Maximaal drie unieke IDs.'
)


class LLMService:
    """Optionele AI-service: kiest alleen ID's uit lokale zoekresultaten.

    Ollama heeft voorrang als OLLAMA_BASE_URL is ingesteld. Zonder werkende
    provider gebruiken we de lokale ranking, dus de demo werkt offline.
    """

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "").rstrip("/")
        self.openai_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")

    @property
    def configured_mode(self) -> str:
        """Toon de configuratie; een onbereikbare provider valt alsnog terug."""
        if self.ollama_url:
            return "ollama"
        if self.openai_url and self.openai_key:
            return "openai-compatible"
        return "deterministic"

    def generate_response(self, profile, candidates: list[dict]) -> list[dict]:
        if not candidates:
            return []
        # De provider krijgt nooit de volledige catalogus. Alleen deze reeds
        # opgehaalde kandidaten mogen in het antwoord voorkomen.
        allowed = [item["minor"] for item in candidates]
        payload = {"profile": profile.model_dump(), "ALLOWED_MINORS": [
            {"id": m["id"], "name": m["name"], "description": m.get("description", "")}
            for m in allowed
        ]}
        try:
            if self.ollama_url:
                response = requests.post(self.ollama_url + "/api/chat", json={
                    "model": os.getenv("OLLAMA_MODEL", "llama3.2"), "stream": False,
                    "format": "json", "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": str(payload)},
                    ]}, timeout=8)
                response.raise_for_status()
                raw = response.json()["message"]["content"]
            elif self.openai_url and self.openai_key:
                response = requests.post(self.openai_url + "/chat/completions", json={
                    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    "response_format": {"type": "json_object"},
                    "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                                 {"role": "user", "content": str(payload)}],
                }, headers={"Authorization": f"Bearer {self.openai_key}"}, timeout=8)
                response.raise_for_status()
                raw = response.json()["choices"][0]["message"]["content"]
            else:
                # Geen Ollama of API ingesteld: dit is regelgebaseerd gedrag,
                # geen generatieve AI.
                return candidates[:3]
            import json
            selected = json.loads(raw).get("recommended_ids")
            # Onbekende of dubbele ID's worden door safe_selection verworpen.
            # Vrije LLM-tekst wordt nooit rechtstreeks aan de student getoond.
            return safe_selection(selected, candidates)
        except (requests.RequestException, KeyError, ValueError, TypeError):
            LOG.warning("LLM niet beschikbaar of ongeldig antwoord; veilige selectie gebruikt")
            return candidates[:3]
