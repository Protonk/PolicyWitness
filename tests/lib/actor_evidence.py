"""Independent actor authority/setup/equipment evidence checks.

No policy interpretation, native authority call, binary inspection, generated
limit import or production classifier participates in this reader.
"""
import plistlib
import re


def obj(value):
    return value if isinstance(value, dict) else {}


def array(value):
    return value if isinstance(value, list) else []


def integer(value, low=0, high=(1 << 64) - 1):
    return type(value) is int and low <= value <= high


def bounded(value, size):
    return isinstance(value, str) and 0 < len(value.encode('utf-8')) <= size and '\0' not in value


def hexadecimal(value, count):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(count) + '}', value) is not None


WORKER_OPS = ('issue_symbol', 'consume_symbol', 'release_symbol', 'core_limit', 'descriptor_presence',
              'fstat', 'page_size', 'object_size', 'mmap', 'descriptor_close', 'header_binding',
              'terminal_owned_inbound_clear', 'rejected_mapping_munmap')
REGION_OPS = ('shm_open', 'shm_unlink', 'fd_cloexec', 'ftruncate', 'mmap', 'header_initialize',
              'authority_duplicate', 'authority_spawn_dup2', 'close_launch_duplicate',
              'close_original_descriptor', 'shared_clear', 'munmap')
CUSTODY_OPS = ('mmap', 'final_erase', 'munmap')
OPERAND_KEYS = {'slot', 'operation', 'role', 'state', 'native_kind', 'native_rc', 'errno', 'detail', 'value'}


