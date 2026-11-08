"""Scoring and the renewal recommendation. Both fail closed: no analysis means no pass."""
import re
from typing import Dict, List

from .config import REVIEW_SCORE, SEVERITY_POINTS

NOT_SCORED = "Not Scored - Human Review Required"
PASS = "Pass - Audit Ready"
REVIEW = "Review Required"
FAIL = "Fail - Critical Action Needed"

RECOMMEND_RENEWAL = "Recommend Renewal - Underwriter Approval Required"
RECOMMEND_REVIEW = "Recommend Manual Underwriter Review"
RECOMMEND_HOLD = "Recommend Hold - Compliance Escalation"
NO_RECOMMENDATION = "No Recommendation - Analysis Incomplete"


def calculate_audit_score(findings: List[dict], failed_documents: List[str]) -> dict:
    deductions = [
        {"rule_id": f["rule_id"], "points": SEVERITY_POINTS[f["severity"]], "summary": f["summary"]}
        for f in findings if f["status"] == "fail"
    ]
    if failed_documents:
        return {"score": None, "status": NOT_SCORED, "deductions": deductions,
                "reason": f"Could not analyse: {', '.join(failed_documents)}"}

    score = max(0, 100 - sum(d["points"] for d in deductions))
    if score < REVIEW_SCORE:
        status = FAIL
    elif findings:  # any open finding needs a person, however few points it costs
        status = REVIEW
    else:
        status = PASS
    return {"score": score, "status": status, "deductions": deductions, "reason": ""}


def generate_renewal_recommendation(audit: dict, findings: List[dict], risk_grade: str) -> dict:
    """Always a recommendation for an underwriter (REN-003), never an approval."""
    failing = [f for f in findings if f["status"] == "fail"]
    critical = [f for f in failing if f["severity"] == "critical"]
    if audit["score"] is None:
        return {"recommendation": NO_RECOMMENDATION, "rule_ids": ["REN-001"],
                "rationale": f"{audit['reason']}. No recommendation is possible until a person reviews this folder."}
    if critical:
        return {"recommendation": RECOMMEND_HOLD, "rule_ids": ["REN-001"] + [f["rule_id"] for f in critical],
                "rationale": "Open critical findings: " + "; ".join(f"{f['summary']} [{f['rule_id']}]" for f in critical)}
    if risk_grade.lower() == "high":
        return {"recommendation": RECOMMEND_REVIEW, "rule_ids": ["REN-002"],
                "rationale": "Risk grade is High, so an underwriter must review this policy [REN-002]."}
    if audit["status"] != PASS:
        return {"recommendation": RECOMMEND_REVIEW, "rule_ids": sorted({f["rule_id"] for f in findings}),
                "rationale": f"Audit status is '{audit['status']}'. Findings need review first: "
                             + "; ".join(f"{f['summary']} [{f['rule_id']}]" for f in findings)}
    return {"recommendation": RECOMMEND_RENEWAL, "rule_ids": ["REN-003"],
            "rationale": "No blocking findings were detected. An authorised underwriter must make the decision [REN-003]."}


def draft_rationale(llm, renewal: dict, findings: List[dict]) -> dict:
    """AI wording over fixed facts. It is discarded if it cites anything outside those facts."""
    allowed = set(renewal["rule_ids"]) | {f["rule_id"] for f in findings}
    facts = [f"{f['summary']} [{f['rule_id']}]" for f in findings] or ["No findings."]
    prompt = f"""Write two plain sentences for an underwriter explaining this renewal recommendation.
Use ONLY these facts and cite rule IDs in square brackets. Never say a renewal is approved.
Recommendation: {renewal['recommendation']}
Basis: {renewal['rationale']}
Facts: {facts}"""
    try:
        text = llm.generate_text(prompt).strip()
    except Exception:
        return {**renewal, "rationale_source": "template"}
    cited = set(re.findall(r"\b[A-Z]{3}-\d{3}\b", text))
    if not text or not cited or not cited <= allowed or re.search(r"\bapproved\b", text, re.IGNORECASE):
        return {**renewal, "rationale_source": "template"}
    return {**renewal, "rationale": text, "rationale_source": "ai"}
