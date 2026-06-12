"""Run the AgentGuard CLI with ``python -m agentguard``.

This mirrors the ``agentguard`` console script so the tool works even when the
script is not on PATH, without forcing users to remember ``-m agentguard.cli``.
"""

from agentguard.cli import main

if __name__ == "__main__":  # pragma: no cover
    main()
