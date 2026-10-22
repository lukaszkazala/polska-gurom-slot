from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / 'test-interface-any-start'
path = ROOT / 'web/app.js'
s = path.read_text('utf-8')

def replace(old, new):
    global s
    assert s.count(old) == 1, (old[:100], s.count(old))
    s = s.replace(old, new)

replace('  function savePending() {', '''  Object.assign(words.pl, { replay: "Odtwórz rundę", replayAgain: "Odtwórz ponownie", replayPlaying: "Odtwarzanie…", replayNotice: "REPLAY · zapisany wynik · bez nowego zakładu", replayReady: "Replay gotowy. Naciśnij Odtwórz rundę.", replayError: "Nie udało się odczytać replay. Zapis jest niedostępny lub niezgodny z tą wersją gry.", replayCost: "Koszt pierwotnej rundy", replayFinished: "Replay zakończony" });
  Object.assign(words.en, { replay: "Play replay", replayAgain: "Play again", replayPlaying: "Replaying…", replayNotice: "REPLAY · recorded result · no new bet", replayReady: "Replay ready. Press Play replay.", replayError: "Could not load replay. The recording is unavailable or incompatible with this game version.", replayCost: "Original round cost", replayFinished: "Replay complete" });
  Object.assign(words.de, { replay: "Runde abspielen", replayAgain: "Erneut abspielen", replayPlaying: "Wiedergabe…", replayNotice: "REPLAY · gespeichertes Ergebnis · kein neuer Einsatz", replayReady: "Replay bereit. Runde abspielen drücken.", replayError: "Replay konnte nicht geladen werden. Die Aufzeichnung ist nicht verfügbar oder mit dieser Spielversion unvereinbar.", replayCost: "Ursprüngliche Rundenkosten", replayFinished: "Replay abgeschlossen" });
  function savePending() {''')
replace('state.rgs ? window.PG_RGS.payout(bet, units, state.config.payout_scale)', 'state.config?.amount_scale === 1_000_000 ? window.PG_RGS.payout(bet, units, state.config.payout_scale)')
replace('  function validateSpinResponse(result, request) {', '  function validateSpinResponse(result, request, { replay = false } = {}) {')
replace('    if (state.rgs) require(result.rgs === true', '    if (!replay && state.rgs) require(result.rgs === true')
replace('    else require(result.balance_cents === result.balance_before_cents', '    else if (!replay) require(result.balance_cents === result.balance_before_cents')
replace('const expectedWin = state.rgs ?', 'const expectedWin = state.config?.amount_scale === 1_000_000 ?')

