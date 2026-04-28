import requests
from typing import List, Dict, Optional


class OllamaService:
    """
    Production-ready Ollama chat wrapper.

    Compatible with:
    - Gemma
    - Llama3
    - Mistral
    """

    def __init__(
        self,
        model: str = "gemma4:latest",
        base_url: str = "http://localhost:11434/api/chat",
        timeout: int = 180,
    ):
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def chat(
        self,
        messages: List[Dict],
        system: Optional[str] = None,
        temperature: float = 1,
    ) -> str:
        """
        Sends chat request to Ollama and returns text response.
        """

        payload = {
            "model": self.model,
            "messages": [],
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        # Inject system prompt (if provided)
        if system:
            payload["messages"].append({
                "role": "system",
                "content": system
            })

        # Add conversation messages
        payload["messages"].extend(messages)

        try:
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama request failed: {e}")

        try:
            data = response.json()
        except Exception:
            raise RuntimeError("Invalid JSON response from Ollama")

        if "message" not in data or "content" not in data["message"]:
            raise RuntimeError(f"Unexpected Ollama response: {data}")

        return data["message"]["content"].strip()

    def add_user_message(self, messages: List[Dict], content: str):
        messages.append({
            "role": "user",
            "content": content
        })

    def add_assistant_message(self, messages: List[Dict], content: str):
        messages.append({
            "role": "assistant",
            "content": content
        })