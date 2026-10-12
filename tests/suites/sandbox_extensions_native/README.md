# sandbox_extensions_native

Opt-in native feasibility equipment for file sandbox extensions. The
`feasibility` case requires a Developer ID Application identity and the macOS C
toolchain. It does not launch PW, install a service or alter the distribution.
Run outside an automation sandbox, with `IDENTITY` or `PW_BYOXPC_IDENTITY` set:

```sh
PW_TEST_OUT_DIR=tests/out/runs/extensions-native tests/run.sh --suite sandbox_extensions_native
```

The [fixture](../../fixtures/sandbox_extensions/README.md) execs an ordinary
issuer and a once-sandboxed worker. The checker creates owned regular files and
a symlink, verifies their contents and metadata independently, and checks fresh
open/read/close observations at the native boundaries. This file discipline is
not a production admission rule.

## Controls

| Scenario | Intervention and required observation |
| --- | --- |
| `lifecycle` | Issue, consume into a real handle, call release; retain queries and fresh access observations. |
| `issuer_exit` | Reap the issuer before releasing the worker; the real lifecycle still runs. |
| `no_consume` | Deliver the token but omit consumption; fresh access remains denied. |
| `no_release` | Consume but omit release; later fresh access retrieves known contents. |
| `no_predicate` | Remove only the extension predicate; retain native calls and denied fresh access. |
| `different_target` | Issue for the other controlled file; the attempted target remains denied. |
| `issue_failure` | Replace the prepared native path argument with an empty path; require a null issuance result with no fabricated consume/release. |
| `rejected_token` | Replace transient delivery with an invalid token; require failed consumption and no release. |
| `retained_fd` | Keep the post-consume descriptor open; independently report its read after release beside a fresh open. |

Each scenario runs with and without allocation instrumentation in fresh
processes. Positive malloc/free and available VM logger controls must work on
both sides of application. Query changes, query availability and access after
release are observations, not an expected agreement or revocation pattern.
Constructed checker controls reject missing handles, results, content, identity,
boundaries, cleanup and confinement, while accepting unchanged/unavailable
queries and a failed release result.

## Evidence

The case artifact directory retains compiler and signing commands, signature
and entitlement read-backs, OS/SDK/compiler facts, source snapshots and hashes,
controlled target metadata and contents, per-experiment commands and raw reports,
checker-control results and the summary. It never retains extension tokens.
The native supervisor owns its children and reports their wait results; the
outer test deadline kills the experiment process group if necessary. Such a
deadline is a harness failure, not a native sandbox observation.

These controls establish native feasibility under the recorded environment.
They do not establish production phase ordering, XPC transport, BYOXPC signing,
public admission or product token confinement.
