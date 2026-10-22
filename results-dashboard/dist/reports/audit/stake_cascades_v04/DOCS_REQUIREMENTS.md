# Kontrakt matematyki kaskad i eksportu Stake Engine

Sprawdzono **19.10.2026, Europe/Warsaw**, bezpośrednio w aktualnych publicznych plikach oficjalnych repozytoriów `engineio/docs` i `engineio/math-sdk`, gałąź `main`. Punktem wyjścia był wcześniejszy audyt `audit/stake_engine_2026_10_19/OFICJALNE_WYMAGANIA.md`; poniższe ustalenia zweryfikowano ponownie. Publiczna strona renderowana JavaScript nie dostarczyła treści; wykorzystano otwarte źródła dokumentacji. Nie uzyskano prywatnego approval/uploadera.

## Wymagania i wytyczne matematyczne

| Warunek | Jak go stosować |
|---|---|
| RTP **90–98%** w każdym trybie | Wymóg dokumentacji; 96%, 96,5% ani 96,7% nie są uniwersalnym obowiązkowym celem. |
| RTP trybów różnią się najwyżej o **0,5 punktu procentowego** | Stosować ostrzejszy opis approval, nie liberalniejszy próg ostrzeżenia SDK. |
| Koszt i maksymalna wygrana odpowiadają zasadom gry | Limit musi być dostępny z dodatnim prawdopodobieństwem. |
| Max win zwykle częściej niż **1:10 mln**, zależnie od wypłaty | Wytyczna oceny; checklist podaje **1:20 mln lub częściej**. Źródła są rozbieżne; przyjąć konserwatywnie częściej niż 1:10 mln i ujawnić przyjęty cel. |
| Slot: **100 tys.–1 mln symulacji** dla różnorodności | Wytyczna review, nie twardy limit liczby Monte Carlo. Powtórzenie kilku takich samych books milion razy nie zapewnia różnorodności. |
| Niezerowe wyniki częściej niż **1:20** | Ocena jakości rozkładu; checklist wskazuje typowo **1:3–1:8** w bazie. |
| Raport rozkładu | Liczba wypłat i wag dodatnich, udział płatnych rezultatów, dominacja pojedynczego book, przedziały wygranych, zmienność i dostępność pośrednich wypłat. |

