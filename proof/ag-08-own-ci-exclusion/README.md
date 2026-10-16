# AG-08 input: subtract our own published-wheel installs

Retrieved 2026-10-16T19:22:43Z on Windows 11, Python 3.13.2. The PyPI series
ends 2026-10-15. 2026-10-16 is lag, not a zero day.

## Problem

`.github/workflows/published-wheel.yml` installs the published wheel from PyPI
on a four-job matrix. It has run on a daily cron since 2026-10-03. Each job is
one `pip install` with a real interpreter, so each job adds one row to
`python_minor?mirrors=false` with a non-null category. That is the series behind
`pypi.off_publish_days.*.real_interpreter`, the figure AG-08 (#737) reads.

## Change

The refresh reads every `published-wheel.yml` run in the 30-day window from the
GitHub Actions API: run id, UTC date, event and the count of jobs whose step
`Install the published wheel and run the offline example` concluded success.
Re-run attempts count. The snapshot writes them under
`exclusions.published_wheel_ci`, next to `publish_dates`, `mirrors` and
`simulated_reports`. Each `real_interpreter` block keeps its raw figures and
adds `net_of_own_ci`. If the Actions API fails, `net_of_own_ci` reads
`unavailable` with the reason. It never falls back to raw. No rows are deleted.

## Commands and exit codes

```bash
python scripts/refresh_activation_snapshot.py --fetch-public --retrieved-at 2026-10-16T19:22:43Z --out docs/guides/activation-snapshot-2026-10-16.json   # exit 0
python scripts/activation_weekly_report.py docs/guides/activation-snapshot-2026-10-16.json > proof/ag-08-own-ci-exclusion/report.json                  # exit 0
```

The card's week, replayed offline from the same live reads. `week-2026-09-27/`
holds the PyPI rows cut to 2026-09-04..2026-10-03, the PyPI upload times and the
Actions API run records for that window:

```bash
W=proof/ag-08-own-ci-exclusion/week-2026-09-27
python scripts/refresh_activation_snapshot.py --pypi-json $W/pypi-overall.json --python-minor-json $W/python-minor.json --pypi-releases-json $W/pypi-releases.json --published-wheel-runs-json $W/published-wheel-runs.json --retrieved-at 2026-10-16T19:22:43Z --out $W/snapshot.json   # exit 0
python scripts/activation_weekly_report.py $W/snapshot.json > $W/report.json   # exit 0
```

## Figures

| Window | Off-publish days | Raw real interpreter | Own CI jobs | Net of own CI |
|---|---:|---:|---:|---:|
| 2026-09-27..2026-10-03 | 7 | 15 (2.1/day) | 4 | **11 (1.6/day)** |
| 2026-10-09..2026-10-15 | 7 | 31 (4.4/day) | 28 | 3 (0.4/day) |
| 2026-09-16..2026-10-15 | 27 | 79 (2.9/day) | 52 | 27 (1.0/day) |

The 30-day window leaves out publish days 2026-09-18, 2026-09-24 and
2026-10-06. The runs on 2026-10-06 fall on a publish day, so they are not
subtracted again. No day went below zero.

The net figure is still an upper bound. Other CI, reinstalls and tooling that
reports an interpreter still count, and an interpreter does not identify a
person.

## Test proof

`red-before-change.txt` is the new tests run before the script change: 8 failed.
The core assertion failed with `KeyError: 'net_of_own_ci'`. After the change:

- `python -m pytest sdk/tests/test_activation_evidence.py -q`: 40 passed.
- `python -m pytest sdk/tests/ -q --cov=agentguard --cov-fail-under=80`:
  1577 passed, 114 skipped, coverage 91.55%, exit 0.

Regenerated after review: no. Rerun both command blocks if the script changes.