def _scope(value, names, family):
    errors = []
    scope = obj(value)
    operations = array(scope.get('operations'))
    if 'integrity_errors' in scope and (not isinstance(scope['integrity_errors'], list) or len(scope['integrity_errors']) > 16 or any(not bounded(e, 64) for e in scope['integrity_errors']) or scope['integrity_errors'] and scope.get('disposition') in ('ready', 'not_required')):
        errors.append('invalid setup cells cannot establish readiness')
    if not isinstance(scope.get('operations'), list) or len(operations) > len(names):
        errors.append('setup operation capacity or type')
    seen = set()
    for raw in operations:
        op = obj(raw)
        slot = op.get('slot')
        if not integer(slot, 0, len(names) - 1) or slot in seen or op.get('operation') != names[slot]:
            errors.append('setup operation slot or identity')
            continue
        seen.add(slot)
        if not set(op) <= OPERAND_KEYS:
            errors.append('unknown setup operation field')
        cleanup = slot >= {'worker': 11, 'region': 8, 'custody': 1, 'run': 4}[family]
        if op.get('role') != ('cleanup' if cleanup else 'setup') and not (
                family == 'worker' and slot == 9 and op.get('role') == 'cleanup'):
            errors.append('setup operation role')
        state, kind = op.get('state'), op.get('native_kind')
        rc, err = op.get('native_rc'), op.get('errno')
        if op.get('value') is not None and not integer(op['value']):
            errors.append('invalid setup operation value')
        if op.get('detail') is not None and not bounded(op['detail'], 64):
            errors.append('invalid setup detail')
        if state == 'not_attempted':
            if any(op.get(k) is not None for k in ('native_rc', 'errno', 'value')):
                errors.append('unattempted setup operation fabricates result')
            continue
        expected_kind = ('symbol' if op.get('operation', '').endswith('_symbol') else
                         'mapping' if op.get('operation') == 'mmap' else
                         'memory' if op.get('operation') in ('header_initialize', 'shared_clear', 'final_erase', 'terminal_owned_inbound_clear') else
                         'validation' if op.get('operation') in ('descriptor_presence', 'object_size', 'header_binding') else
                         'error_code' if op.get('operation') == 'authority_spawn_dup2' else 'integer')
        if kind != expected_kind:
            errors.append('setup operation native kind')
        if kind == 'integer':
            if state not in ('succeeded', 'failed') or not integer(rc, -(1 << 63), (1 << 63)-1) or (
                    (rc != -1 or not integer(err, 0, (1 << 31)-1)) if state == 'failed' else (rc < 0 or err is not None)):
                errors.append('setup native result or errno')
        elif kind == 'error_code':
            if state not in ('succeeded', 'failed') or not integer(rc, 0, (1 << 31)-1) or (rc == 0) != (state == 'succeeded') or err is not None:
                errors.append('setup error-code result')
        elif kind == 'mapping':
            if state not in ('succeeded', 'failed') or rc is not None or (
                    not integer(err, 0, (1 << 31)-1) if state == 'failed' else err is not None):
                errors.append('setup mapping invents native integer result')
        elif kind in ('symbol', 'validation', 'memory'):
            allowed = {'symbol': ('available', 'unavailable'), 'validation': ('accepted', 'rejected'), 'memory': ('performed',)}[kind]
            if state not in allowed or rc is not None or err is not None:
                errors.append('setup ' + kind + ' invents native result')
        else:
            errors.append('unknown setup native kind')
    primary = scope.get('primary_operation')
    if primary is not None and (not integer(primary) or not any(obj(op).get('slot') == primary and
            obj(op).get('role') == 'setup' and obj(op).get('state') in ('failed', 'rejected') for op in operations)):
        errors.append('setup primary operation lacks independent failure')
    ownership = obj(scope.get('ownership'))
    for key, state in ownership.items():
        erasure = key in ('shared_erasure', 'private_erasure')
        if state not in (('not_present', 'performed', 'withheld_not_quiescent', 'unobserved') if erasure else
                         ('not_acquired', 'held', 'released', 'unresolved')) or not erasure and key not in ('object_name', 'descriptor', 'mapping'):
            errors.append('invalid setup ownership state')
        if state == 'released':
            names_for_reference = {'object_name': ('shm_unlink',), 'mapping': ('munmap', 'rejected_mapping_munmap'),
                                   'descriptor': ('descriptor_close',) if family == 'worker' else ('close_original_descriptor',)}.get(key, ())
            if not any(obj(op).get('operation') in names_for_reference and obj(op).get('state') == 'succeeded' for op in operations):
                errors.append('released setup ownership lacks successful cleanup')
        if erasure and state == 'performed' and not any(obj(op).get('operation') in (
                'shared_clear', 'final_erase', 'terminal_owned_inbound_clear') and obj(op).get('state') == 'performed' for op in operations):
            errors.append('setup erasure lacks performed observation')
    if 'cleanup_reference' in scope:
        reference = obj(scope['cleanup_reference'])
        if family != 'region' or reference.get('kind') != 'posix_shm_name' or not bounded(reference.get('name'), 31) or \
                not reference['name'].isascii() or not reference['name'].startswith('/') or \
                not integer(reference.get('host_pid'), 1, (1 << 31)-1) or not integer(reference.get('session_nonce')) or \
                reference.get('recovery_state') != 'unresolved_manual' or ownership.get('object_name') != 'unresolved' or \
                not any(obj(op).get('operation') == 'shm_open' and obj(op).get('state') == 'succeeded' for op in operations):
            errors.append('unresolved setup cleanup lacks owned creation')
    return errors


def _setup(runner, actors):
    errors = []
    setup = obj(runner.get('authority_setup'))
    host = obj(setup.get('host'))
    errors += _scope(host.get('run'), ('core_limit',), 'run')
    regions, custody, workers = (array(v) for v in (host.get('regions'), host.get('custody'), setup.get('workers')))
    if not setup or any(not isinstance(v, list) for v in (host.get('regions'), host.get('custody'), setup.get('workers'))) or \
            len(regions) > 8 or len(custody) > 32 or len(workers) != len(actors):
        errors.append('authority setup table capacity or type')
    tokens = array(obj(runner.get('resources')).get('tokens'))
    for family, rows, owners, index_key, id_key in (
            ('region', regions, actors, 'actor_index', 'actor_id'),
            ('custody', custody, tokens, 'token_index', 'token_ref'),
            ('worker', workers, actors, 'actor_index', 'actor_id')):
        seen = set()
        for position, raw in enumerate(rows):
            row = obj(raw)
            errors += _scope(row, {'region': REGION_OPS, 'custody': CUSTODY_OPS, 'worker': WORKER_OPS}[family], family)
            index = row.get(index_key)
            if not integer(index, 0, len(owners)-1) or index in seen or row.get(id_key) != obj(owners[index]).get(id_key) or \
                    family == 'worker' and index != position:
                errors.append(family + ' setup owner association')
                continue
            seen.add(index)
            if family == 'worker':
                if type(row.get('required')) is not bool or row.get('publication') not in ('observed', 'not_observed'):
                    errors.append('worker setup publication or applicability')
                if row.get('publication') == 'not_observed':
                    if row.get('disposition') is not None or row.get('primary_operation') is not None:
                        errors.append('unpublished setup decision carries values')
                elif row.get('disposition') not in ('ready', 'not_required', 'terminal_required_failure'):
                    errors.append('worker setup disposition')
                if row.get('disposition') == 'terminal_required_failure' and (
                        row.get('required') is not True or not integer(row.get('primary_operation'))):
                    errors.append('terminal setup refusal lacks required primary failure')
    return errors


