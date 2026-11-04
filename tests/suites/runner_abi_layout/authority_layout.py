"""Compile-observed authority region geometry against the Swift mirror."""
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
source = (root / 'runner/Sources/PWRunnerCore/AuthorityCustody.swift').read_text()
block = re.search(r'enum PWAuthorityLayout \{(.*?)\n\}', source, re.S).group(1)
declared = set(re.findall(r'static let (\w+)', block))
swift = {k: int(v, 0) for k, v in re.findall(r'static let (\w+): (?:Int|UInt32|UInt64) = (0x[0-9a-f]+|[0-9]+)', block)}
compiled = {k: int(v) for k, v in (line.split('=') for line in Path(sys.argv[1]).read_text().splitlines())}
assert declared == set(swift), 'every layout constant must have a checked numeric value'
assert compiled == swift, f'authority layout disagrees: compiled={compiled}, Swift={swift}'
print(f'ok: {len(compiled)} authority region C/Swift layout values agree')
