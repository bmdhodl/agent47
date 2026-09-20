# AG-02 activation evidence proof

Issue: https://github.com/bmdhodl/agent47/issues/731
Parent: https://github.com/bmdhodl/agent47/issues/729

## Commands

```bash
PYTHONPATH=sdk python -m pytest sdk/tests/test_activation_evidence.py sdk/tests/test_demo.py -q
python scripts/activation_weekly_report.py docs/guides/activation-baseline-2026-09-18.json
make check
```

## Expected

- Default `agentguard demo` tells the user how to inspect or decline feedback.
- `agentguard demo --feedback` prints version, adapter, result, reproduction and
  `Nothing was sent.`
- Weekly classifier reports `install_intent_proven: 0` for the 2026-09-18
  snapshot because both `install_intent` events targeted the landing page.

No SDK telemetry. No new public API. No version bump.
