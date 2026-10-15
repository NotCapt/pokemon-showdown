"""Promote only an audited, tested winner; preserve the exact v4.5 release."""
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/diverse-league-v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((OUT/'manifest.json').read_text())
result=json.loads((OUT/'result.json').read_text())
audit=json.loads((OUT/'audit.json').read_text())
verification=json.loads((OUT/'verification.json').read_text())
assert result['promote'] and audit['promote'],'The predeclared promotion gate did not pass'
assert result['completedGames']==audit['checkedGames']==8856
assert result['manifestSha256']==audit['manifestSha256']==sha(OUT/'manifest.json')
assert audit['allSchedulesAndCompiledTeamsVerified']
assert verification['agentSha256']==result['sourceSha256']
assert verification['pythonTestsPassed'] and verification['jsTestsPassed'] and verification['teamTextMatches']
folder=OUT/'candidates'/result['selected']['id']
assert sha(folder/'agent.py')==result['sourceSha256']
assert json.loads((folder/'team.json').read_text())==result['selected']['team']
for name in ['agent_core.py','team.json','submission/agent.py','submission/team.txt']:
    assert sha(ROOT/name)==manifest['inputSha256'][name],'Unrecognized current release edits: '+name
with zipfile.ZipFile(OUT/'selected_candidate.zip') as archive:
    assert sorted(archive.namelist())==['agent.py','team.txt']
    for name in archive.namelist():assert archive.read(name)==(folder/name).read_bytes()
assert sha(OUT/'selected_candidate.zip')==audit['selectedZipSha256']
old_archive=ROOT/'archive/v4_5'
mapping=[('agent_core.py','agent_core.py'),('team.json','team.json'),
         ('submission/agent.py','agent.py'),('submission/team.txt','team.txt')]
for original,name in mapping:
    dest=old_archive/name
    if dest.exists():assert dest.read_bytes()==(ROOT/original).read_bytes(),'Conflicting archive: '+name
old_archive.mkdir(exist_ok=True)
for original,name in mapping:
    if not (old_archive/name).exists():shutil.copyfile(ROOT/original,old_archive/name)
for name in ('agent.py','team.txt'):shutil.copyfile(folder/name,ROOT/'submission'/name)
shutil.copyfile(folder/'team.json',ROOT/'team.json')
file_manifest={name:sha(ROOT/'submission'/name) for name in ('agent.py','team.txt')}
for label in ('REDLINE_Search','REDLINE_Search_v4_6'):
    shutil.copyfile(OUT/'selected_candidate.zip',ROOT/'dist'/(label+'.zip'))
    (ROOT/'dist'/(label+'-manifest.json')).write_text(json.dumps(file_manifest,indent=2)+'\n',encoding='utf-8')
release=dict(version='v4.6',agentSha256=result['sourceSha256'],zipSha256=audit['selectedZipSha256'],
    teamSha256=sha(ROOT/'team.json'),engineSha256=sha(ROOT/'agent_core.py'),
    previousAgentSha256=sha(old_archive/'agent.py'),versionedZip='dist/REDLINE_Search_v4_6.zip',
    reason='Passed the frozen diverse-league confirmation gate, complete source/schedule audit, team-text consistency and automated checks. Decision engine unchanged; selected team configuration updated.')
(OUT/'release.json').write_text(json.dumps(release,indent=2)+'\n',encoding='utf-8')
print(json.dumps(release,indent=2))
