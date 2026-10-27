#!/usr/bin/env python3
"""Make the shipped-worker harness variants for the pre-touch investigation.

Copies tests/suites/runner_c_worker_harness/harness.c unchanged and in three
patched forms, never editing the original: `notouch` removes the host's
full-region page touch after population, and `v2`/`v3` change the bare
deny-default scenario policy's version line. Each copy's unified diff against
the original is written beside it. Refuses unless each anchor occurs exactly
once, so a changed harness cannot be patched silently.
"""
import difflib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'tests/suites/runner_c_worker_harness/harness.c'
TOUCH_BLOCK = '''    if (!scen->skip_touch) {
        for (size_t off = 0; off < PW_SHM_REGION_BYTES; off += ft.page_size) {
            touch[off] = touch[off];
        }
        touch[PW_SHM_REGION_BYTES - 1u] = touch[PW_SHM_REGION_BYTES - 1u];
    }
'''
DENY_POLICY = '''static const char SCEN_DENY_DEFAULT_POLICY[] =
    "(version 1)\\n"
    "(deny default)\\n";
'''


def variant(text, touch, version):
    out = text
    if not touch:
        out = out.replace(TOUCH_BLOCK, '    /* pretouch investigation: the host page touch is removed. */\n')
    if version != 1:
        out = out.replace(DENY_POLICY, DENY_POLICY.replace('(version 1)', f'(version {version})'))
    return out


def main(out_dir):
    text = SOURCE.read_text()
    for anchor in (TOUCH_BLOCK, DENY_POLICY):
        if text.count(anchor) != 1:
            sys.exit(f'refused: anchor occurs {text.count(anchor)} times in {SOURCE}')
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for touch in (True, False):
        for version in (1, 2, 3):
            name = f"harness_{'touch' if touch else 'notouch'}_v{version}"
            body = variant(text, touch, version)
            (out_dir / f'{name}.c').write_text(body)
            diff = difflib.unified_diff(text.splitlines(keepends=True), body.splitlines(keepends=True),
                                        fromfile=str(SOURCE.relative_to(ROOT)), tofile=f'{name}.c')
            (out_dir / f'{name}.diff').write_text(''.join(diff))
            print(name)


if __name__ == '__main__':
    main(sys.argv[1])
