# opt_in

Manual tests that require special host resources (logs, launchd, DYLD, toolchain).

## Invariants

- Opt-in tests are not part of `tests/run.sh --all`.
- Each test uses `test_skip` when required resources are unavailable.

## Success criteria

- Each script either passes or skips with a clear reason.

## Fixtures

- Varies by test; see `tests/OPT_IN_TESTS.md` for a registry.

## Artifacts

- `tests/out/suites/opt_in/<test_id>/artifacts/*`

Run:

```
tests/suites/opt_in/<test>.sh
```

GUI session note: tests that install or bootstrap launchd services (for example
`runner_instrumentation_dyld_env`) require a logged-in desktop session. Run
them from a local Terminal.app window; SSH/CI or sandboxed harnesses will skip
with a non-GUI session message.
