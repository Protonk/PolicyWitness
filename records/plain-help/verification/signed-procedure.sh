#!/bin/bash
# The common linkage procedure against signed builds, in a scratch worktree.
# usage: signed-rename.sh WORKTREE OUT_DIR
set -u
W="$1"; OUT="$2"; mkdir -p "$OUT"; cd "$W" || exit 2
export PATH="/opt/homebrew/opt/rustup/bin:$PATH"
ID=$(security find-identity -v -p codesigning | sed -n 's/.*"\(Developer ID Application: [^"]*\)".*/\1/p' | head -1)
BIN=dist/PolicyWitness.app/Contents/MacOS/policy-witness
note() { echo "$*" | tee -a "$OUT/summary.txt"; }
build() { make build IDENTITY="$ID" > "$OUT/$1.build.log" 2>&1; local rc=$?; note "$1: make build exit $rc"; grep -h "is stale\|Cargo judgments" "$OUT/$1.build.log" | sed 's/^ *//' | tee -a "$OUT/summary.txt"; return $rc; }
observe() {
  note "$1: binary sha256 $(shasum -a 256 $BIN | cut -c1-16) describe $($BIN --version | python3 -c 'import json,sys; b=json.load(sys.stdin)["build"]; print(b["describe"], b["number"])')"
  $BIN help run > "$OUT/$1.help-run.txt"; note "$1: help run card: $(tr '\n' '|' < "$OUT/$1.help-run.txt")"
  for mode in --runner-mode --runner-kind; do
    note "$1: run $mode standard -> $($BIN run $mode standard | python3 -c 'import json,sys; r=json.load(sys.stdin)["result"]; print(r["normalized_outcome"], r["exit_code"], r["error"])')"
  done
}
suite() { PW_TEST_OUT_DIR="tests/out/runs/signed-$1" tests/run.sh "${@:2}" > "$OUT/$1.dispatch.log" 2>&1; note "$1: tests/run.sh ${*:2} exit $?"; grep -h "pass:\|FAIL" "$OUT/$1.dispatch.log" | cut -c1-200 | tee -a "$OUT/summary.txt"; }
integration_failures() { L=$(find "tests/out/runs/signed-$1" -name cargo-test-integration.log | head -1); grep -h "step [0-9]\|\.\.\. FAILED\|^test result" "$L" | cut -c1-240 | tee -a "$OUT/summary.txt"; }
rename() { python3 - <<'PY'
p='controller/src/interface/run_args.rs'; s=open(p).read(); old='("--runner-mode", Value::Kind(Reader::RunOption))'
assert s.count(old)==1; open(p,'w').write(s.replace(old,'("--runner-kind", Value::Kind(Reader::RunOption))'))
PY
}
copy() { python3 - <<'PY'
p='controller/interface/cards.rs'; s=open(p).read(); old='            out.line(depth, option.def().spelling);'
assert s.count(old)==1
open(p,'w').write(s.replace(old,'''            out.line(
                depth,
                match option {
                    RunOption::TimeoutMs => "--timeout-ms",
                    RunOption::RunnerMode => "--runner-mode",
                },
            );'''))
PY
}
[ -z "$(git status --porcelain)" ] || { echo "worktree not clean"; exit 2; }
note "worktree HEAD $(git rev-parse --short HEAD)"

note "== 1. connected baseline"
build 1-baseline && observe 1-baseline
suite 1-baseline --suite integration

note "== 2. governing-source mutation: rename --runner-mode to --runner-kind"
rename; git diff --stat | tee -a "$OUT/summary.txt"
build 2-mutated-stale; note "2: dist binary after refused build: sha256 $(shasum -a 256 $BIN | cut -c1-16)"
tests/lib/python.sh docs/generate_interface.py --refresh-inventory 2>&1 | tee -a "$OUT/summary.txt"
build 2-mutated-regenerated && observe 2-mutated-regenerated
suite 2-mutated --suite integration; integration_failures 2-mutated
git checkout -- .

note "== 3. private identical copy in the card renderer"
copy
build 3-copy && observe 3-copy
suite 3-copy --suite integration
suite 3-copy-drift --case source_drift/runner_source_manifests_agree
L=$(find tests/out/runs/signed-3-copy-drift -name check.log | head -1); grep -h "interface_literals\|renderer" "$L" | cut -c1-260 | tee -a "$OUT/summary.txt"

note "== 4. the copy, then the rename"
rename
build 4-copy-mutated; note "4: dist binary after refused build: sha256 $(shasum -a 256 $BIN | cut -c1-16)"
tests/lib/python.sh docs/generate_interface.py --refresh-inventory 2>&1 | tee -a "$OUT/summary.txt"
build 4-copy-mutated-after-generator; note "4: dist binary: sha256 $(shasum -a 256 $BIN | cut -c1-16)"
git checkout -- .
note "restored: $(git status --porcelain | wc -l | tr -d ' ') changed files"