def _application(actor, setup):
    assessment = obj(actor.get('application'))
    state, basis = assessment.get('state'), assessment.get('basis')
    mode, applied = actor.get('mode'), actor.get('applied') is True
    sub = obj(actor.get('subprocess'))
    evidence = obj(sub.get('worker_evidence'))
    failure = obj(evidence.get('failure'))
    published = evidence.get('failure_state') == 'published' and all(integer(failure.get(k), 0, (1 << 32)-1) for k in ('operation', 'code', 'native_kind'))
    op, code, kind = failure.get('operation'), failure.get('code'), failure.get('native_kind')
    input_refusal = published and (op == 1 and code in (4, 7, 10, 12) and kind == 0 or op == 2 and code in (2, 3, 9, 13))
    parameter_refusal = published and (op == 1 and code == 5 and kind == 0 or op == 3 and code == 1 and kind == 2 or op == 4 and (code == 1 and kind == 1 or code == 6 and kind == 0))
    compile_refusal = published and op == 5 and code == 1 and kind == 2
    timing_refusal = published and op == 12 and (code == 1 and kind == 1 or code == 14 and kind == 0 or code == 15 and kind == 0 and failure.get('detail') == 1)
    progress = obj(obj(sub.get('worker_evidence')).get('progress'))
    supported = {
        ('not_requested', 'unapplied_declaration'): mode == 'unapplied' and not applied,
        ('not_attempted', 'worker_not_launched'): mode == 'apply' and actor.get('setup_status') in ('launch_refused', 'setup_timeout', 'not_launched') and not applied and actor.get('subprocess') is None and actor.get('launch') is None,
        ('not_attempted', 'terminal_authority_setup_refusal'): mode == 'apply' and setup.get('publication') == 'observed' and setup.get('disposition') == 'terminal_required_failure' and not applied,
        ('not_attempted', 'terminal_input_refusal'): mode == 'apply' and input_refusal and not applied,
        ('not_attempted', 'terminal_parameter_refusal'): mode == 'apply' and parameter_refusal and not applied,
        ('not_attempted', 'terminal_compile_refusal'): mode == 'apply' and compile_refusal and not applied,
        ('not_attempted', 'terminal_timing_refusal'): mode == 'apply' and timing_refusal and not applied,
        ('observed', 'applied_publication'): mode == 'apply' and applied,
        ('observed', 'apply_failure_publication'): mode == 'apply' and published and op == 8 and code == 1 and kind == 1 and integer(failure.get('native_result'), -(1 << 63), (1 << 63)-1) and failure['native_result'] != 0 and not applied,
        ('unobserved', 'apply_call_boundary_without_result'): mode == 'apply' and progress.get('operation') == 8 and progress.get('stage') in (1, 2) and not applied,
        ('unobserved', 'no_eligible_apply_publication'): mode == 'apply' and not applied and not (setup.get('publication') == 'observed' and setup.get('disposition') == 'terminal_required_failure'),
    }
    errors = []
    if set(assessment) != {'state', 'basis'} or not isinstance(state, str) or not isinstance(basis, str) or not supported.get((state, basis), False):
        errors.append('application assessment lacks its eligible source')
    # Independent ordered interpretation: eligibility of a lower-priority pair
    # does not erase a higher-priority publication.
    terminal = setup.get('publication') == 'observed' and setup.get('disposition') == 'terminal_required_failure'
    if mode == 'unapplied':
        expected = ('not_requested', 'unapplied_declaration')
    elif actor.get('launch') is None:
        expected = ('not_attempted', 'worker_not_launched')
    elif applied:
        expected = ('observed', 'applied_publication')
    elif terminal and setup.get('integrity_errors') is None:
        expected = ('not_attempted', 'terminal_authority_setup_refusal')
    elif published and op == 8 and code == 1 and kind == 1 and integer(failure.get('native_result'), -(1 << 63), (1 << 63)-1) and failure['native_result'] != 0:
        expected = ('observed', 'apply_failure_publication')
    elif input_refusal:
        expected = ('not_attempted', 'terminal_input_refusal')
    elif parameter_refusal:
        expected = ('not_attempted', 'terminal_parameter_refusal')
    elif compile_refusal:
        expected = ('not_attempted', 'terminal_compile_refusal')
    elif timing_refusal:
        expected = ('not_attempted', 'terminal_timing_refusal')
    elif progress.get('operation') == 8 and progress.get('stage') in (1, 2):
        expected = ('unobserved', 'apply_call_boundary_without_result')
    else:
        expected = ('unobserved', 'no_eligible_apply_publication')
    if (state, basis) != expected:
        errors.append('application assessment violates source precedence')
    if applied and (mode == 'unapplied' or actor.get('launch') is None or terminal or
                    published and op in (1, 2, 3, 4, 5, 8, 12)):
        errors.append('contradictory application publication')
    if type(actor.get('application_count')) is not int or actor['application_count'] not in (0, 1) or (actor['application_count'] == 1) != applied:
        errors.append('application count contradicts successful publication')
    return errors


