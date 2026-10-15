const test=require('node:test');
const assert=require('node:assert/strict');
const {spawnSync}=require('child_process');
const {Battle}=require('pokemon-showdown');

test('nondefault Choice move stays locked after hitting Protect',()=>{
  const b=new Battle({formatid:'gen9customgame',seed:[2,4,8,16],
    p1:{team:[{species:'Metagross',ability:'Clear Body',item:'Choice Band',nature:'Adamant',
      evs:{atk:252,spe:252,spd:4},moves:['Thunder Punch','Earthquake']}]},
    p2:{team:[{species:'Blastoise',ability:'Torrent',moves:['Protect']}]}});
  b.makeChoices('team 1','team 1');b.makeChoices('move 1','move 1');
  const legal=b.p1.activeRequest.active[0].moves.filter(m=>!m.disabled).map(m=>m.id);
  assert.deepEqual(legal,['thunderpunch']);
  const code=`import importlib.util,sys
s=importlib.util.spec_from_file_location('agent',sys.argv[1]);a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
x=a.build_mon({'name':'Metagross','item':'Choice Band'});y=a.build_mon({'name':'Blastoise'});y['protect']=True
a.apply_move(x,y,a.DATA['moves']['thunderpunch'],'',.925)
print(a.best_attack(x,a.build_mon({'name':'Garchomp'}),'')['id'])`;
  const reply=spawnSync('python',['-c',code,process.env.AGENT_FILE||'submission/agent.py'],{encoding:'utf8'});
  assert.equal(reply.status,0,reply.stderr);assert.equal(reply.stdout.trim(),legal[0]);
  b.destroy();
});
