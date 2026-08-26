# Quellcode

Die Pipeline ist in Ausführungsreihenfolge nummeriert. Alle Skripte lesen und schreiben
`data/bahn.db`; es gibt keinen anderen Zustand. Pfade kommen ausschließlich aus
[`lib/paths.py`](lib/paths.py) — `DATA` für Zwischenergebnisse, `OUT` für Dokumente, `DB`
für die Datenbank. Harte oder arbeitsverzeichnisrelative Pfade gehören nicht hierher.

| Datei | Aufgabe |
|---|---|
| `01_build_db.py` | GTFS-Rohdaten nach SQLite, Verkehrstage expandieren |
| `02_stations.py` | Betriebsstellen bilden, Staat und Bundesland zuordnen |
| `03_fix_names.py` | Bahnhofsnamen normalisieren |
| `04_cities.py` | Bahnhöfe zu Städten gruppieren |
| `05_trip_summary.py` | Kennzahlen je Zugtrasse (Dauer, Halte, Distanz, Geschwindigkeit) |
| `06_classify_sprinter.py` | ICE-Sprinter über Korridore und Fahrzeit-Ranking identifizieren |
| `07_analysis.py` | Linien, Streckenkanten, Bahnhofsbedienung ableiten |
| `08_ziel_liniennetz.py` | Zielliniennetz in zwei Szenarien, Betriebsleistung |
| `09_itf_edges.py` | Netzkanten zwischen Knoten bilden |
| `10_systemfahrzeiten.py` | Kantenbasis auf die Systemfahrzeit der Linien setzen |
| `11_knotenwahl.py` | Knotenmengen von 16 bis 64 vergleichen |
| `12_optimize_final.py` | Finale exakte Optimierung mit beidseitiger Knotenbindung |
| `13_build_fahrplan.py` | Minutenplan zum Tagesfahrplan ausrollen |
| `14_pdf_kursbuch.py` | Kursbuch der Linienfahrpläne |
| `15_pdf_bahnhoefe.py` | Bahnhofsfahrpläne |
| `16_build_xlsx.py` | Excel-Arbeitsmappe |
| `17_frankfurt_varianten.py` | Frankfurter Sonderfrage |
| `18_zentrierung.py` | Zentralität und Zentrierungswirkung |
| `19_ist_takt.py` | Taktqualität des heutigen Fahrplans |
| `20_kapazitaet.py` | Gleisbedarf je Knotenfenster |
| `21_sprinter_ueberholung.py` | Überholbedarf der Sprinter |

## Bibliothek

| Datei | Inhalt |
|---|---|
| `lib/pesp_sym.py` | **Der finale Optimierer.** MILP mit beidseitiger Knotenbindung und Zeitfenstern |
| `lib/pesp.py` | MILP mit einseitiger Bindung (Vorstufe, für die Vergleichsvarianten) |
| `lib/pesp2.py` | wie `pesp.py`, zusätzlich mit bestrafter Beschleunigung |
| `lib/opt2.py` | Heuristischer Optimierer (simuliertes Ausglühen) — nur noch für Schnellvergleiche |
| `lib/knotenwahl.py` | Kantenbildung für beliebige Knotenmengen, Reisezeitbewertung |
| `lib/fahrplan2.py` | **Die Fahrplan-Engine.** Minutenplan je Linie und Richtung |
| `lib/pdfbase.py` | Gemeinsame PDF-Grundlagen (Seitengerüst, Farben, Lesezeichen) |

## Web

`web/` enthält die Bausteine des interaktiven Dashboards (`head/style/body/script.part`,
zusammengesetzt zu `dashboard.html` — im Browser zu öffnen, ohne Server) und `makedoc.js`,
das die Studie als Word-Dokument erzeugt. Die Node-Abhängigkeit steht in
[`web/package.json`](web/package.json):

```bash
cd src/web && npm install && node makedoc.js
```

Zum Zusammenbau der `.part`-Dateien und zur fehlenden Eingabedatei `doc_data.json` siehe
[`docs/07-bekannte-luecken.md`](../docs/07-bekannte-luecken.md).

## Legacy

`legacy/` enthält die verworfenen Fassungen der Optimierer und Klassifikatoren. Sie sind
nicht Teil der Pipeline, dokumentieren aber den Weg — siehe
[`docs/CHANGELOG.md`](../docs/CHANGELOG.md). Wer nachvollziehen will, wie ein heuristischer
Optimierer einen Infrastrukturbedarf erfindet, der nicht existiert, findet dort das
Material.
