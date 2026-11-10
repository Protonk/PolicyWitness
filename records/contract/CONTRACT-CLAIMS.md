# CONTRACT.md claim inventory

Stage 3 of the plan in `records/contract/CONTRACT-CONTACT-PLAN.md`. One row per
claim in `docs/CONTRACT.md`: what the repository does that makes it true, the
source that implements it, and the check that would fail if it were false.
This file is the index. The rows themselves, with their full mechanism
accounts, are in `records/contract/claims/`, one file per unit. Sibling
artifacts are named by path without links, under the records link rule.

## How the rows were made, and how far to trust them

- Ten delegated passes wrote the rows on 2026-11-09, each with a narrow
  brief, read-only. Each was told to read the source and the checks itself,
  to treat the report and traces as leads, to describe the machinery
  literally without judging it, and to say what it did not open.
- The first four passes (the examples, the `equipment` region, `lifecycle`
  and `profile`) worked at `00a32ef7`. The other six worked on the tree at
  `399a3951` while the C:243 correction was pending, and were also asked
  whether each sentence states four things: who acts, what is compared with
  what, at which boundary, and with what consequence. The first four passes'
  rows do not have those four fields.
- Nothing was built or run by any pass. A row's grade is "test read" or
  "source read" as its pass states it.
- The coordinator assembled the rows mechanically and has read few of them
  through. Every row is, from the coordinator's seat, a delegated read,
  except where the strain register in `records/contract/CONTRACT-LEDGER.md`
  records a first-hand reading. Each row ends with what its pass did not
  find or did not open.
- Rows are as the passes wrote them, apart from the heading, the added
  **Pass** line, and Markdown links in quoted text turned into literal text.
- Rows `K-243-1` to `K-243-9` describe the `profile` paragraph as it stood
  before commit `a7d9b320` rewrote it. The ledger's section on C:243 gives
  the current state.

## Coverage

Every unit is inventoried: 332 rows over all 441 lines. The
generated stamp table, headings and connectives have no rows.

## Reading the index

- **Claim ID** is `K-<first line>-<n>`.
- **Kind** is one of the plan's ten. **Status** is the plan's owner status:
  `owned`, `sourced`, `split` or `unowned`. Where a pass qualified a status,
  for instance "owned, with one member only sourced", the qualification is
  in the row, not here.
- **Sentence leaves out** lists which of the four things the contract
  sentence does not state, as the pass judged it, with a count of those it
  states only partly. "Not collected" marks rows from the first four passes.
- **Source files** and **Check files** count the distinct paths a row cites.
  They are a rough guide to how much machinery stands behind a sentence, for
  choosing which rows to open first. They are not a judgment, and a low
  number does not mean a simple mechanism.

## Counts

By kind and owner status:

| Kind | owned | sourced | split | unowned | Total |
| --- | --- | --- | --- | --- | --- |
| `admission` | 69 | 6 | 4 | 1 | 80 |
| `evidence` | 53 | 6 | 14 | 0 | 73 |
| `shape` | 39 | 4 | 0 | 0 | 43 |
| `denial` | 19 | 11 | 3 | 7 | 40 |
| `identity` | 19 | 1 | 6 | 0 | 26 |
| `machinery` | 15 | 4 | 2 | 1 | 22 |
| `example` | 16 | 2 | 1 | 1 | 20 |
| `procedure` | 6 | 2 | 1 | 4 | 13 |
| `referral` | 2 | 5 | 1 | 0 | 8 |
| `residue` | 2 | 4 | 0 | 1 | 7 |
| Total | 240 | 45 | 32 | 15 | 332 |

By unit:

| Unit | Rows | owned | sourced | split | unowned |
| --- | --- | --- | --- | --- | --- |
| U01, preamble: identity, admission, reuse | 22 | 15 | 2 | 4 | 1 |
| U02, surface stamps | 11 | 8 | 2 | 1 | 0 |
| U03, `request` region | 51 | 41 | 7 | 1 | 2 |
| U04, `policy` region | 6 | 5 | 1 | 0 | 0 |
| U05, `probes` region | 6 | 5 | 1 | 0 | 0 |
| U06, `actors` region | 8 | 6 | 2 | 0 | 0 |
| U07, `envelope` region | 6 | 5 | 0 | 1 | 0 |
| U08, `dossier` region | 5 | 3 | 1 | 1 | 0 |
| U09, `steps` region | 7 | 6 | 0 | 1 | 0 |
| U10, `lifecycle` region | 5 | 4 | 0 | 1 | 0 |
| U11, `equipment` region | 63 | 48 | 8 | 5 | 2 |
| U12, `profile` region | 9 | 2 | 1 | 4 | 2 |
| U13, `transport` region | 6 | 6 | 0 | 0 | 0 |
| U14, `refusals` region | 36 | 31 | 0 | 3 | 2 |
| U15, `installation` region | 12 | 9 | 1 | 2 | 0 |
| U16, `transport_encoding` region, "Typed response transport" | 32 | 23 | 5 | 3 | 1 |
| U17, maintaining the contract | 13 | 6 | 4 | 2 | 1 |
| U18, internal host/worker identity | 25 | 13 | 7 | 1 | 4 |
| U19, shape goldens | 5 | 2 | 2 | 1 | 0 |
| U20, build stamp | 4 | 2 | 1 | 1 | 0 |

What the sentences state, over the 238 rows where it was asked:

| What a rule sentence owes | stated | partly | not stated | not applicable |
| --- | --- | --- | --- | --- |
| Who acts | 34 | 25 | 159 | 5 |
| Compared with what | 19 | 70 | 91 | 21 |
| Boundary | 14 | 29 | 165 | 1 |
| Consequence | 23 | 59 | 133 | 1 |

## Index

### U01, preamble: identity, admission, reuse

Rows in `records/contract/claims/U01.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-3-1` | C:3 | identity | The public contract is the release. | split | who, compared, boundary, consequence | 3 | 2 |
| `K-3-2` | C:3 | admission | Saved specimens assert `contract` | owned | compared, boundary, consequence (+1 partly) | 3 | 4 |
| `K-3-3` | C:3-5 | shape | every independently arriving envelope, host reply and client capture names its producer | owned | compared, boundary, consequence (+1 partly) | 7 | 5 |
| `K-5-1` | C:5 | admission | Admission is exact. | owned | who, compared, boundary, consequence | 0 | 3 |
| `K-5-2` | C:5-6 | denial | There is no negotiation, implicit acceptance, historical translation … | owned | who, compared, boundary, consequence | 3 | 4 |
| `K-5-3` | C:5-6 | denial | There is no … bypass. | split | who, compared, boundary, consequence | 4 | 1 |
| `K-8-1` | C:8 | identity | A clean tree at exactly one annotated `vX.Y.Z` tag emits `release:vX.Y.Z`. | owned | who, boundary (+2 partly) | 1 | 1 |
| `K-9-1` | C:9-10 | identity | Other packaged builds emit `development:<sha256>` over the shipped source and build inputs. | split | who, boundary, consequence (+1 partly) | 2 | 1 |
| `K-10-1` | C:10-11 | identity | The digest includes on-disk contents and paths, so shipped-input edits change it. | owned | who, boundary (+1 partly) | 1 | 0 |
| `K-11-1` | C:11 | denial | Ordinary documentation and test edits do not change that digest. | owned | who, boundary, consequence | 1 | 0 |
| `K-12-1` | C:12 | identity | A dirty release tree is a development build. | owned | who, boundary (+1 partly) | 2 | 2 |
| `K-12-2` | C:12 | identity | Release admission also compares actual scoped source bytes with the tag's blobs; Git index flags cannot hide… | owned | who, boundary, consequence | 2 | 2 |
| `K-12-3` | C:12 | identity | The source scope uses declared language/resource suffixes and explicit build helpers equally in Git checkout… | owned | who, boundary, consequence | 2 | 0 |
| `K-12-4` | C:12 | denial | Incidental executables and OS files are excluded. | owned | who, compared, boundary, consequence | 2 | 2 |
| `K-12-5` | C:12-13 | identity | Direct Cargo and SwiftPM builds are `unbound` | split | who (+2 partly) | 4 | 4 (opt-in among them) |
| `K-13-1` | C:13 | admission | [`unbound` builds] refuse public requests | owned | boundary, consequence (+1 partly) | 2 | 3 (opt-in among them) |
| `K-13-2` | C:13 | admission | [`unbound` builds refuse] packaged peer checks | sourced | compared, boundary, consequence (+1 partly) | 0 | 0 |
| `K-14-1` | C:14-15 | identity | `--version`, the envelope `build.contract`, and app/service `PWContract` report the compiled identity. | owned | who, compared, boundary, consequence | 4 | 2 |
| `K-15-1` | C:15 | denial | Describe and commit remain provenance, not admission keys. | sourced | who, boundary, consequence | 3 | 2 |
| `K-17-1` | C:17-19 | procedure | To reuse a specimen with another release, inspect the surface rows changed since its asserted release, revis… | unowned | consequence (+1 partly) | 2 | 0 |
| `K-19-1` | C:19 | denial | PolicyWitness never rewrites a user's specimen. | owned | boundary (+1 partly) | 1 | 1 |
| `K-19-2` | C:19-20 | procedure | Reinstall external runners from the current app when its contract changes. | owned | boundary, consequence (+2 partly) | 3 | 2 |

