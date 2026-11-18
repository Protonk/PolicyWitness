# G-import-inventory

Read-only assessment for two coverage-map rows of `records/TRACE-MANAGEMENT-PLAN.md`:

- **Subject A** — DT-29/81–87: import scanner, resolver and helper projection (nonliteral signal, missed literal, unevaluated forms, hash scope, claimed coverage).
- **Subject B** — both unnumbered import/receipt investigations, import-inventory side, and the shared source/file-input question. The receipt findings (DT-95–104/134) belong to another pass.

## 0. Pass identity, evidence and conventions

- HEAD `837296af`, branch `main`. No tracked file was changed. No build, cargo, test case or `policy-witness run` was executed.
- The product and test sources of this thread are byte-identical to the snapshot the import investigation read: `git diff --stat 1413c20e HEAD` is empty for `controller/src/sbpl_lex.rs`, `controller/src/sbpl_imports.rs`, `controller/src/bin/sbpl-check.rs`, `controller/src/dossier.rs`, `controller/integration/cli_contract.rs`, `docs/contract/11-policy.surface.md`, `docs/contract/42-dossier.surface.md`, `docs/RESPONSE.md`, `docs/limits.json`, `docs/LIMITS.md`, `tests/lib/consumer.py`, `tests/suites/failure_boundaries/check.py` and `tests/suites/blackbox_e2e/checker_controls.py`. The review's line numbers for these files hold; every one cited below was re-read at HEAD.
- Helper executed here: `dist/PolicyWitness.app/Contents/MacOS/sbpl-check`, SHA-256 `1cb53333febf45372c5d13a79c26e335092ac5137221397289716fe7f0a9a25a`. Its envelopes report build commit `2f4d76e49e5b6b4dff25307b2f0e36ffbe10e1e6`, contract `development:b55acb20…744719e`, version `0.3.7`, number `1519`, `macos_build_version` `25G241` (macOS 26.7.1). This is **not** the binary the review used (SHA `1d447028…`, commit `8b5de2b2`, number 1482).
- Availability of the review's evidence: both scratchpads it names (`…/1f71e0b5-…/scratchpad`, `…/8e36ddab-…/scratchpad`) are absent. `.tmp/82-103-OBSV.md` and `.tmp/SHARED-INTERP-FOLLOW-UP.md` are present and, apart from link targets and heading levels, textually equal to review lines 8393–8577 and 8590–8759 (normalized diff: only the missing final newline). They are accounts, not raw observations.
- Disclosure: one `codesign -dv dist/PolicyWitness.app` display was run by mistake (the brief lists `codesign` as not permitted). It is a read-only display; nothing below relies on its output.

### 0.1 Path abbreviations

| Short | File |
| --- | --- |
| `lex` | `controller/src/sbpl_lex.rs` |
| `imp` | `controller/src/sbpl_imports.rs` |
| `chk` | `controller/src/bin/sbpl-check.rs` |
| `dos` | `controller/src/dossier.rs` |
| `rf` | `controller/src/run_flow.rs` |
| `cli` | `controller/integration/cli_contract.rs` |
| `P11` | `docs/contract/11-policy.surface.md` (generator input; owner of the helper inventory statements) |
| `D42` | `docs/contract/42-dossier.surface.md` (generator input; owner of the dossier statements) |
| `RESP` | `docs/RESPONSE.md` (generated from P11/D42; never edited by hand) |
| `GUIDE` | `docs/PolicyWitness.md` (frozen at `3d3f8e65`; never edited) |

### 0.2 Evidence classes

| Tag | Meaning |
| --- | --- |
| SRC | Re-read at HEAD in this pass. |
| RX | Executed by the review with the `8b5de2b2` helper on constructed inputs; raw outputs absent locally. |
| HX | Re-executed in this pass with the signed helper built at `2f4d76e4`, constructed inputs, section 0.3. Gitignored, no retention guarantee. |
| MODEL | `work-G-import-inventory/lex_model.py`, a line-by-line Python transliteration of `lex` used as a reading aid. Not the Rust code. In all 53 cases every MODEL ref is a helper record name and the helper lists no other name except transitive ones (B, Od, N3); its `scan_complete` values equal every value the review's Rust lexer probe reported. |
| NV | The review's native bytecode probe through the private 24-byte view; not repeated; depends on DT-103 (receipt pass). |
| LIVE-R | The investigator's direct `policy-witness run` series (`joint-1/2/3`): unregistered, one run per case, build `8b5de2b2`; outputs absent; not replayable in this pass. |
| GIT | Read-only git history check in this pass. |

Classification legend: **CEC** contradicted explicit commitment · **CA** consequential ambiguity · **UI** unsupported inference · **IMA** inaccurate mechanism account · **OCC** overstated coverage credit · **AO** accurate observation needing no change.

### 0.3 Contrasts executed in this pass (HX)

Driver scripts and outputs, all under `.tmp/trace-integration/assessments/work-G-import-inventory/`:

| File | SHA-256 |
| --- | --- |
| `contrast.py` (33 cases → `run-1/`) | `69e4764c…68441` |
| `contrast2.py` (9 cases → `run-2/`, plus MODEL over run-1) | `ac0e03bb…a2793` |
| `contrast3.py` (5 cases → `run-3/`) | `0062d6f7…cc8f7` |
| `contrast4.py` (4 cases → `run-4/`) | `bba99746…246d3` |
| `contrast5.py` (2 cases → `run-5/`; re-invokes run-3 and run-4; hash-pair count) | `1dd8752b…d290a` |
| `lex_model.py` | `1cf81f1a…35b1d` |
| `run-1.summary.jsonl`, `run-2…`, `run-3…`, `run-4…`, `run-5…` | `4e84b95c…`, `acc6633a…`, `482737fa…`, `1c061ade…`, `901f0a00…` |

Each case wrote `{"policy":{"format":"sbpl","sbpl_source":S},"probe_plan":[]}` to `run-N/cases/<id>.request.json` and ran `sbpl-check --request <file>` with only `PATH=/usr/bin:/bin`; the envelope is beside it as `<id>.envelope.json`. Invocation: `tests/lib/python.sh -I <script> "$PWD/dist/PolicyWitness.app/Contents/MacOS/sbpl-check" <work>/run-N` (`contrast5.py` takes `<work>`). There are 53 envelopes. For run-1 (33) the driver asserted the four inventory keys, `policy_sha256 == SHA-256(source)` and `policy_closure_sha256 == SHA-256(source ‖ 0x1F ‖ sorted "path sha" lines)`; for run-2 (9), the key set and the closure framing. Every invocation exited 0 (`ok`) or 1 (`compile_error`) with empty stderr; for run-3 and run-4 the stderr length was recorded on a second invocation, which returned the same `data` and `result`. `policy_sha256` differs from the closure in all 53.

`S` is a base plus the third line shown. Base **D** = `(version 1)\n(deny default)\n`; base **W** = `(version 1)\n(allow default)\n`. `<D>` = `<work>/run-1/files`. Files: `marker.sb` = `(allow pw-trace-marker-operation)\n` (SHA `30c8c5e0…69df9`); `wrapper-bsd.sb` = `(import (string-append "bsd" ".sb"))\n` (`45444b5e…9b4a`); `wrapper-marker.sb` = `(import (string-append "<D>" "/marker.sb"))\n`; `wrapper-literal-marker.sb` = `(import "<D>/marker.sb")\n`; `bad-utf8.sb` = `(version 1)\n(allow default)\n\xff\n` (`390ca7ba…fcd4`).

"**marker**" in the native column means `compile_error` with the diagnostic `unbound variable: pw-trace-marker-operation at <D>/marker.sb, line 1, column 8`: the helper's host-side compiler evaluated `marker.sb`. This shows evaluation, not which file descriptor was opened, and it is the helper's compiler, not the worker's.

**Reproductions of the review's cases**

| Case | Base, third line | Native result | `records` (all `truncated:false`, `cycle:null`) | MODEL refs / `scan_complete` |
| --- | --- | --- | --- | --- |
| A | D, none | ok | `[]`; policy `6906c7cd…1d5f`, closure `f6aa3063…8f6c` | `[]` / true |
| B | D, `(import "bsd.sb")` | ok | `bsd.sb` `f69ffbef…f8c8` 858, `dyld-support.sb` `06215a5d…bf1c` 2655, `system.sb` `1b2c4487…846f` 12024, all under `/System/Library/Sandbox/Profiles`, `error:null`; closure `7fddbed8…d84c` | `["bsd.sb"]` / true |
| C | D, `(import (string-append "bsd" ".sb"))` | ok | `[]`; policy `91f3e8b7…a1fa`, closure `17601787…b6d1` | `[]` / **false** |
| Od | D, `(if #f (import "bsd.sb"))` | ok | the same three records as B; closure `47eb6312…055c` | `["bsd.sb"]` / true |
| Nd | D, `(import "<D>/wrapper-bsd.sb")` | ok | `wrapper-bsd.sb` `45444b5e…`, `error:null` | top `[wrapper-bsd]` / true; file `[]` / **false** |
| M1 | W, `(import "<D>/marker.sb")` | marker | `marker.sb` `30c8c5e0…`, `error:null` | `[marker]` / true |
| M2 | W, `(import (string-append "<D>" "/marker.sb"))` | marker | `[]` | `[]` / **false** |
| M3 | W, `(import "<D>/absent.sb")` | `unable to open <D>/absent.sb: No such file or directory` | `absent.sb`, path null, `error:"not found in search path"` | `[absent]` / true |
| M4 | W, `(import (string-append "<D>" "/absent.sb"))` | same diagnostic as M3 | `[]` | `[]` / **false** |
| N2 | W, `(import "<D>/wrapper-marker.sb")` | marker | `wrapper-marker.sb` only, `error:null` | top true; file **false** |
| N3 | W, `(import "<D>/wrapper-literal-marker.sb")` | marker | `marker.sb` and `wrapper-literal-marker.sb` | true |
| L1 | W, `(IMPORT "<D>/marker.sb")` | `unbound variable: IMPORT at <input string>, line 3, column 2` | `[]` | `[]` / true |
| L2 | W, `(import "<D>/marker.sb" ; note⏎)` | marker | `[]`; closure = SHA-256(source ‖ 0x1F) | `[]` / **true** |
| O1 | W, `(if #f (import "<D>/marker.sb"))` | ok | `marker.sb`, `error:null` | `[marker]` / true |
| U1 | W, `(import "<D>/bad-utf8.sb")` | `compile_error` located at `<D>/bad-utf8.sb, line 3` | `bad-utf8.sb`, sha `390ca7ba…`, `error:"not valid UTF-8; its imports were not scanned"`; closure contains its path/hash line | `[bad-utf8]` / true |

A, B, C and Od reproduce the review's `policy_sha256`, closure and record hashes exactly. The three Profiles file hashes were also read independently with `shasum`.

**Further spellings (new in this pass; see "Outside the review")**

