# Vom Knotenplan zum Fahrplan

Der Knotenplan legt nur die Zeiten an 20 Bahnhöfen fest. Ein Fahrplan braucht Zeiten an
allen 266. Dieser Schritt ist reine Ableitung — er trifft keine Entscheidungen mehr.

## Das Verfahren

Für jede Linie und jede Richtung ([`src/lib/fahrplan2.py`](../src/lib/fahrplan2.py)):

1. **Laufweg bestimmen.** Aus den Fahrplandaten wird für jede Linie das häufigste
   Haltemuster ermittelt. Für jedes Paar aufeinanderfolgender Halte wird die heutige
   Fahrzeit als Median über alle beobachteten Fahrten dieser Linie berechnet.

2. **Knoten verankern.** An jedem Vollknoten des Laufwegs stehen Ankunft und Abfahrt fest:
   φ − a bzw. φ + d, mit den Fensteroffsets der jeweiligen Fahrtrichtung.

3. **Abschnitte einpassen.** Zwischen zwei aufeinanderfolgenden Vollknoten ist die
   Gesamtzeit durch den Knotenplan vorgegeben. Die heutigen Fahrzeiten der einzelnen
   Teilstrecken werden proportional auf diese Gesamtzeit skaliert; Zwischenhalte erhalten
   eine Haltezeit von einer Minute, an Bahnhöfen mit mehr als 60 Halten am Tag zwei.
   Rundungsdifferenzen werden reihum verteilt, so dass die Summe exakt stimmt.

4. **Enden anhängen.** Vor dem ersten und nach dem letzten Vollknoten fährt der Zug mit
   seinen heutigen Fahrzeiten weiter — dort gibt es nichts einzupassen.

5. **Takt ausrollen.** Die Abfahrtsminute am Startbahnhof wird über die Betriebszeit
   5 bis 23 Uhr im Takt der Linie wiederholt (30, 60 oder 120 Minuten, Szenario A).

Zeiten nach Mitternacht werden als 24:xx und 25:xx geführt.

## Umfang

| Produktebene | Züge je Tag | Halte je Tag | Linien |
|---|---|---|---|
| ICE-Sprinter | 126 | 684 | 7 |
| ICE | 1.010 | 8.556 | 50 |
| IC/EC | 564 | 3.636 | 27 |
| **Summe** | **1.700** | **12.876** | **84** |

266 Bahnhöfe werden bedient, 168 Linienrichtungen sind ausgewiesen.

## Prüfungen

* **Knotendisziplin.** Alle 4.014 Halte an Vollknoten liegen in ihrem Fenster. Kein
  einziger Ausreißer.
* **Reisezeit.** Die mittlere Verlängerung gegenüber dem heutigen Fahrplan beträgt
  **+16,6 Minuten**, gewichtet nach Bedienhäufigkeit.
* **Anschlüsse.** Stichprobe Frankfurt Hbf: alle Ankünfte zwischen :09 und :12, alle
  Abfahrten zwischen :16 und :19. Der Knoten funktioniert.

## Die Ausgaben

**[Kursbuch der Linienfahrpläne](../output/Kursbuch_Linienfahrplaene.pdf)** (192 Seiten, quer)
Für jede Linie und Richtung eine Tabelle: Zeilen sind die Halte in Fahrtreihenfolge,
Spalten die einzelnen Züge des Tages. An Vollknoten stehen zwei Zeiten übereinander —
oben die Ankunft, unten fett die Abfahrt. Mit Inhaltsverzeichnis und PDF-Lesezeichen.

**[Bahnhofsfahrpläne](../output/Bahnhofsfahrplaene.pdf)** (292 Seiten, hoch)
Für jeden Bahnhof eine Aushangtafel: Abfahrtszeit, Linie, Ziel und die wichtigsten
Unterwegshalte, darunter die Ankünfte endender Züge. Der Kopf nennt die Rolle im Takt.
Mit alphabetischem Register und Lesezeichen.

An den Vollknoten wird die Taktstruktur in der Tafel unmittelbar sichtbar: In Frankfurt Hbf
sammeln sich die 306 täglichen Abfahrten in zwei kurzen Fenstern je Stunde.

## Grenzen dieser Ableitung

Die Fahrzeiten zwischen den Halten sind Sollzeiten des heutigen Fahrplans, keine Ergebnisse
einer Fahrdynamikrechnung. Die proportionale Skalierung eines Abschnitts verteilt den
Taktzuschlag gleichmäßig — ein echter Fahrplan würde ihn dort konzentrieren, wo er
betrieblich am wenigsten stört. Überholungen, Kreuzungen auf eingleisigen Abschnitten und
Gleisbelegungen in den Bahnhöfen sind nicht geprüft.
