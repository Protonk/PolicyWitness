// Public header for the PWSandboxCheckShim SwiftPM target.
//
// Swift call sites in PWRunnerCore link to these symbols via
// @_silgen_name and do not import this module. The declarations here
// exist to satisfy SwiftPM's publicHeadersPath bookkeeping and to
// document the C ABI of the shim.

#ifndef PW_SANDBOX_CHECK_SHIM_H
#define PW_SANDBOX_CHECK_SHIM_H

#include <sys/types.h>

int pw_sandbox_check(pid_t pid, const char *operation, int type,
                     const char *arg, int *out_errno);

int pw_sandbox_check_noarg(pid_t pid, const char *operation, int *out_errno);

#endif /* PW_SANDBOX_CHECK_SHIM_H */
