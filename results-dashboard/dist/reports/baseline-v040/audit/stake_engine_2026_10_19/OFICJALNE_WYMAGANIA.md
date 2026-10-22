# Oficjalne wymagania Stake Engine — lista kontrolna

Data sprawdzenia: **19.10.2026**, Europe/Warsaw.

Dokument opisuje wymagania platformy, nie stan zgodności konkretnej paczki gry. Źródła to otwarte pliki oficjalnej dokumentacji `engineio/docs` i oficjalny walidator Math SDK. Pliki źródłowe zostały otwarte i przeczytane; ustalenia nie opierają się wyłącznie na wynikach wyszukiwania. Nie zmieniano implementacji ani materiałów w `sources/`.

## Jak interpretować status

- **Wymóg** — dokumentacja jednoznacznie wymaga danej funkcji lub warunku.
- **Wytyczna oceny** — oczekiwanie review, orientacyjna wartość lub kryterium zależne od charakteru gry.
- **Do wyjaśnienia** — oficjalne źródła zawierają rozbieżne zapisy; samo przejście lokalnego sprawdzenia nie rozstrzyga approval.

## 1. Matematyka

- [ ] **Wymóg:** RTP każdego trybu wynosi 90–98%; opis approval wymaga bliskości RTP trybów do 0,5 punktu procentowego. Podany przykład: baza 97%, pozostałe tryby 96,5–97,5%.
- [ ] **Wymóg:** koszt i maksymalna wygrana każdego trybu zgadzają się z zasadami widocznymi graczowi. Reklamowany max win ma dodatnie prawdopodobieństwo i jest rzeczywiście dostępny.
- [ ] **Wytyczna oceny:** dla slotów dokumentacja wskazuje 100 tys.–1 mln symulacji, różnorodność wyników, rozsądną liczbę płatnych rezultatów i brak nadmiernej dominacji jednej symulacji.
- [ ] **Wytyczna oceny:** trafienie niezerowej wygranej powinno występować częściej niż raz na 20 zakładów; zmienność bazowego trybu 1× ma odpowiadać standardom branży.
- [ ] **Wytyczna oceny:** raport podaje liczbę wyników z niezerową wagą i sprawdza rozkład przedziałów wypłat, w tym pośrednie wygrane między małymi wypłatami a limitem.

Źródło: [Math Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx).

### Rozbieżności, których nie należy przemilczeć

1. **Max win 10 mln / 20 mln.** Strona Math Requirements mówi orientacyjnie o częstości większej niż 1:10 mln, zależnie od kwoty. Oficjalna lista kontrolna podaje 1:20 mln lub częściej. Nie ma podstaw, aby przedstawiać 1:10 mln jako bezwarunkowy, jednolity limit platformy. Wyniki rzadsze od wskazań należy wyjaśnić z review.
2. **Różnica RTP 0,5 p.p. / stała `0.05`.** Opis approval wskazuje 0,5 p.p.; w SDK odnotowano próg `0.05`. Jednostki mają znaczenie: przy RTP zapisanym jako ułamek `0.05` oznacza 5 p.p., a nie 0,05%. Nie należy osłabiać wymagania dokumentacji na podstawie bardziej liberalnego sprawdzenia kodu.
3. **Krok payout 0,01× / 0,1×.** How RGS Works opisuje skalę 100 i dokładność 0,01×. Aktualny walidator SDK wymaga payout całkowitego, nieujemnego, dla dodatniej wypłaty co najmniej 10 oraz `payout % 10 == 0`; w skali 100 oznacza to krok 0,1×. Paczka powinna uwzględnić aktualny walidator i nie opierać się wyłącznie na opisowej granulatności dokumentacji.
4. **Progi 3-star a minimum publikacji.** W `verify_mode_volatility` SDK występują kryteria 3-star, m.in. `prob5k=.01`, `prob10k=.005`, `etl40b=.9`, `etl10k=.8`, `cvar=800`, `rtp=.967`. Nie są one automatycznie ogólnym minimum approval. Oficjalny opis jakości wymaga średniej co najmniej 1,0 gwiazdki z ocen trzech recenzentów.

