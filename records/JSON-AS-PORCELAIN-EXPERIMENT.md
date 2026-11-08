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

The authoritative field inventory, primitive sizes and evidence selections are
reported below after final verification. Line counts are inventory, not a proof
of maintainability; review triggers count normal formatting, not compressed code.

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

## Verification and dispositions

Final verification and claim dispositions are being assembled from retained runs.
The implementation is isolated on `experiment/json-porcelain`; it is not merged
into the main checkout. Main-checkout user edits remain untouched.
