import importlib.util
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
path=sys.argv[1] if len(sys.argv)>1 else 'submission/agent.py'
spec=importlib.util.spec_from_file_location('hazard_agent',root/path)
agent=importlib.util.module_from_spec(spec);spec.loader.exec_module(agent)
data=json.loads((root/'research/f-hazard-oracle.json').read_text())
for f in data['fixtures']:
    mon=agent.build_mon(f['source'],True)
    predicted=agent.entry_damage(mon,f['state'])
    assert abs(predicted-f['damage'])<1e-8,(f,predicted)
print(f"All {len(data['fixtures'])} official-simulator hazard damage fixtures match.")
