# Audit-readiness report: POL200007

Decision support only. Rules come from a fictional demonstration rulebook.

- Audit date: 2026-11-07
- Score: 65
- Status: Fail - Critical Action Needed
- AI recommendation: Recommend Hold - Compliance Escalation
- Rationale: The renewal is currently on hold pending a compliance escalation because the document shows policy number POL888888 while the folder is POL200007 [POL-001]. Additionally, the risk assessment conducted on January 6, 2026, predates the application submitted on January 9, 2026 [DAT-001].
- Human renewal decision: Hold pending remediation
- Signed off by: Demo Reviewer at 2026-11-07T09:44:52.275050+00:00

## Findings

### F001 · POL-001 · critical · MEDIUM confidence
- Finding: Document shows POL888888; folder is POL200007.
- Document: POL200007_Risk_Assessment_2026-01-06.pdf (page 1)
- Evidence: "Proposal Ref No.: POL888888" (no_text_layer)
- Human decision: Confirm: Checked against the source document.

### F002 · DAT-001 · major · MEDIUM confidence
- Finding: Risk Assessment (2026-01-06) predates the Application (2026-01-09).
- Document: POL200007_Risk_Assessment_2026-01-06.pdf (page 1)
- Evidence: "Dated: 06/01/2026" (no_text_layer)
- Human decision: Confirm: Checked against the source document.
