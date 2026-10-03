# Final review proof for issue #820

Windows, 2026-10-03. Fixes OverflowError from unrepresentable JSON timing.
Before: 6 failures/35 passes. Final Py3.9.6 and 3.13.2: 41 passes each,
zero skips/warnings. Oversized-fixture CLI exit 1 becomes 0/400 ms;
sequential calls remain 446.6 ms. Full SDK: 1479 passed, 3 optional skips,
92.38% coverage. Configured checks and 11 MCP tests pass.

Receipts verify all 49 source/installed files, metadata, CRC and zero mandatory
dependencies. Isolated Python, no checkout conftest, optional providers or
credentials. Py3.9 installer digest is absent and flagged. Raw logs are retained
in gzip; public JSON is compacted without changing parsed values.

Final wheel: 3671cd33312a4c8dcffec8db8a4459a175ebe5cc9b16c0074c23d1c1aa3ba009
Prior wheel: f864b1e9b79ac2fb55a031275d6d49cda2eb768795266c0d3c811f83e955ae8f

Manifest: LF text/exact gzip bytes. Showwork checks saved artifacts.
No public API, dependency, workflow or release change; existing fallback stays.
