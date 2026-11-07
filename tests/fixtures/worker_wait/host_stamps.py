"""Instrumented disposable host for the worker-wait pilot: patch set, builder, stager.

Only copies change. build_host copies a source tree's runner/ (this
checkout's by default), applies PATCHES with an assert-once replacement,
prepends the literal stamp directory to HostStamps.swift and compiles that
tree's Meson source list with fixed flags. An optional patch applies when its
anchor occurs once and is skipped, and recorded, when it is absent. With no
patches it builds the uninstrumented neighbor by the same recipe, without
HostStamps.swift. stage substitutes the host and one worker in both roles into
a copy of a signed app, the way the order-barrier control's signed_copy does.

Both workers keep the generated ABI identity of their source tree, which does
not describe their bytes; receipts name the actual hashes and the substitution.

The request's specimen_id reaches the recorder from PWRunnerService's
runReservedSpecimen, right after the request decodes and before admission.
The host then writes <stamp_dir>/<stem>.started (pre-spawn, close-on-exec,
temporary file plus rename), <stamp_dir>/<stem>.stamps.json immediately before
the reply is sent and, once that file is renamed into place, the
<stamp_dir>/<stem>.exported marker. A missing directory skips every write.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import secrets
import shutil
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
sys.path.insert(0, str(ROOT / 'tests/fixtures/caller_auth'))
import native_sources
from artifact import digest, inventory, inspect, EXECUTABLES, MANIFEST, PROVENANCE
from bundle import command, save
from contract import WORKER_IDENTITY

FIXTURE = Path(__file__).resolve().parent
STAMP_SOURCE = FIXTURE / 'HostStamps.swift'
SERVICE = Path('Contents/XPCServices/PWRunner.xpc')
WORKER = SERVICE / 'Contents/MacOS/pw-probe-runner'
UNENTITLED = SERVICE / 'Contents/MacOS/pw-probe-runner-unentitled'
EQUIPMENT = SERVICE / 'Contents/Resources/worker-equipment.json'
HOST = SERVICE / 'Contents/MacOS/PWRunner'
SWIFT_FLAGS = ('-Onone', '-g')
SWIFT_JOBS = '2'
STAMP_DIR_PATTERN = re.compile(r'/[A-Za-z0-9/._-]+')
VOLATILE_ROOTS = (Path('/private/tmp'), Path('/private/var/folders'))

HOST_EVENTS = {
    100: 'REQUEST_START', 101: 'WORKER_SPAWNED', 102: 'READY_OBSERVED', 103: 'APPLIED_OBSERVED',
    110: 'ARRIVAL_OBSERVED', 111: 'PREMATURE_CHECK_DONE', 112: 'HOOK_MARK',
    120: 'PLANNING_START', 121: 'PLANNING_END', 122: 'SERIALIZE_START', 123: 'SERIALIZE_END',
    124: 'PIPES_READY', 125: 'SPAWN_START', 126: 'SPAWN_END', 127: 'FIRST_WRITE', 128: 'STDIN_CLOSED',
    129: 'FIRST_READ', 130: 'STDOUT_EOF', 131: 'DECODE_START', 132: 'DECODE_END', 133: 'GRACE_START',
    134: 'VALIDATOR_REAPED', 135: 'GRACE_END', 136: 'VALIDATOR_TERMINATE',
    139: 'RELEASE_STORE_BEGIN', 140: 'HOOK_END', 141: 'RELEASE_STORED', 142: 'ACK_OBSERVED', 143: 'COMPLETION_OBSERVED',
    144: 'DONE_OBSERVED', 145: 'DEATH_CHECK', 146: 'EXIT_REQUESTED', 147: 'WORKER_REAPED',
    149: 'ACTIVATION_STORE_BEGIN', 150: 'ACTIVATION_STORED', 151: 'COLLECTION_START', 152: 'COLLECTION_END',
    153: 'CUSTODY_SERVICE_START', 154: 'CUSTODY_SERVICE_END', 155: 'TRANSFER_WAIT_START',
    156: 'TRANSFER_WAIT_END', 160: 'SETUP_DONE', 161: 'SCHEDULE_DONE',
    170: 'STAMP_PAGE_COPIED', 171: 'FLUSH_BEGIN',
    180: 'HOST_SLEEP_BEGIN', 181: 'HOST_SLEEP_END',
}
SLEEP_KEYS = {
    0: 'ready-byte wait (10 ms sleep on the baseline, bounded readability wait on HOST-01)', 1: 'ordinary sentinel 2 ms', 2: 'actor setup 1 ms',
    3: 'actor execution 1 ms', 4: 'validator grace 10 ms', 5: 'worker grace 10 ms',
    6: 'custody recipient 1 ms', 7: 'termination gate 1 ms',
}
GRACE_STOP_CODES = {0: 'exhausted', 1: 'reaped', 2: 'wait_error'}
DEATH_CHECK_CODES = {0: 'pending', 1: 'reaped', 2: 'failed'}


def sanitize_specimen_id(specimen_id):
    """The host's file stem: each UTF-8 byte outside [A-Za-z0-9._-] becomes '_', then 120 bytes."""
    allowed = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-')
    return bytes(b if b in allowed else 0x5f for b in specimen_id.encode()[:120]).decode('ascii')


def stamp_paths(stamp_dir, specimen_id):
    stem = sanitize_specimen_id(specimen_id)
    return Path(stamp_dir) / (stem + '.started'), Path(stamp_dir) / (stem + '.stamps.json')


