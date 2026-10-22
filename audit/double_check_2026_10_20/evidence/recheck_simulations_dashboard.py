"""Fresh read-only reconciliation; never imports a production calculator.

Route A uses Python arbitrary-precision integers and Fraction; route B uses
independent SQLite relational joins and integer SUMs over all source records.
Only this evidence directory receives output.
"""
from __future__ import annotations
import ast
import base64
from collections import Counter
import csv
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
from html.parser import HTMLParser
import io
import json
import math
from pathlib import Path
import sqlite3
from statistics import NormalDist
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FIX = ROOT / "audit/bonus12_fix_2026_10_20"
EXPORT = ROOT / "test-interface/stake_math"
DIST = ROOT / "results-dashboard/dist"
sys.path.insert(0, str(ROOT / "audit/stake_cascades_v04/dependencies"))
import zstandard
from scipy.stats import beta, binom

checks = []
def check(name, condition, detail=None):
    checks.append({"name": name, "status": "PASS" if condition else "FAIL", "detail": detail})
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))
def close(a, b):
    return math.isclose(a, b, rel_tol=2e-12, abs_tol=2e-13)
def vector_close(a, b):
    return len(a) == len(b) and all(close(x, y) for x, y in zip(a, b))

dashboard = read(DIST / "data.json")
mathematics = read(EXPORT / "mathematics.json")
manifest = read(EXPORT / "selection.json")
weighted = read(FIX / "weighted_results/weighted_simulation_report.json")
bonus = read(FIX / "bonus_frequency.json")
lut_raw = (EXPORT / "lookUpTable_base_0.csv").read_bytes()
lut = [tuple(map(int, row)) for row in csv.reader(io.StringIO(lut_raw.decode("utf-8-sig")))]
ids = [i for i, _, _ in lut]
by_id = {i: (w, p) for i, w, p in lut}
check("LUT unique contiguous IDs, legal payouts, positive weights", len(ids) == len(set(ids)) == 100048 and ids == list(range(100048)) and all(w > 0 and 0 <= p <= 500000 and p % 10 == 0 for _, w, p in lut))
check("All current report LUT hashes", all(x["lut_sha256"] == sha(lut_raw) for x in (manifest, weighted, bonus, read(FIX / "coverage_results.json"), read(FIX / "book_mechanics_report.json"))))

# Actual book payloads provide bonus classifications, independent of metadata.
books = []
awards = {}
book_scatter_counts = Counter()
book_payout_discrepancies = []
bonus_credit_weighted_sum = expanded_bonus_mass = expansions = 0
with (EXPORT / "books_base.jsonl.zst").open("rb") as compressed:
    with zstandard.ZstdDecompressor().stream_reader(compressed) as decoded:
        for line in io.TextIOWrapper(decoded, encoding="utf-8"):
            book = json.loads(line)
            i = book["id"]
            data = book["events"][0]["data"]
            award = data["base"]["free_spins_awarded"]
            scatter = data["base"]["scatter_count"]
            payout = book["payoutMultiplier"]
            if payout != by_id[i][1] or data["payout_units"] != payout:
                book_payout_discrepancies.append(i)
            awards[i] = award
            book_scatter_counts[(scatter, award)] += 1
            books.append((i, award, scatter))
            w = by_id[i][0]
            if award:
                bonus_credit_weighted_sum += w * data["bonus_payout_units"]
                expanded_bonus_mass += w * any(s["expanding_reel"] is not None for s in data["free_spins"])
                expansions += w * sum(s["expanding_reel"] is not None for s in data["free_spins"])
check("100048 book IDs and actual payload payouts equal LUT", len(books) == len(set(awards)) == len(lut) and not book_payout_discrepancies)
check("Book Scatter-to-bonus rules", all((a == 0 and s < 3) or (s, a) in {(3,8), (4,10), (5,12)} for _, a, s in books))

