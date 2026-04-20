# Release Content Quoting Proof

This proof covers the `release-content.yml` fix for issue `#364`.

The dry run feeds announcement text containing Markdown backticks and shell
command-substitution syntax into the same `printf`-based body construction used
by the workflow. The expected result is that the body preserves those characters
as literal text and does not create marker files.

