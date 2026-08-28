"""Automated Evaluation Runner for Triage and TAM AI Agents."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure repository root is on sys.path
eval_dir = Path(__file__).resolve().parent
project_root = eval_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.tam.agent import generate_account_brief
from app.tam.data_loader import get_account
from app.triage.agent import triage_ticket
from app.triage.schemas import TicketInput
from evals.scorers import score_tam_case, score_triage_case


def _write_reports(
    results: List[Dict[str, Any]],
    triage_scores: List[float],
    triage_passes: List[bool],
    tam_scores: List[float],
    tam_passes: List[bool],
    triage_count: int,
    tam_count: int,
) -> Dict[str, Any]:
    total_cases = len(results)
    total_passed = sum(1 for r in results if r["passed"])
    overall_pass_rate = round((total_passed / total_cases) * 100, 1) if total_cases else 0.0

    avg_triage_score = (
        round(sum(triage_scores) / len(triage_scores), 2) if triage_scores else 0.0
    )
    triage_pass_rate = (
        round((sum(1 for p in triage_passes if p) / len(triage_passes)) * 100, 1)
        if triage_passes
        else 0.0
    )

    avg_tam_score = round(sum(tam_scores) / len(tam_scores), 2) if tam_scores else 0.0
    tam_pass_rate = (
        round((sum(1 for p in tam_passes if p) / len(tam_passes)) * 100, 1)
        if tam_passes
        else 0.0
    )

    summary_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": total_cases,
        "total_passed": total_passed,
        "overall_pass_rate": overall_pass_rate,
        "triage": {
            "cases": triage_count,
            "evaluated": len(triage_scores),
            "pass_rate": triage_pass_rate,
            "average_score": avg_triage_score,
        },
        "tam": {
            "cases": tam_count,
            "evaluated": len(tam_scores),
            "pass_rate": tam_pass_rate,
            "average_score": avg_tam_score,
        },
        "results": results,
    }

    # Write evals/eval_report.json
    json_path = eval_dir / "eval_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())

    # Write evals/eval_report.md
    md_path = eval_dir / "eval_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Automated AI Evaluation Report\n\n")
        f.write(f"**Generated at:** {summary_data['generated_at']}\n\n")
        f.write("## Executive Summary\n\n")
        f.write(f"- **Overall Pass Rate:** {overall_pass_rate}% ({total_passed}/{total_cases} passed)\n")
        f.write(f"- **Triage Agent (Task 1):** {triage_pass_rate}% Pass Rate | Avg Score: {avg_triage_score}/1.0\n")
        f.write(f"- **TAM Brief Agent (Task 2):** {tam_pass_rate}% Pass Rate | Avg Score: {avg_tam_score}/1.0\n\n")
        f.write("## Detailed Case Results\n\n")
        f.write("| Case ID | Task | Status | Score | Details |\n")
        f.write("|---------|------|--------|-------|---------|\n")
        for r in results:
            status_icon = "PASS" if r["passed"] else "FAIL"
            clean_details = r["details"].replace("|", "\\|")
            f.write(f"| `{r['case_id']}` | {r['task']} | {status_icon} | {r['score']:.2f} | {clean_details} |\n")
        f.flush()
        os.fsync(f.fileno())

    return summary_data


def run_all_evals() -> Dict[str, Any]:
    test_cases_dir = eval_dir / "test_cases"
    triage_file = test_cases_dir / "triage_cases.json"
    tam_file = test_cases_dir / "tam_cases.json"

    with open(triage_file, "r", encoding="utf-8") as f:
        triage_cases = json.load(f)

    with open(tam_file, "r", encoding="utf-8") as f:
        tam_cases = json.load(f)

    results: List[Dict[str, Any]] = []
    triage_scores: List[float] = []
    triage_passes: List[bool] = []
    tam_scores: List[float] = []
    tam_passes: List[bool] = []

    print("=" * 80, flush=True)
    print("RUNNING AI SUITE EVALUATIONS (Task 1: Triage & Task 2: TAM Brief)", flush=True)
    print("=" * 80, flush=True)

    # 1. Evaluate Triage Cases
    print("\n[PART 1] Evaluating Ticket Triage Agent...", flush=True)
    print("-" * 80, flush=True)

    for case in triage_cases:
        cid = case["id"]
        ticket_data = case["ticket"]
        print(f"  -> Running {cid}: {ticket_data['subject'][:45]}...", end=" ", flush=True)

        try:
            inp = TicketInput(
                subject=ticket_data["subject"],
                body=ticket_data["body"],
                account_id=ticket_data.get("account_id"),
            )
            output = triage_ticket(inp)
            score_res = score_triage_case(case, output.model_dump())
            passed = score_res["passed"]
            score = score_res["score"]
            details = score_res["details"]
            print(f"[{'PASS' if passed else 'FAIL'}] Score: {score:.2f} ({details})", flush=True)
        except Exception as exc:
            passed = False
            score = 0.0
            details = f"Execution error: {exc}"
            print(f"[ERROR] {details}", flush=True)

        triage_scores.append(score)
        triage_passes.append(passed)
        results.append(
            {
                "case_id": cid,
                "task": "Triage",
                "passed": passed,
                "score": score,
                "details": details,
            }
        )
        _write_reports(
            results,
            triage_scores,
            triage_passes,
            tam_scores,
            tam_passes,
            len(triage_cases),
            len(tam_cases),
        )

    # 2. Evaluate TAM Brief Cases
    print("\n[PART 2] Evaluating TAM Account Brief Agent...", flush=True)
    print("-" * 80, flush=True)

    for case in tam_cases:
        cid = case["id"]
        acc_id = case["account_id"]
        print(f"  -> Running {cid} ({acc_id})...", end=" ", flush=True)

        try:
            brief_output = generate_account_brief(acc_id)
            account_data = get_account(acc_id)
            score_res = score_tam_case(
                case, brief_output.model_dump(), account_data=account_data
            )
            passed = score_res["passed"]
            score = score_res["score"]
            details = score_res["details"]
            print(f"[{'PASS' if passed else 'FAIL'}] Score: {score:.2f} ({details})", flush=True)
        except Exception as exc:
            passed = False
            score = 0.0
            details = f"Execution error: {exc}"
            print(f"[ERROR] {details}", flush=True)

        tam_scores.append(score)
        tam_passes.append(passed)
        results.append(
            {
                "case_id": cid,
                "task": "TAM Brief",
                "passed": passed,
                "score": score,
                "details": details,
            }
        )
        _write_reports(
            results,
            triage_scores,
            triage_passes,
            tam_scores,
            tam_passes,
            len(triage_cases),
            len(tam_cases),
        )

    summary_data = _write_reports(
        results,
        triage_scores,
        triage_passes,
        tam_scores,
        tam_passes,
        len(triage_cases),
        len(tam_cases),
    )

    md_path = eval_dir / "eval_report.md"
    print("\n" + "=" * 80, flush=True)
    print("EVALUATION SUMMARY", flush=True)
    print("=" * 80, flush=True)
    print(
        f"Overall Pass Rate : {summary_data['overall_pass_rate']}% ({summary_data['total_passed']}/{summary_data['total_cases']})",
        flush=True,
    )
    print(
        f"Triage Pass Rate  : {summary_data['triage']['pass_rate']}% (Avg Score: {summary_data['triage']['average_score']})",
        flush=True,
    )
    print(
        f"TAM Pass Rate     : {summary_data['tam']['pass_rate']}% (Avg Score: {summary_data['tam']['average_score']})",
        flush=True,
    )
    print(f"Report written to : {md_path}", flush=True)
    print("=" * 80, flush=True)

    return summary_data


if __name__ == "__main__":
    run_all_evals()
