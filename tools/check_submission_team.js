// Compare the text actually submitted with the policy's extracted OWN config.
const fs=require('fs');
const {Teams,Dex}=require('pokemon-showdown');
const actual=Teams.import(fs.readFileSync(process.argv[2],'utf8'));
const expected=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
function normalized(p){
  const evs=typeof p.evs==='string'?Object.fromEntries([...p.evs.matchAll(/(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)/gi)].map(m=>[m[2].toLowerCase(),+m[1]])):p.evs;
  return {name:Dex.toID(p.species||p.name),item:Dex.toID(p.item),ability:Dex.toID(p.ability),nature:p.nature,
    evs:Object.fromEntries(['hp','atk','def','spa','spd','spe'].map(k=>[k,evs[k]||0])),moves:p.moves.map(Dex.toID)};
}
if(JSON.stringify(actual.map(normalized))!==JSON.stringify(expected.map(normalized)))throw Error('team.txt and embedded OWN mismatch');
console.log(JSON.stringify({teamTextMatchesEmbeddedConfig:true,members:actual.map(p=>p.species)}));
