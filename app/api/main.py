import uvicorn
from fastapi import FastAPI, APIRouter
from app.api.routers.triage import router as triage_router

app = FastAPI(
    title="Support & TAM AI Tooling Suite",
    description="Internal AI tooling suite for Support Ticket Triage and TAM Account Intelligence",
    version="0.1.0",
)

# Empty routers for tam and retrieval modules (to be implemented in subsequent tasks)
tam_router = APIRouter(prefix="/tam", tags=["TAM"])
retrieval_router = APIRouter(prefix="/retrieval", tags=["Retrieval"])

app.include_router(triage_router)
app.include_router(tam_router)
app.include_router(retrieval_router)


@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="0.0.0.0", port=8000, reload=True)
