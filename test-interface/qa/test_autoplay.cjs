"use strict";
// Deterministic logic regression: real app.js, minimal DOM, virtual clock and mock API.
// This does not claim browser rendering, browser throttling or real-network coverage.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const crypto = require("node:crypto");

const APP = path.resolve(process.argv[2] || path.join(__dirname, "../web/app.js"));
const HTML = fs.readFileSync(path.join(__dirname, "../web/index.html"), "utf8");
const source = fs.readFileSync(APP, "utf8");
const clone = value => JSON.parse(JSON.stringify(value));
const currentMathVersion = fs.readFileSync(path.join(__dirname, "../engine/polska_gurom/config.py"), "utf8")
  .match(/^MATH_VERSION\s*=\s*["']([^"']+)["']/m)?.[1];
assert.ok(currentMathVersion, "Current engine mathematics version is declared");

class Element {
  constructor(tag = "div") {
    this.tagName = tag.toUpperCase(); this.children = []; this.dataset = {};
    this.value = ""; this.disabled = false; this.hidden = false; this.checked = false;
    this.listeners = {}; this.attrs = {}; this.classes = new Set(); this._text = "";
    this.style = { setProperty(key, value) { this[key] = String(value); } };
    this.classList = {
      add: (...values) => values.forEach(value => this.classes.add(value)),
      remove: (...values) => values.forEach(value => this.classes.delete(value)),
      toggle: (value, force) => {
        const present = force === undefined ? !this.classes.has(value) : force;
        present ? this.classes.add(value) : this.classes.delete(value); return present;
      }
    };
  }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent || "").join(""); }
  set className(value) { this.classes = new Set(value.split(/\s+/).filter(Boolean)); }
  get className() { return [...this.classes].join(" "); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = [...nodes]; this._text = ""; }
  setAttribute(key, value) { this.attrs[key] = String(value); }
  removeAttribute(key) { delete this.attrs[key]; }
  addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); }
  emit(type, event = {}) {
    for (const callback of this.listeners[type] || []) callback({ target: this, type, ...event });
  }
  click() { if (!this.disabled) this.emit("click"); }
  querySelectorAll(selector) {
    const descendants = this.children.flatMap(child => [child, ...(child.querySelectorAll?.("*") || [])]);
    return descendants.filter(child => selector === "*" || selector === "button" && child.tagName === "BUTTON");
  }
  querySelector(selector) { return this.children.find(child => selector === `[value="${child.value}"]`) || null; }
  showModal() { this.attrs.open = ""; }
  close() { delete this.attrs.open; }
  getBoundingClientRect() { return { left: 0, right: 500, top: 0, bottom: 500, width: 500, height: 500 }; }
}

class Clock {
  constructor() { this.now = 0; this.serial = 0; this.timers = new Map(); }
  set(callback, milliseconds = 0, interval = false) {
    const id = ++this.serial;
    this.timers.set(id, { callback, due: this.now + Math.max(0, milliseconds), interval: interval ? milliseconds : 0 });
    return id;
  }
  clear(id) { this.timers.delete(id); }
  async flush() { for (let i = 0; i < 40; i++) await Promise.resolve(); }
  async step() {
    await this.flush();
    const next = [...this.timers].sort((a, b) => a[1].due - b[1].due || a[0] - b[0])[0];
    if (!next) return false;
    const [id, timer] = next; this.now = timer.due; this.timers.delete(id);
    if (timer.interval) this.timers.set(id, { ...timer, due: this.now + timer.interval });
    timer.callback(); await this.flush(); return true;
  }
  async until(predicate, message, maximumSteps = 30000) {
    for (let step = 0; step < maximumSteps; step++) {
      await this.flush(); if (predicate()) return;
      assert.ok(await this.step(), `No continuation while waiting: ${message}`);
    }
    assert.fail(`Virtual clock step limit: ${message}`);
  }
  async drain(milliseconds = 60000) {
    const deadline = this.now + milliseconds;
    for (let step = 0; step < 30000; step++) {
      await this.flush();
      if (![...this.timers.values()].some(timer => timer.due <= deadline)) return;
      await this.step();
    }
    assert.fail("Unexpected recurring work while draining stopped autoplay");
  }
}

