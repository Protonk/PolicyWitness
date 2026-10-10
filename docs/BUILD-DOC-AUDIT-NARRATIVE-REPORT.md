# Build documentation audit narrative report

All experiment changes and outputs are confined to `.tmp/audit-narrative/src/`. This report is uncommitted. No pre-existing scratch contents, `records/`, or `docs/BUILD-DOC-PLAN.md` were read.

## Current result

Task 1 is **not yet fully green**. The signed make build passed (A019), artifact inspection passed against unchanged bytes outside the sandbox (A021), and the helper's exact output was verified (A026). The first source-drift run failed (A022). Its implementation-related failures have been repaired and checked separately: thirteen build-document tests pass (A033) and thirty-three planner/host-source controls pass (A038).

The final whole-suite run awaits clarification about restoring the excluded .tmp/AGENTS.md. The audit prompt prohibits reading anything under .tmp, while its prescribed copy removes this file and the suite requires the linked path. I asked to copy only that tracked policy file without opening or displaying it. No permission was inferred from elapsed time, and the file has not been copied or opened. This report does not claim all three requested checks are green.

Task 2 succeeded: a sixty-three-line grounded query computes an exact declared-control coverage frontier for full and partial builds, with independent optimum checks and a negative grounding control. No default battery, notarization, release, publication, or commit was performed. The original source files sampled in the pre-edit baseline remain byte-identical. Only this report was written outside the authorized disposable experiment tree.

## Part 1: ordered action log

### A001 — Read the audit instructions

- Before: the chat announcement was “I’ll read the audit narrative, carry out its instructions, and summarize the findings and checks here.” No more specific prediction or start timestamp was recorded before this first read.
- Action: `cat docs/BUILD-DOC-AUDIT-NARRATIVE.md` in the original checkout.
- Result: read the two-task protocol, excluded paths, disposable-copy setup, required ordered checks, and report format. The shell command took under 0.1 seconds; thinking time before the first timestamp was not measured.

### A002 — Create the disposable working-tree copy

- Start: 2026-10-10T15:40:39+00:00
- Before: I expect rsync to preserve uncommitted source and documentation while excluding existing build, distribution, scratch, and test-output trees; I expect it to finish within a minute.
- Action: `mkdir -p .tmp/audit-narrative` followed by `rsync -a --exclude 'builddir*' --exclude controller/target --exclude dist --exclude .tmp --exclude tests/out . .tmp/audit-narrative/src/` in the original checkout.
- Result: exit 0; elapsed 1.49 seconds. 

- Recorded outcome: The working tree copied in 1.49 seconds. The later log records two kinds of tracked documentation omitted by the prescribed exclusions.

### A003 — Establish the audit recorder

- Start: 2026-10-10T15:41:20+00:00
- Before: I expect a small recorder inside the copy to preserve each expectation before its command, capture complete output, and record elapsed command and between-action time without changing project sources.
- Action: create `.audit/run.py` and `.audit/state.json` in the copy. The recorder runs commands only from that copy and appends this report.
- Result: recorder created; elapsed 0.00 seconds. Timestamp correction made during report review: about forty seconds after the copy completed were spent selecting a way to preserve pre-action predictions; the initial unmeasured prose estimate of two minutes was incorrect.

### A004 — Read the newcomer entry points

- Start: 2026-10-10T15:41:20+00:00
- Since previous action ended: 0.1 seconds (reading, planning, or conversation unless noted).
- Before: I expect AGENTS.md and the README to route helper additions to Meson, signing, inventory, identity regeneration, and source-drift checks; BUILD.md and SIGNING.md should give runnable build prerequisites without reading the excluded plan.
- Action (in the disposable copy):

```sh
cat AGENTS.md README.md docs/BUILD.md docs/SIGNING.md
```

- Result: exit 0; command elapsed 0.02 seconds; complete output in `.tmp/audit-narrative/src/.audit/A004.txt`.

- Observation (A004): The combined read produced 31,523 tokens and the tool display truncated it; I saw the routing and signing sections, but must read the hidden middle in smaller stretches. This was an unanticipated read-side dead end.

### A005 — Read README and map the long documents

- Start: 2026-10-10T15:41:35+00:00
- Since previous action ended: 15.5 seconds (reading, planning, or conversation unless noted).
- Before: I expect the smaller read to expose the complete shipped inventory and build links; line counts and headings will let me finish the initially truncated read in bounded chunks.
- Action (in the disposable copy):

```sh
cat README.md; wc -l docs/BUILD.md docs/SIGNING.md; rg -n "^#" docs/BUILD.md docs/SIGNING.md; rg --files -g AGENTS.md -g "!records/**" -g "!.tmp/**" -g "!.audit/**"
```

- Result: exit 0; command elapsed 0.05 seconds; complete output in `.tmp/audit-narrative/src/.audit/A005.txt`.

- Recorded outcome: The README contained the complete bundle inventory; BUILD and SIGNING had 530 and 570 lines respectively. The applicable non-scratch instruction files were identified.

### A006 — Read build inputs and phase order

- Start: 2026-10-10T15:41:46+00:00
- Since previous action ended: 10.8 seconds (reading, planning, or conversation unless noted).
- Before: I expect this section to identify the minimum toolchain, output-directory knobs, and the order in which compilation, inventory, signing, evidence, and archive creation happen.
- Action (in the disposable copy):

```sh
sed -n "1,204p" docs/BUILD.md
```

- Result: exit 0; command elapsed 0.02 seconds; complete output in `.tmp/audit-narrative/src/.audit/A006.txt`.

- Recorded outcome: The guide supplied the input list, thirty-step ordering, pre-assembly checks, output-directory behavior, and build-directory trust limits.

### A007 — Read build refusals and maintenance ownership

- Start: 2026-10-10T15:41:46+00:00
- Since previous action ended: 0.1 seconds (reading, planning, or conversation unless noted).
- Before: I expect the refusal catalogue and ownership sections to name every production file that adding a simple C helper requires, including generated documentation inputs.
- Action (in the disposable copy):

```sh
sed -n "205,426p" docs/BUILD.md
```

- Result: exit 0; command elapsed 0.02 seconds; complete output in `.tmp/audit-narrative/src/.audit/A007.txt`.

- Recorded outcome: The guide connected signing calls to the artifact, evidence, and README inventories and named the build manifest and baseline checks.

### A008 — Finish the generated phase and refusal tables

- Start: 2026-10-10T15:42:05+00:00
- Since previous action ended: 18.5 seconds (reading, planning, or conversation unless noted).
- Before: I expect bounded output to recover the table rows hidden by the earlier combined tool output, including the catalogue's declared coverage limits.
- Action (in the disposable copy):

```sh
sed -n "180,316p" docs/BUILD.md
```

- Result: exit 0; command elapsed 0.02 seconds; complete output in `.tmp/audit-narrative/src/.audit/A008.txt`.

- Recorded outcome: Recovered the refusal catalogue and its distinctions between behavioral, helper, and textual coverage.

### A009 — Read the build self-checking model

- Start: 2026-10-10T15:42:05+00:00
- Since previous action ended: 0.1 seconds (reading, planning, or conversation unless noted).
- Before: I expect the final build sections to explain manifest edits, grounding rules, and what regeneration does and does not prove.
- Action (in the disposable copy):

```sh
sed -n "427,530p" docs/BUILD.md
```

- Result: exit 0; command elapsed 0.02 seconds; complete output in `.tmp/audit-narrative/src/.audit/A009.txt`.

- Recorded outcome: The generator documentation specified the compared declarations and explicitly limited the guarantees to textual consistency.

### A010 — Read the signing build and native compile instructions

- Start: 2026-10-10T15:42:05+00:00
- Since previous action ended: 0.1 seconds (reading, planning, or conversation unless noted).
- Before: I expect the signing guide to provide concrete build commands, the known sandbox remedy, and a source-list maintenance recipe consistent with BUILD.md.
- Action (in the disposable copy):

```sh
sed -n "1,262p" docs/SIGNING.md
```

- Result: exit 0; command elapsed 0.02 seconds; complete output in `.tmp/audit-narrative/src/.audit/A010.txt`.

- Recorded outcome: SIGNING supplied the make invocation, toolchain minima, partial-build behavior, explicit signing list, and sandbox retry procedure.

### A011 — Source read with a recorder lapse

- Before: **No pre-action prediction was written.** I accidentally called the shell directly; this entry is retrospective and is not counted as a calibrated prediction.
- Action: `sed -n '95,157p' docs/SIGNING.md; cat meson.build; sed -n '1,220p' build.sh` in the disposable copy.
- Result: read the missing signing paragraphs, all Meson targets, and build admission through signing-identity validation. The shell completed in under 0.1 seconds. This exposed the fixed native flags and the location for an additional C executable. No files were changed by that read.

### A012 — Read assembly and inventory implementations

- Start: 2026-10-10T15:42:42+00:00
- Since previous action ended: 0.1 seconds (reading, planning, or conversation unless noted).
- Before: I expect an existing helper to provide the exact pattern for copying, minimum-version checks, signing, and evidence registration, with no need for a new build phase.
- Action (in the disposable copy):

```sh
sed -n "220,550p" build.sh; sed -n "1,105p" tests/lib/artifact.py; rg -n "sbpl-check|helpers|EXECUTABLES|def |ArgumentParser" tests/build-evidence.py tests/lib/native_sources.py; sed -n "1,110p" Makefile
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A012.txt`.

- Recorded outcome: Located the native-output minimum checks, assembly copies, explicit signing calls, evidence helper list, artifact inventory, and Makefile entry.

### A013 — Read linked checks and discover local prerequisites

- Start: 2026-10-10T15:43:01+00:00
- Since previous action ended: 19.1 seconds (reading, planning, or conversation unless noted).
- Before: I expect native_sources.py to have a target expectation list that must grow with the helper, generator instructions to identify the manifest schema, and the local keychain to list a usable Developer ID identity (the sandbox may hide it).
- Action (in the disposable copy):

