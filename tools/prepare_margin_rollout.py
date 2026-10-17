"""Two small policy guards, keeping v4.7 mechanics and team unchanged."""
import ast
import hashlib
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/robust-rollout-v3'
assert not (OUT/'manifest.json').exists()
base=(ROOT/'archive/v4_7/agent_core.py').read_text(encoding='utf-8')
assert base.count('        self.mc_last=None')==1
base=base.replace('        self.mc_last=None','        self.mc_cycles={}\n        self.mc_last=None')
helper=(OUT/'margin_helpers.py').read_text(encoding='utf-8')
for label in ('margin','cycle'):
    folder=OUT/'candidates'/label;folder.mkdir(parents=True,exist_ok=True)
    core=base+'\nCYCLE_GUARD = '+repr(label=='cycle')+'\n'+helper
    ast.parse(core);(folder/'agent_core.py').write_text(core,encoding='utf-8')
    (folder/'team.json').write_bytes((ROOT/'archive/v4_7/team.json').read_bytes())
    subprocess.run([sys.executable,'tools/build_agent.py','--core',str(folder/'agent_core.py'),'--team',str(folder/'team.json'),'--out',str(folder)],cwd=ROOT,check=True)
    print(label,hashlib.sha256((folder/'agent.py').read_bytes()).hexdigest())
