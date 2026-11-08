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

## Disposition

Pending implementation and controls. Choose pursue adoption, retain a narrower
result, revise one bounded assumption, or close without adoption. A working binary
codec alone is insufficient. Record source/build identities, exact test selections,
raw receipt locations, limitations and bounded migration work before completion.
