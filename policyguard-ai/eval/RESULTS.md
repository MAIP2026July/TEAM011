# Evaluation Results

Generated from `results_dev.json` and `results_holdout.json`. All data is synthetic. See `TEAM011_Submission/05_Data_Model_Evaluation.md` for how to read these numbers.

Model: `gemini-3.5-flash-lite`. Embeddings: `gemini-embedding-001`.

| Set | System | True positives | False positives | Missed | Precision | Recall |
|---|---|---|---|---|---|---|
| dev | File-name baseline | 4 | 1 | 10 | 80.0% | 28.6% |
| dev | PolicyGuard AI | 14 | 0 | 0 | 100.0% | 100.0% |
| holdout | File-name baseline | 4 | 2 | 12 | 66.7% | 25.0% |
| holdout | PolicyGuard AI | 16 | 1 | 0 | 94.1% | 100.0% |

| Measure | Dev | Holdout |
|---|---|---|
| Renewal match | 100% | 100% |
| Missed critical | 0 | 0 |
| Clean folders flagged | 0 of 3 | 0 of 3 |
| Failed documents | 0 | 0 |
| Rejected citations | 0 | 0 |
| Rule recall at 10 | 100% | 100% |
| Confidence bands | HIGH 12, MEDIUM 2 | HIGH 12, MEDIUM 5 |

## PolicyGuard AI by rule (holdout)

| Rule | Found | False alarm | Missed |
|---|---|---|---|
| CNT-002 | 1 | 0 | 0 |
| CNT-003 | 1 | 0 | 0 |
| CNT-004 | 1 | 0 | 0 |
| DAT-001 | 1 | 0 | 0 |
| DAT-003 | 1 | 0 | 0 |
| FRM-001 | 1 | 0 | 0 |
| NAM-001 | 2 | 0 | 0 |
| NAM-002 | 1 | 0 | 0 |
| POL-001 | 1 | 0 | 0 |
| POL-002 | 1 | 0 | 0 |
| SIG-001 | 1 | 0 | 0 |
| SIG-003 | 1 | 0 | 0 |
| SIG-004 | 1 | 1 | 0 |
| STR-001 | 1 | 0 | 0 |
| STR-002 | 1 | 0 | 0 |
