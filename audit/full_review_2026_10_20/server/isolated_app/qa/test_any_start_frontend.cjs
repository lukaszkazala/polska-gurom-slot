"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const {harness, clone, config} = require("./test_autoplay.cjs");
const OUT = path.resolve(process.env.PG_QA_OUT_DIR || path.join(__dirname,"../../audit/any_start_2026_10_20"));
const fixture = JSON.parse(fs.readFileSync(path.join(OUT,"middle_fixture.json"),"utf8"));
assert.equal(fixture.math_version, config.math_version);

async function run() {
  const checks = [];
  const h = harness({roundFactory: () => clone(fixture.round), speed:"normal"});
  h.ids["spin-button"].click();
  await h.clock.until(() => h.ids["win-detail"].textContent.includes("Bębny 2–4"),"shifted winning line");
  const highlighted = h.state.cells.filter(c => c.classes.has("winning")).map(c => [Number(c.dataset.row),Number(c.dataset.col)]);
  assert.deepEqual(clone(highlighted), [[0,1],[0,2],[0,3]]);
  assert.equal(h.ids["payline-overlay"].children[1].attrs.points,"150,50 250,50 350,50");
  assert.ok(h.ids["theme-select"].disabled);
  checks.push("Only reels 2–4 highlight, with the line drawn at the actual winning offset");
  await h.finished();
  assert.equal(h.backend.totalBet,200);
  assert.equal(h.backend.totalWin,60);
  assert.equal(h.state.stats.rounds,1);
  assert.equal(h.state.history.length,1);
  assert.equal(h.backend.ledger.size,1);
  checks.push("Real shifted round settles one 2 PLN bet and the complete 0.60 PLN award");

  const invalid = clone(fixture.round);
  invalid.base.line_wins[0].start_reel = 3;
  invalid.base.cascades[0].line_wins[0].start_reel = 3;
  const bad = harness({roundFactory:() => invalid});
  bad.ids["spin-button"].click(); await bad.finished();
  assert.ok(bad.state.pending);
  assert.equal(bad.state.history.length,0);
  assert.equal(bad.backend.ledger.size,1);
  assert.ok(bad.ids["spin-button"].classes.has("retry-state"));
  checks.push("An out-of-bounds winning offset is rejected and preserves a retry of the same round");
  const result = {passed:true,math_version:fixture.math_version,checks};
  fs.writeFileSync(path.join(OUT,"any_start_frontend.json"),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
}
run().catch(error => {console.error(error);process.exitCode=1;});
