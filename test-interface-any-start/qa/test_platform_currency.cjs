"use strict";
// Contract and application regressions; the DOM probe does not claim visual or live-platform QA.
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path"), vm = require("node:vm"), crypto = require("node:crypto");
const { RgsMock, fixtures } = require("./rgs_mock.cjs");
const { harness } = require("./test_autoplay.cjs");
const context = { window: {}, URL, TextEncoder, AbortController, setTimeout, clearTimeout, Intl };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../web/rgs-client.js"), "utf8"), context);
const RGS = context.window.PG_RGS;
const href = "http://127.0.0.1:8800/?sessionID=local-test-session&rgs_url=127.0.0.1%3A8800&demo=true&lang=pl";
const checks = [];
async function check(name, work) {
  try { await work(); checks.push({ name, passed: true }); console.log("PASS " + name); }
  catch (error) { checks.push({ name, passed: false, error: error.stack }); console.error("FAIL " + name + ": " + error.stack); }
}
function client(mock = new RgsMock(), launchHref = href, storage = new Map()) {
  return new RGS.Client(RGS.launch(launchHref), {
    fetch: mock.fetch, crypto: crypto.webcrypto,
    storage: { getItem: key => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value) }
  });
}
async function ui(mock = new RgsMock(), options = {}) {
  const h = harness({ rgs: true, boot: true, href: options.href || href, fetch: mock.fetch,
    sessionStorage: options.storage, localStorage: options.preferences });
  await h.app.init();
  assert.equal(h.state.online, true, h.ids["win-detail"].textContent);
  return h;
}
async function spin(h) { const work = h.app.spin(); await h.finished(); await work; }
const digits = value => value.replace(/[^\d.,-]/g, "").replace(/,/g, "");
const formats = [
  [500000, "USD", "0.50"], [1, "USD", "0.000001"], [1234567, "MXN", "1.234567"],
  [1000000, "JPY", "1"], [500000, "JPY", "0.5"], [1, "JPY", "0.000001"],
  [500000, "KWD", "0.500"], [1234567, "KWD", "1.234567"],
  [1, "BTC", "0.000001"], [1, "USDT", "0.000001"], [1234567, "DOGE", "1.234567"],
  [-1, "USD", "-0.000001"], [0, "USD", "0.00"], [0, "JPY", "0"],
  [Number.MAX_SAFE_INTEGER, "USD", "9007199254.740991"],
  [-Number.MAX_SAFE_INTEGER, "USD", "-9007199254.740991"]
];
async function main() {
  for (const [amount, currency, expected] of formats) await check(`Exact display ${amount} micro-units in ${currency}`, () => {
    const formatted = RGS.formatAmount(amount, currency);
    assert.ok(formatted.includes(currency), formatted);
    assert.ok(!formatted.includes("$"), formatted);
    assert.equal(digits(formatted), expected);
  });
  await check("Polish and German display retain every authenticated fractional unit", () => {
    for (const locale of ["pl-PL", "de-DE"]) {
      const formatted = RGS.formatAmount(1234567, "USD", locale);
      assert.ok(formatted.includes("1,234567"), formatted);
      assert.ok(formatted.includes("USD"), formatted);
    }
  });
  await check("Fractional, non-finite and unsafe micro-unit values are rejected", () => {
    for (const amount of [1.5, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
      assert.throws(() => RGS.formatAmount(amount, "USD"), error => error.code === "rgs_amount_overflow");
    }
  });
  await check("Every fiat currency in the official Stake Engine client can display exact micro-units", () => {
    // https://raw.githubusercontent.com/engineio/ts-client/main/src/types.ts — checked 2026-10-22.
    const currencies = ["USD", "CAD", "JPY", "EUR", "RUB", "CNY", "PHP", "INR", "IDR", "KRW", "BRL", "MXN", "DKK", "PLN", "VND", "TRY", "CLP", "ARS", "PEN", "NGN", "SAR", "ILS", "AED", "TWD", "NOK", "KWD", "JOD", "CRC", "TND", "SGD", "MYR", "OMR", "QAR", "BHD"];
    for (const currency of currencies) for (const amount of [1, 1234567]) {
      const formatted = RGS.formatAmount(amount, currency);
      assert.ok(formatted.includes(currency), formatted);
      assert.equal(digits(formatted), amount === 1 ? "0.000001" : "1.234567");
    }
  });
  await check("Authoritative currency overrides the optional URL currency hint", async () => {
    const app = client(new RgsMock({ currency: "MXN" }), href + "&currency=EUR");
    const boot = await app.boot(fixtures.config);
    assert.equal(boot.config.currency, "MXN");
  });
  for (const currency of ["USD", "EUR", "PLN", "JPY", "KWD", "MXN", "BTC", "USDT", "DOGE"]) {
    await check(`UI ${currency}: exact balance, bet, win and history use the same platform denomination`, async () => {
      const mock = new RgsMock({ currency });
      mock.config = { ...mock.config, minBet: 1, stepBet: 1, defaultBetLevel: 1234567,
        betLevels: [2000000, 1, 1234567, 500000] };
      mock.balance = 100123457;
      const h = await ui(mock); h.state.instant = true;
      const expectedBet = RGS.formatAmount(1234567, currency, "pl-PL");
      assert.equal(h.ids["bet-value"].textContent, expectedBet);
      assert.equal(h.ids["meter-bet"].textContent, expectedBet);
      assert.equal(h.ids["balance-value"].textContent, RGS.formatAmount(mock.balance, currency, "pl-PL"));
      assert.equal(h.ids["meter-balance"].textContent, h.ids["balance-value"].textContent);
      await spin(h);
      assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1);
      const record = h.state.history[0];
      assert.equal(record.bet_cents, 1234567);
      assert.equal(h.state.balance, mock.balance);
      assert.equal(h.ids["balance-value"].textContent, RGS.formatAmount(mock.balance, currency, "pl-PL"));
      assert.equal(h.ids["meter-balance"].textContent, h.ids["balance-value"].textContent);
      const expectedWin = RGS.formatAmount(record.win_cents, currency, "pl-PL");
      assert.equal(h.ids["total-win-value"].textContent, expectedWin);
      assert.equal(h.ids["meter-win"].textContent, expectedWin);
      const history = h.ids["history-list"].textContent;
      assert.ok(history.includes(expectedBet), history); assert.ok(history.includes(expectedWin), history);
      assert.equal(h.errors.length, 0);
      const play = mock.calls.find(call => call.path === "/wallet/play");
      assert.equal(play.body.amount, 1234567); assert.equal(play.body.mode, "base");
    });
  }
  await check("Irregular platform levels are sorted, defaulted and bounded without inventing intermediate stakes", async () => {
    const mock = new RgsMock();
    mock.config = { ...mock.config, minBet: 10, stepBet: 10, defaultBetLevel: 123450,
      betLevels: [2000000, 10, 500000, 123450] };
    const h = await ui(mock);
    assert.deepEqual([...h.state.config.bet_options_cents], [10, 123450, 500000, 2000000]);
    assert.equal(h.state.config.min_bet_cents, 10);
    assert.equal(h.state.config.max_bet_cents, 2000000);
    assert.equal(h.state.config.bet_step_cents, 10);
    assert.equal(h.state.bet, 123450);
    h.ids["bet-decrease"].click(); assert.equal(h.state.bet, 10);
    assert.equal(h.ids["bet-decrease"].disabled, true);
    h.ids["bet-increase"].click(); assert.equal(h.state.bet, 123450);
    h.ids["bet-increase"].click(); assert.equal(h.state.bet, 500000);
    h.ids["bet-increase"].click(); assert.equal(h.state.bet, 2000000);
    assert.equal(h.ids["bet-increase"].disabled, true);
    h.state.instant = true; await spin(h);
    assert.equal(mock.calls.find(call => call.path === "/wallet/play").body.amount, 2000000);
  });
  for (const limit of ["minBet", "maxBet"]) await check(`Configured ${limit} missing from the permitted levels blocks play`, async () => {
    const mock = new RgsMock(); mock.config.betLevels = mock.config.betLevels.filter(value => value !== mock.config[limit]);
    await assert.rejects(client(mock).boot(fixtures.config));
    assert.equal(mock.charges, 0);
  });
  await check("A non-platform stake is rejected before sending a debit request", async () => {
    const mock = new RgsMock(), app = client(mock); await app.boot(fixtures.config);
    await assert.rejects(app.play({ bet_cents: 12345, mode: "random", request_id: crypto.randomUUID() }), error => error.code === "rgs_invalid_bet");
    assert.equal(mock.calls.filter(call => call.path === "/wallet/play").length, 0);
  });
  await check("Stake preferences are isolated by platform session and authenticated currency", async () => {
    const mock = new RgsMock(), preferences = new Map([["pg-bet-cents", "1000"]]);
    const h = await ui(mock, { preferences }); h.ids["bet-increase"].click();
    assert.equal(h.state.bet, 2000000);
    const usdKey = `pg-rgs-bet-${h.state.rgs.sessionLabel}-USD`;
    assert.equal(preferences.get(usdKey), "2000000");
    const reload = await ui(mock, { preferences, storage: h.storage });
    assert.equal(reload.state.bet, 2000000);
    mock.currency = "EUR";
    const euro = await ui(mock, { preferences });
    assert.equal(euro.state.bet, mock.config.defaultBetLevel);
    assert.equal(preferences.get(usdKey), "2000000");
    assert.equal(preferences.get("pg-bet-cents"), "1000");
    const sessionPreferences = new Map([[`pg-rgs-bet-other-session-USD`, "2000000"]]);
    const other = await ui(new RgsMock(), { preferences: sessionPreferences });
    assert.equal(other.state.bet, other.state.config.default_bet_cents);
  });
  await check("An obsolete saved stake falls back to the new authoritative default", async () => {
    const mock = new RgsMock(), preferences = new Map(), h = await ui(mock, { preferences });
    h.ids["bet-increase"].click(); assert.equal(h.state.bet, 2000000);
    mock.config.betLevels = [10000, 100000, 500000]; mock.config.maxBet = 500000;
    const reload = await ui(mock, { preferences, storage: h.storage });
    assert.equal(reload.state.bet, mock.config.defaultBetLevel);
  });
  for (const interrupted of [false, true]) await check(`Updated platform levels reach the UI after ${interrupted ? "recovery" : "settlement"} and replace an unavailable stake`, async () => {
    const mock = new RgsMock(), original = mock.fetch;
    const updated = { ...mock.config, defaultBetLevel: 100000, betLevels: [2000000, 10000, 100000] };
    mock.fetch = async (url, init) => {
      try { return await original(url, init); }
      finally { if (url.endsWith("/wallet/play")) mock.config = updated; }
    };
    const h = await ui(mock); h.state.instant = true;
    if (interrupted) mock.failNext("/wallet/play", "lost-response");
    await spin(h);
    if (interrupted) { assert.ok(h.state.pending); await spin(h); }
    assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1);
    assert.equal(h.state.pending, null); assert.equal(h.state.history[0].bet_cents, 500000);
    assert.deepEqual([...h.state.config.bet_options_cents], [10000, 100000, 2000000]);
    assert.deepEqual([...h.state.rgs.configuration().bet_options_cents], [10000, 100000, 2000000]);
    assert.equal(h.state.config.default_bet_cents, 100000); assert.equal(h.state.bet, 100000);
    assert.equal(h.ids["bet-value"].textContent, RGS.formatAmount(100000, "USD", "pl-PL"));
    assert.equal(h.ids["meter-bet"].textContent, h.ids["bet-value"].textContent);
    assert.equal(mock.calls.filter(call => call.path === "/wallet/play").length, 1);
    assert.equal(h.state.balance, mock.balance);
  });
  await check("Autoplay stops after its accepted round when authentication removes the chosen stake", async () => {
    const mock = new RgsMock(), original = mock.fetch;
    mock.fetch = async (url, init) => {
      const response = await original(url, init);
      if (url.endsWith("/wallet/play")) mock.config = { ...mock.config, defaultBetLevel: 100000, betLevels: [10000, 100000, 2000000] };
      return response;
    };
    const h = await ui(mock); h.state.instant = true; h.start(); await h.finished();
    assert.equal(mock.charges, 1); assert.equal(mock.settlements, 1);
    assert.equal(h.state.auto, 0); assert.equal(h.state.autoCompleted, 1);
    assert.equal(h.state.bet, 100000); assert.equal(h.state.pending, null);
    await h.clock.drain();
    assert.equal(mock.calls.filter(call => call.path === "/wallet/play").length, 1);
  });
  for (const language of ["pl", "en", "de"]) await check(`RGS rules in ${language} remove the local PLN wallet paragraph and retain the cap rule`, async () => {
    const h = await ui(new RgsMock(), { href: href.replace("lang=pl", "lang=" + language) });
    const rules = h.ids["rules-content"].children.map(node => node.textContent);
    assert.ok(rules.length >= 8);
    assert.ok(!rules.some(text => /PLN|10[ ,.]000|10 000|zł|whole-PLN|całkowitymi kwotami|walletRule|local server|lokalnego serwera|lokalen Servers/.test(text)), rules.join("\n"));
    const platformPhrases = { pl: "Saldo, dozwolone stawki i rozliczenie pochodzą z serwera platformy.", en: "Balance, available bets and settlement come from the platform server.", de: "Guthaben, verfügbare Einsätze und Abrechnung stammen vom Plattformserver." };
    assert.ok(rules.some(text => text.includes(platformPhrases[language])), rules.join("\n"));
    const capPhrases = { pl: "Limit 5000× dotyczy całej rundy razem z bonusem", en: "The 5000× cap applies to the complete paid round including its bonus", de: "Das Limit 5000× gilt für die gesamte bezahlte Runde einschließlich Bonus" };
    assert.ok(rules.some(text => text.includes(capPhrases[language])), rules.join("\n"));
    assert.equal(h.ids["test-mode-select"].disabled, true); assert.equal(h.ids["reset-button"].disabled, true);
  });
  await check("A wallet currency change during a session blocks the update", async () => {
    const mock = new RgsMock(), app = client(mock); await app.boot(fixtures.config);
    const before = app.balance; mock.currency = "EUR"; mock.balance++;
    await assert.rejects(app.readWallet(), error => error.code === "rgs_currency_changed");
    assert.equal(app.currency, "USD"); assert.equal(app.balance, before); assert.equal(mock.charges, 0);
    assert.equal(app.authenticated, false);
    await assert.rejects(app.play({ bet_cents: 500000, mode: "random", request_id: crypto.randomUUID() }));
    assert.equal(mock.calls.filter(call => call.path === "/wallet/play").length, 0);
  });
  for (const pending of [false, true]) await check(`A persisted session currency change blocks reload with pending=${pending}`, async () => {
    const mock = new RgsMock(), storage = new Map(), app = client(mock, href, storage);
    await app.boot(fixtures.config);
    if (pending) await app.play({ bet_cents: 500000, mode: "random", request_id: crypto.randomUUID() });
    const previousState = [...storage.entries()];
    const charges = mock.charges, settlements = mock.settlements;
    mock.currency = "EUR";
    const reload = client(mock, href, storage);
    await assert.rejects(reload.boot(fixtures.config), error => error.code === "rgs_currency_changed");
    assert.equal(reload.authenticated, false); assert.equal(reload.currency, "USD");
    assert.equal(mock.charges, charges); assert.equal(mock.settlements, settlements);
    assert.deepEqual([...storage.entries()], previousState);
  });
  await check("Social launch remains explicitly unavailable in this non-social release", () => {
    assert.throws(() => RGS.launch(href + "&social=true"), error => error.code === "rgs_social_unavailable");
  });
  for (const currency of ["XSC", "XGC", "SC", "GC"]) await check(`${currency} authentication is blocked before a bet in this release`, async () => {
    const mock = new RgsMock({ currency }), app = client(mock);
    await assert.rejects(app.boot(fixtures.config), error => error.code === "rgs_social_unavailable");
    assert.equal(mock.charges, 0); assert.equal(mock.calls.filter(call => call.path === "/wallet/play").length, 0);
  });
  for (const structure of ["official jurisdictionFlags", "legacy config.jurisdiction"]) {
    for (const reauthenticate of [false, true]) await check(`Social ${structure} is blocked during ${reauthenticate ? "reauthentication" : "boot"} and prevents play`, async () => {
      const mock = new RgsMock(), app = client(mock);
      if (reauthenticate) { await app.boot(fixtures.config); assert.equal(app.authenticated, true); }
      if (structure === "official jurisdictionFlags") {
        mock.failNext("/wallet/authenticate", data => ({ ...data, jurisdictionFlags: { socialCasino: true } }));
      } else mock.config.jurisdiction.socialCasino = true;
      await assert.rejects(reauthenticate ? app.authenticate() : app.boot(fixtures.config), error => error.code === "rgs_social_unavailable");
      assert.equal(app.authenticated, false);
      await assert.rejects(app.play({ bet_cents: 500000, mode: "random", request_id: crypto.randomUUID() }));
      assert.equal(mock.charges, 0); assert.equal(mock.calls.filter(call => call.path === "/wallet/play").length, 0);
    });
  }
  const passed = checks.every(item => item.passed), out = process.env.PG_QA_OUT_DIR || __dirname;
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, "platform_currency_results.json"), JSON.stringify({ passed, total: checks.length, checks }, null, 2));
  console.log(JSON.stringify({ passed, total: checks.length, failed: checks.filter(item => !item.passed).length }));
  if (!passed) process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
