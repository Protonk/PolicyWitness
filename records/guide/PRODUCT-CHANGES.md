# Product changes in the guide overhaul

Each entry is a change made for the guide overhaul since `3b7cf293`, to what PolicyWitness does or promises or to what a test requires of it. The reasoning and evidence stay beside the finding that prompted the change. This ledger lists the changes together so that the release account and the guide can cover each one. An investigation that keeps today's behavior also gets an entry, saying why.

## Keeping the ledger current

- Land each product change in its own commit, together with its decision beside the finding and its entry here.
- At each milestone, list the public statements that changed since the overhaul began and check that each one has an entry. Run this from the repository root:

  ```sh
  tests/lib/python.sh - 3b7cf293 <<'EOF'
  import json, subprocess, sys
  def statements(text):
      found = {}
      def walk(node):
          if isinstance(node, dict):
              if isinstance(node.get('id'), str) and 'kind' in node:
                  found.setdefault(node['id'], json.dumps(node, sort_keys=True))
              for value in node.values():
                  walk(value)
          elif isinstance(node, list):
              for value in node:
                  walk(value)
      walk(json.loads(text)['surfaces'])
      return found
  base = subprocess.run(['git', 'show', sys.argv[1] + ':docs/contract/public.json'],
                        capture_output=True, text=True, check=True).stdout
  old, new = statements(base), statements(open('docs/contract/public.json').read())
  for key in sorted(set(old) | set(new)):
      if old.get(key) != new.get(key):
          print('added' if key not in old else 'removed' if key not in new else 'changed', key)
  EOF
  ```

- For the compatibility notes, `git diff --stat 3b7cf293 -- tests/fixtures/contract/envelope_shape.json tests/fixtures/contract/response_shape.json controller/interface/inventory.json` shows changes to the envelope and reply shapes and to command-line spellings.
- A change to a test's assertions alone appears in neither diff. Add its entry when the assertion changes.
- These entries are the guide overhaul's part of the release account planned in the trace closeout. Release notes drawn from them still check each claim against code and commits.

## Changes

### 1. Repeated field names leave acceptance and the value unspecified

- **Kind.** Narrowed promise.
- **What changed.** Statement `request.specimen.duplicate_keys`. The admission tests no longer submit the 24 paired requests that repeat a field name or their 24 single-value neighbours. A CLI submission with a scalar `runner` was added.
- **Prompted by.** Responsibility finding 1. [Decision and surviving checks](USER-RESPONSIBILITIES-AND-TESTS.md#changes-made-with-the-draft)
- **Guide.** "Describe the run you intend" in the draft's [Responsibilities](../../docs/guide/PolicyWitness.md#responsibilities).
- **Compatibility.** PW no longer promises that the CLI keeps the last value of a repeated name or that a direct host request keeps the first. Request and reply shapes are unchanged.
- **Verification.** Signed build 1661, runs `20261122T173245Z_dac40c01` (`guide-responsibilities-live-20261122`) and `20261122T174522Z_176d7a01` (`guide-responsibilities-final-20261122`). Both are gitignored under `tests/out/runs/` and available only in this checkout.
- **Commit.** `cf7d9bba`.

### 2. An incomplete import scan may report any file error

- **Kind.** Narrowed promise.
- **What changed.** Statement `dossier.imports.failure`. When several imported files have errors, `failure` may name any of them. Previously it named the first problem in the scanner's depth-first traversal. Each file still keeps its own error in `records`. A form the scan could not follow in the submitted source is still reported in `failure`.
- **Prompted by.** Responsibility findings 9 and 20. [Decision and surviving checks](USER-RESPONSIBILITIES-AND-TESTS.md#changes-made-with-the-draft)
- **Guide.** The "Reproducing a run" row of [User responsibilities](../../docs/REQUIREMENTS.md).
- **Compatibility.** A reader that took the first failing import from `failure` has to read the file records instead. Shapes are unchanged.
- **Verification.** As for entry 1.
- **Commit.** `cf7d9bba`.

### 3. Create and extension tests accept whichever answer the validator gives

- **Kind.** Test assertions only.
- **What changed.** The existing-file create cases (`witness_contract/check_create_existing.py`, `run_effects/check_file_actions.py`) and extension qualification (`witness_contract/check_extension_policy_qualification.py`) record the validator's answer instead of requiring one. They still check the worker's results and independent filesystem observations.
- **Prompted by.** Responsibility findings 12 and 15. [Decision and surviving checks](USER-RESPONSIBILITIES-AND-TESTS.md#changes-made-with-the-draft)
- **Guide.** No passage needed, because the guide promises no particular validator answer. "Observe the effect you care about" in the draft's Responsibilities teaches the observation these tests still make.
- **Compatibility.** None. Product behavior is unchanged.
- **Verification.** As for entry 1.
- **Commit.** `d33ddd2a`.

### 4. The denied-helper test no longer requires the helper's wording

- **Kind.** Test assertions only.
- **What changed.** `run_effects/exec_helper_effect_is_real` no longer requires `--write` in the denied helper's stderr. It still observes the marker bytes or their absence before decoding the envelope, then checks the child's PID, exit and signal.
- **Prompted by.** Responsibility finding 14. [Decision and surviving checks](USER-RESPONSIBILITIES-AND-TESTS.md#changes-made-with-the-draft)
- **Guide.** The "Claiming an effect" row of [User responsibilities](../../docs/REQUIREMENTS.md).
- **Compatibility.** None.
- **Verification.** As for entry 1.
- **Commit.** `d33ddd2a`.

### 5. The envelope carries the digest of the request file

- **Kind.** New field.
- **What changed.** Statement `dossier.specimen.request_sha256` adds `data.specimen.request_sha256`, the SHA-256 of the request-file bytes the controller read before parsing. It is null when nothing was read.
- **Prompted by.** Outside-PW finding 2. [Decision and evidence](REQUIREMENTS-AND-EXPECTATIONS.md#what-must-a-user-arrange-outside-of-pw)
- **Guide.** The draft's [Handing a run to someone else](../../docs/guide/PolicyWitness.md#handing-a-run-to-someone-else), and the "Reproducing a run" row of [User responsibilities](../../docs/REQUIREMENTS.md).
- **Compatibility.** The run envelope gains one key under `data.specimen`, holding a string or null. Requests and the runner reply are unchanged. A reader that requires an exact key set for `data.specimen` has to accept the new key.
- **Verification.** Development build 1666. Default battery run `20261123T154043Z_70d02f53` (`specimen-digest-20261123`), gitignored and available only in this checkout. The study's runs and handoff are retained in `work/evidence/specimen-digest/`.
- **Commit.** `a971b658`.