```sh
sed -n '1,64p' tests/lib/native_sources.py; sed -n '186,255p' tests/lib/native_sources.py; sed -n '195,260p' tests/build-evidence.py; sed -n '1,100p' docs/generate_build.py; sed -n '1,150p' tests/suites/source_drift/README.md; rg -n 'source_drift|PW_TEST_OUT_DIR|sandboxed|Comparing native' tests/README.md; sed -n '550,650p' build.sh; security find-identity -v -p codesigning; command -v meson ninja dot
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A013.txt`.

- Recorded outcome: Found the explicit native target expectation and generator conventions. The sandbox listed zero identities; Meson, Ninja, and Graphviz were available.

### A014 — List signing identities outside the sandbox

- Start: 2026-10-10T15:43:32+00:00
- Since previous action ended: 31.0 seconds (reading, planning, or conversation unless noted).
- Before: The sandbox listed zero identities; SIGNING.md predicts keychain visibility can be refused there, so I expect the same security command outside it to list the installed Developer ID Application identity without a prompt.
- Action (in the disposable copy):

```sh
security find-identity -v -p codesigning
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A014.txt`.

- Recorded outcome: The same identity-listing command outside the sandbox found the Developer ID Application identity; no prompt was observed.

### A015 — Locate manifest and prose maintenance points

- Start: 2026-10-10T15:44:16+00:00
- Since previous action ended: 43.5 seconds (reading, planning, or conversation unless noted).
- Before: I expect to add one signing row, one native source expectation, and the helper to four inventories; count-bearing prose may also have baseline entries that must stay consistent with the new third C executable.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
import json
from pathlib import Path
m=json.loads(Path('docs/build.json').read_text())
print('BUILD MANIFEST KEYS', list(m))
for k in ('signing','knobs'):
 print(k, json.dumps(m[k], indent=2))
print('ASSEMBLE',json.dumps(next(s for s in m['steps'] if s['id']=='assemble'),indent=2))
p=json.loads(Path('tests/fixtures/docs/prose_baseline.json').read_text())
print('PROSE BASELINE',json.dumps(p,indent=2))
PY
rg -n 'two C|four executables|5 native|five native|sb_api_validator.*pw-probe-runner|pw-probe-runner.*sb_api_validator' AGENTS.md docs/SIGNING.md docs/BUILD.md tests/suites/source_drift tests/lib/native_sources.py tests/lib/meson_receipts.py
sed -n '1,115p' docs/generate_worker_identity.py
sed -n '496,539p' tests/README.md
```

- Result: exit 0; command elapsed 0.06 seconds; complete output in `.tmp/audit-narrative/src/.audit/A015.txt`.

- Recorded outcome: Located the signing-row schema and partial-build descriptions. The prose baseline contained no corresponding helper-count entry requiring an update.

### A016 — Repair copy prerequisites and save the pre-edit baseline

- Start: 2026-10-10T15:44:48+00:00
- Since previous action ended: 32.3 seconds (reading, planning, or conversation unless noted).
- Before: The prescribed dist exclusion removed documents build.sh copies and source_drift links to; I expect restoring just the working-tree README and AGENTS files to satisfy that dependency, and the baseline to isolate my edits from the copied uncommitted work.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
import shutil
root=Path.cwd()
(root/'dist').mkdir()
for name in ('README.md','AGENTS.md'):
 shutil.copy2(root.parents[2]/'dist'/name,root/'dist'/name)
print('Restored the two working-tree distribution documents; no distribution binaries copied.')
paths=['AGENTS.md','README.md','meson.build','build.sh','docs/build.json','docs/BUILD.md','docs/SIGNING.md','docs/build-steps.dot','docs/build-steps.svg','tests/lib/native_sources.py','tests/lib/artifact.py','tests/build-evidence.py','tests/suites/source_drift/README.md','tests/suites/source_drift/check_planner.py','controller/tools/pw_probe_runner/pw_probe_runner_abi.h','runner/Sources/PWRunnerCore/CWorker.swift','tests/lib/contract.py']
for name in paths:
 target=root/'.audit/baseline'/name
 target.parent.mkdir(parents=True,exist_ok=True)
 shutil.copy2(root/name,target)
print('Snapshotted',len(paths),'candidate edit paths before changing any project file.')
PY
cat dist/README.md dist/AGENTS.md
```

- Result: exit 0; command elapsed 0.05 seconds; complete output in `.tmp/audit-narrative/src/.audit/A016.txt`.

- Recorded outcome: Restored exactly the two distribution documents from the working tree and saved seventeen pre-edit files; no distribution binary was copied.

### A017 — Add and integrate the minimal stamp helper

- Start: 2026-10-10T15:46:10+00:00
- Since previous action ended: 82.0 seconds (reading, planning, or conversation unless noted).
- Before: I expect this six-line C program and conventional Meson target, copy, minimum check, explicit signature, source expectation, inventories, manifest row, and current-behavior prose to complete the source changes. Generated copies will deliberately remain stale until the next action.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
import json, copy

def edit(name, old, new):
 p=Path(name); text=p.read_text()
 if old not in text: raise ValueError(f'{name}: expected text absent: {old!r}')
 p.write_text(text.replace(old,new))
 print('edited',name)

