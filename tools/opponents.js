/* Independent evaluation opponent. Knows its own set/state, but infers the
 * enemy from public species/types/rounded HP and curated default sets only.
 * No enemy simulator item, ability, moves, stats or reserve team are accessed.
 */
const {Battle,Dex}=require('pokemon-showdown');
const options=require('../research/options.json');
const memory=new WeakMap();
function defaultSet(name){const p=options.pokemon[name],evs={};
  for(const m of p.defaultEvs.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi))evs[m[2].toLowerCase()]=+m[1];
  return {species:name,ability:p.defaultAbility,item:p.defaultItem,nature:p.defaultNature,evs,moves:p.defaultMoves,level:100};
}
function adaptive(b,side,o){
  if(o.team_preview)return 'team 123';
  const prior=memory.get(side)||{lastSwitch:-99};
  memory.set(side,prior);
  const sets=side.pokemon.map(p=>({...p.set,item:p.item,ability:p.ability,moves:p.moveSlots.map(m=>m.id)}));
  const model=new Battle({formatid:'gen9customgame',seed:[3,5,7,11],
    p1:{name:'model-own',team:sets},p2:{name:'model-foe',team:[defaultSet(o.foe.name)]}});
  model.makeChoices('team 1','team 1');
  model.field.weather=o.weather;
  const foe=model.p2.active[0];
  foe.setType(o.foe.types);foe.hp=Math.max(1,Math.round(foe.maxhp*o.foe.hp_percent/100));
  const own=model.p1.pokemon;
  own.forEach((p,i)=>{const actual=side.pokemon[i];p.hp=actual.hp;p.status=actual.status;
    p.boosts={...actual.boosts};p.setType(actual.getTypes());});
  const enemyNames=[...new Set([...options.pokemon[o.foe.name].defaultMoves,...options.pokemon[o.foe.name].legalMoves])];
  function hit(a,d,id){
    const m=Dex.getActiveMove(id);if(m.category==='Status')return 0;
    if((m.type==='Water'&&d.hasAbility('waterabsorb')||m.type==='Fire'&&d.hasAbility('flashfire'))&&!a.hasAbility('moldbreaker'))return 0;
    m.willCrit=false;m.ignoreAbility=a.hasAbility('moldbreaker');
    const types=a.getTypes();
    if(a.hasAbility('protean')&&types.length>1)a.setType(m.type);
    model.setActiveMove(m,a,d);model.randomizer=n=>Math.floor(n*.925);
    let damage=model.actions.getDamage(a,d,m,true)||0;
    a.setType(types);model.clearActiveMove(true);
    if(m.multihit)damage*=typeof m.multihit==='number'?m.multihit:3;
    if(m.id==='dragondarts')damage*=2;
    if(m.flags.charge)damage*=.52;
    return damage*(m.accuracy===true?1:m.accuracy/100);
  }
  const actions=[];
  function score(p,id,switched){
    const incoming=enemyNames.map(n=>({id:n,d:hit(foe,p,n)})).sort((a,b)=>b.d-a.d);
    const danger=incoming[0]?.d||0;
    const likely=incoming.filter(x=>options.pokemon[o.foe.name].defaultMoves.some(n=>Dex.toID(n)===Dex.toID(x.id))).slice(0,2);
    const expected=likely.length?likely.reduce((s,x)=>s+x.d,0)/likely.length:danger;
    const reply=.7*expected+.3*danger;
    const m=Dex.moves.get(id),out=hit(p,foe,id);
    const first=m.priority>0||m.priority===0&&p.getStat('spe')>foe.getStat('spe');
    const ko=out>=foe.hp;
    let loss=switched?reply:ko&&first?0:reply;
    let s=100*Math.min(out,foe.hp)/foe.maxhp-.8*100*Math.min(loss,p.hp)/p.maxhp;
    if(ko)s+=first?95:55;
    if(loss>=p.hp)s-=110;
    if(m.heal){const heal=Math.min(p.maxhp-p.hp,p.maxhp*m.heal[0]/m.heal[1]);
      s+=100*heal/p.maxhp*.95;
      if(!first&&reply>=p.hp)s-=100;
      if(reply*1.5<heal)s+=18;
    }
    if(m.boosts&&m.target==='self'&&reply<p.hp*.45){
      const old={...p.boosts};
      for(const [k,v]of Object.entries(m.boosts))p.boosts[k]=Math.max(-6,Math.min(6,(p.boosts[k]||0)+v));
      const after=Math.max(...p.moveSlots.map(x=>hit(p,foe,x.id)));
      p.boosts=old;
      const before=Math.max(...p.moveSlots.map(x=>hit(p,foe,x.id)));
      s+=Math.min(85,170*(after-before)/foe.maxhp)+Math.min(20,3*(m.boosts.spe||0));
    }
    if(m.status&&!foe.status)s+=m.status==='slp'?24:12;
    if(switched)s-=18+(o.turn-prior.lastSwitch<=2?35:0);
    return s;
  }
  try{
    if(!o.force_switch)for(const m of o.valid_moves)actions.push({action:'move '+m.index,score:score(own[0],m.id,false)});
    for(const s of o.valid_switches){const p=own[s.index-1];
      p.boosts={atk:0,def:0,spa:0,spd:0,spe:0,accuracy:0,evasion:0};
      const best=Math.max(...p.moveSlots.map(m=>score(p,m.id,!o.force_switch)));
      actions.push({action:'switch '+s.index,score:best});
    }
    actions.sort((a,b)=>b.score-a.score);
    const action=actions[0]?.action||'pass';
    if(action.startsWith('switch'))prior.lastSwitch=o.turn;
    return action;
  }finally{model.destroy();}
}
module.exports={adaptive};
