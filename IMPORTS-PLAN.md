# IMPORTS-PLAN.md

**Status:** ephemeral. Delete when A/B/C have all landed or been explicitly
abandoned. Not user-facing documentation.

## Background

A downstream integration report confirmed that `(import ...)`, `(param ...)`,
and `(string-append (param ...))` already compile and run correctly against
the notarized `policy-witness` binary (sha256
`36540b248e8b973007add07212ee151f425a9136c40f91f9c4761ef1a34460f9`). That's
because `sbpl-preflight` delegates to Apple's `sandbox_compile_string` +
`sandbox_create_params` / `sandbox_set_param`; libsandbox does the heavy
lifting and we hand the source through unchanged
(`controller/src/bin/sbpl-preflight.rs:18-31`).

What we *don't* do is help users debug what they wrote, audit what got
compiled, or understand why a probe denied. This plan adds three discrete
capabilities (A → B → C) without reimplementing anything libsandbox already
does well.

Order is set so the SBPL tokenizer from A is reused by B; C is independent
and ships when we want it. Each section is independently shippable behind a
single feature add — don't bundle.

---

## A — Pre-validate params before `sandbox_compile_string`

### Problem

Today, when a profile references `(param "HOME")` but the request omits
`HOME` from `policy.params`, libsandbox falls back to a sentinel false and
the surrounding pattern check produces:

```
sandbox_compile_string failed: invalid data type of path filter; expected pattern, got boolean
```

That error is incomprehensible to anyone not steeped in libsandbox internals.
Verified against our current binary in this session.

### Scope

Add a minimal SBPL tokenizer to `sbpl-preflight` that scans for `(param
"NAME")` references; diff against `policy.params` keys; surface the diff in
the preflight envelope; emit a clean `normalized_outcome` for the
missing-params case.

### Files to touch

- `controller/src/bin/sbpl-preflight.rs` — new module-local
  `sbpl_lex::param_refs(source) -> BTreeSet<String>`, new envelope fields,
  new outcome.
- `controller/integration/cli_contract.rs` — at least one integration test
  that covers `missing_params`.
- `PolicyWitness.md` — short note in the policy section documenting the new
  fields and outcome.

### Tokenizer requirements

- Paren-aware: must not confuse `(param "X")` inside a string literal with a
  real reference. Strings are double-quoted with `\"` escapes per Scheme.
- Comment-aware: `;` starts a line comment. Tokens inside comments don't
  count.
- Deduplicating: each unique name listed once.
- Robust to whitespace, newlines, and nested forms. No need to handle
  s-expression macros beyond the literal `(param "..." )` shape — libsandbox
  catches the rest.
- Cap source size to something reasonable (e.g. 4 MiB) so a malformed input
  can't push us into long scans.

Don't pull a parser crate. ~80 lines of hand-written Rust. Mark the module
`#[cfg_attr(test, allow(dead_code))]` if needed so future reuse from B
doesn't fight visibility.

### Envelope schema (preflight)

Additive — existing consumers unaffected. New `data` fields:

```json
{
  "params_referenced": ["HOME", "USER"],
  "params_supplied":   ["HOME"],
  "params_missing":    ["USER"],
  "params_unused":     []
}
```

All four are always present (possibly empty arrays). Sorted, deduplicated.

### Outcome semantics

- If `params_missing` is non-empty: set `result.normalized_outcome =
  "missing_params"`, `result.error = "policy references params not supplied:
  USER"` (comma-joined list, cap length). Still attempt the
  `sandbox_compile_string` call so a *separate* syntax error in the source
  also surfaces (in `compile_error`). The envelope can carry both signals;
  consumers branch on `normalized_outcome`.
- If `params_missing` is empty but `params_unused` is non-empty: just record
  it; do not fail. Unused params are often harmless leftovers from a
  template.
- Otherwise unchanged from today.

Exit code unchanged: `0` on compile success, `1` on any failure including
`missing_params`.

### Tests

`controller/src/bin/sbpl-preflight.rs` `#[cfg(test)] mod tests`:

- `param_refs_finds_single` — `(allow file-read-data (subpath (param "X")))`
  → `{"X"}`.
- `param_refs_finds_inside_string_append` —
  `(string-append (param "A") "/" (param "B"))` → `{"A","B"}`.
- `param_refs_ignores_strings` — `"(param \"FAKE\")"` (inside a string
  literal) → `{}`.
- `param_refs_ignores_comments` — `; (param "FAKE")` on its own line → `{}`.
- `param_refs_dedupes` — same name twice → singleton.
- `param_refs_empty_source` → `{}`.

Integration (`controller/integration/cli_contract.rs`):

- `preflight_missing_params_returns_clean_outcome` — request omitting `HOME`
  against a source that references it; expect `normalized_outcome:
  "missing_params"` and `params_missing: ["HOME"]`.

### Exit criteria

