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

## Directory authority

The opt-in `directory` case uses the same signing and process equipment. Its
fixed policy denies data reads and file writes, permits reads through the native
read and read-write extension predicates, and permits writes through the
read-write predicate. It compares `com.apple.app-sandbox.read-write` issuance
for an owned directory with no consumption, omitted predicates, a different
directory and `com.apple.app-sandbox.read` issuance. Developer ID signing and its
timestamp service justify opt-in membership, as with `feasibility`.

Each boundary has a separate existing file and absent child name. The issuer
records absence before issuance, the host before releasing the worker, and the
worker immediately before exclusive creation. Existing-file open, explicit
truncation, write, descriptor sizes and close are separately observed. The host
reads effects after each completed boundary, after release and after worker
exit; Python independently reads back the final filesystem state. Before-policy
operations establish ordinary permissions. The positive consumed arrangement
must modify the existing file and create the child; the four controls must not.
Fresh post-release operations and native query answers have no required pattern.
An absent child has no invented query prediction.

`directory_check.py` verifies these observations independently of production
actions and classifiers. Constructed controls reject missing absence, lifecycle,
identity, operation and persistence evidence. It accepts unavailable or unchanged
queries and failed release results without translating them into access claims.
The case retains exact source, signing, native and external observations under
the same evidence ownership as `feasibility`.
