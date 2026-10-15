const test=require('node:test');
const assert=require('node:assert/strict');
const {Battle,Dex}=require('pokemon-showdown');
const {adaptive}=require('../tools/opponents');
const team=require('../team.json');
function convert(p){const evs={};for(const m of p.evs.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi))evs[m[2].toLowerCase()]=+m[1];return {...p,species:p.name,evs};}
function run(enemy){
  const b=new Battle({formatid:'gen9customgame',seed:[1,2,3,4],p1:{name:'own',team:team.map(convert)},p2:{name:'enemy',team:enemy}});
  b.makeChoices('team 1','team 1');
  const side=b.p1,a=side.active[0],f=b.p2.active[0];
  const o={turn:b.turn,weather:b.field.weather,my_active:{name:a.species.name},
    foe:{name:f.species.name,types:f.getTypes(),hp_percent:100},
    valid_moves:side.activeRequest.active[0].moves.map((m,i)=>({...m,index:i+1})).filter(m=>!m.disabled&&m.pp>0),
    valid_switches:side.pokemon.map((p,i)=>({name:p.species.name,index:i+1})).filter((p,i)=>i>0)};
  const before=JSON.stringify(b.toJSON());
  const action=adaptive(b,side,o);
  assert.equal(JSON.stringify(b.toJSON()),before,'opponent evaluation mutated the actual battle');
  const legal=new Set([...o.valid_moves.map(m=>'move '+m.index),...o.valid_switches.map(s=>'switch '+s.index)]);
  assert.ok(legal.has(action));b.destroy();return action;
}
test('evaluation policy ignores hidden enemy set and reserve information',()=>{
  const a=run([{species:'Garchomp',ability:'Rough Skin',item:'Life Orb',moves:['Earthquake'],nature:'Jolly'},
    {species:'Scizor',ability:'Technician',moves:['Bullet Punch']}]);
  const b=run([{species:'Garchomp',ability:'Sand Veil',item:'Choice Scarf',moves:['Draco Meteor'],nature:'Modest'},
    {species:'Blastoise',ability:'Torrent',moves:['Surf']}]);
  assert.equal(a,b);
});
