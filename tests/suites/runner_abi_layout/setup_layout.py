"""Compiled setup geometry compared with independent Swift constants and fixed bounds."""
import re
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
source=(root/'runner/Sources/PWRunnerCore/AuthoritySetupRuntime.swift').read_text()
block=re.search(r'enum PWAuthoritySetupLayout \{(.*?)\n\}',source,re.S).group(1)
values={k:int(v) for k,v in re.findall(r'static let (\w+): Int = (\d+)',block)}
assert values.pop('encodedReserve')==524288
compiled={k:int(v) for k,v in (line.split('=') for line in Path(sys.argv[1]).read_text().splitlines())}
assert compiled==values,(compiled,values)
assert compiled['bytes']==832 and compiled['capacity']==16 and compiled['cellBytes']==48
assert compiled['flagsOffset']==28 and compiled['cellsOffset']==64
print('ok: compiled setup publication geometry and independent fixed bounds')
