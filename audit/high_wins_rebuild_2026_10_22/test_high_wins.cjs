"use strict";
// Current weighted-bank outcomes through the actual UI and RGS client code.
// Minimal DOM and virtual timers; this is not visual/browser/platform QA.
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
const ROOT = path.resolve(__dirname, "../../test-interface-any-start");
const { harness, source } = require(path.join(ROOT, "qa/test_autoplay.cjs"));
const { RgsMock, fixtures, clone } = require(path.join(ROOT, "qa/rgs_mock.cjs"));
const OUT = process.env.PG_QA_OUT_DIR || __dirname;
const checks = [];
const caps = [8, 10, 12].map(fs => `bonus_cap${fs}`).filter(name => fixtures.rounds[name]);
assert.ok(caps.length, "Regenerate fixtures from the rebuilt bank: at least one actual weighted FS cap is required");

function observe(h, id) {
  const values = [], element = h.ids[id];
  const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(element), "textContent");
  Object.defineProperty(element, "textContent", {
    get() { return descriptor.get.call(this); },
    set(value) { values.push(String(value)); descriptor.set.call(this, value); }
  });
  return values;
}
async function check(name, work) {
  try { checks.push({ name, passed: true, ...await work() }); console.log("PASS " + name); }
  catch (error) { checks.push({ name, passed: false, error: error.stack }); console.error("FAIL " + name + ": " + error.message); }
}
async function spin(h) { const work = h.app.spin(); await h.finished(); await work; }
function summary(h, round) {
  const selected = h.state.selected || h.state.replayResult, amount = h.app.money(selected.win_cents);
  assert.equal(selected.round.payout_units, 500000);
  assert.equal(h.ids["bonus-progress"].textContent, `${round.free_spins.length} / ${round.base.free_spins_awarded}`);
  assert.equal(h.ids["meter-win"].textContent, amount);
  assert.ok(h.ids["bonus-label"].textContent.includes("5000×"));
  for (const id of ["round-note", "win-detail"]) {
    assert.ok(h.ids[id].textContent.includes("5000×"), id + " states cap");
    assert.ok(h.ids[id].textContent.includes(amount), id + " states actual granted payout");
    assert.doesNotMatch(h.ids[id].textContent, /\{(?:amount|remaining)\}/);
  }
  const unused = round.base.free_spins_awarded - round.free_spins.length;
  if (unused) assert.ok(h.ids["round-note"].textContent.includes(String(unused)), "original awarded but unplayed FS remain explicit");
  assert.equal(h.state.pending, null);
  assert.equal(h.errors.length, 0);
}

