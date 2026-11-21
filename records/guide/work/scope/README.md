# Basis and leads for the scope findings

This directory supports the further instance under scope finding 1 and
findings 2–8. The application studies for findings 3 and 7 are in
`records/guide/GUIDE-STUDIES.md`. The question about PW's path diagnostics in
finding 3 and the other scope findings are in
`records/guide/REQUIREMENTS-AND-EXPECTATIONS.md`. The layout follows the trust
account one level up.

## Conditions

- Written on 2026-11-20 against `main` at `f8d78885`. Six explorers (one Opus,
  five Sonnet) each started from one question someone might ask about their
  own app. They ran the app, `sandbox-exec` and small C helpers they wrote. The
  main session checked the replies and outputs each finding relies on, and
  reran the checks marked as such below.
- App: `dist/PolicyWitness.app` from `e7937ecc` (build 1634, contract
  `development:089e36a6…c00d55`) on macOS 26.7.1 (25G241), with the built-in
  runner. No registered test case ran.
- The same availability notes apply as for the trust account:
  - The copies here are the retained form.
  - Absolute paths inside refer to a session scratch directory.
  - Compiled helper binaries and target files were not kept. Each C source
    is here, and every setup is described below.
- Three settings profiles name `~/Library/Preferences` because that is the
  path they test. No run wrote there.

## Basis by finding

### 1, further instance. Descriptor kept across release

- `evidence/extension-class/held.c` is a native control in one process. It
  issues a read extension, applies the policy with `sandbox_init`, consumes the
  token, opens and reads the file, releases the token, then reads again.
- Explorer's output:
  - Before consumption, a fresh open fails with errno 1.
  - After consumption, both the fresh open and the held descriptor read 20
    bytes.
  - After release, a fresh open fails with errno 1, but a read through the held
    descriptor still returns 20 bytes.
- PW's `base` run (finding 8) shows only the fresh-open half: a read after
  release is denied.
- This was not rerun in the main session.

### 2. Absent names

- `evidence/policy-comparison/`: `orig.sb` denies reads in a directory `D`,
  and `hole.sb` adds an allow for `D/hole`. The target tree `tgt/` (with
  `d/a`, `d/b`, `d/sub/c`, `o`, `link -> d` and `d/la -> a`) was not
  retained.
- The wrapper (`bin/wrap.sh`, `bin/chk.c`, `bin/try.c`) holds `/bin/sleep`
  under each profile, queries it, then opens from a fresh process.
  `hole_absent_wrap.txt` and `hole_present_wrap.txt` hold its output, with
  `hole_absent_pw.txt` and `hole_present_pw.txt` the PW equivalents.
- PW runs (checked):
  - With `hole` absent, `pw/orig_holeabs` and `pw/hole_holeabs` both give
    `prediction_unavailable` and ENOENT.
  - With `hole` present, `orig_holepres` gives `deny` with EPERM, and
    `hole_holepres` gives `allow` with `ok`.
- Absent-path query (rerun in the main session with `bin/chk2.c`): an existing
  file gave `rc 0`; an absent name and a name in a missing directory gave
  `rc 1, errno 0`. That held for an unsandboxed `/bin/sleep` and for one under
  `(allow default)`.
- Explorer only:
  - The `SANDBOX_CHECK_CANONICAL` and `NOFOLLOW` flags did not change that
    result, and neither did a `file-write-create` query.
  - The `vt.sb` / `vs.sb` pair shows a `vnode-type` rule tested differently by
    a file and by a directory witness.
  - The `cA.sb` / `cB.sb` pair shows a create rule observed only by the create.
- This supports the planner's exclusion of absent paths. The PAWL maintainer
  reading called that premise untested. See matter 1.

### 3. Links in the app's spelling

- `pw/dorig` applies `(deny default)` with `file-read*` allowed in `D`, and
  `pw/drewr` allows only `D/a` (checked).
- In `dorig`, the `/tmp` spellings of `d/a` and `d/b` and the paths through
  `link/` are predicted `allow` and fail with EPERM. The read through `d/la`
  succeeds. In `drewr`, the `d/la` read also fails.
- No comparison carries a limitation.
- Wrapper rows matching these runs are in `wrap_wdorig.txt` and
  `wrap_wdrewr.txt`; their startup rules are in `wdorig.sb` and `wdrewr.sb`.