### U02, surface stamps

Rows in `records/contract/claims/U02.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-24-1` | C:24 | machinery | The manifest contract_surfaces.json defines the scope. | owned | who, compared, boundary, consequence | 2 | 0 |
| `K-25-1` | C:25-26 | machinery | The transport golden includes the complete binary record identity, including host-reply field tags, native w… | owned | who, compared, boundary, consequence | 2 | 1 |
| `K-26-1` | C:26-28 | machinery | Transport and installation goldens include reservation limits and the overall client allowance, with their c… | owned | who, compared, boundary, consequence | 2 | 0 |
| `K-29-1` | C:29-30 | machinery | The generator hashes canonical shape goldens and each delimited normative region across reachable annotated … | owned | boundary, consequence (+1 partly) | 1 | 0 |
| `K-30-1` | C:30-31 | machinery | A new or changed surface is stamped `unreleased` until release preparation | owned | who, compared (+2 partly) | 3 | 3 |
| `K-31-1` | C:31 | machinery | removed surfaces retain a removal row. | owned | who, compared, boundary | 1 | 0 |
| `K-32-1` | C:32 | denial | Stamps are navigation aids and are never asserted or used for admission. | sourced | who, boundary, consequence | 1 | 0 |
| `K-52-1` | C:52-54 | machinery | When annotated release history is unavailable, `--check` validates the current inputs and agreement between … | owned | nothing (+3 partly) | 1 | 0 |
| `K-54-1` | C:54-55 | machinery | Regeneration refuses to erase existing release stamps without history. | split | nothing (+3 partly) | 1 | 0 |
| `K-55-1` | C:55-56 | machinery | Release preflight requires annotated history and a full derivation | sourced | consequence (+2 partly) | 1 | 4 |
| `K-56-1` | C:56 | machinery | `--check --require-history` requests the same completeness. | owned | boundary, consequence (+1 partly) | 1 | 0 |

### U03, `request` region

