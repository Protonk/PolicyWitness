# JSON as porcelain experiment

## Frozen question and baseline

Source baseline: `76de8ca3`, with the revised JSON-AS-PORCELAIN plan supplied on
2026-11-08. Prototype branch: `experiment/json-porcelain`; isolated worktree:
`/private/tmp/pw-json-porcelain`. HOST-04 has not begun on this baseline. Do not
combine later host changes into this experiment without recording a new baseline.
The main checkout has unrelated FOOTPRINT edits; they are outside this experiment.

The user's primary criterion is maintenance: typed storage, explicit field access
and validation should replace generic parsing, not recreate it through string
conversion adapters. Flat or modestly worse performance can be acceptable.

## Model and codec decision, before implementation

Select Option A: a repository-owned, bounded tagged binary format and schema
generator. Option B (SwiftProtobuf/prost) remains the alternative if the primitive
layer exceeds 400 authored lines per language, the generator exceeds 900 authored
lines, or ordinary record changes need a general codec or string conversion
framework. These are review triggers, not goals to satisfy by compressing code.
Both alternatives still need typed admission and independent semantic controls.

The schema owns stable record/field tags, field names, integer widths/sign,
optionality, list/map shape and public presence rules. Generate Swift stored-field
regions and direct writers, Rust owned typed records/readers and JSON serialization,
and Python structural tables. Preserve native evidence strings as strings; use
bytes for transport payloads. No generic value tree, reflection or stringify/parse
adapter may mediate the converted result path. Request JSON and validator NDJSON
remain outside the experiment.

Draft record closure: reply summary/reporting failure; phases/ordering/comparison;
steps/attempts; validator records/association faults; worker evidence/subprocess;
disposition claims/issues; actors/launch/visits/owned reap; transfers/resources and
the supporting actor setup records actually read by the slice. Equipment property
lists and unexercised input echoes may remain explicitly opaque. Recount source
records/fields before freezing generated coverage. The maintenance ceiling remains
approximately 150 records for full coverage, with no invented per-field classes.

Wire draft: fixed magic and schema fingerprint, root record identity, bounded
length-delimited records and fields; fixed-width little-endian signed/unsigned
integers, strict booleans/UTF-8, bytes, optional absence, homogeneous lists and
ordered unique map entries. No native memory layout or pointers. Reject duplicate
or unknown tags/records, wrong kind, missing required fields, invalid UTF-8,
overflow, short/trailing data and excessive depth before semantic claims. Size and
count checks precede allocations; raw rejected input remains available.

Own raw received bytes once per capture; decoded typed records own their strings
and collections. This intentionally allows a raw receipt and an immutable decoded
interpretation to coexist; it makes no zero-copy claim. Presentation borrows typed
records. A later view-based design is unnecessary to answer this experiment.

Extract producer semantic gates from JSON encoding into explicit typed validation,
including encoder-only ordering, disposition, association and fresh-read checks.
Observation storage must still represent conflicts. Rich degradation retains facts
and withdraws comparisons; minimal reporting stays independent. Rust admission
uses direct typed fields and named associations; generated Python tables describe
structure, while authored semantic controls remain independent.

## Necessary corrections to the proposed prototype boundary

The existing Python transport reader interprets retained host bytes as JSON.
Keeping it unchanged would require falsely relabelling regenerated JSON as received
bytes. Preserve the public semantic reply shape, version the binary raw-capture
interpretation, and adapt the independent transport reader. Keep semantic assertions
unchanged where their meanings remain unchanged. This is a transport reader change,
not a reception cutoff or rewrite of observations.

Actor coherence reads setup/application/equipment support. Include the supporting
typed closure actually needed, or explicitly withhold unconverted claims; never
parse opaque JSON to feed the old generic-tree validator and call it typed admission.

Client framing carries typed acquisition/submission observations and opaque host
bytes. Preserve single invocation, no replay, complete stdout/stderr collection and
post-collection retention caps. No receiver deadline/drain change or artifact bundle
is included. Final JSON serialization completes before output; output failure cannot
guarantee another envelope. The XPC payload remains whole Data.

## Falsifiable claims and controls

