"""GitHub stand-in for `preflight/release_publish_controls`: no network, no gh."""
import hashlib
import json
from pathlib import Path
import subprocess


class GitHub:
    """Replaces release_publish.run: git runs for real against a local bare remote; gh is simulated."""

    def __init__(self, receipts, *, mode=None):
        self.receipts, self.mode = Path(receipts), mode
        self.calls = []
        self.release = None
        self.assets = {}

    def __call__(self, argv, *, cwd=None):
        argv = list(map(str, argv))
        self.calls.append(argv)
        with self.receipts.open('a') as stream:
            stream.write(json.dumps(dict(argv=argv, cwd=str(cwd))) + '\n')
        if argv[0] == 'git':
            return subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
        assert argv[0] == 'gh', argv
        if argv[1:3] == ['release', 'view']:
            if self.release is None:
                return subprocess.CompletedProcess(argv, 1, '', 'release not found\n')
            body = json.dumps(self.view()) if '--json' in argv else self.release['title'] + '\n'
            return subprocess.CompletedProcess(argv, 0, body, '')
        if argv[1:3] == ['release', 'create']:
            assert self.release is None, 'a second create was attempted'
            tag, rest = argv[3], argv[4:]
            positional = []
            for item in rest:
                if item.startswith('--'):
                    break
                positional.append(Path(item))
            files = positional
            options = {rest[i]: rest[i + 1] for i, item in enumerate(rest) if item.startswith('--') and i + 1 < len(rest)}
            assert '--verify-tag' in rest, 'release created without --verify-tag'
            for path in files:
                self.assets[path.name] = path.read_bytes()
            self.release = dict(tag=tag, title=options.get('--title'),
                                notes=Path(options['--notes-file']).read_text())
            return subprocess.CompletedProcess(argv, 0, f'https://github.invalid/releases/tag/{tag}\n', '')
        if argv[1:3] == ['release', 'download']:
            name = argv[argv.index('--pattern') + 1]
            data = self.assets[name]
            if self.mode == 'corrupt_download' and name.endswith('.zip'):
                data += b'\0'
            (Path(argv[argv.index('--dir') + 1]) / name).write_bytes(data)
            return subprocess.CompletedProcess(argv, 0, '', '')
        raise AssertionError(f'unexpected gh invocation: {argv}')

    def view(self):
        tag = self.release['tag']
        assets = []
        for name, data in self.assets.items():
            value = hashlib.sha256(data).hexdigest()
            if self.mode == 'digest_mismatch' and name.endswith('.zip'):
                value = 'f' * 64
            assets.append(dict(name=name, state='uploaded', size=len(data), digest=f'sha256:{value}',
                               url=f'https://github.invalid/releases/download/{tag}/{name}'))
        return dict(assets=assets, isDraft=False, publishedAt='2026-09-29T00:00:00Z', tagName=tag,
                    targetCommitish='main', url=f'https://github.invalid/releases/tag/{tag}')
