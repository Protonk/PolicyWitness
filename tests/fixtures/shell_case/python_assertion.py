"""Test-owned assertion and receipt; imports no harness code."""
import json
import os
from pathlib import Path

mode = os.environ['PW_CONTROL_ASSERTION']
Path(os.environ['PW_CONTROL_CHECKER_RECEIPT']).write_text(json.dumps({
    'assertions_enabled': __debug__, 'mode': mode,
}) + '\n')
assert mode == 'pass', 'deliberate assertion failure'