Źródła: [oficjalna lista kontrolna](https://github.com/engineio/docs/blob/main/static/mockchecklist.json), [walidator SDK](https://github.com/engineio/math-sdk/blob/main/utils/rgs_verification.py), [How RGS Works](https://github.com/engineio/docs/blob/main/src/routes/docs/architecture/how-rgs-works/%2Bpage.svx), [Quality Rankings](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/quality/%2Bpage.svx).

## 2. Kontrakt paczki matematycznej

- [ ] **Wymóg:** plik nazywa się dokładnie `index.json`; pole `modes` zawiera dla każdego trybu `name`, liczbowy `cost`, `events` i `weights`.
- [ ] **Wymóg:** każdy tryb wskazuje istniejący CSV wag i plik `.jsonl.zst` skompresowany Zstandard. Manifest może być wspólny dla wielu trybów.
- [ ] **Wymóg:** CSV nie ma nagłówka; każdy wiersz zawiera ID symulacji, wagę oraz wypłatę jako trzy liczby `uint64`.
- [ ] **Wymóg:** każda linia book jest jednym obiektem JSON zawierającym `id`, `events` oraz `payoutMultiplier`.
- [ ] **Wymóg:** payout w CSV i book jest identyczny. Upload porównuje wyodrębnione wypłaty i ich skróty.
- [ ] **Wymóg:** payout zapisany jest w skali 100, np. 1150 oznacza 11,5× dla kosztu trybu 1×; nie mylić tej skali ze skalą kwot portfela.
- [ ] **Do wyjaśnienia:** How RGS Works opisuje ID od zera odpowiadające indeksowi linii, a FAQ pokazuje przykłady od 1. Spójność konkretnego eksportu należy sprawdzić aktualnym walidatorem i uploaderem.

Przykładowy manifest:

```json
{
  "modes": [
    {
      "name": "base",
      "cost": 1.0,
      "events": "books_base.jsonl.zst",
      "weights": "lookUpTable_base_0.csv"
    }
  ]
}
```

Źródła: [FAQ formatu i wymaganych plików](https://github.com/engineio/docs/blob/main/src/routes/faq/math/what-files-are-required/%2Bpage.svx), [How RGS Works](https://github.com/engineio/docs/blob/main/src/routes/docs/architecture/how-rgs-works/%2Bpage.svx).

## 3. Frontend, grafika i efekty

- [ ] **Wymóg:** własne obrazy, animacje i audio. Assets przykładowych gier web-sdk nie są akceptowane do publikacji.
- [ ] **Wymóg:** brak brakujących zasobów i błędów animacji; działające mobile, skalowanie oraz mały mini-player/popout bez deformowania planszy.
- [ ] **Wymóg:** obrazy i fonty z CDN Stake Engine.
- [ ] **Wymóg:** dostępne zasady, instrukcja przycisków, tabela wszystkich wypłat i wartości symboli specjalnych; opis kosztu, RTP i max win osobno dla każdego trybu; wyjaśnienie wyzwalania funkcji.
- [ ] **Wymóg:** wybór stawek, saldo i czytelna końcowa wygrana. Przy kilku wygrywających akcjach licznik sumuje wypłaty do prawidłowego finału.
- [ ] **Wymóg:** możliwość wyciszenia; spacja powiązana z przyciskiem zakładu; potwierdzenie uruchomienia autoplay, jeśli funkcja istnieje.
- [ ] **Wymóg:** fastplay nadal pozwala odczytać wygrane, kombinacje symboli i informacje.
- [ ] **Weryfikacja:** brak błędów sieciowych i logowania informacji gry; sprawdzenie różnych walut i języków oraz zgodności odtwarzanych rezultatów z zasadami.

Źródło: [Frontend Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/frontend-requirements/%2Bpage.svx).

Dodatkowe punkty oficjalnej checklisty: potwierdzenie trybu kosztującego więcej niż 2×, zachowanie stawki po odświeżeniu w trakcie rundy, sprawdzenie po 10 wygranych każdego trybu z zasadami. [Approval Checklist — dane](https://github.com/engineio/docs/blob/main/static/mockchecklist.json).

## 4. RGS i kwoty

- [ ] **Wymóg:** sesje i transakcje obsługuje RGS. Gra czyta `rgs_url` z parametrów URL, bez stałego adresu serwera.
- [ ] **Wymóg:** statyczny build bez pobierania zewnętrznych źródeł, w tym fontów.
- [ ] **Wymóg:** respektowane minimum, maksimum, dostępne poziomy i krok stawki zwracane przez authenticate; także najniższa i najwyższa stawka możliwe do wybrania.
- [ ] **Wymóg:** język angielski; inne parametry języka nie mogą psuć tekstu, gdy gra obsługuje wyłącznie angielski.

Źródło: [RGS Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/rgs-requirements/%2Bpage.svx).

- [ ] Authenticate poprzedza inne wywołania portfela. Aktywną rundę zwróconą przy wznowieniu należy kontynuować.
- [ ] Dodatnią wygraną zamyka `/wallet/end-round` po wszystkich czynnościach rundy, również bonusie/free spins. Zerowe rundy RGS zamyka automatycznie.
- [ ] Kwoty API są całkowite w skali **1 000 000**; formatowanie zależy od waluty, np. JPY bez miejsc dziesiętnych.

Źródła: [Authenticate](https://github.com/engineio/docs/blob/main/src/routes/docs/api/authenticate/%2Bpage.svx), [End Round](https://github.com/engineio/docs/blob/main/src/routes/docs/api/end-round/%2Bpage.svx), [Currencies](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/currencies/%2Bpage.svx).

**Uwaga o jurisdiction:** przykład odpowiedzi zawiera flagi `disabledTurbo`, `disabledSpacebar` i inne, lecz bieżący opis `config.jurisdiction` mówi „Do not used. Ignore.” Bez dodatkowego potwierdzenia nie należy uznawać braku ich obsługi za jednoznaczne naruszenie approval. Wymagania social opisane poniżej są osobne i jednoznaczne.

## 5. Replay — obowiązkowy

- [ ] **Wymóg:** wykrycie `replay=true` i automatyczne pobranie `GET {rgs_url}/bet/replay/{game}/{version}/{mode}/{event}`.
- [ ] **Wymóg:** replay działa bez sesji i bez wywołań authenticate, balance lub play. Nie pozwala przejść do normalnego obstawiania.
- [ ] **Wymóg:** stan ładowania i obsługa błędów; przycisk rozpoczęcia, pełne animacje/dźwięki/efekty, końcowy wynik oraz ponowne odtworzenie.
- [ ] **Wymóg:** sterowanie zakładami, wybór stawki i autoplay są wyłączone lub ukryte. Widoczne pozostają parametry odtwarzanej rundy.
- [ ] **Wymóg:** prawidłowa obsługa opcjonalnych parametrów, m.in. `amount`, `currency`, `lang`, `social`.
- [ ] **Do review:** ID zwykłej wygranej, dużej wygranej, limitu wygranej, przegranej i wyzwolenia bonusu dla każdego trybu, jeśli dotyczy.

Źródło: [Bet Replay](https://github.com/engineio/docs/blob/main/src/routes/docs/api/bet-replay/%2Bpage.svx).

Oficjalna checklist wymaga także wyraźnego pokazania stawki bazowej, mnożnika kosztu i rzeczywistego kosztu rundy, np. tryb bonus przy stawce 1 USD i koszcie 250 USD. [Approval Checklist — dane](https://github.com/engineio/docs/blob/main/static/mockchecklist.json).

## 6. Stake.us i social

- [ ] **Wymóg dla Stake.us:** przy `social=true` angielski niezależnie od `lang`; wszystkie zakazane określenia zastąpione w UI, zasadach i obrazach.
- [ ] Przykłady: `bet → play`, `buy → play`, `bonus buy → bonus / feature`, `pay table → win table`, `currency → token`, `cash → coins`. Pełny słownik znajduje się w źródle.
- [ ] Sprawdzenie obejmuje również komunikaty błędów, potwierdzenia, nazwy autoplay oraz ekran replay.
- [ ] Obsługa `XGC` i `XSC`, prezentowanych jako GC i SC bez prefiksu `$`.

Źródła: [Social Mode i pełna lista zamian](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/social-mode/%2Bpage.svx), [Currencies](https://github.com/engineio/docs/blob/main/src/routes/docs/reference/currencies/%2Bpage.svx), [Approval Checklist — dane](https://github.com/engineio/docs/blob/main/static/mockchecklist.json).

## 7. Zasady publikacji i disclaimer

- [ ] **Wymóg:** niezależne zakłady; brak jackpotów, gamble, kontynuacji lub wcześniejszego cashoutu.
- [ ] **Wymóg:** oryginalny projekt, respektowanie praw autorskich; brak brandingu Stake/Kick i treści kierowanych do dzieci.
- [ ] Po publikacji dozwolone są drobne poprawki problemów wizualnych; nie zmiany matematyki, trybów lub mechanik.

Źródło: [Approval](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/%2Bpage.svx).

- [ ] **Wymóg:** disclaimer dostępny w zasadach/info. Obejmuje skutki awarii, stabilne połączenie, wznowienie niedokończonych rund przez reload, RTP liczone dla wielu rozgrywek, ilustracyjny charakter animacji, wypłatę określaną przez RGS oraz odpowiednią informację o prawach autorskich. Można użyć własnego brzmienia zawierającego wszystkie te punkty.

Źródło: [Game Disclaimer](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/disclaimer/%2Bpage.svx).

## 8. Kafelek gry

- [ ] Kafelek składany w aktualnym Tile Editorze; logo dostawcy ustawiane w Branding.
- [ ] Jasne tło i brzegi, wyraźny foreground w obszarze zainteresowania, czytelny tytuł w granicach prowadnic.
- [ ] Brak tekstu i mnożników wtopionych w obraz tła/foreground; napis dodawany osobną warstwą tytułu.

Źródło: [Game Tile](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/game-tile/%2Bpage.svx).

## Dostępność i granice sprawdzenia

Publiczna strona `stake-engine.com/docs` zwróciła w narzędziu pustą aplikację JavaScript. Nie traktowano tego jako potwierdzenia wymogu logowania. Treści approval, replay i social były dostępne bez logowania w oficjalnym repozytorium. Nie uzyskano dostępu do prywatnego ACP, faktycznych wyników walidacji uploadu ani statusów Approved/Active konkretnej gry. Zaliczenie tej listy nie zastępuje decyzji review i sprawdzenia paczki na platformie.

