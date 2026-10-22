"use strict";
// Real app.js with an actual exported 12-FS round, a minimal DOM and virtual clock.
// This verifies presentation state, completion, retry and autoplay bookkeeping;
// it does not claim graphical rendering or randomness/frequency coverage.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const { harness, assertCompleted, config, clone, source } = require("./test_autoplay.cjs");
const OUT = path.resolve(process.env.PG_QA_OUT_DIR || path.join(__dirname, "../../audit/bonus12_fix_2026_10_20"));
const fixture = JSON.parse(fs.readFileSync(path.join(OUT, "actual_export_12fs_fixture.json"), "utf8"));
const round = fixture.round;
assert.equal(fixture.math_version, config.math_version, "Fixture belongs to current engine mathematics");
assert.equal(round.base.scatter_count, 5);
assert.equal(round.base.free_spins_awarded, 12);
assert.equal(round.free_spins.length, 12);
const checks = [];

function probe(options = {}) {
  const h = harness({ roundFactory: () => clone(round), ...options });
  h.state.bet = 100;
  h.app.controls();
  h.progress = [];
  const element = h.ids["bonus-progress"];
  const descriptor = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(element), "textContent");
  Object.defineProperty(element, "textContent", {
    get() { return descriptor.get.call(this); },
    set(value) {
      h.progress.push(String(value));
      descriptor.set.call(this, value);
      options.onProgress?.(String(value), h);
    },
  });
  return h;
}

async function manual(h) {
  const pending = h.app.spin();
  await h.finished();
  await pending;
}

function assertWallet(h, count) {
  assert.equal(h.ledger.size, count);
  assert.equal(h.state.stats.rounds, count);
  assert.equal(h.state.stats.total_bet_cents, 100 * count, "Only paid rounds debit bets");
  assert.equal(h.state.stats.total_win_cents, round.payout_units * count);
  assert.equal(h.state.balance, h.wallet().balance_cents);
  assert.equal(h.errors.length, 0);
  assert.equal(h.state.selected.round.free_spins.length, 12);
  assert.equal(h.ids["bonus-progress"].textContent, "12 / 12");
}

async function check(name, fn) {
  try {
    const details = await fn();
    checks.push({ name, status: "pass", ...details });
    console.log(`PASS ${name}`);
  } catch (error) {
    checks.push({ name, status: "fail", error: error.stack || String(error) });
    console.error(`FAIL ${name}: ${error.message}`);
  }
}

async function main() {
  for (const mode of ["normal", "quick", "turbo", "instant"]) {
    await check(`Actual exported 12-FS round renders through completion in ${mode} mode`, async () => {
      const h = probe({ speed: mode === "instant" ? "normal" : mode, instant: mode === "instant" });
      await manual(h);
      assertWallet(h, 1);
      if (mode !== "instant") {
        for (let i = 1; i <= 12; i++) assert.ok(h.progress.includes(`${i} / 12`), `Free spin ${i}/12 presented`);
      }
      assert.equal(h.requests.length, 1);
      return { paid_rounds: 1, free_spins: 12, bonus_final_counter: h.ids["bonus-progress"].textContent };
    });
  }

  await check("100 autoplay rounds containing 12 FS each count 100 paid rounds and 1200 free spins", async () => {
    const h = probe({ speed: "turbo" });
    h.start(); await h.finished(); assertCompleted(h); assertWallet(h, 100);
    assert.equal(h.requests.length, 100);
    assert.equal(h.progress.filter(value => value === "11 / 12").length, 100);
    return { paid_rounds: 100, free_spins: 1200, requests: 100 };
  });

  await check("Lost 12-FS reply retries the original paid round without double counting", async () => {
    const h = probe({ instant: true, behavior: request => request.attempt === 1 ? "lost-response" : undefined });
    h.start(); await h.finished(); assertCompleted(h); assertWallet(h, 100);
    assert.equal(h.requests.length, 200);
    assert.equal(new Set(h.requests.map(request => request.request_id)).size, 100);
    return { paid_rounds: 100, free_spins: 1200, requests: 200, unique_charges: 100 };
  });

  await check("STOP during the fifth free spin completes all twelve but starts no extra paid round", async () => {
    let stopped = false;
    const h = probe({ speed: "turbo", onProgress(value, current) {
      if (value === "5 / 12" && !stopped) { stopped = true; current.stop(); }
    } });
    h.start(); await h.finished(); await h.clock.drain(); assertWallet(h, 1);
    assert.equal(h.state.autoCompleted, 1);
    assert.equal(h.state.autoStatus, "autoStopped");
    assert.equal(h.requests.length, 1);
    assert.ok(h.progress.includes("12 / 12"));
    return { paid_rounds: 1, free_spins_completed_after_stop: 12, requests: 1 };
  });

  const report = {
    generated_at: new Date().toISOString(),
    status: checks.every(check => check.status === "pass") ? "pass" : "fail",
    method: "Actual app.js evaluated in Node VM; actual exported positive-weight 12-FS book; minimal DOM, virtual timers and idempotent mock API. Not a browser rendering or random-frequency test.",
    math_version: config.math_version,
    actual_export_witness: { book_id: fixture.book_id, weight: fixture.weight },
    source_sha256: crypto.createHash("sha256").update(source).digest("hex"),
    tests_run: checks.length, passed: checks.filter(check => check.status === "pass").length, checks,
  };
  fs.writeFileSync(path.join(OUT, "frontend_12fs_results.json"), JSON.stringify(report, null, 2) + "\n");
  if (report.status !== "pass") process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
