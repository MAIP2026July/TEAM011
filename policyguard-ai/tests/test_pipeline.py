"""Runs without an API key: Gemini is replaced by a scripted fake."""
import hashlib
import json
from datetime import date

import pytest

from backend import audit_engine as ae
from backend.evidence import confidence_band, verify_quote
from backend.pipeline import run_audit
from backend.review_log import missing_reviews, record_sign_off
from backend.rulebook_store import RulebookStore, load_rules
from backend.structure_validator import validate_folder_structure

AS_OF = date(2026, 11, 1)
P = "POL100001"
TYPES = ["Application", "Risk_Assessment", "Inspection_Report", "Signed_Disclosure"]
DATES = {"Application": "2026-01-10", "Risk_Assessment": "2026-01-14", "Inspection_Report": "2026-01-19", "Signed_Disclosure": "2026-01-24"}


def fake_embed(texts):
    vectors = []
    for text in texts:
        words = set(text.lower().replace(":", " ").replace(",", " ").split())
        vectors.append([1.0 if hashlib.md5(str(i).encode()).hexdigest()[0] in "".join(sorted(w[0] for w in words)) else 0.1 for i in range(32)])
    return vectors


class AllRulesStore:
    """Returns every rule, so tests exercise the pipeline rather than the fake embedding."""
    def retrieve(self, query, top_k=6):
        return list(load_rules().values())


def value(text, quote=None):
    return {"value": text, "quote": quote if quote is not None else text, "page": 1, "confidence": "high"}


def extraction(doc_type, policy=P, signed=True, when=None, form="DF-2025", grade="Low"):
    return {"document_type": value(doc_type), "policy_number": value(policy), "document_date": value(when or DATES[doc_type]),
            "effective_date": value("2026-02-09"), "proposer_name": value("Acme"), "risk_location": value("Pune"), "sum_insured": value("100"),
            "risk_grade": value(grade), "form_version": value(form), "signature": {"signed": signed, "quote": "Signature", "page": 1, "confidence": "high"}, "summary": "x"}


class FakeLLM:
    model, embed_model = "fake", "fake"

    def __init__(self, extractions, assessments=None, fail_on=None, narrative="Summary [REN-003]."):
        self.extractions, self.assessments, self.fail_on, self.narrative = extractions, assessments or {}, fail_on, narrative

    def analyse_file(self, file_bytes, filename, mime_type, prompt, schema):
        if filename == self.fail_on:
            raise RuntimeError("503")
        if schema.__name__ == "DocumentExtraction":
            return self.extractions[filename]
        return {"assessments": self.assessments.get(filename, [])}

    def generate_json(self, prompt, schema):
        return {"issues": []}

    def generate_text(self, prompt):
        return self.narrative


def folder(types=TYPES):
    return [(f"{P}_{t}_{DATES[t]}.pdf", b"not a real pdf", "application/pdf") for t in types]


def extractions_for(types=TYPES):
    return {f"{P}_{t}_{DATES[t]}.pdf": extraction(t) for t in types}


def test_clean_folder_passes_but_only_recommends():
    result = run_audit(P, folder(), AS_OF, FakeLLM(extractions_for()), AllRulesStore())
    assert result["audit"]["score"] == 100 and result["audit"]["status"] == ae.PASS
    assert result["renewal"]["recommendation"] == ae.RECOMMEND_RENEWAL
    assert "approved for" not in result["renewal"]["recommendation"].lower()


def test_no_api_key_fails_closed():
    result = run_audit(P, folder(), AS_OF)
    assert result["audit"]["score"] is None and result["audit"]["status"] == ae.NOT_SCORED
    assert result["renewal"]["recommendation"] == ae.NO_RECOMMENDATION


def test_one_document_failing_fails_closed():
    names = list(extractions_for())
    result = run_audit(P, folder(), AS_OF, FakeLLM(extractions_for(), fail_on=names[0]), AllRulesStore())
    assert result["audit"]["score"] is None and result["renewal"]["recommendation"] == ae.NO_RECOMMENDATION


def test_content_type_rescues_nonstandard_name():
    name = f"{P}_App_2026-01-10.pdf"
    found = {f["rule_id"] for f in validate_folder_structure(P, [name], {name: "Application"})}
    assert "NAM-001" in found
    assert "Application" not in " ".join(f["summary"] for f in validate_folder_structure(P, [name], {name: "Application"}) if f["rule_id"] == "STR-002")


def test_filename_only_treats_nonstandard_name_as_missing():
    findings = validate_folder_structure(P, [f"{P}_App_2026-01-10.pdf"])
    assert any("Application" in f["summary"] for f in findings if f["rule_id"] == "STR-002")


def test_wrong_policy_number_is_critical_and_holds_renewal():
    ex = extractions_for()
    name = f"{P}_Risk_Assessment_{DATES['Risk_Assessment']}.pdf"
    ex[name] = extraction("Risk_Assessment", policy="POL888888")
    result = run_audit(P, folder(), AS_OF, FakeLLM(ex), AllRulesStore())
    assert "POL-001" in {f["rule_id"] for f in result["findings"]}
    assert result["renewal"]["recommendation"] == ae.RECOMMEND_HOLD


def test_risk_assessment_before_application_is_flagged():
    ex = extractions_for()
    name = f"{P}_Risk_Assessment_{DATES['Risk_Assessment']}.pdf"
    ex[name] = extraction("Risk_Assessment", when="2026-01-01")
    result = run_audit(P, folder(), AS_OF, FakeLLM(ex), AllRulesStore())
    assert {"DAT-001", "NAM-002"} <= {f["rule_id"] for f in result["findings"]}


