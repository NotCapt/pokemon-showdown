/* Cross-check the fast getDamage fixtures through the full move execution path.
 * Charge moves need turn/volatile fixtures and are outside this single-hit check.
 */
const fs=require('fs');
const {Battle,Dex}=require('pokemon-showdown');
const fixtures=JSON.parse(fs.readFileSync('research/damage-oracle.json'));
const checked=[],failures=[];
for(let i=1;i<fixtures.length;i+=38){
  const f=fixtures[i],m=Dex.getActiveMove(f.move);
  // Sucker Punch additionally needs a queued damaging action from its target.
  if(m.flags.charge||m.id==='suckerpunch')continue;
  function set(o,moves){return {species:o.name,ability:o.ability,item:o.item,nature:o.nature,evs:o.evs,level:o.level,moves};}
  const b=new Battle({formatid:'gen9customgame',seed:[1,2,3,4],p1:{name:'a',team:[set(f.source,[f.move])]},p2:{name:'b',team:[set(f.target,['splash'])]}});
  b.makeChoices('team 1','team 1');
  const a=b.p1.active[0],d=b.p2.active[0];
  let actual=0;
  const original=b.actions.getDamage.bind(b.actions);
  b.actions.getDamage=(source,target,move,...args)=>{
    move.willCrit=false;
    const n=original(source,target,move,...args);
    if(source===a&&target===d)actual+=n||0;
    return n;
  };
  b.randomizer=n=>Math.floor(n*f.roll);
  m.accuracy=true;m.willCrit=false;
  b.actions.useMove(m,a,d);
  const result={source:f.source.name,target:f.target.name,move:f.move,expected:f.damage,actual};
  checked.push(result);
  if(actual!==f.damage)failures.push(result);
  b.destroy();
}
fs.writeFileSync('research/damage-oracle-validation.json',JSON.stringify({checked:checked.length,failures,results:checked},null,2));
console.log(JSON.stringify({checked:checked.length,failures}));
if(failures.length)process.exitCode=1;
