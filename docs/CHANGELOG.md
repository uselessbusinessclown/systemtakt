# Änderungsprotokoll

Diese Untersuchung ist in vier Fassungen entstanden. Drei davon mussten inhaltliche
Ergebnisse der vorherigen widerrufen. Das Protokoll hält fest, was wann falsch war und
warum — die verworfenen Fassungen liegen unter [`src/legacy/`](../src/legacy/).

---

## Fassung 4 — 20 Vollknoten, beidseitige Bindung, Fahrplan

**Neu**
* Vollständiger Tagesfahrplan: 1.700 Züge, 12.876 Halte, als Kursbuch und Bahnhofsfahrpläne
* Knotenbindung in **beiden** Fahrtrichtungen mit richtungsgetrennten Zeitfenstern
* Studie über die Zahl der Vollknoten (16 bis 64)
* Kantenbasis auf die **Systemfahrzeit der Linien** umgestellt statt auf die Bestzeit eines
  Einzelzuges

**Korrigiert**

*Die Zahl der Vollknoten war viel zu hoch.* Die Fassungen 1 bis 3 machten alle 64 in Frage
kommenden Bahnhöfe zu Vollknoten. Erst der Bau des Fahrplans machte sichtbar, was das
kostet: Ein ICE von Berlin nach Köln sammelte 90 Minuten Wartezeit an, ohne dass irgendwer
davon einen Anschluss hatte. Mit 20 Vollknoten sinkt die mittlere Reisezeitverlängerung von
38 auf 17 Minuten.

*Die Knotenbindung galt nur in einer Richtung.* Das Modell der Fassungen 1 bis 3 prüfte die
Taktbedingung je Kante nur in der gespeicherten Orientierung. In der Gegenrichtung lagen die
Halte damit außerhalb des Knotenfensters — die Anschlüsse hätten in einer Richtung nicht
bestanden. Die Behauptung „Symmetrieminute 0" in den Fassungen 1 bis 3 war ebenfalls falsch:
Eine globale Symmetrieachse verlangt, dass alle Knotenminuten auf einem Viertelstundenraster
liegen, und das kostet 35,7 % Fahrzeitreserve.

*Die Kantenbasis war zu optimistisch.* Als Basiszeit diente die schnellste je gefahrene
Zeit. Ein Linienzug mit einem Zwischenhalt braucht mehr, sprang deshalb um volle 30 Minuten
und verlängerte seine Reisezeit unnötig.

---

## Fassung 3 — exakt gelöst, neubaufrei

**Neu**
* Formulierung als gemischt-ganzzahliges Programm, gelöst mit HiGHS — Optimalität bewiesen
* Harte Nebenbedingung: keine Fahrzeitverkürzung unter die heutige Zeit
* Vergleichsvarianten mit erlaubtem Ausbau (3 und 6 Minuten) und mit grobem Knotenraster
* Zentralitätsanalyse und Zentrierungsstudie

**Korrigiert**

*Der ausgewiesene Infrastrukturbedarf war ein Artefakt.* Die Fassungen 1 und 2 nannten fünf
bis neun Netzkanten, die beschleunigt werden müssten — darunter Fulda–Erfurt und
Wuppertal–Dortmund. Die exakte Lösung zeigt: keine einzige. Das simulierte Ausglühen der
Vorfassungen lag je nach Zufallsstartwert bis zu 18 Prozent über dem Optimum und erzeugte
den Beschleunigungsbedarf selbst.

---

## Fassung 2 — Frankfurt-Sonderfrage

**Neu**
* Prüfung, ob Fernverkehr vom Frankfurter Hauptbahnhof an den Flughafen-Fernbahnhof
  verlagert werden sollte (Ergebnis: nein, in allen geprüften Varianten)
* Gleisbelegungsrechnung beider Bahnhöfe

**Korrigiert**

*Der Knotenplan war suboptimal.* Ein längerer Optimierungslauf unterbot die erste Lösung um
14 Prozent und senkte die Zahl der Kanten mit Beschleunigungsbedarf von neun auf fünf. Erste
Warnung, dass die Heuristik nicht konvergierte — die Konsequenz wurde erst in Fassung 3
gezogen.

---

## Fassung 1 — Datenbank und erster Knotenplan

**Neu**
* Datenbank aus dem DELFI/gtfs.de-Fernverkehrsfeed: 567 Bahnhöfe, 96 Linien, 5.589 Trassen
* Sprinter-Klassifikation über Korridore und Fahrzeit-Ranking, kalibriert an bahn.de
* Erster Knotenplan mit simuliertem Ausglühen, 64 Knoten
* Zielliniennetz in zwei Szenarien, Kapazitätsabschätzung, Betriebsleistung

---

## Was daraus zu lernen ist

Drei Fehlerklassen, alle drei nicht in den Daten, sondern im Modell:

1. **Die Heuristik gab vor, ein Ergebnis zu sein.** Ein Optimierer, der bei jedem längeren
   Lauf ein besseres Ergebnis findet, ist nicht konvergiert. Das war früh sichtbar und
   wurde zu spät ernst genommen.
2. **Ein halb modelliertes Symmetrieproblem.** Die Knotenbindung nur einer Richtung zu
   prüfen wirkt wie eine Vereinfachung, macht aber die Kernaussage — jeder Anschluss in
   jede Richtung — unhaltbar.
3. **Ein ungeprüfter Parameter.** Dass alle 64 Bahnhöfe Vollknoten sein sollen, war nie
   entschieden, sondern nur nie hinterfragt. Es war der teuerste Freiheitsgrad im ganzen
   Modell.

Alle drei wurden erst sichtbar, als aus dem Konzept ein konkreter Fahrplan werden musste.
Das ist ein Argument dafür, Konzepte früh auszurollen.
