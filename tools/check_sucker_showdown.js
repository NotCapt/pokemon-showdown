// Sucker Punch on actual Showdown: switches, faster priority, ordinary attacks.
const assert=require('assert/strict');
const fs=require('fs');
const {Battle}=require('pokemon-showdown');
const results=[];
for(const [name,choice] of [['higher priority','move 1'],['ordinary attack','move 2'],['switch','switch 2']]){
  const b=new Battle({formatid:'gen9customgame',seed:[4,17,22,71],
    p1:{name:'target',team:[{species:'Arcanine',ability:'Flash Fire',moves:['Extreme Speed','Crunch']},
                           {species:'Snorlax',ability:'Immunity',moves:['Crunch']}]},
    p2:{name:'attacker',team:[{species:'Dragapult',ability:'Infiltrator',moves:['Sucker Punch']}]}});
  b.makeChoices('team 12','team 1');
  b.makeChoices(choice,'move 1');
  const p=b.p1.active[0], lost=p.maxhp-p.hp;
  assert.equal(lost>0,name==='ordinary attack',name);
  results.push({case:name,damage:lost,log:b.log});b.destroy();
}
fs.writeFileSync(process.argv[2]||'research/e-sucker-showdown.json',JSON.stringify(results,null,2));
console.log('Three official-simulator Sucker Punch fixtures passed.');
