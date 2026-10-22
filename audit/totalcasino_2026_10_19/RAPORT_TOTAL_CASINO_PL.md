# POLSKA GUROM — warunki wejścia do Total Casino

Data sprawdzenia: **19 października 2026 r.** Zakres: dostarczenie własnego slota przez studio gier do Totalizatora Sportowego. Sprawdzono oficjalne źródła internetowe i odniesiono ustalenia do istniejącej dokumentacji naszego prototypu. Nie przeprowadzono nowego audytu matematyki ani testu integracji z operatorem.

## Wniosek

**Można zgłosić własną grę do Totalizatora Sportowego.** Operator zaprasza producentów gier kasynowych przez oficjalny formularz. Samo zgłoszenie nie oznacza przyjęcia gry. Nie znalazłem w sprawdzonych materiałach pełnej publicznej specyfikacji dostawy pojedynczego slota ani tabeli wynagrodzenia dla studia. Przed przebudową projektu trzeba uzyskać potwierdzenie zainteresowania, ścieżkę integracji oraz warunki ekonomiczne. [Formularz współpracy](https://www.totalizator.pl/wspolpraca/wspolpraca-z-dostawcami).

Obecny POLSKA GUROM v0.2 stanowi materiał do przedstawienia koncepcji i demonstracji matematyki. Nie ma podstaw, aby uznać go za gotowy do uruchomienia na prawdziwe pieniądze w Total Casino.

## Zgłoszenie dostawcy

Aktualna strona [Local Content](https://www.totalizator.pl/wspolpraca/local-content) zawiera formularz dla producentów gier. Wybiera się obszar gier online i podaje opis produktu, przewagi, wymagania techniczne, przewidywany czas oraz koszt wdrożenia, korzyści i klientów. Potrzebne są dane firmy i kontaktu oraz NIP albo VAT. Formularz dopuszcza wskazanie rejestracji firmy poza Polską; nie jest to samo w sobie gwarancja kwalifikacji.

Można dołączyć maksymalnie 10 plików PDF/JPG/JPEG/PNG, do 15 MB każdy. ZIP z kodem nie mieści się w wymienionych formatach. Do pierwszego zgłoszenia proponuję PDF z opisem gry, zrzutami ekranu i podstawowymi parametrami; dostęp do dema i kodu należy ustalić z odbiorcą. To propozycja przygotowania oferty, nie dodatkowy wymóg operatora.

Oficjalny kontakt dla zainteresowanych dostawców: **biuro.zakupow@totalizator.pl**, podany na [stronie postępowań](https://www.totalizator.pl/wspolpraca/postepowania-ofertowe). [Profil zakupowy TS](https://platformazakupowa.pl/pn/totalizator) pozwala zapisać się do grup wykonawców. Nie ustalono otwartego postępowania dotyczącego zakupu naszego pojedynczego slota.

## Technologia i badania

Playtech ogłosił 30 stycznia 2024 r. przedłużenie współpracy z Totalizatorem Sportowym obejmującej platformę kasyna i treści. Jest to potwierdzenie relacji technologicznej; nie określa publicznie interfejsu, którego mamy użyć. [Komunikat Playtech](https://www.playtech.com/playtech-wins-extension-to-multi-year-partnership-with-totalizator-sportowy/).

Playtech opisuje dostęp do gier innych producentów przez POP, a także możliwość tworzenia treści w jego ekosystemie. To wskazuje potencjalne ścieżki techniczne, lecz nie potwierdza, że nasza gra zostanie dopuszczona do Total Casino przez określony agregator lub narzędzie. Najpierw należy uzyskać wskazanie właściwego partnera i aktualną specyfikację. [Oficjalny opis POP](https://www.playtech.com/playtechs-player-account-management-pam-platform-is-selected-to-power-ocean-casino-resorts-online-casino-relaunch/).

**Nie ustalono publicznie:** wymaganego formatu paczki, API portfela, zasad hostowania, dopuszczalnych technologii serwera, listy akceptowanych raportów laboratoryjnych, konkretnego standardu badań, zasad zmian wersji i kosztu certyfikacji. Nie należy zamawiać badania na podstawie samej popularności nazwy GLI, iTech lub eCOGRA. Potrzebne jest potwierdzenie zakresu i akceptacji raportu dla wybranej architektury.

## Ramy prawne istotne dla integracji

Podstawa: [ustawa o grach hazardowych, tekst ujednolicony Kancelarii Sejmu z 8.10.2026](https://eli.gov.pl/api/acts/DU/2009/1540/text/U/D20091540Lj.pdf), uwzględniający zmiany z 2026 r.

- Art. 5 ust. 1b ustanawia monopol na kasyno online. W tym projekcie studio oferuje treść operatorowi. MF wskazuje TS jako operatora Total Casino w [wykazie legalnego hazardu](https://www.gov.pl/web/finanse/legalny-hazard).
- Art. 15d nakłada na organizatora obowiązki archiwizacji przebiegu, wyników i transakcji oraz dostępu KAS; retencja wynosi pięć lat od końca roku archiwizacji. Integracja musi dostarczać operatorowi odpowiednie dane.
- Art. 15i wymaga odpowiedzialnej gry, m.in. weryfikacji wieku, konta i kontroli aktywności. Dostawca musi współpracować z mechanizmami operatora.
- Opinia o oprogramowaniu w art. 2 ust. 7 dotyczy procedury klasyfikacji gry. Nie dowodzi samodzielnie obowiązku identycznego certyfikatu dla każdego tytułu.
- Art. 18 ust. 3 zawiera próg 75% dla automatów, ale nie ustalono jednoznacznego oficjalnego objaśnienia jego stosowania do naszego wdrożenia online. Wymagania RTP trzeba potwierdzić z TS i jednostką badającą. Nie potwierdzono wymogu dokładnie 96%.

## Co oznacza to dla POLSKA GUROM v0.2

Poniższe fakty pochodzą z bieżących plików oraz istniejącego audytu z 19.10.2026. Nie oznaczają nowego przeliczenia ani certyfikacji.

| Obszar | Stan projektu i znaczenie |
|---|---|
| Matematyka | Mamy specyfikację, PAR sheet i wcześniejsze wyniki weryfikacji z nominalnym RTP 96%. To podstawa oceny produktu; akceptacja parametrów przez TS pozostaje nieustalona. |
| Losowanie | Tester używa `random.Random`. Produkcyjna ścieżka losowania wymaga rozwiązania uzgodnionego z operatorem i uwzględnionego w badaniach. |
| Saldo i sesje | Wirtualne saldo i sesje działają w pamięci serwera. Nie jest to integracja portfela operatora. |
| Wznawianie rund | Brakuje trwałej obsługi przerwanych rund. Cache ponowień obejmuje 100 żądań, a stan prezentacji znika po odświeżeniu strony. |
| Prezentacja | Istniejący audyt wykazał m.in. znikanie komunikatu limitu, podmianę licznika przy zmianie języka i brak RTP w zasadach dostępnych graczowi. |
| Materiały | Zestaw symboli wymaga ujednolicenia z dokumentacją; finalne grafiki, dźwięki i fonty oraz prawa do ich użycia wymagają udokumentowania. |
| Maksymalna wygrana | 5000× jest osiągalne kombinatorycznie, ale według wcześniejszego audytu skrajnie rzadkie. To kwestia modelu do przedstawienia operatorowi; nie ustalono progu częstości wymaganego przez TS. |

Lokalne źródła: [README v0.2](../../polska_gurom_v0_2/README.md), [serwer testera](../../test-interface/server.py), [frontend](../../test-interface/web/app.js), [wcześniejszy raport](../stake_engine_2026_10_19/RAPORT_STAKE_ENGINE_PL.md).

Nie ustalono, aby Total Casino wymagało Stake'owego kroku wypłat 0,10×, częstości max win 1:10 mln lub 1:20 mln, paczek `books/index/CSV`, endpointów Stake ani trybu social. Wymagań konkretnej platformy nie można przenosić bez jej specyfikacji. Ogólne braki produkcyjne w rozliczaniu, odzyskiwaniu rund i prezentacji pozostają do usunięcia niezależnie od wyboru platformy.

## Warunki handlowe do ustalenia

W przejrzanych oficjalnych materiałach nie ustalono wartości poniższych warunków. Powinny znaleźć się w odpowiedzi TS lub projekcie umowy:

| Warunek | Co trzeba uzyskać |
|---|---|
| Wynagrodzenie | Procent lub opłata stała; dokładna definicja podstawy GGR/NGR i traktowania ujemnych okresów. |
| Potrącenia | Podatki, bonusy, jackpoty, zwroty, koszty agregatora i ewentualne pozostałe opłaty. |
| Koszty wejścia | Integracja, badania, ponowne badania zmian, hosting i utrzymanie; kto je ponosi. |
| Zobowiązania | Ewentualna minimalna liczba gier, harmonogram dostaw, minimum gwarantowane i opłaty miesięczne. |
| Prawa | Licencja do gry, własność kodu i matematyki, wyłączność, terytorium i możliwość innych wdrożeń. |
| Eksploatacja | Wymagana dostępność, czas reakcji na awarię, dyżury, odpowiedzialność i zasady wycofania gry. |
| Rozliczenie | Raportowanie, audyt naliczeń, waluta i termin płatności. |

## Pytania do operatora przed adaptacją

1. Czy przyjmują Państwo zgłoszenie nowego studia z jednym autorskim slotem i działającym prototypem?
2. Czy oczekiwana jest dostawa kompletnej gry z serwerem, integracja z wybranym RGS/agregatorem czy wdrożenie w narzędziach partnera?
3. Jakie badania gry, matematyki i generatora są akceptowane oraz kto je zamawia i opłaca?
4. Jakie obowiązują RTP, maksymalne wygrane, poziomy stawek, precyzja i zasady zaokrąglania wypłat?
5. Jakie są wymagania sesji, portfela, ponowień, odzyskiwania rund, historii i archiwizacji?
6. Jaki obowiązuje standard interfejsu, języków, urządzeń mobilnych i mechanizmów odpowiedzialnej gry?
7. Jak wyglądają wynagrodzenie, potrącenia, koszty integracji, prawa do produktu i wymagana obsługa?
8. Jak przebiega ocena: materiały początkowe, dostęp do specyfikacji, ewentualne NDA, testy i ostateczna akceptacja?

**Zalecany następny krok:** przedstawić TS opis POLSKA GUROM, demo i dokumentację matematyczną z uczciwym oznaczeniem etapu prototypu, a następnie uzyskać odpowiedzi na powyższe pytania. Pozwoli to wybrać architekturę i ocenić opłacalność przed poniesieniem kosztów integracji i badań.

W ramach tego sprawdzenia nie wysyłano formularzy, wiadomości ani plików do operatora. Nie zmieniano implementacji, istniejących paczek ani materiałów `sources/`.