# One shared presentation: live rounds provide checkpoints; replays never do.
start = s.index('      const free = result.round.free_spins;\n      const progress = state.presentation;', s.index('  async function spin()'))
end = s.index('      if (state.rgs) {\n        result.wallet = await state.rgs.finish(result);', start)
presentation = s[start:end].replace('      const progress = state.presentation;\n', '').replace('await checkpointPresentation()', 'await checkpoint()')
presentation = '\n'.join(line[2:] if line.startswith('  ') else line for line in presentation.split('\n'))
s = s[:start] + '      await presentRound(result, state.presentation, checkpointPresentation);\n' + s[end:]
insert = '''  async function presentRound(result, progress, checkpoint = async () => {}) {
PRESENTATION  }
  function savedReplays() {
    if (!state.rgs) return [];
    try {
      const records = JSON.parse(sessionStorage.getItem(`pg-replays-${state.sessionId}`) || "[]");
      if (!Array.isArray(records)) return [];
      return records.slice(0, 100).filter(record => {
        try {
          if (record.rgs_active !== false || record.currency !== state.config.currency || record.amount_scale !== state.config.amount_scale || !Number.isFinite(Date.parse(record.displayed_at))) return false;
          validateSpinResponse(record, record, { replay: true }); return true;
        } catch { return false; }
      });
    } catch { return []; }
  }
  function persistReplays() {
    if (!state.rgs) return;
    // Store complete settled results, with an allowlist that excludes launch/session tokens.
    const fields = ["request_id", "round_id", "session_id", "math_version", "mode", "is_scenario", "bet_cents", "win_cents", "balance_cents", "balance_before_cents", "stats", "round", "rgs", "rgs_active", "created_at", "displayed_at", "currency", "amount_scale"];
    try { sessionStorage.setItem(`pg-replays-${state.sessionId}`, JSON.stringify(state.history.map(record => Object.fromEntries(fields.map(key => [key, record[key]]))))); } catch {}
  }
  async function replayRound(record = state.selected) {
    if (!record || state.busy || state.pending || state.auto || state.walletReading) return;
    try {
      if (!Number.isSafeInteger(record.bet_cents) || record.bet_cents <= 0 || (record.currency && record.currency !== state.config.currency) || (record.amount_scale && record.amount_scale !== (state.config.amount_scale || 100))) throw new Error("replay_format");
      validateSpinResponse(record, record, { replay: true });
    } catch { toast(t("replayError")); return; }
    const result = JSON.parse(JSON.stringify(record));
    const settings = { instant: state.instant, skipScreens: state.skipScreens };
    state.busy = true; state.replaying = true; state.currentBet = result.bet_cents;
    state.instant = false; state.skipScreens = false;
    $("details-dialog").close();
    document.querySelector("#settings-dialog")?.close();
    controls(); refreshStats(); clearLines();
    $("replay-status").hidden = false; $("replay-status").textContent = t("replayNotice");
    try {
      await presentRound(result, { baseComplete: false, freeCompleted: 0 });
      state.replayPlayed = true;
      $("win-caption").textContent = `${t("replayFinished")} · ${money(result.win_cents)}`;
    } catch { $("win-detail").textContent = t("replayError"); toast(t("replayError")); }
    finally {
      Object.assign(state, settings); state.busy = false; state.replaying = false;
      state.cells.forEach(cell => cell.classList.remove("spinning", "expanding", "cascade-removing", "cascade-vacant", "cascade-winning"));
      $("bonus-announcement").hidden = true; $("cascade-layer").hidden = true; $("cascade-layer").replaceChildren();
      refreshStats(); controls();
    }
  }
'''.replace('PRESENTATION', presentation)
replace('  async function spin() {', insert + '''  async function spin() {
    if (state.replayMode) { await replayRound(state.replayResult); return; }''')
replace('    const blocked = state.busy || !state.online;', '''    const blocked = state.busy || !state.online;
    const replayBlocked = state.busy || !!state.pending || !!state.auto || !!state.walletReading;
    $("replay-button").disabled = !state.selected || replayBlocked;
    $("details-replay-button").disabled = !state.selected || replayBlocked;
    $("replay-button").hidden = !!state.replayMode;
    $("details-replay-button").textContent = t("replay");
    $("replay-button").textContent = t("replay");''')
replace('    renderAutoplaySettings();\n  }\n  function stopAuto', '''    if (state.replayMode) {
      for (const id of ["auto-button", "autoplay-start", "auto-count", "bet-decrease", "bet-increase", "test-mode-select", "reset-button", "hyperplay-button"]) $(id).disabled = true;
      $("spin-button").disabled = state.busy || !state.replayResult;
      $("spin-label").textContent = t(state.replaying ? "replayPlaying" : state.replayPlayed ? "replayAgain" : "replay");
      $("spin-button").setAttribute("aria-label", $("spin-label").textContent);
      $("spin-button").title = $("spin-label").textContent;
      $("spin-button").classList.add("replay-control");
      $("test-hint").textContent = t("replayNotice");
      $("connection-status").textContent = "REPLAY";
    }
    renderAutoplaySettings();
  }
  function stopAuto''')
