# AG-05 stream reservation

Store-backed OpenAI streams reserve before send. Two spawned processes share
one `JsonFileStateStore` and `max_calls=1`. Exactly one mock stream runs.
In-memory streams still consume after the fact. A token or dollar cap with
no usage, an early stop, or a partial usage chunk keeps the hold. An
exception while entering the stream context stays unresolved. A manager
that is never entered stays reserved. This is not an invoice cap.

Windows was not executed. Spawn is the start method; Linux was.

```bash
python examples/enforcement_boundary/reserved_stream_dispatch.py
```

```json
{"dispatched": 1, "results": ["dispatched", "blocked"], "blocked": 1, "settled_calls": 1, "reserved_calls": 0, "unresolved_calls": 0, "workers": 2, "start_method": "spawn", "exit_codes": [0, 0], "network_calls": 0, "path": "openai-sync-stream-statestore", "fixed": true}
```
