# Request lesson ownership (pass 1)

Scope: source/check-read mapping at `9eb81540`; no execution credit.
Actual dispatch model: `gpt-6.1-sol`, fresh context, confirmed by the coordinator.
Exposure: the teaching pair is a test-owned identity-free JSON corpus
rendered by repository Python, with separately authored shipped-guide shell inputs;
the app currently exposes one fixed read-hosts example, not this pair.

## Inputs and copies

- `tests/fixtures/request_contract/examples.json`: `create` and `capture_typo`
  own complete request templates (`specimen_id: request-grammar`, allow-default
  SBPL, step `create`, file-write-create path query and file/create attempt).
  `capture_typo` additionally owns the deliberate `capture_compiled_profiel` field.
  Both use `$EFFECT` in query and attempt; neither uses `$NONCE`.
- `tests/lib/request_examples.py::materialize` recursively substitutes exact
  scalar `$EFFECT`/`$NONCE` values, then `build_context.asserted_request` copies
  and inserts the selected candidate's `Contents/Info.plist` `PWContract`.
  Identity-free templates containing `contract` or `schema_version` are refused.
  CLI `--effect` is required; its help requests an absent absolute path but the
  renderer does not establish absence. CLI generates `secrets.token_hex(16)`;
  it prints JSON only, with no specimen execution. Other corpus cases also use
  assertion mutations, raw JSON and repetition recipes: do not silently move
  those test facilities into a user interface.
- `docs/REQUEST-GRAMMAR.md` invokes that renderer for both cases, then runs the
  CLI and checks external file presence/absence. It explicitly assigns the guide
  an alignment obligation; it does not contain a second literal pair of JSON
  templates. Its refusal table/prose repeats independently expected diagnostics.
- `docs/PolicyWitness.md` Quick start owns a literal create JSON heredoc:
  `guide-create`, `$PW_CONTRACT` from app `--version` via `plutil`, targets under
  a new `/private/tmp/pw-guide.XXXXXX` directory, umask 077. It guards existing
  targets, saves exit/envelope/stderr and observes file/stat independently.
  The refusal exercise edits that saved JSON using sed: changes target to
  `capture-target`, adds misspelled capture field, repairs spelling (missing
  nonce refusal), then inserts `/usr/bin/openssl rand -hex 16` nonce. This is
  a shell recipe copy of corpus semantics, not generated corpus content.
- Guide downstream examples reuse `create.json`, `guide-create`, target spelling
  and result paths (including BYOXPC sed transformation). Removing the literal
  heredoc requires updating these real consumers, not just two documentation
  paragraphs. Guide remains standalone in distribution; repository Python and
  corpus paths cannot become prerequisites for its commands.

## Independent expectations and actual consumers

- Corpus `expected.cli`/`expected.xpc` own accepted null versus exact
  `unknown_field` / `[policy, capture_compiled_profiel]`. Keep these oracle data
  independent of any future production material renderer/admission classifier.
- `runner/Tests/PWRunnerCoreTests/RequestContractTests.swift` reads the corpus,
  injects `testRequestContract`, uses fixed effect/nonce substitutions, decodes
  and calls `admitSpecimen`; it compares refusal code/path (and contextual
  expected identity). It establishes admission checks, not OS file effects.
- `tests/suites/runner_outcome_bad_request/contract.py` reads/materializes the
  corpus separately for signed CLI and direct XPC. CLI checks exit 0/1,
  envelope success/refusal, exact expected diagnostics, attempt `ok`, external
  file existence, and request-byte preservation; refusal checks absent effects,
  absent worker/validator and empty steps when a runner reply exists. Direct
  XPC checks transport success separately, admitted host reply, finished versus
  bad_request, exact diagnostics, attempt outcome and independent file presence
  or absence. Both remove successful effects before the next input. For this
  pair the loop does not assert empty file bytes or a particular query verdict.
- That file also has an independently constructed base request and a separate
  `cli('capture_typo', changed(...))` control; do not describe every typo test
  as consuming the corpus or collapse boundary-specific controls by name alone.
- `tests/suites/witness_contract/opt_in/guide_workflows.py::perform` extracts and
  executes actual guide fences. `created` checks consumer validation, finished,
  sandbox applied, one create step, exact requested target, native rc/outcome,
  and independent file observation. `refuse` hardcodes each expected code/path
  and checks both envelope and runner diagnostic plus absence. It checks the
  existing-target guard preserves receipts/effect, nonce format, request
  preservation and repair equivalence; successful capture has additional receipt
  checks. These expectations must survive a change to how inputs are obtained.
  This is the guide execution owner; corpus tests do not test guide shell text.

## Existing app example boundary

`controller/src/example.rs::EXAMPLE_DOCUMENT` is a different fixed request:
`example`, read-hosts, /etc/hosts, allow-default. `render` inserts the binary's
BUILD_CONTRACT through run's parser/gate and pretty serialization. `emit` accepts
no arguments, reads no files, launches nothing, requires complete output/flush,
and reports failures with exit 2. Its argument/identity/output checks own that
command's contract, not the create/refusal lesson.
`docs/contract/10-request.surface.md` extracts this constant as a document;
`12-probes.surface.md` extracts its first probe member. Edit the cited constant
and regenerate to change those derived views. This already removes literal
contract-example duplication; it does not supply target/nonce materialization
or the guide teaching pair. Do not merge its verification with lesson oracles.

## Least maintenance-removing sequence

1. Keep current example and extracted contract views as their existing owner.
   No maintenance is removed by renaming or wrapping the Python renderer alone.
2. If app-owned lesson inputs are justified, move only the reusable create and
   deliberate-typo input definitions to an app-owned source and make corpus input
   construction consume that source; retain corpus expected data separately.
   First account for differing specimen IDs and target parameterization, and
   preserve malformed/raw/repetition fixtures as independent test inputs.
3. Have both repository lesson and standalone guide obtain that same pair from
   the installed app; remove the guide heredoc/typo sed copy and obsolete manual
   alignment instruction only after their consumers are updated. Preserve user
   work-directory, absence guards, saved bytes/results and independent effects.
   Keep missing-nonce/repair teaching only if its actual input owner is supplied;
   moving two cases does not automatically remove those additional recipes.
4. Adapt the existing corpus and guide consumers to the new input acquisition,
   retaining their independent diagnostics/effect expectations and distinct
   CLI/direct-XPC/guide scopes. An app-owned source must work without checkout,
   Python, fixtures or a signed-app plist selected through test environment.

These are ownership moves, not a new command/API design. Future `policywitness
help` remains unspecified and distinct; no permanent catalog, syntax, execution,
file creation or nonce-generation behavior is assumed. Any concrete exposure
needs an explicit identity source, caller-supplied target/materialization model,
and refusal/output behavior before docs can rely on it.
