"""Promote only the audited, validation-selected Monte Carlo winner."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import evaluate_monte_carlo as experiment

ROOT,OUT=experiment.ROOT,experiment.OUT
m=experiment.prepare()
result=experiment.load(OUT/'result.json')
audit=experiment.load(OUT/'audit.json')
assert audit['allSourcesSchedulesScoresAndGatesVerified']
assert result['gates']['promote'] and audit['gates']==result['gates'], 'Candidate did not earn promotion'
assert result['manifestSha256']==experiment.sha(OUT/'manifest.json')==audit['manifestSha256']
label=result['validationSelected']
assert label==audit['validationSelected']==result['recommended']
source=OUT/'candidates'/label
assert experiment.sha(source/'agent.py')==m['candidateSha256'][label]
standalone=experiment.load(OUT/'standalone.json')[label]
assert standalone['isolatedStdlibExecutionPassed'] and standalone['sourceSha256']==m['candidateSha256'][label]
assert experiment.sha(ROOT/'submission/agent.py')==m['candidateSha256']['control'], 'Recommended source changed outside this trial'
assert (ROOT/'agent_core.py').read_bytes()==(ROOT/'archive/v4_6/agent_core.py').read_bytes()
assert (ROOT/'team.json').read_bytes()==(ROOT/'archive/v4_6/team.json').read_bytes()
archive=ROOT/'archive/v4_7'
assert not archive.exists(), 'Do not overwrite an existing release'
team=experiment.load(source/'team.json')
experiment.engine.team_search.validate(team)
tree=ast.parse((source/'agent.py').read_text(encoding='utf-8'))
own=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(getattr(t,'id',None)=='OWN' for t in n.targets))
assert list(own.values())==team
subprocess.run(['node','tools/check_submission_team.js',str(source/'team.txt'),str(source/'team.json')],cwd=ROOT,check=True)
subprocess.run([sys.executable,'tools/package_submission.py','--name','REDLINE_Search_v4_7','--source',str(source),'--team',str(source/'team.json')],cwd=ROOT,check=True)
subprocess.run([sys.executable,'tools/audit_submission_readiness.py','--zip','dist/REDLINE_Search_v4_7.zip',
                '--source',str(source),'--team',str(source/'team.json'),'--out','research/monte-carlo-v1/release-readiness.json'],cwd=ROOT,check=True)
# Package compatibility is verified before changing any recommended files.
archive.mkdir()
for name in ('agent.py','agent_core.py','team.json','team.txt'):
    shutil.copyfile(source/name,archive/name)
shutil.copyfile(source/'agent.py',ROOT/'submission/agent.py')
shutil.copyfile(source/'team.txt',ROOT/'submission/team.txt')
shutil.copyfile(source/'agent_core.py',ROOT/'agent_core.py')
shutil.copyfile(source/'team.json',ROOT/'team.json')
shutil.copyfile(ROOT/'dist/REDLINE_Search_v4_7.zip',ROOT/'dist/REDLINE_Search.zip')
shutil.copyfile(ROOT/'dist/REDLINE_Search_v4_7-manifest.json',ROOT/'dist/REDLINE_Search-manifest.json')
subprocess.run([sys.executable,'tools/verify_release.py'],cwd=ROOT,check=True)
record=dict(version='v4.7',candidate=label,sourceSha256=experiment.sha(source/'agent.py'),
            zip='dist/REDLINE_Search_v4_7.zip',zipSha256=experiment.sha(ROOT/'dist/REDLINE_Search_v4_7.zip'),
            manifestSha256=experiment.sha(OUT/'manifest.json'),auditSha256=experiment.sha(OUT/'audit.json'),
            originalV46Preserved=True,practiceUploadPerformed=False)
experiment.write(OUT/'release.json',record)
print(json.dumps(record,indent=2))
