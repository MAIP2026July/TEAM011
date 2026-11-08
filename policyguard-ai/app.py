import mimetypes
import os
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from backend.audit_engine import NOT_SCORED, PASS, RECOMMEND_RENEWAL, REVIEW
from backend.llm_client import GeminiClient
from backend.pipeline import run_audit
from backend.review_log import DECISIONS, build_report, missing_reviews, record_sign_off
from backend.rulebook_store import RulebookStore

SAMPLES = Path(__file__).parent / "eval" / "folders"
SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2}
BAND_ICON = {"HIGH": "🟢", "MEDIUM": "🟠", "LOW": "🔴"}

st.set_page_config(page_title="PolicyGuard AI", page_icon="🛡️", layout="wide")
st.title("🛡️ PolicyGuard AI")
st.subheader("Compliance copilot for underwriting document folders")
st.info("Decision support only. A person reviews every finding and makes every renewal decision. "
        "Rules come from a fictional demonstration rulebook. Use synthetic data only.")


@st.cache_resource(show_spinner="Loading the rulebook index...")
def load_services(api_key: str):
    llm = GeminiClient(api_key=api_key)
    return llm, RulebookStore(llm.embed, llm.embed_model)


with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Gemini API Key", value=os.environ.get("GEMINI_API_KEY", ""), type="password")
    as_of = st.date_input("Audit date", value=date.today())
    if not api_key:
        st.warning("No API key: the folder cannot be analysed, so it will not be scored.")

st.header("1. Choose a policy folder")
source = st.radio("Source", ["Sample folder", "Upload files"], horizontal=True)
folder_name, files = "", []
if source == "Sample folder":
    samples = sorted(p for p in SAMPLES.glob("*/POL*") if p.is_dir())
    if samples:
        picked = st.selectbox("Sample folder (synthetic)", samples, format_func=lambda p: f"{p.parent.name} / {p.name}")
        folder_name = picked.name
        files = [(p.name, p.read_bytes(), "application/pdf") for p in sorted(picked.glob("*.pdf"))]
    else:
        st.warning("No samples yet. Run: python eval/generate_folders.py")
else:
    folder_name = st.text_input("Policy folder name", placeholder="POL123456")
    uploads = st.file_uploader("Policy documents (PDF, JPG, PNG)", accept_multiple_files=True, type=["pdf", "jpg", "jpeg", "png"])
    files = [(u.name, u.getvalue(), u.type or mimetypes.guess_type(u.name)[0]) for u in uploads or []]

if files and folder_name and st.button("Run compliance audit", type="primary"):
    with st.spinner("Auditing the folder..."):
        llm, store = load_services(api_key) if api_key else (None, None)
        st.session_state.result = run_audit(folder_name, files, as_of, llm, store)
        st.session_state.signed = None

result = st.session_state.get("result")
if result:
    audit, renewal = result["audit"], result["renewal"]
    findings = sorted(result["findings"], key=lambda f: SEVERITY_ORDER[f["severity"]])

    st.header(f"2. Audit readiness: {result['folder']}")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Audit readiness score", "Not scored" if audit["score"] is None else f"{audit['score']}/100")
        show = st.success if audit["status"] == PASS else st.warning if audit["status"] == REVIEW else st.error
        show(audit["status"])
        if audit["reason"]:
            st.write(audit["reason"])
    with col2:
        st.metric("Open findings", len(findings))
        show = st.success if renewal["recommendation"] == RECOMMEND_RENEWAL else st.warning if "Manual" in renewal["recommendation"] else st.error
        show(f"AI suggestion: {renewal['recommendation']}")
        st.write(f"**Rationale:** {renewal['rationale']}")

    for name, reason in result["failed_documents"].items():
        st.error(f"Could not analyse {name}: {reason}")
    if result["rejected_citations"]:
        st.warning(f"{len(result['rejected_citations'])} AI statement(s) cited a rule that was not retrieved and were removed.")

    st.header("3. Review each finding")
    decisions = {}
    for finding in findings:
        title = f"{BAND_ICON[finding['confidence_band']]} {finding['id']} · {finding['severity'].upper()} · {finding['rule_id']}: {finding['summary']}"
        with st.expander(title, expanded=finding["severity"] == "critical"):
            st.write(f"**Document:** {finding['document']}" + (f" (page {finding['page']})" if finding["page"] else ""))
            st.write(f"**Rule:** {finding['rule_text']}")
            if finding["quote"]:
                st.write(f"**Evidence:** “{finding['quote']}” ({finding['verification'].replace('_', ' ')})")
            st.write(f"**Confidence:** {finding['confidence_band']} · **Source:** {finding['source']} · **Status:** {finding['status']}")
            decision = st.radio("Your decision", DECISIONS, index=None, horizontal=True, key=f"decision-{finding['id']}")
            reason = st.text_input("Reason (required)", key=f"reason-{finding['id']}")
            decisions[finding["id"]] = {"decision": decision, "reason": reason}
    if not findings:
        if result["failed_documents"]:
            st.warning("Nothing to review because the analysis did not run. This does not mean the folder is compliant.")
        else:
            st.success("No findings. A person must still sign off below.")

    st.header("4. Human sign-off")
    if audit["status"] == NOT_SCORED:
        st.warning("This folder was not fully analysed, so check it by hand before signing.")
    reviewer = st.text_input("Reviewer name")
    renewal_decision = st.selectbox("Your renewal decision", ["Approve renewal", "Reject renewal", "Refer to underwriting SME", "Hold pending remediation"],
                                    index=None, placeholder="Choose a decision")  # no default: the reviewer must decide
    outstanding = missing_reviews(findings, decisions)
    if outstanding:
        st.caption(f"Still to review: {', '.join(outstanding)}")
    if st.button("Sign off", disabled=bool(outstanding) or not reviewer.strip() or renewal_decision is None):
        st.session_state.signed = record_sign_off(result, decisions, reviewer, renewal_decision)
    if st.session_state.get("signed"):
        st.success("Signed off and written to the audit log.")
        st.download_button("Download audit report", build_report(result, st.session_state.signed), f"{result['folder']}_audit_report.md")

    with st.expander("What the AI extracted"):
        st.dataframe(pd.DataFrame([{"File": name, **{k: v["value"] for k, v in e.items() if isinstance(v, dict) and "value" in v}, "Signed": e["signature"]["signed"]}
                                   for name, e in result["extractions"].items()]), use_container_width=True)
    with st.expander("Rules retrieved for each document (RAG)"):
        st.json(result["retrieved_rules"])
