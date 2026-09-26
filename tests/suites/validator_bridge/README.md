# Native validator bridge controls

`protocol_controls` builds the test-only Objective-C bridge (Foundation JSON,
direct C sandbox calls) and independent exec observer outside the app. A real
sandboxed helper supplies allowed and denied targets. A separate ctypes call
provides the native rc/errno oracle for PATH and NONE queries.

The controls require readiness before any stdout, query receipts before emission,
exact native records, an open collection pipe after every record has been sent,
and a live child while held. Closing collection discards a pending record and
rejects later queries/emission; disconnecting the gate also cannot emit it.
These are equipment controls, not evidence that the runner obeys its barrier.
