# POLSKA GUROM — założenia i plan weryfikacji Stake Engine

Data opracowania: 20.10.2026. Dokument do sprawdzania finalnej wersji gry.

To plan kontroli, nie potwierdzenie zaliczenia testów ani zgody platformy. W tej pracy przeczytano dokumentację i materiały projektu; nie wykonano ponownie audytu kodu, matematyki, przeglądarki ani integracji ACP. Wszystkie pola pozostają do sprawdzenia dla konkretnej paczki.

Oznaczenia: **SE** — wymóg opisany przez platformę; **W** — wytyczna oceny, orientacyjny próg lub rozbieżność do potwierdzenia; **G** — założenie naszej gry do zweryfikowania; **QA** — moja dodatkowa kontrola jakości. Dla każdego punktu należy zapisać: wynik TAK/NIE/NIE DOTYCZY/NIEZWERYFIKOWANE, wersję, dowód i ewentualny błąd. „Nie dotyczy” wymaga uzasadnienia.

## 1. Jedna obowiązująca specyfikacja gry

Podstawą roboczą jest `test-interface-any-start/README_PL.md`: opis v0.5.0-any-start. README zawiera również historyczne fragmenty v0.4.1; nie wolno mieszać ich z nową specyfikacją. Poniższe liczby są deklaracjami projektu, które trzeba potwierdzić na finalnym eksporcie.

- [ ] G01 — Plansza 5×3 i dokładnie 20 aktywnych linii; definicje współrzędnych identyczne w silniku, zdarzeniach, grafice i zasadach.
- [ ] G02 — Wygrywa co najmniej 3 kolejnych pasujących symboli na linii, od dowolnego bębna: 1–3, 2–4 albo 3–5. Cztery i pięć symboli mają jednoznaczne wypłaty.
- [ ] G03 — Jedna linia wypłaca jeden najwyższy wynik. Zdefiniować rozstrzyganie remisów i dopasowań z Wildem; suma kilku możliwych fragmentów nie może zastąpić tej reguły.
- [ ] G04 — Ten sam symbol może uczestniczyć w wielu liniach. W kaskadzie każde wygrywające pole usuwa się tylko raz.
- [ ] G05 — Tabela wypłat jednoznacznie wskazuje, czy wartości odnoszą się do całej stawki czy stawki na linię. Sprawdzić przykład: przy stawce 2 PLN trzy obwarzanki na jednej linii płacą 0,20 PLN; całkowita wygrana konkretnej planszy może obejmować dodatkowe linie.
- [ ] G06 — Dla Wilda opisać zastępowane symbole, wykluczenie Scattera, własne wypłaty lub ich brak oraz układ samych Wildów.
- [ ] G07 — Scatter jest oceniany na początkowej planszy, przed ekspansją Wilda. Sprawdzić mapowanie liczby Scatterów na 8/10/12 darmowych obrotów i każdą wypłatę Scattera.
- [ ] G08 — Uzupełnienia kaskad nie zawierają Scatterów; bonus nie przyznaje kolejnych darmowych obrotów.
- [ ] G09 — W bonusie ekspansja Wilda może nastąpić raz na początku darmowego obrotu; ustalić wybór bębna, zakres ekspansji i późniejsze zachowanie Wildów w kaskadach.
- [ ] G10 — Mnożnik ×4 dotyczy wyłącznie wygranych liniowych w bonusie, także jego kaskad; nie mnoży ponownie sumy bonusu ani wypłat Scattera.
- [ ] G11 — Jedna płatna runda zawiera obrót bazowy, wszystkie jego kaskady i cały bonus. Nie pobiera się kolejnych stawek za te elementy.
- [ ] G12 — Limit 5000× dotyczy sumy całej rundy. Osiągnięcie limitu kończy rundę, nawet jeśli zostały darmowe obroty. Interfejs musi wyraźnie wyjaśniać takie zakończenie.
- [ ] G13 — Cele eksportu: RTP 96%, maksimum 5000×, częstość maksimum 1:8 000 000, krok wypłat 0,1×. Wszystko przeliczyć z finalnych wag.
- [ ] G14 — Brak zakupu bonusu i Double Chance. Nie mogą pozostać aktywne przyciski lub opisy sugerujące te funkcje.
- [ ] G15 — Trzy zestawy wyglądu przedstawiają te same kody i wypłaty. Katalog 18 ilustracji nie oznacza 18 losowanych typów symboli jednocześnie.
- [ ] G16 — Ujednolicić GDD, README, konfigurację i zasady. Usunąć z aktywnej instrukcji sprzeczne liczby rund, wersje silnika oraz historyczne przypisania symboli.

