"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
class Node {
  constructor(){this.children=[];this.dataset={};this.style={setProperty(){}};this.events={};}
  append(...nodes){for(const n of nodes){n.parent=this;this.children.push(n);}}
  remove(){this.parent.children=this.parent.children.filter(n=>n!==this);}
  setAttribute(){}
  addEventListener(name,fn){this.events[name]=fn;}
}
async function run(){
  const cabinet=new Node(),listeners={},timers=new Map();let reduced=false,serial=0;
  const document={hidden:false,documentElement:{lang:"pl"},querySelector:()=>cabinet,createElement:()=>new Node(),addEventListener:(name,fn)=>listeners[name]=fn};
  const window={addEventListener(){}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,"../web/celebrations.js"),"utf8"),{window,document,matchMedia:()=>({matches:reduced}),setTimeout:(fn,ms)=>{timers.set(++serial,{fn,ms});return serial;},clearTimeout:id=>timers.delete(id)});
  const fx=window.PG_CELEBRATION;
  for(const [win,bet,expected] of [[0,200,null],[3999,200,null],[4000,200,"big"],[9999,200,"big"],[10000,200,"mega"],[19999,200,"mega"],[20000,200,"epic"],[100,0,null],[Infinity,200,null]])assert.equal(fx.tier(win,bet),expected);
  let p=fx.play({kind:"mega",value:"100,00 zł",duration:2200});
  assert.equal(cabinet.children.length,1);assert.equal([...timers.values()][0].ms,2200);
  assert.equal(cabinet.children[0].children[2].children[2].textContent,"100,00 zł");
  cabinet.children[0].children[3].events.click();await p;
  assert.equal(cabinet.children.length,0);assert.equal(timers.size,0);
  const first=fx.play();const second=fx.play();await first;assert.equal(cabinet.children.length,1);
  document.hidden=true;listeners.visibilitychange();await second;assert.equal(cabinet.children.length,0);assert.equal(timers.size,0);
  await fx.play();assert.equal(cabinet.children.length,0);
  document.hidden=false;reduced=true;p=fx.play();
  assert.equal(cabinet.children[0].children[1].children.length,0);assert.equal([...timers.values()][0].ms,650);
  [...timers.values()][0].fn();await p;assert.equal(timers.size,0);assert.equal(cabinet.children.length,0);
  console.log("PASS: thresholds, credited amounts supplied unchanged, skip resolves wait, replacement removes previous overlay, hidden-page cleanup, reduced motion, timer cleanup.");
}
run().catch(error=>{console.error(error);process.exitCode=1;});
