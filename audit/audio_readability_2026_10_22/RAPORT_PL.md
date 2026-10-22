# Dźwięk, wyciszenie i czytelność wygranych

Wykonano 22.10.2026 w aktualnym testerze `test-interface-any-start`, matematyka `0.5.0-any-start`.

## Zmiany

Zintegrowano sześć istniejących autorskich plików folk/disco z `music-polska-gurom-v1/wav`. To przygotowany wcześniej szkic v1, bez nowego masteringu. Zasoby są identyczne z oryginałami; parametry i porównanie zapisano w `assets.json`.

Web Audio odtwarza bezszwowe pętle bazy i bonusu, przenikanie 300 ms i ściszenie tła pod sygnałami. Tylko jeden sygnał jednorazowy może grać równocześnie. Brak wygranej milczy; zwrot mniejszy lub równy stawce używa neutralnego sygnału. Fanfara zwykła dotyczy wyniku ponad stawkę, a większa wyniku od 20×. Tryb błyskawiczny gra sygnał końcowy całej rundy.

Przycisk głośnika ma obszar 44×44 px i etykiety PL/EN/DE. Jest dostępny podczas obrotu. Wyciszenie natychmiast zeruje wspólną głośność, ucina sygnał i zapisuje preferencję. Ukrycie karty wycisza całość, a powrót nie odtwarza pominiętych sygnałów. Dźwięk zaczyna się po obrocie lub włączeniu dźwięku. Błąd pobrania, blokada przeglądarki lub brak Web Audio nie blokuje gry.

## Czas na odczyt

Wcześniej funkcja wspólnych opóźnień skracała część prezentacji turbo do 35 ms. Czas odczytu oddzielono od szybkości animacji i preferencji ograniczonego ruchu.

| Pokazywany wynik | Minimalna pauza przed kolejną rundą AUTO |
|---|---:|
| Częściowy / równy zwrot stawki | 900 ms |
| Wygrana ponad stawkę, poniżej 20× | 1200 ms |
| Co najmniej 20× | 1800 ms |
| Limit 5000× | 2400 ms |

Wygrywające etapy kaskad mają 450 ms na odczyt w szybkim/turbo i 650 ms w normalnym tempie. Dodatnia wypłata darmowego obrotu ma 700 ms. Ręczne uruchomienie kolejnego obrotu po zakończeniu rundy pozostaje dostępne. Kwota końcowa ma większy krój pisma, ciemne tło i nie znika do następnej rundy. Styl jest zachowany po odświeżeniu i zmianie języka.

## Weryfikacja

- `test_audio_readability.cjs`: **24/24**, w tym brak fanfar dla zwrotów, natychmiastowe wyciszenie, zapis preferencji, ukrycie karty, opóźnione/błędne zasoby, jedna aktywna fanfara, czasy wszystkich klas wyniku w turbo/błyskawicznym i ograniczonym ruchu oraz przycisk podczas obrotu w PL/EN/DE. Dźwięk: symulowany graf Web Audio; logika gry: rzeczywisty kod i scenariusze z silnika.
- Regresja AUTO: **13/13**, w tym po 100 rund w czterech trybach, bonusy, STOP, odzyskiwanie odpowiedzi i brak podwójnych obciążeń.
- Komunikaty limitu: **47/47**; replay: **34/34**; lokalizacja: **73/73**; RGS: **60/60**; odzyskiwanie RGS: **33/33**; wygrana od przesuniętego bębna: **3/3**. Łącznie **287 sprawdzeń**.
- Przeglądarka: rzeczywista gra lokalna pod `127.0.0.1:8774`, desktop 1280×720, telefon 390×844 i 320×740. Obejrzano wygraną w turbo, końcowy wynik trybu błyskawicznego i zachowanie po odświeżeniu. Brak poziomego przepełnienia. Przy 320 px dłuższy podpis poprawnie zajmuje dwa wiersze. Zapis wyciszenia potwierdzono po odświeżeniu. Wszystkie sześć WAV pobrano z odpowiedzią HTTP 200; konsola bez błędów i ostrzeżeń.
- Zrzuty: `desktop-turbo.jpg`, `mobile-turbo.jpg`, `mobile-320.jpg`.
- Trzy paczki ZIP sprawdzono pod względem integralności i zgodności nowego kodu oraz sześciu WAV z plikami roboczymi: `packages.json`.

Nie wykonywano odsłuchu na fizycznych głośnikach ani pomiaru głośności całego miksu. Kontrola dotyczy integracji technicznej i czytelności na wskazanych widokach; nie potwierdza wdrożenia na rzeczywistej platformie RGS. Materiały w `sources/` i matematyka gry nie były edytowane.

## Dostarczenie

Zaktualizowano `POLSKA_GUROM_TESTER.zip`, `POLSKA_GUROM_RGS_FRONTEND.zip` i `POLSKA_GUROM_RGS_TEST.zip` w folderze aktualnego testera. Demo uruchamia się przez `START_UX.cmd` po wypakowaniu całego ZIP. Źródła sprzed zmiany znajdują się w `before/`.
