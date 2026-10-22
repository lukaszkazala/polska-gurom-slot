"use strict";
// Real client code in the existing deterministic DOM/API harness. Browser layout is separate QA.
const assert = require("node:assert/strict");
const fs = require("node:fs"), path = require("node:path");
const { harness, config, source } = require("./test_autoplay.cjs");
const { RgsMock, fixtures, clone } = require("./rgs_mock.cjs");

const checks = [];
const locales = { pl: "pl-PL", en: "en-GB", de: "de-DE" };
const base = "http://127.0.0.1:8800/";
const launch = "?sessionID=local-test-session&rgs_url=127.0.0.1%3A8800&demo=true";
const response = (body, status = 200) => ({ ok: status < 400, status, json: async () => body });
async function check(name, work) {
  try { const details = await work(); checks.push({ name, passed: true, ...details }); console.log("PASS " + name); }
  catch (error) { checks.push({ name, passed: false, error: error.stack }); console.error("FAIL " + name + ": " + error.message); }
}
async function initialize(h) {
  // These startup cases have no timed artwork/network faults; let native WebCrypto finish.
  await h.app.init();
}
function changeLanguage(h, lang) { h.ids["lang-select"].value = lang; h.ids["lang-select"].emit("change"); }
async function manual(h) { const pending = h.app.spin(); await h.finished(); await pending; }

