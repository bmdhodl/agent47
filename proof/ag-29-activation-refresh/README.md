# AG-29 activation refresh

Retrieved 2026-09-25T01:40:00Z. PyPI series ends 2026-09-24. 2026-09-25 is lag, not a zero day.

```bash
python scripts/refresh_activation_snapshot.py --fetch-public --retrieved-at 2026-09-25T01:40:00Z --out docs/guides/activation-snapshot-2026-09-25.json
python scripts/activation_weekly_report.py docs/guides/activation-snapshot-2026-09-25.json
```

`report.json` is that classifier stdout. 7-day downloads are 255 package events. 30-day downloads are 537. Release days are annotated and not removed. Repository visits, site events, real-workflow activation, and repeat use are unknown. No public demo-feedback issues were found. That is not a count of outside users.
