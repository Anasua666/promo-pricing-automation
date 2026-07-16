# Architecture

## Domain concepts

| Concept | Meaning | Where in code |
|---|---|---|
| Quarter / Division / Sub-division | Filters used in the UI (e.g. Men's → Men's Active) | `models/pricing.py: PricingSubmission` |
| Sub number | e.g. `6650` — indicates channel: STORE only, DIRECT (.com) only, or BOTH | `models/pricing.py: Channel` |
| Fiscal calendar file + price file | Excel sheets the merchant team supplies to verify against uploaded DB data | `tools/excel_tools.py` |
| Submission | A verified weekly pricing package, one per sub/brand/week | `models/pricing.py: PricingSubmission` |
| Approval screen (STORE / DIRECT) | Two separate review queues | `agents/approval_agent.py` |
| Approved / Rejected / Pending folders | Physical file destinations after review | `tools/file_tools.py` |
| Reject email | Notification sent to merchant when a submission is rejected | `tools/email_tools.py` |
| Week color coding | Red = current week, pink = +1-2 wks, green = +3 wks, yellow = +4-5 wks | `models/pricing.py: week_status()` |

## Flow

1. **Upload job** (out of scope) lands rows in the pricing DB: subs,
   brands, groups, start/end dates.
2. **Submission Agent**
   - Pulls uploaded rows for a given fiscal week via `db/repository.py`.
   - Loads the merchant-supplied fiscal calendar + price Excel files via
     `tools/excel_tools.py`.
   - Compares price points row-by-row (division → sub-division → sub
     number → channel) against the DB rows.
   - If everything matches: marks the submission `SUBMITTED` and writes a
     JSON package to `submissions/pending/{week}/{sub}.json`
     (`tools/file_tools.py`).
   - If mismatches are found: flags them for human/agent review instead of
     auto-submitting (configurable — see `TODO` in
     `agents/submission_agent.py`).
3. **Approval Agent**
   - Watches `submissions/pending/{week}/` for the two channel queues
     (STORE vs DIRECT).
   - For each submission, applies approval rules (currently a
     LangChain/Bedrock reasoning step you can extend with real business
     rules) and decides `APPROVE`, `REJECT`, or leaves it `PENDING`.
   - `APPROVE` → moves file to `submissions/approved/{week}/`.
   - `REJECT` → moves file to `submissions/rejected/{week}/` **and** sends
     an email to the merchant via `tools/email_tools.py` explaining the
     issue.
   - `PENDING` → left in place for another pass / human escalation.
4. **Downstream inference job** (out of scope) reads from
   `submissions/approved/{week}/` per channel. `approval_agent.py` exposes
   a `notify_inference_job()` hook you can wire up to whatever trigger
   mechanism you use (SQS message, HTTP call, etc.)

## LangGraph state machine

```
        ┌────────────┐
        │   START     │
        └─────┬───────┘
              ▼
      ┌───────────────┐
      │ verify_submission │  (Submission Agent node)
      └───────┬───────────┘
        submitted / flagged
              ▼
      ┌───────────────┐
      │ review_approval    │  (Approval Agent node, loops per submission)
      └───────┬───────────┘
      approve/reject/pending
              ▼
        ┌────────────┐
        │    END      │
        └────────────┘
```

Defined in `src/graph/workflow.py` using `langgraph.graph.StateGraph`,
shared state defined in `src/graph/state.py`.

## Why LangGraph over plain LangChain

Your process has real branching + retry semantics (flagged submissions,
pending approvals that need another pass, reject-then-notify), which maps
naturally onto LangGraph's graph/state model rather than a single linear
LangChain chain. Each node can also be swapped for a human-in-the-loop step
later (e.g. keep approval as agent-drafted-recommendation + human sign-off
for the first few months) by adding an `interrupt` before the approval node.
