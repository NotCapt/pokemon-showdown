"""Build isolated forecasts while preserving the exact released v4.6 bytes."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/roster-forecast-v1'
OUT.mkdir(parents=True, exist_ok=True)
base = (ROOT / 'agent_core.py').read_text(encoding='utf-8')
assert hashlib.sha256((ROOT / 'submission/agent.py').read_bytes()).hexdigest() == '07b1e968db139b43ebf4dcf49900719977096ac42434d217f1f8534984183ac5'


def replace(source, before, after):
    assert source.count(before) == 1, before[:80]
    return source.replace(before, after)


def recovery(source):
    source = replace(source, """    if a['status']=='slp' and m.get('id')!='sleeptalk':
        a['sleep']+=1
        if a['sleep']<2: return
        a['status']=''
""", """    if a['status']=='slp' and m.get('id')!='sleeptalk':
        if 'rest_sleep' in a:
            if a['rest_sleep']>0:
                a['rest_sleep']-=1
                return
            a.pop('rest_sleep')
        else:
            # Observed sleep has an unknown remaining duration. Keep its prior.
            a['sleep']+=1
            if a['sleep']<2: return
        a['status']=''
""")
    source = replace(source, """    if m.get('heal') or mid=='rest':
        a['hp']=min(100,a['hp']+(100 if mid=='rest' else 50))
        if mid=='rest': a['status']='slp'; a['sleep']=0
        return
""", """    if m.get('heal') or mid=='rest':
        if a['hp']>=100: return  # A failed heal creates no Roost or Rest state.
        a['hp']=min(100,a['hp']+(100 if mid=='rest' else 50))
        if mid=='rest':
            a['status']='slp'; a['sleep']=0; a['rest_sleep']=2
        if mid=='roost' and 'Flying' in a['types']:
            a['_roost_types']=a['types']
            a['types']=[t for t in a['types'] if t!='Flying']
        return
""")
    source = replace(source, """        p['hp']=max(0,p['hp']-loss)


def turn""", """        p['hp']=max(0,p['hp']-loss)
    for p in (a,b):
        if '_roost_types' in p: p['types']=p.pop('_roost_types')


def turn""")
    return source


HELPERS = '''def roster_value(roster,foe):
    return sum(value(p,dict(foe,hp=0)) for p in roster.values())-value(foe,dict(foe,hp=0))


def replacement(roster,foe,weather,roll,entry_loss):
    living=[p for p in roster.values() if p['hp']>0]
    if not living: return None
    def utility(p):
        x,y=clone_mon(p),clone_mon(foe)
        x['boosts']={}; x.pop('locked',None)
        x['hp']=max(0,x['hp']-entry_loss(x))
        if x['hp']<=0: return -10000.
        enter_intimidate(x,y)
        before=value(x,y)
        turn(x,y,best_attack(x,y,weather),best_attack(y,x,weather),weather,roll)
        return value(x,y)-before+.15*value(x,y)
    entering=max(living,key=utility)
    entering['boosts']={}; entering.pop('locked',None)
    entering['hp']=max(0,entering['hp']-entry_loss(entering))
    if entering['hp']>0: enter_intimidate(entering,foe)
    return entering


'''


def roster(source):
    source = replace(source, 'class PokemonAgent:', HELPERS + 'class PokemonAgent:')
    source = replace(source, "        # Defaults get most prior mass; custom coverage is considered pessimistically.", """        own_team={}
        for raw in o.get('my_team') or [o.get('my_active') or {}]+switches:
            mon=build_mon(raw,True)
            if mon['key']:
                if raw.get('fainted'): mon['hp']=0
                own_team[mon['key']]=mon
        own_team[a['key']]=a
        full_active=build_mon(o.get('my_active') or {},True)
        team_initial=roster_value(own_team,b)
        # Defaults get most prior mass; custom coverage is considered pessimistically.""")
    source = replace(source, """                    x=clone_mon(entry)
                    y=clone_mon(b)
""", """                    roster={key:clone_mon(p) for key,p in own_team.items()}
                    if s:
                        roster[a['key']]['boosts']={}; roster[a['key']].pop('locked',None)
                        roster[a['key']]['moves']=full_active['moves']
                    x=clone_mon(entry); roster[x['key']]=x
                    y=clone_mon(b)
""")
    source = replace(source, """                    first=value(x,y)
                    switch_faint=bool(s) and not o.get('force_switch') and x['hp']<=0
""", """                    first=roster_value(roster,y)
                    switch_faint=bool(s) and not o.get('force_switch') and x['hp']<=0
                    if continuation_turn<=100 and x['hp']<=0 and y['hp']>0:
                        x=replacement(roster,y,weather,roll,self.entry_loss) or x
""")
    source = replace(source, "                    second=value(x,y)\n", """                    second=roster_value(roster,y)
                    if continuation_turn<100 and x['hp']<=0 and y['hp']>0:
                        x=replacement(roster,y,weather,roll,self.entry_loss) or x
""")
    source = replace(source, "                    score=(first-initial)+.65*(second-first)+.40*(value(x,y)-second)+.12*value(x,y)",
                     "                    score=(first-team_initial)+.65*(second-first)+.40*(roster_value(roster,y)-second)+.12*roster_value(roster,y)")
    source = replace(source, "                        score=x['hp']-starting_hp-(y['hp']-b['hp'])", "                        score=sum(p['hp'] for p in roster.values())-sum(p['hp'] for p in own_team.values())-(y['hp']-b['hp'])")
    return source


cores = dict(control=base, recovery=recovery(base), roster=roster(base), combined=roster(recovery(base)))
for label, core in cores.items():
    ast.parse(core)
    folder = OUT / 'candidates' / label
    folder.mkdir(parents=True, exist_ok=True)
    source = folder / 'agent_core.py'
    if source.exists():
        assert source.read_text(encoding='utf-8') == core, 'Do not change a frozen candidate'
    else:
        source.write_text(core, encoding='utf-8')
    (folder / 'team.json').write_bytes((ROOT / 'team.json').read_bytes())
    subprocess.run([sys.executable, 'tools/build_agent.py', '--core', str(source), '--out', str(folder)], cwd=ROOT, check=True)
assert (OUT / 'candidates/control/agent.py').read_bytes() == (ROOT / 'submission/agent.py').read_bytes()
print(json.dumps({label: hashlib.sha256((OUT / 'candidates' / label / 'agent.py').read_bytes()).hexdigest() for label in cores}, indent=2))
