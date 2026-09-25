# AG-07 compatibility matrix proof

Linux. Each run is a fresh Python 3.12 venv with `pip install --require-hashes -r .github/requirements/compat-<lock>.txt`, then `PYTHONPATH=sdk AGENTGUARD_REQUIRE_REAL_DEPS=1 python -m pytest sdk/tests/ -q`, the same as the CI `compat` job.

## compat-floor
```text
anthropic==0.34.0
langchain-core==1.6.3
langgraph==1.2.11
langgraph-checkpoint==4.2.0
langgraph-sdk==0.4.4
openai==1.40.0
opentelemetry-api==1.44.0
opentelemetry-sdk==1.44.0
============================ 1205 passed in 32.34s =============================
```

## compat-latest
```text
anthropic==1.8.0
langchain-core==1.6.5
langgraph==1.2.12
langgraph-checkpoint==4.2.0
langgraph-sdk==0.4.5
openai==3.19.2
opentelemetry-api==1.45.0
opentelemetry-sdk==1.45.0
============================ 1205 passed in 34.75s =============================
```

## Negative checks

- If `_patch_openai_instance` returns early (a silent no-op), both OpenAI real-dispatch tests fail: 2 failed.
- With `AGENTGUARD_REQUIRE_REAL_DEPS=1` and no packages installed, all 6 real-dispatch tests fail instead of skipping.
- Changing `langchain-core==1.6.3` in `compat-floor.in` fails `test_compat_floor_lock_matches_sdk_extra_floors`.
- anthropic 1.8.0 rejects `httpx.Client` (it moved to `httpx2`). The test builds its mock transport from the SDK's own `DefaultHttpxClient`.
