"""REDLINE: bounded simultaneous-action search. Generated data precedes this file.

Standard library only. The simulator below is deliberately approximate; actual
Showdown, not this model, is used for benchmark results. Unknown enemy sets are
priors, never privileged information. No network, subprocesses or file reads.
"""
import math
import re

_CHOICE_STATS = {'atk': 'choiceband', 'spa': 'choicespecs',
                 'spe': 'choicescarf', 'spd': 'assaultvest'}


def clone_mon(mon):
    result=mon.copy()
    result['boosts']=mon['boosts'].copy()
    return result


def enter_intimidate(entering,target):
    if entering['ability']!='intimidate' or target['hp']<=0: return
    if target['ability'] in ('clearbody','innerfocus'): return
    victim=entering if target['ability']=='mirrorarmor' else target
    victim['boosts']['atk']=max(-6,victim['boosts'].get('atk',0)-1)


def ident(value):
    return re.sub('[^a-z0-9]', '', str(value).lower())


def stage(n):
    n = max(-6, min(6, n))
    return (2+n)/2 if n >= 0 else 2/(2-n)


def effectiveness(kind, types, move=''):
    result = 1.0
    for t in types:
        v = DATA['chart'].get(t, {}).get(kind, 0)
        result *= (1, 2, .5, 0)[v] if isinstance(v, int) and 0 <= v <= 3 else 1
        if move == 'freezedry' and t == 'Water':
            result *= 4
    return result


