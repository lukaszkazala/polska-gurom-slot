"use strict";
// Real legacy app, current exported books, minimal DOM and virtual time.
// These checks cover presentation logic; they do not claim browser rendering.
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
const { spawnSync } = require("node:child_process");
const ROOT = path.resolve(__dirname, "../..");
const { harness, config, source } = require(path.join(ROOT, "test-interface/qa/test_autoplay.cjs"));
const fixtures = JSON.parse(fs.readFileSync(path.join(ROOT, "test-interface-any-start/qa/regression_fixtures.json"), "utf8"));
assert.equal(config.math_version, fixtures.config.math_version);
const locale = { pl: "pl-PL", en: "en-GB", de: "de-DE" };
const checks = [];

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
  try { checks.push({ name, passed: true, ...await work() }); }
  catch (error) { checks.push({ name, passed: false, error: error.stack }); console.error("FAIL " + name + ": " + error.message); }
}
const money = (h, cents) => new Intl.NumberFormat(locale[h.state.lang], { style: "currency", currency: "PLN" }).format(cents / 100);
async function run(round, lang, mode) {
  const h = harness({ roundFactory: () => round, speed: "turbo", instant: mode === "instant" });
  h.state.lang = lang; h.state.skipScreens = mode === "skip-screens";
  h.progress = observe(h, "bonus-progress"); h.titles = observe(h, "bonus-announcement-title");
  const work = h.app.spin(); await h.finished(); await work;
  assert.equal(h.errors.length, 0); assert.equal(h.state.pending, null);
  assert.equal(h.requests.length, 1); assert.equal(h.ledger.size, 1); assert.equal(h.state.history.length, 1);
  assert.equal(h.state.balance, h.wallet().balance_cents);
  assert.equal(h.state.stats.total_bet_cents, h.state.selected.bet_cents);
  return h;
}
function summary(h, round) {
  const amount = money(h, h.state.selected.win_cents);
  assert.equal(h.ids["meter-win"].textContent, amount);
  assert.equal(h.ids["round-note"].hidden, false);
  for (const id of ["round-note", "win-detail"]) {
    assert.ok(h.ids[id].textContent.includes("5000×"), id + " states round cap");
    assert.ok(h.ids[id].textContent.includes(amount), id + " states actual credited payout");
    assert.doesNotMatch(h.ids[id].textContent, /\{(?:amount|remaining)\}/);
  }
  const awarded = round.base.free_spins_awarded;
  if (awarded) {
    assert.equal(h.ids["bonus-progress"].textContent, `${round.free_spins.length} / ${awarded}`);
    assert.ok(h.ids["bonus-label"].textContent.includes("5000×"));
    const unused = awarded - round.free_spins.length;
    if (unused) assert.ok(h.ids["round-note"].textContent.includes(String(unused)));
  }
}

// Exact cap with no reduction is an engine-produced boundary case, not a
// claimed weighted-book outcome. The real current engine evaluates every step.
const generated = spawnSync(process.env.PYTHON || "python", ["-B", "-c", `
import json
from dataclasses import asdict
from polska_gurom.game import evaluate_paid_spin
class Refill:
    def __init__(self): self.symbols=iter(['P3']*(11*15)+['L1']*(5*15))
    def choice(self, population):
        symbol=next(self.symbols,'P4')
        assert symbol in population
        return symbol
base=asdict(evaluate_paid_spin([['P3']*5 for _ in range(3)],Refill()))
assert base['payout_units']==500000 and base['raw_payout_units']==500000
print(json.dumps(dict(base=base,free_spins=[],free_spin_credits=[],
    raw_payout_units=500000,payout_units=500000,bonus_payout_units=0,cap_reduction_units=0)))
`], { cwd: ROOT, encoding: "utf8", env: { ...process.env, PYTHONPATH: path.join(ROOT, "test-interface/engine") } });
assert.equal(generated.status, 0, generated.stderr || generated.error?.message || generated.stdout);
const exactCap = JSON.parse(generated.stdout);

async function main() {
  for (const name of ["cap", "bonus_cap8", "bonus_cap10", "bonus_cap12"]) {
    const round = fixtures.rounds[name];
    for (const lang of ["pl", "en", "de"]) for (const mode of ["animated", "instant", "skip-screens"]) {
      await check(`${name} ${lang} ${mode}: cap payout and awarded FS count`, async () => {
        const h = await run(round, lang, mode); summary(h, round);
        const awarded = round.base.free_spins_awarded;
        if (awarded && mode === "animated") {
          assert.ok(h.titles.some(value => value.startsWith(`${awarded} `)), "intro announces original award");
          for (let i = 1; i <= round.free_spins.length; i++) assert.ok(h.progress.includes(`${i} / ${awarded}`));
        }
        for (let i = round.free_spins.length + 1; i <= awarded; i++) {
          assert.ok(!h.progress.includes(`${i} / ${awarded}`), "unused FS is never presented");
        }
        await h.clock.drain(6000); summary(h, round);
        // Translation must preserve the cap and original denominator too.
        h.ids["lang-select"].value = lang === "pl" ? "de" : "pl";
        h.ids["lang-select"].emit("change"); summary(h, round);
        await h.clock.drain(6000); summary(h, round);
        if (round.free_spins.length) {
          const note = h.ids["round-note"].textContent;
          const button = h.ids["win-lines"].querySelectorAll("button")[0];
          assert.ok(button); button.click();
          const expected = h.state.lang === "pl" ? "przed limitem" : "vor dem Limit";
          assert.ok(h.ids["win-detail"].textContent.includes(expected), "manual partial-stage line names raw amount before cap");
          assert.equal(h.ids["round-note"].textContent, note, "cap remains visible during manual line inspection");
        }
        return { book_id: fixtures.book_ids[name], played: round.free_spins.length, awarded };
      });
    }
  }
  for (const lang of ["pl", "en", "de"]) for (const mode of ["animated", "instant", "skip-screens"]) {
    await check(`synthetic exact cap ${lang} ${mode}: no reduction still states cap`, async () => {
      assert.equal(exactCap.cap_reduction_units, 0);
      const h = await run(exactCap, lang, mode); summary(h, exactCap);
      await h.clock.drain(6000); summary(h, exactCap);
    });
  }
  const report = { math_version: fixtures.config.math_version, method: "Real legacy app.js in a minimal DOM with virtual time and a local API double; actual current weighted cap books plus an engine-produced exact-cap boundary fixture. No visual/browser claim.",
    source_sha256: crypto.createHash("sha256").update(source).digest("hex"), tests_run: checks.length,
    passed: checks.filter(check => check.passed).length, checks };
  report.status = report.tests_run === report.passed ? "pass" : "fail";
  fs.writeFileSync(path.join(__dirname, "legacy_cap_regressions.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(`${report.passed}/${report.tests_run} legacy cap presentation checks passed`);
  if (report.status !== "pass") process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
