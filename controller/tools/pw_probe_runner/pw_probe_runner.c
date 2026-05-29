/*
 * pw_probe_runner.c — sandboxed C worker that owns the post-apply
 * syscall surface. Per RUNNER-RESHAPE-PLAN.md Step 5 (R5+R6+R7+R8).
 *
 * Current state: SKELETON. This file establishes the build pipeline,
 * the embed/sign treatment, and the public ABI (see
 * pw_probe_runner_abi.h). The real flow (read inputs from shm,
 * compile policy from stdin, write pre-apply ready byte, sandbox_apply,
 * run attempts, write done sentinel, spin on exit_requested) lands in
 * Step 5 Chunk 2.
 *
 * Today this binary accepts --version and otherwise prints usage to
 * stderr and exits 2. The host code does not invoke it yet.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pw_probe_runner_abi.h"

static void print_usage(FILE *to) {
    fprintf(to,
        "usage: pw-probe-runner --shm-fd <N> --ready-fd <N> --step-count <N>\n"
        "                       [--policy-fd <N>]\n"
        "\n"
        "  --shm-fd N        FD of the host's pw_shm_region mapping.\n"
        "                    Worker mmaps PW_SHM_REGION_BYTES from this FD.\n"
        "  --ready-fd N      FD the worker writes one byte to after\n"
        "                    parsing the request and just before\n"
        "                    sandbox_apply(). Pre-apply readiness only;\n"
        "                    post-apply readiness is the `applied`\n"
        "                    sentinel in shm.\n"
        "  --step-count N    Number of populated slots, 0..PW_SHM_MAX_STEPS.\n"
        "  --policy-fd N     Optional FD carrying the SBPL policy text.\n"
        "                    Defaults to stdin (FD 0).\n"
        "\n"
        "  --version         Print ABI version and exit.\n"
        "\n"
        "This is the C worker spawned by the runner host (PWRunnerService).\n"
        "It is not meant to be invoked directly outside the runner\n"
        "host or its dedicated harness (see\n"
        "tests/suites/runner_c_worker_harness/ when Chunk 4 lands).\n");
}

int main(int argc, char **argv) {
    if (argc >= 2 && strcmp(argv[1], "--version") == 0) {
        printf("pw-probe-runner abi=%u region_bytes=%zu max_steps=%u slot_bytes=%u\n",
               PW_PROBE_RUNNER_ABI_VERSION,
               (size_t)PW_SHM_REGION_BYTES,
               PW_SHM_MAX_STEPS,
               PW_SHM_SLOT_BYTES);
        return 0;
    }

    /* No real flow yet — Chunk 2 wires up shm/policy/apply/spin. */
    print_usage(stderr);
    fprintf(stderr,
            "\npw-probe-runner: skeleton build (Step 5 Chunk 1). "
            "Real flow not yet implemented; this binary exists to "
            "exercise the build/sign/embed pipeline.\n");
    return 2;
}
