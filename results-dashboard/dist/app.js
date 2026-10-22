"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const D = window.DASHBOARD_DATA;
  const fmt = (n, digits = 0) => Number.isFinite(Number(n)) ? new Intl.NumberFormat("pl-PL", { maximumFractionDigits: digits, minimumFractionDigits: digits }).format(Number(n)) : "—";
  const pct = (n, digits = 2) => Number.isFinite(Number(n)) && n !== null ? `${fmt(Number(n) * 100, digits)}%` : "—";
  const compact = n => n >= 1e6 ? `${fmt(n / 1e6, n % 1e6 ? 1 : 0)} mln` : fmt(n);
  const esc = text => String(text ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  const icon = name => `<svg aria-hidden="true"><use href="#i-${name}"/></svg>`;
  const labels = { overview: "Przegląd", simulations: "Symulacje", bonus: "Bonusy", tests: "Testy i awarie", history: "Historia projektu", reports: "Wszystkie raporty" };
  const kinds = { weighted: "Końcowy rozkład", natural: "Generator kandydatów", calibration: "Strojenie", diagnostic: "Kontrola pomocnicza", historical: "Wersja historyczna" };
  const statuses = { pass: ["good", "Zaliczone"], passed: ["good", "Zaliczone"], verified: ["good", "Sprawdzone"], exact: ["good", "Dokładne"], fail: ["bad", "Nie przeszło"], failed: ["bad", "Nie przeszło"], open: ["amber", "Do poprawy"], warning: ["amber", "Ograniczenie"], "known-limit": ["amber", "Ograniczenie"], historical_issues: ["amber", "Historyczne uwagi"], historical_pass: ["neutral", "Wynik historyczny"], historical_research: ["neutral", "Badanie historyczne"], reference: ["neutral", "Materiał referencyjny"], "not-performed": ["neutral", "Nie wykonano"], info: ["neutral", "Informacja"] };
  const badge = status => { const [cls, label] = statuses[String(status).toLowerCase()] || ["neutral", "Archiwum"]; return `<span class="badge ${cls}">${label}</span>`; };
  const state = { view: "overview", simFilter: "weighted", testFilter: "current", selectedRun: "weighted-100000000" };
  const reports = D?.reports || [];
  const embeddedReports = window.DASHBOARD_REPORTS || {};
  const embeddedUrls = new Map();
  const reportFor = path => reports.find(report => report.path === String(path).replaceAll("\\", "/"));
  const evidenceList = evidence => Array.isArray(evidence) ? evidence : evidence ? [evidence] : [];
  const currentSuite = suite => typeof suite.current === "boolean" ? suite.current : typeof suite.isCurrent === "boolean" ? suite.isCurrent : suite.countedInRegressionTotal || String(suite.version).startsWith("0.4") && !/wcześ|history/i.test(suite.scope || "");
  if (!D) { $("overview-metrics").innerHTML = '<div class="data-error">Nie udało się wczytać danych. Zachowaj plik data-embed.js obok dashboardu i odśwież stronę.</div>'; return; }
  const bonus12 = D.bonus.bonus_types.find(type => type.free_spins === 12);
  const verified12 = D.summary.bonus12Verified === true && bonus12?.books > 0 && bonus12?.weight > 0;
  const activeEvidence = (name, fallback) => D.meta[name] || fallback;

  function renderCoverageUi() {
    const open = Number(D.summary.criticalOpen || 0);
    $("coverage-banner").innerHTML = verified12
      ? `<div class="finding-icon">${icon("check")}</div><div><span class="mini-label">NAPRAWIONE I SPRAWDZONE</span><h2>12 darmowych obrotów jest dostępne w grze.</h2><p>${fmt(bonus12.books)} legalne pełne rundy z 5 Scatterami · dodatnia masa ${fmt(bonus12.weight)} / 10¹² · RTP 96%.</p></div><a href="#bonus" class="text-link">Zobacz częstość ${icon("arrow")}</a>`
      : `<div class="finding-icon">${icon("warn")}</div><div><span class="mini-label">DO POPRAWY W AKTUALNYM MODELU</span><h2>Bonus 12 darmowych obrotów nie występuje w wynikach.</h2><p>Zasady przewidują 5 Scatterów, ale w końcowej tabeli nie ma takiej rundy.</p></div><a href="#bonus" class="text-link">Zobacz analizę ${icon("arrow")}</a>`;
    $("coverage-status").className = `badge ${verified12 ? "good" : "amber"}`;
    $("coverage-status").textContent = verified12 ? "12FS sprawdzone" : `${open || 1} otwarty problem`;
    $("bonus-status").className = `badge ${verified12 ? "good" : "amber"} large`;
    $("bonus-status").innerHTML = `${icon(verified12 ? "check" : "warn")}${verified12 ? "Dostępne 8, 10 i 12 FS" : "Brakuje wariantu 12 FS"}`;
    $("bonus-coverage-note").innerHTML = verified12
      ? `${icon("check")}<p><strong>Pokrycie zasad potwierdzone.</strong> Wariant 12 obrotów ma ${fmt(bonus12.books)} legalne wyniki i dodatnią wagę. Częstość jest rzadka: średnio 1:${fmt(bonus12.one_in)} płatnych rund. Całkowita częstość bonusu i dokładny RTP pozostały zachowane.</p>`
      : `${icon("warn")}<p><strong>Wykryta luka w pokryciu zasad.</strong> Wariant 12 obrotów ma zero wyników w eksporcie. Wymaga poprawki zestawu wyników i ponownej kontroli wag.</p>`;
    $("bonus-nav-warning").hidden = verified12;
    $("model-version").textContent = D.meta.mathVersion;
  }

  function syncMenu() {
    const open = document.body.classList.contains("menu-open");
    $("sidebar").inert = window.matchMedia("(max-width: 760px)").matches && !open;
    $("menu-toggle").setAttribute("aria-expanded", String(open));
  }
  function showView(name) {
    if (!labels[name]) name = "overview";
    state.view = name;
    document.querySelectorAll(".view").forEach(section => { section.hidden = section.id !== `view-${name}`; section.classList.toggle("active", !section.hidden); });
    document.querySelectorAll(".nav-link").forEach(link => { const selected = link.dataset.view === name; link.classList.toggle("active", selected); if (selected) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current"); });
    $("breadcrumb-view").textContent = labels[name];
    document.title = `${labels[name]} · Polska Gurom`;
    document.body.classList.remove("menu-open"); syncMenu();
    window.scrollTo({ top: 0, behavior: "instant" });
  }
  function metric(label, value, detail, symbol, extra = "") {
    return `<article class="metric-card ${extra}"><div class="metric-label">${esc(label)}<span class="metric-icon">${icon(symbol)}</span></div><div class="metric-value">${value}</div><p class="metric-sub">${detail}</p></article>`;
  }
  function renderOverview() {
    const s = D.summary;
    $("math-facts").innerHTML = detailGrid([["Dokładny RTP",pct(s.exactRtp,2)],["Maksymalna wypłata",`${fmt(s.maxWin)}×`],["Szansa na maksimum",`1 : ${fmt(s.maxWinOneIn)}`],["Dowolna wypłata",pct(s.hitFrequency,4)],["Wypłata większa od stawki",pct(s.netProfitFrequency,4)],["Różne pełne rundy w zestawie",fmt(s.bookCount)]]);
    $("overview-metrics").innerHTML = metric("TEORETYCZNY RTP", pct(s.exactRtp, 0), "Dokładnie z wag wszystkich rund", "chart") + metric("LOSOWANIA KOŃCOWE", compact(s.weightedDraws), "Serie 10 mln + 50 mln + 100 mln", "grid") + metric("CZĘSTOŚĆ BONUSU", `1<span class="metric-separator">:</span>${fmt(s.meanRoundsToBonus, 0)}`, `${pct(s.bonusFrequency, 3)} na płatną rundę`, "gift") + metric("TESTY REGRESJI", `${fmt(s.regressionPassed)}<span class="metric-denominator"> / ${fmt(s.regressionChecks)}</span>`, `${s.currentSuiteCount || 6} zestawów regresji · ${verified12 ? "12FS potwierdzone" : "luka w zasadach"}`, "shield");
    const quality = [
      ["Format matematyki Stake", "Publiczny SDK — kontrola lokalna", "pass", activeEvidence("sdkReportPath", "audit/stake_cascades_v04/official_validation/official_validation_report.json")],
      ["Pełne wyniki i kaskady", `${fmt(s.bookCount)} rund sprawdzonych niezależnie`, "pass", activeEvidence("bookReportPath", "audit/stake_cascades_v04/book_mechanics_report.json")],
      ["Odporność na awarie", `${s.networkFaultChecks} testów HTTP i logiki interfejsu`, "pass", activeEvidence("networkReportPath", "audit/network_resilience_2026_10_19/results.json")],
      ["Pokrycie bonusu 12 obrotów", verified12 ? `${fmt(bonus12.books)} pełne rundy · dodatnia waga` : "Brak rund z 5 Scatterami w eksporcie", verified12 ? "pass" : "open", activeEvidence("coverageReportPath", "audit/bonus_frequency_2026_10_19/results.json")]
    ];
    $("quality-list").innerHTML = quality.map(([title,detail,status,path]) => `<button class="quality-row" data-evidence="${esc(path)}"><span class="quality-symbol ${status === "pass" ? "good" : "amber"}">${icon(status === "pass" ? "check" : "warn")}</span><span class="quality-copy"><strong>${esc(title)}</strong><small>${esc(detail)}</small></span>${icon("arrow")}</button>`).join("");
    $("milestones").innerHTML = [
      ["01", "Matematyka i duże próby", "RTP, rozkład wypłat, maksimum 5000× i trzy rozmiary symulacji.", "simulations"],
      ["02", "Kaskady i autospin", "Ruch symboli w dół, cały bonus w jednej rundzie oraz serie 100/100.", "tests"],
      ["03", "Awarie i odzyskiwanie", "Zerwana odpowiedź, timeout, restart i blokada drugiego pobrania stawki.", "tests"],
      ["04", "Analiza bonusów", verified12 ? "Dokładna częstość oraz naprawiony wariant 12 darmowych obrotów." : "Dokładna częstość i wykryty brak wariantu 12 darmowych obrotów.", "bonus"]
    ].map(([n,title,text,view]) => `<a class="milestone" href="#${view}"><span class="milestone-step">${n}</span><strong>${title}</strong><p>${text}</p>${icon("arrow")}</a>`).join("");
    renderRtpChart();
  }
  function renderRtpChart() {
    const kind = $("overview-model").value;
    const runs = D.simulations.filter(run => run.kind === kind).sort((a,b) => a.rounds-b.rounds);
    if (!runs.length) { $("overview-chart").innerHTML = '<div class="empty-state">Brak serii w tym modelu.</div>'; return; }
    if (!runs.some(run => run.id === state.selectedRun)) state.selectedRun = runs.at(-1).id;
    const values = runs.flatMap(run => run.interval95?.length ? run.interval95 : [run.rtp]);
    const lo = Math.floor((Math.min(.96,...values)-.0008)*1000)/1000;
    const hi = Math.ceil((Math.max(.96,...values)+.0008)*1000)/1000;
    const w = 680, h = 245, left = 57, right = 28, top = 22, bottom = 40;
    const x = i => left+(w-left-right)*(i+.5)/runs.length;
    const y = value => top+(h-top-bottom)*(hi-value)/(hi-lo);
    let svg = `<svg class="chart-svg" viewBox="0 0 ${w} ${h}" role="img" aria-label="Wykres zmierzonego RTP z przedziałami 95 procent. Wybierz serię, aby zobaczyć szczegóły.">`;
    for (let i=0;i<5;i++) { const value = lo+(hi-lo)*i/4; svg += `<line class="chart-grid" x1="${left}" y1="${y(value)}" x2="${w-right}" y2="${y(value)}"/><text class="chart-label" x="${left-12}" y="${y(value)+4}" text-anchor="end">${fmt(value*100,1)}%</text>`; }
    svg += `<line class="chart-reference" x1="${left}" y1="${y(.96)}" x2="${w-right}" y2="${y(.96)}"/><text class="chart-reference-label" x="${w-right}" y="${y(.96)-7}" text-anchor="end">CEL 96%</text>`;
    svg += `<path class="chart-connection" d="${runs.map((run,i)=>`${i ? "L" : "M"}${x(i)} ${y(run.rtp)}`).join(" ")}"/>`;
    runs.forEach((run,i) => {
      const interval = run.interval95 || [run.rtp,run.rtp];
      svg += `<g class="chart-run ${state.selectedRun === run.id ? "selected" : ""}" data-chart-run="${esc(run.id)}" tabindex="0" role="button" aria-label="Seria ${compact(run.rounds)}, RTP ${pct(run.rtp,4)}"><title>${compact(run.rounds)} · RTP ${pct(run.rtp,4)} · przedział ${pct(interval[0],4)}–${pct(interval[1],4)}</title><rect class="chart-hitbox" x="${x(i)-46}" y="${top}" width="92" height="${h-top}"/><line class="chart-interval" x1="${x(i)}" y1="${y(interval[0])}" x2="${x(i)}" y2="${y(interval[1])}"/><line class="chart-interval" x1="${x(i)-6}" y1="${y(interval[0])}" x2="${x(i)+6}" y2="${y(interval[0])}"/><line class="chart-interval" x1="${x(i)-6}" y1="${y(interval[1])}" x2="${x(i)+6}" y2="${y(interval[1])}"/><circle class="chart-halo" cx="${x(i)}" cy="${y(run.rtp)}" r="12"/><circle class="chart-point" cx="${x(i)}" cy="${y(run.rtp)}" r="5"/><text class="chart-value" x="${x(i)+14}" y="${y(run.rtp)+5}">${pct(run.rtp,3)}</text><text class="chart-label x-label" x="${x(i)}" y="${h-10}" text-anchor="middle">${compact(run.rounds)}</text></g>`;
    });
    $("overview-chart").innerHTML = svg+"</svg>";
    $("chart-caption").textContent = kind === "weighted" ? "Każdy punkt to osobna seria losowań końcowych wag. Wybierz punkt, aby zobaczyć liczby." : "Pełne symulacje generatora kandydatów. Ich zwrot nie jest dokładnym RTP końcowej gry.";
    const selected = runs.find(run => run.id === state.selectedRun);
    $("selected-run").innerHTML = `<div><span>WYBRANA SERIA</span><strong>${compact(selected.rounds)} rund</strong></div><div><span>RTP Z PRÓBY</span><strong>${pct(selected.rtp,4)}</strong></div><div><span>${kind === "weighted" ? "TRAFIENIA 5000×" : "TRAFIENIA BONUSU"}</span><strong>${kind === "weighted" ? fmt(selected.maxWinHits) : pct(selected.bonusFrequency,3)}</strong></div><button class="text-link" data-run-detail="${esc(selected.id)}">Szczegóły ${icon("arrow")}</button>`;
  }
  function renderSimulations() {
    const runs = D.simulations.filter(run => state.simFilter === "all" || run.kind === state.simFilter);
    $("sim-count").textContent = `${runs.length} ZAPISANYCH SERII`;
    $("simulations-body").innerHTML = runs.map(run => { const delta = run.referenceRtp === null || run.referenceRtp === undefined ? null : (run.rtp-run.referenceRtp)*100; const maximum = run.details?.max_observed_payout_units != null ? `${fmt(run.details.max_observed_payout_units/100,1)}×` : run.details?.maximumUnits != null ? `${fmt(run.details.maximumUnits/100,1)}×` : run.details?.max_observed_win != null ? `${fmt(run.details.max_observed_win,1)}×` : run.maxWinHits != null ? `${fmt(run.maxWinHits)} trafień limitu` : "—"; return `<tr><td><strong>${esc(run.title)}</strong><small>${esc(kinds[run.kind] || run.kind)} · ${esc(run.version || "archiwum")}</small></td><td class="tabular">${fmt(run.rounds)}</td><td class="table-emphasis">${pct(run.rtp,4)}</td><td class="tabular muted">${delta === null ? "—" : `${delta > 0 ? "+" : ""}${fmt(delta,4)} pp`}</td><td class="tabular">${maximum}</td><td><button class="row-action" data-run-detail="${esc(run.id)}" aria-label="Szczegóły serii ${compact(run.rounds)} ${esc(run.title)}">${icon("arrow")}</button></td></tr>`; }).join("") || '<tr><td colspan="6" class="empty-state">Brak zapisanych serii w tej kategorii.</td></tr>';
  }
  function renderBonus() {
    const b = D.bonus;
    $("bonus-metrics").innerHTML = metric("SZANSA NA BONUS",pct(b.bonus_probability,3),"Na jedną płatną rundę","gift") + metric("ŚREDNI ODSTĘP",fmt(b.mean_paid_rounds_to_bonus,2),"płatnych rund do bonusu","clock") + metric("MEDIANA CZEKANIA",fmt(b.waiting_time_quantiles["0.5"]),"rund do osiągnięcia 50% szansy","chart");
    $("bonus-types").innerHTML = b.bonus_types.map(type => `<div class="bonus-type ${type.books ? "" : "missing"}"><div class="bonus-type-number">${type.free_spins}<small>OBROTÓW</small></div><div class="bonus-type-copy"><strong>${type.scatters} Scattery</strong><span>${fmt(type.books)} różnych rund w zestawie</span><div class="bonus-type-track"><i style="width:${Math.max(type.share_of_bonuses*100,type.books ? 2 : 0)}%"></i></div></div><div class="bonus-type-frequency"><strong>${pct(type.probability,type.free_spins === 12 && type.books ? 6 : type.books ? 4 : 0)}</strong><small>${type.one_in ? `średnio 1:${fmt(type.one_in,0)}` : "brak w wynikach"}</small></div></div>`).join("");
    $("bonus-runs-body").innerHTML = b.previous_simulations_aggregated.map(run => `<tr><td>${fmt(run.rounds)}</td><td class="table-emphasis">${fmt(run.bonuses)}</td><td>${pct(run.bonus_frequency,6)}</td><td>1:${fmt(run.one_in,2)}</td><td>${run.by_free_spins ? fmt(run.by_free_spins["12"] || 0) : "—"}</td></tr>`).join("");
    renderBonusProbability(100);
  }
  function renderBonusProbability(value) {
    const n = Math.max(1,Math.min(1000,Math.round(Number(value)||1)));
    const p = -Math.expm1(n*Math.log1p(-D.bonus.bonus_probability));
    $("bonus-rounds").value = n; $("bonus-rounds-number").value = n;
    $("bonus-rounds").style.setProperty("--range-progress",`${(n-1)/999*100}%`);
    $("probability-fill").style.width = `${p*100}%`;
    $("bonus-probability").innerHTML = `<div class="probability-numbers"><div class="probability-stat"><strong>${pct(p,2)}</strong><span>szansy na przynajmniej jeden bonus</span></div><div class="probability-stat secondary"><strong>${pct(1-p,2)}</strong><span>szansy na brak bonusu</span></div></div><div class="probability-expectation">Średnia liczba bonusów w ${fmt(n)} rundach: <strong>${fmt(n*D.bonus.bonus_probability,2)}</strong></div>`;
    document.querySelectorAll("[data-rounds]").forEach(button => { const on = Number(button.dataset.rounds) === n; button.classList.toggle("active",on); button.setAttribute("aria-pressed",String(on)); });
  }
  function suiteMethod(suite) {
    if (/network-http/.test(suite.id)) return "Rzeczywiste lokalne połączenia HTTP/TCP i izolowany przekaźnik awarii.";
    if (/network-logic|autoplay-logic/.test(suite.id)) return "Rzeczywista logika interfejsu, kontrolowany transport i przyspieszony zegar.";
    if (/portable/.test(suite.id)) return "Wypakowana paczka ZIP i uruchomiony lokalny serwer.";
    if (/book|mechanic/.test(suite.id)) return "Niezależne sprawdzenie pełnych wyników, wypłat i opadania symboli.";
    return suite.method || suite.scope || "Zakres kontroli zapisany w raporcie źródłowym.";
  }
  function renderTests() {
    $("test-summary").innerHTML = `<div><strong>${fmt(D.summary.regressionPassed)}<small> / ${fmt(D.summary.regressionChecks)}</small></strong><span>kontroli bieżącej wersji</span></div><div><strong>${fmt(D.summary.networkFaultChecks)}</strong><span>przypadków awarii połączenia</span></div><div><strong>100<small> / 100</small></strong><span>autoobrotów po zgubionej odpowiedzi</span></div><div class="${verified12 ? "" : "amber"}"><strong>${fmt(D.summary.criticalOpen)}</strong><span>otwartych błędów pokrycia bonusów</span></div>`;
    const query = $("test-search").value.trim().toLocaleLowerCase("pl");
    const suites = D.suites.filter(suite => state.testFilter === "all" || state.testFilter === "current" && currentSuite(suite) || state.testFilter === "historical" && !currentSuite(suite) || state.testFilter === "network" && /network|awari|sieć/i.test(suite.id+" "+suite.title)).map(suite => ({ ...suite, visibleTests: (suite.tests||[]).filter(test => !query || JSON.stringify(test).toLocaleLowerCase("pl").includes(query) || suite.title.toLocaleLowerCase("pl").includes(query)) })).filter(suite => !query || suite.visibleTests.length || suite.title.toLocaleLowerCase("pl").includes(query));
    $("test-suites").innerHTML = suites.map(suite => `<details class="suite-card" ${query ? "open" : ""}><summary class="suite-summary"><span class="suite-symbol">${icon(/network/.test(suite.id) ? "shield" : "check")}</span><span class="suite-title"><strong>${esc(suite.title)}</strong><small>${esc(suite.version || "Archiwum")} · ${esc(suite.scope || "Zapisana kontrola")}</small></span><span class="suite-meta">${suite.testsCount != null ? `${fmt(suite.passedCount??suite.testsCount)} / ${fmt(suite.testsCount)}` : "Audyt"}</span>${badge(suite.status)}<span class="suite-chevron">⌄</span></summary><div class="suite-content"><p class="suite-method">${esc(suiteMethod(suite))}</p><div class="test-list">${suite.visibleTests.map((test,index) => `<button class="test-row" data-test-suite="${esc(suite.id)}" data-test-index="${(suite.tests||[]).indexOf(test)}"><span class="test-status ${test.status === "pass" ? "good" : "amber"}">${icon(test.status === "pass" ? "check" : "info")}</span><span>${esc(test.label_pl || test.name || test.scenario || `Kontrola ${index+1}`)}</span>${test.details?.limitation ? '<span class="badge amber">Z ograniczeniem</span>' : ""}${icon("arrow")}</button>`).join("") || '<p class="empty-state">Szczegóły dostępne w raporcie zbiorczym.</p>'}</div><div class="suite-sources">${evidenceButtons(suite.evidence)}</div></div></details>`).join("") || '<div class="empty-state">Brak testów pasujących do wyszukiwania.</div>';
  }
  function historyStats(phase) {
    const r = phase.results || {};
    const stats = [];
    const exact = r.exact_rtp ?? r.rtp;
    if (typeof exact === "number") stats.push(["RTP",pct(exact,4)]);
    if (r.maximum_reachable_x) stats.push(["Maksimum",`${fmt(r.maximum_reachable_x,1)}×`]);
    if (r.original_tests_total) stats.push(["Testy",`${r.original_tests_passed}/${r.original_tests_total}`]);
    if (r.tests_total || r.test_count) stats.push(["Testy",fmt(r.tests_total || r.test_count)]);
    if (r.variants) stats.push(["Warianty",fmt(r.variants.length)]);
    if (r.book_count || r.complete_books) stats.push(["Pełne rundy",fmt(r.book_count || r.complete_books)]);
    return stats.slice(0,3).map(([label,value])=>`<span>${label}<strong>${value}</strong></span>`).join("");
  }
  function renderHistory() {
    const phases = Array.isArray(D.history) ? D.history : D.history?.phases || [];
    $("history-timeline").innerHTML = phases.map((phase,index) => `<article class="history-item"><div class="history-marker"><span>${String(index+1).padStart(2,"0")}</span></div><div class="history-card"><div class="history-top"><span class="history-version">${esc(phase.version)}</span><span>${esc(phase.date||"")}</span>${badge(phase.status)}</div><h2>${esc(phase.name || phase.title)}</h2><p>${esc(phase.scope || phase.description || "")}</p><div class="history-stats">${historyStats(phase)}</div>${(phase.limitations || []).length ? `<div class="history-limitations">${phase.limitations.slice(0,2).map(text=>`<p>${esc(text)}</p>`).join("")}</div>` : ""}<button class="text-link" data-history="${esc(phase.id)}">Wyniki i źródła ${icon("arrow")}</button></div></article>`).join("");
  }
  const reportTitles = { "RAPORT_PL.md": "Raport podsumowujący", "official_validation_report.json": "Walidacja publicznym Stake SDK", "weighted_simulation_report.json": "Symulacje końcowych wag — 10 / 50 / 100 mln", "book_mechanics_report.json": "Niezależny audyt wszystkich pełnych rund", "network_faults_results.json": "17 testów rzeczywistych awarii HTTP/TCP", "network_logic_results.json": "30 scenariuszy awarii interfejsu", "autoplay_logic_results.json": "13 testów autospinu", "portable_check.json": "27 kontroli paczki po wypakowaniu", "mathematics.json": "Parametry aktualnej matematyki", "browser_check.json": "Kontrola gry w przeglądarce", "DOCS_REQUIREMENTS.md": "Wymagania matematyczne Stake", "RAPORT_STAKE_ENGINE_PL.md": "Wcześniejszy przegląd wymagań Stake Engine", "RAPORT_TOTAL_CASINO_PL.md": "Analiza referencyjna Total Casino" };
  const reportTitle = report => report.displayTitle || reportTitles[report.path.split("/").at(-1)] || report.title || report.path.split("/").at(-1);
  function renderReports() {
    const query = $("report-search").value.trim().toLocaleLowerCase("pl");
    const category = $("report-category").value;
    const list = reports.filter(report => (category === "all" || report.category === category) && (!query || `${reportTitle(report)} ${report.path} ${report.category}`.toLocaleLowerCase("pl").includes(query)));
    $("report-count").textContent = `${list.length} z ${reports.length} plików`;
    $("reports-grid").innerHTML = list.map(report => { const ext = report.path.split(".").at(-1).toUpperCase(); const type = ext === "MD" ? "RAPORT" : ext === "JSON" ? "DANE" : ext; return `<article class="report-card"><div class="report-meta"><span class="report-type ${ext.toLowerCase()}">${icon(ext === "MD" ? "file" : "grid")}${type}</span><span>${esc(report.category)}</span></div><h2 class="report-title">${esc(reportTitle(report))}</h2><p class="report-path">${esc(report.path)}</p><div class="report-actions"><button class="text-link" data-report="${esc(report.id)}">Otwórz ${icon("arrow")}</button><a class="icon-button" href="${safeHref(report.href)}" download="${esc(report.path.split("/").at(-1))}" aria-label="Pobierz ${esc(reportTitle(report))}">${icon("download")}</a></div></article>`; }).join("") || '<div class="empty-state">Brak raportów pasujących do wyszukiwania.</div>';
  }
  function safeHref(value) {
    const path = String(value || "");
    if (!/^reports\//.test(path) || path.includes("..")) return "#";
    const bundled = embeddedReports[path.slice(8)];
    if (bundled) {
      if (!embeddedUrls.has(path)) {
        const bytes = bundled.base64 ? Uint8Array.from(atob(bundled.base64), char => char.charCodeAt(0)) : bundled.text;
        embeddedUrls.set(path, URL.createObjectURL(new Blob([bytes], {type: bundled.mime})));
      }
      return esc(embeddedUrls.get(path));
    }
    return esc(path.split("/").map(encodeURIComponent).join("/"));
  }
  function evidenceButtons(evidence) { return evidenceList(evidence).map(path => { const report = reportFor(path); return report ? `<button class="text-link" data-report="${esc(report.id)}">${icon("file")}${esc(reportTitle(report))}</button>` : ""; }).join(""); }
  function openDialog(title, body, eyebrow = "SZCZEGÓŁY", source = null) {
    $("detail-dialog").dataset.activeReport = "";
    $("dialog-title").textContent = title; $("dialog-eyebrow").textContent = eyebrow; $("dialog-body").innerHTML = body;
    $("dialog-footnote").textContent = source ? source.path : "Dane z zapisanych analiz projektu.";
    $("dialog-download").hidden = !source;
    if (source) { $("dialog-download").href = safeHref(source.href).replaceAll("&amp;","&"); $("dialog-download").setAttribute("download",source.path.split("/").at(-1)); }
    if (!$("detail-dialog").open) $("detail-dialog").showModal();
    $("dialog-body").scrollTop = 0;
  }
  function detailGrid(fields) { return `<div class="detail-grid">${fields.filter(([,value])=>value!==undefined&&value!==null).map(([label,value])=>`<div class="detail-field"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join("")}</div>`; }
  function rawDetails(object) { return `<details class="raw-details"><summary>Dane źródłowe JSON</summary><pre class="source-code">${esc(JSON.stringify(object,null,2))}</pre></details>`; }
  function showRun(id) {
    const run = D.simulations.find(item=>item.id===id); if (!run) return;
    const interval = run.interval95;
    openDialog(`${compact(run.rounds)} rund · ${kinds[run.kind] || run.kind}`, `<p class="dialog-intro">${esc(run.scope || run.title)}</p>${detailGrid([["Wersja",run.version],["Płatne rundy",fmt(run.rounds)],["Zmierzony RTP",pct(run.rtp,7)],["Cel / odniesienie",run.referenceRtp==null?"Nie dotyczy":pct(run.referenceRtp,2)],["Przedział 95%",interval?`${pct(interval[0],5)} – ${pct(interval[1],5)}`:"Brak w źródle"],["Seed",run.seed==null?"Brak w źródle":String(run.seed)],["Częstość bonusu",run.bonusFrequency==null?null:pct(run.bonusFrequency,6)],["Liczba bonusów",run.bonuses==null?null:fmt(run.bonuses)],["Trafienia 5000×",run.maxWinHits==null?null:fmt(run.maxWinHits)]])}<div class="dialog-sources">${evidenceButtons(run.evidence)}</div>${rawDetails(run.details||run)}`,"ZAPISANA SYMULACJA",reportFor(evidenceList(run.evidence)[0]));
  }
  function renderMarkdown(text) {
    const lines = text.split(/\r?\n/); let html="", list=false, table=false, code=false;
    const inline = line => esc(line).replace(/\[([^\]]+)\]\((?:&lt;)?[^)]+\)/g,"$1").replace(/\*\*([^*]+)\*\*/g,"<strong>$1</strong>").replace(/`([^`]+)`/g,"<code>$1</code>");
    for (const line of lines) {
      if (line.startsWith("```")) { if(list){html+="</ul>";list=false;} if(table){html+="</table></div>";table=false;} html += code ? "</pre>" : '<pre class="source-code">'; code=!code; continue; }
      if(code){html+=esc(line)+"\n";continue;}
      if(line.startsWith("|")){ if(list){html+="</ul>";list=false;} if(!table){html+='<div class="table-scroll"><table class="data-table">';table=true;} if(/^\|[\s:|\-]+\|$/.test(line))continue; const cells=line.replace(/^\||\|$/g,"").split("|"); html+="<tr>"+cells.map(cell=>`<td>${inline(cell.trim())}</td>`).join("")+"</tr>"; continue; }
      if(table){html+="</table></div>";table=false;}
      if(/^[-*] /.test(line)){if(!list){html+="<ul>";list=true;}html+=`<li>${inline(line.slice(2))}</li>`;continue;}
      if(list){html+="</ul>";list=false;}
      const heading=line.match(/^(#{1,4}) (.+)/); if(heading){const level=Math.min(4,heading[1].length+1);html+=`<h${level}>${inline(heading[2])}</h${level}>`;continue;}
      if(line.trim())html+=`<p>${inline(line)}</p>`;
    }
    return html+(list?"</ul>":"")+(table?"</table></div>":"")+(code?"</pre>":"");
  }
  async function showReport(id) {
    const report = reports.find(item=>item.id===id||item.path===id); if(!report)return;
    const isImage = /\.(png|jpg|jpeg|webp|svg)$/i.test(report.path);
    if(isImage){openDialog(reportTitle(report),`<img class="evidence-image" src="${safeHref(report.href)}" alt="${esc(reportTitle(report))}">`,"DOWÓD WIZUALNY",report);return;}
    openDialog(reportTitle(report),'<p class="dialog-intro">Wczytuję raport…</p>',"RAPORT ŹRÓDŁOWY",report);
    $("detail-dialog").dataset.activeReport = report.id;
    const bundled = embeddedReports[report.path];
    let text = bundled?.text ?? report.preview ?? report.content ?? "";
    if (!bundled) {
      try { const response=await fetch(report.href); if(!response.ok)throw new Error("missing"); text=await response.text(); } catch { if(!text) { if($("detail-dialog").dataset.activeReport === report.id)$("dialog-body").innerHTML='<p class="dialog-intro">Otwórz pojedynczy plik dashboard.html, aby korzystać ze wszystkich raportów także bez internetu.</p>';return; } }
    }
    if($("detail-dialog").dataset.activeReport !== report.id || !$("detail-dialog").open)return;
    text=text.replace(/C:[\\/]+Users[\\/]+Kazaluka[\\/]+\.codex[\\/]+\.chatgpt-projects[\\/]+g-p-6ad10d7dc94881919023097cba0cf4b4/gi,"[projekt]");
    if(/\.json$/i.test(report.path)){try{text=JSON.stringify(JSON.parse(text),null,2);}catch{} $("dialog-body").innerHTML=`<pre class="source-code">${esc(text)}</pre>`;}
    else if(/\.md$/i.test(report.path))$("dialog-body").innerHTML=`<div class="markdown-report">${renderMarkdown(text)}</div>`;
    else $("dialog-body").innerHTML=`<pre class="source-code">${esc(text)}</pre>`;
  }
  function showHistory(id){const phase=(Array.isArray(D.history)?D.history:D.history.phases||[]).find(item=>item.id===id);if(!phase)return;openDialog(phase.name||phase.title,`<p class="dialog-intro">${esc(phase.scope)}</p>${detailGrid([["Wersja",phase.version],["Data analizy",phase.date]])}${phase.limitations?.length?`<div class="history-limitations">${phase.limitations.map(text=>`<p>${esc(text)}</p>`).join("")}</div>`:""}<div class="dialog-sources">${evidenceButtons(phase.sourcepaths||phase.evidence)}</div>${rawDetails(phase.results||phase)}`,"HISTORYCZNY ETAP PROJEKTU");}
  function download(filename,text,type){const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement("a");a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function aboutData(){openDialog("Co pokazuje dashboard?",`<p class="dialog-intro">Zapisane wyniki wszystkich dostępnych etapów projektu, z aktualną matematyką i osobnym archiwum wcześniejszych wersji.</p>${detailGrid([["Model końcowy",D.meta.mathVersion],["RTP dokładne",pct(D.summary.exactRtp,0)],["Regresje bieżące",`${D.summary.regressionPassed}/${D.summary.regressionChecks}`],["Raporty źródłowe",fmt(reports.length)]])}<p>${esc(D.integrity.deduplication)} Raporty zbiorcze, duże symulacje i starsze wersje nie zwiększają liczby bieżących kontroli.</p><p>160 mln końcowych losowań i 160 mln pełnych symulacji generatora to różne metody, pokazane osobno. Publiczny SDK sprawdza pliki lokalnie; nie wykonano zatwierdzenia przez Stake.</p><h3>Otwarte kwestie i ograniczenia</h3>${D.findings.map(f=>`<div class="about-finding"><strong>${esc(f.title)}</strong><p>${esc(f.detail)}</p>${evidenceButtons(f.evidence)}</div>`).join("")}<details class="raw-details"><summary>Zgodność danych i sumy kontrolne</summary><pre class="source-code">${esc(JSON.stringify(D.integrity,null,2))}</pre></details>`,"ZAKRES I POCHODZENIE WYNIKÓW");}
  function bind(){
    window.addEventListener("hashchange",()=>showView(location.hash.slice(1)));
    $("menu-toggle").addEventListener("click",()=>{document.body.classList.toggle("menu-open");syncMenu();});
    window.matchMedia("(max-width: 760px)").addEventListener("change",syncMenu);
    document.addEventListener("keydown",event=>{if(event.key === "Escape" && document.body.classList.contains("menu-open")){document.body.classList.remove("menu-open");syncMenu();$("menu-toggle").focus();}});
    $("overview-model").addEventListener("change",renderRtpChart);
    $("simulation-filters").addEventListener("click",event=>{const button=event.target.closest("[data-sim-filter]");if(!button)return;state.simFilter=button.dataset.simFilter;document.querySelectorAll("[data-sim-filter]").forEach(b=>b.classList.toggle("active",b===button));renderSimulations();});
    $("test-filters").addEventListener("click",event=>{const button=event.target.closest("[data-test-filter]");if(!button)return;state.testFilter=button.dataset.testFilter;document.querySelectorAll("[data-test-filter]").forEach(b=>b.classList.toggle("active",b===button));renderTests();});
    $("test-search").addEventListener("input",renderTests);$("report-search").addEventListener("input",renderReports);$("report-category").addEventListener("change",renderReports);
    $("bonus-rounds").addEventListener("input",event=>renderBonusProbability(event.target.value));$("bonus-rounds-number").addEventListener("input",event=>renderBonusProbability(event.target.value));
    document.querySelectorAll("[data-rounds]").forEach(button=>button.addEventListener("click",()=>renderBonusProbability(button.dataset.rounds)));
    document.querySelectorAll(".export-data").forEach(button=>button.addEventListener("click",()=>download("polska-gurom-wyniki.json",JSON.stringify(D,null,2),"application/json;charset=utf-8")));
    $("export-simulations").addEventListener("click",()=>{const rows=D.simulations.filter(run=>state.simFilter==="all"||run.kind===state.simFilter);const fields=["id","kind","version","rounds","rtp","referenceRtp","seed","bonuses","bonusFrequency","maxWinHits"];download("polska-gurom-symulacje.csv","\ufeff"+[fields.join(";"),...rows.map(run=>fields.map(key=>`"${String(run[key]??"").replaceAll('"','""')}"`).join(";"))].join("\r\n"),"text/csv;charset=utf-8");});
    $("open-bonus-evidence").addEventListener("click",()=>showReport(activeEvidence("bonusReportPath", "audit/bonus_frequency_2026_10_19/RAPORT_PL.md")));$("about-data").addEventListener("click",aboutData);
    $("close-dialog").addEventListener("click",()=>$("detail-dialog").close());$("detail-dialog").addEventListener("click",event=>{if(event.target===$("detail-dialog"))$("detail-dialog").close();});
    document.addEventListener("click",event=>{
      const point=event.target.closest("[data-chart-run]");if(point){state.selectedRun=point.dataset.chartRun;renderRtpChart();return;}
      const run=event.target.closest("[data-run-detail]");if(run){showRun(run.dataset.runDetail);return;}
      const report=event.target.closest("[data-report]");if(report){showReport(report.dataset.report);return;}
      const evidence=event.target.closest("[data-evidence]");if(evidence){const r=reportFor(evidence.dataset.evidence);if(r)showReport(r.id);return;}
      const history=event.target.closest("[data-history]");if(history){showHistory(history.dataset.history);return;}
      const test=event.target.closest("[data-test-suite]");if(test){const suite=D.suites.find(s=>s.id===test.dataset.testSuite);const item=suite?.tests[Number(test.dataset.testIndex)];if(item)openDialog(item.label_pl||item.name,`<p class="dialog-intro">${esc(suite.title)}</p>${badge(item.status)}${item.details?.limitation?'<p class="amber-note">Przypadek przeszedł z opisanym ograniczeniem lokalnego testera.</p>':""}<div class="dialog-sources">${evidenceButtons(suite.evidence)}</div>${rawDetails(item.details||item)}`,"SZCZEGÓŁY TESTU",reportFor(evidenceList(suite.evidence)[0]));}
    });
    document.addEventListener("keydown",event=>{const point=event.target.closest?.("[data-chart-run]");if(point&&["Enter"," "].includes(event.key)){event.preventDefault();state.selectedRun=point.dataset.chartRun;renderRtpChart();}});
  }
  function init(){
    $("snapshot-date").textContent=(D.meta.snapshotDate||"2026-10-19").split("-").reverse().join(".");
    $("report-nav-count").textContent=reports.length;$("footer-report-count").textContent=reports.length;
    [...new Set(reports.map(r=>r.category))].sort((a,b)=>a.localeCompare(b,"pl")).forEach(category=>{const option=document.createElement("option");option.value=category;option.textContent=category.charAt(0).toUpperCase()+category.slice(1);$("report-category").append(option);});
    renderCoverageUi();renderOverview();renderSimulations();renderBonus();renderTests();renderHistory();renderReports();bind();showView(location.hash.slice(1));
  }
  init();
})();
