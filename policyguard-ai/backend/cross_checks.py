"""Deterministic checks over AI-extracted values. Exact comparisons stay out of the LLM on purpose."""
import re
from datetime import date
from typing import Dict, List, Optional

from .config import FILENAME_DATE, INSPECTION_VALID_MONTHS, MIN_DISCLOSURE_FORM_YEAR
from .document_analyzer import NOT_FOUND_VALUE, field_band
from .evidence import verify_quote


# Signature rules are always applied, so a retrieval miss can never hide an unsigned document.
SIGNATURE_RULES = {"Application": "SIG-001", "Signed_Disclosure": "SIG-002", "Risk_Assessment": "SIG-003", "Inspection_Report": "SIG-004"}


def _date(value: str) -> Optional[date]:
    try:
        return date.fromisoformat(value.strip())
    except (AttributeError, ValueError):
        return None


def _finding(rule_id: str, summary: str, filename: str, field: dict, pages: List[str], status: str = "fail") -> dict:
    return {"rule_id": rule_id, "summary": summary, "document": filename, "source": "ai+rule", "status": status,
            "quote": field.get("quote", ""), "page": field.get("page", 0),
            "verification": verify_quote(field.get("quote", ""), pages), "confidence_band": field_band(field, pages)}


def _months_between(earlier: date, later: date) -> int:
    return (later.year - earlier.year) * 12 + later.month - earlier.month - (later.day < earlier.day)


def run_cross_checks(folder_name: str, extractions: Dict[str, dict], pages: Dict[str, List[str]], as_of: date) -> List[dict]:
    findings: List[dict] = []
    dated: Dict[str, tuple] = {}

    for filename, extraction in extractions.items():
        doc_pages = pages[filename]
        policy = extraction["policy_number"]
        if policy["value"] == NOT_FOUND_VALUE:
            findings.append(_finding("POL-001", "Policy number could not be found in this document.", filename, policy, doc_pages, "unclear"))
        elif policy["value"].strip() != folder_name:
            findings.append(_finding("POL-001", f"Document shows {policy['value']}; folder is {folder_name}.", filename, policy, doc_pages))

        signature_rule = SIGNATURE_RULES.get(extraction["document_type"]["value"])
        if signature_rule and not extraction["signature"]["signed"]:
            findings.append(_finding(signature_rule, "No signature was detected on this document.", filename, extraction["signature"], doc_pages))

        field = extraction["document_date"]
        parsed = _date(field["value"])
        if parsed is None:
            findings.append(_finding("DAT-002", "Document date could not be read.", filename, field, doc_pages, "unclear"))
            continue
        dated[extraction["document_type"]["value"]] = (parsed, filename, field)
        in_name = FILENAME_DATE.search(filename)
        if in_name and _date(in_name.group()) != parsed:
            findings.append(_finding("NAM-002", f"File name says {in_name.group()}; document says {parsed}.", filename, field, doc_pages))

    application = dated.get("Application")
    if application:
        for doc_type in ("Risk_Assessment", "Inspection_Report"):
            if doc_type in dated and dated[doc_type][0] < application[0]:
                when, filename, field = dated[doc_type]
                findings.append(_finding("DAT-001", f"{doc_type.replace('_', ' ')} ({when}) predates the Application ({application[0]}).", filename, field, pages[filename]))

    effective = next((_date(e["effective_date"]["value"]) for e in extractions.values()
                      if e["document_type"]["value"] == "Application"), None)
    if effective:
        for doc_type in ("Risk_Assessment", "Inspection_Report", "Signed_Disclosure"):
            if doc_type in dated and dated[doc_type][0] > effective:
                when, filename, field = dated[doc_type]
                findings.append(_finding("DAT-002", f"{doc_type.replace('_', ' ')} ({when}) is after the effective date ({effective}).", filename, field, pages[filename]))

    inspection = dated.get("Inspection_Report")
    if inspection and _months_between(inspection[0], as_of) > INSPECTION_VALID_MONTHS:
        when, filename, field = inspection
        findings.append(_finding("DAT-003", f"Inspection dated {when} is over {INSPECTION_VALID_MONTHS} months old.", filename, field, pages[filename]))

    for filename, extraction in extractions.items():
        if extraction["document_type"]["value"] != "Signed_Disclosure":
            continue
        field = extraction["form_version"]
        year = re.search(r"DF-(\d{4})", field["value"])
        if year is None:
            findings.append(_finding("FRM-001", "Form version could not be identified.", filename, field, pages[filename], "unclear"))
        elif int(year.group(1)) < MIN_DISCLOSURE_FORM_YEAR:
            findings.append(_finding("FRM-001", f"Withdrawn form version {field['value']}.", filename, field, pages[filename]))
    return findings
