# Worker harness equipment

`build.sh <output binary>` compiles the existing
`tests/suites/runner_c_worker_harness/harness.c` adapter against the current
worker ABI header. The C-worker suite, exec-inheritance suite, and inheritance
mutation controls share this recipe. Each caller owns its output path and logs;
the C-worker suite compiles once per invocation. No app or worker is built here.

`control.sh` and `control.py` are independent stand-ins for the builder and
harness in the `shell_helpers/worker_setup` controls. They record actual argv,
emit explicit transcripts, and simulate equipment failures in disposable copies
of the real suite. They never apply a sandbox or invoke the production worker.
These shell controls require Python and Bash only; live suites exercise the
actual compiler recipe and worker.
