// Read-only logic probes. This minimal DOM is deliberately not a browser/E2E test.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const crypto = require('crypto');
const assert = require('assert');
const OUT = __dirname;
const ROOT = path.resolve(OUT, '../../..');
const APP = path.join(ROOT, 'test-interface/web/app.js');
const source = fs.readFileSync(APP, 'utf8');
const fixtures = JSON.parse(fs.readFileSync(path.join(OUT, 'fixtures.json'), 'utf8'));

class Element {
  constructor(tagName='DIV') { this.tagName=tagName.toUpperCase(); this.children=[]; this.dataset={}; this.value=''; this.disabled=false; this.hidden=false; this.listeners={}; this.attrs={}; this.classes=new Set(); this._text=''; this.classList={add:(...v)=>v.forEach(x=>this.classes.add(x)),remove:(...v)=>v.forEach(x=>this.classes.delete(x)),toggle:(x,b)=>{b=b??!this.classes.has(x);b?this.classes.add(x):this.classes.delete(x);return b;}}; }
  set textContent(v) {this._text=String(v);this.children=[];} get textContent(){return this._text;}
  set className(v) {this.classes=new Set(v.split(/\s+/));} get className(){return [...this.classes].join(' ');}
  append(...nodes){this.children.push(...nodes);} replaceChildren(...nodes){this.children=[...nodes];this._text='';}
  setAttribute(k,v){this.attrs[k]=String(v);} removeAttribute(k){delete this.attrs[k];}
  addEventListener(k,fn){(this.listeners[k]??=[]).push(fn);} emit(k,event={}) {for(const fn of this.listeners[k]??[])fn({target:this,...event});}
  querySelectorAll(q){return this.children.filter(c=>q==='button'?c.tagName==='BUTTON':false);}
  querySelector(q){return this.children.find(c=>q===`[value="${c.value}"]`)??null;}
  showModal(){this.attrs.open='';} close(){delete this.attrs.open;} click(){this.emit('click');}
}
function makeHarness(response=fixtures.cap) {
  const ids = Object.fromEntries([...fs.readFileSync(path.join(ROOT,'test-interface/web/index.html'),'utf8').matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));
  ids['test-mode-select'].value='random';ids['auto-count'].value='10';
  for(const mode of ['random','win','bonus','expansion']){const option=new Element('option');option.value=mode;ids['test-mode-select'].append(option);}
  const document={hidden:false,documentElement:{lang:'pl'},getElementById:id=>ids[id],createElement:tag=>new Element(tag),createElementNS:(_,tag)=>new Element(tag),querySelector:()=>null,querySelectorAll:()=>[],addEventListener:()=>{}};
  const intervals=new Map(),autoTimers=new Map();let next=0,requests=0;
  const timer=(fn,ms)=>{const id=++next;if(fn.name==='spin'){autoTimers.set(id,fn);return id;} if(ms>=10000){return {real:setTimeout(fn,ms)};}setImmediate(fn);return id;};
  const context={console,document,Intl,URL,Blob,AbortController,crypto,localStorage:{getItem:()=>null,setItem:()=>{}},location:{origin:'http://127.0.0.1:8765'},window:{matchMedia:()=>({matches:false}),addEventListener:()=>{}},matchMedia:()=>({matches:false}),setTimeout:timer,clearTimeout:id=>{if(id?.real)clearTimeout(id.real);autoTimers.delete(id);},setInterval:fn=>{const id=++next;intervals.set(id,fn);return id;},clearInterval:id=>intervals.delete(id),fetch:async(url,options)=>{if(url==='/api/spin')requests++;return {ok:true,json:async()=>JSON.parse(JSON.stringify(response))};}};
  const exposed=source.replace(/\s+init\(\);\s+\}\)\(\);\s*$/, '\n globalThis.audit={state,controls,spin,translate,presentWins,createGrid,bindEvents};\n})();');
  assert.notEqual(exposed,source);
  vm.runInNewContext(exposed,context,{filename:APP});
  const audit=context.audit;
  Object.assign(audit.state,{config:fixtures.config,symbols:fixtures.symbols,online:true,balance:1_000_000,bet:100,currentBet:100,fast:true});
  audit.createGrid();
  return {audit,ids,intervals,autoTimers,requests:()=>requests};
}

(async()=>{
  const cap=makeHarness();
  await cap.audit.spin();
  assert.equal(cap.audit.state.history.length,1);
  assert.equal(cap.audit.state.balance,fixtures.cap.balance_cents);
  const capMessage=cap.ids['win-detail'].textContent;
  assert.match(capMessage,/5000/);
  const lineCycle=[...cap.intervals.values()][0];assert.equal(typeof lineCycle,'function');lineCycle();
  const afterCycle=cap.ids['win-detail'].textContent;
  assert.notEqual(afterCycle,capMessage);
  assert.equal(fixtures.cap.round.free_spin_credits.at(-1),0);

  const language=makeHarness();
  language.audit.state.history=[{...fixtures.history,displayed_at:fixtures.history.created_at}];
  language.audit.state.currentSpin=fixtures.cap.round.free_spins[0];
  language.audit.state.busy=true;
  language.ids['total-win-value'].textContent='123,45 zł';
  language.audit.controls();
  assert.equal(language.ids['lang-select'].disabled,false);
  language.audit.state.lang='en';language.audit.translate();
  assert.notEqual(language.ids['total-win-value'].textContent,'123,45 zł');

  const automatic=makeHarness();automatic.audit.bindEvents();
  automatic.audit.state.auto=2;await automatic.audit.spin();
  assert.equal(automatic.audit.state.auto,1);assert.equal(automatic.autoTimers.size,1);
  const callbacks=[...automatic.autoTimers.values()];automatic.ids['auto-button'].emit('click');
  assert.equal(automatic.audit.state.auto,0);assert.equal(automatic.autoTimers.size,0);assert.equal(automatic.requests(),1);
  // Captured old callbacks would only run if an external caller deliberately ran them.
  const report={
    method:'Original app.js evaluated with a minimal fake DOM and real engine-result fixtures; no browser layout, touch, rendering, or network integration is claimed.',
    source_sha256:crypto.createHash('sha256').update(source).digest('hex'),
    cap_warning_overwritten_by_line_cycle:{before:capMessage,after:afterCycle,last_free_spin_credit_units:0,total_win_stays:cap.ids['total-win-value'].textContent,balance_correct:cap.audit.state.balance===fixtures.cap.balance_cents},
    change_language_during_spin:{language_control_enabled:true,total_before:'123,45 zł',total_after:language.ids['total-win-value'].textContent,caption_after:language.ids['win-caption'].textContent,busy:language.audit.state.busy},
    autoplay:{after_one_of_two_rounds_remaining:1,scheduled_next:callbacks.length,stop_clears_scheduled:true,requests_after_stop:automatic.requests()},
  };
  fs.writeFileSync(path.join(OUT,'presentation_probe_results.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify(report,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