p=Path('controller/tools/pw_stamp/pw_stamp.c'); p.parent.mkdir(); p.write_text('#include <stdio.h>\n\nint main(void) {\n    puts("policy witness");\n    return 0;\n}\n')
p=Path('meson.build'); p.write_text(p.read_text()+'''\n# A top-level helper that prints the project name.\npw_stamp = executable('pw-stamp',\n  files('controller/tools/pw_stamp/pw_stamp.c'),\n  c_args: c_executable_flags,\n  link_args: [macos_version_min],\n  override_options: executable_options)\n''')
edit('meson.build','# Native compilation for PolicyWitness: the C worker and validator, the C shim','# Native compilation for PolicyWitness: the C worker, validator and stamp helper, the C shim')
edit('meson.build','# The two C executables','# The C executables')
edit('build.sh','The two C executables still build.','The C executables still build, and pw-stamp ships.')
edit('build.sh','# Native compilation (the C worker and validator, the C shim, the Swift client','# Native compilation (the C worker, validator and stamp helper, the C shim, the Swift client')
edit('build.sh','SB_API_VALIDATOR_BIN="${MESON_BUILD_DIR}/sb_api_validator"','SB_API_VALIDATOR_BIN="${MESON_BUILD_DIR}/sb_api_validator"\n\n# Top-level project-name helper.\nPW_STAMP_BIN="${MESON_BUILD_DIR}/pw-stamp"')
edit('build.sh','NATIVE_OUTPUTS=("${SB_API_VALIDATOR_BIN}" "${PW_PROBE_RUNNER_BIN}")','NATIVE_OUTPUTS=("${SB_API_VALIDATOR_BIN}" "${PW_PROBE_RUNNER_BIN}" "${PW_STAMP_BIN}")')
edit('build.sh','chmod +x "${APP_BUNDLE}/Contents/MacOS/sbpl-check"','chmod +x "${APP_BUNDLE}/Contents/MacOS/sbpl-check"\n\ncp "${PW_STAMP_BIN}" "${APP_BUNDLE}/Contents/MacOS/pw-stamp"\nchmod +x "${APP_BUNDLE}/Contents/MacOS/pw-stamp"')
edit('build.sh','sign_macho "${APP_BUNDLE}/Contents/MacOS/sbpl-check"','sign_macho "${APP_BUNDLE}/Contents/MacOS/sbpl-check"\nsign_macho "${APP_BUNDLE}/Contents/MacOS/pw-stamp"')
edit('tests/lib/artifact.py',"('pw-runner-client', 'sandbox-log-observer', 'sbpl-check')","('pw-runner-client', 'sandbox-log-observer', 'sbpl-check', 'pw-stamp')")
edit('tests/build-evidence.py','        "sbpl-check",','        "sbpl-check",\n        "pw-stamp",')
edit('tests/lib/native_sources.py',"VALIDATOR = 'controller/tools/sb_api_validator/sb_api_validator.c'","VALIDATOR = 'controller/tools/sb_api_validator/sb_api_validator.c'\nSTAMP = 'controller/tools/pw_stamp/pw_stamp.c'")
edit('tests/lib/native_sources.py',"targets = {'sb_api_validator': {VALIDATOR}, 'pw-probe-runner': {WORKER}}","targets = {'sb_api_validator': {VALIDATOR}, 'pw-probe-runner': {WORKER}, 'pw-stamp': {STAMP}}")
edit('tests/lib/native_sources.py','and the client, worker and validator their single known','and the client, worker, validator and stamp helper their single known')
edit('README.md','  - `Contents/MacOS/sbpl-check` (SBPL compile-check helper)','  - `Contents/MacOS/sbpl-check` (SBPL compile-check helper)\n  - `Contents/MacOS/pw-stamp` (C helper that prints `policy witness` and exits 0)')
edit('AGENTS.md','the two C executables still build, no Swift compiler is discovered','the C executables still build and `pw-stamp` ships, no Swift compiler is discovered')
edit('docs/SIGNING.md','the C worker and validator, the C shim and the two','the C worker, validator and stamp helper, the C shim and the two')
edit('docs/SIGNING.md','copies the four executables from there','copies the native executables from there')
edit('docs/SIGNING.md','the two\nC executables still build','the\nC executables still build and `pw-stamp` ships')
edit('docs/SIGNING.md','both C executables','the C executables')
edit('docs/SIGNING.md','partial bundle without the XPC service, client or embedded helpers.','partial bundle with `pw-stamp` but without the XPC service, client or its embedded helpers.')
edit('docs/SIGNING.md','(when `BUILD_XPC=1`), `sandbox-log-observer`, `sbpl-check`.','(when `BUILD_XPC=1`), `sandbox-log-observer`, `sbpl-check`, `pw-stamp`.')
edit('docs/BUILD.md','minimum-checks the two C executables','minimum-checks the C executables')
edit('docs/BUILD.md','and packages a bundle without the client, the service or the embedded helpers;','and packages a bundle with `pw-stamp` but without the client, the service or its embedded helpers;')
edit('docs/BUILD.md','the C worker and validator, the C shim and the two Swift executables','the C worker, validator and stamp helper, the C shim and the two Swift executables')
edit('tests/suites/source_drift/README.md',"and the client's, worker's and validator's","and the client's, worker's, validator's and stamp helper's")
edit('tests/suites/source_drift/README.md','`pw-runner-client`, `pw-probe-runner` and `sb_api_validator`','`pw-runner-client`, `pw-probe-runner`, `sb_api_validator` and `pw-stamp`')
edit('tests/suites/source_drift/check_planner.py','only the two C executables','only the C executables')
p=Path('docs/build.json'); m=json.loads(p.read_text()); row=copy.deepcopy(m['signing'][2]); row['id']='sig_stamp'; row['target']=row['target'].replace('sbpl-check','pw-stamp'); row['sources'][0]['symbol']=row['target']; m['signing'].insert(3,row)
m['knobs'][0]['values']['0']='skip them; the C executables still build and pw-stamp ships (Meson xpc=false)'
s=next(s for s in m['steps'] if s['id']=='assemble'); s['reads']=s['reads'].replace('the three Rust outputs','the three Rust outputs, builddir/pw-stamp'); s['writes']=s['writes'].replace('the three Rust executables','the three Rust executables, pw-stamp')
p.write_text(json.dumps(m,indent=2)+'\n')
print('Updated build manifest; no new phase, refusal, flag, entitlement, or CLI command.')
PY
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A017.txt`.

- Recorded outcome: Added the six-line helper, conventional Meson target, minimum check, copy and signature, native expectation, inventory/evidence entries, build-manifest row, and current-behavior prose.

### A018 — Regenerate build documentation and worker identity

- Start: 2026-10-10T15:46:24+00:00
- Since previous action ended: 14.4 seconds (reading, planning, or conversation unless noted).
- Before: I expect the grounded build generator to accept the matching signing and inventory additions and update its tables, then the identity generator to update exactly its three owned copies. No graph topology or refusal-baseline change should be required.
- Action (in the disposable copy):

```sh
set -e
python3 docs/generate_build.py
python3 docs/generate_worker_identity.py
```

- Result: exit 0; command elapsed 0.38 seconds; complete output in `.tmp/audit-narrative/src/.audit/A018.txt`.

- Recorded outcome: The build generator wrote the document and figures. Worker identity regeneration changed exactly its three copies.

### A019 — Run the required signed make build

- Start: 2026-10-10T15:46:38+00:00
- Since previous action ended: 12.8 seconds (reading, planning, or conversation unless noted).
- Before: The generators passed, the local identity is known, and the missing distribution documents are restored. I expect this clean build to compile the Rust and native outputs, check six native targets, sign all eight bundled executables, generate evidence, verify it, and package within roughly two minutes. The known keychain restriction requires an unsandboxed command; if a keychain prompt appears I will stop.
- Action (in the disposable copy):

```sh
PATH=/opt/homebrew/opt/rustup/bin:$PATH make build IDENTITY='Developer ID Application: Adam Hyland (42D369QV8E)' DIST_DIR=/Users/raccoon/Desktop/Security/PolicyWitness/.tmp/audit-narrative/src/dist
```

- Result: exit 0; command elapsed 24.72 seconds; complete output in `.tmp/audit-narrative/src/.audit/A019.txt`.

- Observation (A019): The complete fresh signed build passed in 24.72 seconds, much sooner than my roughly two-minute estimate. It checked six native targets and eight consistently signed bundled executables, including pw-stamp. Cargo and Swift emitted warnings in unchanged sources; no keychain prompt was observed.

### A020 — Inspect the signed app as required

- Start: 2026-10-10T15:47:12+00:00
- Since previous action ended: 9.8 seconds (reading, planning, or conversation unless noted).
- Before: I expect the updated inventory and evidence entry to pass inspection; codesign may still report the documented sandbox-only verification failure, in which case I will retry the unchanged app outside it.
- Action (in the disposable copy):

```sh
python3 tests/lib/artifact.py /Users/raccoon/Desktop/Security/PolicyWitness/.tmp/audit-narrative/src/dist/PolicyWitness.app /Users/raccoon/Desktop/Security/PolicyWitness/.tmp/audit-narrative/src/inspection.json
```

- Result: exit 1; command elapsed 0.25 seconds; complete output in `.tmp/audit-narrative/src/.audit/A020.txt`.

- Recorded outcome: Inspection failed with signature errors on the app, service, and executable paths inside the sandbox.

### A021 — Retry unchanged artifact inspection outside the sandbox

The preceding gap includes waiting for the escalation request to complete, not artifact inspection work.

- Start: 2026-10-10T15:53:00+00:00
- Since previous action ended: 347.2 seconds (reading, planning, or conversation unless noted).
- Before: The inspector reported the exact signature failure SIGNING.md warned about; the build already verified these bytes outside the sandbox. I expect the identical inspection command outside it to pass without rebuilding, resigning, or changing the app.
- Action (in the disposable copy):

```sh
python3 tests/lib/artifact.py /Users/raccoon/Desktop/Security/PolicyWitness/.tmp/audit-narrative/src/dist/PolicyWitness.app /Users/raccoon/Desktop/Security/PolicyWitness/.tmp/audit-narrative/src/inspection.json
```

- Result: exit 0; command elapsed 0.30 seconds; complete output in `.tmp/audit-narrative/src/.audit/A021.txt`.

- Recorded outcome: Inspection passed against the unchanged app outside the sandbox; its saved JSON has ok true and no errors.

### A022 — Run the required source-drift suite

- Start: 2026-10-10T15:53:19+00:00
- Since previous action ended: 19.1 seconds (reading, planning, or conversation unless noted).
- Before: The build and artifact inspection are green in the requested order. I expect source_drift to accept the source and manifest changes, with any remaining issue most likely in documentation links or test fixtures after the prescribed copy exclusions. I expect roughly one minute and will not run the default battery.
- Action (in the disposable copy):

```sh
PATH=/opt/homebrew/opt/rustup/bin:$PATH PW_TEST_OUT_DIR=tests/out/runs/audit-narrative-01 tests/run.sh --suite source_drift
```

- Result: exit 1; command elapsed 91.14 seconds; complete output in `.tmp/audit-narrative/src/.audit/A022.txt`.

- Recorded outcome: The run failed four of six source-drift cases: source manifests, limits documentation, build documentation, and generator contracts. Contract and architecture cases passed. Full receipts remain in the first run directory.

### A023 — Inspect the failed drift-control output

- Start: 2026-10-10T15:55:07+00:00
- Since previous action ended: 16.3 seconds (reading, planning, or conversation unless noted).
- Before: I expect the retained logs to identify concrete missing copy files or fixed helper lists in test machinery; the already-passed direct build-document check suggests the production manifest itself is consistent.
- Action (in the disposable copy):

```sh
rg --files tests/out/runs/audit-narrative-01/suites/source_drift -g '*.log'; rg -n -C 3 'ERROR|FAIL|AssertionError|Traceback|missing|No such|unexpected|stale|not found' tests/out/runs/audit-narrative-01/suites/source_drift -g '*.log'
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A023.txt`.

- Recorded outcome: Found the missing staged helper source, missing scratch-policy links, obsolete mutation expectations, report prose scan, and Swift setup assertion failures. Before A024 I asked permission to copy only the missing policy file without opening or displaying it; no answer had arrived by report assembly.

### A024 — Read failing mutation controls and retained setup receipts

- Start: 2026-10-10T15:55:34+00:00
- Since previous action ended: 27.4 seconds (reading, planning, or conversation unless noted).
- Before: I expect the planner fixture to omit the new C source, the inventory mutation to match an obsolete exact tuple, and the seal mutation to assert an old numeric index; I also expect to find the actual Meson setup diagnostic before treating it as a sandbox failure.
- Action (in the disposable copy):

```sh
sed -n '145,225p' tests/suites/source_drift/check_planner.py; sed -n '215,380p' tests/suites/source_drift/build.py; cat tests/out/runs/audit-narrative-01/suites/source_drift/generator_contract/artifacts/generators.log; rg --files tests/out/runs/audit-narrative-01/suites/source_drift/runner_source_manifests_agree/artifacts -g '*.json' -g '*stdout*' -g '*stderr*'
```

- Result: exit 0; command elapsed 0.03 seconds; complete output in `.tmp/audit-narrative/src/.audit/A024.txt`.

- Recorded outcome: Confirmed the inventory substitutions and seal index depended on the old helper layout. The copied report was explicitly named by the prose-baseline failure.

### A025 — Confirm the omitted fixture source and test setup

- Start: 2026-10-10T15:55:52+00:00
- Since previous action ended: 17.7 seconds (reading, planning, or conversation unless noted).
- Before: I expect setup.stdout to name pw_stamp.c as absent from the planner fixture, and the fixture constructor to copy only the worker and validator tool directories. Swift-specific setup errors have no retained stdout in build.py, so I will use the documented unsandboxed retry when rerunning the suite.
- Action (in the disposable copy):

```sh
cat tests/out/runs/audit-narrative-01/suites/source_drift/runner_source_manifests_agree/artifacts/planner-controls/configured-unmodified/setup.stdout; sed -n '1,80p' tests/suites/source_drift/check_planner.py; sed -n '1,85p' tests/suites/source_drift/build.py; sed -n '1,60p' tests/README.md
```

- Result: exit 0; command elapsed 0.02 seconds; complete output in `.tmp/audit-narrative/src/.audit/A025.txt`.

- Recorded outcome: Meson setup.stdout named the missing pw_stamp.c in the nested fixture. Swift setup stdout was not retained by the other test.

### A026 — Update fixture staging and mutation targets

- Start: 2026-10-10T15:56:22+00:00
- Since previous action ended: 30.1 seconds (reading, planning, or conversation unless noted).
- Before: I expect copying the new source into the planner fixture, targeting the seal by manifest id, and making each inventory mutation independent of the last list element to preserve the intended negative controls. Moving my accidentally copied incomplete report out of docs should remove that audit-only prose failure. The signed helper should print exactly the requested words.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
import shutil, subprocess
p=Path('tests/suites/source_drift/build.py')
b=Path('.audit/baseline')/p; b.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,b)
s=p.read_text()
old="'signing order: entry 7'"
new='f"signing order: entry {next(i for i, row in enumerate(manifest[\'signing\'], 1) if row[\'id\'] == \'seal_app\')}"'
assert s.count(old)==1; s=s.replace(old,new)
old='artifact.write_text(artifact.read_text().replace("\'sbpl-check\'))", "\'sbpl-check\', \'extra-tool\'))", 1))'
new='artifact.write_text(self.mutated("\'sbpl-check\'", "\'sbpl-check\', \'extra-tool\'", text=artifact.read_text()))'
assert s.count(old)==1; s=s.replace(old,new)
old='evidence.write_text(evidence.read_text().replace(\'"sbpl-check",\\n    ]\', \'"sbpl-check",\\n        "extra-tool",\\n    ]\', 1))'
new='evidence.write_text(self.mutated(\'"sbpl-check",\', \'"sbpl-check",\\n        "extra-tool",\', text=evidence.read_text()))'
assert s.count(old)==1; p.write_text(s.replace(old,new))
p=Path('tests/suites/source_drift/check_planner.py'); s=p.read_text()
old="             'controller/tools/sb_api_validator/sb_api_validator.c',"
assert s.count(old)==1; p.write_text(s.replace(old,old+" 'controller/tools/pw_stamp/pw_stamp.c',"))
Path('docs/BUILD-DOC-AUDIT-NARRATIVE-REPORT.md').rename('.audit/report-copied-during-setup.md')
print('Updated planner source staging and three mutation expectations; moved the accidentally copied incomplete report out of docs, preserving it.')
r=subprocess.run(['dist/PolicyWitness.app/Contents/MacOS/pw-stamp'],capture_output=True,text=True)
assert (r.returncode,r.stdout,r.stderr)==(0,'policy witness\\n'.replace('\\n','\n'),'')
print('pw-stamp: stdout exactly policy witness plus newline; exit 0; empty stderr.')
PY
```