| Case | Base W, third line(s) | Native result | `records` | MODEL refs / `scan_complete` |
| --- | --- | --- | --- | --- |
| G17 | `(⇥import⏎⇥"<D>/marker.sb"⏎)` (tab, CR LF) | marker | `marker.sb` | followed / true |
| G33, G34 | `(import⇥"<D>/marker.sb")`; `(import⏎"<D>/marker.sb")` (tab or LF directly after `import`) | marker | `marker.sb` | followed / true |
| G12 | `(let () (import "<D>/marker.sb"))` | marker | `marker.sb` | followed / true |
| G1 | `(import ; note⏎ "<D>/marker.sb")` | marker | `[]` | `[]` / false |
| G18 | `(define (pw-pull n) (import n))⏎(pw-pull "<D>/marker.sb")` | marker | `[]` | `[]` / false |
| G24 | `(import (begin (import "<D>/marker.sb") "bsd.sb"))` | marker | `[]` | `[]` / false |
| G23 | `(import "<D>/marker.sb";c⏎)` | marker | `[]` | `[]` / **true** |
| G4 | `(import "<D>/marker.sb"␌)` (form feed 0x0C) | marker | `[]` | `[]` / **true** |
| G22 | `(import "<D>/marker.sb"␋)` (vertical tab 0x0B) | marker | `[]` | `[]` / **true** |
| G20 | `(import;c⏎"<D>/marker.sb")` | marker | `[]` | `[]` / **true** |
| G28 | `(␌import "<D>/marker.sb")` | marker | `[]` | `[]` / **true** |
| G29 | `( ; c⏎ import "<D>/marker.sb")` | marker | `[]` | `[]` / **true** |
| G19 | `(import(string-append "<D>" "/marker.sb"))` | marker | `[]` | `[]` / **true** |
| G15 | `(define pw-q #\")⏎(import "<D>/marker.sb")` | marker | `[]` | `[]` / **true** |
| G16 | `(define pw-s #\;) (import "<D>/marker.sb")` | marker | `[]` | `[]` / **true** |
| G5 | `(import "<D>/mark\x65r.sb")` | marker | `<D>/markx65r.sb`, `error:"not found in search path"` | wrong name / true |
| E3 | `(import "<D4>/n\nl.sb")` (file name contains LF) | marker diagnostic naming the LF-named file | `<D4>/nnl.sb`, not found | wrong name / true |
| E4 | `(import "<D4>/t\tab.sb")` (file name contains TAB) | marker diagnostic naming the TAB-named file | `<D4>/ttab.sb`, not found | wrong name / true |
| E1 | `(import "<D4>/q\"uote.sb")` | marker diagnostic naming `q"uote.sb` | `q"uote.sb`, resolved | followed / true |
| E2 | `(import "<D4>/b\\slash.sb")` | marker diagnostic naming `b\slash.sb` | `b\slash.sb`, resolved | followed / true |
| G6 | `(define pw-alias import)⏎(pw-alias "<D>/marker.sb")` | marker | `[]` | `[]` / true |
| G7 | `(apply import (list "<D>/marker.sb"))` | marker | `[]` | `[]` / true |
| G8 | `(eval (list (quote import) "<D>/marker.sb"))` | marker | `[]` | `[]` / true |
| G21 | `(eval (list (string->symbol (string-append "imp" "ort")) "<D>/marker.sb"))` | marker | `[]` | `[]` / true |
| G9 | `(load "<D>/marker.sb")` | marker | `[]` | `[]` / true |
| G25 | `(define pw-l load)⏎(pw-l "<D>/marker.sb")` | marker | `[]` | `[]` / true |
| G11 | `(define pw-data (quote (import "<D>/marker.sb")))` | ok | `marker.sb` | followed / true |
| G31 | `(define pw-d '(import "<D>/marker.sb"))` | ok | `marker.sb` | followed / true |
| G13 | `((lambda (import) (import "<D>/marker.sb")) (lambda (x) #t))` | ok | `marker.sb` | followed / true |
| G32 | `(define (pw-never) (import "<D>/marker.sb"))` | ok | `marker.sb` | followed / true |
| G2 | `(import"<D>/marker.sb")` | `unbound variable: import"<D>/marker.sb"` (one symbol) | `[]` | `[]` / true |
| G3, G3b | form feed or vertical tab directly after `import` | `unbound variable` (one symbol) | `[]` | `[]` / true |
| G10 | `(import "<D>/marker.sb" "<D>/marker.sb")` | `too many arguments` | `[]` | `[]` / true |
| G27 | `(import "")` | `unable to open : No such file or directory` | `[]` | `[]` / true |
| G30 | `(import)` | `not enough arguments` | `[]` | `[]` / true |

---

# Subject A — DT-29/81–87: scanner, resolver and helper projection

## A.1 Claims table

"Boundary" names input form · representation · observer · time. All helper claims are at the standalone `sbpl-check --request` boundary unless stated; the same binary is the fallback helper (`controller/src/policy_check.rs:65–75`), whose envelope the controller retains unparsed under `data.policy_check.envelope` (`policy_check.rs:28–30`).

### DT-29

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-29.a | The subject statement says an unevaluable import argument "records an incomplete inventory"; for `(import (string-append "bsd" ".sb"))` the helper returns `ok` and `records: []`, `truncated: false`, `cycle: null`, while the literal form returns three records. | top-level computed import · `data.import_inventory` · envelope reader · helper run | yes — statement P11:547 (RESP:862); producer chk:86–92, 347–355 | RX; HX C vs B identical, closure `17601787…b6d1` | CEC |
| DT-29.b | The closure hash identifies the source bytes and collected records; it does not expose that a nonliteral form was met. | `policy_closure_sha256` | yes — imp:350–364 | SRC; HX: closure(C) = SHA-256(C ‖ 0x1F), asserted | AO |
| DT-29.c | The helper's inventory construction omits the resolver's `nonliteral_imports`; the comment at imp:113–115 assigns that flag to the dossier. | Rust source | yes — chk:347–355; imp:113–115 | SRC | AO (mechanism of .a) |
| DT-29.d | Qualification: what the native compiler imported in that run was not examined. | — | discharged by DT-82.a/.b; HX M2 | — | AO |

### Import-inventory investigation conventions (review 3201–3274)

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| IC.a | The scanner, helper, reader and document sources were identical between the helper's build `8b5de2b2` and inspected HEAD `1413c20e`; correspondence, not a new build. | git | yes for `1413c20e`→`837296af` (empty diff, section 0); the review's helper binary is no longer the local app | GIT | AO; availability changed |
| IC.b | All 20 envelopes: exit 0/`ok` or 1/`compile_error`, empty stderr, seven `data` keys, four inventory keys, `policy_sha256` = source hash, closure = stated framing, record hash = separate file read. | helper envelope | yes — framing asserted for 42 envelopes here, exit and empty stderr for 53; record hashes compared with `shasum` of the five constructed files and the three Profiles files | RX; HX | AO |
| IC.c | Evaluating `marker.sb` fails compilation with a diagnostic naming the file, so the compile outcome shows whether the compiler evaluated it. | helper's host-side compiler | yes — HX M1 against O1 | HX | AO (shows evaluation, not file opens) |
| IC.d | A lexer probe built from the unmodified `lex` printed `scan_complete` and `refs`. | Rust unit | probe absent; MODEL reproduces every reported value | MODEL | AO |
| IC.e | A native probe read compiled bytes through the worker's 24-byte view; two runs were identical. | host process, private view | unverifiable by reading; not repeated | NV | AO; depends on DT-103 |

