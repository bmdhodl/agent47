# MCP1 JWT dependency repair

GHSA-42vr-xj54-vc7v was reproduced with PyJWT2.14.0 in both unsigned-decode and JWKS key-lookup paths, before any network. The fixed2.15.1 dependency passes both cases. Its declared minimum2.15.0 excludes vulnerable releases while keeping MCP>=1.23,<2. Genuine Python3.11 compilation preserves the other28 versions/hash sets and adds the explicitly conditional Windows pywin32 dependency; Linux skips its marker. Full Windows MCP tests, stdio, SDK source, lint/security and installed Python3.10 product smoke results are retained. No SDK runtime dependency, new API, authentication-policy change or release.

`python proof/mcp-pyjwt-security-20261004/verify.py` checks retained artifact integrity, required command/source inventories, actual recorded exit expectations and frozen source snapshots. Exact-head hosted CI is a separate gate.
