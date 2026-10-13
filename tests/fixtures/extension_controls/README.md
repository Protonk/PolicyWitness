# Extension boundary controls

`control.c` includes the production native issuer or worker and substitutes
selected native entrypoints at compile time. Worker modes interrupt after its
pre-call marker, inside a substituted operation before return, or after the real
native call returned but before result publication. The middle control establishes
position inside the controlled replacement, not inside the kernel extension API.
Other modes supply native refusal, issuer death/deadline, unavailable symbols,
invalid token contents and malformed transient-channel publications.

A unique test-owned POSIX shared-memory object receives independent intervention
receipts and a copy of the real issued token. The checking process compares
captured output with those bytes in memory, then erases and unlinks the object
after child cleanup is established. No raw token is printed or written to a
retained fixture. The observer channel and its pre-application mapping belong
only to these test binaries; they are not evidence of production descriptor
inheritance. Separate receipts check closure of the production channel descriptor
and disabled core dumps at the observed native boundaries.

Each channel has a case-local ownership receipt and a duplicate recovery record
in a uniquely created temporary directory, outside prunable run output. The
record is retained when native child cleanup is unknown. Recovery must use that
exact channel name and independently establish child cleanup before erasing and
unlinking it; a name prefix alone is not ownership. Successful cleanup removes
the duplicate while preserving the case receipt.

The fixture is built outside the inspected app. Its worker retains the current
production ABI/source identity for transport, but the executable override and
independent binary provenance identify the instrumentation. These substitutions
establish boundary handling and publication, not policy effects of fabricated
native return values. The ordinary signed experiment establishes native success.
