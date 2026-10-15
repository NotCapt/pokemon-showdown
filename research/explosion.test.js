// Compare the agent's faint semantics with the official engine on legal sets.
const test=require('node:test');
const assert=require('node:assert/strict');
const {spawnSync}=require('child_process');
const {Battle}=require('pokemon-showdown');
const options=require('../research/options.json');
function set(name,moves){const p=options.pokemon[name],evs={};
  for(const m of p.defaultEvs.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi))evs[m[2].toLowerCase()]=+m[1];
  assert.ok(moves.every(m=>p.legalMoves.includes(m)));
  return {species:name,ability:p.defaultAbility,item:p.defaultItem,nature:p.defaultNature,evs,moves};
}
for(const [target,move]of [['Snorlax','Rest'],['Dragapult','Will-O-Wisp'],['Blastoise','Protect']]){
  test('Explosion self-KO matches Showdown against '+target,()=>{
    const b=new Battle({formatid:'gen9customgame',seed:[4,8,16,32],
      p1:{team:[set('Metagross',['Explosion'])]},p2:{team:[set(target,[move])]}});
    b.makeChoices('team 1','team 1');
    b.makeChoices('move 1','move 1');
    const actual=b.p1.pokemon[0].hp;
    assert.equal(actual,0);
    const code=`import importlib.util,json,sys
s=importlib.util.spec_from_file_location('agent',sys.argv[1]);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
x=a.build_mon({'name':'Metagross'});y=a.build_mon({'name':sys.argv[2]});y['protect']=sys.argv[3]=='Protect'
a.apply_move(x,y,a.DATA['moves']['explosion'],'',.925)
print(json.dumps({'ownHP':x['hp'],'targetHP':y['hp']}))`;
    const reply=spawnSync('python',['-c',code,process.env.AGENT_FILE||'research/v4_3-explosion-agent.py',target,move],{encoding:'utf8'});
    assert.equal(reply.status,0,reply.stderr);
    const predicted=JSON.parse(reply.stdout);
    assert.equal(predicted.ownHP,actual);
    if(target==='Dragapult'||move==='Protect')assert.equal(predicted.targetHP,100);
    else assert.ok(predicted.targetHP<100);
    b.destroy();
  });
}
