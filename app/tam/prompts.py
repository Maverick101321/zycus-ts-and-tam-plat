"""Prompts and prompt versioning for TAM Account Intelligence & Briefs."""

import json
from typing import Any, Dict, List, Tuple

PROMPT_VERSION: str = "v1"

CHANGELOG: Dict[str, str] = {
    "v1": "Initial TAM account health brief prompt with grounded direct quotes for risk flags, strict JSON schema, and executive summary guidelines."
}


def build_account_brief_prompt(
    account: Dict[str, Any], tickets: List[Dict[str, Any]]
) -> Tuple[str, str]:
    """Constructs system and user prompts for generating a TAM executive account brief."""
    system_prompt = """You are an expert Technical Account Management (TAM) Intelligence Assistant.
Your task is to analyze customer account data and their recent support tickets to produce a concise, actionable executive account brief.

### GUIDELINES:
1. **Executive Summary**: 3-5 sentences summarizing the account's overall status. You MUST explicitly reference:
   - Current health status and usage trend
   - ARR and seat utilization (active vs licensed seats)
   - Contract renewal date and customer tenure
   - Escalation notes or recent ticket sentiment
2. **Open Risks**: Identify key risk signals (churn risks, competitive threats, recurring technical failures, skipped meetings, billing issues).
   - For EACH risk flag, you MUST include an exact DIRECT QUOTE copied verbatim from either:
     a) One of the account's `escalation_notes` strings, OR
     b) The `body` text of one of the provided support tickets.
   - For `ticket_id`, specify the exact ticket ID (e.g., "TKT-10042") if the quote comes from a ticket, or "ACCOUNT" if the quote comes from the account's escalation notes.
   - DO NOT fabricate, paraphrase, or invent quotes. Only use text that literally appears in the provided data.
   - If there are no open risks, return an empty list `[]`.
3. **Talking Points**: 3-5 concrete, strategic discussion points for the TAM's upcoming customer sync or QBR, referencing specific facts from the account or tickets.

### OUTPUT FORMAT:
You must output a STRICT raw JSON object matching this schema with no markdown fences or preambles:
{
  "account_id": "Exact account ID string",
  "company": "Company name string",
  "executive_summary": "3-5 sentence narrative summary covering health, ARR, renewal, trend, and notes",
  "open_risks": [
    {
      "ticket_id": "TKT-XXXXX or ACCOUNT",
      "quote": "Exact verbatim quote from ticket body or escalation notes",
      "reason": "Specific risk explanation"
    }
  ],
  "talking_points": [
    "Discussion point 1",
    "Discussion point 2"
  ]
}"""

    # Prepare formatted ticket summaries
    formatted_tickets = []
    for t in tickets:
        formatted_tickets.append(
            {
                "ticket_id": t.get("ticket_id"),
                "subject": t.get("subject"),
                "product": t.get("product"),
                "category": t.get("category"),
                "urgency": t.get("urgency"),
                "status": t.get("status"),
                "created_at": t.get("created_at"),
                "body": t.get("body"),
            }
        )

    account_json_str = json.dumps(account, indent=2)
    tickets_json_str = json.dumps(formatted_tickets, indent=2) if formatted_tickets else "No support tickets in last 90 days."

    user_prompt = f"""### CUSTOMER ACCOUNT DATA:
{account_json_str}

### RECENT SUPPORT TICKETS (LAST 90 DAYS):
{tickets_json_str}

Generate the strict JSON account brief for account {account.get('account_id')}."""

    return system_prompt, user_prompt
