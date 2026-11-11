"""Join contract field nodes to the repository's public JSON definitions.

The tree owns meanings, request applicability, and the shapes authored directly
at dynamic JSON call sites. These imports supply names, types and serialization
facts. Source extraction deliberately accepts the forms used by these owners;
a changed form must acquire an explicit reader before it can supply facts.
"""
from copy import deepcopy
from pathlib import Path
import json
import re

RUST_INPUTS = (
    'controller/src/json_contract.rs', 'controller/src/run_flow.rs',
    'controller/src/dossier.rs', 'controller/src/evidence.rs',
    'controller/src/runner_select.rs', 'controller/src/runner_manager.rs',
    'controller/src/runner_commands.rs', 'controller/src/runner_client.rs',
    'controller/src/policy_check.rs', 'controller/src/utils.rs',
    'controller/src/sbpl_imports.rs', 'controller/src/request_patch.rs',
    'controller/src/porcelain_admission.rs', 'controller/src/bin/sbpl-check.rs',
)
SHAPE_INPUTS = ('tests/fixtures/contract/envelope_shape.json',)
# Public entry records whose declarations were traced to their producers or
# decoders. Dynamic json! payloads and controller selector fields are authored
# in the contract tree, with their own source/check owners.
PUBLIC_ROOTS = {
    'request': 'PWRunnerRunSpec',
    'reservation': 'PWRunnerReservationRequest',
    'control': 'PWRunnerControlReply',
    'equipment': 'ActorEquipmentManifest',
    'envelope': 'rust.RunEnvelope',
    'result': 'rust.JsonResult',
    'helper_envelope': 'rust.HelperEnvelope',
    'helper_request': 'rust.CheckRequest',
    'runner_install': 'rust.RunnerInstallData',
    'runner_verify': 'rust.RunnerVerifyData',
    'runner_validate': 'rust.RunnerValidateData',
    'runner_not_found': 'rust.RunnerNotFoundData',
    'runner_registry': 'rust.RunnerRegistry',
    'runner_record': 'rust.RunnerRecord',
    'runner_cleanup': 'rust.CleanupReport',
    'runner_plist': 'rust.PlistObservation',
}
SCALARS = {'String', 'Bool', 'Int', 'Int32', 'Int64', 'UInt32', 'UInt64',
           'Number', 'Data', 'JSON'}


def _swift_paths(root):
    return sorted(p.relative_to(root).as_posix()
                  for p in (root / 'runner/Sources/PWRunnerCore').glob('*.swift'))


def input_paths(root):
    return sorted({'docs/contract/record_definitions.py', 'docs/porcelain.json',
                   'docs/generate_porcelain.py', *RUST_INPUTS, *SHAPE_INPUTS,
                   *_swift_paths(Path(root))})


def _without_comments(text):
    # These declaration owners use line comments, including doc comments.
    return re.sub(r'//[^\n]*', '', text)


def _block(text, opening):
    """Return a brace-delimited body, ignoring strings and comments."""
    tokens = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\]|\\.)*"|[{}]', re.S)
    depth = 0
    for match in tokens.finditer(text, opening):
        if match[0] == '{':
            depth += 1
        elif match[0] == '}':
            depth -= 1
            if depth == 0:
                return text[opening + 1:match.start()]
    raise ValueError('unterminated imported declaration')


def _type_base(value):
    value = value.removesuffix('?')
    if value.startswith('[String: ') and value.endswith(']'):
        return _type_base(value[9:-1])
    if value.startswith('[') and value.endswith(']'):
        return _type_base(value[1:-1])
    return value


