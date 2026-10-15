/* Differential fixtures from the pinned local official Showdown simulator.
 * getDamage gives one hit, not a full turn; exclude multihit and status moves.
 * Critical hits are explicitly disabled, and randomizer fixes the damage roll.
 */
const fs=require('fs');
const {Battle,Dex}=require('pokemon-showdown');
const options=JSON.parse(fs.readFileSync('research/options.json')).pokemon;
const own=JSON.parse(fs.readFileSync('team.json'));
function preset(name){const p=options[name];return {name,species:name,ability:p.defaultAbility,item:p.defaultItem,nature:p.defaultNature,
  evs:Object.fromEntries([...p.defaultEvs.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi)].map(m=>[m[2].toLowerCase(),+m[1]])),moves:p.defaultMoves,level:100};}
const sets=Object.keys(options).map(preset);
for(const p of own){const s=preset(p.name);Object.assign(s,p);s.evs=Object.fromEntries([...p.evs.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi)].map(m=>[m[2].toLowerCase(),+m[1]]));sets.push(s);}
const fixtures=[];
for(let i=0;i<sets.length;i++)for(let j=0;j<sets.length;j++){
  const s=sets[i],t=sets[j];
  const b=new Battle({formatid:'gen9customgame',seed:[1,2,i+1,j+1],p1:{name:'source',team:[s]},p2:{name:'target',team:[t]}});
  b.makeChoices('team 1','team 1');
  const a=b.p1.active[0],d=b.p2.active[0];
  const moves=options[s.name].legalMoves;
  function obs(p,set){return {name:set.name,ability:set.ability,item:set.item,nature:set.nature,evs:set.evs,level:p.level,
    boosts:{...p.boosts},types:p.getTypes(),hp_percent:100,condition:p.hp+'/'+p.maxhp};}
  for(const mid of moves){
    const m=Dex.getActiveMove(mid);
    if(m.category==='Status'||m.multihit||m.id==='dragondarts')continue;
    m.willCrit=false;
    // getDamage bypasses ModifyMove and BeforeMove; prepare their relevant
    // first-attack effects explicitly while preserving the input observation.
    const source=obs(a,s),target=obs(d,t),originalTypes=a.getTypes();
    if(a.hasAbility('moldbreaker'))m.ignoreAbility=true;
    b.setActiveMove(m,a,d);
    if(a.hasAbility('protean'))a.setType(m.type);
    for(const roll of [.85,1.]){
      b.randomizer=n=>Math.floor(n*roll);
      // Ability absorption runs in TryHit, before getDamage in a real attack.
      const absorbed=!m.ignoreAbility && ((m.type==='Water'&&d.hasAbility('waterabsorb')) || (m.type==='Fire'&&d.hasAbility('flashfire')));
      const amount=absorbed?0:b.actions.getDamage(a,d,m,true)||0;
      fixtures.push({source,target,move:m.id,weather:b.field.weather,roll,damage:amount,maxhp:d.maxhp});
    }
    a.setType(originalTypes);b.clearActiveMove(true);
  }
  b.destroy();
}
fs.writeFileSync('research/damage-oracle.json',JSON.stringify(fixtures));
console.log(JSON.stringify({fixtures:fixtures.length,sets:sets.length,simulatorVersion:require('pokemon-showdown/package.json').version}));
