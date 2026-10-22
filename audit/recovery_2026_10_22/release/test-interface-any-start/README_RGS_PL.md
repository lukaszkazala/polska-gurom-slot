# POLSKA GUROM — integracja RGS, aktualizacja 22.10.2026

Przygotowano klienta kontraktu Stake Engine i testy lokalne. **Nie wykonano połączenia z prawdziwym środowiskiem Stake ani akceptacji ACP.** Brak dostępu do środowiska testowego potwierdzono z użytkownikiem. Paczki są gotowe do dalszej integracji i jej odbioru, nie oznaczają zatwierdzenia publikacji.

## Lokalne sprawdzenie

Wypakuj **POLSKA_GUROM_RGS_TEST.zip** do osobnego folderu i uruchom **START_RGS_TEST.cmd**. Potrzebny Python 3.12+. Przeglądarka otworzy lokalny symulator pod portem 8800. Saldo jest wyłącznie wirtualne. Zakończenie procesu usuwa dane symulatora.

Symulator celowo odtwarza jedną rzeczywistą rundę „middle” z aktualnego banku, aby łatwo sprawdzić rozliczenie: 100 USD, stawka 0,50 USD, wypłata 0,15 USD, końcowe saldo 99,65 USD. To test kontraktu, nie losowanie RTP. Inne scenariusze: `python qa/rgs_mock_server.py --scenario bonus12 --port 8801` (również `loss`, `bonus8`, `cap`, `middle`). Każda próba tego symulatora powtarza wybrany scenariusz.

Z kodu projektu można również uruchomić `python test-interface-any-start/qa/rgs_mock_server.py`. Symulator przyjmuje tylko stałą, publiczną sesję testową `local-test-session`; nie podawaj mu prawdziwych tokenów. Nasłuchuje wyłącznie na 127.0.0.1. Nie jest częścią paczki interfejsu dla platformy.

## Paczka dla serwera platformy

**POLSKA_GUROM_RGS_FRONTEND.zip** zawiera pliki statyczne z `index.html` na najwyższym poziomie, zachowane tło husarii i `game-config.json`. Nie zawiera lokalnego serwera, symulatora, wyboru wyniku ani silnika Pythona. Zwykła gra wymaga uruchomienia z sesją platformy. Publiczny replay działa bez sesji; brak prawidłowego uruchomienia nie przełącza paczki na demo.

Budowanie obu paczek: `python test-interface-any-start/build_rgs.py`. Osobna paczka lokalnego demo nadal powstaje przez `package_demo.py`.

W panelu platformy trzeba oddzielnie załadować **dokładnie aktualny** eksport `stake_math/index.json`, wskazane przez niego books i CSV. Tryb tej matematyki nazywa się **base**, ma koszt 1×. Klient wysyła `mode: "base"`, zgodnie z manifestem; przykładowego `BASE` z dokumentacji nie traktuje jako nazwy naszego trybu.

Uruchomienie przez operatora ma postać `https://HOST_GRY/SCIEZKA/?sessionID=TOKEN&rgs_url=HOST_RGS&lang=pl&demo=true`. `HOST_RGS` jest samą nazwą hosta, bez protokołu i ścieżki. Klient dodaje HTTPS. Jedyny wyjątek HTTP to symulator na dokładnie tym samym lokalnym hoście i porcie co strona. Token dostarcza operator w linku uruchomienia; nie wpisuje się go do kodu, paczki, raportu ani czatu.

Adres RGS i jego sesja pochodzą wyłącznie z parametrów uruchomienia. Nie wpisano na stałe adresu Stake. Błąd sesji lub niekompletne parametry blokują grę; nie uruchamiają alternatywnego portfela demo. Endpoint musi dopuszczać połączenia z docelowej domeny gry zgodnie z ustawieniami platformy.

## Zaimplementowany cykl

1. `POST /wallet/authenticate`: sesja, saldo, waluta, minimum, maksimum, krok, dozwolone poziomy i domyślna stawka. Aktywna runda jest wznawiana, bez nowego zakładu. `lang` obsługuje PL/EN/DE; nieobsługiwany lub pusty kod przechodzi na EN.
2. `POST /wallet/play`: jeden zakład `base` za całą rundę, kaskady i wszystkie darmowe obroty. Wynik pochodzi z RGS. Nie jest losowany ani przeliczany lokalnie w celu wyboru wygranej.
3. Pełna walidacja wyniku i animacja. Kwoty portfela są całkowite w skali 1 000 000; `payout_units` w book używa skali 100. Obliczenia wypłaty używają BigInt, a format waluty uwzględnia liczbę miejsc dziesiętnych, np. JPY i KWD.
4. `POST /wallet/end-round` po prezentacji całej aktywnej rundy. Gdy RGS zwraca `active: false`, klient nie wywołuje zakończenia. Końcowe saldo jest odpowiedzią serwera, a nie lokalnym dodaniem wygranej.
5. `POST /wallet/balance` co minutę podczas bezczynności, poza rundą i otwartym odczytem. Starsza odpowiedź nie cofa salda po nowszym rozpoczęciu/rozliczeniu rundy.

