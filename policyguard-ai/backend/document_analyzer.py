"""AI analysis. Every answer must point to evidence, and rules come from the rulebook."""
from typing import Dict, List

from pydantic import BaseModel, Field

from .config import ALL_DOCUMENT_TYPES
from .evidence import confidence_band, verify_quote

NOT_FOUND_VALUE = "Not Found"


class EvidencedValue(BaseModel):
    value: str = Field(description="The value exactly as printed. Dates as YYYY-MM-DD. 'Not Found' if absent.")
    quote: str = Field(description="Short verbatim text from the document supporting the value. Empty if absent.")
    page: int = Field(description="1-based page of the quote. 0 if absent.")
    confidence: str = Field(description="high, medium or low")


class SignatureObservation(BaseModel):
    signed: bool = Field(description="True only if a real signature or a marked signature is present. A blank line or printed name alone is False.")
    quote: str = Field(description="Verbatim text of the signature line.")
    page: int = Field(description="1-based page of the signature line.")
    confidence: str = Field(description="high, medium or low")


class DocumentExtraction(BaseModel):
    document_type: EvidencedValue = Field(description=f"Judge from the content, not the filename. One of: {', '.join(ALL_DOCUMENT_TYPES)}, Unknown.")
    policy_number: EvidencedValue
    document_date: EvidencedValue = Field(description="The date this document was issued, assessed, inspected or signed.")
    effective_date: EvidencedValue = Field(description="The policy effective date, if stated.")
    proposer_name: EvidencedValue
    risk_location: EvidencedValue
    sum_insured: EvidencedValue
    risk_grade: EvidencedValue = Field(description="Low, Medium or High, if stated.")
    form_version: EvidencedValue = Field(description="The form version such as DF-2024, if stated.")
    signature: SignatureObservation
    summary: str = Field(description="One sentence on what this document is.")


class RuleAssessment(BaseModel):
    rule_id: str = Field(description="An ID from the rules provided. Never invent one.")
    status: str = Field(description="pass, fail or unclear")
    explanation: str = Field(description="One sentence on why, using only this document.")
    quote: str = Field(description="Verbatim supporting text. For something missing, quote the nearest label.")
    page: int = Field(description="1-based page of the quote.")
    confidence: str = Field(description="high, medium or low")


class RuleAssessments(BaseModel):
    assessments: List[RuleAssessment]


class FolderIssue(BaseModel):
    rule_id: str = Field(description="An ID from the rules provided. Never invent one.")
    explanation: str
    document: str = Field(description="Filename of the document in conflict.")
    quote: str = Field(description="Verbatim value from the extracted details.")
    confidence: str = Field(description="high, medium or low")


class FolderReview(BaseModel):
    issues: List[FolderIssue]


def extract_document(llm, file_bytes: bytes, filename: str, mime_type: str) -> dict:
    prompt = f"""You are an expert insurance underwriting auditor. Read this document (filename: {filename}).
Identify the document type from its content; the filename may be wrong or non-standard.
Extract each field with a verbatim quote and page. Never guess: return 'Not Found' when a value is absent.
Inspect the signature area closely, including any image of a signature."""
    return llm.analyse_file(file_bytes, filename, mime_type, prompt, DocumentExtraction)


def rule_query(document_type: str, summary: str) -> str:
    return f"Compliance requirements for a {document_type.replace('_', ' ')}: {summary}"


def _rules_text(rules: List[dict]) -> str:
    return "\n".join(f"- {rule['id']}: {rule['text']}" for rule in rules)


def assess_rules(llm, file_bytes: bytes, filename: str, mime_type: str, rules: List[dict]) -> List[dict]:
    prompt = f"""You are an expert insurance underwriting auditor. Check this document (filename: {filename})
against ONLY the rules below. Some may not apply to this document type: leave those out.
Use 'unclear' when you cannot tell. Do not rely on outside knowledge.

Rules:
{_rules_text(rules)}"""
    return llm.analyse_file(file_bytes, filename, mime_type, prompt, RuleAssessments)["assessments"]


def review_folder(llm, extractions: Dict[str, dict], rules: List[dict]) -> List[dict]:
    details = {
        filename: {field: extraction[field]["value"] for field in ("document_type", "proposer_name", "risk_location", "sum_insured")}
        for filename, extraction in extractions.items()
    }
    prompt = f"""You are an expert insurance underwriting auditor. These are details extracted from one policy folder:
{details}

Report only real conflicts between documents under the rules below. Values that are 'Not Found' are not conflicts.
Return an empty list if there are none.

Rules:
{_rules_text(rules)}"""
    return llm.generate_json(prompt, FolderReview)["issues"]


def extraction_quote_is_real(field: dict, pages: List[str]) -> str:
    return verify_quote(field.get("quote", ""), pages)


def field_band(field: dict, pages: List[str]) -> str:
    return confidence_band(field.get("confidence", ""), extraction_quote_is_real(field, pages))
