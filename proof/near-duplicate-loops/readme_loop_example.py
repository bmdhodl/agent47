from agentguard import LoopDetected, LoopGuard

loop = LoopGuard(normalize=True, max_no_progress=3)

for pattern in ["retry_count", "retryCount", "retries"]:
    loop.check("grep", {"pattern": pattern})
    matches = []  # Put your search here. This one finds nothing.
    try:
        loop.record_result("grep", matches, tool_args={"pattern": pattern})
    except LoopDetected as stop:
        print(stop)
