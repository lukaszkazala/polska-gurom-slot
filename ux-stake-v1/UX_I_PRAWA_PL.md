# Polska Gurom — UX v1 i rejestr praw

Stan: 20 października 2026. Kierunek wskazany przez użytkownika: inne kraje / Stake. To wstępny przegląd projektu i koncepcja UX, a nie zatwierdzenie gry do publikacji ani pełna opinia prawna. Brakuje listy docelowych państw i pełnej umowy z platformą.

## Projekt ekranu

Makieta `makieta-ux-v1.svg` pokazuje komputer i telefon. Wariant mobilny zakłada obszar gry 390 × 780 px; trzeba go jeszcze sprawdzić w rzeczywistym osadzeniu platformy i przy mniejszej wysokości. Układ 5 × 3, 20 linii i dotychczasowa matematyka pozostają punktem odniesienia. Kwoty w USD są ilustracją, a nie docelową walutą. RTP 96% i limit 5000× pochodzą z obecnego projektu; nie wykonano tutaj nowego audytu matematyki.

Kierunek: ciemny granat, ciepłe złoto jako akcent, spokojne tło i czytelne geometryczne symbole. Na telefonie usuwamy duży nagłówek wprowadzający i kafle statystyk znad planszy. Pierwszy widok mieści planszę, saldo, wypłatę, stawkę i przycisk obrotu. Narzędzia testera i eksport nie należą do ekranu gracza. Zasady i tabela są dostępne z jednego przycisku. Opcje otwierają osobny panel; ustawienia automatycznych obrotów wymagają wyraźnego uruchomienia.

Makieta jest statyczna i pokazuje stan gotowości. Symbole są roboczymi kształtami przygotowanymi w kodzie tej makiety. Nie są finalnym zestawem dziesięciu symboli. Ikony dźwięku i informacji wymagają nazw dostępności w implementacji. Docelowo: dotykowe cele co najmniej 44 × 44 px, obsługa klawiatury, widoczny fokus, ograniczenie ruchu zgodnie z preferencją użytkownika, brak informacji przekazywanej wyłącznie kolorem. Są to założenia projektowe, nie deklaracja ukończonego audytu dostępności.

## Wymagania Stake uwzględniane przy wdrożeniu

