"""Independent constructed layouts for build-placement checks; no Swift needed."""
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tests/lib'))
from build_receipt import inspect_layout, record_build


def main(output, scratch):
    output.mkdir(parents=True)
    results = []
    for name in ('valid', 'missing_product', 'package_build_tree',
                 'product_outside_scratch', 'scratch_inside_output', 'scratch_outside_case'):
        fixture = scratch / name
        package, evidence, build = fixture / 'package', fixture / 'evidence', fixture / 'build'
        if name == 'scratch_inside_output':
            build = evidence / 'build'
        package.mkdir(parents=True)
        build.mkdir(parents=True)
        product = (fixture if name == 'product_outside_scratch' else build) / 'product'
        if name != 'missing_product':
            product.write_bytes(b'independent product bytes\n')
        if name == 'package_build_tree':
            (package / '.build').mkdir()
        boundary = fixture / 'other' if name == 'scratch_outside_case' else scratch
        try:
            receipt = inspect_layout(package, evidence, build, product, boundary)
        except ValueError as error:
            assert name != 'valid' and str(error) == name, (name, error)
            results.append(dict(control=name, diagnostic=str(error)))
        else:
            assert name == 'valid', (name, receipt)
            assert receipt == dict(scratch_path=str(build.resolve()),
                                   product_path=str(product.resolve()),
                                   product_sha256=hashlib.sha256(b'independent product bytes\n').hexdigest())
            results.append(dict(control=name, receipt=receipt))
    # A multi-argument launcher must survive intact. A decoy swift on PATH
    # makes falling back to a bare command fail without invoking a real compiler.
    fixture = scratch / 'command with spaces'
    package, build = fixture / 'package', fixture / 'build'
    package.mkdir(parents=True)
    build.mkdir()
    (build / 'Product').write_bytes(b'launcher product\n')
    launcher = fixture / 'launcher.py'
    forwarded = output / 'forwarded-argv.json'
    launcher.write_text(
        'import json, sys\nfrom pathlib import Path\n'
        'Path(sys.argv[1]).write_text(json.dumps(sys.argv[3:]))\n'
        'print(sys.argv[2])\n')
    decoy = fixture / 'swift'
    decoy.write_text('#!/bin/sh\nexit 97\n')
    decoy.chmod(0o755)
    swift = [sys.executable, str(launcher), str(forwarded), str(build), 'swift']
    with patch.dict(os.environ, PATH=str(fixture) + os.pathsep + os.environ.get('PATH', '')):
        product = record_build(package, output, build, 'Product', swift_command=swift)
    assert product == build / 'Product', product
    assert json.loads(forwarded.read_text()) == [
        'swift', 'build', '--package-path', str(package),
        '--scratch-path', str(build), '--show-bin-path']
    receipt = json.loads((output / 'build-receipt.json').read_text())
    assert receipt['query_argv'][:len(swift)] == swift, receipt
    assert receipt['product_sha256'] == hashlib.sha256(b'launcher product\n').hexdigest(), receipt
    results.append(dict(control='producer_swift_command', receipt=receipt))
    (output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(f'{len(results)} build receipt controls passed')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
