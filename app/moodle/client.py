from __future__ import annotations

import httpx

from app.config import settings
from app.schemas.moodle import (
    AssignmentSubmissionsResponse,
    CompletionStatusResponse,
    EnrolledUser,
    GradeItemsResponse,
    QuizAttemptsResponse,
)


def _flatten_params(params: dict[str, object], prefix: str = "") -> dict[str, object]:
    """Encode nested dict/list params the way Moodle's REST protocol expects.

    Moodle parses array/object-typed Web Service parameters from indexed
    keys, e.g. `assignmentids[0]=1&assignmentids[1]=2`, not repeated keys.
    """
    flat: dict[str, object] = {}
    for key, value in params.items():
        full_key = f"{prefix}[{key}]" if prefix else key
        if isinstance(value, dict):
            flat.update(_flatten_params(value, full_key))
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                indexed_key = f"{full_key}[{index}]"
                if isinstance(item, dict):
                    flat.update(_flatten_params(item, indexed_key))
                else:
                    flat[indexed_key] = item
        else:
            flat[full_key] = value
    return flat


class MoodleAPIError(Exception):
    """Raised when Moodle's REST endpoint returns an exception payload."""

    def __init__(self, wsfunction: str, errorcode: str, message: str) -> None:
        self.wsfunction = wsfunction
        self.errorcode = errorcode
        self.message = message
        super().__init__(f"{wsfunction} failed: [{errorcode}] {message}")


class MoodleClient:
    """Thin async wrapper around the Moodle Web Services REST endpoint.

    Methods here are only added once verified against this instance's
    enabled-function list (see core_webservice_get_site_info) — see
    CLAUDE.md. Do not add a method for a wsfunction that hasn't been
    confirmed enabled.
    """

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self._base_url = (base_url or settings.moodle_base_url).rstrip("/")
        self._token = token or settings.moodle_token

    async def call(self, wsfunction: str, **params: object) -> object:
        query: dict[str, object] = {
            "wstoken": self._token,
            "wsfunction": wsfunction,
            "moodlewsrestformat": "json",
        }
        query.update(_flatten_params(params))
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._base_url}/webservice/rest/server.php", params=query
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and "exception" in data:
                raise MoodleAPIError(
                    wsfunction, data.get("errorcode", "unknown"), data.get("message", "")
                )
            return data

    async def get_enrolled_users(self, course_id: int) -> list[EnrolledUser]:
        raw = await self.call("core_enrol_get_enrolled_users", courseid=course_id)
        return [EnrolledUser.model_validate(item) for item in raw]

    async def get_grade_items(self, course_id: int, user_id: int) -> GradeItemsResponse:
        raw = await self.call(
            "gradereport_user_get_grade_items", courseid=course_id, userid=user_id
        )
        return GradeItemsResponse.model_validate(raw)

    async def get_assignment_submissions(
        self, assign_id: int
    ) -> AssignmentSubmissionsResponse:
        raw = await self.call("mod_assign_get_submissions", assignmentids=[assign_id])
        return AssignmentSubmissionsResponse.model_validate(raw)

    async def get_quiz_attempts(self, quiz_id: int, user_id: int) -> QuizAttemptsResponse:
        raw = await self.call(
            "mod_quiz_get_user_attempts", quizid=quiz_id, userid=user_id
        )
        return QuizAttemptsResponse.model_validate(raw)

    async def get_completion_status(
        self, course_id: int, user_id: int
    ) -> CompletionStatusResponse:
        raw = await self.call(
            "core_completion_get_course_completion_status",
            courseid=course_id,
            userid=user_id,
        )
        return CompletionStatusResponse.model_validate(raw)
