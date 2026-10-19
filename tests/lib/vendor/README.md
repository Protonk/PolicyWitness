# Vendored libraries

Third-party code the build helpers import, kept unmodified so the system
`/usr/bin/python3` (3.9) can run them with nothing installed during a build.
Python 3.9 has no `tomllib`, and markdown-it-py 3.0.0 is the last release that
supports it.

| Library | Version | Used by | Source | License |
| --- | --- | --- | --- | --- |
| `tomli/` | 2.4.1 | `tests/lib/cargo_config.py`, to parse Cargo configuration | `tomli-2.4.1-py3-none-any.whl` from PyPI, SHA-256 `0d85819802132122da43cb86656f8d1f8c6587d54ae7dcaf30e90533028b49fe` | MIT, [tomli/LICENSE](tomli/LICENSE) |
| `markdown_it/` | markdown-it-py 3.0.0 | [`docs/markdown_reader.py`](../../../docs/markdown_reader.py) only, to parse Markdown | `markdown_it_py-3.0.0-py3-none-any.whl` from PyPI, SHA-256 `355216845c60bd96232cd8d8c40e8f9765cc86f46880e43a8fd22dc1a1a8cab1` | MIT, [markdown_it/LICENSE](markdown_it/LICENSE) and [markdown_it/LICENSE.markdown-it](markdown_it/LICENSE.markdown-it) |
| `mdurl/` | 0.1.2 | markdown-it-py | `mdurl-0.1.2-py3-none-any.whl` from PyPI, SHA-256 `84008a41e51615a49fc9966191ff91509e3c40b939176e643fd50a5c2196b8f8` | MIT, [mdurl/LICENSE](mdurl/LICENSE) |

The package files are the wheel's `tomli/` directory byte for byte; the
license is the wheel's `licenses/LICENSE`. To update, replace the files from a
newer wheel whose digest matches PyPI's, record the version and digest here,
and run the Cargo configuration controls under `/usr/bin/python3`.

`markdown_it/` and `mdurl/` are their wheels' package directories byte for
byte, with each wheel's license files from its `.dist-info` directory placed in
the package. Each wheel's `RECORD` is kept here as
`markdown_it_py-3.0.0.RECORD` and `mdurl-0.1.2.RECORD`. The
`source_drift/markdown_reader` case compares every vendored file with its
`RECORD` digest and refuses an import of either package anywhere except
`docs/markdown_reader.py`, which loads them only from this directory. Moving to
a newer markdown-it-py needs a newer Python than `/usr/bin/python3`.
