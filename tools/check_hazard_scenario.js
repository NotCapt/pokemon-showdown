// Controlled late-game position. Both policies receive only public history.
const fs=require('fs');
const crypto=require('crypto');
const {spawnSync}=require('child_process');
const {Battle,Dex}=require('pokemon-showdown');
const options=require('../research/options.json');
const own=require('../archive/v4_3_2/team.json');
function convert(p){return {...p,species:p.name,level:100,evs:Object.fromEntries([...p.evs.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi)].map(m=>[m[2].toLowerCase(),+m[1]]))};}
function defaults(name){const p=options.pokemon[name];return {name,ability:p.defaultAbility,item:p.defaultItem,
  nature:options.natures.includes(p.defaultNature)?p.defaultNature:'Impish',
  evs:options.evPresets.find(e=>e.split(' (')[0]===p.defaultEvs.split(' (')[0]),moves:p.defaultMoves};}
function run(path){
  const b=new Battle({formatid:'gen9customgame',seed:[2,6,18,24],p1:{name:'agent',team:own.map(convert)},
    p2:{name:'enemy',team:['Corviknight','Ferrothorn','Garchomp'].map(defaults).map(convert)}});
  b.makeChoices('team 123','team 123');
  // Establish the real Choice lock through move execution before placing the
  // controlled last-turn HP/field state. No disabled-move shortcut is used.
  b.makeChoices('move 2','move 1');b.turn=100;
  for(const [side,hps]of [[b.p1,[.3,0,.24]],[b.p2,[.6,0,0]]])side.pokemon.forEach((p,i)=>{
    p.hp=Math.floor(p.maxhp*hps[i]);if(!p.hp){p.fainted=true;side.pokemonLeft--;}
  });
  b.p1.addSideCondition('stealthrock',b.p2.active[0]);
  b.makeRequest('move');
  function summary(p,i){return {name:p.species.name,types:p.getTypes(),hp_percent:100*p.hp/p.maxhp,fainted:p.fainted,active:p.isActive,index:i+1};}
  function observe(){
    const a=b.p1.active[0],f=b.p2.active[0],req=b.p1.activeRequest;
    return {turn:b.turn,force_switch:!!req.forceSwitch,weather:b.field.weather,
      my_active:{...summary(a,0),condition:a.getHealth().secret,boosts:{}},
      foe:{name:f.species.name,types:f.getTypes(),hp_percent:Math.ceil(100*f.hp/f.maxhp)},
      my_team:b.p1.pokemon.map(summary),valid_switches:b.p1.pokemon.map(summary).filter(p=>!p.active&&!p.fainted),
      valid_moves:req.active?.[0]?.moves.map((m,i)=>({...require('../research/battle_data.json').moves[m.id],index:i+1,disabled:m.disabled,pp:m.pp})).filter(m=>!m.disabled&&m.pp>0)||[]};
  }
  // A past forced Dragonite entry from 100% to 243/323 establishes Rock
  // damage. Dragapult was already fainted and remains fainted in this state.
  const history=[{turn:89,force_switch:true,my_active:{name:'Dragapult',hp_percent:0},foe:{name:'Snorlax',hp_percent:100},
    valid_moves:[],valid_switches:[{name:'Dragonite',hp_percent:100,index:1}]},
    {turn:90,my_active:{name:'Dragonite',hp_percent:243/323*100},foe:{name:'Snorlax',hp_percent:100},valid_moves:[{id:'extremespeed',index:1}]}];
  const code='import importlib.util,json,sys;s=importlib.util.spec_from_file_location("a",sys.argv[1]);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);p=a.PokemonAgent();actions=[p.decide(o) for o in json.load(sys.stdin)];print(actions[-1])';
  const actions=[];
  for(let step=0;step<16&&!b.ended&&b.turn<=100;step++){
    if(b.p1.requestState){
      const o=observe();history.push(o);
      const reply=spawnSync('python',['-c',code,path],{input:JSON.stringify(history),encoding:'utf8'});
      if(reply.status!==0)throw Error(reply.stderr);
      const action=reply.stdout.trim();actions.push({turn:b.turn,force:o.force_switch,action,active:o.my_active.name});
      if(!b.choose('p1',action))throw Error('Illegal agent choice '+action);
    }
    if(b.p2.requestState==='switch'){
      const i=b.p2.pokemon.findIndex(p=>!p.active&&!p.fainted);if(!b.choose('p2','switch '+(i+1)))throw Error('Enemy switch failed');
    }else if(b.p2.requestState==='move'){
      const p=b.p2.active[0],move='roost';
      const i=p.moveSlots.findIndex(m=>m.id===move);if(!b.choose('p2','move '+(i+1)))throw Error('Enemy move failed');
    }
  }
  const hp=b.sides.map(s=>s.pokemon.reduce((v,p)=>v+100*p.hp/p.maxhp,0));
  const result={path,agentSha256:crypto.createHash('sha256').update(fs.readFileSync(path)).digest('hex'),
    warmupObservations:history.slice(0,2),initialObservation:history[2],actions,ownHP:hp[0],enemyHP:hp[1],capWinner:hp[0]>hp[1]?'agent':hp[0]<hp[1]?'enemy':'tie',turn:b.turn,log:b.log};
  b.destroy();return result;
}
const results=[run('archive/v4_3_2/agent.py'),run(process.argv[2]||'submission/agent.py')];
fs.writeFileSync(process.argv[3]||'research/v4_4-hazard-scenario.json',JSON.stringify({
  scenario:'Controlled last turn: Dragonite at 30% locked into Earthquake, fainted Dragapult, Arcanine at 24%, Stealth Rock, Corviknight at 60% uses Roost. Public earlier Dragonite entry establishes Rock damage. This verifies avoiding lethal entry and HP preservation, not a win-rate gain or a full-game replay.',
  simulatorVersion:require('pokemon-showdown/package.json').version,results},null,2));
console.log(JSON.stringify(results.map(({log,...rest})=>rest),null,2));
if(results[0].actions[0].action!=='switch 3'||results[1].actions[0].action!=='move 2')throw Error('Hazard decision fixture regressed');
if(results[1].ownHP<=results[0].ownHP)throw Error('Hazard entry cost failed to preserve HP');
