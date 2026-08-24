# Sonderfragen

## Frankfurt Hbf oder Flughafen-Fernbahnhof?

Frankfurt ist der einzige Knoten, an dem das Konzept an der Infrastruktur scheitert. Liegt
die Lösung darin, den Fernverkehr an den elf Bahnminuten entfernten Flughafen-Fernbahnhof zu
verlagern? Geprüft wurden drei Varianten ([`src/17_frankfurt_varianten.py`](../src/17_frankfurt_varianten.py)).

**Die Gleisbelegung enthält die Antwort.** Von den 3.383 Gleisminuten, die der Fernverkehr
täglich am Hauptbahnhof beansprucht, entfallen **78 % auf wendende Züge** und nur 22 % auf
durchfahrende. Die ICE-Sprinter tragen zusammen 335 Gleisminuten — knapp 10 %.

| Variante | Zielfunktion je Gewicht | Kanten mit Beschl. | Gleismin. Hbf | Gleismin. Flughafen | Auslastung Flughafen |
|---|---|---|---|---|---|
| Status quo | 1,91 | 5 | 3.383 | 1.050 | 24 % |
| A — alles an den Flughafen | 2,23 | 6 | 0 | 4.433 | **103 %** |
| B — Sprinter an den Flughafen | 2,74 | 11 | 3.048 | 1.385 | 32 % |
| C — Fernbahntunnel | 1,91 | 5 | **1.373** | 1.050 | 24 % |

**Variante A** scheitert an der Kapazität: 4.433 Gleisminuten auf vier Bahnsteiggleisen sind
103 % rechnerische Auslastung; bei realistischem Nutzungsgrad wären rund sieben Gleise nötig.
Dazu verlören eine halbe Million Reisende täglich die Innenstadtanbindung.

**Variante B** ist die schlechteste. Sie erzwingt zwei Vollknoten im Abstand von elf
Bahnminuten, während das Raster nur Schritte von 30 Minuten kennt: Zielfunktion +43 %,
Kanten mit Beschleunigungsbedarf von 5 auf 11 — für eine Entlastung des Hauptbahnhofs um
lediglich 10 %.

**Variante C** greift dort an, wo das Problem liegt: Werden die wendenden Züge
durchgebunden, sinkt die Gleisbelegung um **59 %** — das Sechsfache der Sprinterverlagerung.

Sieben Linien mit zusammen 47 Fahrten am Tag (21 % des Hauptbahnhofsangebots) wären vom
Flughafen aus nicht direkt erreichbar. Die Größenordnung ist ohnehin nicht vergleichbar:
vier Bahnsteiggleise und rund 30.000 Nutzer täglich am Flughafen gegen 25 Fernbahngleise,
neun S-Bahn-Linien, zwei U-Bahn-Linien und etwa 493.000 Reisende am Hauptbahnhof.

**Ohne Tunnel geht ein Zwischenschritt:** Von den 91,5 wendenden ICE-Fahrten am Tag lässt
sich ein Teil zu durchgehenden Linien über Frankfurt Süd und den Flughafen verknüpfen. Jede
durchgebundene Fahrt spart rund 19 Gleisminuten; zwanzig davon entsprechen bereits der
Entlastung einer vollständigen Sprinterverlagerung.

---

## Hilft eine Zentrierung auf einen großen Bahnhof?

Zwei Fragen, gegensätzliche Antworten
([`src/18_zentrierung.py`](../src/18_zentrierung.py)).

### Die Ankerwahl ist wirkungslos

Der Knotenplan ist nur bis auf eine gemeinsame Verschiebung eindeutig. Numerisch geprüft:
dieselbe Lösung, acht verschiedene Anker, jedes Mal exakt derselbe Zielfunktionswert von
11.805,429. Welcher Bahnhof auf :00 liegt, ist eine Frage der Darstellung.

### Welcher Bahnhof ist der zentralste?

Gemessen über die Zwischenzentralität — der Anteil aller schnellsten Verbindungen im Netz,
die über den Knoten führen — und über die mittlere Fahrzeit zum verkehrsgewichteten Rest
des Netzes.

