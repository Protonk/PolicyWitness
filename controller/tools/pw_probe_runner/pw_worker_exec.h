#ifndef PW_WORKER_EXEC_H
#define PW_WORKER_EXEC_H

/* Private exec implementation for the worker's single translation unit.
 * The sole lifecycle entry is attempt_exec_spawn(slot, timing, phase, index).
 * Descriptor/spawn bookkeeping stays here; timing is borrowed and all resources
 * are acquired inside the attempt. Fixture interception macros precede the
 * worker include and therefore reach these actual production calls. */
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <spawn.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>
#include "pw_worker_timing.h"

/* ---- exec attempt machinery ------------------------------------ */

/*
 * Exec attempts need two pipes and posix_spawn handles to capture the
 * child's stdout/stderr. The worker creates them inside the attempt,
 * after sandbox_apply, and releases them before the slot completes, so
 * no exec step holds descriptors across compilation, application or
 * another step's attempt, and a plan needs no descriptor budget.
 *
 * The Darwin 23.6 measurement reached posix_spawn after successful setup
 * under the tested denying profile. The harness case
 * `exec_setup_post_apply_denied` and public case
 * `runner_use_c_worker/exec_attempt_without_baseline_fails_cleanly` require
 * that boundary for their inputs. They do not establish that every native
 * implementation or resource condition permits setup.
 *
 * A setup failure records its call and errno and claims no spawn. Neither
 * a permission-shaped return nor a resource-shaped return identifies a
 * sandbox cause. Source placement keeps this setup inside the experiment;
 * the descriptor-ceiling control tests reuse, not placement by itself.
 */
typedef struct {
    int stdout_rfd;                 /* parent's read end; -1 when closed */
    int stdout_wfd;                 /* child's stdout source; closed post-spawn */
    int stderr_rfd;
    int stderr_wfd;
    posix_spawn_file_actions_t actions;
    posix_spawnattr_t           attr;
    int actions_initialized;
    int attr_initialized;
} pw_exec_resources_t;

static void exec_resources_release(pw_exec_resources_t *r) {
    if (r->stdout_rfd >= 0) { close(r->stdout_rfd); r->stdout_rfd = -1; }
    if (r->stdout_wfd >= 0) { close(r->stdout_wfd); r->stdout_wfd = -1; }
    if (r->stderr_rfd >= 0) { close(r->stderr_rfd); r->stderr_rfd = -1; }
    if (r->stderr_wfd >= 0) { close(r->stderr_wfd); r->stderr_wfd = -1; }
    if (r->actions_initialized) {
        posix_spawn_file_actions_destroy(&r->actions);
        r->actions_initialized = 0;
    }
    if (r->attr_initialized) {
        posix_spawnattr_destroy(&r->attr);
        r->attr_initialized = 0;
    }
}

/* Record a failed setup call: rc -1 with the call's errno, the exec
 * sentinel shape with no child (file probes use rc 1 for their own
 * failures). */
static void exec_setup_failed(pw_shm_slot_t *slot, const char *what, int err) {
    slot->rc = -1;
    slot->errno_val = err;
    snprintf(slot->error, sizeof(slot->error), "%s: %s", what, strerror(err));
}

/* Create both pipes and the spawn handles for one attempt. On failure the
 * slot names the failing call, nothing stays open, and the caller must
 * not spawn. */
