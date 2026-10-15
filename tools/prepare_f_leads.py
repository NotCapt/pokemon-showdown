"""Compile legal lead-order alternatives with the exact incumbent policy."""
import json
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
team=json.loads((root/'archive/v4_3_2/team.json').read_text())
for label,order in [('pult',[1,0,2]),('arca',[2,0,1])]:
    folder=root/f'research/f-lead-{label}';folder.mkdir(exist_ok=True)
    path=folder/'team.json';path.write_text(json.dumps([team[i] for i in order],indent=2))
    subprocess.run([sys.executable,'tools/build_agent.py','--core','archive/v4_3_2/agent_core.py','--team',str(path),'--out',str(folder)],cwd=root,check=True)
