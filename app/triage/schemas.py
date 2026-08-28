from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TicketCategory(str, Enum):
    """Permitted category values exactly as defined in DATA_SCHEMA.md."""
    BUG = "Bug"
    FEATURE_REQUEST = "Feature Request"
    HOW_TO = "How-To"
    PERFORMANCE = "Performance"
    BILLING = "Billing"
    INTEGRATION = "Integration"
    ONBOARDING = "Onboarding"
    DATA_LOSS = "Data Loss"


class TicketUrgency(str, Enum):
    """Permitted urgency values exactly as defined in DATA_SCHEMA.md."""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class TicketInput(BaseModel):
    """Input ticket payload for triage classification."""
    subject: str = Field(..., description="Ticket subject line")
    body: str = Field(..., description="Full ticket body text")
    account_id: Optional[str] = Field(None, description="Associated customer account identifier")


class TriageOutput(BaseModel):
    """Structured result of the ticket triage analysis."""
    product_area: str = Field(..., description="Identified product module or product area")
    category: str = Field(..., description="Category from DATA_SCHEMA.md enum")
    urgency: str = Field(..., description="Urgency level (P1, P2, P3, P4)")
    reasoning: str = Field(..., description="Detailed rationale behind classification and urgency")
    matched_kb_doc: Optional[str] = Field(None, description="File path or heading of matching KB document")
    matched_kb_snippet: Optional[str] = Field(None, description="Relevant excerpt or troubleshooting steps from KB")
    recommended_team: str = Field(..., description="Recommended internal team to route the ticket to")
    draft_response: str = Field(..., description="Initial customer-facing draft response")
