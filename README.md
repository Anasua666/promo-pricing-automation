# Promo Pricing Automation

AI-agent automation for the pricing & promotion submission and approval cycle
(currently a manual process run by a verification team and pricing admins).

This replaces two manual steps with LangGraph-orchestrated agents backed by
Amazon Bedrock:

1. **Submission Agent** — verifies uploaded pricing data (subs, brands,
   divisions, sub-divisions, store/dot-com channel) against the fiscal
   calendar + price files the merchant team provides, then submits the
   week's pricing package.
2. **Approval Agent** — reviews submitted packages per channel (STORE vs
   DIRECT/.com), approves, rejects (with merchant email notification), or
   leaves pending, and moves files between `approved/ rejected/ pending`
   folders. Approved data becomes available to the downstream inference job.

The CSV upload job that lands pricing data in the database is **out of
scope** — this system starts *after* data is already in the DB.

## Architecture

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full flow diagram
and a mapping of every step you described (color-coded week states, sub
numbers, folder paths, email-on-reject, etc.) to the code that implements it.

```
Uploaded pricing data (DB)
        │
        ▼
┌───────────────────┐
│ Submission Agent   │  verifies vs fiscal calendar/price files
└─────────┬──────────┘
          │ submit
          ▼
   /submissions/pending/{week}/*.json
          │
          ▼
┌───────────────────┐
│  Approval Agent    │  per-channel review (STORE / DIRECT)
└─────────┬──────────┘
     ┌────┼─────┐
     ▼    ▼     ▼
 approved reject pending
     │    │
     │    └─► email merchant
     ▼
 Inference job picks up approved data (out of scope, downstream)
```

## Project layout

```
src/
  config.py            # env-driven settings incl. Bedrock model id/region
  models/pricing.py     # PricingSubmission, PricingLineItem, etc.
  db/repository.py       # DB access layer (stub — plug in your real DB)
  tools/
    excel_tools.py       # compare fiscal calendar / price sheets vs DB rows
    file_tools.py         # move files between pending/approved/rejected
    email_tools.py         # notify merchants on rejection
  agents/
    submission_agent.py    # LangChain agent wrapping verification tools
    approval_agent.py       # LangChain agent wrapping approval tools
  graph/
    state.py                 # LangGraph shared state schema
    workflow.py                # LangGraph graph wiring both agents together
  main.py                       # CLI entry point to run one cycle
tests/
  test_workflow.py               # smoke test with mock data
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # fill in AWS creds / Bedrock model id / DB URL
```

## Run

```bash
python -m src.main --week 2026-07-14
```

This runs one full cycle (submission verification → approval decisions) for
the given fiscal week using whatever data your `db/repository.py`
implementation returns.

## Configuring Amazon Bedrock

Set these in `.env` (see `.env.example`):

```
BEDROCK_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

`src/config.py` reads these and `src/agents/*.py` build a `ChatBedrock`
(from `langchain-aws`) using them. Swap the model id for whatever's
available in your account/region.

## Next steps to wire up your real system

- [ ] Implement `db/repository.py` against your actual pricing tables
      (subs, brands, divisions, start/end dates).
- [ ] Point `file_tools.py` at your real submission/approval folder paths.
- [ ] Implement `email_tools.py` against your mail provider (SES, SMTP, etc.)
- [ ] Decide how "current week / +1 / +2 / +3-4 weeks" color coding maps to
      any business rules the agent should apply (e.g. stricter checks for
      current-week red items) — see `TODO` markers in `submission_agent.py`.
- [ ] Add the downstream inference-job trigger once approvals land in the
      approved folder (out of scope here, but there's a hook noted in
      `approval_agent.py`).

## Pushing this to GitHub

```bash
cd promo-pricing-automation
git init
git add .
git commit -m "Initial scaffold: LangGraph submission + approval agents"
git branch -M main
git remote add origin https://github.com/<your-username>/promo-pricing-automation.git
git push -u origin main
```

Then invite your teammate: GitHub repo → **Settings → Collaborators → Add people**.