| Bahnhof | Kanten | Halte/Tag | Zentralität | Ø Fahrzeit zum Netz |
|---|---|---|---|---|
| Frankfurt(Main)Hbf | 17 | 224,2 | **0,2862** | 109,9 min |
| Hanau Hbf | 9 | 43,5 | 0,2570 | 105,9 min |
| Mannheim Hbf | 14 | 157,2 | 0,2499 | 129,4 min |
| Fulda | 9 | 98,3 | 0,2446 | 105,6 min |
| Hannover Hbf | 15 | 221,1 | 0,2341 | 123,1 min |

Frankfurt Hbf ist der zentralste Knoten, und zwar deutlich. Hanau und Fulda liegen
geografisch noch günstiger, sind aber verkehrlich klein — Durchgangsknoten, keine Quell- und
Zielorte.

### Eine echte Zentrierung hilft

Wirksam ist die Höhergewichtung eines Knotens in der Optimierung (Faktor 6 auf seine
Kanten), für acht Kandidaten exakt gelöst.

| Prioritätsknoten | Reserve ohne | Reserve mit | Gewinn | Effekt aufs Netz |
|---|---|---|---|---|
| Frankfurt(Main)Hbf | 7,78 % | 4,73 % | **+3,05 Pp** | −0,47 Pp |
| Köln Hbf | 13,60 % | 10,75 % | +2,85 Pp | +0,05 Pp |
| Nürnberg Hbf | 5,48 % | 3,09 % | +2,39 Pp | −0,03 Pp |
| Hannover Hbf | 7,17 % | 5,20 % | +1,97 Pp | −0,23 Pp |
| Kassel-Wilhelmshöhe | 1,64 % | 0,25 % | +1,39 Pp | −0,09 Pp |
| Fulda | 4,06 % | 2,68 % | +1,38 Pp | +0,33 Pp |
| Berlin Hbf | 1,61 % | 1,36 % | +0,25 Pp | +0,12 Pp |
| Mannheim Hbf | 5,85 % | 5,83 % | +0,02 Pp | +0,08 Pp |

Frankfurt Hbf ist der klare Sieger — und das übrige Netz wird dabei minimal besser. Kein
Zufall: Weil Frankfurt der zentralste Knoten ist, läuft seine Optimierung mit der des
Gesamtnetzes weitgehend gleich. Bei Berlin und Mannheim bringt Zentrierung nichts, weil
deren Kanten im freien Optimum schon nahezu perfekt liegen.

*(Werte aus dem 64-Knoten-Modell, in dem die Studie durchgeführt wurde.)*

### Ein grobes Knotenraster ist keine Lösung

| Variante | Ø Reserve | Sollband |
|---|---|---|
| freie Knotenminuten | 7,7 % | 60,1 % |
| Fünf-Minuten-Raster | 15,5 % | 30,1 % |
| Raster :00 / :15 | **35,7 %** | 20,7 % |

Deutschland hat keine dominante Achse, sondern ein Maschennetz mit sehr unterschiedlichen
Kantenlängen. Die Schweiz kann ihr Raster halten, weil ihre Knotenabstände von Anfang an auf
Halbstundenschritte gebaut wurden. In Deutschland müssen die Knotenminuten frei bleiben.

---

## Was Streckenausbau brächte

Zum Vergleich wurde dieselbe Optimierung mit erlaubter Beschleunigung gelöst.

| Variante | Kanten mit Verkürzung | Ø Reserve |
|---|---|---|
| neubaufrei | 0 | 7,68 % |
| bis 3 min Verkürzung erlaubt | 11 | 7,01 % |
| bis 6 min Verkürzung erlaubt | 16 | 6,97 % |

Die Verdopplung des erlaubten Ausbaus bringt noch vier Hundertstel eines Prozentpunkts. Der
Nutzen von Streckenausbau für die Taktbildung ist nach wenigen Minuten erschöpft — was den
Takt trägt, ist die Ordnung der Fahrplanlagen, nicht die Geschwindigkeit.

*(Werte aus dem 64-Knoten-Modell mit einseitiger Bindung.)*
