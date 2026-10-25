# Test retirement plan

## Approved result and scope

Implement three approved reductions: replace the historical known-loss capture
in the unsupported-envelope control; retire the former-red wrappers' promotion
classification; and withdraw support for schema-1 release-evidence bundles.
Preserve the current evidence and release operations specified below.

Prepared against clean `main` at
`087f095279b3d55956a07a32cea114218306115a`. The
[historical continuity investigation report](../records/tests/PW-HISTORICAL-CONTINUITY-INVESTIGATION-REPORT.md)
supplies the evidence and traced dependencies, especially findings 2, 4 and 5.
This plan records the approved implementation decisions, including acceptance
of the constructed replacement for finding 2. The report's source inspection
is evidence, not a claim that these changes have been implemented or tested.

| Retirement | Work retained | Accepted loss |
| --- | --- | --- |
| Live use of `a1_known_loss.json` | Unsupported-envelope refusal at all three readers; current-format acceptance and semantic rejection controls | Rejection of that particular historical capture |
| Tables of former assertion messages and promotion counts in the two Rust wrappers | Six exact regression tests, execution/count/status guards, raw logs and harness reports | Classification of designated assertion failures separately from other assertion failures, including the still-valid BYOXPC classifications |
| Schema-1 release-evidence support | Current-format packing and verification, publication checks, owned-output cleanup and interrupted current-format rotation recovery | Current-tool verification/publishing and archive-driven rotation/recovery for existing schema-1 archives |

The setup sensitivity proposal in finding 3 is not approved work under this
plan. Leave that case, its native observers and its checker-acceptance
requirements unchanged. The comparison matrix and its historical baseline
also remain unchanged. This work does not consolidate test execution, rename
canonical case IDs, change default membership, change product wire admission,
or alter Rust regression assertions. Preserve historical captures, release
archives and retained evidence. Do not introduce a historical reader, archive
migration framework, replay service or compatibility matrix.