- Explorer only:
  - `wdorig_tmpmeta.sb` (adds `file-read-metadata` on `/tmp`) lets the `/tmp`
    read succeed.
  - `wdrewr_lameta.sb` does the same for `la`.
  - The `psys_a.sb` / `psys_b.sb` runs add `(import "system.sb")`, and the
    `/tmp` read then succeeds. Their PW replies were not retained; the
    wrapper output is `wrap_sys_*.txt`.
- `/System/Library/Sandbox/Profiles/system.sb`, around lines 83–88, allows
  `file-read-metadata file-test-existence` on `/etc`, `/tmp`, `/var` and
  `/private/etc/localtime` (checked).

### 4. Compiled bytes

- `bin/compile.c` calls the private `sandbox_compile_string` and hashes the
  result. The explorer reports:
  - `orig.sb`, `orig_ws.sb`, `orig_slash.sb`, `orig_regex.sb`,
    `orig_redund.sb` and `orig_redund2.sb` all compile to 644 bytes,
    `30495e47…`;
  - `two1` equals `two2`, and `lit2a` equals `lit2b`;
  - `rewr`, `rewr_tmp` and `hole` each differ.
- The explorer's opt-in receipts for `orig` and `orig_regex` both reported
  644 bytes and `bytecode_sha256` `30495e473a26dc6a…`. The receipts were not
  retained, because the guide treats them as sensitive.
- Process identity (checked): `pw/sigid` denies reads in `D` for signing
  identifier `com.apple.sleep`, and PW's worker read the file. `pw/sigid_pw`
  names `pw-probe-runner`, and the worker's read failed with EPERM.

### 5. Helper startup

- `evidence/helper-startup/helper.c` opens a compiled-in config path, prints
  it, and exits 2 or 3 on failure. The binary was built from it with
  `/usr/bin/cc`; neither the binary nor the config file was kept.
- Runs (checked):

  | Run | Result |
  | --- | --- |
  | `e-readfresh` | `read_fresh` allowed only the config read; `ok` |
  | `o2-devnull-cfg` | exec, fork, `/dev/null` and config read allowed; child signal 6 |
  | `p1-minimal` | adds two `sysctl-read` names and `(allow file-read-data (literal "/"))`; exit 0, `mode=fast`. The explorer found the `sysctl-read` rules unnecessary in a run that was not retained |
  | `p2-minimal-nocfg` | `p1` without the config rule; exit 2, stderr `open failed: Operation not permitted` |
  | `p4-minimal-noroot` | `p1` without `/`; signal 6 |
  | `b-exec-base` | `(deny default)` with `exec_baseline` only; exit 0, `mode=fast` |

- Explorer only: under `sandbox-exec`, exec of the helper plus reads of the
  config and `/` was enough, with no fork or `/dev/null` rule. The unified
  log listed startup denials for `sysctl-read` and `file-read-data /`.
- The shell-script variant (`helper.sh`) also needed exec of `/bin/sh`, and
  its full rule set was not found. It is not part of the finding.

### 6. Name resolution and network rules

- `evidence/name-resolution/h.c` connects, resolves and connects, or binds and
  listens, printing each call's return and errno. `lis.py` is the loopback
  listener on port 47811.
- PW runs (checked), all `(deny default)` with `exec_baseline` and the
  outbound rule `(remote ip "localhost:47811")`:

  | Run | Result |
  | --- | --- |
  | `b2` | connects to `127.0.0.1` |
  | `b4` | resolves `localhost` and connects over IPv6 |
  | `b5` | adds `(deny file-read* (subpath "/private/etc"))`; `getaddrinfo` returns 8 and nothing connects |
  | `b7` | `bind` fails with EPERM |
  | `b8` | adds `network-bind`; `listen` fails with EPERM |
  | `b9` | adds `network-inbound`; `listen` succeeds |
  | `c1` | allowed port with no listener; `ECONNREFUSED` |

- Explorer only, under `sandbox-exec`:
  - A literal-address connect succeeded with the `/private/etc` deny in
    place.
  - A rule may name only `*` or `localhost` as host.
  - A `udp` rule did not admit a TCP connect.
  - Under a narrow profile, the lookup needed `file-read-metadata`.
  - A `network-outbound` query with filter `none` predicted `deny` beside a
    successful port-scoped connect.

### 7. Settings

- `evidence/settings/setpref.c` sets and synchronizes `PWTestKey` in a domain
  named by an absolute path, then reads it back. `lk.c` looks up a Mach
  name. `rd.c` reads a key from a named domain.
