"use strict";
// Contract double only: tests use real exported complete-round events.
const fixtures = require("./regression_fixtures.json");
const clone = value => JSON.parse(JSON.stringify(value));
class RgsMock {
  constructor(options = {}) {
    this.options = options; this.calls = []; this.balance = 100_000_000;
    this.currency = options.currency || "USD"; this.round = null; this.serial = 0;
    this.charges = 0; this.settlements = 0; this.authenticated = false;
    this.config = { minBet: 10000, maxBet: 2000000, stepBet: 10000,
      defaultBetLevel: 500000, betLevels: [2000000, 10000, 500000, 100000], jurisdiction: { socialCasino: false } };
    this.kind = options.kind || "middle"; this.faults = new Map();
    this.fetch = this.fetch.bind(this);
  }
  body() { return { balance: { amount: this.balance, currency: this.currency } }; }
  failNext(path, fault) { this.faults.set(path, fault); }
  response(body, status = 200) { return { ok: status >= 200 && status < 300, status, json: async () => clone(body) }; }
  async fetch(url, init = {}) {
    if (url === "game-config.json") return this.response(fixtures.config);
    if (url === "assets/symbols.json") return this.response({});
    const path = new URL(url).pathname, body = JSON.parse(init.body);
    this.calls.push({ path, body, init });
    if (init.method !== "POST" || body.sessionID !== "local-test-session") return this.response({ error: "ERR_IS" }, 401);
    const fault = this.faults.get(path); this.faults.delete(path);
    if (fault === "network-before") throw new TypeError("Synthetic offline");
    if (fault === "insufficient") return this.response({ error: "ERR_IPB" }, 400);
    if (fault === "expired") return this.response({ error: "ERR_IS" }, 401);
    if (fault === "invalid") return this.response({ error: "ERR_VAL" }, 400);
    if (fault === "500") return this.response({ error: "ERR_GEN" }, 500);
    let result;
    if (path === "/wallet/authenticate") {
      this.authenticated = true;
      result = { ...this.body(), config: clone(this.config), round: this.options.nullClosed && !this.round?.active ? null : clone(this.round) };
    } else if (!this.authenticated) return this.response({ error: "ERR_IS" }, 401);
    else if (path === "/wallet/balance") result = this.body();
    else if (path === "/wallet/play") {
      if (this.round?.active || !this.config.betLevels.includes(body.amount) || body.mode !== "base") return this.response({ error: "ERR_VAL" }, 400);
      if (body.amount > this.balance) return this.response({ error: "ERR_IPB" }, 400);
      const round = clone(fixtures.rounds[this.kind]);
      const payout = Number(BigInt(body.amount) * BigInt(round.payout_units) / 100n);
      this.balance -= body.amount; this.charges++;
      this.round = { betID: ++this.serial, amount: body.amount, payout, mode: "base", active: payout > 0,
        state: [{ index: 0, type: "roundResult", data: round }] };
      result = { ...this.body(), round: clone(this.round) };
    } else if (path === "/bet/event") {
      if (!this.round?.active || typeof body.event !== "string" || body.event.length > 2048) return this.response({ error: "ERR_VAL" }, 400);
      this.round.event = body.event; result = { event: body.event };
    } else if (path === "/wallet/end-round") {
      if (!this.round?.active) return this.response({ error: "ERR_VAL" }, 400);
      this.balance += this.round.payout; this.round.active = false; this.settlements++; result = this.body();
    } else return this.response({ error: "ERR_VAL" }, 404);
    if (fault === "lost-response") throw new TypeError("Synthetic response lost after commit");
    if (fault === "bad-json") return { ok: true, status: 200, json: async () => { throw new SyntaxError("Synthetic malformed response"); } };
    if (typeof fault === "function") result = fault(result);
    return this.response(result);
  }
}
module.exports = { RgsMock, fixtures, clone };