**Moja uwaga:** reguła „od dowolnego bębna” wymaga osobnego zestawu testów. Poprawność dawnego liczenia od lewej nie potwierdza poprawności v0.5.

## 2. Matematyka i rozkład wyników

- [ ] SE01 — Wyliczyć RTP każdego płatnego trybu z jego rzeczywistych wag i kosztu; wymagany zakres 90–98%. Przy wielu trybach uwzględnić ograniczenie różnic opisane w dokumentacji jako 0,5 punktu procentowego względem wskazanego RTP bazowego.
- [ ] SE02 — Koszt trybu i realnie osiągalna maksymalna wygrana zgadzają się z informacjami gracza.
- [ ] W01 — Oceniać częstość maksimum, hit rate, zmienność i różnorodność rezultatów. Dokumentacja matematyczna podaje zwykle maksimum częstsze niż 1:10 mln, zależnie od kwoty, a oficjalna checklista 1:20 mln lub częściej; tę rozbieżność zachować w raporcie.
- [ ] W02 — Wytyczne dla slotów wskazują 100 tys.–1 mln symulacji i trafienie dodatniej wypłaty częstsze niż 1:20. To nie dowód poprawności rzadkich zdarzeń ani gwarancja akceptacji.
- [ ] W03 — Podać liczbę rekordów z dodatnią wagą, udział płatnych rezultatów, największe prawdopodobieństwo pojedynczego rekordu i rozkład przedziałów wypłat. Sprawdzić brak nieuzasadnionych luk do maksimum.
- [ ] QA01 — Niezależny kalkulator odtwarza wypłaty z plansz, zasad i tabeli, zamiast ufać zapisanej sumie z generatora. Sprawdzić wszystkie rekordy finalnego banku, jeżeli wykonalne.
- [ ] QA02 — Dla wag w_i, wypłat m_i w jednostkach mnożnika stawki i kosztu trybu c: RTP = Σ(w_i × m_i) / (Σw_i × c). Jeżeli CSV zapisuje mnożnik w skali 100, najpierw podzielić go przez 100.
- [ ] QA03 — Osobno raportować: wygraną >0, zwrot części stawki, zwrot równy kosztowi i wygraną przewyższającą koszt. Dodatnia wypłata nie zawsze oznacza zysk.
- [ ] QA04 — Obliczyć częstości bonusu, wariantów 8/10/12, ekspansji Wilda i długości kaskad z końcowych wag. Prawdopodobieństwa generatora kandydatów nie muszą być rozkładem RGS.
- [ ] QA05 — Każdy reklamowany wariant ma co najmniej jeden poprawny rekord z dodatnią wagą. Samo istnienie scenariusza demonstracyjnego nie wystarcza.
- [ ] QA06 — Zbadać wkład bazy, Scatterów, bonusu i maksimum w RTP oraz koncentrację RTP w najrzadszych wynikach. Podać wariancję i przedziały niepewności symulacji.
- [ ] QA07 — Symulator losuje według finalnych wag. Częstość 1:8 mln sprawdzić analitycznie; nie wymagać przypadkowego trafienia w małej próbce.
- [ ] QA08 — Historia gracza, saldo, wcześniejsze przegrane, tempo, skin i urządzenie nie zmieniają wag ani wyniku.

