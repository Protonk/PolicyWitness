# Built-in caller-auth fixtures

`bundle.py` copies the selected app, installs a caller-supplied client, adjusts
the service's authorization plist, and seals the service and app. It does not
decide whether a connection should succeed. The smoke checker supplies those
expectations and independently reads the probe's file effect.
The selected app must complete a real request before fixture signing begins,
so fixture preparation cannot silently repair a broken production signature.

Every app and service receives a unique identifier before launch. The client
stays at `Contents/MacOS/pw-runner-client`; a second, unchanged signed client in
the same bundle checks that a restricted service remains reachable. Candidate
clients are signed once and copied byte-for-byte into both policy variants.
All executable staging, request files, and probe targets live under `/private/tmp`.
The artifacts directory receives copies of evidence, never live request inputs.

Signing follows the production hardened-runtime and timestamp options, retaining
the selected binaries' embedded entitlements. Ad-hoc signing intentionally omits
the trusted timestamp. Unchanged nested tools keep their signatures; the changed
service and outer app are signed in that order. `--deep` is used only to verify.
The checker inspects the resulting identities, teams, entitlements, runtime flag,
and timestamps, and verifies that outer signing did not change the client bytes.

Commands retain arguments, exits, elapsed time, and raw streams. Successful
requests must return matching specimen/step evidence and leave a changed,
nonempty file. Rejected requests must leave the seed bytes intact, including
after fixture process cleanup. A connection-interrupted/invalidated error alone
does not establish authorization: the same client's relaxed-policy call and the
restricted service's authorized call must both succeed.

Cleanup only targets executable paths beneath this fixture's unique staging
directory. It is separate from the observations used to judge authorization.
The selected source app's inventory is compared before and after the case.
These copies are test fixtures, not distributable artifacts; their embedded
production evidence manifest is not regenerated after the intentional changes.
