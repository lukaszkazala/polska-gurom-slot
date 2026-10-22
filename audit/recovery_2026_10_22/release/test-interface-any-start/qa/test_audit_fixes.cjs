"use strict";
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const {harness, clone} = require("./test_autoplay.cjs");
const fixtures = JSON.parse(fs.readFileSync(path.join(__dirname,"regression_fixtures.json"),"utf8"));
const artContext={window:{}};
require("node:vm").runInNewContext(fs.readFileSync(path.join(__dirname,"../web/art-catalog.js"),"utf8"),artContext);
const checks=[];
async function check(name, work) {
  try { checks.push({name,passed:true,...await work()}); console.log(`PASS ${name}`); }
  catch(error) { checks.push({name,passed:false,error:error.stack}); console.error(`FAIL ${name}: ${error.message}`); }
}
async function manual(h) { const pending=h.app.spin(); await h.finished(); await pending; }
async function initialize(h) { let done=false; const pending=h.app.init().finally(()=>{done=true;}); await h.clock.until(()=>done,"initialization"); await pending; }
async function main() {
  for (const [name,round] of Object.entries(fixtures.rounds)) await check(`Real ${name} round passes full validation and exact presentation`,async()=>{
    const h=harness({roundFactory:()=>round,speed:"turbo"}); await manual(h);
    assert.equal(h.state.pending,null);assert.equal(h.state.selected.round.payout_units,round.payout_units);
    assert.equal(h.state.balance,h.wallet().balance_cents);assert.equal(h.errors.length,0);assert.equal(h.ledger.size,1);
    return {payout_units:round.payout_units};
  });
  await check("Recovery after a second tab uses the current wallet without charging again",async()=>{
    let lost=true; const first=harness({instant:true,bonuses:false,behavior:()=>lost?"lost-response":undefined});await manual(first);
    const second=harness({instant:true,bonuses:false,backend:first.backend});second.state.bet=500;await manual(second);
    lost=false;await manual(first);
    assert.equal(first.state.balance,first.wallet().balance_cents);assert.equal(first.state.stats.rounds,2);assert.equal(first.ledger.size,2);
    assert.notEqual(first.state.selected.balance_cents,first.state.balance);
    return {current_wallet_cents:first.state.balance,immutable_round_wallet_cents:first.state.selected.balance_cents};
  });
  for (const failure of ["http-404","fetch-stall"]) await check(`Wallet ${failure} after settlement preserves the original paid request`,async()=>{
    let failing=true;
    const h=harness({instant:true,bonuses:false,initBehavior:url=>url==="/api/wallet"&&failing?failure:undefined});
    await manual(h);assert.equal(h.ledger.size,1);assert.ok(h.state.pending);assert.equal(h.state.history.length,0);
    const id=h.state.pending.request_id;failing=false;await manual(h);
    assert.equal(h.ledger.size,1);assert.equal(h.state.pending,null);assert.ok(h.requests.every(r=>r.request_id===id));
    assert.equal(h.state.balance,h.wallet().balance_cents);return {unique_charges:1};
  });
  await check("Reload during base presentation retains stake and the same paid request",async()=>{
    const first=harness({bonuses:false});first.state.bet=10000;first.app.spin();
    await first.clock.until(()=>!!first.state.selected,"accepted response");
    assert.equal(first.state.busy,true);assert.ok(first.state.pending);
    const id=first.state.pending.request_id;
    const reloaded=harness({boot:true,backend:first.backend,sessionStorage:first.storage,localStorage:first.preferences});await initialize(reloaded);
    assert.equal(reloaded.state.bet,10000);assert.equal(reloaded.state.currentBet,10000);assert.equal(reloaded.state.pending.request_id,id);
    await manual(reloaded);assert.equal(reloaded.ledger.size,1);assert.equal(reloaded.state.pending,null);assert.equal(reloaded.storage.size,0);
    return {bet_cents:reloaded.state.bet,unique_charges:reloaded.ledger.size};
  });
  await check("Reload after four bonus spins resumes at the fifth and leaves AUTO stopped",async()=>{
    const first=harness({roundFactory:()=>fixtures.rounds.bonus12,speed:"turbo"});first.state.autoCount=10;first.start();
    await first.clock.until(()=>first.state.presentation?.freeCompleted===4,"four completed free spins");
    const reloaded=harness({boot:true,backend:first.backend,sessionStorage:first.storage,localStorage:first.preferences});await initialize(reloaded);
    assert.equal(reloaded.state.presentation.freeCompleted,4);assert.equal(reloaded.state.auto,0);
    reloaded.state.speed="turbo";
    const progress=[],element=reloaded.ids["bonus-progress"],descriptor=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(element),"textContent");
    Object.defineProperty(element,"textContent",{get(){return descriptor.get.call(this);},set(value){progress.push(String(value));descriptor.set.call(this,value);}});
    await manual(reloaded);
    assert.ok(progress.includes("5 / 12"));assert.ok(!progress.includes("1 / 12"));assert.equal(element.textContent,"12 / 12");
    assert.equal(reloaded.state.auto,0);assert.equal(reloaded.state.autoCompleted,1);assert.equal(reloaded.ledger.size,1);
    assert.equal(reloaded.state.balance,reloaded.wallet().balance_cents);assert.equal(reloaded.errors.length,0);
    return {unique_charges:reloaded.ledger.size,resumed_progress:progress};
  });
  const mutations={
    "removed row outside board":r=>r.base.cascades[0].removed_positions=[[999,0]],
    "malformed position":r=>r.base.cascades[0].removed_positions=[[0]],
    "duplicate removed position":r=>r.base.cascades[0].removed_positions.push(clone(r.base.cascades[0].removed_positions[0])),
    "missing removal":r=>r.base.cascades[0].removed_positions.pop(),
    "movement outside board":r=>r.base.cascades[0].movements[0].to_row=999,
    "fractional movement source":r=>r.base.cascades[0].movements[0].from_row=-0.5,
    "missing movement":r=>r.base.cascades[0].movements.pop(),
    "incorrect moving symbol":r=>r.base.cascades[0].movements[0].symbol="SCATTER",
    "incorrect stage sum":r=>r.base.cascades[0].line_payout_units+=10,
    "incorrect bonus aggregate":r=>r.bonus_payout_units+=10,
    "incorrect cap reduction":r=>r.cap_reduction_units+=10,
    "missing cascade data":r=>delete r.base.cascades,
    "empty cascade data":r=>r.base.cascades=[],
  };
  for(const [name,mutate] of Object.entries(mutations))await check(`Reject ${name} before presenting or clearing pending`,async()=>{
    const bad=clone(fixtures.rounds.cap);mutate(bad);
    const h=harness({instant:true,roundFactory:()=>bad});await manual(h);
    assert.ok(h.state.pending);assert.equal(h.state.history.length,0);assert.equal(h.errors.length,0);assert.equal(h.ledger.size,1);
    return {unique_charges:1,pending_preserved:true};
  });
  for(const behavior of ["stall","error"])await check(`Artwork ${behavior} falls back and leaves the game usable`,async()=>{
    const h=harness({boot:true,imageBehavior:behavior,artwork:artContext.window.PG_ART});
    h.state.online=false;await initialize(h);
    assert.equal(h.state.online,true);assert.equal(h.state.artReady,false);assert.equal(h.ids["spin-button"].disabled,false);assert.equal(h.errors.length,0);
    if(behavior==="stall")assert.equal(h.clock.now,15000);
    return {startup_ms:h.clock.now,play_enabled:true};
  });
  for(const lang of ["pl","en","de"])await check(`Rules in ${lang} explain all-WILD payouts and tie removal`,async()=>{
    const h=harness({boot:true});h.state.lang=lang;await initialize(h);h.ids["rules-button"].click();const text=h.ids["rules-content"].textContent;
    assert.match(text,/P4/);assert.match(text,/40×/);assert.match(text,lang==="pl"?/najbardziej z lewej/:lang==="en"?/furthest left/:/weitesten links/);
    return {explained:true};
  });
  const out=process.env.PG_QA_OUT_DIR||__dirname;fs.mkdirSync(out,{recursive:true});
  const report={passed:checks.every(c=>c.passed),checks_total:checks.length,checks_passed:checks.filter(c=>c.passed).length,checks};
  fs.writeFileSync(path.join(out,"audit_fixes_frontend.json"),JSON.stringify(report,null,2));
  console.log(JSON.stringify({passed:report.passed,total:checks.length,passed_count:report.checks_passed}));if(!report.passed)process.exitCode=1;
}
main().catch(error=>{console.error(error);process.exitCode=1;});