- `cargo test` passes.
- The probe from the integration report ("param referenced but not provided"
  → "expected pattern, got boolean") now returns `missing_params` with a
  clear error string and the missing name listed.
- No change to existing envelopes for inputs that already compiled.

### Out of scope for A

- Param *value* validation (type/length/charset checks). Libsandbox owns
  that.
- Default values. SBPL doesn't have them; not our job to invent.
- Param normalization (e.g. trailing-slash stripping). Pass-through.

---

## B — Import provenance + `policy_closure_sha256`

### Problem

`policy_sha256` is `sha256(sbpl_source)`. For any profile with `(import
"system.sb")`, that hash doesn't identify what actually got compiled — the
imported content is invisible. Reproducibility, audit, and "did this fixture
behave the same after the OS update?" workflows can't rely on the current
hash.

### Scope

Extend A's tokenizer to also extract `(import "NAME")`. Resolve each import
against libsandbox's actual search path (which we have to verify
empirically). Record the closure as evidence. Compute a hash that covers
both the user source and the resolved imports.

### Files to touch

- `controller/src/bin/sbpl-preflight.rs` — extend tokenizer, add resolver,
  add closure-hash computation, extend envelope.
- `tests/suites/preflight/` — new fixture exercising `(import "system.sb")`
  and a no-such-import case.
- `PolicyWitness.md` — short note on import provenance and the new closure
  hash.

### Resolution order

**Verify before implementing.** Run something like:

```
dtruss -t open xcrun policy-witness run /tmp/probe-import.json 2>&1 \
  | grep -E 'Profiles/|sandbox/'
```

against a fixture that imports a deliberately-missing name to surface the
search path libsandbox actually walks. The expected candidates (in some
order):

- `/System/Library/Sandbox/Profiles/<name>`
- `/System/Library/Sandbox/Profiles/<name>.sb`
- `/usr/share/sandbox/<name>`
- `/usr/share/sandbox/<name>.sb`

Treat the dtruss output as authoritative. Document the resolved order at the
top of the resolver function with a comment naming the macOS build it was
verified against. If Apple changes it later we'll re-verify; this is not
worth caching across releases.

### Recursion

Imports can import. Resolve transitively. Cap at depth 8 and at 64 unique
imports; record the cap as `data.imports_truncated = true` if hit. Cycle
detection by tracking already-resolved names; on a cycle, stop and record
`imports_cycle: [...names...]`.

### Envelope schema (preflight)

Additive. New `data` fields:

```json
{
  "imports": [
    {
      "name": "system.sb",
      "resolved_path": "/System/Library/Sandbox/Profiles/system.sb",
      "sha256": "<hex>",
      "size_bytes": 4711,
      "mtime_unix": 1700000000
    }
  ],
  "imports_truncated": false,
  "imports_cycle": null,
  "macos_build_version": "24D70",
  "policy_closure_sha256": "<hex>"
}
```

`policy_closure_sha256` is computed as:

```
sha256(
  sbpl_source           (raw bytes) ||
  0x1F                  (record separator) ||
  "\n".join(sorted(import.resolved_path + " " + import.sha256))
)
```

The separator and join shape are part of the contract — pick once, document
once, don't change. `macos_build_version` is `sw_vers -buildVersion` cached
per-process.

### Failure modes

