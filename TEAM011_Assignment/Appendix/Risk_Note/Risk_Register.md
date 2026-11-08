# Risk Register

L = likelihood and I = impact (Low, Medium, High, Very high). Owners are proposed pilot roles, and the status reflects the prototype.

| ID | Risk | L | I | Control | Owner | Status | Early warning |
|---|---|---|---|---|---|---|---|
| R1 | Missed defect / false pass | Medium | Very high | Always-on signature rules; open findings block a Pass; critical recall gate | Product owner | Partly controlled | Auditor finds something the tool missed |
| R2 | Hallucination: fabricated or wrong evidence | Low–Medium | High | Quote and citation checks; evidence audit | Product owner | Partly controlled; scans unverified | Quote not found; reviewers report errors |
| R3 | False alarm on a real signature | Medium | Medium | MEDIUM cap on scans; human review; expert test | Rulebook owner | Open | Signature findings often rejected |
| R4 | Inconsistent results between runs | High | Medium | Repeatability test; rules for exact checks | Product owner | Open | Same folder gives different findings |
| R5 | Over-reliance | Medium | Very high | Required reasons; no default; rejection band | Compliance lead | Partly controlled | Rejection rate under 5%; very short review times |
| R6 | Personal and financial data exposure | Low–Medium | Very high | Synthetic only now; enterprise terms; masking; access control | Security / privacy lead | Pilot prerequisite | Access anomalies; provider terms change |
| R7 | Bias: unequal customer impact | Medium | Medium–High | Flag-rate check by segment; no pricing or eligibility role | Compliance lead | Pilot | Flags cluster in a region or era |
| R8 | Silent failure | Low | Very high | Fail-closed scoring; warning message | Product owner | Controlled and tested | Any score with failed documents |
| R9 | Outdated rules | Medium | High | Versioned rulebook; named owner; regulatory watch | Rulebook owner | Pilot | Rule older than review cycle |
| R10 | Misuse of scores or logs | Low–Medium | Medium | Pilot charter; "decision support" wording | Underwriting manager | Pilot | Logs requested for appraisals |
| R11 | Provider or model change | Medium | Medium | Pinned versions; one connection module; regression test | Tech lead | Partly controlled | Deprecation notices. The 2.5-series models were already unavailable to new users during this project. |
| R12 | Rate limits or outage | Medium | Medium | Enterprise quota; fail closed; manual fallback | Tech lead | Partly controlled | 429 errors; rising Not Scored count |
| R13 | Prompt injection in a document | Low–Medium | High | Quote checks; rules decide scores; fixed output schema; test needed | Tech lead | Not tested | Odd output after reading a document |
| R14 | Team or skills change | Medium | Medium | Rulebook ownership; written rules | Compliance lead | Pilot | Owner role unfilled |
