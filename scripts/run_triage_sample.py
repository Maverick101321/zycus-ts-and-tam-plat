"""Sample script to run the Ticket Triage agent on 3 representative tickets from data/tickets.json."""

import json
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.triage.agent import triage_ticket
from app.triage.schemas import TicketInput


def main():
    tickets_path = project_root / "data" / "tickets.json"
    if not tickets_path.exists():
        print(f"Error: {tickets_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(tickets_path, "r", encoding="utf-8") as f:
        all_tickets = json.load(f)

    # Selected ticket IDs:
    # 1. TKT-10088: Clear P1 (critical missing data affecting finance operations)
    # 2. TKT-10006: Ambiguous / Integration (SecureVault + HubSpot configuration error)
    # 3. TKT-10013: Billing (Invoice seat overage query)
    sample_ids = ["TKT-10088", "TKT-10006", "TKT-10013"]
    tickets_by_id = {t["ticket_id"]: t for t in all_tickets}

    print("=" * 80)
    print("SUPPORT TICKET TRIAGE AGENT - SAMPLE RUN")
    print("=" * 80)

    for i, tid in enumerate(sample_ids, 1):
        raw_ticket = tickets_by_id.get(tid)
        if not raw_ticket:
            print(f"Warning: {tid} not found in tickets.json, skipping...")
            continue

        print(f"\n[{i}/3] SAMPLE TICKET: {tid}")
        print("-" * 80)
        print(f"Subject    : {raw_ticket['subject']}")
        print(f"Account ID : {raw_ticket.get('account_id', 'N/A')}")
        print(f"Body       :\n{raw_ticket['body'].strip()}")
        print("-" * 40)
        print("Running Triage Agent...")

        # Build clean input using only subject, body, account_id (ignoring dataset ground truth labels)
        ticket_input = TicketInput(
            subject=raw_ticket["subject"],
            body=raw_ticket["body"],
            account_id=raw_ticket.get("account_id"),
        )

        try:
            output = triage_ticket(ticket_input)
            print("\nTRIAGE AGENT OUTPUT:")
            print(f"  * Product Area    : {output.product_area}")
            print(f"  * Category        : {output.category}")
            print(f"  * Urgency         : {output.urgency}")
            print(f"  * Recommended Team: {output.recommended_team}")
            print(f"  * Matched KB Doc  : {output.matched_kb_doc}")
            print(f"  * Matched Snippet : {output.matched_kb_snippet}")
            print(f"  * Reasoning       : {output.reasoning}")
            print(f"\n  * Draft First Response:\n{output.draft_response}")
        except Exception as e:
            print(f"Error during triage: {e}", file=sys.stderr)

        print("=" * 80)


if __name__ == "__main__":
    main()
