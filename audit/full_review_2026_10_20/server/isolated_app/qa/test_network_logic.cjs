"use strict";
// Exercises the actual frontend against deterministic transport/protocol faults.
// Uses the same VM/minimal DOM as the autoplay regression; no browser or real socket claim.
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { harness, source, config } = require("./test_autoplay.cjs");

const PENDING_KEY = "pg-pending-round";
const checks = [];

async function check(scenario, work) {
  try {
    const evidence = await work();
    checks.push({ scenario, passed: true, ...evidence });
    console.log(`PASS ${scenario}`);
  } catch (error) {
    checks.push({ scenario, passed: false, error: error.stack || String(error) });
    console.error(`FAIL ${scenario}: ${error.message}`);
  }
}

async function manual(h) {
  let failure;
  const work = h.app.spin().catch(error => { failure = error; });
  await h.finished(); await work;
  assert.ifError(failure);
}

function assertPending(h, id) {
  assert.ok(h.state.pending, "unresolved request must remain recoverable");
  if (id !== undefined) assert.equal(h.state.pending.request_id, id);
  const persisted = JSON.parse(h.storage.get(PENDING_KEY));
  assert.equal(persisted.session_id, "probe-session", "pending belongs to the original session");
  assert.equal(persisted.request.request_id, h.state.pending.request_id, "persistent request keeps the original ID");
  return h.state.pending.request_id;
}

function assertOneSettled(h, requestId) {
  assert.equal(h.ledger.size, 1, "one uniquely charged round");
  assert.equal(h.state.stats.rounds, 1);
  assert.equal(h.state.balance, h.wallet().balance_cents);
  assert.equal(h.state.pending, null);
  assert.equal(h.storage.has(PENDING_KEY), false, "validated result clears persistent pending");
  assert.equal(h.state.history.length, 1, "one presented round");
  assert.ok(h.requests.every(request => request.request_id === requestId), "all attempts reuse one ID");
  assert.ok(h.requests.every(request => request.session_id === "probe-session"), "every attempt carries its original session");
  assert.equal(h.errors.length, 0, "no uncaught presentation errors");
}

async function initialize(h) {
  let done = false, error;
  const work = h.app.init().then(() => { done = true; }, failure => { done = true; error = failure; });
  await h.clock.until(() => done, "initialization to settle"); await work;
  assert.ifError(error);
}

