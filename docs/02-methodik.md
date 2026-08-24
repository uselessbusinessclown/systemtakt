# Methodik

## Das Problem

Ein integraler Taktfahrplan verlangt, dass an bestimmten Bahnhöfen — den **Vollknoten** —
alle Züge innerhalb weniger Minuten eintreffen und gemeinsam wieder abfahren. Dann besteht
jeder Anschluss in jede Richtung, ohne dass man die Verbindungen einzeln planen müsste.

Die Aufgabe lautet also: Weise jedem Vollknoten *i* eine **Knotenminute** φ(i) im
30-Minuten-Raster zu, so dass die Fahrzeiten zwischen den Knoten möglichst gut zu diesen
Minuten passen. Das ist ein *Periodic Event Scheduling Problem* (PESP) und NP-schwer.

## Formulierung

### Grundbedingung

Fährt ein Zug am Knoten *i* zur Minute φ(i)+d ab und soll am Knoten *j* zur Minute φ(j)−a
ankommen, so muss seine Fahrzeit *R* die Bedingung

```
R  ≡  (φ(j) − a)  −  (φ(i) + d)      (mod 30)
```

erfüllen. Die tatsächliche Fahrzeit ist dann R = T + p, wobei **T** die Systemfahrzeit der
Strecke ist (die Zeit, die die dort verkehrenden Linien heute brauchen) und **p ≥ 0** der
Fahrzeitzuschlag, den der Takt erzwingt.

### Beide Fahrtrichtungen

Ein Knoten funktioniert nur, wenn die Bindung in **beiden** Richtungen gilt. Fordert man
Ankunft und Abfahrt auf dieselbe Minute in beiden Richtungen, ergibt sich

```
φ(j) − φ(i) ≡ 0  oder  15   (mod 30)
```

— alle Knotenminuten müssten also auf einem Viertelstundenraster liegen. Diese Variante
wurde gerechnet (T2) und kostet 35,7 % mittlere Fahrzeitreserve; sie ist nicht darstellbar.

Die Lösung sind **schmale Zeitfenster**: Ankunft 2 bis 5 Minuten vor der Knotenminute,
Abfahrt 2 bis 5 Minuten danach, für jede Richtung getrennt wählbar. Die Fensterlagen sind
Variablen des Optimierungsproblems. Damit ist die beidseitige Bindung erfüllbar, ohne das
Raster zu vergröbern — und der kürzeste Übergang im Knoten beträgt immer noch vier Minuten.

### Zielfunktion

Jede Kante geht mit dem Gewicht

```
w  =  3 × Sprinterfahrten  +  2 × ICE-Fahrten  +  1 × IC-Fahrten     (je Tag)
```

ein. Die geforderte Prioritätenordnung *Sprinter vor ICE vor IC* steckt damit unmittelbar
in der Zielfunktion, nicht nur im Vorwort.

Die Kosten eines Zuschlags *p* sind stückweise linear:

```
c(p)  =  w · ( 0,15 · p  +  2 · max(0, p − L) )      mit  L = 0,07 · T + 2
```

Bis zur ohnehin nötigen Fahrzeitreserve von sieben Prozent ist der Zuschlag also billig,
darüber hinaus teuer.

### Als gemischt-ganzzahliges Programm

| Variablen | Anzahl | Bereich |
|---|---|---|
| Knotenminute φ(i) | 20 | ganzzahlig 0…29 |
| Fensteroffsets a₁, d₁, a₂, d₂ je Knoten | 80 | ganzzahlig 2…5 |
| Periodenzähler k je Kante und Richtung | 136 | ganzzahlig |
| Zuschlag p je Kante und Richtung | 136 | 0…29 |
| Hilfsvariable u je Kante und Richtung | 136 | ≥ 0 |

Nebenbedingungen je Kante (i,j) und Richtung:

```
(φ(j) − a) − (φ(i) + d) + 30·k − p  =  T
u ≥ p − L
```

Die Rotationssymmetrie wird durch Fixierung eines Ankers (`Berlin Hbf = :00`) gebrochen —
das beschleunigt den Solver erheblich und ändert am Ergebnis nichts (siehe unten).

Gelöst wird mit **HiGHS** über `scipy.optimize.milp`. Implementierung:
[`src/lib/pesp_sym.py`](../src/lib/pesp_sym.py).

## Neubaufreiheit

Im Grundfall ist `p ≥ 0` — eine Fahrzeit *unter* der heutigen ist gar nicht zugelassen.
Der Takt entsteht ausschließlich aus Zuschlägen. Zum Vergleich wurden Varianten gerechnet,
die Verkürzungen bis 3 bzw. 6 Minuten erlauben, bewertet mit dem vierfachen Kostensatz
([`src/lib/pesp2.py`](../src/lib/pesp2.py)).

## Systemfahrzeit statt Bestzeit

Die Basiszeit T einer Kante ist **nicht** die schnellste je gefahrene Zeit, sondern die
Zeit, die die dort tatsächlich verkehrenden Linien brauchen — konkret das 75.-Perzentil
der linienbezogenen Fahrzeitbedarfe, gewichtet nach Bedienhäufigkeit und gedeckelt bei
125 % der Bestzeit. Ohne diese Korrektur verlangt ein Linienzug mit einem Zwischenhalt
mehr Zeit als die Kante hergibt und springt um volle 30 Minuten
([`src/10_systemfahrzeiten.py`](../src/10_systemfahrzeiten.py)).

## Rotationsinvarianz

Die Lösung ist nur bis auf eine gemeinsame Verschiebung eindeutig. Verschiebt man alle
Knotenminuten um denselben Betrag, ändert sich keine Fahrzeit und kein Anschluss. Numerisch
geprüft für acht verschiedene Anker — in jedem Fall exakt derselbe Zielfunktionswert.

Die Wahl des Ankers ist damit eine Frage der Darstellung, nicht der Fahrplanqualität.
Gewählt wurde Berlin Hbf auf :00.

## Was die Optimierung *nicht* leistet

Sie bestimmt die Knotenminuten, nicht die Zahl der Knoten. Diese ist der eigentliche
Stellhebel und wurde durch eine separate Studie über Knotenmengen von 16 bis 64 bestimmt
([`src/11_knotenwahl.py`](../src/11_knotenwahl.py), Ergebnisse in
[03-knotenplan.md](03-knotenplan.md)).

## Warum exakt und nicht heuristisch

Frühere Fassungen dieser Arbeit nutzten simuliertes Ausglühen. Die Ergebnisse schwankten je
nach Zufallsstartwert um bis zu 18 Prozent und wiesen fünf Netzkanten als ausbaubedürftig
aus, die es in Wahrheit nicht sind — der scheinbare Infrastrukturbedarf war ein Artefakt
der Lösungsmethode. Die heuristischen Fassungen liegen zur Nachvollziehbarkeit unter
[`src/legacy/`](../src/legacy/); das Änderungsprotokoll in [CHANGELOG.md](CHANGELOG.md)
hält fest, was wann korrigiert wurde.