def build_mon(obs, own=False):
    name = obs.get('species') or obs.get('name', '')
    key = ident(name)
    base = DATA['species'].get(key, {})
    config = OWN.get(key, {}) if own else {}
    nature = obs.get('nature') or config.get('nature') or base.get('defaultNature', 'Hardy')
    evs = obs.get('evs') or config.get('evs') or base.get('defaultEvs', '')
    if isinstance(evs, str):
        evs = {k.lower():int(v) for v,k in re.findall(r'(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)', evs, re.I)}
    level = obs.get('level') or 100
    stats = {}
    for k, v in base.get('stats', dict(hp=80,atk=90,def_=80,spa=90,spd=80,spe=80)).items():
        if k == 'def_': k = 'def'
        stat = math.floor((2*v+31+int(evs.get(k,0))//4)*level/100) + (level+10 if k == 'hp' else 5)
        n = DATA['natures'].get(nature, {})
        if k == n.get('plus'): stat = math.floor(stat*1.1)
        if k == n.get('minus'): stat = math.floor(stat*.9)
        stats[k] = stat
    stats.update(obs.get('stats') or {})
    condition = str(obs.get('condition', ''))
    if '/' in condition:
        try: stats['hp'] = int(condition.split('/')[1].split()[0])
        except ValueError: pass
    status = obs.get('status', '') or next((x for x in ('brn','par','slp','frz','tox','psn') if x in condition), '')
    return dict(name=name, key=key, types=obs.get('types') or base.get('types', []),
                hp=float(obs.get('hp_percent',100) or 0), stats=stats, level=level,
                boosts=dict(obs.get('boosts') or {}), status=status,
                ability=ident(obs.get('ability') if 'ability' in obs else config.get('ability',base.get('defaultAbility',''))),
                item=ident(obs.get('item') if 'item' in obs else config.get('item',base.get('defaultItem',''))),
                moves=[ident(m) for m in config.get('moves',base.get('defaultMoves',[]))],
                protean_used=bool(obs.get('types') and obs['types']!=base.get('types',[])),
                seed=False, protect=False, sleep=0)


def stat(mon, k, weather=''):
    result = mon['stats'].get(k,100)*stage(mon['boosts'].get(k,0))
    item = mon['item']
    if item and item == _CHOICE_STATS.get(k): result *= 1.5
    if k == 'spe':
        if mon['status']=='par': result *= .5
        if (weather in ('sand','sandstorm') and mon['ability']=='sandrush') or (weather in ('sun','sunnyday') and mon['ability']=='chlorophyll'): result *= 2
    if k == 'spd' and 'Rock' in mon['types'] and weather in ('sand','sandstorm'): result *= 1.5
    return result


def damage(a,b,m,weather='',roll=.925):
    power = m.get('base_power',0) or 0
    mid = m.get('id','')
    physical = m.get('category') == 'Physical'
    typ = m.get('type','Normal')
    if mid == 'bodypress': attack = stat(a,'def',weather)
    else: attack = stat(a,'atk' if physical else 'spa',weather)
    defense = stat(b,'def' if physical or mid=='psyshock' else 'spd',weather)
    if mid == 'gyroball': power = min(150,25*stat(b,'spe',weather)/max(1,stat(a,'spe',weather))+1)
    if mid in ('lowkick','grassknot'):
        w=DATA['species'].get(b['key'],{}).get('weight',100)
        power = 20+20*sum(w>=t for t in [10,25,50,100,200])
    if mid == 'heavyslam':
        ratio=DATA['species'].get(a['key'],{}).get('weight',100)/max(1,DATA['species'].get(b['key'],{}).get('weight',100))
        power=40+20*sum(ratio>=t for t in [2,3,4,5])
    if not power: return 0.
    mult = effectiveness(typ,b['types'],mid)
    mold = a['ability']=='moldbreaker'
    if not mold:
        if (typ=='Ground' and b['ability']=='levitate') or (typ=='Water' and b['ability']=='waterabsorb') or (typ=='Fire' and b['ability']=='flashfire'): return 0.
        if b['ability']=='thickfat' and typ in ('Fire','Ice'): mult *= .5
        if b['ability']=='multiscale' and b['hp']>=99.9: mult *= .5
    if a['ability']=='technician' and power<=60: mult *= 1.5
    if a['ability'] in ('blaze','torrent','overgrow','swarm') and a['hp']<=100/3 and typ==dict(blaze='Fire',torrent='Water',overgrow='Grass',swarm='Bug')[a['ability']]: mult *= 1.5
    if a['item']=='lifeorb': mult *= 1.3
    if a['item']=='expertbelt' and mult>1: mult *= 1.2
    if a['item']=='metalcoat' and typ=='Steel': mult *= 1.2
    if typ in a['types'] or (a['ability']=='protean' and not a.get('protean_used')): mult *= 1.5
    if a['status']=='brn' and physical: mult *= .5
    if weather in ('rain','raindance'): mult *= 1.5 if typ=='Water' else .5 if typ=='Fire' else 1
    if weather in ('sun','sunnyday'): mult *= 1.5 if typ=='Fire' else .5 if typ=='Water' else 1
    if mid=='knockoff' and b['item']: power *= 1.5
    hits=1
    if mid=='dragondarts': hits=2
    elif m.get('multihit'):
        count=m['multihit']; hits=count if isinstance(count,int) else 3
    result = ((2*a['level']/5+2)*power*attack/max(1,defense)/50+2)*mult*roll
    # Multiscale applies only to the first hit when it breaks full HP.
    result *= (2*hits-1) if hits>1 and b['ability']=='multiscale' and b['hp']>=99.9 and not mold else hits
    return 100*result/max(1,b['stats']['hp'])


def moves_for(mon, coverage=False):
    base=DATA['species'].get(mon['key'],{})
    names=mon['moves'][:]
    if coverage:
        names += [ident(x) for x in base.get('legalMoves',[]) if ident(x) not in names]
    # Move definitions stay read-only; chance annotations use branch copies.
    return [DATA['moves'][n] for n in names if n in DATA['moves']]


def accuracy(m):
    a=m.get('accuracy',100)
    return 1. if a is True or a is None else max(0,min(1,float(a)/100))


def flinch_chance(mon,move,target):
    if target['ability']=='innerfocus': return 0.
    secondary=move.get('secondary') or {}
    if secondary.get('volatileStatus')!='flinch': return 0.
    return min(1.,secondary.get('chance',0)/100*(2 if mon['ability']=='serenegrace' else 1))


def best_attack(a,b,weather):
    choices=moves_for(a)
    if a.get('locked') in DATA['moves']: choices=[DATA['moves'][a['locked']]]
    faster=stat(a,'spe',weather)>stat(b,'spe',weather)
    def utility(m):
        d=damage(a,b,m,weather)
        priority=m.get('priority',0)
        first=priority>0 or (priority==0 and faster)
        ko=sum(d*r/.925>=b['hp'] for r in (.85,.925,1.0))/3
        return accuracy(m)*(min(d,b['hp'])+ko*(65 if first else 30))
    return max(choices, key=utility, default={'id':'splash','category':'Status','base_power':0})


def apply_move(a,b,m,weather,roll):
    if a['hp']<=0 or a['status']=='frz': return
    if a['status']=='slp' and m.get('id')!='sleeptalk':
        a['sleep']+=1
        if a['sleep']<2: return
        a['status']=''
    mid=m.get('id','')
    if a['item'] in ('choiceband','choicespecs','choicescarf'): a['locked']=mid
    if a['ability']=='protean' and not a.get('protean_used') and m.get('type'):
        a['types']=[m['type']]; a['protean_used']=True
    if m.get('_hit') is False: return
    if mid=='protect': a['protect']=True; return
    if b['protect'] and m.get('target') not in ('self','allySide'): return
    if m.get('heal') or mid=='rest':
        a['hp']=min(100,a['hp']+(100 if mid=='rest' else 50))
        if mid=='rest': a['status']='slp'; a['sleep']=0
        return
    if m.get('boosts') and m.get('target')=='self':
        for k,v in m['boosts'].items(): a['boosts'][k]=max(-6,min(6,a['boosts'].get(k,0)+v))
        return
    if mid=='leechseed':
        if 'Grass' not in b['types']: b['seed']=True
        return
    if m.get('status'):
        s=m['status']; immune=(s in ('psn','tox') and any(t in b['types'] for t in ('Steel','Poison'))) or (s=='brn' and 'Fire' in b['types']) or (s=='par' and ('Electric' in b['types'] or (mid=='thunderwave' and 'Ground' in b['types']))) or (mid=='sleeppowder' and 'Grass' in b['types'])
        if not b['status'] and not immune: b['status']=s
        if b['item']=='lumberry': b['status']=''; b['item']=''
    d=damage(a,b,m,weather,roll)*(1 if m.get('_hit') else accuracy(m))
    if mid in ('phantomforce','bounce','solarbeam','gigaimpact'): d *= .55
    if mid=='suckerpunch' and (b.get('using_status') or b.get('acted')): d=0
    if d<=0: return
    before=b['hp']
    if b['item']=='focussash' and before>=99.9 and d>=before and not m.get('multihit') and mid!='dragondarts':
        d=before-100/max(1,b['stats']['hp']); b['item']=''
    b['hp']=max(0,b['hp']-d)
    actual=before-b['hp']
    if b['item']=='weaknesspolicy' and effectiveness(m.get('type'),b['types'],mid)>1:
        for k in ('atk','spa'): b['boosts'][k]=min(6,b['boosts'].get(k,0)+2)
        b['item']=''
    if m.get('drain'):
        a['hp']=min(100,a['hp']+actual*b['stats']['hp']/a['stats']['hp']*m['drain'][0]/m['drain'][1])
    if m.get('recoil') and a['ability']!='magicguard': a['hp']=max(0,a['hp']-actual*b['stats']['hp']/a['stats']['hp']*m['recoil'][0]/m['recoil'][1])
    if a['item']=='lifeorb' and a['ability']!='magicguard': a['hp']=max(0,a['hp']-10)
    if m.get('flags',{}).get('contact') and a['ability']!='magicguard':
        if b['ability'] in ('roughskin','ironbarbs'): a['hp']=max(0,a['hp']-12.5)
        if b['item']=='rockyhelmet': a['hp']=max(0,a['hp']-100/6)
    if m.get('self',{}).get('boosts'):
        for k,v in m['self']['boosts'].items(): a['boosts'][k]=max(-6,min(6,a['boosts'].get(k,0)+v))
    if b['hp']==0 and a['ability']=='moxie': a['boosts']['atk']=min(6,a['boosts'].get('atk',0)+1)


def end_turn(a,b,weather):
    for p,q in ((a,b),(b,a)):
        if p['hp']<=0: continue
        p['protect']=False
        if p['item']=='leftovers' or (p['item']=='blacksludge' and 'Poison' in p['types']): p['hp']=min(100,p['hp']+6.25)
        if p['ability']=='magicguard': continue
        loss={'brn':6.25,'psn':12.5,'tox':12.5}.get(p['status'],0)
        if p['seed']: loss+=12.5; q['hp']=min(100,q['hp']+12.5*p['stats']['hp']/q['stats']['hp']) if q['hp']>0 else 0
        if weather in ('sand','sandstorm') and not any(t in p['types'] for t in ('Rock','Ground','Steel')): loss+=6.25
        p['hp']=max(0,p['hp']-loss)


def turn(a,b,ma,mb,weather,roll,tie_first=True):
    a['using_status']=ma.get('category')=='Status'; b['using_status']=mb.get('category')=='Status'
    a['acted']=b['acted']=False
    pa,pb=ma.get('priority',0),mb.get('priority',0)
    sa,sb=stat(a,'spe',weather),stat(b,'spe',weather)
    faster=pa>pb or (pa==pb and (sa>sb or (sa==sb and tie_first)))
    order=((a,b,ma),(b,a,mb)) if faster else ((b,a,mb),(a,b,ma))
    flinch=0
    for i,(p,q,m) in enumerate(order):
        if p['hp']<=0 or q['hp']<=0: continue
        if i==1 and flinch==1: continue
        before=q['hp']
        p['acted']=True
        apply_move(p,q,m,weather,roll)
        # Expected-value flinch approximation, not a full chance tree.
        if i==1 and flinch: q['hp']+=max(0,before-q['hp'])*flinch
        secondary=m.get('secondary') or {}
        if i==0 and secondary.get('volatileStatus')=='flinch' and q['ability']!='innerfocus':
            if '_flinch' in m:
                flinch=int(m['_flinch'] and m.get('_hit') is not False)
            else:
                flinch=flinch_chance(p,m,q)*accuracy(m)
    end_turn(a,b,weather)


def value(a,b):
    # KO dominates fractional HP; alive reserves retain strategic value.
    v=a['hp']-b['hp']+100*(int(a['hp']>0)-int(b['hp']>0))
    for p,sign in ((a,1),(b,-1)):
        if p['hp']>0:
            v+=sign*(6*p['boosts'].get('atk',0)+6*p['boosts'].get('spa',0)+4*p['boosts'].get('spe',0))
            v-=sign*{'slp':22,'brn':12,'par':15,'tox':18,'psn':8,'frz':35}.get(p['status'],0)
    return v


def entry_damage(mon,state):
    """Exact floor damage for one plausible (Stealth Rock, Spikes) state."""
    if mon['item']=='heavydutyboots' or mon['ability']=='magicguard': return 0.
    rock,layers=state
    hp=max(1,mon['stats']['hp'])
    loss=max(1,math.floor(hp*effectiveness('Rock',mon['types'])/8)) if rock else 0
    if layers and 'Flying' not in mon['types'] and mon['ability']!='levitate':
        loss+=max(1,math.floor(hp/(8 if layers==1 else 6 if layers==2 else 4)))
    return 100*loss/hp


MC_PRIORS = {'garchomp': [{'name': 'Garchomp', 'item': 'Life Orb', 'ability': 'Rough Skin', 'nature': 'Jolly', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Earthquake', 'Outrage', 'Stone Edge', 'Swords Dance']}, {'name': 'Garchomp', 'item': 'Choice Scarf', 'ability': 'Rough Skin', 'nature': 'Jolly', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Earthquake', 'Outrage', 'Stone Edge', 'Iron Head']}, {'name': 'Garchomp', 'item': 'Choice Scarf', 'ability': 'Rough Skin', 'nature': 'Jolly', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Earthquake', 'Outrage', 'Stone Edge', 'Swords Dance']}], 'dragonite': [{'name': 'Dragonite', 'item': 'Lum Berry', 'ability': 'Multiscale', 'nature': 'Adamant', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Extreme Speed', 'Outrage', 'Earthquake', 'Fire Punch']}, {'name': 'Dragonite', 'item': 'Weakness Policy', 'ability': 'Multiscale', 'nature': 'Adamant', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Dragon Dance', 'Extreme Speed', 'Earthquake', 'Ice Spinner']}, {'name': 'Dragonite', 'ability': 'Multiscale', 'item': 'Choice Band', 'nature': 'Adamant', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Extreme Speed', 'Earthquake', 'Ice Spinner', 'Fire Punch']}, {'name': 'Dragonite', 'item': 'Choice Scarf', 'ability': 'Multiscale', 'nature': 'Adamant', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Extreme Speed', 'Outrage', 'Earthquake', 'Fire Punch']}], 'tyranitar': [{'name': 'Tyranitar', 'item': 'Leftovers', 'ability': 'Sand Stream', 'nature': 'Adamant', 'evs': 'Bulky Attacker (252 HP / 252 Atk / 4 SpD)', 'moves': ['Stone Edge', 'Crunch', 'Earthquake', 'Ice Punch']}, {'name': 'Tyranitar', 'item': 'Choice Scarf', 'ability': 'Sand Stream', 'nature': 'Adamant', 'evs': 'Bulky Attacker (252 HP / 252 Atk / 4 SpD)', 'moves': ['Stone Edge', 'Crunch', 'Earthquake', 'Ice Punch']}], 'hydreigon': [{'name': 'Hydreigon', 'item': 'Choice Specs', 'ability': 'Levitate', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Dark Pulse', 'Draco Meteor', 'Flamethrower', 'Flash Cannon']}, {'name': 'Hydreigon', 'item': 'Choice Scarf', 'ability': 'Levitate', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Dark Pulse', 'Draco Meteor', 'Flamethrower', 'Flash Cannon']}], 'dragapult': [{'name': 'Dragapult', 'item': 'Choice Band', 'ability': 'Infiltrator', 'nature': 'Jolly', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Dragon Darts', 'Phantom Force', 'Flamethrower', 'U-turn']}, {'name': 'Dragapult', 'item': 'Choice Specs', 'ability': 'Infiltrator', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Shadow Ball', 'Draco Meteor', 'Flamethrower', 'Thunderbolt']}, {'name': 'Dragapult', 'item': 'Choice Scarf', 'ability': 'Infiltrator', 'nature': 'Jolly', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Dragon Darts', 'Phantom Force', 'Flamethrower', 'U-turn']}], 'volcarona': [{'name': 'Volcarona', 'item': 'Heavy-Duty Boots', 'ability': 'Flame Body', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Fiery Dance', 'Bug Buzz', 'Giga Drain', 'Quiver Dance']}, {'name': 'Volcarona', 'item': 'Lum Berry', 'ability': 'Flame Body', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Fiery Dance', 'Bug Buzz', 'Giga Drain', 'Quiver Dance']}, {'name': 'Volcarona', 'item': 'Choice Scarf', 'ability': 'Flame Body', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Fiery Dance', 'Bug Buzz', 'Giga Drain', 'Quiver Dance']}], 'scizor': [{'name': 'Scizor', 'item': 'Metal Coat', 'ability': 'Technician', 'nature': 'Adamant', 'evs': 'Bulky Attacker (252 HP / 252 Atk / 4 SpD)', 'moves': ['Bullet Punch', 'Close Combat', 'Swords Dance', 'U-turn']}, {'name': 'Scizor', 'item': 'Choice Band', 'ability': 'Technician', 'nature': 'Adamant', 'evs': 'Bulky Attacker (252 HP / 252 Atk / 4 SpD)', 'moves': ['Bullet Punch', 'Close Combat', 'Knock Off', 'U-turn']}, {'name': 'Scizor', 'item': 'Choice Scarf', 'ability': 'Technician', 'nature': 'Adamant', 'evs': 'Bulky Attacker (252 HP / 252 Atk / 4 SpD)', 'moves': ['Bullet Punch', 'Close Combat', 'Swords Dance', 'U-turn']}], 'gengar': [{'name': 'Gengar', 'item': 'Life Orb', 'ability': 'Cursed Body', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Shadow Ball', 'Sludge Bomb', 'Focus Blast', 'Thunderbolt']}, {'name': 'Gengar', 'item': 'Focus Sash', 'ability': 'Cursed Body', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Shadow Ball', 'Sludge Bomb', 'Focus Blast', 'Thunderbolt']}, {'name': 'Gengar', 'item': 'Choice Scarf', 'ability': 'Cursed Body', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Shadow Ball', 'Sludge Bomb', 'Focus Blast', 'Thunderbolt']}], 'charizard': [{'name': 'Charizard', 'item': 'Choice Specs', 'ability': 'Blaze', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Flamethrower', 'Air Slash', 'Focus Blast', 'Dragon Pulse']}, {'name': 'Charizard', 'item': 'Choice Scarf', 'ability': 'Blaze', 'nature': 'Timid', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Flamethrower', 'Air Slash', 'Focus Blast', 'Dragon Pulse']}], 'blastoise': [{'name': 'Blastoise', 'item': 'Leftovers', 'ability': 'Torrent', 'nature': 'Modest', 'evs': 'Bulky Special (252 HP / 252 SpA / 4 SpD)', 'moves': ['Hydro Pump', 'Ice Beam', 'Flash Cannon', 'Protect']}, {'name': 'Blastoise', 'item': 'Choice Scarf', 'ability': 'Torrent', 'nature': 'Modest', 'evs': 'Bulky Special (252 HP / 252 SpA / 4 SpD)', 'moves': ['Hydro Pump', 'Ice Beam', 'Flash Cannon', 'Protect']}], 'venusaur': [{'name': 'Venusaur', 'item': 'Black Sludge', 'ability': 'Overgrow', 'nature': 'Modest', 'evs': 'Bulky Special (252 HP / 252 SpA / 4 SpD)', 'moves': ['Giga Drain', 'Sludge Bomb', 'Earth Power', 'Sleep Powder']}, {'name': 'Venusaur', 'item': 'Choice Scarf', 'ability': 'Overgrow', 'nature': 'Modest', 'evs': 'Bulky Special (252 HP / 252 SpA / 4 SpD)', 'moves': ['Giga Drain', 'Sludge Bomb', 'Earth Power', 'Sleep Powder']}], 'excadrill': [{'name': 'Excadrill', 'item': 'Focus Sash', 'ability': 'Mold Breaker', 'nature': 'Jolly', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Earthquake', 'Iron Head', 'Rock Slide', 'Swords Dance']}, {'name': 'Excadrill', 'item': 'Life Orb', 'ability': 'Sand Rush', 'nature': 'Jolly', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Earthquake', 'Iron Head', 'Rock Slide', 'Swords Dance']}, {'name': 'Excadrill', 'item': 'Choice Scarf', 'ability': 'Mold Breaker', 'nature': 'Jolly', 'evs': 'Physical Sweeper (252 Atk / 252 Spe / 4 SpD)', 'moves': ['Earthquake', 'Iron Head', 'Rock Slide', 'Swords Dance']}], 'togekiss': [{'name': 'Togekiss', 'item': 'Choice Scarf', 'ability': 'Serene Grace', 'nature': 'Modest', 'evs': 'Special Sweeper (252 SpA / 252 Spe / 4 SpD)', 'moves': ['Air Slash', 'Dazzling Gleam', 'Flamethrower', 'Aura Sphere']}], 'lapras': [{'name': 'Lapras', 'item': 'Leftovers', 'ability': 'Water Absorb', 'nature': 'Modest', 'evs': 'Bulky Special (252 HP / 252 SpA / 4 SpD)', 'moves': ['Freeze-Dry', 'Hydro Pump', 'Thunderbolt', 'Ice Beam']}, {'name': 'Lapras', 'item': 'Choice Scarf', 'ability': 'Water Absorb', 'nature': 'Modest', 'evs': 'Bulky Special (252 HP / 252 SpA / 4 SpD)', 'moves': ['Freeze-Dry', 'Hydro Pump', 'Thunderbolt', 'Ice Beam']}], 'corviknight': [{'name': 'Corviknight', 'item': 'Leftovers', 'ability': 'Mirror Armor', 'nature': 'Impish', 'evs': 'Physical Wall (252 HP / 252 Def / 4 SpD)', 'moves': ['Brave Bird', 'Body Press', 'Roost', 'Iron Defense']}, {'name': 'Corviknight', 'ability': 'Mirror Armor', 'item': 'Leftovers', 'nature': 'Impish', 'evs': 'Physical Wall (252 HP / 252 Def / 4 SpD)', 'moves': ['Body Press', 'Iron Defense', 'Roost', 'Brave Bird']}, {'name': 'Corviknight', 'item': 'Choice Scarf', 'ability': 'Mirror Armor', 'nature': 'Impish', 'evs': 'Physical Wall (252 HP / 252 Def / 4 SpD)', 'moves': ['Brave Bird', 'Body Press', 'Roost', 'Iron Defense']}]}