const grid = [["L1", "L2", "P3", "L3", "P2"], ["P4", "L4", "WILD", "P1", "P4"], ["L3", "P2", "L1", "SCATTER", "L2"]];
const config = {
  symbols: ["L1", "L2", "L3", "L4", "P1", "P2", "P3", "P4", "WILD", "SCATTER"],
  paylines: [[1, 1, 1, 1, 1]], paytable_units: { L1: { 3: 100, 4: 200, 5: 500 } },
  payout_scale: 100, fs_line_multiplier: 4, free_spins: { 3: 8, 4: 10, 5: 12 },
  max_win_units: 500000, bet_options_cents: [100, 200, 500, 1000, 2000, 5000, 10000],
  math_version: currentMathVersion
};
function makeRound(number, bonuses = true) {
  const bonus = bonuses && number % 13 === 0;
  const spin = (free = false, index = 0) => ({
    grid: clone(grid), evaluation_grid: clone(grid),
    expanding_reel: free && index === 2 ? 2 : null,
    scatter_count: bonus && !free ? 3 : 0, scatter_payout_units: bonus && !free ? 100 : 0,
    payout_units: free ? 400 : bonus ? 100 : 0, bonus_triggered: bonus && !free,
    line_wins: free ? [{ line_id: 1, rows: [1, 1, 1, 1, 1], symbol: "L1", count: 3, payout_units: 400, line_multiplier: 4 }] : []
  });
  return { base: spin(), free_spins: bonus ? Array.from({ length: 8 }, (_, index) => spin(true, index)) : [],
    free_spin_credits: bonus ? Array(8).fill(400) : [], bonus_payout_units: bonus ? 3200 : 0,
    payout_units: bonus ? 3300 : 0, cap_reduction_units: 0 };
}

