# Validator I/O deadline

Baseline case `validator_io_deadline_releases_worker` uses a checked-in transcript
that returns one of two predictions and keeps stdout open. The public CLI sends
`validator_io_timeout_ms: 500` to the real monotonic I/O boundary. The test checks
`validator_no_reply`, the deadline diagnostic, exact override echo, retained partial
records, validator cleanup and normal worker completion. Both file writes are
observed independently before decoding the envelope. The received prediction is
`query_first`; the missing prediction stays `unestablished` with its missing reason.

The retained timing measures the whole CLI run with a shortened deadline. It is
not a worst-case bound on host setup, scheduling, final reap or worker lifetime.
