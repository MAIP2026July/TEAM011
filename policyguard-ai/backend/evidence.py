"""Checks that AI evidence is real, and turns that into a confidence band."""
import io
import re
from typing import List

from pypdf import PdfReader

VERIFIED = "verified"
NOT_FOUND = "not_found"
NO_TEXT_LAYER = "no_text_layer"


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def extract_pages(file_bytes: bytes) -> List[str]:
    """Text per page. Empty for scans, images and anything pypdf cannot read."""
    try:
        return [page.extract_text() or "" for page in PdfReader(io.BytesIO(file_bytes)).pages]
    except Exception:
        return []


def verify_quote(quote: str, pages: List[str]) -> str:
    """Scans cannot be checked here, so they are reported as such and never as verified."""
    if not any(page.strip() for page in pages):
        return NO_TEXT_LAYER
    needle = _normalise(quote)
    if needle and needle in _normalise(" ".join(pages)):
        return VERIFIED
    return NOT_FOUND


def confidence_band(model_confidence: str, verification: str) -> str:
    """Model self-confidence alone can never give HIGH: the quote must also be verified."""
    confidence = (model_confidence or "").lower()
    if verification == NOT_FOUND:
        return "LOW"
    if verification == VERIFIED:
        return {"high": "HIGH", "medium": "MEDIUM"}.get(confidence, "LOW")
    return "MEDIUM" if confidence == "high" else "LOW"