def _metadata_fits(values):
    # Independent literal boundary: metadata counts retained text, not JSON
    # escaping, field names, fixed scalars, or the referenced entitlement plist.
    return all(value is None or isinstance(value, str) for value in values) and sum(
        len(value.encode('utf-8')) for value in values if value is not None) <= 32768


def _equipment(runner, actors):
    errors = []
    inventory = obj(runner.get('equipment_inventory'))
    bindings, reads = array(runner.get('equipment_bindings')), array(runner.get('equipment_entitlements'))
    if not inventory or inventory.get('status') not in ('verified', 'refused', 'unobserved') or \
            not isinstance(runner.get('equipment_bindings'), list) or not isinstance(runner.get('equipment_entitlements'), list) or len(bindings) > 4 or len(reads) > 12:
        errors.append('equipment table type or capacity')
    if inventory.get('status') == 'verified' and (not integer(inventory.get('schema_version'), 1, 1) or
            any(not hexadecimal(inventory.get(k), 64) for k in ('sha256', 'worker_identity', 'unsigned_worker_sha256')) or not integer(inventory.get('seal_osstatus'), 0, 0)):
        errors.append('verified equipment inventory lacks sealed identity')
    # Rows are named by table position. A binding is identified by its role and
    # source, a read-back by the binding row or the actor it belongs to.
    def row_at(table, reference):
        return obj(table[reference]) if integer(reference, 0, len(table) - 1) else None
    identities, owners, dictionaries = set(), set(), {}
    for binding in bindings:
        row = obj(binding)
        identity = (row.get('role'), row.get('source'))
        if not all(isinstance(part, str) for part in identity) or identity in identities:
            errors.append('duplicate or invalid equipment binding'); continue
        identities.add(identity)
        fields = ('role', 'source', 'implementation_identity', 'relative_path',
                  'path', 'status', 'reason', 'identifier', 'team_id')
        error = obj(row.get('error'))
        if not _metadata_fits([row.get(k) for k in fields] + [error.get(k) for k in ('operation', 'domain', 'message')]):
            errors.append('equipment binding metadata bound')
    for position, raw in enumerate(reads):
        row = obj(raw)
        binding = row_at(bindings, row.get('binding_ref'))
        if binding is None:
            errors.append('entitlement read-back binding')
        if row.get('source') == 'binding':
            owner = ('binding', row.get('binding_ref')) if binding is not None and row.get('actor_id') is None and \
                integer(binding.get('entitlements_ref'), position, position) else None
        elif row.get('source') == 'execution':
            owner = next((('execution', i) for i, a in enumerate(actors) if obj(a).get('actor_id') == row.get('actor_id')), None)
        else:
            owner = None
        if owner is None:
            errors.append('entitlement read-back actor or identity')
        elif owner in owners:
            errors.append('duplicate equipment read-back')
        else:
            owners.add(owner)
        if row.get('status') == 'observed':
            text = row.get('raw_plist')
            try:
                if not isinstance(text, str) or len(text.encode('utf-8')) > 65_536 or not text.lstrip().startswith(('<?xml', '<plist')):
                    raise ValueError('invalid serialized XML')
                value = plistlib.loads(text.encode('utf-8'))
                if not isinstance(value, dict):
                    raise ValueError('entitlements are not a dictionary')
                dictionaries[position] = value
            except Exception:
                # XML parser failures are malformed evidence, never an observer
                # process failure or permission-shaped native result.
                errors.append('invalid or oversized entitlement plist')
        elif row.get('status') != 'failed' or row.get('raw_plist') is not None:
            errors.append('failed entitlement observation invents plist')
    for position, raw in enumerate(bindings):
        binding = obj(raw)
        role, instrumented = binding.get('role'), binding.get('source') == 'test_override'
        expected = 'Contents/MacOS/pw-probe-runner' + ('-unentitled' if role == 'unentitled' else '')
        if role not in ('selected', 'unentitled') or not bounded(binding.get('path'), 1023) or (
                binding.get('implementation_identity') != 'unverified_fixture' or any(binding.get(k) is not None for k in ('relative_path', 'expected_sha256', 'expected_cdhash')) if instrumented else
                binding.get('source') != 'packaged' or binding.get('implementation_identity') != 'inventory_verified' or binding.get('relative_path') != expected):
            errors.append('equipment role or fixed path association')
        if binding.get('status') == 'bound':
            reference = binding.get('entitlements_ref')
            own = row_at(reads, reference)
            if inventory.get('status') != 'verified' or not hexadecimal(binding.get('sha256'), 64) or not instrumented and binding.get('sha256') != binding.get('expected_sha256') or \
                    not hexadecimal(binding.get('cdhash'), 40) or not instrumented and binding.get('cdhash') != binding.get('expected_cdhash') or \
                    not integer(binding.get('signature_osstatus'), 0, 0) or not instrumented and binding.get('entitlements_match') is not True or \
                    own is None or own.get('source') != 'binding' or not integer(own.get('binding_ref'), position, position) or reference not in dictionaries:
                errors.append('bound equipment lacks inspected identity')
            if role == 'unentitled' and not instrumented and (own is None or dictionaries.get(reference) != {}):
                errors.append('unentitled worker carries entitlements')
        elif binding.get('status') != 'refused':
            errors.append('invalid equipment binding status')
    runtime_failed = False
    for index, raw in enumerate(actors):
        actor = obj(raw)
        equipment = obj(actor.get('equipment'))
        resolved = equipment.get('resolved')
        bound = equipment.get('binding_ref')
        binding = row_at(bindings, bound)
        # The actor names its binding row whenever one exists for its role.
        associated = binding.get('role') == resolved if binding is not None else \
            bound is None and not any(obj(b).get('role') == resolved for b in bindings)
        if resolved not in ('selected', 'unentitled') or not associated or \
                not (equipment.get('requested') is None and resolved == 'selected' or equipment.get('requested') == resolved):
            errors.append('actor equipment selector association')
        binding = binding or {}
        requirements = array(equipment.get('required_entitlements'))
        if not isinstance(equipment.get('required_entitlements'), list) or len(requirements) > 64 or \
                any(not bounded(k, 255) for k in requirements) or len(set(k for k in requirements if isinstance(k, str))) != len(requirements):
            errors.append('invalid actor entitlement requirements')
        static_ref = binding.get('entitlements_ref') if row_at(reads, binding.get('entitlements_ref')) is not None else None
        static = dictionaries.get(static_ref)
        granted = {k for k, v in static.items() if v is True} if isinstance(static, dict) else set()
        missing = [k for k in requirements if isinstance(k, str) and k not in granted]
        if equipment.get('requirements_status') in ('satisfied', 'unsatisfied'):
            if static is None or not isinstance(equipment.get('missing_requirements'), list) or \
                    sorted(equipment['missing_requirements'], key=str) != sorted(missing) or \
                    (equipment['requirements_status'] == 'satisfied') != (not missing):
                errors.append('actor requirements disagree with observed entitlements')
        elif equipment.get('requirements_status') != 'unobserved' or equipment.get('missing_requirements') is not None:
            errors.append('unobserved actor requirements invent result')
        execution = obj(equipment.get('execution'))
        fields = ('status', 'path', 'identifier', 'team_id', 'reason')
        if not _metadata_fits([execution.get(k) for k in fields] + [obj(call).get('operation') for call in array(execution.get('native_observations'))]):
            errors.append('equipment execution metadata bound')
        status = execution.get('status')
        if status not in ('matched', 'mismatched', 'inspection_failed', 'unobserved'):
            errors.append('invalid execution equipment status')
        if status == 'matched':
            read = row_at(reads, execution.get('entitlements_ref'))
            live_ref = execution.get('entitlements_ref') if read is not None else None
            read = read or {}
            if binding.get('status') != 'bound' or equipment.get('requirements_status') != 'satisfied' or execution.get('eligible') is not True or execution.get('reason') is not None or \
                    not integer(execution.get('pid'), 1, (1 << 31)-1) or execution.get('pid') != obj(actor.get('launch')).get('pid') or \
                    any(execution.get(k) != binding.get(k) for k in ('path', 'cdhash', 'identifier', 'team_id')) or \
                    read.get('source') != 'execution' or not integer(read.get('binding_ref'), bound, bound) or read.get('actor_id') != actor.get('actor_id') or \
                    static is None or dictionaries.get(live_ref) != static or \
                    not all(obj(dictionaries.get(live_ref)).get(key) is True for key in requirements if isinstance(key, str)):
                errors.append('execution equipment does not match its owned binding')
            calls = array(execution.get('native_observations'))
            if len(calls) != 4 or any(obj(call).get('operation') != name or obj(call).get('attempted') is not True or not integer(obj(call).get('osstatus'), 0, 0)
                    for call, name in zip(calls, ('guest_code', 'dynamic_validity', 'associated_static_code', 'signing_information'))):
                errors.append('matched execution lacks native inspection results')
        else:
            if execution.get('eligible') is not False:
                errors.append('unmatched equipment permits activation')
            runtime_failed |= isinstance(actor.get('launch'), dict) and status in ('mismatched', 'inspection_failed')
    if runtime_failed and (runner.get('normalized_outcome') == 'finished' or runner.get('preparation_failure') is not None or
            not bounded(obj(runner.get('schedule')).get('cancelled'), 64) or
            any(obj(p.get('ordering')).get('proceed_set') is True or obj(p.get('ordering')).get('proceed_observed') is True or p.get('activation_observation') is not None or p.get('arrival_observed') is not False or p.get('completion_observed') is not False or p.get('validator_subprocess') is not None or p.get('collection_status') != 'not_reached'
                for p in map(obj, array(runner.get('phases'))))):
        errors.append('runtime equipment refusal lost evidence or enabled schedule')
    return errors


