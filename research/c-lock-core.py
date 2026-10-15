"""REDLINE: bounded simultaneous-action search. Generated data precedes this file.

Standard library only. The simulator below is deliberately approximate; actual
Showdown, not this model, is used for benchmark results. Unknown enemy sets are
priors, never privileged information. No network, subprocesses or file reads.
"""
import math
import re


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
    if (k,item) in [('atk','choiceband'),('spa','choicespecs'),('spe','choicescarf'),('spd','assaultvest')]: result *= 1.5
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
    return [dict(DATA['moves'][n]) for n in names if n in DATA['moves']]


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
    if a.get('locked') in DATA['moves']: choices=[dict(DATA['moves'][a['locked']])]
    def utility(m):
        d=damage(a,b,m,weather)
        priority=m.get('priority',0)
        first=priority>0 or (priority==0 and stat(a,'spe',weather)>stat(b,'spe',weather))
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
    if mid=='suckerpunch' and b.get('using_status'): d=0
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
    pa,pb=ma.get('priority',0),mb.get('priority',0)
    sa,sb=stat(a,'spe',weather),stat(b,'spe',weather)
    faster=pa>pb or (pa==pb and (sa>sb or (sa==sb and tie_first)))
    order=((a,b,ma),(b,a,mb)) if faster else ((b,a,mb),(a,b,ma))
    flinch=0
    for i,(p,q,m) in enumerate(order):
        if p['hp']<=0 or q['hp']<=0: continue
        if i==1 and flinch==1: continue
        before=q['hp']
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


class PokemonAgent:
    def __init__(self):
        self.last_switch_turn=-100
        self.last_turn=0
        self.active_key=None
        self.estimated_boosts={}
        self.pending=None
        self.setup_attempts={}
        self.last_foe_key=None
        self.foe_boost_est={}
        self.entry_boosts={}

    def decide(self, observation):
        o=observation or {}
        if o.get('team_preview'): return 'team 123'
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
            outcomes=[]
            for enemy in candidates:
                # Three deterministic damage quantiles, no expensive random rollouts.
                vals=[]
                # Enumerate independent first-turn hit/miss outcomes exactly,
                # averaged over three damage quantiles.
                tied=bool(m) and m.get('priority',0)==enemy.get('priority',0) and stat(a,'spe',weather)==stat(b,'spe',weather)
                order_count=2 if tied else 1
                flinch_count=2 if m and (flinch_chance(a,m,b)>0 or flinch_chance(b,enemy,a)>0) else 1
                for sample in range(12*order_count*flinch_count):
                    roll=(.85,.925,1.0)[sample%3]
                    branch=(sample//3)%4
                    own_hit=bool(branch&1); enemy_hit=bool(branch&2)
                    own_p=accuracy(m) if m else 1.
                    enemy_p=accuracy(enemy)
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
                    x=build_mon(s,True) if s else clone_mon(a)
                    y=clone_mon(b)
                    starting_hp=x['hp']
                    initial=value(x,y)
                    if s:
                        x['boosts']={}
                        enter_intimidate(x,y)
                        if not o.get('force_switch'): apply_move(y,x,enemy_move,weather,roll); end_turn(x,y,weather)
                    else: turn(x,y,own_move,enemy_move,weather,roll,tie_first=tie_first)
                    first=value(x,y)
                    if continuation_turn<=100 and x['hp']>0 and y['hp']>0:
                        turn(x,y,best_attack(x,y,weather),best_attack(y,x,weather),weather,roll)
                    second=value(x,y)
                    if continuation_turn<100 and x['hp']>0 and y['hp']>0:
                        turn(x,y,best_attack(x,y,weather),best_attack(y,x,weather),weather,roll)
                    # Evaluate progress plus future matchup, rather than sacrificing
                    # healthy reserves just to increase the active HP display.
                    score=(first-initial)+.65*(second-first)+.40*(value(x,y)-second)+.12*value(x,y)
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
        command=max(scored,key=lambda v:v[0])[1]
        if command.startswith('switch'):
            self.last_switch_turn=turn_no
            self.active_key=None; self.pending=None
            target=next(s for cmd,m,s in actions if cmd==command)
            entering=build_mon(target,True)
            defender=clone_mon(b)
            enter_intimidate(entering,defender)
            self.entry_boosts=dict(entering['boosts'])
            self.foe_boost_est=dict(defender['boosts'])
        else:
            selected=next(m for cmd,m,s in actions if cmd==command)
            self.pending=(turn_no,selected)
            if selected.get('boosts') and selected.get('target')=='self':
                mid=selected['id']; self.setup_attempts[mid]=self.setup_attempts.get(mid,0)+1
        return command
