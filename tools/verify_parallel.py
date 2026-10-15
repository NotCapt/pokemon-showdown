"""Verify embedded source, shard identities and exported smoke artifacts."""
import ast
import base64
import hashlib
import io
import json
from pathlib import Path
import tempfile
import types
import zipfile

root=Path(__file__).resolve().parents[1]
hashes=[]
for index,name in enumerate(['REDLINE_Screen_1.ipynb','REDLINE_Screen_2.ipynb','REDLINE_Screen_3.ipynb','REDLINE_Final_Comparison.ipynb']):
    notebook=json.loads((root/'notebooks'/name).read_text(encoding='utf-8'))
    config={}
    exec(''.join(notebook['cells'][1]['source']),config)
    assert config['MODE']==('finalize' if index==3 else 'screen')
    if index<3:assert config['SHARD_INDEX']==index
    tree=ast.parse(''.join(notebook['cells'][2]['source']))
    values={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
            and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('BUNDLE','BUNDLE_SHA256')}
    binary=base64.b64decode(values['BUNDLE'])
    assert hashlib.sha256(binary).hexdigest()==values['BUNDLE_SHA256']
    hashes.append(values['BUNDLE_SHA256'])
    with zipfile.ZipFile(io.BytesIO(binary)) as z:
        for path in z.namelist():assert z.read(path)==(root/path).read_bytes(), 'Stale embedded source: '+path
    for cell in notebook['cells']:
        if cell['cell_type']=='code':compile(''.join(cell['source']),name,'exec')
assert len(set(hashes))==1
print('Four notebooks: matching source bundles, correct shard identities, all code cells compile.')

# Simulate Kaggle mounting both root outputs and their results-folder copies.
notebook=json.loads((root/'notebooks/REDLINE_Final_Comparison.ipynb').read_text())
discovery=ast.Module(body=[ast.parse(''.join(notebook['cells'][4]['source'])).body[0]],type_ignores=[])
with tempfile.TemporaryDirectory() as tmp:
    fixture=Path(tmp)
    for index in range(1,4):
        folder=fixture/f'notebook-{index}';(folder/'results').mkdir(parents=True)
        for path in [folder/f'redline-screen-{index}.zip',folder/'results'/f'redline-screen-{index}.zip']:
            with zipfile.ZipFile(path,'w') as z:z.writestr('screening.json',json.dumps({'shard':index}))
        with zipfile.ZipFile(folder/f'redline-screen-{index}-checkpoint.zip','w') as z:z.writestr('irrelevant','checkpoint')
    def scope():return dict(MODE='finalize',SCREENING_ZIPS=[],SHARD_COUNT=3,zipfile=zipfile,hashlib=hashlib,
                           pathlib=types.SimpleNamespace(Path=lambda path:fixture),print=lambda *a:None)
    variables=scope();exec(compile(discovery,'discovery','exec'),variables)
    assert len(variables['SCREENING_ZIPS'])==3
    with zipfile.ZipFile(fixture/'notebook-1/results/redline-screen-1.zip','w') as z:z.writestr('screening.json','different')
    try:exec(compile(discovery,'discovery','exec'),scope())
    except ValueError:pass
    else:raise AssertionError('Conflicting screening copies were not rejected')
print('Final input discovery ignores checkpoints, collapses duplicate copies, rejects conflicting inputs.')

final=root/'runs/e2-final'
if (final/'result.json').exists():
    data=json.loads((final/'result.json').read_text())
    assert data['completedGames']==102 and 'comparison' in data
    with zipfile.ZipFile(final/'best_candidate.zip') as z:
        assert sorted(z.namelist())==['agent.py','team.txt']
        tree=ast.parse(z.read('agent.py').decode())
        own=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                 and any(isinstance(t,ast.Name) and t.id=='OWN' for t in n.targets))
        assert list(own.values())==data['selected']['team']
    print('Merged smoke export: exact selected team compiled into the two-file agent ZIP.')
