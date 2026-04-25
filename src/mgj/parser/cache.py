"""
mgj.parser.cache
----------------
Local extraction-result cache.

Cache key: SHA-256 over (model_id, prompt_hash, input_hash). On cache
hit we skip the API call entirely and replay the prior parsed output.

Cache files live under ``submissions/<slug>/.cache/extractions/<key>.json``.
Each file is a JSON serialization of the ``ExtractionResult``.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from mgj.parser.backends import ExtractionResult


def cache_dir(submission_dir: Path) -> Path:
    return submission_dir / ".cache" / "extractions"


def cache_key(*, model_id: str, prompt_hash: str, input_hash: str) -> str:
    h = sha256()
    h.update(model_id.encode("utf-8"))
    h.update(b"|")
    h.update(prompt_hash.encode("utf-8"))
    h.update(b"|")
    h.update(input_hash.encode("utf-8"))
    return h.hexdigest()


def cache_path(submission_dir: Path, *, model_id: str, prompt_hash: str, input_hash: str) -> Path:
    return cache_dir(submission_dir) / f"{cache_key(model_id=model_id, prompt_hash=prompt_hash, input_hash=input_hash)}.json"


def load_cached(
    submission_dir: Path,
    *,
    model_id: str,
    prompt_hash: str,
    input_hash: str,
) -> ExtractionResult | None:
    p = cache_path(
        submission_dir,
        model_id=model_id,
        prompt_hash=prompt_hash,
        input_hash=input_hash,
    )
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    return ExtractionResult(**data)


def save_cached(submission_dir: Path, result: ExtractionResult) -> None:
    cache_dir(submission_dir).mkdir(parents=True, exist_ok=True)
    p = cache_path(
        submission_dir,
        model_id=result.model_id,
        prompt_hash=result.prompt_hash,
        input_hash=result.input_hash,
    )
    p.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n")
