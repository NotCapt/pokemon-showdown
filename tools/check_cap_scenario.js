/* Legal curated scenario at turn 100. Compare decisions and resulting summed
 * HP in the real simulator, without the agent's internal damage model.
 */
const fs=require('fs');
const {spawnSync}=require('child_process');
const crypto=require('crypto');
const {Battle,Dex}=require('pokemon-showdown');
const options=require('../research/options.json');
const own=require('../team.json');
function convert(p){const evs={};for(const m of p.evs.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi))evs[m[2].toLowerCase()]=+m[1];return {...p,species:p.name,evs};}
function defaults(name){const p=options.pokemon[name];return {name,ability:p.defaultAbility,item:p.defaultItem,nature:p.defaultNature,evs:p.defaultEvs,moves:p.defaultMoves};}
function run(path){
  const corvi=defaults('Corviknight');corvi.moves=['Body Press','Roost'];
  const b=new Battle({formatid:'gen9customgame',seed:[2,6,18,24],p1:{name:'agent',team:[corvi,own[0],own[1]].map(convert)},
    p2:{name:'enemy',team:['Tyranitar','Arcanine','Metagross'].map(defaults).map(convert)}});
  b.makeChoices('team 1','team 1');b.turn=100;
  for(const [side,hps]of [[b.p1,[.01,.7,0]],[b.p2,[.01,.8,0]]]){
    side.pokemon.forEach((p,i)=>{p.hp=Math.floor(p.maxhp*hps[i]);if(!p.hp){p.fainted=true;side.pokemonLeft--;}});
  }
  function summary(p,i){return {name:p.species.name,types:p.getTypes(),hp_percent:100*p.hp/p.maxhp,fainted:p.fainted,active:p.isActive,index:i+1};}
  const a=b.p1.active[0],f=b.p2.active[0];
  const o={turn:100,weather:b.field.weather,my_active:{...summary(a,0),condition:a.getHealth().secret,boosts:{...a.boosts}},
    foe:{name:f.species.name,types:f.getTypes(),hp_percent:Math.ceil(100*f.hp/f.maxhp)},
    my_team:b.p1.pokemon.map(summary),valid_switches:b.p1.pokemon.map(summary).filter(p=>!p.active&&!p.fainted),
    valid_moves:a.moveSlots.map((m,i)=>({index:i+1,...require('../research/battle_data.json').moves[m.id]}))};
  const code='import importlib.util,json,sys;s=importlib.util.spec_from_file_location("a",sys.argv[1]);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);p=a.PokemonAgent();p.last_turn=99;print(p.decide(json.loads(sys.argv[2])))';
  const reply=spawnSync('python',['-c',code,path,JSON.stringify(o)],{encoding:'utf8'});
  if(reply.status!==0)throw Error(reply.stderr);
  const action=reply.stdout.trim();
  b.makeChoices(action,'move 1');
  for(let k=0;k<4&&b.turn<=100&&!b.ended;k++){
    if(!b.sides.some(s=>s.requestState==='switch'))break;
    for(const s of b.sides)if(s.requestState==='switch'){
      const index=s.pokemon.findIndex(p=>!p.isActive&&!p.fainted);
      if(index<0||!b.choose(s.id,'switch '+(index+1)))throw Error('forced switch failed');
    }
  }
  const hp=b.sides.map(s=>s.pokemon.reduce((v,p)=>v+100*p.hp/p.maxhp,0));
  const result={path,agentSha256:crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex'),action,ownHP:hp[0],enemyHP:hp[1],capWinner:hp[0]>hp[1]?'agent':hp[0]<hp[1]?'enemy':'tie',turn:b.turn};
  b.destroy();return result;
}
const results=[run('archive/v4_1/agent.py'),run(process.argv[2]||'submission/agent.py')];
fs.writeFileSync('research/cap-scenario.json',JSON.stringify({scenario:'Corviknight at 1%, Tyranitar at 1%, own reserve Dragonite at 70%, enemy reserve Arcanine at 80%, one fainted member each, turn 100; enemy Stone Edge.',results},null,2));
console.log(JSON.stringify(results,null,2));
if(results[0].capWinner!=='enemy'||results[1].capWinner!=='agent')process.exitCode=1;
