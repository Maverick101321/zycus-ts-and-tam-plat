from fastapi import APIRouter, HTTPException
from app.triage.agent import triage_ticket
from app.triage.schemas import TicketInput, TriageOutput

router = APIRouter(prefix="/triage", tags=["Triage"])


@router.post("/analyze", response_model=TriageOutput, summary="Triage an incoming support ticket")
def analyze_ticket(ticket: TicketInput) -> TriageOutput:
    """Classify product area, category, urgency, retrieve KB grounding, and draft first response."""
    try:
        return triage_ticket(ticket)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