"""Bounded root-bandit Monte Carlo; injected into a standalone agent.

This is rollout search, not full information-set MCTS or a Nash solver.
Both players choose using public opponent views. The transition model retains
the selected base engine's approximations; no enemy reserve is invented.
"""
import random

MC_ROLLOUTS = 96
MC_HORIZON = 6


def mc_seed(turn_no, a, b):
    text = repr((turn_no, a['key'], b['key'], round(a['hp'], 2), round(b['hp'], 2),
                 sorted(a['boosts'].items()), sorted(b['boosts'].items()), a['status'], b['status']))
    seed = 2166136261
    for char in text:
        seed = ((seed ^ ord(char)) * 16777619) & 0xffffffff
    return seed


def mc_public(mon):
    # Do not let a rollout policy condition on the other player's sampled set.
    view = build_mon(dict(name=mon['name'], hp_percent=mon['hp'],
                          types=mon['types'], status=mon['status'], boosts=mon['boosts']))
    return view


def mc_hypothesis(foe, observed, rng):
    priors = MC_PRIORS.get(foe['key'], [])
    config = rng.choice(priors) if priors and rng.random() < .5 else {}
    # Explicit public fields take precedence over our sampled hidden prior.
    raw = dict(config)
    raw.update(observed)
    mon = build_mon(raw)
    if config.get('moves'):
        mon['moves'] = [ident(m) for m in config['moves']]
    mon['boosts'] = dict(foe['boosts'])
    return mon