W interfejsie zachowano historyczne nazwy wewnętrznych pól `*_cents` dla współdzielonego kodu demo. **W ścieżce RGS ich wartości są mikrojednostkami waluty**, nie groszami. `amount_scale` wynosi 1 000 000, a waluta pochodzi z authenticate. Tych wewnętrznych nazw nie wysyła się do RGS; jego kontrakt używa `amount`, `mode`, `sessionID`.

Nasz eksport koduje pełną rundę jako `state: [{index: 0, type: "roundResult", data: ...}]`. Ten format trzeba potwierdzić na realnym uploadzie bieżącego banku. Klient wymaga poprawnego `betID`, `active`, `amount` i zgodnego trybu. Nie zgaduje obcych formatów zdarzeń ani wersji matematyki. Kwota `payout`, jeśli serwer ją zwraca, musi zgadzać się z wynikiem book.

## Odporność na przerwania

Oficjalny kontrakt play nie opisuje klucza idempotencji. Dlatego klient **nie ponawia automatycznie zakładu o nieznanym wyniku**. Zachowuje zamiar i odczytuje authenticate. Jeżeli serwer pozwala rozpoznać nową rundę, prezentacja jest wznawiana. Gdy brak identyfikowalnej rundy — np. utracona odpowiedź zerowej rundy i `round: null` — dalsze zakłady pozostają zablokowane. Ten przypadek wymaga sprawdzenia z platformą; nie przedstawiamy go jako pełnego recovery produkcyjnego.

Utracone potwierdzenie wypłaty jest sprawdzane przez authenticate przed następnym end-round. Inna aktywna runda albo zmieniona treść wyniku pod tym samym betID blokuje zamknięcie przez stary widok. Identyfikator i postęp prezentacji pozostają do zakończenia rozliczenia. AUTO zatrzymuje się po błędzie i nie startuje samo po odświeżeniu. Stawka RGS jest zapamiętywana osobno od stawek lokalnego demo. Token sesji nie trafia do historii, eksportu ani pamięci odzyskiwania.

Po ukończeniu bazy i każdego darmowego obrotu klient wysyła **POST /bet/event** z ciągiem JSON opisującym postęp prezentacji. Znacznik zawiera wersję protokołu, nazwę gry, wersję matematyki, betID i liczbę ukończonych FS. Nie zawiera stawki do pobrania ani decyzji o wypłacie. Authenticate zwraca zapis w `round.event`, dzięki czemu również nowa karta bez poprzedniego sessionStorage może wznowić pokaz od następnego FS. Niepełny obrót może zostać odtworzony od początku.

Klient sprawdza tożsamość rundy i zakres znacznika, wybiera najdalszy poprawny ukończony etap spośród zapisu lokalnego i serwerowego, a błędny lub obcy znacznik pomija. Awaria zapisu postępu zatrzymuje prezentację i AUTO; wynik oraz żądanie pozostają do ponownego odczytu. Ponowienie nie wysyła play. Przed rozliczeniem weryfikowana jest ponownie treść aktywnego wyniku. Równoczesne operacje checkpoint/finish w jednym kliencie są blokowane.

Po odświeżeniu wstrzymanego bonusu widać zachowany etap, stawkę i dotychczas pokazaną wygraną, np. 4/12. Przycisk PONÓW ODCZYT wznawia tę samą rundę. Jeśli samo otwarcie sesji się nie powiedzie, przycisk POŁĄCZ PONOWNIE powtarza uwierzytelnienie bez dodawania drugich przycisków, bębnów ani obsługi kliknięć. Nierozliczonej rundy nie dopisuje się do historii ukończonych rund. Usunięcie stawki z nowych poziomów operatora nie przerywa już opłaconego bonusu; nową dozwoloną stawkę wybiera się dopiero po jego rozliczeniu.

Próbę awarii można uruchomić lokalnie przez `python qa/rgs_mock_server.py --scenario bonus12 --fail-event-at 4 --port 8804`. Symulator jednorazowo zrywa odpowiedź po zapisaniu czwartego FS. Saldo pozostaje wirtualne; po odświeżeniu i dokończeniu należy sprawdzić jeden zakład i jedną wypłatę. Ta opcja nie trafia do statycznej paczki platformowej.

## Replay ukończonych rund

Otwórz **Ustawienia → Historia rund**, wybierz wynik i w szczegółach kliknij **Odtwórz rundę**. Replay pokazuje zapisany wynik od początku: bazę, kaskady, wszystkie wykonane darmowe obroty i zakończenie bonusu lub maksymalną wygraną 5000×. Nie wysyła nowego zakładu, znacznika postępu ani rozliczenia; nie zmienia salda, statystyk ani historii. Powtórzenie jest dostępne po ukończeniu pokazu. Podczas aktywnej lub oczekującej rundy i AUTO nie można uruchomić replay.

Historia RGS przechowuje do 100 ukończonych rund w tej samej karcie, również po jej odświeżeniu, o ile przeglądarka udostępnia `sessionStorage`. Jest to zapis pomocniczy; jego brak lub usunięcie nie zmienia rozliczenia na serwerze. Token sesji nie jest częścią zapisu rundy ani eksportu. Historia w lokalnym demo nadal pochodzi z pamięci serwera demo.

