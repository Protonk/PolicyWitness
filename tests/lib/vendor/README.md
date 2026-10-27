# Vendored libraries

Third-party code the build helpers import, kept unmodified so that a build
installs nothing and the helpers, which start with `-S`, import only from the
tree. `tomli` stays because Cargo 1.94 and later read TOML 1.1 in
`.cargo/config.toml` and Python's `tomllib` reads TOML 1.0 only.

| Library | Version | Used by | Source | License |
| --- | --- | --- | --- | --- |
| `tomli/` | 2.4.1 | `tests/lib/cargo_config.py`, to parse Cargo configuration | `tomli-2.4.1-py3-none-any.whl` from PyPI, SHA-256 `0d85819802132122da43cb86656f8d1f8c6587d54ae7dcaf30e90533028b49fe` | MIT, [tomli/LICENSE](tomli/LICENSE) |
| `markdown_it/` | markdown-it-py 3.0.0 | [`docs/markdown_reader.py`](../../../docs/markdown_reader.py) only, to parse Markdown | `markdown_it_py-3.0.0-py3-none-any.whl` from PyPI, SHA-256 `355216845c60bd96232cd8d8c40e8f9765cc86f46880e43a8fd22dc1a1a8cab1` | MIT, [markdown_it/LICENSE](markdown_it/LICENSE) and [markdown_it/LICENSE.markdown-it](markdown_it/LICENSE.markdown-it) |
| `mdurl/` | 0.1.2 | markdown-it-py | `mdurl-0.1.2-py3-none-any.whl` from PyPI, SHA-256 `84008a41e51615a49fc9966191ff91509e3c40b939176e643fd50a5c2196b8f8` | MIT, [mdurl/LICENSE](mdurl/LICENSE) |
| `pytest/`, `_pytest/`, `py.py` | pytest 9.1.1 | [`tests/lib/pytest_host.py`](../pytest_host.py) only, to run a test file under pytest | `pytest-9.1.1-py3-none-any.whl` from PyPI, SHA-256 `37a86b45efb9a47a61a36449063e8e18d0cab3161329fc099eb21783169c4f0c` | MIT, [pytest-9.1.1.dist-info/licenses/LICENSE](pytest-9.1.1.dist-info/licenses/LICENSE) |
| `pluggy/` | 1.7.0 | pytest | `pluggy-1.7.0-py3-none-any.whl` from PyPI, SHA-256 `7dd7b0d8832ba3cb632c306926ded123429211b83641b35dc5c41ad2d34f9bec` | MIT, [pluggy-1.7.0.dist-info/licenses/LICENSE](pluggy-1.7.0.dist-info/licenses/LICENSE) |
| `iniconfig/` | 2.3.1 | pytest | `iniconfig-2.3.1-py3-none-any.whl` from PyPI, SHA-256 `9121e2c1fdb355232495be3194c8dfe87ccc2d5dee45947b78e68f499790d7a7` | MIT, [iniconfig-2.3.1.dist-info/licenses/LICENSE](iniconfig-2.3.1.dist-info/licenses/LICENSE) |
| `packaging/` | 26.3 | pytest | `packaging-26.3-py3-none-any.whl` from PyPI, SHA-256 `d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c` | Apache-2.0 or BSD-2-Clause, [packaging-26.3.dist-info/licenses/LICENSE](packaging-26.3.dist-info/licenses/LICENSE) |
| `pygments/` | 2.21.0 | pytest, for highlighted tracebacks | `pygments-2.21.0-py3-none-any.whl` from PyPI, SHA-256 `2363c69b61c4a97c838da3b130dcd6468f4848992b21a82f2a63ec34377137d9` | BSD-2-Clause, [pygments-2.21.0.dist-info/licenses/LICENSE](pygments-2.21.0.dist-info/licenses/LICENSE) |

The package files are the wheel's `tomli/` directory byte for byte; the
license is the wheel's `licenses/LICENSE`. To update, replace the files from a
newer wheel whose digest matches PyPI's, record the version and digest here,
and run the Cargo configuration controls through `tests/lib/python.sh`.

`markdown_it/` and `mdurl/` are their wheels' package directories byte for
byte, with each wheel's license files from its `.dist-info` directory placed in
the package. Each wheel's `RECORD` is kept here as
`markdown_it_py-3.0.0.RECORD` and `mdurl-0.1.2.RECORD`. The
`source_drift/markdown_reader` case compares every vendored file with its
`RECORD` digest and refuses an import of either package anywhere except
`docs/markdown_reader.py`, which loads them only from this directory.

The pytest host's five wheels are vendored with their `.dist-info` directories
complete, except `RECORD`, which is kept beside the packages as
`<name>-<version>.RECORD`: pluggy reads its own version through
`importlib.metadata`, which needs the metadata on the path. Their licenses
stay under `<dist-info>/licenses/`. The same case compares every file of the
five wheels with its `RECORD` digest, refuses an import of pytest outside
`tests/lib/pytest_host.py` and the test files it is allowed to run, and refuses
an import of the other four packages anywhere outside this directory. The host
refuses to run a pytest whose version is not 9.1.1 or whose module path is
outside this directory. To update the set, replace every file from the new
wheels whose digests match PyPI's, record the versions and digests here and the
new `RECORD` digests in [markdown.py](../../suites/source_drift/markdown.py),
change the host's pin, and run `source_drift/markdown_reader`,
`dispatcher/pytest_host_controls` and `preflight/build_provenance_controls`.