Rows in `records/contract/claims/U03.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-63-1` | C:63 | example | a foreign assertion plus an invalid runner selector reports the contract refusal | owned | not collected | 8 | 6 |
| `K-63-2` | C:63 | example | …and starts no client | owned | not collected | 5 | 6 (opt-in among them) |
| `K-63-3` | C:63 | admission | The request root requires a string `contract` exactly equal to the running build identity. | owned | who, boundary, consequence (+1 partly) | 2 | 5 (opt-in among them) |
| `K-63-4` | C:63 | admission | Missing, null, nonstring and foreign assertions refuse before selectors, augments, helpers or children. | owned | who (+3 partly) | 0 | 2 (opt-in among them) |
| `K-63-5` | C:63 | admission | Unknown fields are refused after this gate. | owned | who, compared (+2 partly) | 0 | 0 |
| `K-63-6` | C:63 | admission | `runner`, aliases and required entitlements select one installed or bundled runner. | owned | who, compared, boundary, consequence | 0 | 0 |
| `K-67-1` | C:67 | residue | The existing Swift `Codable` types remain the parser. | sourced | who, boundary | 0 | 0 |
| `K-67-2` | C:67-70 | admission | Their `CodingKeys` also define the accepted fields of every request object: the root, policy, each phase, or… | owned | who, boundary, consequence | 1 | 2 |
| `K-70-1` | C:70-72 | admission | An unknown key is a `bad_request` with a bounded field path, rather than an ignored option. For example, `po… | owned | who, boundary (+2 partly) | 0 | 0 |
| `K-72-1` | C:72-74 | admission | `policy.params` is a dictionary of caller-chosen names to string values; its names are data, not closed obje… | owned | who, boundary, consequence | 0 | 0 |
| `K-74-1` | C:74-75 | admission | Missing required fields and wrong value types are also rejected. | owned | who, boundary, consequence (+1 partly) | 0 | 1 |
| `K-75-1` | C:75 | admission | Optional null values generally have the same meaning as absence. | owned | who, boundary | 0 | 0 |
| `K-75-2` | C:75 | admission | Actor `equipment`, `required_entitlements`, phase `after_termination`, and the actor equipment override map … | owned | who, boundary (+1 partly) | 0 | 0 |
| `K-77-1` | C:77-78 | admission | The controller additionally accepts runner selection and resolves `policy.augments`." (with a link to `contr… | owned | boundary | 0 | 0 |
| `K-78-1` | C:78-79 | admission | It validates selector types and every required entitlement, including shadowed aliases. | owned | boundary, consequence (+1 partly) | 0 | 0 |
| `K-79-1` | C:79-80 | admission | Unknown nested selector fields are errors. | owned | who, boundary (+2 partly) | 0 | 0 |
| `K-80-1` | C:80-81 | admission | A non-null nested selector value takes precedence over its top-level alias, including an explicit empty enti… | owned | who, boundary (+1 partly) | 0 | 0 |
| `K-81-1` | C:81-82 | shape | Selection fields are removed before XPC delivery | owned | who, consequence | 0 | 0 |
| `K-82-1` | C:82-83 | evidence | …and their resolved meaning is recorded in runner provenance. | split | who, consequence (+1 partly) | 0 | 0 |
| `K-83-1` | C:83 | admission | Direct XPC requests reject runner selection fields. | owned | who, compared (+2 partly) | 0 | 0 |
| `K-83-2` | C:83 | admission | Actor `required_entitlements` remains in the XPC request and is checked separately for each actor by the hos… | owned | compared, boundary, consequence | 1 | 3 (opt-in among them) |
| `K-83-3` | C:83-84 | admission | Nonempty augment lists require a string `sbpl_source` | owned | who, boundary, consequence | 0 | 0 |
| `K-84-1` | C:84-85 | admission | the controller splices the named fragments and strips the list. | owned | boundary, consequence | 0 | 1 |
| `K-85-1` | C:85 | admission | A direct XPC request with unresolved fragments is rejected. | owned | who, boundary (+2 partly) | 0 | 0 |
| `K-87-1` | C:87-88 | admission | Meaning checks reject unknown attempt kind/action pairs and filter kinds before any worker or validator is c… | owned | who (+3 partly) | 0 | 3 |
| `K-88-1` | C:88-89 | admission | A non-null `attempt.args` is accepted only for `exec/spawn` | owned | who, boundary, consequence | 0 | 0 |
| `K-89-1` | C:89 | admission | a non-null `filter.value` is refused for `kind: \"none\"` | owned | who, boundary (+1 partly) | 0 | 1 |
| `K-90-1` | C:90 | admission | `capture_nonce` requires enabled `capture_compiled_profile`. | owned | who, boundary, consequence | 0 | 0 |
| `K-90-2` | C:90-91 | admission | Enabled capture requires a valid nonce. | sourced | who, compared, boundary, consequence | 1 | 3 |
| `K-91-1` | C:91-92 | admission | Exactly one non-null plan form, `probe_plan` or `phases`, is required. | owned | who, boundary, consequence (+1 partly) | 0 | 0 |
| `K-92-1` | C:92-93 | admission | Explicit phases are nonempty and have unique nonempty phase IDs. | owned | who, boundary, consequence | 0 | 0 |
| `K-93-1` | C:93 | admission | Every ordinary action requires both query and attempt. | owned | who, boundary, consequence (+1 partly) | 0 | 0 |
| `K-93-2` | C:93-94 | admission | Step IDs must be distinct across all phases | owned | who, boundary, consequence | 0 | 0 |
| `K-94-1` | C:94 | admission | …and exec targets absolute. | sourced | who, boundary, consequence (+1 partly) | 0 | 6 |
| `K-95-1` | C:95-96 | evidence | Known operation/filter pairs excluded from prediction still produce explicit `prediction_unavailable` observ… | owned | who, boundary (+1 partly) | 0 | 0 |
| `K-97-1` | C:97-98 | evidence | Operation names passed to `sandbox_check` remain OS queries; the validator can report `unsupported_operation… | owned | compared, boundary (+2 partly) | 0 | 2 |
| `K-98-1` | C:98 | denial | Query and attempt scopes need not match. | owned | boundary | 0 | 2 |
| `K-100-1` | C:100 | identity | Every shipped-source change changes a development contract. | owned | who, boundary, consequence (+1 partly) | 1 | 3 (opt-in among them) |
| `K-100-2` | C:100-101 | identity | A clean annotated release binds all public surfaces to that release. | owned | who, boundary, consequence (+1 partly) | 1 | 0 |
| `K-101-1` | C:101-103 | procedure | Additions, removals, meaning changes and implementation fixes therefore require the specimen author to revie… | owned | consequence | 0 | 0 |
| `K-103-1` | C:103-105 | procedure | Keep the affected normative definition, verified examples and shape goldens current so the release stamp tab… | owned | who, compared, boundary, consequence | 2 | 0 |
| `K-105-1` | C:105-106 | residue | There is no separate request counter or compatibility exception for optional additions. | owned | nothing (+1 partly) | 0 | 0 |
| `K-108-1` | C:108 | referral | Runtime admission limits are separate from this syntax and meaning." (link to `docs/LIMITS.md`) | owned | who, boundary | 0 | 1 |
| `K-109-1` | C:109-110 | admission | For example, a structurally valid plan can exceed the worker's step capacity; the refusal names the field, a… | owned | who (+3 partly) | 0 | 1 |
| `K-111-1` | C:111-112 | admission | Raising capacity accepts more plans; lowering it can refuse previously runnable requests. | unowned | nothing (+2 partly) | 0 | 0 |
| `K-112-1` | C:112-113 | denial | The caller decides whether to revise the specimen or use a build with more capacity; PW never truncates or r… | owned | nothing (+1 partly) | 0 | 1 |
| `K-113-1` | C:113-114 | procedure | Capacity changes must be documented and tested even when they do not change the input grammar. | sourced | who | 1 | 2 |
| `K-116-1` | C:116-117 | machinery | Maintenance consists of the existing decoder/selector fields, their meaning in the guide, and acceptance/ref… | sourced | who | 2 | 0 |
| `K-117-1` | C:117-118 | denial | No additional schema language or parser generator is used. | sourced | nothing | 1 | 0 |
| `K-118-1` | C:118-119 | denial | These rules protect requested intent; they do not promise identical sandbox observations across builds or ma… | unowned | nothing | 0 | 0 |
| `K-121-1` | C:121-122 | referral | The developer lesson works through the same specimens used by Swift decoding/validation tests and signed CLI… | sourced | nothing | 3 | 0 |

### U04, `policy` region

Rows in `records/contract/claims/U04.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-129-1` | C:129 | example | a missing augment refuses before worker creation | owned | not collected | 4 | 5 |
| `K-129-2` | C:129 | example | …and leaves the input file unchanged | sourced | not collected | 4 | 4 |
| `K-129-3` | C:129 | shape | A policy supplies SBPL source and optional string parameters. | owned | who, boundary, consequence (+1 partly) | 4 | 2 |
| `K-129-4` | C:129 | admission | Named augments are resolved by the controller in memory before submission. | owned | compared, consequence (+1 partly) | 2 | 5 |
| `K-129-5` | C:129 | admission | direct XPC refuses unresolved augments. | owned | boundary (+3 partly) | 3 | 3 |
| `K-129-6` | C:129 | evidence | Imports and hashes describe the held policy input and its closure. | owned | who, compared, boundary, consequence | 2 | 1 |

### U05, `probes` region

Rows in `records/contract/claims/U05.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-135-1` | C:135 | example | file `open_write` opens with truncation | owned | not collected | 5 | 6 (opt-in among them) |
| `K-135-2` | C:135 | example | a same-shape foreign build assertion prevents that operation | owned | not collected | 1 | 4 (opt-in among them) |
| `K-135-3` | C:135 | admission | Each probe step has a unique step ID, a sandbox query and an attempt. | owned | who, boundary, consequence (+1 partly) | 3 | 3 |
| `K-135-4` | C:135 | admission | Supported attempt actions and filter kinds are closed vocabularies. | owned | who, boundary, consequence (+1 partly) | 3 | 2 |
| `K-135-5` | C:135 | evidence | Predictions are observations distinct from attempts. | sourced | who, compared, boundary, consequence | 2 | 1 |
| `K-135-6` | C:135 | evidence | [Predictions] do not establish enforcement agreement. | owned | who, compared, boundary (+1 partly) | 2 | 2 |

### U06, `actors` region

Rows in `records/contract/claims/U06.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-141-1` | C:141 | example | a phase naming a nonexistent actor is refused | owned | not collected | 4 | 5 |
| `K-141-2` | C:141 | example | …before children | owned | not collected | 4 | 4 |
| `K-141-3` | C:141 | admission | A specimen uses either the ordinary single-worker form or named actors and phases. | owned | who, compared, boundary, consequence | 3 | 2 |
| `K-141-4` | C:141 | denial | Every sandboxed process is fresh. | owned | who, compared, boundary, consequence | 3 | 1 |
| `K-141-5` | C:141 | evidence | An actor applies its policy once. | owned | who, compared, boundary, consequence | 3 | 2 |
| `K-141-6` | C:141 | admission | Phases name the active actor. | owned | who, compared, boundary, consequence | 4 | 1 |
| `K-141-7` | C:141 | shape | Phases … preserve action order. | sourced | who, compared, boundary, consequence | 4 | 1 |
| `K-141-8` | C:141 | shape | Extension transfer and consumption use explicit owned records. | sourced | who, compared, boundary, consequence | 3 | 0 |

### U07, `envelope` region

Rows in `records/contract/claims/U07.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-147-1` | C:147 | example | a foreign helper envelope claiming compilation cannot supply a successful policy-check status | owned | not collected | 4 | 5 |
| `K-147-2` | C:147 | shape | Every envelope carries `kind`, `generated_at_unix_ms`, `build`, `result` and `data`. | owned | who, compared, boundary, consequence | 2 | 3 |
| `K-147-3` | C:147 | identity | `build.contract` identifies its producer. | owned | who, compared, boundary, consequence | 1 | 3 |
| `K-147-4` | C:147 | admission | Readers admit it before semantic fields. | owned | who, compared, consequence (+1 partly) | 3 | 2 |
| `K-147-5` | C:147 | identity | Nested helper envelopes have independent build context. | owned | who, compared, boundary, consequence | 3 | 2 |
| `K-147-6` | C:147 | evidence | Unsupported received bytes remain available without inferred claims. | split | who, compared, boundary (+1 partly) | 3 | 2 |

### U08, `dossier` region

Rows in `records/contract/claims/U08.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-153-1` | C:153 | example | changing the source file after admission does not change the held submission | sourced | not collected | 5 | 3 |
| `K-153-2` | C:153 | shape | The dossier records the held request path, policy provenance, imports, selected runner, host context … | owned | who, compared, boundary, consequence | 2 | 1 |
| `K-153-3` | C:153 | evidence | The dossier records … observed binary inventory. | split | who, compared, boundary, consequence | 1 | 3 (opt-in among them) |
| `K-153-4` | C:153 | evidence | Unknown observations remain unknown. | owned | who, compared, boundary, consequence | 1 | 2 |
| `K-153-5` | C:153 | evidence | The submitted serialization and fallback compiler use the same held input. | owned | who, boundary, consequence (+1 partly) | 3 | 2 |

### U09, `steps` region

Rows in `records/contract/claims/U09.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-159-1` | C:159 | example | a foreign host reply inside a current envelope yields one unsupported diagnostic | owned | not collected | 5 | 7 (opt-in among them) |
| `K-159-2` | C:159 | example | ... without recovered comparisons" (no comparison from the foreign reply is interpreted or reported as a com… | split | not collected | 5 | 6 (opt-in among them) |
| `K-159-3` | C:159 | shape | A host reply carries `producer.contract`, `producer.describe` and `producer.commit`. | owned | compared, boundary, consequence (+1 partly) | 3 | 2 |
| `K-159-4` | C:159 | admission | Admission is exact before interpreting steps. | owned | who, consequence (+2 partly) | 4 | 4 (opt-in among them) |
| `K-159-5` | C:159 | shape | Comparisons relate query and attempt observations. | owned | who, boundary, consequence (+1 partly) | 3 | 3 |
| `K-159-6` | C:159 | evidence | Permission-shaped failures do not prove a sandbox cause. | owned | who, compared, boundary (+1 partly) | 1 | 3 |
| `K-159-7` | C:159 | evidence | `query_first` requires the collection/release evidence chain. | owned | who, boundary, consequence (+1 partly) | 7 | 4 (opt-in among them) |

### U10, `lifecycle` region

Rows in `records/contract/claims/U10.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-165-1` | C:165 | evidence | Lifecycle claims depend on native progress, collection and termination observations. | owned | not collected | 2 | 2 |
| `K-165-2` | C:165 | evidence | Unknown or contradictory observations withhold dependent claims. | owned | not collected | 3 | 1 |
| `K-165-3` | C:165 | evidence | An exit request is not proof of reap. | owned | not collected | 3 | 3 |
| `K-165-4` | C:165 | evidence | Successful return alone is not an effect witness. | split | not collected | 2 | 3 |
| `K-165-5` | C:165 | example | an unreaped worker remains unconfirmed even after a successful termination request | owned | not collected | 6 | 8 |

### U11, `equipment` region

Rows in `records/contract/claims/U11.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-171-1` | C:171 | evidence | Actor evidence binds observations to the named process and service-sealed equipment. | owned | not collected | 10 | 10 (opt-in among them) |
| `K-171-2` | C:171 | identity | The worker ABI identity remains independent of the public build identity. | sourced | not collected | 6 | 1 |
| `K-171-3` | C:171 | machinery | Worker entitlements are read from the selected binary. | sourced | not collected | 2 | 3 (opt-in among them) |
| `K-171-4` | C:171 | example | an equipment hash mismatch prevents use of the claimed equipment | owned | not collected | 5 | 5 |
| `K-176-1` | C:176 | residue | Actor execution has no declaration reply. | owned | not collected | 3 | 5 (opt-in among them) |
| `K-176-2` | C:176 | denial | Actor execution has no … singular worker projection. | owned | not collected | 4 | 3 |
| `K-177-1` | C:177-178 | shape | `actors[]` owns each launch, subprocess, application assessment and equipment association. | owned | not collected | 3 | 5 |
| `K-178-1` | C:178-180 | evidence | The `authority_setup.host` run/region/custody scopes and `authority_setup.workers` cells retain primary setu… | owned | not collected | 6 | 5 |
| `K-180-1` | C:180-181 | denial | An acquired decision does not publish another cell. | unowned | not collected | 2 | 1 |
| `K-181-1` | C:181 | denial | A scheduling summary does not replace any actor's facts. | split | not collected | 4 | 3 |
| `K-183-1` | C:183-184 | evidence | `equipment_inventory` identifies the selected service's sealed equipment inventory. | owned | not collected | 4 | 2 |
| `K-184-1` | C:184-186 | shape | Rows of `equipment_bindings` and `equipment_entitlements` are named by position: a binding is identified by … | owned | not collected | 4 | 1 |
| `K-186-1` | C:186-187 | shape | `binding_ref` and `entitlements_ref` are zero-based indexes into those two arrays. | owned | not collected | 5 | 2 (opt-in among them) |
| `K-187-1` | C:187-188 | shape | An actor's `binding_ref` is null when no binding row was produced for its role. | sourced | not collected | 5 | 1 (opt-in among them) |
| `K-188-1` | C:188-190 | shape | `equipment_bindings` separates packaged roles from explicitly instrumented overrides; the latter carry `unve… | owned | not collected | 5 | 2 (opt-in among them) |
| `K-190-1` | C:190 | denial | Override rows "cannot establish packaged selection. | unowned | not collected | 4 | 1 |
| `K-190-2` | C:190-191 | shape | `equipment_entitlements` contains independently associated static and live XML read-backs. | owned | not collected | 4 | 2 (opt-in among them) |
| `K-191-1` | C:191-192 | evidence | Every actor's requirements are evaluated separately using boolean true keys. | owned | not collected | 4 | 6 (opt-in among them) |
| `K-192-1` | C:192-193 | evidence | Requirements are evaluated with boolean true keys "including in the live read-back. | owned | not collected | 4 | 1 |
| `K-193-1` | C:193 | referral | Bounds and reserve geometry belong to LIMITS. | split | not collected | 4 | 2 |
| `K-194-1` | C:194 | evidence | Runtime inspection failure cancels all scheduled activation. | owned | not collected | 5 | 2 |
| `K-194-2` | C:194-195 | evidence | Runtime inspection failure "retains any already published setup/application facts. | owned | not collected | 3 | 1 |
| `K-195-1` | C:195-196 | denial | Runtime inspection failure "is not a before-launch `preparation_failure`. | owned | not collected | 5 | 2 |
| `K-196-1` | C:196 | evidence | Independent earlier cancellation remains visible. | sourced | not collected | 3 | 0 |
| `K-198-1` | C:198-199 | evidence | `preparation_failure` admits only `resolved_plan/inconsistent_assignment` or `equipment/equipment_binding_re… | split | not collected | 4 | 5 (opt-in among them) |
| `K-199-1` | C:199 | evidence | `preparation_failure` comes "with `runner_failed`, `rc: 1`. | owned | not collected | 5 | 2 (opt-in among them) |
| `K-199-2` | C:199-200 | evidence | `preparation_failure` comes with "no launched actors. | owned | not collected | 4 | 4 (opt-in among them) |
| `K-200-1` | C:200 | evidence | Observation arrays are empty. | owned | not collected | 4 | 2 (opt-in among them) |
| `K-200-2` | C:200-202 | evidence | Unique bounded declarative phase and action identities may remain, without claiming that those actions ran. | sourced | not collected | 4 | 1 (opt-in among them) |
| `K-202-1` | C:202 | denial | This is the sole exception to their normal complete observation partition. | split | not collected | 3 | 1 (opt-in among them) |
| `K-204-1` | C:204 | shape | `actors[].application` has closed state/basis pairs. | owned | not collected | 3 | 5 |
| `K-204-2` | C:204-205 | evidence | Unapplied intent is `not_requested/unapplied_declaration`. | owned | not collected | 4 | 2 |
| `K-205-1` | C:205-206 | evidence | `not_attempted` requires host proof of no launch or an eligible terminal worker branch before application. | owned | not collected | 4 | 5 |
| `K-207-1` | C:207 | evidence | `observed` requires an applied publication or the native apply-failure publication. | split | not collected | 4 | 3 |
| `K-208-1` | C:208 | evidence | With no such source, requested application is `unobserved`. | owned | not collected | 3 | 1 |
| `K-209-1` | C:209-210 | denial | Setup timeout, `done`, process death or an auxiliary reporting failure alone cannot establish application no… | owned | not collected | 4 | 2 |
| `K-212-1` | C:212-213 | evidence | Termination dependencies retain a source actor's `owned_reap`. | owned | not collected | 5 | 5 |
| `K-212-2` | C:212-214 | shape | `owned_reap` includes native PID/return/raw wait status, capture stage, ownership/departure flags, `capture_… | owned | not collected | 5 | 4 |
| `K-214-1` | C:214-215 | shape | Each phase may retain `activation_observation: {capture_ordinal, observed_ns?}`. | owned | not collected | 3 | 3 |
| `K-215-1` | C:215-216 | denial | These ordinals are local to the source actor process, not a global process counter. | sourced | not collected | 1 | 0 |
| `K-217-1` | C:217-218 | shape | `termination_gate.observation` is `{capture_ordinal}` referencing that source actor's owned reap. | owned | not collected | 2 | 2 |
| `K-218-1` | C:218-220 | evidence | Every nonnull observation, including a failed gate's, requires a positive matching source reap ordinal and a… | owned | not collected | 5 | 4 |
| `K-220-1` | C:220-221 | evidence | A satisfied gate additionally requires the source's final activation before its owned reap. | owned | not collected | 3 | 2 |
| `K-221-1` | C:221 | evidence | …[the source's] owned reap before gate closure. | owned | not collected | 2 | 0 |
| `K-221-2` | C:221 | evidence | …consistent child PID. | owned | not collected | 2 | 0 |
| `K-221-3` | C:221-222 | evidence | …and decoded wait status. | owned | not collected | 2 | 0 |
| `K-222-1` | C:222 | evidence | …unbroken ownership. | owned | not collected | 2 | 0 |
| `K-222-2` | C:222 | evidence | …and no prior host departure request. | owned | not collected | 2 | 0 |
| `K-223-1` | C:223-224 | evidence | Both source final-activation and owned-reap timestamps must be present and monotonically ordered. | owned | not collected | 3 | 0 |
| `K-224-1` | C:224 | evidence | The gate wait also requires a usable clock. | owned | not collected | 2 | 0 |
| `K-224-2` | C:224-225 | evidence | …no native wait error. | sourced | not collected | 2 | 0 |
| `K-225-1` | C:225-226 | evidence | …and elapsed time within the positive termination-gate allowance. | owned | not collected | 2 | 0 |
| `K-225-2` | C:225-226 | referral | The termination-gate allowance is given in LIMITS. | sourced | not collected | 5 | 1 |
| `K-227-1` | C:227 | evidence | An abnormal natural reap can satisfy termination. | owned | not collected | 2 | 0 |
| `K-227-2` | C:227-228 | evidence | Final phase completion [or] `done` … cannot substitute. | owned | not collected | 2 | 0 |
| `K-228-1` | C:228 | evidence | A requested exit … cannot substitute. | owned | not collected | 0 | 0 |
| `K-228-2` | C:228 | evidence | A cleanup-only reap cannot substitute. | owned | not collected | 3 | 0 |
| `K-230-1` | C:230 | evidence | Native facts may retain absent source timestamps after clock failure. | owned | not collected | 2 | 0 |
| `K-230-2` | C:230-231 | evidence | …but cannot satisfy the dependency without them. | owned | not collected | 0 | 0 |
| `K-231-1` | C:231-233 | evidence | Once dependent activation has been stored, a missing post-store dependent timestamp retains that activation … | owned | not collected | 2 | 0 |
| `K-234-1` | C:234 | evidence | A present dependent timestamp must not precede the source reap. | owned | not collected | 2 | 0 |
| `K-234-2` | C:234-235 | evidence | Reached failed gates withhold activation, collection and release. | owned | not collected | 2 | 0 |
| `K-235-1` | C:235-236 | evidence | …even if cleanup later observes reap. | owned | not collected | 1 | 0 |

### U12, `profile` region

Rows in `records/contract/claims/U12.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-243-1` | C:243 | evidence | A compiled-profile receipt inherits its admitted host reply context. | owned | not collected | 2 | 1 |
| `K-243-2` | C:243 | denial | It has no independent schema marker. | sourced | not collected | 2 | 1 |
| `K-243-3` | C:243 | evidence | Status … [and] stage … must be consistent. | owned | not collected | 4 | 6 |
| `K-243-4` | C:243 | evidence | …nonce … must be consistent. | split | not collected | 4 | 2 |
| `K-243-5` | C:243 | evidence | …worker binding … must be consistent. | split | not collected | 2 | 2 |
| `K-243-6` | C:243 | evidence | …byte count … must be consistent. | split | not collected | 2 | 0 |
| `K-243-7` | C:243 | evidence | …digest must be consistent. | split | not collected | 2 | 0 |
| `K-243-8` | C:243 | denial | A detached receipt grants no producer context. | unowned | not collected | 2 | 0 |
| `K-243-9` | C:243 | example | a wrong nonce refuses the receipt even inside a current reply | unowned | not collected | 7 | 11 |

### U13, `transport` region

Rows in `records/contract/claims/U13.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-249-1` | C:249 | example | a foreign live peer behind a matching registry entry receives no specimen submission | owned | not collected | 6 | 7 (opt-in among them) |
| `K-249-2` | C:249 | shape | Client capture and reservation messages carry a string `contract`. | owned | who, boundary, consequence (+1 partly) | 4 | 4 |
| `K-249-3` | C:249 | admission | The capture and embedded host frame are independently admitted. | owned | who, compared, boundary, consequence | 2 | 3 (opt-in among them) |
| `K-249-4` | C:249 | admission | The binary shape fingerprint guards decoding. | owned | who, compared, consequence (+1 partly) | 2 | 1 |
| `K-249-5` | C:249 | identity | [The fingerprint] is not a public compatibility identity. | owned | who, compared, boundary, consequence | 1 | 1 |
| `K-249-6` | C:249 | denial | Reservation and submission failures never authorize replay after an uncertain invocation. | owned | who, boundary, consequence (+1 partly) | 4 | 4 (opt-in among them) |

### U14, `refusals` region

Rows in `records/contract/claims/U14.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-255-1` | C:255 | example | an old `schema_version`-only specimen reports missing `contract` | owned | not collected | 4 | 3 |
| `K-255-2` | C:255 | example | …not an unknown-field error | owned | not collected | 4 | 2 |
| `K-255-3` | C:255 | admission | Request refusals use `bad_request`" (restated in full at C:258-259). | owned | who, boundary (+2 partly) | 4 | 1 |
| `K-255-4` | C:255 | shape | Request refusals use "bounded diagnostic paths" (the bound is given at C:268-269). | owned | who, compared, boundary, consequence | 2 | 0 |
| `K-255-5` | C:255 | admission | Request refusals use "distinct missing/type/unsupported codes". | owned | who, compared, boundary (+1 partly) | 3 | 2 |
| `K-255-6` | C:255 | shape | Contract failures include `expected_contract`" (restated at C:266-267). | owned | who, boundary (+1 partly) | 4 | 1 |
| `K-255-7` | C:255 | admission | foreign output is unsupported, malformed output remains malformed. | owned | who, compared, boundary (+1 partly) | 2 | 1 |
| `K-255-8` | C:255 | admission | Delivery failure takes precedence over interpreting a reply. | owned | who, consequence (+1 partly) | 2 | 1 |
| `K-258-1` | C:258-259 | admission | Malformed JSON, request contract assertions, selectors, augments … report `bad_request`" (the members the co… | split | who, compared, boundary (+1 partly) | 4 | 3 |
| `K-258-2` | C:258-259 | admission | Malformed JSON, request contract assertions, … field structure and meaning, and capacity refusals report `ba… | owned | who, compared, boundary (+1 partly) | 7 | 2 |
| `K-259-1` | C:259 | admission | the controller exits 1. | owned | compared (+1 partly) | 1 | 1 |
| `K-260-1` | C:260-261 | admission | Unreadable request files, unavailable runner installations and transport failures remain tool/execution fail… | split | who, compared, boundary (+1 partly) | 3 | 1 (opt-in among them) |
| `K-261-1` | C:261 | shape | The controller exposes `data.request_failure`. | owned | boundary (+1 partly) | 1 | 0 |
| `K-262-1` | C:262-263 | shape | when the runner refuses the request, this is an unchanged copy of the runner's `request_failure`. | owned | boundary (+2 partly) | 2 | 0 |
| `K-263-1` | C:263-264 | evidence | It is optional additive response/envelope information: absence means no structured diagnostic was supplied, … | owned | who (+1 partly) | 2 | 1 |
| `K-266-1` | C:266-267 | shape | The record has `code` and `path`, plus `expected_contract` for contract-field refusals. | owned | who, boundary (+1 partly) | 3 | 1 |
| `K-267-1` | C:267-268 | shape | `path` is an array of object keys and decimal array positions, with `[]` naming the root. | owned | who, boundary | 5 | 1 |
| `K-268-1` | C:268-269 | shape | It is `null` when the full location cannot be reported: at most eight components of at most 63 UTF-8 bytes e… | owned | who, boundary | 5 | 2 |
| `K-269-1` | C:269-270 | denial | Refused parameter keys are also withheld. | owned | who, compared, boundary (+1 partly) | 2 | 0 |
| `K-270-1` | C:270-271 | procedure | Human-readable `error` is supplementary; consumers use the code and path without parsing that prose. | unowned | nothing | 3 | 0 |
| `K-275-1` | C:275 | admission | `invalid_json`: "The request could not be parsed as JSON. | owned | who, boundary (+1 partly) | 2 | 1 |
| `K-276-1` | C:276 | admission | `unsupported_contract`: "The request marker names another contract. | owned | who, boundary (+2 partly) | 2 | 1 |
| `K-277-1` | C:277 | admission | `unknown_field`, `missing_field`, `missing_value`, `type_mismatch`, `invalid_value`: "The named input is unk… | owned | who, compared, boundary | 3 | 2 |
| `K-277-2` | C:277 | admission | The same five codes as produced by the host. | owned | who, compared, boundary | 4 | 0 |
| `K-278-1` | C:278 | admission | `unsupported_policy_format`, `missing_policy_source`: "The policy's structural prerequisites are absent. | owned | who, compared, boundary (+1 partly) | 2 | 2 |
| `K-279-1` | C:279 | admission | `unknown_filter_kind`, `missing_filter_value`, `empty_operation`: "A sandbox query cannot be formed from the… | owned | who, compared, boundary (+1 partly) | 2 | 2 |
| `K-280-1` | C:280 | admission | `unsupported_attempt`, `relative_exec_target`, `duplicate_step_id`: "The plan cannot be carried out with its… | owned | who, compared, boundary (+1 partly) | 3 | 2 |
| `K-281-1` | C:281 | admission | `invalid_termination_dependency`: "A phase names an unknown source actor, itself, or a source whose final vi… | owned | who, boundary | 2 | 0 |
| `K-282-1` | C:282 | admission | `inapplicable_field`, `invalid_capture_nonce`: "A supplied field cannot take effect or satisfy its prerequis… | owned | who, compared, boundary (+1 partly) | 2 | 1 |
| `K-283-1` | C:283 | admission | `conflicting_selector`, `unresolved_augments`, `augment_unavailable`: "Controller-owned instructions conflic… | owned | nothing (+4 partly) | 6 | 2 |
| `K-284-1` | C:284 | admission | `admission_refused`: "Capacity or native-string admission failed; `admission_failure` retains the field, act… | owned | who, boundary (+1 partly) | 3 | 2 |
| `K-286-1` | C:286 | denial | These refusals contain no steps or child-process observations. | owned | who (+1 partly) | 4 | 1 |
| `K-286-2` | C:286-287 | evidence | The XPC host itself may have launched to decode a request. | owned | nothing (+2 partly) | 2 | 1 |
| `K-287-1` | C:287-288 | admission | Capacity checks precede meaning checks. | split | who, boundary (+1 partly) | 2 | 1 |
| `K-288-1` | C:288 | shape | diagnostics identify one refusal, not an exhaustive list of defects. | owned | who, boundary | 0 | 2 |
| `K-289-1` | C:289 | procedure | Retain unfamiliar codes as unclassified refusals rather than guessing their cause. | unowned | nothing | 2 | 0 |

### U15, `installation` region

Rows in `records/contract/claims/U15.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-296-1` | C:296 | example | an owned legacy record cannot execute | owned | not collected | 4 | 4 (opt-in among them) |
| `K-296-2` | C:296 | example | …but can be removed after observed absence | owned | not collected | 2 | 3 (opt-in among them) |
| `K-296-3` | C:296 | admission | Install admits service `PWContract` before signing or launchd mutation. | owned | compared, consequence (+1 partly) | 3 | 2 (opt-in among them) |
| `K-296-4` | C:296 | admission | and rechecks after signing. | sourced | compared, consequence (+2 partly) | 1 | 2 |
| `K-296-5` | C:296 | identity | Registry and live-peer identities must both match for execution. | split | who, compared, consequence (+1 partly) | 6 | 5 (opt-in among them) |
| `K-296-6` | C:296 | admission | Records without a contract remain listable, reconcilable and removable under the existing ownership rules. | owned | who, boundary (+2 partly) | 2 | 3 (opt-in among them) |
| `K-297-1` | C:297 | evidence | Unknown record, ownership, signature, entitlements and registry metadata survives unrelated writes and pendi… | split | who (+2 partly) | 2 | 1 (opt-in among them) |
| `K-297-2` | C:297 | shape | A pending cleanup entry contains a nested `runner` record, `cleanup_started_at_unix_ms`, and `observations`. | owned | who, boundary | 1 | 1 (opt-in among them) |
| `K-297-3` | C:297 | admission | the reader also accepts historical flattened entries. | owned | boundary (+2 partly) | 1 | 1 |
| `K-297-4` | C:297 | admission | Publication requires a lossless read-back before atomic replacement. | owned | who, compared (+1 partly) | 1 | 2 (opt-in among them) |
| `K-297-5` | C:297 | denial | It never establishes execution compatibility or ownership. | owned | who, boundary (+1 partly) | 1 | 2 (opt-in among them) |
| `K-297-6` | C:297 | shape | Known retired kind aliases project as their current kind. | owned | who, boundary (+1 partly) | 1 | 1 (opt-in among them) |

### U16, `transport_encoding` region, "Typed response transport"

Rows in `records/contract/claims/U16.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-304-1` | C:304-305 | machinery | porcelain.json owns response and client-capture record structure. | owned | who, compared, boundary, consequence | 2 | 1 |
| `K-305-1` | C:305-307 | machinery | `generate_porcelain.py` emits the Swift writers and stored fields, Rust owned records/readers/JSON projectio… | owned | boundary, consequence (+1 partly) | 3 | 1 |
| `K-307-1` | C:307-308 | machinery | All three derive from the one schema, so they cannot disagree with each other about structure. | split | compared, boundary, consequence (+1 partly) | 5 | 5 |
| `K-308-1` | C:308-309 | denial | none of them checks the schema itself. | sourced | compared, boundary, consequence (+1 partly) | 1 | 1 |
| `K-309-1` | C:309-310 | denial | Request and reservation JSON and validator NDJSON retain their own boundaries. | sourced | who, compared, boundary, consequence | 4 | 0 |
| `K-310-1` | C:310-311 | shape | JSON reply fixtures are test inputs; production reply ingestion is binary and public JSON is projected from … | owned | who, compared, boundary, consequence | 4 | 2 |
| `K-313-1` | C:313-314 | shape | A frame is `PWP1`, the SHA-256 of the schema's wire identity, and one root value. | owned | who, boundary, consequence (+1 partly) | 4 | 2 |
| `K-314-1` | C:314-316 | shape | Values have a one-byte kind, four-byte little-endian payload length, and payload. Kinds are boolean, signed … | owned | who, compared, boundary, consequence | 3 | 2 |
| `K-316-1` | C:316-317 | shape | Integers occupy eight bytes; readers enforce each field's native signedness and width. | owned | boundary, consequence (+1 partly) | 4 | 2 |
| `K-317-1` | C:317-319 | shape | Digests travel as their bytes, and a reference from one equipment row to another is an unsigned index into t… | sourced | who, boundary, consequence (+1 partly) | 2 | 0 |
| `K-319-1` | C:319-322 | evidence | Enumerated values such as outcomes, states and reasons travel as text, as do the names a request chose (step… | split | compared, boundary, consequence (+1 partly) | 3 | 2 |
| `K-322-1` | C:322-324 | shape | Records begin with a two-byte identity and contain strictly increasing nonzero two-byte field tags followed … | owned | who, boundary, consequence (+1 partly) | 4 | 2 |
| `K-324-1` | C:324-325 | shape | Lists/maps begin with a four-byte count; map keys are unique and sorted by UTF-8 bytes. | owned | who, boundary, consequence (+1 partly) | 3 | 2 |
| `K-325-1` | C:325 | shape | Variants begin with a two-byte case tag. | owned | who, compared, boundary, consequence | 4 | 2 |
| `K-326-1` | C:326 | denial | Optional fields are absent, never filled with fabricated defaults. | owned | who, boundary, consequence | 3 | 3 |
| `K-328-1` | C:328-330 | admission | Readers reject unsupported fingerprints, unknown tags/records/cases, missing required fields, incorrect kind… | owned | boundary, consequence (+1 partly) | 4 | 3 |
| `K-330-1` | C:330-332 | admission | The primitive reader enforces byte and nesting budgets and charges decoded collection slots, strings and byt… | owned | compared, boundary, consequence | 1 | 3 |
| `K-332-1` | C:332-333 | denial | These are not physical peak-memory bounds. | unowned | nothing | 2 | 0 |
| `K-333-1` | C:333-334 | shape | The client capture and the host reply it carries are separate frames, each read under its own budget. | owned | who, boundary, consequence | 3 | 1 |
| `K-334-1` | C:334-335 | admission | The host writer bounds a reply by the frame limit. | sourced | boundary, consequence (+1 partly) | 2 | 2 |
| `K-335-1` | C:335-336 | referral | the client retains at most its smaller reply allowance (LIMITS.md). | owned | boundary (+2 partly) | 3 | 3 |
| `K-336-1` | C:336-337 | admission | a larger reply arrives truncated and is refused as `runner_reply_truncated`. | sourced | who, compared, boundary (+1 partly) | 2 | 3 |
| `K-337-1` | C:337-339 | admission | The controller collects the client's complete output before applying its retention cap; reading is not strea… | owned | consequence (+2 partly) | 2 | 2 |
| `K-341-1` | C:341-344 | identity | The fingerprint covers every record identity, field tag, field name, kind and public presentation rule, so i… | owned | who, boundary, consequence (+1 partly) | 3 | 1 |
| `K-344-1` | C:344 | denial | Source locations, defaults and comments are outside it. | owned | who, boundary, consequence | 1 | 1 |
| `K-344-2` | C:344-345 | denial | There is no negotiation and no additive compatibility at this layer. | owned | who, compared, consequence (+1 partly) | 3 | 2 |
| `K-345-1` | C:345 | admission | The public build contract is checked during reservation before execution. | owned | who, compared, consequence | 2 | 3 |
| `K-345-2` | C:345 | evidence | The binary fingerprint remains a structural decoder check; it supplies no independent compatibility permissi… | owned | who, compared, boundary, consequence | 3 | 3 |
| `K-347-1` | C:347-351 | shape | The public envelope projects typed records. Byte fields are carried as bytes: retained host reply bytes, com… | owned | who, consequence | 4 | 2 |
| `K-351-1` | C:351-352 | denial | Unsupported or malformed input cannot become a semantic claim. | owned | who, boundary, consequence | 3 | 2 |
| `K-352-1` | C:352-355 | evidence | Structural admission establishes the declared shape; named validators separately check native operations, li… | owned | who, compared, consequence (+1 partly) | 3 | 1 |
| `K-355-1` | C:355 | evidence | Conflicting observations remain publishable with dependent claims withheld. | split | who, compared, boundary (+1 partly) | 2 | 3 |

### U17, maintaining the contract

Rows in `records/contract/claims/U17.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-362-1` | C:362-363 | procedure | Edit schema-owned record declarations in `docs/porcelain.json` and regenerate with `tests/lib/python.sh docs… | sourced | compared, boundary, consequence (+1 partly) | 1 | 2 |
| `K-363-1` | C:363-364 | procedure | Review shape changes, update their goldens. | owned | compared, boundary, consequence (+1 partly) | 3 | 1 |
| `K-364-1` | C:364-365 | procedure | …and keep each normative definition and verified example current. | unowned | compared, consequence | 1 | 1 |
| `K-365-1` | C:365 | denial | No public schema counter is maintained. | owned | who, compared, boundary (+1 partly) | 3 | 3 |
| `K-365-2` | C:365-368 | machinery | Run `…generate_contract_stamps.py`; `--check` verifies freshness without writing when annotated history is a… | owned | boundary (+3 partly) | 1 | 1 |
| `K-368-1` | C:368-369 | machinery | Use `--check --require-history` for a complete derivation check. | owned | who, boundary, consequence (+1 partly) | 2 | 1 |
| `K-369-1` | C:369-370 | procedure | Prepare the table with `--release vX.Y.Z` before committing and tagging; on the tagged tree ordinary `--chec… | owned | consequence (+1 partly) | 3 | 1 |
| `K-372-1` | C:372-373 | residue | The registry, provenance and other infrastructure format markers … retain their separate purposes. | sourced | who, compared, boundary, consequence | 4 | 1 |
| `K-372-2` | C:372-373 | residue | …validator NDJSON marker … retain[s its] separate purpose. | sourced | who, compared, boundary, consequence | 2 | 0 |
| `K-373-1` | C:373 | residue | …and worker ABI identity retain[s its] separate purpose. | sourced | who, consequence | 2 | 1 (opt-in among them) |
| `K-373-2` | C:373-374 | evidence | Historical captures keep their bytes and are rejected if their producer is unsupported. | split | who, compared, boundary (+1 partly) | 3 | 4 |
| `K-375-1` | C:375-376 | identity | Authored request templates carry no identity; the harness asserts the independently inspected candidate at s… | split | consequence (+1 partly) | 2 | 1 |
| `K-376-1` | C:376-377 | identity | Constructed response tests supply an explicit producer context. | owned | compared, consequence (+2 partly) | 5 | 1 |

### U18, internal host/worker identity

Rows in `records/contract/claims/U18.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-382-1` | C:382-384 | identity | The XPC host and its bundle-local `pw-probe-runner` use an exact SHA-256 source identity, generated by gener… | owned | compared, boundary, consequence (+1 partly) | 4 | 4 |
| `K-384-1` | C:384-385 | denial | There is no worker ABI ordinal or compatibility negotiation. | sourced | nothing (+1 partly) | 2 | 1 |
| `K-385-1` | C:385-387 | machinery | The build checks the C, Swift and test copies before compilation and again before signing, and never writes … | owned | compared (+1 partly) | 1 | 5 (opt-in among them) |
| `K-387-1` | C:387-388 | procedure | `tests/lib/python.sh docs/generate_worker_identity.py` regenerates them after an edit to any input, and `--c… | owned | consequence (+2 partly) | 1 | 1 |
| `K-389-1` | C:389 | machinery | Direct source-test builds regenerate the same way. | unowned | who, consequence | 2 | 0 |
| `K-389-2` | C:389-390 | referral | The build account (BUILD.md#one-build-in-time) owns the sequence of checks and signatures. | sourced | nothing | 1 | 0 |
| `K-392-1` | C:392-395 | identity | The digest covers sorted repository-relative paths and file contents, each length-framed: all `.c`, `.h` and… | owned | boundary (+1 partly) | 2 | 3 |
| `K-396-1` | C:396 | identity | Generated identity region bodies are excluded to avoid self-reference. | owned | who, boundary, consequence | 1 | 1 |
| `K-397-1` | C:397-398 | machinery | Discovery includes new helpers automatically when they are ordinary files beneath those directories; a symli… | owned | who, boundary (+2 partly) | 1 | 3 |
| `K-398-1` | C:398-401 | machinery | The build reads Ninja's dependency log to check that the compiler consumed nothing for the worker and the sh… | owned | boundary, consequence | 1 | 2 |
| `K-401-1` | C:401-403 | identity | This conservative scope includes the C wait and publication code, Swift release and collection code, orchest… | owned | nothing | 2 | 1 |
| `K-403-1` | C:403-404 | identity | Even comments or unrelated changes within those files change the identity; there is no manual semantic-versi… | owned | who, consequence | 1 | 1 |
| `K-406-1` | C:406-407 | shape | The shared header has a fixed bootstrap magic at byte 0 and 32 identity bytes at byte 64. | owned | who, compared, boundary, consequence | 2 | 2 |
| `K-407-1` | C:407-408 | admission | The worker checks the mapped region's size and these fields before reading policy input, publishing evidence… | owned | consequence (+1 partly) | 1 | 1 |
| `K-409-1` | C:409-410 | admission | An identity or magic mismatch exits with code 4 and no ready/applied/done publication. | owned | nothing (+2 partly) | 1 | 1 |
| `K-410-1` | C:410-411 | residue | The bootstrap magic also makes ordinal-era workers refuse the header. | unowned | compared (+1 partly) | 1 | 1 |
| `K-411-1` | C:411-412 | admission | The host checks the identity before decoding worker evidence and before releasing attempts. | split | compared, consequence (+1 partly) | 4 | 5 |
| `K-412-1` | C:412-414 | evidence | These checks do not assert that a child validated the header: `runner_subprocess.worker_evidence.abi_identit… | owned | boundary | 3 | 2 |
| `K-416-1` | C:416 | evidence | Equality establishes agreement on the selected source bytes. | sourced | nothing | 0 | 1 (opt-in among them) |
| `K-416-2` | C:416-418 | denial | It does not prove correct implementation, compiled layout agreement, identical compiler or SDK, binary authe… | unowned | nothing | 1 | 0 |
| `K-418-1` | C:418-420 | referral | Compiled C/Swift layout checks, signed artifact provenance, and lifecycle/order tests retain those separate … | sourced | nothing | 0 | 1 |
| `K-420-1` | C:420 | denial | The hash is not a security authentication mechanism. | unowned | nothing | 2 | 0 |
| `K-422-1` | C:422 | denial | This exact-match requirement is confined to the jointly built host/worker pair. | sourced | nothing (+1 partly) | 1 | 4 |
| `K-423-1` | C:423-424 | referral | The external runner XPC protocol, JSON request and public envelope, and binary response contracts retain the… | sourced | nothing | 0 | 0 |
| `K-424-1` | C:424-425 | denial | Validator diagnostic JSON keeps its own contract; it is consumed independently of this memory interface. | sourced | who, consequence (+1 partly) | 3 | 0 |

### U19, shape goldens

Rows in `records/contract/claims/U19.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-430-1` | C:430 | shape | Shape goldens record public keys and their JSON types. | owned | who | 3 | 1 |
| `K-430-2` | C:430-431 | machinery | Producer controls collect the current shape and write a candidate when it differs. | sourced | boundary (+3 partly) | 3 | 2 |
| `K-431-1` | C:431-432 | procedure | Review the difference, update the golden and keep its normative definition and example current. | split | consequence | 0 | 0 |
| `K-433-1` | C:433 | admission | Missing or mistyped required fields still fail semantic admission. | owned | who, compared, boundary, consequence | 4 | 2 |
| `K-433-2` | C:433-434 | denial | There is no separate version-bump classifier. | sourced | nothing | 2 | 0 |

### U20, build stamp

Rows in `records/contract/claims/U20.md`.

| Claim | Lines | Kind | Claim, shortened | Status | Sentence leaves out | Source files | Check files |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `K-438-1` | C:438-439 | shape | Every envelope carries `build.contract`, `build.describe`, `build.commit`, `build.version` and `build.number… | owned | who, consequence | 2 | 4 |
| `K-439-1` | C:439 | identity | Contract is the exact admission identity. | owned | who, boundary (+1 partly) | 2 | 1 |
| `K-440-1` | C:440 | evidence | The remaining fields describe the build. | sourced | nothing (+1 partly) | 1 | 1 |
| `K-440-2` | C:440-441 | identity | Only an annotated release tag on a clean tree can produce a release contract. | split | who, boundary, consequence (+1 partly) | 4 | 1 |
