# Repair build provenance acceptance

## Goal and scope

Make the build's provenance and cache-safety guarantees hold at the boundaries
where review found counterexamples, and replace the affected acceptance claims
with independently observed results. Repair lock ownership and lifetime, path
admission before writes, Cargo selection and freshness, record validation and
effective-setting capture, and bounded tool probes.

The existing passing runs establish the cases they exercised. They do not
establish the missing distinctions below. Preserve their evidence and correct
the conclusions in the associated
[acceptance record](records/BUILD-PROVENANCE-ACCEPTANCE.md). This plan also restores
portable wrong-SDK fixtures needed for acceptance. The worker clock finding is
separate work under [SAFE-WAIT-TIME-PLAN.md](runner/SAFE-WAIT-TIME-PLAN.md); it does
not require redesigning the build or delaying independent repairs here.

Keep one stable `tests/.checkout.lock`, explicit fresh mode, the existing cache
replacement scope, inside-out signing, and the distinction between current
tool observations and Cargo's testimony about reused outputs. This work does
not promise reproducible builds or authenticate a cached binary's compilation
history. It does not change the runner wire contract or `app_provenance`.

## Starting evidence and order of work

The reviewed implementation is `a785007`, with control corrections in `4cb989f`
and `de5034b` and the acceptance record in `e845b02`. Disposable review probes
exposed the failures described below; those probes were not retained acceptance
runs. Turn each into a retained regression control before crediting its repair.

Start with the lock and path-admission repairs together: mutation helpers must
have both verified ownership and admitted paths. Probe bounds can be repaired
independently. Cargo selection then uses those bounds; record production and
inspection must be updated together after the captured observations are correct.
Integrate the corresponding documentation with each increment, then run final
acceptance against the final implementation and controls.

Read the root and [test guidance](tests/AGENTS.md), and the owning suite 
references before execution. Use disposable checkouts and fresh managed 
run directories. Never unlink the checkout lock or alter the accepted app 
to conceal a failed check.

## 1. Establish ownership and preserve it through protected descendants

**Defect.** [checkout_lock.py](tests/lib/checkout_lock.py) verifies a claim by
attempting `LOCK_EX | LOCK_NB` on the supplied descriptor. A stale, independently
opened descriptor can acquire a free lock and pass as an inherited hold.
[build_provenance.py](tests/lib/build_provenance.py)'s `load_session` checks nonce
equality without verifying a hold; two absent nonces compare equal, allowing a
direct `fresh-remove` invocation to delete caches without ownership.

The dispatcher's [retention lock](tests/lib/retention.py) is non-inheritable and
[suite_run.py](tests/lib/suite_run.py) does not pass it to suite children. Killing
the dispatcher can therefore free the lock while its child still runs. The
build's orphan control in
[build_refusals.py](tests/suites/preflight/opt_in/build_refusals.py) records
`held_after_kill` but never asserts it. Its credited value was true; the defect
is that a false value would also pass.

**Repair.** Centralize acquisition, nested admission and child launching in
`checkout_lock.py`, used by builds, the dispatcher, retention operations and
supported standalone Cargo commands. Expose an owned scope to Python callers
instead of independently reconstructing ownership from environment strings.
Keep nonblocking busy refusal and closing descriptors as the release mechanism.

For nested admission, use a live acquisition owner to hand off an already-held
descriptor over a local descriptor-passing channel. The launcher remains a
small supervisor for its command; Python callers keep the owner for their
scope. Establish the private channel at child launch; knowledge of a socket
pathname and nonce alone must not admit an unrelated process to an active build.
Bind the handoff to the checkout inode and the current acquisition's nonce,
and reject missing, stale, foreign or malformed claims. Environment
values locate a claim; they cannot substitute for a successful handoff from
the owner. This deliberately replaces re-locking an alleged inherited hold:
successfully acquiring a free lock says nothing about earlier ownership.
Keep the owner channel private to the operation, bound its waits and cleanup,
and refuse new nested mutations if its owner is gone. Already-running protected
children must continue to hold the actual lock independently of that owner.

