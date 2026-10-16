"""Freeze a temporal-move follow-up before inspecting reference holdout outcomes."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/phantom-forecast-v1';REF=ROOT/'research/roster-forecast-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (OUT/'manifest.json').exists():
    m=json.loads((OUT/'manifest.json').read_text())
    for p,d in m['inputSha256'].items():assert sha(ROOT/p)==d
    print(json.dumps({'alreadyFrozen':True,'candidateSha256':m['candidateSha256']}));raise SystemExit
core=(REF/'candidates/recovery/agent_core.py').read_text(encoding='utf-8')
def replace(before,after):
    global core
    assert core.count(before)==1,before[:70]
    core=core.replace(before,after)
replace("    if a.get('locked') in DATA['moves']: choices=[DATA['moves'][a['locked']]]",
        "    if a.get('phantom_charging'): choices=[DATA['moves']['phantomforce']]\n    elif a.get('locked') in DATA['moves']: choices=[DATA['moves'][a['locked']]]")
replace("    if m.get('_hit') is False: return\n", """    if mid=='phantomforce':
        if a.get('phantom_charging'):
            a.pop('phantom_charging',None); a.pop('phantom_hidden',None)
        elif a['item']=='powerherb':
            a['item']=''
        else:
            a['phantom_charging']=True; a['phantom_hidden']=True
            return
    if m.get('_hit') is False: return
    if b.get('phantom_hidden') and m.get('target') not in ('self','allySide','all'):
        if a['ability']!='noguard' and b['ability']!='noguard': return
""")
replace("    if b['protect'] and m.get('target') not in ('self','allySide'): return",
        "    if b['protect'] and mid!='phantomforce' and m.get('target') not in ('self','allySide'): return")
replace("    if mid in ('phantomforce','bounce','solarbeam','gigaimpact'): d *= .55",
        "    if mid in ('bounce','solarbeam','gigaimpact'): d *= .55")
ast.parse(core)
folder=OUT/'candidates/phased';folder.mkdir(parents=True,exist_ok=True)
(folder/'agent_core.py').write_text(core,encoding='utf-8')
(folder/'team.json').write_bytes((REF/'candidates/control/team.json').read_bytes())
subprocess.run([sys.executable,'tools/build_agent.py','--core',str(folder/'agent_core.py'),
                '--team',str(folder/'team.json'),'--out',str(folder)],cwd=ROOT,check=True)
reference=json.loads((REF/'manifest.json').read_text())
# Copy frozen sets as opaque files. Do not read reference battle results here.
for category in ('opponents','suites'):
    for file in (REF/category).rglob('*'):
        if file.is_file() and file.suffix in ('.py','.json','.txt'):
            target=OUT/file.relative_to(REF);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(file.read_bytes())
inputs=['tools/prepare_phased_forecast.py','tools/evaluate_roster_forecast.py','tools/evaluate_diverse_league.py',
        'tools/benchmark.js','tools/worker.py','tools/opponents.js','package-lock.json',
        'research/roster-forecast-v1/manifest.json','research/roster-forecast-v1/candidates/control/agent.py',
        'research/roster-forecast-v1/candidates/recovery/agent.py']
inputs+=[p.relative_to(ROOT).as_posix() for pattern in ('candidates/*/*','opponents/*/*.py','opponents/*/*.json','suites/*.json') for p in OUT.glob(pattern) if p.is_file()]
m=dict(candidateSha256={'phased':sha(folder/'agent.py')},inputSha256={p:sha(ROOT/p) for p in inputs},
       referenceManifestSha256=sha(REF/'manifest.json'),jobs={p:reference['jobs'][p] for p in ('validation','confirmation')},
       additionalGames=1296,referenceComparisons=['control','recovery'],
       heldout='Candidate frozen before inspecting any confirmation outcomes from the reference study. Validation is exploratory; confirmation reuses the already scheduled reference sets/seeds/sides. Shared control/recovery games are not additional independent evidence.',
       changes='Recovery fixes plus explicit Phantom Force charge, invulnerability, forced continuation, later full-power attack and Protect bypass. No whole-roster valuation or team changes.',
       strengthRule='Confirmation mean higher with positive lower paired 95% bound against both original control and recovery; no confirmation category regression above five points against either.',
       correctnessRule='All simulator and automated checks pass; confirmation mean not lower than control, lower paired bound above -3 pp, no validation or confirmation category regression beyond two points against control. No strength claim through this gate.')
(OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'candidateSha256':m['candidateSha256'],'newScheduledGames':1296,'referenceManifestSha256':m['referenceManifestSha256']},indent=2))
