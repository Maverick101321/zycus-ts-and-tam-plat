"""TAM Account Brief Generation Agent with deterministic grounding and quote verification."""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app import config
from app.llm_client import get_llm_client
from app.tam.data_loader import get_account, get_account_tickets
from app.tam.prompts import build_account_brief_prompt
from app.tam.schemas import AccountBrief, RiskFlag

logger = logging.getLogger(__name__)


def _clean_json_text(raw_text: str) -> str:
    """Strip markdown code fences and extraneous text surrounding JSON."""
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    if not text.startswith("{"):
        match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if match:
            text = match.group(1).strip()

    return text


def _normalize_text(text: str) -> str:
    """Normalize whitespace and lower case for substring verification."""
    return " ".join(text.lower().split())


def _verify_quote(quote: str, corpus: List[str]) -> bool:
    """Check if normalized quote is a substring of any entry in the corpus."""
    clean_quote = _normalize_text(quote)
    if not clean_quote:
        return False

    for item in corpus:
        if clean_quote in _normalize_text(item):
            return True
    return False


def _parse_and_validate(raw_text: str, account_id: str, company: str) -> Dict[str, Any]:
    """Parse raw LLM response into a dictionary ready for AccountBrief instantiation."""
    cleaned = _clean_json_text(raw_text)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ValueError(f"Parsed response is not a JSON object: {data}")

    # Fallback missing root fields if needed
    data.setdefault("account_id", account_id)
    data.setdefault("company", company)
    data.setdefault("executive_summary", "")
    data.setdefault("open_risks", [])
    data.setdefault("talking_points", [])

    return data


def generate_account_brief(account_id: str) -> AccountBrief:
    """Generate a grounded executive brief for the given account ID.

    Args:
        account_id: The unique account ID (e.g. ACC-3336).

    Returns:
        AccountBrief containing summary, grounded open risks, and talking points.

    Raises:
        ValueError: If the account_id does not exist in the dataset.
    """
    account = get_account(account_id)
    if not account:
        raise ValueError(f"Account ID '{account_id}' not found in database.")

    tickets = get_account_tickets(account_id, days=90)
    company = account.get("company", "Unknown Company")

    # Build prompt
    system_prompt, user_prompt = build_account_brief_prompt(account=account, tickets=tickets)

    # Call LLM client with hardcoded temperature=0 for deterministic output
    client = get_llm_client()
    raw_response = client.generate(
        prompt=user_prompt,
        system=system_prompt,
        temperature=0.0,
        seed=config.DEFAULT_SEED,
        json_mode=True,
    )

    try:
        brief_data = _parse_and_validate(raw_response, account_id=account_id, company=company)
    except Exception as exc:
        logger.warning(
            "First attempt to parse account brief JSON for %s failed (%s). Retrying once...",
            account_id,
            exc,
        )
        stricter_system = (
            f"{system_prompt}\n\n"
            "CRITICAL: Your previous response was invalid JSON. "
            "You must return ONLY a single valid raw JSON object matching the schema with no extra text or explanations."
        )
        retry_response = client.generate(
            prompt=user_prompt,
            system=stricter_system,
            temperature=0.0,
            seed=config.DEFAULT_SEED,
            json_mode=True,
        )
        try:
            brief_data = _parse_and_validate(
                retry_response, account_id=account_id, company=company
            )
        except Exception as retry_exc:
            raise RuntimeError(
                f"Failed to produce valid AccountBrief JSON after retry for account {account_id}. Raw response: {retry_response}"
            ) from retry_exc

    # Build corpus for post-processing quote verification
    corpus: List[str] = []
    for note in account.get("escalation_notes", []):
        if isinstance(note, str) and note.strip():
            corpus.append(note)

    for t in tickets:
        body = t.get("body", "")
        if body:
            corpus.append(body)
        subject = t.get("subject", "")
        if subject:
            corpus.append(subject)

    # Validate and filter open_risks against source text
    verified_risks: List[RiskFlag] = []
    raw_risks = brief_data.get("open_risks", [])

    for item in raw_risks:
        if isinstance(item, dict):
            quote = item.get("quote", "")
            ticket_id = item.get("ticket_id", "ACCOUNT")
            reason = item.get("reason", "")
            if _verify_quote(quote, corpus):
                verified_risks.append(
                    RiskFlag(ticket_id=ticket_id, quote=quote, reason=reason)
                )
            else:
                logger.warning(
                    "Dropping unverified risk flag quote '%s' for account %s (not found in source data)",
                    quote,
                    account_id,
                )

    generated_at_str = datetime.now(timezone.utc).isoformat()

    return AccountBrief(
        account_id=account_id,
        company=company,
        executive_summary=brief_data.get("executive_summary", ""),
        open_risks=verified_risks,
        talking_points=brief_data.get("talking_points", []),
        generated_at=generated_at_str,
    )
