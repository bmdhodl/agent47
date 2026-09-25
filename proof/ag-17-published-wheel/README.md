# AG-17 published-wheel matrix

Local run (Linux, Python 3.11.15, base 07d62be):

```text
$ python scripts/verify_release_example.py --tag v1.4.0 --wheel-only
## Published AgentGuard v1.4.0: offline example passed on Linux, Python 3.11.15

Installed the exact PyPI wheel in a fresh environment. Budget, loop and retry stop events appeared; the report command completed. This is a simulated example, not proof of customer adoption or savings.
exit=0
```

Demo and report output is ASCII-only, so Windows cp1252 pipes cannot fail on encoding.

Windows and macOS were not run from this environment. After merge, dispatch
`published-wheel.yml` with `tag=v1.4.0` and record the run URL here.
