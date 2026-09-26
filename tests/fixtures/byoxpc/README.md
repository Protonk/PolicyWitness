# Disposable BYOXPC ownership

`session.py` copies the selected app's complete `PWRunner.xpc` to a unique
`/private/tmp/pw-byoxpc-*` staging directory and assigns a unique
`com.policywitness.test.byoxpc.*` service. It inspects the registry first and
verifies source signatures, metadata, entitlements and copy identity. Source
aliases and paths escaping the bundle are rejected before signing.

The ordinary variant preserves caller-auth keys and uses a matching Developer
ID. `install-noauth` removes those keys and requests ad-hoc signing through the
public installer. Both preserve extracted entitlements and embedded helper bytes;
only `runner install` signs the copy. Signature, runtime and connection checks
must succeed before the wrapper receives its runner environment. Installation
failure is a failed case.

The wrapper arms cleanup before setup. Staging contains durable `session.json`
with its service, bundle/plist paths, domain, source inventory, installation
observations and removal state. The run-local `session.json` is a diagnostic
receipt pointing to that durable path; cleanup follows the pointer. The
registry record's `bundle_path`, shown by `runner reconcile`, locates staging
when original output is gone. Cleanup can be resumed directly with:

```sh
python3 tests/fixtures/byoxpc/session.py cleanup /path/to/policy-witness /private/tmp/pw-byoxpc-<id>/session.json
```

Cleanup searches both active and pending-cleanup registry collections and uses
public `runner remove` after checking exact ownership. If installer completion
is uncertain, a matching durable registry record permits recovery; without one,
staging remains for inspection. No helper bootout is inferred from a prefix.

Deletion requires verified service/plist absence and confirmed registry cleanup.
Warnings, unknown observations and ownership disagreements retain staging and
fail the wrapper. State survives interruption after machine cleanup, so a later
attempt can finish bundle deletion. Cleanup command receipts live in staging
and are copied to existing run output before successful removal. The source
inventory is checked again before staged files are deleted. Direct installation
owns cleanup itself; suite installation stays alive across selected specimens.

`tools.py` supplies independent fake OS observations to
`shell_helpers/byoxpc_setup`, including partial and uncertain installation,
pending cleanup, and interrupted staging deletion. It creates no real service.
`runner_byoxpc/registry_recovery` separately exercises real CLI filesystem and
launchd behavior with fixture-child `HOME` and `PW_RUNNER_REGISTRY`, unique owned
services and verified final cleanup. Production entrypoints have no switch for
fake tools.
