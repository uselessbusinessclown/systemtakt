# Systemtakt Fernverkehr Deutschland

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

**5. Ein grobes Knotenraster ist keine Lösung.**
Zwingt man alle Knoten auf das schweizerische :00/:15-Schema, springt die mittlere Reserve
von 7,7 auf 35,7 %. Deutschland hat kein Netz mit dominanter Achse; die Knotenminuten
müssen frei bleiben.

## Aufbau

```
docs/      Methodik, Ergebnisse, Grenzen, Änderungsprotokoll
src/       Die vollständige Pipeline, in Ausführungsreihenfolge nummeriert
src/lib/   Die Optimierer und die Fahrplan-Engine
src/legacy/Frühere Fassungen der Optimierer (Dokumentation des Irrwegs, siehe CHANGELOG)
data/      bahn.db (SQLite, 36 Tabellen) und CSV-Export aller Tabellen
output/    Die fertigen PDFs, die Word-Studie und die Excel-Arbeitsmappe
```

Einstiegspunkte:

* **[docs/02-methodik.md](docs/02-methodik.md)** — wie das Optimierungsproblem formuliert und exakt gelöst wird
* **[docs/03-knotenplan.md](docs/03-knotenplan.md)** — die 20 Vollknoten mit ihren Zeiten
* **[docs/04-fahrplan.md](docs/04-fahrplan.md)** — wie aus dem Knotenplan der Fahrplan wird
* **[docs/CHANGELOG.md](docs/CHANGELOG.md)** — vier Fassungen, drei Korrekturen, ehrlich protokolliert

## Reproduzieren

```bash
pip install -r requirements.txt
make all          # lädt die Rohdaten, baut die Datenbank, optimiert, erzeugt alle Ausgaben
```

Die Optimierung läuft mit HiGHS über `scipy.optimize.milp`. Der finale Lauf braucht auf
zwei Kernen rund 15 Minuten; die Knotenzahl-Studie in Summe etwa eine Stunde.

## Datenquellen

* **Fahrplandaten**: [gtfs.de](https://gtfs.de/de/feeds/de_fv/), Feed „Fernverkehr Deutschland" (`de_fv`),
  Daten bereitgestellt von **DELFI e. V.** — ausgewerteter Zeitraum 22.08.–21.09.2026
* **Sprinterangebot**: [bahn.de, Seite „ICE Sprinter"](https://www.bahn.de/service/ueber-uns/zugtypen/ice-sprinter)
* **Staatsgrenzen**: [datasets/geo-countries](https://github.com/datasets/geo-countries)
* **Bundeslandgrenzen**: [isellsoap/deutschlandGeoJSON](https://github.com/isellsoap/deutschlandGeoJSON)

## Lizenz

Der Quellcode steht unter der MIT-Lizenz (siehe [LICENSE](LICENSE)).
Die Fahrplan-Rohdaten unterliegen den Bedingungen von DELFI e. V. / gtfs.de und sind
hier nur in abgeleiteter, aggregierter Form enthalten.
