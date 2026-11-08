# PRD: PolicyGuard AI (MVP and Pilot)

**Owner:** Joydev Pain, TEAM011 · **Status:** MVP prototype complete; pilot proposed · **Scope:** commercial property, one folder at a time

## 1. Problem

Underwriting operations analysts check policy folders by hand for structure, naming and content. Checks are slow and inconsistent, so gaps are often found late, during audits or renewals.

## 2. Goals

| Goal | Measure |
|---|---|
| Find compliance gaps earlier | Time from gap arising to detection falls |
| Reduce review effort | Analyst time per folder −40% |
| Support better renewals | Fewer renewals delayed by document gaps |
| Keep people accountable | 100% of findings and renewals have a recorded human decision |

**Non-goals:** automatic sign-off, automatic renewal, pricing, remediation, a general chatbot.

## 3. Users

Operations analysts (primary); compliance and audit teams, renewal teams, underwriting managers, and risk officers (secondary).

## 4. User stories and acceptance criteria

| ID | Story | Acceptance criteria | Status |
|---|---|---|---|
| U1 | As an analyst, I can audit a folder | Sample or upload; PDF, JPG, PNG; result with score and findings | Done |
| U2 | I can see structure and naming problems | Missing, duplicate and misnamed files, and folder/policy mismatches, are flagged | Done |
| U3 | Non-standard names don't look like missing documents | Type read from content; misnamed files raise NAM-001, not STR-002 | Done |
| U4 | I can see content problems | Signature, required content, and form version flagged against rules | Done |
| U5 | I can see cross-document conflicts | Policy number, dates, names, locations and sums compared | Done |
| U6 | I can see why a finding exists | Rule ID and text, document, page, quote, verification, confidence | Done |
| U7 | As a compliance officer, I can trust a Pass | Any open finding blocks a Pass | Done |
| U8 | The system can't hide a failure | Any failed analysis: no score, no recommendation, clear warning | Done |
| U9 | As an underwriter, I get a renewal suggestion | Suggestion with rationale; never worded as an approval | Done |
| U10 | As a reviewer, I decide | Confirm, Reject or Escalate per finding; reason required | Done |
| U11 | As a compliance officer, I have a record | Sign-off blocked until complete; log entry; downloadable report | Done |
| U12 | I work in bulk | Scan and prioritize many folders | Phase 3 |
| U13 | Access is controlled | SSO, roles, masking | Pilot |

## 5. AI role and limits

| AI may | AI may not |
|---|---|
| Classify, extract, and quote documents | Approve a renewal or sign off compliance |
| Assess content against retrieved rules | Invent rules, or rely on outside knowledge |
| Compare soft fields across documents | Decide date or number comparisons (rules do this) |
| Draft a rationale from fixed facts | Add facts, or change the score or recommendation |

## 6. Functional logic

**Score:** starts at 100; critical −25, major −10, minor −5. Below 70 = Fail. Any other open finding = Review Required. Pass requires no open findings.

**Renewal suggestion, in order:**

1. Any analysis failure → No Recommendation.
2. Open critical finding → Recommend Hold.
3. High risk grade, or status is not Pass → Recommend Manual Underwriter Review.
4. Otherwise → Recommend Renewal, Underwriter Approval Required.

**Confidence:** see [04](../../02_Final_Report.pdf).

## 7. Data assumptions

Real documents can be used lawfully; rules can be written as clear statements; scans are legible; past findings can support labeling. See [05](../../02_Final_Report.pdf).

## 8. Fallback logic

| Failure | Behavior |
|---|---|
| No API key, AI error or quota | Not Scored; No Recommendation; warning |
| Rule cited but not retrieved | Statement removed and counted |
| Retrieval misses a signature rule | Signature rules run anyway |
| Quote not found | LOW confidence |
| Scan cannot be verified | Maximum MEDIUM confidence |
| AI rationale fails check | Template rationale |

## 9. Risks

| Risk | Product response |
|---|---|
| Missed critical defect | Signature rules always run; open findings block a Pass; recall gate |
| Fabricated or wrong evidence | Quote and citation checks; person decides; evidence audit |
| Unstable results between runs | Exact checks stay as rules; repeatability gate |
| Over-reliance on AI | Required reasons; no default renewal choice; rejection-rate monitoring |
| Policyholder data exposure | Synthetic data only now; enterprise terms and privacy approval before the pilot |

The full list with owners is in the [Risk Register](../Risk_Note/Risk_Register.md).

## 10. Non-functional requirements

| Area | Prototype | Pilot requirement |
|---|---|---|
| Speed | 33–42 s in live app for one folder | Under 2 minutes |
| Privacy | Synthetic only | Enterprise terms, no retention, approved region, masking |
| Access | None | SSO and roles |
| Audit | Plain log | Tamper-evident log with model and rule versions |
| Change control | Tests and evaluation | Regression gate before any change |

## 11. Release criteria

See the launch thresholds in [05](../../02_Final_Report.pdf) and the blockers in [07](../../02_Final_Report.pdf).

## 12. Open questions

- Which business rules can be automated, and which need people?
- Is a dedicated OCR service needed?
- What retention period applies to audit logs?
- Which model gives the best accuracy at acceptable cost?
- How should repeated runs of one folder be handled if results differ?
