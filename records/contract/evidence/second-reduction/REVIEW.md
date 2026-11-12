# Independent presentation review

Compared with committed baseline `6f65612b`. The reviewer inspected the
renderer delta, generated document and amended presentation controls, without
editing their implementation or executing the product, build or test battery.

Reviewed final identities (SHA-256):

- `docs/contract/tree.py`:
  `a69fa53367d9008bf9cb12a486fca774dc45cb3d98e359d0e0da0ce0ec1e5a8e`
- Renderer body, before the runtime adds stamp-table content and document markers:
  `448f9614258dddc301af5d121a3d90a8866fc64596007c94c0e207a6a1f9029e`
- Generated `docs/CONTRACT.md`:
  `4d8e40e1d7a4fba1df60b8f12a7d28fdebd1bd80ad08564af83db2eca6e304d7`

## Preservation findings

No remaining preservation defect was found within the scope below.
Mechanical comparison established that all nineteen canonical public payloads
remain equal. Every one of the 1,004 fields retains its complete authored
meaning and unique original anchor. All 145 support paragraphs are
byte-identical. Original anchor order remains intact; only the notation anchor
is added. All twenty first-match tables, 64 condition/effect tables, four
variant tables, sixteen examples and seven gaps remain. The vendored
CommonMark parser recognizes exactly 1,004 separate top-level field entries.

Direct comparative readings covered compiled-profile fields and checks;
envelope fields, completion and refusal precedence; actor termination gates;
helper admission cases; ordinary and actor ending mappings; and reply-wide
withholding and retention. These retain production versus interpretation,
separate entry points, complete operands and quantifiers, first-match ordering,
and worker-local versus reply-wide consequences. The gate still distinguishes
unreached evaluation, failed evaluation and later retained termination
observations.

Every exceptional presence family was inspected: conditional-null fields,
`same_as_input` omission, required nullable input and omission when empty.
Their qualifications remain explicit. Compact suffixes apply to the whole
field; the reading key distinguishes omitted keys, nulls and false values.
Expression function roles are defined, and grouped effects remain distinct
from assigning an empty array. Existing controls retain their operand, scope,
rejection and ordering assertions while changing expected presentation. New
controls cover field meanings, serialization exceptions, nested obligations,
grouping and notation coverage. Their execution was not part of this review.

One new wording risk was identified and corrected: “when available” could
imply emission of a known but intentionally withheld value. The final legend
describes omission representationally instead. The reviewer checked that
correction against the previously reviewed body.

## Declined prototypes and limits

The companion-reference prototype retained the examined meanings but left
several “below” references pointing toward rules on another page. Its split
improved the main behavior sequence while relocating about 31,000 words and
adding navigation overhead. The final single-document form avoids those
cross-document repairs. Local path abbreviations offered limited size benefit
for their additional interpretation burden and were also abandoned. Temporary
prototype files were local investigative material, not retained release
evidence.

This was a representation review with exhaustive mechanical field/support
comparisons and selected direct semantic readings, not a new uninterrupted
reading of every unchanged paragraph. It establishes no fresh product
behavior, native observation or release-execution evidence. Size reporting
must distinguish removed Markdown scaffolding from compressed reader-facing
text; neither represents eliminated contractual facts.
