const fs = require('fs');
const {Dex} = require('pokemon-showdown');
const options = JSON.parse(fs.readFileSync('research/options.json'));
const data = {species:{}, moves:{}, chart:{}, natures:{}};
for (const [name,r] of Object.entries(options.pokemon)) {
  const s = Dex.species.get(name);
  data.species[s.id] = {...r, name, stats:s.baseStats, weight:s.weightkg};
  for (const name of r.legalMoves) {
    const m = Dex.moves.get(name);
    data.moves[m.id] = {id:m.id,name:m.name,type:m.type,category:m.category,
      base_power:m.basePower,accuracy:m.accuracy,priority:m.priority,
      boosts:m.boosts,self:m.self,secondary:m.secondary,secondaries:m.secondaries,
      heal:m.heal,drain:m.drain,recoil:m.recoil,status:m.status,
      target:m.target,flags:m.flags,multihit:m.multihit};
  }
}
for (const t of Dex.types.all()) data.chart[t.name] = t.damageTaken;
for (const n of Dex.natures.all()) data.natures[n.name] = {plus:n.plus,minus:n.minus};
fs.writeFileSync('research/battle_data.json', JSON.stringify(data));