def test_expired_inspection_and_old_form():
    ex = extractions_for()
    ex[f"{P}_Signed_Disclosure_{DATES['Signed_Disclosure']}.pdf"] = extraction("Signed_Disclosure", form="DF-2021")
    result = run_audit(P, folder(), date(2029, 6, 1), FakeLLM(ex), AllRulesStore())
    assert {"DAT-003", "FRM-001"} <= {f["rule_id"] for f in result["findings"]}


def test_invented_rule_id_is_rejected():
    name = f"{P}_Application_{DATES['Application']}.pdf"
    bad = {"rule_id": "XXX-999", "status": "fail", "explanation": "made up", "quote": "q", "page": 1, "confidence": "high"}
    result = run_audit(P, folder(), AS_OF, FakeLLM(extractions_for(), {name: [bad]}), AllRulesStore())
    assert result["rejected_citations"] and "XXX-999" not in {f["rule_id"] for f in result["findings"]}


def test_ai_narrative_with_bad_citation_falls_back():
    result = run_audit(P, folder(), AS_OF, FakeLLM(extractions_for(), narrative="All fine [ZZZ-001]."), AllRulesStore())
    assert result["renewal"]["rationale_source"] == "template"


def test_ai_narrative_saying_approved_falls_back():
    result = run_audit(P, folder(), AS_OF, FakeLLM(extractions_for(), narrative="Renewal is approved [REN-003]."), AllRulesStore())
    assert result["renewal"]["rationale_source"] == "template"


def test_unsigned_is_caught_even_if_retrieval_misses_the_rule():
    class NoSignatureRules:
        def retrieve(self, query, top_k=6):
            return [r for r in load_rules().values() if not r["id"].startswith("SIG")]
    ex = extractions_for()
    ex[f"{P}_Application_{DATES['Application']}.pdf"] = extraction("Application", signed=False)
    result = run_audit(P, folder(), AS_OF, FakeLLM(ex), NoSignatureRules())
    assert "SIG-001" in {f["rule_id"] for f in result["findings"]}
    assert result["renewal"]["recommendation"] == ae.RECOMMEND_HOLD


def test_same_rule_on_same_document_counts_once():
    name = f"{P}_Application_{DATES['Application']}.pdf"
    ex = extractions_for()
    ex[name] = extraction("Application", signed=False)
    ai = {"rule_id": "SIG-001", "status": "fail", "explanation": "Blank", "quote": "q", "page": 1, "confidence": "high"}
    result = run_audit(P, folder(), AS_OF, FakeLLM(ex, {name: [ai]}), AllRulesStore())
    assert [f["rule_id"] for f in result["findings"]] == ["SIG-001"]
    assert result["audit"]["score"] == 75


def test_one_open_finding_never_passes():
    ex = extractions_for()
    ex[f"{P}_Signed_Disclosure_{DATES['Signed_Disclosure']}.pdf"] = extraction("Signed_Disclosure", form="DF-2021")
    result = run_audit(P, folder(), AS_OF, FakeLLM(ex), AllRulesStore())
    assert result["audit"]["score"] == 90 and result["audit"]["status"] == ae.REVIEW
    assert result["renewal"]["recommendation"] == ae.RECOMMEND_REVIEW


def test_high_grade_goes_to_manual_review():
    ex = extractions_for()
    ex[f"{P}_Risk_Assessment_{DATES['Risk_Assessment']}.pdf"] = extraction("Risk_Assessment", grade="High")
    result = run_audit(P, folder(), AS_OF, FakeLLM(ex), AllRulesStore())
    assert result["renewal"]["recommendation"] == ae.RECOMMEND_REVIEW


def test_evidence_and_bands():
    pages = ["Signature: ____  Policy  Number: POL1"]
    assert verify_quote("policy number: pol1", pages) == "verified"
    assert verify_quote("something invented", pages) == "not_found"
    assert verify_quote("anything", []) == "no_text_layer"
    assert confidence_band("high", "verified") == "HIGH"
    assert confidence_band("high", "not_found") == "LOW"
    assert confidence_band("high", "no_text_layer") == "MEDIUM"


def test_sign_off_needs_every_review_and_a_reason(tmp_path):
    result = run_audit(P, folder(TYPES[:3]), AS_OF, FakeLLM(extractions_for(TYPES[:3])), AllRulesStore())
    ids = [f["id"] for f in result["findings"]]
    assert missing_reviews(result["findings"], {}) == ids
    empty_reason = {i: {"decision": "Confirm", "reason": " "} for i in ids}
    with pytest.raises(ValueError):
        record_sign_off(result, empty_reason, "Reviewer", "Reject renewal", tmp_path / "log.jsonl")
    good = {i: {"decision": "Confirm", "reason": "Checked"} for i in ids}
    record_sign_off(result, good, "Reviewer", "Reject renewal", tmp_path / "log.jsonl")
    assert json.loads((tmp_path / "log.jsonl").read_text())["renewal_decision"] == "Reject renewal"


def test_chroma_store_builds_and_retrieves(tmp_path):
    store = RulebookStore(fake_embed, "test", path=tmp_path)
    retrieved = store.retrieve("signature on the application", top_k=3)
    assert len(retrieved) == 3 and all("distance" in rule for rule in retrieved)
