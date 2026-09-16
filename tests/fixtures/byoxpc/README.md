# Disposable BYOXPC ownership

`session.py` prepares a complete copy of the selected app's `PWRunner.xpc` under
`/private/tmp`, with a unique service identifier and unchanged caller-auth keys.
It inspects the registry before installation, verifies the source signature,
records its metadata/entitlements, and checks the copy before changing its plist.
Source aliases and paths escaping the bundle are rejected before signing.

Only the public `runner install --identity` command signs the copy. Nonempty or
explicit empty entitlement dictionaries are passed from actual signature
extraction; absent entitlement data stays absent. Extraction warnings and malformed
data fail setup. After installation the copy must verify, retain its team,
entitlements and runtime flag, and have unchanged embedded helpers. Connection
verification must succeed before the wrapper receives its runner environment.

The wrapper installs its EXIT trap before setup. `session.json` records the unique
service, staging directory, expected plist, and source app before installation.
Cleanup can therefore find an owned registration even if install output was
malformed or setup failed afterward. It uses public removal when registered;
for a partial install with no registry entry, the exact plist must establish
ownership before the documented bootout/plist-removal procedure is used.

Deletion of staging requires confirmed absence from launchd, the registry, and
the expected plist path. Warnings, ambiguous ownership, incomplete installer
execution, and removal failures retain staging and fail the wrapper, with its
service/path in the diagnostic. Cleanup does not retry signing, change identity,
or delete unrelated registrations. Source inventory is checked again on exit.
Direct invocation of `runner_install.sh` owns cleanup itself; suite invocation
keeps the copy alive across its selected specimens.

`tools.py` is an independent fake-command executable used by
`shell_helpers/byoxpc_setup`. It records requests and simulates signing,
registry/plist/launchd state, and failures. No real keychain, signing, launchctl,
or product execution occurs in those controls. Production fixture entrypoints
have no environment switch for these fake tools.
