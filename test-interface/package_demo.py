"""Build the portable tester ZIP without modifying the reference engine."""

from __future__ import annotations

from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "POLSKA_GUROM_TESTER.zip"


def included_files(folder: Path):
    for path in sorted(folder.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}:
            yield path


def build() -> Path:
    engine = ROOT / "engine" / "polska_gurom"
    if not (engine / "game.py").is_file():
        engine = ROOT.parent / "polska_gurom_v0_2" / "polska_gurom"
    if not (engine / "game.py").is_file():
        raise FileNotFoundError("Brakuje kompletnego silnika polska_gurom.")

    required = [ROOT / name for name in ("server.py", "START.cmd", "README_PL.md")]
    required += [ROOT / "web" / "index.html", ROOT / "web" / "assets" / "symbols.json"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Brakuje plików testera: " + ", ".join(missing))

    temporary = OUTPUT.with_suffix(".zip.tmp")
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in required[:3]:
                archive.write(path, path.name)
            for path in included_files(ROOT / "web"):
                archive.write(path, "web/" + path.relative_to(ROOT / "web").as_posix())
            for path in included_files(engine):
                archive.write(path, "engine/polska_gurom/" + path.relative_to(engine).as_posix())
            for path in included_files(ROOT / "stake_math"):
                archive.write(path, "stake_math/" + path.relative_to(ROOT / "stake_math").as_posix())
        with zipfile.ZipFile(temporary) as archive:
            bad_file = archive.testzip()
            if bad_file is not None:
                raise RuntimeError("Uszkodzony plik w archiwum: " + bad_file)
            print(f"Sprawdzono {len(archive.infolist())} plików.")
        temporary.replace(OUTPUT)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    print(f"Gotowa paczka: {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    build()