### DT-81

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-81.a | `ResolvedImports` has six members; the helper publishes `records`, `truncated`, `cycle` and a closure computed over `records`. | resolver → helper | yes — imp:117–132; chk:86–92, 347–355 | SRC; HX key set | AO (mechanism) |
| DT-81.t1 | Name not found → record with null path and `error: "not found in search path"`. | record | yes — imp:273–292 | HX M3 | AO |
| DT-81.t2 | Open/fstat failure or nonregular file → record carrying the `read_regular_file` error. | record | yes — imp:76–92, 167–185, 233–237; unit imp:612–640, 643–686 | SRC | AO |
| DT-81.t3 | Invalid UTF-8 import → record keeps hash and size, `error: "not valid UTF-8; its imports were not scanned"`. | record | yes — imp:242–253 | HX U1 | AO |
| DT-81.t4 | Depth bound → `truncated` and a `depth limit exceeded (8)` record. | inventory | yes — imp:219–230; unit imp:689–725 | SRC | AO |
| DT-81.t5 | Count bound → `truncated` only, no record. | inventory | yes — imp:155–163, 213–216, 277–280; unit imp:574–609 | SRC | AO |
| DT-81.t6 | Cycle → `cycle` chain. | inventory | yes — imp:196–206; unit imp:496–530 | SRC | AO |
| DT-81.t7 | Nonliteral form in the submitted source → resolver sets `nonliteral_imports` and `failure`; the helper shows nothing. | inventory | yes — imp:313–317; chk:347–355 | HX C, M2, M4 | CEC (= DT-29.a) |
| DT-81.t8 | Nonliteral form in an imported file → resolver sets `nonliteral_imports` and `failure`; the helper shows nothing and that file's record has `error: null`. | inventory, record | yes — imp:259–265 | HX Nd, N2 | CEC (= DT-83) |
| DT-81.t9 | The first problem (`failure`) is dropped by the helper. | inventory | yes — chk:347–355 | SRC | AO (no statement promises it for the helper) |
| DT-81.t10 | Which bound stopped the walk (`exceeded`) is dropped; a depth hit leaves an error record, a count hit leaves none; their order is lost. | inventory | yes — chk:347–355 | SRC | AO (P11:555 names both bounds without promising which) |
| DT-81.b | The helper inventory has no field meaning "incomplete"; unreadable, nonregular and invalid-UTF-8 inputs can be inferred only from `records[].error` text; a nonliteral argument cannot be inferred. | envelope reader | yes — chk:86–92 | SRC; HX | CEC (root of DT-29.a) |
| DT-81.c | The lexer documentation says consumers treat empty `refs` with `scan_complete = false` as "not followed"; no reader of the helper envelope can. | code comment vs envelope | yes — lex:13–18 | SRC | AO (the comment's "consumers" is the resolver, which does) |
| DT-81.d | The guide's helper passage promises only that "Resolution errors, truncation and cycles stay in the inventory", which matches the projection. | frozen guide | yes — GUIDE:869–870 | SRC | AO; frozen |
| DT-81.e | History: the helper never published a nonliteral signal; the lexer dates from `b9c02792`; `ed0bd3da` added the import scan's completeness flag and the resolver flags; `7a0dcbac` grouped the four fields; the "incomplete inventory" sentence first appears in `f6551bf9` (in v0.3.7, not v0.3.6). | git | partly — all commit facts verified; "v0.3.6's RESPONSE contains no …" is imprecise: no `docs/RESPONSE.md` exists at v0.3.6. The conclusion (the sentence arrived after the projection) holds. | GIT | AO |

### DT-82

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-82.a | For A (no import), B (literal) and C (computed), C's compiled bytecode equals B's and differs from A's, while C's helper inventory equals A's field for field except the closure, which differs only because the source differs. | helper inventory; host-side native compile | inventory part yes (HX A, B, C exact hashes); bytecode part unverifiable by reading | RX+NV; HX; M2 gives view-independent evidence that a computed argument is evaluated | CEC (executed form of DT-29.a) |
| DT-82.b | Marker controls: the compiler evaluates or tries to open a computed path (M2, M4); the inventory is empty in both; the literal forms (M1, M3) give the same diagnostics and one record. | helper | yes | HX M1–M4 | AO |
| DT-82.c | The allow-default versions of A, B, C compile to identical bytecode, so an allow-everything base cannot reveal imported rules by byte comparison. | host-side probe | unverifiable by reading | NV | AO (method limit) |
| DT-82.d | For C: `records: []` means no literal name was collected, `truncated: false` no bound, `cycle: null` no cycle, the closure identifies the source and an empty set of files; no field or combination distinguishes C from A. | envelope reader | yes | SRC; HX | CEC (= DT-29.a) |

### DT-83

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-83.a | An invalid-UTF-8 import marks its record; a nonliteral form inside an imported file sets only `nonliteral_imports` and `failure`, leaving the record `error: null` with hash, size and mtime. | resolver | yes — imp:242–253 against imp:259–265 | SRC | CEC for the helper (P11:547 has no top-level restriction); AO for the dossier |
| DT-83.b | The records statement says held bytes are "both hashed and scanned"; a record shows a scan happened, not that it was complete. | P11:551 (RESP:864) | yes | SRC | CA |
| DT-83.c | Executed: Nd returns one error-free record while the compiler followed the nested computed import; N2 returns only the wrapper record while the compiler evaluated `marker.sb`; N3 records both files. The lexer reports `scan_complete: false` for the two wrapper files. | helper | yes; Nd's "compiler followed" rests on NV, N2's on the diagnostic | RX; HX Nd, N2, N3; MODEL | AO |
| DT-83.d | No test exercises imp:259–265; the resolver tests contain no nonliteral form; the helper's constructed variants fix `nonliteral_imports: false`. | tests | yes — imp:366–726; chk:987–1011 (line 992) | SRC | AO (coverage gap) |
| DT-83.e | From source the dossier would report `incomplete` with failure `import "<name>": a nonliteral (import ...) form could not be followed`; not executed. | `run` envelope | still unexecuted for the nested case (R3 was top-level); source agrees — dos:159–172, imp:261–264 | SRC | AO; unverified by execution |
| DT-83.f | The nested branch was added in `ed0bd3da`. | git | yes | GIT | AO |

### DT-84

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-84.a | L2, `(import "<D>/marker.sb" ; note⏎)`: the compiler evaluated `marker.sb`; the helper reports `records: []`, `truncated: false`, `cycle: null`, closure = SHA-256(source ‖ 0x1F); the lexer gives `scan_complete: true`, `refs: []`, so even the internal flag is false. | helper; lexer | yes | RX; HX L2; MODEL | CEC against D42:51 and D42:229 on their natural reading; no carrier at all in the helper |
| DT-84.b | Mechanism: after the closing quote `try_match_keyword_form` skips only space, tab, CR, LF and requires `)`; a comment yields `None`; `try_match_form` returns `None` rather than `NonLiteral`; the outer scan advances one byte and later skips the string. | lexer | yes — lex:100–106, 191–194, 204–206, 62, 50–52 | SRC | AO (mechanism accurate) |
| DT-84.c | Derived: the dossier gives that source `status: "complete"` with no records. | `run` envelope | consistent with source (dos:160–166); executed later as R2 (LIVE-R) | SRC; LIVE-R | AO |
| DT-84.d | The dossier status defines `complete` as having "exhausted the literal closure without a reported problem". | D42:229 (RESP:3341) | yes | SRC | CA (whether "literal closure" means the compiler's syntax or the scanner's grammar) |
| DT-84.e | A comment between `import` and its argument reaches the `NonLiteral` path and is flagged. | lexer | yes — lex:100, 108–131; the compiler evaluates that spelling (HX G1) | SRC; MODEL; HX | AO |
| DT-84.f | The `)` rule has existed since `b9c02792`. | git | yes (`controller/src/bin/sbpl_lex.rs:119` at that commit) | GIT | AO |
| DT-84.g | Bounding: `(IMPORT …)` is not an import for the compiler either; a hash-bar block comment is rejected as "undefined sharp expression"; other reader-accepted spellings were not tested natively. | helper | L1 yes (HX); block comment not repeated; other spellings now tested (section 0.3, "Outside the review") | RX; HX | AO; the untested remainder is now partly observed |

### DT-85

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-85.a | Od, `(if #f (import "bsd.sb"))`: the helper returns the same three records as B; the compiled bytecode equals A's and differs from B's. | helper; host-side probe | inventory yes (HX Od, closure `47eb6312…055c`); bytecode unverifiable by reading | RX+NV; HX | AO |
| DT-85.b | O1, `(if #f (import "<D>/marker.sb"))`: compiles `ok` although evaluating the marker fails; the inventory has one `marker.sb` record. | helper | yes | HX O1 (also G11, G13, G31, G32) | AO |
| DT-85.c | The lexer collects literal names in every position; a unit test asserts both branches of an `if`. | lexer | yes — lex:232–238 | SRC | AO (designed, tested) |
| DT-85.d | Records are neither a subset nor a superset of the files the compiler incorporated. | inventory vs compilation | yes | HX M2/L2 (missing) and O1 (extra) | AO; bounds what a record establishes |
| DT-85.e | Qualification: the untaken import was not evaluated; whether the compiler opened the file was not observed. | — | still unobserved; no component observes file opens | — | AO |
| DT-85.f | The policy section and the reads statement say inventories describe their own reads, which agrees. | P11:573–577 (RESP:869–874) | yes | SRC | AO |
| DT-85.g | "Native compilation examples establish their selected literal imports" does not identify the examples or say whether "selected" covers conditional evaluation. | P11:585 (RESP:879) | yes; in addition, the three native compilations of a source with a literal import in the tree (cli:1479 through the helper; `tests/suites/witness_contract/check_dossier.py:178` and `tests/suites/runner_c_worker_harness/harness.c:452` through the worker, all `(import "system.sb")`) assert only that compilation succeeds, which it also would if the compiler incorporated nothing from the import | SRC | UI / OCC |
| DT-85.h | Od's closure covers three files that did not contribute to the compiled profile; Od and A compile identically with different closures. | `policy_closure_sha256` | closure part yes; "compile identically" is NV | HX; NV | AO |
| DT-85.i | No statement claims that records are compiler reads; the entry bounds what a record establishes. | P11, D42 | yes — D42:10, P11:577, imp:6–7, dos:114–117 | SRC | AO |

### DT-86

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-86.a | The subtree support is `source_read`; it cites `resolve_imports`, `read_regular_file`, `compute_closure_hash` and `ImportInventory` and no check. | P11:596–604 (RESP:885) | yes | SRC | AO (the grade claims no check) |
| DT-86.b | `sbpl_check_records_import_provenance_for_system_sb` asserts `policy_sha256 != policy_closure_sha256` "when imports were resolved"; the hashes always differ; the unit test `closure_hash_differs_from_policy_sha_when_imports_resolved` has the same property. The test does not compare a hash with file bytes, recompute the closure, or check transitive records. | integration; unit | yes — cli:1513–1516; imp:346–353, 447–453 | SRC; HX: the two hashes differ in all 53 envelopes, including A | OCC (an assertion that cannot fail, with a message crediting import resolution) |
| DT-86.c | `sbpl_check_verdicts_follow_the_native_compiler` runs 14 import-free sources and asserts empty records each time; its "nonliteral parameter name" case computes a `param` name. | integration | yes — cli:619–809; 14 cases counted; no import form | SRC | AO |
| DT-86.d | `inventory_findings_survive_in_their_group_and_never_change_the_verdict` replaces the walk with constructed values, all with `nonliteral_imports: false`; it asserts the three-field projection and verdict independence and nothing about `failure` or `exceeded`. | unit | yes — chk:987–1072 | SRC | AO |
| DT-86.e | `absent_null_and_empty_params_compile_without_setup_calls` compares the closure with the producer's own `compute_closure_hash`; the closure unit tests use constructed records. | unit | yes — chk:811–815; imp:392–453 | SRC | AO (the framing is not independently checked by a registered test) |
| DT-86.f | The resolver tests establish cycle, diamond, count, depth, read errors and FIFO handling; none contains a nonliteral form. The lexer tests flag an identifier argument and contain no computed-expression argument and no comment inside a form. | unit | yes — imp:495–725; lex:346–374 | SRC | AO |
| DT-86.g | `import_scan_statuses_never_report_an_unscanned_closure_as_complete` is the only executed check that the nonliteral flag reaches a published field, and that field is the dossier's `status`. | unit | yes — dos:1426–1464 (identifier-argument form only) | SRC | AO |
| DT-86.h | `fallback_helper` covers only the refusal path; `checker_controls.py` constructs a helper envelope with an empty inventory to test capture admission. | live helper; constructed | yes — `tests/suites/failure_boundaries/check.py:415–439`; `tests/suites/blackbox_e2e/checker_controls.py:39–52` | SRC | AO |
| DT-86.i | No test sends the helper a computed import argument and examines the envelope; no test compares inventory records with what the compiler read. | all tests | yes — `git grep` for `import_inventory` and `nonliteral` in tests and `controller/` finds no such case | SRC | AO (coverage gap) |

### DT-87

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| DT-87.a | An error record can contribute a closure line: the invalid-UTF-8 record carries a hash and an error, and the closure includes its path/hash line, while the statement says "Failed imports remain error records and contribute no path/hash line". The producer selects by presence of path and hash. | `policy_closure_sha256` | yes — P11:563 (RESP:867); imp:354–360 | RX; HX U1 (framing asserted with the line included) | CEC (second clause of P11:563) |
| DT-87.b | The guide says "A performed walk over a source with no imports is an empty list"; cases with imports the compiler followed also give an empty list. RESPONSE's "an empty records list is a performed walk with no import records" describes records only. | frozen guide; P11:378 (RESP:3534) | yes — GUIDE:878–879; HX C, M2, M4, L2 | SRC; HX | Guide: CA, frozen. P11:378: AO |
| DT-87.c | The guide's closure description omits the 0x1F separator, and its "Unresolved imports are excluded" omits read failures and depth-limit records. | frozen guide | yes — GUIDE:889–893 | SRC; HX framing with 0x1F matched 42 closures | Guide: IMA, frozen. The technical owner P11:563 states the separator |

### Coverage and limits (review 3588–3625)

| Id | Claim | Holds at HEAD? | Class |
| --- | --- | --- | --- |
| IL.a | The trace covered the lexer matcher, the resolver branches, the helper path, the RESPONSE subject and its source, the guide passage, the dossier's use of the flags, and every test naming `import_inventory`, the nonliteral flag or the helper. | yes; the same set was re-read | AO |
| IL.b | Executed evidence: 14 allow-default, 5 deny-default and 1 invalid-UTF-8 helper cases, lexer-probe output, two identical bytecode runs. | unverifiable (outputs absent); the helper cases named in entries are reproduced in 0.3 | AO |
| IL.c | Native import behavior was observed through diagnostics and identical bytecode, not file-access tracing; identical bytecode shows equal output, not which path was opened; untaken imports were shown unevaluated, not unopened. | yes; unchanged by this pass | AO |
| IL.d | The dossier consequences in DT-83 and DT-84 come from source and were not executed through `policy-witness run`. | partly discharged later: DT-84's by R2, a top-level nonliteral by R3 (LIVE-R); the nested case is still unexecuted | AO |
| IL.e | Not exercised: search-order collisions; count and depth bounds; unreadable and FIFO imports; changes between reads; other reader-accepted spellings; worker-side compilation. | bounds, unreadable and FIFO have unit tests (imp:574–725) but no helper execution; collisions cannot be exercised by content on this host (B.1 U2.4a); spellings are now exercised (0.3); worker-side compilation only by LIVE-R; changes within one run by nothing | AO |
| IL.f | Historical inspection shows when mechanisms and statements appeared, not how older binaries behaved. | yes | AO |

## A.2 Comparison

### Obligations as stated

1. **Helper subject**, owner P11:547: "The resolver follows literal imports recursively; an unevaluable import argument, unreadable/nonregular file or invalid UTF-8 scan input records an incomplete inventory."
2. **Helper records**, P11:551: "Each resolved file is opened once, checked as a regular file, and its held bytes are both hashed and scanned."
3. **Helper closure**, P11:563: "SHA-256 of source bytes, byte 0x1F, then newline-joined sorted strings of each successfully hashed resolved path, one space and its SHA-256. … Failed imports remain error records and contribute no path/hash line."
4. **Helper field**, P11:378: "Null means admission prevented the walk; an empty records list is a performed walk with no import records."
5. **Separate reads**, P11:573–577: "Bind each digest to the bytes held by its producing read. The controller dossier walk, fallback helper walk and worker native compiler perform their own reads. … A literal inventory describes the producer's walk; the worker compiled-profile receipt has its own observation boundary."
6. **Evidence scope**, P11:585: "Native compilation examples establish their selected literal imports; collision precedence, macro-generated dependencies and files changing between independent reads retain their own evidence limits."
7. **Dossier scan**, owner D42:51: "Scan literal import forms … Mark unresolved names, nonliteral forms, cycles, decoding failures and bound hits as incomplete."
8. **Dossier status**, D42:229: "`complete` exhausted the literal closure without a reported problem".
9. **Dossier scope**, D42:263: "The scan also classifies nonliteral forms, an observation with no dedicated carried Boolean." D42:83: "Literal import completeness belongs to the scanner convention".
10. **Frozen guide**, GUIDE:869–870, 878–879, 889–893 (quoted in DT-81.d, DT-87.b, DT-87.c). Not editable.

### What the producer does (observation)

- **Lexer** (`lex:38–71`): a byte scan that skips `;` comments and `"` strings and tests each `(`. A form is *literal* only as `(` ws* `import` ws+ `"name"` ws* `)` with ws ∈ {space, tab, LF, CR} (lex:151–202). A form with the keyword, a following ws byte and a first argument byte other than `"` is *nonliteral*: the scan skips it whole and clears `scan_complete` (lex:108–131). Every other shape is not a form: the scan moves one byte on (lex:105, 62). The name keeps the byte after any backslash (lex:176–179).
- **Resolver** (`imp:299–339`): `nonliteral_imports = !scan_complete` for the source (imp:313–317) or for any scanned imported file (imp:259–265); `failure` keeps the first problem; records sort by path then name.
- **Helper** (`chk:345–361`): projects `records`, `truncated`, `cycle` and the closure. `nonliteral_imports`, `exceeded` and `failure` are not projected. The inventory never changes the verdict.
- **Dossier** (`dos:151–173`): `status` is `incomplete` when `exceeded`, `cycle`, `nonliteral_imports` or any record error is present; it also carries `exceeded` and `failure`.
- **Closure** (`imp:350–364`): source ‖ 0x1F ‖ sorted `path sha` lines for every record having both a path and a hash, whatever its `error`.

Observed results per contrast (HX, helper's host-side compiler, macOS 25G241):

| Contrast | Compiler | Helper inventory today | Resolver flag today (MODEL/SRC) | Dossier status today (derived from source unless marked) |
| --- | --- | --- | --- | --- |
| Literal import followed (B, M1) | evaluates the file | record | false | `complete`, record (LIVE-R R1) |
| Computed argument the compiler follows (C, M2) | evaluates the file | same as no import | **true**, dropped | `incomplete`, failure text (LIVE-R R3; unit dos:1434–1443 for the identifier form) |
| Nonliteral inside an imported file (Nd, N2) | evaluates the nested file | wrapper record, `error: null` | **true**, dropped | `incomplete`, failure names the wrapper; never executed |
| Literal the scanner does not recognize (L2) | evaluates the file | same as no import | false | `complete`, no record (LIVE-R R2) |
| Unevaluated import form (Od, O1) | does not evaluate it | record, `error: null` | false | `complete`, record (LIVE-R R4) |

### What readers and tests assert

- `tests/lib/consumer.py:994–999`: `data.specimen.policy.imports` must be an object with a known `status` and a list `records`; `failed`/`not_applicable` carry no records or closure. Nothing about `complete`. The helper envelope under `data.policy_check.envelope` is checked for shape only, against `tests/fixtures/contract/envelope_shape.json`, where an unknown key is an error and an absent key is allowed (`consumer.py:322–355`).
- `tests/suites/witness_contract/check_dossier.py:163–165`: an import-free source gives `complete`, no records, null `cycle`/`exceeded`/`failure`. `:177–190`: a source importing `system.sb` has that record with a hash equal to an independent file read; `status` may be `complete` or `incomplete`.
- `dos:1426–1464`: the dossier test (DT-86.g). `cli:1468–1557` and `cli:619–809`: DT-86.b, DT-86.c. `chk:1013–1072`, `chk:765–822`: DT-86.d, DT-86.e. `chk:1077–1130` and `rf:3998–4013`: the helper envelope's shape equals the golden subtree.
- No reader or test anywhere examines a helper envelope produced from a source with an import form other than `(import "system.sb")`.

### Inference kept apart from observation

- That the *worker's* compiler treats these spellings as the helper's host-side compiler does is an inference from the same OS library; only the R/E series (LIVE-R) observed the worker, for R1–R4 spellings.
- That the dossier reports `complete` for G4, G19, G20, G22, G23, G28, G29, G15, G16 is derived from MODEL plus dos:160–166; not executed.
- "The compiler read file X" is never observed. The diagnostic shows evaluation of a file's content; the probes show nothing about files opened and not evaluated.

## A.3 Plausible treatments

Build-contract note used below: `docs/build_contract.py:15–27` selects every `.rs` under `controller/src` (test modules included). **Any edit to `lex`, `imp`, `chk`, `dos` or `rf` changes the build contract and requires a signed rebuild.** `controller/integration/`, `docs/contract/*.surface.md`, `docs/limits.json`, `tests/fixtures/` and `tests/suites/` are not build-contract inputs. None of the edits touches `controller/tools`. The worker identity (`docs/generate_worker_identity.py:27–29`: `controller/tools/pw_probe_runner`, `runner/Sources`) is unaffected. No Meson target, interface definition, limit value or architecture row changes.

### T1 — Carry the unfollowed-form observation in the helper inventory (product behavior change)

- **Change**: `ImportInventory` gains one required boolean, proposed spelling `unfollowed_imports` (the implementer may choose another; avoid `scan_complete`, which reads like the retired `params_scan_complete`). Meaning: *true when the submitted source or any scanned imported file contains a form headed by `import` that the scan did not follow.* It is the resolver's existing `nonliteral_imports` (imp:125, set at imp:261 and imp:314).
- **Where projected**: `data.import_inventory.unfollowed_imports` in the standalone envelope, and therefore, unchanged by the controller, `data.policy_check.envelope.data.import_inventory.…` and `data.actor_policy_checks[].policy_check.envelope.data.import_inventory.…` in a fallback run envelope.
- **Files**: `chk` (struct 86–92, doc comment 83–85, construction 347–355, `inventory_variant` 987–1011, `inventory_findings_…` 1013–1072, shape fixture 1090–1102); `imp` (comment 113–115); `rf` (fixture `sbpl_check_envelope` 3998–4013); `tests/fixtures/contract/envelope_shape.json` (the two `…import_inventory` subtrees, lines 75–80 and 143–148, replaced from the candidate that `envelope_shape_golden_agrees_with_the_manifest` writes); P11 (new field heading under "Literal import inventory", rewrite of 547, clause at 378); `tests/fixtures/contract/surfaces/policy.json` (record `rust.ImportInventory`, regenerated with `--refresh-shapes`); `tests/suites/blackbox_e2e/checker_controls.py:50–51` (constructed helper envelope); `cli` (new contrasts, T9).
- **Build contract**: yes (`chk`, `imp`, `rf`).
- **Consequence**: a new key in the helper envelope and in fallback run envelopes. `tests/lib/consumer.py` rejects unknown keys against the golden, so the golden and the producer must land together; an external strict-schema reader must admit the key. Verdict, exit code and all existing fields are unchanged. The guide's four-item field list becomes incomplete but not false.
- **A check must reject**: an envelope for a source containing an unfollowed import form whose inventory equals the no-import inventory in every field but the closure (C against A).

### T2 — Scanner: no form headed by `import` is dropped without report (product behavior change)

- **Change**: a form is *recognized* when, after `(` and any run of inter-token bytes, the atom `import` follows and ends at a delimiter. A recognized form that is not followed sets the unfollowed flag instead of returning `None` (lex:105 and the early returns at lex:92–99). Inter-token bytes and atom delimiters as observed on 25G241: space, tab, CR, LF, form feed and vertical tab and `;` comments are skipped between tokens (G17, G28, G29, G4, G22, G23; vertical tab was observed only before `)`); the atom `import` ends at space (B), tab (G33), LF (G34), CR (G17), `(` (G19), `)` (G30) and `;` (G20), and does **not** end at `"`, form feed or vertical tab (G2, G3, G3b).
- **Effect per case**: L2, G4, G22, G23, G20, G28, G29, G19, G10, G27, G30 change from unreported to flagged. G2, G3, L1 stay "not an import form", as for the compiler.
- **Files**: `lex` (`try_match_form` 82–132, `try_match_keyword_form` 151–202, `is_ws`/`skip_ws` 204–214, doc comments 11–33 and 73–80, tests; `handles_unterminated_form_without_panic` at 310–318 asserts `scan_complete` for `(import ` at end of input and must be decided); `imp` failure strings 263 and 316 if reworded (they say "nonliteral"; a flagged form may now have a literal argument) and then `dos:1437–1443`, which asserts `contains("nonliteral")`; `dos` doc comment 114–117; D42:51 and D42:263 wording.
- **Build contract**: yes.
- **Consequence**: policies using those spellings change dossier `status` from `complete` to `incomplete`; `failure` text changes if reworded. No verdict change.
- **A check must reject**: any import-headed form in the 0.3 table that is neither followed nor flagged.

### T3 — Scanner: follow the literal spellings the native reader accepts (product behavior change)

- **Change**: follow `(` skip* `import` sep skip* `"name"` skip* `)`, where skip is whitespace 0x09–0x0D/0x20 or a `;` comment. Treat `#\` plus the next byte as a character literal in the outer scan and in the nonliteral walk, so `#\"` and `#\;` do not open a string or a comment (G15, G16). For the name: `\"` and `\\` decode as today (E1, E2); for any other backslash sequence either decode the observed ones (`\n`→LF, `\t`→TAB, `\xHH`→byte: E3, E4, G5) or do not follow and set the flag. The second is the smaller commitment and is recommended, because the reader's escape table is private and only those three were observed.
- **Effect**: L2, G23, G4, G22, G20, G28, G29, G1, G15, G16 become followed, with records and a closure covering the file. G5, E3, E4 become flagged instead of producing a wrong-name record.
- **Files**: `lex` as in T2, plus unit tests for every row of the 0.3 table.
- **Build contract**: yes.
- **Consequence**: for those spellings `records` and both closure digests change for unchanged source and files; `status` stays `complete`.
- **A check must reject**: a trailing-comment literal import that the compiler evaluates and the inventory omits.
- **Still undecidable from text after T2 and T3**: (i) evaluation — whether a recognized literal form is evaluated at all (Od, O1, G11, G13, G31, G32); (ii) import without an `import`-headed form — aliasing, `apply`, `eval`, a constructed symbol (G6, G7, G8, G21); (iii) other file-reading procedures — `load` (G9, G25), and any other the private prelude may define; (iv) reader features the scan does not model, on OS builds not probed; (v) which directory, which bytes and when the compiler reads (Subject B).

### T4 — Mark the record of a scanned file that contains an unfollowed form (product behavior change)

- **Change**: at imp:260–265 also set that file's record `error` (as imp:249–251 does for invalid UTF-8), for example `an (import ...) form in this file was not followed`. The record keeps its path, hash, size and mtime and still contributes its closure line.
- **Files**: `imp` (260–265; new resolver test with a wrapper file); D42:309 (`error` field: add the case); P11:551.
- **Build contract**: yes.
- **Consequence**: `records[].error` non-null no longer implies the file was not read or hashed — already the case for invalid UTF-8. Dossier `status` is unaffected (already `incomplete`).
- **A check must reject**: a wrapper record indistinguishable from the record of a file whose import forms were all followed.

### T5 — Correct statement P11:547 without a product change (account correction; alternative to T1)

- **Change**: rewrite the sentence to what the helper records today: an unreadable or nonregular file and invalid UTF-8 leave an error on the record; a bound sets `truncated`; a cycle sets `cycle`; an import form whose argument is not a string literal is not followed and leaves no trace in the helper inventory.
- **Files**: P11:547, regenerated RESP. No build-contract input.
- **Consequence**: withdraws a commitment that is one release old (`f6551bf9`) and that the frozen guide never made. The scanner keeps a distinction it computes and the helper keeps discarding it. Users of the standalone helper must read the source to know whether the list can be partial.
- **A check must reject**: nothing behavioral; `source_drift` checks the regenerated copies.

### T6 — State the instrument's limit in its owners (account correction; independent of T1–T4)

- **Change**: put sentences L-A, L-B and L-C of A.4 beside the technical claims: P11 "Literal import evidence scope" (585), P11 `records` (551), P11 `policy_closure_sha256` (563), D42 `status` (229), D42 "Retained scan scope" (263), D42 "Held input and file observation scope" (83).
- **Files**: P11, D42; regenerated RESP, `docs/CONTRACT.md`, `docs/contract/public.json`. No build-contract input.
- **Consequence**: none for behavior. The statements stop inviting "complete = what the compiler read".
- **A check must reject**: nothing behavioral. The limit is pinned by the T9 contrasts that assert present behavior for O1 (record without evaluation) and G6 (evaluation without record or flag).

### T7 — Correct the closure statement (account correction)

- **Change**, P11:563 second and last sentences: a line is contributed by every record that carries both a resolved path and a hash, including a record whose `error` reports that its text could not be scanned or (with T4) fully followed; records without a hash — unresolved, unreadable, nonregular, depth-limited — contribute none.
- **Files**: P11:563; regenerate. No build-contract input.
- **Alternative**: change `compute_closure_hash` to skip error records. Rejected: it changes published digests and discards a hash of bytes that were read; imp:38–42 says not to change the framing without a deliberate format change.
- **A check must reject**: (T9) a closure that differs from an independent recomputation for the invalid-UTF-8 case.

### T8 — Correct the evidence-scope clause and the support owner (account correction)

- **Change**: remove "Native compilation examples establish their selected literal imports" from P11:585. After T9 lands, the subtree support at P11:596–604 may cite the new checks with their limit: constructed inputs, the helper's host-side compiler, evaluation shown by a diagnostic naming the file, on the tested OS build.
- **Files**: P11:585, 596–604; regenerate. No build-contract input.

### T9 — Assertion and coverage repair

- **C-H, helper contrasts** in `cli` (case `integration/cli.integration`; not a build input). One test builds a temporary directory with `marker.sb` and the wrapper files and sends each contrast to the shipped helper:

  | Contrast | Native witness asserted | Inventory asserted (after T1–T4) | Behavior rejected |
  | --- | --- | --- | --- |
  | no import | `ok` | no records, flag false | — |
  | literal followed | diagnostic names `marker.sb` | one record whose hash equals an independent hash of the file; flag false | — |
  | computed argument | diagnostic names `marker.sb` | no records; flag **true** | today's envelope (no key) |
  | nonliteral inside an imported file | diagnostic names `marker.sb` | wrapper record only, with hash and (T4) error; flag **true** | today's envelope |
  | trailing-comment literal | diagnostic names `marker.sb` | `marker.sb` record; flag false | today's `records: []` |
  | unevaluated form `(if #f …)` | `ok` (evaluation would fail) | `marker.sb` record; flag false — asserts the stated limit | a silent change of what a record means |
  | aliased `import` | diagnostic names `marker.sb` | no records; flag false — asserts the stated limit | — |
  | invalid-UTF-8 import | compile error in that file | record with hash and error; closure equal to an independent recomputation that includes its line | T7's statement being false |

  Assert only that the diagnostic contains the file path; its wording is the OS's. The closure is recomputed without calling `compute_closure_hash`.
- **Replace the assertion that cannot fail** at cli:1513–1516 with: each record hash equals an independent hash of its `resolved_path`; the closure equals an independent recomputation; the transitive `dyld-support.sb` record is present. In the same rebuild as T1–T4, delete or rename the unit test at imp:447–453 (the comment at imp:346–349 already states that the two hashes always differ).
- **C-U, unit tests** (in `lex`, `imp`, `chk`, `dos`; build inputs, same rebuild): one lexer test per row of the 0.3 table; a resolver test with a wrapper file that reaches imp:259–265; an `unfollowed` variant in `inventory_variant` asserting the wire key true and false and verdict independence; dossier cases for a computed argument without a space (G19) and a trailing-comment literal.
- **C-D, dossier contrasts** in `tests/suites/witness_contract/check_dossier.py` (case `witness_contract/dossier_witness`; live; not a build input): computed import → `incomplete`, no records; literal import of a wrapper file → `incomplete` and (T4) the wrapper record's error; trailing-comment literal import of `marker.sb` → record present and the worker compiler's diagnostic naming `marker.sb` in the run's failure text (the review's DT-33 records `result.error` carrying the worker compiler's message for an unresolved import; confirm the carrying field when writing the control); `(if #f (import "<benign file>"))` → `complete` with the record and a finished run. This is the first registered execution of the dossier consequences in DT-83 and DT-84 and the first registered observation of the *worker's* compiler for these spellings. Update `tests/suites/witness_contract/README.md` ("Specimen dossier", ~1565–1572).
- **Order**: the plan requires exercising a revised test against existing behavior first. Run C-H and C-D against the present app before the product edits and keep the expected failures (missing key; `records: []` for the trailing-comment literal; `complete` for it in the dossier).

### Candidates considered and not recommended

- **T10 — a token-mention signal**: set the flag whenever the symbol `import`, `load` or `eval` occurs anywhere outside a followed form. It would flag G6, G7, G8, G9, G25. It cannot flag G21, where no such token exists, and it needs more of the private reader's token rules. The limit sentence is required with or without it.
- **T11 — observe the compiler's file reads**: no supported in-process observer exists for `sandbox_compile_string`; the worker's compile is the one that matters for a run, and adding an observer there conflicts with runner simplicity. The plan's bounded decision already excludes a new compiler-file observer.
- **T12 — a dedicated boolean in the dossier `Imports`**: with T2–T4 a top-level unfollowed form is always the dossier's `failure` (imp:316 assigns it before any walk) and a nested one is on its record. A dossier field would add `dos` constructors, D42, `tests/fixtures/contract/surfaces/dossier.json`, two more `envelope_shape.json` subtrees, `check_dossier.py:238`, `tests/lib/blackbox.py:82` and `rf` fixtures for no additional distinction.
- **T13 — a constant label saying the inventory is a text scan**: a field that is always the same value observes nothing; the statement belongs in the contract text (T6).
- **Projecting `failure` and `exceeded` into the helper** (DT-81.t9, t10): no statement promises them, and after T1 and T4 each cause has its own carrier.

## A.4 Recommended disposition per claim

Recommended set: **T1 + T2 + T3 + T4 in one signed rebuild, with T6, T7, T8 and T9**. T5 is the fallback only if the rebuild is declined. Reason: the scanner already distinguishes "saw an import form and did not follow it" from "no import form", and the helper discards it; the standalone helper is the one place a user has no dossier beside it. An inventory that is the no-import inventory while the compiler evaluates an imported file is the silent best-effort list that "witness over interpretation" and "no dishonest attribution" argue against. The instrument's limit (T6) is decided separately and does not depend on the repairs: no repair turns a text scan into an observation of the compiler.

Accepted-limit sentences (wording is the implementer's; the content is the disposition):

- **L-A** (P11 "Literal import evidence scope", replacing the "Native compilation examples" clause): *The inventory is a scan of source text and of the files that scan read. It is not an observation of the compiler's file reads. A record states that the scan found that literal name and read those bytes during its walk, not that the compiler evaluated the form or read the file. An inventory with no record and no unfollowed form does not state that the compiler read no file: SBPL is evaluated, a policy can cause a file to be read through a computed argument, a rebound or applied `import`, `eval` or `load`, and the scan recognizes only forms headed by `import`.*
- **L-B** (D42 `status`): *`complete`: every import form the scan recognized was followed and the walk ended with no unresolved name, read or decoding error, cycle or bound. It describes the scan, not the compiler's inputs.*
- **L-C** (P11 `records` and `policy_closure_sha256`; D42 `closure_sha256`): *Literal names are collected in every syntactic position, including forms the compiler does not evaluate. The closure digest identifies the source and every file the scan hashed; it does not encode `truncated`, `cycle`, record errors or the unfollowed flag, and it is not a digest of the compiler's inputs.*
- **L-D** (P11 "Literal import inventory" subject): *The helper inventory carries no first-problem text and does not name which bound was reached; each cause is read from its own field.*

| Claim | Disposition | Reason | Discriminating check, or why none is needed |
| --- | --- | --- | --- |
| DT-29.a, DT-81.a, DT-81.b, DT-81.t7, DT-82.a, DT-82.d | Product change T1; P11:547 rewritten with it | Contradicted commitment; the information exists and is dropped | New C-H "computed argument" in `integration/cli.integration`; `unit/rust.unit` variant; shape via `blackbox_e2e/checker_controls` |
| DT-29.b | Retain; L-C | The digest is defined over source and hashed files only | None needed: deterministic algorithm, 42 recomputations matched |
| DT-29.c | Closed by T1 (comment imp:113–115 updated) | Mechanism | — |
| DT-29.d | No action | Discharged by DT-82 | — |
| IC.a, IC.b, IC.d, IL.a, IL.b, IL.f | No action; record that the review's outputs are absent and that 0.3 is a gitignored reproduction | Availability, not a product matter | C-H and C-U become the durable evidence |
| IC.c | Adopt the marker diagnostic as the native witness in C-H and C-D, with its limit | It is independent of the private capture view | — |
| IC.e, DT-82.c | No action here; method note: contrasts must not rely on allow-default bytecode | Belongs to DT-103 (receipt pass); no import decision depends on it | Further bytecode evidence would not change a decision: M2, N2, L2 and O1 are diagnostic-based |
| DT-81.t1–t6 | No change | Accurate; each has a carrier | Existing `unit/rust.unit` resolver tests |
| DT-81.t8, DT-83.a | Product change T1 (flag is already set for nested forms, imp:261) and T4 | Same commitment; the record should say which file | C-H "nonliteral inside an imported file"; C-U resolver test |
| DT-81.t9, DT-81.t10 | Reasoned retention; L-D | No statement promises them; each cause has a carrier after T1/T4 | None needed |
| DT-81.c | No change beyond the T2/T3 comment updates | The comment speaks of code consumers | — |
| DT-81.d, DT-87.b (guide), DT-87.c (guide) | No action: frozen | The guide's narrower promise stays true; the closure framing and the empty-list reading are user duties (A.5) | — |
| DT-81.e, DT-83.f, DT-84.f | No action | History; one imprecision noted | — |
| DT-82.b, DT-83.c | Adopt as C-H cases | Reproduced | C-H |
| DT-83.b | Account: P11:551 states that scanning collects import forms and that an unfollowed form is reported by the flag and the record error | "Scanned" read as "fully followed" | `source_drift` for the regenerated copy |
| DT-83.d, DT-86.f | Coverage repair C-U | imp:259–265 has no test; lexer has no computed or commented form | `unit/rust.unit` |
| DT-83.e, IL.d | Coverage repair C-D | The nested dossier result has never been executed | `witness_contract/dossier_witness` |
| DT-84.a, DT-84.b | Product change T2 and T3 | A literal import the compiler evaluates is neither recorded nor flagged | C-H "trailing-comment literal"; C-U table tests |
| DT-84.c | Covered by C-D | R2 was one unregistered run whose output is gone | `witness_contract/dossier_witness` |
| DT-84.d | Account: L-B at D42:229; D42:51 and D42:263 reworded to "import forms the scan did not follow" | The definition must name the scanner's grammar as its basis | — |
| DT-84.e | Followed after T3 (G1) | The compiler evaluates that spelling | C-U |
| DT-84.g | Scope T2/T3 by the 0.3 table; state that the followed set is established for macOS 26.7.1 (25G241) only | The native reader's grammar is private | C-H runs against whatever OS the battery runs on and re-establishes the set |
| DT-85.a, DT-85.b, DT-85.c, DT-85.d, DT-85.h | Reasoned retention; L-A and L-C | Evaluation is undecidable from text; dropping nested forms would lose imports that are evaluated (G12) | C-H "unevaluated form" asserts present behavior |
| DT-85.e, IL.c | Retain as a stated unknown inside L-A ("evaluated the form or read the file") | No observer of file opens exists | No further evidence obtainable without T11 |
| DT-85.f, DT-85.i | No change | Accurate | — |
| DT-85.g | Account correction T8 | The clause credits examples that do not exist | After T9, cite C-H with its limit |
| DT-86.a | Support stays `source_read` until T9 lands, then cite checks (T8) | The grade is honest today | — |
| DT-86.b | Assertion repair (T9): replace cli:1513–1516; remove imp:447–453 with the rebuild | An assertion that cannot fail is credited in its message to import resolution | The replacement rejects a wrong record hash, a wrong closure and a missing transitive record |
| DT-86.c, DT-86.d, DT-86.e, DT-86.g, DT-86.h | No change to the existing tests; extend per T1/T9 (`inventory_variant`, `checker_controls.py:50–51`) | Accurate descriptions of what each establishes | — |
| DT-86.i | Coverage repair C-H; the second half ("what the compiler read") is closed only to "what the compiler evaluated" | File reads stay unobserved (L-A) | C-H |
| DT-87.a | Account correction T7 | Producer behavior is the better behavior; the statement's last sentence is false | C-H "invalid-UTF-8 import" |
| DT-87.b (P11:378) | Small account addition with T1: the flag says whether the scan saw a form it did not follow | Accurate today; needs the pointer once the flag exists | — |
| IL.e | Record per item: bounds, unreadable and FIFO stay unit-level; collisions and in-run file changes stay unexercised (Subject B); spellings exercised in 0.3; worker-side compilation becomes C-D | — | C-D |

## A.5 Resulting user duties

Present tense, for the recommended disposition; D5 states the duty while the current app is in use.

- **D1 (every inventory; no output indicates it).** Do not conclude from an empty or flag-free inventory that the compiler read no imported file, and do not conclude from a record that the compiler evaluated or read that file. Standing: established (M2, G6–G9, G21, O1 by constructed helper runs; R2/R4 by the investigator's live runs).
- **D2 (helper `unfollowed_imports: true`; dossier `status: "incomplete"`).** Treat `records` as partial. The envelope does not carry the source text: keep the request and find the unfollowed forms in it. Standing: established after T1–T4 are verified.
- **D3 (closure digests).** Use the framing in RESPONSE (source, byte 0x1F, sorted `path sha` lines) to recompute. Equal closures do not establish equal compiled inputs; different closures do not establish different compiled profiles (Od and A). Standing: established for the framing (42 recomputations); the Od/A compile equality rests on the review's bytecode probe.
- **D4 (escapes and unusual spellings).** A literal import written with a backslash escape other than `\"` or `\\` is reported as unfollowed, not resolved. Standing: follows from T3.
- **D5 (current app, build `2f4d76e4` and earlier).** The standalone helper's inventory carries no trace of a computed or otherwise unfollowed import; read the source for `import`, `load` and `eval` before relying on the list. Standing: established (C, M2, L2 and the G cases).
- Developers: none beyond the working guidance in A.6.

## A.6 Implementation worklist

1. **Tests first, no build input.** Add C-H to `controller/integration/cli_contract.rs` and C-D to `tests/suites/witness_contract/check_dossier.py`. Run `tests/run.sh --case integration/cli.integration` and `--case witness_contract/dossier_witness` against the present app with a fresh `PW_TEST_OUT_DIR`; keep the expected failures as the pre-change observation.
2. **`controller/src/sbpl_lex.rs`** (build input): T2 recognition and flagging; T3 following, character literals and the escape rule; doc comments 11–33, 73–80; unit tests per 0.3 row; decide `handles_unterminated_form_without_panic` (310–318).
3. **`controller/src/sbpl_imports.rs`** (build input): T4 at 260–265; failure strings at 263 and 316 if reworded; comment 113–115; resolver test with a wrapper file; remove or rename the test at 447–453.
4. **`controller/src/bin/sbpl-check.rs`** (build input): T1 at 83–92 and 347–355; `inventory_variant` and its test; shape fixture 1090–1102.
5. **`controller/src/run_flow.rs`** (build input): fixture `sbpl_check_envelope` (3998–4013).
6. **`controller/src/dossier.rs`** (build input): doc comment 114–117; test 1426–1464 gains the G19 and trailing-comment cases and follows any failure-text change.
7. **Goldens.** Replace `tests/fixtures/contract/envelope_shape.json` from the candidate the unit test writes; the reviewed diff is one added key in two subtrees. Update `tests/suites/blackbox_e2e/checker_controls.py:50–51` and add a rejected control with a wrongly typed flag.
8. **Contract inputs.** `docs/contract/11-policy.surface.md`: new field under "Literal import inventory"; 547 (statement), 551 (records), 563 (T7), 378 (clause), 585 (L-A, T8), 596–604 (support after checks exist). `docs/contract/42-dossier.surface.md`: 51, 229 (L-B), 233 (L-C), 263, 309 (T4), 83. No `presentation.json` change: no subject moves.
9. **Regenerate.** `tests/lib/python.sh docs/generate_contract_stamps.py --refresh-shapes`, review `tests/fixtures/contract/surfaces/policy.json`; then `tests/lib/python.sh docs/generate_contract_stamps.py`; then `--check` for the contract, limits, architecture and build generators. The guide stays frozen; development checks compare it with its `3d3f8e65` bytes, and strict publication stays withheld. If the free-text baseline (`docs/contract/free_text.json`) refuses the change, revise that rule with its controls as the plan directs.
10. **Test documentation.** `tests/suites/witness_contract/README.md` (dossier section); a route row in `tests/CHANGE-VERIFICATION.md` "Find verification for a change" for "import scanner grammar, resolver flags or helper inventory projection" naming `unit`, `integration`, `witness_contract/dossier_witness`, `blackbox_e2e/checker_controls` and `source_drift`.
11. **Signed rebuild**, then routed verification from `controller/AGENTS.md` "Verify the changed boundary": `unit/rust.unit`, `unit/rust.fmt`, `integration/cli.integration`, `witness_contract/dossier_witness`, `failure_boundaries/fallback_helper` (refusal path keeps null groups), `blackbox_e2e/checker_controls`, and the `source_drift` suite (`build_contracts`, `generator_contract`, `limits_documentation`). The order-barrier mutation control is not triggered: no wait, release store or eligibility rule changes. Group the rebuild with other signed-app verification as the plan's sequence says.

If the rebuild is declined, steps 1 (C-H asserting present behavior), T5, T6, T7, T8 and the `cli` assertion repair can land without any build-contract input.

---

# Subject B — the two unnumbered import/receipt investigations: import side and the shared source/file-input question

`U1` is "Additional investigation: interdependencies of import inventories and compiled-profile receipts" (review 8384–8577). `U2` is "Follow-up investigation: boundaries of the shared import and receipt interpretation" (review 8579–8759). Rows whose substance is the receipt (DT-98, DT-103 internals, "consumed input bytes", "identifies compiler output") are listed only where they meet the shared question and are marked *receipt pass*.

## B.1 Claims table

### First investigation (U1)

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| U1.o1 | Nothing observes the compiler's file inputs; the dossier walk and the receipt share only the source digest, "and I found no reader that compares the two". | `run` envelope | first half yes (imp:6–7; dos:114–117; P11:573–577). Second half no: tests compare the reply's `policy_sha256` with the dossier's `applied_sha256` (`check_dossier.py:161`, `:202`; cli:1293, 1460–1464; `tests/suites/runner_use_c_worker/run.sh:706`) and the receipt's source digest with the request source (`tests/suites/witness_contract/check_actor_compositions.py:132`); the host checks the worker's digest (`runner/Sources/PWRunnerCore/CWorker.swift:706–710`) | SRC | First half AO; second half UI (narrowed by U2.N1, and further here) |
| U1.o2 | One ordinary `run` envelope can report `complete` with no records beside a captured receipt whose bytes match a compilation that included the imported rule, and whose applied policy refused the write that rule denies (R2/E2); R4/E4 is the reverse. | `run` envelope; worker | unverifiable by reading; dossier half consistent with source and MODEL; helper analogues reproduced (L2, O1) | LIVE-R | AO; observed only against known baselines (U2) |
| U1.o3 | DT-103 limits only the bytecode parts of the import findings; each import finding has evidence independent of the private layout. | evidence dependency | yes — M2, N2, L2, O1 are diagnostic or compile-success based | HX | AO |
| U1.o4 | DT-82 never appears beside a receipt in a `run` envelope; in a run the dossier keeps the signal the helper drops. | `run` envelope | holds within the scope U2.4d states — rf:360–368, 374–394, 699–701, 715–724; `controller/src/runner_client.rs:651–661` | SRC | AO as narrowed by U2.N7 |
| U1.1-82 | DT-82 arises in the helper's projection; the lexer flags the form and the resolver sets the flag. Not observed: file opens; the dossier (source and unit test only). | — | yes; the dossier for a top-level computed import was later executed (R3) | SRC; HX | AO |
| U1.1-84 | DT-84 arises in the lexer grammar; a miss returns `None`. Evidence is the diagnostic only. Not observed: the dossier result, worker compilation. | — | yes; both later executed once (R2, E2) | SRC; HX; LIVE-R | AO |
| U1.1-85 | DT-85: the lexer collects literal names in every position, designed and tested. Not observed: whether the compiler opened the file. | — | yes | SRC; HX | AO |
| U1.2a | `applied_sha256` covers the selected source string, computed by the controller before delivery, checked against "nothing found". | `run` envelope | computation yes (rf:607–613; dos:75–93); "nothing" is incomplete — tests compare it (see U1.o1) | SRC | IMA (product readers: none; test readers: several) |
| U1.2b | `imports.{status, records, closure_sha256}` cover the source and each walked file as read then; the consumer checks shape only. | `run` envelope | yes — `tests/lib/consumer.py:994–999` checks the status vocabulary, the list type and the unrun-scan rule | SRC | AO |
| U1.2c | No component computes "imported bytes the worker's compiler consumed". | all processes | yes | SRC | AO |
| U1.2d | The helper inventory and verdict are in a run envelope only when fallback is eligible (client `xpc_error`), when there is no admitted receipt. | `run` envelope | yes for the first half (`runner_client.rs:651–661`); the second half rests on DT-116 (transport pass) | SRC | AO |
| U1.2e | The separation is documented: each digest belongs to its own read and "final equal hashes do not establish read ownership or simultaneity"; neither walk identifies what the worker's compiler read; `complete` "does not mean compiler-complete". | P11, source comments | partly — the rendered public text is the effect sentence and the prose (P11:573, 577; RESP:872–874). The quoted "final equal hashes…" phrase is a `retained_free` authoring reason at P11:574 and appears in no rendered document (`grep` finds it in none of `docs/RESPONSE.md`, `docs/CONTRACT.md`, `docs/contract/public.json`). The other two are source comments (imp:6–7; dos:117) | SRC | AO for the files; OCC as public documentation |
| U1.2f | The dossier walk always runs before delivery, so a window for a file to change exists by construction; nothing exercised a change inside one run. | controller, time | yes — rf:609–613 precedes rf:678–686; still unexercised | SRC | AO |
| U1.3a | R0–R4: dossier `complete`/0, `complete`/1, `complete`/0, `incomplete`/0 with the nonliteral failure, `complete`/1; receipt bytes 492, 548, 548, 548, 492. | `run` envelope | unverifiable by reading; dossier values consistent with source and MODEL | LIVE-R | AO |
| U1.3b | E0, E1, E2, E4: with the imported deny rule evaluated (E1, E2) the create fails with errno 1 and the target is absent; without it (E0, E4) the create succeeds. | worker attempt; file system | unverifiable by reading | LIVE-R | AO |
| U1.3c | The query was `prediction_unavailable`; attribution of the refusals to the applied policy rests on the matched contrast; no kernel log or query observed the denial. | — | as stated; the product makes no cause claim | LIVE-R | AO (the attribution is the investigator's inference) |
| U1.3d | DT-84's dossier consequence and its effect on the worker's compilation are now executed. | — | once, unregistered, outputs absent | LIVE-R | AO |
| U1.3e | E2/E4 show the worker's applied policy included or excluded the imported rule without the 24-byte view; they do not show that the captured bytes are what apply consumed. | — | as narrowed by U2.N3 | LIVE-R | AO |
| U1.3f | R1–R3's bytes equal DT-98 run 1's bytes, so "the bytes carry neither the import path nor the split". | captured bytes | narrowed by U2.N4: true only for arrangements evaluating the same rules in the same order | LIVE-R | UI as written |
| U1.4a | DT-103 is a premise for the bytecode parts of DT-82 and DT-85 and for interpreting DT-98. | — | yes | — | AO |
| U1.4b | DT-103 is not a premise for M2, L2, O1, E2/E4 or DT-98's field-level claim. | — | yes for the import items (HX) | — | AO |
| U1.4c | In DT-98 the dossier closure changed with the bytes, which looks like confirmation; R4 shows the closure can cover a file the compiler never evaluated, so the co-variation establishes no association. | closure vs bytes | consistent with O1 and Od | LIVE-R; HX | AO |
| U1.4d | DT-84 and DT-85 share the lexer's grammar and reach the helper and the dossier identically. | — | yes — one resolver (imp), two projections | SRC | AO |
| U1.4e | DT-82 has a different mechanism: the lexer flags the form, the helper projection loses it, the dossier keeps it (R3). | — | yes; not true of every computed spelling: G19 is not flagged even internally (Outside the review) | SRC; HX | AO, with that exception |
| U1.4f | Different mechanisms leave one question unanswered: which file bytes did this compilation consume. | — | yes | — | AO |
| U1.4g | `complete` plus a captured receipt with a matching source digest invites "compiled from this source, these parameters and these files"; R2 and R4 are executed counterexamples in which every field checks out. | reader inference | yes as a statement about inference | LIVE-R | AO; the inference is what L-A and L-B exclude |
| U1.5q1a | Even with a complete literal inventory, whether the compiler read the same bytes is unobserved: the walk is a separate, earlier read. | — | yes; narrowed by U2.N5 | SRC | AO |
| U1.5q1b | Which search directory the compiler used is unknown; `BTLEServer.sb` is in both directories, which "contradicts" the resolver comment. | host file system | no as written; see U2.4a | SRC (stat) | UI ("contradicts"), corrected by U2.N6 |
| U1.5q1c | The receipt would still carry no import identity. | receipt | yes (*receipt pass* owns the receipt statement) | SRC | AO |
| U1.5q2 | Every reported digest can be accurate while their apparent association stays unestablished (R2, R4). | — | yes | LIVE-R; HX | AO |
| U1.5q3a | Observed by no component: the compiler's file reads; the form DT-84 misses is not known even internally. | — | yes (MODEL L2: `scan_complete` true) | SRC; MODEL | AO |
| U1.5q3b | Observed but dropped: DT-82. | helper | yes | SRC | AO |
| U1.5q3c | Meaning: DT-85's records are accurate as reads and wrong as imports; the guide's "a source with no imports is an empty list" is contradicted by R2 and R3. | — | yes; the guide sentence is frozen | SRC | AO |
| U1.5q3d | Judgment: DT-84 is the only case where the dossier's own definition fails on a natural reading; DT-82 and DT-85 do not contradict it. | D42:229 | agreed for those three; G19 and the other unflagged spellings fail it the same way | SRC; HX | AO, with additions |
| U1.5q4 | Each finding stays meaningful without the others; DT-82's relevance to what was compiled is limited to the standalone helper and fallback captures. | — | yes | — | AO |
| U1.6 | Narrower formulation: no field observes the compiled bytes' file inputs; the dossier identifies a walk made before delivery; the receipt identifies the compile's arguments and output; the only shared term is the source digest, "which no reader compares". | — | first three sentences yes; the fourth is corrected by U2.N1 | SRC | AO / UI (fourth sentence) |
| U1.7 | Arrangement judgment: not an unmet promise; the disclaimers sit on the inventory side, the receipt's owner and the guide do not point at the inventory's limits; R2 is the concrete cost. | P11, 35-profile, guide | disclaimers located as stated (P11:573–577; `docs/contract/35-profile.surface.md:394` says "consumed input bytes"; GUIDE:746) | SRC | AO (judgment; placement on the receipt side is the *receipt pass*'s) |
| U1.8 | Keep distinct: stages (lexer grammar, helper projection, walk reads, compiler evaluation, file opens, capture, application); host-side and worker compilations; changes between runs and within a run; equal bytes and same files. | — | adopted | — | AO |
| U1.L | Limits: single runs per case, no file-access tracing, the query unavailable in E; R4 shows non-evaluation, not that the file was unopened; scripts and outputs in a scratchpad. | — | outputs absent | — | AO |

### Follow-up (U2)

| Id | Claim | Boundary | Holds at HEAD? | Evidence | Class |
| --- | --- | --- | --- | --- | --- |
| U2.o | The interpretation holds as a description of a documented separation; divergence was observed only through the DT-84 and DT-85 mechanisms and only by comparison with runs of known composition; no single envelope shows it. | — | yes | — | AO |
| U2.1a | The source association holds by construction: the dossier is built from the resolved request value, that value is serialized once and delivered, the host checks the worker's digest against what it received; the three digests were equal in every run. | controller, host, worker | yes — rf:607–613, 678–686; `CWorker.swift:706–710` | SRC | AO |
| U2.1b | One test joins the receipt to the request source. | test | yes — `check_actor_compositions.py:132`; others join the reply's `policy_sha256` to `applied_sha256` (U1.o1) | SRC | AO, incomplete list |
| U2.1c | The envelope carries `specimen.request_path` and digests, not the source text; a reader needs the retained request and can check it against `original_sha256`. | `run` envelope | yes — D42:104, 181–187 | SRC | AO; becomes a user duty |
| U2.1d | Case table: R0/E0 nothing to associate; R1/E1 divergence not observed, possible by construction, unsignaled; R3 signaled; R2/E2 observed only by contrast, not signaled; R4/E4 observed by contrast between record and compiled content. | — | unverifiable by reading; consistent with source | LIVE-R | AO |
| U2.1e | Without a scanner miss two facts remain: the receipt names no files and the walk is a separate earlier read; no run with an ordinary literal import showed divergence; a change within one run and the directory a relative name resolves to were not exercised. | — | yes; still unexercised | — | AO |
| U2.1f | An expected object made by compiling the same source on the same host would match R2's bytes and not reveal the missed import (reasoning, not run). | reader practice | not executed; follows from compilation being a function of source and files | — | UI until executed; plausible |
| U2.1g | The formulation's first three sentences hold; the fourth should say the source association holds by construction; any claim of unsignaled divergence should name DT-84 and DT-85 as the only observed sources. | — | adopted; after 0.3 the DT-84 class has more members | — | AO |
| U2.2b | Arrangements that evaluate the same rules in the same order gave identical bytes; for them the import identity cannot be recovered from the bytes. | captured bytes, this build and OS | unverifiable by reading | LIVE-R | AO (*receipt pass* for the bytes) |
| U2.2c | Not supported: that compiled bytes never carry import-path information; `joint-2` and `joint-3` differ only in a directory name and their outputs differ, attributable to the rule's literal. | captured bytes | unverifiable by reading | LIVE-R | AO |
| U2.3a | With a sibling path that no rule names, the imported rule's effect — refusal confined to its literal path — was in force in E1 and E2 and absent in E4; the refusal follows compiler evaluation, not the dossier. | worker attempt; file system | unverifiable by reading | LIVE-R | AO (matched-contrast inference, stated as such) |
| U2.3b | Not supported: how the compiler got the file; which bytes application consumed; the mechanism in kernel terms; breadth beyond one operation, one deny form, one pair of paths. | — | yes | — | AO |
| U2.4a | On this host `BTLEServer.sb` is the only name in both search directories (59 and 511 entries) and the two paths are one file: same device and inode, link count 2, 3398 bytes. A changed condition, not a contradiction; the comment's conclusion still holds. | host file system | yes — `stat` now: inode `1152921500312489006`, 2 links, 3398 bytes, entry counts 59 and 511; device is `16777232` today, not `16777233` | SRC (stat) | AO |
| U2.4b | The contract already carries this limit: the directory order is "a platform convention"; search-order observations are "inherited from the source comments, not reproduced here". | P11:585, 603 | yes | SRC | AO |
| U2.4c | Both search directories are on the read-only system snapshot, so files there cannot change between the walk and the compile within one boot; the in-run window matters for imports outside it (inferred from the mount; writes not tested). | host | not tested here | — | UI until tested; plausible |
| U2.4d | "DT-82 never appears beside a receipt" holds for both request forms within the examined callers, eligibility rule and fields; external runners were not examined separately. | `run` envelope | yes for the cited lines | SRC | AO |
| U2.4e | Outside that scope: the guide documents running `sbpl-check --request` on the same saved request, which puts the helper's projection beside a receipt in the reader's hands; a fallback envelope also contains the dossier, so the two would disagree for a computed import (source reading, not executed). | reader practice; fallback envelope | yes — GUIDE:768–772; rf:699–724 | SRC | AO; the fallback disagreement is unexecuted |
| U2.N1 | Review 8397, 8535 — "which no reader compares" → the source join holds by construction; nothing joins records to compiled inputs. | — | adopted; additionally, tests do compare the digests (U1.o1) | SRC | qualification |
| U2.N2 | Review 8398, 8556 — R2 as the concrete cost → holds; observed divergence comes only from DT-84/DT-85; ordinary literal imports give an unverified association. | — | adopted | — | qualification |
| U2.N3 | Review 8477 — E2/E4 show the rule included or excluded → supported and confined to the rule's path; still a matched-contrast inference; says nothing about which bytes apply consumed. | — | adopted | — | qualification |
| U2.N4 | Review 8478 — "bytes carry neither the import path nor the split" → true only for arrangements evaluating the same rules in the same order; bytes do carry rule-supplied paths. | — | adopted | — | qualification |
| U2.N5 | Review 8436, 8508 — "separate, earlier read" → matters for imports outside the sealed system snapshot. | — | adopted as an inference from the mount | — | qualification |
| U2.N6 | Review 8509 — "contradicts the 14.8.3 comment" → a changed condition; one file under two names; the comment's conclusion holds. | — | adopted; re-verified by `stat` | SRC | qualification |
| U2.N7 | Review 8400, 8528 — "DT-82 never appears beside a receipt" → holds for `run` envelopes in the examined callers; the guide's direct workflow pairs them outside an envelope; a fallback envelope puts DT-82 beside the dossier. | — | adopted | SRC | qualification |
| U2.D1 | Four statuses: documented separation (always); unverified association (whenever there are imports); observed divergence (DT-84 and DT-85 only, by contrast); signaled incompleteness (R3). | — | adopted | — | AO |
| U2.D2 | Source join by construction; for the file join no field exists. | — | adopted; the plan's bounded decision | SRC | AO |
| U2.D3 | "Same rules, same order, same bytes" is not "bytes never carry path information". | — | adopted (*receipt pass*) | — | AO |
| U2.D4 | Three different claims: a rule's effect on one path (supported); file opens (unobserved); which bytes application consumed (unobserved). | — | adopted | — | AO |
| U2.D5 | Changed OS conditions are not contradiction; one file under two names is not two files. | — | adopted | — | AO |
| U2.D6 | Appearing together in one envelope is not a reader putting two outputs side by side. | — | adopted | — | AO |
| U2.E | Evidence for `joint-3`: build `8b5de2b2`, one run per case, unregistered; scripts and output in a scratchpad. | — | outputs absent | — | AO |

## B.2 Comparison

**Obligation as stated.** Owner P11:573–577: "Bind each digest to the bytes held by its producing read. The controller dossier walk, fallback helper walk and worker native compiler perform their own reads. Preserve import errors and bounds beside each inventory." and "Files named by imports can change between these independent reads. A literal inventory describes the producer's walk; the worker compiled-profile receipt has its own observation boundary." Owner D42:10: "its import records identify controller file reads … Native compilation, application and execution have their own reports." Owner D42:36: "Serialize the held selected request once and use those bytes for client delivery and whole-request fallback compilation." Owner D42:83: "The dossier scanner and selected-file hashes describe their own reads."

No statement promises an association between import records and the worker's compiled inputs. The obligation is the separation itself.

**Producer.** The controller builds the dossier from the resolved in-memory request (rf:607–613), then serializes that value once (rf:678) and delivers the text (rf:681–686). The host recomputes the source digest over the string it received and refuses a capture whose worker digest differs (`CWorker.swift:706–710`). The import walk is a controller read made before delivery; the worker's compiler reads imported files later, in another process; the helper's walk and compile are a third and fourth read.

**Readers and tests.** Source join: `check_dossier.py:161`, `:202`; cli:1293, 1460–1464; `runner_use_c_worker/run.sh:706`; `check_actor_compositions.py:132`. File join: nothing, and nothing could — no field exists. `consumer.py:994–999` checks the imports object's shape and one relation.

**Observation and inference.**

- Observed (LIVE-R, single unregistered runs): dossier status and records for R0–R4; receipt bytes equal across R1–R3 and across R0/R4; file-create outcomes in E.
- Observed here (HX): the helper-side analogues of R2 (L2), R3 (M2) and R4 (O1).
- By construction (SRC): equality of the three source digests; the existence of a window between walk and compile.
- Inferred: that the E refusals were caused by the applied policy (matched contrast); that system-directory imports cannot change within a boot (mount); that a same-source recompilation cannot reveal a scanner miss.
- Unobserved by any component: the compiler's file opens; the bytes it read; the bytes application consumed.

## B.3 Plausible treatments

- **S1 — reasoned retention of the separation** (the plan's bounded decision): keep held-source association and compiler-file-input association distinct; add no dossier/receipt source-digest comparison, which would only restate what construction guarantees and could not say which imported bytes the compiler read. Files: none in product. The limit is stated by T6 (L-A, L-B, L-C) plus **L-E** below at P11 "Separate reads and their identities". Not a build-contract input.
- **S2 — coverage**: the C-D dossier contrasts of T9 replace reliance on the R/E runs, whose outputs are gone, for the import-side facts (status and records per spelling; the worker compiler's diagnostic naming the file). They do not and cannot establish the file join. Enforcement contrasts of the E kind belong with the receipt pass's capture rehearsal.
- **S3 — arrangement** (shared with the receipt pass): P11 "Separate reads and their identities" is the one owner of the cross-record statement (L-E). The receipt pass's file `I-receipts.md` (its disposition D-INPUT) puts a receipt-side sentence in `docs/contract/35-profile.surface.md` "Captured input identity" (:112) — "No receipt field identifies a file the compiler reads for an `import` form…" — with a link to `#contract-policy-imports-holds`, and narrows the pin at :394. The two placements agree: the receipt subject says what its identity excludes and links here; this rule says that no field joins the two records. The wording of the linked pair should be settled once by whoever lands both edits. Adding L-E as prose adds no `free.*` fact.
- **Not a candidate**: a compiler-file observer (T11); a product check that refuses or relabels a run on an import/receipt mismatch — there is no second identity to compare.

## B.4 Recommended disposition per claim

- **L-E** (P11 "Separate reads and their identities", after "…has its own observation boundary"): *No field of a run envelope or a helper envelope associates an import record with the bytes the worker's compiler read. The dossier's applied-source digest, the reply's policy digest and the receipt's source digest are digests of one held source string; their equality says nothing about imported files.*

| Claim | Disposition | Reason | Check, or why none is needed |
| --- | --- | --- | --- |
| U1.o1 (first half), U1.2c, U1.4f, U1.5q1a, U1.5q1c, U1.5q2, U2.o, U2.1e, U2.D1, U2.D2 | Reasoned retention S1; L-E, L-A | The separation is the stated design; the file join has no observer | A source-digest comparison would not change the decision; it restates construction |
| U1.o1 (second half), U1.6 (fourth sentence), U1.2a, U2.1b, U2.N1 | Adopt the narrowed reading and correct it further: the source join holds by construction **and** is compared by tests at the lines in U1.o1 | The review's "no reader compares" and "nothing found" are mistaken for test readers | Existing: `witness_contract/dossier_witness` (`check_dossier.py:161`, `:202`), `integration/cli.integration` (cli:1293, 1460), `witness_contract/actor_compositions` |
| U1.o2, U1.3a, U1.3d, U1.5q3a, U2.1d, U2.N2 | Accurate observations; the R2 divergence is removed for the observed spellings by T2/T3; the R4 divergence is retained under L-A and L-C | Scanner repairs and the instrument limit are separate decisions | C-D (T9) |
| U1.o3, U1.4a, U1.4b | No action | Dependency map is accurate | — |
| U1.o4, U1.2d, U2.4d, U2.4e, U2.N7 | Adopt the narrowed reading; T1 removes the disagreement between a fallback envelope's helper inventory and its dossier for a computed import | After T1 both carry the unfollowed observation | C-H; the fallback-envelope pairing itself stays unexecuted — it needs a client `xpc_error` and belongs to the transport thread |
| U1.1-82, U1.1-84, U1.1-85, U1.4d, U1.5q3b, U1.5q4 | See Subject A (DT-82, DT-84, DT-85) | Same claims | — |
| U1.4e | Adopt, with the exception that a computed import written `(import(…))` is not flagged today; closed by T2 | New observation G19 | C-U |
| U1.2b | No change | The surface states the relations as produced-field conditions (D42:268), not as a reader check | — |
| U1.2e | Account: L-E puts the non-inference into rendered text; the authoring reason at P11:574 and the two source comments stay | Only one public sentence states the separation today | `source_drift` for the regenerated copy |
| U1.2f, U2.N5, U2.4c | Reasoned retention; the mount inference is not asserted in the contract. Accepted limit, already at P11:577: "Files named by imports can change between these independent reads." | Nothing exercised an in-run change; the read-only inference is untested | Would need a constructed in-run file change during a live run; it would not change the decision, since the contract already disclaims simultaneity |
| U1.3b, U1.3c, U1.3e, U2.3a, U2.3b, U2.N3, U2.D4 | Retain as stated: a rule's effect on one path is supported by matched contrast; file opens and bytes applied are unobserved. The product makes no cause claim and should not gain one | "No dishonest attribution" | *Receipt pass* capture rehearsal for the enforcement side |
| U1.3f, U2.2b, U2.2c, U2.N4, U2.D3 | Adopt the narrowed reading; *receipt pass* owns any statement about bytes | Counter-observation in `joint-3` | — |
| U1.4c | Adopt; reflected in L-C | A closure change is not evidence of a compiled-input change | C-H "unevaluated form" |
| U1.4g, U1.7 | Adopt the judgment that this is not an unmet promise; L-A, L-B, L-E state the exclusion on the inventory side; placement on the receipt side is S3 | The inference is the reader's; the statements must not invite it | — |
| U1.5q1b, U2.4a, U2.4b, U2.N6, U2.D5 | Adopt the corrected reading; no product or account change. The comment at imp:15–24 is scoped to macOS 14.8.3 and stays | One file under two names offers no collision; the contract already calls the order a platform convention | Not checkable by content on this host |
| U1.5q3c | Guide sentence frozen; duty D1 | — | — |
| U1.5q3d, U2.1g | Adopt, extended: every unflagged spelling in 0.3 fails the definition as L2 does | — | C-U |
| U1.8, U2.D6, U1.L, U2.E, U2.1a | Adopt as assessment conventions; no action | — | — |
| U2.1c | Becomes a user duty (B.5) | The envelope cannot show import forms | — |
| U2.1f | Record as an unexecuted inference and a candidate user restraint (B.5) | Not run | A constructed same-source recompilation would settle it; not needed for any product decision here |

## B.5 Resulting user duties

- **D6 (any run whose policy imports files).** Do not read dossier `complete` plus a captured receipt with a matching source digest as "compiled from this source, these parameters and these files". The source digests agree by construction; no field ties an import record to what the compiler read. Standing: established for the absence of the field (source); divergence observed by the investigator's single live runs.
- **D7 (imports outside `/System/Library/Sandbox/Profiles` and `/usr/share/sandbox`).** Keep imported files unchanged from before the run until it ends, or do not treat the dossier record as describing what the worker compiled. Standing: by construction; an in-run change was never exercised.
- **D8 (reading import forms).** Keep the request file; the envelope carries its path and source digests, not the source text. Confirm the file against `original_sha256` / `applied_sha256`. Standing: established (D42:104, 181–187).
- **D9 (comparing compiled bytes; candidate, unsettled).** An expected object produced by compiling the same source on the same host does not check the inventory; its composition must be known independently. Missing: the execution (U2.1f).

## B.6 Implementation worklist

1. Record in `records/TRACE-MANAGEMENT-PLAN.md` the dispositions of B.4, including the correction to U1.o1/U2.N1 (tests do compare the source digests) and the two unexecuted inferences (U2.1f, U2.4c). The review stays unchanged.
2. `docs/contract/11-policy.surface.md`, "Separate reads and their identities" (573–577): add L-E as prose after line 577. Land it with the receipt pass's D-INPUT sentence and link in `docs/contract/35-profile.surface.md` (:112, :394) so the linked pair reads as one statement. Regenerate with `tests/lib/python.sh docs/generate_contract_stamps.py`; verify with `--check` and the `source_drift` suite. No build-contract input.
3. C-D from A.6 step 1 covers the import-side live facts. No other test change is recommended for Subject B.

---

# Outside the review

New observations from the constructed helper runs of section 0.3. They are not review findings; they bear on the scope of T2/T3 and on the limit sentences.

1. **More literal spellings the compiler evaluates and the scan neither follows nor flags** (same class as DT-84): form feed or vertical tab before `)` (G4, G22); a comment touching the string (G23); a comment or nothing between `import` and the string where the atom ends at `;` (G20); whitespace 0x0C or a comment between `(` and `import` (G28, G29).
2. **A computed import that is not flagged even internally**: `(import(string-append …))` with no space after `import` (G19). From source, the dossier would report `complete` with no records for a computed import, contrary to D42:51 ("Mark … nonliteral forms … as incomplete"). Derived, not executed through `run`.
3. **Character literals desynchronize the scan**: after `#\"` or `#\;` a following literal import is not seen (G15, G16).
4. **String escapes are decoded differently**: the compiler reads `\x65`, `\n` and `\t` as the byte, LF and TAB; the scan keeps the letter and records a different name as "not found" (G5, E3, E4). If a file with the scan's name existed, the scan would record a file the compiler did not read, with no error.
5. **Files reach the compilation without any `import`-headed form**: an aliased `import`, `apply`, `eval` with a quoted or constructed symbol (G6, G7, G8, G21), and `load` directly or aliased (G9, G25). G21 contains no `import` token at all, so no scan of text can be made complete. `load` means the instrument's subject — "imports" — is itself narrower than "files the compiler reads".
6. **No native compilation in the tree distinguishes import from no import**: cli:1479, `check_dossier.py:178` and `runner_c_worker_harness/harness.c:452` each compile a source containing `(import "system.sb")` and assert success, which shows that the compiler did not fail on the form and nothing about what it incorporated.
7. **Review details that differ at HEAD**: no `docs/RESPONSE.md` exists at v0.3.6 (DT-81.e); the device number of the two `BTLEServer.sb` links is `16777232` today (follow-up says `16777233`), with inode and link count unchanged; tests compare the source digests the first investigation says nothing compares (U1.o1, U1.2a).

All of these are observations of the helper's host-side compiler on macOS 26.7.1 (25G241). The worker's compiler and other OS builds were not observed.
