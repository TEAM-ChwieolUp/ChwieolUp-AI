from __future__ import annotations

import json
from typing import Any

import httpx

from app.core.config import settings


def generate_json_with_llm(system_prompt: str, user_prompt: str) -> dict[str, Any]:
    """Call the local Ollama server and return a parsed JSON object."""
    payload = {
        "model": settings.ollama_model,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False,
        "format": "json",
    }

    with httpx.Client(base_url=settings.ollama_base_url, timeout=60.0) as client:
        response = client.post("/api/generate", json=payload)
        response.raise_for_status()

    response_data = response.json()
    raw_content = response_data.get("response", "")
    if not isinstance(raw_content, str):
        raise ValueError("Ollama response payload is missing a JSON string in 'response'.")

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValueError("Failed to parse JSON returned by Ollama.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("LLM JSON response must be a JSON object.")

    return parsed
