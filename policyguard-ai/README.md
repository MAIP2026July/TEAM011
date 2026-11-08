# PolicyGuard AI

An intelligent compliance assistant for insurance underwriting document audit and policy renewal. It is decision support only: a person reviews every finding and makes every renewal decision. All data and rules here are fictional.

**TEAM011 · Joydev Pain (2025MB26105) · MBA ZG583 Management of AI Products.** The assignment package (executive summary, final report, deck, AI collaboration log, contribution statement and appendix) is at the [repository root](../). This folder holds the prototype code.

## Setup

If this project is in an iCloud-synced folder, keep the virtual environment outside it.

```bash
python3.13 -m venv ~/.venvs/policyguard-ai
~/.venvs/policyguard-ai/bin/pip install -r requirements.txt
cp .env.example .env    # then add your Gemini API key
```

## Run

```bash
~/.venvs/policyguard-ai/bin/python -m streamlit run app.py      # app
~/.venvs/policyguard-ai/bin/python -m pytest tests              # tests, no API key needed
~/.venvs/policyguard-ai/bin/python eval/evaluate.py holdout     # evaluation
```

`eval/generate_folders.py` rebuilds the test folders. `mock_data/` and `create_mock_data.py` are the original sample data; use `eval/folders/` instead. The old "compliant" folder now raises a date finding, because its risk assessment predates its application.

Do not use real policyholder data, or a free API tier, for anything beyond this demonstration.