replace('    roundNote(null);\n    if (!state.pending)', '    $("replay-status").hidden = true;\n    roundNote(null);\n    if (!state.pending)')
replace('state.history = [{ ...result, displayed_at: new Date().toISOString() },', 'state.history = [{ ...result, currency: state.config.currency || "PLN", amount_scale: state.config.amount_scale || 100, displayed_at: new Date().toISOString() },')
replace('state.selected = state.history[0]; renderHistory();', 'state.selected = state.history[0]; persistReplays(); renderHistory();')
replace('    state.history.slice(0, 25).forEach', '    state.history.forEach')
replace('$("details-dialog").showModal(); }', '$("details-replay-button").disabled = state.busy || !!state.pending || !!state.auto || !!state.walletReading; $("details-dialog").showModal(); }')
replace('    if (state.rgs) return;\n    if (state.busy || state.pending) return;', '    if (state.rgs || state.replayMode) return;\n    if (state.busy || state.pending) return;')
replace('  function bindEvents() {', '''  function bindEvents() {
    $("replay-button").addEventListener("click", () => replayRound());
    $("details-replay-button").addEventListener("click", () => replayRound());''')
replace('else if (!state.busy && !state.pending && state.online &&', 'else if (!state.replayMode && !state.busy && !state.pending && state.online &&')
replace('      if (state.busy || state.pending || state.auto || !state.online ||', '      if (state.replayMode || state.busy || state.pending || state.auto || !state.online ||')
replace('function changeBet(direction) { if (state.busy || state.pending)', 'function changeBet(direction) { if (state.replayMode || state.busy || state.pending)')
replace('state.platformLaunch = params.has("sessionID") || params.has("rgs_url") ||', 'state.replayMode = params.get("replay") === "true";\n      state.platformLaunch = state.replayMode || params.has("sessionID") || params.has("rgs_url") ||')
replace('      if (launch) {\n        state.rgs', '''      if (launch?.replay) {
        state.lang = launch.lang; state.rgs = null;
        const loaded = await Promise.all([api("game-config.json"), api("assets/symbols.json")]);
        const replay = await window.PG_RGS.loadReplay(launch, loaded[0]);
        config = replay.config; symbols = loaded[1]; state.replayResult = replay.result;
        wallet = { session_id: "replay", balance_cents: 0, rounds: 0, total_bet_cents: 0, total_win_cents: 0 };
        state.bet = replay.result.bet_cents; state.currentBet = state.bet;
        const badge = document.querySelector(".player-demo-label"); if (badge) badge.textContent = "REPLAY";
        const tools = document.querySelector(".testing-tools"); if (tools) tools.hidden = true;
      } else if (launch) {
        state.rgs''')
replace('      state.history = (wallet.recent_rounds || []).map(record => ({ ...record, displayed_at: record.created_at }));', '      state.history = state.replayMode ? [] : state.rgs ? savedReplays() : (wallet.recent_rounds || []).map(record => ({ ...record, displayed_at: record.created_at }));')
replace('      if (config.bet_options_cents.includes(savedBet)) state.bet = savedBet;', '      if (!state.replayMode && config.bet_options_cents.includes(savedBet)) state.bet = savedBet;')
replace('      translate();\n      const saved = savedPending();', '''      translate();
      if (state.replayMode) {
        validateSpinResponse(state.replayResult, state.replayResult, { replay: true });
        state.selected = state.replayResult;
        showGrid(state.replayResult.round.base.grid);
        setWin(state.replayResult.win_cents);
        $("win-caption").textContent = t("replayReady");
        $("win-detail").textContent = `${t("bet")}: ${money(state.bet)} · ×1 · ${t("replayCost")}: ${money(state.bet)} · ×${number(state.replayResult.round.payout_units / config.payout_scale)}`;
        $("replay-status").textContent = t("replayNotice"); $("replay-status").hidden = false;
        $("replay-summary").textContent = `${t("bet")}: ${money(state.bet)} · ×1 · ${t("replayCost")}: ${money(state.bet)} · ${t("roundWin")}: ${money(state.replayResult.win_cents)} (×${number(state.replayResult.round.payout_units / config.payout_scale)})`;
        $("replay-summary").hidden = false;
        document.querySelector(".slot-cabinet").classList.add("replay-view");
        controls(); return;
      }
      const saved = savedPending();''')
replace('      const message = state.platformLaunch ? messages[state.lang] : t("loadError");', '''      if (state.replayMode) state.replayResult = null;
      const message = state.replayMode ? t("replayError") : state.platformLaunch ? messages[state.lang] : t("loadError");''')
path.write_text(s, 'utf-8')