- Result: exit 0; command elapsed 0.35 seconds; complete output in `.tmp/audit-narrative/src/.audit/A026.txt`.

- Recorded outcome: Repaired fixture staging and three mutation expressions; preserved the accidentally copied report under .audit. The built helper printed the requested words plus newline, returned zero, and emitted no stderr.

### A027 — Task 2: enumerate and choose a challenge while awaiting the policy-file answer

- Start: 2026-10-10T15:56:57+00:00
- Since previous action ended: 34.8 seconds (reading, planning, or conversation unless noted).
- Before: I expect the grounded manifest to support a small exact minimum-control query using substantially fewer than one hundred implementation lines. I will compare three candidate ideas before selecting that one, and distinguish declared coverage from proof that a test actually asserts a refusal.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
import json
from pathlib import Path
m=json.loads(Path('docs/build.json').read_text())
choices=[
 {'name':'Minimum refusal-control portfolio','why':'The manifest can become an exact set-cover problem: find the smallest existing behavioral/helper citation roster that spans every covered refusal, while retaining textual-only gaps. No document proposes that query.','work':'A small Python command importing the existing grounded manifest reader, enumerating control subsets, and emitting a verifiable JSON answer.'},
 {'name':'Signed native lineage card','why':'Join one real native receipt to the signed BOM and structural comparison, giving each shipped native helper a trace from configured target and compile command to observed signed bytes; the docs describe those ingredients separately.','work':'A small adapter over meson_receipts, native_compare, and the evidence manifest, with explicit distinctions between source membership and byte provenance.'},
 {'name':'Failure disambiguator from a real build log','why':'Combine the last banner and exit status with the manifest to enumerate candidate refusal sites and expose where additional message evidence is necessary. No document provides a run-specific query.','work':'A short banner matcher and manifest filter with a test on a retained failed run.'}
]
Path('.audit/challenge-candidates.json').write_text(json.dumps(choices,indent=2)+'\n')
controls={}
for r in m['refusals']:
 for c in r['checks']:
  if c['coverage'] in ('behavioral','helper'):
   controls.setdefault((c['path'],c['symbol']),set()).add(r['id'])
print('Selected:',choices[0]['name'])
print('Control references:',len(controls))
print('Covered refusal ids:',len(set().union(*controls.values())))
for (path,symbol),rows in sorted(controls.items()):
 print(len(rows),path,symbol)
PY
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A027.txt`.

- Recorded outcome: Listed three candidates and selected the coverage query. The first inventory found sixteen controls covering thirty-seven distinct refusal rows.

### A028 — Inspect grounding APIs for the challenge

- Start: 2026-10-10T15:57:28+00:00
- Since previous action ended: 30.7 seconds (reading, planning, or conversation unless noted).
- Before: The first query found sixteen distinct controls for thirty-seven covered rows, with disjoint row sets; a minimum-full-coverage answer alone would simply return all sixteen. I expect the same small implementation to answer the more useful budget frontier: the most declared coverage available at each control-count budget, retaining helper versus behavioral distinctions and all uncovered rows.
- Action (in the disposable copy):

```sh
rg -n '^def (load_manifest|.*problems|validate|main|.*model|.*ground)' docs/generate_build.py; sed -n '1120,1210p' docs/generate_build.py; cat tests/suites/source_drift/build_rules.py; sed -n '408,439p' tests/README.md
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A028.txt`.

- Recorded outcome: The row sets were disjoint, so the complete minimum roster alone would return all controls; the attempt expanded to the optimal coverage frontier at each control-count budget.

### A029 — Read the combined grounding entry point

- Start: 2026-10-10T15:58:04+00:00
- Since previous action ended: 36.6 seconds (reading, planning, or conversation unless noted).
- Before: I expect script_problems to combine all existing grounding checks, letting the challenge refuse an inconsistent manifest instead of producing a plausible optimization from stale declarations.
- Action (in the disposable copy):

```sh
sed -n '715,766p' docs/generate_build.py; sed -n '975,1015p' docs/generate_build.py
```

- Result: exit 0; command elapsed 0.02 seconds; complete output in `.tmp/audit-narrative/src/.audit/A029.txt`.

- Recorded outcome: The existing script_problems entry point included every grounding comparison and the baseline check.

### A030 — Implement the exact coverage-budget query

- Start: 2026-10-10T15:58:43+00:00
- Since previous action ended: 38.4 seconds (reading, planning, or conversation unless noted).
- Before: I expect a standalone script below one hundred lines to reuse all existing grounding checks, enumerate every subset of the sixteen cited controls, maximize covered rows at each control-count budget, prefer behavioral coverage on ties, and report all baseline gaps without changing build behavior.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
program = "#!/usr/bin/env python3\n\"\"\"Exact declared-refusal coverage by cited-control budget; no tests are run.\"\"\"\nimport argparse\nimport hashlib\nimport json\nimport sys\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[2]\nsys.path.insert(0, str(ROOT / \"docs\"))\nimport generate_build as build\n\nparser = argparse.ArgumentParser(description=__doc__)\nparser.add_argument(\"--variant\", choices=(\"full\", \"partial\"), default=\"full\")\nargs = parser.parse_args()\nmanifest = build.load_manifest(ROOT / build.MANIFEST_NAME, ROOT)\nproblems = build.script_problems(manifest, ROOT)\nif problems:\n    raise SystemExit(\"\\n\".join(problems))\nrows = [r for r in manifest[\"refusals\"] if args.variant in r[\"variants\"]]\ncontrols = {}\nfor i, row in enumerate(rows):\n    for ref in row[\"checks\"]:\n        if ref[\"coverage\"] not in (\"behavioral\", \"helper\"):\n            continue\n        key = ref[\"path\"] + \"::\" + ref[\"symbol\"]\n        masks = controls.setdefault(key, [0, 0])\n        masks[0] |= 1 << i\n        if ref[\"coverage\"] == \"behavioral\":\n            masks[1] |= 1 << i\nkeys = sorted(controls)\nif len(keys) > 22:\n    raise SystemExit(\"Exact search is bounded to 22 cited controls; no approximate answer.\")\ncount = lambda mask: bin(mask).count(\"1\")\nstates = [(0, 0)] * (1 << len(keys))\nbest = {0: (0, 0, 0)}\nfor chosen in range(1, len(states)):\n    bit = chosen & -chosen\n    previous = states[chosen ^ bit]\n    coverage, behavioral = controls[keys[bit.bit_length() - 1]]\n    states[chosen] = (previous[0] | coverage, previous[1] | behavioral)\n    budget = count(chosen)\n    score = (count(states[chosen][0]), count(states[chosen][1]), -chosen)\n    if budget not in best or score > best[budget]:\n        best[budget] = score\nids = lambda mask: [row[\"id\"] for i, row in enumerate(rows) if mask & (1 << i)]\nfrontier = [\n    dict(budget=budget, covered=score[0], behavioral=score[1],\n         controls=[key for i, key in enumerate(keys) if -score[2] & (1 << i)])\n    for budget, score in sorted(best.items())\n]\nuncovered = ((1 << len(rows)) - 1) ^ states[-1][0]\nreport = dict(\n    variant=args.variant, unit=\"one cited control, not runtime or subtest count\",\n    guarantee=\"Optimal over declared coverage; citations do not prove test assertions.\",\n    manifest_sha256=hashlib.sha256((ROOT / build.MANIFEST_NAME).read_bytes()).hexdigest(),\n    total_refusals=len(rows), covered=count(states[-1][0]), uncovered=ids(uncovered),\n    controls={key: dict(refusals=ids(masks[0]), behavioral_refusals=ids(masks[1]))\n              for key, masks in sorted(controls.items())},\n    subsets_enumerated=len(states), frontier=frontier,\n    minimum_complete_budget=next(p[\"budget\"] for p in frontier if p[\"covered\"] == count(states[-1][0])),\n)\nprint(json.dumps(report, indent=2))\n"
p=Path('tests/lib/build_control_frontier.py')
assert not p.exists()
p.write_text(program)
print('Created',p,'with',len(program.splitlines()),'physical lines.')
PY
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A030.txt`.

- Recorded outcome: Created a standalone sixty-three-line query without changing production build machinery.

### A031 — Run the challenge for both variants and independently check optimality

- Start: 2026-10-10T15:59:09+00:00
- Since previous action ended: 26.4 seconds (reading, planning, or conversation unless noted).
- Before: The initial row sets were disjoint, so I expect the full-build frontier to cover twenty rows with one control, twenty-three with two, and all thirty-seven only with all sixteen. An independent set-based check can prove each optimum by the sum of the largest disjoint set sizes; the partial variant should remove the two Swift-only covered rows.
- Action (in the disposable copy):

