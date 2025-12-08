from fastapi import FastAPI

app = FastAPI(
    title="Code-Inspector",
    description="A simple workflow engine for AI engineering assignment",
    version="1.0.0"
)

@app.get("/", tags=["System"])
def health_check() -> dict[str, str]:
    """
    Perform a health check on the API.

    Returns:
        dict[str, str]: System status and message
    """
    return {"status": "active", "message": "Engine is running"}
