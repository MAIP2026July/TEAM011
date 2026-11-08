from typing import Dict, List, Optional

from .config import (ALL_DOCUMENT_TYPES, FILENAME_POLICY, FOLDER_NAME_PATTERN, NAMING_CONVENTIONS,
                     REQUIRED_DOCUMENTS, guess_document_type)


def _finding(rule_id: str, summary: str, document: str = "Folder") -> dict:
    return {"rule_id": rule_id, "summary": summary, "document": document, "source": "rule", "status": "fail",
            "quote": "", "page": 0, "verification": "not_applicable", "confidence_band": "HIGH"}


def validate_folder_structure(folder_name: str, filenames: List[str], content_types: Optional[Dict[str, str]] = None) -> List[dict]:
    """Deterministic checks. content_types (filename -> AI-read type) overrides the filename guess."""
    content_types = content_types or {}
    findings: List[dict] = []
    by_type: Dict[str, List[str]] = {}
    for filename in filenames:
        doc_type = content_types.get(filename, "Unknown")
        if doc_type not in ALL_DOCUMENT_TYPES:
            doc_type = guess_document_type(filename)
        by_type.setdefault(doc_type, []).append(filename)

    if not FOLDER_NAME_PATTERN.match(folder_name):
        findings.append(_finding("STR-001", f"Folder name '{folder_name}' is not a policy number."))
    for filename in filenames:
        match = FILENAME_POLICY.search(filename)
        if match is None or match.group() != folder_name:
            findings.append(_finding("STR-001", "File name does not carry the folder's policy number.", filename))

    for doc_type in REQUIRED_DOCUMENTS:
        if doc_type not in by_type:
            findings.append(_finding("STR-002", f"Required document missing: {doc_type.replace('_', ' ')}."))
        elif len(by_type[doc_type]) > 1:
            findings.append(_finding("STR-003", f"Multiple versions of {doc_type.replace('_', ' ')}: {', '.join(by_type[doc_type])}."))

    for doc_type, files in by_type.items():
        for filename in files:
            if doc_type == "Unknown":
                findings.append(_finding("NAM-001", "File could not be matched to a document type.", filename))
            elif not NAMING_CONVENTIONS[doc_type].match(filename):
                findings.append(_finding("NAM-001", f"Name does not follow the standard for {doc_type.replace('_', ' ')}.", filename))
    return findings
