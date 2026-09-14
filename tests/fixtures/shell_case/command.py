"""Independent shell-helper control; records execution and emits fixed evidence."""
import json
import os
from pathlib import Path
import sys


config = json.loads(Path(os.environ['CONTROL_CONFIG']).read_text())
phase = sys.argv[1]
with Path(config['journal']).open('a') as stream:
    stream.write(json.dumps({'phase': phase, 'argv': sys.argv[2:]}) + '\n')

# An optimistic diagnostic must not turn a nonzero command into a passing test.
sys.stdout.buffer.write(f"{phase}: ok {config['marker']}\n".encode())
sys.stdout.buffer.flush()
sys.stderr.buffer.write(f"{phase}: stderr {config['marker']}\n".encode())
sys.stderr.buffer.flush()

rc = config.get(f'{phase}_exit', 0)
if phase == 'build' and rc == 0 and config.get('produce_output', True):
    output = Path(sys.argv[2])
    output.write_text('#!/bin/sh\nexit 0\n')
    output.chmod(0o755 if config.get('executable_output', True) else 0o644)
sys.exit(rc)
