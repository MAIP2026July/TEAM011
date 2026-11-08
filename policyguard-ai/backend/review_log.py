"""Human decisions: the audit trail, and the sign-off gate on the final report."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from .config import REVIEW_LOG_PATH

DECISIONS = ("Confirm", "Reject", "Escalate")


def missing_reviews(findings: List[dict], decisions: Dict[str, dict]) -> List[str]:
    """Finding IDs with no decision and reason. The report cannot be signed until this is empty."""
    return [f["id"] for f in findings
            if decisions.get(f["id"], {}).get("decision") not in DECISIONS or not decisions[f["id"]].get("reason", "").strip()]


def record_sign_off(result: dict, decisions: Dict[str, dict], reviewer: str, renewal_decision: str, path: Path = REVIEW_LOG_PATH) -> dict:
    if not reviewer.strip():
        raise ValueError("A reviewer name is required.")
    outstanding = missing_reviews(result["findings"], decisions)
    if outstanding:
        raise ValueError(f"Review needed for: {', '.join(outstanding)}")
    record = {"signed_at": datetime.now(timezone.utc).isoformat(), "reviewer": reviewer, "folder": result["folder"],
              "ai_score": result["audit"]["score"], "ai_status": result["audit"]["status"],
              "ai_recommendation": result["renewal"]["recommendation"], "renewal_decision": renewal_decision,
              "decisions": decisions}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    return record


def build_report(result: dict, sign_off: dict) -> str:
    lines = [f"# Audit-readiness report: {result['folder']}", "",
             "Decision support only. Rules come from a fictional demonstration rulebook.", "",
             f"- Audit date: {result['as_of']}", f"- Score: {result['audit']['score']}", f"- Status: {result['audit']['status']}",
             f"- AI recommendation: {result['renewal']['recommendation']}", f"- Rationale: {result['renewal']['rationale']}",
             f"- Human renewal decision: {sign_off['renewal_decision']}",
             f"- Signed off by: {sign_off['reviewer']} at {sign_off['signed_at']}", "", "## Findings", ""]
    for finding in result["findings"]:
        decision = sign_off["decisions"][finding["id"]]
        lines += [f"### {finding['id']} · {finding['rule_id']} · {finding['severity']} · {finding['confidence_band']} confidence",
                  f"- Finding: {finding['summary']}", f"- Document: {finding['document']} (page {finding['page']})",
                  f"- Evidence: \"{finding['quote']}\" ({finding['verification']})",
                  f"- Human decision: {decision['decision']}: {decision['reason']}", ""]
    if not result["findings"]:
        lines.append("No findings.")
    return "\n".join(lines)
