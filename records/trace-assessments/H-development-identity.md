# H — Development build identity (DT-08 executed counterpart, DT-88–94)

Read-only assessment at HEAD `837296af`. Coverage-map row: "DT-88–94 — source
inventory, traversal refusal, selected suffixes/roots, framing, metadata and
support", with DT-08 joined to DT-91. One shared subject: what the
`development:<sha256>` form of the public build identity covers, how it is
derived, and what its statement and checks say about that.

> **Identity change — read first.** The recommended DT-89 remedy edits
> `docs/source_identity.py`. That file is a selected input of the public build
> contract (`docs/build_contract.py:19-20`) **and** of the host/worker protocol
> identity (`docs/generate_worker_identity.py:27`). Any byte change to it
> therefore changes `development:<sha256>` for an otherwise unchanged tree,
> changes the worker identity, requires regenerating the three worker-identity
> copies (two of which are under selected roots and change the public identity
> again), and forces a signed rebuild. The framing (prefix, order, length
> encoding) and the inventory of the unchanged readable tree do not change; a
> prototype of the replacement walk returned the identical 119-path and 56-path
> inventories for this checkout. Consequences: the current value
> `development:b55acb20d6a00395f6a422eafef1a4c18fd64e5140b71a1331cbe3b76744719e`
> (the tree at HEAD, the signed app at `dist/`, and the value recorded for the
> `2f4d76e4` build) stops matching the tree; the development-candidate verifier
> refuses the existing app until a rebuild; `tests/lib/contract.py`'s
> `WORKER_IDENTITY` stops matching the existing app's worker; every saved
> specimen asserting the old development identity is refused by the rebuilt app.
> No fix for DT-89 avoids the public identity change: `docs/build_contract.py`
> is also a selected input.

## Evidence base

Abbreviations used in the tables:

- **R-exec** — executed by the review at `458fcbb2` in a disposable clone. Its
  drivers and outputs were under the Claude scratchpad `…/cc77ea91-900e-4bb1-b90b-f9633a3b29b8/scratchpad`,
  which is **absent** now. Only the values printed in the review remain.
- **R-read** — the review's source inspection.
- **H-read** — re-read at HEAD in this pass. `docs/source_identity.py` is
  unchanged since `cbf5f298`; `docs/build_contract.py` gained `docs/publication.py`
  in `FILES` (`bba8bca3`); `00-identity.surface.md` is unchanged since `33806e55`.
- **H-exec** — executed in this pass at HEAD with the pinned interpreter
  (`tests/lib/python.sh`, Python 3.14.9), on a constructed copy of the selected
  files or a literal tree under
  `.tmp/trace-integration/assessments/work-H-development-identity/`. Drivers,
  logs and JSON: `devid_head_controls.{py,log,json}`, `devid_head_rows.{py,log,json}`.
  Gitignored scratch with no retention guarantee; all constructed, no build, no
  registered case, checkout `git status` clean before and after.
- **H-git** — read-only git at HEAD.

H-exec results (full digests in the JSON files):

| Row | Change | Result at HEAD |
| --- | --- | --- |
| H0 | none; checkout, copy, an independent `os.walk` inventory with a raising error handler, and an independent framing | 119 paths; `development:b55acb20…719e` every way; equals `dist/…/policy-witness --version` `build.contract` |
| H1 | `controller/src/interface` mode 0000 (review M4) | exit 0, empty stderr, 114 paths, `development:132ad9da9c7ce44e647e7786f37569965bf7362de11873220686231a04d8b3e8` |
| H2 | `mod.rs` bytes changed, then the directory 0000 (review M4b) | exit 0, the same `132ad9da…b3e8` |
| H3 | the directory mode 0111 (searchable, not listable) | same as H1: 114 paths, `132ad9da…b3e8`. Separately observed: a file in a 0111 directory opens by name while listing fails |
| H4 | the directory mode 0444 (listable, not searchable) | exit 1, `build contract: nonregular identity source: controller/src/interface/run_args.rs` |
| H5 | root `runner/augments` mode 0000 | exit 1, `build contract: missing protocol sources: runner/augments` |
| H6 | new empty directory `controller/src/zz_unreadable_empty` mode 0000 | exit 0, baseline identity |
| H7 | `runner/Sources/PWCWorkerShim` mode 0000 (root shared with worker identity) | build contract: exit 0, 117 paths, `development:052d3324…5a7a`. `generate_worker_identity.py --check`: exit 1, `worker identity: stale controller/tools/pw_probe_runner/pw_probe_runner_abi.h, runner/Sources/PWRunnerCore/CWorker.swift, tests/lib/contract.py; run tests/lib/python.sh docs/generate_worker_identity.py` |
| H8 | `controller/src/main.rs` mode 0000 (review M5) | exit 1, `build contract: [Errno 13] Permission denied: '<copy>/controller/src/main.rs'`; inventory still 119 |
| H9 | dangling symlink `controller/src/zz_dangling.md` | exit 1, `symlink under identity sources: controller/src/zz_dangling.md` |
| H10 | `PolicyWitness.entitlements` replaced by a dangling symlink | exit 1, `symlink under identity sources: PolicyWitness.entitlements` |
| H11 | FIFO `controller/src/zz_control.fifo` (review C3d) | exit 1, `nonregular identity source: controller/src/zz_control.fifo` |
| C1a, C3a, T1, T3 | one byte-level edit in `exec_baseline.sb`, `controller/interface/cards.rs`, a `#[cfg(test)]` module of `porcelain.rs`, `tests/lib/signer_check.py` | each changes the digest; each equals the independent framing |
| C3b, C3c, C1b, C2f | `controller/interface/inventory.json` bytes; `test_inputs/README.md` bytes; mode+mtime of `main.rs`; four names outside the exact suffix | digest unchanged |
| C1c, C2a, C2d, C2e, M3 | rename; eligible addition; eligible file in a hidden `.build/`; nested `.sb`; discoverable file removed | digest changes; inventory 119/120/120/120/118 as the literal expectation |
| M1, M2 | declared `read.json` removed; root left with no selected file | exit 1 `missing identity source: controller/src/test_inputs/read.json`; exit 1 `missing protocol sources: runner/augments` |
| P1 | `docs/publication.py` bytes (selected only at HEAD) | digest changes |
| N1 | `café.rs` written once in NFC and once in NFD (not run by the review) | the volume returns each spelling as written; the two digests differ |
| L1 | literal tree `sel/{Upper.rs,a.rs,sub/b.rs}`, `top.cfg`, declarations substituted on a private module instance | inventory `['sel/Upper.rs','sel/a.rs','sel/sub/b.rs','top.cfg']`; `development:89898dff6ed143459c8de8d18e81ed63a450b050fb0b33024bf5c83762619c79`, equal to a `printf`/`shasum -a 256` computation of the stated framing. With `sel/sub` mode 0000: inventory without `sel/sub/b.rs` and `development:2f7232f8ef3a56b0d466d0351936427406ffbae75fe84e5e766d58a5462ee316`, identical to the tree with `sel/sub` removed |
| L2 | literal tree: root is a directory symlink; directory symlink under root; root is a regular file; declared file is a directory | `symlink under identity sources: sel`; `…: sel/linkdir`; `missing protocol sources: sel`; `nonregular identity source: top.cfg` |
| S1 | prototype walk (`os.scandir` + `os.lstat`, no discarded error) | same inventories as the code for the checkout and the copy (119 public, 56 worker); refuses H1–H7 naming the path; H8–H11 unchanged |

## 1. Claims

Boundary column: input form / representation / observer / time. Unless noted
the input form is a source tree on disk, the representation is the generator's
exit status and printed `development:` value, the observer is the developer or
build running `docs/build_contract.py`, and the time is derivation.

