"""LangGraph workflow: verify_submission -> review_approval, per fiscal week."""
from __future__ import annotations

from langgraph.graph import END, StateGraph

from src.agents import approval_agent, submission_agent
from src.config import settings
from src.db.repository import PricingRepository
from src.graph.state import CycleState
from src.models.pricing import Channel, SubmissionStatus


def verify_submission_node(state: CycleState) -> CycleState:
    repo = PricingRepository(settings.db_connection_string)
    line_items = repo.get_uploaded_line_items(state["fiscal_week"])
    submissions = repo.group_into_submissions(state["fiscal_week"], state["quarter"], line_items)

    verified, flagged = [], []
    for submission in submissions:
        result = submission_agent.verify_and_submit(submission)
        (flagged if result.status == SubmissionStatus.FLAGGED else verified).append(result)

    state["submissions"] = verified
    state["flagged"] = flagged
    return state


def review_approval_node(state: CycleState) -> CycleState:
    # TODO: replace with your real merchant contact lookup
    merchant_email_lookup = lambda sub_number: f"merchant-{sub_number}@example.com"

    approved, rejected, pending = [], [], []
    for channel in (Channel.STORE, Channel.DIRECT, Channel.BOTH):
        reviewed = approval_agent.review_pending_queue(
            state["fiscal_week"], channel, merchant_email_lookup
        )
        for submission in reviewed:
            if submission.status == SubmissionStatus.APPROVED:
                approved.append(submission)
            elif submission.status == SubmissionStatus.REJECTED:
                rejected.append(submission)
            else:
                pending.append(submission)

    state["approved"] = approved
    state["rejected"] = rejected
    state["pending"] = pending
    return state


def build_graph():
    graph = StateGraph(CycleState)
    graph.add_node("verify_submission", verify_submission_node)
    graph.add_node("review_approval", review_approval_node)

    graph.set_entry_point("verify_submission")
    graph.add_edge("verify_submission", "review_approval")
    graph.add_edge("review_approval", END)

    return graph.compile()


def run_cycle(fiscal_week: str, quarter: str) -> CycleState:
    app = build_graph()
    return app.invoke({"fiscal_week": fiscal_week, "quarter": quarter})