def exported_path(stamp_dir, specimen_id):
    """The marker written after the stamps file: host_pid, begin_raw (event 171), end_raw, bytes."""
    return Path(stamp_dir) / (sanitize_specimen_id(specimen_id) + '.exported')


def default_stamp_dir():
    """A fresh, not yet created directory name; the caller creates and owns it."""
    return Path('/private/tmp/pw-worker-wait-stamps') / secrets.token_hex(8)


def _after(file, anchor, text):
    return (file, anchor, anchor + text)


def _before(file, anchor, text):
    return (file, anchor, text + anchor)


def _swap(file, old, new):
    return (file, old, new)


def _optional(patch):
    """Applied when its anchor occurs once, skipped and recorded when absent; more than once fails."""
    return (*patch, 'optional')


CW = 'Sources/PWRunnerCore/CWorker.swift'
AS = 'Sources/PWRunnerCore/ActorSession.swift'
SCH = 'Sources/PWRunnerCore/ActorScheduler.swift'
VC = 'Sources/PWRunnerCore/ValidatorClient.swift'
ORD = 'Sources/PWRunnerCore/CWorkerOrchestrator.swift'
ACT = 'Sources/PWRunnerCore/ActorOrchestration.swift'
CUS = 'Sources/PWRunnerCore/AuthorityCustody.swift'
SVC = 'Sources/PWRunnerCore/PWRunnerService.swift'
MAIN = 'Services/PWRunner/main.swift'

_PLAN = ('            queryPlans[index] = planValidatorQueries(phases[index].actions.compactMap { $0.probe })\n'
         '            let probes = queryPlans[index].compactMap { $0.probe }\n')
_GLOBAL = 'UInt32(truncatingIfNeeded: (input.phases[index].globalPhase ?? (index + 1)) - 1)'
_CUSTODY_WORK = '(custody?.custody.count ?? 0) + (custody?.transfers.count ?? 0)'

