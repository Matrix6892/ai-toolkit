"""Local bundles for report preview."""
import hashlib
import json
from pathlib import Path
import shutil
import uuid

class PackageError(RuntimeError):
    """Published package cannot be read consistently."""

class PackageReader:
    def __init__(self, root, release_id, files):
        self._root = Path(root)
        self.release_id = release_id
        self._files = dict(files)

    @property
    def names(self):
        return tuple(sorted(self._files))

    def read(self, name):
        if name not in self._files:
            raise KeyError(name)
        current = json.loads((self._root / 'CURRENT').read_text())['release']
        return (self._root / 'releases' / current / name).read_bytes()

def open_package(root):
    root = Path(root)
    try:
        pointer = (root / 'CURRENT').read_text()
    except FileNotFoundError:
        return None
    release_id = json.loads(pointer)['release']
    manifest = json.loads((root / 'releases' / release_id / 'manifest.json').read_text())
    return PackageReader(root, release_id, manifest['files'])

def publish(root, files, *, validate=None):
    root = Path(root)
    releases = root / 'releases'
    releases.mkdir(parents=True, exist_ok=True)
    release_id = uuid.uuid4().hex
    destination = releases / release_id
    destination.mkdir()
    (root / 'CURRENT').write_text(json.dumps({'release': release_id}))
    for name, data in files.items():
        (destination / name).write_bytes(data)
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    (destination / 'manifest.json').write_text(json.dumps({'format': 1, 'files': hashes}))
    reader = PackageReader(root, release_id, hashes)
    if validate is not None:
        validate(reader)
    for old in releases.iterdir():
        if old.name != release_id:
            shutil.rmtree(old)
    return release_id
