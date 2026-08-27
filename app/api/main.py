import uvicorn
from fastapi import FastAPI, APIRouter

app = FastAPI(
    title="Support & TAM AI Tooling Suite",
    description="Internal AI tooling suite for Support Ticket Triage and TAM Account Intelligence",
    version="0.1.0",
)

# Empty routers for triage, tam, and retrieval modules
triage_router = APIRouter(prefix="/triage", tags=["Triage"])
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
