# PR review proof, 2026-10-02

`reviewed-prs.json` preserves GitHub API readbacks; `sdk-tests.txt` is the unedited final SDK test output. Tests ran on the SDK source after the activation review fixes; the subsequent scanner merge changed workflow files only.

## GitHub merge semantics

GitHub reports PR #790 as MERGED, with `mergeCommit.oid` `4872f834251178b6dc2998e25b1eceb4546d076d`. That is the real two-parent merge commit incorporating #790 into the paired #788 branch, whose head was therefore the same commit. Its second parent is #790's reviewed head `e4b4b37ab506c5ffacb02a4332e422da68b66e27`. PR #788 subsequently landed through main merge `6fdd55f7948bc2ac85538a5cd4cca9ded5601d29`. The raw API value is intentionally retained.

Reproduction: `gh pr view 790 --repo bmdhodl/agent47 --json state,headRefOid,mergeCommit,mergedAt` and `gh api repos/bmdhodl/agent47/git/commits/4872f834251178b6dc2998e25b1eceb4546d076d`. Both exited 0 on Windows after review.

## Windows checkout paths

The logical checkout under the user's GitHub directory resolves through a Windows junction to `E:/C-Offload/github/agent47-review-20261002`. Python's `os.path.realpath()` verified this mapping. Pytest reports the logical root while some module warnings use the physical path. The raw output was preserved without normalizing or editing either path.

## Test trace retention and receipt repair

`test-generated-traces.jsonl` is the ignored root trace produced by the mocked SDK dispatch tests, retained byte-for-byte as dated local-test evidence. It is not a real provider or broker transaction. The source file was moved into this proof folder after the review raised a valid concern about an indirect artifact declaration. The trace JSON lines and SHA-256 preservation were checked with Python on Windows, exit 0; the final showwork acceptance directly checks `path_moved` from `traces.jsonl` to this dated file. Historical refused events remain append-only. The earlier indirect claim was retracted and replaced with this direct check.

These receipts certify artifacts; executed tests and linked hosted Actions provide the behavior evidence. No package release was performed.
