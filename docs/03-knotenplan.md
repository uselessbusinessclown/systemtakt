# Der Knotenplan

## Die zwanzig Vollknoten

Vollknoten sind die Bahnhöfe, an denen alle Züge in ein gemeinsames Zeitfenster gezwungen
werden, damit jeder Anschluss in jede Richtung besteht. Alle übrigen 246 Fernverkehrs-
bahnhöfe sind **Durchgangshalte**: Der Zug hält dort, wann immer es sein Laufweg ergibt,
ohne Bindung an eine Knotenminute.

Anker ist Berlin Hbf auf :00. Ri1 und Ri2 sind die beiden Fahrtrichtungen; ihre Fenster
dürfen sich um wenige Minuten unterscheiden — das ist der Freiheitsgrad, der die
beidseitige Knotenbindung überhaupt erst möglich macht (siehe [Methodik](02-methodik.md)).

| Vollknoten | Knotenzeit | Ankunft | Abfahrt | Kanten |
|---|---|---|---|---|
| Berlin Hbf | :00 / :30 | Ri1 :58 · Ri2 :55 | Ri1 :05 · Ri2 :02 | 8 |
| Dortmund Hbf | :00 / :30 | Ri1 :58 · Ri2 :57 | Ri1 :03 · Ri2 :02 | 7 |
| Leipzig Hbf | :00 / :30 | Ri1 :58 · Ri2 :55 | Ri1 :05 · Ri2 :02 | 5 |
| Mannheim Hbf | :00 / :30 | Ri1 :56 · Ri2 :58 | Ri1 :05 · Ri2 :02 | 10 |
| Duisburg Hbf | :13 / :43 | Ri1 :08 · Ri2 :11 | Ri1 :17 · Ri2 :18 | 7 |
| Frankfurt(Main)Hbf | :14 / :44 | Ri1 :09 · Ri2 :12 | Ri1 :16 · Ri2 :19 | 13 |
| Fulda | :14 / :44 | Ri1 :12 · Ri2 :09 | Ri1 :19 · Ri2 :16 | 8 |
| Bremen Hbf | :15 / :45 | Ri1 :13 · Ri2 :13 | Ri1 :17 · Ri2 :17 | 3 |
| Dresden Hbf | :15 / :45 | Ri1 :10 · Ri2 :13 | Ri1 :17 · Ri2 :20 | 2 |
| Hamburg Hbf | :15 / :45 | Ri1 :13 · Ri2 :13 | Ri1 :17 · Ri2 :17 | 4 |
| Münster(Westf)Hbf | :15 / :45 | Ri1 :10 · Ri2 :13 | Ri1 :17 · Ri2 :20 | 5 |
| Erfurt Hbf | :16 / :46 | Ri1 :12 · Ri2 :14 | Ri1 :18 · Ri2 :18 | 7 |
| Stuttgart Hbf | :17 / :47 | Ri1 :15 · Ri2 :15 | Ri1 :19 · Ri2 :20 | 6 |
| München Hbf | :24 / :54 | Ri1 :19 · Ri2 :19 | Ri1 :29 · Ri2 :29 | 6 |
| Nürnberg Hbf | :26 / :56 | Ri1 :21 · Ri2 :24 | Ri1 :31 · Ri2 :28 | 6 |
| Karlsruhe Hbf | :27 / :57 | Ri1 :22 · Ri2 :25 | Ri1 :30 · Ri2 :29 | 5 |
| Hannover Hbf | :29 / :59 | Ri1 :26 · Ri2 :27 | Ri1 :31 · Ri2 :34 | 11 |
| Kassel-Wilhelmshöhe | :29 / :59 | Ri1 :24 · Ri2 :24 | Ri1 :34 · Ri2 :34 | 8 |
| Köln Hbf | :29 / :59 | Ri1 :24 · Ri2 :24 | Ri1 :34 · Ri2 :34 | 7 |
| Würzburg Hbf | :29 / :59 | Ri1 :27 · Ri2 :27 | Ri1 :31 · Ri2 :31 | 8 |