static int exec_resources_acquire(pw_exec_resources_t *r, pw_shm_slot_t *slot) {
    r->stdout_rfd = r->stdout_wfd = r->stderr_rfd = r->stderr_wfd = -1;
    r->actions_initialized = r->attr_initialized = 0;

    int out_pipe[2] = {-1, -1};
    int err_pipe[2] = {-1, -1};
    if (pipe(out_pipe) != 0) {
        exec_setup_failed(slot, "pipe(stdout)", errno);
        return -1;
    }
    r->stdout_rfd = out_pipe[0];
    r->stdout_wfd = out_pipe[1];
    if (pipe(err_pipe) != 0) {
        exec_setup_failed(slot, "pipe(stderr)", errno);
        exec_resources_release(r);
        return -1;
    }
    r->stderr_rfd = err_pipe[0];
    r->stderr_wfd = err_pipe[1];

    /* The posix_spawn* setup calls return errno-style values. */
    int rc = posix_spawn_file_actions_init(&r->actions);
    if (rc != 0) {
        exec_setup_failed(slot, "posix_spawn_file_actions_init", rc);
        exec_resources_release(r);
        return -1;
    }
    r->actions_initialized = 1;

    rc = posix_spawnattr_init(&r->attr);
    if (rc != 0) {
        exec_setup_failed(slot, "posix_spawnattr_init", rc);
        exec_resources_release(r);
        return -1;
    }
    r->attr_initialized = 1;

    /*
     * Two attr flags carry the witness-honesty guarantees:
     *
     *   POSIX_SPAWN_CLOEXEC_DEFAULT - Darwin extension. Closes
     *     every inherited FD in the child EXCEPT those mentioned
     *     in this file_actions handle. Without this, the helper
     *     would inherit the worker's shm fd (FD 3 carries the
     *     result region) and the policy-pipe read end (would expose
     *     the SBPL source). With it, the child sees exactly the FDs
     *     we explicitly dup/open below and nothing more.
     *
     *   POSIX_SPAWN_SETPGROUP + setpgroup(0) - puts the child in
     *     its own process group with pgid == child_pid. Lets the
     *     cleanup path request termination of members that remain
     *     in this group. Descendants can leave the group; this is
     *     not a general process-tree containment mechanism.
     */
    short flags = (short)(POSIX_SPAWN_CLOEXEC_DEFAULT | POSIX_SPAWN_SETPGROUP);
    rc = posix_spawnattr_setflags(&r->attr, flags);
    if (rc == 0) rc = posix_spawnattr_setpgroup(&r->attr, 0);
    if (rc != 0) {
        exec_setup_failed(slot, "posix_spawnattr_set*", rc);
        exec_resources_release(r);
        return -1;
    }

    /* File actions: child gets stdin from /dev/null (so a helper
     * that read(STDIN) gets EOF rather than blocking on an
     * inherited fd that doesn't exist under CLOEXEC_DEFAULT),
     * stdout/stderr dup'd from our pipes. addopen runs in the
     * child after fork, so the FD it produces is one of the
     * CLOEXEC_DEFAULT exceptions. The originals are closed after
     * the adddup2 so the child doesn't carry the pipe-source fds
     * redundantly; CLOEXEC_DEFAULT would close them anyway. */
    rc = posix_spawn_file_actions_addopen(&r->actions, STDIN_FILENO,
                                          "/dev/null", O_RDONLY, 0);
    if (rc == 0) rc = posix_spawn_file_actions_adddup2(&r->actions, out_pipe[1], STDOUT_FILENO);
    if (rc == 0) rc = posix_spawn_file_actions_adddup2(&r->actions, err_pipe[1], STDERR_FILENO);
    if (rc == 0) rc = posix_spawn_file_actions_addclose(&r->actions, out_pipe[1]);
    if (rc == 0) rc = posix_spawn_file_actions_addclose(&r->actions, err_pipe[1]);
    if (rc == 0) rc = posix_spawn_file_actions_addclose(&r->actions, out_pipe[0]);
    if (rc == 0) rc = posix_spawn_file_actions_addclose(&r->actions, err_pipe[0]);
    if (rc != 0) {
        exec_setup_failed(slot, "posix_spawn_file_actions_add*", rc);
        exec_resources_release(r);
        return -1;
    }
    return 0;
}

/* Drain a single stream into the slot buffer. Returns updated `*used`
 * via the in/out parameter, and sets *overflow when content exceeded
 * the buffer. Reads up to one buffered chunk per call so the caller's
 * poll loop can interleave both streams. */
static int drain_one(int fd, char *dst, size_t cap, size_t *used, int *overflow) {
    char buf[256];
    ssize_t n = read(fd, buf, sizeof(buf));
    if (n <= 0) return (int)n;            /* 0 = EOF; <0 = error */
    size_t room = (cap > *used + 1u) ? (cap - 1u - *used) : 0u;
    size_t to_copy = ((size_t)n < room) ? (size_t)n : room;
    if (to_copy > 0) memcpy(dst + *used, buf, to_copy);
    *used += to_copy;
    if ((size_t)n > to_copy) *overflow = 1;
    return (int)n;
}

