"""Preserve an unsubmitted reference; never rebuild or modify game sources."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import io
import json
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
APP = ROOT / "test-interface-any-start"
EXPECTED_ZIP = "c52258d775e16188190f6ac457746ea6cbfe55043ea9c6863669b947246eb2eb"
MATH_HASHES = {
    "index.json": "5b2e930c746350b937e30430c61b4dd32c161c6506d2338079fc902fd490a13e",
    "books_base.jsonl.zst": "78507157eb412b0b9d7258b86312292dd87f2cfb7a5d3cb44b14b9c5a233ec57",
    "lookUpTable_base_0.csv": "d15fb64fe8435566598dbdfafe64b6215f376a1ed4d7d93545cc8eb3ac57983b",
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

raw = (APP / "POLSKA_GUROM_RGS_FRONTEND.zip").read_bytes()
assert sha(raw) == EXPECTED_ZIP, "Archive changed: do not silently select another release"
math_data = {name: (APP / "stake_math" / name).read_bytes() for name in MATH_HASHES}
assert all(sha(math_data[name]) == expected for name, expected in MATH_HASHES.items())
with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    assert archive.testzip() is None
    entries = [{"path": name, "bytes": len(archive.read(name)), "sha256": sha(archive.read(name))}
               for name in sorted(archive.namelist())]
    assert len(entries) == 18
    assert b'data-rgs-only="true"' in archive.read("index.html")
    assert json.loads(archive.read("game-config.json"))["math_version"] == "0.5.0-any-start"
    assert not any(e["path"].endswith(".py") for e in entries)

BASELINE = OUT / "unsubmitted_reference"
BASELINE.mkdir(exist_ok=False)
(BASELINE / "POLSKA_GUROM_RGS_FRONTEND.zip").write_bytes(raw)
(BASELINE / "math").mkdir()
for name, data in math_data.items():
    (BASELINE / "math" / name).write_bytes(data)
assert sha((BASELINE / "POLSKA_GUROM_RGS_FRONTEND.zip").read_bytes()) == EXPECTED_ZIP
assert all(sha((BASELINE / "math" / name).read_bytes()) == value for name, value in MATH_HASHES.items())
manifest = {
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "status": "awaiting_acp_access_and_final_release",
    "reference_only": True,
    "submission_ready": False,
    "math_version": "0.5.0-any-start",
    "mode": "base",
    "frontend": {"file": "unsubmitted_reference/POLSKA_GUROM_RGS_FRONTEND.zip",
                 "sha256": EXPECTED_ZIP, "bytes": len(raw), "entries": entries},
    "math": [{"file": "unsubmitted_reference/math/" + name, "sha256": value,
              "bytes": len(math_data[name])} for name, value in MATH_HASHES.items()],
    "integrity_verified": True,
    "acp": {"url": "https://studio.engine.io/signin", "authenticated": False,
            "game_id": None, "frontend_version_id": None, "math_version_id": None,
            "uploaded": False, "validation": "not_run", "review_comments": None,
            "frontend_approval": "not_observed", "math_approval": "not_observed"},
    "final_audit": {"performed": False, "reason": "No accepted final package or ACP evidence"},
    "evidence_limits": [
        "47 cap-message checks explicitly bind the reference app.js hash.",
        "The historical 275-check total contains tests against earlier app.js hashes.",
        "Integrity verification here is not a new gameplay, browser, SDK or platform test.",
        "Concurrent audio and publication work is absent from this reference ZIP.",
        "Decision to rebuild high-win mathematics is recorded but not implemented in this export."
    ],
    "dependencies": [
        {"thread_id": "01a1628c-a5e1-76c3-b7fc-c9933dcf4772", "title": "Dodaj dźwięki i wyciszenie", "observed_status": "active"},
        {"thread_id": "01a1628d-1c93-7db2-b7a5-f8cde0c397b4", "title": "Przygotuj materiały do publikacji", "observed_status": "active"},
        {"thread_id": "01a1628c-e9ce-7ed0-9afa-65f9a6c4e721", "title": "Przetestować telefony i przeglądarki", "observed_status": "active"}
    ],
    "evidence": ["audit/cap_messages_2026_10_22/delivery_verification.json",
                 "audit/cap_messages_2026_10_22/cap_messages_results.json",
                 "audit/recovery_2026_10_22/FINAL_STATUS.json",
                 "decisions/high_wins_2026_10_22/DECYZJA_PL.md"]
}
(OUT / "STATUS.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
report = """# Zgłoszenie ACP — stan 22.10.2026

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
"""
(OUT / "STATUS_PL.md").write_text(report, encoding="utf-8")
print(json.dumps({"reference_sha256": EXPECTED_ZIP, "integrity_verified": True,
                  "frontend_files": len(entries), "math_files": len(math_data),
                  "uploaded": False, "final_audit_performed": False}, ensure_ascii=False))
