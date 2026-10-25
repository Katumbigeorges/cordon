from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ModelResponse:
    content: dict[str, Any]
    provider: str
    model: str


class ModelProvider(Protocol):
    def complete(self, prompt: str) -> ModelResponse:
        """Return structured JSON for a bounded orchestration prompt."""


class DeterministicProvider:
    """Offline provider used by sample mode and tests."""

    def complete(self, prompt: str) -> ModelResponse:
        return ModelResponse(
            content={"hypotheses": ["internet_reachable_patient_impact"]},
            provider="sample",
            model="deterministic",
        )


class JsonHttpProvider:
    """Small JSON-in/JSON-out provider seam for a live model gateway."""

    def __init__(self, url: str, model: str, api_key: str | None = None, timeout: float = 10.0) -> None:
        self.url = url
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def complete(self, prompt: str) -> ModelResponse:
        payload = json.dumps({"model": self.model, "prompt": prompt}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = Request(self.url, data=payload, headers=headers, method="POST")
        with urlopen(request, timeout=self.timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body.get("content", body)
        if not isinstance(content, dict):
            raise ValueError("model provider response must contain a JSON object")
        return ModelResponse(content=content, provider="http", model=self.model)


def provider_from_environment() -> ModelProvider:
    url = os.getenv("MODEL_PROVIDER_URL")
    if not url:
        return DeterministicProvider()
    return JsonHttpProvider(
        url=url,
        model=os.getenv("MODEL_NAME", "cordon-model"),
        api_key=os.getenv("MODEL_PROVIDER_API_KEY"),
    )