function harness(options = {}) {
  const clock = new Clock();
  const ids = Object.fromEntries([...HTML.matchAll(/<([\w-]+)\b[^>]*\bid="([^"]+)"[^>]*>/g)].map(match => [match[2], new Element(match[1])]));
  ids["test-mode-select"].value = "random"; ids["playline-select"].value = "none";
  for (const value of ["random", "win", "bonus", "expansion"]) {
    const option = new Element("option"); option.value = value; ids["test-mode-select"].append(option);
  }
  const presets = [10, 25, 50, 100, 250, 500].map(count => {
    const element = new Element("button"); element.dataset.count = String(count); return element;
  });
  const cabinet = new Element(), presetContainer = new Element();
  const document = {
    hidden: false, documentElement: { lang: "pl" }, listeners: {},
    getElementById: id => { assert.ok(ids[id], `Unknown DOM id: ${id}`); return ids[id]; },
    createElement: tag => new Element(tag), createElementNS: (_, tag) => new Element(tag),
    querySelector: selector => selector === ".slot-cabinet" ? cabinet : selector === ".autoplay-presets" ? presetContainer :
      selector === "dialog[open]" ? Object.values(ids).find(element => element.tagName === "DIALOG" && "open" in element.attrs) || null : null,
    querySelectorAll: selector => selector === "[data-count]" ? presets : [],
    addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); }
  };
  const backend = options.backend || { ledger: new Map(), balance: options.balance ?? 1000000,
    totalBet: 0, totalWin: 0, sessionId: "probe-session", requests: [], attempts: new Map() };
  const { ledger, requests, attempts } = backend, errors = [];
  const storage = options.sessionStorage || new Map();
  let api;
  const stateData = () => ({ balance_cents: backend.balance, session_id: backend.sessionId,
    rounds: ledger.size, total_bet_cents: backend.totalBet, total_win_cents: backend.totalWin,
    recent_rounds: [...ledger.values()].reverse() });
  const response = (payload, status = 200) => ({ ok: status < 400, status, json: async () => clone(payload) });
  const abortError = () => Object.assign(new Error("Simulated request deadline"), { name: "AbortError" });
  const untilAbort = signal => new Promise((resolve, reject) => {
    if (signal?.aborted) reject(abortError());
    else signal?.addEventListener("abort", () => reject(abortError()), { once: true });
  });
  const waitForResponse = (milliseconds, signal) => new Promise((resolve, reject) => {
    if (signal?.aborted) { reject(abortError()); return; }
    const timer = clock.set(resolve, milliseconds);
    signal?.addEventListener("abort", () => { clock.clear(timer); reject(abortError()); }, { once: true });
  });
  const context = {
    console: { log() {}, error: error => errors.push(String(error)) }, document, Intl, URL, Blob, AbortController, crypto,
    location: { origin: "http://127.0.0.1:8765" },
    localStorage: { getItem: () => null, setItem() {} },
    sessionStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => storage.set(key, String(value)),
      removeItem: key => storage.delete(key)
    },
    window: { matchMedia: () => ({ matches: false }), addEventListener() {} },
    matchMedia: () => ({ matches: false }),
    setTimeout: (callback, ms) => clock.set(callback, ms), clearTimeout: id => clock.clear(id),
    setInterval: (callback, ms) => clock.set(callback, ms, true), clearInterval: id => clock.clear(id),
    fetch: async (url, init = {}) => {
      if (url !== "/api/spin") {
        const initBehavior = options.initBehavior?.(url, api);
        if (initBehavior === "fetch-stall") return untilAbort(init.signal);
        if (initBehavior === "network-before") throw new TypeError("Simulated startup connection failure");
        if (url === "/api/config") return response(config);
        if (url === "/api/state") return response(stateData());
        if (url === "/assets/symbols.json") return response({});
        assert.fail(`The isolated probe does not implement ${url}`);
      }
      const body = JSON.parse(init.body), requestId = body.request_id;
      attempts.set(requestId, (attempts.get(requestId) || 0) + 1);
      const number = ledger.has(requestId) ? ledger.get(requestId).stats.rounds : ledger.size + 1;
      const request = { ...body, session_id: init.headers?.["X-Game-Session"], number, attempt: attempts.get(requestId) }; requests.push(request);
      const behavior = options.behavior?.(request, api);
      if (behavior === "network-before") throw new TypeError("Simulated connection failure");
      if (behavior === "fetch-stall") return untilAbort(init.signal);
      if (behavior === "server-error") return response({ error: "Simulated server error", code: "internal_error" }, 503);
      if (typeof behavior === "string" && /^http-\d+$/.test(behavior)) {
        return response({ error: "Simulated temporary HTTP response", code: "temporary_error" }, Number(behavior.slice(5)));
      }
      if (typeof behavior === "object" && behavior?.type === "error") {
        return response({ error: behavior.message || "Sesja zakończona. Odśwież stronę.", code: behavior.code }, behavior.status);
      }
      if (behavior === "no-funds") return response({ error: "Za mało środków testowych.", code: "insufficient_funds" }, 409);
      let result = ledger.get(requestId);
      if (!result) {
        if (backend.balance < body.bet_cents) return response({ error: "Za mało środków testowych.", code: "insufficient_funds" }, 409);
        const before = backend.balance, round = options.roundFactory ? clone(options.roundFactory(number)) : makeRound(number, options.bonuses !== false);
        const win = body.bet_cents * round.payout_units / config.payout_scale;
        backend.balance += win - body.bet_cents; backend.totalBet += body.bet_cents; backend.totalWin += win;
        result = { round_id: `round-${number}`, mode: "random", is_scenario: false,
          request_id: requestId, session_id: backend.sessionId, math_version: config.math_version,
          created_at: new Date(number * 1000).toISOString(), bet_cents: body.bet_cents,
          balance_before_cents: before, balance_cents: backend.balance, win_cents: win, round,
          stats: { rounds: number, total_bet_cents: backend.totalBet, total_win_cents: backend.totalWin } };
        ledger.set(requestId, result);
      }
      options.accepted?.(request, api);
      if (behavior === "lost-response") throw new TypeError("Simulated response lost after settlement");
      if (behavior === "body-stall") return { ok: true, status: 200, json: () => untilAbort(init.signal) };
      if (behavior === "bad-json") return { ok: true, status: 200, json: async () => { throw new SyntaxError("Simulated malformed JSON"); } };
      if (behavior === "empty-json") return response({});
      if (behavior === "wrong-request-id") return response({ ...result, request_id: "unrelated-request" });
      if (behavior === "wrong-session-id") return response({ ...result, session_id: "unrelated-session" });
      if (behavior === "wrong-version") return response({ ...result, math_version: "0.0.0-invalid" });
      if (typeof behavior === "object" && behavior?.type === "delay") await waitForResponse(behavior.milliseconds, init.signal);
      return response(result);
    }
  };
  const exposed = source.replace(/\s+init\(\);\s+\}\)\(\);\s*$/, "\n globalThis.autoplayProbe={state,controls,spin,createGrid,bindEvents,init};\n})();");
  assert.notEqual(exposed, source, "Could not expose the unmodified application entry points");
  vm.runInNewContext(exposed, context, { filename: APP });
  const app = context.autoplayProbe;
  Object.assign(app.state, { config, symbols: {}, online: true, balance: backend.balance, sessionId: backend.sessionId,
    speed: options.speed || "normal", instant: !!options.instant, skipScreens: false });
  if (!options.boot) { app.createGrid(); app.bindEvents(); app.controls(); }
  api = { app, state: app.state, ids, clock, document, ledger, requests, attempts, errors, backend, storage, wallet: stateData,
    hide(hidden) {
      document.hidden = hidden;
      for (const listener of document.listeners.visibilitychange || []) listener({ type: "visibilitychange", target: document });
    },
    start() { ids["auto-button"].click(); ids["autoplay-start"].click(); },
    stop() { ids["autoplay-stop"].click(); },
    async finished() { await clock.until(() => !app.state.busy && !app.state.auto && !app.state.autoRetrying, "series to finish"); }
  };
  return api;
}

