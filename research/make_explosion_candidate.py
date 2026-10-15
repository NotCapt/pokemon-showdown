"""Reproduce a scoped mechanics experiment without modifying the release."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / 'archive/v4_2/agent.py').read_text()
changes = {
    "if m.get('_hit') is False: return": "if m.get('_hit') is False:\n        if mid=='explosion': a['hp']=0\n        return",
    "if b['protect'] and m.get('target') not in ('self','allySide'): return": "if b['protect'] and m.get('target') not in ('self','allySide'):\n        if mid=='explosion': a['hp']=0\n        return",
    'if d<=0: return': "if mid=='explosion': a['hp']=0\n    if d<=0: return",
}
for old, new in changes.items():
    assert source.count(old) == 1
    source = source.replace(old, new)
(root / 'research/v4_3-explosion-agent.py').write_text(source)