# Ordered (runner-relative file, old, new[, 'optional']). Each old text must occur
# exactly once in its file when its turn comes; an optional one may also be absent.
PATCHES = [
    # HostWaitClock: a caller key per wait, and the actual length of every sleep.
    _after(CW, '    let calls: ChildProcessCalls\n    let started: UInt64?\n', '    let stampLabel: UInt32\n'),
    _swap(CW, '    init(milliseconds: Int, pollNs: UInt64, calls: ChildProcessCalls) {\n',
          '    init(milliseconds: Int, pollNs: UInt64, calls: ChildProcessCalls, label: UInt32 = 0) {\n'
          '        stampLabel = label\n'),
    _swap(CW, '        fallbackRemainingNs -= sleep\n        calls.sleep(sleep)\n',
          '        fallbackRemainingNs -= sleep\n        let stampPre = mach_continuous_time()\n        calls.sleep(sleep)\n'
          '        HostStamps.shared.sleep(stampLabel, pre: stampPre, requestedNs: sleep)\n'),
    # A readiness-driven ready-byte wait (HostWaitClock.expiredAfterWaiting in a tree that has it) is
    # bracketed by the same hook, so its bounded waits appear under key 0 like the sleeps it replaces.
    _optional(_swap(CW, '        fallbackRemainingNs -= wait\n        calls.waitReadable(fd, wait)\n',
                    '        fallbackRemainingNs -= wait\n        let stampPre = mach_continuous_time()\n        calls.waitReadable(fd, wait)\n'
                    '        HostStamps.shared.sleep(stampLabel, pre: stampPre, requestedNs: wait)\n')),
    # Owned reaps: the stamp precedes the observed_ns read of the same reap.
    _after(CW, '    private var captureOrdinal: UInt64 = 0\n',
           '    var stampEvent: UInt32 = 0\n    var stampPhase: UInt32 = UInt32.max\n'),
    _swap(CW, '            if rc == pid {\n                status = candidate\n',
          '            if rc == pid {\n'
          '                if stampEvent != 0 { HostStamps.shared.record(stampEvent, stampPhase, UInt64(UInt32(bitPattern: pid))) }\n'
          '                status = candidate\n'),
    # Ordinary polling loop.
    _swap(CW, '        var clock = HostWaitClock(milliseconds: input.sentinelTimeoutMs, pollNs: 2_000_000, calls: processCalls)\n',
          '        var clock = HostWaitClock(milliseconds: input.sentinelTimeoutMs, pollNs: 2_000_000, calls: processCalls, label: 1)\n'),
    _swap(CW, '            if !sawApplied && session.appliedObserved {\n',
          '            if !sawApplied && HostStamps.shared.sample(103, session.input.actorIndex, session.appliedObserved) {\n'),
    _swap(CW, '                && session.arrived(nextPhase) {\n',
          '                && HostStamps.shared.sample(110, UInt32(nextPhase), session.arrived(nextPhase)) {\n'),
    _after(CW, '                session.phaseOutputs[index].arrived = true\n                session.checkPrematurePublication(index)\n',
           '                HostStamps.shared.record(111, UInt32(index))\n'),
    _after(CW, '                let hookStarted = clock.mark()\n', '                HostStamps.shared.record(112, UInt32(index))\n'),
    _after(CW, '                clock.excludeSince(hookStarted)\n', '                HostStamps.shared.record(140, UInt32(index))\n'),
    _swap(CW, '            if session.doneObserved {\n                session.pollStopReason = "done"\n',
          '            if HostStamps.shared.sample(144, session.input.actorIndex, session.doneObserved) {\n'
          '                session.pollStopReason = "done"\n'),
    _swap(CW, '                nextExitCheckNs = (elapsed ?? 0) + 50_000_000\n                switch session.waitChild(stage: "poll") {\n',
          '                nextExitCheckNs = (elapsed ?? 0) + 50_000_000\n'
          '                let stampDeathCheck = session.waitChild(stage: "poll")\n'
          '                HostStamps.shared.record(145, session.input.actorIndex, stampDeathCheck == .pending ? 0 : (stampDeathCheck == .reaped ? 1 : 2))\n'
          '                switch stampDeathCheck {\n'),
    # ActorSession: launch, readiness, publications the host stores (a record
    # immediately before and after each release and activation store), reap
    # role, page copy.
    _before(AS, '        for fd in relocated { close(fd) }\n        relocated.removeAll()\n',
            '        let stampSpawnReturned = mach_continuous_time()\n'),
    _swap(AS, '        pid = child\n        closeAuthorityDuplicate()\n',
          '        pid = child\n'
          '        HostStamps.shared.record(101, input.actorIndex, UInt64(UInt32(bitPattern: child)), raw: stampSpawnReturned)\n'
          '        closeAuthorityDuplicate()\n'),
    _after(AS, '        process = ChildProcessState(pid: pid, calls: processCalls)\n',
           '        process.stampEvent = 147\n        process.stampPhase = input.actorIndex\n'),
    _swap(AS, '                    if n == 1 { readyByteReceived = true; stop = "received"; break }\n',
          '                    if n == 1 { HostStamps.shared.record(102, input.actorIndex); readyByteReceived = true; stop = "received"; break }\n'),
    _before(AS, '        if let base { _ = munmap(base, PWShmLayout.regionBytes) }\n',
            '        if base != nil && spawned { HostStamps.shared.copyWorkerPage(rawBase, actor: input.actorIndex, pid: pid,'
            ' reaped: process.status != nil, captureRequested: input.captureCompiledProfile) }\n'),
    _swap(AS, '            let ack = loadAcquire(base, offset: PWShmLayout.phaseAcknowledgedOffset)\n'
              '            if ownershipUnbroken && phaseOutputs[index].releaseSet && ack == 1 {\n',
          '            let ack = loadAcquire(base, offset: PWShmLayout.phaseAcknowledgedOffset)\n'
          f'            if phaseOutputs[index].releaseSet {{ HostStamps.shared.sample(142, {_GLOBAL}, ack == 1) }}\n'
          '            if ownershipUnbroken && phaseOutputs[index].releaseSet && ack == 1 {\n'),
    _before(AS, '        storeRelease(rawBase, offset: PWShmLayout.proceedOffset, ordinal)\n',
            f'        HostStamps.shared.record(139, {_GLOBAL}, UInt64(ordinal))\n'),
    _after(AS, '        storeRelease(rawBase, offset: PWShmLayout.proceedOffset, ordinal)\n',
           f'        HostStamps.shared.record(141, {_GLOBAL}, UInt64(ordinal))\n'),
    _before(AS, '        storeRelease(rawBase, offset: PWShmLayout.activationOffset, globalPhase)\n',
            '        HostStamps.shared.record(149, globalPhase &- 1, UInt64(globalPhase))\n'),
    _after(AS, '        storeRelease(rawBase, offset: PWShmLayout.activationOffset, globalPhase)\n',
           '        HostStamps.shared.record(150, globalPhase &- 1, UInt64(globalPhase))\n'),
    _after(AS, '        storeRelease(rawBase, offset: PWShmLayout.exitRequestedOffset, 1)\n',
           '        HostStamps.shared.record(146, input.actorIndex)\n'),
    _swap(AS, '            var clock = HostWaitClock(milliseconds: input.exitGraceMs, pollNs: 10_000_000, calls: calls)\n',
          '            var clock = HostWaitClock(milliseconds: input.exitGraceMs, pollNs: 10_000_000, calls: calls, label: 5)\n'),
    # ActorScheduler: setup, schedule walk, activation/arrival/collection/completion, custody passes.
    _swap(SCH, '        var clock = HostWaitClock(milliseconds: input.setupAllowanceMs, pollNs: 1_000_000, calls: calls)\n',
          '        var clock = HostWaitClock(milliseconds: input.setupAllowanceMs, pollNs: 1_000_000, calls: calls, label: 2)\n'),
    _swap(SCH, '                if let status = setupDisposition(session) {\n',
          '                let stampSetup = setupDisposition(session)\n'
          '                HostStamps.shared.sample(103, UInt32(index), stampSetup != nil)\n'
          '                if let status = stampSetup {\n'),
    _swap(SCH, '        let executionWait = walkSchedule(collect: collect)\n',
          '        HostStamps.shared.record(160, UInt32.max)\n'
          '        let executionWait = walkSchedule(collect: collect)\n'
          '        HostStamps.shared.record(161, UInt32.max)\n'),
    _swap(SCH, '        var clock = HostWaitClock(milliseconds: input.executionAllowanceMs, pollNs: 1_000_000, calls: calls)\n',
          '        var clock = HostWaitClock(milliseconds: input.executionAllowanceMs, pollNs: 1_000_000, calls: calls, label: 3)\n'),
    _swap(SCH, '                if session.arrived(index) { break }\n',
          '                if HostStamps.shared.sample(110, UInt32(entry.phaseIndex), session.arrived(index)) { break }\n'),
    _after(SCH, '                session.phaseOutputs[index].arrived = true\n                session.checkPrematurePublication(index)\n',
           '                HostStamps.shared.record(111, UInt32(entry.phaseIndex))\n'),
    _swap(SCH, '                let mark = clock.mark()\n                let collectionStarted = calls.clock()\n',
          '                let mark = clock.mark()\n'
          '                HostStamps.shared.record(112, UInt32(entry.phaseIndex))\n'
          '                let collectionStarted = calls.clock()\n'
          '                HostStamps.shared.record(151, UInt32(entry.phaseIndex))\n'),
    _swap(SCH, '                clock.excludeSince(mark)\n                visit.collectionMs = millis(collectionStarted, calls.clock())\n',
          '                clock.excludeSince(mark)\n'
          '                HostStamps.shared.record(140, UInt32(entry.phaseIndex))\n'
          '                visit.collectionMs = millis(collectionStarted, calls.clock())\n'
          '                HostStamps.shared.record(152, UInt32(entry.phaseIndex))\n'),
    _swap(SCH, '                custody?.service(active: entry.actorIndex, phaseIndex: entry.phaseIndex,\n'
               '                                 waitAllowanceMs: remainingMs, recipientUsable: recipientUsable)\n',
          f'                let stampCustodyWork = {_CUSTODY_WORK}\n'
          '                let stampCustodyStart = custody == nil ? 0 : mach_continuous_time()\n'
          '                custody?.service(active: entry.actorIndex, phaseIndex: entry.phaseIndex,\n'
          '                                 waitAllowanceMs: remainingMs, recipientUsable: recipientUsable)\n'
          '                HostStamps.shared.custodyPass(UInt32(entry.phaseIndex), start: stampCustodyStart,\n'
          f'                                              workBefore: stampCustodyWork, workAfter: {_CUSTODY_WORK})\n'),
    _swap(SCH, '                if session.completed(index) { break }\n',
          '                if HostStamps.shared.sample(143, UInt32(entry.phaseIndex), session.completed(index)) { break }\n'),
    _swap(SCH, '        var wait=HostWaitClock(milliseconds:budget,pollNs:1_000_000,calls:calls)\n',
          '        var wait=HostWaitClock(milliseconds:budget,pollNs:1_000_000,calls:calls,label:7)\n'),
    # ValidatorClient: serialization, pipes, spawn, duplex I/O, decode, grace, termination.
    _swap(VC, '        payload = try serializeProbes(input.probes)\n',
          '        HostStamps.shared.phaseEvent(122)\n'
          '        payload = try serializeProbes(input.probes)\n'
          '        HostStamps.shared.phaseEvent(123, UInt64(payload.count))\n'),
    _before(VC, '    var fa: posix_spawn_file_actions_t? = nil\n', '    HostStamps.shared.phaseEvent(124)\n'),
    _swap(VC, '    let spawnRC = withCStringArrayCopy(argv) { argvPtr in\n        spawn(&pid, input.executablePath, &fa, argvPtr)\n    }\n',
          '    HostStamps.shared.phaseEvent(125)\n'
          '    let spawnRC = withCStringArrayCopy(argv) { argvPtr in\n        spawn(&pid, input.executablePath, &fa, argvPtr)\n    }\n'
          '    HostStamps.shared.phaseEvent(126, UInt64(UInt32(bitPattern: pid)))\n'),
    _after(VC, '    let deadline = MonotonicDeadline(milliseconds: input.verdictReadTimeoutMs)\n',
           '    var stampFirstWrite = true\n    var stampFirstRead = true\n'),
    _swap(VC, '                        if n > 0 {\n                            writeOffset += n\n',
          '                        if n > 0 {\n'
          '                            if stampFirstWrite { stampFirstWrite = false; HostStamps.shared.phaseEvent(127, UInt64(n)) }\n'
          '                            writeOffset += n\n'),
    _after(VC, '                    if stdinOpen && writeOffset >= payload.count {\n'
               '                        close(stdinPipe[1])\n                        stdinOpen = false\n',
           '                        HostStamps.shared.phaseEvent(128, UInt64(writeOffset))\n'),
    _swap(VC, '                    if n > 0 {\n                        stdoutReceived += n\n',
          '                    if n > 0 {\n'
          '                        if stampFirstRead { stampFirstRead = false; HostStamps.shared.phaseEvent(129, UInt64(n)) }\n'
          '                        stdoutReceived += n\n'),
    _swap(VC, '                    else if n == 0 { stdoutOpen = false }\n',
          '                    else if n == 0 { stdoutOpen = false; HostStamps.shared.phaseEvent(130, UInt64(stdoutReceived)) }\n'),
    _swap(VC, '    let decoded = decodeValidatorFrames(stdoutBytes, maximumRecords: recordLimit)\n',
          '    HostStamps.shared.phaseEvent(131)\n'
          '    let decoded = decodeValidatorFrames(stdoutBytes, maximumRecords: recordLimit)\n'
          '    HostStamps.shared.phaseEvent(132, UInt64(decoded.verdicts.count))\n'),
    _swap(VC, '    var process = ChildProcessState(pid: pid, calls: processCalls)\n'
              '    var graceClock = HostWaitClock(milliseconds: input.exitGraceMs, pollNs: 10_000_000, calls: processCalls)\n',
          '    var process = ChildProcessState(pid: pid, calls: processCalls)\n'
          '    process.stampEvent = 134\n    process.stampPhase = HostStamps.shared.currentPhase\n'
          '    HostStamps.shared.phaseEvent(133)\n'
          '    var graceClock = HostWaitClock(milliseconds: input.exitGraceMs, pollNs: 10_000_000, calls: processCalls, label: 4)\n'),
    _swap(VC, '    let graceWait = graceClock.record(stop: graceStop)\n    process.terminate()\n',
          '    let graceWait = graceClock.record(stop: graceStop)\n'
          '    HostStamps.shared.phaseEvent(135, graceStop == "reaped" ? 1 : (graceStop == "wait_error" ? 2 : 0))\n'
          '    process.terminate()\n'
          '    HostStamps.shared.phaseEvent(136, process.terminationRequest == nil ? 0 : 1)\n'),
    # Phase callbacks: live planning bracket and its eligible query count.
    _swap(ORD, _PLAN, '            HostStamps.shared.planningStart(index)\n' + _PLAN
          + '            HostStamps.shared.phaseEvent(121, UInt64(probes.count))\n'),
    _swap(ACT, _PLAN, '            HostStamps.shared.planningStart(index)\n' + _PLAN
          + '            HostStamps.shared.phaseEvent(121, UInt64(probes.count))\n'),
    # AuthorityCustody: the nested recipient-acknowledgement wait.
    _swap(CUS, '        var clock = HostWaitClock(milliseconds: min(PWAuthorityLayout.exchangeWaitMs, waitAllowanceMs), pollNs: 1_000_000, calls: calls)\n',
          '        HostStamps.shared.record(155, UInt32(phaseIndex), UInt64(delivery.index))\n'
          '        var clock = HostWaitClock(milliseconds: min(PWAuthorityLayout.exchangeWaitMs, waitAllowanceMs), pollNs: 1_000_000, calls: calls, label: 6)\n'),
    _swap(CUS, '            ack = loadAcquire(inbound, offset: PWAuthorityLayout.slotAcknowledgedOffset)\n'
               '            if ack != PWAuthorityAck.none { break }\n',
          '            ack = loadAcquire(inbound, offset: PWAuthorityLayout.slotAcknowledgedOffset)\n'
          '            if HostStamps.shared.sample(156, UInt32(delivery.index), ack != PWAuthorityAck.none, append: false) { break }\n'),
    _before(CUS, '        observation.recipientWait = clock.record(stop: stop)\n',
            '        HostStamps.shared.record(156, UInt32(phaseIndex), UInt64(ack))\n'),
    # Service: request entry, specimen naming and .started marker, export before exit.
    _before(SVC, '        let decision = admission.submit(owner: connectionID, token: reservation)\n',
            '        HostStamps.shared.requestStart()\n'),
    _before(SVC, '        let admitted: AdmittedSpecimen\n', '        HostStamps.shared.specimenStarted(parsed.specimen_id)\n'),
    # Export before the reply leaves the host: launchd tears the service down as
    # soon as the client disconnects, which can precede the delayed exit closure.
    _before(SVC, '            reply(true, data)\n            // Allow the XPC reply to flush before exiting the process.\n',
            '            HostStamps.shared.flush()\n'),
    _swap(SVC, '.milliseconds(hostExitDelayMs)) { exit(0) }', '.milliseconds(hostExitDelayMs)) { HostStamps.shared.flush(); exit(0) }'),
    # Allocate and touch the recorder's storage at service start, outside any request.
    _before(MAIN, 'let delegate = PWRunnerSessionDelegate()\n', '_ = HostStamps.shared\n'),
]


