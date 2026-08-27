# Mitwirken

Dies ist eine abgeschlossene Untersuchung, kein Produkt in Entwicklung. Am wertvollsten
sind deshalb **Korrekturen an den Ergebnissen** — jeder Befund hier ist nachrechenbar, und
drei der vier Fassungen mussten Aussagen der vorherigen widerrufen (siehe
[`docs/CHANGELOG.md`](docs/CHANGELOG.md)). Die vierte wird nicht die letzte sein.

## Was besonders willkommen ist

* **Widerlegungen.** Wer eine Zahl nachrechnet und etwas anderes herausbekommt, sollte ein
  Issue öffnen — mit Skript, Datenstand und Ergebnis.
* **Fahrplanfachliche Einwände.** Die Kapazitätsaussagen sind Grobabschätzungen ohne
  Betriebssimulation; die [Grenzen](docs/06-grenzen.md) sind bewusst offen benannt.
* **Fehler in Bahnhofsnamen, Linienzuordnung, Sprinterklassifikation.** Der offene
  Datensatz enthält keine Zugnummern, die Zuordnung ist rekonstruiert.
* **Reproduzierbarkeit.** Wenn `make all` bei dir nicht durchläuft, ist das ein Fehler
  dieses Repositories, kein Anwendungsfehler.

## Entwicklungsumgebung

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Für den Dokumentgenerator zusätzlich Node 18 oder neuer:

```bash
cd src/web && npm install
```

## Vor dem Pull Request

Die drei Prüfungen, die auch im CI laufen:

```bash
python -m compileall -q src && python tools/check_bootstrap.py && python tools/check_links.py
```

Zusätzlich, wenn `ruff` installiert ist:

```bash
ruff check src
```

Die Lint-Regeln sind absichtlich schmal ([`ruff.toml`](ruff.toml)): geprüft wird, was
bricht — Syntaxfehler, undefinierte Namen, kaputte f-Strings. Der Stil der Analyseskripte
ist dicht und soll dicht bleiben; Formatierungs-Pull-Requests werden nicht angenommen.

## Konventionen

* **Sprache.** Code, Kommentare, Commit-Nachrichten und Dokumentation sind deutsch.
  Bezeichner folgen der Fachsprache des Fahrplans (`knotenminute`, `sollband`, `zuschlag`).
* **Zustand.** Es gibt genau einen: `data/bahn.db`. Jedes Skript liest und schreibt dort.
  Pfade kommen ausschließlich aus [`src/lib/paths.py`](src/lib/paths.py) — keine harten
  und keine arbeitsverzeichnisrelativen Pfade.
* **Reihenfolge.** Die Nummerierung in `src/` ist die Ausführungsreihenfolge. Ein neues
  Skript bekommt die nächste Nummer und einen Eintrag im [`Makefile`](Makefile) und in
  [`src/README.md`](src/README.md).
* **Verworfenes.** Was durch eine bessere Fassung ersetzt wird, wandert nach `src/legacy/`
  und wird in [`docs/CHANGELOG.md`](docs/CHANGELOG.md) protokolliert — mit der Angabe, was
  daran falsch war. Gelöscht wird nichts.

## Was nicht hineingehört

* **Fahrplanrohdaten.** Der GTFS-Feed unterliegt den Bedingungen von DELFI e. V. und
  gtfs.de. Im Repository liegen nur abgeleitete, aggregierte Ergebnisse.
* **Neu erzeugte Ausgabedateien** ohne inhaltlichen Grund. PDF, DOCX und XLSX unter
  `output/` sind Binärdateien; jede Neuerzeugung bläht die Historie auf.
