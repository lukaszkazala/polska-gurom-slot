'use strict';
const fs=require('node:fs'),path=require('node:path'),readline=require('node:readline');
const {harness,config}=require('../../test-interface-any-start/qa/test_autoplay.cjs');
const h=harness({boot:true}), rgs=harness({boot:true,rgs:true}), failures=[]; rgs.state.rgs={};let count=0;
(async()=>{
 for await(const line of readline.createInterface({input:process.stdin,crlfDelay:Infinity})){
  const book=JSON.parse(line),round=book.events[0].data;
  const request={bet_cents:200,mode:'random',request_id:'bank-validator'};
  const win=2*round.payout_units;
  const result={...request,round,round_id:'book-'+book.id,session_id:'probe-session',math_version:config.math_version,
    is_scenario:false,balance_before_cents:1000000,balance_cents:999800+win,win_cents:win,
    stats:{rounds:1,total_bet_cents:200,total_win_cents:win}};
  try{h.app.validateSpinResponse(result,request);}catch(e){if(failures.length<20)failures.push({id:book.id,error:e.message});}
  try { const micro={...result,rgs:true,rgs_active:win>0,balance_cents:999800}; rgs.app.validateSpinResponse(micro,request); } catch(e) { if(failures.length<20)failures.push({id:book.id,transport:'rgs',error:e.message}); }
  count++;
 }
 const report={passed:count===100049&&!failures.length,books_checked:count,failures,
    rgs_envelopes_checked:count,scope:'Every real exported round through the actual UI validator, local and synthetic RGS envelopes; not a real platform response test'};
 fs.writeFileSync(path.join(__dirname,'frontend_bank_validation.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report));if(!report.passed)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
