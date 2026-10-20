# MCP runtime account guidance (#886)

The missing-key error now states that hosted accounts are closed to new users
and points to `pip install agentguard47`. The `query_traces` description gives
the same limit and local SDK path. Existing-key authentication and request
handling are unchanged.

## Reproduction and validation

- Before the runtime strings changed, `npm --prefix mcp-server test` reported
  10 passed / 2 failed. Both `REGRESSION:` tests rejected the old copy.
- After the change, the same command builds TypeScript and passes all 12 tests.
  This includes the existing mocked bearer-authentication test.
- Running `node mcp-server/dist/index.js` without an API key exits 1 and prints:

  ```text
  AGENTGUARD_API_KEY environment variable is required for an existing hosted account. New hosted accounts are closed. For the local SDK, run: pip install agentguard47.
  ```

- Full SDK suite: 1687 passed / 3 skipped, 92.72% coverage (80% required).
  The optional Agents package is absent. The test subprocess used a clean
  AgentGuard environment; host configuration is a separate issue (#887).
- Structural tests: 9 passed. Native Ruff, Bandit, CI-tool pins,
  review-readiness, release guard, PyPI README sync and `git diff --check` pass.
- Two separate local reviewer sessions: correctness/security PASS;
  house-style PASS. Both recorded a verdict before reading the work plan and
  retained it afterward. These reviews do not grant merge approval.

One initial full-suite attempt failed on a missing scratch-directory parent.
The corrected run created that parent and used an absolute temporary path.
The SDK result above is from the fresh successful run.

The initial showwork close refused an undeclared second source file. That
attempt is retained as blocked. The completion receipt is a separate final
verification session that declares its acceptance checks before any claims.

## Scope and limits

No SDK production, authentication, dependency, version or publication change.
No rendered app/browser surface changed; this package has no `test:e2e`
command. The existing README and Registry metadata already carry this limit.
Roadmap and architecture were reviewed; no structural update is needed.
Final-head CI and independent merge approval remain separate gates. This proof
does not claim npm or MCP Registry publication.

Sign-off: OpenAI | gpt-6.1-sol | xhigh.
