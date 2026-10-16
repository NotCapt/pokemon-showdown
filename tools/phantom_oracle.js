const fs=require('fs');
const assert=require('assert/strict');
const {Battle}=require('pokemon-showdown');
const rows=[];
for(const protect of [false,true]){
  const b=new Battle({formatid:'gen9customgame',seed:[43,47,53,59],
    p1:{name:'phased',team:[{species:'Dragapult',ability:'Clear Body',item:'Choice Band',nature:'Jolly',evs:{atk:252,spe:252,spd:4},moves:['Phantom Force']}]},
    p2:{name:'target',team:[{species:protect?'Metagross':'Lucario',ability:'Inner Focus',moves:protect?['Splash','Protect']:['Ice Punch']}]}});
  b.makeChoices('team 1','team 1');const first=[b.p1.active[0].hp,b.p2.active[0].hp];
  b.makeChoices('move 1','move 1');const charged=[b.p1.active[0].hp,b.p2.active[0].hp];
  assert.deepEqual(first,charged);
  b.makeChoices('move 1',protect?'move 2':'move 1');const after=[b.p1.active[0].hp,b.p2.active[0].hp];
  assert(after[1]<first[1]);
  rows.push({case:protect?'break Protect':'charge evasion and later hit',first,charged,after,log:b.log});b.destroy();
}
fs.writeFileSync('research/phantom-forecast-v1/oracle.json',JSON.stringify({simulatorVersion:require('pokemon-showdown/package.json').version,rows},null,2));
console.log('Official simulator confirms a damage-free/evasive charge turn, later hit and Protect bypass.');