Źródła: [Math Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx), [oficjalna checklista](https://github.com/engineio/docs/blob/main/static/mockchecklist.json).

## 3. Paczka matematyczna i zgodność zdarzeń

- [ ] SE03 — Dostarczyć `index.json` oraz dla każdego trybu wskazane pliki wag CSV i wyników `.jsonl.zst`. Manifest zawiera nazwę, koszt i właściwe ścieżki.
- [ ] SE04 — CSV ma wymagane trzy pola bez nagłówka: ID, wagę i wypłatę; sprawdzić dozwolone zakresy całkowite i sumę wag.
- [ ] SE05 — Każda linia książki jest poprawnym JSON z `id`, `events`, `payoutMultiplier`. Wypłaty CSV i książki są identyczne.
- [ ] QA09 — Brak brakujących ID, duplikatów i przesunięcia indeksów. Konwencję ID potwierdzić aktualnym uploaderem; nie zakładać jej z pojedynczego przykładu.
- [ ] QA10 — Rozdzielić skalę 100 dla wypłat eksportu od skali 1 000 000 dla kwot portfela. Sprawdzić krok dodatnich wypłat aktualnym walidatorem SDK i uploaderem.
- [ ] QA11 — Przejście publicznego walidatora zapisać z jego wersją; dodatkowo wykonać upload i analizę ACP. Kryteria ocen gwiazdkowych nie zastępują ogólnych wymagań approval.
- [ ] QA12 — Każdy rekord opisuje pełną rundę: plansze, Wildy, wygrane, usunięcia, opadanie, uzupełnienia, bonus i zakończenie. Frontend nie dolosowuje brakujących rozstrzygnięć.
- [ ] QA13 — Kolejność zdarzeń i współrzędne mają jeden kontrakt. Stan po opadaniu wynika ze stanu poprzedniego, a wyświetlone linie rzeczywiście istnieją na planszy.
- [ ] QA14 — Suma faktycznie uznanych wypłat zdarzeń równa się payout książki i RGS. Przy limicie rozdzielić surowe należności od faktycznej wypłaty.
- [ ] QA15 — Finalny ZIP, frontend i matematyka mają zgodne wersje oraz manifest skrótów. Sprawdzać paczkę dostarczaną, a nie wyłącznie katalog roboczy.

Źródła: [opis formatu](https://stake-engine.com/docs/architecture/how-rgs-works), [walidator SDK](https://github.com/engineio/math-sdk/blob/main/utils/rgs_verification.py). Szczegóły formatu wymagają potwierdzenia na wersji stosowanej przy publikacji.

## 4. RGS, stawki i saldo

- [ ] SE06 — Finalna gra jest statycznym buildem; sesje i transakcje obsługuje RGS. Lokalny serwer Python i fikcyjne saldo są narzędziami testowymi.
- [ ] SE07 — Odczytać parametry uruchomienia, w tym `sessionID`, `rgs_url`, `lang`, `device`; adres RGS nie jest wpisany na stałe.
- [ ] SE08 — W zwykłej grze najpierw authenticate, potem play i zamknięcie rundy zgodnie z aktualnym kontraktem. Cały bonus należy do tej samej płatnej rundy.
- [ ] SE09 — Udostępnić stawki, minimum, maksimum, domyślną wartość i krok z uwierzytelnienia; stosować rzeczywiste nazwy pól aktualnego API.
- [ ] QA16 — Rozliczenia w jednostkach całkowitych API; sprawdzić precyzję i format USD, JPY, MXN, walut cyfrowych i tokenów. Saldo nie może być źródłem wyliczania wyniku.
- [ ] QA17 — Przy wznowieniu odtworzyć aktywną rundę i jej stawkę z RGS. Pamięć przeglądarki może wspierać prezentację, lecz nie rozstrzyga stanu finansowego.
- [ ] QA18 — Utrata odpowiedzi play nie uruchamia nowego płatnego obrotu. Stan rozstrzygać udokumentowaną ścieżką recovery RGS; lokalny request ID nie dowodzi idempotencji produkcyjnego API.
- [ ] QA19 — Przetestować utratę połączenia przed i po play oraz przed i po end-round, reload w bonusie, błędy 4xx/5xx, wygaśniętą sesję i brak salda.
- [ ] QA20 — Podwójny klik, spacja trzymana wciśnięta i wiele kart nie powodują równoległych, niekontrolowanych zakładów ani podwójnych wypłat.
- [ ] QA21 — Blokować nowe zakłady, gdy stan poprzedniej rundy jest nieznany. Odrzucona stawka lub awaria nie może wyglądać jak przegrana.
- [ ] QA22 — Nie ujawniać tokenów sesji w logach i błędach; sprawdzić produkcyjną konsolę oraz ruch sieciowy.

Źródła: [RGS Overview](https://stakeengine.org/docs/rgs), [RGS Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/rgs-requirements/%2Bpage.svx). Nowe strony wallet są w budowie; detale zamykania zerowych rund i recovery potwierdzić na aktualnym API, bez ślepego kopiowania dawnego testera.

## 5. Interfejs, reguły i dźwięk

- [ ] SE10 — Informacje w grze zawierają pełne zasady, wszystkie wypłaty, symbole specjalne i ich wartości, warunki bonusu, koszty, RTP oraz maksimum dla każdego trybu.
- [ ] SE11 — Widoczne są saldo, stawka i końcowa wygrana; przy wielu wygrywających działaniach suma narasta do prawidłowej wartości.
- [ ] SE12 — Dostępne są opis przycisków, wyciszenie i obsługa spacji; autoplay ma osobny krok potwierdzenia startu.
- [ ] SE13 — Jeśli dodamy tryb kosztujący ponad 2×, wymaga potwierdzenia. Obecnie oznaczyć jako nie dotyczy po sprawdzeniu braku takich trybów.
- [ ] SE14 — Cała gra działa na desktopie, fizycznym telefonie i w rzeczywistym oknie platformy oraz popout S/M; plansza nie jest deformowana, przyciski i tekst pozostają dostępne. Odbiór wymaga osobnych wyników urządzenie–przeglądarka i wersji wdrożenia. Zmiany rozmiaru okna oraz lokalny iframe nie zastępują testu na urządzeniu i platformie.
- [ ] SE15 — Także w fastplay można odczytać kwoty, zwycięskie symbole i komunikaty. Tryb błyskawiczny wymaga osobnej oceny czytelności.
- [ ] SE16 — Brak brakujących zasobów; własne grafiki, animacje i audio. Obrazy i fonty dostarczane z CDN platformy, bez pobierania z niedozwolonych źródeł zewnętrznych.
- [ ] SE17 — Angielski działa; nieobsługiwany parametr języka nie psuje napisów. Dodatkowe PL/DE mają zgodne znaczenie zasad i kwot.
- [ ] QA23 — Zmiana języka, tempa, rozmiaru lub skina nie zmienia bieżącego wyniku, stawki i licznika. Rozważyć blokadę skina do końca rundy.
- [ ] QA24 — STOP AUTO zatrzymuje dalsze płatne rundy po dokończeniu bieżącej wraz z bonusem. Po awarii seria nie startuje samoczynnie.
- [ ] QA25 — Przy maksimum pokazywać faktycznie wypłaconą kwotę i trwałą informację o limicie. Podgląd linii nie może sugerować wypłaty ponad limit.
- [ ] QA26 — Efekty rozróżniają częściowy zwrot od zysku; wielka celebracja nie powinna sugerować zysku przy wypłacie mniejszej niż koszt.
- [ ] QA27 — Na fizycznych telefonach sprawdzić dotyk, poziom/pion również w kaskadzie i bonusie, małe ekrany, zoom, klawiaturę w polach, brak dźwięku przed gestem użytkownika, wyciszenie oraz powrót z innej aplikacji i blokady ekranu. Zapisać model, system, wersję przeglądarki, skrót paczki i dowód każdej próby. Testy rozmiarów ekranu tego nie zastępują. [Protokół i status przygotowania, 22.10.2026](audit/physical_devices_2026_10_22/TESTY_FIZYCZNE_PL.md): testy fizyczne i odsłuch niewykonane, brak dostępu do platformy. Audio dodawane równolegle wymaga odbioru na jednej wskazanej wersji paczki.
- [ ] QA28 — Scenariusze studyjne i możliwość podmiany grafik są wyłączone w paczce produkcyjnej lub bezpiecznie odizolowane od rozliczeń.

Źródło: [Frontend Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/frontend-requirements/%2Bpage.svx).

## 6. Replay

- [ ] SE18 — Obsłużyć `replay=true` oraz game/version/mode/event/rgs_url i pobrać właściwy historyczny wynik przez endpoint replay.
- [ ] SE19 — Replay działa bez sesji i wywołań portfela. Nie pozwala uruchomić zwykłej gry, stawki ani autoplay.
- [ ] SE20 — Są ładowanie, błąd, rozpoczęcie, pełny przebieg z efektami, wynik i ponowne odtworzenie.
- [ ] SE21 — Obsłużyć opcjonalne amount/currency/lang/device/social. Wyraźnie pokazać stawkę bazową, mnożnik kosztu, rzeczywisty koszt i wygraną.
- [ ] SE22 — Przygotować ID przegranej, zwykłej wygranej, dużej wygranej, maksimum i bonusu dla każdego właściwego trybu.
- [ ] QA29 — Dodać ID bonusów 8/10/12, kaskad od środkowego/prawego bębna, ekspansji Wilda i limitu osiągniętego w bonusie. Powtórne replay nie zmienia wyniku ani salda.
- [ ] QA30 — Stare replay korzysta z właściwej wersji matematyki i zgodnej prezentacji; aktualizacja nie interpretuje starego wyniku według nowych reguł.

Źródło: [Bet Replay](https://github.com/engineio/docs/blob/main/src/routes/docs/api/bet-replay/%2Bpage.svx).

## 7. Social, treści i publikacja

- [ ] SE23 — Dla Stake.us `social=true` włącza angielski i pełny słownik zamian w przyciskach, zasadach, obrazach, błędach, autoplay i replay.
- [ ] SE24 — Obsłużyć SC/GC bez znaku dolara, prawidłowo mapując kody API. Testować właściwy szablon stawek dla rynku US.
- [ ] SE25 — Zakłady są niezależne; brak jackpotu, gamble, kontynuacji między zakładami i wcześniejszego cashoutu. Bezstanowość nie zabrania sekwencji bonusowej w jednej rundzie.
- [ ] SE26 — Oryginalna gra, unikalna nazwa, prawa do grafik/fontów/muzyki i brak niedozwolonego brandingu. Brak treści obraźliwych oraz kierowanych do nieletnich.
- [ ] QA31 — Dla polskiej tematyki sprawdzić konkretne źródła ilustracji, znaków, strojów i odniesień do malarstwa. Samo wygenerowanie obrazu nie zastępuje sprawdzenia finalnego projektu.
- [ ] SE27 — Dostępny disclaimer dotyczący awarii, połączenia, wznowienia rund, długoterminowego RTP, ilustracyjnych animacji i rozstrzygnięcia RGS; prawa autorskie opisane zgodnie z faktycznym uprawnieniem.
- [ ] SE28 — Kafelek gry spełnia aktualne wymagania edytora, czytelności tytułu i obszaru grafiki; poprawne logo dostawcy.
- [ ] SE29 — Zgłoszenie obejmuje konkretną finalną wersję frontendu i matematyki oraz krótki opis motywu i mechanik do promocji.
- [ ] SE30 — Potwierdzić w ACP statusy frontend/math Approved i Active, właściwe szablony stawek i finalne uruchomienie. Lokalne testy nie nadają tych statusów.
- [ ] SE31 — Zamrozić matematykę i mechaniki przed approval. Aktualne zasady dopuszczają po akceptacji małe poprawki wizualne; inne zmiany wymagają uzgodnienia z platformą.

Źródła: [Core Requirements](https://stakeengine.org/docs/approval-guidelines), [Social Mode](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/social-mode/%2Bpage.svx), [checklista](https://github.com/engineio/docs/blob/main/static/mockchecklist.json), [Disclaimer](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/disclaimer/%2Bpage.svx), [Game Tile](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/game-tile/%2Bpage.svx).

## 8. Kolejność i dowody odbioru — moja rekomendacja

1. Uzgodnić i zamrozić jeden opis v0.5, zwłaszcza wypłaty od dowolnego bębna, Wildy, Scattery i cap.
2. Sprawdzić całą finalną bibliotekę wyników niezależnym kalkulatorem i wyliczyć parametry z wag. Dopiero wtedy utrwalać RTP w UI.
3. Sprawdzić rzeczywisty RGS: portfel, recovery, brak podwójnych zakładów i kompletne replay.
4. Na tej samej paczce przetestować zasady, mobile/popout, audio, autoplay, fastplay i social.
5. Zarchiwizować paczkę, skróty plików, konfigurację, wersję walidatora, raport matematyki, logi testów i ID replay. Dołączyć przynajmniej 10 ręcznie sprawdzonych wygranych każdego trybu, zgodnie z checklistą platformy.
6. Dopiero po usunięciu blokad zgłosić gotową grę. Kryterium mojego odbioru: zero nierozstrzygniętych błędów rozliczenia, sprzecznych zasad i niedziałających wymaganych funkcji; jawna lista pozostałych uwag jakościowych.

Najważniejszy dodatkowy warunek: ten sam wynik musi być zgodny w pięciu miejscach — matematyka, eksport, odpowiedź RGS, animacja oraz zasady. Sam poprawny procent RTP nie gwarantuje tej zgodności.

## 9. Granice aktualności źródeł

20.10.2026 otwarto aktualne Core Requirements i RGS Overview na stakeengine.org oraz oficjalne pliki engineio/docs dotyczące matematyki, frontendu, RGS, replay, social i checklisty. Nowa [Submission Checklist](https://stakeengine.org/docs/approval-guidelines/submission-checklist) oraz [Wallet Endpoints](https://stakeengine.org/docs/rgs/wallet) informują, że są w budowie. Dlatego szczegółowe wymagania uzupełniono oficjalnym repozytorium i wcześniejszym opracowaniem projektu z 19.10.2026. Nie należy przedstawiać wszystkich historycznych detali jako ponownie potwierdzonych na nowym portalu.

Do wyjaśnienia przy finalnym uploadzie: jednostki i krok wypłat w aktualnym walidatorze, konwencja ID, rozbieżne progi częstości maksimum, interpretacja odległości RTP wielu trybów oraz ewentualne flagi jurysdykcji. Publiczna dokumentacja i lokalne testy nie dają dostępu do prywatnego wyniku review.
