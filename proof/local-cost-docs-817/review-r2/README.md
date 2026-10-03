# Review follow-up

Initial proof remains historical. Claude's unnecessary post-exception list
assertion was removed; `pytest.raises(BudgetExceeded)` still checks refusal.
The documented example and SDK source are unchanged. The revised test passes
both cases again against all three previously clean installed profiles, with
zero skips/errors/warnings. Each package file and metadata still equals its
recorded wheel; test and guide hashes bind these reruns to the revised files.
These runs recheck existing isolated installs, not new installations.

The parent manifest was corrected to hash Git repository blob bytes after
newline normalization. No artifact data changed. The preserved historical
Ollama README is explicitly claimed for archive normalization coverage.
Showwork remains saved-artifact verification; no runtime API or publication change.
Sign-off: OpenAI | GPT-6 | auto.