def mc_move_scores(mon, target, weather):
    if mon.get('phantom_charging'):
        return [(DATA['moves']['phantomforce'], 100.)]
    choices = moves_for(mon)
    if mon.get('locked') in DATA['moves']:
        choices = [DATA['moves'][mon['locked']]]
    scored = []
    incoming = damage(target, mon, best_attack(target, mon, weather), weather)
    for move in choices:
        mid = move['id']
        if move.get('category') != 'Status':
            d = damage(mon, target, move, weather)
            first = move.get('priority', 0) > 0 or (move.get('priority', 0) == 0 and stat(mon, 'spe', weather) > stat(target, 'spe', weather))
            score = accuracy(move) * (min(d, target['hp']) + (55 if first else 25) * (d >= target['hp']))
            if mid in ('phantomforce', 'bounce', 'solarbeam', 'gigaimpact'):
                score *= .65
            if move.get('recoil'):
                score -= min(d, target['hp']) * .2
            if mid == 'suckerpunch' and target['status'] == 'slp':
                score *= .3
        elif move.get('heal') or mid == 'rest':
            healing = min(100 - mon['hp'], 100 if mid == 'rest' else 50)
            score = healing * .8 - incoming * .35 - (14 if mid == 'rest' else 0)
            if mon['hp'] >= 85:
                score = -100
        elif move.get('boosts') and move.get('target') == 'self':
            gains = sum(max(0, min(v, 6 - mon['boosts'].get(k, 0))) for k, v in move['boosts'].items())
            score = 13 * gains - incoming * .65
            if mon['hp'] <= incoming or not gains:
                score = -100
        elif move.get('status'):
            score = 20 * accuracy(move) if not target['status'] else -100
        elif mid == 'leechseed':
            score = 16 if not target['seed'] and 'Grass' not in target['types'] else -100
        else:
            score = -100
        scored.append((move, score))
    return scored or [({'id': 'splash', 'category': 'Status', 'base_power': 0}, -100.)]


