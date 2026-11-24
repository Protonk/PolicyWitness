# Runner and request workflow fixtures

## Quick start

```sh
APP="/Applications/PolicyWitness.app"
PW="$APP/Contents/MacOS/policy-witness"
umask 077
PW_WORK=$(mktemp -d /private/tmp/pw-guide.XXXXXX)
printf 'Work directory: %s\n' "$PW_WORK"
"$PW" --version > "$PW_WORK/version.json"
PW_CONTRACT=$(/usr/bin/plutil -extract build.contract raw -o - "$PW_WORK/version.json")
printf 'Contract: %s\n' "$PW_CONTRACT"
```

```sh
cat > "$PW_WORK/create.json" <<'JSON' &&
{
  "contract": "BUILD_CONTRACT",
  "specimen_id": "guide-create",
  "policy": {
    "format": "sbpl",
    "sbpl_source": "(version 1) (allow default)"
  },
  "probe_plan": [
    {
      "step_id": "create",
      "sandbox_check": {
        "operation": "file-write-create",
        "filter": { "kind": "path", "value": "TARGET" }
      },
      "attempt": { "kind": "file", "action": "create", "target": "TARGET" }
    }
  ]
}
JSON
/usr/bin/plutil -replace contract -string "$PW_CONTRACT" "$PW_WORK/create.json" &&
/usr/bin/plutil -replace probe_plan.0.sandbox_check.filter.value -string "$PW_WORK/created" "$PW_WORK/create.json" &&
/usr/bin/plutil -replace probe_plan.0.attempt.target -string "$PW_WORK/created" "$PW_WORK/create.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/created"; then
  "$PW" run "$PW_WORK/create.json" > "$PW_WORK/create-result.json" 2> "$PW_WORK/create-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/create-exit.txt"
  cat "$PW_WORK/create-result.json"
  test -f "$PW_WORK/created"
  /usr/bin/stat -f 'size=%z mode=%Sp inode=%i' "$PW_WORK/created" > "$PW_WORK/create-observation.txt"
  cat "$PW_WORK/create-observation.txt"
else
  printf '%s\n' 'Request preparation failed or target exists; discard failed input and prepare a fresh work directory.' >&2
fi
```

## Try an accepted request and a refusal

```sh
/usr/bin/plutil -replace specimen_id -string guide-capture \
  -o "$PW_WORK/capture-typo.json" "$PW_WORK/create.json" &&
/usr/bin/plutil -replace probe_plan.0.sandbox_check.filter.value -string "$PW_WORK/capture-target" "$PW_WORK/capture-typo.json" &&
/usr/bin/plutil -replace probe_plan.0.attempt.target -string "$PW_WORK/capture-target" "$PW_WORK/capture-typo.json" &&
/usr/bin/plutil -insert policy.capture_compiled_profiel -bool YES "$PW_WORK/capture-typo.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/capture-target"; then
  "$PW" run "$PW_WORK/capture-typo.json" > "$PW_WORK/capture-typo-result.json" 2> "$PW_WORK/capture-typo-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/capture-typo-exit.txt"
  test "$PW_EXIT" -eq 1
  test ! -e "$PW_WORK/capture-target"
else
  printf '%s\n' 'Request preparation failed or target exists; preserve earlier records and prepare a fresh target.' >&2
fi
```

```sh
/usr/bin/plutil -remove policy.capture_compiled_profiel \
  -o "$PW_WORK/capture-no-nonce.json" "$PW_WORK/capture-typo.json" &&
/usr/bin/plutil -insert policy.capture_compiled_profile -bool YES "$PW_WORK/capture-no-nonce.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/capture-target"; then
  "$PW" run "$PW_WORK/capture-no-nonce.json" > "$PW_WORK/capture-no-nonce-result.json" 2> "$PW_WORK/capture-no-nonce-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/capture-no-nonce-exit.txt"
  test "$PW_EXIT" -eq 1
  test ! -e "$PW_WORK/capture-target"
else
  printf '%s\n' 'Request repair failed or target exists; preserve earlier records before continuing.' >&2
fi
```

```sh
PW_NONCE=$(/usr/bin/openssl rand -hex 16)
printf '%s\n' "$PW_NONCE"
```

```sh
/usr/bin/plutil -insert policy.capture_nonce -string "$PW_NONCE" \
  -o "$PW_WORK/capture.json" "$PW_WORK/capture-no-nonce.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/capture-target"; then
  "$PW" run "$PW_WORK/capture.json" > "$PW_WORK/capture-result.json" 2> "$PW_WORK/capture-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/capture-exit.txt"
  cat "$PW_WORK/capture-result.json"
  test -f "$PW_WORK/capture-target"
else
  printf '%s\n' 'Request repair failed or capture target exists; preserve its records before continuing.' >&2
fi
```

