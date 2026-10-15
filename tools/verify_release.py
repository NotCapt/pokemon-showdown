"""Check that the recommended ZIP, manifest, tested source and team agree."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'dist/REDLINE_Search-manifest.json').read_text())
source=(root/'submission/agent.py').read_text(encoding='utf-8')
assert source.endswith((root/'agent_core.py').read_text(encoding='utf-8')), 'Generated agent has a stale core'
tree=ast.parse(source)
own=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='OWN' for t in n.targets))
team=json.loads((root/'team.json').read_text())
assert own=={''.join(c for c in p['name'].lower() if c.isalnum()):p for p in team}, 'Generated own-team data differs from team.json'
with zipfile.ZipFile(root/'dist/REDLINE_Search.zip') as archive:
    assert sorted(archive.namelist())==['agent.py','team.txt']
    for name in archive.namelist():
        source=(root/'submission'/name).read_bytes()
        assert archive.read(name)==source, name+' differs from ZIP'
        assert hashlib.sha256(source).hexdigest()==manifest[name], name+' has a stale manifest'
print('Core, team configuration, recommended ZIP and manifest match submission files.')
