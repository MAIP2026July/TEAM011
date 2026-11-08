# Metric Tree

Model metrics matter only when they connect to business outcomes.

```mermaid
flowchart TD
    N[North star:<br/>Compliance gaps fixed before<br/>an auditor or renewal finds them]
    N --> B1[Findings first raised<br/>by third-party audit]
    N --> B2[Time from gap to detection]
    N --> B3[Renewals delayed<br/>by document gaps]
    N --> B4[Analyst time per folder]
    B1 --> P1[Share of in-scope folders<br/>reviewed with the tool]
    B2 --> P1
    B3 --> P1
    B4 --> P2[Time to review findings]
    P1 --> T1[Usefulness rating]
    P2 --> T2[Precision]
    B1 --> M1[Recall on critical defects]
    B1 --> M2[Overall recall]
    M1 --> M3[Rule retrieval recall]
    M1 --> M4[Extraction and signature accuracy]
    T1 --> T3[Evidence accuracy]
    T1 --> T4[Repeatability]
    T5[Rejection rate band] --> T1
    T6[False passes on failed analysis] --> N
```

| Level | Metric | Prototype result (synthetic holdout) | Pilot target |
|---|---|---|---|
| Business | Findings first raised by auditors | Not measured | Trend down |
| Business | Time from gap to detection | Not measured | Falling |
| Business | Renewals delayed by gaps | Not measured | Trend down |
| Product | Analyst time per folder | Not measured | −40% |
| Product | Adoption | Not measured | ≥ 80% |
| Model | Recall on critical defects | 3 of 3 | ≥ 95% |
| Model | Overall recall | 16 of 16 | ≥ 85% |
| Model | Precision | 94.1% | ≥ 70% |
| Model | Rule retrieval recall at 10 | 100% | ≥ 98% |
| Trust | Fabricated evidence | Not audited by a person | 0 of 100 |
| Trust | Repeatability | Not measured formally; variation seen | ≥ 95% |
| Trust | False passes on failed analysis | 0 | 0 |
| Trust | Usefulness | Not measured | ≥ 70% |
| Trust | Rejection rate | Not measured | 10–40% |

**Reading the table:** model metrics exist today only on synthetic data. Every business metric still needs the pilot.
