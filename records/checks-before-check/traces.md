# Representative edit paths

Source: `7562d24ac2334122499ea349010fd67211058ac3`. These are source traces
supported by identified historical controls, not fresh executions at this
revision. `trace-evidence.json` identifies16 controls from run
20261027T233059Z_1f7c68fa; their15 selected test/generator/helper files match
this source by hash. Catalog, README and other input differences prevent a
whole-checkout passing credit. Each trace separates identity, pointers,
actual assertions and the semantic judgment left to the author.

## T1 — shared question into a distributed guide

Editable example: the “Almost no one.” answer inside the SHARED QUESTIONS
markers in docs/QUESTIONS.md. Edit that source; use guide-local links in the
form required by docs/AGENTS. Run from root:

```
tests/lib/python.sh docs/generate_limits.py
tests/lib/python.sh docs/generate_limits.py --check
```

`generate_limits.main` loads limits/matrix, renders owned source spans and
tables in memory, reads QUESTIONS without rewriting it, demotes its headings
and converts guide references, then copies into PolicyWitness's COPIED QUESTIONS
region. It validates the prospective guide's regions, headings, mandatory
rows, standalone references and anchors before writing anything. Only declared
regions/spans change; author text outside those regions remains authored.
The question text is shared authority for the copy, not factual authority for
claims about the program.

Accepted/invalid/restoration controls: limits.py's current-document assertion;
`test_generation_updates_values_and_shared_prose_then_is_idempotent` changes
that answer to “Almost nobody.”, asserts it in the guide, preserves QUESTIONS,
checks other content and repeated generation; `test_question_links_must_target_the_guide_and_resolve`
rejects invalid source links. The stale/staging control first uses current
inputs, then introduces stale/broken documents, requires failure and unchanged
source/destination bytes, and restores inputs. Historical controls passed;
none establishes that a newly authored answer is true.

`source_drift/limits_documentation` owns those default controls.
`source_drift/generator_contract` separately checks G11 links across its21
selected documents; it is not called by limits.py. `build.sh` checks limits
before compilation and again stages through:

```
tests/lib/python.sh docs/generate_limits.py --stage-guide DESTINATION
```

Here DESTINATION denotes the chosen output path (normally
dist/PolicyWitness.md), not a command to execute in this investigation.
Staging refuses stale source, copies the checked guide bytes and does not
regenerate. The existing standalone control removes the source checkout and
validates the staged guide itself; use of its internal anchors needs no
repository companion. A user can correct a stale copy by regenerating the
source guide, then rerunning the owning check; a bad authored link must be
fixed in QUESTIONS first.

Bounded scope extension: follow the staged guide through
`release_archive.archive` and `release_publish.publish` to explain publication,
without inventorying release behavior generally. Archive requires the staged
guide beside the accepted ZIP, copies it into the release directory and hashes
the copy against its staged source; publication verifies archive checksums and
publishes guide/ZIP/checksums together. This establishes the copied bytes, not
independent semantic compatibility. No signing, upload or publication ran here.

## T2 — limits are descriptive; implementation values are elsewhere

Editable example: docs/limits.json `policy_source.value` describes262143 UTF-8
bytes; runtime storage comes from PW_SHM_POLICY_BYTES and admission code.
Changing just the manifest followed by `generate_limits.py` updates generated
LIMITS/guide values and registered limit scalar spans. It does not change the
C/Swift implementation. A generator-current document may therefore disagree
with compiled behavior.

The accepted/mutated/restored generator control above changes the value and
requires262144 in the generated sources/copies, then idempotence. The compiled
comparison is separately owned by runner_abi_layout/limits.py `compare` and
Swift LimitsContractTests; its own ABI mapping/subtraction expects the C
storage minus one for this limit. The C comparison deliberately mutates the
manifest value and requires rejection. `failure_boundaries/check.py admission`
has the separately cited at/over-limit/multibyte behavior. Those native/CLI
paths are source-traced here; D2 supplies no new runtime result for them.