```sh
set -e
python3 tests/lib/build_control_frontier.py --variant full > .audit/challenge-full.json
python3 tests/lib/build_control_frontier.py --variant partial > .audit/challenge-partial.json
python3 - <<'PY'
import json
from pathlib import Path
for variant in ('full','partial'):
 r=json.loads(Path(f'.audit/challenge-{variant}.json').read_text())
 sets=[set(c['refusals']) for c in r['controls'].values()]
 assert sum(map(len,sets))==len(set().union(*sets))
 sizes=sorted(map(len,sets),reverse=True)
 for p in r['frontier']:
  chosen=[r['controls'][key] for key in p['controls']]
  union=set().union(*(set(c['refusals']) for c in chosen))
  behavioral=set().union(*(set(c['behavioral_refusals']) for c in chosen))
  assert len(chosen)==p['budget'] and len(union)==p['covered']
  assert len(behavioral)==p['behavioral']
  assert p['covered']==sum(sizes[:p['budget']])
 assert r['minimum_complete_budget']==len(sets)
 assert r['covered']+len(r['uncovered'])==r['total_refusals']
 print(variant,':',r['total_refusals'],'refusals;',r['covered'],'covered;',len(r['uncovered']),'uncovered;',len(sets),'controls;',r['subsets_enumerated'],'subsets')
 print('Budget frontier:',[(p['budget'],p['covered'],p['behavioral']) for p in r['frontier']])
 print('Independent check: disjoint declared row sets establish the sum-of-largest-sets upper bound, attained at every budget.')
PY
```

- Result: exit 0; command elapsed 0.45 seconds; complete output in `.tmp/audit-narrative/src/.audit/A031.txt`.

- Recorded outcome: Both full and partial variants completed. Independent disjoint-set upper bounds matched every budget point.

### A032 — Check that the challenge refuses inconsistent build data

- Start: 2026-10-10T15:59:36+00:00
- Since previous action ended: 26.5 seconds (reading, planning, or conversation unless noted).
- Before: I expect removing the declared timestamp flag from pw-stamp's manifest row, while leaving the real signing command intact, to make the query refuse before producing JSON. I will restore the exact manifest bytes in a finally block; this is a control of the new reader, with no build or signing operation.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
import json, subprocess
from pathlib import Path
p=Path('docs/build.json'); before=p.read_bytes()
try:
 m=json.loads(before); row=next(r for r in m['signing'] if r['id']=='sig_stamp')
 row['flags'].remove('--timestamp')
 p.write_text(json.dumps(m,indent=2)+'\n')
 r=subprocess.run(['python3','tests/lib/build_control_frontier.py'],capture_output=True,text=True)
 Path('.audit/challenge-refusal.stdout').write_text(r.stdout)
 Path('.audit/challenge-refusal.stderr').write_text(r.stderr)
 assert r.returncode!=0 and 'signing order: entry 4' in r.stderr and not r.stdout
 print('Controlled manifest mismatch refused with exit',r.returncode,'before emitting any frontier.')
 print(r.stderr.strip())
finally:
 p.write_bytes(before)
assert p.read_bytes()==before
print('Original manifest bytes restored exactly.')
PY
```

- Result: exit 0; command elapsed 0.18 seconds; complete output in `.tmp/audit-narrative/src/.audit/A032.txt`.

- Recorded outcome: A timestamp-flag disagreement was refused with exit one before any JSON answer; the exact manifest bytes were restored.

### A033 — Retry build-document controls outside the sandbox

The preceding gap includes waiting for the escalation request to complete.

- Start: 2026-10-10T16:03:07+00:00
- Since previous action ended: 210.3 seconds (reading, planning, or conversation unless noted).
- Before: The helper-list and seal-index controls are updated. I expect the two Swift option controls that failed at Meson setup inside the sandbox to pass outside it, as SIGNING.md predicts for Swift discovery. This targeted run does not depend on the pending scratch-policy copy and does not invoke the default battery.
- Action (in the disposable copy):

```sh
PATH=/opt/homebrew/opt/rustup/bin:$PATH python3 tests/suites/source_drift/build.py
```

- Result: exit 0; command elapsed 33.83 seconds; complete output in `.tmp/audit-narrative/src/.audit/A033.txt`.

- Recorded outcome: All thirteen build-document tests passed outside the sandbox, including both Swift-option controls.

### A034 — Capture experiment-only diffs and verify source isolation

- Start: 2026-10-10T16:04:12+00:00
- Since previous action ended: 31.0 seconds (reading, planning, or conversation unless noted).
- Before: I expect the saved pre-edit files still to match the original checkout exactly, with all helper and test changes confined to the copy. The new challenge should show a one-file, sixty-three-line diff, and neither experiment should include the user's pre-existing uncommitted work in its diff statistics.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
import difflib, json
base=Path('.audit/baseline'); original=Path.cwd().parents[2]
paths=sorted(p.relative_to(base) for p in base.rglob('*') if p.is_file())
paths.append(Path('controller/tools/pw_stamp/pw_stamp.c'))
stats=[]; patches=[]
for path in paths:
 old=(base/path).read_text() if (base/path).exists() else ''
 new=path.read_text()
 if (base/path).exists():
  assert (original/path).read_bytes()==(base/path).read_bytes(),f'Original source no longer matches saved baseline: {path}'
 else:
  assert not (original/path).exists()
 diff=list(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+str(path),tofile='b/'+str(path)))
 if not diff: continue
 additions=sum(line.startswith('+') and not line.startswith('+++') for line in diff)
 deletions=sum(line.startswith('-') and not line.startswith('---') for line in diff)
 stats.append(dict(path=str(path),additions=additions,deletions=deletions)); patches.extend(diff)
Path('.audit/task1.patch').write_text(''.join(patches))
Path('.audit/task1-stat.json').write_text(json.dumps(stats,indent=2)+'\n')
for row in stats: print(row['path'],f"+{row['additions']} -{row['deletions']}")
print('Task 1:',len(stats),'files;',sum(r['additions'] for r in stats),'insertions;',sum(r['deletions'] for r in stats),'deletions, relative to copied working-tree baseline.')
p=Path('tests/lib/build_control_frontier.py')
Path('.audit/task2.patch').write_text(''.join(difflib.unified_diff([],p.read_text().splitlines(keepends=True),fromfile='/dev/null',tofile='b/'+str(p))))
print('Task 2: 1 file changed,',len(p.read_text().splitlines()),'insertions.')
assert not (original/p).exists()
print('Original sources checked against saved pre-edit bytes: unchanged. Experiment source files exist only in the disposable copy.')
PY
```

- Result: exit 0; command elapsed 0.06 seconds; complete output in `.tmp/audit-narrative/src/.audit/A034.txt`.

- Recorded outcome: Task 1 diff: nineteen files, 109 insertions and 47 deletions. Task 2 diff: one file, 63 insertions. Saved original source bytes still matched.

### A035 — Review audit timing and verified results for the report

- Start: 2026-10-10T16:05:17+00:00
- Since previous action ended: 65.4 seconds (reading, planning, or conversation unless noted).
- Before: I expect the chronological timestamps to support exact elapsed stretches, the saved inspection to remain green, and the action records to expose any logging gaps instead of silently smoothing them over. The policy-file clarification is still pending, so no final source-drift success is claimed.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
import json
r=Path('../../../docs/BUILD-DOC-AUDIT-NARRATIVE-REPORT.md')
for line in r.read_text().splitlines():
 if line.startswith('### A') or line.startswith('- Start:') or 'About two minutes' in line:
  print(line)
actions=[json.loads(s) for s in Path('.audit/actions.jsonl').read_text().splitlines()]
for a in actions:
 print(a['id'],a['label'],a['start'],a['end'],f"{a['elapsed']:.2f}s",'exit',a['code'])
p=Path('inspection.json'); d=json.loads(p.read_text()); print('INSPECTION',d['ok'],'errors',len(d['errors']))
PY
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A035.txt`.

- Recorded outcome: Inspection remained green. Timestamp review exposed the inaccurate informal setup estimate, corrected in A036.

### A036 — Correct timing prose against the recorded timestamps

- Start: 2026-10-10T16:05:43+00:00
- Since previous action ended: 26.2 seconds (reading, planning, or conversation unless noted).
- Before: I expect the setup interval to be about forty seconds, not the unmeasured two-minute phrase I initially wrote. I will correct that result explicitly and identify the long pre-command intervals that included escalation waits, while preserving the disclosure that A011 lacked a pre-action expectation.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
p=Path('../../../docs/BUILD-DOC-AUDIT-NARRATIVE-REPORT.md')
s=p.read_text()
s=s.replace('Timestamp correction made during report review: about forty seconds after the copy completed were spent selecting a way to preserve pre-action predictions; the initial unmeasured prose estimate of two minutes was incorrect.','Timestamp correction made during report review: about forty seconds after the copy completed were spent selecting a way to preserve pre-action predictions; the initial unmeasured prose estimate of two minutes was incorrect.')
s=s.replace('### A021 — Retry unchanged artifact inspection outside the sandbox\n','### A021 — Retry unchanged artifact inspection outside the sandbox\n\nThe preceding gap includes waiting for the escalation request to complete, not artifact inspection work.\n')
s=s.replace('### A033 — Retry build-document controls outside the sandbox\n','### A033 — Retry build-document controls outside the sandbox\n\nThe preceding gap includes waiting for the escalation request to complete.\n')
p.write_text(s)
print('Corrected the recorder-setup estimate and annotated the two long escalation gaps; retained the explicit A011 prediction lapse.')
PY
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A036.txt`.

- Observation (A036): A report-drafting tool call after this entry failed at JavaScript parsing (Unexpected identifier policy), before any shell command or file write. Its submitted expectation was to prepare the surprise table, calibration count, and challenge result. I will resubmit the report text with safe delimiters; no project or report bytes changed in that failed call.

- Recorded outcome: Corrected the setup estimate and identified escalation waits in the long timing gaps; preserved the A011 logging lapse.

### A037 — Draft findings with safe text delimiters