static void attempt_exec_spawn(pw_shm_slot_t *slot, pw_timing_t *timing,
                               uint32_t phase, uint32_t index) {
    /* Sentinel conventions when no child runs (header documents these). */
    slot->child_pid          = 0;
    slot->child_exit_code    = -1;
    slot->child_term_signal  = 0;
    slot->child_stdout[0]    = '\0';
    slot->child_stderr[0]    = '\0';
    memset(&slot->exec_valid, 0, PW_SHM_EXEC_EVIDENCE_BYTES);

    /* Attempt budget admission. Refusal is per-step evidence with no spawn
     * claimed; sandbox attribution stays unestablished (errno ETIMEDOUT is
     * not a permission result). Otherwise the child's deadline is the
     * smaller of the per-step deadline and the budget remainder. An unusable
     * clock refuses the spawn with no errno: it is a local fault. */
    uint64_t now = 0;
    uint32_t admit_fault = pw_clock_sample(&timing->clock, PW_CLOCK_EXEC_ADMIT, phase, index, &now);
    if (admit_fault) {
        slot->rc = -1;
        slot->errno_val = 0;
        pw_text_t text = {slot->error, 0, sizeof(slot->error)};
        pw_text_add(&text, "exec attempt budget: worker clock unusable before spawn; ");
        pw_text_add_local(&text, admit_fault, PW_CLOCK_EXEC_ADMIT, &timing->clock.fault);
        return;
    }
    if (now >= timing->plan_deadline) {
        slot->rc = -1;
        slot->errno_val = ETIMEDOUT;
        snprintf(slot->error, sizeof(slot->error),
                 "exec attempt budget: %ld ms exhausted before spawn", timing->budget_ms);
        return;
    }

    /* Build argv from slot->target + slot->argv[1..argv_count-1].
     * The host always writes argv[0] = target plus the caller's args,
     * so argv_count is at least 1 when the host populated the slot;
     * be defensive (use slot->target as the sole entry) if a slot
     * somehow arrives with argv_count == 0. */
    uint32_t total = slot->argv_count;
    if (total == 0u) total = 1u;
    if (total > PW_SHM_MAX_ARGV) total = PW_SHM_MAX_ARGV;

    char *argv_local[PW_SHM_MAX_ARGV + 1];
    /* Defensive NUL-terminate every populated argv entry; the host
     * bounds these but a stray missing NUL would let posix_spawn
     * read past the slot field. */
    argv_local[0] = slot->target;
    for (uint32_t i = 1u; i < total; i++) {
        slot->argv[i][PW_SHM_ARGV_BYTES - 1u] = '\0';
        argv_local[i] = slot->argv[i];
    }
    argv_local[total] = NULL;

    /* Pass an EMPTY environment per the plan: the exec attempt is a
     * witness for the kernel's sandbox enforcement against
     * posix_spawn, not for environment-variable behavior. Inheriting
     * the worker's environ would leak dyld/DYLD_* settings and TMPDIR
     * into the helper. macOS dyld uses the shared cache without env
     * for system binaries; helpers that rely on PATH or HOME must
     * pass absolute paths via target/args anyway. */
    static char *empty_envp[] = { NULL };

    /* Post-apply setup: the pipes and spawn handles live only for this
     * attempt. A failure here names its own call and claims no spawn. */
    pw_exec_resources_t res;
    pw_exec_resources_t *r = &res;
    if (exec_resources_acquire(r, slot) != 0) return;

    pid_t child = 0;
    int spawn_rc = posix_spawn(&child, slot->target, &r->actions, &r->attr,
                               argv_local, empty_envp);
    if (spawn_rc != 0) {
        exec_resources_release(r);
        /* posix_spawn returns an errno-style value rather than -1+errno. */
        slot->rc = -1;
        slot->errno_val = spawn_rc;
        snprintf(slot->error, sizeof(slot->error),
                 "posix_spawn: %s", strerror(spawn_rc));
        return;
    }

    slot->child_pid = (int32_t)child;
    /* The child is now its own process-group leader (pgid == child)
     * thanks to POSIX_SPAWN_SETPGROUP. Stash the pgid so the deadline
     * path can request termination of that group. */
    pid_t child_pgid = child;

    /* Close the parent's copy of the write ends. The child holds them
     * (via the dup2'd STDOUT/STDERR), and once the child exits the
     * kernel closes its references; the read end then sees EOF. If we
     * leave the parent's write ends open here, the read end would
     * never see EOF and the poll loop would spin until the bounded
     * deadline. */
    if (r->stdout_wfd >= 0) { close(r->stdout_wfd); r->stdout_wfd = -1; }
    if (r->stderr_wfd >= 0) { close(r->stderr_wfd); r->stderr_wfd = -1; }

    /* The plan deadline is absolute: spawn/setup latency cannot restart its
     * remainder. A blocking spawn itself cannot be interrupted here. Local
     * timing faults are kept apart from native observation errors. */
    int observation_errno = 0;
    const char *observation_call = NULL;
    int deadline_expired = 0, child_exited = 0, ownership_known = 1;
    uint64_t deadline = timing->plan_deadline, child_deadline = 0;
    int deadline_clamped = 1;
    uint32_t local_fault = pw_clock_sample(&timing->clock, PW_CLOCK_EXEC_OBSERVE, phase, index, &now);
    if (!local_fault) local_fault = pw_ticks_add(now, timing->child_ticks, &child_deadline);
    if (!local_fault && child_deadline < deadline) {
        deadline = child_deadline;
        deadline_clamped = 0;
    }
    const char *deadline_note = deadline_clamped ? "exec attempt budget deadline" : "exec child deadline";

    /* Pipe EOF and leader exit are independent observations. WNOWAIT retains
     * our unreaped child (and its PID) until group cleanup has been requested;
     * an exited leader must not suppress termination of pipe-holding peers. */
    size_t stdout_n = 0, stderr_n = 0;
    int stdout_overflow = 0, stderr_overflow = 0;
    int stdout_open = 1, stderr_open = 1;
    while (!observation_errno && !local_fault) {
        local_fault = pw_clock_sample(&timing->clock, PW_CLOCK_EXEC_OBSERVE, phase, index, &now);
        if (local_fault) break;
        if (now >= deadline) { deadline_expired = 1; break; }
        if (!child_exited) {
            siginfo_t info = {0};
            if (waitid(P_PID, (id_t)child, &info, WEXITED | WNOHANG | WNOWAIT) != 0) {
                if (errno == EINTR) continue; /* still subject to the deadline */
                observation_errno = errno; observation_call = "waitid";
                slot->exec_waitid_errno = observation_errno;
                ownership_known = 0; break;
            }
            child_exited = info.si_pid == child;
        }
        if (child_exited && !stdout_open && !stderr_open) break;

        struct pollfd pfds[2];
        nfds_t npfds = 0;
        int stdout_idx = -1, stderr_idx = -1;
        if (stdout_open) {
            stdout_idx = (int)npfds;
            pfds[npfds++] = (struct pollfd){r->stdout_rfd, POLLIN, 0};
        }
        if (stderr_open) {
            stderr_idx = (int)npfds;
            pfds[npfds++] = (struct pollfd){r->stderr_rfd, POLLIN, 0};
        }
        /* Also revisit leader status when no pipe is open. Round up sub-ms
         * remainders so a near-boundary observation cannot busy-loop; cap
         * the bounded delta before narrowing it to a poll timeout. */
        uint64_t left_ms = 0;
        local_fault = pw_ms_for_ticks(&timing->clock, deadline - now, &left_ms);
        if (local_fault) break;
        int poll_ms = left_ms > 10 ? 10 : (int)left_ms;
        int pr = poll(pfds, npfds, poll_ms);
        if (pr < 0 && errno == EINTR) continue;
        if (pr < 0) {
            observation_errno = errno; observation_call = "poll";
            slot->exec_poll_errno = observation_errno;
            break;
        }
        if (pr == 0) continue;
        int indices[] = {stdout_idx, stderr_idx};
        for (int stream = 0; stream < 2; stream++) {
            int index = indices[stream];
            if (index < 0) continue;
            int *open = stream ? &stderr_open : &stdout_open;
            if (pfds[index].revents & (POLLIN | POLLHUP)) {
                int n = drain_one(pfds[index].fd,
                    stream ? slot->child_stderr : slot->child_stdout,
                    PW_SHM_CHILD_OUTPUT_BYTES,
                    stream ? &stderr_n : &stdout_n,
                    stream ? &stderr_overflow : &stdout_overflow);
                if (n == 0) *open = 0;
                else if (n < 0 && errno != EINTR && errno != EAGAIN) {
                    observation_errno = errno; observation_call = "read";
                    if (stream) slot->exec_stderr_read_errno = observation_errno;
                    else slot->exec_stdout_read_errno = observation_errno;
                }
            } else if (pfds[index].revents & (POLLERR | POLLNVAL)) {
                observation_errno = EIO; observation_call = "poll stream";
                if (stream) slot->exec_stderr_poll_revents = pfds[index].revents;
                else slot->exec_stdout_poll_revents = pfds[index].revents;
            }
        }
    }

    /* Freeze collection before any cleanup or reap. EOF records only a read
     * returning zero; closing descriptors later cannot change this snapshot. */
    slot->exec_collection_stop = local_fault ? PW_EXEC_COLLECTION_CLOCK_FAULT
        : observation_errno ? PW_EXEC_COLLECTION_ERROR
        : deadline_expired ? PW_EXEC_COLLECTION_DEADLINE : PW_EXEC_COLLECTION_COMPLETE;
    slot->exec_leader_exit_observed = child_exited;
    slot->exec_stdout_eof = !stdout_open;
    slot->exec_stderr_eof = !stderr_open;
    slot->exec_deadline_kind = deadline_expired
        ? (deadline_clamped ? PW_EXEC_DEADLINE_PLAN : PW_EXEC_DEADLINE_CHILD) : 0;
    slot->exec_collection_clock_fault = local_fault;

    /* Append truncation marker when content overflowed the buffer.
     * The marker eats the tail of the buffer so the resulting string
     * stays NUL-terminated within PW_SHM_CHILD_OUTPUT_BYTES. */
    static const char marker[] = "\n... [truncated]";
    const size_t mlen = sizeof(marker) - 1u;
    if (stdout_overflow) {
        size_t start = (stdout_n + mlen + 1u > sizeof(slot->child_stdout))
            ? sizeof(slot->child_stdout) - 1u - mlen
            : stdout_n;
        memcpy(slot->child_stdout + start, marker, mlen);
        stdout_n = start + mlen;
    }
    if (stdout_n >= sizeof(slot->child_stdout)) stdout_n = sizeof(slot->child_stdout) - 1u;
    slot->child_stdout[stdout_n] = '\0';

    if (stderr_overflow) {
        size_t start = (stderr_n + mlen + 1u > sizeof(slot->child_stderr))
            ? sizeof(slot->child_stderr) - 1u - mlen
            : stderr_n;
        memcpy(slot->child_stderr + start, marker, mlen);
        stderr_n = start + mlen;
    }
    if (stderr_n >= sizeof(slot->child_stderr)) stderr_n = sizeof(slot->child_stderr) - 1u;
    slot->child_stderr[stderr_n] = '\0';

    int cleanup_errno = 0;
    slot->exec_cleanup_state = (deadline_expired || observation_errno || local_fault)
        ? PW_EXEC_CLEANUP_OWNERSHIP_UNCONFIRMED : PW_EXEC_CLEANUP_NOT_REQUESTED;
    if ((deadline_expired || observation_errno || local_fault) && ownership_known) {
        slot->exec_cleanup_state = PW_EXEC_CLEANUP_REQUESTED;
        slot->exec_group_target = -child_pgid;
        slot->exec_group_signal = SIGKILL;
        int group_rc = kill(-child_pgid, SIGKILL);
        int group_errno = group_rc != 0 ? errno : 0;
        slot->exec_group_rc = group_rc;
        slot->exec_group_errno = group_errno;
        if (group_rc != 0 && group_errno != ESRCH) {
            cleanup_errno = group_errno;
            /* A leader-only fallback cannot prove group cleanup. */
            slot->exec_fallback_present = 1;
            slot->exec_fallback_target = child;
            slot->exec_fallback_signal = SIGKILL;
            int fallback_rc = kill(child, SIGKILL);
            int fallback_errno = fallback_rc != 0 ? errno : 0;
            slot->exec_fallback_rc = fallback_rc;
            slot->exec_fallback_errno = fallback_errno;
        }
    }

    /* No blocking reap, even after a successful kill request. Keep raw status
     * only after waitpid returns our child. Failed cleanup must neither hang
     * the worker nor fabricate a clean exit from a zero-initialized status.
     * Unusable reap time still permits the immediate nonblocking observation;
     * otherwise timed reaping stops with the local fault and no status. */
    int status = 0, reap_errno = 0;
    pid_t reaped = 0;
    uint64_t reap_deadline = 0;
    uint32_t reap_fault = pw_clock_sample(&timing->clock, PW_CLOCK_EXEC_REAP, phase, index, &now);
    if (!reap_fault) reap_fault = pw_ticks_add(now, timing->reap_ticks, &reap_deadline);
    for (;;) {
        reaped = waitpid(child, &status, WNOHANG);
        int wait_errno = reaped < 0 ? errno : 0;
        slot->exec_reap_wait_rc = reaped;
        slot->exec_reap_wait_errno = wait_errno;
        if (reaped == child) {
            slot->exec_reap_status = status;
            slot->exec_reap_stop = PW_EXEC_REAP_REAPED;
            break;
        }
        if (reaped < 0 && wait_errno != EINTR) {
            reap_errno = wait_errno;
            slot->exec_reap_stop = PW_EXEC_REAP_WAIT_ERROR;
            break;
        }
        if (!ownership_known || cleanup_errno) {
            /* Pending, not a native wait failure. Preserve the guard order. */
            slot->exec_reap_stop = !ownership_known ? PW_EXEC_REAP_OWNERSHIP_UNCONFIRMED
                                                   : PW_EXEC_REAP_GROUP_REQUEST_FAILED;
            break;
        }
        if (reap_fault) { slot->exec_reap_stop = PW_EXEC_REAP_CLOCK_FAULT; break; }
        reap_fault = pw_clock_sample(&timing->clock, PW_CLOCK_EXEC_REAP, phase, index, &now);
        if (reap_fault) { slot->exec_reap_stop = PW_EXEC_REAP_CLOCK_FAULT; break; }
        if (now >= reap_deadline) {
            reap_errno = ETIMEDOUT;
            slot->exec_reap_stop = PW_EXEC_REAP_DEADLINE;
            break;
        }
        (void)poll(NULL, 0, 1);
    }
    slot->exec_reap_clock_fault = reap_fault;

    exec_resources_release(r);
    /* This is payload validity, not publication. run_attempt release-stores
     * completed only after the legacy result has also been assembled. */
    slot->exec_valid = 1;

    if (reaped == child) {
        if (WIFEXITED(status)) slot->child_exit_code = WEXITSTATUS(status);
        else if (WIFSIGNALED(status)) slot->child_term_signal = WTERMSIG(status);
    }
    if (observation_errno || cleanup_errno || reaped != child || local_fault || reap_fault) {
        slot->rc = -1;
        /* Post-spawn errno is never a claim that sandbox admission failed. A
         * local timing fault contributes none; native errors keep theirs. */
        slot->errno_val = observation_errno ? observation_errno : cleanup_errno ? cleanup_errno : reap_errno;
        int length = snprintf(slot->error, sizeof(slot->error),
                 "exec observation=%s errno=%d; group_cleanup_errno=%d; reaped=%d reap_errno=%d",
                 observation_call ? observation_call : local_fault ? "local timing"
                     : deadline_expired ? deadline_note : "complete",
                 observation_errno, cleanup_errno, reaped == child, reap_errno);
        if ((local_fault || reap_fault) && length > 0 && (size_t)length < sizeof(slot->error)) {
            pw_text_t text = {slot->error, (size_t)length, sizeof(slot->error)};
            pw_text_add(&text, "; ");
            pw_text_add_local(&text, local_fault ? local_fault : reap_fault,
                              local_fault ? PW_CLOCK_EXEC_OBSERVE : PW_CLOCK_EXEC_REAP, &timing->clock.fault);
        }
        return;
    }

    if (WIFEXITED(status)) {
        slot->child_exit_code   = WEXITSTATUS(status);
        slot->child_term_signal = 0;
        slot->rc                = deadline_expired ? -1 : slot->child_exit_code;
        slot->errno_val         = 0;
        if (deadline_expired) {
            /* Edge case: the helper happened to finish between the
             * deadline-expired check and the WNOHANG waitpid. Surface
             * the natural exit code but still mark the deadline in
             * the error string so a downstream consumer can see that
             * the run was bounded. */
            snprintf(slot->error, sizeof(slot->error),
                     "child exit observed after %s expired", deadline_note);
        }
    } else if (WIFSIGNALED(status)) {
        slot->child_exit_code   = -1;
        slot->child_term_signal = WTERMSIG(status);
        slot->rc                = -1;
        slot->errno_val         = 0;
        if (deadline_expired && slot->child_term_signal == SIGKILL) {
            snprintf(slot->error, sizeof(slot->error),
                     "%s expired; child SIGKILL'd", deadline_note);
        } else {
            snprintf(slot->error, sizeof(slot->error),
                     "child signaled: signal=%d", slot->child_term_signal);
        }
    } else {
        slot->rc                = -1;
        slot->errno_val         = 0;
        snprintf(slot->error, sizeof(slot->error),
                 "child did not exit or signal: status=%d", status);
    }
}

#endif
