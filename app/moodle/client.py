from __future__ import annotations

import httpx

from app.config import settings


class MoodleClient:
    """Thin async wrapper around the Moodle Web Services REST endpoint.

    Only exposes a generic `call`. Do not add a method for a specific
    wsfunction until it has been verified against this instance's
    enabled-function list — see CLAUDE.md.
    """

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self._base_url = (base_url or settings.moodle_base_url).rstrip("/")
        self._token = token or settings.moodle_token

    async def call(self, wsfunction: str, **params: object) -> object:
        query: dict[str, object] = {
            "wstoken": self._token,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json",
            **params,
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/webservice/rest/server.php", params=query
            )
            response.raise_for_status()
            return response.json()