def replace_once(source, old, new, label=''):
    assert source.count(old) == 1, f'host stamp anchor changed{label}: {old!r}'
    return source.replace(old, new, 1)


def macos_minimum(tree=ROOT):
    values = re.findall(r"^macos_minimum = '([0-9.]+)'$", (Path(tree) / 'meson.build').read_text(), re.M)
    assert len(values) == 1, values
    return values[0]


def host_sources(out, tree=ROOT):
    """The PWRunner source list read from the tree's meson.build in file mode.

    The same reading as the order-barrier control's meson_host_sources, built
    on tests/lib/native_sources directly so this fixture does not import an
    opt-in checker and its check_ordering dependency."""
    command(out / 'introspect', ['meson', 'introspect', Path(tree) / 'meson.build', '--targets'], timeout=60)
    targets, problems = native_sources.parse_targets((out / 'introspect/stdout').read_text(), tree, 'meson.build')
    problems += native_sources.problems(targets, native_sources.expected(tree), 'meson.build')
    assert not problems, 'meson.build disagrees with the tree:\n' + '\n'.join(problems)
    sources = [s[len('runner/'):] for s in targets['PWRunner']]
    core = [s for s in sources if s.startswith('Sources/PWRunnerCore/') and s.endswith('.swift')]
    entry = [s for s in sources if s not in core]
    assert entry == ['Services/PWRunner/main.swift'], sources
    return core, entry[0]


