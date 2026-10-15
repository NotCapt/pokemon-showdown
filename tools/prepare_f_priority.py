"""Preserve legal priority attacks when pruning the opposing action list."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'archive/v4_3_2/agent_core.py').read_text()
old="        candidates=foe_moves[:3]\n        for m in moves_for(b):"
new="""        candidates=foe_moves[:3]
        priority=next((m for m in foe_moves if m.get('priority',0)>0 and m.get('base_power',0)),None)
        if priority and priority not in candidates:
            candidates=candidates[:2]+[priority]
        for m in moves_for(b):"""
assert old in s
s=s.replace(old,new)
(root/'research/f-priority-core.py').write_text(s)
# A second, separately scored hypothesis covers a coherent alternate attacking
# build for off-role priority coverage; it is an explicit prior, not inference.
q=s
q=q.replace("        weights=[(2 if m['id'] in b['moves'] else .6) for m in candidates]", """        threats=[(m,b,2 if m['id'] in b['moves'] else .6) for m in candidates]
        raw_foe=o.get('foe') or {}
        alternate=None
        if priority and priority['id'] not in b['moves'] and not any(k in raw_foe for k in ('stats','nature','evs')):
            physical=priority.get('category')=='Physical'
            variant=dict(raw_foe,nature='Adamant' if physical else 'Modest',
                         evs='252 Atk / 252 Spe / 4 SpD' if physical else '252 SpA / 252 Spe / 4 SpD')
            alternate=build_mon(variant)
            alternate['boosts']=dict(b['boosts'])
            alternate['moves']=[priority['id']]+[mid for mid in b['moves'] if mid!=priority['id']][:3]
            threats.append((priority,alternate,.6))
        weights=[weight for enemy,model,weight in threats]""")
head,q=q.split('class PokemonAgent:',1)
q=q.replace('            for enemy in candidates:', '            for enemy,foe_model,weight in threats:')
q=q.replace("stat(a,'spe',weather)==stat(b,'spe',weather)","stat(a,'spe',weather)==stat(foe_model,'spe',weather)")
q=q.replace('flinch_chance(a,m,b)>0 or flinch_chance(b,enemy,a)>0','flinch_chance(a,m,foe_model)>0 or flinch_chance(foe_model,enemy,a)>0')
q=q.replace("stat(a,'spe',weather)>stat(b,'spe',weather)","stat(a,'spe',weather)>stat(foe_model,'spe',weather)")
q=q.replace('fp=flinch_chance(a,m,b) if own_first and own_hit else flinch_chance(b,enemy,a)', 'fp=flinch_chance(a,m,foe_model) if own_first and own_hit else flinch_chance(foe_model,enemy,a)')
q=q.replace('                    y=clone_mon(b)','                    y=clone_mon(foe_model)')
(root/'research/f-priority-alt-core.py').write_text(head+'class PokemonAgent:'+q)
