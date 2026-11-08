"""One audit run. The Streamlit app and the evaluation harness both call run_audit."""
from datetime import date
from typing import Dict, List, Optional, Tuple

from .audit_engine import calculate_audit_score, draft_rationale, generate_renewal_recommendation
from .config import ALL_DOCUMENT_TYPES
from .cross_checks import run_cross_checks
from .document_analyzer import NOT_FOUND_VALUE, assess_rules, extract_document, review_folder, rule_query
from .evidence import confidence_band, extract_pages, verify_quote
from .rulebook_store import RulebookStore, load_rules
from .structure_validator import validate_folder_structure

FolderFile = Tuple[str, bytes, str]  # filename, bytes, mime type


def _attach_rule(findings: List[dict], rules: Dict[str, dict]) -> List[dict]:
    for index, finding in enumerate(findings, start=1):
        rule = rules[finding["rule_id"]]
        finding.update(id=f"F{index:03d}", severity=rule["severity"], category=rule["category"], rule_text=rule["text"])
    return findings


def _ai_rule_findings(assessments: List[dict], retrieved_ids: set, filename: str, pages: List[str], rejected: List[dict]) -> List[dict]:
    findings = []
    for item in assessments:
        if item["rule_id"] not in retrieved_ids:
            rejected.append({"document": filename, **item})  # citation check: only retrieved rules may be cited
            continue
        if item["status"] not in ("fail", "unclear"):
            continue
        verification = verify_quote(item["quote"], pages)
        findings.append({"rule_id": item["rule_id"], "summary": item["explanation"], "document": filename, "source": "ai",
                         "status": item["status"], "quote": item["quote"], "page": item["page"], "verification": verification,
                         "confidence_band": confidence_band(item["confidence"], verification)})
    return findings


def run_audit(folder_name: str, files: List[FolderFile], as_of: date, llm=None, store: Optional[RulebookStore] = None) -> dict:
    rules = load_rules()
    extractions: Dict[str, dict] = {}
    pages: Dict[str, List[str]] = {}
    failed: Dict[str, str] = {}
    findings: List[dict] = []
    rejected_citations: List[dict] = []
    retrieved_log: Dict[str, List[str]] = {}

    for filename, file_bytes, mime_type in files:
        pages[filename] = extract_pages(file_bytes)
        if llm is None or store is None:
            failed[filename] = "AI analysis unavailable"
            continue
        try:
            extraction = extract_document(llm, file_bytes, filename, mime_type)
            doc_type = extraction["document_type"]["value"]
            retrieved = store.retrieve(rule_query(doc_type, extraction["summary"]))
            retrieved_log[filename] = [rule["id"] for rule in retrieved]
            checkable = [rule for rule in retrieved if rule["method"] == "llm" and doc_type in rule["applies_to"]]
            extractions[filename] = extraction
            if checkable:
                assessments = assess_rules(llm, file_bytes, filename, mime_type, checkable)
                findings += _ai_rule_findings(assessments, {r["id"] for r in checkable}, filename, pages[filename], rejected_citations)
        except Exception as error:
            failed[filename] = f"{type(error).__name__}: {error}"
            extractions.pop(filename, None)

    content_types = {name: e["document_type"]["value"] for name, e in extractions.items()
                     if e["document_type"]["value"] in ALL_DOCUMENT_TYPES}
    findings += validate_folder_structure(folder_name, [f[0] for f in files], content_types)
    findings += run_cross_checks(folder_name, extractions, pages, as_of)

    if llm is not None and store is not None and len(extractions) > 1:
        try:
            retrieved = store.retrieve("Proposer name, risk location and sum insured must agree across documents")
            checkable = [rule for rule in retrieved if rule["id"] == "POL-002"]
            if checkable:
                for issue in review_folder(llm, extractions, checkable):
                    findings.append({"rule_id": "POL-002", "summary": issue["explanation"], "document": issue["document"], "source": "ai",
                                     "status": "fail", "quote": issue["quote"], "page": 0, "verification": "extracted_value",
                                     "confidence_band": confidence_band(issue["confidence"], "no_text_layer")})
        except Exception as error:
            failed["Folder consistency review"] = f"{type(error).__name__}: {error}"

    unique = {}
    for finding in findings:
        unique.setdefault((finding["rule_id"], finding["document"], finding["summary"] if finding["document"] == "Folder" else ""), finding)
    findings = _attach_rule(list(unique.values()), rules)
    audit = calculate_audit_score(findings, list(failed))
    grade = next((e["risk_grade"]["value"] for e in extractions.values()
                  if e["document_type"]["value"] == "Risk_Assessment"), NOT_FOUND_VALUE)
    renewal = generate_renewal_recommendation(audit, findings, grade)
    renewal = draft_rationale(llm, renewal, findings) if llm is not None else {**renewal, "rationale_source": "template"}

    return {"folder": folder_name, "as_of": as_of.isoformat(), "findings": findings, "audit": audit, "renewal": renewal,
            "failed_documents": failed, "extractions": extractions, "rejected_citations": rejected_citations,
            "retrieved_rules": retrieved_log}
