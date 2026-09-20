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
- `--omit version` drops the version field and still prints `Nothing was sent.`
- Weekly classifier reports `install_intent_proven: 0` for the 2026-09-18
  snapshot because both `install_intent` events targeted the landing page.
- `landing_page_never_counts_as_install` stays `true` even when a mixed snapshot
  has proven PyPI/copy targets.

## Viewport proof

`browser-checks.json`: overflowX 0 at 375/768/1440 on `index.html` and
`activation.html`. Caption copy: "Viewing this page is not an install."

No SDK telemetry. No new public API. No version bump.
