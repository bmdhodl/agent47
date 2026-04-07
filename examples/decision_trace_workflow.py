"""Minimal decision-trace workflow example.

Run:
    python examples/decision_trace_workflow.py
    agentguard report decision_trace_workflow.jsonl
"""
from agentguard import JsonlFileSink, Tracer, decision_flow


def main() -> None:
    tracer = Tracer(
        sink=JsonlFileSink("decision_trace_workflow.jsonl"),
        service="decision-trace-example",
        watermark=False,
    )

    with tracer.trace("agent.run", data={"workflow": "deploy-approval"}) as run:
        with decision_flow(
            run,
            workflow_id="deploy-approval",
            object_type="deployment",
            object_id="deploy-042",
            actor_type="agent",
            actor_id="release-bot",
            span_name="deploy.review",
        ) as decision:
            decision.proposed(
                {
                    "action": "deploy",
                    "environment": "staging",
                    "version": "2026.04.06",
                },
                reason="Tests and canary checks passed",
                comment="Ready for human review",
            )
            decision.edited(
                {
                    "action": "deploy",
                    "environment": "production",
                    "version": "2026.04.06",
                },
                actor_type="human",
                actor_id="pat",
                reason="Promote directly to production",
                comment="Customer asked for immediate rollout",
            )
            decision.approved(
                actor_type="human",
                actor_id="pat",
                comment="Approved after environment change",
            )
            decision.bound(
                actor_type="system",
                actor_id="deploy-api",
                binding_state="applied",
                outcome="success",
                comment="Deployment API accepted the release request",
            )

    print("Wrote decision_trace_workflow.jsonl")


if __name__ == "__main__":
    main()