def _owned_reap_valid(actor):
    reap, sub = obj(actor.get('owned_reap')), obj(actor.get('subprocess'))
    pid, status = reap.get('pid'), reap.get('raw_status')
    if not integer(pid, 1, (1 << 31)-1) or not integer(status, 0, (1 << 31)-1):
        return False
    # waitpid without stopped/continued flags publishes a terminal exit or
    # signal. Decode independently of the producer's status projection.
    signal = status & 0x7f
    status_matches = (integer(sub.get('exit_code'), 0, 255) and sub.get('exit_code') == ((status >> 8) & 0xff) and sub.get('term_signal') is None) if signal == 0 else \
                     (signal != 0x7f and integer(sub.get('term_signal'), 1, 127) and sub.get('term_signal') == signal and sub.get('exit_code') is None)
    return integer(reap.get('native_rc'), 1, (1 << 31)-1) and reap.get('native_rc') == pid and integer(obj(actor.get('launch')).get('pid'), 1, (1 << 31)-1) and obj(actor.get('launch')).get('pid') == pid and integer(sub.get('pid'), 1, (1 << 31)-1) and sub.get('pid') == pid and \
        sub.get('reaped') is True and status_matches and integer(reap.get('capture_ordinal'), 1) and \
        (reap.get('observed_ns') is None or integer(reap['observed_ns'])) and type(reap.get('ownership_unbroken')) is bool and \
        type(reap.get('departure_requested')) is bool and bounded(reap.get('stage'), 64)