total = sum(w for _, w, _ in lut)
first = sum(w*p for _, w, p in lut)
second = sum(w*p*p for _, w, p in lut)
mean = Fraction(first, total*100)
variance = Fraction(second, total*10000) - mean*mean
mass = Counter()
type_books = Counter()
for i, w, p in lut:
    mass[awards[i]] += w
    type_books[awards[i]] += 1
hit = Fraction(sum(w for _, w, p in lut if p > 0), total)
profit = Fraction(sum(w for _, w, p in lut if p > 100), total)
cap = Fraction(sum(w for _, w, p in lut if p == 500000), total)
bonus_p = Fraction(sum(v for k, v in mass.items() if k), total)

db = sqlite3.connect(":memory:")
db.executescript("CREATE TABLE lut (id INTEGER PRIMARY KEY, weight INTEGER, payout INTEGER); CREATE TABLE books (id INTEGER PRIMARY KEY, award INTEGER, scatters INTEGER); CREATE TABLE hist (id INTEGER PRIMARY KEY, weight INTEGER, payout INTEGER, n INTEGER);")
db.executemany("INSERT INTO lut VALUES (?,?,?)", lut)
db.executemany("INSERT INTO books VALUES (?,?,?)", books)
sql_total, sql_first, sql_second = db.execute("SELECT SUM(weight), SUM(weight*payout), SUM(weight*payout*payout) FROM lut").fetchone()
sql_mass = dict(db.execute("SELECT award,SUM(weight) FROM lut JOIN books USING(id) GROUP BY award"))
check("Route B SQL exact weighted moments equal route A integers", (sql_total, sql_first, sql_second) == (total, first, second) and sql_mass == dict(mass))
check("Exact 96% RTP, cap and variance match written mathematics and simulation reference", total == 10**12 and str(mean) == mathematics["rtp_exact_fraction"] == weighted["reference"]["exact_rtp_fraction"] == "24/25" and str(variance) == mathematics["variance_fraction"] == weighted["reference"]["exact_variance_fraction"] and cap == Fraction(1,8000000) and first == mathematics["weighted_payout_units_sum"])
check("Written maths frequencies match exact sums", close(float(hit), mathematics["hit_frequency"]) and close(float(profit), mathematics["net_profit_frequency"]) and close(float(bonus_p), mathematics["bonus_frequency"]) and close(math.sqrt(float(variance)), mathematics["standard_deviation"]))

for t in bonus["bonus_types"]:
    fs = t["free_spins"]
    p = Fraction(mass[fs], total)
    check(f"Exact {fs} FS books, weight, fraction, one-in and share", type_books[fs] == t["books"] and mass[fs] == t["weight"] and str(p) == t["probability_fraction"] and close(float(p),t["probability"]) and close(1/float(p),t["one_in"]) and close(mass[fs]/sum(mass[k] for k in (8,10,12)),t["share_of_bonuses"]))
check("Bonus derived means and RTP contribution", close(float(1/bonus_p),bonus["mean_paid_rounds_to_bonus"]) and close(sum(k*mass[k] for k in (8,10,12))/sum(mass[k] for k in (8,10,12)),bonus["mean_awarded_free_spins_per_bonus"]) and close(bonus_credit_weighted_sum/(100*total),bonus["free_spin_rtp_contribution"]) and close(bonus_credit_weighted_sum/(100*sum(mass[k] for k in (8,10,12))),bonus["conditional_mean_credited_free_spin_return_x_bet"]) and close(expanded_bonus_mass/sum(mass[k] for k in (8,10,12)),bonus["bonus_with_at_least_one_expansion_probability"]) and close(expansions/total,mathematics["expansions_per_paid_round"]))
check("Bonus waiting quantiles and series probabilities", all(math.ceil(math.log1p(-float(q))/math.log1p(-float(bonus_p))) == n for q,n in bonus["waiting_time_quantiles"].items()) and all(close(x["expected_bonus_count"],x["paid_rounds"]*float(bonus_p)) and close(x["probability_no_bonus"],float(1-bonus_p)**x["paid_rounds"]) and close(x["probability_at_least_one_bonus"],1-float(1-bonus_p)**x["paid_rounds"]) for x in bonus["series_probabilities"]))

