"""
mgj.parser.backends
-------------------
Provider-agnostic LLM extraction interface.

The parser depends on the ``LLMBackend`` Protocol; concrete backends
plug in via dependency injection. Today there's a Claude backend; a
GPT/Gemini/local backend can be added by implementing the same
interface without touching the rest of the parser.

The Protocol contract:
    extract(system_prompt, user_prompt, json_schema, max_tokens=...)
        → ExtractionResult{parsed, model_id, prompt_hash, input_hash, timestamp}

Backends should:
- Use structured output / tool use to produce JSON conforming to
  ``json_schema``.
- Cache stable parts of the prompt where supported (Claude: ephemeral
  prompt cache).
- Return a deterministic ``model_id`` string.

The backend MUST NOT do its own validation against ``json_schema`` —
the parser layer does that. The backend's job is "talk to the model
and return what it said as a dict."
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Callable, Protocol


@dataclass(frozen=True)
class ExtractionResult:
    """Structured response from an ``LLMBackend.extract`` call.

    ``parsed`` is the model's JSON output as a dict. ``model_id`` and
    the hashes give us provenance and cache-key material.
    """

    parsed: dict[str, Any]
    model_id: str
    prompt_hash: str
    input_hash: str
    timestamp: str


class LLMBackend(Protocol):
    """Provider-agnostic structured-extraction interface."""

    def extract(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        max_tokens: int = 4096,
    ) -> ExtractionResult: ...


# ---------------------------------------------------------------------------
# Claude backend (default)
# ---------------------------------------------------------------------------


class ClaudeBackend:
    """Anthropic Claude implementation.

    Uses tool-use to produce JSON output conforming to the schema. The
    ``system_prompt`` is sent with ``cache_control`` so multiple
    extractions over the same per-question prompt template hit the
    Anthropic prompt cache.
    """

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(self, model: str | None = None, api_key: str | None = None):
        # Imported lazily so the rest of the package works without anthropic installed.
        from anthropic import Anthropic

        self._model = model or self.DEFAULT_MODEL
        self._client = Anthropic(api_key=api_key) if api_key else Anthropic()

    def extract(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        max_tokens: int = 4096,
    ) -> ExtractionResult:
        tool = {
            "name": "record_extraction",
            "description": "Record the extracted entities for this catechism question.",
            "input_schema": json_schema,
        }
        msg = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
            tools=[tool],
            tool_choice={"type": "tool", "name": "record_extraction"},
        )
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use" and block.name == "record_extraction":
                return ExtractionResult(
                    parsed=block.input,
                    model_id=self._model,
                    prompt_hash=_sha(system_prompt),
                    input_hash=_sha(user_prompt),
                    timestamp=_now_iso(),
                )
        raise RuntimeError(
            f"Claude did not return a record_extraction tool_use block "
            f"(stop_reason={msg.stop_reason})"
        )


# ---------------------------------------------------------------------------
# Mock backend for tests
# ---------------------------------------------------------------------------


class MockLLMBackend:
    """Test double that returns whatever a callable produces.

    Use in unit tests to drive extraction deterministically without an
    API call. The callable receives ``(system_prompt, user_prompt)`` and
    returns the parsed dict that would have come from a real model.
    """

    def __init__(
        self,
        responder: Callable[[str, str], dict[str, Any]],
        *,
        model_id: str = "mock-llm-1",
    ):
        self._responder = responder
        self._model_id = model_id
        self.calls: list[tuple[str, str]] = []

    def extract(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, Any],
        max_tokens: int = 4096,
    ) -> ExtractionResult:
        self.calls.append((system_prompt, user_prompt))
        parsed = self._responder(system_prompt, user_prompt)
        return ExtractionResult(
            parsed=parsed,
            model_id=self._model_id,
            prompt_hash=_sha(system_prompt),
            input_hash=_sha(user_prompt),
            timestamp="2026-01-01T00:00:00Z",
        )


def _sha(s: str) -> str:
    return sha256(s.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


__all__ = [
    "ExtractionResult",
    "LLMBackend",
    "ClaudeBackend",
    "MockLLMBackend",
]