def mc_policy(mon, opponent, weather, rng):
    # A simulated player sees its own set and only a public view of the other.
    scored = mc_move_scores(mon, mc_public(opponent), weather)
    scored.sort(key=lambda pair: pair[1], reverse=True)
    if rng.random() < .85 or len(scored) == 1:
        return scored[0][0]
    choices = scored[:3]
    weights = [math.exp(max(-20., (score - choices[0][1]) / 18.)) for _, score in choices]
    return rng.choices([move for move, _ in choices], weights=weights, k=1)[0]


def mc_turn(a, b, ma, mb, weather, rng):
    # Simultaneous choices precede all hit, speed-tie, damage and flinch rolls.
    a['using_status'] = ma.get('category') == 'Status'
    b['using_status'] = mb.get('category') == 'Status'
    a['acted'] = b['acted'] = False
    pa, pb = ma.get('priority', 0), mb.get('priority', 0)
    sa, sb = stat(a, 'spe', weather), stat(b, 'spe', weather)
    first = pa > pb or (pa == pb and (sa > sb or (sa == sb and rng.random() < .5)))
    order = ((a, b, ma), (b, a, mb)) if first else ((b, a, mb), (a, b, ma))
    flinched = False
    for i, (p, q, move) in enumerate(order):
        if p['hp'] <= 0 or q['hp'] <= 0 or (i == 1 and flinched):
            continue
        p['acted'] = True
        if p['status'] == 'par' and rng.random() < .25:
            continue
        sampled = dict(move, _hit=rng.random() < accuracy(move))
        before = q['hp']
        apply_move(p, q, sampled, weather, (.85 + rng.randrange(16) / 100))
        if i == 0 and q['hp'] < before:
            flinched = rng.random() < flinch_chance(p, move, q)
    end_turn(a, b, weather)