sim_rechecks = []
observed_bonus_reports = {r["rounds"]:r for r in bonus["previous_simulations_aggregated"]}
active_dashboard_sims = {s["rounds"]:s for s in dashboard["simulations"] if s["kind"] == "weighted"}
names = ["0x", ">0x-1x", "1x-5x", "5x-20x", "20x-100x", "100x-500x", "500x-1000x", "1000x-5000x", "5000x"]
bounds = [(0,1),(1,100),(100,500),(500,2000),(2000,10000),(10000,50000),(50000,100000),(100000,500000),(500000,500001)]
for run in weighted["runs"]:
    n = run["rounds"]
    histogram_path = FIX / "weighted_results" / run["outcome_histogram_file"]
    raw = histogram_path.read_bytes()
    rows = [tuple(int(row[k]) for k in ("id","weight","payout_units","observed_count")) for row in csv.DictReader(io.StringIO(raw.decode("utf-8")))]
    check(f"{n} histogram complete unique IDs, nonnegative counts and current LUT columns", len(rows)==len(lut) and len({r[0] for r in rows})==len(lut) and all((w,p)==by_id[i] and c>=0 for i,w,p,c in rows))
    check(f"{n} original histogram SHA256", sha(raw)==run["outcome_histogram_sha256"])
    count = sum(c for _,_,_,c in rows)
    payout = sum(c*p for _,_,p,c in rows)
    squares = sum(c*p*p for _,_,p,c in rows)
    observed_by_fs = Counter()
    for i,_,_,c in rows:
        observed_by_fs[awards[i]]+=c
    db.execute("DELETE FROM hist")
    db.executemany("INSERT INTO hist VALUES (?,?,?,?)",rows)
    sql_n,sql_p,sql_s = db.execute("SELECT SUM(n),SUM(n*lut.payout),SUM(n*lut.payout*lut.payout) FROM hist JOIN lut USING(id)").fetchone()
    sql_bonus = dict(db.execute("SELECT award,SUM(n) FROM hist JOIN books USING(id) GROUP BY award"))
    check(f"{n} route B relational join matches every route A moment and bonus count", (count,payout,squares)==(sql_n,sql_p,sql_s) and dict(observed_by_fs)==sql_bonus)
    check(f"{n} true count and payout/square sums equal report", count==n==run["actual_integer_tickets_drawn"]==run["accounted_outcome_counts"] and payout==run["total_payout_units"] and squares==run["squared_payout_units_sum"])
    empirical_rtp = Fraction(payout,n*100)
    empirical_var = Fraction(squares,n*10000)-empirical_rtp**2
    se = math.sqrt(float(variance)/n)
    z = (float(empirical_rtp)-float(mean))/se
    intervals = {conf:[float(empirical_rtp)-NormalDist().inv_cdf((1+conf)/2)*se,float(empirical_rtp)+NormalDist().inv_cdf((1+conf)/2)*se] for conf in (.95,.99)}
    check(f"{n} RTP, empirical variance, SE, z and 95/99 intervals", close(float(empirical_rtp),run["rtp"]) and close(float(empirical_var),run["empirical_variance"]) and close(se,run["reference_standard_error"]) and close(z,run["z_score"]) and vector_close(intervals[.95],run["normal_95_interval_around_observed"]) and vector_close(intervals[.99],run["normal_99_interval_around_observed"]) and (abs(z)<=NormalDist().inv_cdf(.975))==run["within_95_normal_reference_band"] and (abs(z)<=NormalDist().inv_cdf(.995))==run["within_99_normal_reference_band"])
    wins = sum(c for _,_,p,c in rows if p>0)
    caps = sum(c for _,_,p,c in rows if p==500000)
    def cp(k):
        return [0.0 if k==0 else float(beta.ppf(.025,k,n-k+1)),1.0 if k==n else float(beta.ppf(.975,k+1,n-k))]
    check(f"{n} hit, max and binomial exact intervals", wins==run["hit_count"] and caps==run["max_win_hits"] and close(wins/n,run["hit_frequency"]) and close(n*float(cap),run["max_win_expected_hits"]) and vector_close(cp(wins),run["hit_frequency_clopper_pearson_95"]) and vector_close(cp(caps),run["max_win_observed_rate_clopper_pearson_95"]) and [int(binom.ppf(.025,n,float(cap))),int(binom.ppf(.975,n,float(cap)))]==run["max_win_binomial_95_prediction_count_interval"])
    for name,(lo,hi) in zip(names,bounds):
        bucket=run["win_buckets"][name]
        bc = sum(c for _,_,p,c in rows if lo<=p<hi)
        bp = Fraction(sum(w for _,w,p in lut if lo<=p<hi),total)
        check(f"{n} {name} bucket", bc==bucket["observed_count"] and close(bc/n,bucket["observed_frequency"]) and str(bp)==bucket["exact_probability"] and close(float(bp)*n,bucket["expected_count"]))
    b = observed_bonus_reports[n]
    bonus_count=sum(c for a,c in observed_by_fs.items() if a)
    check(f"{n} all 8/10/12 bonus counts and binomial z", {str(a):c for a,c in observed_by_fs.items()}==b["by_free_spins"] and bonus_count==b["bonuses"] and close(bonus_count/n,b["bonus_frequency"]) and close((bonus_count-n*float(bonus_p))/math.sqrt(n*float(bonus_p*(1-bonus_p))),b["binomial_z"]) and observed_by_fs[12]==b["twelve_fs_count"] and close(n*mass[12]/total,b["expected_twelve_fs_count"]))
    d = active_dashboard_sims[n]
    check(f"{n} dashboard active cards exactly match raw recomputation", d["version"]==mathematics["math_version"] and d["rtp"]==float(empirical_rtp) and d["bonuses"]==bonus_count and d["bonus12Count"]==observed_by_fs[12] and d["maxWinHits"]==caps and vector_close(d["interval95"],intervals[.95]))
    sim_rechecks.append({"rounds":n,"total_payout_units":payout,"squared_payout_units_sum":squares,"rtp":float(empirical_rtp),"empirical_variance":float(empirical_var),"reference_z":z,"by_free_spins":dict(observed_by_fs),"max_win_hits":caps,"both_routes_match":True})

