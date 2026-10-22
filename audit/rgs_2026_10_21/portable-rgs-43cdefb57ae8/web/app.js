"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const locale = { pl: "pl-PL", en: "en-GB", de: "de-DE" };
  const words = {
    pl: {
      testMode: "SALDO TESTOWE", connected: "Silnik połączony", connecting: "Łączenie z silnikiem…", offline: "Brak połączenia", balance: "Saldo testowe", roundWin: "Wygrana rundy", net: "Wynik sesji", rounds: "Rozegrane rundy", bet: "Stawka", spin: "ZAKRĘĆ", spinning: "OBRÓT…", retry: "PONÓW ODCZYT", auto: "AUTO", stopAuto: "STOP AUTO", speed: "Szybkość", normal: "Normalna", fast: "Szybka", paytable: "Tabela wypłat", symbol: "Symbol", rules: "Zasady gry", history: "Historia rund", noHistory: "Tutaj pojawią się rozegrane rundy.", tools: "Narzędzia do testów", scenario: "Scenariusz", random: "Gra losowa", win: "Pokaż wygraną", bonus: "Pokaż bonus", expansion: "Pokaż rozwinięcie WILD", previewLine: "Podgląd linii", noLine: "Bez podglądu", line: "Linia", reset: "Nowa sesja", export: "Pobierz JSON", assets: "Dodaj grafiki", assetsEmpty: "Symbole zastępcze • gotowe do podmiany", details: "Szczegóły rundy", close: "Zamknij", ready: "Gotowy do pierwszego obrotu", readyDetail: "20 linii jest zawsze aktywnych. Spacja uruchamia obrót.", noWin: "Bez wygranej", smallReturn: "Częściowy zwrot stawki", returned: "Zwrot równy stawce", won: "Wygrana", roundTotal: "Suma całej rundy", scenarioNotice: "Podgląd scenariusza — bez zmiany salda i statystyk.", randomNotice: "Losowe rundy z silnika v0.2. Saldo jest wyłącznie testowe.", bonusStart: "DARMOWE OBROTY", freeSpin: "Darmowy obrót", bonusTotal: "Wygrana bonusu", charge: "SZARŻA HUSARZA", expanded: "WILD rozwija się na bębnie", scatter: "Scatter", scatterWin: "Wygrana Scatter", noFunds: "Za mało środków testowych. Zmniejsz stawkę lub rozpocznij nową sesję.", resetDone: "Rozpoczęto nową sesję z saldem 10 000 zł.", loadError: "Nie udało się połączyć. Uruchom START.cmd i odśwież stronę.", requestError: "Nie udało się odczytać wyniku. Ponów odczyt — stawka nie zostanie pobrana ponownie.", cap: "Osiągnięto limit 5000×. Saldo uwzględnia tylko zaksięgowaną wypłatę.", previewHint: "Podgląd ścieżki; wypłaty zaczynają się od pierwszego bębna.", stopHidden: "Automatyczne obroty zatrzymane po ukryciu okna.", graphicsLoaded: "Załadowano grafik", graphicsHint: "Nazwij pliki L1.png–P4.png, WILD.png i SCATTER.png. Grafiki wybrane tutaj działają do odświeżenia strony.", graphicsInvalid: "Nie znaleziono pasujących plików. Użyj nazw L1, L2, L3, L4, P1, P2, P3, P4, WILD, SCATTER.", imageFailed: "Nie udało się wczytać grafiki symbolu", sessionRtp: "Zwrot w tej sesji", round: "Runda", test: "TEST", credited: "Zaksięgowano", rawLine: "Wypłata tej linii", footer: "Demo lokalne • saldo testowe • matematyka v0.2", activeLines: "20 aktywnych linii", maxWin: "Limit rundy 5000×", autoCount: "Liczba obrotów", allLines: "Wszystkie wygrane", ruleText: ["Plansza ma 5 bębnów i 3 rzędy. Wszystkie 20 linii jest aktywnych przy każdej stawce. Zwykłe symbole płacą za co najmniej 3 kolejne dopasowania od pierwszego bębna z lewej.", "Tabela pokazuje mnożniki całkowitej stawki. WILD zastępuje zwykłe symbole. Każda linia otrzymuje jedną, najwyższą należną wypłatę.", "3 / 4 / 5 Scatterów płaci 1× / 5× / 20× stawki i przyznaje 8 / 10 / 12 darmowych obrotów. Scatter płaci w dowolnym miejscu planszy.", "Darmowe obroty mnożą wygrane linii przez 4. Scatter pozostaje bez mnożnika. Bonus nie przyznaje kolejnych darmowych obrotów.", "W darmowym obrocie SZARŻA HUSARZA może rozwinąć WILD na całym bębnie 2, 3 lub 4. Scattery są liczone przed rozwinięciem. Limit 5000× dotyczy całej rundy razem z bonusem.", "Saldo i historia są przechowywane w pamięci lokalnego serwera. Nowa sesja resetuje je do 10 000 zł. Scenariusze są odtworzeniem rzeczywistych wyników silnika i nie wpływają na saldo ani statystyki. W tym demo stawki są całkowitymi kwotami PLN."]
    },
    en: {
      testMode: "TEST BALANCE", connected: "Engine connected", connecting: "Connecting to engine…", offline: "Disconnected", balance: "Test balance", roundWin: "Round win", net: "Session result", rounds: "Rounds played", bet: "Bet", spin: "SPIN", spinning: "SPINNING…", retry: "RETRY RESULT", auto: "AUTO", stopAuto: "STOP AUTO", speed: "Speed", normal: "Normal", fast: "Fast", paytable: "Paytable", symbol: "Symbol", rules: "Game rules", history: "Round history", noHistory: "Your played rounds will appear here.", tools: "Testing tools", scenario: "Scenario", random: "Random play", win: "Show a win", bonus: "Show bonus", expansion: "Show expanding WILD", previewLine: "Preview payline", noLine: "No preview", line: "Line", reset: "New session", export: "Download JSON", assets: "Add artwork", assetsEmpty: "Placeholder symbols • ready for your artwork", details: "Round details", close: "Close", ready: "Ready for your first spin", readyDetail: "All 20 paylines are active. Press Space to spin.", noWin: "No win", smallReturn: "Partial bet returned", returned: "Bet returned", won: "Win", roundTotal: "Complete round total", scenarioNotice: "Scenario preview — balance and statistics are unchanged.", randomNotice: "Random rounds from engine v0.2. Test balance only.", bonusStart: "FREE SPINS", freeSpin: "Free spin", bonusTotal: "Bonus win", charge: "HUSSAR CHARGE", expanded: "WILD expands on reel", scatter: "Scatter", scatterWin: "Scatter win", noFunds: "Insufficient test balance. Lower your bet or start a new session.", resetDone: "New session started with PLN 10,000.", loadError: "Could not connect. Run START.cmd and refresh this page.", requestError: "Could not read the result. Retry the result — your bet will not be charged again.", cap: "5000× round cap reached. Only credited winnings are added to the balance.", previewHint: "Payline preview; wins start at the leftmost reel.", stopHidden: "Autoplay stopped when the window was hidden.", graphicsLoaded: "Artwork loaded", graphicsHint: "Name files L1.png–P4.png, WILD.png and SCATTER.png. Uploaded artwork lasts until you refresh.", graphicsInvalid: "No matching files. Use L1, L2, L3, L4, P1, P2, P3, P4, WILD, SCATTER as filenames.", imageFailed: "Could not load symbol artwork", sessionRtp: "Session return", round: "Round", test: "TEST", credited: "Credited", rawLine: "This line pays", footer: "Local demo • test balance • mathematics v0.2", activeLines: "20 active paylines", maxWin: "5000× round cap", autoCount: "Number of spins", allLines: "All winning lines", ruleText: ["The grid has 5 reels and 3 rows. All 20 paylines are active on every bet. Regular symbols pay for at least 3 consecutive matches starting on the leftmost reel.", "The paytable shows multiples of your total bet. WILD substitutes for regular symbols. Each payline pays its single highest award.", "3 / 4 / 5 Scatters pay 1× / 5× / 20× and award 8 / 10 / 12 free spins. Scatters pay anywhere on the grid.", "Free spins multiply line wins by 4. Scatter wins are not multiplied. Free spins cannot retrigger.", "HUSSAR CHARGE can expand a WILD across reel 2, 3 or 4 in a free spin. Scatters are counted before expansion. The 5000× cap applies to the complete paid round including its bonus.", "Balance and history are held in the local server's memory. New session resets the balance to PLN 10,000. Scenarios replay real engine results without changing the balance or statistics. This demo uses whole-PLN bets."]
    },
    de: {
      testMode: "TESTGUTHABEN", connected: "Engine verbunden", connecting: "Verbindung wird hergestellt…", offline: "Keine Verbindung", balance: "Testguthaben", roundWin: "Rundengewinn", net: "Sitzungsergebnis", rounds: "Gespielte Runden", bet: "Einsatz", spin: "DREHEN", spinning: "DREHT…", retry: "ERGEBNIS LADEN", auto: "AUTO", stopAuto: "AUTO STOPPEN", speed: "Tempo", normal: "Normal", fast: "Schnell", paytable: "Gewinntabelle", symbol: "Symbol", rules: "Spielregeln", history: "Rundenverlauf", noHistory: "Hier erscheinen deine gespielten Runden.", tools: "Testwerkzeuge", scenario: "Szenario", random: "Zufallsspiel", win: "Gewinn zeigen", bonus: "Bonus zeigen", expansion: "WILD-Erweiterung zeigen", previewLine: "Gewinnlinie ansehen", noLine: "Keine Vorschau", line: "Linie", reset: "Neue Sitzung", export: "JSON herunterladen", assets: "Grafiken hinzufügen", assetsEmpty: "Platzhaltersymbole • bereit für deine Grafiken", details: "Rundendetails", close: "Schließen", ready: "Bereit für die erste Drehung", readyDetail: "Alle 20 Gewinnlinien sind aktiv. Leertaste zum Drehen.", noWin: "Kein Gewinn", smallReturn: "Teil des Einsatzes zurück", returned: "Einsatz zurück", won: "Gewinn", roundTotal: "Gesamtergebnis der Runde", scenarioNotice: "Szenariovorschau — Guthaben und Statistik bleiben unverändert.", randomNotice: "Zufällige Runden mit Engine v0.2. Nur Testguthaben.", bonusStart: "FREISPIELE", freeSpin: "Freispiel", bonusTotal: "Bonusgewinn", charge: "HUSARENANGRIFF", expanded: "WILD erweitert sich auf Walze", scatter: "Scatter", scatterWin: "Scatter-Gewinn", noFunds: "Zu wenig Testguthaben. Einsatz senken oder neue Sitzung starten.", resetDone: "Neue Sitzung mit 10.000 PLN gestartet.", loadError: "Keine Verbindung. START.cmd ausführen und Seite neu laden.", requestError: "Ergebnis nicht lesbar. Erneut laden — der Einsatz wird nicht erneut abgezogen.", cap: "Rundenlimit von 5000× erreicht. Nur gutgeschriebene Gewinne zählen zum Guthaben.", previewHint: "Linienvorschau; Gewinne beginnen auf der linken Walze.", stopHidden: "Automatische Drehungen beim Ausblenden des Fensters gestoppt.", graphicsLoaded: "Grafiken geladen", graphicsHint: "Dateien L1.png–P4.png, WILD.png und SCATTER.png nennen. Die Auswahl gilt bis zum Neuladen.", graphicsInvalid: "Keine passenden Dateien. Dateinamen: L1, L2, L3, L4, P1, P2, P3, P4, WILD, SCATTER.", imageFailed: "Symbolgrafik konnte nicht geladen werden", sessionRtp: "Rücklauf der Sitzung", round: "Runde", test: "TEST", credited: "Gutgeschrieben", rawLine: "Gewinn dieser Linie", footer: "Lokale Demo • Testguthaben • Mathematik v0.2", activeLines: "20 aktive Gewinnlinien", maxWin: "Rundenlimit 5000×", autoCount: "Anzahl Drehungen", allLines: "Alle Gewinnlinien", ruleText: ["Das Raster hat 5 Walzen und 3 Reihen. Alle 20 Gewinnlinien sind bei jedem Einsatz aktiv. Reguläre Symbole zahlen für mindestens 3 aufeinanderfolgende Treffer ab der linken Walze.", "Die Tabelle zeigt Vielfache des Gesamteinsatzes. WILD ersetzt reguläre Symbole. Jede Linie zahlt ihren höchsten einzelnen Gewinn.", "3 / 4 / 5 Scatter zahlen 1× / 5× / 20× und vergeben 8 / 10 / 12 Freispiele. Scatter zählen überall auf dem Raster.", "Freispiele vervierfachen Liniengewinne. Scatter-Gewinne werden nicht multipliziert. Freispiele können nicht erneut ausgelöst werden.", "Der HUSARENANGRIFF kann einen WILD über Walze 2, 3 oder 4 erweitern. Scatter werden davor gezählt. Das Limit 5000× gilt für die gesamte bezahlte Runde einschließlich Bonus.", "Guthaben und Verlauf bleiben im Speicher des lokalen Servers. Neue Sitzung setzt auf 10.000 PLN zurück. Szenarien zeigen echte Engine-Ergebnisse ohne Änderung von Guthaben oder Statistik. Die Demo verwendet ganze PLN als Einsätze."]
    }
  };
  Object.assign(words.pl, { studioLabel: "STUDIO TESTOWE", playgroundLabel: "TWOJA PRZESTRZEŃ DO TESTÓW", pageTitle: "Wszystko gotowe do gry.", pageIntro: "Sprawdź rundy, odkryj bonus i dodaj własne symbole.", demoMode: "TRYB DEMONSTRACYJNY", demoSubline: "Grasz wyłącznie saldem testowym", gridMeta: "5 BĘBNÓW · 20 LINII", bonusReady: "3 symbole Scatter otwierają rundy bonusowe", loadingGame: "Przygotowujemy bębny…", readyToSpin: "Gotowy do pierwszego obrotu", spinHint: "Wybierz stawkę i zakręć bębnami.", autoRounds: "AUTOOBROTY", speedNormal: "NORMALNA", scenarioHint: "Losowania odbywają się w lokalnym silniku gry.", yourArtwork: "Twoja grafika", knowYourSymbols: "POZNAJ SYMBOLE", paytableIntro: "Kolumny 3, 4 i 5 oznaczają liczbę symboli. Wypłaty są mnożnikami całej stawki.", paytableFootnote: "Symbole liczone od pierwszego bębna z lewej. Jedna najwyższa wypłata na każdej linii.", mathVersion: "MATEMATYKA GRY · v0.2", sessionLabel: "TA SESJA", latestResult: "WYNIK SILNIKA", jsonIntro: "Pełny wynik wybranej rundy. Przycisk „Pobierz JSON” zapisuje ostatnie 100 rund tej sesji.", spaceToSpin: "aby zakręcić", wildRule: "Zastępuje zwykłe symbole", scatterRule: "3/4/5 → 1×/5×/20× + 8/10/12 FS", decreaseBet: "Zmniejsz stawkę", increaseBet: "Zwiększ stawkę", language: "Język interfejsu", chooseGraphics: "Wybierz grafiki symboli" });
  Object.assign(words.en, { studioLabel: "TEST STUDIO", playgroundLabel: "YOUR TESTING SPACE", pageTitle: "Ready to play.", pageIntro: "Try the rounds, explore the bonus and add your artwork.", demoMode: "DEMO MODE", demoSubline: "Play with a test balance only", gridMeta: "5 REELS · 20 PAYLINES", bonusReady: "3 Scatters unlock the bonus", loadingGame: "Preparing reels…", readyToSpin: "Ready for your first spin", spinHint: "Choose your bet and spin the reels.", autoRounds: "AUTOPLAY", speedNormal: "NORMAL", scenarioHint: "Results come from the local game engine.", yourArtwork: "Your artwork", knowYourSymbols: "MEET THE SYMBOLS", paytableIntro: "Columns 3, 4 and 5 are symbol counts. Awards are multiples of your total bet.", paytableFootnote: "Matches start at the leftmost reel. Each payline pays its single highest award.", mathVersion: "GAME MATHEMATICS · v0.2", sessionLabel: "THIS SESSION", latestResult: "ENGINE RESULT", jsonIntro: "Full result of the selected round. Download JSON saves the latest 100 rounds in this session.", spaceToSpin: "to spin", wildRule: "Substitutes for regular symbols", scatterRule: "3/4/5 → 1×/5×/20× + 8/10/12 FS", decreaseBet: "Decrease bet", increaseBet: "Increase bet", language: "Interface language", chooseGraphics: "Choose symbol artwork" });
  Object.assign(words.de, { studioLabel: "TESTSTUDIO", playgroundLabel: "DEIN TESTBEREICH", pageTitle: "Bereit zum Spielen.", pageIntro: "Runden testen, Bonus entdecken und eigene Grafiken hinzufügen.", demoMode: "DEMOMODUS", demoSubline: "Du spielst nur mit Testguthaben", gridMeta: "5 WALZEN · 20 GEWINNLINIEN", bonusReady: "3 Scatter starten den Bonus", loadingGame: "Walzen werden vorbereitet…", readyToSpin: "Bereit für die erste Drehung", spinHint: "Einsatz wählen und Walzen drehen.", autoRounds: "AUTOMATIK", speedNormal: "NORMAL", scenarioHint: "Ergebnisse kommen von der lokalen Spiel-Engine.", yourArtwork: "Deine Grafiken", knowYourSymbols: "DIE SYMBOLE", paytableIntro: "Spalten 3, 4 und 5 zeigen die Symbolanzahl. Gewinne als Vielfache des Gesamteinsatzes.", paytableFootnote: "Treffer beginnen links. Jede Gewinnlinie zahlt nur ihren höchsten Gewinn.", mathVersion: "SPIELMATHEMATIK · v0.2", sessionLabel: "DIESE SITZUNG", latestResult: "ENGINE-ERGEBNIS", jsonIntro: "Vollständiges Ergebnis der gewählten Runde. JSON herunterladen speichert die letzten 100 Runden dieser Sitzung.", spaceToSpin: "zum Drehen", wildRule: "Ersetzt reguläre Symbole", scatterRule: "3/4/5 → 1×/5×/20× + 8/10/12 FS", decreaseBet: "Einsatz senken", increaseBet: "Einsatz erhöhen", language: "Sprache der Oberfläche", chooseGraphics: "Symbolgrafiken wählen" });
  const interfaceWords = {
    pl: { autoplaySettings: "Ustawienia autoplay", turboSpin: "Turbo", turboHint: "Najszybsze animacje", quickSpin: "Szybko", quickHint: "Krótsze animacje", skipScreens: "Pomijaj ekrany", skipHint: "Wejście i koniec bonusu", autoplayStart: "URUCHOM AUTOPLAY", autoplayFootnote: "Jeden autoobrót to cała płatna runda wraz z darmowymi obrotami. STOP kończy serię po bieżącej rundzie.", hyperplayTitle: "Graj bez animacji bębnów", hyperplayDescription: "Tryb błyskawiczny pokazuje od razu wynik całej rundy, razem z bonusem.", hyperplayMode: "Tryb błyskawiczny", enabled: "WŁ.", disabled: "WYŁ.", featureScatters: "Za 3 / 4 / 5 Scatterów", featureMultiplier: "Wygrane linii w bonusie", featureMax: "MAKS. WYGRANA", featureRules: "Zobacz zasady ↗", autoActive: "Autoplay · ukończone rundy", autoStopped: "Autoplay zatrzymany", autoComplete: "Autoplay zakończony", bonusComplete: "Darmowe obroty zakończone", bonusSummary: "Darmowe obroty", settingsSaved: "Ustawienia zapisane", speedQuick: "Szybko", speedTurbo: "Turbo", speedInstant: "Błyskawicznie", autoplayStopHint: "Bieżąca runda zostanie dokończona.", bonusLineOnly: "Mnożnik dotyczy wygranych linii" },
    en: { autoplaySettings: "Autoplay settings", turboSpin: "Turbo", turboHint: "Fastest animations", quickSpin: "Quick spin", quickHint: "Shorter animations", skipScreens: "Skip screens", skipHint: "Bonus intro and outro", autoplayStart: "START AUTOPLAY", autoplayFootnote: "One autospin is a complete paid round, including all free spins. STOP ends the series after the current round.", hyperplayTitle: "Play without reel animations", hyperplayDescription: "Instant mode shows the complete round result immediately, including its bonus.", hyperplayMode: "Instant mode", enabled: "ON", disabled: "OFF", featureScatters: "For 3 / 4 / 5 Scatters", featureMultiplier: "Bonus line wins", featureMax: "MAXIMUM WIN", featureRules: "View game rules ↗", autoActive: "Autoplay · completed rounds", autoStopped: "Autoplay stopped", autoComplete: "Autoplay complete", bonusComplete: "Free spins completed", bonusSummary: "Free spins", settingsSaved: "Settings saved", speedQuick: "Quick", speedTurbo: "Turbo", speedInstant: "Instant", autoplayStopHint: "The current round will finish.", bonusLineOnly: "Multiplier applies to line wins" },
    de: { autoplaySettings: "Automatik-Einstellungen", turboSpin: "Turbo", turboHint: "Schnellste Animationen", quickSpin: "Schnell", quickHint: "Kürzere Animationen", skipScreens: "Bildschirme überspringen", skipHint: "Bonusstart und Bonusende", autoplayStart: "AUTOMATIK STARTEN", autoplayFootnote: "Eine automatische Drehung ist eine bezahlte Runde mit allen Freispielen. STOP beendet die Serie nach der laufenden Runde.", hyperplayTitle: "Ohne Walzenanimation spielen", hyperplayDescription: "Der Sofortmodus zeigt sofort das gesamte Rundenergebnis einschließlich Bonus.", hyperplayMode: "Sofortmodus", enabled: "AN", disabled: "AUS", featureScatters: "Für 3 / 4 / 5 Scatter", featureMultiplier: "Liniengewinne im Bonus", featureMax: "MAXIMALGEWINN", featureRules: "Spielregeln ansehen ↗", autoActive: "Automatik · beendete Runden", autoStopped: "Automatik gestoppt", autoComplete: "Automatik beendet", bonusComplete: "Freispiele beendet", bonusSummary: "Freispiele", settingsSaved: "Einstellungen gespeichert", speedQuick: "Schnell", speedTurbo: "Turbo", speedInstant: "Sofort", autoplayStopHint: "Die laufende Runde wird beendet.", bonusLineOnly: "Multiplikator gilt für Liniengewinne" }
  };
  Object.entries(interfaceWords).forEach(([lang, entries]) => Object.assign(words[lang], entries));
  Object.assign(words.pl, { autoActive: "Autoplay · wykonano", autoRetrying: "Autoplay · ponawiam odczyt rundy…", autoNoFunds: "Autoplay przerwany · za mało salda", autoConnectionError: "Autoplay przerwany · brak połączenia. Ponów odczyt rundy.", autoPresentationError: "Autoplay przerwany · błąd wyświetlania rundy" });
  Object.assign(words.en, { autoActive: "Autoplay · completed", autoRetrying: "Autoplay · retrying round result…", autoNoFunds: "Autoplay stopped · insufficient balance", autoConnectionError: "Autoplay stopped · connection lost. Retry the round result.", autoPresentationError: "Autoplay stopped · round display error" });
  Object.assign(words.de, { autoActive: "Automatik · abgeschlossen", autoRetrying: "Automatik · Ergebnis erneut laden…", autoNoFunds: "Automatik gestoppt · zu wenig Guthaben", autoConnectionError: "Automatik gestoppt · keine Verbindung. Rundenergebnis erneut laden.", autoPresentationError: "Automatik gestoppt · Anzeigefehler" });
  Object.assign(words.pl, { cascade: "Pokaż kaskadę", cascadeLabel: "KASKADA", cascadeDone: "Kaskady zakończone", cascadeSummary: "Kaskady w rundzie", cascadeLimit: "Osiągnięto techniczny limit kaskad w wersji testowej.", mathVersion: "WARIANT TESTOWY · v0.3 · KASKADY", footer: "Demo lokalne • saldo testowe • kaskady v0.3", randomNotice: "Losowe rundy z kaskadami. Saldo jest testowe; matematyka v0.3 wymaga nowego wyliczenia RTP." });
  Object.assign(words.en, { cascade: "Show cascades", cascadeLabel: "CASCADE", cascadeDone: "Cascades completed", cascadeSummary: "Cascades in round", cascadeLimit: "The prototype's technical cascade limit was reached.", mathVersion: "TEST VARIANT · v0.3 · CASCADES", footer: "Local demo • test balance • cascades v0.3", randomNotice: "Random rounds with falling cascades. Test balance; v0.3 requires a new RTP calculation." });
  Object.assign(words.de, { cascade: "Kaskaden zeigen", cascadeLabel: "KASKADE", cascadeDone: "Kaskaden beendet", cascadeSummary: "Kaskaden in der Runde", cascadeLimit: "Das technische Kaskadenlimit des Prototyps wurde erreicht.", mathVersion: "TESTVARIANTE · v0.3 · KASKADEN", footer: "Lokale Demo • Testguthaben • Kaskaden v0.3", randomNotice: "Zufallsrunden mit fallenden Kaskaden. Testguthaben; v0.3 benötigt eine neue RTP-Berechnung." });
  Object.assign(words.pl, { cascadesActive: "Kaskady aktywne", cascadeAfterWin: "Po wygranej", pageIntro: "Zakręć — po wygranej symbole automatycznie spadają i tworzą kolejne układy.", hyperplayDescription: "Pomija animacje bębnów i kaskad. Pokazuje od razu wynik całej rundy. Działa do odświeżenia strony." });
  Object.assign(words.en, { cascadesActive: "Cascades active", cascadeAfterWin: "After a win", pageIntro: "Spin — winning symbols disappear and the remaining symbols automatically fall into new combinations.", hyperplayDescription: "Skips reel and cascade animations and immediately shows the complete result. Applies until the page reloads." });
  Object.assign(words.de, { cascadesActive: "Kaskaden aktiv", cascadeAfterWin: "Nach einem Gewinn", pageIntro: "Drehen — nach einem Gewinn fallen die Symbole automatisch in neue Kombinationen.", hyperplayDescription: "Überspringt Walzen- und Kaskadenanimationen und zeigt sofort das Ergebnis. Gilt bis zum Neuladen." });
  words.pl.ruleText.splice(2, 0, "Po wygranej znikają symbole należące do wygrywających linii. Każde pole znika tylko raz, nawet jeśli należy do kilku linii. Pozostałe symbole spadają w dół w swoich kolumnach, a nowe wpadają z góry. Nowy układ jest sprawdzany ponownie bez kolejnej stawki. Scattery płacą i przyznają bonus tylko na początkowej planszy; nowe symbole w kaskadzie nie zawierają Scatterów. Rozwinięcie WILD odbywa się raz, na początku darmowego obrotu. Limit 5000× obejmuje całą rundę ze wszystkimi kaskadami i bonusem.");
  words.en.ruleText.splice(2, 0, "Winning line symbols disappear; a shared cell is removed once. Remaining symbols fall down within their columns and fresh symbols enter from above. Each new grid is evaluated at no extra bet. Scatters pay and award free spins only on the initial grid; refills contain no Scatters. WILD expansion happens once at the start of a free spin. The 5000× cap includes every cascade and the bonus.");
  words.de.ruleText.splice(2, 0, "Gewinnende Liniensymbole verschwinden; gemeinsame Felder werden nur einmal entfernt. Verbleibende Symbole fallen in ihrer Spalte nach unten, neue kommen von oben. Jedes neue Raster wird ohne weiteren Einsatz ausgewertet. Scatter zählen nur im anfänglichen Raster; neue Symbole enthalten keine Scatter. WILD erweitert sich einmal zu Beginn des Freispiels. Das Limit 5000× umfasst alle Kaskaden und den Bonus.");
  Object.assign(words.pl, { mathVersion: "RTP 96% · v0.4 · KASKADY", footer: "Demo lokalne • saldo testowe • RTP 96%", randomNotice: "Gra losowa · RTP teoretyczne 96% · limit rundy 5000×. Saldo jest testowe." });
  Object.assign(words.en, { mathVersion: "RTP 96% · v0.4 · CASCADES", footer: "Local demo • test balance • RTP 96%", randomNotice: "Random play · theoretical RTP 96% · round cap 5000×. Test balance only." });
  Object.assign(words.de, { mathVersion: "RTP 96% · v0.4 · KASKADEN", footer: "Lokale Demo • Testguthaben • RTP 96%", randomNotice: "Zufallsspiel · theoretischer RTP 96% · Rundenlimit 5000×. Testguthaben." });
  words.pl.ruleText.push("Teoretyczny RTP gry losowej wynosi 96%. Jest liczony z ważonego zestawu pełnych rund, razem z kaskadami i bonusem. Najwyższa wygrana 5000× występuje średnio raz na 8 mln płatnych rund. Zwrot krótkiej sesji może znacznie odbiegać od RTP.");
  words.en.ruleText.push("Random play has a theoretical RTP of 96%, calculated from weighted complete rounds including cascades and bonuses. The 5000× maximum win occurs on average once per 8 million paid rounds. Short-session returns can differ substantially from RTP.");
  words.de.ruleText.push("Der theoretische RTP des Zufallsspiels beträgt 96%, berechnet aus gewichteten vollständigen Runden einschließlich Kaskaden und Bonus. Der Höchstgewinn 5000× tritt durchschnittlich einmal pro 8 Millionen bezahlten Runden auf. Kurze Sitzungen können erheblich vom RTP abweichen.");
  words.pl.sessionEnded = "Poprzednia sesja zakończyła się. Przerwanego obrotu nie ponowiono. Odczytano aktualną sesję testową.";
  words.en.sessionEnded = "The previous session ended. Its interrupted round was not replayed. The current test session has been loaded.";
  words.de.sessionEnded = "Die vorherige Sitzung wurde beendet. Ihre unterbrochene Runde wurde nicht erneut gespielt. Die aktuelle Testsitzung wurde geladen.";
  const autoCounts = [10, 25, 50, 100, 250, 500];
  const anyStartCopy = {
    pl: {middle:"3 obwarzanki na bębnach 2–4", mathVersion:"RTP 96% · v0.5 · DOWOLNY START", readyDetail:"3–5 kolejnych symboli na linii wygrywa od dowolnego bębna.", previewHint:"Podgląd linii; wygrywający ciąg może zaczynać się na bębnie 1, 2 lub 3.", paytableFootnote:"3–5 kolejnych symboli na aktywnej linii. Początek na dowolnym bębnie. Jedna najwyższa wypłata na linię.", reelRange:"Bębny", rule:"Plansza ma 5 bębnów i 3 rzędy. Wszystkie 20 linii jest aktywnych przy każdej stawce. Zwykłe symbole płacą za co najmniej 3 kolejne dopasowania na linii, zaczynając od dowolnego bębna: układy 1–2–3, 2–3–4 i 3–4–5 mogą wygrywać. WILD zastępuje zwykłe symbole. Każda linia wypłaca jeden najwyższy należny wynik, bez dodatkowych wypłat za jego krótsze fragmenty. Ten sam symbol może brać udział w wygranych na różnych aktywnych liniach."},
    en: {middle:"3 bread rings on reels 2–4", mathVersion:"RTP 96% · v0.5 · ANY START", readyDetail:"3–5 consecutive matching symbols on a payline win from any reel.", previewHint:"Payline preview; a winning run may start on reel 1, 2 or 3.", paytableFootnote:"3–5 consecutive matches on an active payline, starting on any reel. One highest award per line.", reelRange:"Reels", rule:"The grid has 5 reels and 3 rows. All 20 paylines are active on every bet. Regular symbols pay for at least 3 consecutive matches on a payline, starting on any reel: 1–2–3, 2–3–4 and 3–4–5 can win. WILD substitutes for regular symbols. Each payline pays one highest award, without extra awards for shorter parts of the same run. A symbol can participate in awards on different active paylines."},
    de: {middle:"3 Gebäckringe auf Walzen 2–4", mathVersion:"RTP 96% · v0.5 · BELIEBIGER START", readyDetail:"3–5 aufeinanderfolgende gleiche Symbole auf einer Gewinnlinie zählen ab jeder Walze.", previewHint:"Linienvorschau; ein Gewinn kann auf Walze 1, 2 oder 3 beginnen.", paytableFootnote:"3–5 aufeinanderfolgende Treffer auf einer aktiven Linie, ab jeder Walze. Nur der höchste Gewinn je Linie.", reelRange:"Walzen", rule:"Das Spielfeld hat 5 Walzen und 3 Reihen. Alle 20 Gewinnlinien sind aktiv. Normale Symbole zahlen für mindestens 3 aufeinanderfolgende Treffer auf einer Linie, beginnend auf jeder Walze: 1–2–3, 2–3–4 und 3–4–5 können gewinnen. WILD ersetzt normale Symbole. Jede Linie zahlt nur den höchsten Gewinn, ohne zusätzliche Gewinne für kürzere Teile derselben Folge. Ein Symbol kann auf mehreren aktiven Linien zu Gewinnen beitragen."}
  };
  for (const [lang, copy] of Object.entries(anyStartCopy)) {
    Object.assign(words[lang], copy); words[lang].ruleText[0] = copy.rule;
  }
  words.pl.settingsTitle = "Ustawienia gry"; words.en.settingsTitle = "Game settings"; words.de.settingsTitle = "Spieleinstellungen";
  words.pl.ruleText.push("Sterowanie: okrągły przycisk ze strzałką lub spacja rozpoczyna obrót. Minus i plus zmieniają stawkę. AUTO otwiera ustawienia i wymaga potwierdzenia serii; STOP kończy serię po bieżącej rundzie. Symbol tabeli otwiera wypłaty, i — zasady, a koło zębate — ustawienia wyglądu i języka. Po błędzie połączenia przycisk Ponów odczyt pobiera ten sam wynik, bez ponownego pobrania stawki.");
  words.en.ruleText.push("Controls: the round arrow button or Space starts a spin. Minus and plus change the bet. AUTO opens settings and requires confirmation; STOP ends autoplay after the current round. The table icon opens payouts, i opens rules, and the gear opens appearance and language settings. After a connection error, Retry Result reads the same round without charging another bet.");
  words.de.ruleText.push("Steuerung: Der runde Pfeil oder die Leertaste startet eine Runde. Minus und Plus ändern den Einsatz. AUTO öffnet die Einstellungen und erfordert eine Bestätigung; STOP beendet die Serie nach der aktuellen Runde. Das Tabellensymbol öffnet Auszahlungen, i die Regeln und das Zahnrad Aussehen und Sprache. Nach einem Verbindungsfehler lädt Ergebnis laden dieselbe Runde ohne erneuten Einsatz.");
  const artwork = window.PG_ART || null;
  Object.assign(words.pl, { artSet: "Zestaw symboli", artSetHint: "Zmień klimat gry. Stawki i wypłaty pozostają takie same.", artCatalog: "Wszystkie symbole · 18", catalogHint: "Każdy zestaw zawiera 8 symboli zwykłych oraz WILD i SCATTER. Złote oznaczenie wskazuje symbole bieżącego zestawu.", inSet: "W tym zestawie", otherSet: "Inny zestaw", artReady: "Grafiki gotowe do gry", artError: "Nie udało się wczytać grafik. Odśwież stronę, aby spróbować ponownie.", artRules: "Zestawy Polska, Legendy i Klasyczny zmieniają wyłącznie nazwy i grafiki. Każdy zestaw ma 8 zwykłych symboli oraz WILD i SCATTER. Obowiązuje tabela wypłat widoczna dla wybranego zestawu. Zmiana zestawu jest dostępna między rundami." });
  Object.assign(words.en, { artSet: "Symbol set", artSetHint: "Change the atmosphere. Bets and payouts stay the same.", artCatalog: "All symbols · 18", catalogHint: "Each set contains 8 regular symbols plus WILD and SCATTER. Gold marks the symbols in the current set.", inSet: "In this set", otherSet: "Other set", artReady: "Artwork ready to play", artError: "Artwork could not load. Refresh to try again.", artRules: "Poland, Legends and Classic change names and artwork only. Each set has 8 regular symbols plus WILD and SCATTER. The paytable shown applies to the selected set. Sets can be changed between rounds." });
  Object.assign(words.de, { artSet: "Symbolset", artSetHint: "Andere Atmosphäre. Einsätze und Auszahlungen bleiben gleich.", artCatalog: "Alle Symbole · 18", catalogHint: "Jedes Set enthält 8 normale Symbole sowie WILD und SCATTER. Gold markiert die Symbole des aktuellen Sets.", inSet: "In diesem Set", otherSet: "Anderes Set", artReady: "Grafiken spielbereit", artError: "Grafiken konnten nicht geladen werden. Seite neu laden.", artRules: "Polen, Legenden und Klassisch ändern nur Namen und Grafiken. Jedes Set hat 8 normale Symbole sowie WILD und SCATTER. Es gilt die angezeigte Gewinntabelle. Sets können zwischen den Runden geändert werden." });
  for (const lang of Object.keys(locale)) words[lang].ruleText.push(words[lang].artRules);
  words.pl.ruleText.push("WILD zastępuje wyłącznie osiem zwykłych symboli, nigdy Scattera. Nie ma własnej tabeli wypłat. Ciąg samych Wildów jest oceniany jako najwyżej płatny pasujący symbol P4 (Husarz): 3 / 4 / 5 Wildów na linii daje odpowiednio 1,6× / 8× / 40× całej stawki przed mnożnikiem bonusu. Przy kilku jednakowo płatnych układach na jednej linii wybierany jest układ zaczynający się najbardziej z lewej. Tylko jego pola należą do wygranej tej linii i są usuwane w kaskadzie; inne linie są oceniane osobno.");
  words.en.ruleText.push("WILD substitutes only for the eight regular symbols, never Scatter. It has no separate paytable. An all-WILD run is evaluated as the highest-paying matching symbol P4 (Hussar): 3 / 4 / 5 Wilds on a payline award 1.6× / 8× / 40× the total bet before the bonus multiplier. If several runs on one payline have the same highest award, the run starting furthest left wins. Only that run's cells belong to that payline's win and are removed in the cascade; other paylines are evaluated separately.");
  words.de.ruleText.push("WILD ersetzt nur die acht regulären Symbole, niemals Scatter. Es besitzt keine eigene Gewinntabelle. Eine Folge nur aus Wilds wird als höchstbezahltes passendes Symbol P4 (Husar) bewertet: 3 / 4 / 5 Wilds auf einer Gewinnlinie zahlen 1,6× / 8× / 40× des Gesamteinsatzes vor dem Bonusmultiplikator. Bei mehreren gleich hohen Gewinnen auf einer Linie zählt die Folge mit dem am weitesten links liegenden Anfang. Nur ihre Felder gehören zum Gewinn dieser Linie und werden in der Kaskade entfernt; andere Linien werden separat bewertet.");
  const getSaved = (key, fallback) => { try { return localStorage.getItem(key) || fallback; } catch { return fallback; } };
  const save = (key, value) => { try { localStorage.setItem(key, value); } catch {} };
  function savePending() {
    try {
      if (state.pending) sessionStorage.setItem("pg-pending-round", JSON.stringify({ session_id: state.sessionId, request: state.pending, autoplay: state.pendingAutoplay, autoTotal: state.autoTotal, autoCompleted: state.autoCompleted, presentation: state.presentation }));
      else sessionStorage.removeItem("pg-pending-round");
    } catch {} // Memory recovery and the unload warning still work if storage is disabled.
  }
  function savedPending() { try { return JSON.parse(sessionStorage.getItem("pg-pending-round") || "null"); } catch { return null; } }
  const transientError = error => error.uncertain || !error.status || error.status >= 500 || [408, 429].includes(error.status);
  const state = { lang: getSaved("pg-lang", "pl"), speed: "normal", skipScreens: getSaved("pg-skip-screens", "true") === "true", instant: false, autoCount: Number(getSaved("pg-auto-count", "100")), autoTotal: 0, autoCompleted: 0, autoStatus: "autoComplete", autoRetrying: false, pendingAutoplay: false, config: null, symbols: {}, images: {}, grid: [], cells: [], bet: 200, balance: 0, busy: false, online: false, auto: 0, pending: null, history: [], selected: null, currentSpin: null, currentBet: 200, cycle: null, autoTimer: null, stats: { rounds: 0, total_bet_cents: 0, total_win_cents: 0 } };
  if (!words[state.lang]) state.lang = "pl";
  if (!["normal", "quick", "turbo"].includes(state.speed)) state.speed = "normal";
  if (!autoCounts.includes(state.autoCount)) state.autoCount = 100;
  const t = key => words[state.lang][key] || words.pl[key] || key;
  const money = amount => new Intl.NumberFormat(locale[state.lang], { style: "currency", currency: state.config?.currency || "PLN" }).format(amount / (state.config?.amount_scale || 100));
  const betPreferenceKey = () => state.rgs ? `pg-rgs-bet-${state.rgs.sessionLabel}` : "pg-bet-cents";
  const roundMoney = (units, bet = state.currentBet) => state.rgs ? window.PG_RGS.payout(bet, units, state.config.payout_scale) : bet * units / state.config.payout_scale;
  const number = value => new Intl.NumberFormat(locale[state.lang], { maximumFractionDigits: 2 }).format(value);
  state.theme = getSaved("pg-art-theme", "polska");
  if (!artwork?.themes[state.theme]) state.theme = "polska";
  state.artReady = false;
  state.presentation = null;
  const themedSymbol = code => state.artReady ? artwork?.symbols[artwork.themes[state.theme]?.symbols[code]] : null;
  const symbolName = code => themedSymbol(code)?.[state.lang] || state.symbols[code]?.[state.lang] || code;
  const lastFrame = spin => spin.cascades?.at(-1) || spin;
  const cascadeCount = round => [round.base, ...round.free_spins].reduce((sum, spin) => sum + Math.max(0, (spin.cascades?.length || 1) - 1), 0);
  const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
  const wait = (normal, fast = 100) => delay(window.matchMedia("(prefers-reduced-motion: reduce)").matches ? Math.min(fast, 60) : state.speed === "turbo" ? Math.min(fast, 35) : state.speed === "quick" ? fast : normal);
  let toastTimer;
  function toast(message) { $("toast").textContent = message; $("toast").classList.add("visible"); clearTimeout(toastTimer); toastTimer = setTimeout(() => $("toast").classList.remove("visible"), 5500); }
  async function api(path, data) {
    if (state.rgs && path === "/api/spin") return state.rgs.play(data);
    if (state.rgs && path === "/api/wallet") return state.rgs.readWallet();
    if (state.rgs && path.startsWith("/api/")) throw new Error("rgs_local_api_disabled");
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(path, { method: data === undefined ? "GET" : "POST", headers: data === undefined ? {} : { "Content-Type": "application/json", "X-Game-Session": state.sessionId || "" }, body: data === undefined ? undefined : JSON.stringify(data), credentials: "same-origin", cache: "no-store", signal: controller.signal });
      const result = await response.json();
      if (!response.ok) { const error = new Error(result.error || "Request failed"); error.code = result.code; error.status = response.status; throw error; }
      return result;
    } finally { clearTimeout(timer); }
  }
  function preloadArtwork(file) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      const finish = error => {
        clearTimeout(timer); image.onload = image.onerror = null;
        error ? reject(error) : resolve();
      };
      const timer = setTimeout(() => finish(new Error("Artwork timeout")), 15000);
      image.onload = () => finish(); image.onerror = () => finish(new Error("Artwork unavailable"));
      image.src = file.src;
    });
  }
  async function currentWallet(result) {
    if (state.rgs) return { ...state.rgs.wallet(), ...result.stats };
    let wallet;
    try { wallet = await api("/api/wallet"); }
    catch (error) {
      if (["session_expired", "session_changed"].includes(error.code)) throw error;
      // A wallet-read rejection is not a rejection of the already accepted bet.
      // Preserve its request ID even for 4xx responses from an outdated server.
      throw new Error(t("requestError"));
    }
    if (wallet?.session_id !== state.sessionId) {
      const error = new Error(t("sessionEnded")); error.code = "session_changed"; error.status = 409; throw error;
    }
    const values = [wallet.balance_cents, wallet.rounds, wallet.total_bet_cents, wallet.total_win_cents];
    if (!values.every(value => Number.isSafeInteger(value) && value >= 0) || wallet.rounds < result.stats.rounds) throw new Error(t("requestError"));
    return wallet;
  }
  function applyWallet(wallet) {
    if (wallet.rounds < state.stats.rounds) return;
    state.balance = wallet.balance_cents; statsFrom(wallet);
  }
  const iconShapes = {
    L1: '<path d="M50 8 83 50 50 92 17 50Z"/><path d="m50 8 12 42-12 42-12-42Zm-33 42h66" fill="none" stroke="currentColor" opacity=".5"/>',
    L2: '<path d="M50 10C39 29 18 37 18 55c0 21 24 28 32 11 8 17 32 10 32-11C82 37 61 29 50 10Zm0 53-12 25h24Z"/>',
    L3: '<path d="M50 87 18 55C-4 29 27 5 50 29 73 5 104 29 82 55Z"/>',
    L4: '<path d="M50 12a18 18 0 0 0-13 31C7 30 4 75 29 75c11 0 17-7 21-16 4 9 10 16 21 16 25 0 22-45-8-32A18 18 0 0 0 50 12Zm0 48L38 90h24Z"/>',
    P1: '<path d="M50 12C28 28 30 47 45 61 19 42 8 48 16 65c5 12 22 13 30 4L39 88h22l-7-19c8 9 25 8 30-4 8-17-3-23-29-4C70 47 72 28 50 12Z"/><path d="M30 73h40" fill="none" stroke="currentColor"/>',
    P2: '<path d="M25 17h50v16c0 19-9 30-21 34v15h14v7H32v-7h14V67C34 63 25 52 25 33Zm0 8H13v13c0 15 12 23 25 23M75 25h12v13c0 15-12 23-25 23"/>',
    P3: '<path d="m13 29 22 17L50 15l15 31 22-17-9 47H22Zm10 55h54"/><circle cx="50" cy="57" r="6" fill="currentColor"/>',
    P4: '<path d="M28 17v46c0 14 22 26 22 26s22-12 22-26V17Z"/><path d="M36 64 50 30l14 34-14-8Z" fill="currentColor"/><path d="m24 29-14-9 9 17-11-4 10 17-10-3 13 18M76 29l14-9-9 17 11-4-10 17 10-3-13 18" fill="none"/>',
    WILD: '<path d="m50 8 11 25 27 3-20 19 6 29-24-14-24 14 6-29L12 36l27-3Z"/><text x="50" y="59" text-anchor="middle" fill="currentColor" stroke="none" font-size="31" font-weight="900">W</text>',
    SCATTER: '<circle cx="50" cy="50" r="29"/><path d="M50 4v10m0 72v10M4 50h10m72 0h10M17 17l8 8m50 50 8 8M17 83l8-8m50-50 8-8" fill="none"/><path d="m50 28 7 14 16 2-12 11 3 17-14-8-14 8 3-17-12-11 16-2Z" fill="currentColor"/>'
  };
  let artSequence = 0;
  function art(code, artId = null) {
    const wrapper = document.createElement("span"); wrapper.className = "symbol-art";
    const entry = artId ? artwork?.symbols[artId] : themedSymbol(code);
    if (!artId && state.images[code]) {
      const img = document.createElement("img"); img.src = state.images[code]; img.alt = "";
      img.addEventListener("error", () => { delete state.images[code]; wrapper.replaceWith(art(code)); toast(`${t("imageFailed")}: ${code}`); }, { once: true });
      wrapper.append(img);
    } else if (state.artReady && entry) {
      const file = artwork.files[entry.file];
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("class", "atlas-art"); svg.setAttribute("viewBox", entry.box.join(" "));
      svg.setAttribute("aria-hidden", "true"); svg.setAttribute("overflow", "hidden");
      const img = document.createElementNS("http://www.w3.org/2000/svg", "image");
      img.setAttribute("href", file.src); img.setAttribute("width", file.width); img.setAttribute("height", file.height);
      // A viewBox alone can expose adjacent atlas cells in the letterbox area.
      // Clip in source coordinates as well, so every symbol remains isolated.
      const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
      const clip = document.createElementNS("http://www.w3.org/2000/svg", "clipPath");
      const clipId = `pg-art-${++artSequence}`; clip.setAttribute("id", clipId);
      const crop = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      for (const [index, key] of ["x", "y", "width", "height"].entries()) crop.setAttribute(key, entry.box[index]);
      clip.append(crop); defs.append(clip); img.setAttribute("clip-path", `url(#${clipId})`);
      svg.append(defs, img); wrapper.append(svg);
    } else {
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.setAttribute("viewBox", "0 0 100 100"); svg.setAttribute("aria-hidden", "true");
      svg.innerHTML = iconShapes[code] || iconShapes.L1; wrapper.append(svg);
    }
    return wrapper;
  }
  function paintCell(row, col, code) {
    const cell = state.cells[row * 5 + col]; cell.dataset.symbol = code;
    cell.setAttribute("aria-label", `${row + 1}, ${col + 1}: ${symbolName(code)}`);
    const name = document.createElement("span"); name.className = "symbol-name"; name.textContent = symbolName(code);
    cell.replaceChildren(art(code), name);
  }
  function showGrid(grid) { state.grid = grid.map(row => [...row]); grid.forEach((row, r) => row.forEach((code, c) => paintCell(r, c, code))); }
  function createGrid() {
    $("reel-grid").replaceChildren();
    for (let row = 0; row < 3; row++) for (let col = 0; col < 5; col++) {
      const cell = document.createElement("div"); cell.className = "symbol-cell"; cell.dataset.row = row; cell.dataset.col = col; cell.setAttribute("role", "img"); $("reel-grid").append(cell); state.cells.push(cell);
    }
    showGrid([["L1", "L2", "P3", "L3", "P2"], ["P4", "L4", "WILD", "P1", "P4"], ["L3", "P2", "L1", "SCATTER", "L2"]]);
  }
  function clearLines() { clearInterval(state.cycle); state.cycle = null; $("payline-overlay").replaceChildren(); state.cells.forEach(c => c.classList.remove("winning", "dimmed", "expanding", "scatter-highlight")); $("win-lines").replaceChildren(); }
  function drawLine(rows, count = 5, preview = false, startReel = 0) {
    $("payline-overlay").replaceChildren();
    const svg = $("payline-overlay");
    const addPath = (start, length, opacity, width) => {
      const path = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
      path.setAttribute("points", rows.slice(start, start + length).map((row, col) => `${(start + col) * 100 + 50},${row * 100 + 50}`).join(" "));
      path.setAttribute("fill", "none"); path.setAttribute("stroke", preview ? "#d9b868" : "#67e8f9"); path.setAttribute("stroke-width", width); path.setAttribute("stroke-linecap", "round"); path.setAttribute("stroke-linejoin", "round"); path.setAttribute("opacity", opacity); svg.append(path);
    };
    addPath(0, 5, .22, 2); addPath(startReel, count, .95, 3);
    state.cells.forEach(c => { const r = Number(c.dataset.row), col = Number(c.dataset.col); const active = rows[col] === r && col >= startReel && col < startReel + count; c.classList.toggle("winning", active); c.classList.toggle("dimmed", !active && !preview); });
  }
  function showLineWin(win) {
    drawLine(win.rows, win.count, false, win.start_reel ?? 0);
    $("win-detail").textContent = `${t("line")} ${win.line_id} · ${symbolName(win.symbol)} ×${win.count} · ${t("rawLine")}: ${money(roundMoney(win.payout_units))}${win.line_multiplier > 1 ? ` · ×${win.line_multiplier}` : ""}`;
    $("win-detail").textContent += ` · ${t("reelRange")} ${(win.start_reel ?? 0) + 1}–${(win.start_reel ?? 0) + win.count}`;
    $("win-lines").querySelectorAll("button").forEach(b => b.classList.toggle("active", Number(b.dataset.line) === win.line_id));
  }
  function presentWins(spin, cycle = false) {
    clearLines(); state.currentSpin = spin;
    spin.line_wins.forEach(win => { const button = document.createElement("button"); button.type = "button"; button.className = "line-chip"; button.dataset.line = win.line_id; button.textContent = `${t("line")} ${win.line_id}`; button.addEventListener("click", () => { clearInterval(state.cycle); showLineWin(win); }); $("win-lines").append(button); });
    if (spin.line_wins.length) {
      let index = 0; showLineWin(spin.line_wins[0]);
      if (cycle && spin.line_wins.length > 1) state.cycle = setInterval(() => { index = (index + 1) % spin.line_wins.length; showLineWin(spin.line_wins[index]); }, 2100);
    } else {
      $("win-detail").textContent = spin.scatter_payout_units ? `${t("scatterWin")}: ${money(roundMoney(spin.scatter_payout_units))}` : t("readyDetail");
      if (spin.scatter_count >= 3) state.cells.forEach(cell => cell.classList.toggle("winning", cell.dataset.symbol === "SCATTER"));
    }
  }
  function statsFrom(data) { const stats = data.stats || data; state.stats = { rounds: stats.rounds || 0, total_bet_cents: stats.total_bet_cents || 0, total_win_cents: stats.total_win_cents || 0 }; }
  function refreshStats() {
    $("balance-value").textContent = money(state.balance); $("bet-value").textContent = money(state.bet);
    $("meter-balance").textContent = money(state.balance); $("meter-bet").textContent = money(state.bet);
    const net = state.stats.total_win_cents - state.stats.total_bet_cents;
    $("net-value").textContent = `${net > 0 ? "+" : ""}${money(net)}`; $("net-value").classList.toggle("negative", net < 0);
    $("rounds-value").textContent = number(state.stats.rounds);
  }
  function setWin(cents) { $("total-win-value").textContent = money(cents); $("meter-win").textContent = money(cents); }
  function roundNote(result) {
    const free = result?.round.free_spins || [];
    const cascades = result ? cascadeCount(result.round) : 0;
    $("cascade-status").hidden = false; $("cascade-label").textContent = t(cascades ? "cascadeSummary" : "cascadesActive"); $("cascade-count").textContent = cascades || t("cascadeAfterWin");
    const notes = [];
    if (result?.round.cap_reduction_units || result?.round.payout_units >= state.config?.max_win_units) notes.push(t("cap"));
    if (state.instant && free.length) notes.push(`${free.length} ${t("bonusSummary")} · ${t("bonusTotal")}: ${money(roundMoney(result.round.bonus_payout_units, result.bet_cents))}`);
    if (cascades) notes.push(`${t("cascadeSummary")}: ${cascades}`);
    if (result && [result.round.base, ...free].some(spin => spin.cascade_limit_reached)) notes.push(t("cascadeLimit"));
    const message = notes.join(" · ");
    $("round-note").textContent = message; $("round-note").hidden = !message;
  }
  function renderAutoplaySettings() {
    $("turbo-option").checked = state.speed === "turbo";
    $("quick-option").checked = state.speed === "quick";
    $("skip-screens-option").checked = state.skipScreens;
    $("auto-count").value = autoCounts.indexOf(state.autoCount);
    $("auto-count").setAttribute("aria-valuetext", String(state.autoCount));
    $("auto-count-value").value = state.autoCount;
    $("autoplay-start").textContent = `${t("autoplayStart")} (${state.autoCount})`;
    document.querySelectorAll("[data-count]").forEach(button => button.setAttribute("aria-pressed", String(Number(button.dataset.count) === state.autoCount)));
    $("hyperplay-button").setAttribute("aria-pressed", String(state.instant));
    $("hyperplay-state").textContent = t(state.instant ? "enabled" : "disabled");
    document.querySelector(".slot-cabinet").classList.toggle("skip-presentation", state.instant);
  }
  function controls() {
    const blocked = state.busy || !state.online;
    if ($("theme-select")) $("theme-select").disabled = blocked || !!state.pending || !!state.auto || !state.artReady;
    if ($("catalog-button")) $("catalog-button").disabled = !state.artReady;
    $("lang-select").disabled = state.busy || !!state.pending || !!state.auto;
    $("spin-button").disabled = blocked;
    $("spin-label").textContent = state.busy ? t("spinning") : state.pending ? t("retry") : state.auto ? t("stopAuto") : $("test-mode-select").value === "random" ? t("spin") : t($("test-mode-select").value);
    $("spin-button").setAttribute("aria-label", $("spin-label").textContent);
    $("spin-button").title = $("spin-label").textContent;
    $("spin-button").classList.toggle("retry-state", !!state.pending && !state.busy);
    $("spin-button").classList.toggle("auto-running", state.auto > 0 && !state.pending);
    $("bet-decrease").disabled = blocked || !!state.pending || !!state.auto || state.bet === state.config?.bet_options_cents[0];
    $("bet-increase").disabled = blocked || !!state.pending || !!state.auto || state.bet === state.config?.bet_options_cents.at(-1);
    for (const id of ["test-mode-select", "reset-button", "assets-button", "playline-select"]) $(id).disabled = blocked || !!state.pending || !!state.auto;
    if (state.rgs) for (const id of ["test-mode-select", "reset-button"]) $(id).disabled = true;
    $("auto-button").disabled = (!state.auto && (blocked || !!state.pending || $("test-mode-select").value !== "random"));
    $("auto-label").textContent = state.auto ? t("stopAuto") : t("auto"); $("auto-button").classList.toggle("active", state.auto > 0); $("auto-button").setAttribute("aria-pressed", String(state.auto > 0));
    $("auto-count").disabled = blocked || !!state.pending || !!state.auto;
    $("autoplay-start").disabled = blocked || !!state.pending || !!state.auto || $("test-mode-select").value !== "random";
    for (const id of ["speed-button", "turbo-option", "quick-option", "skip-screens-option", "hyperplay-button"]) $(id).disabled = blocked || !!state.auto;
    $("export-button").disabled = !state.history.length || state.busy || !!state.pending;
    $("details-button").disabled = !state.history.length;
    const connected = state.online && !state.connectionLost;
    $("connection-status").textContent = t(connected ? "connected" : "offline"); $("connection-status").classList.toggle("offline", !connected);
    const speedLabel = t(state.instant ? "speedInstant" : state.speed === "normal" ? "normal" : state.speed === "quick" ? "speedQuick" : "speedTurbo");
    $("speed-button").textContent = `ϟ ${speedLabel}`; $("speed-button").setAttribute("aria-pressed", String(state.instant || state.speed !== "normal")); $("speed-button").setAttribute("aria-label", `${t("speed")}: ${speedLabel}`);
    $("autoplay-progress").hidden = !state.autoTotal;
    $("autoplay-progress-label").textContent = t(state.autoRetrying ? "autoRetrying" : state.auto ? "autoActive" : state.autoStatus);
    $("autoplay-progress-value").textContent = `${state.autoCompleted} / ${state.autoTotal}`;
    $("autoplay-stop").hidden = !state.auto;
    $("test-hint").textContent = t($("test-mode-select").value === "random" ? "randomNotice" : "scenarioNotice");
    $("test-hint").classList.toggle("scenario-notice", $("test-mode-select").value !== "random");
    renderAutoplaySettings();
  }
  function stopAuto(reason = "autoStopped") { if (state.auto) state.autoStatus = reason; state.auto = 0; clearTimeout(state.autoTimer); state.autoTimer = null; controls(); }
  function scheduleAutoSpin() {
    clearTimeout(state.autoTimer); state.autoTimer = null;
    if (!state.auto || state.busy || state.pending) return;
    state.autoTimer = setTimeout(() => {
      state.autoTimer = null;
      if (state.auto > 0) spin();
    }, state.instant ? 180 : state.speed === "turbo" ? 120 : state.speed === "quick" ? 300 : 850);
  }
  async function requestSpinResult(autoplayRound) {
    const request = state.pending;
    try {
      for (let attempt = 0; ; attempt++) {
        try { const result = await api("/api/spin", request); validateSpinResponse(result, request); const wallet = await currentWallet(result); state.connectionLost = false; return { ...result, wallet }; }
        catch (error) {
          if (state.rgs || !autoplayRound || !transientError(error) || attempt >= 2) throw error;
          state.autoRetrying = true; controls();
          await delay(500 * (attempt + 1));
        }
      }
    } finally { state.autoRetrying = false; }
  }
  function validateSpinResponse(result, request) {
    const integer = value => Number.isSafeInteger(value) && value >= 0;
    const require = condition => { if (!condition) throw new Error(t("requestError")); };
    const equal = (a, b) => JSON.stringify(a) === JSON.stringify(b);
    const grid = value => Array.isArray(value) && value.length === 3 && value.every(row => Array.isArray(row) && row.length === 5 && row.every(symbol => state.config.symbols.includes(symbol)));
    const round = result?.round;
    require(result && result.request_id === request.request_id && result.session_id === state.sessionId && result.math_version === state.config.math_version && result.bet_cents === request.bet_cents && result.mode === request.mode && typeof result.round_id === "string" && result.is_scenario === (request.mode !== "random") && integer(result.balance_cents) && integer(result.balance_before_cents) && integer(result.win_cents) && result.stats && [result.stats.rounds, result.stats.total_bet_cents, result.stats.total_win_cents].every(integer) && round && Array.isArray(round.free_spins) && Array.isArray(round.free_spin_credits) && round.free_spin_credits.length === round.free_spins.length && round.free_spin_credits.every(integer));
    if (state.rgs) require(result.rgs === true && typeof result.rgs_active === "boolean" && result.mode === "random" && result.balance_cents === result.balance_before_cents - result.bet_cents + (result.rgs_active ? 0 : result.win_cents));
    else require(result.balance_cents === result.balance_before_cents + (result.is_scenario ? 0 : result.win_cents - result.bet_cents));
    let remaining = state.config.max_win_units, rawRound = 0;
    function validateSpin(value, free) {
      require(value && grid(value.grid) && grid(value.evaluation_grid) && integer(value.payout_units) && integer(value.scatter_payout_units) && integer(value.raw_payout_units) && integer(value.line_payout_units) && Array.isArray(value.line_wins) && Array.isArray(value.cascades) && value.cascades.length > 0 && value.cascades.length <= state.config.max_cascades);
      const multiplier = free ? state.config.fs_line_multiplier : 1;
      const scatterCount = value.grid.flat().filter(symbol => symbol === "SCATTER").length;
      const award = free ? 0 : state.config.free_spins[Math.min(5, scatterCount)] || 0;
      require(value.scatter_count === scatterCount && value.scatter_payout_units === (state.config.scatter_paytable_units[Math.min(5, scatterCount)] || 0) && value.free_spins_awarded === award && value.bonus_triggered === (award > 0) && value.line_multiplier === multiplier && typeof value.cascade_limit_reached === "boolean");
      const initial = value.grid.map(row => [...row]);
      if (value.expanding_reel !== null) {
        require(free && [1, 2, 3].includes(value.expanding_reel));
        initial.forEach(row => { row[value.expanding_reel] = "WILD"; });
      }
      require(equal(initial, value.evaluation_grid) && equal(value.cascades[0].evaluation_grid, initial) && equal(value.line_wins, value.cascades[0].line_wins));
      let credited = Math.min(remaining, value.scatter_payout_units), rawLines = 0;
      value.cascades.forEach((step, index) => {
        require(step && grid(step.evaluation_grid) && Array.isArray(step.line_wins) && Array.isArray(step.removed_positions) && Array.isArray(step.movements));
        let raw = 0;
        const positions = new Set(), lines = new Set();
        step.line_wins.forEach(win => {
          require(win && integer(win.line_id) && win.line_id >= 1 && win.line_id <= state.config.paylines.length && !lines.has(win.line_id) && equal(win.rows, state.config.paylines[win.line_id - 1]) && integer(win.start_reel) && Number.isInteger(win.count) && win.count >= 3 && win.start_reel + win.count <= 5 && win.line_multiplier === multiplier && integer(win.payout_units) && win.payout_units > 0 && win.payout_units === state.config.paytable_units[win.symbol]?.[win.count] * multiplier);
          lines.add(win.line_id); raw += win.payout_units;
          for (let col = win.start_reel; col < win.start_reel + win.count; col++) {
            const symbol = step.evaluation_grid[win.rows[col]][col];
            require(symbol === win.symbol || symbol === "WILD"); positions.add(`${win.rows[col]},${col}`);
          }
        });
        require(integer(raw) && step.line_payout_units === raw && step.payout_units === Math.min(raw, remaining - credited));
        credited += step.payout_units; rawLines += raw;
        const next = value.cascades[index + 1];
        if (!next) {
          require(step.removed_positions.length === 0 && step.movements.length === 0 && (!step.line_wins.length || credited === remaining || value.cascade_limit_reached));
          return;
        }
        require(grid(next.evaluation_grid) && positions.size > 0 && credited < remaining);
        const removed = step.removed_positions.map(position => {
          require(Array.isArray(position) && position.length === 2 && position.every(Number.isInteger) && position[0] >= 0 && position[0] < 3 && position[1] >= 0 && position[1] < 5);
          return position.join(",");
        });
        require(removed.length === positions.size && new Set(removed).size === removed.length && removed.every(position => positions.has(position)));
        const expectedMoves = [];
        for (let col = 0; col < 5; col++) {
          const survivors = [0, 1, 2].filter(row => !positions.has(`${row},${col}`));
          const holes = 3 - survivors.length;
          for (let row = 0; row < holes; row++) {
            const symbol = next.evaluation_grid[row][col]; require(symbol !== "SCATTER");
            expectedMoves.push([symbol, row - holes, row, col]);
          }
          survivors.forEach((from, n) => {
            const to = holes + n, symbol = step.evaluation_grid[from][col];
            require(next.evaluation_grid[to][col] === symbol);
            if (from !== to) expectedMoves.push([symbol, from, to, col]);
          });
        }
        const moves = step.movements.map(move => { require(move && typeof move === "object"); return [move.symbol, move.from_row, move.to_row, move.reel]; });
        require(equal(moves.map(JSON.stringify).sort(), expectedMoves.map(JSON.stringify).sort()));
      });
      require(value.line_payout_units === rawLines && value.raw_payout_units === rawLines + value.scatter_payout_units && value.payout_units === credited);
      remaining -= credited; rawRound += value.raw_payout_units;
    }
    validateSpin(round.base, false);
    require(round.free_spins.length <= round.base.free_spins_awarded);
    round.free_spins.forEach((spin, index) => { require(remaining > 0); validateSpin(spin, true); require(round.free_spin_credits[index] === spin.payout_units); });
    require(round.free_spins.length === round.base.free_spins_awarded || remaining === 0);
    const expectedWin = state.rgs ? window.PG_RGS.payout(result.bet_cents, round.payout_units, state.config.payout_scale) : Math.floor(result.bet_cents * round.payout_units / state.config.payout_scale);
    require(round.payout_units === state.config.max_win_units - remaining && round.raw_payout_units === rawRound && round.cap_reduction_units === rawRound - round.payout_units && round.bonus_payout_units === round.free_spin_credits.reduce((sum, value) => sum + value, 0) && result.win_cents === expectedWin);
  }
  async function announceBonus(title, detail) {
    if (state.skipScreens || state.instant) return;
    $("bonus-announcement-title").textContent = title; $("bonus-announcement-detail").textContent = detail; $("bonus-announcement").hidden = false;
    try { await delay(1400); } finally { $("bonus-announcement").hidden = true; }
  }
  async function tumbleTransition(step, next) {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const duration = reduced ? 0 : state.speed === "turbo" ? 140 : state.speed === "quick" ? 240 : 480;
    const layer = $("cascade-layer");
    clearLines();
    state.cells.forEach(cell => cell.style.setProperty("--cascade-duration", `${duration}ms`));
    for (const [row, col] of step.removed_positions) state.cells[row * 5 + col].classList.add("cascade-removing");
    await delay(reduced ? 0 : Math.round(duration * .6));
    state.cells.forEach(cell => cell.classList.remove("cascade-removing", "cascade-winning"));
    showGrid(next.evaluation_grid);
    layer.replaceChildren();
    const rowHeight = $("reels-stage").getBoundingClientRect().height / 3;
    for (const move of step.movements) {
      const cell = state.cells[move.to_row * 5 + move.reel]; cell.classList.add("cascade-vacant");
      const token = document.createElement("div"); token.className = "cascade-token"; token.dataset.symbol = move.symbol;
      token.style.left = `${move.reel * 20}%`; token.style.top = `${move.to_row * 100 / 3}%`;
      token.style.setProperty("--fall-offset", `${(move.from_row - move.to_row) * rowHeight}px`);
      token.style.setProperty("--cascade-duration", `${duration}ms`);
      const name = document.createElement("span"); name.className = "symbol-name"; name.textContent = symbolName(move.symbol);
      token.append(art(move.symbol), name); layer.append(token);
    }
    layer.hidden = false;
    try { await delay(duration); }
    finally { layer.hidden = true; layer.replaceChildren(); state.cells.forEach(cell => cell.classList.remove("cascade-vacant", "cascade-removing", "cascade-winning")); }
  }
  async function animateCascades(spin, credit) {
    const frames = spin.cascades || [];
    if (!frames.length) return;
    const before = state.presentedUnits || 0;
    let credited = Math.min(credit, spin.scatter_payout_units || 0);
    for (let i = 0; i < frames.length; i++) {
      const frame = frames[i]; showGrid(frame.evaluation_grid); presentWins(frame);
      credited = Math.min(credit, credited + frame.payout_units);
      setWin(roundMoney(before + credited));
      if (i + 1 < frames.length) {
        $("cascade-status").hidden = false; $("cascade-label").textContent = t("cascadeLabel"); $("cascade-count").textContent = i + 1;
        $("win-caption").textContent = `${t("cascadeLabel")} ${i + 1} · ${money(roundMoney(credited))}`;
        const winning = new Set(frame.removed_positions.map(([row, col]) => row * 5 + col));
        state.cells.forEach((cell, index) => { cell.classList.remove("dimmed"); cell.classList.toggle("cascade-winning", winning.has(index)); });
        await wait(650, 280);
        await tumbleTransition(frame, frames[i + 1]);
      }
    }
    state.presentedUnits = before + credit;
    if (frames.length > 1) { $("cascade-label").textContent = t("cascadeDone"); $("cascade-count").textContent = frames.length - 1; }
  }
  async function animateSpin(spin, credit, index, total) {
    clearLines(); $("playline-select").value = "none";
    state.cells.forEach(cell => cell.classList.add("spinning"));
    await wait(360, 55);
    state.grid = spin.grid.map(row => [...row]);
    for (let col = 0; col < 5; col++) {
      for (let row = 0; row < 3; row++) { paintCell(row, col, spin.grid[row][col]); state.cells[row * 5 + col].classList.remove("spinning"); }
      await wait(105, 22);
    }
    if (spin.expanding_reel !== null) {
      if (spin.scatter_count >= 3) { state.cells.forEach(c => c.classList.toggle("scatter-highlight", c.dataset.symbol === "SCATTER")); $("win-detail").textContent = `${t("scatterWin")}: ${money(roundMoney(spin.scatter_payout_units))}`; await wait(650, 90); }
      $("bonus-label").textContent = `${t("charge")} · ${t("expanded")} ${spin.expanding_reel + 1}`;
      for (let row = 0; row < 3; row++) { paintCell(row, spin.expanding_reel, "WILD"); state.cells[row * 5 + spin.expanding_reel].classList.add("expanding"); }
      state.grid = spin.evaluation_grid.map(row => [...row]); await wait(550, 100);
    }
    await animateCascades(spin, credit);
    $("win-caption").textContent = `${index ? `${t("freeSpin")} ${index}/${total}` : t("roundWin")} · ${money(roundMoney(credit))}`;
    presentWins(lastFrame(spin));
    if (index) $("bonus-progress").textContent = `${index} / ${total}`;
  }
  async function spin() {
    if (state.busy || !state.online) return;
    const autoplayRound = state.auto > 0 || !!state.pendingAutoplay;
    if (!autoplayRound) state.autoTotal = 0;
    if (!state.pending && $("test-mode-select").value === "random" && state.balance < state.bet) { stopAuto("autoNoFunds"); toast(t("noFunds")); return; }
    clearTimeout(state.autoTimer); state.busy = true; controls();
    roundNote(null);
    if (!state.pending) { state.pending = { bet_cents: state.bet, mode: $("test-mode-select").value, request_id: crypto.randomUUID() }; state.pendingAutoplay = autoplayRound; }
    savePending();
    let result;
    try {
      result = await requestSpinResult(autoplayRound);
    } catch (error) {
      stopAuto(error.code === "insufficient_funds" ? "autoNoFunds" : "autoConnectionError"); state.busy = false;
      state.connectionLost = transientError(error);
      const rejection = error.code === "insufficient_funds" ? t("noFunds") : state.rgs ? t("loadError") : error.message;
      if (!transientError(error)) { state.pending = null; state.pendingAutoplay = false; savePending(); toast(rejection); }
      else toast(t(state.rgs ? "rgsPending" : "requestError"));
      if (["session_expired", "session_changed", "result_expired"].includes(error.code)) { state.online = false; $("win-caption").textContent = t("offline"); $("win-detail").textContent = rejection; }
      state.cells.forEach(c => c.classList.remove("spinning")); controls(); return;
    }
    state.currentBet = result.bet_cents; state.bet = result.bet_cents; state.selected = result;
    save(betPreferenceKey(), String(state.bet));
    const previous = state.presentation;
    state.presentation = previous?.round_id === result.round_id && typeof previous.baseComplete === "boolean" && Number.isSafeInteger(previous.freeCompleted) && previous.freeCompleted >= 0 && previous.freeCompleted <= result.round.free_spins.length && (previous.baseComplete || previous.freeCompleted === 0)
      ? previous : { round_id: result.round_id, baseComplete: false, freeCompleted: 0 };
    savePending();
    if (autoplayRound && !state.auto && state.autoStatus === "autoConnectionError") state.autoStatus = "autoStopped";
    let presentationComplete = false;
    try {
      applyWallet(result.wallet); refreshStats();
      const free = result.round.free_spins;
      const progress = state.presentation;
      let paid = progress.baseComplete ? result.round.base.payout_units + result.round.free_spin_credits.slice(0, progress.freeCompleted).reduce((sum, value) => sum + value, 0) : 0;
      state.presentedUnits = paid;
      $("bonus-bar").hidden = false; $("bonus-label").textContent = t("bonusReady"); $("bonus-progress").textContent = ""; setWin(0);
      if (state.instant) {
        clearLines(); $("playline-select").value = "none";
        showGrid(lastFrame(free.at(-1) || result.round.base).evaluation_grid);
        if (cascadeCount(result.round)) { $("cascade-status").hidden = false; $("cascade-label").textContent = t("cascadeSummary"); $("cascade-count").textContent = cascadeCount(result.round); }
        progress.baseComplete = true; progress.freeCompleted = free.length; savePending();
      } else {
        if (!progress.baseComplete) {
          await animateSpin(result.round.base, result.round.base.payout_units, 0, 0);
          paid = result.round.base.payout_units; progress.baseComplete = true; savePending();
        } else showGrid(lastFrame(free[progress.freeCompleted - 1] || result.round.base).evaluation_grid);
        setWin(roundMoney(paid));
        if (free.length) {
          $("bonus-label").textContent = `${t("bonusStart")} · ×${state.config.fs_line_multiplier}`; $("bonus-progress").textContent = `${progress.freeCompleted} / ${free.length}`;
          if (!progress.freeCompleted) await announceBonus(`${free.length} ${t("bonusStart")}`, `×${state.config.fs_line_multiplier} · ${t("bonusLineOnly")}`);
          for (let i = progress.freeCompleted; i < free.length; i++) {
            $("bonus-label").textContent = `${t("bonusStart")} · ×${state.config.fs_line_multiplier}`;
            await animateSpin(free[i], result.round.free_spin_credits[i], i + 1, free.length);
            paid += result.round.free_spin_credits[i]; setWin(roundMoney(paid));
            progress.freeCompleted = i + 1; savePending();
            await wait(750, 95);
          }
          await announceBonus(t("bonusComplete"), `${t("bonusTotal")}: ${money(roundMoney(result.round.bonus_payout_units))}`);
        }
      }
      if (free.length) {
        $("bonus-label").textContent = `${t("bonusComplete")} · ${t("bonusTotal")}: ${money(roundMoney(result.round.bonus_payout_units))}`;
        $("bonus-progress").textContent = `${free.length} / ${free.length}`;
      }
      presentWins(lastFrame(free.at(-1) || result.round.base), true);
      roundNote(result);
      const label = result.win_cents === 0 ? "noWin" : result.win_cents < result.bet_cents ? "smallReturn" : result.win_cents === result.bet_cents ? "returned" : "won";
      $("win-caption").textContent = `${result.is_scenario ? `${t("test")} · ` : ""}${t(label)} · ${money(result.win_cents)}`;
      if (result.round.cap_reduction_units) $("win-detail").textContent = t("cap");
      else if (state.instant && free.length) $("win-detail").textContent = `${free.length} ${t("bonusSummary")} · ${t("roundTotal")}: ${money(result.win_cents)}`;
      else if (!state.currentSpin.line_wins.length) $("win-detail").textContent = result.is_scenario ? t("scenarioNotice") : `${t("roundTotal")}: ${money(result.win_cents)}`;
      if (state.rgs) {
        result.wallet = await state.rgs.finish(result);
        result.balance_cents = result.wallet.balance_cents; result.rgs_active = false;
      }
      presentationComplete = true;
    } catch (error) {
      if (!state.rgs) console.error(error);
      stopAuto(state.rgs ? "autoConnectionError" : "autoPresentationError");
      if (state.rgs) { state.connectionLost = true; $("win-detail").textContent = t("rgsPending"); }
      toast(state.rgs ? t("rgsPending") : error.message);
    }
    finally {
      applyWallet(result.wallet); refreshStats(); setWin(result.win_cents);
      state.history = [{ ...result, displayed_at: new Date().toISOString() }, ...state.history.filter(record => record.round_id !== result.round_id)].slice(0, 100); state.selected = state.history[0]; renderHistory();
      state.busy = false; state.cells.forEach(c => c.classList.remove("spinning"));
      $("cascade-layer").hidden = true; $("cascade-layer").replaceChildren(); state.cells.forEach(c => c.classList.remove("cascade-removing", "cascade-vacant", "cascade-winning"));
      if (presentationComplete) {
        if (autoplayRound && !result.is_scenario) state.autoCompleted++;
        if (state.auto && !result.is_scenario) { state.auto--; if (!state.auto) state.autoStatus = "autoComplete"; }
        state.pending = null; state.pendingAutoplay = false; state.presentation = null; savePending();
      }
      controls();
      scheduleAutoSpin();
    }
  }
  function renderHistory() {
    const list = $("history-list"); list.replaceChildren();
    if (!state.history.length) { const p = document.createElement("p"); p.className = "empty-history"; p.textContent = t("noHistory"); list.append(p); return; }
    state.history.slice(0, 25).forEach((record, i) => {
      const button = document.createElement("button"); button.type = "button"; button.className = "history-item";
      const label = document.createElement("span"); label.textContent = `${record.is_scenario ? t("test") : t("round")} · ${new Intl.DateTimeFormat(locale[state.lang], { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date(record.displayed_at))}`;
      const bet = document.createElement("span"); bet.textContent = `${t("bet")}: ${money(record.bet_cents)}`;
      const win = document.createElement("strong"); win.className = record.win_cents > record.bet_cents ? "history-win" : record.win_cents ? "history-return" : "history-loss"; win.textContent = money(record.win_cents);
      const badge = document.createElement("span"); badge.className = "history-tag"; badge.textContent = record.round.free_spins.length ? `${record.round.free_spins.length} FS` : record.is_scenario ? t("scenario") : `×${number(record.round.payout_units / state.config.payout_scale)}`;
      button.append(label, bet, win, badge); button.setAttribute("aria-label", `${t("details")} ${i + 1}: ${label.textContent}, ${bet.textContent}, ${win.textContent}`); button.addEventListener("click", () => openDetails(record)); list.append(button);
    });
  }
  function openDetails(record = state.selected) { if (!record) return; state.selected = record; $("details-json").textContent = JSON.stringify(record, null, 2); $("details-dialog").showModal(); }
  function renderPaytable() {
    const body = $("paytable-body"); body.replaceChildren();
    state.config.symbols.filter(code => state.config.paytable_units[code]).forEach(code => {
      const row = document.createElement("tr"); const symbol = document.createElement("td"); const token = document.createElement("span"); token.className = "paytable-token"; token.dataset.symbol = code; token.append(art(code)); const name = document.createElement("span"); name.textContent = symbolName(code); symbol.append(token, name); row.append(symbol);
      for (const count of [3, 4, 5]) { const td = document.createElement("td"); td.textContent = `${number(state.config.paytable_units[code][count] / state.config.payout_scale)}×`; row.append(td); } body.append(row);
    });
    $("special-rules").replaceChildren();
    for (const code of ["WILD", "SCATTER"]) { const item = document.createElement("div"); item.className = "special-rule"; const token = document.createElement("span"); token.className = "paytable-token"; token.dataset.symbol = code; token.append(art(code)); const text = document.createElement("span"); text.textContent = `${symbolName(code)} · ${t(code === "WILD" ? "wildRule" : "scatterRule")}`; item.append(token, text); $("special-rules").append(item); }
  }
  function renderThemeUI() {
    if (!artwork || !$("theme-select")) return;
    const select = $("theme-select"); select.replaceChildren();
    for (const [id, theme] of Object.entries(artwork.themes)) {
      const option = document.createElement("option"); option.value = id; option.textContent = theme[state.lang]; select.append(option);
    }
    select.value = state.theme;
    const active = new Set(Object.values(artwork.themes[state.theme].symbols));
    $("catalog-grid").replaceChildren();
    for (const [id, entry] of Object.entries(artwork.symbols)) {
      const card = document.createElement("div"); card.className = `catalog-card${active.has(id) ? " in-set" : ""}`;
      card.dataset.art = id; card.append(art(null, id));
      const name = document.createElement("strong"); name.textContent = entry[state.lang];
      const badge = document.createElement("small"); badge.textContent = t(active.has(id) ? "inSet" : "otherSet"); card.append(name, badge);
      $("catalog-grid").append(card);
    }
    if (state.artReady) $("asset-status").textContent = t("artReady");
    $("catalog-close").setAttribute("aria-label", t("close"));
  }
  function translate() {
    document.documentElement.lang = state.lang; $("lang-select").value = state.lang;
    document.querySelectorAll("[data-i18n]").forEach(node => { const key = node.dataset.i18n; if (words[state.lang][key] && !Array.isArray(words[state.lang][key])) node.textContent = t(key); });
    for (const mode of ["random", "win", "bonus", "expansion", "cascade", "middle"]) { const option = $("test-mode-select").querySelector(`[value="${mode}"]`); if (option) option.textContent = t(mode); }
    const selectedLine = $("playline-select").value; $("playline-select").replaceChildren();
    [null, ...(state.config?.paylines || [])].forEach((_, index) => { const option = document.createElement("option"); option.value = index ? index : "none"; option.textContent = index ? `${t("line")} ${index}` : t("noLine"); $("playline-select").append(option); }); $("playline-select").value = selectedLine || "none";
    $("rules-content").replaceChildren(); t("ruleText").forEach(text => { const p = document.createElement("p"); p.textContent = text; $("rules-content").append(p); });
    $("assets-button").title = t("graphicsHint");
    const labels = { "rules-button": "rules", "feature-rules-button": "rules", "lang-select": "language", "bet-decrease": "decreaseBet", "bet-increase": "increaseBet", "auto-count": "autoCount", "assets-input": "chooseGraphics", "rules-close": "close", "details-close": "close", "autoplay-close": "close" };
    Object.entries(labels).forEach(([id, key]) => $(id).setAttribute("aria-label", t(key)));
    const settingsButton = document.querySelector("#settings-button");
    if (settingsButton) { settingsButton.setAttribute("aria-label", t("settingsTitle")); settingsButton.title = t("settingsTitle"); }
    document.querySelectorAll(".player-dialog .close-button").forEach(button => button.setAttribute("aria-label", t("close")));
    $("rules-button").title = t("rules"); $("auto-button").removeAttribute("aria-label");
    $("paytable-toggle").setAttribute("aria-label", t("paytable")); $("paytable-toggle").title = t("paytable");
    const spaceKey = document.querySelector(".footer-shortcut kbd"); if (spaceKey) spaceKey.textContent = { pl: "SPACJA", en: "SPACE", de: "LEERTASTE" }[state.lang];
    document.querySelector(".autoplay-presets").setAttribute("aria-label", t("autoCount"));
    if (state.config) {
      const fs = Object.values(state.config.free_spins);
      $("feature-spins-value").textContent = `${Math.min(...fs)}–${Math.max(...fs)}`;
      $("feature-multiplier-value").textContent = `×${state.config.fs_line_multiplier}`;
      $("feature-max-value").textContent = `${number(state.config.max_win_units / state.config.payout_scale)}×`;
      renderPaytable(); showGrid(state.grid); refreshStats(); renderHistory();
    }
    renderThemeUI(); controls();
    $("bonus-label").textContent = t("bonusReady"); $("bonus-progress").textContent = "";
    roundNote(state.history[0]);
    if (!state.history.length) { $("win-caption").textContent = t("ready"); $("win-detail").textContent = t("readyDetail"); setWin(0); }
    else {
      const last = state.history[0], free = last.round.free_spins;
      setWin(last.win_cents); if (state.currentSpin) presentWins(state.currentSpin, !state.busy);
      $("win-caption").textContent = `${last.is_scenario ? `${t("test")} · ` : ""}${t("roundTotal")} · ${money(last.win_cents)}`;
      if (free.length) { $("bonus-label").textContent = `${t("bonusComplete")} · ${t("bonusTotal")}: ${money(roundMoney(last.round.bonus_payout_units, last.bet_cents))}`; $("bonus-progress").textContent = `${free.length} / ${free.length}`; }
      if (last.round.cap_reduction_units) $("win-detail").textContent = t("cap");
      else if (state.instant && free.length) $("win-detail").textContent = `${free.length} ${t("bonusSummary")} · ${t("roundTotal")}: ${money(last.win_cents)}`;
    }
  }
  async function resetSession() {
    if (state.rgs) return;
    if (state.busy || state.pending) return;
    stopAuto(); state.busy = true; controls();
    try { const result = await api("/api/reset", {}); state.sessionId = result.session_id; state.connectionLost = false; state.balance = result.balance_cents; statsFrom(result); state.history = []; state.autoTotal = 0; state.autoCompleted = 0; state.selected = null; state.currentSpin = null; clearLines(); $("bonus-bar").hidden = false; $("bonus-label").textContent = t("bonusReady"); $("bonus-progress").textContent = ""; $("playline-select").value = "none"; translate(); toast(t("resetDone")); } catch (error) { toast(error.message); }
    finally { state.busy = false; controls(); }
  }
  function exportJson() {
    const payload = { game: "POLSKA GUROM", math_version: state.config.math_version || "0.4.0-weighted", exported_at: new Date().toISOString(), balance_cents: state.balance, stats: state.stats, config: state.config, rounds: state.history };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url; link.download = `polska-gurom-test-${new Date().toISOString().replace(/[:.]/g, "-")}.json`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function bindEvents() {
    if ($("theme-select")) $("theme-select").addEventListener("change", () => {
      if (state.busy || state.pending || state.auto || !artwork?.themes[$("theme-select").value]) { $("theme-select").value = state.theme; return; }
      state.theme = $("theme-select").value; save("pg-art-theme", state.theme);
      for (const url of Object.values(state.images)) if (url.startsWith("blob:")) URL.revokeObjectURL(url);
      state.images = {}; translate();
    });
    if ($("catalog-button")) $("catalog-button").addEventListener("click", () => { stopAuto(); renderThemeUI(); $("catalog-dialog").showModal(); });
    $("spin-button").addEventListener("click", () => state.auto ? stopAuto() : spin());
    $("bet-decrease").addEventListener("click", () => changeBet(-1)); $("bet-increase").addEventListener("click", () => changeBet(1));
    $("auto-button").addEventListener("click", () => { if (state.auto) stopAuto(); else if (!state.busy && !state.pending && state.online && $("test-mode-select").value === "random") { controls(); $("autoplay-dialog").showModal(); } });
    $("autoplay-stop").addEventListener("click", () => stopAuto());
    $("autoplay-start").addEventListener("click", () => {
      if (state.busy || state.pending || state.auto || !state.online || $("test-mode-select").value !== "random") return;
      state.auto = state.autoCount; state.autoTotal = state.autoCount; state.autoCompleted = 0; state.autoStatus = "autoActive";
      $("autoplay-dialog").close(); controls(); spin();
    });
    const setCount = value => { if (autoCounts.includes(value)) { state.autoCount = value; save("pg-auto-count", String(value)); renderAutoplaySettings(); } };
    $("auto-count").addEventListener("input", () => setCount(autoCounts[Number($("auto-count").value)]));
    document.querySelectorAll("[data-count]").forEach(button => button.addEventListener("click", () => setCount(Number(button.dataset.count))));
    for (const [id, speed] of [["turbo-option", "turbo"], ["quick-option", "quick"]]) $(id).addEventListener("change", () => { state.speed = $(id).checked ? speed : "normal"; controls(); });
    $("skip-screens-option").addEventListener("change", () => { state.skipScreens = $("skip-screens-option").checked; save("pg-skip-screens", String(state.skipScreens)); });
    $("hyperplay-button").addEventListener("click", () => { state.instant = !state.instant; controls(); });
    $("speed-button").addEventListener("click", () => { state.instant = false; const speeds = ["normal", "quick", "turbo"]; state.speed = speeds[(speeds.indexOf(state.speed) + 1) % speeds.length]; controls(); });
    $("test-mode-select").addEventListener("change", () => {
      stopAuto();
      if ($("test-mode-select").value === "middle" && artwork?.themes.polska) {
        state.theme = "polska"; save("pg-art-theme", state.theme); translate();
      }
      controls();
    });
    $("lang-select").addEventListener("change", () => { state.lang = $("lang-select").value; save("pg-lang", state.lang); translate(); });
    $("playline-select").addEventListener("change", () => { clearLines(); const value = $("playline-select").value; if (value !== "none") { drawLine(state.config.paylines[Number(value) - 1], 5, true); $("win-detail").textContent = t("previewHint"); } else if (state.currentSpin) presentWins(state.currentSpin, true); });
    $("paytable-toggle").addEventListener("click", () => { const open = $("paytable-panel").classList.toggle("open"); $("paytable-toggle").setAttribute("aria-expanded", String(open)); if (open && matchMedia("(max-width:760px)").matches) $("paytable-panel").scrollIntoView({ behavior: "smooth", block: "start" }); });
    $("reset-button").addEventListener("click", resetSession); $("export-button").addEventListener("click", exportJson); $("details-button").addEventListener("click", () => openDetails());
    for (const id of ["rules-button", "feature-rules-button"]) $(id).addEventListener("click", () => { stopAuto(); $("rules-dialog").showModal(); });
    for (const prefix of ["rules", "details", "autoplay", "catalog"]) { if (!$(prefix + "-close")) continue; $(prefix + "-close").addEventListener("click", () => $(prefix + "-dialog").close()); $(prefix + "-dialog").addEventListener("click", event => { if (event.target === $(prefix + "-dialog")) { const rect = event.target.getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) event.target.close(); } }); }
    $("assets-button").addEventListener("click", () => $("assets-input").click());
    $("assets-input").addEventListener("change", event => {
      let count = 0;
      for (const file of event.target.files) { const code = file.name.replace(/\.[^.]+$/, "").toUpperCase(); if (!state.config.symbols.includes(code) || !file.type.startsWith("image/") || file.size > 8 * 1024 * 1024) continue; if (state.images[code]?.startsWith("blob:")) URL.revokeObjectURL(state.images[code]); state.images[code] = URL.createObjectURL(file); count++; }
      event.target.value = "";
      if (count) { showGrid(state.grid); renderPaytable(); $("asset-status").textContent = `${t("graphicsLoaded")}: ${Object.keys(state.images).length} / 10`; toast(`${t("graphicsLoaded")}: ${count}`); } else toast(t("graphicsInvalid"));
    });
    document.addEventListener("keydown", event => { if (event.code === "Space" && !event.repeat && !/INPUT|SELECT|TEXTAREA|BUTTON/.test(event.target.tagName) && !event.target.isContentEditable && !document.querySelector("dialog[open]")) { event.preventDefault(); if (state.auto) stopAuto(); else spin(); } });
    document.addEventListener("visibilitychange", controls);
    window.addEventListener("beforeunload", event => { if (state.busy || state.pending || state.auto) { event.preventDefault(); event.returnValue = ""; } });
  }
  function changeBet(direction) { if (state.busy || state.pending) return; stopAuto(); const options = state.config.bet_options_cents; state.bet = options[Math.max(0, Math.min(options.length - 1, options.indexOf(state.bet) + direction))]; save(betPreferenceKey(), String(state.bet)); refreshStats(); controls(); }
  async function init() {
    // Every visit opens ordinary play with the falling animation visible.
    $("test-mode-select").value = "random";
    bindEvents(); controls(); $("connection-status").textContent = t("connecting");
    try {
      const params = new URLSearchParams(location.search || "");
      state.platformLaunch = params.has("sessionID") || params.has("rgs_url") || document.documentElement.dataset?.rgsOnly === "true";
      if ((params.has("sessionID") || params.has("rgs_url")) && !window.PG_RGS) throw new Error("rgs_client_unavailable");
      const launch = window.PG_RGS?.launch(location.href);
      if (state.platformLaunch && !launch) throw new Error("rgs_invalid_launch");
      let config, wallet, symbols, resumed;
      if (launch) {
        state.rgs = new window.PG_RGS.Client(launch);
        state.lang = launch.lang;
        Object.assign(words.pl, { balance: "Saldo", connected: "Platforma połączona", noFunds: "Za mało środków. Zmniejsz stawkę.", loadError: "Nie udało się uwierzytelnić sesji platformy. Otwórz grę ponownie z lobby.", randomNotice: "Wynik i saldo pochodzą z serwera platformy.", rgsPending: "Runda oczekuje na odczyt lub rozliczenie. Ponów odczyt; nowy zakład pozostaje zablokowany." });
        Object.assign(words.en, { balance: "Balance", connected: "Platform connected", noFunds: "Insufficient balance. Lower your bet.", loadError: "Could not authenticate the platform session. Reopen the game from the lobby.", randomNotice: "Results and balance are provided by the platform server.", rgsPending: "The round awaits recovery or settlement. Retry the result; new bets remain blocked." });
        Object.assign(words.de, { balance: "Guthaben", connected: "Plattform verbunden", noFunds: "Guthaben reicht nicht aus. Einsatz senken.", loadError: "Plattformsitzung konnte nicht authentifiziert werden. Spiel aus der Lobby neu öffnen.", randomNotice: "Ergebnis und Guthaben stammen vom Plattformserver.", rgsPending: "Die Runde wartet auf Wiederherstellung oder Abrechnung. Ergebnis erneut laden; neue Einsätze bleiben gesperrt." });
        const platformRules = { pl: "Saldo, dozwolone stawki i rozliczenie pochodzą z serwera platformy. Gra wysyła jeden zakład za całą rundę z bonusem. Wygrana jest rozliczana po prezentacji pełnego wyniku. Nierozstrzygnięte żądanie blokuje nowy zakład; w razie problemu wróć do gry przez lobby.", en: "Balance, available bets and settlement come from the platform server. One bet covers the entire round including its bonus. Winnings are settled after the full result is presented. An unresolved request blocks new bets; reopen the game from the lobby if necessary.", de: "Guthaben, verfügbare Einsätze und Abrechnung stammen vom Plattformserver. Ein Einsatz umfasst die gesamte Runde samt Bonus. Gewinne werden nach Anzeige des vollständigen Ergebnisses abgerechnet. Eine ungeklärte Anfrage sperrt neue Einsätze; bei Bedarf das Spiel aus der Lobby erneut öffnen." };
        for (const lang of Object.keys(locale)) words[lang].ruleText[5] = platformRules[lang];
        const loaded = await Promise.all([api("game-config.json"), api("assets/symbols.json")]);
        const boot = await state.rgs.boot(loaded[0]);
        ({ config, wallet } = boot); symbols = loaded[1]; resumed = boot.pending;
        state.bet = resumed?.request.bet_cents || config.default_bet_cents; state.currentBet = state.bet;
        const badge = document.querySelector(".player-demo-label");
        if (badge) badge.textContent = launch.demo ? "RGS · DEMO" : "RGS";
        const tools = document.querySelector(".testing-tools"); if (tools) tools.hidden = true;
      } else {
        [config, wallet, symbols] = await Promise.all([api("/api/config"), api("/api/state"), api("/assets/symbols.json")]);
      }
      if (artwork) {
        try {
          await Promise.all(Object.values(artwork.files).map(preloadArtwork));
          state.artReady = true;
        } catch { toast(t("artError")); }
      }
      state.config = config; state.symbols = symbols; state.balance = wallet.balance_cents; statsFrom(wallet); state.online = true;
      state.sessionId = wallet.session_id;
      state.history = (wallet.recent_rounds || []).map(record => ({ ...record, displayed_at: record.created_at }));
      state.selected = state.history[0] || null;
      const savedBet = Number(getSaved(betPreferenceKey(), String(state.selected?.bet_cents || state.bet)));
      if (config.bet_options_cents.includes(savedBet)) state.bet = savedBet;
      for (const [code, entry] of Object.entries(symbols)) if (entry.image) { const url = new URL(entry.image, `${location.origin}/assets/`); if (url.origin === location.origin && url.pathname.startsWith("/assets/")) state.images[code] = url.href; }
      createGrid(); $("bonus-bar").hidden = false;
      if (state.selected) { state.currentBet = state.selected.bet_cents; state.currentSpin = lastFrame(state.selected.round.free_spins.at(-1) || state.selected.round.base); showGrid(state.currentSpin.evaluation_grid); }
      translate();
      const saved = savedPending();
      const interrupted = resumed ? { session_id: wallet.session_id, request: resumed.request, presentation: saved?.session_id === wallet.session_id ? saved.presentation : null } : state.rgs ? null : saved;
      if (interrupted?.request) {
        if (interrupted.session_id === wallet.session_id && config.bet_options_cents.includes(interrupted.request.bet_cents) && ["random", "win", "bonus", "expansion", "cascade", "middle"].includes(interrupted.request.mode) && typeof interrupted.request.request_id === "string") {
          state.pending = interrupted.request; state.pendingAutoplay = !!interrupted.autoplay;
          state.bet = interrupted.request.bet_cents; state.currentBet = state.bet;
          state.presentation = interrupted.presentation || null;
          state.autoTotal = Number.isSafeInteger(interrupted.autoTotal) ? interrupted.autoTotal : 0;
          state.autoCompleted = Number.isSafeInteger(interrupted.autoCompleted) ? interrupted.autoCompleted : 0;
          state.autoStatus = "autoStopped"; controls(); toast(t("requestError"));
        } else { savePending(); $("win-detail").textContent = t("sessionEnded"); toast(t("sessionEnded")); }
      }
      refreshStats();
      if (state.rgs) state.walletTimer = setInterval(async () => {
        if (!state.online || state.busy || state.pending || state.auto || document.hidden || state.walletReading) return;
        state.walletReading = true;
        try { const latest = await state.rgs.readWallet(); if (!state.busy && !state.pending) { applyWallet(latest); state.connectionLost = false; refreshStats(); } }
        catch (error) { state.connectionLost = true; if (error.code === "session_expired") state.online = false; }
        finally { state.walletReading = false; controls(); }
      }, 60000);
    } catch (error) {
      if (!state.platformLaunch) console.error(error);
      state.online = false; controls(); $("win-caption").textContent = t("offline");
      const messages = { pl: "Nie udało się otworzyć sesji platformy. Uruchom grę ponownie z lobby. Nowe zakłady są zablokowane.", en: "Could not open the platform session. Reopen the game from the lobby. New bets are blocked.", de: "Plattformsitzung konnte nicht geöffnet werden. Spiel erneut aus der Lobby öffnen. Neue Einsätze sind gesperrt." };
      const message = state.platformLaunch ? messages[state.lang] : t("loadError");
      $("win-detail").textContent = message; toast(message);
    }
  }
  init();
})();