| Claim | Refuting control |
| --- | --- |
| The schema owns converted record structure. | Add a field/change its kind; regenerate only one language; stale copies and mismatched fingerprints must be refused. Count authored edits for a complete change. |
| Converted Rust coherence uses typed access. | Source audit for Value/reflection/string field lookup or encode/parse adapters; malformed kinds cannot enter typed storage. |
| Supported order has a validation owner. | Remove collection closure/acknowledgement, change actor/phase/PID association, add a future ordinal/late validator record; withhold unsupported claims while retaining facts. |
| Ending observations remain separate. | Successful signal with unconfirmed reap, partial and conflicting evidence; no requested action becomes an observed ending. |
| Degradation preserves evidence honestly. | Force integrity, rich encoder, minimal reporting and emission failures; compare retained facts and outer failure observations. |
| Raw capture and typed storage have clear owners. | Preserve arbitrary/NUL bytes; discard temporaries; audit lifetimes and copies without claiming XPC physical sharing. |
| JSON is presentation. | Independent reader compares admitted facts with public projection; key order cannot grant eligibility. |

Independently authored bytes exercise duplicate/unknown tags, exact integer bounds,
missing/false/zero, malformed lengths, invalid text, trailing bytes, combined faults
and interrupted emission. Do not generate all expected outcomes from the same
schema or production validator.

## Verification and maintenance experiment

Prove the generator on a small record set, then run signed ordinary multi-phase
order and actor/ending slices with independent file/process observations. Register
codec/generator controls through the dispatcher. Run affected Rust/Swift controls,
source/ABI checks, independent consumers, validator failure/association and the
order-barrier mutation control. Full-family adoption remains subsequent work.
Builds and native trials are serialized; compiler concurrency is capped at two.

Measure record coverage, primitive/generator size, generated lines per record, and
a field addition, field-kind change and semantic-rule change. Record remaining
manual validators and unconverted representations. Audit conversions: native
integer/boolean/reference values stay typed until public formatting. Give each
claim established/refuted/unestablished status.

Representative small, query-dense, byte-heavy, actor and failure cases establish
cost scope. Retain size/lifetime/copy counts and per-process observations available
from the apparatus. No speed or energy improvement claim is planned; any later
quantitative claim needs a separately frozen matched schedule and arranged quiet
conditions. Unknown measurements remain unknown.

## Codec disposition

Keep Option A for adoption work: the measured maintenance inventory remains below
both review triggers, and the generator expresses this closed record vocabulary
without a general value tree. Option B was reviewed, not built or benchmarked;
its dependency and generation setup would still leave per-family semantic
admission and public projection to this repository. This is a scope and ownership
decision, not a comparative performance result.

The plan's initial claim that both Protobuf runtimes preserve unknown fields was
too broad. SwiftProtobuf's [decoding options](https://github.com/apple/swift-protobuf/blob/main/Sources/SwiftProtobuf/BinaryDecodingOptions.swift)
retain unknown fields by default; prost's [generated message reader](https://github.com/tokio-rs/prost/blob/master/prost-derive/src/lib.rs)
skips unrecognized tags. These primary sources were inspected on 2026-11-08.
Either choice still needs an explicit unknown/default admission policy here.
A primitive/generator budget overrun or ordinary fields requiring general parsing
would reopen Option B; neither occurred in the demonstrated slice.

## Implemented representation and ownership

The prototype chooses the repository-owned codec. The schema closes over 83
records: 81 Swift source records and two fixed lifecycle-question adapters. Its
606 stored-field entries produce 605 wire fields; the host-local exec decode
problem is deliberately excluded. This is below the approximate 150-record
budget even though the closure includes supporting actor records whose semantic
admission is not yet migrated. Existing hex/digest evidence stays text. Client
host payloads become Data/Vec<u8>, with base64 only at the public JSON boundary.

The exact format is `PWP1`, a 32-byte schema fingerprint and one TLV root. TLVs
carry kind:u8, length:u32LE and payload; records carry identity:u16 and ascending
nonzero tag:u16/value pairs. Signed/unsigned integers occupy eight bytes with
native-width range checks; bool accepts only 0/1. Lists and ordered unique UTF-8
maps carry u32 counts, and the one declared claim-value variant carries a u16
case. Unknown tags, record identities, cases and fingerprints refuse admission.
Absence is distinct from zero/false. Limits are 128 MiB per frame, depth 32 and
128 MiB of charged decoded slots/strings/bytes per Rust frame. These are logical
bounds, not measured peak memory. Schema prose/source-location changes do not
change the wire fingerprint; structural and projection changes do.