Źródła: [Math Requirements](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/math-requirements/%2Bpage.svx), [oficjalna checklist](https://github.com/engineio/docs/blob/main/static/mockchecklist.json).

## Znaczenie jednej rundy i prawdopodobieństw

RGS wybiera **gotowy book według wagi**; nie losuje kaskad w przeglądarce. Book musi opisywać całą płatną rundę: początkową planszę, wszystkie usunięcia i opadania, uzupełnienia, bonus/free spins, wszystkie wygrane i ostateczny wynik. Każdy zakład jest niezależny od wcześniejszych wyników. Stan kaskady wewnątrz jednej rundy jest częścią tej rundy; nie może przenosić przewagi na następną płatną rundę. Limit 5000× przy deklaracji takiego limitu musi dotyczyć sumy całej rundy, a nie osobno każdego spadania.

Źródła: [How RGS Works](https://github.com/engineio/docs/blob/main/src/routes/docs/architecture/how-rgs-works/%2Bpage.svx), [Approval](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/%2Bpage.svx).

Poniższe równania są bezpośrednim wyprowadzeniem z modelu wag. Dla book `i`: `w_i` to jego całkowita waga, `u_i` to całkowita wypłata w skali 100, `c` to koszt trybu w jednostkach bazowej stawki, `W = Σw_i`:

```text
P(book i)       = w_i / W
RTP            = Σ(w_i × u_i) / (100 × c × W)
P(wygrana > 0) = Σ(w_i dla u_i > 0) / W
P(max win)     = Σ(w_i dla u_i = u_max) / W
częstość 1:N   = 1 / P(zdarzenie)
```

Koszt trybu w mianowniku jest niezbędny. Przykładowo 96× wypłaty średnio przy koszcie 100× daje RTP 96%. Kontrola rozkładu ma uwzględniać faktyczne wagi, również gdy books celowo generowano z wymuszeniem rzadkich zdarzeń.

## Pliki publikacji

Manifest musi nazywać się `index.json`. Dla każdego trybu zawiera `name`, liczbowy `cost`, nazwę `events` oraz `weights`. Pliki istnieją i odpowiadają tej samej wersji matematyki. LUT jest CSV bez nagłówka: trzy wartości `uint64` — ID, waga, wypłata. Books to Zstandard `.jsonl.zst`; każda linia zawiera `id`, `events`, `payoutMultiplier`. Wypłaty LUT i books muszą zgadzać się dokładnie, w tej samej kolejności.

Źródło: [What files are required?](https://github.com/engineio/docs/blob/main/src/routes/faq/math/what-files-are-required/%2Bpage.svx).

Skala mnożnika wynosi **100**: `1150` oznacza 11,5× bazowej stawki. Użyć ID **0..N−1**, zgodnych z fizycznym indeksem linii book; jest to jednoznaczny zapis How RGS Works. FAQ pokazuje przykład od 1, dlatego nie należy traktować go jako dowodu wymaganego indeksowania od 1. Zastosować osobną kontrolę ID, długości, referencji plików i typów.

Źródło: [How RGS Works — format](https://github.com/engineio/docs/blob/main/src/routes/docs/architecture/how-rgs-works/%2Bpage.svx).

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

## Rzeczywiste kontrole aktualnego Math SDK

`verify_lookup_format` sprawdza nieujemne całkowite wypłaty; dodatnia wypłata ma co najmniej **10** i `payout % 10 == 0`. Wagi są całkowite i nieujemne, suma wag nie przekracza **18446744073709551615**. Books wymagają `id`, `events`, `payoutMultiplier`; porównanie skrótów tablic wypłat wykrywa zmianę wartości, kolejności lub długości. Obsługiwane rozszerzenia walidatora to `.jsonl.zst` i `.jsonl.zstd`.

Opis architektury dopuszcza krok 0,01×, lecz walidator wymaga **0,1× w skali 100**. Dla tej wersji eksportu przyjąć krok 0,1×. Nie wolno jedynie zaokrąglić eksportu przy zachowaniu innej wypłaty w silniku i UI.

Kontrola różnic RTP w SDK ostrzega dopiero powyżej `0.05` przy zapisie RTP jako ułamka; oznacza to 5 p.p. i nie zastępuje 0,5 p.p. z approval. `verify_mode_volatility` raportuje kryteria **3-star**, m.in. `rtp=0.967`, `prob5k=0.01`, `prob10k=0.005`, `etl40b=0.9`, `etl10k=0.8`, `cvar=800`; są to ostrzeżenia jakościowe, a nie uniwersalne minimum publikacji.

Źródło: [aktualny walidator SDK](https://github.com/engineio/math-sdk/blob/main/utils/rgs_verification.py). Zasady ocen opisano osobno w [Quality Rankings](https://github.com/engineio/docs/blob/main/src/routes/docs/approval/quality/%2Bpage.svx).

Obserwacja do implementacji: sam walidator parsuje wartości przez `float`, więc nie powinien być jedyną kontrolą `uint64`. Lokalny audyt powinien parsować wszystkie trzy pola jako liczby całkowite z kontrolą zakresu, wymagać `W > 0`, sprawdzić ID i brak powtórzeń. To dodatkowe kontrole spójności, nie twierdzenie o kompletnym zachowaniu prywatnego uploadera.

## Kontrakt testów dla tego zadania

Poniższe punkty są planem weryfikacji implementacji, nie dodatkowymi oficjalnymi wymaganiami platformy.

1. Sprawdzić wszystkie wygrane liniowe i Wild; każdą kaskadę niezależnie przeliczyć z planszy. Usuwane pola są sumą pól wygrywających linii, bez wielokrotnego usuwania przecięcia. Pozostałe symbole zachowują kolejność i opadają; nowe symbole uzupełniają wolne miejsca od góry.
2. Zweryfikować naliczanie scatter, bonus i brak dodatkowej stawki podczas kaskad. Limit rundy stosuje się do całej sumy; wszystkie końcowe wypłaty, UI, books i LUT są identyczne.
3. Dokładnie policzyć RTP i prawdopodobieństwa z **końcowej** LUT. Dodatnia waga max win oraz jawny poprawny book są dowodem osiągalności; samo obcięcie wypłaty do 5000× nie dowodzi jego osiągalności.
4. Uruchomić regresje wcześniej istniejące i osobne kampanie **10 000 000, 50 000 000 oraz 100 000 000** rzeczywistych losowań docelowego modelu. Zapisać metodę, seed, liczbę rund, czas, wersję/skrót danych, RTP, odchylenie standardowe, przedział ufności, hit rate, max win i rozkład wypłat. Wyników nie ekstrapolować z krótszego przebiegu.
5. Rozróżnić dwa dowody: losowanie z końcowej LUT bada rozkład faktycznie używany przez RGS; symulacja generatora bez wag bada inny rozkład, jeśli użyto optymalizacji wag. Test powtórzonych losowań LUT nie jest testem poprawności zdarzeń każdej kaskady; do tego potrzebny jest niezależny przegląd books.
6. Brak max win w skończonej próbce nie dowodzi jego niemożliwości. Oczekiwana liczba trafień to `n × p`; prawdopodobieństwo zera to `(1−p)^n`. Obok Monte Carlo pokazać dokładne wartości wynikające z LUT.

Testy lokalne i zgodność struktury plików **nie stanowią zatwierdzenia Stake Engine**. Końcowy status publikacji zależy od sprawdzenia uploaderem i review platformy.