def mc_roster(observation, active, switches):
    roster = {}
    for raw in observation.get('my_team') or [observation.get('my_active') or {}] + switches:
        mon = build_mon(raw, True)
        if mon['key']:
            if raw.get('fainted'):
                mon['hp'] = 0
            roster[mon['key']] = mon
    roster[active['key']] = clone_mon(active)
    return roster


def mc_enter(roster, active, target, foe, entry_loss):
    outgoing = roster[active['key']]
    outgoing['boosts'] = {}
    outgoing.pop('locked', None)
    outgoing.pop('phantom_charging', None)
    outgoing.pop('phantom_hidden', None)
    if outgoing['key'] in OWN:
        outgoing['moves'] = [ident(m) for m in OWN[outgoing['key']]['moves']]
    entering = roster[target['key']]
    entering['boosts'] = {}
    entering.pop('locked', None)
    entering['hp'] = max(0, entering['hp'] - entry_loss(entering))
    if entering['hp'] > 0:
        enter_intimidate(entering, foe)
    return entering


def mc_replacement(roster, active, foe, weather, entry_loss):
    living = [p for p in roster.values() if p['hp'] > 0 and p['key'] != active['key']]
    if not living:
        return active
    public = mc_public(foe)
    def utility(p):
        return p['hp'] - entry_loss(p) + damage(p, public, best_attack(p, public, weather), weather) - damage(public, p, best_attack(public, p, weather), weather)
    return mc_enter(roster, active, max(living, key=utility), foe, entry_loss)


def mc_rollout(action, a, b, weather, turn_no, observation, roster, entry_loss, seed):
    rng = random.Random(seed)
    team = {key: clone_mon(p) for key, p in roster.items()}
    x = team[a['key']]
    y = mc_hypothesis(b, observation.get('foe') or {}, rng)
    initial_hp = sum(p['hp'] for p in team.values())
    initial_alive = sum(p['hp'] > 0 for p in team.values())
    initial_value = value(x, y)
    enemy_initial_hp = y['hp']
    root_switch_faint = False
    switched_hp = 0
    command, move, switch = action
    for ply in range(min(MC_HORIZON, 101 - turn_no)):
        if x['hp'] <= 0:
            x = mc_replacement(team, x, y, weather, entry_loss)
        if x['hp'] <= 0 or y['hp'] <= 0:
            break
        if ply == 0:
            own_move = move
        else:
            own_move = mc_policy(x, y, weather, rng)
        # Enemy policy cannot see our simultaneous selected move or switch.
        enemy_move = mc_policy(y, x, weather, rng)
        if ply == 0 and switch:
            target = build_mon(switch, True)
            if target['key'] not in team:
                team[target['key']] = target
            switched_hp = team[target['key']]['hp']
            x = mc_enter(team, x, target, y, entry_loss)
            x['using_status'] = True
            x['acted'] = False
            if x['hp'] > 0:
                sampled = dict(enemy_move, _hit=rng.random() < accuracy(enemy_move))
                apply_move(y, x, sampled, weather, .85 + rng.randrange(16) / 100)
            end_turn(x, y, weather)
            root_switch_faint = x['hp'] <= 0
        else:
            mc_turn(x, y, own_move, enemy_move, weather, rng)
    hp_gain = sum(p['hp'] for p in team.values()) - initial_hp - (y['hp'] - enemy_initial_hp)
    faint_gain = int(y['hp'] <= 0) - (initial_alive - sum(p['hp'] > 0 for p in team.values()))
    score = hp_gain + 100 * faint_gain + .12 * (value(x, y) - initial_value)
    if switch:
        score -= 9
        if root_switch_faint:
            score -= .5 * switched_hp
    return score


def monte_carlo_choice(agent, scored, actions, a, b, weather, turn_no, observation, switches):
    ranked = sorted(scored, key=lambda pair: pair[0], reverse=True)
    baseline = ranked[0][1]
    agent.mc_last = dict(rollouts=0, changed=False, baseline=baseline)
    # Preserve forced-entry and exact capped-HP handling from the base engine.
    if observation.get('force_switch') or turn_no >= 98 or len(ranked) < 2:
        return baseline
    choices = {command: (command, move, switch) for command, move, switch in actions}
    def safe_override(command):
        switch = choices[command][2]
        if command == baseline or not switch:
            return True
        entrant = build_mon(switch, True)
        entrant['hp'] = max(0, entrant['hp'] - agent.entry_loss(entrant))
        if entrant['hp'] <= 0:
            return False
        if entrant['hp'] <= 25:
            return True  # Keep deliberate weak-reserve sacrifices available.
        foe = clone_mon(b)
        enter_intimidate(entrant, foe)
        replies = moves_for(foe, True)
        replies.sort(key=lambda m: damage(foe, entrant, m, weather) * accuracy(m), reverse=True)
        # Monte Carlo averages must not bypass the established reserve guard.
        return not any(damage(foe, entrant, move, weather, 1.) >= entrant['hp'] for move in replies[:3])
    arms = [(score, command) for score, command in ranked[:3]
            if score >= ranked[0][0] - 20 and safe_override(command)]
    if len(arms) < 2:
        return baseline
    roster = mc_roster(observation, a, switches)
    seed = mc_seed(turn_no, a, b)
    samples = [[] for _ in arms]
    for trial in range(MC_ROLLOUTS):
        if trial < 12 * len(arms):
            arm = trial % len(arms)
        else:
            def ucb(i):
                values = samples[i]
                return sum(values) / len(values) / 300 + .4 * math.sqrt(math.log(trial + 1) / len(values))
            arm = max(range(len(arms)), key=ucb)
        # The nth sample of each arm shares its seed, reducing comparison noise.
        scenario_seed = (seed + 104729 * len(samples[arm])) & 0xffffffff
        samples[arm].append(mc_rollout(choices[arms[arm][1]], a, b, weather, turn_no,
                                       observation, roster, agent.entry_loss, scenario_seed))
    estimates = [.65 * prior + .35 * sum(values) / len(values) for (prior, _), values in zip(arms, samples)]
    winner = max(range(len(arms)), key=lambda i: estimates[i])
    selected = baseline
    if winner:
        n = min(len(samples[0]), len(samples[winner]))
        differences = [samples[winner][j] - samples[0][j] for j in range(n)]
        mean = sum(differences) / n
        se = math.sqrt(sum((v - mean) ** 2 for v in differences) / max(1, n - 1) / n)
        if mean > se + 2:
            selected = arms[winner][1]
    agent.mc_last = dict(rollouts=MC_ROLLOUTS, changed=selected != baseline, baseline=baseline,
                         actions=[command for _, command in arms], samples=[len(v) for v in samples],
                         estimates=estimates)
    return selected