def _gates(runner, actors):
    errors = []
    phases = list(map(obj, array(runner.get('phases'))))
    for actor in map(obj, actors):
        if 'owned_reap' in actor and not _owned_reap_valid(actor):
            errors.append('owned reap disagrees with child identity or wait status')
    for index, phase in enumerate(phases):
        if 'activation_observation' in phase:
            activation = obj(phase['activation_observation'])
            if not set(activation) <= {'capture_ordinal', 'observed_ns'} or not integer(activation.get('capture_ordinal'), 1) or activation.get('observed_ns') is not None and not integer(activation['observed_ns']):
                errors.append('invalid phase activation observation')
        if 'termination_gate' not in phase:
            continue
        gate = obj(phase['termination_gate'])
        source = next((obj(a) for a in actors if obj(a).get('actor_id') == gate.get('source_actor_id')), {})
        final = next((i for i, p in enumerate(phases) if p.get('phase_id') == gate.get('source_final_phase_id')), None)
        if not gate or gate.get('condition') != 'terminated' or not source or gate.get('source_actor_id') == phase.get('actor_id') or \
                final is None or final >= index or phases[final].get('actor_id') != source.get('actor_id') or \
                any(p.get('actor_id') == source.get('actor_id') for p in phases[final+1:]):
            errors.append('termination dependency source or ordering')
        outcome = gate.get('outcome')
        if outcome not in ('not_reached', 'satisfied', 'timed_out', 'ownership_lost', 'clock_unavailable', 'source_unavailable', 'source_departure_requested', 'execution_allowance_exhausted'):
            errors.append('termination gate outcome')
        wait = obj(gate.get('wait'))
        if outcome != 'not_reached' and (not integer(wait.get('budget_ms'), 0, 5000) or type(wait.get('clock_fault')) is not bool or
                wait.get('elapsed_ms') is not None and not integer(wait['elapsed_ms']) or wait.get('stop') != outcome or wait.get('excluded_ms') is not None):
            errors.append('termination gate wait budget or accounting')
        if gate.get('observation') is not None:
            reference, source_reap = obj(gate['observation']), obj(source.get('owned_reap'))
            if set(reference) != {'capture_ordinal'} or not integer(reference.get('capture_ordinal'), 1) or \
                    reference.get('capture_ordinal') != source_reap.get('capture_ordinal') or not _owned_reap_valid(source) or \
                    not integer(gate.get('capture_ordinal'), 1) or not integer(source_reap.get('capture_ordinal'), 1) or source_reap['capture_ordinal'] >= gate['capture_ordinal']:
                errors.append('termination gate observation does not resolve to its source owned reap')
        if outcome == 'satisfied':
            reap = obj(source.get('owned_reap'))
            activation = obj(phases[final].get('activation_observation')) if final is not None else {}
            reference = obj(gate.get('observation'))
            ordinals = (activation.get('capture_ordinal'), reap.get('capture_ordinal'), gate.get('capture_ordinal'))
            order = all(integer(v, 1) for v in ordinals) and ordinals[0] < ordinals[1] < ordinals[2]
            time = integer(activation.get('observed_ns')) and integer(reap.get('observed_ns')) and activation['observed_ns'] <= reap['observed_ns']
            if not _owned_reap_valid(source) or reap.get('ownership_unbroken') is not True or reap.get('departure_requested') is not False or \
                    reap.get('stage') not in ('schedule', 'termination_gate') or set(reference) != {'capture_ordinal'} or \
                    reference.get('capture_ordinal') != reap.get('capture_ordinal') or not order or not time:
                errors.append('satisfied termination gate lacks natural owned reap after final activation')
            if not integer(wait.get('budget_ms'), 1, 5000) or wait.get('clock_fault') is not False or wait.get('native_errno') is not None or \
                    not integer(wait.get('elapsed_ms')) or wait['elapsed_ms'] > wait['budget_ms']:
                errors.append('satisfied termination gate lacks a timely clocked wait')
            dependent = obj(phase.get('activation_observation'))
            if dependent.get('observed_ns') is not None and not (integer(reap.get('observed_ns')) and integer(dependent.get('observed_ns')) and reap['observed_ns'] <= dependent['observed_ns']):
                errors.append('dependent activation precedes owned termination')
        elif gate.get('activation_eligible') is not False or 'activation_observation' in phase or obj(phase.get('ordering')).get('proceed_set') is True or \
                obj(phase.get('ordering')).get('proceed_observed') is True or phase.get('collection_status') != 'not_reached':
            errors.append('failed termination gate enabled collection or release')
        if gate.get('activation_eligible') is True and (outcome != 'satisfied' or not any(
                obj(a).get('actor_id') == phase.get('actor_id') and obj(a).get('setup_status') in ('applied', 'unapplied_declared') and
                obj(obj(obj(a).get('equipment')).get('execution')).get('eligible') is True for a in actors)):
            errors.append('termination gate eligibility lacks independent setup')
    return errors