def rust_type(text, scalars=(), known=()):
    text = re.sub(r"^&(?:'[a-z_]+\s+)?", '', text.strip())
    if text.startswith('Option<') and text.endswith('>'):
        return rust_type(text[7:-1], scalars, known) + '?'
    if text.startswith('Vec<') and text.endswith('>'):
        return '[' + rust_type(text[4:-1], scalars, known) + ']'
    if text.startswith(('BTreeMap<', 'HashMap<')) and text.endswith('>'):
        key, value = text[text.index('<') + 1:-1].split(',', 1)
        if rust_type(key, scalars, known) != 'String':
            raise ValueError(f'unsupported JSON map key type {key}')
        return '[String: ' + rust_type(value, scalars, known) + ']'
    if text in {'String', 'str', 'PathBuf'} or text.split('::')[-1] in scalars:
        return 'String'
    if text == 'bool':
        return 'Bool'
    if re.fullmatch(r'[ui](?:8|16|32|64|128|size)', text):
        return 'UInt64' if text.startswith('u') else 'Int64'
    if text in {'Value', 'serde_json::Value', 'T'}:
        return 'JSON'
    name = text.split('::')[-1]
    return name if name in known else 'rust.' + name


def _serde(attrs, allowed, context):
    values = {}
    for attr in re.findall(r'#\[serde\(([^\n]*)\)\]', attrs):
        for item in re.split(r',\s*(?=[a-z_]+(?:\s*=|\s*$|\s*,))', attr):
            match = re.fullmatch(r'\s*([a-z_]+)(?:\s*=\s*"([^"\\]*)")?\s*', item)
            if not match or match[1] not in allowed:
                raise ValueError(f'{context}: unsupported serde attribute {item!r}')
            values[match[1]] = match[2] if match[2] is not None else True
    return values


