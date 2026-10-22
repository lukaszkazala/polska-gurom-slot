"use strict";
// Direct Stake Engine wallet transport. No local outcome selection or wallet settlement.
(() => {
  const SCALE = 1_000_000;
  const natural = value => Number.isSafeInteger(value) && value >= 0;
  const clone = value => JSON.parse(JSON.stringify(value));
  const canonical = value => JSON.stringify(value, (_, item) => item && typeof item === "object" && !Array.isArray(item) ? Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]])) : item);
  function failure(code, status, uncertain = false) {
    const error = new Error(code); Object.assign(error, { code, status, uncertain }); return error;
  }
  function requireThat(condition, code = "rgs_invalid_response") {
    if (!condition) throw failure(code, undefined, true);
  }
  function validateCurrency(currency) {
    if (["SC", "GC", "XSC", "XGC"].includes(currency)) throw failure("rgs_social_unavailable", 400);
    requireThat(typeof currency === "string" && /^[A-Z]{3,8}$/.test(currency), "rgs_invalid_currency");
  }
  function formatAmount(amount, currency, locale = "en-GB") {
    validateCurrency(currency);
    requireThat(Number.isSafeInteger(amount), "rgs_amount_overflow");
    // Preserve micro-units even above the safe range for floating point division.
    const absolute = BigInt(amount < 0 ? -amount : amount);
    const whole = absolute / BigInt(SCALE);
    const fraction = String(absolute % BigInt(SCALE)).padStart(6, "0").replace(/0+$/, "");
    const options = currency.length === 3 ? { style: "currency", currency, currencyDisplay: "code" } : { minimumFractionDigits: 2 };
    const minimum = new Intl.NumberFormat(locale, options).resolvedOptions().minimumFractionDigits;
    const digits = Math.max(minimum, fraction.length);
    const formatter = new Intl.NumberFormat(locale, { ...options, minimumFractionDigits: digits, maximumFractionDigits: digits });
    const signedWhole = amount < 0 ? (whole === 0n ? -0 : -whole) : whole;
    const text = formatter.formatToParts(signedWhole).map(part => part.type === "fraction" ? fraction.padEnd(digits, "0") : part.value).join("");
    return currency.length === 3 ? text : `${text}\u00a0${currency}`;
  }
  function payout(amount, units, scale = 100) {
    requireThat(natural(amount) && natural(units) && Number.isSafeInteger(scale) && scale > 0);
    const value = BigInt(amount) * BigInt(units) / BigInt(scale);
    requireThat(value <= BigInt(Number.MAX_SAFE_INTEGER), "rgs_amount_overflow");
    return Number(value);
  }
  function language(value, fallback = "en") {
    const normalized = typeof value === "string" ? value.trim().replace(/_/g, "-").toLowerCase() : "";
    const base = normalized.split("-")[0];
    return /^(pl|en|de)(?:-[a-z0-9]{2,8})*$/.test(normalized) ? base : fallback;
  }
  function launch(href) {
    const page = new URL(href), params = page.searchParams;
    const replay = params.get("replay") === "true";
    if (!replay && !params.has("sessionID") && !params.has("rgs_url")) return null;
    const sessionID = params.get("sessionID"), host = params.get("rgs_url");
    if ((!replay && (!sessionID || sessionID.length > 4096)) || !host || host !== host.trim() || /[\s/@?#\\]/.test(host)) throw failure("rgs_invalid_launch", 400);
    let endpoint;
    try { endpoint = new URL(`https://${host}`); } catch { throw failure("rgs_invalid_launch", 400); }
    if (endpoint.username || endpoint.password || endpoint.pathname !== "/" || endpoint.search || endpoint.hash) throw failure("rgs_invalid_launch", 400);
    // Plain HTTP is exclusively for a loopback test server serving this very page.
    if (page.protocol === "http:" && ["127.0.0.1", "localhost", "[::1]"].includes(page.hostname) && page.host === endpoint.host) endpoint.protocol = "http:";
    if (replay) {
      const game = params.get("game"), version = params.get("version"), mode = params.get("mode"), event = params.get("event");
      const segment = value => typeof value === "string" && /^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/.test(value);
      if (!["replay", "game", "version", "mode", "event", "rgs_url"].every(key => params.getAll(key).length === 1) || !/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(game || "") || !segment(version) || !segment(event) || mode !== "base") throw failure("rgs_invalid_replay", 400);
      const rawAmount = params.get("amount"), amount = /^\d+$/.test(rawAmount || "") ? Number(rawAmount) : NaN;
      const currency = params.get("currency");
      return { replay: true, origin: endpoint.origin, game, version, mode, event,
        amount: natural(amount) && amount > 0 ? amount : SCALE,
        currency: /^[A-Z]{3,8}$/.test(currency || "") && !["SC", "GC", "XSC", "XGC"].includes(currency) ? currency : "USD",
        lang: language(params.get("lang")),
        device: params.get("device") === "mobile" ? "mobile" : "desktop",
        social: params.get("social") === "true", demo: params.get("demo") === "true" };
    }
    if (params.get("social") === "true") throw failure("rgs_social_unavailable", 400);
    return { sessionID, origin: endpoint.origin, lang: language(params.get("lang")), demo: params.get("demo") === "true" };
  }
  async function loadReplay(options, gameConfig, dependencies = {}) {
    requireThat(options?.replay === true && options.mode === "base" && natural(options.amount) && options.amount > 0, "rgs_invalid_replay");
    requireThat(["0.5.0-any-start", "0.6.0-high-wins"].includes(gameConfig?.math_version) && gameConfig.payout_scale === 100, "rgs_incompatible_math");
    const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 15000);
    try {
      const fetchReplay = dependencies.fetch || window.fetch.bind(window);
      const path = [options.game, options.version, options.mode, options.event].map(encodeURIComponent).join("/");
      const response = await fetchReplay(options.origin + "/bet/replay/" + path, {
        method: "GET", signal: controller.signal, cache: "no-store", credentials: "omit", referrerPolicy: "no-referrer"
      });
      // An unknown event can return a plain 404 with no JSON body.
      if (!response.ok) throw failure(response.status === 404 ? "rgs_replay_not_found" : "rgs_replay_failed", response.status);
      let body;
      try { body = await response.json(); } catch { throw failure("rgs_invalid_replay"); }
      const events = body?.state;
      requireThat(body && Number.isFinite(body.payoutMultiplier) && body.payoutMultiplier >= 0 && body.costMultiplier === 1 && Array.isArray(events) && events.length === 1 && events[0]?.index === 0 && events[0]?.type === "roundResult" && events[0]?.data, "rgs_invalid_replay");
      const round = clone(events[0].data);
      requireThat(natural(round.payout_units) && round.payout_units <= gameConfig.max_win_units && body.payoutMultiplier === round.payout_units / gameConfig.payout_scale, "rgs_payout_mismatch");
      const win = payout(options.amount, round.payout_units, gameConfig.payout_scale);
      const id = "replay:" + [options.game, options.version, options.mode, options.event].join(":");
      return {
        config: { ...gameConfig, amount_scale: SCALE, currency: options.currency, default_bet_cents: options.amount, bet_options_cents: [options.amount] },
        result: { session_id: "replay", request_id: id, round_id: id, math_version: gameConfig.math_version,
          mode: "random", is_scenario: false, bet_cents: options.amount, win_cents: win,
          balance_cents: 0, balance_before_cents: 0, stats: { rounds: 0, total_bet_cents: 0, total_win_cents: 0 },
          round, replay: true }
      };
    } catch (error) {
      if (!error.code) throw failure("rgs_replay_failed");
      throw error;
    } finally { clearTimeout(timer); }
  }
  class Client {
    constructor(options, dependencies = {}) {
      this.options = options;
      this.fetch = dependencies.fetch || window.fetch.bind(window);
      this.storage = dependencies.storage || window.sessionStorage;
      this.crypto = dependencies.crypto || window.crypto;
      this.authenticated = false; this.pending = null; this.lastRound = null;
      this.stats = { rounds: 0, total_bet_cents: 0, total_win_cents: 0 };
      this.inFlight = false;
    }
    async post(path, data = {}) {
      const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 15000);
      try {
        const response = await this.fetch(this.options.origin + path, {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...data, sessionID: this.options.sessionID }),
          signal: controller.signal, cache: "no-store", credentials: "omit", referrerPolicy: "no-referrer"
        });
        let body;
        try { body = await response.json(); } catch { throw failure("rgs_invalid_response", undefined, true); }
        if (!response.ok) {
          const code = body?.error || body?.code;
          if (code === "ERR_IPB") throw failure("insufficient_funds", response.status);
          if (code === "ERR_IS" || response.status === 401) throw failure("session_expired", response.status);
          throw failure(code === "ERR_VAL" ? "rgs_rejected" : "rgs_request_failed", response.status, response.status >= 500 || [408, 429].includes(response.status));
        }
        requireThat(body && typeof body === "object"); return body;
      } catch (error) {
        if (!error.code) throw failure("rgs_connection_failed", undefined, true);
        throw error;
      } finally { clearTimeout(timer); }
    }
    balanceFrom(data) {
      const balance = data?.balance;
      requireThat(balance && natural(balance.amount));
      validateCurrency(balance.currency);
      if (this.currency && balance.currency !== this.currency) {
        this.authenticated = false;
        throw failure("rgs_currency_changed", undefined, true);
      }
      this.currency = balance.currency; this.balance = balance.amount;
      this.balanceVersion = (this.balanceVersion || 0) + 1; return balance;
    }
    persist() {
      // The session token is never written to storage, history or exported results.
      try { this.storage.setItem(this.storageKey, JSON.stringify({ pending: this.pending, stats: this.stats, lastBetID: this.lastBetID, currency: this.currency })); }
      catch { /* Live recovery still uses authenticate; do not stop a settled round for storage failure. */ }
    }
    roundID(round) {
      requireThat(round && ((typeof round.betID === "string" && round.betID.length > 0) || natural(round.betID)) && typeof round.active === "boolean", "rgs_invalid_round");
      return String(round.betID);
    }
    async authenticate() {
      const data = await this.post("/wallet/authenticate");
      this.balanceFrom(data);
      const config = data.config;
      requireThat(config && [config.minBet, config.maxBet, config.stepBet, config.defaultBetLevel].every(value => natural(value) && value > 0) && config.maxBet >= config.minBet);
      requireThat(Array.isArray(config.betLevels) && config.betLevels.length > 0 && config.betLevels.length <= 10000 && new Set(config.betLevels).size === config.betLevels.length);
      requireThat(config.betLevels.every(value => natural(value) && value >= config.minBet && value <= config.maxBet && value % config.stepBet === 0) && config.betLevels.includes(config.defaultBetLevel));
      requireThat(config.betLevels.includes(config.minBet) && config.betLevels.includes(config.maxBet), "rgs_invalid_bet_config");
      if (config.jurisdiction?.socialCasino || data.jurisdictionFlags?.socialCasino) {
        this.authenticated = false;
        throw failure("rgs_social_unavailable", 400);
      }
      this.remoteConfig = clone(config); this.levels = [...config.betLevels].sort((a, b) => a - b);
      if (data.round != null) this.roundID(data.round);
      this.lastRound = data.round || null; this.authenticated = true;
      return data;
    }
    wallet() { return { session_id: this.sessionLabel, balance_cents: this.balance, ...this.stats }; }
    configuration() {
      return { ...this.gameConfig, bet_options_cents: [...this.levels], default_bet_cents: this.remoteConfig.defaultBetLevel,
        min_bet_cents: this.remoteConfig.minBet, max_bet_cents: this.remoteConfig.maxBet, bet_step_cents: this.remoteConfig.stepBet,
        amount_scale: SCALE, currency: this.currency };
    }
    progress(result, ...candidates) {
      let best = { round_id: result.round_id, baseComplete: false, freeCompleted: 0 };
      for (const value of candidates) {
        if (!value || value.round_id !== result.round_id || typeof value.baseComplete !== "boolean" || !natural(value.freeCompleted) || value.freeCompleted > result.round.free_spins.length || (!value.baseComplete && value.freeCompleted)) continue;
        if (Number(value.baseComplete) + value.freeCompleted > Number(best.baseComplete) + best.freeCompleted) best = { round_id: result.round_id, baseComplete: value.baseComplete, freeCompleted: value.freeCompleted };
      }
      return best;
    }
    remoteProgress(remote, result) {
      try {
        if (typeof remote?.event !== "string" || remote.event.length > 2048) return null;
        const event = JSON.parse(remote.event);
        if (event.game !== "polska-gurom" || event.v !== 1 || event.math !== this.gameConfig.math_version) return null;
        return this.progress(result, event);
      } catch { return null; }
    }
    normalize(remote, request) {
      const id = this.roundID(remote);
      requireThat(remote.mode === "base" && natural(remote.amount) && remote.amount > 0 && remote.amount === request.bet_cents, "rgs_round_mismatch");
      const events = remote.state;
      requireThat(Array.isArray(events) && events.length === 1 && events[0]?.index === 0 && events[0]?.type === "roundResult" && events[0]?.data, "rgs_incompatible_math");
      const round = clone(events[0].data), win = payout(remote.amount, round.payout_units, this.gameConfig.payout_scale);
      if (remote.payout !== undefined) requireThat(remote.payout === win, "rgs_payout_mismatch");
      requireThat(!remote.active || win > 0, "rgs_invalid_round");
      const stats = { rounds: this.stats.rounds + 1, total_bet_cents: this.stats.total_bet_cents + remote.amount, total_win_cents: this.stats.total_win_cents + win };
      requireThat(Object.values(stats).every(natural));
      return { request_id: request.request_id, round_id: id, session_id: this.sessionLabel,
        math_version: this.gameConfig.math_version, mode: "random", is_scenario: false,
        bet_cents: remote.amount, win_cents: win, balance_cents: this.balance,
        balance_before_cents: this.balance + remote.amount - (remote.active ? 0 : win),
        created_at: new Date().toISOString(), stats, round, rgs: true, rgs_active: remote.active };
    }
    async boot(gameConfig) {
      this.gameConfig = gameConfig;
      requireThat(["0.5.0-any-start", "0.6.0-high-wins"].includes(gameConfig?.math_version) && gameConfig.payout_scale === 100, "rgs_incompatible_math");
      const digest = await this.crypto.subtle.digest("SHA-256", new TextEncoder().encode(this.options.origin + "\n" + this.options.sessionID));
      this.sessionLabel = "rgs-" + [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, "0")).join("");
      this.storageKey = "pg-rgs-" + this.sessionLabel;
      try {
        const saved = JSON.parse(this.storage.getItem(this.storageKey) || "null");
        if (saved?.currency !== undefined) { validateCurrency(saved.currency); this.currency = saved.currency; }
        if (saved?.pending) this.pending = saved.pending;
        if (saved?.stats && Object.values(saved.stats).length === 3 && Object.values(saved.stats).every(natural)) this.stats = saved.stats;
        this.lastBetID = saved?.lastBetID;
      } catch { throw failure("rgs_recovery_required", undefined, true); }
      await this.authenticate();
      if (this.pending) await this.recover();
      else if (this.lastRound?.active) {
        const request = { mode: "random", bet_cents: this.lastRound.amount, request_id: this.crypto.randomUUID() };
        this.pending = { request, baseline: null, phase: "presenting", result: this.normalize(this.lastRound, request) };
        this.pending.presentation = this.progress(this.pending.result, this.remoteProgress(this.lastRound, this.pending.result));
        this.persist();
      }
      this.lastBetID = this.lastRound ? this.roundID(this.lastRound) : this.lastBetID;
      this.persist();
      return { config: this.configuration(), wallet: this.wallet(), pending: this.pending };
    }
    async recover() {
      const pending = this.pending, remote = this.lastRound;
      requireThat(pending && pending.request && typeof pending.request.request_id === "string", "rgs_recovery_required");
      if (pending.result) {
        if (remote?.active) {
          requireThat(this.roundID(remote) === pending.result.round_id, "rgs_other_active_round");
          const authoritative = this.normalize(remote, pending.request);
          requireThat(canonical(authoritative.round) === canonical(pending.result.round) && authoritative.win_cents === pending.result.win_cents, "rgs_round_mismatch");
        }
        else if (pending.phase === "settling" || pending.phase === "settled") pending.phase = "settled";
        else if (pending.result.rgs_active) requireThat(remote && this.roundID(remote) === pending.result.round_id, "rgs_recovery_required");
        if (remote && this.roundID(remote) === pending.result.round_id) pending.result.rgs_active = remote.active;
        if (pending.phase === "settled") pending.result.rgs_active = false;
        pending.result.balance_cents = this.balance;
        pending.result.balance_before_cents = this.balance + pending.result.bet_cents - (pending.result.rgs_active ? 0 : pending.result.win_cents);
        pending.presentation = this.progress(pending.result, pending.presentation, this.remoteProgress(remote, pending.result));
        this.persist(); return;
      }
      // RGS has no documented idempotency key. Never resend an uncertain play.
      requireThat(remote && this.roundID(remote) !== pending.baseline, "rgs_recovery_required");
      pending.result = this.normalize(remote, pending.request); pending.phase = "presenting"; this.persist();
      pending.presentation = this.progress(pending.result, this.remoteProgress(remote, pending.result)); this.persist();
    }
    async play(request) {
      if (!this.authenticated) throw failure("session_expired", 401);
      if (this.inFlight) throw failure("rgs_request_in_progress", undefined, true);
      this.inFlight = true;
      try {
        if (this.pending) {
          requireThat(this.pending.request.request_id === request.request_id && this.pending.request.bet_cents === request.bet_cents, "rgs_recovery_required");
          try { await this.authenticate(); await this.recover(); }
          catch (error) { error.uncertain = true; throw error; }
          return clone(this.pending.result);
        }
        if (this.lastRound?.active) throw failure("rgs_other_active_round", undefined, true);
        if (request.mode !== "random" || !this.levels.includes(request.bet_cents)) throw failure("rgs_invalid_bet", 400);
        this.pending = { request: clone(request), baseline: this.lastBetID ?? null, phase: "play_sent" };
        this.persist();
        let data;
        try { data = await this.post("/wallet/play", { amount: request.bet_cents, mode: "base" }); }
        catch (error) {
          if (!error.uncertain) { this.pending = null; this.persist(); }
          throw error;
        }
        this.balanceFrom(data); this.lastRound = data.round;
        this.pending.result = this.normalize(data.round, request); this.pending.phase = "presenting";
        this.lastBetID = this.roundID(data.round); this.persist();
        return clone(this.pending.result);
      } finally { this.inFlight = false; }
    }
    async checkpoint(value) {
      if (this.inFlight) throw failure("rgs_request_in_progress", undefined, true);
      this.inFlight = true;
      try {
        requireThat(this.pending?.result?.round_id === value?.round_id, "rgs_recovery_required");
        const pending = this.pending;
        pending.presentation = this.progress(pending.result, pending.presentation, value); this.persist();
        if (!pending.result.rgs_active || pending.phase === "settled") return;
        const event = JSON.stringify({ v: 1, game: "polska-gurom", math: this.gameConfig.math_version, ...pending.presentation });
        if (pending.acknowledgedEvent === event) return;
        const response = await this.post("/bet/event", { event });
        requireThat(response.event === event, "rgs_progress_unconfirmed");
        pending.acknowledgedEvent = event; this.persist();
      } catch (error) { error.uncertain = true; throw error; }
      finally { this.inFlight = false; }
    }
    async finish(result) {
      if (this.inFlight) throw failure("rgs_request_in_progress", undefined, true);
      this.inFlight = true;
      try {
      requireThat(this.pending?.result?.round_id === result.round_id, "rgs_recovery_required");
      if (this.pending.result.rgs_active && this.pending.phase !== "settled") {
        // Check identity before a session-scoped end-round, especially after reload/retry.
        await this.authenticate(); await this.recover();
        if (this.pending.result.rgs_active && this.pending.phase !== "settled") {
          this.pending.phase = "settling"; this.persist();
          const settled = await this.post("/wallet/end-round"); this.balanceFrom(settled);
          this.pending.phase = "settled"; this.pending.result.rgs_active = false; this.persist();
        }
      }
      this.stats = clone(result.stats); this.lastBetID = result.round_id; this.lastRound = null;
      this.pending = null; this.persist(); return this.wallet();
      } catch (error) { error.uncertain = true; throw error; }
      finally { this.inFlight = false; }
    }
    async readWallet() {
      if (!this.authenticated) throw failure("session_expired", 401);
      const version = this.balanceVersion, data = await this.post("/wallet/balance");
      if (version === this.balanceVersion) this.balanceFrom(data);
      return this.wallet();
    }
  }
  window.PG_RGS = Object.freeze({ launch, language, loadReplay, Client, payout, formatAmount, SCALE });
})();
