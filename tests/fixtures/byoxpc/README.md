# Disposable BYOXPC ownership

`session.py` copies the selected app's complete `PWRunner.xpc` to a unique
`/private/tmp/pw-byoxpc-*` staging directory and assigns a unique
`com.policywitness.test.byoxpc.*` service. It inspects the registry and reconciliation report first and
verifies source signatures, metadata, entitlements and copy identity. Source
aliases and paths escaping the bundle are rejected before signing.

The ordinary variant preserves caller-auth keys and uses a matching Developer
ID. `install-noauth` removes those keys and requests ad-hoc signing through the
public installer. Both supply the source's extracted entitlements unless the
caller passes a plist of its own (an optional seventh argument); only
`runner install` signs the copy, and it signs the embedded worker with those
entitlements and the validator and issuer with the identity alone before sealing
the bundle. After installation the helper reads each binary's entitlements and
signatures back separately and checks the registry
record against them. Signature, runtime and connection checks must succeed
before the wrapper receives its runner environment. Installation failure is a
failed case.

Every ordinary team or no-auth session uses a registry at
`~/Library/Application Support/PolicyWitness/test-sessions/<service>/runners.json`.
Its path is persisted in durable `session.json` before the first registry read,
and every helper CLI and specimen wrapper receives `PW_RUNNER_REGISTRY`.
`HOME` remains real for signing and the user LaunchAgents location. The registry
survives reboot independently of temporary bundle staging. Only
`runner_byoxpc/default_location` installs without a registry override.

For recovery, inspect `runner list` and `runner reconcile` first. An unregistered
candidate's label names its directory under `test-sessions`; set
`PW_RUNNER_REGISTRY` to that directory's `runners.json` and inspect its records.
Ownership comes from the record's exact service, scope, bundle and pending-cleanup
state, never from the label alone. The record's bundle path locates the durable
session receipt. Preserve staging and that registry until removal is verified;
the helper deletes a private registry directory only after confirming it is empty.

The wrapper arms cleanup before setup. Staging contains durable `session.json`
with its service, bundle/plist paths, domain, source inventory, installation
observations and removal state. The run-local `session.json` is a diagnostic
receipt pointing to that durable path; cleanup follows the pointer. The
registry record's `bundle_path`, shown by `runner reconcile`, locates staging
when original output is gone. Cleanup can be resumed directly with:

```sh
tests/lib/python.sh tests/fixtures/byoxpc/session.py cleanup /path/to/policy-witness /private/tmp/pw-byoxpc-<id>/session.json
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

`neighbor_lab.py` observes process generations for coexistence controls. A
generation is a PID plus its kernel start time from `proc_pidinfo`; only ESRCH
is absence, and any other failed query is an observation failure.
`ProcessWatch` pauses one millisecond between sweeps and records each process
whose executable path is watched, with first and last sweep times. Start-time
reads bracket the executable read. A host must have launchd as its parent;
children still exposing the host path before exec are recorded as fork children,
and observed executable transitions are retained. A generation
missing from a later sweep is reported as unseen, not as exited. Processes
shorter than a sweep can be missed; sweep timing is retained with the samples.