function assertCompleted(h, count = 100) {
  assert.equal(h.state.autoCompleted, count, "completed paid rounds");
  assert.equal(h.ledger.size, count, "uniquely charged rounds");
  assert.equal(h.state.stats.rounds, count, "server round count");
  assert.equal(h.state.auto, 0, "no remaining rounds");
  assert.equal(h.state.autoStatus, "autoComplete");
  assert.equal(h.ids["autoplay-progress-value"].textContent, `${count} / 100`);
  assert.equal(h.state.balance, h.wallet().balance_cents, "displayed balance matches settled balance");
  assert.equal(new Set(h.state.history.map(result => result.round_id)).size, count, "unique displayed results");
  assert.equal(h.errors.length, 0, "no presentation errors");
}

async function runOriginalTests() {
  const checks = [];
  for (const mode of ["normal", "quick", "turbo", "instant"]) {
    const h = harness({ speed: mode === "instant" ? "normal" : mode, instant: mode === "instant" });
    h.start(); await h.finished(); assertCompleted(h);
    assert.equal(h.requests.length, 100);
    assert.ok(h.state.history.some(result => result.round.free_spins.length), "bonus rounds exercised");
    checks.push({ scenario: `100 ${mode} rounds with deterministic bonuses`, passed: true, rounds: h.ledger.size, virtual_ms: h.clock.now });
  }
  {
    const h = harness(); h.start();
    await h.clock.until(() => h.state.autoCompleted === 80 && !h.state.busy, "80 completed rounds before hiding");
    h.hide(true); await h.finished(); assertCompleted(h);
    h.hide(false); await h.clock.drain(); assert.equal(h.ledger.size, 100);
    checks.push({ scenario: "Hide at 80/100, complete hidden, show again without extra spins", passed: true });
  }
  {
    let hidden = false;
    const h = harness({ accepted(request, probe) { if (request.number === 81 && !hidden) { hidden = true; probe.hide(true); } } });
    h.start(); await h.finished(); assertCompleted(h);
    checks.push({ scenario: "Hide during round 81 presentation and finish 100/100", passed: true });
  }
  {
    let lost = false;
    const h = harness({ behavior(request) { if (request.number === 81 && !lost) { lost = true; return "lost-response"; } } });
    h.start(); await h.finished(); assertCompleted(h);
    assert.equal(h.requests.length, 101); assert.equal(h.attempts.size, 100);
    assert.equal(h.requests[80].request_id, h.requests[81].request_id, "retry reuses settled request id");
    checks.push({ scenario: "Lost response at round 81 retries same ID: 100 charges, 100 results, 101 requests", passed: true });
  }
  {
    let failed = false;
    const h = harness({ behavior(request) { if (request.number === 81 && !failed) { failed = true; return "server-error"; } } });
    h.start(); await h.finished(); assertCompleted(h); assert.equal(h.requests.length, 101);
    assert.equal(h.requests[80].request_id, h.requests[81].request_id);
    checks.push({ scenario: "Transient 503 at round 81 recovers to exactly 100/100", passed: true });
  }
  for (const serverReject of [false, true]) {
    const h = harness({ balance: serverReject ? 1000000 : 16000, bonuses: false,
      behavior: request => serverReject && request.number === 81 ? "no-funds" : undefined });
    h.start(); await h.finished();
    assert.equal(h.state.autoCompleted, 80); assert.equal(h.ledger.size, 80);
    assert.equal(h.state.autoStatus, "autoNoFunds"); assert.equal(h.state.pending, null);
    assert.equal(h.ids["autoplay-progress-value"].textContent, "80 / 100");
    assert.match(h.ids["autoplay-progress-label"].textContent, /środk|sald/i);
    checks.push({ scenario: `${serverReject ? "API 409" : "Local balance check"} after 80 rounds shows explicit insufficient balance reason`, passed: true });
  }
  {
    const h = harness(); h.start();
    await h.clock.until(() => h.state.autoCompleted === 5 && !h.state.busy, "five rounds before STOP");
    h.stop(); await h.clock.drain();
    assert.equal(h.ledger.size, 5); assert.equal(h.state.autoCompleted, 5); assert.equal(h.state.autoStatus, "autoStopped");
    checks.push({ scenario: "STOP between rounds cancels continuation with no extra charge", passed: true });
  }
  {
    let stopped = false;
    const h = harness({ accepted(request, probe) { if (request.number === 5 && !stopped) { stopped = true; probe.stop(); } } });
    h.start(); await h.finished(); await h.clock.drain();
    assert.equal(h.ledger.size, 5); assert.equal(h.state.autoCompleted, 5); assert.equal(h.state.autoStatus, "autoStopped");
    checks.push({ scenario: "STOP in flight finishes current round and starts no extra rounds", passed: true });
  }
  {
    const h = harness({ behavior: request => request.number === 81 ? "network-before" : undefined });
    h.start(); await h.finished();
    assert.equal(h.ledger.size, 80); assert.equal(h.state.autoCompleted, 80);
    assert.equal(h.state.autoStatus, "autoConnectionError"); assert.ok(h.state.pending);
    const failures = h.requests.filter(request => request.number === 81);
    assert.ok(failures.length >= 2 && failures.length <= 4, "bounded retries");
    assert.equal(new Set(failures.map(request => request.request_id)).size, 1);
    assert.equal(failures[0].request_id, h.state.pending.request_id, "pending recovery keeps original request id");
    await h.clock.drain(); assert.equal(h.ledger.size, 80);
    checks.push({ scenario: "Persistent connection failure stops with reason and preserves same pending ID", passed: true, attempts: failures.length });
  }
  const report = { passed: true,
    math_version: config.math_version,
    method: "Real app.js evaluated in Node VM with a minimal DOM, accelerated virtual timers and an idempotent mock API; deterministic logic regression, not browser/rendering/network integration QA.",
    source_sha256: crypto.createHash("sha256").update(source).digest("hex"), checks };
  const reportDirectory = process.env.PG_QA_OUT_DIR || __dirname;
  fs.mkdirSync(reportDirectory, { recursive: true });
  fs.writeFileSync(path.join(reportDirectory, "autoplay_logic_results.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify(report, null, 2));
  return report;
}

module.exports = { harness, assertCompleted, runOriginalTests, config, makeRound, clone, source, APP };
if (require.main === module) runOriginalTests().catch(error => { console.error(error); process.exitCode = 1; });