Platforma wymaga oryginalnej gry i materiałów zgodnych z prawem własności intelektualnej; zabrania brandingu Stake w zasobach gry i treści atrakcyjnych dla nieletnich. Nazwa naszej gry pozostaje robocza. [Ogólne wytyczne](https://stake-engine.com/docs/approval-guidelines).

Do zaprojektowania i sprawdzenia w działającej grze: telefon i mini-player bez deformacji, zasady, pełna tabela wypłat, RTP i limit wygranej, wszystkie stawki zwrócone przez RGS, saldo, końcowa wypłata i jej narastanie w rundzie, wyciszenie, spacja oraz potwierdzenie autoplay. Grafiki i fonty mają być dostarczane przez CDN platformy; szybka prezentacja musi zachować czytelność. [Wymagania frontendu](https://stake-engine.com/docs/approval-guidelines/front-end-communication).

Nowe gry wymagają odtwarzania rund. Projektujemy oddzielny ekran „Odtwórz” / „Odtwórz ponownie”, bez możliwości postawienia zakładu lub przejścia do normalnej gry. [Bet Replay](https://stake-engine.com/docs/approval-guidelines/game-replay-requirements).

Waluta, dostępne stawki i ograniczenia rynku muszą pochodzić z konfiguracji sesji. Dokumentacja uwierzytelniania pokazuje m.in. `jurisdiction.socialCasino` i `disabledTurbo`; pełen aktualny zestaw flag trzeba potwierdzić podczas integracji. Obecny tester formatuje kwoty jako PLN, więc nie jest jeszcze gotową warstwą portfela Stake. [Wallet](https://stake-engine.com/docs/rgs/wallet).

Zasady wymagają również objaśnienia działania serwera wyników i zachowania po rozłączeniu. Tekst zostanie dopasowany do faktycznej integracji; nie wolno obiecywać odzyskania rundy przed jego wdrożeniem. [Objaśnienie działania gry](https://stake-engine.com/docs/approval-guidelines/general-disclaimer).

## Stany do kolejnej wersji UX

| Stan | Zachowanie i treść |
|---|---|
| Ładowanie | Postęp zasobów, obrót niedostępny do zakończenia autoryzacji i wczytania. |
| Runda i kaskady | Zablokowana zmiana stawki; aktualizacja wypłaty zgodnie z danymi wyniku. |
| Częściowy zwrot | Np. stawka 1,00 USD, wypłata 0,40 USD, wynik −0,60 USD; neutralna prezentacja. |
| Bonus | Licznik wykonanych i pozostałych obrotów, mnożnik oraz łączna wypłata; bez sugerowania nowej stawki. |
| Limit rundy | Zaksięgowana wypłata i trwałe objaśnienie zastosowanego limitu. |
| Autoplay | Liczba rund, potwierdzenie startu, dostępny STOP; funkcja zależna od konfiguracji rynku. |
| Utrata połączenia | Wstrzymanie nowych zakładów, odczyt stanu i wznowienie istniejącej rundy zgodnie z RGS. |
| Błąd sesji / lokalizacji / limitu | Konkretne wyjaśnienie, bez automatycznego ponawiania zakładu. |
| Replay | Odtwarzanie wskazanego wyniku, koszt rundy i wypłata; brak aktywnego salda i zakładów. |
| Social | Osobny zestaw tekstów i formatów waluty; pełna weryfikacja terminologii w trybie platformy. |

## Rejestr materiałów i praw

„Do weryfikacji” oznacza brak wystarczającego dowodu w sprawdzonych plikach, a nie ustalenie naruszenia. Zakres przeglądu: aktywny folder `test-interface/web`, dokumentacja muzyki i początek źródła jej syntezy, wcześniejsze raporty projektu oraz wskazane źródła publiczne. Nie przeprowadzono porównania wszystkich grafik z bazami podobnych utworów ani pełnego audytu zależności.

| Materiał | Co ustalono | Status / dalsze działanie |
|---|---|---|
| Nazwa „Polska Gurom” | Istnieje w grze i dokumentacji. Nie wykonano przeszukania rejestrów znaków. | DO WERYFIKACJI: nazwy identyczne i podobne, właściciele, terytoria oraz właściwe towary/usługi; osobno domeny i użycie rynkowe. |
| Symbole w grze | Dziesięć kształtów SVG zapisanych w `app.js`; wszystkie pola `image` w `assets/symbols.json` są puste. | ROBOCZE: pochodzenie i prawa trzeba udokumentować. Zapis w kodzie nie dowodzi autorstwa ani braku podobieństwa. |
| Husarz, korona, lilia, kolory kart | Są tematami aktualnych symboli. | KIERUNEK: opracować własne rysunki; nie kopiować konkretnego herbu, logo, ilustracji, zdjęcia ani modelu. Motyw historyczny nie rozstrzyga praw do jego współczesnego przedstawienia. |
| Muzyka | README i źródło deklarują syntezę bez zewnętrznych sampli; istnieją WAV, MIDI i skrypt. | DO UDOKUMENTOWANIA: pochodzenie kompozycji, udział człowieka / narzędzi i uprawnienia firmy. Nie wykonano badania podobieństwa melodii. |
| Fonty | CSS wskazuje Inter, Segoe UI, Arial i sans-serif; nie znaleziono plików fontów w aktywnym `web/assets`. | PRZED WDROŻENIEM: wybrać i przypiąć konkretny font z licencją dopuszczającą dystrybucję webową, zachować jej tekst oraz wdrożyć zgodnie z CDN platformy. Lista fontów systemowych nie jest licencją na pakowanie ich plików. |
| Nowa makieta | Kształty SVG i układ utworzono w tej sesji; brak zewnętrznych bitmap i logo platformy. | ROBOCZA: nie daje potwierdzenia dostępności nazwy, wyłączności ani praw do finalnych materiałów. |
| Grafiki wgrywane przez tester | Użytkownik może lokalnie wybrać pliki symboli. | NIEZWERYFIKOWANE: każda finalna grafika trafia do rejestru przed włączeniem do paczki. |
| Biblioteki i SDK | Poza zakresem tego przeglądu materiałów wizualnych. | DO AUDYTU: zależności, licencje, wymagane noty; oddzielnie przykładowe zasoby SDK. |

Dla każdego finalnego pliku zapisujemy: nazwę i SHA-256, autora/dostawcę, adres źródła lub plik źródłowy, datę pozyskania, licencję i jej wersję, dowód zakupu/umowę, obowiązek podpisu, zakres komercyjnego użycia, modyfikacji i dystrybucji oraz zgodność z prawami wymaganymi w umowie platformy. Przy AI zapisujemy także narzędzie, wersję warunków, datę, prompt i wszystkie referencje; wygenerowanie materiału nie jest dowodem jego prawnej dostępności.

Licencja albo przeniesienie praw powinny odpowiadać rzeczywistym sposobom wykorzystania dzieła. Nie każda „darmowa grafika” lub licencja do własnego użytku dopuszcza grę komercyjną i udostępnienie jej platformie. [MKiDN: licencje i przeniesienie praw](https://www.gov.pl/web/kultura/informacja-dotyczaca-umow-licencyjnych-niewylacznych-jako-mozliwej-formy-nabywania-praw-do-utworow-artystycznych).

Do wyszukiwania znaków wykorzystujemy m.in. TMview / EUIPO; sama dostępność domeny i brak wyniku w wyszukiwarce internetowej nie stanowią sprawdzenia znaku. Na tym etapie rejestry nie zostały przeszukane. [EUIPO: wyszukiwanie dostępności](https://www.euipo.europa.eu/en/help-centre/tm/faq-search-availability).

## Zakres krajowy

Wybór Stake nie zastępuje listy państw i wymagań operatora. Jako przykład odmiennych ograniczeń: brytyjski UKGC wymaga dla slotów co najmniej 2,5 s pomiędzy rozpoczęciami cykli, zabrania funkcji skracających czas do prezentacji wyniku i celebracji wypłat nieprzekraczających stawki. To przykład dla działalności podlegającej temu regulatorowi, a nie twierdzenie o obsłudze Wielkiej Brytanii przez tę platformę. [UKGC RTS 14](https://www.gamblingcommission.gov.uk/standards/remote-gambling-and-software-technical-standards/rts-14-responsible-product-design).

W tej wersji przygotowano makietę i założono rejestr. Nie zmieniono działającego testera, nie opublikowano gry i nie przyznano żadnemu materiałowi statusu „prawa sprawdzone”. Kolejny etap to pełne ekrany stanów, finalny styl symboli i integracja UX z rzeczywistym RGS oraz jego konfiguracją jurysdykcji.