def _rust_records(read, known):
    records, scalar_types, texts = {}, {'ReplyError'}, {p: read(p) for p in RUST_INPUTS}
    enum_pattern = re.compile(
        r'((?:^#\[[^\n]*\]\s*\n)+)(?:pub(?:\([^)]*\))? )?enum (\w+)\s*\{', re.M)
    for path, text in texts.items():
        for match in enum_pattern.finditer(text):
            if not re.search(r'\bSerialize\b', match[1]) or '#[cfg(test)]' in match[1]:
                continue
            attrs = _serde(match[1], {'rename_all', 'untagged'}, path + ':' + match[2])
            if attrs.get('untagged'):
                continue
            body = _without_comments(_block(text, match.end() - 1))
            for variant_attrs in re.findall(r'#\[serde\([^\n]*\)\]', body):
                _serde(variant_attrs, {'alias', 'rename'}, path + ':' + match[2])
            body = re.sub(r'#\[(?:serde\([^\n]*\)|default)\]', '', body)
            if not re.fullmatch(r'(?:\s*\w+\s*,)+\s*', body):
                raise ValueError(f'{path}: unsupported serializable enum {match[2]}')
            scalar_types.add(match[2])
    reply_text = texts['controller/src/runner_client.rs']
    reply_serializer = re.search(r'impl Serialize for ReplyError\s*\{', reply_text)
    if not reply_serializer or not re.search(
            r'\{\s*serializer\.serialize_str\(&self\.message\)\s*\}',
            _block(reply_text, reply_serializer.end() - 1)):
        raise ValueError('ReplyError string projection needs review')

    pattern = re.compile(
        r'((?:^#\[[^\n]*\]\s*\n)+)(?:pub(?:\([^)]*\))? )?struct (\w+)'
        r'(?:<[^{}]+>)?\s*\{', re.M)
    member_pattern = re.compile(
        r'((?:\s*#\[[^\n]*\])*)\s*(?:pub(?:\([^)]*\))?\s+)?'
        r'(\w+)\s*:\s*([^\n]+),')
    for path, text in texts.items():
        for match in pattern.finditer(text):
            input_only = path.endswith('/sbpl-check.rs') and match[2] in {'CheckRequest', 'CheckPolicy'}
            if (not re.search(r'\bSerialize\b', match[1]) and not input_only) or '#[cfg(test)]' in match[1]:
                continue
            name = 'rust.' + match[2]
            if input_only and not re.search(r'\bDeserialize\b', match[1]):
                raise ValueError(f'{name}: expected a derived input definition')
            _serde(match[1], {'deny_unknown_fields'}, name)
            body = _without_comments(_block(text, match.end() - 1))
            fields, flattened, end = {}, [], 0
            for member in member_pattern.finditer(body):
                if body[end:member.start()].strip():
                    raise ValueError(f'{name}: unrecognized field declaration')
                end = member.end()
                attrs, key, native = member.groups()
                if re.sub(r'#\[serde\([^\n]*\)\]', '', attrs).strip():
                    raise ValueError(f'{name}.{key}: conditional field attributes need review')
                settings = _serde(attrs, {'skip', 'skip_serializing', 'flatten', 'rename',
                                          'default', 'skip_serializing_if'}, name + '.' + key)
                if settings.get('skip') or settings.get('skip_serializing'):
                    continue
                value = rust_type(native, scalar_types, known)
                if settings.get('flatten'):
                    if value.endswith('?') or set(settings) != {'flatten'}:
                        raise ValueError(f'{name}.{key}: conditional flatten needs review')
                    flattened.append(value)
                    continue
                key = settings.get('rename', key)
                if key in fields:
                    raise ValueError(f'{name}: duplicate JSON field {key}')
                omission = settings.get('skip_serializing_if')
                expected = {'Option::is_none': value.endswith('?'),
                            'String::is_empty': value == 'String',
                            'Vec::is_empty': value.startswith('[') and not value.startswith('[String: ')}
                if omission and not expected.get(omission):
                    raise ValueError(f'{name}.{key}: unsupported omission {omission}')
                fields[key] = dict(name=key, swift_type=value, native_type=native,
                    optional=value.endswith('?'), json_null=value.endswith('?') and not omission,
                    omission=omission, source=path, declared_in=name)
            if body[end:].strip() or not fields and not flattened:
                raise ValueError(f'{path}: incomplete field collection for {name}')
            if name in records:
                raise ValueError(f'duplicate imported Rust record {name}')
            records[name] = dict(name=name, source=path, fields=fields,
                                 flattened=flattened, input=input_only)
    active, done = set(), set()

    def flatten(name):
        if name in done:
            return
        record = records[name]
        if name in active:
            raise ValueError(f'cyclic flattened record {name}')
        active.add(name)
        for target in record.pop('flattened', []):
            if target.startswith('[String: '):
                record['open'] = True
                record['additional_type'] = target[9:-1]
                continue
            if target not in records:
                raise ValueError(f'{name}: unknown flattened type {target}')
            flatten(target)
            overlap = record['fields'].keys() & records[target]['fields'].keys()
            if overlap:
                raise ValueError(f'{name}: colliding flattened fields {sorted(overlap)}')
            record['fields'].update(deepcopy(records[target]['fields']))
            if records[target].get('open'):
                record['open'] = True
                record['additional_type'] = records[target]['additional_type']
        active.remove(name)
        done.add(name)

    for name in records:
        flatten(name)
    # Both current untagged enums are deliberately read as alternatives. An
    # alternative's fields never become obligations on all other alternatives.
    for path, enum_name in (
            ('controller/src/run_flow.rs', 'RequestFailureProjection'),
            ('controller/src/runner_client.rs', 'TransportCapture')):
        matches = [m for m in enum_pattern.finditer(texts[path]) if m[2] == enum_name]
        if len(matches) != 1 or not _serde(matches[0][1], {'untagged'}, enum_name).get('untagged'):
            raise ValueError(f'{enum_name}: expected one untagged enum')
        body = _without_comments(_block(texts[path], matches[0].end() - 1))
        variants = {}
        if enum_name == 'TransportCapture':
            # The retained-byte projection is a custom serializer. Check its
            # exact owner instead of treating its Vec<u8> as a JSON array.
            rejected = re.search(r'Rejected\s*\{\s*format:\s*&\x27static str,\s*'
                r'#\[serde\(serialize_with = "serialize_rejected_bytes"\)\]\s*'
                r'data_base64:\s*Vec<u8>,\s*\},', body)
            serializer = re.search(r'fn serialize_rejected_bytes[^{}]*\{', texts[path])
            if not rejected or not serializer or _block(texts[path], serializer.end() - 1).strip() != 'crate::porcelain::Base64(bytes).serialize(serializer)':
                raise ValueError('TransportCapture rejected-byte projection needs review')
            rejected_name = 'rust.TransportCapture.Rejected'
            records[rejected_name] = dict(name=rejected_name, source=path, input=False,
                fields={key: dict(name=key, swift_type='String', optional=False, json_null=False,
                                 **({'projection': 'base64'} if key == 'data_base64' else {}))
                        for key in ('format', 'data_base64')})
            variants['Rejected'] = rejected_name
            body = body[:rejected.start()] + body[rejected.end():]
        for case in re.finditer(r'(\w+)\(([^()]+)\),', body):
            native = case[2]
            if native == 'Capture':
                if not re.search(r'PWRunnerClientCapture\s+as\s+Capture\b', texts[path]):
                    raise ValueError('TransportCapture typed alias needs review')
                native = 'PWRunnerClientCapture'
            variants[case[1]] = rust_type(native, scalar_types, known)
        if re.sub(r'(\w+)\(([^()]+)\),', '', body).strip() or not variants:
            raise ValueError(f'{enum_name}: unsupported untagged alternative')
        name = 'rust.' + enum_name
        records[name] = dict(name=name, source=path, fields={}, variants=variants, input=False)
    return records


