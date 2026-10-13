"""Public CLI boundary controls with token comparison only in transient memory."""
import ctypes
import hashlib
import json
import mmap
import os
from pathlib import Path
import struct
import stat
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
import consumer
from lifecycle_oracle import check_record
from check_extensions import probe, intervention, specimen

SIZE, TOKEN_OFFSET, TOKEN_CAPACITY = 32768, 128, 16384
LIBC = ctypes.CDLL(None, use_errno=True)
# mode is variadic; declaring it fixed uses the wrong arm64 calling convention.
LIBC.shm_open.argtypes = [ctypes.c_char_p, ctypes.c_int]
LIBC.shm_open.restype = ctypes.c_int
LIBC.shm_unlink.argtypes = [ctypes.c_char_p]
LIBC.shm_unlink.restype = ctypes.c_int


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def compile_fixture(out, channel, mode, issuer):
    path = out / ('issuer' if issuer else 'worker')
    command = ['/usr/bin/xcrun', '--sdk', 'macosx', 'clang', '-std=c11', '-O2', '-Wall', '-Wextra',
        '-Wno-deprecated-declarations', '-Wno-unused-function', f'-DPW_CONTROL_MODE={mode}',
        '-DPW_CONTROL_CHANNEL=' + json.dumps(channel), '-I', str(ROOT / 'controller/tools/pw_probe_runner')]
    if issuer:
        command.append('-DPW_CONTROL_ISSUER')
    command += [str(ROOT / 'tests/fixtures/extension_controls/control.c'), '-lsandbox', '-o', str(path)]
    result = subprocess.run(command, capture_output=True, timeout=30)
    (out / (path.name + '-build.log')).write_bytes(result.stdout + result.stderr)
    assert result.returncode == 0, f'{path.name} compile failed; see build log'
    return path


def observations(mapping):
    return dict(issuer_pid=struct.unpack_from('I', mapping, 4)[0], worker_pid=struct.unpack_from('I', mapping, 8)[0],
        stage=struct.unpack_from('I', mapping, 12)[0], operation=struct.unpack_from('I', mapping, 16)[0],
        actual_returned=bool(struct.unpack_from('I', mapping, 20)[0]), actual_result=struct.unpack_from('q', mapping, 24)[0],
        issuer_core_disabled=bool(struct.unpack_from('I', mapping, 32)[0]),
        worker_core_disabled=bool(struct.unpack_from('I', mapping, 36)[0]),
        issuer_channel_closed=bool(struct.unpack_from('I', mapping, 40)[0]),
        worker_channel_closed=bool(struct.unpack_from('I', mapping, 44)[0]),
        token_length=struct.unpack_from('I', mapping, 48)[0],
        issuer_argv_clean=bool(struct.unpack_from('I', mapping, 52)[0]),
        issuer_env_clean=bool(struct.unpack_from('I', mapping, 56)[0]),
        worker_argv_env_clean=bool(struct.unpack_from('I', mapping, 60)[0]),
        worker_token_erased=bool(struct.unpack_from('I', mapping, 64)[0]),
        issuer_token_erased=bool(struct.unpack_from('I', mapping, 68)[0]))