def preparation_failure_valid(runner):
    failure = obj(runner.get('preparation_failure'))
    pair = (failure.get('stage'), failure.get('code'))
    if pair not in (('resolved_plan', 'inconsistent_assignment'), ('equipment', 'equipment_binding_refused')):
        return False
    actors = array(runner.get('actors'))
    phases = array(runner.get('phases'))
    identities = [identity for p in phases for identity in array(obj(p).get('action_ids'))]
    if runner.get('execution_form') != 'actors' or runner.get('normalized_outcome') != 'runner_failed' or not integer(runner.get('rc'), 1, 1) or not actors or \
            any(obj(a).get('setup_status') != 'launch_refused' or obj(a).get('launch') is not None or obj(a).get('subprocess') is not None for a in actors) or \
            runner.get('steps') != [] or runner.get('extension_events') != [] or runner.get('transfers') != [] or \
            any(array(obj(runner.get('resources')).get(k)) for k in ('tokens', 'deliveries', 'handles')) or \
            obj(obj(obj(runner.get('authority_setup')).get('host')).get('run')).get('disposition') != 'not_attempted' or \
            any(obj(obj(p).get('ordering')).get(k) is True for p in phases for k in ('proceed_set', 'proceed_observed')) or \
            any(obj(p).get('collection_status') != 'not_reached' or obj(p).get('arrival_observed') is not False or
                obj(p).get('completion_observed') is not False for p in phases) or runner.get('request_failure') is not None or \
            any(array(obj(obj(runner.get('authority_setup')).get('host')).get(k)) for k in ('regions', 'custody')):
        return False
    return len(identities) <= 256 and all(bounded(i, 63) for i in identities) and len(set(identities)) == len(identities)