def _request_records(read, swift_paths, known):
    records = {}
    for path in swift_paths:
        text = read(path)
        declarations = list(re.finditer(
            r'^\s*(?:(?:private|public|internal) )?(?:struct|enum) (\w+)[^{\n]*\{', text, re.M))
        for match in re.finditer(r'enum CodingKeys: String, CodingKey, CaseIterable \{(.*?)\}', text, re.S):
            enclosing = [d for d in declarations if d.start() < match.start() and d[1] != 'CodingKeys'
                         and match.start() < d.end() + len(_block(text, d.end() - 1))]
            if not enclosing:
                raise ValueError(f'{path}: CodingKeys has no enclosing declaration')
            declaration = enclosing[-1]
            name = declaration[1]
            if name == 'Worker' and enclosing[0][1] == 'ActorEquipmentManifest':
                name = 'ActorEquipmentManifest.Worker'
            body = _block(text, declaration.end() - 1)
            prefix = text[declaration.end():match.start()]
            properties = dict(re.findall(
                r'^\s+(?:(?:private|public|internal) )?(?:var|let) (\w+):\s*([^\n={]+)', prefix, re.M))
            fields = {}
            for case in re.findall(r'\bcase\s+([^;\n}]+)', match[1]):
                for item in case.split(','):
                    parsed = re.fullmatch(r'\s*(\w+)(?:\s*=\s*("(?:[^"\\]|\\.)*"))?\s*', item)
                    if not parsed:
                        raise ValueError(f'{path}: unsupported CodingKeys declaration {item!r}')
                    prop, key = parsed[1], json.loads(parsed[2]) if parsed[2] else parsed[1]
                    if prop not in properties:
                        raise ValueError(f'{path}: missing declared type for {name}.{key}')
                    native = properties[prop].strip()
                    if name in known:
                        prior = known[name]['fields'].get(key)
                        if prior is None or prior['swift_type'] != native:
                            raise ValueError(f'{name}.{key}: CodingKeys and porcelain definition disagree')
                        fields[key] = prior
                        continue
                    decoded = re.findall(r'\.decode(?:IfPresent)?\(([^()]+)\.self,\s*forKey:\s*\.' + prop + r'\)', body)
                    if len(set(decoded)) != 1:
                        raise ValueError(f'{name}.{key}: expected one explicit decoded JSON type')
                    value = decoded[0].strip()
                    if name == 'ActorEquipmentManifest' and value == '[Worker]':
                        value = '[ActorEquipmentManifest.Worker]'
                    # This captures native optional storage, not admission or
                    # missing/null applicability; those remain tree obligations.
                    optional = native.endswith('?') or bool(re.search(
                        r'\.decodeIfPresent\([^()]+\.self,\s*forKey:\s*\.' + prop + r'\)', body))
                    fields[key] = dict(name=key, swift_type=value + ('?' if optional else ''),
                        native_type=native, optional=optional, json_null=False, source=path)
                    if name == 'ActorEquipmentManifest.Worker' and key == 'team_id':
                        presence_guard = re.search(
                            r'guard\s+c\.contains\(\.team_id\)\s+else\s*\{\s*'
                            r'throw\s+ActorEquipmentProblem\("missing team_id"\)\s*\}', body)
                        nullable_decode = re.search(
                            r'team_id\s*=\s*try\s+c\.decodeIfPresent\('
                            r'String\.self,\s*forKey:\s*\.team_id\)', body)
                        if (not presence_guard or not nullable_decode or native != 'String?'
                                or presence_guard.end() > nullable_decode.start()):
                            raise ValueError(f'{name}.{key}: required-key nullable decoder needs review')
                        fields[key].update(required_key=True, json_null=True)
            if name in known:
                if fields.keys() != known[name]['fields'].keys():
                    raise ValueError(f'{name}: CodingKeys and porcelain field sets disagree')
                known[name]['input_source'] = path
                continue
            if name in records:
                raise ValueError(f'duplicate imported Swift record {name}')
            records[name] = dict(name=name, source=path, fields=fields,
                                 input=name != 'PWRunnerControlReply')
            if name == 'PWRunnerControlReply' and re.search(r'func encode\(to ', body):
                raise ValueError('PWRunnerControlReply custom encoding needs review')
    path = 'runner/Sources/PWRunnerCore/PWRunnerRequest.swift'
    text = read(path)
    declaration = re.search(r'enum PWRunnerPhaseAction: Codable\s*\{', text)
    if not declaration:
        raise ValueError('missing PWRunnerPhaseAction definition')
    body = _block(text, declaration.end() - 1)
    variants = {}
    for case_text in re.findall(r'^    case ([^\n]+)', body, re.M):
        case = re.fullmatch(r'(\w+)\((\w+)\)', case_text.strip())
        if not case or case[1] in variants:
            raise ValueError('PWRunnerPhaseAction alternative needs review')
        variants[case[1]] = case[2]
    for case, target in variants.items():
        if (not re.search(r'self = \.' + case + r'\(try ' + target + r'\(from: decoder\)\)', body)
                or not re.search(r'case \.' + case + r'\(let value\): try value\.encode\(to: encoder\)', body)):
            raise ValueError('PWRunnerPhaseAction forwarding representation needs review')
    if not variants:
        raise ValueError('missing PWRunnerPhaseAction alternatives')
    records['PWRunnerPhaseAction'] = dict(name='PWRunnerPhaseAction', source=path,
        fields={}, variants=variants, input=True)
    return records