def apply_patches(package, patches, out):
    """Apply in order; returns the patched files, runner-relative, in first-touch order, and the skipped
    optional patches."""
    touched, skipped = [], []
    for index, (relative, old, new, *mode) in enumerate(patches):
        path = package / relative
        source = path.read_text()
        if mode == ['optional'] and old not in source:
            skipped.append(dict(index=index, file=relative, old=old))
            continue
        path.write_text(replace_once(source, old, new, f' (patch {index}, {relative})'))
        if relative not in touched: touched.append(relative)
    for relative in touched:
        copy = out / 'patched-sources' / relative
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(package / relative, copy)
    return touched, skipped


def build_host(package, work, out, patches, stamp_dir, runner=ROOT / 'runner'):
    """Copy `runner` (a source tree's runner/) to `package`, patch it and compile PWRunner into `work`.

    `out` receives the command logs, patched-file copies and host-build.json;
    the same receipt is written beside the binary for stage(). No patches build
    the neighbor: same flags, Meson source list only, `stamp_dir` unused."""
    package, work, out = Path(package), Path(work), Path(out)
    runner = Path(runner).resolve(); tree = runner.parent
    assert runner.name == 'runner' and (tree / 'meson.build').is_file(), f'not a source tree runner/ directory: {runner}'
    assert not package.exists(), package
    work.mkdir(parents=True, exist_ok=True); out.mkdir(parents=True, exist_ok=True)
    patches = list(patches)
    instrumented = bool(patches)
    if instrumented:
        stamp_dir = str(stamp_dir)
        assert STAMP_DIR_PATTERN.fullmatch(stamp_dir) and '..' not in stamp_dir.split('/'), stamp_dir
    shutil.copytree(runner, package, ignore=shutil.ignore_patterns('.build', '.swiftpm'))
    sources, entry = host_sources(out, tree)
    compiled = [*sources, entry]
    for relative, *_ in patches:
        assert relative in compiled, f'patch outside the host source list: {relative}'
    touched, skipped = apply_patches(package, patches, out)
    stamp = None
    if instrumented:
        generated = package / 'WorkerWait/HostStamps.swift'
        generated.parent.mkdir()
        generated.write_text(f'let PWW_STAMP_DIR = {json.dumps(stamp_dir)}\n'
                             f'let PWW_STAMP_SWIFT_FLAGS = {json.dumps(" ".join(SWIFT_FLAGS))}\n'
                             f'let PWW_STAMP_INSPECTION = {"true" if SWIFT_FLAGS == ("-Onone", "-g") else "false"}\n'
                             + STAMP_SOURCE.read_text())
        shutil.copy2(generated, out / 'HostStamps.generated.swift')
        stamp = dict(fixture_path=str(STAMP_SOURCE.relative_to(ROOT)), fixture_sha256=digest(STAMP_SOURCE),
                     generated_path=str(generated), generated_sha256=digest(generated))
    minimum = macos_minimum(tree)
    shim = work / 'PWCWorkerShim.o'
    shim_argv = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-c', '-arch', 'arm64', f'-mmacosx-version-min={minimum}',
                 package / 'Sources/PWCWorkerShim/PWCWorkerShim.c', '-o', shim]
    command(out / 'compile-shim', shim_argv, timeout=120)
    host = work / 'PWRunner'
    host_argv = ['/usr/bin/xcrun', '--sdk', 'macosx', 'swiftc', '-j', SWIFT_JOBS, *SWIFT_FLAGS,
                 '-target', f'arm64-apple-macosx{minimum}', '-module-cache-path', work / 'module-cache', '-o', host,
                 *[package / p for p in compiled], *([Path(stamp['generated_path'])] if stamp else []), shim]
    command(out / 'compile-host', host_argv, timeout=600)
    toolchain = {}
    for name, argv in (('swiftc', ['/usr/bin/xcrun', '--sdk', 'macosx', 'swiftc', '--version']),
                       ('clang', ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '--version']),
                       ('sdk', ['/usr/bin/xcrun', '--sdk', 'macosx', '--show-sdk-path'])):
        command(out / ('toolchain-' + name), argv, timeout=60)
        toolchain[name] = (out / ('toolchain-' + name) / 'stdout').read_text().strip()
    receipt = dict(
        schema_version=1, kind='instrumented' if instrumented else 'neighbor',
        flavour=dict(swift=' '.join(SWIFT_FLAGS), inspection=SWIFT_FLAGS == ('-Onone', '-g'),
                     target=f'arm64-apple-macosx{minimum}', swift_jobs=int(SWIFT_JOBS)),
        commands=dict(shim=list(map(str, shim_argv)), host=list(map(str, host_argv))),
        stamp_dir=stamp_dir if instrumented else None, stamp_source=stamp,
        builder=dict(path=str(Path(__file__).resolve().relative_to(ROOT)), sha256=digest(Path(__file__).resolve())),
        source_tree=dict(root=str(tree), runner=str(runner)),
        sources=[dict(path=p, tree_sha256=digest(runner / p), compiled_sha256=digest(package / p),
                      patched=p in touched) for p in compiled],
        patched_files=touched,
        patches=[dict(file=f, old=o, new=n, optional=mode == ['optional'],
                      applied=not any(s['index'] == i for s in skipped)) for i, (f, o, n, *mode) in enumerate(patches)],
        patches_skipped=skipped,
        shim_object_sha256=digest(shim), output=dict(path=str(host), sha256=digest(host)),
        toolchain=toolchain,
        note=('Disposable host compiled from patched copies; never the tree or the signed app.' if instrumented else
              'Uninstrumented neighbor: the same recipe and flags over unpatched copies, without HostStamps.swift.'))
    for row in receipt['sources']:
        assert (row['tree_sha256'] != row['compiled_sha256']) == row['patched'], row
    save(out / 'host-build.json', receipt)
    shutil.copy2(out / 'host-build.json', host.with_name('host-build.json'))
    return host


