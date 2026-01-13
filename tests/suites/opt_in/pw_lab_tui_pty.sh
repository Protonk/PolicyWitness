#!/usr/bin/env bash
# Opt-in PTY-driven smoke test for the pw-lab TUI.
# Exercises: curses startup, resize handling, and clean exit under a PTY.
# Intentionally small and dependency-free (stdlib Python + testlib only).
set -euo pipefail

# Repo root for locating tools and fixtures.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
# Test harness utilities (events, artifacts, reports).
source "${ROOT_DIR}/tests/lib/testlib.sh"

# Suite name keeps opt-in tests separate from default smoke output.
PW_TEST_SUITE="opt_in"
# Stable test id for reporting.
PW_TEST_ID="pw_lab_tui_pty"
# pw-lab entrypoint.
LAB_TOOL="${ROOT_DIR}/laboratory/pw-lab"
# Small fixture bundle for the TUI to render.
RUN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_lab/run_basic"

# Start test bookkeeping (events, artifacts, report path).
test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
# Single step: PTY-driven launch + resize + quit.
test_step "pty_resize" "pty-driven tui resize smoke"

# Fail fast if the lab tool is missing (this test is not meaningful otherwise).
if [[ ! -x "${LAB_TOOL}" ]]; then
  test_fail "pw-lab tool is missing or not executable: ${LAB_TOOL}"
fi

# Ensure artifacts directory exists (owned by testlib).
mkdir -p "${PW_TEST_ARTIFACTS}"

# Drive the TUI under a PTY via Python's stdlib.
/usr/bin/python3 - "${LAB_TOOL}" "${RUN_FIXTURE}" <<'PY'
import fcntl
import os
import pty
import struct
import sys
import termios
import time

# Arguments passed from the shell wrapper.
lab_tool = sys.argv[1]
run_fixture = sys.argv[2]
# Command to execute in the child process.
cmd = [lab_tool, "tui", run_fixture]

# Fork a PTY. Child becomes the TUI process attached to the slave PTY.
pid, fd = pty.fork()
if pid == 0:
    # Provide a reasonable TERM; avoid env overrides that break resize handling.
    os.environ["TERM"] = os.environ.get("TERM") or "xterm-256color"
    os.environ.pop("LINES", None)
    os.environ.pop("COLUMNS", None)
    # Exec pw-lab TUI in the child process.
    os.execv(cmd[0], cmd)

# Parent: make the PTY nonblocking to avoid deadlocks.
flags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

# Helper: change PTY window size (triggers SIGWINCH in the child).
def set_winsz(rows, cols):
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

# Helper: drain output so the PTY buffer does not fill.
def drain():
    while True:
        try:
            data = os.read(fd, 4096)
            if data == b"":
                break
        except BlockingIOError:
            break
        except OSError:
            break

# Start at a small window, then resize up.
set_winsz(6, 40)
start = time.time()
sent_q = False
resized = False

# Poll loop: resize once, send q, and wait for the child to exit.
while True:
    drain()
    now = time.time()
    if not resized and now - start > 0.2:
        set_winsz(24, 80)
        resized = True
    if not sent_q and now - start > 0.5:
        try:
            os.write(fd, b"q")
            sent_q = True
        except OSError:
            pass

    # Nonblocking wait: exit if the child finished.
    pid_done, status = os.waitpid(pid, os.WNOHANG)
    if pid_done == pid:
        if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
            raise SystemExit(0)
        code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else 1
        raise SystemExit(code if code != 0 else 1)

    # Hard timeout: kill if stuck (keeps CI from hanging).
    if now - start > 5:
        try:
            os.kill(pid, 9)
        except OSError:
            pass
        raise SystemExit(1)

    time.sleep(0.05)
PY

# Record a successful run.
test_pass "pw-lab tui pty ok" "{}"
