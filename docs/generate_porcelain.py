#!/usr/bin/env python3
"""Generate fixed evidence records; no runtime source inference."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ['runner/Sources/PWRunnerCore/PWPorcelainRecords.swift',
           'controller/src/porcelain_records.rs', 'tests/lib/porcelain_schema.py']
PRIMITIVES = {'String': ('String', 'text'), 'Bool': ('bool', 'bool'),
              'Int': ('i64', 'i64'), 'Int32': ('i32', 'i32'), 'Int64': ('i64', 'i64'),
              'UInt32': ('u32', 'u32'), 'UInt64': ('u64', 'u64'), 'Data': ('Vec<u8>', 'bytes')}


def input_paths(root):
    """Relative read/output inventory for relocated generator and build fixtures."""
    paths = {'docs/porcelain.json', 'docs/generate_porcelain.py', *OUTPUTS}
    try:
        schema = json.loads((Path(root) / 'docs/porcelain.json').read_text())
    except (OSError, ValueError):
        # Discovery does not replace validation: the command diagnoses the input.
        return sorted(paths)
    for record in schema.get('records', []):
        if isinstance(record, dict) and isinstance(record.get('source'), str):
            paths.add(record['source'])
    return sorted(paths)


def markers(record):
    return ('    // BEGIN GENERATED PORCELAIN ' + record['name'],
            '    // END GENERATED PORCELAIN ' + record['name'])


def ownership(root):
    schema = json.loads((root / 'docs/porcelain.json').read_text())
    regions = {}
    for record in schema['records']:
        if 'source' in record:
            # Ownership consumers search literal markers, so the newline is
            # part of the identity (Step must not match StepQuestions).
            regions.setdefault(record['source'], []).append(tuple(marker + '\n' for marker in markers(record)))
    return regions, set(OUTPUTS)


def shape(text):
    if text.endswith('?'):
        return ('optional', shape(text[:-1]))
    if text.startswith('[') and text.endswith(']'):
        inner = text[1:-1]
        if inner.startswith('String: '):
            return ('map', shape(inner[8:]))
        return ('list', shape(inner))
    return text


def rust_type(value):
    if isinstance(value, tuple):
        kind, item = value
        return {'optional': 'Option<{}>', 'list': 'Vec<{}>',
                'map': 'crate::porcelain::OrderedMap<{}>'}[kind].format(rust_type(item))
    return PRIMITIVES.get(value, (value,))[0]


def field_shape(field):
    return shape(field['swift_type'])


def rust_name(field):
    name = 'data' if field.get('projection') == 'base64' else field['name']
    return 'r#' + name if name in ('type', 'ref', 'match', 'loop') else name


def descriptor(value, ids):
    if isinstance(value, tuple):
        return {value[0]: descriptor(value[1], ids)}
    if value in PRIMITIVES:
        return PRIMITIVES[value][1]
    return {'record': ids[value]} if value in ids else {'variant': value}


def validate(schema):
    records = schema['records']
    assert type(schema['version']) is int and schema['version'] == 1
    assert len(records) <= 150, 'record maintenance budget'
    ids = [r['id'] for r in records]
    names = [r['name'] for r in records]
    assert len(set(ids)) == len(ids) and all(type(i) is int and 0 < i < 65536 for i in ids), 'duplicate/invalid record ID'
    assert len(set(names)) == len(names), 'duplicate record name'
    assert all(re.fullmatch(r'[A-Z][A-Za-z0-9_]*', name) and name not in PRIMITIVES for name in names), 'invalid/shadowed record name'
    for record in records:
        fields = record['fields']
        tags = [f['tag'] for f in fields]
        assert tags == sorted(set(tags)) and all(type(i) is int and 0 < i < 65536 for i in tags), 'duplicate/invalid field tag'
        assert len({f['name'] for f in fields}) == len(fields), 'duplicate field name'
        assert len({f['swift_name'] for f in fields}) == len(fields), 'duplicate Swift field name'
        by_field = {f['name']: f for f in fields}
        for dependent, guard in record.get('conditional_null', {}).items():
            assert dependent in by_field and guard in by_field, 'unknown presence field'
            assert by_field[dependent]['swift_type'].endswith('?') and by_field[guard]['swift_type'].endswith('?'), 'presence requires optional fields'
        if record.get('path_forms'):
            assert by_field['input']['swift_type'] == 'String', 'path input must be text'
            assert len(set(record['path_forms'])) == len(record['path_forms']), 'duplicate path form'
            assert all(by_field[name]['swift_type'] == 'String?' for name in record['path_forms']), 'path forms must be optional text'

        for field in fields:
            assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', field['name']) and not field['name'].startswith('__pw_'), 'invalid/reserved field name'
            value = field_shape(field)
            while isinstance(value, tuple):
                value = value[1]
            assert value in PRIMITIVES or value in names or value in schema['variants'], ('unknown type', value)


    known = set(names) | set(PRIMITIVES) | set(schema['variants'])
    for name, cases in schema['variants'].items():
        assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name), 'invalid variant name'
        assert name not in names and name not in PRIMITIVES and cases, 'variant identity'
        assert len({case['name'] for case in cases.values()}) == len(cases), 'duplicate variant case'
        for tag, case in cases.items():
            assert tag.isdecimal() and str(int(tag)) == tag and 0 < int(tag) < 65536, 'invalid variant tag'
            assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', case['name']), 'invalid variant case'
            assert case['type'] in known, 'unknown variant type'
    by_name = {record['name']: record for record in records}
    def depth(value, active):
        if isinstance(value, tuple):
            return (0 if value[0] == 'optional' else 1) + depth(value[1], active)
        if value in PRIMITIVES:
            return 1
        assert value not in active, 'recursive schema is outside this fixed model'
        if value in by_name:
            children = [field_shape(f) for f in by_name[value]['fields'] if not f.get('local_only')]
        else:
            children = [shape(case['type']) for case in schema['variants'][value].values()]
        return 1 + max((depth(child, active | {value}) for child in children), default=0)
    for name in names:
        assert depth(name, set()) <= 32, 'schema exceeds wire depth'
    assert all(root in names for root in schema['roots'].values()), 'unknown root'


def swift(schema, fingerprint):
    lines = ['// Generated by docs/generate_porcelain.py. Edit docs/porcelain.json.', 'import Foundation',
             'enum PWPorcelainSchema {', '    static let fingerprint: [UInt8] = [' + ', '.join(str(n) for n in bytes.fromhex(fingerprint)) + ']', '}']
    for record in schema['records']:
        name = record['name']
        lines += [f'extension {name}: PWPorcelainWritable {{']
        lines += [f'    static let porcelainRecordID: UInt16 = {record["id"]}', '    enum PorcelainTag {']
        for field in record['fields']:
            if not field.get('local_only'):
                lines += [f'        static let {field["name"]}: UInt16 = {field["tag"]}']
        lines += ['    }', '    func porcelainWrite() throws -> Data {', '        var writer = PWPorcelainRecordWriter(Self.porcelainRecordID)']
        for field in record['fields']:
            if field.get('local_only'):
                continue
            expr = field['swift_name']
            lines += [f'        try writer.field(PorcelainTag.{field["name"]}, {expr})']
        lines += ['        return try writer.finish()', '    }', '}']
    return '\n'.join(lines) + '\n'


def rust(schema, fingerprint):
    lines = ['// Generated by docs/generate_porcelain.py. Edit docs/porcelain.json.',
             '#![allow(non_snake_case, dead_code)]',
             'use serde::Serialize;', '#[cfg(test)] use serde::Deserialize;', 'use serde::ser::SerializeMap;',
             'use crate::porcelain::{WireRead, RecordReader};',
             'pub const FINGERPRINT: [u8; 32] = [' + ', '.join(str(n) for n in bytes.fromhex(fingerprint)) + '];']
    for name, cases in schema['variants'].items():
        lines += ['#[derive(Clone, Debug, PartialEq, Serialize)]', '#[cfg_attr(test, derive(Deserialize))]', '#[serde(untagged)]', f'pub enum {name} {{']
        lines += [f'    {case["name"]}({rust_type(shape(case["type"]))}),' for case in cases.values()]
        lines += ['}', f'impl WireRead for {name} {{', '    const KIND: u8 = 9;',
                  '    fn read_payload(data: &[u8], depth: usize, budget: &std::cell::Cell<usize>) -> Result<Self, String> {',
                  '        let (tag, value) = crate::porcelain::variant(data, depth, budget)?;', '        match tag {']
        lines += [f'            {tag} => Ok(Self::{case["name"]}(value.decode()?)),' for tag, case in cases.items()]
        lines += ['            _ => Err("unknown variant".into()),', '        }', '    }', '}']
    for record in schema['records']:
        name = record['name']
        fields = [f for f in record['fields'] if not f.get('local_only')]
        lines += ['#[derive(Clone, Debug, PartialEq)]', '#[cfg_attr(test, derive(Deserialize))]', '#[cfg_attr(test, serde(deny_unknown_fields))]', f'pub struct {name} {{']
        for field in fields:
            if field.get('projection') == 'base64':
                lines += ['    #[cfg_attr(test, serde(rename = "data_base64", deserialize_with = "crate::porcelain::bytes_from_json"))]']
            lines += [f'    pub {rust_name(field)}: {rust_type(field_shape(field))},']
        if record.get('path_forms'):
            lines += ['    #[cfg(test)]', '    #[serde(default)]', '    pub same_as_input: Vec<String>,']
        lines += ['}', f'impl WireRead for {name} {{', '    const KIND: u8 = 6;',
                  '    fn read_payload(data: &[u8], depth: usize, budget: &std::cell::Cell<usize>) -> Result<Self, String> {',
                  f'        let mut __pw_reader = RecordReader::new(data, {record["id"]}, depth, budget)?;']
        for field in fields:
            fs = field_shape(field)
            if isinstance(fs, tuple) and fs[0] == 'optional':
                fs = fs[1]
            lines += [f'        let mut {rust_name(field)}: Option<{rust_type(fs)}> = None;']
        lines += ['        while let Some((__pw_tag, __pw_value)) = __pw_reader.next()? {', '            match __pw_tag {']
        for field in fields:
            read = '__pw_value.bytes()?' if field['swift_type'].rstrip('?') == 'Data' else '__pw_value.decode()?'
            lines += [f'                {field["tag"]} => {rust_name(field)} = Some({read}),']
        lines += ['                _ => return Err("unknown field tag".into()),', '            }', '        }', '        Ok(Self {']
        for field in fields:
            fs = field_shape(field); n = rust_name(field)
            optional = isinstance(fs, tuple) and fs[0] == 'optional'
            lines += [f'            {n},' if optional else f'            {n}: {n}.ok_or("missing {name}.{field["name"]}")?,']
        if record.get('path_forms'):
            lines += ['            #[cfg(test)]', '            same_as_input: Vec::new(),']
        lines += ['        })', '    }', '}', f'impl Serialize for {name} {{',
                  '    fn serialize<S: serde::Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {',
                  '        let mut map = serializer.serialize_map(None)?;']
        if record.get('path_forms'):
            lines += ['        let mut same: Vec<&str> = Vec::new();']
        for field in sorted(fields, key=lambda f: f['name']):
            key=field['name']; n=rust_name(field); fs=field_shape(field)
            expr='&self.'+n
            if field.get('projection')=='base64':
                expr='&crate::porcelain::Base64(&self.'+n+')'
            action=f'map.serialize_entry("{key}", {expr})?;'
            if key in record.get('path_forms', []):
                lines += [f'        let is_same = self.{n}.as_deref() == Some(self.input.as_str());',
                          '        #[cfg(test)]',
                          f'        let is_same = is_same || self.same_as_input.iter().any(|v| v == "{key}");',
                          '        if is_same {',
                          f'            same.push("{key}");', f'        }} else {{ {action} }}']
            elif key in record.get('conditional_null', {}):
                condition=record['conditional_null'][key]
                lines += [f'        if self.{condition}.is_some() {{ {action} }}']
            elif isinstance(fs,tuple) and fs[0]=='optional' and not field.get('json_null'):
                lines += [f'        if self.{n}.is_some() {{ {action} }}']
            else:
                lines += ['        '+action]
        if record.get('path_forms'):
            order = ', '.join('"'+name+'"' for name in record['path_forms'])
            lines += [f'        let order = [{order}];', '        same.sort_by_key(|name| order.iter().position(|v| v == name).unwrap());', '        map.serialize_entry("same_as_input", &same)?;']
        lines += ['        map.end()', '    }', '}']
    return '\n'.join(lines)+'\n'


def python_tables(schema, fingerprint):
    ids={r['name']:r['id'] for r in schema['records']}
    records={}
    for r in schema['records']:
        fields={}
        for f in r['fields']:
            if f.get('local_only'):continue
            fs=field_shape(f);optional=isinstance(fs,tuple) and fs[0]=='optional'
            fields[f['tag']]=dict(name=f['name'],type=descriptor(fs[1] if optional else fs,ids),optional=optional,json_null=f.get('json_null',False))
            if f.get('projection'):fields[f['tag']]['projection']=f['projection']
        records[r['id']]=dict(name=r['name'],fields=fields)
        for key in ('path_forms','conditional_null'):
            if key in r:records[r['id']][key]=r[key]
    variants={name:{int(tag):descriptor(shape(v['type']),ids) for tag,v in cases.items()} for name,cases in schema['variants'].items()}
    return ('# Generated by docs/generate_porcelain.py. Edit docs/porcelain.json.\n'
            +f'SCHEMA_FINGERPRINT = {fingerprint!r}\nRECORDS = {records!r}\n'
            +f'ROOTS = { {k:ids[v] for k,v in schema["roots"].items()}!r}\nVARIANTS = {variants!r}\n')



def wire_identity(schema):
    # Source locations, defaults and prose belong to source provenance. They do
    # not change what a received record means and must not force wire churn.
    ids = {record['name']: record['id'] for record in schema['records']}
    records = []
    for record in schema['records']:
        fields = []
        for field in record['fields']:
            if field.get('local_only'):
                continue
            item = dict(tag=field['tag'], name=field['name'],
                        type=descriptor(field_shape(field), ids),
                        json_null=field.get('json_null', False))
            if field.get('projection'):
                item['projection'] = field['projection']
            fields.append(item)
        item = dict(id=record['id'], name=record['name'], fields=fields)
        for key in ('path_forms', 'conditional_null'):
            if key in record:
                item[key] = record[key]
        records.append(item)
    return dict(version=schema['version'], records=records,
                roots={name: ids[value] for name, value in schema['roots'].items()},
                variants=schema['variants'])


def outputs(root, schema):
    validate(schema)
    fingerprint=hashlib.sha256(json.dumps(wire_identity(schema),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    changes={OUTPUTS[0]:swift(schema,fingerprint),OUTPUTS[1]:rust(schema,fingerprint),OUTPUTS[2]:python_tables(schema,fingerprint)}
    for record in schema['records']:
        if 'source' not in record:continue
        path=record['source'];text=changes.get(path,(root/path).read_text())
        start,end=markers(record)
        assert text.count(start+'\n')==1 and text.count(end+'\n')==1, ('missing field region',record['name'])
        lines=[start]
        for field in record['fields']:
            for comment in field.get('doc',[]):lines.append('    '+comment)
            decl='    '+('var ' if field['mutable'] else 'let ')+field['swift_name']+': '+field['swift_type']
            if 'default' in field:decl+=' = '+field['default']
            lines.append(decl)
        lines.append(end)
        a=text.index(start+'\n');b=text.index(end+'\n',a)+len(end)
        changes[path]=text[:a]+'\n'.join(lines)+text[b:]
    return changes


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate schema key: ' + key)
        result[key] = value
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    try:
        schema=json.loads((ROOT/'docs/porcelain.json').read_text(), object_pairs_hook=unique_object)
        rendered = outputs(ROOT, schema)
        changed = [name for name, content in rendered.items()
                   if not (ROOT / name).exists() or (ROOT / name).read_text() != content]
        if not args.check:
            for name in changed:
                (ROOT / name).write_text(rendered[name])
        if args.check and changed:
            print('stale porcelain output: '+', '.join(changed),file=sys.stderr)
            print('Run tests/lib/python.sh docs/generate_porcelain.py',file=sys.stderr)
            return 1
        print(('checked' if args.check else 'generated')+f' {len(schema["records"])} porcelain records')
        return 0
    except (AssertionError,KeyError,ValueError,OSError,TypeError) as error:
        print('invalid porcelain schema: '+str(error),file=sys.stderr);return 1

if __name__ == '__main__':
    sys.exit(main())