- Import name doesn't resolve: record the failure as `imports: [{name,
  resolved_path: null, error: "not found in search path"}]` but **don't
  fail preflight** — libsandbox's own compile will produce its error
  message which we'll surface in `compile_error`. We're documenting what we
  saw; libsandbox is authoritative on whether the policy is valid.
- Resolved file unreadable (perms): record `error: "permission denied"`,
  same disposition.

### Tests

- `import_refs_finds_single` — `(import "system.sb")` → `["system.sb"]`.
- `import_refs_ignores_strings_and_comments` — same defenses as A.
- `resolve_system_sb_against_real_filesystem` — gated on the file existing;
  resolved path and non-empty sha. Skip on CI where the file is absent.
- `closure_hash_changes_when_source_changes` — fixture A and fixture B
  (different sources, same imports) produce different closure hashes.
- `closure_hash_stable_for_identical_inputs` — re-run on the same input,
  same hash.

### Exit criteria

- The dtruss verification is recorded in a comment at the top of the
  resolver with the macOS build it was checked against.
- A fixture with `(import "system.sb")` produces an envelope with non-empty
  `imports[0].sha256` matching the file on disk.
- `policy_closure_sha256` changes if either the source or any imported file
  changes; doesn't change otherwise.
- No regression in existing envelopes for sources with no imports
  (`imports: []`, `imports_truncated: false`, `imports_cycle: null`,
  `policy_closure_sha256 == policy_sha256` is acceptable but spell out the
  rule in code).

### Out of scope for B

- Re-resolving imports across OS versions ("would this still resolve on
  macOS 15.x?"). We record what we saw on the host, period.
- Patching imports to a pinned content. If a user wants that they can
  inline the import into `sbpl_source` and skip the import statement.
- Anything that would block compile on import resolution failure.
  Libsandbox decides; we observe.

---

## C — Kernel-side path diagnostics on probe results

### Problem

When `(subpath "/etc")` denies `/etc/hosts` even though the file exists and
the rule "should" match, the caller has no way to see which path form
libsandbox compared against. The integration report's Q2 mystery dies here:
firmlinks plus the data/system volume split mean the kernel-side path is
likely `/System/Volumes/Data/private/etc/hosts`, not what the SBPL rule
matches literally. Today we record `effective_filter_value` (realpath
result) for display but don't expose the other candidate forms.

### Scope

Extend the probe result with a `path_diagnostics` block carrying every
candidate form of the check path. Don't change which form gets passed to
`sandbox_check` — this is observation only.

### Files to touch

- `runner/ProbeRunner.swift` — extend `runSandboxCheck` with the
  diagnostics computation; extend `PWRunnerSandboxCheckResult`.
- `runner/PWRunnerAPI.swift` — add `path_diagnostics` field, bump wire
  version (additive only — old clients ignoring unknown fields keep
  working).
- `runner/PathUtils.swift` — add a `firmlinkResolved(_:)` helper that
  parses `/usr/share/firmlinks` once per process (lazy static).
- Controller side: serde struct in `controller/src/runner_select.rs` or
  wherever sandbox_check results are deserialized — add the new optional
  field.

### Candidate forms to record

For path-filter checks only (filter kind = path):

```swift
struct PathDiagnostics: Codable {
  let input: String                   // raw, as passed
  let realpath_resolved: String?      // current effective_filter_value
  let firmlink_resolved: String?      // input with /usr/share/firmlinks
                                      //   prefix rewritten if applicable
  let data_volume_form: String?       // /private/foo → /System/Volumes/Data/private/foo
}
```

All optional; nil when computation fails or the form isn't applicable
(e.g. relative path). For non-path filters, omit the block entirely.

### Firmlinks parser

`/usr/share/firmlinks` is a small text file:

```
/AppleInternal	AppleInternal
/Applications	Applications
/Library	Library
/System/Volumes/Data/mnt	mnt
/Users	Users
/Volumes	Volumes
/private	private
/usr/local	usr/local
/usr/libexec/cups	usr/libexec/cups
/opt	opt
```

Each line is `<source-path>\t<data-volume-subpath>`. Resolution:

- If `input` starts with `source-path`, replace that prefix with
  `/System/Volumes/Data/<data-volume-subpath>`; return.
- Else return nil for the firmlink form.

Parse once per process. Tolerate missing file (older OS) — diagnostics
just won't include the firmlink form.

### Tests

- `firmlinks_parser_handles_real_file` — parse the on-disk file; expect
  `/private` in the map.
- `data_volume_form_for_private` — `/private/etc/hosts` →
  `/System/Volumes/Data/private/etc/hosts`.
- `data_volume_form_for_unaffected` — `/usr/local/foo` returns nil for
  data_volume_form (because `/usr/local` is itself a firmlink with a
  different target).
- `runner_smoke_emits_path_diagnostics` — integration smoke that runs a
  trivial probe and asserts the `path_diagnostics` block is present and
  populated.

### Exit criteria

- A probe with filter kind = path and input `/etc/hosts` produces a
  `path_diagnostics` block listing all four candidate forms; at least one
  should be `/System/Volumes/Data/private/etc/hosts`.
- No change to which path string is passed to `sandbox_check` — this is
  observation only, never input.
- Old controllers reading new runner output ignore the new field
  gracefully (additive only).

### Out of scope for C

- Changing what `sandbox_check` is called with. Too easy to break existing
  probes.
- Suggesting "use this subpath instead" — that's a downstream call.
- Anything Q2-specific beyond surfacing the candidate forms. Whether
  `(subpath "/private/etc")` *should* match `/etc/hosts` is Apple-internal
  and not something we'll resolve in this codebase.

---

## Sequencing notes

- A and B share a tokenizer. Build it in A as a small internal module;
  re-export only what B needs.
- B's dtruss verification step is the riskiest unknown. Do it first within
  B and lock the resolution order down in code with a citation comment.
- C is fully independent — it could ship before A/B if priorities shift.
  Keeping it last only because A/B are higher leverage for the
  integration-report cohort that's actively writing policies.

## What we are NOT doing

- Building our own SBPL parser. Libsandbox already does this correctly.
- Reimplementing import resolution differently from libsandbox. We observe;
  libsandbox decides.
- Caching compiled profiles (`sandbox_compile_file`). Not worth it at our
  scale.
- Validating `(import ...)` recursively against a hypothetical OS version.
  We record what *this* host sees.
- Anything for `policy.compiled_profile_b64`. It was never planned; the
  downstream report's reference was an error in their planning doc.