Use the shell command entrypoint specified in section 4 to preserve caller
requests before starting the Python owner. Acquisition and descriptor handoff
still belong to `checkout_lock.py`; the shell front end captures requests and
executes that implementation. Route documented nested-build commands through
the front end along with the standalone Cargo examples.

Pass the held descriptor explicitly across every managed subprocess boundary,
including suite wrappers and test-equipment wrappers. Check the real
Cargo/Meson/Ninja paths as well as the fixtures. An inheritable descriptor in
the parent alone does not override a child's `close_fds` behavior. On orderly
cancellation, forward termination and observe protected children finish; on
parent death, inherited descriptors keep the lock held until the last protected
child exits. Unrelated descendants must not keep the hold indefinitely.

Every helper that creates or updates a session, removes a cache, or publishes
or extends a stamp must enter through the owned scope and validate the session's
nonempty acquisition identity. Direct invocations without that ownership refuse
before mutation. Preserve acceptance's separate lifetime lock and its release
of the checkout lock before launching the child dispatcher. Do not add a
release-wide outer hold around commands that acquire the checkout lock anew.

**Acceptance.** Use an outside process to observe busy/free state and protected
child exit, with explicit synchronization rather than sleep-based guesses:

- A stale claim, an unheld descriptor on the correct inode, another open while
  a real owner holds the lock, a wrong nonce, a closed descriptor and another
  worktree all refuse. The real holder's state and the lock inode are unchanged.
  Exercise owner exit during nested admission; it must not create a new hold
  under an old session identity.
- Session writes, fresh removal and stamp publication refuse with no claim,
  missing nonces or a stale session. Valid owned neighbours succeed.
- Kill a dispatcher with a protected suite child running, and kill a build with
  a protected tool child running. A competing build and battery refuse until
  the last protected child exits, then succeed. Include a grandchild beyond a
  wrapper and kill the wrapper too, so the wrapper cannot mask a dropped FD.
- Exercise SIGINT, SIGTERM and SIGKILL at the relevant parent boundaries,
  successful nesting, packaging through build exit, standalone Cargo exclusion,
  and independent worktrees. Assert every recorded lifetime condition, including
  `held_after_kill`. A mutation that drops the passed descriptor must fail its
  control.

Establish the owner-handoff and lifetime controls before routing destructive
helpers through the new API. If a supported tool drops the descriptor, repair
that launch boundary or refuse that unsupported path; a supervisor's survival
alone cannot satisfy the orphan gate.

Small review probes through real Cargo and Meson/Ninja preserved an explicitly
passed descriptor. This supports feasibility on the installed tools; those
probes did not kill parents and do not establish the lifetime gate above.

## 2. Admit cache paths before the first write

**Defect.** [build.sh](build.sh) creates `controller/target/` and starts the
session before `fresh-remove` validates cache paths. With `controller/target`
symlinked outside the checkout, review observed the outside session file being
overwritten before the later removal refusal.

**Repair.** Under the verified checkout hold, admit all components of
`builddir/`, `controller/target/`, `controller/target/release/` and the session
destination before creating directories, writing sessions or inspecting mutable
cache state through those paths. Refuse symlinked, foreign-owned and non-directory
components and unsafe existing destination files. Missing directories may be
created only beneath admitted parents. Keep this admission in the shared helper
so direct mutation commands cannot bypass it.

Anchor writes and removals to the admitted parents, rechecking identity where
an operation reopens a path. The checkout lock excludes cooperating builds; it
does not make a checked pathname immutable. Admit both removal roots before
deleting either. Fresh mode still removes only `builddir/` and
`controller/target/release/`, preserving debug outputs and downloaded caches.

**Acceptance.** Run the actual script with symlinks at each relevant component,
including the session destination, in incremental and fresh mode. Retain outside
sentinels, hashes and directory inventories showing no outside file was created,
changed or deleted. Assert refusal before `session-start` writes or tool work.
Exercise an owned missing path, an ordinary existing cache, a failed removal,
and a deterministic path replacement between admission and use. The valid
neighbours must still build; disabling early admission must expose the original
outside-session overwrite.

