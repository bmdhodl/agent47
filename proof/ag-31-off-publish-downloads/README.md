# AG-31 off-publish-day downloads

Retrieved 2026-09-28T08:16:02Z. The PyPI series ends 2026-09-27. 2026-09-28 is
lag, not a zero day.

```bash
python scripts/refresh_activation_snapshot.py --fetch-public --retrieved-at 2026-09-28T08:16:02Z --out docs/guides/activation-snapshot-2026-09-28.json
python scripts/activation_weekly_report.py docs/guides/activation-snapshot-2026-09-28.json
```

`report.json` is that classifier stdout.

AG-29 annotated the publish days and then stopped, so
`pypi_events_outside_publish_burst` read `not computed`. It is a number now, in
the snapshot and in the classifier, for the 7-day and the 30-day window.

Seven days, 2026-09-21 to 2026-09-27. 142 package events. The 1.4.0 publish day
2026-09-24 holds 86 of them, so **56 events fall on the other six days, 9.3 a
day**. 28 of the 142 name a Python interpreter; 16 of those land on the publish
day, so **12 real-interpreter events fall on the other six days, 2.0 a day**.

Thirty days, 2026-08-29 to 2026-09-27. 567 events, four publish days removed
from the sum, leaving 155 across 26 days, 6.0 a day. 17 of those name an
interpreter, 0.7 a day.

The publish dates are read from `exclusions.publish_dates` and listed beside
every figure. Release-day rows stay in the data, annotated, exactly as AG-29
left them. Nothing is deleted.

A null interpreter almost always means tooling rather than a person, and a real
interpreter still does not prove a distinct person. Neither figure is a count of
people. Repository visits, site events, real-workflow activation and repeat use
stay unknown.
