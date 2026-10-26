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


class NvidiaOpenAIProvider:
    """NVIDIA NIM API provider using OpenAI-compatible interface for Nemotron models."""

    def __init__(
        self,
        api_key: str,
        model: str = "nvidia/nemotron-3.5-lightning-30b-a3b",
        base_url: str = "https://integrate.api.nvidia.com/v1",
        timeout: float = 45.0,
        use_reasoning: bool = False,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.use_reasoning = use_reasoning

    def complete(self, prompt: str) -> ModelResponse:
        """Call NVIDIA NIM API using OpenAI-compatible chat completions endpoint."""
        # Build the structured prompt for investigation planning
        system_prompt = """You are a hospital vulnerability investigation planner.
Given a vulnerability scenario, return JSON with an array of investigation hypotheses.
Focus on patient-safety-critical attack paths and internet-reachable exposures.

Return ONLY valid JSON in this exact format:
{"hypotheses": ["hypothesis1", "hypothesis2"]}

Example hypotheses:
- "internet_reachable_patient_impact"
- "credential_chain_to_ehr"
- "exploit_in_the_wild_kev_priority"
"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 1024,
            "stream": False,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))

            # Extract content from OpenAI-compatible response
            if "choices" not in body or not body["choices"]:
                raise ValueError("NVIDIA API returned no choices")

            message = body["choices"][0].get("message", {})
            
            # Check for reasoning_content first (Nemotron 3.5 Lightning)
            reasoning_content = message.get("reasoning_content")
            content_text = message.get("content")
            
            # Use reasoning if available and enabled, otherwise use content
            if reasoning_content and self.use_reasoning:
                response_text = reasoning_content
            elif content_text:
                response_text = content_text
            else:
                # Fallback: try to extract any text we can
                response_text = reasoning_content or str(message)

            # Parse JSON from the response
            try:
                content = json.loads(response_text)
            except json.JSONDecodeError:
                # If model returns text instead of JSON, try to extract JSON
                # Look for JSON object in the text
                import re
                json_match = re.search(r'\{[^}]*"hypotheses"\s*:\s*\[[^\]]*\][^}]*\}', response_text, re.DOTALL)
                if json_match:
                    try:
                        content = json.loads(json_match.group(0))
                    except:
                        content = {"hypotheses": ["internet_reachable_patient_impact"]}
                else:
                    content = {"hypotheses": ["internet_reachable_patient_impact"]}

            # Validate structure
            if not isinstance(content, dict) or "hypotheses" not in content:
                content = {"hypotheses": ["internet_reachable_patient_impact"]}

            return ModelResponse(
                content=content,
                provider="nvidia",
                model=self.model,
            )

        except Exception as error:
            # Fallback to deterministic on any error
            return ModelResponse(
                content={"hypotheses": ["internet_reachable_patient_impact"]},
                provider="nvidia-fallback",
                model=f"{self.model}-error:{str(error)[:50]}",
            )


def provider_from_environment() -> ModelProvider:
    """Create a model provider from environment variables.

    Priority order:
    1. NVIDIA_API_KEY → NvidiaOpenAIProvider (Nemotron via NIM)
    2. MODEL_PROVIDER_URL → JsonHttpProvider (custom gateway)
    3. Default → DeterministicProvider (sample mode)
    """
    # Check for NVIDIA API key first
    nvidia_key = os.getenv("NVIDIA_API_KEY")
    if nvidia_key:
        return NvidiaOpenAIProvider(
            api_key=nvidia_key,
            model=os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"),
            timeout=float(os.getenv("NVIDIA_TIMEOUT", "45.0")),
            use_reasoning=os.getenv("NVIDIA_USE_REASONING", "true").lower() == "true",
        )

    # Fall back to custom provider URL
    url = os.getenv("MODEL_PROVIDER_URL")
    if url:
        return JsonHttpProvider(
            url=url,
            model=os.getenv("MODEL_NAME", "cordon-model"),
            api_key=os.getenv("MODEL_PROVIDER_API_KEY"),
        )

    # Default to deterministic for sample mode
    return DeterministicProvider()