def validate_actor_evidence(runner):
    """Ordinary actor relationship findings; degradation retains these assertions.

    The containing report's degradation form is checked by the general consumer.
    An empty list here on that branch means this rule family is inapplicable.
    """
    if runner.get('reporting_failure') is not None:
        return []
    errors = []
    if 'extensions' in runner:
        errors.append('removed declaration reply field')
    if runner.get('execution_form') != 'actors':
        if runner.get('extension_events') or any(runner.get(k) is not None for k in
                ('authority_setup', 'equipment_inventory', 'equipment_bindings', 'equipment_entitlements', 'preparation_failure')):
            errors.append('ordinary reply carries actor authority evidence')
        return errors
    if 'preparation_failure' in runner and not preparation_failure_valid(runner):
        errors.append('invalid before-launch preparation failure')
    actors = array(runner.get('actors'))
    errors += _setup(runner, actors)
    errors += _equipment(runner, actors)
    workers = array(obj(runner.get('authority_setup')).get('workers'))
    for index, actor in enumerate(actors):
        errors += _application(obj(actor), obj(workers[index]) if index < len(workers) else {})
    errors += _gates(runner, actors)
    phases = array(runner.get('phases'))
    ids = [obj(a).get('actor_id') for a in actors]
    for index, actor in enumerate(actors):
        actor = obj(actor)
        if not bounded(actor.get('actor_id'), 63) or actor.get('index') != index:
            errors.append('actor index or identity conflict')
        declared = [i + 1 for i, p in enumerate(phases) if obj(p).get('actor_id') == actor.get('actor_id')]
        if actor.get('visits') != declared:
            errors.append('actor visits disagree with schedule')
    seen = {}
    for phase in phases:
        phase = obj(phase)
        owner = phase.get('actor_id')
        if not isinstance(owner, str) or owner not in ids:
            errors.append('phase actor is absent')
            continue
        seen[owner] = seen.get(owner, 0) + 1
        if phase.get('actor_visit') != seen[owner]:
            errors.append("phase actor_visit disagrees with that actor's visit order")
        if not bounded(phase.get('phase_id'), 63) or any(not bounded(i, 63) for i in array(phase.get('action_ids'))):
            errors.append('phase/action identity exceeds admitted grammar')
    return errors
