import json
import logging
import re
from typing import Any, Dict, Iterator, List, Optional

from app import config
from app.llm_client import get_llm_client
from app.retrieval.kb_loader import search_kb
from app.triage.prompts import build_triage_prompt
from app.triage.schemas import TicketInput, TriageOutput

logger = logging.getLogger(__name__)


def _clean_json_text(raw_text: str) -> str:
    """Strip markdown code fences and extraneous text surrounding JSON."""
    text = raw_text.strip()
    if text.startswith("```"):
        # Strip ```json and ```
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    # If still not starting with '{', attempt to extract first JSON object
    if not text.startswith("{"):
        match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if match:
            text = match.group(1).strip()

    return text


def _parse_and_validate(raw_text: str) -> TriageOutput:
    """Parse raw LLM string into TriageOutput model."""
    cleaned = _clean_json_text(raw_text)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError(f"Parsed JSON is not a dictionary: {data}")
    return TriageOutput(**data)


def triage_ticket(ticket: TicketInput) -> TriageOutput:
    """Analyze an incoming ticket, ground against knowledge base, and return triage classification."""
    # 1. Search knowledge base for top 3 relevant chunks
    query = f"{ticket.subject}\n{ticket.body}"
    kb_chunks = search_kb(query=query, top_k=3)

    # 2. Build KB context string
    context_blocks = []
    for i, chunk in enumerate(kb_chunks, 1):
        context_blocks.append(
            f"--- KB Article {i} ---\n"
            f"Document: {chunk.get('doc_path', 'unknown')}\n"
            f"Section: {chunk.get('heading', 'general')}\n"
            f"Content:\n{chunk.get('text', '')}"
        )
    kb_context = "\n\n".join(context_blocks)

    # 3. Build prompt
    system_prompt, user_prompt = build_triage_prompt(ticket=ticket, kb_context=kb_context)

    # 4. Generate response via LLM client with retry on parse failure
    client = get_llm_client()
    raw_response = client.generate(
        prompt=user_prompt,
        system=system_prompt,
        temperature=config.DEFAULT_TEMPERATURE,
        seed=config.DEFAULT_SEED,
        json_mode=True,
    )

    try:
        triage_result = _parse_and_validate(raw_response)
    except Exception as exc:
        logger.warning("First attempt to parse triage JSON failed (%s). Retrying once...", exc)
        stricter_system = (
            f"{system_prompt}\n\n"
            "CRITICAL: Your previous response was invalid JSON. "
            "You must return ONLY a single valid raw JSON object matching the schema with no extra text or explanations."
        )
        retry_response = client.generate(
            prompt=user_prompt,
            system=stricter_system,
            temperature=config.DEFAULT_TEMPERATURE,
            seed=config.DEFAULT_SEED,
            json_mode=True,
        )
        try:
            triage_result = _parse_and_validate(retry_response)
        except Exception as retry_exc:
            raise RuntimeError(
                f"Failed to produce valid TriageOutput JSON after retry. Raw response: {retry_response}"
            ) from retry_exc

    # 5. Populate or fallback KB metadata from top search result if available
    if not triage_result.matched_kb_doc and kb_chunks:
        top_chunk = kb_chunks[0]
        # If the search score indicates meaningful relevance (> 0.1)
        if top_chunk.get("score", 0) > 0.1:
            triage_result.matched_kb_doc = top_chunk.get("doc_path")
            if not triage_result.matched_kb_snippet:
                snippet = top_chunk.get("text", "")
                triage_result.matched_kb_snippet = (
                    snippet[:300] + "..." if len(snippet) > 300 else snippet
                )

    return triage_result


def stream_draft_response(ticket: TicketInput, classification: TriageOutput) -> Iterator[str]:
    """Stream a polished customer-facing draft response given the ticket and triage classification."""
    client = get_llm_client()
    system_prompt = (
        "You are an empathetic, professional Tier 2 support engineer. "
        "Write a concise, helpful, and empathetic initial response to the customer based on the ticket details "
        "and internal triage classification. Include immediate troubleshooting steps or next steps if applicable."
    )
    user_prompt = f"""### TICKET:
Subject: {ticket.subject}
Body:
{ticket.body}

### CLASSIFICATION & CONTEXT:
Product Area: {classification.product_area}
Category: {classification.category}
Urgency: {classification.urgency}
Reasoning: {classification.reasoning}
Matched KB Guide: {classification.matched_kb_doc or 'None'}
KB Guidance: {classification.matched_kb_snippet or 'None'}
Assigned Team: {classification.recommended_team}

Write ONLY the customer-facing email/message response."""

    return client.generate_stream(
        prompt=user_prompt,
        system=system_prompt,
        temperature=config.DEFAULT_TEMPERATURE,
        seed=config.DEFAULT_SEED,
    )


def triage_ticket_stream(ticket: TicketInput) -> Iterator[str]:
    """Helper that computes ticket classification and streams the draft response text."""
    classification = triage_ticket(ticket)
    return stream_draft_response(ticket, classification)