For an independent boundary example the same limits.py's `query_boundary`
constructs fixed65534/65535 payloads and requires accepted/rejected/recovery
frames. It does not derive its expectation from limits.json. This distinction
prevents a manifest edit from silently changing every oracle.

For scalar-only example `probe_steps.value`, the registered limits span in
REQUEST-GRAMMAR is rendered from the manifest; G9 verifies the owned marker,
prefix and currency. Invalid/stale/unknown span and malformed-marker controls
are in generator_contract; prose outside registered spans is not automatically
an implementation-value check. A new literal may be a G9 baseline site or may
not match its bounded pattern. Manual numerical reasoning is still necessary.

Runtime limit changes require corresponding production edits and the broader
limit-change verification from tests/AGENTS. If a changed limit appears in
architecture placeholders, regenerate architecture too; limits generation does
not invoke it. Source review determines affected placeholders, not the mere
fact that both files live in docs/.

## T3 — graph/source/check relationships and figure publication

Editable example: docs/architecture.json documents graph node `drift_limits`
and edge D33. Current authored data wrongly attribute general local-doc-link
checking to limits.py, while their source pointer names generators.py.
Correct the manifest's account and pointers; never directly edit the rendered
ARCHITECTURE region, architecture-documents.dot or SVG.

The command is `tests/lib/python.sh docs/generate_architecture.py`, with
Graphviz available for actual SVG rendering; `--check` needs no Graphviz.
The loader validates schema, IDs, declared fact columns, registered destinations,
non-self source/check citations, check forms and limit placeholders. Source
symbols are presence checks; check forms add definition/registration conventions.
It does not adjudicate D33's alleged support, so the wrong account can pass.

The writer renders document regions/spans and every changed figure into
pending memory before publishing. `--skip-svg` changes dot/text and leaves
SVGs alone; it is not a complete freshness repair when their dot stamps differ.
Check compares exact dot and region bytes plus SVG's dot-hash stamp, not every
SVG pixel. All output destinations must be registered before authoring a graph
there; an arbitrary document link does not register one.

Accepted/invalid/restoration: architecture.py checks current documents/figures,
then independently damages dot, SVG stamp and region text; `--check` must fail
with stale/stamp/region diagnostics and leave the mutation untouched. Regeneration
without SVG restores text; check still rejects the stale SVG; restoring/rendering
it passes and a second generation writes nothing. Broken citations/markers
refuse before writes. `generator_contract`'s last-graph render refusal requires
the entire fixture snapshot unchanged. Historical receipts cover these controls.
These are validation/render failure guarantees, not a filesystem transaction
across arbitrary I/O failures or multiple generator commands.

`source_drift/architecture_documentation` and generator_contract are default;
build.sh invokes architecture currency before compilation. A correct reference
and current generated copy still leave assertion adequacy to human review.

## T4 — a version manifest defines constants consumed by code

Editable example: docs/contract.json `versions.response_schema` (23 at this
source). Author the contract decision there; run:

```
tests/lib/python.sh docs/generate_contract.py
tests/lib/python.sh docs/generate_worker_identity.py
```

The first command validates the manifest and all seven targets before writing
their owned regions: PWRunnerAPI's PWContract, Rust json_contract constants,
test contract constants, CONTRACT/PolicyWitness and controller/runner README
prose. The C ABI header is not a contract-version target. The second command is
needed because changed Swift API source belongs to the host/worker identity
inputs; it updates ABI/CWorker/test-reader identity regions, excluding those
regions from their own digest. The two generators share tests/lib/contract.py
through separate markers. A version bump alone is not a compatibility design
or proof of correct handling of unsupported versions.

