# Odbiór odzyskiwania rund na rzeczywistym Stake Engine

Data: 22.10.2026. **Wszystkie poniższe próby pozostają niewykonane na rzeczywistym środowisku.** Użytkownik potwierdził brak dostępu i wybrał przygotowanie oraz weryfikację lokalną. Testy HTTP z symulatorem nie zastępują tego odbioru.

Warunki rozpoczęcia: zatwierdzone środowisko testowe operatora, aktualna paczka interfejsu, pasujący eksport matematyki 0.5.0-any-start z trybem `base`, testowa sesja oraz dostęp do dziennika transakcji RGS. Nie używać pieniędzy produkcyjnych. Tokenów sesji nie zapisywać w raporcie.

| Próba | Wymagany wynik i dowód |
|---|---|
| Pierwsze uruchomienie | Authenticate działa z hostem z linku. Saldo, waluta i stawki odpowiadają platformie; frontend nie uruchamia portfela demo. |
| Utrata odpowiedzi play po pobraniu stawki | Authenticate zwraca tę samą aktywną rundę. Brak drugiego play. W dzienniku operatora dokładnie jedno obciążenie. |
| Zerwanie przed dostarczeniem play | Bez identyfikowalnej rundy klient zachowuje blokadę. Należy ustalić z platformą sposób jednoznacznego sprawdzenia, czy żądanie zostało wykonane. Nie zakładać, że wolno powtórzyć zakład. |
| Odświeżenie podczas bonusu | Stawka i właściwy betID pozostają. Zapisany etap 4/12 pozwala wznowić od piątego FS. Niepełny obrót może odtworzyć się od początku, bez dodatkowego obciążenia. |
| Nowa karta / inne urządzenie | Authenticate zwraca aktywną rundę i właściwy `round.event`, także bez poprzedniego sessionStorage. Sprawdzić, czy nowy token operatora odnosi się do tej samej rundy. |
| Limit i format bet/event | Serwer przyjmuje znacznik JSON z wersją, grą, matematyką, betID oraz ukończonym etapem. Potwierdzić maksymalną długość, limity żądań i trwałość znacznika. |
| Utrata potwierdzenia bet/event | Zapisany postęp można odczytać przez authenticate. Ponowienie nie rozpoczyna nowej rundy. AUTO pozostaje zatrzymane. |
| Zerwanie przed wykonaniem end-round | Runda pozostaje aktywna. Po weryfikacji betID można dokończyć rozliczenie; dziennik pokazuje jedną wypłatę. |
| Utrata odpowiedzi end-round po wypłacie | Authenticate potwierdza zamknięcie. Klient nie wypłaca drugi raz i pokazuje aktualne saldo. |
| Błędy 400/401/429/500, opóźnienia i wygasanie sesji | Brak porzucenia niepewnego zakładu, brak samoczynnego nowego play. Komunikat i ponowne połączenie nie kasują aktywnej rundy. |
| Dwie karty i rozliczenie sesyjne | Stary widok nie zamyka nowej, obcej rundy. Potwierdzić serwerowe gwarancje dla wyścigu między authenticate a end-round; sam frontend nie może zapewnić atomowości tych dwóch operacji. |
| Zerowy wynik i utracona odpowiedź | Potwierdzić zachowanie `round: null` / ostatniej zamkniętej rundy. Gdy brak identyfikatora, pozostaje blokada i wyjaśnienie z platformą, zamiast ponownego pobrania stawki. |
| Zmiana poziomów stawki podczas bonusu | Wcześniej opłacony bonus kończy się ze swoją stawką; następna runda korzysta już z dozwolonych poziomów. |
| Minimalna/maksymalna stawka i waluty | Kwoty są w skali 1 000 000, zgodne z portfelem. Sprawdzić minimum, maksimum, krok, formatowanie i brak zaokrągleń wypłat. |
| Hosting, CORS, urządzenia | Test na docelowej domenie, w ramce platformy i na urządzeniu fizycznym; zamknięcie karty, utrata sieci i powrót z tła. Brak tokenów w logach i eksporcie. |

Do każdej próby zapisać: wersję frontendu i matematyki, czas, scenariusz, betID, liczbę faktycznych obciążeń i wypłat, końcowe saldo oraz wynik PASS/FAIL. Nagranie interfejsu nie zastępuje dziennika transakcji.

Źródła kontraktu: [Authenticate](https://github.com/engineio/docs/blob/main/src/routes/docs/api/authenticate/%2Bpage.svx), [Event](https://github.com/engineio/docs/blob/main/src/routes/docs/api/event/%2Bpage.svx), [End round](https://github.com/engineio/docs/blob/main/src/routes/docs/api/end-round/%2Bpage.svx). Odbiór wymaga aktualnych ustawień i dostępu operatora.
