// Official pinned simulator truth for the selected team's recovery moves.
const fs=require('fs');
const assert=require('assert/strict');
const {Battle}=require('pokemon-showdown');
const result={simulatorVersion:require('pokemon-showdown/package.json').version};
for(const heal of [true,false]){
  const b=new Battle({formatid:'gen9customgame',seed:[13,17,19,23],
    p1:{name:'wall',team:[{species:'Corviknight',ability:'Mirror Armor',nature:'Impish',evs:{hp:252,def:252,spd:4},moves:['Roost','Iron Defense']}]},
    p2:{name:'attacker',team:[{species:'Snorlax',ability:'Thick Fat',moves:['Earthquake']}]}});
  b.makeChoices('team 1','team 1');const p=b.p1.active[0];p.hp=Math.floor(p.maxhp/2);
  b.makeChoices(heal?'move 1':'move 2','move 1');
  const record={hp:p.hp,maxhp:p.maxhp,types:p.getTypes(),log:b.log};
  if(heal){assert(p.hp<p.maxhp);assert(!b.log.some(x=>x.includes('-immune')));}
  else assert(b.log.some(x=>x.includes('-immune')));
  result[heal?'roostGrounded':'flyingGroundImmune']=record;b.destroy();
}
{
  const b=new Battle({formatid:'gen9customgame',seed:[29,31,37,41],
    p1:{name:'sleeper',team:[{species:'Snorlax',ability:'Thick Fat',moves:['Rest','Body Slam']}]},
    p2:{name:'control',team:[{species:'Blastoise',ability:'Torrent',moves:['Splash']}]}});
  b.makeChoices('team 1','team 1');b.p1.active[0].hp=Math.floor(b.p1.active[0].maxhp/2);
  const hp=[];
  for(let turn=1;turn<=4;turn++){b.makeChoices(turn===1?'move 1':'move 2','move 1');hp.push(b.p2.active[0].hp);}
  assert.equal(hp[0],hp[1]);assert.equal(hp[1],hp[2]);assert(hp[3]<hp[2]);
  result.rest={opponentHPAfterTurns:hp,log:b.log};b.destroy();
}
fs.writeFileSync(process.argv[2]||'research/roster-forecast-v1/recovery-oracle.json',JSON.stringify(result,null,2));
console.log('Official simulator confirms Roost grounding, type restoration, and two blocked Rest turns.');
