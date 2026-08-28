# Automated AI Evaluation Report

**Generated at:** 2026-08-28T13:42:16.535129+00:00

## Executive Summary

- **Overall Pass Rate:** 100.0% (12/12 passed)
- **Triage Agent (Task 1):** 100.0% Pass Rate | Avg Score: 0.95/1.0
- **TAM Brief Agent (Task 2):** 100.0% Pass Rate | Avg Score: 0.88/1.0

## Detailed Case Results

| Case ID | Task | Status | Score | Details |
|---------|------|--------|-------|---------|
| `triage_001` | Triage | PASS | 1.00 | Urgency 'P1' matched 'P1'; Category matched keywords: ['Bug']; KB doc referenced: 'knowledge-base/products/databridge-pro.md (Section: DataBridge Pro — Product Reference > Core Modules > API)' |
| `triage_002` | Triage | PASS | 1.00 | Urgency 'P4' matched 'P4'; Category matched keywords: ['How-To', 'AnalyticsHub']; Optional KB doc referenced: 'knowledge-base/products/analyticshub.md' |
| `triage_003` | Triage | PASS | 1.00 | Urgency 'P3' in allowed ['P3', 'P4']; Category matched keywords: ['Billing']; KB doc referenced: 'knowledge-base/billing/billing-and-plans.md' |
| `triage_004` | Triage | PASS | 1.00 | Urgency 'P3' in allowed ['P2', 'P3']; Category matched keywords: ['Integration', 'Authentication', 'SSO']; KB doc referenced: 'knowledge-base/troubleshooting/authentication-sso.md' |
| `triage_005` | Triage | PASS | 0.70 | Urgency 'P4' in allowed ['P3', 'P4']; Category 'Performance'/'Platform > General' missing keywords ['Bug', 'How-To']; Optional KB doc referenced: 'knowledge-base/troubleshooting/performance-and-integrations.md' |
| `triage_006` | Triage | PASS | 1.00 | Urgency 'P4' in allowed ['P3', 'P4']; Category matched keywords: ['Bug'] |
| `tam_001` | TAM Brief | PASS | 0.75 | Flagged 3 risks (min required: 1); Judge Grounding: 0.50 |
| `tam_002` | TAM Brief | PASS | 1.00 | Flagged 3 risks (min required: 2); Judge Grounding: 1.00 |
| `tam_003` | TAM Brief | PASS | 0.75 | Correctly flagged 0 risks for healthy/sparse account; Judge Grounding: 0.50 |
| `tam_004` | TAM Brief | PASS | 1.00 | Correctly flagged 0 risks for healthy/sparse account; Judge Grounding: 1.00 |
| `tam_005` | TAM Brief | PASS | 0.75 | Correctly flagged 0 risks for healthy/sparse account; Judge Grounding: 0.50 |
| `tam_006` | TAM Brief | PASS | 1.00 | Correctly flagged 0 risks for healthy/sparse account; Judge Grounding: 1.00 |