Publiczny link replay działa bez `sessionID`:

`https://HOST_GRY/SCIEZKA/?replay=true&game=UUID_GRY&version=WERSJA_MATEMATYKI&mode=base&event=ID_SYMULACJI&rgs_url=HOST_RGS&amount=500000&currency=USD&lang=pl`

Wymagane są `replay=true`, `game`, `version`, `mode`, `event` i `rgs_url` bez protokołu oraz ścieżki. Wersję i identyfikator zdarzenia nadaje załadowany eksport platformy; nie należy zastępować ID symulacji identyfikatorem zakładu. `amount` to stawka w mikrojednostkach: 500000 oznacza 0,50. Opcjonalne `currency` i `lang` ustalają walutę oraz język. Brak lub nieprawidłowa wartość opcjonalna korzysta z domyślnych: 1,00 USD i EN. Obsługiwany tryb tej gry to `base`, koszt 1×. Parametry `social` i `demo` w publicznym replay są informacją o prezentacji i nie uruchamiają portfela. Zwykła gra social pozostaje nieobsługiwana.

Klient pobiera `GET /bet/replay/{game}/{version}/{mode}/{event}`, sprawdza pełny zapis `roundResult` oraz zgodność mnożnika wypłaty i kosztu. Po wczytaniu czeka na **Odtwórz**; po pokazie oferuje **Odtwórz ponownie**. Wszystkie animacje rundy są odtwarzane, także gdy zwykła gra ma włączony tryb błyskawiczny. W publicznym replay nie ma uwierzytelniania, odczytu salda, zakładów ani przejścia do normalnej gry. Brak zdarzenia, brak stanu lub niezgodny wynik wyświetla błąd.

Lokalna próba pełnego bonusu: `python qa/rgs_mock_server.py --replay --scenario bonus12 --port 8805`. Próba maksimum: `python qa/rgs_mock_server.py --replay --scenario cap --port 8806`. Z katalogu całego projektu dodaj przed ścieżką `test-interface-any-start/`. Symulator otwiera publiczny link ze stawką 0,50 USD i obsługuje także `loss`, `bonus8` oraz `middle`. Kontrola `http://127.0.0.1:PORT/__rgs-test/state` pokazuje ścieżki żądań; przy samym publicznym replay liczby zakładów i wypłat pozostają zerowe.

## Zakres do potwierdzenia na platformie

- Prawdziwy launch, ważna sesja i ustawienia CORS/hostingu.
- Format odpowiedzi rundy po uploadzie aktualnej matematyki, w tym bazowa nazwa trybu `base`.
- Błędy i wygasanie sesji operatora, niejednoznaczne przerwania oraz współbieżność wielu kart. Sam kontrakt sesyjnego end-round nie pozwala dołączyć oczekiwanego `betID`; sprawdzenie ID przez authenticate nie zastępuje gwarancji serwera przy zmianie rundy w innej karcie.
- Zapis `/bet/event` i wznowienie bez poprzedniej pamięci przeglądarki są wdrożone oraz sprawdzone lokalnie. Na prawdziwej platformie pozostaje potwierdzić obsługę znacznika JSON, jego dopuszczalną długość, limity żądań oraz trwałość `round.event` między sesjami/urządzeniami.
- Replay jest wdrożony i sprawdzany lokalnie. Na prawdziwym środowisku pozostają do potwierdzenia identyfikatory gry/wersji/zdarzeń, dostępność pełnego stanu, kontrakt odpowiedzi i CORS. Zwykłe uruchomienia `social=true` oraz waluty XSC/XGC pozostają nieobsługiwane.
- Końcowe komunikaty wymagane przez platformę, audio, urządzenia fizyczne i odbiór ACP pozostają otwarte.

## Źródła kontraktu

- [Stake Engine RGS](https://stake-engine.com/docs/rgs)
- [Authenticate — oficjalne źródło](https://github.com/engineio/docs/blob/main/src/routes/docs/api/authenticate/%2Bpage.svx)
- [Play — oficjalne źródło](https://github.com/engineio/docs/blob/main/src/routes/docs/api/play/%2Bpage.svx)
- [End round — oficjalne źródło](https://github.com/engineio/docs/blob/main/src/routes/docs/api/end-round/%2Bpage.svx)
- [Typy oficjalnego klienta](https://github.com/engineio/ts-client/blob/main/src/types.ts)
- [Event — oficjalne źródło](https://github.com/engineio/docs/blob/main/src/routes/docs/api/event/%2Bpage.svx)
- [Wymagania replay](https://stake-engine.com/docs/approval-guidelines/game-replay-requirements)
- [Replay — oficjalne źródło](https://github.com/engineio/docs/blob/main/src/routes/docs/api/bet-replay/%2Bpage.svx)

Kontrakty event i replay sprawdzono 22.10.2026. Schemat wymaga odbioru na rzeczywistym środowisku; testy kontraktu z symulatorem nie są akceptacją platformy.
