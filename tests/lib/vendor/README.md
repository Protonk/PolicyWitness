# Vendored libraries

Third-party code the build helpers import, kept unmodified so the system
`/usr/bin/python3` (3.9, without `tomllib`) can run them with nothing installed
during a build.

| Library | Version | Used by | Source | License |
| --- | --- | --- | --- | --- |
| `tomli/` | 2.4.1 | `tests/lib/cargo_config.py`, to parse Cargo configuration | `tomli-2.4.1-py3-none-any.whl` from PyPI, SHA-256 `0d85819802132122da43cb86656f8d1f8c6587d54ae7dcaf30e90533028b49fe` | MIT, [tomli/LICENSE](tomli/LICENSE) |

The package files are the wheel's `tomli/` directory byte for byte; the
license is the wheel's `licenses/LICENSE`. To update, replace the files from a
newer wheel whose digest matches PyPI's, record the version and digest here,
and run the Cargo configuration controls under `/usr/bin/python3`.
