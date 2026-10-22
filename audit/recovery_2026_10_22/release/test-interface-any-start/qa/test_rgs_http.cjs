"use strict";
const vm = require("node:vm"), fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto"), assert = require("node:assert/strict");
const ctx = { window: {}, URL, TextEncoder, AbortController, setTimeout, clearTimeout };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../web/rgs-client.js"), "utf8"), ctx);
async function main() {
  const origin = process.argv[2], fault = process.argv[3] || "none";
  const url = `${origin}/?sessionID=local-test-session&rgs_url=${new URL(origin).host}&demo=true&lang=en`;
  const memory = new Map(), client = new ctx.window.PG_RGS.Client(ctx.window.PG_RGS.launch(url), {
    fetch, crypto: crypto.webcrypto, storage: { getItem: key => memory.get(key) || null, setItem: (key, value) => memory.set(key, value) }
  });
  const config = await (await fetch(origin + "/game-config.json")).json();
  const boot = await client.boot(config), req = { request_id: crypto.randomUUID(), bet_cents: boot.config.default_bet_cents, mode: "random" };
  let result;
  if (fault === "play") {
    await assert.rejects(client.play(req)); result = await client.play(req);
  } else result = await client.play(req);
  let wallet;
  if (fault === "end") {
    await assert.rejects(client.finish(result)); result = await client.play(req); wallet = await client.finish(result);
  } else wallet = await client.finish(result);
  const state = await (await fetch(origin + "/__rgs-test/state")).json();
  assert.equal(state.charges, 1); assert.equal(state.active, false);
  assert.equal(state.settlements, result.win_cents > 0 ? 1 : 0); assert.equal(wallet.balance_cents, state.balance.amount);
  assert.equal(state.calls[0], "/wallet/authenticate"); assert.equal(state.calls.filter(p => p === "/wallet/play").length, 1);
  console.log(JSON.stringify({ passed: true, fault, charges: state.charges, settlements: state.settlements, balance: state.balance.amount }));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