## SBPL check (sbpl-check)

```sh
"$APP/Contents/MacOS/sbpl-check" --request "$PW_WORK/create.json" > "$PW_WORK/compile-result.json" 2> "$PW_WORK/compile-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/compile-exit.txt"
cat "$PW_WORK/compile-result.json"
```

## External runners (BYOXPC)

```sh
"$PW" runner list > "$PW_WORK/runners-before.json" 2> "$PW_WORK/runners-before-stderr.txt"
"$PW" runner reconcile > "$PW_WORK/reconcile-before.json" 2> "$PW_WORK/reconcile-before-stderr.txt"
```

## Install a BYOXPC runner

```sh
IDENTITY="Developer ID Application: Your Name (TEAMID)"
ENT="/absolute/path/to/your-entitlements.plist"
PW_RUNNER_STAGE=$(mktemp -d "$PW_WORK/runner.XXXXXX")
BYO="$PW_RUNNER_STAGE/PWRunner.guide.xpc"
SERVICE="com.policywitness.guide.$(id -u).$(basename "$PW_RUNNER_STAGE")"
cp -R "$APP/Contents/XPCServices/PWRunner.xpc" "$BYO"
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $SERVICE" "$BYO/Contents/Info.plist"
/usr/bin/codesign --force --options runtime --sign "$IDENTITY" "$BYO"
```

```sh
"$PW" runner install --bundle "$BYO" --identity "$IDENTITY" \
  --entitlements "$ENT" --scope user \
  > "$PW_WORK/install.json" 2> "$PW_WORK/install-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/install-exit.txt"
cat "$PW_WORK/install.json"
cat "$PW_WORK/install-stderr.txt"
"$PW" runner list > "$PW_WORK/runners-after-install.json"
"$PW" runner reconcile > "$PW_WORK/reconcile-after-install.json"
```

## Verify the runner

```sh
"$PW" runner status --service-name "$SERVICE" > "$PW_WORK/status.json" 2> "$PW_WORK/status-stderr.txt"
"$PW" runner verify --service-name "$SERVICE" --timeout-ms 20000 \
  > "$PW_WORK/verify.json" 2> "$PW_WORK/verify-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/verify-exit.txt"
cat "$PW_WORK/verify.json"
```

## Use the runner in a specimen

```sh
/usr/bin/plutil -replace specimen_id -string guide-byoxpc-create \
  -o "$PW_WORK/byoxpc-create.json" "$PW_WORK/create.json" &&
/usr/bin/plutil -insert runner -dictionary "$PW_WORK/byoxpc-create.json" &&
/usr/bin/plutil -insert runner.service -string "$SERVICE" "$PW_WORK/byoxpc-create.json" &&
/usr/bin/plutil -insert runner.mode -string byoxpc "$PW_WORK/byoxpc-create.json" &&
/usr/bin/plutil -replace probe_plan.0.sandbox_check.filter.value -string "$PW_WORK/byoxpc-created" "$PW_WORK/byoxpc-create.json" &&
/usr/bin/plutil -replace probe_plan.0.attempt.target -string "$PW_WORK/byoxpc-created" "$PW_WORK/byoxpc-create.json"
PW_PREPARE_EXIT=$?
if test "$PW_PREPARE_EXIT" -eq 0 && test ! -e "$PW_WORK/byoxpc-created"; then
  "$PW" run "$PW_WORK/byoxpc-create.json" --timeout-ms 20000 \
    > "$PW_WORK/byoxpc-create-result.json" 2> "$PW_WORK/byoxpc-create-stderr.txt"
  PW_EXIT=$?
  printf '%s\n' "$PW_EXIT" > "$PW_WORK/byoxpc-create-exit.txt"
  cat "$PW_WORK/byoxpc-create-result.json"
  test -f "$PW_WORK/byoxpc-created"
  /usr/bin/stat -f 'size=%z mode=%Sp inode=%i' "$PW_WORK/byoxpc-created" > "$PW_WORK/byoxpc-observation.txt"
  cat "$PW_WORK/byoxpc-observation.txt"
else
  printf '%s\n' 'Request preparation failed or target exists; preserve its records and prepare a new effect target.' >&2
fi
```

## List, validate, or remove runners

```sh
"$PW" runner validate > "$PW_WORK/validate.json" 2> "$PW_WORK/validate-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/validate-exit.txt"
"$PW" runner remove --service-name "$SERVICE" > "$PW_WORK/remove.json" 2> "$PW_WORK/remove-stderr.txt"
PW_EXIT=$?
printf '%s\n' "$PW_EXIT" > "$PW_WORK/remove-exit.txt"
"$PW" runner list > "$PW_WORK/runners-after-remove.json"
"$PW" runner reconcile > "$PW_WORK/reconcile-after-remove.json"
```
