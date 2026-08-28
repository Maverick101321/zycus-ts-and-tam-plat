"""Pydantic schemas for TAM Account Intelligence & Briefs."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AccountBriefRequest(BaseModel):
    """Request payload for generating an account brief."""
    account_id: str = Field(..., description="Unique customer account identifier")


class RiskFlag(BaseModel):
    """Specific risk signal grounded in ticket text or account escalation notes."""
    ticket_id: str = Field(
        ...,
        description="Associated ticket ID (e.g. TKT-10042) or 'ACCOUNT' if sourced from account escalation notes",
    )
    quote: str = Field(
        ...,
        description="Direct exact quote from the ticket body or account escalation notes",
    )
    reason: str = Field(
        ...,
        description="Explanation of why this excerpt presents a churn or customer health risk",
    )


class AccountBrief(BaseModel):
    """Structured executive brief summarizing customer health and risk points."""
    account_id: str = Field(..., description="Unique customer account identifier")
    company: str = Field(..., description="Customer company name")
    executive_summary: str = Field(
        ...,
        description="High-level 3-5 sentence summary referencing health status, trend, ARR, renewal date, and notes",
    )
    open_risks: List[RiskFlag] = Field(
        default_factory=list,
        description="List of verified risk flags directly quoted from customer interactions",
    )
    talking_points: List[str] = Field(
        default_factory=list,
        description="Concrete, actionable discussion points tailored for the TAM's next sync",
    )
    generated_at: str = Field(
        ...,
        description="ISO 8601 UTC timestamp when this brief was generated",
    )
