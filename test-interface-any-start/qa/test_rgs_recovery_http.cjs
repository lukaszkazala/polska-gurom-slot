"use strict";
const vm = require("node:vm"), fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto"), assert = require("node:assert/strict");
const ctx = { window: {}, URL, TextEncoder, AbortController, setTimeout, clearTimeout };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../web/rgs-client.js"), "utf8"), ctx);
async function main() {
  const origin = process.argv[2], fault = process.argv[3];
  const options = ctx.window.PG_RGS.launch(`${origin}/?sessionID=local-test-session&rgs_url=${new URL(origin).host}&demo=true&lang=pl`);
  const config = await (await fetch(origin + "/game-config.json")).json();
  const memory = new Map();
  const make = (storage = memory) => new ctx.window.PG_RGS.Client(options, { fetch, crypto: crypto.webcrypto,
    storage: { getItem: key => storage.get(key) || null, setItem: (key, value) => storage.set(key, value) } });
  let client = make(), boot;
  if (fault === "auth-before") await assert.rejects(client.boot(config));
  boot = await client.boot(config);
  const req = { request_id: crypto.randomUUID(), bet_cents: boot.config.default_bet_cents, mode: "random" };
  let result = await client.play(req);
  const marker = { round_id: result.round_id, baseComplete: true, freeCompleted: 4 };
  if (fault.startsWith("event-")) await assert.rejects(client.checkpoint(marker));
  else await client.checkpoint(marker);
  client = make(fault === "event-before" ? memory : new Map());
  boot = await client.boot(config);
  assert.equal(boot.pending.presentation.freeCompleted, 4); result = boot.pending.result;
  await client.checkpoint({ ...marker, freeCompleted: 12 });
  if (fault.startsWith("end-")) {
    await assert.rejects(client.finish(result));
    const sameStorage = client.storage;
    client = new ctx.window.PG_RGS.Client(options, { fetch, crypto: crypto.webcrypto, storage: sameStorage });
    boot = await client.boot(config); result = boot.pending.result;
    assert.equal(boot.pending.presentation.freeCompleted, 12);
  }
  const wallet = await client.finish(result), state = await (await fetch(origin + "/__rgs-test/state")).json();
  assert.equal(state.charges, 1); assert.equal(state.settlements, 1); assert.equal(state.active, false);
  assert.equal(wallet.balance_cents, state.balance.amount);
  assert.equal(state.calls.filter(p => p === "/wallet/play").length, 1);
  const endCalls = state.calls.filter(p => p === "/wallet/end-round").length;
  assert.equal(endCalls, fault === "end-before" ? 2 : 1);
  console.log(JSON.stringify({ passed: true, fault, resumed_after_free_spins: 4, charges: state.charges, settlements: state.settlements, end_calls: endCalls }));
}
main().catch(error => { console.error(error); process.exitCode = 1; });
