"""Sample script to run the TAM Account Health Summarizer on representative accounts."""

import json
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.tam.agent import generate_account_brief


def print_brief(brief):
    print(f"Company           : {brief.company} ({brief.account_id})")
    print(f"Generated At (UTC): {brief.generated_at}")
    print(f"\nExecutive Summary :\n{brief.executive_summary}")
    print("\nOpen Risks (Grounded & Verified):")
    if not brief.open_risks:
        print("  (None identified)")
    else:
        for idx, risk in enumerate(brief.open_risks, 1):
            print(f"  [{idx}] Sourced: {risk.ticket_id}")
            print(f"      Quote  : \"{risk.quote}\"")
            print(f"      Reason : {risk.reason}")
    print("\nTalking Points for TAM:")
    for idx, tp in enumerate(brief.talking_points, 1):
        print(f"  {idx}. {tp}")


def main():
    print("=" * 80)
    print("TAM ACCOUNT HEALTH SUMMARIZER - SAMPLE RUN")
    print("=" * 80)

    # 1. At Risk / Churning account with real escalation signals
    at_risk_acc = "ACC-3336"  # Omni Consumer Products ($500k ARR, At Risk)
    print(f"\n[1/2] AT-RISK ACCOUNT BRIEF: {at_risk_acc}")
    print("-" * 80)
    brief_at_risk = generate_account_brief(at_risk_acc)
    print_brief(brief_at_risk)
    print("=" * 80)

    # 2. Healthy account for contrast
    healthy_acc = "ACC-3033"  # Polaris Group (Healthy, Increasing)
    print(f"\n[2/2] HEALTHY ACCOUNT BRIEF: {healthy_acc}")
    print("-" * 80)
    brief_healthy = generate_account_brief(healthy_acc)
    print_brief(brief_healthy)
    print("=" * 80)

    # 3. Determinism test: run ACC-3336 a second time and compare executive summary
    print("\n[3/3] DETERMINISM VERIFICATION (Running ACC-3336 Run 1 vs Run 2)")
    print("-" * 80)
    brief_run2 = generate_account_brief(at_risk_acc)

    print("RUN 1 Executive Summary:")
    print(brief_at_risk.executive_summary)
    print("\nRUN 2 Executive Summary:")
    print(brief_run2.executive_summary)
    print("-" * 40)

    match = brief_at_risk.executive_summary.strip() == brief_run2.executive_summary.strip()
    print(f"Exact Executive Summary Match: {match}")
    print("=" * 80)


if __name__ == "__main__":
    main()
