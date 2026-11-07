"""Minimal live LLM connectivity check using the application's own configuration.

This never prints or logs the API key or raw provider payloads. It performs one
small structured request through the real llm_service boundary so that a failing
credential, model id, or endpoint is surfaced before any expensive workflow runs.

Usage (from the project root, with the backend virtualenv active):
    python scripts/verify_llm.py            # uses LLM_PROVIDER from backend/.env
    python scripts/verify_llm.py --provider openai
    python scripts/verify_llm.py --provider gemini
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from pydantic import BaseModel, Field  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.services import llm_service  # noqa: E402
from app.services.errors import ServiceError  # noqa: E402


class Probe(BaseModel):
    label: str = Field(min_length=1, max_length=40)
    http_status_meaning: int = Field(ge=100, le=599)


async def run(provider: str | None) -> int:
    settings = get_settings()
    if provider:
        settings = settings.model_copy(update={"llm_provider": provider})
    configured_provider = settings.llm_provider
    key_name = f"{configured_provider}_api_key"
    model_name = getattr(settings, f"{configured_provider}_model")
    print(f"provider={configured_provider} model={model_name} key_present={bool(getattr(settings, key_name, ''))}")
    if not getattr(settings, key_name, ""):
        print(f"BLOCKED: {key_name.upper()} is empty in backend/.env")
        return 2
    system = "Return JSON describing the label for HTTP 404 and its numeric status code."
    try:
        result = await llm_service.complete(system, {"request": "HTTP 404"}, Probe, settings)
    except ServiceError as exc:
        print(f"FAILED: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 - surface unexpected error type only
        print(f"FAILED: unexpected {type(exc).__name__}")
        return 1
    print(f"OK: structured response accepted -> {result.model_dump()}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["openai", "gemini"], default=None)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.provider)))
