import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from app.tam.agent import generate_account_brief
from app.tam.data_loader import AccountDataLoader
from app.triage.agent import stream_draft_response, triage_ticket
from app.triage.schemas import TicketInput

# Page configuration
st.set_page_config(
    page_title="Support & TAM AI Suite",
    page_icon="🛠️",
    layout="wide",
)

# Sidebar
st.sidebar.title("AI Tooling Suite")
st.sidebar.markdown("---")
st.sidebar.info("Demo UI — internal tool for Support/TAM teams")

st.title("🛠️ Support & TAM AI Tooling Suite")
st.markdown("Automated ticket triage and customer account health summarization.")

tab1, tab2 = st.tabs(["🎫 Ticket Triage", "📊 Account Brief"])

# Tab 1: Ticket Triage
with tab1:
    st.header("Support Ticket Triage & Response Generator")
    st.markdown(
        "Classify urgency, identify product area, match knowledge-base guides, "
        "and generate streaming draft responses."
    )

    col_in1, col_in2 = st.columns([3, 1])
    with col_in1:
        subject = st.text_input(
            "Ticket Subject",
            value="CRITICAL: Production DataBridge Pro pipeline completely down across all 50 connectors",
            placeholder="Enter ticket subject line...",
        )
    with col_in2:
        account_id = st.text_input(
            "Account ID (Optional)",
            value="ACC-3336",
            placeholder="e.g. ACC-1001",
        )

    body = st.text_area(
        "Ticket Body",
        value=(
            "Our main DataBridge Pro pipeline has stopped processing all data feeds. "
            "All 50 connectors are failing with ERR_CONNECTION_TIMEOUT. Over 1000 users are impacted "
            "and our real-time customer ingestion is halted. This is an active production outage "
            "affecting our core business operations. Please treat as P1 emergency."
        ),
        height=140,
        placeholder="Enter ticket details...",
    )

    if st.button("Analyze Ticket", type="primary", use_container_width=True):
        if not subject.strip() or not body.strip():
            st.warning("Please provide both a subject and body for the ticket.")
        else:
            ticket_input = TicketInput(
                subject=subject.strip(),
                body=body.strip(),
                account_id=account_id.strip() if account_id.strip() else None,
            )

            try:
                with st.spinner("Analyzing ticket & searching knowledge base..."):
                    classification = triage_ticket(ticket_input)

                st.success("Triage analysis complete!")

                # Key classification metrics
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    urgency_color = "🚨" if classification.urgency in ["P1", "P2"] else "ℹ️"
                    st.metric("Urgency", f"{urgency_color} {classification.urgency}")
                with m2:
                    st.metric("Category", classification.category)
                with m3:
                    st.metric("Product Area", classification.product_area)
                with m4:
                    st.metric("Assigned Team", classification.recommended_team)

                # Reasoning & Knowledge Base Reference
                st.markdown("### 📋 Triage Reasoning")
                st.write(classification.reasoning)

                if classification.matched_kb_doc:
                    st.markdown("### 📚 Knowledge Base Match")
                    st.info(
                        f"**Article:** `{classification.matched_kb_doc}`\n\n"
                        f"> {classification.matched_kb_snippet or 'Relevant section matched.'}"
                    )

                # Live Streamed Draft Response
                st.markdown("### ✍️ Draft Customer Response (Live Streamed)")
                stream_container = st.empty()
                with stream_container:
                    st.write_stream(stream_draft_response(ticket_input, classification))

            except Exception as e:
                st.error(
                    f"Triage execution error: {str(e)}\n\n"
                    "If rate limits were encountered, please check provider availability in your fallback chain."
                )


# Tab 2: Account Brief
with tab2:
    st.header("Technical Account Manager (TAM) Health Brief")
    st.markdown(
        "Synthesize customer telemetry, usage trends, and ticket history into executive summaries "
        "with strictly grounded churn risk signals."
    )

    accounts = AccountDataLoader.get_instance().accounts

    if not accounts:
        st.warning("No account data found in `data/accounts.json`.")
    else:
        account_options = {
            f"{acc.get('company', 'Unknown')} ({acc.get('account_id', '')}) — Health: {acc.get('health_status', 'N/A')} [ARR: ${acc.get('arr_usd', 0):,}]": acc.get(
                "account_id", ""
            )
            for acc in accounts
        }

        selected_label = st.selectbox(
            "Select Customer Account",
            options=list(account_options.keys()),
        )
        selected_account_id = account_options[selected_label]

        if st.button("Generate Brief", type="primary", use_container_width=True):
            try:
                with st.spinner(f"Synthesizing account brief for {selected_account_id}..."):
                    brief = generate_account_brief(selected_account_id)

                st.success(f"Brief generated for {brief.company} ({brief.account_id})")

                # Executive Summary
                st.markdown("### 📝 Executive Summary")
                st.write(brief.executive_summary)

                # Open Risks & Signals
                st.markdown("### ⚠️ Open Churn Risks & Grounded Signals")
                if brief.open_risks:
                    for i, risk in enumerate(brief.open_risks, 1):
                        with st.expander(
                            f"Risk Flag {i} [{risk.ticket_id}]: {risk.reason[:75]}...",
                            expanded=True,
                        ):
                            st.markdown(f"**Reason:** {risk.reason}")
                            st.markdown(
                                f"**Source Quote (Grounded):**\n> *\"{risk.quote}\"*"
                            )
                else:
                    st.success(
                        "✅ No open churn risks or critical escalation flags identified for this account."
                    )

                # Talking Points
                st.markdown("### 🎯 Recommended TAM Talking Points")
                if brief.talking_points:
                    for point in brief.talking_points:
                        st.markdown(f"- {point}")
                else:
                    st.info("No specific talking points generated.")

                st.caption(f"Generated at: {brief.generated_at}")

            except Exception as e:
                st.error(
                    f"Account Brief generation error: {str(e)}\n\n"
                    "If rate limits were encountered, please check provider availability in your fallback chain."
                )
