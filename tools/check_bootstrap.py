#!/usr/bin/env python3
"""Prüft, dass jedes Skript seinen Pfad-Bootstrap ausführen kann.

Der Refactor bbf00d0 hatte den Bootstrap so eingebaut, dass `from paths import ...`
in src/*.py ins Leere zeigte und die gesamte Pipeline sofort abbrach. Diese Prüfung
führt nur den Kopf jeder Datei aus — bis einschließlich der paths-Zeile — und stellt
damit sicher, dass der Fehler nicht zurückkehrt, ohne die Pipeline zu starten.

Der Kopf wird dafür als temporäre Datei im Originalverzeichnis abgelegt, damit
`__file__` dieselbe Verzeichnistiefe hat wie im Ernstfall.
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
MARKER = "from paths import"

fehler = []
geprueft = 0

for pfad in sorted(ROOT.glob("src/**/*.py")):
    if pfad.name == "paths.py":
        continue

    kopf = []
    for zeile in pfad.read_text(encoding="utf-8").splitlines():
        kopf.append(zeile)
        if zeile.startswith(MARKER):
            break
    else:
        continue  # Datei nutzt paths.py nicht

    geprueft += 1
    probe = pfad.parent / f"_bootstrap_probe_{pfad.stem}.py"
    probe.write_text("\n".join(kopf) + "\n", encoding="utf-8")
    try:
        ergebnis = subprocess.run(
            [sys.executable, probe.name],
            cwd=pfad.parent,
            capture_output=True,
            text=True,
        )
    finally:
        probe.unlink(missing_ok=True)

    if ergebnis.returncode != 0:
        meldung = ergebnis.stderr.strip().splitlines()
        fehler.append(f"{pfad.relative_to(ROOT)}: {meldung[-1] if meldung else 'unbekannter Fehler'}")

for eintrag in fehler:
    print(f"FEHLER  {eintrag}")

print(f"{geprueft} Skripte geprüft, {len(fehler)} fehlerhaft")
sys.exit(1 if fehler else 0)