Follow [test guidance](AGENTS.md), the owning suite/fixture READMEs and
[documentation guidance](../docs/AGENTS.md) when editing their accounts.
Use the [wire contract](../docs/CONTRACT.md#supported-versions) for envelope
refusal and the [release procedure](../docs/SIGNING.md#release-procedure) for
release evidence and recovery. This preparation task creates and commits only
the plan; implementation is subsequent work.

## 1. Replace the known-loss input with a constructed envelope

Change `expected_fixture_controls` in
[disposition_controls.py](suites/blackbox_e2e/disposition_controls.py).
Replace its read of `fixtures/disposition/a1_known_loss.json` with this local
constructed input, using the existing generated `contract` constants:

```python
unsupported = {
    "schema_version": contract.CONTROLLER_ENVELOPE - 1,
    "kind": "run",
    "data": {},
}
```

The unequal integer exercises unsupported-version refusal, rather than a
missing/noninteger version error. `data` and the absence of `steps` make it an
envelope for the shared gate. The empty body supplies none of the fields needed
for current interpretation. The expected result comes from the exact-version
contract; no producer or historical reply supplies the answer. No separate
fixture file or capture run is needed. The existing constructed control in
[checker_controls.py](suites/blackbox_e2e/checker_controls.py),
`consumer_controls`, supplies the same kind of frame; leave that independent
consumer/CLI coverage in place.

Keep the three entry-point checks and make their expectations precise:

| Entry point | Required result |
| --- | --- |
| `lifecycle_adapter.read_lifecycle` | Raises `ValueError` identifying an unsupported controller envelope |
| `lifecycle_oracle.check_record` | Exactly one finding, rule `D8`, kind `unsupported_version`, identifying the unsupported controller envelope |
| `consumer.validate` | Exactly one unsupported-controller-envelope error, with no downstream shape errors |

These entry points share [document_versions.py](lib/document_versions.py);
the controls establish each entry point's refusal behavior, not three
independent implementations of version admission. Do not change that gate or
any contract version. Use a descriptive control label for unsupported-envelope
refusal in the emitted records, replacing `known_loss_unsupported_version`.

Preserve acceptance of the unmodified
`fixtures/disposition/response23/a1_expected.json` and the final check that
mutations did not change that baseline. Preserve rejection of its missing
disposition record and all six existing semantic mutations: removed termination
request, exit beside signal, supported cause replaced with unknown, identical
unresolved steps, swapped step answers, and swapped answers with debug indices.
Their independently expected rules remain unchanged. The historical capture's
contents were never interpreted by its current rejection control.

Update the current-role descriptions in
[the disposition fixture README](fixtures/disposition/README.md) and
[the blackbox suite README](suites/blackbox_e2e/README.md). The historical file
stays unchanged as retained evidence with no live consumer. The current
acceptance capture and its existing refresh procedure remain in place. Check
references to `a1_known_loss.json` to confirm that no executable reader remains;
historical records and this plan may still name it.

## 2. Retire promotion classification in the Rust wrappers

Change [disposition_reds.sh](suites/unit/disposition_reds.sh) and
[byoxpc_reds.sh](suites/unit/byoxpc_reds.sh). Keep their canonical case IDs,
current exact-selection flags and artifact paths. Replace the name/message
pairs with the selected names and remove expected-assertion matching,
red/promoted counters and transition-stage verdicts. Describe the tests and
failures in terms of their current work.

The selections remain:

| Case | Exact Rust test names |
| --- | --- |
| `unit/rust.disposition_reds` | `disposition::tests::conflicting_status_representation_is_not_silently_resolved`; `disposition::tests::conflicting_status_reports_the_status_rule`; `disposition::tests::disposition_record_projects_witnessed_host_cleanup_cause`; `disposition::tests::record_contradicting_its_basis_is_withheld` |
| `unit/rust.byoxpc_reds` | `runner_manager::tests::false_valued_key_does_not_satisfy_a_requirement`; `runner_select::tests::selection_refuses_a_false_valued_required_key` |

Each wrapper passes only when every selected test ran and passed, the reported
count is exactly four or two respectively, and Cargo exited zero. Missing or
ignored results, wrong selections, build/equipment failures and nonzero Cargo
status remain failures. Preserve the complete Cargo log and the structured
harness report. The six tests remain unignored and reachable both by these
selections and by `unit/rust.unit`; their assertions are unchanged.

Update `rust_wrapper_controls` in
[disposition_controls.py](suites/blackbox_e2e/disposition_controls.py) within
the existing `blackbox_e2e/checker_controls` case. Remove the requirements for
old messages and promotion counts. Exercise both real wrappers with controlled
Cargo transcripts, using independent expectations for their exact names and
counts. Do not derive both the expected selection and passing transcript solely
from the wrapper being checked. Preserve argument and report inspection.

Cover the distinct ways a wrapper could otherwise pass misleadingly:

- All and only selected tests pass with the exact count and zero exit: pass.
- A selected test fails, with arbitrary assertion wording or no assertion text:
  fail, including a mixture of passing and failing tests.
- A selected result is missing/ignored, zero tests run, or another test is
  substituted: fail even if Cargo reports success.
- All selected success lines appear but the count includes extra tests: fail.
- All selected tests appear to pass but Cargo exits nonzero: fail.
- Compilation fails or Cargo is unavailable: fail and retain its diagnostics.

Reuse the existing transcript harness; this is not a new catalog case or a
general wrapper framework. The loss of designated-assertion classification is
intentional. Recreating that distinction under new labels would retain the
retired responsibility.

Update descriptions in [catalog.json](catalog.json),
[the unit README](suites/unit/README.md) and
[the blackbox README](suites/blackbox_e2e/README.md), plus directly affected
comments and report messages. Keep membership, prerequisites and execution
routes. `docs/architecture.json` cites `rust_wrapper_controls`: preserve a valid
citation to the continuing check. If a cited symbol or its account must change,
edit the manifest and regenerate through its owning generator; do not edit
generated architecture documentation directly.

## 3. Withdraw schema-1 release-evidence support

### Settle recovery that still needs the old reader

Before removing the recovery route, inspect the implementation checkout's
release-rotation journals and `tests/out/.release-rotation/` for unfinished
operations that depend on schema 1. Preserve their owned staging and journals.
If such an operation exists, settle it through the existing
[recovery procedure](../docs/SIGNING.md#portable-test-evidence-and-release-cleanup)
while its reader remains available. An ambiguous or unresumable transaction
blocks this retirement until its disposition is resolved; the two test
retirements can proceed, be verified and committed, and be reported individually
complete under the criteria below. Retirement 3 and the overall plan remain
incomplete. Never bypass recovery by deleting its quarantine, changing journal
state or unlinking `tests/.checkout.lock`.

The investigation's local-only observations found six schema-1 archives, all
with completed rotation records and an empty quarantine. That observation is
not a fresh recovery check and makes no claim about other checkouts. The
transition requirement is to settle unfinished work encountered in the
operating scope, not to retain compatibility indefinitely for completed archives.

### Narrow the reader and remove its old-format test machinery

In [release_runs.py](lib/release_runs.py), make schema 2 the sole supported
release-evidence bundle format. Remove schema-1 admission and its separate
battery-role/summary interpretation from `verify_bundle`, `battery_source` and
`verify_release`. Remove branches that become unreachable under the narrowed
admission rule without weakening required fields or validations. Keep the
packer writing schema 2; this reader retirement does not change schema-2 bytes
or any PW request/response version.

Preserve current-format checks for archive/member inventories, hashes, modes
and symlink targets; summary binding; ZIP identity and provenance; acceptance
of that exact ZIP; and a successful, terminal default battery nested at
`acceptance/tests/run.json`. Preserve refusal of malformed battery references
and of an `all` selection even when its explicit selector arrays are empty.

The callers in [release_archive.py](lib/release_archive.py),
[release_publish.py](lib/release_publish.py) and
[release_rotate.py](lib/release_rotate.py) must retain verification before
exposing a newly prepared archive, publishing it or using it to retire working
evidence. A freshly prepared release package is also called an archive by these
tools; its verification remains required. Existing schema-1 archives remain
intact, with their loss of current-tool service explicitly accepted.

In [check_release_rotation.py](suites/preflight/check_release_rotation.py):

1. Remove `legacy_pack`, `make_legacy_release`, the `legacy` compatibility
   scenarios, their invocations and the old-format option in `fixture`.
2. Keep `battery_contract`'s schema-2 default-selection and malformed-reference
   controls while removing its schema-1 branch. Do not delete the mixed-purpose
   helper merely because it currently uses the old fixture builder.
3. Preserve current-format archive portability, corruption/symlink refusals,
   output ownership and pins, active-resource protection, replacement-path
   protection, atomic index updates, locking and interrupted deletion recovery.
4. Preserve the observation that a new schema-2 release can retire older owned
   acceptance and separately retained battery output. Set up that old working
   output with current ownership/retention fixtures, without reconstructing or
   verifying an old archive. The new archive must verify; an inert retained
   historical artifact can establish that cleanup leaves archive bytes alone.

Add a bounded unsupported-format rejection control using an otherwise valid
current fixture with only the manifest's schema number changed to 1. Update
the enclosing manifest-hash reference when needed so the check reaches format
admission rather than stopping at an unrelated checksum mismatch. The unchanged
schema-2 neighbor must still pass. Do not retain an old-format packer to test
refusal.

Exercise the refusal through bundle/release verification and the affected
publication and rotation callers in their existing fixture controls. Confirm
that publication refuses before remote commands and rotation refuses before
index, journal or output mutation. The publication controls use their existing
offline command fixtures; no real publishing, tagging, notarization or release
cleanup is needed to validate the change. Retain current-format success and
failure controls in
[check_release_publish.py](suites/preflight/check_release_publish.py).

Update [the preflight README](suites/preflight/README.md), the format and recovery
account in [SIGNING.md](../docs/SIGNING.md), and affected helper docstrings to
state the current supported format and operations. Check
[the distribution README](../dist/README.md) and recovery guidance for claims
that would now imply unsupported service. Keep the current-format recovery
instructions and artifact-preservation rules. Do not add migration promises
or rewrite historical records to describe the new reader.

## Verification and completion

Make the retirements as separately reviewable changes, with their affected
current documentation. The capture and wrapper changes share
`disposition_controls.py`; keep their input and diagnostic changes distinct
within that file. Recheck the source state and preserve preexisting work before
implementation. No historical release build or native setup experiment is
required by these changes.

### Verification credited to each retirement

Each retirement needs recorded verification against a source state containing
its implementation and updated controls. Use this mapping:

| Retirement | Required cases | Required evidence |
| --- | --- | --- |
| 1. Constructed unsupported envelope | `blackbox_e2e/checker_controls` | The three reader refusals, accepted current capture and preserved semantic mutations specified in section 1 |
| 2. Wrapper promotion machinery | `blackbox_e2e/checker_controls`; `unit/rust.disposition_reds`; `unit/rust.byoxpc_reds`; `unit/rust.unit` | Controlled pass/failure transcripts for both revised wrappers, actual execution of their exact selections, and the continuing Rust batch route specified in section 2 |
| 3. Schema-1 release-evidence support | `preflight/release_publish_controls`; `preflight/release_rotation_controls` | Schema-1 refusal through the narrowed reader and callers before side effects, plus preserved current-format verification, publication, cleanup and recovery specified in section 3 |

Also run `source_drift/runner_source_manifests_agree` against each completed
change's current documentation and registry state, with any additional generator
checks described below. This case can be shared by retirements verified together.
Review each mapped case's specific outcomes; an overall passing status does not
establish an omitted assertion or a retirement that is not implemented.

Three separate physical runs are not required. A shared run can credit several
retirements when all of their changes and controls are present in its recorded
source state and all of their mapped cases succeed. For example, retirements 1
and 2 can share the checker, unit and source-drift cases while retirement 3 is
blocked. Omit the release cases from that partial selection. If they run anyway
against the unchanged reader, their results establish existing behavior and
cannot credit schema-1 withdrawal.

A single run of the following union can credit all three retirements after all
three are implemented. It is not a required final rerun when separate applicable
evidence already covers every retirement. Inspect the intended selection with
`--list`, then execute through the dispatcher from the repository root. Use a
fresh unused output directory for each run; the following name is an example:

```sh
PW_TEST_OUT_DIR=tests/out/runs/test-retirement-implementation-01 tests/run.sh \
  --case blackbox_e2e/checker_controls \
  --case unit/rust.disposition_reds \
  --case unit/rust.byoxpc_reds \
  --case unit/rust.unit \
  --case preflight/release_publish_controls \
  --case preflight/release_rotation_controls \
  --case source_drift/runner_source_manifests_agree
```

The catalog currently requires an app for `blackbox_e2e/checker_controls`, Cargo
for the unit cases, Clang for the release fixtures, and Meson for the selected
source-drift case. Honor dispatcher prerequisites even where a nested control
uses constructed input. Reuse a suitable signed app only under the
[evidence applicability rules](AGENTS.md#evaluate-and-reuse-evidence); build
through the signed pipeline if required. Do not bypass the dispatcher or add
skips. Apply the documented sandbox retry procedure to actual environmental
refusals. If generator inputs change, regenerate with the owning tool and add
the corresponding source-drift case, such as
`source_drift/architecture_documentation` for architecture inputs.

Review the resulting evidence for the specific preservation/refusal outcomes
of the retirements being credited, not only the overall exit status. For those
retirements, confirm that active consumers no longer read the historical capture,
classify expected old assertions or admit schema 1, respectively.
Check affected source references, descriptions, links, canonical IDs, generated
copies when applicable, and `git diff --check`. Keep existing evidence immutable
and distinguish new test results from reused observations.

Record an evidence mapping for each retirement with its implementation commits
or completion notes: implementation revision, tested source snapshot (including
any uncommitted delta), run ID/location, credited case IDs, command/configuration,
app or equipment applicability, and the specific outcomes established. One run
may appear in several mappings; no duplicate evidence files are needed. When
later work changes a dependency, apply the test guidance's rerun or reviewed-
exception rules before carrying earlier credit forward. In particular,
retirements 1 and 2 share `disposition_controls.py`; their evidence is not
automatically interchangeable across edits to that file.

### Individual and overall completion

A retirement is complete when its own approved responsibility is removed, its
mapped verification and preservation checks succeed against the applicable
implementation, and its affected documentation reflects the accepted loss.
It may then be committed and reported complete independently of the other two.
If a preservation check fails, resolve it before declaring that retirement
complete; do not broaden the accepted losses to obtain a pass.

The overall plan is complete only when all three retirements are complete.
If schema-1 recovery blocks retirement 3, verified retirements 1 and 2 may be
committed and reported as complete, with retirement 3 explicitly reported as
blocked and the overall plan as incomplete. Record the recovery blocker and
what must be resolved before the narrowed reader can be implemented and tested.
Passing release controls against the unchanged reader do not change that status.

This plan was prepared with source inspection and static document checks.
No retirement, test execution, build, release operation or evidence cleanup
was performed while preparing it.