## 3. Resolve Cargo selection honestly and require explicit freshness

**Defect.** The configuration scanner uses line-oriented regular expressions.
Valid inline TOML such as `build = { rustc = "/configured-wrapper" }` escapes
detection: Cargo uses the wrapper while the collector reports PATH selection.
Recognized file settings instead cause unconditional refusal even when an
explicit `RUSTC` overrides them. Discovery starts at the manifest directory,
although Cargo is invoked from the caller's working directory. `cargo_judge`
coerces a missing or null `fresh` value to false, allowing an absent observation
to count as a fresh-mode rebuild.

Cargo 1.99 also follows recursive `include` files, which the collector ignores.
A disposable review crate compiled successfully with `build.rustc` supplied
by an included file while the collector reported PATH selection. A second
successful build used `[env]` with `force = true` to select another compiler
command through PATH and pass `MACOSX_DEPLOYMENT_TARGET=26.1` to it despite
the invoking shell's `26.0`; the collector still reported the original compiler
command. These compilation receipts establish selection counterexamples, not
acceptance of a complete PolicyWitness build with the wrong minimum.

**Repair.** Preserve the caller's working directory and make configuration
discovery match that exact Cargo invocation, including ancestor and `CARGO_HOME`
configuration and Cargo's choice when both configuration filenames exist. Parse
TOML structurally, with bounded input, rather than extracting keys with regexes.
Vendor a TOML parser compatible with the Python interpreter the build actually
invokes, retaining its license and version information. This keeps parsing
available without assuming `/usr/bin/python3` supplies `tomllib`, changing the
interpreter-selection policy or installing a dependency during a build. Exercise
the parser through that same interpreter in the controls.

