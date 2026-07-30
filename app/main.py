from fastapi import FastAPI

app = FastAPI(title="Moodle Digital Twin")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