def _porcelain_records(schema):
    records = {}
    for row in schema['records']:
        fields = {}
        for field in row['fields']:
            if field.get('local_only'):
                continue
            value = dict(field, optional=field['swift_type'].endswith('?'),
                         json_null=bool(field.get('json_null', False)))
            if field['name'] in row.get('path_forms', []):
                value.update(json_null=True, omission='same_as_input')
            if field['name'] in row.get('conditional_null', {}):
                value.update(json_null=True,
                    conditional_presence=row['conditional_null'][field['name']])
            fields[field['name']] = value
        if row.get('path_forms'):
            fields['same_as_input'] = dict(name='same_as_input', swift_type='[String]',
                optional=False, json_null=False, derived=True,
                source='docs/generate_porcelain.py')
        records[row['name']] = dict(row, fields=fields, input=False,
                                   definition_source='docs/porcelain.json')
    for name, cases in schema.get('variants', {}).items():
        records[name] = dict(name=name, source='docs/porcelain.json', input=False,
            fields={}, variants={case['name']: case['type'] for case in cases.values()})
    return records


def _reachable(records, aliases):
    selected = set()

    def visit(value):
        name = _type_base(value)
        if name in SCALARS or name in selected:
            return
        if name not in records:
            raise ValueError(f'public field references unresolved type {name}')
        selected.add(name)
        for field in records[name]['fields'].values():
            if not field.get('projection'):
                visit(field['swift_type'])
        for target in records[name].get('variants', {}).values():
            visit(target)
        if records[name].get('additional_type'):
            visit(records[name]['additional_type'])

    for name in aliases.values():
        visit(name)
    return {name: dict(records[name], coverage_required=True) for name in sorted(selected)}