| Id | Claim | Boundary | Holds at HEAD? | Evidence class | Classification |
| --- | --- | --- | --- | --- | --- |
| DT-08.a | The inputs statement lists six discovery roots and omits `controller/interface`, which `DIRECTORIES` selects. | Authored statement vs generator declaration / prose / reader of CONTRACT / any | yes: `docs/contract/00-identity.surface.md:63-65`, `docs/CONTRACT.md:80-82`; `docs/build_contract.py:15-16`. Now also `docs/publication.py` (`build_contract.py:20`) is absent from `surface:66-73` | R-read; H-read | inaccurate mechanism account (statement disposition is recorded by the DT-05–08 pass; the edit is the one in T3 below) |
| DT-08.b | A change to `cards.rs` or `inventory.rs` changes the identity through a root the description does not name. | working-tree bytes | yes | inference in DT-08; R-exec C3a (unavailable); H-exec C3a (`development:2bf2cf9f…e8d0` ≠ baseline) | accurate observation; the account is what is inaccurate |
| DT-08.c | The omission predates the documentation-trace reorganization. | history | yes: `b16f32d0` is an ancestor of `2fcf9dbc` | H-git | accurate observation needing no change |
| Conv.a | Checkout, clone, inventory copy and `git archive` each selected the same 118 paths and gave `bdefcb44…fb18`; per-root counts; all selected paths tracked; eight tracked files under roots unselected; one ignored unsuffixed file; all ASCII. | four trees at `458fcbb2` | **partly**: at HEAD the inventory is 119 paths (19 explicit outside roots) and the value is `b55acb20…719e`; the other facts hold (same eight tracked unselected files, same single ignored file, all ASCII) | R-exec (unavailable); H-exec H0; H-git | accurate observation at its revision; stale values |
| Conv.b | For every successful control the printed value equalled `identity()` and an independent recomputation. | generator output vs independent hashlib | yes for every H-exec row | R-exec; H-exec | accurate observation needing no change |
| Conv.c | Git neither lists nor cleans FIFOs. | `git status`, `git clean -fdx` | not re-run; consistent with this machine's prior observation | R-exec | accurate observation needing no change |
| Conv.d | The 25-control table (expectation column read only from the inputs statement). | disposable clone | the non-Git rows re-ran with the same outcomes (table above); C2b, C2c and `Git` columns not re-run | R-exec (unavailable); H-exec | accurate observation; evidence for the entries below |
| DT-88.a | Selection uses no Git command; the walk includes hidden files and directories; the suffix is the final suffix, compared case-sensitively; `FILES` are added regardless of suffix. | source | yes: `docs/source_identity.py:7,19,22`; `docs/build_contract.py:36-37`; Git only at `:82-90` | R-read; H-read; H-exec C2d, C2f | accurate observation needing no change |
| DT-88.b | The same path and bytes untracked, ignored or committed give one inventory and digest; a file in an ignored directory enters. | Git state of an eligible file | yes by reading; C2a/C2d re-ran outside a repository; C2b/C2c not re-run | R-exec; H-read; H-exec | accurate observation needing no change |
| DT-88.c | A development identity identifies files present in the working tree, not a commit; one rule can select different sets in a checkout and a source copy of one commit; the statements do not say whether untracked or ignored files are selected. | statement `surface:48,63,75` vs behavior | yes | R-exec; H-read | consequential ambiguity ("the same inventory" admits a reading that is false) |
| DT-88.d | The named check excludes its two artifacts by suffix; its first assertion precedes any repository; no cited check adds an eligible untracked or ignored file. | test assertions | yes: `tests/suites/source_drift/build_contracts.py:181-198` (names at `:185`, assertion `:187`, `.gitignore` `:188`) | R-read; H-read | overstated coverage credit (the sentence about checkouts and source copies has no check of Git independence) |
| DT-88.e | Walk, suffix rule and Git independence unchanged since `cbf5f298` (v0.3.6); earlier releases used generated contract versions. | history | yes: `git log -- docs/source_identity.py` has one commit | R-read; H-git | accurate observation needing no change |
| DT-89.a | An unreadable directory under a selected root is omitted with exit 0 and no diagnostic; two trees differing in a selected file under it receive one identity. | directory mode 0000 below a root | **yes**: `docs/source_identity.py:19-25` has no listing check; pinned `glob.py:453-456` and `:505-508` discard the `OSError` | R-exec M4/M4b; H-exec H1, H2, H3, H6, H7, L1 | contradicted explicit commitment (`surface:48` "identifies the selected source paths and bytes"; `docs/REQUEST.md:326`) |
| DT-89.b | Contrast: an unreadable selected file stays listed and fails the read (exit 1, raw errno text); a deleted discoverable file shrinks the inventory without refusal. | file mode 0000; file removal | yes: `build_contract.py:78`, `:122-123` | R-exec M5, M3; H-exec H8, M3 | accurate observation needing no change |
| DT-89.c | In the M4 state `git status --porcelain --ignored --untracked-files=all` exits 0 with empty stdout and warnings on stderr; the generator prints nothing comparable. | Git as second observer | not re-run; matches this machine's recorded Git behavior | R-exec | accurate observation needing no change |
| DT-89.d | The walker checks existence only for roots and declared files and refuses an empty root; the skipped directory was observed with Python 3.14.9 and pathlib's handling was not traced. | source | yes; now traced: `glob.py:452-456` (`select_wildcard`) and `:503-508` (`select_recursive_step`) of the pinned 3.14.9 catch `OSError` from `os.scandir` and continue | R-read; H-read of the pinned stdlib | accurate observation needing no change (its untraced-mechanism limit is closed by this reading) |
| DT-89.e | Limits: whether a packaged build could compile with such a directory was not established; the Rust modules in the example would be unreadable to the compiler too; Meson's `--swift-stdout` and the `inputs(ROOT)` fixtures were not executed in that state. | build in a changed state | unverifiable by reading for a whole build. The second sentence is true for mode 0000 only: with a searchable, unlistable directory (H3) the files open by name and the walker still omits them | R-read; H-exec H3 and a POSIX open/list check; no build run | unsupported inference if generalized beyond mode 0000 |
| DT-90.a | Symlink and nonregular refusals apply to every walked entry before the suffix filter; "nonregular source objects" therefore also covers objects without a source suffix; the same object outside the roots changes nothing. | object kind × location | yes: `source_identity.py:20-25` (suffix tested only inside the regular-file branch `:22`) | R-exec C3d/C3f; H-exec H11 | consequential ambiguity ("source objects" reads narrower than the refusal) |
| DT-90.b | Git lists neither FIFO; a checkout with empty status can fail derivation and `git clean -fdx` does not remove the cause. | Git as observer | not re-run | R-exec | accurate observation needing no change |
| DT-90.c | A symlink named `.md` under a root is refused, as stated. | symlink, unselected suffix | yes | R-exec C3e; H-exec H9 | accurate observation needing no change |
| DT-90.d | Missing-input refusals come only from declared existence (`:15-16`), an empty root (`:26-27`) and a declared non-regular path (`:29-31`); M1 refused; M2 refused with `missing protocol sources` although the root has no protocol role; M3 and M4 not refused; M5 refused by the read, not by the walker. | refusal set and wording | yes | R-exec; H-exec M1, M2, M3, H1, H8, L2 | consequential ambiguity (the empty-root refusal and the read failure are unstated); inaccurate mechanism account in the diagnostic's wording (`missing protocol sources`) |
| DT-90.e | No public-contract check exercises a missing declared input, an empty root, a nonregular object, an unreadable file or an unreadable directory; three messages occur only in `source_identity.py`; symlink refusal is checked by replacing `main.rs`. | test assertions | yes: `git grep` finds `missing identity source`, `missing protocol sources`, `nonregular identity source` only at `docs/source_identity.py:16,25,27,31`; `build_contracts.py:255-259` | R-read; H-git | overstated coverage credit (the refusal sentence `surface:75-77` has one checked case) |
| DT-91.a | The statement names six roots; `DIRECTORIES` names seven; the inventory holds `controller/interface/cards.rs` and `inventory.rs`. | statement vs declaration | yes, and wider at HEAD: `docs/publication.py` is selected (`build_contract.py:20`, since `bba8bca3`) and unnamed | R-read; H-read; H-exec H0 (2 paths under `controller/interface`) | inaccurate mechanism account |
| DT-91.b | Changing `cards.rs` changes the digest; changing `controller/interface/inventory.json` does not. | bytes | yes | R-exec C3a/C3b; H-exec C3a/C3b | accurate observation needing no change |
| DT-91.c | `build.rs` compiles the two files and renders the help cards that `help.rs` embeds; a stale `inventory.json` stops the build, which is a generated-output freshness check, not selection. | Cargo build script | yes: `controller/build.rs:24-27`, `:71-82`, `:87-97`; `controller/src/help.rs:11-14` | R-read; H-read | accurate observation needing no change |
| DT-91.d | History: code-only inputs at `d04a3819` (two lesson files) and from `b16f32d0` (`controller/interface`); the statement never named an input missing from the code; suffixes always agreed; neither divergence is in a tagged release. | commits `f6551bf9^..458fcbb2` | yes for its range (`git show v0.3.7:docs/build_contract.py` has six roots). **A third divergence exists at HEAD**: `bba8bca3` added `docs/publication.py` to `FILES` and did not touch the surface; no tag contains it | R-exec `devid_history.py` (unavailable); H-git | accurate observation; incomplete at HEAD |
| DT-91.e | No check compares the statement's list with the code; every fixture that uses `build_contract.inputs` copies whatever the code selects. | test fixtures | yes: `build_contracts.py:214-215`; `generators.py:982-985`, `:1022-1026`; `preflight/check_release_publish.py:60-64`, `:341-344`; `preflight/opt_in/build_refusals.py:1941-1945`; `tests/lib/fixture_inputs.py:94-97`; also `source_drift/limits.py:736-738` | R-read; H-read | overstated coverage credit |
| DT-92.a | The digest framing matches the statement. | bytes hashed | yes: `build_contract.py:75-80`; `surface:49-52` | R-exec; H-exec H0, L1, every successful row | accurate observation needing no change |
| DT-92.b | Path names are hashed; mode and mtime are not. | metadata | yes | R-exec C1c/C1b; H-exec C1c/C1b | accurate observation needing no change |
| DT-92.c | The generator sorts by code point (equal to UTF-8 byte order); the statement says "sorted" without naming the order; a case-folded order gives another digest. | order | yes: `source_identity.py:32`; `surface:50`. L1: code-point order `89898dff…9c79`, case-folded order `23a48dab…6730` | R-exec `devid_order.py`; H-exec L1 | consequential ambiguity |
| DT-92.d | Unicode normalization of non-ASCII names was not exercised. | non-ASCII path | now exercised: N1 — names are hashed as the volume returns them; NFC and NFD spellings give different digests | H-exec N1 | accurate observation; resulting limit stated in §4 |
| DT-92.e | Different absolute roots give one digest. | location | yes | R-exec; H-exec H0 (checkout vs copy) | accurate observation needing no change |
| DT-92.f | No test asserts the prefix, length encoding, order, an expected value or an independent recomputation; the prefix string occurs only in the generator. | test assertions | yes: `git grep` finds the prefix at `build_contract.py:75` and in the statement copies only | R-read; H-git | overstated coverage credit (`surface:105` pins nothing about framing) |
| DT-93.a | `checkout()` copies `build_contract.inputs(ROOT)`, the inventory selected by the code under test, and nothing else. | fixture construction | yes: `build_contracts.py:209-217`; `fixture_inputs.py:105-130` | R-read; H-read | overstated coverage credit |
| DT-93.b | No cited check adds an eligible file, renames or deletes a selected file, touches `controller/interface`, places a nonregular object or makes a path unreadable. | test assertions | yes: `build_contracts.py:181-198`, `:229-259` | R-read; H-read | overstated coverage credit |
| DT-93.c | The byte-sensitivity loop names `runner/augments/mach-register.sb`, which never existed, and silently substitutes the first `*.sb`. | test input | yes: `build_contracts.py:246-250`; `git log --all -- runner/augments/mach-register.sb` is empty | R-read; H-read; H-git | overstated coverage credit (the test's subject is chosen by a fallback) |
| DT-93.d | Digest stability is checked across `git init`, a commit, a lightweight tag and a documentation commit in one directory; no public-contract check compares locations. | test assertions | yes: `build_contracts.py:232-244` | R-read; H-read | accurate observation needing no change |
| DT-93.e | No check covers framing. | — | yes (DT-92.f) | — | see DT-92.f |
| DT-93.f | The Swift-context check asserts only exit statuses for three `PW_BUILD_CONTRACT` values and does not concern selection. | test assertions | yes: `build_contracts.py:200-207` | R-read; H-read | accurate observation needing no change |
| DT-93.g | The pre-sign guard compares two whole-tree derivations; an edit present during compilation and reverted before the second derivation leaves them equal; the CONTRACT sentence covers only changes that persist; not executed. | build timeline | yes by reading: `build.sh:252`, `:683-687`; statement `surface:96-97`, `CONTRACT:105-106`. At HEAD the build derives at two further points: Meson's `--swift-stdout` (`meson.build:94-96`, `build_contract.py:110-116`) and `docs/generate_limits.py:561-565` from `build.sh:779-780`. All are point samples | R-read; H-read | consequential ambiguity ("refuses a selected-source change during compilation" reads as covering every change) |
| DT-93.h | Generated-output freshness is separate: the `inventory.json` edit leaves the digest unchanged while `build.rs` refuses a stale copy; generator inputs outside the roots are unselected. | generator checks vs identity | yes: `build.sh:224-235`; `controller/build.rs:87-97` | R-read/R-exec C3b; H-exec C3b | accurate observation needing no change |
| DT-93.i | No check compares compiler-consumed files with this inventory; `closure_problems` compares Ninja's dependency log with the worker identity's `source_paths`. | build closure | yes: `tests/lib/native_sources.py:152-157`, `:184-215`, targets `:51` | R-read; H-read | accurate observation; bounds DT-94.e |
| DT-93.j | Summary: the cited tests establish byte sensitivity for four files, two suffix exclusions, one documentation exclusion, symlink refusal and Git-state stability; not additions, path sensitivity, the refusal set, Git independence, statement/code agreement or framing. | support `surface:99-108` | yes | R-read; H-read | overstated coverage credit |
| DT-94.a | Edits to a `#[cfg(test)]` module, a named `tests/lib` helper, an unreferenced `.rs` and a nested `.sb` change the digest without changing a shipped input. | selection vs compiler use | yes; bundle copies only top-level augments (`build.sh:597-603`) | R-exec T1, T3, C2a, C2e; H-exec same rows | accurate observation needing no change (no current statement claims the converse) |
| DT-94.b | A fixture embedded by test-only `include_str!` and a Swift unit-test source do not change the digest. | files outside the selection | yes by reading (`controller/src/reply_fixtures.rs:246`, under `#[cfg(test)]` at `main.rs:27-28`; `runner/Tests` is not a root); not re-run | R-exec T2, T4; H-read | accurate observation needing no change |
| DT-94.c | `controller/tools/sb_api_validator/debug.ent` is selected by suffix; its only user is the manual helper script. | selection | yes: `controller/tools/sb_api_validator/build.sh:6`; `docs/BUILD.md:1028-1031` | R-read; H-read | accurate observation needing no change |
| DT-94.d | The v0.3.6 sentence "Ordinary documentation and test edits do not change that digest" did not describe that release's selection; `f6551bf9` removed it; current statements make no claim about test edits. | released statement | yes: `git show v0.3.6:docs/CONTRACT.md` line 11 | R-read; H-git | accurate observation needing no change (history) |
| DT-94.e | No shipped input outside the selection was found by source inspection; measured against the documented list `cards.rs` is the exception; this was not a build-closure audit. | shipped bytes | holds for what was re-read: production `include_str!` sites are `controller/src/test_input.rs:11` (selected) and `help.rs:11-14` (`OUT_DIR`); every other site is in test code; no tracked Cargo or toolchain configuration file exists outside the selection. Complete closure: unverifiable by reading | R-read; H-read; H-git | accurate observation with a stated limit |
| DT-94.f | Statements examined: `REQUEST` "A shipped-source edit changes the development identity…"; the generator comment; BUILD's "shipped sources and build inputs through docs/build_contract.py". | authored statements | present: `docs/REQUEST.md:326-327` (authored; generated regions begin at `:387`); `build_contract.py:21-23`; `docs/build.json:390` rendered at `docs/BUILD.md:150` | H-read | the REQUEST sentence is an explicit commitment that DT-89 contradicts under one condition and that otherwise rests on inspection; the other two are accurate summaries |
| Lim.a | Not exercised: non-ASCII or normalization-differing names; case-only collisions; a directory symlink at a root; the release form and byte check; `--swift-stdout`; Meson's invocation; a build in any changed state. | — | N1 and L2 now exercise the first and third. The rest remain unexercised | H-exec N1, L2 | accurate statement of limits |
| Lim.b | DT-89 was observed with one Python version; its effect on a build was not established. | — | mechanism now read in the pinned stdlib; build effect still not executed | H-read | accurate statement of limits |
| Lim.c | The pre-sign window (DT-93) and the shipped-input survey (DT-94) come from source inspection. | — | still so | H-read | accurate statement of limits |
| Lim.d | Historical inspection shows when declarations and statements appeared, not how older builds behaved. | — | still so | — | accurate statement of limits |

Nothing in these entries was found mistaken. Three items are stale or narrower
than HEAD: Conv.a (118 paths, `bdefcb44…` → 119 paths, `b55acb20…`), DT-91.d
(a third code-only input, `docs/publication.py`), DT-93.g (two derivations →
four sample points). DT-89.e's remark about compiler readability holds only for
mode 0000.

## 2. Comparison

### The obligation as stated

Owner: `docs/contract/00-identity.surface.md`, rendered into `docs/CONTRACT.md`
and `docs/contract/public.json` by `docs/generate_contract_stamps.py`. The
frozen guide carries none of these sentences (`docs/PolicyWitness.md:56` only
names the two forms).

- Forms, `surface:48-52`: "`development:<sha256>` identifies the selected
  source paths and bytes in other source trees. Its digest is SHA-256 with the
  domain prefix `PolicyWitness public build contract` followed by a NUL byte.
  For each sorted repository-relative path, the generator appends the UTF-8
  path and file bytes, each preceded by its unsigned eight-byte big-endian
  length."
- Inputs, `surface:63-73`: "The development digest includes `.rs`, `.c`, `.h`,
  `.swift`, `.sb`, `.plist` and `.ent` files discovered under `controller/src`,
  `controller/tools`, `runner/Sources`, `runner/Clients`, `runner/Services` and
  `runner/augments`. It also includes `build.sh`, … `docs/build_contract.py`,
  `docs/source_identity.py`, `tests/build_equipment.py`,
  `tests/build-evidence.py`, and the build helpers
  `tests/lib/build_provenance.py`, `signer_check.py`, `cargo_config.py`,
  `checkout_lock.py` and `output_target.py` in that same directory."
- Inputs, `surface:75-79`: "Discovery uses the same inventory in a checkout and
  a source copy. Missing declared inputs, symlinks under the selected roots and
  nonregular source objects refuse derivation. The digest's equality concerns
  those paths and bytes; build configuration, signing identity, SDK and
  observed runtime behavior are recorded and checked by their respective
  operations."
- Derivation, `surface:90`: "…refuse signing if recomputation after
  compilation yields a different identity."; `surface:96-97`: "The pre-sign
  comparison refuses a selected-source change during compilation."
- Support, `surface:103-107`: pins "Selected-source mutations change the
  digest; clean annotated release selection checks actual bytes; Swift context
  disagreement and the extracted pre-sign guard refuse."
- Owner `docs/REQUEST.md:326-327` (authored tour prose): "A shipped-source edit
  changes the development identity, including an optional addition or an
  implementation fix."
- Owner `docs/build.json:390` (rendered `docs/BUILD.md:150`): the
  `check_identity` step reads "shipped sources and build inputs through
  docs/build_contract.py".
- Owner `build.sh:677-681` (comment): "the build otherwise trusts the checkout
  not to change under it".
- Reliance elsewhere: `docs/SIGNING.md:559-562` and
  `tests/lib/release_accept.py:106-134` treat identity equality as "build
  inputs remain identical" (`agreement_scope='build_contract_inputs'`).

### What the producer does

`build_contract.inputs` (`docs/build_contract.py:36-37`) calls the shared
walker `source_paths` (`docs/source_identity.py:5-32`) with seven roots, twenty
explicit files and seven suffixes (`build_contract.py:15-27`).
`identity` (`:74-91`) hashes the prefix, then for each returned name the
length-framed name and file bytes, and returns `development:<hex>` unless the
release branch (`:82-90`) applies. `main` (`:100-123`) prints the value, or
`build contract: <error>` with exit 1 for any `OSError` or `ValueError`.

How the walker treats each object today (observation rows in brackets):

| Object under a selected root | Mechanism | Result today |
| --- | --- | --- |
| Directory that cannot be listed (0000, or searchable-only 0111) | Its parent's scan yields it; `is_symlink()` is false and `is_dir()` is true (`:20-25`), so no refusal fires. `rglob('*')` calls `os.scandir` on it in two selectors and the pinned stdlib discards both `PermissionError`s (`glob.py:453-456`, `:505-508`) | Every file below it is absent from the inventory; exit 0; no diagnostic [H1, H2, H3, H6, H7, L1] |
| A selected root that cannot be listed | `exists()` passes (`:15`); the scan errors are discarded; `found` is empty | Refusal `missing protocol sources: <root>` (`:26-27`), naming another cause [H5] |
| Directory listable but not searchable (0444) | Its entries are yielded; `lstat`/`stat` fail for each and pathlib's predicates return False | Refusal `nonregular identity source: <first entry>` (`:24-25`), naming another cause [H4] |
| Unreadable regular file with a selected suffix | `is_file()` needs only `stat`; the name is listed; `read_bytes()` raises in `identity` (`build_contract.py:78`) | Exit 1, `build contract: [Errno 13] Permission denied: '<absolute path>'`; an importing caller receives `PermissionError` [H8] |
| Unreadable regular file with another suffix | Never opened | No effect |
| Dangling symlink under a root, any suffix | `is_symlink()` uses `lstat` | Refusal `symlink under identity sources: <relative path>` (`:20-21`) [H9] |
| Symlink, dangling or not, at a declared file, a root, or a component between the repository root and either | Component loop (`:10-14`) runs before the existence check (`:15`) | Refusal `symlink under identity sources: <declared name>` [H10, L2] |
| Symlink to a directory under a root | Not descended; yielded and refused | Same refusal [L2; `build_contracts.py:128-143` for the worker roots] |
| FIFO, socket or device under a root, any suffix | Neither regular file nor directory | Refusal `nonregular identity source: <relative path>` (`:24-25`) [H11] |
| Declared file that is a directory or other non-regular object | `:29-31` | Refusal `nonregular identity source: <name>` [L2] |
| Root that is a regular file | `exists()` passes; `NotADirectoryError` discarded | Refusal `missing protocol sources: <root>` [L2] |
| Missing declared file or root | `:15-16` | Refusal `missing identity source: <name>` [M1] |
| Root with no selected file | `:26-27` | Refusal `missing protocol sources: <root>` [M2] |
| A discoverable file removed | Not a declared path | Inventory shrinks, digest changes, no refusal [M3] |

Observation: H1 and H2 hold different bytes in a file the rule selects and
print one identity. H3 gives the same result with a directory whose files open
by name. H7 shows the shared walker producing a `stale …; run … docs/generate_worker_identity.py`
refusal for the worker identity while the public identity is derived over 117
paths without complaint.

Inference, not executed: a compiler opens sources by path and needs only search
permission on the directory, so a build in the H3 state can read files the
identity omitted. In the H7 state, running the regeneration the refusal names
would write the incomplete tree's worker identity into three tracked files
(`generate_worker_identity.py:87-90`). Under an automation sandbox that denies
listing one source directory, today's walker would yield a different identity
with no diagnostic, which then appears as a source/app disagreement.

Where a derivation refusal surfaces (all exist today for the symlink,
nonregular and missing cases and would carry the new refusal unchanged):

| Site | Form |
| --- | --- |
| `build.sh:235` (`generate_worker_identity.py --check`, banner "Checking host/worker identity") for the worker roots `controller/tools/pw_probe_runner` and `runner/Sources` | stderr `worker identity: <message>`, exit 1 (`generate_worker_identity.py:94-96`) |
| `build.sh:252` (`PW_BUILD_CONTRACT="$(…)"` under `set -euo pipefail`; the `export` is a separate command at `:253`) | stderr `build contract: <message>`, exit 1, after the same banner and before `==> Build stamp` (`:254`) |
| Meson configure (`meson.build:94-96`, `--swift-stdout`) | the `configure_file` command exits 1 with `build contract: <message>` |
| `build.sh:683` before signing | stderr `build contract: <message>`, exit 1, before the `public_contract_changed` comparison |
| `build.sh:779-780` (`docs/generate_limits.py:561-565`) | stderr `limits: <message>`, exit 1 (`generate_limits.py:588-590`) |
| `tests/lib/native_sources.py:186-189` at `native_check` (worker inventory) | `  <label>: <message>` among the closure problems |
| Tooling that compares a tree with `policy-witness --version`: `tests/lib/release_accept.py:111-115` (development candidate; compares the derived value with `PWContract` and `--version` `build.contract`) and `tests/lib/release_preflight.py:215-221` | the message becomes an entry of the report's `errors` (`release_accept.py:203-204`) or the problem `build contract: <message>` |

`policy-witness --version` itself derives nothing; it prints the compiled value.
`docs/build.json` lists no refusal row for any derivation refusal of
`docs/build_contract.py` (see "Outside the review").

### What each reader or test asserts

- `test_build_identity_tracks_shipped_inputs_and_requires_an_annotated_clean_release`
  (`build_contracts.py:229-259`): on a copy of `inputs(ROOT)`, the digest is
  stable across `git init`, commit, lightweight tag and a `notes.md` commit; it
  changes after appending `\n` to `main.rs`, to whichever `*.sb` the fallback
  returns, to `PolicyWitness.entitlements` and to `read.json`; a symlinked
  `main.rs` raises `ValueError` matching `symlink`.
- `test_source_copies_ignore_artifacts_and_release_checks_actual_bytes`
  (`:181-198`): two unsuffixed names leave the digest unchanged; release
  selection and the index-flag case follow.
- `test_swift_context_refuses_a_different_compilation_identity` (`:200-207`):
  three exit statuses.
- `test_presign_contract_guard_refuses_changed_sources` (`:271-291`): the
  extracted guard exits 1 with the script's message after `main.rs` gains a
  line that is still present.
- `tests/suites/preflight/check_build_entry.py:88-106`: an unmodified build
  checkout reaches `Build stamp` (derivation succeeds there). No build-entry
  control exercises a derivation refusal.
- No test reads the statement's lists, asserts a digest value or framing, adds
  an eligible file, or changes permissions.
- `closure_problems` (`native_sources.py:184-215`) compares compiler
  dependencies of `pw-probe-runner` and `PWCWorkerShim` with the worker
  identity inventory only.

## 3. Plausible treatments

**T1 — Refuse what the walker cannot list or inspect (product/tool behavior change; DT-89, DT-90.d).**
File: `docs/source_identity.py`, function `source_paths` (keep the name; the
surface cites it at `surface:103`). Replace `Path.rglob('*')` with an explicit
walk in which no listing or inspection error is discarded: for each directory,
`os.scandir` inside `try`, converting any `OSError` to
`ValueError('unreadable identity source directory: <relative path>: <strerror>')`;
for each entry, `os.lstat` inside `try`, converting any `OSError` to
`ValueError('uninspectable identity source: <relative path>: <strerror>')`;
then symlink → the existing `symlink under identity sources: <relative path>`,
directory → descend, regular file → suffix filter, anything else → the existing
`nonregular identity source: <relative path>`. `os.walk(root, onerror=<raise>, followlinks=False)`
with an `lstat` of every directory and file name is an equivalent primitive and
has a precedent in a selected helper (`tests/lib/output_target.py:193-211`);
plain `os.walk` without `onerror`, `Path.walk` without `on_error`, `glob` and
`rglob` all discard listing errors. Keep `ValueError`: every caller handles it
(`build_contract.py:122`, `generate_worker_identity.py:94`,
`native_sources.py:189`, `release_preflight.py:220`, `release_accept.py:203`,
`generate_limits.py:588`). Keep the two symlink message spellings; they are
asserted at `build_contracts.py:141` and `tests/suites/preflight/check_native_sources.py:73`.
In the same edit, replace `missing protocol sources: <root>` with wording that
is true for both identities (for example `no selected identity source under: <root>`);
no test or document cites the old string.

- Build-contract input: **yes**, and a worker-identity input. See the notice
  at the top. Regeneration: `tests/lib/python.sh docs/generate_worker_identity.py`,
  which rewrites the generated regions of
  `controller/tools/pw_probe_runner/pw_probe_runner_abi.h` and
  `runner/Sources/PWRunnerCore/CWorker.swift` (both under selected roots) and
  `tests/lib/contract.py` (not a public-contract input).
- No `build.sh` or `docs/build_contract.py` edit is needed for the refusal to
  stop the build: `set -e` propagates the helper's status at `build.sh:235`,
  `:252` and `:683`.
- Consequence for developers: a directory under a selected root that the
  building user cannot list, or whose entries cannot be inspected, stops the
  build and every derivation with a message naming the path, including a
  directory that holds no selected file (H6 is refused). The checkout holds no
  such directory now (S1). Trees that derive today derive the same inventory.
- Incorrect behavior a check must reject: for a tree with a selected file in
  an unlistable directory, exit 0 or any printed `development:` value; in
  particular the value of the same tree with that directory removed (L1:
  `2f7232f8…e316` for the literal tree), which is what the present code prints.

**T1-alt, not recommended.** (a) Put the check only in `docs/build_contract.py`:
still a public-identity change, leaves the worker identity deriving over an
incomplete inventory and its misattributed `stale` refusal (H7). (b) Hash a
marker for the unlistable directory instead of refusing: gives distinct trees
distinct identities only by directory name, still not by content. (c) Take the
inventory from Git: an untracked top-level `runner/augments/*.sb` is copied
into the bundle (`build.sh:597-603`), so a tracked-only inventory would miss
shipped bytes, and source copies have no Git.

**T2 — Controls for T1 with an oracle the code under test does not supply (assertion/coverage repair; DT-89, DT-90.e, DT-92.f, DT-93.a/b/j).**
File: `tests/suites/source_drift/build_contracts.py`, case
`source_drift/build_contracts`. Not a build-contract input.

1. Literal-tree walker controls: build the tree in the test from literal names
   and bytes (for example L1's), call `source_identity.source_paths(root, ('sel',), ('top.cfg',), ('.rs',))`
   and compare with a literal list. No copy of the checkout and no call to
   `build_contract.inputs` enters the expectation.
2. Readable/unlistable contrast on that tree: (i) readable → the literal
   inventory; (ii) `sel/sub` removed → the literal subset; (iii) `sel/sub` mode
   0000 with `b.rs` inside → `ValueError` matching
   `unreadable identity source directory: sel/sub`; (iv) the same after
   changing `b.rs` bytes → the same refusal. Repeat (iii) for mode 0111, for a
   0444 directory (`uninspectable identity source`), for an unlistable root and
   for an added empty unlistable directory.
3. Digest contrast through the generator: load `docs/build_contract.py` as a
   private module instance, substitute `DIRECTORIES`, `FILES`, `SUFFIXES` for
   the literal tree, and require `identity(root)` to equal the literal
   `development:89898dff6ed143459c8de8d18e81ed63a450b050fb0b33024bf5c83762619c79`
   (computed in this pass two ways: straight-line hashlib and a
   `printf`/`shasum -a 256` pipeline; recompute before pinning) and, for the
   unlistable state, to raise and never return `…2f7232f8…e316` or
   `…89898dff…9c79`. The pinned value also fixes the prefix, length encoding
   and code-point order (the case-folded order gives `23a48dab…6730`).
4. Remaining refusals on the literal tree, each asserting the message and the
   relative path: missing declared file; root with no selected file; dangling
   symlink under the root with an unselected suffix; dangling symlink at the
   declared file; FIFO with an unselected suffix; unreadable selected file
   (exit 1 through the script, stdout empty, the relative path in stderr).
5. Fixture duties: the control must confirm its own precondition in the test
   process (`os.scandir` on the 0000 directory raises `PermissionError`) and
   fail, not pass, when it does not (a uid 0 run lists the directory).
   Register `self.addCleanup(os.chmod, path, 0o755)` immediately after each
   `chmod` and before the first assertion; cleanups run in reverse order, so
   the mode is restored before the input capture and before the temporary
   directory is removed. Remove a FIFO explicitly. `receipts.TestCase`'s input
   capture walks with `os.walk` and no error handler
   (`tests/lib/receipts.py:90`), so call `track_inputs` before the `chmod` if
   the hidden file's bytes should appear in the evidence.
6. Per the management plan, run the new controls against the unchanged walker
   first: expected failures are (iii) and (iv) returning the subset inventory
   and the digest control returning `…2f7232f8…e316`.

Consequence: none for users. A developer who runs the suite as uid 0 gets a
failed precondition, not a pass.

Build-level control. File: `tests/suites/preflight/check_build_entry.py`, case
`preflight/build_entry_controls` (default, no equipment). In
`self.build_checkout()` create a directory holding one eligible file under a
root that only the public identity walks (for example
`runner/Clients/zz_unlistable/extra.swift`), set mode 0000, register the mode
restore, run `self.build(root, {'IDENTITY': ''})` and require: exit 1; stdout
has `Checking host/worker identity` and lacks `Build stamp`; stderr has
`build contract: unreadable identity source directory: runner/Clients/zz_unlistable`;
no `dist` and no `builddir`. A second variant under `runner/Sources` expects
`worker identity: unreadable identity source directory: …` at the same banner.
The positive contrast already exists (`check_build_entry.py:88-106` reaches
`Build stamp` in the unmodified checkout). This fixture is built by
`fixture_inputs.build_script_inputs`, which includes `build_contract.inputs(ROOT)`;
that dependence does not weaken a refusal control whose added object and
expected message are literal. Against the unchanged walker the expected
observation is `Build stamp` followed by `IDENTITY is not set.` (exit 2).

**T3 — Correct the statement in its owner (correction of the account; DT-08, DT-88.c, DT-90.a/d, DT-91.a, DT-92.c/d, DT-93.g, DT-94.a).**
File: `docs/contract/00-identity.surface.md`, definitions `forms` (`:48-55`),
`inputs` (`:63-79`) and the `derive` prose (`:94-97`). Regenerate with
`tests/lib/python.sh docs/generate_contract_stamps.py` (rewrites
`docs/CONTRACT.md` and `docs/contract/public.json`; the guide and its stamp
table stay frozen; every surface is already `unreleased`). Not a
build-contract input. Prose only: no keyed fact, shape or free-text relation
changes. Facts the text must state, with a draft the implementer may reword:

> `development:<sha256>` identifies the selected source paths and bytes present
> in a source tree when it is derived; it does not identify a commit. … For
> each repository-relative path in ascending Unicode code-point order, which is
> also the byte order of the UTF-8 paths, the generator appends …
>
> The development digest includes every regular file whose final suffix is
> exactly `.rs`, `.c`, `.h`, `.swift`, `.sb`, `.plist` or `.ent` anywhere under
> `controller/src`, `controller/tools`, `controller/interface`,
> `runner/Sources`, `runner/Clients`, `runner/Services` and `runner/augments`.
> It also includes `build.sh`, `meson.build`, `meson.options`,
> `runner/Package.swift`, `controller/Cargo.toml`, `controller/Cargo.lock`,
> `controller/build.rs`, `controller/src/test_inputs/read.json`, `Info.plist`,
> `PolicyWitness.entitlements`, `docs/build_contract.py`,
> `docs/source_identity.py`, `docs/publication.py`, `tests/build_equipment.py`,
> `tests/build-evidence.py`, `tests/lib/build_provenance.py`,
> `tests/lib/signer_check.py`, `tests/lib/cargo_config.py`,
> `tests/lib/checkout_lock.py` and `tests/lib/output_target.py`.
>
> Discovery reads the directory tree on disk and applies this rule alike in a
> checkout and a source copy. Git tracking and ignore rules do not enter it: an
> untracked, ignored or hidden file with a listed suffix under a listed root is
> included. The selection is declared by these roots, suffixes and files. It is
> not derived from what the compilers read, and it includes test-only code and
> files that no build step consumes. Derivation refuses a missing declared file
> or root; a root holding no selected file; a symlink, or an object that is
> neither a regular file nor a directory, anywhere under a selected root
> whatever its name; a directory that cannot be listed; an entry that cannot be
> inspected; and a selected file that cannot be read. The digest's equality
> concerns those paths and bytes. File modes, timestamps and extended
> attributes do not enter it, and path names are hashed as the file system
> returns them, without Unicode normalization. Build configuration, …
>
> The pre-sign comparison refuses when the selected paths or bytes at that
> point differ from those hashed before compilation. A change made and reverted
> between the two derivations is not detected.

Settle one corner in the wording: a file named only `.rs` has no suffix and is
not selected (C2f). The refusal sentence about unlistable directories is true
only once T1 lands; land T1 and T3 together.

Consequence: no behavior change. The public text of `identity.public.forms`,
`identity.public.inputs` and `identity.public.derive` changes; readers who
took "the same inventory in a checkout and a source copy" as "a checkout
equals an archive of its commit" lose that reading. The incorrect state a
check must reject: a selected root or file the statement does not name, or a
named one the code does not select (T4).

**T3-alt, not recommended now (arrangement change).** Render the three lists
from the generator's declarations (or declare them as keyed facts) so prose
cannot diverge. It removes the recurrence but needs new generator and tree
syntax; T4 gives the same refusal of divergence with a test.

**T4 — Make the statement the oracle for the real declarations (assertion/coverage repair; DT-91.e, DT-93.a/b, DT-88.d, DT-92.e).**
File: `tests/suites/source_drift/build_contracts.py`. Read the backticked
names from the `inputs` definition of `docs/contract/00-identity.surface.md`
(the T3 text spells every path in full so that this needs no interpretation of
"in that same directory"). (i) Require the sets of roots, files and suffixes to
equal `build_contract.DIRECTORIES`, `FILES` and `SUFFIXES`, naming each
difference. (ii) Build a literal tree from the statement's names only (one
file per root per suffix class, each explicit file, literal bytes), run the
unmodified `docs/build_contract.py --root <tree>` (the option exists at
`build_contract.py:102`) and require stdout to equal an in-test recomputation
of the stated framing over the statement-derived inventory. (iii) On that
tree: one mutation per root and per explicit file changes the value; an
eligible addition, a rename and a removal change it; a mode and mtime change
and files with unlisted suffixes do not; after `git init` an ignored eligible
file still changes it; a second temporary root gives the same value.
At HEAD (i) fails naming `controller/interface` and `docs/publication.py`, and
(ii) fails with `missing identity source: controller/interface`; those are the
divergences it must reject. Not a build-contract input.

**T5 — Bring the support blocks into line (correction of the account; DT-93.j, DT-91 thread: cited support must establish the revised scope).**
File: `docs/contract/00-identity.surface.md`. Add an owner under
`Selected build inputs` (for example `#### Selection support {support: owner}`,
grade `check_read`) citing `docs/build_contract.py` `DIRECTORIES`,
`docs/source_identity.py` `source_paths` and the T2/T4 tests, with pins limited
to what they assert (statement/declaration equality; literal-tree inventory and
framing; listed refusals; Git-state independence) and limits "No check compares
the selection with compiler dependency records; the release-form and guard
checks use copies of the generator's own inventory." Narrow the existing
Derivation support `pins` (`surface:105`) if "Selected-source mutations change
the digest" is kept: after T4 it holds per root and per explicit file. Same
regeneration as T3. Not a build-contract input. Consequence: no behavior
change; CONTRACT gains a support entry for the inputs definition. What review
must reject, since no generator can: a pin that credits behavior no cited
check asserts.

**T6 — Account for the refusal in the build manifest (correction of the account; DT-89).**
File: `docs/build.json`: one `refusals` row of kind `propagated`, status 1,
both variants, steps `check_identity` and `presign` (whose invocations
`inv_build_contract` and `inv_build_contract_presign` satisfy
`propagated_problems`), sources `build.sh` → `docs/build_contract.py` and
`docs/source_identity.py` → the new message, checks `check_propagated_refusals`
(textual) and the T2 build-entry test (behavioral); add its id to those steps'
`refusals`. Regenerate with `tests/lib/python.sh docs/generate_build.py`
(`docs/BUILD.md`; refusal count 65 → 66). Not a build-contract input.
Consequence: BUILD's step and refusal tables name a refusal the script can
produce at those steps. `baseline_problems` rejects a row without a control;
nothing mechanical rejects an unlisted propagated refusal, so the row's
presence is a review matter. Whether the row should instead cover the whole
derivation-refusal family is noted under "Outside the review".

**T7 — Name the file the byte-sensitivity loop means (assertion repair; DT-93.c).**
`tests/suites/source_drift/build_contracts.py:246-250`: use
`runner/augments/exec_baseline.sb` and assert that each named path exists;
delete the `glob` fallback. Not a build-contract input. Rejects: a loop whose
subject silently changes when the named file is absent.

**T8 — Reasoned retention** for the remaining observations; limits in §4.

**Considered and not recommended.** A compiler-closure check of the public
identity (extend `closure_problems` to all native targets and read Cargo's
dep-info against `build_contract.inputs`) would turn `REQUEST:326` from
inspected to checked. It is a new build refusal with its own controls and, if
`build.sh` passes it arguments, another identity-input edit. Nothing found at
HEAD makes the claim false once T1 lands, so it is not needed to leave the
statements true. Scoping `REQUEST:326` to "a selected build input" would
withdraw a commitment users rely on and is not recommended. Refusing non-ASCII
selected names would add a restriction with no present case (all 119 paths are
ASCII).

## 4. Recommended disposition per claim

| Id | Disposition | Reason | Discriminating check, or why none | Accepted limit and where it belongs |
| --- | --- | --- | --- | --- |
| DT-08.a | Correct the account (T3); the DT-05–08 pass's statement disposition should name this same single edit. | The definition lists the selection and omits two selected inputs. | T4(i) in `source_drift/build_contracts`. | — |
| DT-08.b | No behavior change; covered by T3 and T4. | The behavior (a help-card source changes the identity) is the wanted one: `cards.rs` reaches shipped bytes. | T4(iii) mutates one file per root, including `controller/interface`. | — |
| DT-08.c | No change. | History. | None: no decision depends on it. | — |
| Conv.a | No change to any owner; use HEAD values (119 paths, `b55acb20…719e`) in the working record. | Values moved with `bba8bca3`. | H0. | — |
| Conv.b–d | No change. | Evidence for the entries below; the review's raw outputs are gone and are not needed for any recommendation. | H-exec rows reproduce the non-Git rows. | — |
| DT-88.a, .b | Retain the behavior. | On-disk selection is required: an untracked top-level augment is bundled; source copies have no Git. | T4(iii) Git-state step. | In `inputs` (T3): "Git tracking and ignore rules do not enter it: an untracked, ignored or hidden file with a listed suffix under a listed root is included." |
| DT-88.c | Correct the account (T3). | "The same inventory" must read as "the same rule". | T4(iii): an eligible untracked or ignored file changes the value. | In `forms` (T3): "…present in a source tree when it is derived; it does not identify a commit." |
| DT-88.d | Coverage repair (T4). | The sentence has no check. | T4(iii). | — |
| DT-88.e | No change. | History. | None needed. | — |
| DT-89.a | **Product/tool change T1**, with T2, T3, T6. | Different selected bytes share an identity; H3 shows the omitted files can remain readable by name. | T2 items 2–3 and the build-entry control. | — |
| DT-89.b | Retain: an unreadable selected file already refuses. Add the control (T2 item 4). Naming it `unreadable identity source: <relative path>` is optional and would need an edit in each generator's read loop. | It is a refusal, not an omission. | T2 item 4. | In `inputs` (T3): "a selected file that cannot be read" in the refusal list. |
| DT-89.c | No change. | Git is a second observer with its own blind spots. | None: T1 makes the generator's own refusal the signal. | User duty below. |
| DT-89.d | Closed by reading the pinned stdlib; T1 moves the error handling into repository code so it no longer depends on the interpreter's `glob`. | — | T2. | — |
| DT-89.e | Retain as an unexecuted limit; it does not affect the decision. | T1 refuses whether or not a build could complete. | None: a build in the H3 state was not permitted in this pass and its outcome would not change T1. | Working record only: "A packaged build with a searchable, unlistable source directory was not run." |
| DT-90.a | Retain the behavior; correct the account (T3). | Refusing any symlink or special file under a root is the conservative rule; the statement should say "whatever its name". | T2 item 4 (FIFO and symlink with unselected suffixes). | — |
| DT-90.b | No change. | Accurate; follows from on-disk discovery. | None needed. | User duty below. |
| DT-90.c | No change. | Matches the statement. | Existing `build_contracts.py:255-259`; T2 item 4. | — |
| DT-90.d | Correct the account (T3: empty root and unreadable file listed); rename `missing protocol sources` in the T1 edit; M3 retained. | The refusal list was incomplete; the diagnostic names a role the root does not have; a removed discoverable file is a content change, which the digest reports. | T2 item 4 asserts each message. | — |
| DT-90.e | Coverage repair (T2 item 4). | One of the listed refusals is checked today. | `source_drift/build_contracts`. | — |
| DT-91.a | Correct the account (T3). | Seven roots and twenty explicit files are selected. | T4(i). | — |
| DT-91.b, .c | No change. | Accurate; `inventory.json` freshness belongs to `build.rs`. | H-exec C3a/C3b. | — |
| DT-91.d | No change to any owner. The recurrence at `bba8bca3` is the reason for T4. | Hand-maintained prose diverged three times in a week. | T4(i). | — |
| DT-91.e | Coverage repair (T4), support revision (T5). | Fixtures copied from the code cannot show a divergence from the statement. | T4. | In the new support owner's `limits` (T5). |
| DT-92.a, .b, .e | No behavior change; add the framing and relocation assertions (T2 item 3, T4(ii)(iii)). | Behavior matches the statement. | T2 item 3 pinned value; T4(iii) second root. | In `inputs` (T3): "File modes, timestamps and extended attributes do not enter it." |
| DT-92.c | Correct the account (T3). | An independent implementer needs the order. | T2 item 3 (a case-folded order gives another value). | — |
| DT-92.d | Retain with a stated limit. | N1: the name bytes the volume returns are hashed; no selected path is non-ASCII. | None beyond N1: more evidence would not change a retention that states the behavior. | In `inputs` (T3): "path names are hashed as the file system returns them, without Unicode normalization." |
| DT-92.f | Coverage repair (T2 item 3). | No framing assertion exists. | Pinned literal digest. | — |
| DT-93.a, .b, .j | Coverage repair (T2, T4); support revision (T5). | The oracle must not come from the code under test. | T2, T4. | — |
| DT-93.c | Assertion repair (T7). | The loop's second subject is chosen by a fallback. | The repaired test fails if the named file is absent. | — |
| DT-93.d | Covered by T4(iii). | — | T4(iii). | — |
| DT-93.e | See DT-92.f. | — | — | — |
| DT-93.f | No change. | The pin "Swift context disagreement … refuse" is what the three statuses show. | Existing test. | — |
| DT-93.g | Correct the account (T3, derive prose); retain the mechanism. | Point comparisons cannot see a change that is reverted; the script already says it trusts the checkout. | None new: the existing guard test covers a persisting change; a reverted change is by construction not observable at the sample points. | In `derive` (T3): "A change made and reverted between the two derivations is not detected." |
| DT-93.h | No change. | Accurate separation of duties. | H-exec C3b. | — |
| DT-93.i | Retain with a stated limit. | No statement claims a compiler-closure check for the public identity. | The closure check described under "Considered" is the control that would change this; not required to keep the statements true. | In the new support owner's `limits` (T5): "No check compares the selection with compiler dependency records." |
| DT-94.a, .b, .c | Retain. | A superset rule is the conservative choice; no current statement says test edits leave the identity unchanged. | T4(iii) can include an unreferenced eligible file. | In `inputs` (T3): "The selection is declared by these roots, suffixes and files. It is not derived from what the compilers read, and it includes test-only code and files that no build step consumes." |
| DT-94.d | No change; no erratum for a released document. | History. | None needed. | — |
| DT-94.e | Retain `REQUEST:326` as stated. Established: the include sites and bundle copies re-read at HEAD are inside the selection. Unknown: the complete compiler closure. | Nothing found contradicts it once T1 lands. | None executed; see DT-93.i. | Same T5 `limits` sentence. |
| DT-94.f | `REQUEST:326-327`: no edit. Generator comment `build_contract.py:21-23`: no edit (an edit would itself be an identity-input change). `docs/build.json:390`: no edit required; if the row is touched for T6, "the selected build inputs" is the more exact phrase. | The two summaries are not false. | — | — |
| Lim.a | Non-ASCII: retained with the DT-92.d limit. Root symlink: refused (L2). Case-only collisions, the release form, `--swift-stdout`, Meson's invocation, a build in a changed state: remain unexercised; none changes a disposition. By reading, in a release checkout with an unlistable selected directory the inventory comparison at `build_contract.py:56-57` fails and the result is the development form, not a release identity. | — | T1 is exercised through `--swift-stdout` only if a control is added; the existing Swift-context test covers that entry's success and disagreement paths. | — |
| Lim.b, .c, .d | No change. | Accurate statements of limits. | — | — |

No authority is missing for any of these. Information that could not be
obtained in a read-only pass: a full build in the H1/H3 states, and a complete
compiler-closure audit.

## 5. Resulting user duties

- A development identity names the selected files on disk when the build
  derived it. Do not read it as a commit identifier, and do not read a clean
  `git status` as a prediction that derivation will succeed or that two trees
  share an identity: untracked, ignored and hidden eligible files are included,
  and FIFOs or unlistable directories that Git does not report can stop
  derivation.
- Equal development identities establish equal selected paths and bytes. They
  do not establish equal compiler, SDK, build configuration or signing
  identity. A changed development identity does not establish a change in
  shipped bytes: edits to test-only code and to the selected build helpers
  change it.
- When derivation refuses with a path, correct or remove that object. Do not
  run the regeneration that a `stale …` refusal names while a source directory
  is unlistable.
- When T1 lands, every development identity changes. A saved specimen that
  asserts an earlier development identity must be reviewed and reasserted for
  the rebuilt app under the existing "Reviewing a development specimen" rule.
  External runners installed from the earlier app must be reinstalled from the
  rebuilt one.

## 6. Implementation worklist

Record the verification selection and rationale before executing (management
plan, "Verification sequence"). Group T1 with any other pending identity-input
edit so that one signed rebuild serves them.

1. **Tests first, against current behavior.**
   `tests/suites/source_drift/build_contracts.py`: add the T2 literal-tree
   controls and the T4 statement-oracle test; apply T7.
   `tests/suites/preflight/check_build_entry.py`: add the two build-level
   controls. Run `tests/run.sh --case source_drift/build_contracts` and
   `tests/run.sh --case preflight/build_entry_controls` with a fresh
   `PW_TEST_OUT_DIR`; record the expected failures listed under T2 item 6 and
   T4. (Not build-contract inputs.)
2. **T1.** `docs/source_identity.py`, `source_paths`: explicit walk, two new
   refusals, renamed empty-root message. **Build-contract input and
   worker-identity input.**
3. **Regenerate the worker identity.**
   `tests/lib/python.sh docs/generate_worker_identity.py`; review the three
   regions. `pw_probe_runner_abi.h` and `CWorker.swift` are **under selected
   roots**; `tests/lib/contract.py` is not a public-contract input.
4. **T3 and T5.** `docs/contract/00-identity.surface.md`: `forms`, `inputs`,
   `derive` prose; new selection support owner; narrowed derivation pins. Then
   `tests/lib/python.sh docs/generate_contract_stamps.py`; review
   `docs/CONTRACT.md` and `docs/contract/public.json`. If a prose or free-text
   guard refuses the authorized text, revise that rule with positive and
   negative controls (management plan). (Not build-contract inputs.)
5. **T6.** `docs/build.json` refusal row and step lists; then
   `tests/lib/python.sh docs/generate_build.py`; review `docs/BUILD.md`. (Not
   build-contract inputs.)
6. **Test accounts.** `tests/catalog.json` (`preflight/build_entry_controls`
   description gains the unlistable identity source directory);
   `tests/suites/source_drift/README.md` (the `build_contracts` paragraph near
   `:659`); `tests/suites/preflight/README.md` (`build_entry_controls`);
   `tests/CHANGE-VERIFICATION.md#build-entry-controls` (purpose and "When to
   run": identity derivation refusals) and a route row for changes to the
   identity selection, walker or framing. (Not build-contract inputs.)
7. **Checks without the app.** Every generator's `--check` after the last
   regeneration (limits, contract stamps, architecture, footprint, porcelain,
   interface, build, worker identity). Then `tests/run.sh --suite source_drift`,
   `tests/run.sh --case preflight/build_entry_controls`,
   `tests/run.sh --case preflight/native_source_controls`
   (`tests/CHANGE-VERIFICATION.md#native-source-controls`: it reads the worker
   inventory through the walker and asserts a symlink message), and
   `tests/run.sh --suite runner_abi_layout`.
8. **Signed rebuild** (`make build IDENTITY=…`) before any app-requiring case:
   until then `tests/lib/contract.py` and the tree's public identity disagree
   with `dist/PolicyWitness.app`. Record the new `development:` value where the
   plan records its candidate. Then `runner_unit`, `runner_c_worker_harness`
   and the grouped default battery, per the management plan's row "Wire,
   layout, schema or identity derivation".
9. No `docs/architecture.json` change: no process, channel or boundary moves;
   its identity rows cite `SOURCE_DIRS` and remain accurate.

## Outside the review

- **`docs/publication.py` is a selected input the statement does not name**
  (`docs/build_contract.py:20`, added by `bba8bca3` on 2026-11-17, after the
  review's snapshot). It is the same defect as DT-08/DT-91 and is closed by the
  same T3 edit and T4 check; it is listed here because the review could not
  have seen it.
- **`docs/build.json` has no refusal row for any derivation refusal** of
  `docs/build_contract.py` (missing, symlink, nonregular, ambiguous release),
  although each stops the build at `build.sh:252` or `:683`. T6 adds a row for
  the new refusal; whether one row should describe the family is a separate
  choice for whoever owns the build account.
- **The shared walker's omission also affects the worker identity** (H7): an
  unlistable directory under a worker root produces a `stale …; run …`
  refusal whose named remedy would record the incomplete tree's identity. T1
  removes it.
- **Other traversals discard listing errors in the same way**:
  `tests/lib/native_sources.py:223,225` (`rglob` for the expected Meson source
  lists), `tests/lib/fixture_inputs.py:136` (`snapshot`) and the evidence
  capture at `tests/lib/receipts.py:90` (`os.walk` without `onerror`). Not
  assessed here.
