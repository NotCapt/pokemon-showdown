"""Check that the recommended ZIP, manifest, tested source and team agree."""
import hashlib
import json
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'dist/REDLINE_Search-manifest.json').read_text())
with zipfile.ZipFile(root/'dist/REDLINE_Search.zip') as archive:
    assert sorted(archive.namelist())==['agent.py','team.txt']
    for name in archive.namelist():
        source=(root/'submission'/name).read_bytes()
        assert archive.read(name)==source, name+' differs from ZIP'
        assert hashlib.sha256(source).hexdigest()==manifest[name], name+' has a stale manifest'
print('Recommended ZIP and manifest match submission files.')
