"""Package completed network failure evidence and the tested application."""
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
QA = ROOT / "test-interface/qa"
OUT = ROOT / "audit/network_resilience_2026_10_19"


def read(path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def link(label,path): return f"[{label}](<{path.resolve().as_posix()}>)"


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    http = read(QA / "network_faults_results.json")
    logic = read(QA / "network_logic_results.json")
    auto = read(QA / "autoplay_logic_results.json")
    portable = read(QA / "portable_check.json")
    browser = read(QA / "network_browser_results.json")
    math = read(ROOT / "test-interface/stake_math/mathematics.json")
    assert http["tests_run"] == http["passed"] == 17 and not http["failed"] and not http["errors"]
    assert logic["passed"] and logic["checks_passed"] == logic["checks_total"] == 30
    assert auto["passed"] and len(auto["checks"]) == 13 and portable["success"]
    app_hash = sha(ROOT / "test-interface/web/app.js")
    assert logic["source_sha256"] == auto["source_sha256"] == app_hash
    assert all(sha(ROOT/"test-interface/engine/polska_gurom"/name)==value
               for name,value in math["source_fingerprint"].items())
    assert browser["offline_before_recovery"]["rounds"] == "0"
    assert "100 / 100" in browser["after_recovery_and_100_autospins"]["progress"]
    assert browser["after_recovery_and_100_autospins"]["rounds"] == "103"
    events = [json.loads(line) for line in (QA / "browser_fault_events.jsonl").read_text().splitlines()]
    groups = defaultdict(list)
    for event in events: groups[event["request"]["request_id"]].append(event)
    accepted = {}
    for request_id, attempts in groups.items():
        results = [x for x in attempts if x["forwarded"]]
        assert results and len({x["round_id"] for x in results}) == 1
        assert len({json.dumps({key:x[key] for key in ("round_id","book_id","balance_cents","stats")},sort_keys=True) for x in results}) == 1
        accepted[request_id] = results[0]
    assert len(accepted) == 103
    assert max(x["stats"]["rounds"] for x in accepted.values()) == 103
    assert max(x["stats"]["total_bet_cents"] for x in accepted.values()) == 103*200
    assert sum(x["fault"] == "offline_before" for x in events) == 3
    assert sum(x["fault"] == "drop_after" for x in events) == 2
    assert sum(x["fault"] == "delay_after" for x in events) == 1
    archive = ROOT / "test-interface/POLSKA_GUROM_v0_4_NETWORK_FIX.zip"
    shutil.copyfile(ROOT / "test-interface/POLSKA_GUROM_TESTER.zip",archive)
    assert sha(archive) == portable["zip_sha256"]
    result = {"status":"PASS","created_utc":datetime.now(timezone.utc).isoformat(),
        "new_fault_checks":47,"http_tcp_checks":17,"frontend_fault_checks":30,
        "previous_autoplay_checks":13,"http_regression_tests":10,"portable_checks":len(portable["checks"]),
        "browser":browser,"browser_actual_requests":len(events),"browser_distinct_paid_rounds":len(accepted),
        "browser_accounting_matches_unique_request_ids":True,
        "source_sha256":{"app.js":app_hash,"server.py":sha(ROOT/"test-interface/server.py")},
        "math_source_fingerprint_verified":math["source_fingerprint"],"exact_rtp":"24/25",
        "archive":{"path":str(archive),"sha256":sha(archive),"bytes":archive.stat().st_size},
        "scope":"Isolated loopback transport faults and frontend logic. Computer Wi-Fi/WAN and live Stake RGS were not changed or tested.",
        "remaining_limits":["Local virtual wallet/history are memory-only and are lost on process restart.",
                            "Only last100 full round responses are replayable; older processed IDs are rejected without a debit.",
                            "Pending survives same-tab reload only when sessionStorage is available; browser storage clearing is not durable recovery."]}
    (OUT/"results.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    report = f"""# Testy utraty połączenia — POLSKA GUROM

Wynik: **47/47 nowych testów awarii PASS** — 17 przez rzeczywiste połączenia HTTP/TCP oraz 30 testów logiki interfejsu. Ponownie przeszło 13 testów autospinu, 10 testów HTTP i salda oraz 27 kontroli wypakowanej paczki.

## Sprawdzone sytuacje

| Sytuacja | Wynik po poprawkach |
|---|---|
| Brak połączenia przed dotarciem żądania | Brak pobrania stawki; ponowienie używa tego samego identyfikatora. |
| Serwer rozliczył rundę, ale odpowiedź zginęła lub została ucięta | Odzyskano ten sam wynik; stawka i wygrana są księgowane jeden raz. |
| Odpowiedź trwa ponad 15 sekund, również jej treść | Żądanie przestaje blokować interfejs; pozostaje możliwość odczytu tej samej rundy. |
| Błędy 408, 429, 500, 502, 503 | Autospin ponawia tę samą rundę maksymalnie trzy razy. |
| Dłuższa awaria | Seria zatrzymuje się z powodem i przyciskiem „PONÓW ODCZYT”. |
| Błędny JSON, zły kształt odpowiedzi, niezgodny identyfikator rundy/sesji/matematyki | Odpowiedź nie usuwa oczekującego żądania i nie zatwierdza błędnego wyniku. |
| Odświeżenie karty z nierozstrzygniętym obrotem | Żądanie jest odzyskiwane z pamięci sesji karty; nie uruchamia automatycznie nowej serii. |
| Restart, wygaśnięcie sesji lub brak ciasteczka | Stary obrót jest odrzucany przed rozliczeniem; potrzebne odczytanie nowej sesji. |
| Reset sesji w drugiej karcie | Stary identyfikator sesji jest odrzucany; brak naliczenia nowej stawki. |
| Osiem równoległych ponowień, podwójne kliknięcie | Jedna zaakceptowana runda i jedno rozliczenie. |
| Ponowienie po wypadnięciu wyniku z historii 100 rund | Identyfikator pozostaje oznaczony jako rozliczony; brak drugiego pobrania stawki. |
| Utrata połączenia po otrzymaniu całego bonusu | Prezentacja przyznanych darmowych obrotów kończy się; kolejna płatna runda podlega kontroli połączenia. |

## Testy w rzeczywistej przeglądarce

W osobnym środowisku lokalnym przekaźnik fizycznie zrywał połączenia HTTP lub opóźniał odpowiedź. Nie zmieniano ustawień internetu komputera. Samo wyłączenie Wi-Fi nie odcina tej gry od lokalnego adresu 127.0.0.1; badano połączenie gry z jej serwerem.

1. Trzy przerwane próby przed dotarciem do serwera: licznik **0/10**, saldo **10 000 zł**, widoczny komunikat „Brak połączenia” i „PONÓW ODCZYT”. Po przywróceniu połączenia rozliczono tylko jedną rundę; seria pozostała zatrzymana.
2. Zerwana odpowiedź po rozliczeniu: ręczny odczyt zwrócił dokładnie ten sam wynik, bez kolejnej stawki.
3. Odpowiedź opóźniona o 18 sekund: zadziałał limit 15 sekund; ręczny odczyt zwrócił wcześniej rozliczoną rundę.
4. Seria **100/100** ze zgubieniem odpowiedzi po rozliczeniu pierwszej rundy: seria zakończyła się w całości. W całym laboratorium było **103 różnych płatnych rund**, a suma stawek wyniosła dokładnie **103 × 2 zł**. Każde ponowienie miało ten sam wynik, identyfikator i saldo co pierwsza odpowiedź serwera.

Odświeżenie z oczekującym żądaniem, błędny JSON, błędy 408/429/5xx i awaria podczas bonusu zostały dodatkowo sprawdzone deterministycznie w rzeczywistej logice app.js. Testy tej warstwy używają kontrolowanego transportu i przyspieszonego zegara; nie są przedstawiane jako fizyczne odłączenie internetu.

## Usunięte problemy

- Żądanie obrotu jest związane z konkretną sesją. Restart lub reset nie zamienia starego żądania w nową płatną rundę.
- Historia 100 wyników i ślady rozliczonych identyfikatorów są przechowywane osobno. Wyparcie szczegółów nie pozwala ponownie pobrać stawki.
- Oczekujący obrót jest zapisywany w pamięci sesji karty. Wynik po odzyskaniu nie jest dublowany w historii.
- Odpowiedź jest sprawdzana przed usunięciem oczekującego żądania. Dodano poprawną obsługę 408/429 i limit czasu również dla pliku symboli.

RTP wynosi nadal dokładnie **96%**. Sumy SHA-256 silnika oraz opublikowanego rozkładu matematyki zgadzają się z wcześniejszym audytem; ta zmiana dotyczy obsługi połączenia i rozliczania żądań.

## Ograniczenia lokalnego testera

Restart procesu usuwa wirtualny portfel i historię z pamięci. Zabezpieczenie blokuje ponowne rozliczenie starego żądania; nie odtwarza utraconego portfela. Po 100 zapisanych wynikach starszy pełny wynik nie jest odtwarzany, choć stary identyfikator nadal nie może pobrać stawki. Odzyskiwanie po odświeżeniu wymaga dostępnej pamięci sessionStorage tej samej karty. Nie testowano rzeczywistego portfela ani prywatnego RGS Stake.

## Dowody i paczka

- {link('Nowa paczka gry ZIP',archive)}
- {link('17 testów HTTP/TCP',QA/'network_faults_results.json')}
- {link('30 testów logiki awarii',QA/'network_logic_results.json')}
- {link('13 wcześniejszych testów autospinu',QA/'autoplay_logic_results.json')}
- {link('Odczyty z przeglądarki',QA/'network_browser_results.json')}
- {link('Dziennik rzeczywistych prób i rozliczeń laboratorium',QA/'browser_fault_events.jsonl')}
- {link('Kontrole paczki',QA/'portable_check.json')}
- {link('Zbiorczy wynik i sumy kontrolne',OUT/'results.json')}

Testy można odtworzyć poleceniami: `python test-interface/qa/test_network_faults.py`, `node test-interface/qa/test_network_logic.cjs` oraz `node test-interface/qa/test_autoplay.cjs`. Są izolowane od otwartej sesji gry i nie wyłączają internetu komputera.
"""
    (OUT/"RAPORT_PL.md").write_text(report,encoding="utf-8")
    print(json.dumps({"status":"PASS","report":str(OUT/'RAPORT_PL.md'),"new_fault_checks":47,"browser_unique_paid_rounds":len(accepted),"archive":str(archive)},ensure_ascii=False))


if __name__ == '__main__': main()
