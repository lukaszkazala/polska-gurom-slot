# POLSKA GUROM — Karczma Disco, szkic muzyczny v1

Autorska muzyka instrumentalna przygotowana 19 października 2026 r. dla projektu POLSKA GUROM. Kierunek wybrany przez użytkownika: **humorystyczny folk / disco**.

Akordeon o syntezowanym brzmieniu, cymbałowe szarpnięcia, sprężysty bas, taneczna stopa i klaskanie. W bonusie dochodzą gęstsza perkusja, galopujące akcenty i syntezatorowe dęciaki. Bez wokalu. Jest to pierwsza wersja do oceny stylu i brzmienia; instrumenty powstały przez syntezę, bez nagrań żywych muzyków i bez zewnętrznych sampli.

## Odsłuch

Otwórz **ODSLUCH_FOLK_DISCO_44s.wav**:

| Czas | Fragment |
| --- | --- |
| 0:00–0:20 | Zwykła gra — Karczma Disco |
| 0:20–0:24 | Wejście do bonusu |
| 0:24–0:40 | Szarża Husarza — muzyka bonusowa |
| 0:40–0:44 | Duża wygrana / zakończenie odsłuchu |

## Pliki do gry

| Plik w folderze `wav/` | Długość | Użycie |
| --- | ---: | --- |
| `01_Karczma_Disco_BASE_120bpm_Dm.wav` | 64 s | Pętla tła zwykłej gry, 32 takty |
| `02_Szarza_Husarza_BONUS_120bpm_Dm.wav` | 32 s | Pętla bonusu, 16 taktów |
| `03_Wejscie_do_bonusu.wav` | 4 s | Jednorazowa zapowiedź bonusu |
| `04_Wygrana.wav` | 2 s | Krótki sygnał wygranej netto |
| `05_Duza_wygrana.wav` | 4 s | Dłuższy sygnał dużej wygranej netto |
| `06_Czesciowy_zwrot.wav` | 2 s | Cichy, pojedynczy dźwięk neutralny; plik zawiera wybrzmienie |

WAV: stereo, PCM 16 bit, 44,1 kHz. Tempo 120 BPM, metrum 4/4, tonacja d-moll; dominanta A z C♯. Pętle mają dokładną długość taktową i zawinięte wybrzmienia. Należy odtwarzać je z zapętleniem bez przerwy; w przeglądarce najlepiej użyć zdekodowanego bufora Web Audio. Nie dodawać ciszy ani fade-outu do samych plików pętli.

Przy zmianie tła zwykłej gry na bonus zastosować krótkie przenikanie głośności lub przejście na granicy taktu. Pod sygnałami jednorazowymi ściszyć tło. Sam odsłuch 44 s jest montażem demonstracyjnym, nie pętlą do gry.

Częściowy zwrot poniżej stawki ma neutralny dźwięk, wyraźnie cichszy od fanfar. Sygnałów wygranej używać przy dodatnim wyniku netto, zgodnie ze sposobem prezentowania wyniku w projekcie. Muzyka tła ma stałą aranżację, niezależną od historii wyników.

## Dalsza edycja

Folder `midi/` zawiera sześć plików MIDI z osobnymi ścieżkami instrumentów. Można zmienić melodię, tempo lub instrumenty w programie muzycznym. Brzmienie MIDI zależy od użytych instrumentów i będzie różnić się od plików WAV.

W folderze `production/` znajdują się źródło kompozycji i techniczne wyniki kontroli. Do ponownego renderowania potrzebne są Python, NumPy i SciPy. Obecny tester slota nie został zmodyfikowany; paczka zawiera osobne zasoby audio.
