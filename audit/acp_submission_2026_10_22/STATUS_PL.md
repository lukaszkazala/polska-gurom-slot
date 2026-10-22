# Zgłoszenie ACP — stan 22.10.2026

**Nie wykonano uploadu, walidacji ACP, uzyskania akceptacji ani audytu końcowego.** Oficjalny panel Engine Studio zatrzymuje się na ekranie logowania; nie ma dostępnej uwierzytelnionej sesji. Logowanie wymaga zaakceptowania polityki prywatności i warunków licencji gry. Te pola pozostawiono niezaznaczone, do decyzji użytkownika bezpośrednio w panelu.

## Zidentyfikowany punkt odniesienia

Zachowano dokładne bajty ostatniej rozpoznanej paczki z poprawkami komunikatów limitu w `unsubmitted_reference/POLSKA_GUROM_RGS_FRONTEND.zip`: SHA256 `c52258d775e16188190f6ac457746ea6cbfe55043ea9c6863669b947246eb2eb`, 14 427 258 bajtów, 18 plików. Obok zachowano trzy wymagane pliki matematyki `0.5.0-any-start`, tryb `base`, koszt 1×. Skróty każdego pliku są w STATUS.json. Sprawdzono integralność archiwum, flagę uruchomienia platformowego, wersję konfiguracji oraz zgodność skopiowanych bajtów i matematyki z zapisanymi skrótami.

To **niezgłoszony punkt odniesienia, nie finalne wydanie do akceptacji**. Wspólny katalog źródłowy jest obecnie zmieniany przez czaty „Dodaj dźwięki i wyciszenie” i „Przygotuj materiały do publikacji”; trwa też „Przetestować telefony i przeglądarki”. Zapisana decyzja o przebudowie rozkładu wysokich wygranych nie jest wdrożona w tej matematyce. Przed zgłoszeniem trzeba ustalić zakres finalnego wydania i zakończyć dotyczące go prace.

Historyczny raport podaje 275 zaliczonych kontroli, ale nie wszystkie wskazują skrót finalnego app.js. 47 kontroli komunikatów limitu jest bezpośrednio związanych z app.js zapisanym w tym ZIP. Nie przypisano pozostałych testów tej paczce ani nie uznano testów lokalnych za odbiór platformy. W tym etapie nie uruchamiano nowych testów gry.

## Dalsze wykonanie po uzyskaniu dostępu

1. Użytkownik loguje się do https://studio.engine.io i wskazuje grę/zespół; haseł ani tokenów nie należy podawać w czacie lub raporcie.
2. Po zakończeniu zmian przygotować nowe, osobno zamrożone wydanie frontendu i matematyki; zapisać skróty ZIP oraz wszystkich uploadowanych plików. Uruchomić odpowiednie testy dokładnie na tej kopii.
3. Wgrać osobno frontend i matematykę zgodnie z panelem. Zapisać identyfikator gry i nadane przez ACP identyfikatory obu wersji, wyniki walidacji oraz powiązanie z lokalnymi skrótami.
4. Sprawdzić uruchomienie na testowej sesji platformy, format zdarzeń, replay, zapis postępu i integrację. Zarejestrować rzeczywiste uwagi ACP; każda poprawka tworzy nową paczkę z nowymi skrótami, ponowną walidacją i właściwym zgłoszeniem.
5. Złożyć osobne wnioski review dla finalnej matematyki i frontendu. Akceptacja zależy od platformy. Zachować dowód statusów obu konkretnych wersji; zgłoszenie wniosku nie oznacza akceptacji.
6. **Dopiero po akceptacji** wykonać końcowy audyt zaakceptowanych wersji i ich dokładnych plików: integralność, pełna matematyka i reguły, regresje rozliczeń/recovery/replay, komunikaty/zasoby oraz wyniki sprawdzeń platformowych. Nie zmieniać audytowanej paczki; każda zmiana unieważnia zgodność skrótów i wymaga nowej oceny.

STATUS.json pozostawia pola identyfikatorów, walidacji, akceptacji i audytu puste lub jako niewykonane. Niczego nie przesłano na platformę i nie zmieniono plików gry ani materiałów w sources/.
