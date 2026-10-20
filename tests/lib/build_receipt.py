"""Observe SwiftPM product placement before case finalization removes scratch."""
import hashlib
import json
import os
from pathlib import Path
import subprocess


def inspect_layout(package, output, scratch, product, case_scratch=None):
    package, output, scratch, product = (
        Path(path).resolve() for path in (package, output, scratch, product))
    if scratch == output or output in scratch.parents:
        raise ValueError("scratch_inside_output")
    if case_scratch is not None:
        case_scratch = Path(case_scratch).resolve()
        if scratch != case_scratch and case_scratch not in scratch.parents:
            raise ValueError("scratch_outside_case")
    if scratch not in product.parents:
        raise ValueError("product_outside_scratch")
    if not product.is_file():
        raise ValueError("missing_product")
    if (package / '.build').exists() or (package / '.build').is_symlink():
        raise ValueError("package_build_tree")
    return dict(scratch_path=str(scratch), product_path=str(product),
                product_sha256=hashlib.sha256(product.read_bytes()).hexdigest())


def record_build(package, output, scratch, product_name, *, swift_command):
    command = [*swift_command, 'build', '--package-path', str(package),
               '--scratch-path', str(scratch), '--show-bin-path']
    # Retain diagnostics even if SwiftPM refuses the query.
    with (output / 'build-location.log').open('w') as log:
        binary_dir = subprocess.check_output(command, text=True, stderr=log, timeout=120).strip()
    receipt = inspect_layout(package, output, scratch, Path(binary_dir) / product_name,
                             os.environ.get('PW_TEST_SCRATCH'))
    receipt['query_argv'] = command
    (output / 'build-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return Path(receipt['product_path'])
