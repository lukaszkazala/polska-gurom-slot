'use strict';
const fs=require('node:fs'), path=require('node:path'), assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..');
const {harness,config}=require(path.join(root,'test-interface-any-start/qa/test_autoplay.cjs'));
const checks=[];
async function manual(h){const p=h.app.spin(); await h.finished(); await p;}
async function check(name,fn){try{checks.push({name,...await fn()});}catch(e){checks.push({name,error:e.stack});}}
async function main(){
 await check('A hanging artwork request has no application startup deadline',async()=>{
  const Module=require('node:module');
  const hp=path.join(root,'test-interface-any-start/qa/test_autoplay.cjs');
  const m=new Module(hp,module);m.filename=hp;m.paths=Module._nodeModulePaths(path.dirname(hp));
  const original=fs.readFileSync(hp,'utf8');
  const injected=original.replace('window: { matchMedia:', 'Image: class { set src(value) {} }, window: { PG_ART: {files:{pending:{src:"pending.png"}},themes:{},symbols:{}}, matchMedia:');
  assert.notEqual(original,injected);
  m._compile(injected,hp);
  const h=m.exports.harness({boot:true});h.state.online=false;
  let settled=false;h.app.init().then(()=>{settled=true;});
  await h.clock.flush();await h.clock.drain(60000);
  assert.equal(settled,false);assert.equal(h.clock.timers.size,0);
  return {confirmed_robustness_gap:true,fault_injection:true,initialization_resolved:settled,remaining_application_timeout_timers:h.clock.timers.size,network_api_calls_completed:true};
 });
 await check('Historical wallet snapshot regresses the first tab after second tab advances',async()=>{
  let lost=true;
  const first=harness({instant:true,bonuses:false,behavior:()=>lost?'lost-response':undefined});
  await manual(first);
  const second=harness({instant:true,bonuses:false,backend:first.backend});
  second.state.bet=500; await manual(second);
  lost=false; await manual(first);
  assert.equal(first.state.balance,999800); assert.equal(first.wallet().balance_cents,999300);
  return {confirmed_bug:true,displayed_cents:first.state.balance,actual_cents:first.wallet().balance_cents,displayed_rounds:first.state.stats.rounds,actual_rounds:first.wallet().rounds,unique_charges:first.ledger.size};
 });
 await check('Reload during animation forgets the stake of the settled active round',async()=>{
  const first=harness({instant:false,bonuses:false}); first.state.bet=10000;
  const p=first.app.spin(); await first.clock.until(()=>!!first.state.selected,'response accepted');
  assert.equal(first.state.busy,true); assert.equal(first.storage.size,0);
  const reloaded=harness({boot:true,backend:first.backend,sessionStorage:first.storage});
  let done=false; const init=reloaded.app.init().then(()=>{done=true;});
  await reloaded.clock.until(()=>done,'reload'); await init;
  assert.equal(reloaded.state.bet,200); assert.equal(reloaded.state.currentBet,10000);
  await first.finished(); await p;
  return {confirmed_bug:true,displayed_bet_cents:reloaded.state.bet,last_round_bet_cents:reloaded.state.currentBet,pending_retained:!!reloaded.state.pending};
 });
 const cap=JSON.parse(fs.readFileSync(path.join(__dirname,'cap_fixture.json'),'utf8'));
 await check('Actual maximum book settles at cap and leaves a permanent cap notice',async()=>{
  const h=harness({instant:false,roundFactory:()=>cap}); await manual(h);
  assert.equal(h.errors.length,0); assert.equal(h.state.selected.round.payout_units,500000);
  assert.match(h.ids['round-note'].textContent,/5000/);
  return {passed:true,win_cents:h.state.selected.win_cents,cap_reduction_units:cap.cap_reduction_units,note:h.ids['round-note'].textContent,last_line_label:h.ids['win-detail'].textContent};
 });
 await check('Malformed cascade coordinates survive validation then crash presentation',async()=>{
  const bad=JSON.parse(JSON.stringify(cap)); bad.base.cascades[0].removed_positions=[[999,0]];
  const h=harness({instant:false,roundFactory:()=>bad}); await manual(h);
  assert.ok(h.errors.length>0); assert.equal(h.state.pending,null);
  return {confirmed_validation_gap:true,fault_injection:true,presentation_errors:h.errors,pending_retained:!!h.state.pending,recorded_as_history:h.state.history.length,auto_status:h.state.autoStatus};
 });
 fs.writeFileSync(path.join(__dirname,'extended_frontend_results.json'),JSON.stringify({scope:'Actual app.js in Node VM; fresh targeted reproductions, not browser rendering',checks},null,2));
 console.log(JSON.stringify(checks,null,2));
 if(checks.some(x=>x.error))process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
