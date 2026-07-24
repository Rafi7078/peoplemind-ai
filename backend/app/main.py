from fastapi import FastAPI
app = FastAPI(
    title="PeopleMind AI API",
    description="Backend API for the PeopleMind AI HR Intelligence and Management Assistant.",
    version="0.1.0",
)
@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Welcome to PeopleMind AI",
        "status": "running",
    }
@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {
        "service": "PeopleMind AI API",
        "status": "healthy",
        "version": "0.1.0",
    }
