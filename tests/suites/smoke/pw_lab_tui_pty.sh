#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "${ROOT_DIR}/tests/lib/testlib.sh"

PW_TEST_SUITE="smoke"
PW_TEST_ID="pw_lab_tui_pty"

OUT_DIR="${PW_TEST_OUT_DIR}/suites/${PW_TEST_SUITE}/${PW_TEST_ID}"
LAB_TOOL="${ROOT_DIR}/tools/pwlab/pw-lab"
RUN_FIXTURE="${ROOT_DIR}/tests/fixtures/pw_lab/run_basic"

test_begin "${PW_TEST_SUITE}" "${PW_TEST_ID}"
test_step "pty_resize" "pty-driven tui resize smoke"

if [[ ! -x "${LAB_TOOL}" ]]; then
  test_fail "pw-lab tool is missing or not executable: ${LAB_TOOL}"
fi

mkdir -p "${OUT_DIR}"

/usr/bin/python3 - "${LAB_TOOL}" "${RUN_FIXTURE}" <<'PY'
import fcntl
import os
import pty
import struct
import sys
import termios
import time

lab_tool = sys.argv[1]
run_fixture = sys.argv[2]
cmd = [lab_tool, "tui", run_fixture]

pid, fd = pty.fork()
if pid == 0:
    os.environ["TERM"] = os.environ.get("TERM") or "xterm-256color"
    os.environ.pop("LINES", None)
    os.environ.pop("COLUMNS", None)
    os.execv(cmd[0], cmd)

flags = fcntl.fcntl(fd, fcntl.F_GETFL)
fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

def set_winsz(rows, cols):
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

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

set_winsz(6, 40)
start = time.time()
sent_q = False
resized = False

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

    pid_done, status = os.waitpid(pid, os.WNOHANG)
    if pid_done == pid:
        if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
            raise SystemExit(0)
        code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else 1
        raise SystemExit(code if code != 0 else 1)

    if now - start > 5:
        try:
            os.kill(pid, 9)
        except OSError:
            pass
        raise SystemExit(1)

    time.sleep(0.05)
PY

test_pass "pw-lab tui pty ok" "{}"