- Start: 2026-10-10T16:08:55+00:00
- Since previous action ended: 192.0 seconds (reading, planning, or conversation unless noted).
- Before: I expect the recorded actions to support ten explicit expectation gaps and twenty matching observations, plus the challenge's exact diff and timing. I will prepare the after-log sections while leaving final source-drift status pending.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
from datetime import datetime
import json
text="## Part 1: surprises\n\nThese are expectation gaps, not recommendations or explanations of the system. S01, S06, S10, and S11 are audit-process events.\n\n| Id | Log entries | What I believed before the action | What I observed | Valence |\n| --- | --- | --- | --- | ---: |\n| S01 | A004–A010 | The combined newcomer-document read would give me the contents in one usable tool response. | The response was truncated, and smaller reads were necessary. | −1 |\n| S02 | A002, A012, A016, A022–A025 | The prescribed copy would preserve the source and documents needed for the checks while omitting output trees. | It omitted the tracked distribution documents and linked scratch policy; the former needed restoration and the latter triggered link failures and a clarification request. | −1 |\n| S03 | A019 | A fresh Rust, C, Swift, signed and packaged build would take roughly two minutes. | The complete build passed in 24.72 seconds. | +1 |\n| S04 | A022–A025 | The registered helper and native expectation would suffice for the source-manifest controls. | A nested planner fixture omitted the new C file and Meson refused its setup. | −1 |\n| S05 | A022–A024 | The inventory and signing mutation controls would still exercise their intended changes after adding a helper. | Two inventory substitutions depended on the old last element, and the seal assertion expected entry seven instead of eight. | −1 |\n| S06 | A022–A024 | The unlinked, incomplete report copied during setup would remain separate from production-document checks. | The prose baseline scanner included it and rejected a measured-duration sentence. | −1 |\n| S07 | A010, A022, A024, A033 | The guide's description of the source-drift manifest reader suggested the suite would avoid Swift discovery in the sandbox. | The Swift-option controls performed setup, failed there in the sandbox, and passed in the later unsandboxed run. | −1 |\n| S08 | A022 | The source-drift run would take roughly one minute. | The failed run took 91.14 seconds. | −1 |\n| S09 | A023–A025 | Retained failure logs would name the concrete setup problem. | The planner receipt named the absent file, but the Swift controls reported blank captured stderr without retaining setup stdout. | −1 |\n| S10 | After A036 | The report-drafting tool call would write the findings text. | A JavaScript delimiter error rejected the call before any shell command or file write. | −1 |
| S11 | A041 | The report-structure assertion would find the numbered log entries. | An over-escaped digit pattern found none; the later git-status command still made the shell return zero. | −1 |\n\n## Part 1: non-surprise count\n\n**20 calibration observations** matched predictions. This counts the observations below, not every tool invocation; an action can have expected functionality and a surprising duration. A001 has only its original broad chat expectation. A011 had no pre-action prediction and is excluded. No retrospectively invented expectation is counted.\n\n| # | Entries | Expected and observed |\n| ---: | --- | --- |\n| 1 | A005 | README enumerated the shipped executables and build/signing links. |\n| 2 | A006 | BUILD described inputs, directory knobs, and phase order. |\n| 3 | A007 | BUILD identified ownership of compilation, signing, inventories, and generated data. |\n| 4 | A009 | The generator account distinguished textual agreement from runtime refusal. |\n| 5 | A010 | SIGNING supplied concrete build commands and the sandbox retry procedure. |\n| 6 | A012 | Existing helpers supplied copy, minimum-version, signing, and evidence patterns without a new phase. |\n| 7 | A013 | The source checker had an explicit target expectation that needed the helper. |\n| 8 | A013–A014 | The sandbox hid the identity; the unsandboxed listing found it, as documented. |\n| 9 | A015 | The manifest exposed the signing row and partial-build description; no relevant prose-baseline entry needed growth. |\n| 10 | A017 | The direct source and inventory edits applied without an implementation error. |\n| 11 | A018 | Generation accepted the additions and updated exactly three identity copies. |\n| 12 | A019 | The build checked six native targets and signed eight bundled executables in the documented order. |\n| 13 | A020 | Inspection produced the documented sandbox signature-verification failure. |\n| 14 | A021 | The same inspection passed outside the sandbox against unchanged app bytes. |\n| 15 | A023 | The direct production build-document check was green while mutation-control logs held failures. |\n| 16 | A024 | The predicted obsolete inventory literals and numeric seal index were present. |\n| 17 | A025 | The receipt named the absent stamp source, and fixture staging omitted it. |\n| 18 | A026 | The edits applied and the signed helper printed exactly the requested words plus newline, exited zero, and wrote no stderr. |\n| 19 | A033 | All thirteen build-document controls passed outside the sandbox. |\n| 20 | A034–A035 | Saved inspection stayed green and original source files matched pre-edit bytes. |\n\n## Part 2: candidates\n\n1. **Minimum refusal-control portfolio.** Turn declared coverage into an exact set-cover query, finding the smallest existing control roster spanning covered refusals while retaining textual-only gaps. No document read proposes this query. It takes a small Python command using the grounded manifest reader and subset enumeration.\n2. **Signed native lineage card.** Join one native receipt, the signed evidence manifest, and structural comparison to trace a helper from configured target and compile command to observed signed bytes. The documents describe the ingredients separately. It takes a short adapter over the existing native tools with explicit limits on what the join establishes.\n3. **Failure disambiguator from a real build log.** Combine the last banner and exit status with the manifest to enumerate candidate refusal sites and expose where message evidence is still necessary. No document read supplies a run-specific query. It takes a banner matcher and manifest filter, checked against a retained failed run.\n\n## Part 2: attempt and result\n\nSelected the minimum-control idea and added tests/lib/build_control_frontier.py in the copy. The first inventory found that all sixteen control references own disjoint refusal sets, so minimizing the complete roster alone returns every control. The implemented query also calculates optimal coverage at every control-count budget. It validates citations and script/manifest/inventory/baseline agreement through the existing generator before searching, enumerates all subsets, maximizes covered rows, prefers behavioral coverage on ties, and reports textual-only gaps.\n\n**It worked.** Both variants enumerated 65,536 subsets. Independent set-based verification established disjoint row sets and showed that every reported budget attained the sum-of-largest-sets upper bound. A controlled timestamp-flag mismatch in the manifest was refused with exit one and no frontier output; the original manifest bytes were restored exactly.\n\n| Variant | Refusals | Rows with declared controls | Uncovered | One-control maximum | Two-control maximum | Minimum controls for all covered rows |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n| Full | 65 | 37 | 28 | 20 | 23 | 16 |\n| Partial | 57 | 35 | 22 | 18 | 21 | 16 |\n\nThe full-build optimum at budget one is the Meson option-assertion helper control. Budget two adds the build-directory refusal control, cited by three behavioral rows. The complete full-build roster contains fourteen behaviorally cited rows and twenty-three helper-cited rows.\n\nThis enables inspection of declared coverage tradeoffs while keeping helper checks distinct from controls that drive the build, and keeping uncovered refusals visible. The unit is one cited control, not one command, one subtest, or measured runtime. The query neither runs controls nor proves that their assertions establish the cited rows. Exact search is bounded to twenty-two cited controls; larger input is refused.\n\nDiff stat relative to the copied working tree:\n\n    tests/lib/build_control_frontier.py | 63 +++++++++++++++++++++++++++++++++\n    1 file changed, 63 insertions(+)\n\nThe implementation is **63 physical lines**, with no dependency or existing build-code changes. The one-off validation commands remain in the action log and were not added as test files.\n\nArtifacts in the disposable copy: .audit/task1.patch, .audit/task1-stat.json, .audit/task2.patch, .audit/challenge-full.json, .audit/challenge-partial.json, and negative-control stdout/stderr. Task 1's source changes total nineteen files, 109 insertions and 47 deletions relative to the saved working-tree baseline, including generated files. Counts exclude pre-existing changes and restored setup documents.\n"
a={r['id']:r for r in (json.loads(s) for s in Path('.audit/actions.jsonl').read_text().splitlines())}
elapsed=(datetime.fromisoformat(a['A032']['end'])-datetime.fromisoformat(a['A027']['start'])).total_seconds()
text+=f"\nTask 2 candidate selection through the negative control (A027–A032) took **{elapsed:.2f} seconds ({elapsed/60:.2f} minutes)** including reading and reasoning. Both variants plus independent verification took **{a['A031']['elapsed']:.2f} seconds**; the negative-control command took **{a['A032']['elapsed']:.2f} seconds**.\n"
Path('.audit/report-findings.md').write_text(text)
print('Prepared ten signed expectation gaps, twenty calibration observations, and the complete challenge result.')
print('Task 2 selection-to-control elapsed:',elapsed,'seconds')
PY
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A037.txt`.

- Recorded outcome: Prepared the findings and complete challenge write-up without claiming a successful final suite run.

### A038 — Verify the repaired planner fixture independently

- Start: 2026-10-10T16:09:40+00:00
- Since previous action ended: 45.1 seconds (reading, planning, or conversation unless noted).
- Before: The recorded failure named the stamp source omitted from the disposable fixture, and staging now includes it. I expect the planner and configured-source positive and negative controls to pass using C-only builds, independently of the missing scratch-policy link.
- Action (in the disposable copy):

```sh
PATH=/opt/homebrew/opt/rustup/bin:$PATH python3 tests/suites/source_drift/check_planner.py /Users/raccoon/Desktop/Security/PolicyWitness/.tmp/audit-narrative/src/.audit/planner-controls-fixed
```

- Result: exit 0; command elapsed 24.95 seconds; complete output in `.tmp/audit-narrative/src/.audit/A038.txt`.

- Recorded outcome: All thirty-three planner and host-source controls passed, including the repaired configured-source fixture.

### A039 — Keep final report checks inside the ordered log

- Start: 2026-10-10T16:10:31+00:00
- Since previous action ended: 25.6 seconds (reading, planning, or conversation unless noted).
- Before: I expect a small recorder-only change to let report assembly and validation remain in the chronological action log before the surprise table, even after the findings sections are present; no project source or build artifact should change.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
p=Path('.audit/run.py'); s=p.read_text()
old='''def append(s):
    with REPORT.open("a") as f:
        f.write(s)
'''
new='''def append(s):
    text = REPORT.read_text()
    marker = "\\n## Part 1: surprises\\n"
    if marker in text:
        before, after = text.split(marker, 1)
        REPORT.write_text(before + s + marker + after)
    else:
        with REPORT.open("a") as f:
            f.write(s)
'''
assert s.count(old)==1
p.write_text(s.replace(old,new))
print('Recorder now inserts subsequent log entries before the findings sections.')
PY
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A039.txt`.

