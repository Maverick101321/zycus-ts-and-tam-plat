# US Delivery Internship — Starter Dataset

This repository contains the mock dataset for the **US Delivery Internship Technical Task Round**.  
Candidates should use this data exclusively for their submissions.

---

## Repository Structure

```
starter-repo/
├── data/
│   ├── tickets.json          # 500 synthetic support tickets
│   └── accounts.json         # 50 synthetic customer account summaries
├── knowledge-base/
│   ├── products/
│   │   ├── databridge-pro.md
│   │   ├── cloudsync.md
│   │   ├── analyticshub.md
│   │   ├── securevault.md
│   │   └── workflowengine.md
│   ├── troubleshooting/
│   │   ├── authentication-sso.md
│   │   └── performance-and-integrations.md
│   ├── billing/
│   │   └── billing-and-plans.md
│   └── onboarding/
│       └── onboarding-guide.md
└── DATA_SCHEMA.md            # Field-level schema documentation
```

---

## Data Description

### `data/tickets.json`

500 synthetic support tickets submitted by fictitious enterprise customers. Each ticket represents a realistic interaction between a customer and the technical support team.

**Key fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ticket_id` | string | Unique ticket identifier (e.g., `TKT-10042`) |
| `account_id` | string | Links to an account in `accounts.json` |
| `company` | string | Customer company name |
| `subject` | string | Ticket subject line |
| `body` | string | Full ticket body text |
| `product` | string | Product the ticket relates to |
| `product_area` | string | Module within the product |
| `category` | string | Issue type: Bug, Feature Request, How-To, Performance, Billing, Integration, Onboarding, Data Loss |
| `urgency` | string | P1 (critical) to P4 (low) |
| `status` | string | Open, In Progress, Pending Customer, Resolved, Closed |
| `plan_tier` | string | Starter, Professional, Business, Enterprise |
| `assigned_agent` | string | Support agent name |
| `created_at` | ISO 8601 | Ticket creation timestamp |
| `updated_at` | ISO 8601 | Last update timestamp |
| `tags` | array | Free-form tags |
| `channel` | string | Submission channel: email, portal, chat, phone |
| `satisfaction_score` | int\|null | CSAT score 1–5, or null if not submitted |

See [DATA_SCHEMA.md](DATA_SCHEMA.md) for full schema with examples.

---

### `data/accounts.json`

50 synthetic customer account summaries, each representing a fictional enterprise customer's relationship with the platform.

**Key fields:**

| Field | Type | Description |
|-------|------|-------------|
| `account_id` | string | Unique account identifier |
| `company` | string | Company name |
| `tam` | string | Assigned Technical Account Manager |
| `plan_tier` | string | Current plan |
| `arr_usd` | int | Annual recurring revenue in USD |
| `seats_licensed` | int | Number of licensed seats |
| `seats_active` | int | Seats with activity in last 30 days |
| `products` | array | Products in use |
| `health_status` | string | Healthy, At Risk, Churning, or New |
| `usage_trend` | string | Increasing, Stable, Declining, or Inactive |
| `open_tickets` | int | Currently open support tickets |
| `p1_tickets_last_30d` | int | P1 tickets in last 30 days |
| `renewal_date` | YYYY-MM-DD | Contract renewal date |
| `last_qbr_date` | YYYY-MM-DD | Date of last Quarterly Business Review |
| `escalation_notes` | array | Free-text escalation observations |
| `nps_score` | int\|null | Net Promoter Score 1–10, or null |
| `primary_contact` | object | `name` and `title` of main contact |
| `integrations_active` | array | Active third-party integrations |
| `region` | string | Geographic region |
| `industry` | string | Customer industry vertical |

---

### `knowledge-base/`

Markdown documentation files representing a product knowledge base. These docs contain:

- Product feature descriptions and configuration references
- Common error codes and their meanings
- Step-by-step troubleshooting guides
- Plan limits and pricing information
- Onboarding checklists and training paths

Candidates should use these docs as the retrieval corpus for knowledge-base lookup features.

---

## Usage Notes

- All data is **entirely synthetic**. Company names, contact details, and ticket content are fictional.
- Ticket `account_id` values do not always match an entry in `accounts.json` — this is intentional. Handle missing account lookups gracefully.
- The `escalation_notes` field in accounts contains plain-text observations. These are designed to test churn-risk signal detection.
- Some tickets are deliberately ambiguous in category or urgency — this tests edge-case handling.

---

## Project Setup

### 1. Create and Activate Virtual Environment

```bash
# Using python3 venv
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your LLM provider credentials and configuration
```

### 4. Run the API Server

```bash
# Using uvicorn CLI
uvicorn app.api.main:app --reload

