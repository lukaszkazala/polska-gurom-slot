"use strict";
// Real application, engine-created boundary cases, minimal DOM and virtual time.
// Requires Python for the authoritative synthetic fixtures; no browser/live-platform claim.
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
const { spawnSync } = require("node:child_process");
const { harness, source } = require("./test_autoplay.cjs");
const { RgsMock, fixtures, clone } = require("./rgs_mock.cjs");
const ROOT = path.resolve(__dirname, "..");
const OUT = path.resolve(process.env.PG_QA_OUT_DIR || path.join(ROOT, "../audit/cap_messages_2026_10_22"));
const checks = [];

// Scripted refill symbols feed the real engine. These cases test presentation;
// their frequency/reachability in the published weighted book is not asserted.
const generated = spawnSync(process.env.PYTHON || "python", ["-B", "-c", `
from dataclasses import asdict
import json
from polska_gurom.game import evaluate_paid_spin, evaluate_free_spin
from polska_gurom.config import MAX_WIN_UNITS
with open('qa/regression_fixtures.json', encoding='utf-8') as handle:
    fixtures = json.load(handle)
class Refill:
    def __init__(self, symbols=(), fallback='P4'):
        self.symbols = iter(symbols)
        self.fallback = fallback
    def choice(self, population):
        value = next(self.symbols, self.fallback)
        assert value in population
        return value
    def random(self):
        return 1.0
def filled(symbol):
    return [[symbol] * 5 for _ in range(3)]
def round_data(base, spins):
    credits = [spin['payout_units'] for spin in spins]
    raw = base['raw_payout_units'] + sum(spin['raw_payout_units'] for spin in spins)
    paid = base['payout_units'] + sum(credits)
    return dict(base=base, free_spins=spins, free_spin_credits=credits,
                raw_payout_units=raw, payout_units=paid,
                bonus_payout_units=sum(credits), cap_reduction_units=raw-paid)
base = fixtures['rounds']['bonus8']['base']
loss = fixtures['rounds']['loss']['base']['grid']
loss_refill = [loss[row][col] for col in range(5) for row in range(3)]
first = asdict(evaluate_free_spin(filled('P4'), Refill(loss_refill), 0,
    payout_limit_units=MAX_WIN_UNITS-base['payout_units']))
second = asdict(evaluate_free_spin(filled('P4'), Refill(), 0,
    payout_limit_units=MAX_WIN_UNITS-base['payout_units']-first['payout_units']))
bonus_cap = round_data(base, [first, second])
empty_free = asdict(evaluate_free_spin(loss, Refill(), 0))
last_free_cap = round_data(base, [empty_free] * 6 + [first, second])
trigger = filled('P4')
trigger[0][:3] = ['SCATTER'] * 3
base_cap = round_data(asdict(evaluate_paid_spin(trigger, Refill())), [])
exact = asdict(evaluate_paid_spin(filled('P3'), Refill(['P3']*(11*15)+['L1']*(5*15))))
exact_cap = round_data(exact, [])
assert bonus_cap['payout_units'] == base_cap['payout_units'] == exact_cap['payout_units'] == MAX_WIN_UNITS
assert len(bonus_cap['free_spins']) == 2 and bonus_cap['base']['free_spins_awarded'] == 8
assert len(last_free_cap['free_spins']) == last_free_cap['base']['free_spins_awarded'] == 8
assert last_free_cap['payout_units'] == MAX_WIN_UNITS
assert base_cap['base']['free_spins_awarded'] == 8
assert exact_cap['cap_reduction_units'] == 0
print(json.dumps(dict(bonus_cap=bonus_cap, base_cap=base_cap, exact_cap=exact_cap, last_free_cap=last_free_cap)))
`], { cwd: ROOT, encoding: "utf8", env: { ...process.env, PYTHONPATH: path.join(ROOT, "engine") } });
assert.equal(generated.status, 0, generated.stderr || generated.error?.message || generated.stdout);
const synthetic = JSON.parse(generated.stdout);
fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, "bonus_cap_fixture.json"), JSON.stringify({ synthetic: true,
  purpose: "Presentation boundary case produced by the current authoritative engine; not a weighted-bank outcome.",
  math_version: fixtures.config.math_version, round: synthetic.bonus_cap }, null, 2) + "\n");

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
function summary(h, result) {
  const amount = h.app.money(result.win_cents);
  assert.equal(h.ids["round-note"].hidden, false);
  for (const id of ["round-note", "win-detail"]) {
    assert.ok(h.ids[id].textContent.includes("5000×"), id + " states the limit");
    assert.ok(h.ids[id].textContent.includes(amount), id + " states the granted payout " + amount);
    assert.ok(!h.ids[id].textContent.includes("{amount}"), id + " has no unresolved amount placeholder");
  }
  assert.equal(h.ids["meter-win"].textContent, amount);
}
function bonusSummary(h, round) {
  const awarded = round.base.free_spins_awarded, played = round.free_spins.length;
  assert.equal(h.ids["bonus-progress"].textContent, `${played} / ${awarded}`);
  assert.ok(h.ids["bonus-label"].textContent.includes("5000×"), "bonus end states its cap reason");
  assert.ok(h.ids["round-note"].textContent.includes(String(awarded - played)), "unused free spins are explicit");
  assert.ok(!h.ids["round-note"].textContent.includes("{remaining}"));
}
async function local(round, lang, mode) {
  const h = harness({ roundFactory: () => round, speed: "turbo", instant: mode === "instant" });
  h.state.lang = lang; h.state.skipScreens = mode === "skip-screens";
  const progress = observe(h, "bonus-progress"), titles = observe(h, "bonus-announcement-title"), details = observe(h, "bonus-announcement-detail");
  await spin(h);
  assert.equal(h.state.pending, null, "the result passed validation and completed");
  assert.equal(h.errors.length, 0);
  assert.equal(h.ledger.size, 1); assert.equal(h.state.history.length, 1);
  assert.equal(h.state.balance, h.wallet().balance_cents);
  return { h, progress, titles, details };
}
async function main() {
  for (const lang of ["pl", "en", "de"]) for (const mode of ["animated", "instant", "skip-screens"]) {
    await check(`${lang} ${mode}: capped base reports its granted payout`, async () => {
      const { h } = await local(fixtures.rounds.cap, lang, mode);
      summary(h, h.state.selected);
      await h.clock.drain(5000); summary(h, h.state.selected);
    });
    await check(`${lang} ${mode}: bonus ends at 2/8 and explains the six unused spins`, async () => {
      const { h, progress, titles, details } = await local(synthetic.bonus_cap, lang, mode);
      summary(h, h.state.selected); bonusSummary(h, synthetic.bonus_cap);
      if (mode === "animated") {
        assert.ok(progress.includes("1 / 8")); assert.ok(progress.includes("2 / 8"));
        assert.ok(titles.some(title => title.includes("8")), "entry uses all awarded spins");
        assert.ok(titles.at(-1).includes("5000×"), "end announcement names the cap");
        assert.ok(details.at(-1).includes("5000×"));
      }
      assert.ok(!progress.includes("2 / 2"), "truncation never changes the original award");
    });
    await check(`${lang} ${mode}: base reaches cap before awarded bonus starts (0/8)`, async () => {
      const { h, progress, titles } = await local(synthetic.base_cap, lang, mode);
      summary(h, h.state.selected); bonusSummary(h, synthetic.base_cap);
      assert.ok(!progress.some(value => /^1 \/ /.test(value)), "no unused free spin is presented");
      assert.ok(!titles.some(title => /8.*(DARMOWE|FREE|FREISPIELE)/i.test(title)), "bonus entry is not announced");
    });
    await check(`${lang} ${mode}: exact 5000x with no reduction still reports the limit`, async () => {
      const { h } = await local(synthetic.exact_cap, lang, mode);
      assert.equal(h.state.selected.round.cap_reduction_units, 0); summary(h, h.state.selected);
    });
  }
  for (const lang of ["pl", "en", "de"]) await check(`${lang}: reduced line detail separates raw line win from granted stage payout`, async () => {
    const { h } = await local(fixtures.rounds.cap, lang, "animated");
    h.ids["win-lines"].children[0].click();
    const frame = fixtures.rounds.cap.base.cascades.at(-1);
    const stage = h.app.money(h.state.selected.bet_cents * frame.payout_units / fixtures.config.payout_scale);
    assert.match(h.ids["win-detail"].textContent, /przed limitem|before.*cap|vor.*Limit/i);
    assert.ok(h.ids["win-detail"].textContent.includes(stage), "detail includes credited stage " + stage);
    assert.ok(h.ids["round-note"].textContent.includes(h.app.money(h.state.selected.win_cents)));
  });
  for (const lang of ["pl", "en", "de"]) await check(`${lang}: cap on the final awarded free spin shows 8/8 without unused spins`, async () => {
    const { h, progress, titles, details } = await local(synthetic.last_free_cap, lang, "animated");
    summary(h, h.state.selected);
    assert.equal(h.ids["bonus-progress"].textContent, "8 / 8");
    for (let played = 1; played <= 8; played++) assert.ok(progress.includes(`${played} / 8`));
    assert.ok(h.ids["bonus-label"].textContent.includes("5000×"));
    assert.ok(titles.at(-1).includes("5000×"));
    assert.ok(details.at(-1).includes("5000×"));
    assert.doesNotMatch(h.ids["round-note"].textContent + details.at(-1), /niewykorzystan|unused|nicht gespielte|ungenutzt/i);
  });
  await check("Saved capped bonus replay uses its historic stake and leaves all wallet state unchanged", async () => {
    const { h } = await local(synthetic.bonus_cap, "pl", "instant"), record = h.state.history[0];
    h.state.bet = h.state.config.bet_options_cents.at(-1);
    assert.notEqual(h.state.bet, record.bet_cents);
    const before = JSON.stringify([h.state.balance, h.state.stats, h.state.history, h.requests]);
    const work = h.app.replayRound(record); await h.finished(); await work;
    summary(h, record); bonusSummary(h, record.round);
    assert.equal(JSON.stringify([h.state.balance, h.state.stats, h.state.history, h.requests]), before);
    assert.equal(h.errors.length, 0);
  });
  fixtures.rounds.synthetic_bonus_cap = synthetic.bonus_cap;
  await check("RGS reload resumes capped bonus at 1/8 then ends at 2/8 with one charge and settlement", async () => {
    const mock = new RgsMock({ kind: "synthetic_bonus_cap" });
    const href = "http://127.0.0.1:8800/?sessionID=local-test-session&rgs_url=127.0.0.1%3A8800&demo=true&lang=pl";
    const first = harness({ rgs: true, boot: true, href, fetch: mock.fetch });
    await first.app.init(); first.state.speed = "turbo";
    // Abandon this virtual browser once its completed first FS is acknowledged.
    first.app.spin();
    await first.clock.until(() => mock.round?.event && JSON.parse(mock.round.event).freeCompleted === 1, "first FS checkpoint acknowledged");
    assert.equal(mock.charges, 1); assert.equal(mock.settlements, 0);
    const resumed = harness({ rgs: true, boot: true, href, fetch: mock.fetch, sessionStorage: first.storage });
    const progress = observe(resumed, "bonus-progress");
    await resumed.app.init();
    assert.equal(resumed.state.presentation.freeCompleted, 1);
    assert.equal(resumed.ids["bonus-progress"].textContent, "1 / 8");
    resumed.state.speed = "turbo"; await spin(resumed);
    summary(resumed, resumed.state.selected); bonusSummary(resumed, synthetic.bonus_cap);
    assert.ok(progress.includes("1 / 8")); assert.ok(progress.includes("2 / 8"));
    assert.ok(!progress.includes("0 / 8"), "completed base and first FS are not replayed");
    assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1);
    assert.equal(mock.calls.filter(call => call.path === "/wallet/play").length, 1);
    assert.equal(resumed.state.balance, mock.balance); assert.equal(resumed.errors.length, 0);
    return { paid_rounds: mock.charges, settlements: mock.settlements, resumed_counter: progress };
  });
  for (const [lang, currency, amount] of [["pl", "USD", 1234567], ["en", "JPY", 500000], ["de", "KWD", 10000]]) {
    await check(`${lang} RGS ${currency}: cap amount uses authenticated currency and the paid stake`, async () => {
      const mock = new RgsMock({ kind: "synthetic_bonus_cap", currency });
      mock.config = { ...mock.config, minBet: amount, maxBet: amount, stepBet: 1, defaultBetLevel: amount, betLevels: [amount] };
      const href = `http://127.0.0.1:8800/?sessionID=local-test-session&rgs_url=127.0.0.1%3A8800&demo=true&lang=${lang}`;
      const h = harness({ rgs: true, boot: true, href, fetch: mock.fetch });
      await h.app.init(); assert.equal(h.state.online, true, h.ids["win-detail"].textContent); h.state.instant = true;
      await spin(h); summary(h, h.state.selected); bonusSummary(h, synthetic.bonus_cap);
      assert.ok(h.ids["round-note"].textContent.includes(currency));
      assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1);
      assert.equal(h.state.balance, mock.balance); assert.equal(h.errors.length, 0);
    });
  }
  delete fixtures.rounds.synthetic_bonus_cap;
  fs.mkdirSync(OUT, { recursive: true });
  const report = { generated_at: new Date().toISOString(), source_sha256: crypto.createHash("sha256").update(source).digest("hex"),
    method: "Actual app.js in a minimal DOM with virtual timers; real exported cap and synthetic boundary outcomes from the authoritative Python engine. No visual or live-platform coverage.",
    synthetic_cases: Object.fromEntries(Object.entries(synthetic).map(([name, round]) => [name, {
      payout_units: round.payout_units, cap_reduction_units: round.cap_reduction_units,
      awarded: round.base.free_spins_awarded, played: round.free_spins.length
    }])), tests_run: checks.length, passed: checks.filter(check => check.passed).length, checks };
  report.status = report.passed === report.tests_run ? "pass" : "fail";
  fs.writeFileSync(path.join(OUT, "cap_messages_results.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(`${report.passed}/${report.tests_run} cap message checks passed`);
  if (report.status !== "pass") process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