check("Dashboard exact summary matches fresh integers", dashboard["meta"]["mathVersion"]==mathematics["math_version"] and dashboard["math"]==mathematics and dashboard["bonus"]==bonus and dashboard["summary"]["exactRtp"]==float(mean) and dashboard["summary"]["bookCount"]==len(lut) and dashboard["summary"]["bonus12Books"]==type_books[12] and dashboard["summary"]["bonus12Weight"]==mass[12])
check("Dashboard current weighted volume contains no historical simulations", len(active_dashboard_sims)==3 and sum(active_dashboard_sims)==dashboard["summary"]["weightedDraws"]==weighted["total_actual_draws"]==160000000 and all(s["version"]==mathematics["math_version"] for s in dashboard["simulations"] if s["kind"]=="weighted") and all(not s.get("current") and not s.get("countedInRegressionTotal") for s in dashboard["suites"] if s.get("historical")))
check("All dashboard simulation/suite IDs unique", len({s["id"] for s in dashboard["simulations"]})==len(dashboard["simulations"]) and len({s["id"] for s in dashboard["suites"]})==len(dashboard["suites"]))

# Verify each source record, not only top-level PASS counters.
suite_counts = {}
suite_records = []
for suite in dashboard["suites"]:
    if not suite.get("countedInRegressionTotal"):
        continue
    path = ROOT / suite["evidence"][0]
    report = read(path)
    cases = report.get("checks",report.get("tests"))
    if cases is None:
        source = ROOT / "audit/bonus12_fix_2026_10_20/test_coverage.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        methods = [node.name for node in ast.walk(tree) if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith("test_")]
        count = report["tests_run"]
        passed = not report["failures"] and not report["errors"] and report["status"].lower()=="pass"
        check(f"{suite['id']} source actually declares every unittest",count==len(methods),methods)
        basis = "unittest count/status plus independent AST method count; individual results not in original JSON"
    else:
        cases = [x for x in cases if any(k in x for k in ("name","test","scenario"))]
        names_cases = [x.get("name",x.get("test",x.get("scenario"))) for x in cases]
        count = len(cases)
        def ok(x):
            v=x.get("passed",x.get("success"))
            return v is True if v is not None else x.get("status","").lower() in {"pass","passed","ok","success"}
        passed = all(ok(x) for x in cases)
        check(f"{suite['id']} individual source records are unique",len(names_cases)==len(set(names_cases)))
        basis = "individual source check records"
    check(f"{suite['id']} dashboard count and passed cases equal source", report["math_version"]==mathematics["math_version"] and count==suite["testsCount"]==suite["passedCount"] and passed and len(suite["tests"])==count and all(t["status"]=="pass" for t in suite["tests"]))
    if "source_sha256" in report:
        check(f"{suite['id']} executed frontend source hash still current",report["source_sha256"]==sha((ROOT/"test-interface/web/app.js").read_bytes()))
    if "lut_sha256" in report:
        check(f"{suite['id']} executed LUT still current",report["lut_sha256"]==sha(lut_raw))
    suite_counts[suite["id"]]=count
    suite_records.append({"id":suite["id"],"count":count,"passed":passed,"count_basis":basis})
