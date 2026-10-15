/* Actual Showdown battles; observation deliberately restricted to portal schema.
 * No foe item, ability, stats, moves or bench information reaches the agent.
 */
const fs=require('fs');
const {spawn}=require('child_process');
const readline=require('readline');
const crypto=require('crypto');
const {Battle,Dex}=require('pokemon-showdown');
const {adaptive}=require('./opponents');
const options=JSON.parse(fs.readFileSync('research/options.json'));
const configs=JSON.parse(fs.readFileSync(process.env.TEAM_FILE||'team.json'));
const opponentConfigs=process.env.OPP_TEAM_FILE?JSON.parse(fs.readFileSync(process.env.OPP_TEAM_FILE)):null;
const agentFile=process.env.AGENT_FILE||'submission/agent.py';
const agentSha256=crypto.createHash('sha256').update(fs.readFileSync(agentFile)).digest('hex');
const worker=spawn('python',['-u','tools/worker.py'],{stdio:['pipe','pipe','inherit']});
let pending=[];
readline.createInterface({input:worker.stdout}).on('line',line=>pending.shift()(JSON.parse(line)));
function ask(msg){return new Promise(resolve=>{pending.push(resolve);worker.stdin.write(JSON.stringify(msg)+'\n');});}
function convert(p){
  const evs={}; for(const m of p.evs.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi))evs[m[2].toLowerCase()]=Number(m[1]);
  return {name:p.name,species:p.name,item:p.item,ability:p.ability,nature:p.nature,evs,moves:p.moves,level:100};
}
function defaultSet(name){const p=options.pokemon[name];return {name,item:p.defaultItem,ability:p.defaultAbility,nature:p.defaultNature,evs:p.defaultEvs,moves:p.defaultMoves};}
function summary(p){return {name:p.species.name,types:p.getTypes(),hp_percent:p.hp/p.maxhp*100,fainted:p.fainted,active:p.isActive};}
function observation(b,side){
  const req=side.activeRequest,a=side.active[0],f=side.foe.active[0];
  const result={turn:b.turn,weather:b.field.weather,team_preview:!!req.teamPreview,force_switch:!!req.forceSwitch,
    my_active:a?{...summary(a),condition:a.getHealth().secret,boosts:{...a.boosts}}:{},
    foe:f?{name:f.species.name,types:f.getTypes(),hp_percent:Math.ceil(f.hp/f.maxhp*100)}:{},
    my_team:side.pokemon.map(summary),valid_moves:[],valid_switches:[]};
  if(req.active?.[0])result.valid_moves=req.active[0].moves.map((raw,i)=>{
    const m=Dex.moves.get(raw.id);
    return {index:i+1,id:m.id,name:m.name,type:m.type,category:m.category,base_power:m.basePower,accuracy:m.accuracy,
      type_multiplier:f?(Dex.getImmunity(m.type,f)?2**Dex.getEffectiveness(m.type,f):0):1,stab:a.hasType(m.type),disabled:raw.disabled,pp:raw.pp};
  }).filter(m=>!m.disabled&&m.pp!==0);
  if(!req.active?.[0]?.trapped) result.valid_switches=side.pokemon.map((p,i)=>({...summary(p),index:i+1})).filter(p=>!p.active&&!p.fainted);
  if(process.env.SPARSE==='1')result.my_active.boosts={};
  return result;
}
function baseline(o,kind){
  if(o.team_preview)return 'team 123';
  if(o.force_switch||!o.valid_moves.length)return o.valid_switches.length?'switch '+o.valid_switches[0].index:'pass';
  let moves=o.valid_moves;
  if(kind==='random')return 'move '+moves[Math.floor(rng()*moves.length)].index;
  return 'move '+moves.reduce((a,b)=>score(a)>score(b)?a:b).index;
  function score(m){return (m.base_power||0)*m.type_multiplier*(kind==='power'?1:(m.stab?1.5:1)*(m.accuracy===true?1:m.accuracy/100));}
}
let state=Number(process.env.SEED||8191);
function rng(){state=(Math.imul(state,1664525)+1013904223)>>>0;return state/4294967296;}
async function run(){
  const games=Number(process.argv[2]||40),names=Object.keys(options.pokemon),results=[],times=[];
  const fixed=[['Garchomp','Metagross','Volcarona'],['Dragonite','Tyranitar','Scizor'],['Dragapult','Togekiss','Excadrill'],['Corviknight','Snorlax','Ferrothorn']];
  let pairedNames;
  for(let g=0;g<games;g++){
    if(g%2===0)pairedNames=g<8?fixed[Math.floor(g/2)]:names.map(n=>[rng(),n]).sort((a,b)=>a[0]-b[0]).slice(0,3).map(x=>x[1]);
    const oppNames=pairedNames;
    const custom=process.env.CUSTOM?JSON.parse(fs.readFileSync(process.env.CUSTOM)):null;
    const opponent=opponentConfigs||(process.env.MIRROR==='1'?configs:custom?custom[Math.floor(g/2)%custom.length]:oppNames.map(defaultSet));
    const reverse=g%2===1,kind=process.env.OPPONENT||['power','stab','tactical'][Math.floor(g/2)%3];
    const p1=reverse?opponent:configs,p2=reverse?configs:opponent;
    const seed=[1,2,Math.floor(g/2)+1,Number(process.env.SEED||8191)%65536];
    const b=new Battle({formatid:'gen9customgame',seed,p1:{name:reverse?'baseline':'agent',team:p1.map(convert)},p2:{name:reverse?'agent':'baseline',team:p2.map(convert)}});
    let steps=0,errors=0,baselineVoluntarySwitches=0;
    const agentTrace=[];
    while(!b.ended&&b.turn<=100&&steps++<400){
      const requests=b.sides.map(s=>s.requestState?observation(b,s):null);
      const choices=[];
      for(let i=0;i<2;i++){
        if(!requests[i]){choices.push(null);continue;}
        if(b.sides[i].name==='agent'){
          const reply=await ask({key:'agent',reset:steps===1,observation:requests[i]});
          if(reply.error)throw Error(reply.error);
          choices.push(reply.action);times.push(reply.ms);
          if(process.env.TRACE_DIR)agentTrace.push({observation:requests[i],action:reply.action});
        }else if(kind==='adaptive'){
          choices.push(adaptive(b,b.sides[i],requests[i]));
        }else if(['tactical','search','v1','v2','v3','v4','v4_1','frozen'].includes(kind)){
          const reply=await ask({key:kind,policy:kind,reset:steps===1,observation:requests[i]});
          if(reply.error)throw Error(reply.error);choices.push(reply.action);
        }else choices.push(baseline(requests[i],kind));
      }
      for(let i=0;i<2;i++)if(choices[i]&&!b.choose('p'+(i+1),choices[i])){
        errors++;throw Error('Illegal action '+choices[i]+' '+JSON.stringify(requests[i])+' '+b.log.slice(-5));
      }
      for(let i=0;i<2;i++)if(b.sides[i].name==='baseline'&&choices[i]?.startsWith('switch')&&!requests[i].force_switch)baselineVoluntarySwitches++;
    }
    if(!b.ended&&steps>=400&&b.turn<=100)throw Error('Battle failed to progress within 400 decisions');
    if(!b.ended){const totals=b.sides.map(s=>s.pokemon.reduce((sum,p)=>sum+p.hp/p.maxhp,0));b.win(totals[0]===totals[1]?null:b.sides[totals[0]>totals[1]?0:1]);}
    const hp=b.sides.map(s=>s.pokemon.reduce((v,p)=>v+100*p.hp/p.maxhp,0));
    const record={game:g,winner:b.winner,turns:b.turn,opponent:opponent.map(p=>p.name),opponentSets:opponent,baseline:kind,side:reverse?2:1,errors,seed,baselineVoluntarySwitches,
      finalHP:{agent:hp[reverse?1:0],opponent:hp[reverse?0:1]}};
    results.push(record);
    if(process.env.SAVE_LOGS){
      fs.mkdirSync(process.env.SAVE_LOGS,{recursive:true});
      fs.writeFileSync(process.env.SAVE_LOGS+'/game-'+g+'.log',b.log.join('\n'));
    }
    if(process.env.TRACE_DIR){
      fs.mkdirSync(process.env.TRACE_DIR,{recursive:true});
      fs.writeFileSync(process.env.TRACE_DIR+'/game-'+g+'.json',JSON.stringify({agentSha256,game:g,side:record.side,winner:b.winner,decisions:agentTrace}));
    }
    if(b.winner!=='agent'&&process.env.NO_LAST_LOSS!=='1')fs.writeFileSync('research/last-loss.log',b.log.join('\n'));
    if((g+1)%10===0)console.log(JSON.stringify({completed:g+1,wins:results.filter(r=>r.winner==='agent').length}));
    b.destroy();
  }
  times.sort((a,b)=>a-b);
  const wins=results.filter(r=>r.winner==='agent').length,p=wins/games,z=1.96,den=1+z*z/games;
  const center=(p+z*z/(2*games))/den,half=z*Math.sqrt(p*(1-p)/games+z*z/(4*games*games))/den;
  const report={agentFile,agentSha256,sparseBoosts:process.env.SPARSE==='1',stateless:process.env.STATELESS==='1',
    opponentPolicySha256:crypto.createHash('sha256').update(fs.readFileSync('tools/opponents.js')).digest('hex'),
    archivedOpponentSha256:process.env.OPPONENT==='v4_1'?crypto.createHash('sha256').update(fs.readFileSync('archive/v4_1/agent.py')).digest('hex'):null,
    opponentAgentSha256:process.env.OPP_AGENT_FILE?crypto.createHash('sha256').update(fs.readFileSync(process.env.OPP_AGENT_FILE)).digest('hex'):null,
    opponentInformation:'adaptive uses its own exact state plus public enemy species/types/rounded HP; curated defaults for hidden enemy set; no enemy bench',
    simulatorVersion:require('pokemon-showdown/package.json').version,team:configs,games,wins,losses:results.filter(r=>r.winner==='baseline').length,draws:results.filter(r=>!r.winner).length,
    winRate:p,wilson95:[center-half,center+half],latencyMs:{median:times[Math.floor(times.length*.5)],p95:times[Math.floor(times.length*.95)],max:times.at(-1)},results};
  const output=process.env.REPORT||'research/benchmark.json';fs.writeFileSync(output,JSON.stringify(report,null,2));
  console.log(JSON.stringify({...report,results:undefined},null,2));worker.stdin.end();
}
run().catch(e=>{console.error(e);worker.kill();process.exitCode=1;});
