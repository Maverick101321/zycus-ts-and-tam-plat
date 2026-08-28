"""Prompts and prompt versioning for the Ticket Triage Agent."""

from typing import Dict, Tuple
from app.triage.schemas import TicketInput

PROMPT_VERSION: str = "v1"

CHANGELOG: Dict[str, str] = {
    "v1": "Initial ticket triage prompt with strict DATA_SCHEMA.md enums, urgency guidance, KB grounding, and draft response generation."
}


def build_triage_prompt(ticket: TicketInput, kb_context: str) -> Tuple[str, str]:
    """Builds the system and user prompt for ticket triage analysis.

    Returns:
        (system_prompt, user_prompt) tuple.
    """
    system_prompt = """You are an expert Technical Support Triage Engineer for an enterprise SaaS platform.
Your job is to analyze incoming support tickets, accurately categorize and prioritize them according to standard company schemas, ground the analysis in retrieved Knowledge Base (KB) documentation, and draft an empathetic, professional first response.

### CATEGORY ENUM (Choose EXACTLY ONE):
- "Bug" : product defect or unexpected behaviour
- "Feature Request" : request for new functionality
- "How-To" : guidance or documentation request
- "Performance" : slowness, timeouts, throughput issues
- "Billing" : invoice, payment, or plan questions
- "Integration" : third-party integration issues
- "Onboarding" : new user or new organisation setup
- "Data Loss" : missing, corrupted, or inaccessible data

### URGENCY ENUM (Choose EXACTLY ONE based on impact):
- "P1" : Critical — business stopped, core workflow down, active data loss (~5% prior distribution)
- "P2" : Major impact — significant disruption, complex workaround needed (~20% prior distribution)
- "P3" : Moderate impact — normal operational issue, straightforward workaround available (~45% prior distribution)
- "P4" : Low impact — cosmetic, minor inquiry, general how-to (~30% prior distribution)

### OUTPUT FORMAT:
You must respond with a STRICT JSON object containing ONLY the following keys:
{
  "product_area": "Product and sub-module (e.g. DataBridge Pro > Connectors, CloudSync > Storage, Billing)",
  "category": "One of the exact category enums above",
  "urgency": "P1, P2, P3, or P4",
  "reasoning": "Step-by-step rationale for why this category, urgency, and routing were selected",
  "matched_kb_doc": "Path or title of the most relevant KB document found in context, or null if none",
  "matched_kb_snippet": "Key excerpt, error explanation, or resolution steps from the matched KB document, or null if none",
  "recommended_team": "Internal team responsible (e.g., 'DataBridge Pro Engineering', 'Billing Support', 'CloudSync Team', 'Platform Reliability', 'Security & IAM Team')",
  "draft_response": "Professional, courteous first response acknowledging the customer's issue, setting expectations, and providing initial guidance or KB troubleshooting steps if available."
}
Do NOT include markdown backticks around the JSON. Output only valid raw JSON."""

    user_prompt = f"""### RETRIEVED KNOWLEDGE BASE CONTEXT:
{kb_context if kb_context.strip() else "No relevant knowledge base articles found."}

### INCOMING TICKET:
Subject: {ticket.subject}
Account ID: {ticket.account_id or "Not specified"}

Body:
{ticket.body}

Please evaluate the ticket and return the strict JSON triage output."""

    return system_prompt, user_prompt
