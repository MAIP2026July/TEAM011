import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULEBOOK_PATH = ROOT / "knowledge_base" / "rulebook.json"
CHROMA_DIR = Path(os.environ.get("POLICYGUARD_CHROMA_DIR", Path.home() / ".cache" / "policyguard-ai" / "chroma"))  # outside iCloud-synced folders
REVIEW_LOG_PATH = ROOT / "audit_log" / "decisions.jsonl"

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
GEMINI_EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# Expected folder taxonomy
REQUIRED_DOCUMENTS = ["Application", "Risk_Assessment", "Inspection_Report", "Signed_Disclosure"]
OPTIONAL_DOCUMENTS = ["Endorsement", "Renewal_Correspondence"]
ALL_DOCUMENT_TYPES = REQUIRED_DOCUMENTS + OPTIONAL_DOCUMENTS

FOLDER_NAME_PATTERN = re.compile(r"^POL\d+$")
_DATE = r"(?:19|20)\d\d-(?:0[1-9]|1[012])-(?:0[1-9]|[12][0-9]|3[01])"

# Example: POL123456_Application_2023-10-27.pdf
NAMING_CONVENTIONS = {
    doc_type: re.compile(rf"^POL\d+_{doc_type}_{_DATE}\.pdf$") for doc_type in ALL_DOCUMENT_TYPES
}

FILENAME_POLICY = re.compile(r"POL\d+")
FILENAME_DATE = re.compile(_DATE)

# Points lost per open finding
SEVERITY_POINTS = {"critical": 25, "major": 10, "minor": 5}
REVIEW_SCORE = 70

# RAG settings
RETRIEVAL_TOP_K = 10
MIN_DISCLOSURE_FORM_YEAR = 2024
INSPECTION_VALID_MONTHS = 36


def guess_document_type(filename: str) -> str:
    """Filename-only guess. Used as a fallback when content analysis is unavailable."""
    filename_lower = filename.lower()
    for doc_type in ALL_DOCUMENT_TYPES:
        if doc_type.lower() in filename_lower or doc_type.lower().replace("_", " ") in filename_lower:
            return doc_type
    return "Unknown"
