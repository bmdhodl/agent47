# Claims audit - session agent47-otel-r2-20260815

**Verdict: GREEN**  (2/3 verified)

- .. **canonical OTel r2 report records follow-up verification** (`None`, RED)
    - retracted: Vault report is outside the repository root; its existence will be verified through the Vault claims layer instead.
- OK **instrument regression covers absent usage without llm.result or guessed cost** (`file_contains`, RED)
    - /test_missing_usage_does_not_emit_llm_result_or_cost/ found in sdk/tests/test_instrument.py
- OK **OTel bridge regression preserves provider model and normalized usage** (`file_contains`, RED)
    - /test_llm_result_preserves_provider_model_and_usage/ found in sdk/tests/test_otel_sink.py
