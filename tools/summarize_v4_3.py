"""Verify v4.3 artifact provenance, selected battles and portal smoke test."""
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
release=digest(root/'submission/agent.py')
assert release==digest(root/'research/c-final/agent.py')
selected={}
for label in ('adaptive','mixed','custom','stateless','direct'):
    r=json.loads((root/f'research/c-final-{label}.json').read_text())
    assert r['agentSha256']==release
    assert r['team']==json.loads((root/'team.json').read_text())
    assert r['games']==len(r['results']) and all(x['errors']==0 for x in r['results'])
    selected[label]=dict(games=r['games'],wins=r['wins'],latencyMs=r['latencyMs'])
total=0
for p in (root/'research').glob('c-*.json'):
    r=json.loads(p.read_text())
    if 'results' not in r:continue
    assert len(r['results'])==r['games'] and all(x['errors']==0 for x in r['results'])
    src=root/r['agentFile']
    if digest(src)!=r['agentSha256']:
        src=next(p for p in (root/'archive').glob('*/agent.py') if digest(p)==r['agentSha256'])
    assert digest(src)==r['agentSha256']
    total+=r['games']
portal=json.loads((root/'research/v4_3-portal-result.json').read_text())
proof=json.loads((root/'research/v4_3-portal-result.tested.json').read_text())
assert proof['agentSha256']==release and not proof['probe']
assert proof['teamSha256']==digest(root/'team.json')
assert portal['success'] and portal['winnerSlot']=='p1'
html=portal['replayHtml']
(root/'research/v4_3-portal-replay.html').write_text(html,encoding='utf-8')
match=re.search(r'<script[^>]*class="battle-log-data"[^>]*>(.*?)</script>',html,re.S)
assert match
log=match.group(1)
assert not re.search(r'invalid|fallback|\|error\|',log,re.I)
(root/'research/v4_3-portal-battle.log').write_text(log,encoding='utf-8')
result=dict(agentSha256=release,selectedArtifactGames=sum(x['games'] for x in selected.values()),
            selected=selected,researchPassGames=total,illegalActions=0,
            portal=dict(battleId=portal['battleId'],winner=portal['winner'],turns=portal['turns']),
            caveat='Small mixed changes with wide intervals; no established tournament or universal advantage. No final entry submitted.')
(root/'research/v4_3-summary.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
