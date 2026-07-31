from fastapi import FastAPI, HTTPException

from app.moodle.client import MoodleAPIError
from app.services.sync import sync_course

app = FastAPI(title="Moodle Digital Twin")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sync/{course_id}")
async def sync_course_endpoint(course_id: int) -> dict[str, int]:
    try:
        return await sync_course(course_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except MoodleAPIError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
