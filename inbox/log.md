# Inbox Log
**Format:** Newest first. One entry per merged PR or meaningful shipped session.

---

## 2026-04-02 | SDK Builder | Local smoke proof + hosted handoff verified

### What shipped
- `examples/coding_agent_smoke.py` proved healthy, loop, and retry traces locally.
- The hosted replay of that exact smoke payload was verified after the dashboard auth-path fix.
- SDK repo memory now uses `inbox/log.md` as the durable cofounder handoff.

### Decisions made
- SDK stays the free local wedge for coding-agent safety.
- Dashboard picks up only after local proof, for retained history, alerts, and remote controls.

### Blockers
- Glama listing is still blocked; pause there and use other distribution paths first.