- `A.sb` denies file writes in the domain's directory; `B.sb` denies
  `cfprefsd` lookups. Main-session rerun:
  - Under `A`: `sync_ok=0 readback=<new value>`, no file, and the kernel log
    `Sandbox: setpref(…) deny(1) file-write-data …/app.plist`.
  - Under `B`: `sync_ok=1`, and the plist holds the value.
  - A first attempt wrote the denied path with a `..` component. That rule did
    not match, and the save succeeded.
- Explorer only:
  - `R1` to `R3` read `com.apple.dock` `lastShowIndicatorTime`. Denying file
    reads alone, or the lookup alone, still returned the value; denying both
    returned null.
  - `W3`, with both routes closed for a throwaway named domain, logged the
    app's own `file-write-create` denial under `~/Library/Preferences`. No
    file was created there.
  - `spec.json` and `spec2.json` are PW runs of the two halves: a lookup of the
    `cfprefsd` names and a create of the plist path.
- Not run: a named-domain write with the daemon reachable, which would write
  under `~/Library/Preferences`.

### 8. Extension class and rule

- `evidence/extension-class/gen.py` writes the specimens:
  - An unapplied, unentitled issuer, plus Alice and Bob under
    `(allow default) (deny file-read-data) (deny file-write*) (allow file-read-data (extension "com.apple.app-sandbox.read"))`.
  - Reads come before the token, after consumption and after release. Bob
    receives the token.
  - The targets were `w/doc.txt`, `w/other.txt`, `w/dir/inner.txt` and a
    mode-000 `w/noperm.txt`, none retained.
- Checked (`base`, `rw_token_read_policy` and `dir_token` replies retained):

  | Specimen | Bob's read after consumption | Reads after release |
  | --- | --- | --- |
  | `base` | `ok` | both denied |
  | `rw_token_read_policy` (read-write token) | denied, though the consume returned 1 | — |
  | `read_token_rw_policy` | denied | — |
  | `no_predicate` | denied | — |
  | `other_target` | denied | — |
  | `dir_token` | `ok` on the inner file | — |
  | `dac` (mode-000 file) | `read_failed` errno 13, prediction `allow` | — |

  Alice, the control, was denied after consumption in every row.

## Matters to look into

1. **The absent-path premise now has evidence.** On 25G241,
   `sandbox_check` returns `rc 1, errno 0` for an absent path whatever the
   profile, including for an unsandboxed process. That supports the planner's
   exclusion. The raw query proposed in responsibility finding 4 would receive
   that value regardless of policy. The guide calls the predicate only
   "structurally suspect".
2. **No comparison limitation when the resolved spelling differs.** The
   prediction answers for the resolved object, while the attempt also checks
   each link (finding 3). This is the mechanism behind trust matter 8 and the
   menagerie row `read_alias_denied`.
3. **Process-conditioned rules evaluate against `pw-probe-runner`**
   (finding 4). The guide does not say so.
4. **`sbpl-check` reports only a source hash.** Bytecode identity is available
   only through the sensitive opt-in receipt, which needs a live run.
5. **A filtered deny was not overridden by `exec_baseline`'s unfiltered
   `(allow file-read*)`, in either order** (run `b5`, and `sandbox-exec`).
   `docs/contract/11-policy.surface.md`, around lines 168–178, says the
   augment "can mask the denial a file-read experiment intended to observe".
   That holds for a read the profile leaves to `(deny default)` (finding 5's
   `b-exec-base`). It did not hold here for an explicit filtered deny.
   Unfiltered and same-filter denies were not tried.
6. **`exec_failed` covers both a refused spawn and a helper that ran and exited
   nonzero.** `child_pid`, `child_exit_code`, `child_term_signal` and the
   streams tell them apart. A `process-exec*` prediction of `allow` can sit
   beside a refused spawn, because the spawn also needs fork and `/dev/null`.
7. **The `read` and `read_write` extension classes do not substitute for each
   other** (finding 8). Release does not revoke an open descriptor (the
   further instance under finding 1). `docs/EXTENSIONS.md` states neither.
8. **Responsibility finding 28's inference was partly tested.** From a GUI
   session, PW's worker saw the caller's bootstrap namespace: 714 names
   gave identical lookup results from the shell and from an `exec` child of
   the worker, and the child reported manager `Aqua`. Both
   `com.apple.cfprefsd.agent` and `.daemon` resolved. A context without a GUI
   domain was not tried. The specimens, results and helpers are in
   `evidence/mach-namespace/`; the name list was not retained because it
   records the apps installed on this Mac.
9. **Smaller notes.** Every attempt step needs a `sandbox_check`, so an `exec`
   step used only to hold a process carries an unrelated query. Exec `args`
   are limited to 127 bytes each.
