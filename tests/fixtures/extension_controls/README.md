# Extension boundary controls

`control.c` includes the production native issuer or worker and substitutes
selected native entrypoints at compile time. Worker modes interrupt after its
pre-call marker, inside a substituted operation before return, or after the real
native call returned but before result publication. The middle control establishes
position inside the controlled replacement, not inside the kernel extension API.
Other modes supply native refusal, issuer death/deadline, unavailable symbols,
invalid token contents and malformed transient-channel publications. A post-publication
issuer exit retains an independent publication receipt. A worker-side `memchr`
substitution scans a prefix of the mapped token and kills the worker before
framing validation and delivery publication finish; the receipt records the
checked prefix, descriptor closure and disabled core dumps.

Worker modes 107 to 117 substitute exactly one native call of the worker's
channel preparation: a refused core limit, a failed or undersized descriptor
inspection, a failed mapping, a failed inspected close, a failed cleanup close
after the inspection failure, and header or token fields mutated in the mapped
view. Every other call is real, so the production preparation path decides the
published status, stage, native result, errno and cleanup fields; the controls
check that account and that no consumption follows.
Mode 118 combines unavailable consume API support with a failed cleanup close;
both observations must survive without a reporting failure.

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
target is an owned regular file in that same directory. Executable fixtures also
run there, with retained copies in the artifacts, avoiding Desktop access by
the issuer or worker.
The record is retained when native child cleanup is unknown. Recovery must use that
exact channel name and independently establish child cleanup before erasing and
unlinking it; a name prefix alone is not ownership. Successful cleanup removes
the duplicate while preserving the case receipt.

The fixture is a clang `-O2` build with `PW_EXTENSION_OBSERVE`, outside the
inspected app; it does not establish interruption of the shipped executable
bytes. Its worker retains the current
production ABI/source identity for transport, but the executable override and
independent binary provenance identify the instrumentation. These substitutions
establish boundary handling and publication, not policy effects of fabricated
native return values. The ordinary signed experiment establishes native success.
