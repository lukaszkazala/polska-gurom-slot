"use strict";
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path"), vm = require("node:vm");
const { harness, config } = require("./test_autoplay.cjs");
const root = path.resolve(__dirname, ".."), checks = [];
const fixtures = JSON.parse(fs.readFileSync(path.join(__dirname, "regression_fixtures.json")));
Object.assign(fixtures.rounds, JSON.parse(fs.readFileSync(path.join(__dirname, "audio_readability_fixtures.json"))));
function audioHarness(options = {}) {
  const nodes = [], contexts = [], fetches = [], storage = new Map(options.muted ? [["pg-muted", "true"]] : []);
  const listeners = {}, windows = {}, timers = new Map(); let serial = 0;
  const makeNode = type => {
    const node = { type, gain: { value: 1, cancelScheduledValues() {}, setValueAtTime(v) { this.value = v; }, linearRampToValueAtTime(v) { this.value = v; } },
      connect(target) { this.target = target; }, disconnect() { this.disconnected = true; },
      start() { this.started = true; }, stop(at) { this.stopped = true; this.stopAt = at; } };
    nodes.push(node); return node;
  };
  class AudioContext {
    constructor() { this.currentTime = 10; this.state = "suspended"; this.destination = {}; contexts.push(this); }
    createGain() { return makeNode("gain"); } createBufferSource() { return makeNode("source"); }
    async resume() { if (options.blocked) throw Error("blocked"); this.state = "running"; }
    async decodeAudioData(data) { return { file: data }; } async close() { this.state = "closed"; }
  }
  const context = { window: { AudioContext: options.unsupported ? undefined : AudioContext, addEventListener: (k,v) => windows[k] = v },
    document: { hidden: false, addEventListener: (k,v) => listeners[k] = v },
    localStorage: { getItem(k) { if (options.noStorage) throw Error("storage"); return storage.get(k); }, setItem(k,v) { if (options.noStorage) throw Error("storage"); storage.set(k,v); } },
    AbortController, setTimeout(cb) { timers.set(++serial, cb); return serial; }, clearTimeout(id) { timers.delete(id); },
    fetch: async url => { fetches.push(url); if (options.fetchFail) throw Error("offline"); return { ok: true, arrayBuffer: async () => url }; }
  };
  vm.runInNewContext(fs.readFileSync(path.join(root, "web/audio.js"), "utf8"), context);
  return { audio: context.window.PG_AUDIO, nodes, contexts, fetches, storage, timers,
    hide(hidden) { context.document.hidden = hidden; listeners.visibilitychange(); }, windows,
    async flush() { for (let i=0;i<30;i++) await Promise.resolve(); }
  };
}
async function check(name, work) { await work(); checks.push({name, passed:true}); console.log("PASS " + name); }
(async () => {
  await check("No audio before a user gesture; all six local buffers decode once", async () => {
    const h = audioHarness(); assert.equal(h.contexts.length,0); assert.equal(h.fetches.length,0);
    h.audio.unlock(); await h.flush(); assert.equal(h.audio.status.loaded.length,6); assert.equal(h.fetches.length,6);
    assert.equal(h.nodes.filter(n=>n.loop && n.started).length,1); h.audio.unlock(); await h.flush(); assert.equal(h.fetches.length,6);
  });
  await check("Only positive net wins use fanfares; partial/break-even returns remain quiet", async () => {
    const h=audioHarness(); h.audio.unlock(); await h.flush();
    const source=()=>h.nodes.filter(n=>n.type==="source" && !n.loop).at(-1);
    h.audio.result(0,200); assert.equal(source(),undefined);
    for(const win of [100,200]) { h.audio.result(win,200); assert.match(source().buffer.file,/06_/); assert.equal(source().target.gain.value,.28); }
    h.audio.result(201,200); assert.match(source().buffer.file,/04_/);
    const previous=source(); h.audio.result(4000,200); assert.equal(previous.stopped,true); assert.match(source().buffer.file,/05_/);
    assert.equal(h.nodes.filter(n=>n.type==="source" && !n.loop && !n.stopped).length,1);
  });
  await check("Crossfade bonus loop; immediate master mute cuts a fanfare and persists", async () => {
    const h=audioHarness(); h.audio.unlock(); await h.flush(); h.audio.bonus();
    assert.equal(h.audio.status.scene,"bonus"); assert.equal(h.audio.status.cue,true);
    const old=h.nodes.find(n=>n.loop && n.buffer.file.includes("01_")); assert.equal(old.stopped,true); assert.equal(old.stopAt,10.32);
    h.audio.toggle(); assert.equal(h.nodes[0].gain.value,0); assert.equal(h.audio.status.cue,false); assert.equal(h.storage.get("pg-muted"),"true");
    h.audio.result(5000,200); assert.equal(h.audio.status.cue,false);
    h.audio.toggle(); await h.flush(); assert.equal(h.nodes[0].gain.value,1); assert.equal(h.audio.status.cue,false);
  });
  await check("Hidden tabs are silent; returning never replays an old cue", async () => {
    const h=audioHarness(); h.audio.unlock(); await h.flush(); h.audio.result(4000,200); h.hide(true);
    assert.equal(h.nodes[0].gain.value,0); assert.equal(h.audio.status.cue,false); h.audio.bonus(); assert.equal(h.audio.status.cue,false);
    h.hide(false); assert.equal(h.nodes[0].gain.value,1); assert.equal(h.audio.status.cue,false);
  });
  await check("Saved mute, missing files, unavailable storage and blocked audio are nonfatal", async () => {
    for(const options of [{muted:true},{fetchFail:true},{noStorage:true},{blocked:true},{unsupported:true}]) {
      const h=audioHarness(options); h.audio.unlock(); h.audio.result(500,200); await h.flush();
      assert.equal(h.timers.size,0); if(options.muted) assert.equal(h.nodes[0].gain.value,0);
      if(options.fetchFail) { assert.equal(h.audio.status.loaded.length,0); h.audio.unlock(); await h.flush(); assert.equal(h.fetches.length,12); }
    }
  });
  await check("Late buffers never play a stale win; closing page releases audio", async () => {
    const h=audioHarness(); h.audio.unlock(); h.audio.result(5000,200); await h.flush(); assert.equal(h.audio.status.cue,false);
    h.windows.pagehide({persisted:false}); await h.flush(); assert.equal(h.contexts[0].state,"closed");
  });
  const payout = value=>value.payout_units/config.payout_scale;
  const win=Object.values(fixtures.rounds).find(r=>payout(r)>1 && payout(r)<20 && !r.free_spins.length);
  const partial=Object.values(fixtures.rounds).find(r=>payout(r)>0 && payout(r)<1);
  const big=Object.values(fixtures.rounds).find(r=>payout(r)>=20 && payout(r)<5000);
  const cap=Object.values(fixtures.rounds).find(r=>payout(r)===5000);
  assert.ok(win && partial && big && cap,"Fixture coverage for payout classes");
  for(const instant of [false,true]) for(const reducedMotion of [false,true]) for(const [label,round,minimum] of [["partial",partial,900],["win",win,1200],["big",big,1800],["cap",cap,2400]]) {
    await check(`${instant?"instant":"turbo"} ${label}, reduced motion ${reducedMotion}: readable AUTO hold >=${minimum}ms`, async () => {
      const calls=[], audio={muted:false,unlock(){calls.push("unlock");},beginRound(){calls.push("begin");},bonus(){calls.push("bonus");},scene(key){calls.push(key);},result(w,b){calls.push([w,b]);},toggle(){this.muted=!this.muted;}};
      const h=harness({speed:"turbo",instant,reducedMotion,audio,roundFactory:()=>round}); h.start();
      await h.clock.until(()=>h.state.autoCompleted===1&&!h.state.busy,"first visible result");
      const timer=h.clock.timers.get(h.state.autoTimer); assert.ok(timer); assert.ok(timer.due-h.clock.now>=minimum);
      assert.equal(h.ids["meter-win"].textContent,h.app.money(h.state.selected.win_cents));
      assert.ok(h.ids["win-caption"].textContent.includes(h.app.money(h.state.selected.win_cents)));
      h.ids["sound-button"].click(); assert.equal(h.ids["sound-button"].attrs["aria-pressed"],"true");
      assert.equal(h.ids["sound-button"].disabled,false); assert.equal(calls.filter(Array.isArray).length,1);
      h.stop(); await h.clock.drain(); assert.equal(h.ledger.size,1); assert.equal(h.errors.length,0);
    });
  }
  await check("Winning cascade frames remain visible >=450ms even in turbo/reduced motion",async()=>{
    for(const reducedMotion of [false,true]) {
      const h=harness({speed:"turbo",reducedMotion,roundFactory:()=>fixtures.rounds.cascade});
      const events=[], element=h.ids["win-caption"], descriptor=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(element),"textContent");
      Object.defineProperty(element,"textContent",{get(){return descriptor.get.call(this);},set(v){events.push({text:String(v),time:h.clock.now});descriptor.set.call(this,v);}});
      const work=h.app.spin(); await h.finished(); await work;
      const stages=events.filter(e=>/KASKADA/.test(e.text)); assert.ok(stages.length>1);
      for(let i=1;i<stages.length;i++) assert.ok(stages[i].time-stages[i-1].time>=450);
      assert.equal(h.errors.length,0);
    }
  });
  await check("Mute remains operable during a spin, with all localized labels", async()=>{
    for(const [lang,label] of [["pl","Włącz dźwięk"],["en","Enable sound"],["de","Ton einschalten"]]) {
      const audio={muted:false,unlock(){},beginRound(){},result(){},toggle(){this.muted=!this.muted;}};
      const h=harness({audio,speed:"turbo",roundFactory:()=>win}); h.state.lang=lang;
      const work=h.app.spin(); await h.clock.until(()=>h.state.busy && h.state.cells.some(c=>c.classes.has("spinning")),"spinning");
      h.ids["sound-button"].click(); assert.equal(audio.muted,true); assert.equal(h.ids["sound-button"].attrs["aria-label"],label);
      assert.equal(h.ids["sound-button"].disabled,false); await h.finished(); await work; assert.equal(h.errors.length,0);
    }
  });
  const out=path.resolve(root,"../audit/audio_readability_2026_10_22"); fs.mkdirSync(out,{recursive:true});
  fs.writeFileSync(path.join(out,"logic_results.json"),JSON.stringify({passed:true,method:"Real audio module with a simulated Web Audio graph; real app with engine fixtures and virtual time. Browser/subjective listening recorded separately.",checks},null,2));
  console.log(`${checks.length} checks passed`);
})().catch(e=>{console.error(e);process.exitCode=1;});