def _check_shape(read, records):
    """Check overlapping observed keys/types; a golden is not an admission schema.

    Opaque JSON subtrees and untagged unions retain their authored interpretation.
    Shared typed records are reused, rather than creating path-specific copies.
    """
    shapes = json.loads(read(SHAPE_INPUTS[0]))['shape']
    observed = {'envelope': 'rust.RunEnvelope'}
    for path in sorted(shapes, key=lambda p: (p.count('.'), p)):
        name = observed.get(path)
        if name is None:
            continue
        record = records[name]
        if record.get('variants'):
            continue
        record.setdefault('shape_paths', []).append(path)
        for key, kind in shapes[path].items():
            if kind not in {'string', 'number', 'boolean', 'object', 'array', 'null'}:
                raise ValueError(f'{SHAPE_INPUTS[0]}: unknown shape type {kind}')
            field = record['fields'].get(key)
            if field is None:
                if record.get('open'):
                    continue
                raise ValueError(f'{SHAPE_INPUTS[0]}: {path}.{key} has no declared field')
            raw = field['swift_type'].removesuffix('?')
            base = _type_base(raw)
            if base == 'JSON' or base in records and records[base].get('variants'):
                continue
            expected = ('string' if field.get('projection') or raw == 'String' else
                        'boolean' if raw == 'Bool' else
                        'array' if raw.startswith('[') and not raw.startswith('[String: ') else
                        'object' if raw.startswith('[String: ') or base in records else
                        'number' if raw in SCALARS - {'Data', 'JSON'} else None)
            if kind != expected and not (kind == 'null' and field.get('json_null')):
                raise ValueError(f'{SHAPE_INPUTS[0]}: {path}.{key} is {kind}, declared {expected}')
            child = path + '.' + key + ('[]' if expected == 'array' else '')
            if base in records and not raw.startswith('[String: '):
                observed[child] = base


def load(root, read=None, swift_paths=None):
    root = Path(root)
    if read is not None and swift_paths is None:
        raise ValueError('a supplied tree reader requires its own swift_paths')
    read = read or (lambda path: (root / path).read_text())
    swift_paths = _swift_paths(root) if swift_paths is None else sorted(swift_paths)
    schema = json.loads(read('docs/porcelain.json'))
    records = _porcelain_records(schema)
    records.update(_request_records(read, swift_paths, records))
    records.update(_rust_records(read, records))
    for name, payload in (('rust.RunEnvelope', 'rust.RunData'),
                          ('rust.HelperEnvelope', 'rust.CheckData')):
        records[name] = deepcopy(records['rust.Envelope'])
        records[name].update(name=name, template='rust.Envelope', payload=payload)
        records[name]['fields']['data'].update(swift_type=payload)
    aliases = dict(schema['roots'], **PUBLIC_ROOTS)
    records = _reachable(records, aliases)
    _check_shape(read, records)
    return records, aliases


def field_type(field):
    """Public JSON type, retaining names for resolvable records and unions."""
    raw = field['swift_type'].removesuffix('?')
    if field.get('projection'):
        return 'string (' + field['projection'] + ')'
    if raw.startswith('[String: '):
        return 'object (string keys)'
    if raw.startswith('['):
        return 'array of ' + field_type(dict(swift_type=raw[1:-1]))
    return {'String': 'string', 'Bool': 'boolean', 'Int': 'integer',
            'Int32': 'integer', 'Int64': 'integer', 'UInt32': 'integer',
            'UInt64': 'integer', 'Number': 'number', 'Data': 'bytes',
            'JSON': 'JSON value'}.get(raw, raw)


def field_presence(record, field):
    if record.get('input'):
        if field.get('required_key'):
            return 'required; may be null' if field.get('json_null') else 'required'
        return 'as defined below'
    if field.get('conditional_presence'):
        return 'present when ' + field['conditional_presence'] + ' has a value; may be null'
    omission = field.get('omission')
    if omission == 'same_as_input':
        return 'omitted when named in same_as_input; otherwise present, possibly null'
    if omission in {'String::is_empty', 'Vec::is_empty'}:
        return 'omitted when empty'
    if not field.get('optional'):
        return 'required'
    return 'null when absent' if field.get('json_null', False) else 'omitted when absent'
