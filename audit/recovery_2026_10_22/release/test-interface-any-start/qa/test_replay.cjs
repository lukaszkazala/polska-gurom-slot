"use strict";
// Real application and exported outcomes; virtual timers exercise every bonus spin.
const assert = require("node:assert/strict"), fs = require("node:fs"), path = require("node:path");
const { harness } = require("./test_autoplay.cjs");
const { RgsMock, fixtures, clone } = require("./rgs_mock.cjs");
const checks = [];
const liveHref = "http://127.0.0.1:8800/?sessionID=local-test-session&rgs_url=127.0.0.1%3A8800&demo=true&lang=pl";
const replayHref = "https://game.test/?replay=true&rgs_url=replays.test&game=00000000-0000-4000-8000-000000000001&version=0.5.0-any-start&mode=base&event=123&amount=500000&currency=USD&lang=pl";
async function check(name, work) {
  try { await work(); checks.push({ name, passed: true }); console.log("PASS " + name); }
  catch (error) { checks.push({ name, passed: false, error: error.stack }); console.error("FAIL " + name + ": " + error.stack); }
}
async function spin(h) { const work = h.app.spin(); await h.finished(); await work; }
function protectedState(h) {
  return JSON.stringify({ balance: h.state.balance, stats: h.state.stats, history: h.state.history, config: h.state.config,
    bet: h.state.bet, auto: h.state.auto, autoTotal: h.state.autoTotal, autoCompleted: h.state.autoCompleted,
    autoStatus: h.state.autoStatus, pending: h.state.pending, pendingAutoplay: h.state.pendingAutoplay,
    presentation: h.state.presentation, storage: [...h.storage], preferences: [...h.preferences], transportCalls: h.transportCalls,
    remote: h.state.rgs ? { pending: h.state.rgs.pending, stats: h.state.rgs.stats,
      balance: h.state.rgs.balance, lastBetID: h.state.rgs.lastBetID, lastRound: h.state.rgs.lastRound } : null });
}
function expectedMoney(h, amount) {
  const locales = { pl: "pl-PL", en: "en-GB", de: "de-DE" };
  return new Intl.NumberFormat(locales[h.state.lang], { style: "currency", currency: h.state.config.currency || "PLN",
    ...(h.state.config.amount_scale === 1000000 ? { currencyDisplay: "code" } : {}) })
    .format(amount / (h.state.config.amount_scale || 100));
}
async function playReplay(h, record, trigger = () => h.app.replayRound(record)) {
  const before = protectedState(h), original = JSON.stringify(record), progress = new Set();
  const work = trigger();
  assert.equal(h.state.replaying, true, "saved playback begins synchronously");
  assert.equal(h.state.busy, true); assert.equal(h.state.instant, false); assert.equal(h.state.skipScreens, false);
  assert.equal(h.state.currentBet, record.bet_cents, "Replay uses the recorded stake");
  assert.equal(h.ids["replay-status"].hidden, false, "Replay is identified throughout its presentation");
  for (const id of ["spin-button", "auto-button", "bet-increase", "bet-decrease", "reset-button", "replay-button", "details-replay-button"])
    assert.equal(h.ids[id].disabled, true, id + " is blocked during playback");
  for (let steps = 0; steps < 30000 && h.state.busy; steps++) {
    progress.add(h.ids["bonus-progress"].textContent);
    assert.ok(await h.clock.step(), "Playback must have an animation continuation");
    assert.ok(h.state.presentedUnits <= record.round.payout_units, "The win meter never exceeds the credited round payout");
  }
  await work;
  assert.equal(h.state.busy, false); assert.equal(h.state.replaying, false);
  assert.equal(protectedState(h), before, "playback cannot alter the wallet, ledger, history or stored preferences");
  assert.equal(JSON.stringify(record), original, "the saved outcome is immutable");
  assert.equal(h.ids["meter-win"].textContent, expectedMoney(h, record.win_cents));
  const spins = record.round.free_spins;
  for (let i = 1; i <= spins.length; i++) assert.ok(progress.has(`${i} / ${spins.length}`) || h.ids["bonus-progress"].textContent === `${i} / ${spins.length}`, `free spin ${i} was presented`);
  const last = (spins.at(-1) || record.round.base).cascades.at(-1).evaluation_grid;
  assert.equal(JSON.stringify(h.state.grid), JSON.stringify(last), "the recorded final grid is displayed");
  assert.equal(h.errors.length, 0);
}
async function saved(kind, rgs = false) {
  const mock = rgs ? new RgsMock({ kind }) : null;
  const h = harness(rgs ? { rgs: true, boot: true, href: liveHref, fetch: mock.fetch } : { roundFactory: () => fixtures.rounds[kind] });
  if (rgs) await h.app.init();
  h.state.instant = true; await spin(h);
  assert.equal(h.state.history.length, 1);
  h.state.speed = "turbo"; h.state.skipScreens = true;
  h.state.bet = h.state.config.bet_options_cents.at(-1);
  return { h, mock, record: h.state.history[0] };
}
function standalone(kind, overrides = {}) {
  const calls = [], round = clone(fixtures.rounds[kind]);
  const fetch = async (url, init = {}) => {
    calls.push({ url, init });
    const response = body => ({ ok: true, status: 200, json: async () => clone(body) });
    if (url === "game-config.json") return response(fixtures.config);
    if (url === "assets/symbols.json") return response({});
    assert.match(String(url), /^https:\/\/replays\.test\/bet\/replay\//);
    assert.ok(!init.method || init.method === "GET", "Replay only reads its saved event");
    if (overrides.fail) throw new TypeError("Synthetic replay unavailable");
    const body = { payoutMultiplier: round.payout_units / fixtures.config.payout_scale,
      costMultiplier: 1, state: [{ index: 0, type: "roundResult", data: round }] };
    return response(overrides.change ? overrides.change(body) : body);
  };
  return { calls, h: harness({ rgs: true, boot: true, rgsOnly: true, href: overrides.href || replayHref, fetch }) };
}
async function main() {
  for (const rgs of [false, true]) for (const kind of ["loss", "middle", "bonus8", "bonus12", "cap"])
    await check(`${rgs ? "RGS" : "Local"} saved ${kind}: exact replay twice, no new wallet operation`, async () => {
      const { h, mock, record } = await saved(kind, rgs);
      const count = mock ? mock.calls.length : h.requests.length;
      await playReplay(h, record); assert.equal(h.state.instant, true); assert.equal(h.state.skipScreens, true);
      await playReplay(h, record);
      assert.equal(mock ? mock.calls.length : h.requests.length, count, "No replay transport, checkpoint or settlement");
      if (kind === "cap") {
        assert.equal(record.round.payout_units, 500000); assert.ok(record.round.cap_reduction_units > 0);
        assert.match(h.ids["win-detail"].textContent + h.ids["round-note"].textContent, /5000/);
      }
    });
  await check("Saved complete bonus remains playable offline", async () => {
    const { h, mock, record } = await saved("bonus12", true); h.state.online = false; h.state.connectionLost = true;
    const count = mock.calls.length; await playReplay(h, record); assert.equal(mock.calls.length, count); assert.equal(h.state.online, false);
  });
  for (const blocked of ["pending", "auto", "busy", "walletReading"]) await check("Saved replay is refused while " + blocked, async () => {
    const { h, mock, record } = await saved("bonus8", true);
    h.state[blocked] = blocked === "pending" ? { request_id: "unresolved-paid-round" } : blocked === "auto" ? 3 : true;
    const before = protectedState(h), count = mock.calls.length;
    await h.app.replayRound(record);
    assert.notEqual(h.state.replaying, true); assert.equal(protectedState(h), before); assert.equal(mock.calls.length, count);
  });
  await check("Replay ignores unrelated completed recovery progress", async () => {
    const { h, record } = await saved("bonus12");
    h.state.presentation = { round_id: record.round_id, baseComplete: true, freeCompleted: 12 };
    await playReplay(h, record);
  });
  await check("Main and details replay buttons use the selected saved round", async () => {
    const { h, record } = await saved("middle"); h.app.controls();
    await playReplay(h, record, () => h.ids["replay-button"].click());
    h.ids["details-button"].click(); assert.ok("open" in h.ids["details-dialog"].attrs);
    await playReplay(h, record, () => h.ids["details-replay-button"].click());
    assert.ok(!("open" in h.ids["details-dialog"].attrs));
  });
  for (const corrupt of [
    record => record.math_version = "other-version",
    record => record.win_cents++,
    record => record.round.free_spin_credits[0]++,
    record => record.round.free_spins[0].evaluation_grid[0][0] = "INVALID"
  ]) await check("Malformed saved result is blocked before presentation " + checks.length, async () => {
    const { h, mock, record } = await saved("bonus8", true), bad = clone(record); corrupt(bad);
    const before = protectedState(h), grid = JSON.stringify(h.state.grid), count = mock.calls.length;
    try { await h.app.replayRound(bad); } catch { /* Rejection is permitted; side effects are not. */ }
    assert.notEqual(h.state.replaying, true); assert.equal(h.state.busy, false);
    assert.equal(protectedState(h), before); assert.equal(JSON.stringify(h.state.grid), grid); assert.equal(mock.calls.length, count);
  });
  await check("Settled RGS history survives reload without creating a new round", async () => {
    const { h, mock, record } = await saved("bonus12", true);
    const next = harness({ rgs: true, boot: true, href: liveHref, fetch: mock.fetch, sessionStorage: h.storage, localStorage: h.preferences });
    await next.app.init(); assert.equal(next.state.history.length, 1); assert.equal(next.state.history[0].round_id, record.round_id);
    const calls = mock.calls.length; next.state.speed = "turbo"; await playReplay(next, next.state.history[0]);
    assert.equal(mock.calls.length, calls); assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1);
    for (const [key, value] of h.storage) if (key.startsWith("pg-replays-")) assert.ok(!value.includes("local-test-session"));
  });
  for (const kind of ["loss", "middle", "bonus8", "bonus12", "cap"]) await check("Standalone " + kind + " replay launches without a session or wallet", async () => {
    const { h, calls } = standalone(kind); await h.app.init();
    assert.equal(h.state.online, true, h.ids["win-detail"].textContent); assert.equal(h.state.replayMode, true); assert.ok(h.state.replayResult);
    assert.equal(h.state.busy, false, "Replay waits for the user's first Play click"); assert.equal(h.state.history.length, 0);
    const count = calls.length; h.state.speed = "turbo";
    await playReplay(h, h.state.replayResult, () => h.app.spin());
    await playReplay(h, h.state.replayResult, () => h.app.spin());
    assert.equal(calls.length, count); assert.equal(calls.filter(call => /\/bet\/replay\//.test(call.url)).length, 1);
    assert.ok(calls.every(call => !/\/wallet\/|\/api\/|\/bet\/event/.test(call.url)));
    assert.equal(h.state.history.length, 0);
    for (const id of ["auto-button", "bet-increase", "bet-decrease", "reset-button"]) assert.equal(h.ids[id].disabled, true);
  });
  for (const problem of [
    { fail: true }, { change: body => ({ ...body, payoutMultiplier: body.payoutMultiplier + 1 }) },
    { change: body => ({ ...body, costMultiplier: 0 }) },
    { change: body => ({ ...body, state: [] }) },
    { href: replayHref.replace("&event=123", "") },
    { href: replayHref.replace("mode=base", "mode=other") }
  ]) await check("Failed or malformed standalone launch stays blocked without demo fallback " + checks.length, async () => {
    const { h, calls } = standalone("bonus12", problem); await h.app.init();
    assert.equal(h.state.online, false); assert.equal(h.ids["spin-button"].disabled, true); assert.equal(h.state.history.length, 0);
    assert.ok(calls.every(call => !/\/wallet\/|\/api\/|\/bet\/event/.test(call.url)));
  });
  await check("A replay link ignores a supplied session token and never authenticates it", async () => {
    const { h, calls } = standalone("middle", { href: replayHref + "&sessionID=do-not-use" });
    await h.app.init(); assert.equal(h.state.online, true); assert.equal(h.state.replayMode, true);
    h.state.speed = "turbo"; await playReplay(h, h.state.replayResult, () => h.app.spin());
    assert.ok(calls.every(call => !JSON.stringify(call).includes("do-not-use")));
    assert.ok([...h.storage].every(([key, value]) => !key.includes("do-not-use") && !value.includes("do-not-use")));
  });
  const passed = checks.every(check => check.passed), out = process.env.PG_QA_OUT_DIR || __dirname;
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, "replay_results.json"), JSON.stringify({ passed, total: checks.length, checks }, null, 2) + "\n");
  console.log(JSON.stringify({ passed, total: checks.length, failed: checks.filter(check => !check.passed).length }));
  if (!passed) process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