| Process/boundary | Owner, overlap and release |
| --- | --- |
| Host | Typed observed records survive validation and writing. Each nested writer creates Data; ancestors append those bytes. Returned whole Data goes to XPC. There is no borrowed or streaming writer claim. |
| XPC | Foundation/process copying and physical backing identity are unestablished. |
| Client | Received Data, retained prefix and encoded capture Data can overlap. The capture contains opaque bytes, not a decoded host model. It writes one binary frame without a newline. |
| Controller collection | Existing full stdout/stderr collection remains; the retention cap applies afterwards. Decoding borrows the collection while constructing owned fields; rejected retained bytes are copied into an exact-byte carrier. |
| Controller interpretation | Accepted capture owns raw host bytes; the decoded reply separately owns its fields. Raw observation and interpreted model intentionally coexist. No generic response Value, base64 decode or stringify/parse adapter mediates coherence. |
| Public output | A borrowed envelope serializes typed records into one complete String. Base64 temporaries exist for public byte fields. Printing can fail after a prefix; that prefix is not a complete artifact. |

Generated Rust JSON Deserialize implementations, the path-compression fixture
marker and the legacy generic readers are test-only. Request JSON, dossier
construction, reservation control JSON and validator NDJSON remain separate
adapters. Swift's old response Codable implementations remain comparison code;
removing them is adoption work. Equipment metadata's existing JSON-size check
and Swift's string-keyed lifecycle-question construction are explicit remaining
representation dependencies, not credited as JSON-free admission.

## Semantic boundary

Swift reporting validation now runs before the binary writer. It includes the
former encoder-only gates and root/actor compiled-profile context. The rich
failure writer preserves observations and removes comparisons; the independent
minimal writer reports evidence loss and original summary. Total emission failure
can yield no decodable reply; outer observations must carry the failure.

Rust admits the ordinary publication/order and lifecycle slice through direct
fields, including association, collection closure, acknowledgement, native PID,
phase ordinal, policy receipt and witness-basis checks. Partial publication,
requested signal, actual status and owned reap remain distinct. Supporting actor
records are typed and cross-actor references can be challenged, but full actor
setup/equipment, activation/reap gates, authority settlement and fresh-I/O/exec
semantic families remain `unconverted_scope`. Scope alone yields integrity
`unestablished` and withholds the aggregate; contradictions yield `invalid`.
Independent per-actor observations survive both. No opaque JSON is reconstructed
to feed the old production validator.

The typed model does not make arbitrary observation construction impossible.
Raw structs can represent conflicts; named admission controls eligibility. A
schema/generator cannot replace the independently authored Swift, Rust and Python
semantic rules. Neither PID fields nor carried timestamps establish an independent
process generation or a genuinely late validator arrival; native ordering controls
remain necessary.

## Maintenance exercises and cost scope

The inventory at implementation commit `72c7356f` is 342 generator lines,
126 Swift primitive lines and 323 Rust primitive/projection lines before unit
tests (including test-only fixture ingestion helpers). Generated outputs contain
1,970 Swift writer lines, 5,081 Rust record/reader/projection lines, and 55,839
bytes of Python tables. Typed Rust admission occupies 1,545 authored lines before
tests; its manual semantic work is the largest new maintenance cost. Line counts
are inventory, not proof of maintainability. The normal Rust formatter is used;
the frozen 400/900 review triggers are not whitespace targets.

There are still 249 direct String/optional-String fields plus string collections.
Open native codes and evidence text stay representable; closed claim states,
answers and witness-reference vocabularies still use named string matches.
They do not pass through new text parsers, but fixed enums are a useful bounded
adoption refinement. Swift lifecycle dictionaries are the more concrete remaining
structural debt: their generated adapters reject unknown keys, while construction
and validation still use those keys.

| Change exercise | Observed edit path |
| --- | --- |
| Add optional reporting diagnostic | One schema entry changes its Swift stored-field region and three whole generated files. No primitive edit or build-source addition. A useful value also requires a producer assignment and populated independent fixture; explicit Rust test literals must acknowledge the new field. |
| Widen progress raw UInt32 to UInt64 | One schema kind change generates the same owners; native construction and semantic progress checks require deliberate numeric edits. Wire integers stay eight bytes. No text conversion is needed. This was an in-memory generation/edit-site exercise, not an executed widened native protocol. |
| Change final-status witness rule | Swift dispositionBasisSufficient, Rust sufficient/validate_lifecycle and Python lifecycle_oracle.sufficient_basis remain independent owners. A paired typed control removes or substitutes a resolvable witness reference and requires withholding while preserving native facts. No schema or codec change supplies semantic acceptance. |
| Change a field comment | Only the owning documented Swift field region changes; all generated wire fingerprints remain identical. |
| Regenerate only one side | Added/dropped fields, renumbered tags, changed kinds and an added record make the unchanged side stale. Drift refusal precedes replacement; independently authored malformed bytes challenge the actual readers. |

