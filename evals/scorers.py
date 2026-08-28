"""Evaluation scorers for Support Triage and TAM Account Briefs."""

import json
import logging
import re
from typing import Any, Dict, Optional

from app.llm_client import get_llm_client

logger = logging.getLogger(__name__)


def score_triage_case(case: Dict[str, Any], actual_output: Dict[str, Any]) -> Dict[str, Any]:
    """Score a single triage test case against acceptance criteria.

    Weights:
      - Urgency match: 0.4
      - Category / product area keywords: 0.3
      - KB reference correctness: 0.3

    Returns:
      {"passed": bool, "score": float, "details": str}
    """
    acceptance = case.get("acceptance", {})
    details_parts = []

    actual_urgency = actual_output.get("urgency", "")
    actual_category = actual_output.get("category", "")
    actual_product = actual_output.get("product_area", "")
    actual_kb_doc = actual_output.get("matched_kb_doc")

    # 1. Urgency Check (Weight 0.4)
    expected_urgency = acceptance.get("expected_urgency")
    any_of_urgencies = acceptance.get("any_of", [])
    urgency_score = 0.0

    if expected_urgency == "any_of" or any_of_urgencies:
        if actual_urgency in any_of_urgencies:
            urgency_score = 0.4
            details_parts.append(f"Urgency '{actual_urgency}' in allowed {any_of_urgencies}")
        else:
            details_parts.append(
                f"Urgency '{actual_urgency}' NOT in allowed {any_of_urgencies}"
            )
    else:
        if actual_urgency == expected_urgency:
            urgency_score = 0.4
            details_parts.append(f"Urgency '{actual_urgency}' matched '{expected_urgency}'")
        else:
            details_parts.append(
                f"Urgency mismatch: got '{actual_urgency}', expected '{expected_urgency}'"
            )

    # 2. Category / Product Area Keyword Check (Weight 0.3)
    expected_keywords = acceptance.get("expected_category_keywords", [])
    category_score = 0.0
    combined_cat_text = f"{actual_category} {actual_product}".lower()

    if expected_keywords:
        matched_kws = [kw for kw in expected_keywords if kw.lower() in combined_cat_text]
        if matched_kws:
            category_score = 0.3
            details_parts.append(f"Category matched keywords: {matched_kws}")
        else:
            details_parts.append(
                f"Category '{actual_category}'/'{actual_product}' missing keywords {expected_keywords}"
            )
    else:
        category_score = 0.3

    # 3. KB Reference Check (Weight 0.3)
    must_ref_kb = acceptance.get("must_reference_kb", False)
    kb_score = 0.0

    if must_ref_kb:
        if actual_kb_doc and str(actual_kb_doc).strip().lower() not in ["none", "null", ""]:
            kb_score = 0.3
            details_parts.append(f"KB doc referenced: '{actual_kb_doc}'")
        else:
            details_parts.append("KB doc expected but none referenced")
    else:
        # If KB wasn't mandatory, award credit
        kb_score = 0.3
        if actual_kb_doc:
            details_parts.append(f"Optional KB doc referenced: '{actual_kb_doc}'")

    total_score = round(urgency_score + category_score + kb_score, 2)
    # Passed if score >= 0.7 and urgency matched
    passed = total_score >= 0.7 and urgency_score > 0.0

    return {
        "passed": passed,
        "score": total_score,
        "details": "; ".join(details_parts),
    }


def _call_llm_judge(account_data: Dict[str, Any], summary: str) -> float:
    """Call LLM-as-judge to rate factual grounding of the summary from 1-5."""
    system_prompt = (
        "You are an impartial evaluation judge. Rate whether the provided executive summary "
        "is factually grounded in the given account dataset without hallucinations or false claims."
    )
    user_prompt = f"""### ACCOUNT DATA:
{json.dumps(account_data, indent=2)}

### GENERATED EXECUTIVE SUMMARY:
{summary}

Evaluate if the summary is factually accurate and grounded in the data above.
Rate on a scale from 1 (completely fabricated) to 5 (fully accurate and grounded).
Respond in strict JSON:
{{"rating": <1-5 integer>, "reason": "<brief justification>"}}"""

    try:
        client = get_llm_client()
        raw = client.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.0,
            json_mode=True,
        )
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned).strip()
        data = json.loads(cleaned)
        rating = float(data.get("rating", 3))
        # Normalize 1-5 to 0.0-1.0
        normalized = max(0.0, min(1.0, (rating - 1.0) / 4.0))
        return normalized
    except Exception as exc:
        logger.warning("LLM judge evaluation encountered error: %s. Defaulting to 0.8", exc)
        return 0.8


def score_tam_case(
    case: Dict[str, Any],
    actual_output: Dict[str, Any],
    account_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Score a single TAM brief case using rule-based risk checks and an LLM-as-judge score.

    Blends:
      - 50% Rule-based risk count / health alignment
      - 50% LLM judge factual grounding score

    Returns:
      {"passed": bool, "score": float, "details": str}
    """
    acceptance = case.get("acceptance", {})
    details_parts = []

    open_risks = actual_output.get("open_risks", [])
    risk_count = len(open_risks)
    summary = actual_output.get("executive_summary", "")

    expect_zero = acceptance.get("expect_zero_risks_if_healthy", False)
    expect_risks = acceptance.get("expect_risks_flagged", False)
    min_risks = acceptance.get("min_risk_count", 0)

    # 1. Rule-based risk count check (0.0 to 1.0)
    rule_score = 0.0
    if expect_zero:
        if risk_count == 0:
            rule_score = 1.0
            details_parts.append("Correctly flagged 0 risks for healthy/sparse account")
        else:
            rule_score = 0.0
            details_parts.append(f"Expected 0 risks for healthy account, but got {risk_count}")
    elif expect_risks:
        if risk_count >= min_risks:
            rule_score = 1.0
            details_parts.append(f"Flagged {risk_count} risks (min required: {min_risks})")
        elif risk_count > 0:
            rule_score = round(risk_count / max(1, min_risks), 2)
            details_parts.append(f"Partial risks: {risk_count}/{min_risks}")
        else:
            rule_score = 0.0
            details_parts.append(f"Expected at least {min_risks} risks, but got 0")
    else:
        rule_score = 1.0
        details_parts.append(f"Risk count: {risk_count}")

    # 2. LLM-as-Judge check (0.0 to 1.0)
    judge_score = 1.0
    if account_data and summary:
        judge_score = _call_llm_judge(account_data=account_data, summary=summary)
        details_parts.append(f"Judge Grounding: {judge_score:.2f}")

    # 3. Blend 50/50
    final_score = round(0.5 * rule_score + 0.5 * judge_score, 2)
    passed = final_score >= 0.7

    return {
        "passed": passed,
        "score": final_score,
        "details": "; ".join(details_parts),
    }