# Or directly running the module
python -m app.api.main
```

The API will be available at `http://localhost:8000` (interactive documentation at `http://localhost:8000/docs`).

---

## UI Demo

Launch the interactive Streamlit application to test ticket triage and TAM account health briefs with live streaming responses:

```bash
streamlit run ui/streamlit_app.py
```

---

## CI

Evaluation test suites run automatically on push to `main` and on pull requests targeting `main` via GitHub Actions (`.github/workflows/eval-ci.yml`). Evaluation reports (`eval_report.md` and `eval_report.json`) are uploaded and available as workflow artifacts on every run.

> **Note**: Requires `LLM_API_KEY`, `GROQ_API_KEY`, etc. to be set as GitHub repo secrets (**Settings → Secrets and variables → Actions**) for CI to run evals against live models.

---

## Design Note

#### Failure modes

1. **Malformed/non-JSON LLM output.** Both agents depend on the model returning strict JSON; a truncated or chatty response breaks downstream parsing. Mitigation: a retry-with-stricter-reminder pass on parse failure (already implemented in `agent.py` for both tasks). Detection in production: track a parse-failure-rate metric per model; alert if it crosses a threshold, since it usually signals a prompt or model regression.

2. **Hallucinated risk flags in the TAM brief.** An LLM can invent a plausible-sounding "quote" that never appeared in the account data, which is dangerous for a churn-risk tool. Mitigation: a post-processing verification step drops any `RiskFlag` whose quote isn't a substring match (case/whitespace-normalized) of the actual ticket body or `escalation_notes` — implemented, not optional. Detection: log every dropped flag; a high drop rate signals the model is fabricating rather than extracting, worth a prompt revision.

3. **Free-tier LLM provider outages/rate limits.** Nemotron/GLM on OpenRouter and gpt-oss-120b on Groq all hit 429/502s under load, as seen during testing. Mitigation: a cross-provider fallback chain (`FallbackLLMClient`) tries three independent providers before failing. Detection: log which provider actually served each request; a rising fallback-to-tertiary rate is an early warning to move to a paid tier before it becomes a hard outage.

#### Latency vs quality trade-off

The primary model, Nemotron 3 Ultra (550B), was deliberately chosen over faster small models because triage reasoning and churn-risk grounding both benefit from stronger multi-step reasoning — misclassifying a P1 as P4, or fabricating a risk quote, is costlier than a few extra seconds of latency. This costs real time: multi-second responses per ticket, and occasional multi-second fallback delays when the primary is overloaded.

If latency were the hard constraint, the swap would be: make Groq's gpt-oss-120b (fast inference hardware) the primary instead of a fallback, drop to a smaller/faster model for lower-stakes triage tickets (e.g., P3/P4 pre-classified by simple heuristics), cache KB retrieval results per query pattern, and shrink the KB context passed into the prompt (top-1 chunk instead of top-3).

#### Data sensitivity

Ticket bodies and account data can contain names, emails, and business-sensitive details (ARR, escalation notes). Current design already avoids the worst risk — everything is synthetic mock data, and no data leaves the pipeline except to the configured LLM API. For a real production version: (1) add a PII-redaction pass (regex/NER for emails, phone numbers, names) before any text is sent to an external LLM API; (2) use providers with zero-data-retention agreements or self-hosted inference for sensitive tiers; (3) never log raw prompts/responses containing customer data — log redacted versions or hashes only; (4) apply RBAC on which accounts a given TAM/agent identity can query.

#### Scaling to 10x ticket volume

At 10x volume (~5,000 tickets/day), the first thing to break is the LLM provider's free-tier rate limits — the fallback chain would be exhausted within minutes, not just occasionally triggered. Second: the current design calls the LLM synchronously inside the FastAPI request path, so request queuing and latency would spike badly under concurrent load. Third: the in-memory TF-IDF KB index rebuilds/holds fine at this scale, but wouldn't scale further if the KB itself grew 10x.

Fixes, in priority order: move to a paid/dedicated LLM tier with real throughput guarantees; make ticket triage asynchronous (queue + worker pool, e.g. Celery/RQ, with the API returning a job ID); add response caching for near-duplicate tickets; and if the KB grows significantly, move from TF-IDF to a proper vector store (e.g., pgvector/FAISS) instead of the in-memory approach.