Follow the complete selected configuration graph, including recursive
[`include` files](https://doc.rust-lang.org/cargo/reference/config.html#include).
Apply Cargo's include order and merge precedence, with the including file's
values overriding its included values, and preserve each value's origin for
relative-path resolution. Bound individual and aggregate input bytes, file
count and recursion depth, and detect cycles. Honor optional missing includes;
required missing files, malformed files and unsupported or over-bound graphs
must refuse explicitly. Never treat an unread or unvisited include as proof
that no compiler, wrapper or relevant environment setting exists.

Resolve compiler and wrapper selection through Cargo's precedence, including
file settings, environment overrides, relative command paths and explicit empty
wrapper resets. Keep configured commands distinct from their probe identities.
An unresolvable relevant setting must produce a specific required-unknown
refusal, never silent PATH selection. A setting overridden by a known
higher-precedence value must not cause that refusal. Keep raw configuration and
unrelated environment values out of published records.

Resolve Cargo's [`[env]` transformations](https://doc.rust-lang.org/cargo/reference/config.html#env)
for relevant compiler inputs, including `force`, `relative`, and inherited
values. Keep the invocation environment used for Cargo's own configuration
discovery separate from the environment Cargo constructs for its children;
do not feed every `[env]` value back into configuration discovery. Resolve
compiler and wrapper commands and probe their identities in the effective
child environment and working directory. In particular, PATH and Rust toolchain
selection variables can change which compiler runs, while `SDKROOT` and
`MACOSX_DEPLOYMENT_TARGET` can change its inputs. Resolve these effects or refuse
with a required-unknown diagnostic; never silently use the shell's pre-Cargo
values. Keep PATH and unrelated environment contents private. Effective SDK
and deployment settings that conflict with build policy must refuse, with
the independent output checks retained as a separate gate.

Use Cargo's per-output fingerprint for effective flags and label it as Cargo's
record. Determine requested sources by precedence, not just by equal flag
strings. Preserve explicit unresolved attribution for target rules the collector
cannot establish; equality alone does not prove which rule supplied a value.
Do not turn a present-day compiler probe into the historical identity of a
reused executable's compiler.

Require a literal boolean `fresh` on each artifact message bound to a shipped
target, profile and admitted executable. Missing, malformed or ambiguous
judgments refuse. Fresh mode requires an observed `false` for every shipped
Cargo target. Unsupported directory metadata cannot silently establish that
intermediate output stayed inside the admitted target directory.

**Acceptance.** Extend the existing provenance and refusal controls with real
forwarding compiler/wrapper receipts and final-output observations as the oracle.
Cover inline, dotted and table TOML; discovery from a different invocation
directory; ancestor and Cargo-home settings; overridden file settings; compiler
and both wrapper selections; encoded flags versus `RUSTFLAGS`; and target versus
build flags. With retained caches, change compiler selection and effective flags
and verify the observed refusal or rebuild and the resulting record. Keep
version-text substitution controls labelled as parsing/identity controls.

Add included compiler/wrapper selections, recursive includes, include/file
precedence, relative commands from included files, optional missing includes,
required missing or malformed includes, cycles and graph-bound refusals. Add
`[env]` controls with inherited values both present and absent, `force` both
ways and `relative` path values. Reproduce the successful PATH-based compiler
selection counterexample with a forwarding wrapper; record its actual command,
working directory and relevant environment. Exercise SDK and deployment
overrides with valid neighbours and policy conflicts. Changing only an included
file or an effective child-environment input with retained caches must establish
the actual refusal or rebuild, without publishing a secret canary or PATH.

For freshness, pair valid rebuilt/reused messages with missing, null, numeric,
string and contradictory judgments. Verify fresh mode refuses every unknown
case before assembly. Constructed messages test the reader; a real retained-cache
build establishes Cargo's actual judgment and compilation receipts. A wrapper
that only supplies the collector's expected answer cannot be the independent
oracle for selection.

## 4. Validate the complete record and capture effective settings

**Defect.** `record_problems` accepts `null` for `source`, `toolchain`,
`configuration` and `signing` as long as their keys exist. It compares UUID,
platform, minimum and SDK but ignores recorded linker-tool versions. Review
also found `configuration.deployment_target: null` in the accepted app despite
the enforced minimum of 26.0: the session snapshots the environment before
selection is finished. A caller's `SDKROOT` is captured only on the build path
without an inherited lock claim.
The system Python shim also inserts `SDKROOT` when the caller left it unset,
as confirmed by a review probe. A Python owner cannot reconstruct that original
absence from its environment, even if session capture is moved later.

**Repair.** Define one typed validator for the documented record, used by
production before sealing, artifact inspection and release-archive reading.
Validate required nested fields, exact booleans and integers, bounded strings
and collections, conditional full/partial-build fields, observation statuses
and allowed unknowns. A present null is not a required observation. Keep the
controller hash exclusion and the distinction between nested signatures and
the outer seal. Compare every claimed load-command field, including linker
tools, with independently read bytes; validate signature claims against the
existing independently obtained signature observations.

Preserve the existing field meanings and schema version where these are
validation and capture corrections. Document any necessary additive selection
details and update every reader and fixture together. Do not quietly redefine
a field to make an invalid old record pass. Unknown optional observations remain
explicit and never establish compatibility.

Migrate the independent fixture records with the validator:
[dispatcher bundles](tests/fixtures/dispatcher/fixture_bundle.py) currently use
nominal `source`, `toolchain` and `configuration` sections and a `fixture` Cargo
status, while [release publish controls](tests/suites/preflight/check_release_publish.py)
use empty sections and outputs. Give them independently authored valid record
data and corresponding signature observations; do not add production exceptions
for fixture records or generate expected validity with the producer under test.
Update the disposable-repository copy lists, including
[repository.py](tests/fixtures/dispatcher/repository.py), to carry the shared
lock implementation, shell entrypoint, validator and vendored parser dependencies.

Capture caller requests before launcher/interpreter environment changes, for
both direct and nested entrypoints. Add `tests/lib/checkout_lock.sh` as the
supported command launcher: shell builtins capture the allowlisted requests,
including SDKROOT's set/unset state and exact supplied value, before executing
`/usr/bin/python3`. Direct `build.sh` entry delegates through this front end
before starting Python. Carry that snapshot in memory/environment until the
owner binds it to the acquisition; do not write a request file before lock and
path admission. Nested builds consume the owner's saved requests through the verified
handoff, rather than reclassifying the Python shim's environment as caller input.
Python callers of the owned scope must supply an explicitly preserved request
snapshot when launching a build. A build reached through a Python-only launcher
without that snapshot refuses before session/cache writes and names the shell
entrypoint as the remedy; ownership-only commands need no build-request snapshot.
Update the public commands and working guidance with this entrypoint contract.

Capture effective deployment target, SDK selection and compiler inputs after
the script's selection and Cargo's relevant `[env]` transformations have been
resolved. A post-export shell snapshot alone cannot establish Cargo's child
environment. Record requests separately from effects where both are needed.
The effective deployment target must agree with build policy and the binaries'
load commands; the selected SDK must agree with the toolchain observation and
output checks.

**Acceptance.** Mutate each required section and representative nested fields
to missing, null and wrong types, and change only a linker-tool version in an
otherwise valid record. The producer, inspector and archive reader must reject
the applicable faults. Keep a valid neighbour for full and partial builds and
for each permitted optional unknown. Signed-copy controls must refresh the
manifest and signatures when necessary so the semantic validator, rather than
an earlier stale-hash failure, is what rejects the bad record.

Build with default settings and explicit `SDKROOT`, directly and through the
shell lock launcher into `build.sh`, including another nested owned command.
Distinguish an absent request from an explicit request for the default SDK;
retain an explicitly empty value in the request record, with effective selection
following the documented SDK policy. An invalid explicit request must refuse
without silently selecting the shim's default. A Python-only build launch
without preserved requests must refuse, and a valid supplied snapshot must
succeed. Include Cargo `[env]` overrides from section 3. Independently inspect
selected tool commands, the final environment supplied to compilation and the
resulting Mach-O metadata. The published effective settings must agree. Preserve
manifest/output hash checks, A/B record-swap refusal and release ZIP binding
without executing the inspected app.

## 5. Enforce probe bounds while the tool runs

**Defect.** `probe` writes stdout and stderr to temporary files until process
completion. Only afterward does it check stdout size; stderr has no cap.
A review probe emitting 8,192 stderr bytes with a 64-byte limit returned success.
Some comparison identities and effective flags are also silently truncated.

**Repair.** Drain both streams concurrently with live byte limits and a fixed
deadline. Bound stored output as it arrives. Overflow on either stream is a
failed observation even if the tool exits zero. Terminate the probe process
group on overflow or deadline, reap the direct child and independently observe
that fixture descendants are gone. Bound cleanup as well as execution; report
cleanup failure rather than waiting indefinitely or claiming success.

Handle a leader that exits while a descendant retains an output pipe. Do not
let early leader exit bypass stream limits or process cleanup. Keep failure
entries limited to structured kinds, status and counts, without raw stderr.
Comparison inputs must be complete within their declared bounds: oversized
compiler commands, identities or effective flag lists become explicit failed
or unavailable observations, not truncated values that compare equal.

**Acceptance.** Add stdout and stderr overflow, both streams active, exact-limit
success, nonzero exit, empty/malformed output, timeout, ignored termination and
an orphaned pipe writer. Observe bounded completion, retained bytes and child
exit from outside the probe. Long identities differing only after the former
truncation boundary must not compare equal. Preserve secret-canary controls and
prove that a required failed observation refuses compatibility and publication.

## Portable SDK controls and classifier notes

Restore the core build guards to one installed SDK. Produce a tiny Mach-O
through the real linker with a deliberately different `LC_BUILD_VERSION` SDK
value using `-platform_version`, keeping the minimum valid. A review experiment
with the selected SDK 27.0 and `-Wl,-platform_version,macos,26.0,28.0` produced
minimum 26.0 and SDK 28.0 without modifying an existing binary's headers.
Select a distinct value from the observed SDK and verify the fixture's load
commands before substitution. Credit this as a controlled metadata mismatch,
not evidence of compilation against a second SDK.

Keep malformed `otool` text controls for parsing, real wrong-SDK build refusal
for one and all outputs, and the separate two-toolchain switch case for actual
selection changes. Update the catalog, opt-in registry and suite documentation
so core guard/refusal cases do not inherit a second-SDK requirement. Missing
equipment in the genuine switch case remains an equipment failure.

The original record reports three withheld classifier responses but contains
no raw decisions from which to diagnose their exact causes. Preserve that limit.
Correct its fixture description to the established historical SDK:
`/Library/Developer/CommandLineTools/SDKs/MacOSX15.4.sdk`, not 26.5. The retained
receipt is `tests/out/runs/provenance-acceptance-optin-20261016-credited/suites/preflight/build_guard_controls/artifacts/compile-wrong-sdk/command.json`;
its successful command names that SDK with `-isysroot` and minimum 26.0, and
the same run's `artifacts/equipment.json` records other SDK version 15.4 versus
selected SDK 27.0. Preserve those historical receipts and describe the new
single-SDK metadata fixture separately. New controls need no Mach-O header
patching.

## Documentation and final acceptance

Keep [docs/build.json](docs/build.json), the scripts and refusal controls aligned
within each increment; regenerate with `docs/generate_build.py`. Review the
generated step order, reads/writes, invocations, refusals and figure together
with the authored sections of [BUILD.md](docs/BUILD.md). In particular, early
path admission must precede every session/cache write in both accounts, and
nested ownership, caller-request capture, Cargo configuration includes and child
environment resolution, and probe bounds must mean the same thing
in generated tables and surrounding prose.

[SIGNING.md](docs/SIGNING.md#the-provenance-record) owns the published record's
shape and limits. Update it with the validator and producers. Update
[tests/README.md](tests/README.md#retention-ownership-and-execution-locking), the
preflight and dispatcher suite references, fixtures, catalog and opt-in registry
with the actual ownership protocol, controls and equipment. Change working
guidance where commands or contributor obligations change. Regenerate worker
identity after final identity-input changes. Keep the refusal baseline empty;
do not freeze the old refusal count if the repaired boundaries require changes.

Final acceptance requires the targeted controls above, `source_drift`, dispatcher
and preflight coverage, a fresh signed full build, the default battery, managed
`cargo test`, release preflight, and these existing opt-in cases:

- `preflight/signed_artifact_controls`
- `preflight/build_guard_controls`
- `preflight/build_refusal_controls`
- `preflight/build_toolchain_switch_controls`

Use the repaired full/partial controls to establish both build variants. Run
against a clean commit containing the final implementation and controls, with
the acceptance app's record reporting `dirty: false`. Identify that tested
snapshot and app identity rather than attributing a run to the later report
commit. Retain commands, tool receipts, refusals and state transitions. A fixture
failure is not a credited production refusal. Follow the repository's sandbox
retry guidance for environmental failures without changing the artifact.

Append a repair section to the existing acceptance record and qualify its
original closure claim. Preserve original runs and explicitly identify replacement
credits. Record the five repaired boundaries, their reproducing controls,
implementation/tested commits, run IDs, worker identity, updated refusal count,
remaining limitations and a documentation walkthrough tracing one valid build
and each changed refusal through the manifest, authored prose and evidence.
Retain new evidence through the normal index and ownership helpers. Keep the
worker clock finding open under its own plan; a passing rerun does not resolve it.
If it recurs, retain and identify that failure separately from these repairs;
do not credit a failed battery as passing or suppress the case for acceptance.

Completion requires those repairs and gates, with the durable behavior and
operating guidance in their owning files. The report may then close this plan
without losing the explanation or evidence needed to maintain the result.
