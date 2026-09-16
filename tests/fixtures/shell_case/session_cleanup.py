"""Harmless ownership-helper stand-in for wrapper phase/exit controls."""
from pathlib import Path
import subprocess
import sys

assert sys.argv[1] == 'cleanup'
if Path(sys.argv[3]).exists():
    result = subprocess.run([sys.argv[2], 'runner', 'remove', '--id', 'fixture-id'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    raise SystemExit(result.returncode)
