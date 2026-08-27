# Systemtakt Fernverkehr Deutschland

[![CI](https://github.com/uselessbusinessclown/systemtakt/actions/workflows/ci.yml/badge.svg)](https://github.com/uselessbusinessclown/systemtakt/actions/workflows/ci.yml)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-1F3864.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-1F3864.svg)](requirements.txt)
[![Datenstand 08/2026](https://img.shields.io/badge/Datenstand-22.08.–21.09.2026-1F3864.svg)](docs/01-datengrundlage.md)

Eine vollständige Datenbank des deutschen Schienenfernverkehrs (ICE, IC, EC) und daraus
berechnet ein **integraler Taktfahrplan nach schweizerischem Vorbild** — exakt optimiert,
ohne jede Neubaumaßnahme, ausgerollt zu einem minutengenauen Tagesfahrplan für alle
Linien und alle Bahnhöfe.

> **Kein gültiger Fahrplan.** Dies ist eine Studie. Alle Zeiten sind Sollzeiten eines
> Entwurfs. Für Reiseauskünfte gilt ausschließlich der offizielle Fahrplan der
> Eisenbahnverkehrsunternehmen.

---

## Was hier drin ist

| | |
|---|---|
| **Datenbank** | 567 Bahnhöfe (290 in Deutschland), 96 Linien, 5.589 Zugtrassen, 54.928 Halte, 1.044 Streckenkanten mit gemessenen Fahrzeiten |
| **Knotenplan** | 20 Vollknoten mit Knotenminute und richtungsgetrennten Ankunfts-/Abfahrtsfenstern, 68 Netzkanten mit Soll-Fahrzeiten |
| **Fahrplan** | 1.700 Züge und 12.876 Halte je Betriebstag, 5–23 Uhr, 168 Linienrichtungen, 266 Bahnhöfe |
| **Ausgaben** | Kursbuch der Linienfahrpläne (192 S.), Bahnhofsfahrpläne (292 S.), Studie (27 S.), Excel-Arbeitsmappe (22 Blätter) |

## Die wichtigsten Ergebnisse

**1. Der Takt braucht keinen Neubau.**
Unter der harten Nebenbedingung, dass keine Netzkante schneller befahren werden darf als
heute, liegt die mittlere Fahrzeitreserve bei **6,6 %** — unter dem schweizerischen Zielwert
von 7 %. Erlaubt man Beschleunigungen bis zu drei Minuten, sinkt sie auf 7,0 %; verdoppelt
man den erlaubten Ausbau auf sechs Minuten, auf 6,97 %. Der Nutzen von Streckenausbau für
die Taktbildung ist nach wenigen Minuten erschöpft.

**2. Die Zahl der Vollknoten ist der eigentliche Stellhebel.**
Jeder zusätzliche Vollknoten kostet rund **eine halbe Minute mittlere Reisezeit**. Bei
64 Vollknoten verlängert sich die Durchschnittsfahrt um 38 Minuten, bei 20 um 17. Ein
integraler Taktfahrplan braucht wenige, dafür starke Knoten.

**3. Die Wahl des Ankerbahnhofs ist wirkungslos, eine echte Zentrierung hilft.**
Welcher Bahnhof auf :00 liegt, ändert nichts — der Plan ist bis auf eine gemeinsame
Verschiebung eindeutig (numerisch nachgewiesen: acht Anker, identischer Zielfunktionswert).
Wirksam ist die Höhergewichtung eines Prioritätsknotens: Frankfurt Hbf gewinnt dabei
3,05 Prozentpunkte Reserve, ohne dass das übrige Netz schlechter wird.

**4. Der Frankfurter Engpass löst sich nicht durch Verlagerung an den Flughafen.**
78 % der Gleisbelegung des Hauptbahnhofs entfallen auf wendende Züge, die Sprinter tragen
nur 10 %. Eine Sprinterverlagerung entlastet um 10 %, verschlechtert aber die Taktqualität
um 43 %. Die Durchbindung der wendenden Züge entlastet um 59 %.

**5. Der offizielle Zielfahrplan verbessert die Knotenbindung nicht.**
An den zwanzig größten Fernverkehrsknoten erreicht der 3. Gutachterentwurf des
Deutschlandtakts dieselbe Knotengüte wie der heutige Fahrplan — **53 % gegen 53 %**, mit
demselben Maß gemessen. Er verteilt sie um (Dresden +27 Punkte, Dortmund −32), verbessert
sie aber nicht. Sein Ausbau geht in Geschwindigkeit, nicht in Taktintegration.

**6. Neubaufrei kostet 44 Minuten — nachgemessen am offiziellen Zielfahrplan.**
Gegen den 3. Gutachterentwurf des Deutschlandtakts, mit derselben Routing-Engine über
1.140 Relationen zwischen den 20 Knoten gefahren, liegt dieser Plan im Mittel
**44 Minuten** zurück. Das ist nicht die Taktdisziplin — die leistet, was sie soll, und
spart sogar Umstiege. Es ist die Infrastruktur: Der Gutachterentwurf befährt 11 von 16
vergleichbaren Kanten schneller, als heute je gefahren wurde. Ergebnis 1 bleibt damit
richtig und bekommt einen Preis. Siehe
[docs/08-backtest-deutschlandtakt.md](docs/08-backtest-deutschlandtakt.md).

**7. Ein grobes Knotenraster ist keine Lösung.**
Zwingt man alle Knoten auf das schweizerische :00/:15-Schema, springt die mittlere Reserve
von 7,7 auf 35,7 %. Deutschland hat kein Netz mit dominanter Achse; die Knotenminuten
müssen frei bleiben.

## Aufbau

```
Makefile    Der Reproduktionspfad, in fünf Stufen — `make help` zeigt sie
docs/       Methodik, Ergebnisse, Grenzen, Änderungsprotokoll
src/        Die vollständige Pipeline, in Ausführungsreihenfolge nummeriert
src/lib/    Die Optimierer und die Fahrplan-Engine
src/legacy/ Frühere Fassungen der Optimierer (Dokumentation des Irrwegs, siehe CHANGELOG)
src/web/    Das interaktive Dashboard und der Word-Generator
data/       bahn.db (SQLite, 36 Tabellen) und CSV-Export aller Tabellen
output/     Die fertigen PDFs, die Word-Studie und die Excel-Arbeitsmappe
backtest/   Gegenprobe gegen den offiziellen Deutschlandtakt
tools/      Die Prüfungen, die auch im CI laufen
```

Einstiegspunkte:

* **[docs/02-methodik.md](docs/02-methodik.md)** — wie das Optimierungsproblem formuliert und exakt gelöst wird
* **[docs/03-knotenplan.md](docs/03-knotenplan.md)** — die 20 Vollknoten mit ihren Zeiten
* **[docs/04-fahrplan.md](docs/04-fahrplan.md)** — wie aus dem Knotenplan der Fahrplan wird
* **[docs/06-grenzen.md](docs/06-grenzen.md)** — was die Untersuchung fachlich nicht leistet
* **[docs/07-bekannte-luecken.md](docs/07-bekannte-luecken.md)** — wo die Reproduktion heute klemmt
* **[docs/08-backtest-deutschlandtakt.md](docs/08-backtest-deutschlandtakt.md)** — die Gegenprobe gegen den offiziellen Zielfahrplan
* **[docs/CHANGELOG.md](docs/CHANGELOG.md)** — vier Fassungen, drei Korrekturen, ehrlich protokolliert

## Ohne Neuberechnung loslegen

Alle Ergebnisse liegen fertig im Repository. Für einen ersten Blick braucht es nichts
außer einem SQLite-Client:

```bash
sqlite3 data/bahn.db 'SELECT name, knotenminute, knotenzeit FROM itf_knotenzeit ORDER BY gewicht DESC'
```

Wer lieber liest als abfragt: `output/` enthält Kursbuch, Bahnhofsfahrpläne, Studie und
Arbeitsmappe; `data/csv/` alle 36 Tabellen als semikolongetrennte Dateien;
`src/web/dashboard.html` das interaktive Dashboard — im Browser öffnen, kein Server nötig.

## Reproduzieren

Voraussetzung ist Python 3.11 oder neuer; für die Word-Studie zusätzlich Node 18 oder
neuer.

```bash
pip install -r requirements.txt
make help         # zeigt die fünf Stufen einzeln
make all          # lädt die Rohdaten, baut die Datenbank, optimiert, erzeugt alle Ausgaben
```

Die Optimierung läuft mit HiGHS über `scipy.optimize.milp`. Der finale Lauf braucht auf
zwei Kernen rund 15 Minuten; die Knotenzahl-Studie in Summe etwa eine Stunde.

Einige Schritte laufen derzeit nicht durch — welche und warum, steht vollständig in
[docs/07-bekannte-luecken.md](docs/07-bekannte-luecken.md). Die mitgelieferten Ergebnisse
sind davon nicht berührt.

## Datenquellen

* **Fahrplandaten**: [gtfs.de](https://gtfs.de/de/feeds/de_fv/), Feed „Fernverkehr Deutschland" (`de_fv`),
  Daten bereitgestellt von **DELFI e. V.** — ausgewerteter Zeitraum 22.08.–21.09.2026
* **Sprinterangebot**: [bahn.de, Seite „ICE Sprinter"](https://www.bahn.de/service/ueber-uns/zugtypen/ice-sprinter)
* **Staatsgrenzen**: [datasets/geo-countries](https://github.com/datasets/geo-countries)
* **Bundeslandgrenzen**: [isellsoap/deutschlandGeoJSON](https://github.com/isellsoap/deutschlandGeoJSON)

## Mitwirken

Widerlegungen sind der wertvollste Beitrag: Drei der vier Fassungen mussten Aussagen der
vorherigen widerrufen. Wie man eine Zahl bestreitet, einen Datenfehler meldet oder einen
Reproduktionsfehler einreicht, steht in [CONTRIBUTING.md](CONTRIBUTING.md); die
Umgangsregeln in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Zitieren

Zitierangaben stehen maschinenlesbar in [CITATION.cff](CITATION.cff) — GitHub bietet sie
über „Cite this repository" in mehreren Formaten an.

## Lizenz

Der Quellcode steht unter der MIT-Lizenz (siehe [LICENSE](LICENSE)).
Die Fahrplan-Rohdaten unterliegen den Bedingungen von DELFI e. V. / gtfs.de und sind
hier nur in abgeleiteter, aggregierter Form enthalten.
