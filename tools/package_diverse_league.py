"""Package the exact pre-battle campaign inputs, without cached results."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/diverse-league-v1'
manifest=json.loads((OUT/'manifest.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
files={}
for name,digest in manifest['inputSha256'].items():
    data=(ROOT/name).read_bytes();assert sha(data)==digest
    files[name]=data
for name in ['package.json','tools/run_diverse_league.py','tools/audit_diverse_league.py',
             'tools/summarize_diverse_league.py','tools/check_league_execution_modes.py','research/DIVERSE_LEAGUE.md',
             'research/kaggle-v4_5-evaluation/manifest.json','research/kaggle-results-v4_3_2/final/audit.json']:
    files[name]=(ROOT/name).read_bytes()
for name in ['manifest.json','preflight.json','execution-adapter.json']:
    files[str((OUT/name).relative_to(ROOT)).replace('\\','/')]=(OUT/name).read_bytes()
for pattern in ['reference/*','candidates/*/agent.py','candidates/*/team.json','candidates/*/team.txt',
                'suites/*.json','opponents/*/*.json']:
    for path in OUT.glob(pattern):
        if path.is_file():files[path.relative_to(ROOT).as_posix()]=path.read_bytes()
files['REPRODUCE.md']=b'''# Frozen diverse league reproducer

This archive preserves the Windows/Python 3.10/Node 24 campaign inputs,
including the original v4.5 team, exact compiled agents, and frozen schedules.
It contains no cached battle outcomes, private teammate originals or secrets.
The paths in the original manifest use Windows separators. Run this archive
on Windows in a separate extracted directory, rather than over a newer release.

Install Python 3.10 and Node 24. In this extracted project directory run:

    npm ci --omit=optional --no-audit --no-fund
    python tools/audit_diverse_league.py --preflight
    python tools/run_diverse_league.py --workers 6
    python tools/audit_diverse_league.py
    python tools/check_league_execution_modes.py
    python tools/summarize_diverse_league.py

The plan schedules 8,856 games. Complete jobs are cached for resume. Use fewer
workers if needed; workers do not change the frozen scoring or schedules.
The execution-mode diagnostic adds 192 games outside the 8,856-game score.
Results are written to research/diverse-league-v1. No competition entry or
external upload is performed. See research/DIVERSE_LEAGUE.md for the protocol.
'''
destination=ROOT/'dist/REDLINE_Diverse_League_Project_v1.zip'
with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
    for name,data in sorted(files.items()):
        entry=zipfile.ZipInfo(name,date_time=(2026,10,16,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
        archive.writestr(entry,data)
proof=dict(manifestSha256=sha((OUT/'manifest.json').read_bytes()),bundleSha256=sha(destination.read_bytes()),
    bytes=destination.stat().st_size,members=len(files),fileSha256={name:sha(data) for name,data in sorted(files.items())},
    environment='Windows, Python 3.10, Node 24; pokemon-showdown 0.11.11 from package-lock.json')
destination.with_name(destination.stem+'-manifest.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items() if k!='fileSha256'},indent=2))