check("135 tests are sum of nine current suites only",sum(suite_counts.values())==dashboard["summary"]["regressionChecks"]==dashboard["summary"]["regressionPassed"]==135 and suite_counts==dashboard["summary"]["currentTestCounts"] and len(suite_counts)==9)

class InlineScripts(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.buf=None;self.ident=None;self.external=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="script":
            self.buf=[];self.ident=attrs.get("id")
            if attrs.get("src"):self.external.append(attrs["src"])
        if tag=="link" and attrs.get("rel")=="stylesheet":self.external.append(attrs.get("href"))
    def handle_endtag(self,tag):
        if tag=="script" and self.buf is not None:
            self.parts.append((self.ident,"".join(self.buf)));self.buf=None
    def handle_data(self,data):
        if self.buf is not None:self.buf.append(data)
standalone_raw=(DIST/"dashboard.html").read_bytes()
parser=InlineScripts();parser.feed(standalone_raw.decode("utf-8"))
embedded_data=json.loads(next(text[len("window.DASHBOARD_DATA="):].rstrip(";") for _,text in parser.parts if text.startswith("window.DASHBOARD_DATA=")))
embedded_reports=json.loads(gzip.decompress(base64.b64decode(next(text for ident,text in parser.parts if ident=="embedded-reports"))))
check("Standalone data exactly matches active JSON, no external scripts/styles",embedded_data==dashboard and not parser.external)
check("Dashboard embed JS exact data",json.loads((DIST/"data-embed.js").read_text(encoding="utf-8").removeprefix("window.DASHBOARD_DATA = ").removeprefix("window.DASHBOARD_DATA=").strip().rstrip(";"))==dashboard)
report_failures=[]
for report in dashboard["reports"]:
    raw=(DIST/report["href"]).read_bytes()
    embedded=embedded_reports[report["path"]]
    embedded_raw=base64.b64decode(embedded["base64"]) if "base64" in embedded else embedded["text"].encode("utf-8")
    if raw!=embedded_raw or sha(raw)!=report["sha256"] or len(raw)!=report["bytes"]:
        report_failures.append(report["path"])
check("Every registered raw report exact across disk, manifest and standalone",not report_failures and len(embedded_reports)==len(dashboard["reports"])==dashboard["summary"]["reportCount"]==166,report_failures)
baseline=read(FIX/"before/results-dashboard/dist/data.json")
current_registry={r["path"]:r for r in dashboard["reports"]}
check("All 139 historical report SHA256s preserved with explicit archive prefix",len(baseline["reports"])==139 and all(current_registry["baseline-v040/"+r["path"]]["sha256"]==r["sha256"] for r in baseline["reports"]))
check("Delivered standalone identical to tested standalone",(ROOT/"audit/dashboard_delivery/POLSKA_GUROM_DASHBOARD.html").read_bytes()==standalone_raw)

archive=ROOT/"test-interface/POLSKA_GUROM_v0_4_1_12FS_FIX.zip"
zip_mismatches=[]
with zipfile.ZipFile(archive) as z:
    names_zip=z.namelist()
    integrity=z.testzip()
    for name in names_zip:
        source=ROOT/"test-interface"/name
        if not source.is_file() or source.read_bytes()!=z.read(name):zip_mismatches.append(name)
check("19 game ZIP files byte-identical to current source, engine and all exports",len(names_zip)==19 and integrity is None and not zip_mismatches,zip_mismatches)
check("Game ZIP hash equals delivery and portable run",sha(archive.read_bytes())==read(FIX/"delivery.json")["game_zip_sha256"]==read(FIX/"portable_check.json")["zip_sha256"] and archive.read_bytes()==(ROOT/"test-interface/POLSKA_GUROM_TESTER.zip").read_bytes())
check("All math file hashes identify current package bytes",all(sha((EXPORT/name).read_bytes())==info["sha256"] for name,info in mathematics["files"].items()))
check("Engine fingerprints identify current source bytes",all(sha((ROOT/"test-interface/engine/polska_gurom"/name).read_bytes())==digest for name,digest in manifest["source_fingerprint"].items()))

limits=[
    "This is a fresh recalculation of original 160M histograms, not a claim of new 160M draws.",
    "Arbitrary-precision integer aggregation and separate SQLite joins are independent calculation routes; both consume the same immutable raw evidence.",
    "95/99 normal bands quantify sampling noise of this finite model and are not Stake certification or a universal pass criterion.",
    "135 counts distinct checks across nine suites, with overlapping behaviors intentionally covered at several layers; it does not mean 135 disjoint requirements.",
    "Coverage source report records suite count/status rather than 11 individual results; AST count independently matches its 11 methods.",
    "Transport tests use localhost and a virtual wallet. Server memory is lost at restart and full replay cache holds only 100 results; tombstones prevent duplicate settlement but do not provide persistent financial history.",
    "No live remote deployment/API claim is made by this file audit. Root audit checks official documentation and publication separately.",
]
result={"status":"PASS" if all(c["status"]=="PASS" for c in checks) else "FAIL","created_utc":datetime.now(timezone.utc).isoformat(),"math_version":mathematics["math_version"],"lut_sha256":sha(lut_raw),"checks_run":len(checks),"checks_passed":sum(c["status"]=="PASS" for c in checks),"exact_route_a":{"books":len(lut),"total_weight":total,"weighted_payout_units_sum":first,"weighted_squared_payout_units_sum":second,"rtp_fraction":str(mean),"variance_fraction":str(variance),"max_win_probability":str(cap),"bonus_weights":dict(mass),"bonus_books":dict(type_books)},"route_b":"SQLite integer SUMs and relational joins; every count, first/second moment, 8/10/12 bonus count matched route A","simulation_rechecks":sim_rechecks,"regression_suite_counts":suite_records,"standalone_reports":len(embedded_reports),"game_zip_sha256":sha(archive.read_bytes()),"checks":checks,"limitations":limits}
(HERE/"simulation_dashboard_recheck.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({k:result[k] for k in ("status","checks_run","checks_passed","simulation_rechecks","regression_suite_counts")},ensure_ascii=False,indent=2))
if result["status"]!="PASS":
    print(json.dumps([c for c in checks if c["status"]!="PASS"],ensure_ascii=False,indent=2))
    raise SystemExit(1)