def _volatile(path):
    return any(path == root or root in path.parents for root in VOLATILE_ROOTS)


IDENTITY_LINE = re.compile(r'^WORKER_IDENTITY = "([0-9a-f]{64})"$', re.M)


def tree_worker_identity(tree):
    """The worker identity a source tree declares in its tests/lib/contract.py, read as text and never imported."""
    found = IDENTITY_LINE.findall((Path(tree) / 'tests/lib/contract.py').read_text())
    assert len(found) == 1, f'{tree}: tests/lib/contract.py declares {len(found)} worker identities'
    return found[0]


def tree_commit(tree, receipts):
    """HEAD and the porcelain status of a source tree, read without taking its index lock."""
    git = ['/usr/bin/git', '-C', Path(tree), '--no-optional-locks']
    command(receipts / 'source-tree-head', [*git, 'rev-parse', 'HEAD'])
    command(receipts / 'source-tree-status', [*git, 'status', '--porcelain'])
    status = (receipts / 'source-tree-status/stdout').read_text()
    return dict(root=str(tree), head=(receipts / 'source-tree-head/stdout').read_text().strip(), dirty=bool(status.strip()),
                porcelain=status.splitlines())


def _canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def stage(source_app, staging_dir, identity, host, worker_stamps, worker_plain, instrumented, tree=ROOT):
    """Assemble and sign one durable staged app; returns its path.

    The worker in both roles is `worker_stamps` when instrumented, else
    `worker_plain`. `tree` is the source tree the app and workers were built
    from: its declared worker identity must be the app's equipment identity and
    the worker's reported one, and its entitlements sign the copy. Signing
    order, flags and entitlements follow the order-barrier control's
    signed_copy. The only executions are the two worker version probes
    staging.json lists; no request runs here."""
    source_app = Path(source_app).resolve(); staging_dir = Path(staging_dir).resolve(); tree = Path(tree).resolve()
    assert not _volatile(staging_dir), f'staging directory must be durable, not under a temporary root: {staging_dir}'
    host = Path(host).resolve()
    recipe_path = host.with_name('host-build.json')
    recipe_bytes = recipe_path.read_bytes(); recipe = json.loads(recipe_bytes)
    assert recipe['output']['sha256'] == digest(host), 'host differs from its build receipt'
    flavour = 'instrumented' if instrumented else 'neighbor'
    assert recipe['kind'] == flavour, (recipe['kind'], flavour)
    worker_stamps = Path(worker_stamps).resolve(); worker_plain = Path(worker_plain).resolve()
    worker = worker_stamps if instrumented else worker_plain
    staging_dir.mkdir(parents=True, exist_ok=True)
    app = staging_dir / 'PolicyWitness.app'
    receipts = staging_dir / 'staging-receipts'
    assert not app.exists() and not receipts.exists(), staging_dir
    receipts.mkdir()
    worker_identity = tree_worker_identity(tree)
    assert tree != ROOT or worker_identity == WORKER_IDENTITY, (worker_identity, WORKER_IDENTITY)
    source_before = inventory(source_app); save(receipts / 'source-inventory.json', source_before)
    command(receipts / 'copy', ['/usr/bin/ditto', source_app, app])
    common_hash = digest(worker)
    original_equipment = json.loads((app / EQUIPMENT).read_bytes())
    save(receipts / 'source-equipment.json', original_equipment)
    assert original_equipment['worker_identity'] == worker_identity, \
        f"app equipment identity {original_equipment['worker_identity']} is not {tree}'s declared {worker_identity}"
    command(receipts / 'common-worker-identity', [worker, '--version'])
    reported = (receipts / 'common-worker-identity/stdout').read_text().split()
    assert 'abi_identity=' + worker_identity in reported, f'{worker} reports {reported}, not {tree}\'s declared {worker_identity}'
    source_tree = tree_commit(tree, receipts)
    for relative in (WORKER, UNENTITLED):
        shutil.copy2(worker, app / relative)
        assert digest(app / relative) == common_hash
    shutil.copy2(host, app / HOST)
    assert digest(app / HOST) == digest(host), 'host copy differs from its build output'
    assembly = dict(variant=flavour, common_input_sha256=common_hash, declared_worker_identity=worker_identity,
                    generated_identity_regenerated_for_mutation=False, identity_is_mutated_source_digest=False,
                    provenance_kind='substitution',
                    note='Fixture workers and host retain their source tree\'s ABI identity; it does not describe their bytes. '
                         'Actual bytes and substitution provenance remain separate.',
                    stages=['copy_common_worker_to_both_roles', 'copy_host'])
    save(receipts / 'equipment-assembly.json', assembly)
    app_id = 'com.policywitness.test.workerwait.a' + secrets.token_hex(10)
    service_id = 'com.policywitness.test.workerwait.s' + secrets.token_hex(10)
    for bundle, identifier in ((app, app_id), (app / SERVICE, service_id)):
        plist = bundle / 'Contents/Info.plist'; value = plistlib.loads(plist.read_bytes())
        value['CFBundleIdentifier'] = identifier; plist.write_bytes(plistlib.dumps(value))
    selected_entitlements = tree / 'runner/Services/PWRunner/Entitlements.plist'
    assert plistlib.loads(selected_entitlements.read_bytes()) == {}, 'this fixture requires empty worker entitlements'
    command(receipts / 'sign-worker', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', selected_entitlements, '-s', identity, app / WORKER], timeout=90)
    assembly['stages'].append('sign_selected'); save(receipts / 'equipment-assembly.json', assembly)
    command(receipts / 'sign-unentitled-worker', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '-s', identity, app / UNENTITLED], timeout=90)
    assembly['stages'].append('sign_unentitled'); save(receipts / 'equipment-assembly.json', assembly)
    command(receipts / 'equipment', [sys.executable, '-B', '-S', ROOT / 'tests/build_equipment.py',
        '--bundle', app / SERVICE, '--unsigned-worker', worker, '--worker-identity', worker_identity], timeout=90)
    equipment_bytes = (app / EQUIPMENT).read_bytes()
    (receipts / 'worker-equipment.json').write_bytes(equipment_bytes)
    equipment = json.loads(equipment_bytes)
    assert equipment['unsigned_worker_sha256'] == common_hash and digest(worker) == common_hash
    assert equipment['worker_identity'] == worker_identity
    assert {row['role'] for row in equipment['workers']} == {'selected', 'unentitled'} and len(equipment['workers']) == 2
    for row in equipment['workers']:
        expected = WORKER if row['role'] == 'selected' else UNENTITLED
        assert app / SERVICE / row['relative_path'] == app / expected
        assert row['sha256'] == digest(app / expected)
        assert plistlib.loads(row['entitlements_xml'].encode()) == {}, row
    assembly['stages'].append('emit_inventory'); save(receipts / 'equipment-assembly.json', assembly)
    command(receipts / 'sign-service', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', selected_entitlements, '-s', identity, app / SERVICE], timeout=90)
    assembly['stages'].append('seal_service'); save(receipts / 'equipment-assembly.json', assembly)
    assert (app / EQUIPMENT).read_bytes() == equipment_bytes, 'service sealing changed inventory bytes'
    command(receipts / 'evidence', [sys.executable, '-B', '-S', ROOT / 'tests/build-evidence.py', '--app-bundle', app,
        '--app-entitlements', tree / 'PolicyWitness.entitlements', '--substitution-of', source_app, '--identity', identity], timeout=120)
    command(receipts / 'sign-app', ['/usr/bin/codesign', '--force', '--options', 'runtime', '--timestamp',
        '--entitlements', tree / 'PolicyWitness.entitlements', '-s', identity, app], timeout=90)
    report = inspect(app); save(receipts / 'artifact.json', report)
    assert report['ok'], report
    assembly['stages'].append('substitution_evidence_and_app_seal'); save(receipts / 'equipment-assembly.json', assembly)
    assert inventory(source_app) == source_before, 'source app changed during staging'
    staged = inventory(app); save(receipts / 'staged-inventory.json', staged)
    executables = {}
    for relative in EXECUTABLES:
        info = os.stat(app / relative)
        executables[relative] = dict(sha256=digest(app / relative), st_dev=info.st_dev, st_ino=info.st_ino,
                                     st_size=info.st_size, st_mode=info.st_mode)
    provenance = json.loads((app / PROVENANCE).read_bytes())
    record = dict(
        schema_version=1, flavour=flavour, app=str(app), staging_dir=str(staging_dir), identity=identity,
        bundle_ids=dict(app=app_id, service=service_id),
        source_tree=dict(source_tree, worker_identity=worker_identity, identity_source='tests/lib/contract.py WORKER_IDENTITY, read as text'),
        source_app=dict(path=str(source_app), inventory_sha256=_canonical_sha256(source_before),
                        inventory_file='staging-receipts/source-inventory.json', unchanged_by_staging=True),
        staged_inventory=dict(sha256=_canonical_sha256(staged), file='staging-receipts/staged-inventory.json'),
        inventory_hash_form='sha256 of json.dumps(inventory, sort_keys=True, separators=(",", ":"))',
        executables=executables,
        workers=dict(roles=[str(WORKER), str(UNENTITLED)], input_path=str(worker), input_sha256=common_hash,
                     stamp_worker=dict(path=str(worker_stamps), sha256=digest(worker_stamps)),
                     plain_worker=dict(path=str(worker_plain), sha256=digest(worker_plain))),
        host=dict(input_path=str(host), input_sha256=digest(host), staged_sha256=executables[str(HOST)]['sha256'],
                  note='the staged hash differs from the input hash because the service seal signs the host; '
                       'the unsigned copy was checked equal to the build output before signing'),
        recipe=dict(file=str(recipe_path), sha256=hashlib.sha256(recipe_bytes).hexdigest(), receipt=recipe),
        stamp_dir=recipe['stamp_dir'],
        equipment=dict(sha256=digest(app / EQUIPMENT), worker_identity=equipment['worker_identity']),
        manifest_sha256=digest(app / MANIFEST),
        provenance=dict(sha256=digest(app / PROVENANCE), source=provenance.get('source'),
                        substitution=provenance.get('configuration', {}).get('substitution')),
        execution=dict(
            executed=[dict(path=str(worker), argv='--version', by='host_stamps.stage'),
                      dict(path=str(app / WORKER), argv='--version', by='tests/build-evidence.py (worker identity probe)')],
            not_executed='every other staged executable, including PWRunner, pw-probe-runner-unentitled and sb_api_validator',
            note='Only these version probes ran; the caller\'s excluded warm run is the first request execution.'))
    save(staging_dir / 'staging.json', record)
    return app


def main():
    parser = argparse.ArgumentParser(description='Build an instrumented or neighbor host (no signing).')
    parser.add_argument('work', type=Path, help='new scratch directory for the copy, objects and binary')
    parser.add_argument('out', type=Path, help='receipt directory')
    parser.add_argument('--runner', type=Path, default=ROOT / 'runner', help="a source tree's runner/ (default: this checkout's)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--stamp-dir', type=Path)
    group.add_argument('--neighbor', action='store_true')
    args = parser.parse_args()
    work = args.work.resolve()
    host = build_host(work / 'runner', work, args.out.resolve(), [] if args.neighbor else PATCHES, args.stamp_dir, args.runner)
    print(json.dumps(dict(host=str(host), sha256=digest(host)), indent=2))


if __name__ == '__main__':
    main()