class PokemonAgent:
    def __init__(self):
        self.mc_last=None
        self.last_switch_turn=-100
        self.last_turn=0
        self.active_key=None
        self.estimated_boosts={}
        self.pending=None
        self.setup_attempts={}
        self.last_foe_key=None
        self.foe_boost_est={}
        self.entry_boosts={}
        self.hazard_states=None
        self.forced_entry=None

    def observe_entry(self,mon,turn_no):
        pending=self.forced_entry
        self.forced_entry=None
        if not pending or mon['key']!=pending[0] or turn_no not in (pending[2],pending[2]+1): return
        lost=max(0,pending[1]-mon['hp'])
        tolerance=105/max(1,mon['stats']['hp'])
        possible=[]
        for rock in (False,True):
            for layers in range(4):
                state=(rock,layers);damage=entry_damage(mon,state)
                if (damage>=lost-tolerance if mon['hp']<=0 else abs(damage-lost)<=tolerance):
                    possible.append(state)
        if not possible:
            self.hazard_states=None
            return
        prior=set(self.hazard_states or [])
        narrowed=[state for state in possible if state in prior]
        # A changed field can invalidate earlier observations. Restart from the
        # newly compatible states rather than retaining a contradicted estimate.
        self.hazard_states=narrowed or possible

    def entry_loss(self,mon):
        # Infer only damage shared by every compatible field state. A Flying
        # entry cannot establish that Spikes exist beneath it.
        return min((entry_damage(mon,state) for state in self.hazard_states),default=0.) if self.hazard_states else 0.

    def decide(self, observation):
        o=observation or {}
        if o.get('team_preview'):
            self.__init__()
            return 'team 123'
        turn_no=o.get('turn',0)
        cold_start=self.last_turn==0 and turn_no>1
        if turn_no<self.last_turn:
            self.__init__()
        self.last_turn=turn_no
        switches=[s for s in o.get('valid_switches',[]) if not s.get('fainted') and not s.get('active') and s.get('hp_percent',100)>0]
        legal=[m for m in o.get('valid_moves',[]) if not m.get('disabled') and m.get('pp',1)!=0]
        if not legal and not switches: return 'pass'
        a=build_mon(o.get('my_active') or {},True)
        b=build_mon(o.get('foe') or {})
        if 'hp_percent' in (o.get('my_active') or {}): self.observe_entry(a,turn_no)
        else: self.forced_entry=None
        if a['key']!=self.active_key:
            self.active_key=a['key']; self.estimated_boosts=dict(self.entry_boosts); self.entry_boosts={}; self.setup_attempts={}; self.pending=None
        reported=(o.get('my_active') or {}).get('boosts')
        if reported:
            self.estimated_boosts=dict(reported)
        elif self.pending and turn_no>self.pending[0]:
            # An attempted self boost is an estimate: flinches/failed moves are
            # unobservable in the portal. Never repeatedly retry beyond cap.
            previous=self.pending[1]
            delta=previous.get('boosts') if previous.get('target')=='self' else (previous.get('self') or {}).get('boosts')
            for k,v in (delta or {}).items():
                self.estimated_boosts[k]=max(-6,min(6,self.estimated_boosts.get(k,0)+v))
            self.pending=None
        if not reported: a['boosts']=dict(self.estimated_boosts)
        if b['key']!=self.last_foe_key:
            self.foe_boost_est={};self.last_foe_key=b['key']
            if not reported:
                enter_intimidate(b,a)
                self.estimated_boosts=dict(a['boosts'])
        if not (o.get('foe') or {}).get('boosts'):
            b['boosts']=dict(self.foe_boost_est)
        # Continue with the actual equipped moves, not a species default set.
        if legal:
            a['moves']=[ident(m.get('id') or m.get('name')) for m in legal]
            if len(legal)==1 and a['item'] in ('choiceband','choicespecs','choicescarf'):
                a['locked']=a['moves'][0]
        weather=ident(o.get('weather') or '')
        # Defaults get most prior mass; custom coverage is considered pessimistically.
        foe_moves=moves_for(b,True)
        foe_moves.sort(key=lambda m: damage(b,a,m,weather)*accuracy(m)+ (25 if m.get('boosts') else 0),reverse=True)
        candidates=foe_moves[:3]
        for m in moves_for(b):
            if m not in candidates: candidates.append(m)
        candidates=candidates[:7] or [{'id':'splash','category':'Status','base_power':0}]
        weights=[(2 if m['id'] in b['moves'] else .6) for m in candidates]
        actions=[]
        if not o.get('force_switch'):
            for raw in legal:
                mid=ident(raw.get('id') or raw.get('name'))
                # Some integrations omit/static-zero move metadata. Static Dex
                # mechanics are authoritative; availability/index come from API.
                m=dict(raw); m.update(DATA['moves'].get(mid,{})); m['id']=mid
                m['index']=raw['index']
                boosts=m.get('boosts') or {}
                if boosts and m.get('target')=='self':
                    positive=[k for k,v in boosts.items() if v>0]
                    if positive and all(a['boosts'].get(k,0)>=6 for k in positive): continue
                    if cold_start and not any(a['boosts'].values()) and turn_no not in (1,5): continue
                    # Bound setup even with stale/missing boost telemetry or a
                    # service that creates a fresh agent instance every request.
                    if cold_start and turn_no>8: continue
                    if self.setup_attempts.get(mid,0)>=3: continue
                actions.append(('move '+str(raw['index']),m,None))
        for s in switches: actions.append(('switch '+str(s['index']),None,s))
        if not actions:
            return 'move '+str(legal[0]['index']) if legal else 'pass'
        scored=[]
        continuation_turn=turn_no if o.get('force_switch') else turn_no+1
        for command,m,s in actions:
            # Entry stats and configuration are immutable across chance branches.
            entry=build_mon(s,True) if s else a
            own_p=accuracy(m) if m else 1.
            outcomes=[]
            for enemy in candidates:
                # Three deterministic damage quantiles, no expensive random rollouts.
                vals=[]
                enemy_p=accuracy(enemy)
                # Enumerate independent first-turn hit/miss outcomes exactly,
                # averaged over three damage quantiles.
                tied=bool(m) and m.get('priority',0)==enemy.get('priority',0) and stat(a,'spe',weather)==stat(b,'spe',weather)
                order_count=2 if tied else 1
                flinch_count=2 if m and (flinch_chance(a,m,b)>0 or flinch_chance(b,enemy,a)>0) else 1
                for sample in range(12*order_count*flinch_count):
                    roll=(.85,.925,1.0)[sample%3]
                    branch=(sample//3)%4
                    own_hit=bool(branch&1); enemy_hit=bool(branch&2)
                    probability=(own_p if own_hit else 1-own_p)*(enemy_p if enemy_hit else 1-enemy_p)
                    if tied: probability*=.5
                    tie_first=(sample//12)%order_count==0
                    if flinch_count==2:
                        own_first=m.get('priority',0)>enemy.get('priority',0) or (m.get('priority',0)==enemy.get('priority',0) and (stat(a,'spe',weather)>stat(b,'spe',weather) or (tied and tie_first)))
                        fp=flinch_chance(a,m,b) if own_first and own_hit else flinch_chance(b,enemy,a) if not own_first and enemy_hit else 0.
                        flinched=sample//(12*order_count)==1
                        probability*=fp if flinched else 1-fp
                    if probability==0: continue
                    own_move=dict(m) if m else None
                    enemy_move=dict(enemy)
                    if own_move: own_move['_hit']=own_hit
                    enemy_move['_hit']=enemy_hit
                    if flinch_count==2:
                        own_move['_flinch']=flinched
                        enemy_move['_flinch']=flinched
                    x=clone_mon(entry)
                    y=clone_mon(b)
                    starting_hp=x['hp']
                    initial=value(x,y)
                    if s:
                        x['boosts']={}
                        x['using_status']=True  # Switching is not an attacking move.
                        x['hp']=max(0,x['hp']-self.entry_loss(x))
                        if x['hp']>0:
                            enter_intimidate(x,y)
                        if not o.get('force_switch'):
                            if x['hp']>0: apply_move(y,x,enemy_move,weather,roll)
                            end_turn(x,y,weather)
                    else: turn(x,y,own_move,enemy_move,weather,roll,tie_first=tie_first)
                    first=value(x,y)
                    switch_faint=bool(s) and not o.get('force_switch') and x['hp']<=0
                    if continuation_turn<=100 and x['hp']>0 and y['hp']>0:
                        turn(x,y,best_attack(x,y,weather),best_attack(y,x,weather),weather,roll)
                    second=value(x,y)
                    if continuation_turn<100 and x['hp']>0 and y['hp']>0:
                        turn(x,y,best_attack(x,y,weather),best_attack(y,x,weather),weather,roll)
                    # Evaluate progress plus future matchup, rather than sacrificing
                    # healthy reserves just to increase the active HP display.
                    score=(first-initial)+.65*(second-first)+.40*(value(x,y)-second)+.12*value(x,y)
                    # Losing a reserve before it acts also loses its future options.
                    # Scale that cost with HP so a weak sacrifice stays possible.
                    if switch_faint and turn_no<98: score-=.5*starting_hp
                    if s and not o.get('force_switch'):
                        score-=9+(18 if turn_no-self.last_switch_turn<=2 else 0)
                    if m and m.get('id') in ('stealthrock','spikes','toxicspikes'): score+=4 if turn_no<=3 else -15
                    if m and m.get('id') in ('uturn','teleport'): score-=3 if not switches else 0
                    if turn_no>=98:
                        # Unchanged reserves cancel from the summed-HP
                        # tiebreak. There is no extra reward for a KO or for
                        # the number left alive when the turn cap is reached.
                        score=x['hp']-starting_hp-(y['hp']-b['hp'])
                    vals.append(score*probability)
                outcomes.append(sum(vals)/3)
            expected=sum(v*w for v,w in zip(outcomes,weights))/sum(weights)
            robust=.78*expected+.22*min(outcomes)
            scored.append((robust,command))
        command=monte_carlo_choice(self,scored,actions,a,b,weather,turn_no,o,switches)
        if command.startswith('switch'):
            self.last_switch_turn=turn_no
            self.active_key=None; self.pending=None
            target=next(s for cmd,m,s in actions if cmd==command)
            entering=build_mon(target,True)
            # A pivot can leave attacks queued for the entering Pokemon; only
            # a faint replacement gives a clean before/after entry observation.
            if o.get('force_switch') and a['hp']<=0 and target.get('hp_percent') is not None: self.forced_entry=(entering['key'],entering['hp'],turn_no)
            entering['hp']=max(0,entering['hp']-self.entry_loss(entering))
            defender=clone_mon(b)
            if entering['hp']>0: enter_intimidate(entering,defender)
            self.entry_boosts=dict(entering['boosts'])
            self.foe_boost_est=dict(defender['boosts'])
        else:
            selected=next(m for cmd,m,s in actions if cmd==command)
            self.pending=(turn_no,selected)
            if selected.get('boosts') and selected.get('target')=='self':
                mid=selected['id']; self.setup_attempts[mid]=self.setup_attempts.get(mid,0)+1
        return command
