# Dźwięki POLSKA GUROM

Zintegrowany zestaw folk/disco pochodzi z autorskiej paczki projektu `music-polska-gurom-v1/wav` (19.10.2026). Pliki są identyczne z oryginałami: stereo PCM 16 bit, 44,1 kHz. Bez zewnętrznych sampli. Jest to dotychczasowy szkic muzyczny v1 wybrany do tej integracji, nie nowy mastering.

- `01_…` — pętla podstawowa, 64 s.
- `02_…` — pętla bonusowa, 32 s.
- `03_…` — wejście do bonusu, 4 s.
- `04_…` — wygrana netto, 2 s.
- `05_…` — wynik co najmniej 20× stawki, 4 s; dotyczy również maksimum.
- `06_…` — neutralny, cichszy sygnał częściowego zwrotu lub zwrotu stawki, 2 s.

`audio.js` dekoduje WAV do buforów Web Audio. Muzyka startuje po pierwszym obrocie lub włączeniu dźwięku. Pętle mają przenikanie 300 ms; tło jest ściszane pod sygnałem. Jednocześnie gra najwyżej jeden sygnał wyniku. Kolejna runda ucina poprzedni sygnał; brak wygranej nie gra fanfary. Tryb błyskawiczny odtwarza tylko sygnał wyniku całej rundy, bez wejścia do pominiętego bonusu.

Wyciszenie i ukrycie karty zerują wspólną głośność natychmiast. Wyciszenie jest zapisywane w przeglądarce. Po powrocie do karty pominięte sygnały nie są odtwarzane. Niedostępność plików lub Web Audio pozostawia działającą grę bez dźwięku i nie wstrzymuje rozliczenia.
