"use strict";
const assert = require("node:assert/strict"), vm = require("node:vm"), fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
const { RgsMock, fixtures, clone } = require("./rgs_mock.cjs");
const { harness } = require("./test_autoplay.cjs");
const context = { window: {}, URL, TextEncoder, AbortController, setTimeout, clearTimeout };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../web/rgs-client.js"), "utf8"), context);
const RGS = context.window.PG_RGS, checks = [];
const href = "http://127.0.0.1:8800/?sessionID=local-test-session&rgs_url=127.0.0.1%3A8800&demo=true&lang=pl";
async function check(name, work) {
  try { await work(); checks.push({ name, passed: true }); console.log("PASS " + name); }
  catch (error) { checks.push({ name, passed: false, error: error.stack }); console.error("FAIL " + name + ": " + error.stack); }
}
function client(mock = new RgsMock({ kind: "bonus12" }), storage = new Map()) {
  const store = { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value) };
  return { mock, storage, app: new RGS.Client(RGS.launch(href), { fetch: mock.fetch, storage: store, crypto: crypto.webcrypto }) };
}
const request = () => ({ bet_cents: 500000, mode: "random", request_id: crypto.randomUUID() });
const progress = (result, freeCompleted = 4, baseComplete = true) => ({ round_id: result.round_id, baseComplete, freeCompleted });
async function started(mock) { const h = client(mock); await h.app.boot(fixtures.config); h.req = request(); h.result = await h.app.play(h.req); return h; }
async function ui(mock, storage) {
  const h = harness({ rgs: true, boot: true, href, fetch: mock.fetch, sessionStorage: storage });
  await h.app.init(); return h;
}
async function spin(h) { const work = h.app.spin(); await h.finished(); await work; }
function record(result, fields = {}) { return JSON.stringify({ v: 1, game: "polska-gurom", math: fixtures.config.math_version, ...progress(result), ...fields }); }
async function main() {
  await check("Checkpoint uses authenticated bet/event with no amount or new play", async () => {
    const h = await started(); await h.app.checkpoint(progress(h.result));
    const call = h.mock.calls.find(c => c.path === "/bet/event");
    assert.deepEqual(Object.keys(call.body).sort(), ["event", "sessionID"]);
    assert.equal(JSON.parse(call.body.event).freeCompleted, 4); assert.equal(h.mock.charges, 1); assert.equal(h.mock.settlements, 0);
  });
  await check("New browser state resumes server checkpoint without local recovery storage", async () => {
    const h = await started(); await h.app.checkpoint(progress(h.result));
    const next = client(h.mock), boot = await next.app.boot(fixtures.config);
    assert.equal(boot.pending.presentation.freeCompleted, 4); assert.equal(boot.pending.presentation.baseComplete, true);
    assert.equal(boot.pending.result.round_id, h.result.round_id); assert.equal(h.mock.charges, 1);
  });
  await check("Zero payout auto-closed round never sends bet/event or end-round", async () => {
    const h = await started(new RgsMock({ kind: "loss" })); await h.app.checkpoint(progress(h.result, 0)); await h.app.finish(h.result);
    assert.equal(h.mock.calls.filter(c => ["/bet/event", "/wallet/end-round"].includes(c.path)).length, 0);
  });
  await check("Duplicate or older checkpoints do not move progress backwards", async () => {
    const h = await started(); await h.app.checkpoint(progress(h.result, 6)); await h.app.checkpoint(progress(h.result, 4));
    assert.equal(JSON.parse(h.mock.round.event).freeCompleted, 6); assert.equal(h.mock.calls.filter(c => c.path === "/bet/event").length, 1);
  });
  await check("More advanced server checkpoint wins over older local checkpoint", async () => {
    const h = await started(); await h.app.checkpoint(progress(h.result, 4)); h.mock.round.event = record(h.result, { freeCompleted: 7 });
    const boot = await client(h.mock, h.storage).app.boot(fixtures.config); assert.equal(boot.pending.presentation.freeCompleted, 7);
  });
  await check("Local completed presentation survives lost checkpoint acknowledgement", async () => {
    const h = await started(); h.mock.failNext("/bet/event", "lost-response"); await assert.rejects(h.app.checkpoint(progress(h.result)));
    const boot = await client(h.mock, h.storage).app.boot(fixtures.config);
    assert.equal(boot.pending.presentation.freeCompleted, 4); assert.equal(h.mock.charges, 1);
  });
  await check("Lost event response remains recoverable even after losing all browser storage", async () => {
    const h = await started(); h.mock.failNext("/bet/event", "lost-response"); await assert.rejects(h.app.checkpoint(progress(h.result)));
    const boot = await client(h.mock).app.boot(fixtures.config); assert.equal(boot.pending.presentation.freeCompleted, 4);
  });
  await check("Checkpoint not reaching server preserves local completed progress", async () => {
    const h = await started(); h.mock.failNext("/bet/event", "network-before"); await assert.rejects(h.app.checkpoint(progress(h.result)));
    assert.equal(h.mock.round.event, undefined);
    const boot = await client(h.mock, h.storage).app.boot(fixtures.config); assert.equal(boot.pending.presentation.freeCompleted, 4);
  });
  for (const marker of ["not JSON", "{}", result => record(result, { round_id: "other-round" }), result => record(result, { v: 999 }), result => record(result, { game: "other-game" }), result => record(result, { math: "other-version" }), result => record(result, { freeCompleted: 99 }), result => record(result, { freeCompleted: -1 }), result => record(result, { baseComplete: false }), result => record(result, { freeCompleted: 1.5 })]) {
    await check("Malformed or foreign server checkpoint cannot skip unshown bonus " + checks.length, async () => {
      const h = await started(); h.mock.round.event = typeof marker === "function" ? marker(h.result) : marker;
      const boot = await client(h.mock).app.boot(fixtures.config); assert.equal(boot.pending.presentation.freeCompleted, 0); assert.equal(boot.pending.presentation.baseComplete, false);
    });
  }
  await check("Unconfirmed event echo is rejected and round is not settled", async () => {
    const h = await started(); h.mock.failNext("/bet/event", () => ({ event: "wrong" }));
    await assert.rejects(h.app.checkpoint(progress(h.result)), e => e.code === "rgs_progress_unconfirmed"); assert.ok(h.app.pending); assert.equal(h.mock.settlements, 0);
  });
  await check("Same betID with changed authoritative outcome cannot settle cached result", async () => {
    const h = await started(); h.mock.round.state[0].data.base.grid[0][0] = "WILD";
    await assert.rejects(h.app.finish(h.result), e => e.code === "rgs_round_mismatch"); assert.equal(h.mock.settlements, 0); assert.ok(h.app.pending);
  });
  await check("Object key order differences do not change the authoritative outcome", async () => {
    const h = await started(); const data = h.mock.round.state[0].data;
    h.mock.round.state[0].data = Object.fromEntries(Object.entries(data).reverse());
    await h.app.finish(h.result); assert.equal(h.mock.settlements, 1);
  });
  await check("Expired session while recovering does not discard uncertain paid intent", async () => {
    const h = await started(); h.mock.failNext("/wallet/authenticate", "expired");
    await assert.rejects(h.app.play(h.req), e => e.code === "session_expired" && e.uncertain); assert.ok(h.app.pending);
    const result = await h.app.play(h.req); await h.app.finish(result); assert.equal(h.mock.charges, 1); assert.equal(h.mock.settlements, 1);
  });
  await check("Concurrent finish requests cannot issue two end-round calls", async () => {
    const h = await started(); let release; const fetch = h.app.fetch;
    h.app.fetch = async (url, init) => { if (url.endsWith("/wallet/end-round")) await new Promise(resolve => { release = resolve; }); return fetch(url, init); };
    const first = h.app.finish(h.result); while (!release) await Promise.resolve();
    await assert.rejects(h.app.finish(h.result), e => e.code === "rgs_request_in_progress"); release(); await first;
    assert.equal(h.mock.calls.filter(c => c.path === "/wallet/end-round").length, 1); assert.equal(h.mock.settlements, 1);
  });
  for (const fault of ["network-before", "500", "lost-response", "bad-json"]) await check("Settlement " + fault + " retries by recovery, never by new play", async () => {
    const h = await started(); await h.app.checkpoint(progress(h.result, 12));
    h.mock.failNext("/wallet/end-round", fault); await assert.rejects(h.app.finish(h.result));
    const next = client(h.mock, h.storage), boot = await next.app.boot(fixtures.config);
    assert.equal(boot.pending.presentation.freeCompleted, 12);
    await next.app.finish(boot.pending.result); assert.equal(h.mock.charges, 1); assert.equal(h.mock.settlements, 1);
  });
  await check("Initial authentication failure offers reconnect without duplicate handlers or cells", async () => {
    const mock = new RgsMock(); mock.failNext("/wallet/authenticate", "network-before"); const h = await ui(mock);
    assert.equal(h.state.online, false); assert.equal(h.ids["reconnect-button"].hidden, false); assert.equal(mock.charges, 0);
    h.ids["reconnect-button"].click();
    for (let i = 0; i < 1000 && h.state.initializing; i++) await new Promise(setImmediate);
    assert.equal(h.state.online, true); assert.equal(h.ids["reconnect-button"].hidden, true); assert.equal(h.state.cells.length, 15);
    assert.equal(h.ids["spin-button"].listeners.click.length, 1); h.state.instant = true; await spin(h); assert.equal(mock.charges, 1);
  });
  for (const fault of ["network-before", "lost-response"]) await check("Bonus pauses at fourth free spin after event " + fault + " and resumes safely", async () => {
    const mock = new RgsMock({ kind: "bonus12" }), original = mock.fetch; let first = true;
    mock.fetch = async (url, init) => {
      if (url.endsWith("/bet/event") && JSON.parse(JSON.parse(init.body).event).freeCompleted === 4 && first) { first = false; mock.failNext("/bet/event", fault); }
      return original(url, init);
    };
    const h = await ui(mock); h.state.speed = "turbo"; h.start(); await h.finished();
    assert.equal(h.state.presentation.freeCompleted, 4); assert.equal(h.state.history.length, 0); assert.equal(h.state.auto, 0); assert.ok(h.state.pending);
    const shown = fixtures.rounds.bonus12.base.payout_units + fixtures.rounds.bonus12.free_spin_credits.slice(0, 4).reduce((a, b) => a + b, 0);
    assert.equal(h.ids["meter-win"].textContent, new Intl.NumberFormat("pl-PL", { style: "currency", currency: "USD" }).format(RGS.payout(500000, shown) / 1000000));
    await spin(h); assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1); assert.equal(h.state.pending, null); assert.equal(h.state.history.length, 1);
  });
  await check("Fresh UI without old browser storage resumes fifth free spin from RGS event", async () => {
    const first = await started(); await first.app.checkpoint(progress(first.result));
    const h = await ui(first.mock); assert.equal(h.state.presentation.freeCompleted, 4); assert.equal(h.state.bet, 500000);
    assert.equal(h.ids["bonus-progress"].textContent, "4 / 12"); assert.equal(h.ids["win-caption"].textContent, "Runda wstrzymana");
    h.state.instant = true; await spin(h); assert.equal(first.mock.charges, 1); assert.equal(first.mock.settlements, 1);
  });
  await check("Changed permitted stakes do not discard already paid active bonus", async () => {
    const first = await started(); await first.app.checkpoint(progress(first.result));
    first.mock.config.betLevels = [10000, 100000, 2000000]; first.mock.config.defaultBetLevel = 100000;
    const h = await ui(first.mock); assert.ok(h.state.pending); assert.equal(h.state.bet, 500000);
    h.state.instant = true; await spin(h); assert.equal(h.state.bet, 100000); assert.equal(first.mock.charges, 1);
  });
  await check("Offline recovery authentication preserves UI intent until reconnect", async () => {
    const mock = new RgsMock(), h = await ui(mock); h.state.instant = true;
    mock.failNext("/wallet/end-round", "network-before"); await spin(h); const requestID = h.state.pending.request_id;
    mock.failNext("/wallet/authenticate", "expired"); await spin(h);
    assert.equal(h.state.online, false); assert.equal(h.state.pending.request_id, requestID); assert.equal(h.ids["reconnect-button"].hidden, false);
    await h.app.init(); assert.ok(h.state.pending); h.state.instant = true; await spin(h);
    assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1); assert.equal(h.state.history.length, 1);
  });
  const passed = checks.every(c => c.passed), out = process.env.PG_QA_OUT_DIR || __dirname;
  fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(path.join(out, "rgs_recovery_results.json"), JSON.stringify({ passed, total: checks.length, checks }, null, 2));
  console.log(JSON.stringify({ passed, total: checks.length, failed: checks.filter(c => !c.passed).length })); if (!passed) process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
