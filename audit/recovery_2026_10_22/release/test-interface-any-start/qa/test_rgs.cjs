"use strict";
const assert = require("node:assert/strict"), vm = require("node:vm"), fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
const { RgsMock, fixtures, clone } = require("./rgs_mock.cjs");
const { harness } = require("./test_autoplay.cjs");
const context = { window: {}, URL, TextEncoder, AbortController, setTimeout, clearTimeout };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../web/rgs-client.js"), "utf8"), context);
const RGS = context.window.PG_RGS;
const href = "http://127.0.0.1:8800/?sessionID=local-test-session&rgs_url=127.0.0.1%3A8800&demo=true&lang=pl";
const checks = [];
async function check(name, work) {
  try { await work(); checks.push({ name, passed: true }); console.log("PASS " + name); }
  catch (error) { checks.push({ name, passed: false, error: error.stack }); console.error("FAIL " + name + ": " + error.stack); }
}
function client(mock = new RgsMock(), storage = new Map()) {
  const store = { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value) };
  return { mock, storage, app: new RGS.Client(RGS.launch(href), { fetch: mock.fetch, storage: store, crypto: crypto.webcrypto }) };
}
const request = () => ({ bet_cents: 500000, mode: "random", request_id: crypto.randomUUID() });
async function ui(mock, storage, preferences) {
  const h = harness({ rgs: true, boot: true, href, fetch: mock.fetch, sessionStorage: storage, localStorage: preferences });
  await h.app.init(); assert.equal(h.state.online, true, h.ids["win-detail"].textContent); return h;
}
async function spin(h) { const work = h.app.spin(); await h.finished(); await work; }
async function main() {
  await check("Ordinary local launch keeps demo and requires no RGS", () => assert.equal(RGS.launch("http://127.0.0.1:8765/"), null));
  for (const suffix of ["?sessionID=x", "?rgs_url=host.test", "?sessionID=x&rgs_url=https://host.test", "?sessionID=x&rgs_url=bad.test/path", "?sessionID=x&rgs_url=user@host.test", "?sessionID=x&rgs_url=host.test%23x", "?sessionID=x&rgs_url=host.test&replay=true", "?sessionID=x&rgs_url=host.test&social=true"]) {
    await check("Reject incomplete or unsupported launch " + suffix.replace("sessionID=x", "sessionID=…"), () => assert.throws(() => RGS.launch("https://game.test/" + suffix)));
  }
  await check("RGS host uses HTTPS; loopback HTTP only on the exact same host and port", () => {
    assert.equal(RGS.launch(href).origin, "http://127.0.0.1:8800");
    assert.equal(RGS.launch("http://127.0.0.1:8800/?sessionID=x&rgs_url=127.0.0.1:8801").origin, "https://127.0.0.1:8801");
    assert.equal(RGS.launch("https://game.test/?sessionID=x&rgs_url=rgs.test").origin, "https://rgs.test");
  });
  await check("Unsupported launch language falls back to English", () => assert.equal(RGS.launch(href.replace("lang=pl", "lang=xx")).lang, "en"));
  await check("Authenticate precedes wallet calls; configured levels/default/currency are authoritative", async () => {
    const h = client(); const boot = await h.app.boot(fixtures.config);
    assert.deepEqual([...boot.config.bet_options_cents], [10000, 100000, 500000, 2000000]);
    assert.equal(boot.config.default_bet_cents, 500000); assert.equal(boot.config.currency, "USD"); assert.equal(boot.config.amount_scale, 1000000);
    assert.equal(h.mock.calls[0].path, "/wallet/authenticate");
    assert.equal(h.mock.calls[0].init.credentials, "omit"); assert.equal(h.mock.calls[0].init.referrerPolicy, "no-referrer");
  });
  for (const change of [c => c.betLevels.push(12345), c => c.betLevels.push(500000), c => c.stepBet = 0, c => c.defaultBetLevel = 12345, c => c.betLevels = [], c => c.maxBet = Number.MAX_SAFE_INTEGER + 1]) await check("Invalid authenticated betting configuration blocks play " + checks.length, async () => {
    const h = client(); change(h.mock.config); await assert.rejects(h.app.boot(fixtures.config)); assert.equal(h.mock.charges, 0);
  });
  await check("Integer payout arithmetic remains exact above safe multiplication range", () => {
    assert.equal(RGS.payout(900000000000, 500000), 4500000000000000);
    assert.throws(() => RGS.payout(Number.MAX_SAFE_INTEGER, 500000));
  });
  for (const kind of Object.keys(fixtures.rounds)) await check("Real " + kind + " book: one debit, payout only at finish, no end for zero", async () => {
    const h = client(new RgsMock({ kind })); await h.app.boot(fixtures.config);
    const before = h.mock.balance, result = await h.app.play(request());
    assert.equal(h.mock.charges, 1); assert.equal(h.mock.settlements, 0); assert.equal(h.mock.balance, before - result.bet_cents);
    const wallet = await h.app.finish(result);
    assert.equal(wallet.balance_cents, before - result.bet_cents + result.win_cents);
    assert.equal(h.mock.settlements, result.win_cents > 0 ? 1 : 0); assert.equal(h.app.pending, null);
  });
  await check("Same result retry never issues a second play", async () => {
    const h = client(); await h.app.boot(fixtures.config); const req = request();
    const result = await h.app.play(req); assert.equal((await h.app.play(req)).round_id, result.round_id);
    assert.equal(h.mock.charges, 1); assert.equal(h.mock.calls.filter(c => c.path === "/wallet/play").length, 1);
  });
  for (const fault of ["lost-response", "bad-json"]) await check("Uncertain play " + fault + " recovers through authenticate without another debit", async () => {
    const h = client(); await h.app.boot(fixtures.config); const req = request();
    h.mock.failNext("/wallet/play", fault); await assert.rejects(h.app.play(req));
    const result = await h.app.play(req); await h.app.finish(result); assert.equal(h.mock.charges, 1); assert.equal(h.mock.settlements, 1);
  });
  await check("Uncertain request with no identifiable round remains blocked, including after reload", async () => {
    const h = client(new RgsMock({ nullClosed: true })); await h.app.boot(fixtures.config); const req = request();
    h.mock.failNext("/wallet/play", "network-before"); await assert.rejects(h.app.play(req));
    await assert.rejects(h.app.play(req), e => e.code === "rgs_recovery_required");
    const reloaded = client(h.mock, h.storage); await assert.rejects(reloaded.app.boot(fixtures.config));
    assert.equal(h.mock.charges, 0); assert.equal(h.mock.calls.filter(c => c.path === "/wallet/play").length, 1);
  });
  await check("Uncertain closed zero payout with no returned last round is never resent", async () => {
    const h = client(new RgsMock({ kind: "loss", nullClosed: true })); await h.app.boot(fixtures.config); const req = request();
    h.mock.failNext("/wallet/play", "lost-response"); await assert.rejects(h.app.play(req)); await assert.rejects(h.app.play(req));
    assert.equal(h.mock.charges, 1); assert.equal(h.mock.settlements, 0);
  });
  await check("Uncertain closed zero payout with identifiable last round can be recovered", async () => {
    const h = client(new RgsMock({ kind: "loss" })); await h.app.boot(fixtures.config); const req = request();
    h.mock.failNext("/wallet/play", "lost-response"); await assert.rejects(h.app.play(req));
    const result = await h.app.play(req); await h.app.finish(result); assert.equal(h.mock.charges, 1); assert.equal(h.mock.settlements, 0);
  });
  await check("Lost end-round response recovers settled balance without a second payout", async () => {
    const h = client(new RgsMock({ nullClosed: true })); await h.app.boot(fixtures.config); const req = request(), result = await h.app.play(req);
    h.mock.failNext("/wallet/end-round", "lost-response"); await assert.rejects(h.app.finish(result));
    const recovered = await h.app.play(req); await h.app.finish(recovered); assert.equal(h.mock.charges, 1); assert.equal(h.mock.settlements, 1);
  });
  await check("Fresh browser resumes active authenticated round without play", async () => {
    const mock = new RgsMock({ kind: "bonus12" }), first = client(mock); await first.app.boot(fixtures.config); await first.app.play(request());
    const next = client(mock), boot = await next.app.boot(fixtures.config);
    assert.equal(boot.pending.result.round.free_spins.length, 12); await next.app.finish(boot.pending.result); assert.equal(mock.charges, 1);
  });
  await check("A different active round cannot be ended by a stale client", async () => {
    const h = client(); await h.app.boot(fixtures.config); const result = await h.app.play(request());
    h.mock.round.betID = 12345; await assert.rejects(h.app.finish(result)); assert.equal(h.mock.settlements, 0);
  });
  for (const fault of ["insufficient", "expired", "invalid"]) await check("Explicit " + fault + " rejection makes no debit", async () => {
    const h = client(); await h.app.boot(fixtures.config); h.mock.failNext("/wallet/play", fault); await assert.rejects(h.app.play(request()));
    assert.equal(h.mock.charges, 0); assert.equal(h.app.pending, null);
  });
  for (const change of [d => d.round.amount++, d => d.round.mode = "BASE", d => d.round.payout++, d => d.round.state = [], d => d.round.active = "true", d => d.round.betID = null]) await check("Malformed or incompatible RGS result blocks settlement " + checks.length, async () => {
    const h = client(); await h.app.boot(fixtures.config); h.mock.failNext("/wallet/play", change); await assert.rejects(h.app.play(request()));
    assert.equal(h.mock.charges, 1); assert.equal(h.mock.settlements, 0); assert.ok(h.app.pending);
  });
  await check("Session token is absent from persisted recovery state and normalized result", async () => {
    const h = client(); await h.app.boot(fixtures.config); const result = await h.app.play(request());
    assert.ok(!JSON.stringify([...h.storage]).includes("local-test-session")); assert.ok(!JSON.stringify(result).includes("local-test-session"));
  });
  for (const kind of ["loss", "middle", "bonus12", "cap"]) await check("Actual app.js presents and settles RGS " + kind + " using real validation", async () => {
    const mock = new RgsMock({ kind }), h = await ui(mock); h.state.instant = true;
    assert.equal(h.state.bet, 500000); assert.equal(h.ids["test-mode-select"].disabled, true); assert.equal(h.ids["reset-button"].disabled, true);
    await spin(h); assert.equal(h.state.pending, null); assert.equal(h.state.balance, mock.balance); assert.equal(h.state.history.length, 1); assert.equal(mock.charges, 1);
    assert.equal(h.errors.length, 0); assert.match(h.ids["bet-value"].textContent, /0,50/);
  });
  await check("Actual UI keeps failed settlement pending and retries without play", async () => {
    const mock = new RgsMock(), h = await ui(mock); h.state.instant = true;
    mock.failNext("/wallet/end-round", "lost-response"); await spin(h); assert.ok(h.state.pending);
    await spin(h); assert.equal(h.state.pending, null); assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1); assert.equal(h.state.balance, mock.balance);
  });
  await check("Actual UI reload during 12 free spins resumes one paid round", async () => {
    const mock = new RgsMock({ kind: "bonus12" }), h = await ui(mock); h.state.speed = "turbo"; h.app.spin();
    await h.clock.until(() => h.state.presentation?.freeCompleted === 4, "four RGS free spins");
    const next = await ui(mock, h.storage); assert.equal(next.state.presentation.freeCompleted, 4); assert.equal(next.state.bet, 500000);
    next.state.instant = true; await spin(next); assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1); assert.equal(next.state.auto, 0);
  });
  await check("Actual UI never automatically resends an ambiguous autoplay bet", async () => {
    const mock = new RgsMock(), h = await ui(mock); h.state.instant = true;
    mock.failNext("/wallet/play", "network-before"); h.start(); await h.finished();
    assert.ok(h.state.pending); assert.equal(mock.calls.filter(c => c.path === "/wallet/play").length, 1); assert.equal(h.state.auto, 0);
  });
  await check("Minimum and maximum configured stakes can be played; out-of-list stake cannot", async () => {
    const h = client(new RgsMock({ kind: "loss" })); await h.app.boot(fixtures.config);
    for (const bet of [10000, 2000000]) { const req = { ...request(), bet_cents: bet }; await h.app.finish(await h.app.play(req)); }
    await assert.rejects(h.app.play({ ...request(), bet_cents: 12345 })); assert.equal(h.mock.charges, 2);
  });
  await check("Idle wallet polling reads platform balance", async () => {
    const mock = new RgsMock(), h = await ui(mock); mock.balance += 1000000;
    await h.clock.until(() => h.state.balance === mock.balance, "idle balance poll");
    assert.ok(mock.calls.some(c => c.path === "/wallet/balance")); assert.equal(mock.charges, 0);
  });
  await check("Delayed balance read cannot overwrite a newer play response", async () => {
    const h = client(); await h.app.boot(fixtures.config);
    let release; const original = h.app.fetch;
    h.app.fetch = async (url, init) => {
      const response = await original(url, init);
      if (url.endsWith("/wallet/balance")) await new Promise(resolve => { release = resolve; });
      return response;
    };
    const read = h.app.readWallet(); while (!release) await Promise.resolve();
    const result = await h.app.play(request()); release(); await read;
    assert.equal(h.app.balance, h.mock.balance); await h.app.finish(result);
  });
  await check("Chosen platform stake survives reload without replacing the local-demo preference", async () => {
    const mock = new RgsMock(), preferences = new Map([["pg-bet-cents", "1000"]]);
    const h = await ui(mock, undefined, preferences); h.ids["bet-increase"].click();
    assert.equal(h.state.bet, 2000000);
    const next = await ui(mock, h.storage, preferences); assert.equal(next.state.bet, 2000000);
    assert.equal(preferences.get("pg-bet-cents"), "1000");
  });
  await check("Full bonus finishes presentation before end-round is called", async () => {
    const mock = new RgsMock({ kind: "bonus12" }), original = mock.fetch; let h;
    mock.fetch = async (url, init) => {
      if (url.endsWith("/wallet/end-round")) { assert.equal(h.state.presentation.baseComplete, true); assert.equal(h.state.presentation.freeCompleted, 12); }
      return original(url, init);
    };
    h = await ui(mock); h.state.speed = "turbo"; await spin(h); assert.equal(mock.settlements, 1);
  });
  for (const currency of ["JPY", "KWD"]) await check("Currency " + currency + " uses the platform denomination", async () => {
    const mock = new RgsMock({ currency }), h = await ui(mock);
    assert.equal(h.state.config.currency, currency);
    if (currency === "KWD") assert.match(h.ids["bet-value"].textContent, /0,500/);
    else assert.ok(!h.ids["bet-value"].textContent.includes("0,50"));
  });
  await check("Broken cascade response never reaches end-round", async () => {
    const mock = new RgsMock(), h = await ui(mock); h.state.instant = true;
    mock.failNext("/wallet/play", data => { data.round.state[0].data.base.cascades[0].removed_positions.push([99,99]); return data; });
    await spin(h); assert.ok(h.state.pending); assert.equal(mock.charges, 1); assert.equal(mock.settlements, 0); assert.equal(h.state.history.length, 0);
  });
  await check("RGS-only build without launch parameters makes no local API calls", async () => {
    const calls = [], h = harness({ boot: true, rgs: true, rgsOnly: true, fetch: async url => { calls.push(url); throw new Error("unexpected request"); } });
    await h.app.init(); assert.equal(h.state.online, false); assert.equal(h.ids["spin-button"].disabled, true); assert.deepEqual(calls, []);
  });
  await check("Invalid RGS launch fails closed without local-demo fallback", async () => {
    const calls = [], h = harness({ boot: true, rgs: true, href: "https://game.test/?sessionID=x", fetch: async url => { calls.push(url); throw new Error("unexpected request"); } });
    await h.app.init(); assert.equal(h.state.online, false); assert.deepEqual(calls, []); assert.ok(!h.ids["win-detail"].textContent.includes("START.cmd"));
  });
  const passed = checks.every(c => c.passed), out = process.env.PG_QA_OUT_DIR || __dirname;
  fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(path.join(out, "rgs_results.json"), JSON.stringify({ passed, total: checks.length, checks }, null, 2));
  console.log(JSON.stringify({ passed, total: checks.length, failed: checks.filter(c => !c.passed).length }));
  if (!passed) process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