async function main() {
  for (const name of caps) {
    const round = fixtures.rounds[name];
    assert.ok(round.base.payout_units < 500000 && round.free_spins.length > 0);
    for (const lang of ["pl", "en", "de"]) for (const mode of ["animated", "instant", "skip-screens"]) {
      await check(`${name}, ${lang}, ${mode}: actual FS cap displays credited payout and original award`, async () => {
        const h = harness({ roundFactory: () => round, speed: "turbo", instant: mode === "instant" });
        h.state.lang = lang; h.state.skipScreens = mode === "skip-screens";
        const progress = observe(h, "bonus-progress");
        await spin(h); summary(h, round);
        assert.equal(h.ledger.size, 1); assert.equal(h.state.history.length, 1);
        assert.equal(h.state.balance, h.wallet().balance_cents);
        if (mode === "animated") for (let i = 1; i <= round.free_spins.length; i++) {
          assert.ok(progress.includes(`${i} / ${round.base.free_spins_awarded}`), `played FS ${i} is presented`);
        }
        for (let i = round.free_spins.length + 1; i <= round.base.free_spins_awarded; i++) {
          assert.ok(!progress.includes(`${i} / ${round.base.free_spins_awarded}`), "unplayed FS never appears");
        }
        return { book_id: fixtures.book_ids[name], played: round.free_spins.length, awarded: round.base.free_spins_awarded };
      });
    }
    await check(`${name}: saved replay preserves original paid stake and wallet`, async () => {
      const h = harness({ roundFactory: () => round, speed: "turbo", instant: true });
      await spin(h);
      const record = h.state.history[0];
      h.state.bet = h.state.config.bet_options_cents.at(-1);
      const before = JSON.stringify([h.state.balance, h.state.stats, h.state.history, h.requests]);
      const work = h.app.replayRound(record); await h.finished(); await work;
      summary(h, round);
      assert.equal(JSON.stringify([h.state.balance, h.state.stats, h.state.history, h.requests]), before);
      assert.equal(h.state.selected.bet_cents, record.bet_cents);
    });
    await check(`${name}: RGS reload after paid base resumes bonus with one charge and one settlement`, async () => {
      const mock = new RgsMock({ kind: name });
      const href = "http://127.0.0.1:8800/?sessionID=local-test-session&rgs_url=127.0.0.1%3A8800&demo=true&lang=pl";
      const first = harness({ rgs: true, boot: true, href, fetch: mock.fetch });
      await first.app.init(); first.state.speed = "turbo";
      first.app.spin();
      await first.clock.until(() => mock.round?.event && JSON.parse(mock.round.event).baseComplete, "paid base checkpoint acknowledged");
      assert.equal(mock.charges, 1); assert.equal(mock.settlements, 0);
      const resumed = harness({ rgs: true, boot: true, href, fetch: mock.fetch, sessionStorage: first.storage });
      const progress = observe(resumed, "bonus-progress");
      await resumed.app.init();
      assert.equal(resumed.state.presentation.baseComplete, true);
      assert.equal(resumed.state.presentation.freeCompleted, 0);
      resumed.state.speed = "turbo"; await spin(resumed);
      summary(resumed, round);
      assert.ok(progress.includes(`0 / ${round.base.free_spins_awarded}`));
      assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1);
      assert.equal(mock.calls.filter(call => call.path === "/wallet/play").length, 1);
      assert.equal(resumed.state.balance, mock.balance);
    });
    await check(`${name}: public replay uses current ${fixtures.config.math_version} version without wallet requests`, async () => {
      const calls = [], version = encodeURIComponent(fixtures.config.math_version);
      const href = `https://game.test/?replay=true&rgs_url=replays.test&game=00000000-0000-4000-8000-000000000001&version=${version}&mode=base&event=123&amount=500000&currency=USD&lang=pl`;
      const fetch = async (url, init = {}) => {
        calls.push({ url, init });
        const response = body => ({ ok: true, status: 200, json: async () => clone(body) });
        if (url === "game-config.json") return response(fixtures.config);
        if (url === "assets/symbols.json") return response({});
        assert.ok(String(url).includes(`/bet/replay/00000000-0000-4000-8000-000000000001/${version}/base/123`));
        assert.ok(!init.method || init.method === "GET");
        return response({ payoutMultiplier: 5000, costMultiplier: 1,
          state: [{ index: 0, type: "roundResult", data: round }] });
      };
      const h = harness({ rgs: true, boot: true, rgsOnly: true, href, fetch });
      await h.app.init();
      assert.equal(h.state.online, true, h.ids["win-detail"].textContent);
      assert.equal(h.state.replayMode, true);
      const before = JSON.stringify([h.state.balance, h.state.stats, h.state.history, [...h.storage]]);
      const callCount = calls.length; h.state.speed = "turbo";
      await spin(h); summary(h, round);
      await spin(h); summary(h, round);
      assert.equal(calls.length, callCount, "repeated replay uses immutable loaded event");
      assert.equal(JSON.stringify([h.state.balance, h.state.stats, h.state.history, [...h.storage]]), before);
      assert.ok(calls.every(call => !/\/wallet\/|\/api\/|\/bet\/event/.test(call.url)));
      return { replay_version: fixtures.config.math_version, book_id: fixtures.book_ids[name] };
    });
  }
  const report = { math_version: fixtures.config.math_version,
    method: "Actual current weighted FS-cap fixtures through app.js and the RGS contract double, using minimal DOM and virtual time; no visual or live-platform claim.",
    source_sha256: crypto.createHash("sha256").update(source).digest("hex"),
    actual_book_ids: Object.fromEntries(caps.map(name => [name, fixtures.book_ids[name]])),
    tests_run: checks.length, passed: checks.filter(check => check.passed).length, checks };
  report.status = report.passed === report.tests_run ? "pass" : "fail";
  fs.mkdirSync(OUT, { recursive: true });
  fs.writeFileSync(path.join(OUT, "high_win_frontend_regressions.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(`${report.passed}/${report.tests_run} actual high-win UI/RGS checks passed`);
  if (report.status !== "pass") process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