The representation removes generic response trees and internal base64 text, but
retains raw bytes plus decoded ownership, nested Swift Data copies and a complete
public JSON String. It establishes no zero-copy or peak-memory reduction. Existing
FOOTPRINT JSON-control samples are explicitly unavailable as prototype cost
evidence. Current receipts describe byte sizes and whole-request wall duration;
parser-stage CPU, per-process physical memory, energy and comparative speed remain
unestablished. No performance superiority claim or matched statistical comparison
is made. Flat or modestly worse performance remains acceptable under the user's
maintenance criterion, subject to bounded costs and preserved evidence.

### Descriptive execution receipts

These are individual executions from the final signed run, with no matched
baseline, quiet-window arrangement, first-execution exclusion or statistical
performance inference. Bytes are observed byte counts, not memory residency;
wall duration is through CLI exit. The actor row retains the explicit semantic
scope withholding described above.

| Workload | Host binary bytes | Client capture bytes | Public JSON bytes | Whole CLI wall ms |
| --- | ---: | ---: | ---: | ---: |
| Ordinary, three phases/actions | 7,652 | 8,278 | 34,647 | 47.817 |
| Query dense, eight phases/256 actions | 404,902 | 405,528 | 1,579,767 | 139.490 |
| Actor composition, ten visits/actions | 62,728 | 63,354 | 255,771 | 83.092 |
| Partial validator EOF | 8,214 | 8,840 | 35,346 | 259.897 |
| Worker death before result publication | 7,237 | 7,863 | 32,780 | 84.212 |

The raw `run.json` and `capture.json` pairs are in the final run's
`witness_contract/phases/artifacts/ordinary`,
`witness_contract/porcelain_output_controls/artifacts/complete`,
`witness_contract/actor_compositions/artifacts/original`,
`runner_validator_failure/validator_unavailable_reports_degraded/artifacts`,
and `witness_contract/worker_killed_before_slot_publication/artifacts/killed_before_publication`
under `suites/`. The dense case also retains the exact host frame and a size
receipt. It is not a comparison between equally encoded artifacts.

The large-byte control is constructed, not live execution coverage:
ReservationAdmissionTests exercises retained host payloads one byte below, at
and above 92 MiB, and encodes a field-superset binary capture carrying the full
retained payload. It passes the writer/frame/output bounds. It does not measure
peak allocation or prove full semantic admission of that deliberately inconsistent
superset. Full maximal typed-reply semantic coverage belongs to adoption.

## Verification and dispositions

Implementation commit: `72c7356f`. Signed build command:
`env CARGO_BUILD_JOBS=2 make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)'`.
Worker identity: `242eaaf85726e7437de516e895dec198cdfddaeb669fd1ed31f7f31a7855ef84`.
Wire fingerprint: `d9075e30119a1effc04f3813f9e748d1aceb62037aceede04b3a00ab37a33f6f`.
The build uses inspection Swift flags with explicit one-job Swift drivers and
at most two Meson/Cargo jobs. Native executions remain serialized. The build
is signed and staged locally, not notarized or published.

Final coordinated verification **passes all 41 selected cases**, with zero
failures, skips, unrun cases, harness errors or observed system-sleep overlap.
The inspected signed app is valid and unchanged across the run. Rust checks
include 237 controller unit tests and 57 helper tests; the three receipt-dependent
ignored controller cases run explicitly in the Swift wrapper. All 590 Swift
controls and its independent receipt replays pass.

Final coordinated verification is recorded in `tests/out/runs/porcelain-acceptance-a`
(run ID `20261108T200617Z_d5eb9abd`).
Its `plan.json` records the complete selection and requirements; raw artifacts
and `run.json` own outcomes. Source is the implementation commit with the new
output-control wrapper's executable bit corrected before dispatch. Later record,
plan and retention edits do not change the tested implementation. Earlier failed
runs remain failures; their replacement and applicability are accounted below.