async function main() {
  for (const [input, expected] of [["pl", "pl"], ["en", "en"], ["de", "de"], ["PL", "pl"], ["pl-PL", "pl"], ["en_US", "en"], ["de-DE", "de"], ["  DE  ", "de"], ["", "en"], ["fr", "en"], ["__proto__", "en"], ["constructor", "en"]]) {
    for (const platform of [false, true]) await check(`${platform ? "RGS" : "Demo"} launch lang=${JSON.stringify(input)} selects ${expected} before requests`, async () => {
      const mock = new RgsMock(), observations = [];
      let h;
      h = harness({ boot: true, rgs: platform, href: base + (platform ? launch + "&" : "?") + "lang=" + encodeURIComponent(input), localStorage: new Map([["pg-lang", expected === "pl" ? "de" : "pl"]]),
        ...(platform ? { fetch: (url, init) => { observations.push({ state: h.state.lang, html: h.document.documentElement.lang }); return mock.fetch(url, init); } }
          : { initBehavior: () => { observations.push({ state: h.state.lang, html: h.document.documentElement.lang }); } }) });
      assert.equal(h.state.lang, expected, "initial language precedes initialization");
      await initialize(h);
      assert.equal(h.state.online, true, h.ids["win-detail"].textContent);
      assert.ok(observations.length > 0);
      assert.ok(observations.every(value => value.state === expected && value.html === expected), "language and HTML lang set before every request");
      assert.equal(h.ids["lang-select"].value, expected);
      assert.equal(h.ids["rules-button"].attrs["aria-label"], h.app.words[expected].rules);
    });
  }
  for (const [saved, expected] of [["de", "de"], ["en", "en"], ["invalid", "pl"], ["constructor", "pl"], [null, "pl"]]) await check(`Demo without lang uses saved ${saved} as ${expected}`, async () => {
    const h = harness({ boot: true, localStorage: new Map(saved ? [["pg-lang", saved]] : []) });
    await initialize(h); assert.equal(h.state.lang, expected); assert.equal(h.document.documentElement.lang, expected);
  });
  await check("RGS without lang defaults to English despite saved Polish", async () => {
    const mock = new RgsMock();
    const h = harness({ boot: true, rgs: true, href: base + launch, fetch: mock.fetch, localStorage: new Map([["pg-lang", "pl"]]) });
    await initialize(h); assert.equal(h.state.lang, "en"); assert.equal(h.document.documentElement.lang, "en");
  });
  for (const href of [base + "?sessionID=x&lang=de", base + "?rgs_url=rgs.test&lang=en", base + "?sessionID=x&rgs_url=bad.test/path&lang=de", base + launch + "&social=true&lang=en", base + launch + "&replay=true&lang=de"]) await check("Invalid or unsupported launch keeps its language: " + new URL(href).searchParams.get("lang"), async () => {
    const lang = new URL(href).searchParams.get("lang");
    const h = harness({ boot: true, rgs: true, href, localStorage: new Map([["pg-lang", "pl"]]) });
    await initialize(h);
    assert.equal(h.state.online, false); assert.equal(h.state.lang, lang); assert.equal(h.document.documentElement.lang, lang);
    assert.equal(h.ids["rules-button"].attrs["aria-label"], h.app.words[lang].rules);
    assert.ok(h.ids["win-detail"].textContent.length > 10);
    assert.ok(!/Nie udało|Uruchom|rgs_|ERR_|sessionID|local-test-session/.test(h.ids["win-detail"].textContent));
    assert.equal(h.ids["spin-button"].disabled, true);
  });
  for (const platform of [false, true]) await check(`${platform ? "RGS" : "Demo"} reconnect retains manually selected language`, async () => {
    const mock = new RgsMock();
    const h = harness({ boot: true, rgs: platform, href: base + (platform ? launch + "&lang=pl" : "?lang=pl"), ...(platform ? { fetch: mock.fetch } : {}) });
    await initialize(h); changeLanguage(h, "de"); await initialize(h);
    assert.equal(h.state.lang, "de"); assert.equal(h.document.documentElement.lang, "de"); assert.equal(h.preferences.get("pg-lang"), "de");
  });

  for (const lang of Object.keys(locales)) await check(`Complete UI dictionaries and DOM translation keys in ${lang}`, async () => {
    const mock = new RgsMock();
    const h = harness({ boot: true, rgs: true, href: base + launch + "&lang=" + lang, fetch: mock.fetch });
    await initialize(h);
    const html = fs.readFileSync(path.join(__dirname, "../web/index.html"), "utf8");
    const keys = new Set([...Object.values(h.app.words).flatMap(dictionary => Object.keys(dictionary)), ...[...html.matchAll(/data-i18n(?:-[\w-]+)?="([^"]+)"/g)].map(match => match[1]), ...[...source.matchAll(/\bt\("([^"]+)"\)/g)].map(match => match[1])]);
    for (const key of keys) {
      assert.ok(Object.hasOwn(h.app.words[lang], key), `${lang}: missing ${key}`);
      assert.ok(h.app.words[lang][key]?.length, `${lang}: empty ${key}`);
    }
    const rules = h.ids["rules-content"].textContent;
    assert.ok(!/START\.cmd|10 000 zł|10,000|10\.000|whole-PLN|ganze PLN/.test(rules), "RGS rules contain no local-wallet reset instructions");
    return { translation_keys: keys.size };
  });

  for (const lang of Object.keys(locales)) for (const currency of ["PLN", "USD", "EUR", "JPY", "KWD"]) await check(`Amounts in ${lang}/${currency} retain currency precision and nonzero micro units`, () => {
    const h = harness({ boot: true, rgs: true }); h.state.lang = lang;
    h.state.config = { ...config, amount_scale: 1000000, currency };
    const normal = new Intl.NumberFormat(locales[lang], { style: "currency", currency, currencyDisplay: "code" });
    for (const [amount, decimal] of [[0, 0], [1000000, 1], [1250000, 1.25], [-1250000, -1.25], [987654321000, 987654.321]]) {
      const minimum = normal.resolvedOptions().minimumFractionDigits;
      const fraction = String(Math.abs(amount) % 1000000).padStart(6, "0").replace(/0+$/, "").length;
      const expected = new Intl.NumberFormat(locales[lang], { style: "currency", currency, currencyDisplay: "code", minimumFractionDigits: minimum, maximumFractionDigits: Math.max(minimum, fraction) }).format(decimal);
      assert.equal(h.app.money(amount), expected, `amount ${amount}`);
    }
    const decimalMark = new Intl.NumberFormat(locales[lang]).formatToParts(1.1).find(part => part.type === "decimal").value;
    const tiny = h.app.money(1), negativeTiny = h.app.money(-1), large = h.app.money(Number.MAX_SAFE_INTEGER);
    assert.ok(tiny.includes(`0${decimalMark}000001`), tiny);
    assert.ok(negativeTiny.includes(`0${decimalMark}000001`) && negativeTiny.includes("-"), negativeTiny);
    assert.ok(large.includes(`${decimalMark}740991`), large);
    return { one_micro_unit: tiny, maximum_safe_amount: large };
  });
  for (const lang of Object.keys(locales)) await check(`Demo amounts retain PLN formatting in ${lang}`, () => {
    const h = harness({ boot: true }); h.state.lang = lang;
    for (const amount of [0, 1, 12345, -12345, 1000000]) assert.equal(h.app.money(amount), new Intl.NumberFormat(locales[lang], { style: "currency", currency: "PLN" }).format(amount / 100));
  });

  for (const lang of Object.keys(locales)) await check(`Server error codes and unknown error details are localized in ${lang}`, async () => {
    const h = harness({ instant: true, bonuses: false }); changeLanguage(h, lang);
    assert.equal(typeof h.app.localizedError, "function");
    for (const code of ["insufficient_funds", "session_expired", "session_changed", "result_expired", "request_conflict", "session_limit", "invalid_bet", "invalid_mode", "rgs_invalid_launch", "rgs_replay_unavailable", "rgs_social_unavailable", "rgs_rejected", "rgs_currency_changed", "rgs_connection_failed", "rgs_recovery_required", "unknown_private_error"]) {
      const raw = "PRYWATNY KOMUNIKAT SERWERA sessionID=secret";
      const result = h.app.localizedError(Object.assign(new Error(raw), { code }));
      assert.ok(typeof result === "string" && result.length > 3, code);
      assert.ok(!result.includes(raw) && !result.includes("secret") && !result.includes(code), code);
    }
    assert.equal(h.app.localizedError(new Error("Unexpected private payload")), h.app.t("requestError"));
    for (const [code, key] of [["session_expired", "sessionExpired"], ["session_changed", "sessionChanged"], ["result_expired", "resultExpired"], ["session_limit", "sessionLimit"], ["invalid_bet", "invalidBet"], ["invalid_mode", "invalidMode"]]) {
      assert.equal(h.app.localizedError({ code }), h.app.t(key), code);
    }
    const bad = harness({ instant: true, bonuses: false, behavior: () => ({ type: "error", code: "invalid_bet", status: 400, message: "PRYWATNY KOMUNIKAT SERWERA" }) });
    changeLanguage(bad, lang); await manual(bad);
    assert.ok(!bad.ids.toast.textContent.includes("PRYWATNY"));
    assert.equal(bad.ledger.size, 0);
  });
  for (const lang of Object.keys(locales)) await check(`Reset message formats the actual returned balance in ${lang}`, async () => {
    let rejectReset = false;
    const h = harness({ boot: true, href: base + "?lang=" + lang, fetch: async url => {
      if (url === "/api/config") return response(config);
      if (url === "/assets/symbols.json") return response({});
      if (url === "/api/state" || url === "/api/reset") {
        if (url === "/api/reset" && rejectReset) return response({ error: "PRYWATNY KOMUNIKAT SERWERA", code: "invalid_mode" }, 400);
        return response({ session_id: "localized-reset", balance_cents: 123456, rounds: 0, total_bet_cents: 0, total_win_cents: 0 });
      }
      throw new Error("Unexpected test URL: " + url);
    } });
    await initialize(h); await h.app.resetSession();
    assert.ok(h.ids.toast.textContent.includes(h.app.money(123456)), h.ids.toast.textContent);
    assert.ok(!h.ids.toast.textContent.includes("{balance}"));
    rejectReset = true; await h.app.resetSession();
    assert.ok(!h.ids.toast.textContent.includes("PRYWATNY"));
    assert.equal(h.ids.toast.textContent, h.app.t("invalidMode"));
  });

  for (const lang of Object.keys(locales)) await check(`Language switch retains the blocking launch error in ${lang}`, async () => {
    const h = harness({ boot: true, rgs: true, href: base + "?sessionID=incomplete&lang=pl" });
    await initialize(h); changeLanguage(h, lang);
    assert.equal(h.state.online, false);
    assert.equal(h.ids["win-caption"].textContent, h.app.t("offline"));
    assert.equal(h.ids["win-detail"].textContent, h.app.t("invalidLaunch"));
    assert.equal(h.ids["spin-button"].disabled, true);
    assert.equal(h.document.documentElement.lang, lang);
    for (const code of ["constructor", "__proto__", "toString"]) assert.equal(h.app.localizedError({ code }), h.app.t("requestError"));
  });

  for (const lang of Object.keys(locales)) await check(`Actual accessibility attribute hooks translate in ${lang}`, async () => {
    const h = harness({ boot: true, href: base + "?lang=" + lang });
    await initialize(h);
    const html = fs.readFileSync(path.join(__dirname, "../web/index.html"), "utf8");
    const attributes = [...html.matchAll(/data-i18n-(aria-label|title)="([^"]+)"/g)].map(match => ({ attribute: match[1], key: match[2], attrs: {}, getAttribute() { return this.key; }, setAttribute(key, value) { this.attrs[key] = value; } }));
    const originalQuery = h.document.querySelectorAll.bind(h.document);
    h.document.querySelectorAll = selector => selector === "[data-i18n-aria-label]" ? attributes.filter(node => node.attribute === "aria-label") : selector === "[data-i18n-title]" ? attributes.filter(node => node.attribute === "title") : originalQuery(selector);
    h.app.translate();
    assert.ok(attributes.length > 15);
    for (const node of attributes) assert.equal(node.attrs[node.attribute], h.app.words[lang][node.key]);
  });

  for (const lang of Object.keys(locales)) await check(`Public replay rules and amounts translate before and after playback in ${lang}`, async () => {
    const href = base + "?replay=true&rgs_url=127.0.0.1%3A8800&game=00000000-0000-4000-8000-000000000001&version=0.5.0-any-start&mode=base&event=middle&amount=500000&currency=USD&lang=pl";
    const round = clone(fixtures.rounds.middle);
    const h = harness({ boot: true, rgs: true, rgsOnly: true, href, fetch: async url => {
      if (url === "game-config.json") return response(fixtures.config);
      if (url === "assets/symbols.json") return response({});
      assert.ok(String(url).includes("/bet/replay/"));
      return response({ payoutMultiplier: round.payout_units / fixtures.config.payout_scale, costMultiplier: 1, state: [{ index: 0, type: "roundResult", data: round }] });
    } });
    await initialize(h); changeLanguage(h, lang);
    assert.equal(h.state.online, true, h.ids["win-detail"].textContent);
    assert.equal(h.ids["replay-status"].textContent, h.app.t("replayNotice"));
    assert.ok(h.ids["replay-summary"].textContent.includes(h.app.t("replayCost")));
    assert.ok(h.ids["replay-summary"].textContent.includes(h.app.money(500000)));
    assert.ok(h.ids["rules-content"].textContent.includes(h.app.t("replayWalletRule")));
    assert.ok(!/10 000 zł|10,000|10\.000|whole-PLN|ganze PLN|walletRule/.test(h.ids["rules-content"].textContent));
    assert.ok(h.ids["rules-content"].textContent.includes(h.app.words[lang].ruleText[5]), "WILD expansion rule is retained");
    h.state.speed = "turbo"; await manual(h);
    changeLanguage(h, lang === "en" ? "de" : "en");
    assert.ok(h.ids["win-caption"].textContent.includes(h.app.t("replayFinished")));
    assert.ok(h.ids["replay-summary"].textContent.includes(h.app.t("replayCost")));
    assert.ok(h.ids["replay-summary"].textContent.includes(h.app.money(h.state.replayResult.win_cents)));
    assert.equal(h.ids["replay-status"].textContent, h.app.t("replayNotice"));
  });

  const report = { passed: checks.every(value => value.passed), method: "Real app.js and rgs-client.js; deterministic minimal DOM with mock API. Amount and language logic, not browser layout or live platform acceptance.", checks };
  const directory = process.env.PG_QA_OUT_DIR || __dirname;
  fs.mkdirSync(directory, { recursive: true });
  fs.writeFileSync(path.join(directory, "localization_results.json"), JSON.stringify(report, null, 2) + "\n");
  console.log(JSON.stringify({ passed: report.passed, checks: checks.length, failed: checks.filter(value => !value.passed).length }));
  if (!report.passed) process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
