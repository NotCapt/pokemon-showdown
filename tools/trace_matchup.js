// Replay one adaptive/frozen game at its original index, with public diagnostics.
const fs = require('fs');
const Module = require('module');
const path = require('path');
const game = Number(process.env.TRACE_GAME);
if (!Number.isInteger(game) || game < 0) throw Error('Set a nonnegative TRACE_GAME');
if (!['adaptive', 'tactical', 'frozen'].includes(process.env.OPPONENT)) {
  throw Error('Single-game skipping does not preserve random-policy RNG history');
}
let source = fs.readFileSync(path.join(__dirname, 'benchmark.js'), 'utf8');
function replaceOnce(from, to) {
  if (source.split(from).length !== 2) throw Error('Instrumentation target changed: ' + from);
  source = source.replace(from, to);
}
replaceOnce("'tools/worker.py'", "'tools/trace_worker.py'");
replaceOnce('for(let g=0;g<games;g++){', `for(let g=${game};g<${game + 1};g++){`);
replaceOnce('p=wins/games', 'p=wins/results.length');
replaceOnce('team:configs,games,wins,losses:', 'team:configs,games:results.length,wins,losses:');
replaceOnce('action:reply.action});', 'action:reply.action,diagnostics:reply.diagnostics});');
const implementation = new Module(module.id, module.parent);
implementation.filename = path.join(__dirname, 'benchmark.js');
implementation.paths = module.paths;
implementation._compile(source, implementation.filename);