The registered selection comprises `source_drift`, `unit`, `failure_boundaries`,
`runner_validator_failure`, `runner_abi_layout`; preflight signing/build-entry;
Swift core/client controls; five C-worker publication/release/activation cases;
and ordinary phases, actor compositions, deadline/partial-publication, native
order mutations and actual output interruption. Exact IDs, commands, equipment
and configuration remain in the retained `plan.json` and `run.json`.

The native order mutation case accepts its baseline and rejects both worker and
host bypasses through independent effects. Normal/rich/minimal binary reporting
receipts match independent Python projection; 30 truncated prefixes refuse.
Actual public-pipe closes at 128 and 4096 bytes return exit 101 with incomplete
JSON and no harness timeout/cleanup kill; no complete artifact or worker claim
is inferred from those prefixes.

Corrections are preserved rather than credited retroactively: the first signed
partial-publication trial found a real Rust progress-order indexing error, now
fixed with a typed regression and the passing signed rerun. Initial Rust/Swift
fixtures needed version/required-field updates; an old JSON comparison replay
needed explicit fixture admission. Source checks caught an overbroad source-list
mutation and invalid documentation links/literal duplication. The independent
reader was extended to validate exact rejected-frame carriers and unsupported
fingerprints without recovering submission claims. No semantics were weakened
to make those failures pass.

`exploration-prior/index.json` inside the final run identifies 254 copied files
with original paths, run IDs and SHA-256 values, including contrary raw replies,
failed logs, original run accounting and build logs. Early uncommitted source
snapshots are not assigned a commit. These copies do not relocate cleanup
ownership. Superseded originals were removed only through the ordinary pruner
after preservation. The final run is pinned for adoption; its raw evidence is
gitignored and available only in this local worktree.

| Frozen claim | Disposition and limit |
| --- | --- |
| Schema owns converted structure | Established for the 83-record closure by generated stored fields/readers/tables, single-side mutation controls and stale-copy refusals. Custom semantic rules are not generated. |
| Converted Rust coherence uses typed access | Established in the selected slice. Production response records have no JSON Deserialize path, generic Value adapter or string conversion intermediary. Declared unconverted families are withheld. |
| Supported order has a validation owner | Established for the ordinary/actor query slice through typed rejection controls and native ordering checks. These do not create a new generation or arrival-time observation. |
| Ending observations remain separate | Established for worker completion, partial publication and constructed kill/reap conflicts. Full exec and actor settlement admission remains outside the slice. |
| Degradation preserves evidence honestly | Established for normal, rich, minimal and total emission-failure controls, with independent binary receipts. Allocation failure cannot guarantee self-reporting. |
| Raw capture and typed storage have clear owners | Established as source/API ownership and exact-byte retention. Physical Foundation/XPC sharing and peak allocations remain unestablished. |
| JSON is presentation | Established on the converted response coherence path. Equipment size validation and old comparison coders remain explicit exceptions; universal JSON-free internals are unestablished. |

**Disposition: pursue adoption**, as a bounded follow-on. The gain is a single
structural owner and direct typed interpretation; it does not depend on faster
execution. The closed codec has not needed general parsing machinery, and no
new stringify/nudge/parse operation was introduced. Passing old generic controls
is not credited as proof of the new typed runtime.

Adoption still requires these concrete decisions/work:

1. Replace Swift lifecycle question dictionaries with fixed records; use enums
   for truly closed states/answer/reference vocabularies without closing open
   native codes. Preserve received conflicts independently of admitted claims.
2. Migrate one semantic family at a time, beginning with ordinary fresh-read
   admission, then fresh-write/exec and the actor setup/equipment/gates/settlement
   checks. Remove each scope marker only with independent accepted/rejected and
   signed controls. The existing record closure should suffice; expansion beyond
   the budget reopens the design.
3. Retire response Codable comparison paths and the generic test-only run bridge
   after replacing their coverage; resolve equipment's JSON-size admission and
   declare production codec limits in the owning limits account. Keep request,
   reservation and validator boundary formats explicit. Refresh resource
   observations on the completed path and run full-family/default acceptance.

No compatibility shim, production merge, performance recommendation, ARM trial,
wait tuning or custody redesign is included. The isolated branch and the evidence
remain dependencies of this adoption work, so the plan and record are retained.
Main-checkout user edits remain untouched.
