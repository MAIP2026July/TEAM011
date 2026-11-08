# Wireframe Notes

The working prototype acts as the wireframe. These notes explain why each screen area exists.

| Area | Elements | Reason |
|---|---|---|
| Notice | "Decision support only" and synthetic-data warning | Sets the AI boundary before any result |
| 1. Choose a folder | Sample or upload | Minimal input, one folder at a time |
| 2. Audit readiness | Score, status, open findings, AI suggestion, rationale | Answers "what state is this folder in?" first |
| Failure messages | One line per document that failed | A failure must be impossible to miss |
| 3. Review findings | Severity, rule ID, summary; critical findings open by default | Attention goes to the worst items first |
| Finding detail | Document, page, rule text, quote, verification, confidence, source | Everything needed to decide without searching |
| Decision | Confirm, Reject, Escalate; required reason | Forces a real decision |
| 4. Sign-off | Reviewer, renewal decision with no default, disabled button until complete | Prevents rubber-stamping and accidental approval |
| Record | Confirmation and report download | Produces an auditable output |
| On request | Extracted fields; retrieved rules | Transparency without clutter |

**Language choices**

- "AI suggestion", not "decision".
- "Recommend Renewal – Underwriter Approval Required", not "Approved".
- "Not Scored", not 0, because an unanalysed folder is unknown, not bad.

**Known UX gaps for the pilot**

- Show the source page next to the finding.
- Add a queue view for analysts.
- Let reviewers add a defect the AI missed, which also provides data on missed findings.
- Show Rejected findings separately in the final report summary.
