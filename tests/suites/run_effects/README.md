# run_effects

Pins what a run does to the machine: the exact effect of each file attempt
action, the reality of an exec helper's own effect, and the absence of any
persistent registration after a plain run. Every observation is made outside
PolicyWitness, before the envelope is decoded.

## Invariants

- `open_write` under an allowing policy truncates the target in place to one
  byte, `x`, keeping its device, inode and permission bits.
- `create` on an absent target produces an empty file with mode 0600 and one
  link. `create` on an existing target leaves bytes, identity, mode and
  timestamps unchanged.
- `unlink` removes the target.
- `open_read` and `access` leave bytes, size, mode, identity, link count and
  mtime/ctime unchanged. Access time is not compared.
- A denied twin of each mutating action leaves the target identical, and the
  attempt reports the matching failure outcome with a permission errno.
- Predictions are checked where they are stable: allow or deny from the
  validator for targets that exist throughout, and `prediction_unavailable`
  with `query_not_requested` for a target that does not exist when the query
  is planned. For an allowed `unlink`, the native allow query precedes the
  attempt: `query_first`, agreement and `drift:false` are required. The separate
  `witness_contract/queries_precede_attempts` case also checks an
  earlier read of the same target and independent absence after removal.
- A helper spawned under `(deny default)` plus `exec_baseline` with one
  `file-write*` allow creates its marker with the fixture's exact bytes at
  mode 0600. Without the allow the helper still runs (a child PID is reported)
  and exits 3 with a `--write` diagnostic, and the marker does not exist.
- One ordinary run leaves the runner registry file, the registry as
  `policy-witness runner list` reports it, and the user and system launchd
  plist directories unchanged.
- Every expectation is a pure function in `effects.py`. `checker_controls`
  feeds each one fabricated observations and requires it to accept the right
  one and reject each wrong one: an untouched seed, a replaced inode, a wrong
  mode, written bytes, a changed mtime, a missing marker, a plist that
  appeared.

The 0600 expectations assume the process umask removes no owner bits, which
holds for launchd-spawned services and ordinary shells.

## Success criteria

- Every live row's external observation matches its expectation before the
  envelope is read, and the envelope then reports `ok` with the expected
  per-step attempt outcome and prediction.
- Every control accepts or rejects as required.

## Fixtures

- Targets are random names under the case's artifact directory, seeded with
  random bytes at mode 0640 where a file must pre-exist.
- `exec_helper_effect_is_real` builds `tests/fixtures/exec` and uses its
  `--write PATH` mode; the direct control for that mode lives in
  `exec_fixture`.

## Artifacts

`<run>` is the selected output directory: `tests/out/runs/default` for the
public command, or the explicit `PW_TEST_OUT_DIR`; direct shell entrypoints
default to `tests/out/runs/direct`.

- `<run>/suites/run_effects/<case>/artifacts/*`: per row, `before.*` and
  `after.*` snapshots (raw bytes and a JSON description with digest, size,
  mode, device, inode, links, mtime and ctime) beside the `RunCapture` files
  under `run/`; `rows.json` or `attempts.json` summaries; `inventory.*.json`
  and `launchd_labels.*.json` for the plain-run case (labels are diagnostics,
  not an assertion); `controls.json` for the controls.

## Run

```
./tests/run.sh --suite run_effects
```

Included in the default battery. The live cases need the built app and XPC;
the exec case also needs the macOS C toolchain; the controls need only
Python 3. Unified log capture is disabled; it is not this suite's oracle.
