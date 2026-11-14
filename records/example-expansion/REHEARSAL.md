# Example expansion planning rehearsal

On 2026-11-14, three read-only submissions tested the planned flat, phased and
single-actor forms against the existing app. This was exploration outside the
dispatcher, before implementing the expanded publisher or checker. It earns
no test-case, candidate-acceptance or release credit.

## Inputs and equipment

- Checkout: `d18ce849`, with the added `rehearse.py` planning script in this
  directory. It uses the current example observer and independent consumer.
- App: `dist/PolicyWitness.app`, reporting development build 1430,
  commit `b4e007629685602f3eea8acd52400d3897695501`, contract
  `development:b038b12554610eb7c2bbfa7ae7e4e0d4943b165552935b3bc93fcd9a0c223eb4`.
- Reported host: macOS 26.7.1, build 25G241, Darwin 25.6.0, arm64.
- One version query, one `example` emission and three `run` submissions, all
  under the checkout lock and outside the automation sandbox for XPC access.
  No build, external-runner installation, fixture refresh or native mutation
  was performed.

The flat input is the emitted stdout unchanged. The phased input replaces
`probe_plan` with two phases containing the first two and final actions. The
actor input moves that same policy into one applied `selected` actor and
assigns both phases to it. The script verifies that action objects and policy
are unchanged. It samples all three paths before and after each submission
through the current same-descriptor observer.

The invoked command was:

```sh
tests/lib/checkout_lock.sh -- tests/lib/python.sh \
  records/example-expansion/rehearse.py dist/PolicyWitness.app \
  /private/tmp/pw-example-expansion-rehearsal-20261114
```

The output directory must be absent before invoking the script. Local raw
requests, stdout/stderr, process statuses, observer samples and
`observations.json` are at that temporary path. They are not committed,
protected test output or durable acceptance evidence and may disappear.
The committed script and this account preserve the method and inspected
findings, not the entire execution.

## Observed results

| Form | Phase action counts | Query outcomes | Attempt outcomes | Process/result status |
| --- | --- | --- | --- | --- |
| Flat | 3 in implicit `main` | allow, allow, deny | ok, ok, open_failed with EPERM | 0, finished |
| Phased | 2, 1 | allow, allow, deny | ok, ok, open_failed with EPERM | 0, finished |
| Actor | 2, 1; visits 1 and 2 | allow, allow, deny | ok, ok, open_failed with EPERM | 0, finished |

All answers came from the validator. Their native returns were 0, 0 and 1;
all query errnos were 0. Attempts came from the worker with `rc` 0, 0 and 1,
and errnos null, null and 1. Every step recorded `query_first`; every phase
reported arrival, completion and a collected validator.

Each fresh read reported open descriptor 5, stat return 0, read count 64 and
close return 0. Its device/inode, prefix digest and count matched that form's
independent sample of `/usr/share/dict/connectives`. The before/after samples
were equal within each passage. Stderr was empty and `consumer.validate`
reported no error for all three full envelopes. Descriptor 5 is an observed
value, not a proposed expectation.

## Actor topology and fixture consequence

The actor reply retains `steps[]` and `phases[]` at top level. Each step names
`example-reader`; each phase names that actor and its `actor_visit` (1, 2).
There is no `actors[].steps` nesting. The actor's policy/application/process
record is `actors[0]`:

- `setup_status: applied`, `applied: true`, `application_count: 1` and
  `application: {state: observed, basis: applied_publication}`.
- `policy_sha256` and `policy_received_sha256` both equal
  `affa3413994bae450fef3f1913975e0c6608ee356fb993be1a86e9f428e463ff`.
- `equipment.execution.status: matched` and `subprocess.reaped: true`.

The top-level reply holds `authority_setup`, `equipment_inventory`,
`equipment_bindings`, `equipment_entitlements` and `schedule`, even though the
workload uses no extensions. `authority_setup` has host and worker accounts.
Neither phase has a termination-gate record. Singular `runner_subprocess`
and `policy_sha256` fields are absent from this actor reply.

The dossier adds `data.specimen.actors[]`, whose entries hold `actor_id`,
`mode` and `policy`. The controller's sandbox diagnostics have an `actors`
collection alongside their aggregate assessment fields.

Source inspection also established that the existing
`tests/fixtures/contract/actor_*_reply.json` inputs are subaccount models; they
do not provide this complete valid envelope. The expansion plan therefore
assigns one dedicated, independently authored full actor fixture to the
example controls and makes full-consumer admission its first implementation
checkpoint. The live rehearsal supplies a topology reference, not fixture
values to copy or an expected-results generator.

## Scope

These runs support initial workload choice and record-location decisions on
one app and host. They do not qualify phased publication, a new checker,
constructed-control sensitivity, independent signature verification in this
rehearsal, filesystem stability between samples, dictionary-file availability
on other supported installations, or a general equivalence of execution
forms. Candidate acceptance still requires the plan's dispatcher selection.