def run_case(pw, out, name, issuer_mode=0, worker_mode=None):
    out = out / name
    out.mkdir()
    channel = '/pwext_' + uuid.uuid4().hex[:20]
    fd = LIBC.shm_open(channel.encode(), os.O_RDWR | os.O_CREAT | os.O_EXCL, ctypes.c_uint(0o600))
    assert fd >= 0, f'create transient observer failed: errno {ctypes.get_errno()}'
    owner = dict(channel=channel, creator_pid=os.getpid(), exclusive_creation=True, bytes=SIZE,
                 token_bytes_retained=False, cleanup_retained=True)
    recovery = Path(tempfile.mkdtemp(prefix='pw-extension-control-')) / 'owner.json'
    owner.update(recovery_path=str(recovery), case_directory=str(out))
    def save_owner():
        write_json(out / 'channel-owner.json', owner)
        write_json(recovery, owner)
    def retire_owner():
        if not owner['cleanup_retained']:
            (recovery.parent / 'target').unlink(missing_ok=True)
            recovery.unlink()
            recovery.parent.rmdir()
    try:
        save_owner()
        metadata = os.fstat(fd)
        owner.update(mode=stat.S_IMODE(metadata.st_mode), uid=metadata.st_uid)
        assert stat.S_IMODE(metadata.st_mode) == 0o600 and metadata.st_uid == os.getuid(), owner
        os.ftruncate(fd, SIZE)
        mapping = mmap.mmap(fd, SIZE, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ | mmap.PROT_WRITE)
    except BaseException:
        owner['cleanup_retained'] = LIBC.shm_unlink(channel.encode()) != 0
        save_owner()
        retire_owner()
        raise
    finally:
        os.close(fd)
    mapping[:] = b'\0' * SIZE
    struct.pack_into('I', mapping, 0, 0x43545845)
    save_owner()
    launched, cleanup_known = False, False
    try:
        issuer = compile_fixture(out, channel, issuer_mode, True)
        worker = compile_fixture(out, channel, worker_mode, False) if worker_mode is not None else None
        target = recovery.parent / 'target'
        owner['target_path'] = str(target)
        save_owner()
        contents = b'PW boundary witness\n'
        target.write_bytes(contents)
        spec = specimen(target, [[probe('before', target), intervention('consume', 'consume')],
                                 [probe('during', target), intervention('release', 'release')],
                                 [probe('after', target)]])
        spec['_test_overrides'] = dict(issuer_executable_path=str(issuer))
        if worker:
            spec['_test_overrides']['worker_executable_path'] = str(worker)
        request = out / 'specimen.json'
        write_json(request, spec)
        command = [pw, 'run', str(request), '--no-log-capture']
        # Unlike ordinary RunCapture, keep output in memory until comparison
        # with the authority-bearing bytes; a product leak must fail without
        # persisting the leaked token in the failure artifact.
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        launched = True
        try:
            stdout, stderr = child.communicate(timeout=40)
        except subprocess.TimeoutExpired:
            child.kill(); child.communicate(timeout=5)
            raise AssertionError('CLI timeout; observer ownership retained pending child inspection')
        envelope = json.loads(stdout)
        runner = envelope['data']['runner_result']
        declaration, = runner['extensions']
        issuer_record = declaration.get('issuer') or {}
        worker_record = runner.get('runner_subprocess') or {}
        cleanup_known = (issuer_record.get('pid') is None or issuer_record.get('reaped') is True) \
            and (worker_record.get('pid') is None or worker_record.get('reaped') is True)
        observed = observations(mapping)
        length = observed['token_length']
        assert 0 <= length < TOKEN_CAPACITY, 'invalid observer token length'
        token = bytes(mapping[TOKEN_OFFSET:TOKEN_OFFSET + length])
        leaked = bool(token) and (token in stdout or token in stderr or token in request.read_bytes()
            or any(token in os.fsencode(arg) for arg in command)
            or any(token in os.fsencode(value) for value in os.environ.values()))
        observed['captured_output_excludes_token'] = not leaked
        # Pin the detector's sensitivity using this real token in memory only.
        observed['confinement_detector_control'] = bool(token) and token in b'prefix' + token + b'suffix'
        write_json(out / 'observations.json', observed)
        assert not leaked, 'token confinement failure; raw CLI output withheld'
        (out / 'run.json').write_bytes(stdout)
        (out / 'stderr.txt').write_bytes(stderr)
        write_json(out / 'capture.json', dict(argv=command, cli_pid=child.pid, returncode=child.returncode))
        assert cleanup_known, 'unconfirmed native child cleanup; observer ownership retained'
        assert target.read_bytes() == contents, 'independent target bytes changed'
        assert runner.get('test_overrides', {}).get('issuer_executable_path') == str(issuer)
        if worker:
            assert runner['test_overrides']['worker_executable_path'] == str(worker)
        assert consumer.validate(envelope) == [], consumer.validate(envelope)
        assert check_record(envelope) == [], check_record(envelope)
        binary = envelope['data']['specimen']['binaries']['issuer']
        assert binary['path'] == str(issuer)
        assert binary['actual_sha256'] == hashlib.sha256(issuer.read_bytes()).hexdigest()
        assert binary['verification'] == 'mismatch' and binary['baseline_sha256']
        if length:
            assert observed['issuer_argv_clean'] and observed['issuer_env_clean']
            assert observed['issuer_core_disabled'] and observed['issuer_channel_closed']
            assert observed['issuer_token_erased']
            for path in out.rglob('*'):
                if path.is_file():
                    assert token not in path.read_bytes(), 'token found in retained artifact'
        events = runner.get('extension_events', [])
        if issuer_mode == 6:
            assert runner['normalized_outcome'] == 'bad_request'
            assert runner['request_failure']['code'] == 'extension_api_unavailable'
            assert declaration['issuance_status'] == 'native_api_unavailable'
            assert not events and not worker_record
        elif worker_mode in (101, 102, 103, 201, 202, 203):
            which = 0 if worker_mode < 200 else 1
            event = events[which]
            assert runner['normalized_outcome'] == 'runner_failed'
            assert worker_record['term_signal'] == 9 and worker_record['reaped']
            assert observed['operation'] == which + 1
            assert observed['stage'] == {1: 1, 2: 3, 3: 2}[worker_mode % 100]
            assert observed['actual_returned'] == (worker_mode % 100 == 3)
            assert event['call_boundary_observed'] and not event['result_published']
            assert event['status'] == 'unresolved' and event.get('native_result') is None and event.get('errno') is None
            assert observed['worker_core_disabled'] and observed['worker_channel_closed']
            assert runner['steps'][0]['attempt']['result_source'] == 'worker'
            if which:
                assert events[0]['status'] == 'returned' and events[0]['native_result'] != -1
                assert runner['steps'][1]['attempt']['result_source'] == 'worker'
        elif worker_mode == 104 or issuer_mode in (10, 16):
            assert events[0]['status'] == 'returned' and events[0]['native_result'] == -1
            assert events[1]['status'] == 'unavailable' and events[1]['unavailable_reason'] == 'handle_unavailable'
            if issuer_mode == 16:
                assert declaration['issuer']['token_length'] == 16383
                assert declaration['delivery_status'] == 'delivered' and declaration['delivered_bytes'] == 16383
        elif worker_mode == 204:
            assert events[0]['native_result'] != -1
            assert events[1]['status'] == 'returned' and events[1]['native_result'] == -1 and events[1]['errno'] == 5
        elif worker_mode == 105:
            assert declaration['delivery_status'] == 'native_api_unavailable'
            assert all(e['status'] == 'unavailable' and e['unavailable_reason'] == 'native_api_unavailable' for e in events)
        elif issuer_mode:
            expected = {1: 'native_refusal', 2: 'token_oversized', 3: 'token_oversized', 4: 'issuer_result_missing',
                        5: 'issuer_timeout', 7: 'invalid_transport', 8: 'issued', 9: 'issued',
                        11: 'invalid_transport', 12: 'invalid_transport', 13: 'issuer_result_missing',
                        14: 'invalid_transport', 15: 'invalid_transport'}[issuer_mode]
            assert declaration['issuance_status'] == expected, declaration['issuance_status']
            if issuer_mode in (8, 9):
                assert declaration['delivery_status'] == 'malformed_transport'
            assert events[0]['status'] == 'unavailable' and events[0]['unavailable_reason'] == 'token_unavailable'
            assert events[1]['status'] == 'unavailable' and events[1]['unavailable_reason'] == 'handle_unavailable'
        else:
            assert events[0]['native_result'] != -1 and events[1]['native_result'] == 0
            assert observed['worker_argv_env_clean'] and observed['worker_token_erased']
        assert declaration['host_buffer_erased'], 'host did not report clearing its channel'
        return dict(case=name, ok=True, issuer_mode=issuer_mode, worker_mode=worker_mode)
    finally:
        mapping[:] = b'\0' * SIZE
        mapping.close()
        if not launched or cleanup_known:
            assert LIBC.shm_unlink(channel.encode()) == 0, 'observer unlink failed'
            owner['cleanup_retained'] = False
        save_owner()
        retire_owner()


def main():
    pw, directory = sys.argv[1:]
    out = Path(directory).resolve()
    results = []
    cases = [('native', 0, 0)] + [(f'issuer-{mode}', mode, None) for mode in range(1, 17)] \
        + [(f'worker-{mode}', 0, mode) for mode in (101, 102, 103, 104, 105, 201, 202, 203, 204)]
    for name, issuer, worker in cases:
        try:
            results.append(run_case(pw, out, name, issuer, worker))
        except Exception as exc:
            results.append(dict(case=name, ok=False, error=str(exc)))
        write_json(out / 'results.json', results)
    failed = [r['case'] + ': ' + r.get('error', '') for r in results if not r['ok']]
    assert not failed, '\n'.join(failed)
    print(f'{len(results)} native boundary and token-confinement controls passed.')


if __name__ == '__main__':
    main()