async function runNetworkTests() {
  await check("Connection absent before POST: no charge; manual recovery reuses request and session", async () => {
    let offline = true;
    const h = harness({ instant: true, bonuses: false, behavior: () => offline ? "network-before" : undefined });
    await manual(h);
    assert.equal(h.requests.length, 1); assert.equal(h.ledger.size, 0);
    const id = assertPending(h); offline = false;
    await manual(h); assertOneSettled(h, id);
    return { attempts: h.requests.length, unique_charges: h.ledger.size };
  });

  await check("Response lost after settlement: retry displays the original round and never charges twice", async () => {
    let offline = true;
    const h = harness({ instant: true, bonuses: false, behavior: () => offline ? "lost-response" : undefined });
    await manual(h);
    assert.equal(h.ledger.size, 1); assert.equal(h.state.history.length, 0);
    const id = assertPending(h), expected = h.ledger.get(id);
    offline = false; await manual(h); assertOneSettled(h, id);
    assert.equal(h.state.selected.round_id, expected.round_id);
    assert.equal(h.state.balance, expected.balance_cents);
    return { attempts: h.requests.length, unique_charges: h.ledger.size };
  });

  for (const status of [408, 429, 500, 502, 503]) {
    await check(`Transient HTTP ${status}: autoplay retries the same ID and completes all 10 rounds`, async () => {
      const h = harness({ instant: true, bonuses: false,
        behavior: request => request.number === 1 && request.attempt === 1 ? `http-${status}` : undefined });
      h.state.autoCount = 10; h.start(); await h.finished();
      assert.equal(h.state.autoCompleted, 10); assert.equal(h.ledger.size, 10);
      assert.equal(h.requests.length, 11); assert.equal(h.requests[0].request_id, h.requests[1].request_id);
      assert.equal(h.state.pending, null); assert.equal(h.state.autoStatus, "autoComplete");
      assert.equal(h.state.balance, h.wallet().balance_cents);
      return { completed: h.state.autoCompleted, attempts: h.requests.length, unique_charges: h.ledger.size };
    });
  }

  for (const behavior of ["network-before", "lost-response", "http-429", "http-502"]) {
    await check(`Persistent ${behavior}: exactly 3 attempts, explicit stop, pending retained, manual recovery`, async () => {
      let failing = true;
      const h = harness({ instant: true, bonuses: false, behavior: () => failing ? behavior : undefined });
      h.state.autoCount = 10; h.start(); await h.finished();
      assert.equal(h.requests.length, 3, "autoplay retries are bounded to three attempts");
      assert.equal(h.state.autoCompleted, 0); assert.equal(h.state.auto, 0);
      assert.equal(h.state.autoStatus, "autoConnectionError");
      const id = assertPending(h);
      assert.equal(new Set(h.requests.map(request => request.request_id)).size, 1);
      const before = h.requests.length; await h.clock.drain();
      assert.equal(h.requests.length, before, "no requests continue silently after the stop");
      failing = false; await manual(h); assertOneSettled(h, id);
      assert.equal(h.state.autoCompleted, 1, "manual recovery counts only the recovered paid round");
      assert.equal(h.state.auto, 0, "manual recovery does not restart autoplay");
      return { failed_attempts: 3, recovered_attempts: h.requests.length, unique_charges: h.ledger.size };
    });
  }

  for (const behavior of ["fetch-stall", "body-stall"]) {
    await check(`${behavior}: 15-second deadline covers transport and response body, then safe recovery`, async () => {
      let failing = true;
      const h = harness({ instant: true, bonuses: false, behavior: () => failing ? behavior : undefined });
      await manual(h);
      assert.equal(h.clock.now, 15000, "deadline expires at 15 seconds");
      assert.equal(h.requests.length, 1);
      assert.equal(h.ledger.size, behavior === "body-stall" ? 1 : 0);
      const id = assertPending(h); failing = false;
      await manual(h); assertOneSettled(h, id);
      return { timeout_ms: 15000, attempts: h.requests.length, unique_charges: h.ledger.size };
    });
  }

  await check("Persistent transport stalls: autoplay stops after 3 timeouts without any charge", async () => {
    const h = harness({ instant: true, bonuses: false, behavior: () => "fetch-stall" });
    h.state.autoCount = 10; h.start(); await h.finished();
    assert.equal(h.requests.length, 3); assert.equal(h.ledger.size, 0);
    assert.equal(h.clock.now, 46500, "three 15s deadlines plus 0.5s and 1s backoff");
    assertPending(h); assert.equal(h.state.autoStatus, "autoConnectionError");
    return { attempts: h.requests.length, virtual_ms: h.clock.now, unique_charges: h.ledger.size };
  });

  for (const code of ["session_expired", "session_changed", "result_expired"]) {
    await check(`${code}: terminal recovery error stops old-session play without a charge`, async () => {
      const h = harness({ instant: true, bonuses: false,
        behavior: () => ({ type: "error", status: 409, code }) });
      h.state.autoCount = 10; h.start(); await h.finished();
      assert.equal(h.requests.length, 1, "terminal session errors must not retry");
      assert.equal(h.ledger.size, 0); assert.equal(h.state.pending, null);
      assert.equal(h.storage.has(PENDING_KEY), false); assert.equal(h.state.online, false);
      assert.equal(h.ids["spin-button"].disabled, true);
      assert.match(h.ids["win-detail"].textContent, /sesj|odśwież/i);
      await h.clock.drain(); assert.equal(h.requests.length, 1);
      return { attempts: 1, unique_charges: 0 };
    });
  }

  await check("Double-click while a response is delayed: busy guard sends exactly one request", async () => {
    const h = harness({ instant: true, bonuses: false, behavior: () => ({ type: "delay", milliseconds: 8000 }) });
    const first = h.app.spin(); const second = h.app.spin();
    await h.finished(); await Promise.all([first, second]);
    assert.equal(h.requests.length, 1); assertOneSettled(h, h.requests[0].request_id);
    return { attempts: 1, unique_charges: 1 };
  });

  await check("Connection disappears after bonus result arrives: finish all 8 free spins, stop on next paid request", async () => {
    let offline = false;
    const h = harness({ speed: "turbo",
      behavior: () => offline ? "network-before" : undefined,
      accepted(request) { if (request.number === 13) offline = true; } });
    h.state.autoCount = 25; h.start(); await h.finished();
    assert.equal(h.ledger.size, 13); assert.equal(h.state.autoCompleted, 13);
    assert.equal(h.state.selected.round.free_spins.length, 8);
    assert.equal(h.ids["bonus-progress"].textContent, "8 / 8");
    assert.equal(h.state.balance, h.wallet().balance_cents);
    assert.equal(h.requests.filter(request => request.number === 14).length, 3);
    assertPending(h); assert.equal(h.state.autoStatus, "autoConnectionError");
    return { completed_paid_rounds: 13, completed_free_spins_in_last_round: 8,
      next_request_attempts: 3, unique_charges: 13 };
  });

  for (const behavior of ["bad-json", "empty-json", "wrong-request-id", "wrong-session-id", "wrong-version"]) {
    await check(`${behavior}: rejected before clearing pending or presenting a result; exact recovery`, async () => {
      let failing = true;
      const h = harness({ instant: true, bonuses: false, behavior: () => failing ? behavior : undefined });
      await manual(h);
      assert.equal(h.ledger.size, 1); assert.equal(h.state.history.length, 0, "invalid response must not enter history");
      assert.equal(h.state.stats.rounds, 0, "invalid response must not update displayed statistics");
      const id = assertPending(h); failing = false;
      await manual(h); assertOneSettled(h, id);
      return { attempts: h.requests.length, unique_charges: h.ledger.size };
    });
  }

  await check("Slow response below deadline: one round and one request, without retries", async () => {
    const h = harness({ instant: true, bonuses: false, behavior: () => ({ type: "delay", milliseconds: 8000 }) });
    await manual(h); assertOneSettled(h, h.requests[0].request_id);
    assert.equal(h.requests.length, 1); assert.equal(h.clock.now, 8000);
    return { response_delay_ms: h.clock.now, unique_charges: h.ledger.size };
  });

  await check("Late response beyond deadline: timeout retains original ID, retry does not double-charge", async () => {
    let slow = true;
    const h = harness({ instant: true, bonuses: false,
      behavior: () => slow ? { type: "delay", milliseconds: 20000 } : undefined });
    await manual(h); assert.equal(h.clock.now, 15000); assert.equal(h.ledger.size, 1);
    const id = assertPending(h); slow = false; await manual(h); assertOneSettled(h, id);
    await h.clock.drain(); assert.equal(h.ledger.size, 1); assert.equal(h.state.history.length, 1);
    return { attempts: h.requests.length, unique_charges: h.ledger.size };
  });

  await check("Page reload with settled but unread response: recover saved request without duplicate history", async () => {
    const first = harness({ instant: true, bonuses: false, behavior: () => "lost-response" });
    await manual(first); const id = assertPending(first);
    const reloaded = harness({ boot: true, backend: first.backend, sessionStorage: first.storage });
    await initialize(reloaded);
    assertPending(reloaded, id);
    assert.equal(reloaded.requests.length, 1, "initialization never starts a new paid round");
    reloaded.state.instant = true; await manual(reloaded); assertOneSettled(reloaded, id);
    return { attempts: reloaded.requests.length, unique_charges: reloaded.ledger.size, displayed_results: reloaded.state.history.length };
  });

  await check("Reload after autoplay round 81 outage: recover 81/100 and keep autoplay stopped", async () => {
    const first = harness({ instant: true, bonuses: false,
      behavior: request => request.number === 81 ? "lost-response" : undefined });
    first.start(); await first.finished();
    assert.equal(first.state.autoCompleted, 80); assert.equal(first.ledger.size, 81);
    const id = assertPending(first);
    const reloaded = harness({ boot: true, backend: first.backend, sessionStorage: first.storage });
    await initialize(reloaded); assertPending(reloaded, id);
    assert.equal(reloaded.state.autoTotal, 100); assert.equal(reloaded.state.autoCompleted, 80);
    assert.equal(reloaded.state.auto, 0);
    reloaded.state.instant = true; await manual(reloaded);
    assert.equal(reloaded.state.autoCompleted, 81); assert.equal(reloaded.state.auto, 0);
    assert.equal(reloaded.state.stats.rounds, 81); assert.equal(reloaded.ledger.size, 81);
    assert.equal(new Set(reloaded.state.history.map(record => record.round_id)).size, reloaded.state.history.length);
    assert.equal(reloaded.state.balance, reloaded.wallet().balance_cents);
    await reloaded.clock.drain(); assert.equal(reloaded.ledger.size, 81);
    return { completed: reloaded.state.autoCompleted, selected: reloaded.state.autoTotal, unique_charges: reloaded.ledger.size };
  });

  await check("Reload after server session replacement: stale pending never executes in the new session", async () => {
    const first = harness({ instant: true, bonuses: false, behavior: () => "lost-response" });
    await manual(first); assertPending(first);
    const replacement = { ledger: new Map(), balance: 1000000, totalBet: 0, totalWin: 0,
      sessionId: "probe-session-new", requests: [], attempts: new Map() };
    const reloaded = harness({ boot: true, backend: replacement, sessionStorage: first.storage });
    await initialize(reloaded);
    assert.equal(reloaded.state.pending, null, "stale pending must not migrate into a replacement session");
    assert.equal(reloaded.requests.length, 0); assert.equal(reloaded.ledger.size, 0);
    assert.equal(reloaded.state.balance, 1000000);
    assert.equal(reloaded.storage.has(PENDING_KEY), false);
    assert.match(reloaded.ids.toast.textContent, /sesj/i, "session replacement is explained to the player");
    return { new_session_charges: 0 };
  });

  await check("Symbol manifest stalls during startup: initialization ends at its 15-second deadline", async () => {
    const h = harness({ boot: true, initBehavior: url => url === "/assets/symbols.json" ? "fetch-stall" : undefined });
    h.state.online = false; await initialize(h);
    assert.equal(h.clock.now, 15000); assert.equal(h.state.online, false);
    assert.equal(h.ids["spin-button"].disabled, true); assert.equal(h.ledger.size, 0);
    return { timeout_ms: h.clock.now, unique_charges: h.ledger.size };
  });

  const report = {
    math_version: config.math_version,
    passed: checks.every(item => item.passed), checks_passed: checks.filter(item => item.passed).length,
    checks_total: checks.length,
    created_at: new Date().toISOString(),
    method: "Actual app.js evaluated in Node VM with minimal DOM, accelerated timers, AbortSignal-aware transport/body faults, persistent tab storage and an idempotent session mock. Tests frontend state transitions; separate HTTP and browser tests cover their respective layers.",
    source_sha256: crypto.createHash("sha256").update(source).digest("hex"), checks
  };
  const reportDirectory = process.env.PG_QA_OUT_DIR || __dirname;
  fs.mkdirSync(reportDirectory, { recursive: true });
  fs.writeFileSync(path.join(reportDirectory, "network_logic_results.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({ passed: report.passed, checks_passed: report.checks_passed, checks_total: report.checks_total }, null, 2));
  if (!report.passed) process.exitCode = 1;
  return report;
}

module.exports = { runNetworkTests };
if (require.main === module) runNetworkTests().catch(error => { console.error(error); process.exitCode = 1; });