`contract_versions` checks every generated copy. Its mutation control requires
the named stale-copy diagnostic, no check writes, then full restoration by
generation; missing/duplicate/reversed markers refuse before any write.
Worker-identity controls run in build_documentation and check relocation,
determinism, source discovery, handshake inputs and stale identity restoration.
Build checks both currency gates before compiling and identity again before
signing. Version-generated code equality is intentional single-source authority;
separate admission/consumer tests establish behavior. They are not replaced by
a shared generated value.

If generation is interrupted after contract output but before identity refresh,
the next identity check refuses the stale copies. Repair by completing the owning
generation and inspecting the diff; no build auto-regenerates. Each generator
prevalidates its own input/output set, not the whole sequence.

## T5 — independently authored prose and an ordinary new document

Editable example: WORKER's dated launch-observation availability sentence,
outside generated regions. Editing only that prose does not regenerate the
worker graph or receipt. Its links are checked because WORKER is in the21-file
prose scan; its Known gap index and command forms have their separate checks.
The sentence can falsely claim a pin while every link resolves. The compact
receipt likewise contains an authored availability sentence; no checker compares
it to RETAINED. L's actual dated captures and current applicability remain
separate from both sentences.

For an ordinary new document under docs/, the existing glob includes it in
G9/G11, and command discovery includes visible Markdown automatically. A new
document elsewhere generally gains only command discovery unless already an
explicit generated target or selected path. Linking to it adds its bytes as a
fixture destination, not a recursive semantic/prose scan. Owned spans, graph
destinations and Known gap indexing require their specific declarations; no
future CHECK document is proposed or registered here.

Accepted/invalid controls in `test_prose_links_resolve_anchors_and_symbol_links`
use hand-authored valid local/duplicate-heading/code-symbol links, then missing
file/heading/symbol/reference-style inputs and accepted comment/code examples.
The exact diagnostic distinguishes rejection. A changed factual sentence with
the same valid link is outside that contract and can pass. Release preflight
adds only the explicit baseline-growth gate, not general semantic review.

## T6 — build account and release baseline

Edit docs/build.json when its descriptive account changes, keeping build.sh,
Meson and selected inventories aligned. `generate_build.py` textually checks
banners/order, refusal messages/statuses/steps, defaults, signing calls, helper
invocations and inventories, then renders BUILD's figure and six tables.
`build_documentation` executes the ten grounding rules; banner_order gates
the other nine. Syntax/semantic shell analysis beyond admitted forms is not
implied. Real preflight native/entry controls separately establish selected
refusals before protected operations.

Current/stale/restore controls in build.py require the same no-write/stamp
boundaries as T3. Generator_contract checks the before-signing placement of
all five currency commands. `release_preflight` compares both prose and build
baseline multisets with the prior annotated release; equal/subset accepted,
superset/rewritten rejected and first baseline explicitly labeled. Its matching
controls use constructed git histories. The release procedure currently names
only the prose baseline, an account omission localized in reconciliation.

## Cross-generator order and recovery

There is no global regeneration command or all-generator transaction.
The concrete dependencies are narrower:

- Contract-generated API edits precede identity regeneration. Production/build
  source edits may also require identity refresh.
- Limits generation renders its source values before copying shared sections
  within its single invocation. It reads manifest values directly; architecture
  also reads that manifest directly. Refresh both when a changed limit feeds
  both outputs; neither implicitly runs the other.
- Architecture/build share helper implementations, but generate different
  figures/regions. Their validation/currency may both need checking after a
  helper change; a shared file is not itself an ordering dependency.
- Several generators touch one Markdown/code file through disjoint regions or
  span prefixes. Inspect the combined diff. Per-generator idempotence does not
  prove arbitrary ordering, global atomicity or semantic correctness.
- A rendering/validation refusal is pre-write for its generator. Actual file
  writes are sequential; I/O failure or interruption after publication begins
  may leave a partial set. Rerun currency, repair owning inputs, regenerate and
  review. No rollback claim is made by the examined controls.

These are established constraints. None requires introducing a scheduler,
general claim registry, blanket reruns or a test-framework redesign.
