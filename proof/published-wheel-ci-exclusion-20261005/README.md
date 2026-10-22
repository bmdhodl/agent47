# The activation snapshot subtracts our own published-wheel CI

Artifact for `docs/guides/activation-snapshot-2026-10-05.json`, the snapshot this
change ships. Lineage: AG-29 annotated the publish days,
[proof/ag-31-off-publish-downloads](../ag-31-off-publish-downloads/README.md)
(#806) computed the off-publish-day and real-interpreter figures, and this step
subtracts our own CI from them. It carries no AG number of its own, so the
directory is named for the work.

Retrieved 2026-10-05T10:21:28Z. The PyPI series ends 2026-10-04. 2026-10-05 is
lag, not a zero day.

`.github/workflows/published-wheel.yml` installs the published wheel from PyPI on
an OS matrix. Every wheel-install job uses a real Python interpreter, so a job
that fetches the wheel adds one non-null row to `python_minor?mirrors=false`.
That is the exact series `pypi.off_publish_days.*.real_interpreter` reads. The
workflow moved to a daily `cron: "49 8 * * *"` and began firing 2026-10-03, so
from that date the figure grew by about four a day with no outside user involved.

The snapshot now names that exclusion and reports the figure twice. The workflow
itself is unchanged; it is a real release check and it is working.

```bash
python scripts/refresh_activation_snapshot.py --fetch-public --retrieved-at 2026-10-05T10:21:28Z --out docs/guides/activation-snapshot-2026-10-05.json
python scripts/activation_weekly_report.py docs/guides/activation-snapshot-2026-10-05.json
```

`report.json` is that classifier stdout.

## Our own runs inside the 45-day lookback

Read live from `actions/workflows/published-wheel.yml/runs`, then one
`actions/runs/<id>/jobs` read each. The lookback asks for the 30-day window plus
room for pypistats lag. Only one page of runs is read, so when that page fills up
before the lookback ends, the snapshot reports the day the inventory actually
starts, and a window that starts earlier gets `unavailable` rather than a partial
subtraction. A job counts only when it completed the step `Install the published
wheel and run the offline example`; the workflow's `release` job resolves the
version, installs nothing and is not counted.

| Run | Date (UTC) | Wheel-install jobs |
|---|---|---:|
| `36190628659` | 2026-09-25 | 4 |
| `37111363411` | 2026-10-03 | 4 |
| `37196396992` | 2026-10-04 | 4 |
| `37287563982` | 2026-10-05 | 4 |

The 2026-10-05 run is outside both reporting windows, because the series ends
2026-10-04. It is listed and not subtracted.

## The committed snapshot

Seven days, 2026-09-28 to 2026-10-04. No publish day falls in the window, so all
seven days count. 37 no-mirror events, 5.3 a day. 19 of them name a Python
interpreter, so the raw off-publish real-interpreter figure is **19 over 7 days,
2.7 a day**. Two of our runs land in the window with four jobs each, and both
days hold at least four real-interpreter rows, so all eight jobs come out and the
figure net of our own CI is **11 over 7 days, 1.6 a day**.

Thirty days, 2026-09-05 to 2026-10-04. Four publish days leave 26 days in the
sum: 188 no-mirror events, 7.2 a day. Raw real-interpreter: 36 events, 1.4 a day.
Three of our runs land on off-publish days in the window, 12 jobs, so net:
**24 events, 0.9 a day**. Four of those 26 days have no pypistats rows at all
(2026-09-05, 09-06, 09-09, 09-14), so both 30-day means are floors. The 7-day
window has no missing day.

`jobs_not_subtracted` is 0 in both windows. That field counts jobs the per-day cap
refused: no day's subtraction is allowed to exceed that day's real-interpreter
rows, so our CI can never eat another day's genuine downloads.

## The review's clean week, 2026-09-27 to 2026-10-03

This is the window the 2026-10-04 focus review called "the first time the honest
number moved up". The frozen feeds in this directory reproduce it:

```bash
python scripts/refresh_activation_snapshot.py \
  --pypi-json proof/published-wheel-ci-exclusion-20261005/pypi-overall-without-mirrors.json \
  --python-minor-json proof/published-wheel-ci-exclusion-20261005/pypi-python-minor-without-mirrors.json \
  --published-wheel-runs-json proof/published-wheel-ci-exclusion-20261005/published-wheel-runs.json \
  --published-wheel-runs-from 2026-09-25 \
  --retrieved-at 2026-10-04T00:00:00Z --out window.json
```

`--retrieved-at 2026-10-04` ends the series on 2026-10-03, which sets the window.
Write `window.json` to any scratch path.

The frozen run file holds our runs from 2026-09-25 onward, which is what
`--published-wheel-runs-from` declares. The 7-day window starts 2026-09-27, so it
nets out. The 30-day window starts earlier than the run file reaches, so its net
figure reads `unavailable` with that reason rather than a partial subtraction.
The 30-day net in the committed snapshot is live-only: these frozen feeds
reproduce the clean week, not the whole month.

32 no-mirror events over the seven days. 15 of them name a real interpreter, so
the raw figure is 2.1 a day. Run `37111363411` on 2026-10-03 contributed four of
those 15, so the figure **net of our own CI is 11 over 7 days, 1.6 a day**.

Like for like against the week before, 2026-09-21 to 2026-09-27, taken from
`docs/guides/activation-snapshot-2026-09-28.json`: raw 12 over 6 days, 2.0 a day.
That window holds run `36190628659` on 2026-09-25 with four jobs, and 2026-09-25
holds 8 real-interpreter rows, so the cap does not bind and its net is 8 over 6
days, **1.3 a day**.

Each of the two windows therefore contains exactly one four-job run, so our own
CI does not explain the move the review reported. Net rose from 1.3 to 1.6 a day.
What the exclusion does show is that the raw figure overstated both weeks by four
events, and that from 2026-10-03 the cron adds about four a day to every window
it touches: the committed 7-day window above carries 8 of its 19 raw events from
our own jobs.

The frozen feeds hold 2026-09-07 through 2026-10-03, so both download windows
compute even though only the 7-day one can be netted. 2026-09-04 to 2026-09-06
have no pypistats rows and stay in `missing_days`. The offline run uses the
historical release-date baseline rather than the live PyPI release metadata; the
two agree on every date in these windows, because the last release day on or
before 2026-10-04 is 2026-09-24.

The committed snapshot's own figures come from live reads and are not reproducible
from this directory. Re-running the documented `--fetch-public` command later will
read a later window.

## What the net figure is not

The net figure is still an upper bound. Other CI, reinstalls and mirrors-excluded
tooling also use real interpreters, and an interpreter does not identify a person.
A null interpreter almost always means tooling rather than a person. Neither
figure is a count of people.

One job is not provably one download either. A cached or failed install can run
without a fresh PyPI fetch, which is why the subtraction is capped per day and
the surplus is reported rather than guessed.

No row is deleted. A run that fell on a publish day is listed and not subtracted,
because that whole day is already outside the off-publish sum. If the Actions API
is unavailable at run time the net field reads `unavailable` with the reason, and
the raw figure is never presented as the net one.

Repository visits, site events, real-workflow activation and repeat use stay
unknown.
