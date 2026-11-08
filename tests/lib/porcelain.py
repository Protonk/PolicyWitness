"""Independent structural reader for retained porcelain wire observations.

Only structural tables are generated. This reader does not call the Swift/Rust
codec or decide witness semantics. It projects admitted records for the existing
Python semantic readers, retaining the received bytes at their capture owner.
"""
import base64

import porcelain_schema

MAX_BYTES = 128 * 1024 * 1024
MAX_DEPTH = 32
KINDS = {'bool': 1, 'i32': 2, 'i64': 2, 'u32': 3, 'u64': 3,
         'text': 4, 'bytes': 5, 'record': 6, 'list': 7, 'map': 8, 'variant': 9}


class Reader:
    def __init__(self, data, records):
        self.data = memoryview(data)
        self.records = records

    def number(self, at, end, width):
        if at + width > end:
            raise ValueError('short integer')
        return int.from_bytes(self.data[at:at + width], 'little'), at + width

    def value(self, at, end, descriptor, depth=0):
        if depth >= MAX_DEPTH:
            raise ValueError('porcelain depth limit')
        if at + 5 > end:
            raise ValueError('short value header')
        kind = self.data[at]
        length, start = self.number(at + 1, end, 4)
        stop = start + length
        if stop > end:
            raise ValueError('short value payload')
        shape = descriptor if isinstance(descriptor, str) else next(iter(descriptor))
        if kind != KINDS[shape]:
            raise ValueError('wrong value kind for ' + shape)
        if shape == 'bool':
            if length != 1 or self.data[start] not in (0, 1):
                raise ValueError('invalid bool')
            result = bool(self.data[start])
        elif shape in ('i32', 'i64', 'u32', 'u64'):
            if length != 8:
                raise ValueError('wrong integer width')
            result = int.from_bytes(self.data[start:stop], 'little', signed=shape.startswith('i'))
            bits = int(shape[1:])
            low = -(1 << (bits - 1)) if shape.startswith('i') else 0
            high = (1 << (bits - (shape.startswith('i')))) - 1
            if not low <= result <= high:
                raise ValueError('integer outside declared range')
        elif shape == 'text':
            try:
                result = bytes(self.data[start:stop]).decode('utf-8', errors='strict')
            except UnicodeDecodeError as error:
                raise ValueError('invalid UTF-8') from error
        elif shape == 'bytes':
            result = base64.b64encode(self.data[start:stop]).decode('ascii')
        elif shape == 'record':
            ident, cursor = self.number(start, stop, 2)
            if ident != descriptor['record'] or ident not in self.records:
                raise ValueError('unknown or unexpected record identity')
            fields = self.records[ident]['fields']
            result, seen, previous = {}, set(), 0
            while cursor < stop:
                tag, cursor = self.number(cursor, stop, 2)
                if tag <= previous or tag not in fields:
                    raise ValueError('unknown, duplicate or unordered field tag')
                previous = tag
                field = fields[tag]
                result[field['name']], cursor = self.value(cursor, stop, field['type'], depth + 1)
                seen.add(tag)
            for tag, field in fields.items():
                if tag not in seen:
                    if not field['optional']:
                        raise ValueError('missing required field ' + field['name'])
                    if field.get('json_null', False):
                        result[field['name']] = None
            meta = self.records[ident]
            if meta.get('path_forms'):
                same = []
                for name in meta['path_forms']:
                    if result.get(name) is not None and result[name].encode('utf-8') == result['input'].encode('utf-8'):
                        same.append(name)
                        del result[name]
                    elif name not in result:
                        result[name] = None
                result['same_as_input'] = same
            for name, condition in meta.get('conditional_null', {}).items():
                if result.get(condition) is None:
                    result.pop(name, None)
                elif name not in result:
                    result[name] = None
        elif shape in ('list', 'map'):
            count, cursor = self.number(start, stop, 4)
            minimum = 5 if shape == 'list' else 10
            if count > (stop - cursor) // minimum:
                raise ValueError('collection count exceeds available bytes')
            result = [] if shape == 'list' else {}
            previous = None
            for _ in range(count):
                if shape == 'map':
                    key, cursor = self.value(cursor, stop, 'text', depth + 1)
                    encoded = key.encode('utf-8')
                    if previous is not None and encoded <= previous:
                        raise ValueError('duplicate or unordered map key')
                    previous = encoded
                item, cursor = self.value(cursor, stop, descriptor[shape], depth + 1)
                if shape == 'list':
                    result.append(item)
                else:
                    result[key] = item
            if cursor != stop:
                raise ValueError('trailing collection payload')
        elif shape == 'variant':
            case, cursor = self.number(start, stop, 2)
            if descriptor['variant'] != 'PWDispositionValue':
                raise ValueError('unknown variant')
            if case == 1:
                alternative = 'i64'
            elif case == 2:
                matches = [ident for ident, record in self.records.items()
                           if record['name'] == 'PWRunnerTerminationRequest']
                if len(matches) != 1:
                    raise ValueError('unknown termination record')
                alternative = {'record': matches[0]}
            else:
                raise ValueError('unknown variant case')
            result, cursor = self.value(cursor, stop, alternative, depth + 1)
            if cursor != stop:
                raise ValueError('trailing variant payload')
        else:
            raise ValueError('unknown schema descriptor')
        return result, stop


def decode(data, expected_root='reply'):
    """Read one complete binary document, rejecting stale schema and bad structure."""
    if len(data) > MAX_BYTES:
        raise ValueError('porcelain input exceeds byte limit')
    if len(data) < 36 or data[:4] != b'PWP1':
        raise ValueError('wrong porcelain magic or short header')
    if data[4:36] != bytes.fromhex(porcelain_schema.SCHEMA_FINGERPRINT):
        raise ValueError('porcelain schema fingerprint mismatch')
    root = porcelain_schema.ROOTS[expected_root]
    value, end = Reader(data, porcelain_schema.RECORDS).value(36, len(data), {'record': root})
    if end != len(data):
        raise ValueError('trailing porcelain bytes')
    return value
