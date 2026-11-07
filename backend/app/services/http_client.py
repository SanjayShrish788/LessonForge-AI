"""Bounded provider requests. URLs/headers and response bodies never enter errors."""
import asyncio
import httpx
from .errors import ServiceError


async def request_json(client, method, url, *, provider, **kwargs):
    for attempt in range(2):
        try:
            response = await client.request(method, url, **kwargs)
            if response.status_code == 429 or response.status_code >= 500:
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                raise ServiceError(f"{provider} is rate limited or temporarily unavailable (HTTP {response.status_code}). Retry this stage later.")
            if response.status_code in (401, 403):
                raise ServiceError(f"{provider} rejected access. Check the API key, enabled API, quota and billing settings.")
            if response.status_code == 404 and provider == "Gemini":
                raise ServiceError("Gemini model is unavailable for this API key (HTTP 404). Choose an accessible model, update GEMINI_MODEL in backend/.env, and restart. Saved research is preserved.")
            if response.is_error:
                raise ServiceError(f"{provider} rejected the request (HTTP {response.status_code}). Check the configured model and API settings.")
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Expected object")
            return data
        except (httpx.TimeoutException, httpx.NetworkError):
            if attempt == 0:
                await asyncio.sleep(0.5)
                continue
            raise ServiceError(f"{provider} could not be reached. Check your connection and retry.") from None
        except (ValueError, TypeError):
            raise ServiceError(f"{provider} returned an unreadable response. Retry this stage.") from None
        except httpx.HTTPError:
            raise ServiceError(f"{provider} request failed. Check your connection and retry.") from None

