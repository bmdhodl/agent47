Platform: Linux, Python 3.11.15, base af0724d

1) Documented steps applied verbatim in a scratch worktree (fixture appended to usage_payloads.py, test added to test_precision_cost.py):
$ python -m pytest sdk/tests/test_precision_cost.py -q
26 passed (25 existing + the CONTRIBUTING example)

Re-run after the Codex P2 fix (snippet now asserts token buckets and table cost): same result, 26 passed.

2) Doc regression in this PR:
$ python -m pytest sdk/tests/test_documentation.py -q
============================== 20 passed in 0.07s ==============================
Negative checks: changing the documented source to SOURCE_PROVIDER, or the input token count to 301, makes test_contributing_fixture_example_runs fail (1 failed).