- Recorded outcome: Recorder-only adjustment kept later action entries before the findings sections.

### A040 — Assemble the requested report with explicit remaining status

- Start: 2026-10-10T16:12:13+00:00
- Since previous action ended: 102.0 seconds (reading, planning, or conversation unless noted).
- Before: I expect the report to preserve every action and pre-action expectation, add concrete outcomes beside command timings, place the surprise table and calibration count after the log, and include the completed challenge. The final source-drift run remains pending the unanswered policy-file clarification; the report must say so plainly.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
from datetime import datetime, timezone
import re
report=Path('../../../docs/BUILD-DOC-AUDIT-NARRATIVE-REPORT.md')
s=report.read_text()
notes={
 'A002':'The working tree copied in 1.49 seconds. The later log records two kinds of tracked documentation omitted by the prescribed exclusions.',
 'A005':'The README contained the complete bundle inventory; BUILD and SIGNING had 530 and 570 lines respectively. The applicable non-scratch instruction files were identified.',
 'A006':'The guide supplied the input list, thirty-step ordering, pre-assembly checks, output-directory behavior, and build-directory trust limits.',
 'A007':'The guide connected signing calls to the artifact, evidence, and README inventories and named the build manifest and baseline checks.',
 'A008':'Recovered the refusal catalogue and its distinctions between behavioral, helper, and textual coverage.',
 'A009':'The generator documentation specified the compared declarations and explicitly limited the guarantees to textual consistency.',
 'A010':'SIGNING supplied the make invocation, toolchain minima, partial-build behavior, explicit signing list, and sandbox retry procedure.',
 'A012':'Located the native-output minimum checks, assembly copies, explicit signing calls, evidence helper list, artifact inventory, and Makefile entry.',
 'A013':'Found the explicit native target expectation and generator conventions. The sandbox listed zero identities; Meson, Ninja, and Graphviz were available.',
 'A014':'The same identity-listing command outside the sandbox found the Developer ID Application identity; no prompt was observed.',
 'A015':'Located the signing-row schema and partial-build descriptions. The prose baseline contained no corresponding helper-count entry requiring an update.',
 'A016':'Restored exactly the two distribution documents from the working tree and saved seventeen pre-edit files; no distribution binary was copied.',
 'A017':'Added the six-line helper, conventional Meson target, minimum check, copy and signature, native expectation, inventory/evidence entries, build-manifest row, and current-behavior prose.',
 'A018':'The build generator wrote the document and figures. Worker identity regeneration changed exactly its three copies.',
 'A020':'Inspection failed with signature errors on the app, service, and executable paths inside the sandbox.',
 'A021':'Inspection passed against the unchanged app outside the sandbox; its saved JSON has ok true and no errors.',
 'A022':'The run failed four of six source-drift cases: source manifests, limits documentation, build documentation, and generator contracts. Contract and architecture cases passed. Full receipts remain in the first run directory.',
 'A023':'Found the missing staged helper source, missing scratch-policy links, obsolete mutation expectations, report prose scan, and Swift setup assertion failures. Before A024 I asked permission to copy only the missing policy file without opening or displaying it; no answer had arrived by report assembly.',
 'A024':'Confirmed the inventory substitutions and seal index depended on the old helper layout. The copied report was explicitly named by the prose-baseline failure.',
 'A025':'Meson setup.stdout named the missing pw_stamp.c in the nested fixture. Swift setup stdout was not retained by the other test.',
 'A026':'Repaired fixture staging and three mutation expressions; preserved the accidentally copied report under .audit. The built helper printed the requested words plus newline, returned zero, and emitted no stderr.',
 'A027':'Listed three candidates and selected the coverage query. The first inventory found sixteen controls covering thirty-seven distinct refusal rows.',
 'A028':'The row sets were disjoint, so the complete minimum roster alone would return all controls; the attempt expanded to the optimal coverage frontier at each control-count budget.',
 'A029':'The existing script_problems entry point included every grounding comparison and the baseline check.',
 'A030':'Created a standalone sixty-three-line query without changing production build machinery.',
 'A031':'Both full and partial variants completed. Independent disjoint-set upper bounds matched every budget point.',
 'A032':'A timestamp-flag disagreement was refused with exit one before any JSON answer; the exact manifest bytes were restored.',
 'A033':'All thirteen build-document tests passed outside the sandbox, including both Swift-option controls.',
 'A034':'Task 1 diff: nineteen files, 109 insertions and 47 deletions. Task 2 diff: one file, 63 insertions. Saved original source bytes still matched.',
 'A035':'Inspection remained green. Timestamp review exposed the inaccurate informal setup estimate, corrected in A036.',
 'A036':'Corrected the setup estimate and identified escalation waits in the long timing gaps; preserved the A011 logging lapse.',
 'A037':'Prepared the findings and complete challenge write-up without claiming a successful final suite run.',
 'A038':'All thirty-three planner and host-source controls passed, including the repaired configured-source fixture.',
 'A039':'Recorder-only adjustment kept later action entries before the findings sections.'
}
for key,note in notes.items():
 pattern=r'(?ms)(^### '+key+r' — .*?)(?=^### A\\d{3} — |\\Z)'
 pattern=pattern.replace('\\\\','\\')
 match=re.search(pattern,s)
 if not match: raise ValueError('missing action '+key)
 s=s[:match.end()]+f'- Recorded outcome: {note}\n\n'+s[match.end():]
status='''## Current result

Task 1 is **not yet fully green**. The signed make build passed (A019), artifact inspection passed against unchanged bytes outside the sandbox (A021), and the helper's exact output was verified (A026). The first source-drift run failed (A022). Its implementation-related failures have been repaired and checked separately: thirteen build-document tests pass (A033) and thirty-three planner/host-source controls pass (A038).

The final whole-suite run awaits clarification about restoring the excluded .tmp/AGENTS.md. The audit prompt prohibits reading anything under .tmp, while its prescribed copy removes this file and the suite requires the linked path. I asked to copy only that tracked policy file without opening or displaying it. No permission was inferred from elapsed time, and the file has not been copied or opened. This report does not claim all three requested checks are green.

Task 2 succeeded: a sixty-three-line grounded query computes an exact declared-control coverage frontier for full and partial builds, with independent optimum checks and a negative grounding control. No default battery, notarization, release, publication, or commit was performed. The original source files sampled in the pre-edit baseline remain byte-identical. Only this report was written outside the authorized disposable experiment tree.

'''
s=s.replace('## Part 1: ordered action log\n',status+'## Part 1: ordered action log\n',1)
findings=Path('.audit/report-findings.md').read_text()
findings=findings.replace('**20 calibration observations**','**21 calibration observations**')
findings=findings.replace('| 20 | A034–A035 | Saved inspection stayed green and original source files matched pre-edit bytes. |','| 20 | A034–A035 | Saved inspection stayed green and original source files matched pre-edit bytes. |\n| 21 | A038 | The repaired planner fixture passed all thirty-three planner and host-source controls. |')
s+='\n'+findings
report.write_text(s)
print('Assembled report with chronological outcomes, ten surprises, twenty-one calibrations, and the completed challenge result.')
print('Final suite status is explicitly pending the policy-file clarification.')
PY
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A040.txt`.

### A041 — Verify the delivered report structure and uncommitted status

- Start: 2026-10-10T16:12:40+00:00
- Since previous action ended: 27.2 seconds (reading, planning, or conversation unless noted).
- Before: I expect forty-one sequential log entries including this verification, exactly one findings section, all candidate/result sections, and an explicit pending source-drift status. I also expect the report to be uncommitted and the excluded policy file still absent.
- Action (in the disposable copy):

```sh
python3 - <<'PY'
from pathlib import Path
import re
p=Path('../../../docs/BUILD-DOC-AUDIT-NARRATIVE-REPORT.md'); text=p.read_text()
heads=list(re.finditer(r'^### (A\\d{3}) — ',text,re.M))
ids=[m.group(1) for m in heads]
assert ids==[f'A{i:03d}' for i in range(1,42)],ids
assert text.count('\n## Part 1: surprises\n')==1
assert text.count('\n## Part 2: candidates\n')==1
assert text.count('\n## Part 2: attempt and result\n')==1
assert text.index('\n## Part 1: surprises\n')>heads[-1].start()
for i,m in enumerate(heads):
 end=heads[i+1].start() if i+1<len(heads) else text.index('\n## Part 1: surprises\n')
 block=text[m.start():end]
 if m.group(1) not in ('A001','A011'):
  assert '- Before:' in block,m.group(1)
 if m.group(1) not in ('A001','A003','A004','A011','A019','A040','A041'):
  assert '- Recorded outcome:' in block,m.group(1)
