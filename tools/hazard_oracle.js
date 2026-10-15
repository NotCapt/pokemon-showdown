// Differential entry-damage fixtures from the pinned official simulator.
const fs=require('fs');
const {Battle}=require('pokemon-showdown');
const options=require('../research/options.json');
const fixtures=[];
function set(name){const p=options.pokemon[name];const preset=options.evPresets.find(e=>e.split(' (')[0]===p.defaultEvs.split(' (')[0]);
  return {name,species:name,ability:p.defaultAbility,item:'',nature:options.natures.includes(p.defaultNature)?p.defaultNature:'Impish',
  evs:Object.fromEntries([...preset.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi)].map(m=>[m[2].toLowerCase(),+m[1]])),
  moves:p.defaultMoves,level:100};}
for(const name of Object.keys(options.pokemon))for(const rock of [false,true])for(let layers=0;layers<4;layers++)for(const boots of [false,true]){
  const own=set(name);if(boots)own.item='Heavy-Duty Boots';
  const filler=set(name==='Arcanine'?'Dragonite':'Arcanine');
  const enemy=set('Corviknight');enemy.moves=['Roost'];
  const b=new Battle({formatid:'gen9customgame',seed:[1,2,8,37],p1:{name:'agent',team:[filler,own]},p2:{name:'enemy',team:[enemy]}});
  b.makeChoices('team 12','team 1');
  if(rock)b.p1.addSideCondition('stealthrock',b.p2.active[0]);
  for(let n=0;n<layers;n++)b.p1.addSideCondition('spikes',b.p2.active[0]);
  const target=b.p1.pokemon[1],before=target.hp;
  const source={name,types:target.getTypes(),item:target.getItem().name||'',ability:target.getAbility().name,
    stats:{...target.storedStats,hp:target.maxhp},hp_percent:100};
  b.makeChoices('switch 2','move 1');
  fixtures.push({source,state:[rock,layers],damage:100*(before-target.hp)/target.maxhp,maxhp:target.maxhp});
  b.destroy();
}
fs.writeFileSync('research/f-hazard-oracle.json',JSON.stringify({simulatorVersion:require('pokemon-showdown/package.json').version,fixtures}));
console.log(fixtures.length+' official entry-damage fixtures saved.');
