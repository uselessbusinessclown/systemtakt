# Datengrundlage

## Quelle

Grundlage ist der offene GTFS-Datensatz **„Fernverkehr Deutschland"** von
[gtfs.de](https://gtfs.de/de/feeds/de_fv/) (`de_fv`), der die von **DELFI e. V.**
bereitgestellten Solldaten aller Fernverkehrszüge mit Halt in Deutschland enthält.

Ausgewerteter Zeitraum: **22. August bis 21. September 2026** — ein voller Monat mit allen
Wochentagsvarianten und Verkehrstagsausnahmen.

## Umfang

| | |
|---|---|
| Zugtrassen | 5.589 |
| Einzelhalte | 54.928 |
| Bahnhöfe | 567 (290 in Deutschland) |
| Linien | 96 (50 ICE/ECE, 27 IC/EC, 19 sonstige) |
| Verkehrsunternehmen | 13 |
| Züge je Werktag | rund 1.090 |

Bahnhöfe nach Land: Deutschland 290, Polen 112, Österreich 53, Schweiz 22, Tschechien 19,
Dänemark 13, Ungarn 12, Niederlande 10, weitere 36.

## Aufbereitung

**Bahnhöfe** ([`src/02_stations.py`](../src/02_stations.py), [`03`](../src/03_fix_names.py),
[`04`](../src/04_cities.py)).
Die Bahnsteig-Haltepunkte des Rohdatensatzes werden zu 567 Betriebsstellen zusammengefasst.
Jeder wird über eine Punkt-in-Polygon-Prüfung Staat und Bundesland zugeordnet. Namen werden
normalisiert („Aalen, Hauptbahnhof" → „Aalen Hbf"), Sonderfälle wie das generische
„Hauptbahnhof" für Erfurt und Kiel manuell korrigiert. Zusätzlich werden Bahnhöfe zu Städten
gruppiert, damit Berlin Hbf, Südkreuz, Spandau und Gesundbrunnen bei Relationsauswertungen
als ein Ort gelten.

**Linien** ([`src/07_analysis.py`](../src/07_analysis.py)).
Aus den Zugfahrten werden 96 Linien abgeleitet, jeweils mit dem häufigsten Laufweg, der
typischen Fahrzeit, der Bedienhäufigkeit und der vollständigen Haltefolge.

**Kanten** ([`src/07_analysis.py`](../src/07_analysis.py)).
Für 1.044 unmittelbar benachbarte Bahnhofspaare werden kürzeste, mittlere und längste
beobachtete Fahrzeit sowie die Belastung nach Produktklasse bestimmt.

## Die Sprinter-Frage

Der offene Datensatz enthält **keine Zugnummern**; das Merkmal „ICE Sprinter" ist darin
nicht codiert. Die Zuordnung erfolgt deshalb zweistufig
([`src/06_classify_sprinter.py`](../src/06_classify_sprinter.py)):

1. Die sieben von der DB vermarkteten Sprinter-Korridore werden als Städterelationen
   hinterlegt (Quelle: [bahn.de](https://www.bahn.de/service/ueber-uns/zugtypen/ice-sprinter)).
2. Innerhalb jedes Korridors werden die Trassen nach Fahrzeit sortiert und so viele als
   Sprinter markiert, bis die dort veröffentlichte Angebotsdichte erreicht ist.

Das Verfahren reproduziert die offiziellen Frequenzen auf ein bis zwei Fahrten je Tag genau
und ergibt 72 Sprinterfahrten am Tag.

| Korridor | berechnet | bahn.de |
|---|---|---|
| Hamburg/Hannover – Frankfurt | 7,7 | 8 |
| Hamburg – Ruhr/Köln | 5,1 | 6 |
| Berlin – Köln/Bonn | 8,2 | 8 |
| Berlin/Halle/Erfurt – Nürnberg/München | 32,2 | 32 |
| Berlin/Halle/Erfurt – Frankfurt | 14,1 | 14 |
| Frankfurt/Mannheim/Karlsruhe – Paris | 2,6 | 2 |
| Stuttgart – Nürnberg – Berlin | 2,0 | 2 |

Dies ist eine begründete Rekonstruktion, keine amtliche Kennzeichnung.

## Plausibilitätsprüfung

Stichproben gegen bekannte Fahrzeiten:

| Relation | aus den Daten | Erwartung |
|---|---|---|
| Berlin – Hamburg (ohne Halt) | 107 min | ~1:45–1:52 |
| Köln – Frankfurt Flughafen | 49 min | ~50 min |
| Würzburg – Nürnberg | 51 min | ~54 min |
| Hannover – Göttingen | 32 min | ~32 min |
| Frankfurt – Mannheim | 34 min | ~35 min |
| Erfurt – Halle | 27 min | ~27 min |

## Weitere Quellen

* Staatsgrenzen: [datasets/geo-countries](https://github.com/datasets/geo-countries)
* Bundeslandgrenzen: [isellsoap/deutschlandGeoJSON](https://github.com/isellsoap/deutschlandGeoJSON)
* Infrastrukturangaben zu den Frankfurter Bahnhöfen: Wikipedia