assert 'Task 1 is **not yet fully green**' in text
assert '**21 calibration observations**' in text
assert not Path('.tmp/AGENTS.md').exists()
print('Report structure checked:',len(ids),'ordered actions; ten surprise rows; twenty-one calibration rows; challenge candidates and result present.')
print('Report:',p.resolve())
print('Words:',len(text.split()),'lines:',len(text.splitlines()))
PY
GIT_OPTIONAL_LOCKS=0 git -C /Users/raccoon/Desktop/Security/PolicyWitness status --short -- docs/BUILD-DOC-AUDIT-NARRATIVE-REPORT.md
```

- Result: exit 0; command elapsed 0.06 seconds; complete output in `.tmp/audit-narrative/src/.audit/A041.txt`.

### A042 — Correct and rerun the report-structure verification

- Start: 2026-10-10T16:13:11+00:00
- Since previous action ended: 30.8 seconds (reading, planning, or conversation unless noted).
- Before: A041's Python assertion used an over-escaped digit pattern and failed before checking the report; the subsequent git status still returned zero and showed the report untracked. I expect a plain line-based check, with the shell stopping on failure, to verify the actual sections and forty-two action entries. I will record this reporting dead end explicitly.
- Action (in the disposable copy):

```sh
set -e
python3 - <<'PY'
from pathlib import Path
p=Path('../../../docs/BUILD-DOC-AUDIT-NARRATIVE-REPORT.md'); text=p.read_text()
text=text.replace('These are expectation gaps, not recommendations or explanations of the system. S01, S06, S10, and S11 are audit-process events.','These are expectation gaps, not recommendations or explanations of the system. S01, S06, S10, and S11 are audit-process events.')
needle='| S10 | After A036 | The report-drafting tool call would write the findings text. | A JavaScript delimiter error rejected the call before any shell command or file write. | −1 |
| S11 | A041 | The report-structure assertion would find the numbered log entries. | An over-escaped digit pattern found none; the later git-status command still made the shell return zero. | −1 |'
text=text.replace(needle,needle+'\n| S11 | A041 | The report-structure assertion would find the numbered log entries. | An over-escaped digit pattern found none; the later git-status command still made the shell return zero. | −1 |')
p.write_text(text)
lines=text.splitlines()
starts=[i for i,line in enumerate(lines) if line.startswith('### A') and ' — ' in line]
ids=[lines[i].split()[1] for i in starts]
assert ids==[f'A{i:03d}' for i in range(1,43)],ids
assert lines.count('## Part 1: surprises')==1
assert lines.count('## Part 2: candidates')==1
assert lines.count('## Part 2: attempt and result')==1
boundary=lines.index('## Part 1: surprises')
assert boundary>starts[-1]
for n,start in enumerate(starts):
 end=starts[n+1] if n+1<len(starts) else boundary
 block='\n'.join(lines[start:end]); key=ids[n]
 if key not in ('A001','A011'):
  assert '- Before:' in block,key
 if key not in ('A001','A003','A004','A011','A019','A040','A041','A042'):
  assert '- Recorded outcome:' in block,key
assert 'Task 1 is **not yet fully green**' in text
assert '**21 calibration observations**' in text
assert not Path('.tmp/AGENTS.md').exists()
print('Verified:',len(ids),'ordered action entries, eleven surprise rows, twenty-one calibration rows, and challenge candidate/result sections.')
print('Report remains explicitly incomplete for the final source-drift run; uncommitted status was confirmed in A041.')
print('Words:',len(text.split()),'lines:',len(lines))
PY
```

- Result: exit 0; command elapsed 0.04 seconds; complete output in `.tmp/audit-narrative/src/.audit/A042.txt`.


## Part 1: surprises

These are expectation gaps, not recommendations or explanations of the system. S01, S06, S10, and S11 are audit-process events.

| Id | Log entries | What I believed before the action | What I observed | Valence |
| --- | --- | --- | --- | ---: |
| S01 | A004–A010 | The combined newcomer-document read would give me the contents in one usable tool response. | The response was truncated, and smaller reads were necessary. | −1 |
| S02 | A002, A012, A016, A022–A025 | The prescribed copy would preserve the source and documents needed for the checks while omitting output trees. | It omitted the tracked distribution documents and linked scratch policy; the former needed restoration and the latter triggered link failures and a clarification request. | −1 |
| S03 | A019 | A fresh Rust, C, Swift, signed and packaged build would take roughly two minutes. | The complete build passed in 24.72 seconds. | +1 |
| S04 | A022–A025 | The registered helper and native expectation would suffice for the source-manifest controls. | A nested planner fixture omitted the new C file and Meson refused its setup. | −1 |
| S05 | A022–A024 | The inventory and signing mutation controls would still exercise their intended changes after adding a helper. | Two inventory substitutions depended on the old last element, and the seal assertion expected entry seven instead of eight. | −1 |
| S06 | A022–A024 | The unlinked, incomplete report copied during setup would remain separate from production-document checks. | The prose baseline scanner included it and rejected a measured-duration sentence. | −1 |
| S07 | A010, A022, A024, A033 | The guide's description of the source-drift manifest reader suggested the suite would avoid Swift discovery in the sandbox. | The Swift-option controls performed setup, failed there in the sandbox, and passed in the later unsandboxed run. | −1 |
| S08 | A022 | The source-drift run would take roughly one minute. | The failed run took 91.14 seconds. | −1 |
| S09 | A023–A025 | Retained failure logs would name the concrete setup problem. | The planner receipt named the absent file, but the Swift controls reported blank captured stderr without retaining setup stdout. | −1 |
| S10 | After A036 | The report-drafting tool call would write the findings text. | A JavaScript delimiter error rejected the call before any shell command or file write. | −1 |
| S11 | A041 | The report-structure assertion would find the numbered log entries. | An over-escaped digit pattern found none; the later git-status command still made the shell return zero. | −1 |

## Part 1: non-surprise count

**21 calibration observations** matched predictions. This counts the observations below, not every tool invocation; an action can have expected functionality and a surprising duration. A001 has only its original broad chat expectation. A011 had no pre-action prediction and is excluded. No retrospectively invented expectation is counted.

| # | Entries | Expected and observed |
| ---: | --- | --- |
| 1 | A005 | README enumerated the shipped executables and build/signing links. |
| 2 | A006 | BUILD described inputs, directory knobs, and phase order. |
| 3 | A007 | BUILD identified ownership of compilation, signing, inventories, and generated data. |
| 4 | A009 | The generator account distinguished textual agreement from runtime refusal. |
| 5 | A010 | SIGNING supplied concrete build commands and the sandbox retry procedure. |
| 6 | A012 | Existing helpers supplied copy, minimum-version, signing, and evidence patterns without a new phase. |
| 7 | A013 | The source checker had an explicit target expectation that needed the helper. |
| 8 | A013–A014 | The sandbox hid the identity; the unsandboxed listing found it, as documented. |
| 9 | A015 | The manifest exposed the signing row and partial-build description; no relevant prose-baseline entry needed growth. |
| 10 | A017 | The direct source and inventory edits applied without an implementation error. |
| 11 | A018 | Generation accepted the additions and updated exactly three identity copies. |
| 12 | A019 | The build checked six native targets and signed eight bundled executables in the documented order. |
| 13 | A020 | Inspection produced the documented sandbox signature-verification failure. |
| 14 | A021 | The same inspection passed outside the sandbox against unchanged app bytes. |
| 15 | A023 | The direct production build-document check was green while mutation-control logs held failures. |
| 16 | A024 | The predicted obsolete inventory literals and numeric seal index were present. |
| 17 | A025 | The receipt named the absent stamp source, and fixture staging omitted it. |
| 18 | A026 | The edits applied and the signed helper printed exactly the requested words plus newline, exited zero, and wrote no stderr. |
| 19 | A033 | All thirteen build-document controls passed outside the sandbox. |
| 20 | A034–A035 | Saved inspection stayed green and original source files matched pre-edit bytes. |
| 21 | A038 | The repaired planner fixture passed all thirty-three planner and host-source controls. |

## Part 2: candidates

1. **Minimum refusal-control portfolio.** Turn declared coverage into an exact set-cover query, finding the smallest existing control roster spanning covered refusals while retaining textual-only gaps. No document read proposes this query. It takes a small Python command using the grounded manifest reader and subset enumeration.
2. **Signed native lineage card.** Join one native receipt, the signed evidence manifest, and structural comparison to trace a helper from configured target and compile command to observed signed bytes. The documents describe the ingredients separately. It takes a short adapter over the existing native tools with explicit limits on what the join establishes.
3. **Failure disambiguator from a real build log.** Combine the last banner and exit status with the manifest to enumerate candidate refusal sites and expose where message evidence is still necessary. No document read supplies a run-specific query. It takes a banner matcher and manifest filter, checked against a retained failed run.

## Part 2: attempt and result

Selected the minimum-control idea and added tests/lib/build_control_frontier.py in the copy. The first inventory found that all sixteen control references own disjoint refusal sets, so minimizing the complete roster alone returns every control. The implemented query also calculates optimal coverage at every control-count budget. It validates citations and script/manifest/inventory/baseline agreement through the existing generator before searching, enumerates all subsets, maximizes covered rows, prefers behavioral coverage on ties, and reports textual-only gaps.

**It worked.** Both variants enumerated 65,536 subsets. Independent set-based verification established disjoint row sets and showed that every reported budget attained the sum-of-largest-sets upper bound. A controlled timestamp-flag mismatch in the manifest was refused with exit one and no frontier output; the original manifest bytes were restored exactly.

| Variant | Refusals | Rows with declared controls | Uncovered | One-control maximum | Two-control maximum | Minimum controls for all covered rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Full | 65 | 37 | 28 | 20 | 23 | 16 |
| Partial | 57 | 35 | 22 | 18 | 21 | 16 |

The full-build optimum at budget one is the Meson option-assertion helper control. Budget two adds the build-directory refusal control, cited by three behavioral rows. The complete full-build roster contains fourteen behaviorally cited rows and twenty-three helper-cited rows.

This enables inspection of declared coverage tradeoffs while keeping helper checks distinct from controls that drive the build, and keeping uncovered refusals visible. The unit is one cited control, not one command, one subtest, or measured runtime. The query neither runs controls nor proves that their assertions establish the cited rows. Exact search is bounded to twenty-two cited controls; larger input is refused.

Diff stat relative to the copied working tree:

    tests/lib/build_control_frontier.py | 63 +++++++++++++++++++++++++++++++++
    1 file changed, 63 insertions(+)

The implementation is **63 physical lines**, with no dependency or existing build-code changes. The one-off validation commands remain in the action log and were not added as test files.

Artifacts in the disposable copy: .audit/task1.patch, .audit/task1-stat.json, .audit/task2.patch, .audit/challenge-full.json, .audit/challenge-partial.json, and negative-control stdout/stderr. Task 1's source changes total nineteen files, 109 insertions and 47 deletions relative to the saved working-tree baseline, including generated files. Counts exclude pre-existing changes and restored setup documents.

Task 2 candidate selection through the negative control (A027–A032) took **159.43 seconds (2.66 minutes)** including reading and reasoning. Both variants plus independent verification took **0.45 seconds**; the negative-control command took **0.18 seconds**.