Es bilden sich drei Taktfamilien: :00 (Berlin, Dortmund, Leipzig, Mannheim), :13–:17
(Duisburg, Frankfurt, Fulda, Bremen, Dresden, Hamburg, Münster, Erfurt, Stuttgart) und
:24–:29 (München, Nürnberg, Karlsruhe, Hannover, Kassel-Wilhelmshöhe, Köln, Würzburg).
Diese Gruppierung ist nicht gesetzt, sondern Ergebnis der Optimierung — sie spiegelt die
Fahrzeiten zwischen den Knoten.

## Wie viele Vollknoten verträgt das Netz?

Jeder Vollknoten kauft Anschlüsse mit Fahrzeit. Gerechnet wurden Knotenmengen von 16 bis 64,
jeweils exakt gelöst, und für jede die mittlere Verlängerung der Reisezeit gegenüber dem
heutigen Fahrplan bestimmt — gewichtet nach Bedienhäufigkeit der Linien.

| Variante | Vollknoten | Netzkanten | Ø Reserve | Sollband | Reisezeit gegenüber heute |
|---|---|---|---|---|---|
| Top 16 nach Verkehr | 16 | 56 | 5.06 % | 69.7 % | +17.7 min |
| K16 kuratiert | 16 | 53 | 5.08 % | 61.0 % | +15.3 min |
| Top 20 nach Verkehr | 20 | 69 | 5.24 % | 67.0 % | +19.7 min |
| K20 kuratiert | 20 | 68 | 6.7 % | 59.0 % | +18.8 min |
| Top 24 nach Verkehr | 24 | 81 | 6.86 % | 60.9 % | +24.1 min |
| K24 kuratiert | 24 | 80 | 5.7 % | 63.6 % | +22.6 min |
| Top 30 nach Verkehr | 30 | 99 | 6.74 % | 53.1 % | +28.6 min |
| Top 40 nach Verkehr | 40 | 125 | 8.42 % | 53.2 % | +33.5 min |
| Top 64 nach Verkehr | 64 | 173 | 7.65 % | 61.8 % | +38.5 min |

**Jeder zusätzliche Vollknoten kostet rund eine halbe Minute mittlere Reisezeit.** Die
Fahrzeitreserve je Kante bleibt dabei nahezu unverändert — sie verteilt sich nur auf mehr
Knoten, und jede Fahrt sammelt mehr davon ein.

Gewählt wurde **K20 kuratiert**: zwanzig Vollknoten, geografisch ausgewogen und zugleich
die Bahnhöfe mit den meisten Umsteigebeziehungen. Die Werte in der Tabelle stammen aus dem
einseitigen Vergleichsmodell; der finale Plan mit beidseitiger Knotenbindung erreicht
6,61 % mittlere Reserve und +16,6 Minuten mittlere Reisezeit.

## Kantenplan

Die 68 Netzkanten mit Systemfahrzeit, Soll-Fahrzeit je Richtung und resultierender Reserve
stehen in der Datenbanktabelle `itf_ergebnis` und im Excel-Blatt „ITF Kanten Soll".

Die Soll-Zeiten unterscheiden sich je Richtung, weil die Knotenfenster je Richtung anders
liegen dürfen. Keine einzige Kante wird in irgendeiner Richtung schneller befahren als
heute.

## Der Sonderfall Sprinter

Ein Sprinter ist nur an seinen beiden Metropolknoten taktgebunden, nicht an den Knoten
dazwischen. Bindet man ihn auch dort, verliert er seinen Vorsprung — für Berlin–Köln ergäbe
die knotenweise Einpassung 5:26 statt 4:22. Das ist die Regel, die die Prioritätenordnung
auf der Fahrplanebene wirksam macht.
