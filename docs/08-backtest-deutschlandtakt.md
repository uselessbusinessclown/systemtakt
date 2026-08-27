# Backtest gegen den offiziellen Deutschlandtakt

Diese Untersuchung rechnet einen integralen Taktfahrplan von Grund auf und trifft daraus
Aussagen über Knotenzahl, Knotenminuten und Infrastrukturbedarf. Geprüft wurden diese
Aussagen bislang nur gegen sich selbst — gegen die eigene Zielfunktion, die eigene
Kantenbasis, das eigene Reisezeitmodell.

Es gibt eine unabhängige Gegenprobe. Das Bundesministerium für Digitales und Verkehr
musste den **3. Gutachterentwurf des Zielfahrplans Deutschlandtakt** nach dem
Informationsfreiheitsgesetz maschinenlesbar herausgeben. Das ist ein vollständiger
Zielfahrplan für dasselbe Netz, erstellt von Gutachtern mit Betriebssimulation und
Infrastrukturplanung im Rücken — 698 MB railML mit Fern-, Nah- und Güterverkehr.

Der Weg von der Rohdatei zum Vergleich stammt aus
[schaerfo/dtakt-fahrplan](https://github.com/schaerfo/dtakt-fahrplan) (MIT): railML
einlesen, nach GTFS wandeln, mit [MOTIS](https://github.com/motis-project/motis) routen.
Nachvollziehbar über [`backtest/`](../backtest/), `make -C backtest alle`.

---

## Was geprüft wurde und was dabei herauskam

| Prüfung | Ergebnis |
|---|---|
| Treffen unsere Knotenminuten die des Gutachterentwurfs? | **Nein.** Nach der besten gemeinsamen Verschiebung bleiben 7,0 min mittlere Abweichung — bei zufälliger Lage wären 7,5 min zu erwarten. |
| Ist der Gutachterentwurf überhaupt ein strenger Vollknoten-Fahrplan? | **Nein.** An unseren 20 Knoten erreicht er 53 % Knotengüte, unser Plan 100 %. |
| Wie stehen die Reisezeiten zueinander? | Der Gutachterentwurf ist auf 1.082 von 1.140 Relationen schneller, im Mittel um **44 Minuten**. |
| Liegt das an unserer Taktdisziplin? | **Nein.** Auf umsteigefreien Relationen, wo Knotendisziplin keine Rolle spielt, beträgt der Rückstand schon 35 Minuten. Unser Plan hat sogar **weniger** Umstiege (0,55 gegen 0,68). |
| Woran liegt es dann? | An der Infrastruktur. Der Gutachterentwurf befährt **11 von 16** vergleichbaren Netzkanten schneller, als heute je gefahren wurde — in Summe 107 Minuten. Genau das schließt unsere Nebenbedingung aus. |

**Die Kernaussage der Studie wird durch den Backtest nicht widerlegt, sondern beziffert.**
Ein integraler Takt ohne Neubau ist möglich — er kostet gegenüber dem offiziellen
Zielfahrplan rund 44 Minuten mittlere Reisezeit zwischen den großen Knoten. Diese Zahl
fehlte bisher.

---

## Verfahren

### Einlesen

Der Gutachterentwurf liegt als eine railML-2.2-Datei von 698 MB vor. Der Parser von
schaerfo baut daraus ein vollständiges DOM und braucht dafür rund 10 GB Arbeitsspeicher;
[`backtest/dtakt_ingest.py`](../backtest/dtakt_ingest.py) liest dieselbe Datei streamend
in **19 Sekunden** mit vernachlässigbarem Speicherbedarf. Ergebnis sind 16.188
Betriebsstellen, 65.769 Zugteile und 814.758 Halte.

Der Gemeinschaftspatch, den schaerfo mitlädt, ist für die Wohlgeformtheit nicht nötig —
die Datei parst auch ohne ihn. Er behebt rund 360 doppelte `trainPart`-Kennungen und
bleibt deshalb im Ablauf.

### Bahnhöfe zuordnen

Der Gutachterentwurf führt DB-interne Kurznamen: „Hmb-Harburg", „Mü-Pasing",
„Ksl-Wilhelmshöhe", „Lu Wittenberg". Ein Namensabgleich ordnet damit nur 19 unserer 20
Vollknoten zu und trifft im Netz insgesamt nur 181 von 266 Fahrplanbahnhöfen. Die
Zuordnung der 20 Knoten ist deshalb über **RL100-Codes** geprüft und in
[`backtest/knotenanalyse.py`](../backtest/knotenanalyse.py) fest hinterlegt.

Dabei fiel auf, dass der Gutachterentwurf zwei unserer Knoten nach Bahnsteigebene trennt:

* **Berlin Hbf** als `BL` (444 FV-Halte) und `BLS` (180) — Nord-Süd-Ebene und Stadtbahn
* **Frankfurt (Main) Hbf** als `YFFF` „Fernbahn" (360) und `FF` (192)

Unser Modell behandelt beide als je einen Knoten mit einer Knotenminute. Der Name
„Fernbahn" für die Betriebsstelle, die zwei Drittel der Frankfurter Fernverkehrshalte
trägt, legt nahe, dass der Gutachterentwurf dort den geplanten Fernbahntunnel unterstellt
— belegen lässt sich das aus den Fahrplandaten allein nicht.

### Knotenminuten ableiten

Beide Fahrpläne werden mit **demselben** Schätzer ausgewertet. Für jede Kandidatenminute
wird gezählt, wie viele Halte in das Knotenmuster passen (Ankunft davor, Abfahrt danach,
Fenster ±8 min). Bei einem sauber gebauten Knoten erreichen alle Minuten zwischen der
letzten Ankunft und der ersten Abfahrt denselben Höchstwert — genommen wird die **Mitte**
dieses Plateaus.

Diese Feinheit entscheidet über die Brauchbarkeit des ganzen Vergleichs. Ein erster
Anlauf griff den Rand des Plateaus ab und verschob damit jeden Knoten systematisch um ein
bis zwei Minuten; er reproduzierte nur 4 unserer 20 veröffentlichten Knotenminuten. Der
Vergleich hätte dann den eigenen Schätzfehler mitgemessen.

**Eichprobe:** Der endgültige Schätzer findet **20 von 20** veröffentlichten
Knotenminuten aus unserem eigenen Fahrplan exakt wieder. Erst danach ist eine Aussage
über den Gutachterentwurf zulässig.

---

## Befund 1 — Die Knotenminuten stimmen nicht überein

| Knoten | unser | Gutachterentwurf | Knotengüte dort |
|---|---:|---:|---:|
| Münster (Westf) Hbf | :15 | :00 | 92 % |
| Dresden Hbf | :15 | :00 | 75 % |
| Erfurt Hbf | :16 | :00 | 73 % |
| Würzburg Hbf | :29 | :00 | 69 % |
| Karlsruhe Hbf | :27 | :02 | 61 % |
| Leipzig Hbf | :00 | :14 | 58 % |
| Köln Hbf | :29 | :15 | 57 % |
| Nürnberg Hbf | :26 | :00 | 55 % |
| Bremen Hbf | :15 | :15 | 54 % |
| Mannheim Hbf | :00 | :00 | 53 % |
| München Hbf | :24 | :16 | 52 % |
| Hannover Hbf | :29 | :00 | 50 % |
| Stuttgart Hbf | :17 | :00 | 48 % |
| Duisburg Hbf | :13 | :02 | 41 % |
| Frankfurt (Main) Hbf | :14 | :22 | 38 % |
| Hamburg Hbf | :15 | :08 | 36 % |
| Kassel-Wilhelmshöhe | :29 | :16 | 36 % |
| Dortmund Hbf | :00 | :15 | 35 % |
| Berlin Hbf | :00 | :00 | 35 % |
| Fulda | :14 | :13 | 34 % |

Der Knotenplan ist nur bis auf eine gemeinsame Verschiebung eindeutig — das ist Ergebnis 3
der Studie und numerisch nachgewiesen. Also darf man die beste Verschiebung suchen und
erst danach vergleichen. Sie beträgt +13 Minuten und führt zu **7,0 min mittlerer
Abweichung**; bei völlig unabhängiger Lage wären 7,5 min zu erwarten. Sieben der zwanzig
Knoten liegen danach innerhalb von drei Minuten, dreizehn nicht.

Das ist kein Beleg für Übereinstimmung. Aber es ist auch kein Beleg gegen unseren Plan,
denn:

## Befund 2 — Der Gutachterentwurf ist kein strenger Vollknoten-Fahrplan

An unseren 20 Knoten erreicht er im 30-Minuten-Raster **53 % Knotengüte**, unser Plan
erreicht 100 %. Letzteres ist trivial — unser Fahrplan ist aus den Knotenminuten
konstruiert, die Güte ist Definition, kein Qualitätsnachweis. Aussagekräftig ist nur der
Wert des Gutachterentwurfs.

Die naheliegende Gegenerklärung wurde geprüft und **widerlegt**: Ein integraler
Taktfahrplan bindet vor allem Fern- an Nahverkehr, und unsere Auswertung filtert den
Nahverkehr weg — sieht sie den Knoten deshalb gar nicht? Nimmt man Nah- und S-Bahn-Verkehr
hinzu, wird die Knotenstruktur an unseren 20 Bahnhöfen nicht schärfer, sondern **unschärfer**
(39 % statt 53 %). Im 60-Minuten-Raster fällt sie weiter auf 23 %.

Die Bahnhöfe mit der schärfsten Knotenstruktur im Gutachterentwurf sind überwiegend
kleine mit wenigen Linien, bei denen wenige Halte trivial zusammenfallen — Berlin
Ostbahnhof, Flughafen Leipzig/Halle, Magdeburg Hbf, Basel Bad Bf. Unter den großen Knoten
sticht allein Münster Hbf mit 92 % heraus.

**Der offizielle Zielfahrplan verfolgt also gar keinen strengen integralen Takt an den
großen Knoten.** Das ist zunächst eine Feststellung über ihn, nicht über uns. Wer den
Fernverkehr für die Leitschicht hält — und die Verspätungsausbreitung spricht dafür,
siehe unten —, liest diesen Befund als Kritik am Gutachterentwurf: Er lässt genau die
Schicht lose laufen, deren Störungen landesweit kaskadieren.

Beide Pläne liegen an verschiedenen Punkten derselben Abwägung, strenge Knoten gegen kurze
Reisezeit, und die Knotenzahl-Studie in [`02-methodik.md`](02-methodik.md) vermisst diese
Abwägung. Der Gutachterentwurf zeigt, wo erfahrene Planer sie ansetzen — er begründet
nicht, warum dort.

## Befund 3 — Der Reisezeitrückstand ist Infrastruktur, nicht Taktdisziplin

Beide Fahrpläne wurden als GTFS exportiert und mit derselben Routing-Engine (MOTIS 2.11)
gefahren: alle 380 geordneten Paare der 20 Vollknoten zu drei Tageszeiten, 1.140 Anfragen
je Fahrplan, alle in beiden lösbar.

| Maß | unser Plan | Gutachterentwurf | Differenz |
|---|---:|---:|---:|
| Fahrzeit, Mittel | 203,8 min | 159,6 min | −44,2 min |
| Fahrzeit, Median | 201,0 min | 160,0 min | −41,0 min |
| Umstiege, Mittel | 0,55 | 0,68 | +0,13 |

Der Gutachterentwurf ist auf 1.082 Relationen schneller, unser Plan auf 54 — fast alle
davon im Raum Münster/Hannover. Bei den Umstiegen ist es umgekehrt: **unser Plan kommt
auf 281 Relationen mit weniger Umstiegen aus, der Gutachterentwurf nur auf 157.** Die
Knotendisziplin leistet also, was sie soll.

Die Zerlegung des Rückstands:

| Relationsart | Fälle | unser | Gutachter | Differenz |
|---|---:|---:|---:|---:|
| beide umsteigefrei | 411 | 143,9 min | 108,6 min | −35,4 min |
| gemischt | 303 | 216,0 min | 169,8 min | −46,3 min |
| beide mit Umstieg | 426 | 252,8 min | 201,5 min | −51,2 min |

Auf **umsteigefreien** Relationen gibt es keinen Anschluss, keine Knotenwartezeit, keine
Taktdisziplin — und trotzdem 35 Minuten Rückstand. Vier Fünftel der Differenz sind also
reine Fahrzeit. Nur der Rest kann überhaupt mit Knoten und Umstiegen zu tun haben.

Die reine Fahrzeit kommt daher:

| Netzkante | heute schnellstens | Gutachterentwurf | Differenz |
|---|---:|---:|---:|
| Würzburg – Nürnberg | 51 min | 29 min | −22 |
| Frankfurt – Kassel-Wilhelmshöhe | 85 min | 65 min | −20 |
| Frankfurt – Fulda | 54 min | 35 min | −19 |
| Berlin – Hannover | 94 min | 81 min | −13 |
| Erfurt – Nürnberg | 68 min | 56 min | −12 |
| Mannheim – Stuttgart | 36 min | 31 min | −5 |
| Frankfurt – Mannheim | 34 min | 29 min | −5 |
| Nürnberg – München | 65 min | 61 min | −4 |
| Karlsruhe – Stuttgart | 36 min | 32 min | −4 |
| Kassel-Wilhelmshöhe – Hannover | 55 min | 53 min | −2 |
| Münster – Dortmund | 27 min | 26 min | −1 |

**11 von 16 vergleichbaren Kanten befährt der Gutachterentwurf schneller, als heute je
gefahren wurde** — in Summe 107 Minuten. Das ist keine bessere Fahrplankonstruktion, das
ist unterstellte Infrastruktur: die Neubaustrecke Würzburg–Nürnberg, der Ausbau
Hanau–Fulda, die Ertüchtigung Berlin–Hannover auf 300 km/h.

Nur drei Kanten fährt er langsamer als heute möglich — Erfurt–Leipzig um 4 Minuten,
Fulda–Würzburg und Kassel–Fulda um je eine.

**Ergebnis 1 der Studie** („Der Takt braucht keinen Neubau") bleibt damit bestehen: Für
die *Taktbildung* ist Neubau entbehrlich, die Fahrzeitreserve liegt auch ohne ihn unter
dem schweizerischen Zielwert. Der Backtest ergänzt, was die Studie nicht beziffert hat:
Für die *Reisezeit* ist er es nicht. Der offizielle Zielfahrplan kauft mit erheblichem
Ausbau rund 44 Minuten. Beide Aussagen widersprechen sich nicht — sie beantworten
verschiedene Fragen.

---

## Was der Backtest an unserer Methodik offenlegt

**Dass wir nur den Fernverkehr binden, ist kein Fehler.** Ein erster Entwurf dieses
Blattes hat das als Methodiklücke geführt: Ein integraler Taktfahrplan lebe überwiegend
von Anschlüssen zwischen Fern- und Nahverkehr, unsere Knotenminuten seien deshalb gegen
die falsche Menge optimiert. Das war falsch, und die Daten des Gutachterentwurfs zeigen
warum.

Der Fernverkehr ist die **Leitschicht**, der Nahverkehr wird auf sie geplant — so hält es
auch die Schweiz, deren Knotenzeiten aus dem Fernverkehrssystem stammen. Der Grund ist die
Ausbreitung von Verspätung, und die lässt sich auszählen:

| | Vollknoten je Zuglauf | berührt zwei oder mehr | Höchstwert |
|---|---:|---:|---:|
| Fernverkehr (2.532 Läufe) | 2,63 | 57 % | 8 |
| Nahverkehr (50.473 Läufe) | 0,32 | 3 % | 3 |

Ein Fernverkehrslauf ist eine Kette durch das Netz: Verspätung wandert von Knoten zu
Knoten quer durchs Land, und der Umlauf trägt sie am Abend an das andere Ende der
Republik. Ein Nahverkehrslauf berührt in 97 % der Fälle höchstens einen Vollknoten — dort
endet die Ausbreitung, weil der Fernverkehr nach den üblichen Anschlussregeln nicht auf
ihn wartet. Die Asymmetrie ist der Grund für die Hierarchie, nicht ihr Nebeneffekt.

Eine Ausnahme verdient Beachtung: Der **Rhein-Ruhr-Express** kommt auf 2,36 Vollknoten je
Lauf und verhält sich damit wie Fernverkehr. Zwischen Duisburg, Dortmund, Münster und Köln
verschwimmt die Hierarchie; wer die Knotenminuten dort setzt, sollte ihn mitrechnen.

**Was dennoch bleibt: die Kapazität.** Wer die Knotenminute setzt, ist eine Frage der
Hierarchie. Wer im Knotenfenster am Bahnsteig steht, ist es nicht. Im Gutachterentwurf
sind **52 % aller Halte im Knotenfenster Nahverkehr** — auf jeden Fernverkehrshalt kommt
1,1 Nahverkehrshalte am selben Bahnhof zur selben Zeit, und zwar gerade deshalb, weil der
Nahverkehr auf den Knoten hin geplant ist.

| Knoten | FV im Fenster | NV im Fenster | NV-Anteil |
|---|---:|---:|---:|
| Münster (Westf) Hbf | 264 | 672 | 72 % |
| Dresden Hbf | 144 | 360 | 71 % |
| Bremen Hbf | 156 | 348 | 69 % |
| Kassel-Wilhelmshöhe | 192 | 384 | 67 % |
| Köln Hbf | 414 | 816 | 66 % |
| … | | | |
| München Hbf | 336 | 156 | 32 % |
| Frankfurt (Main) Hbf Fernbahn | 276 | 24 | 8 % |
| **zusammen** | **5.862** | **6.372** | **52 %** |

[`20_kapazitaet.py`](../src/20_kapazitaet.py) schätzt den Gleisbedarf je Knotenfenster
allein aus Fernverkehrshalten. Der tatsächliche Bedarf liegt damit rund beim Doppelten.
[`06-grenzen.md`](06-grenzen.md) nennt die Kapazitätsaussagen bereits eine
Grobabschätzung — der Backtest beziffert, in welche Richtung sie danebenliegt, und es ist
die unangenehme.

Der niedrige Wert für Frankfurt ist dabei kein Ausreißer, sondern eine Bestätigung: `YFFF`
ist die getrennte Fernbahn-Betriebsstelle, dort hält kein Nahverkehr.

**Unser Fahrplan war bisher nicht routingfähig.** Er lag als PDF, Excel und SQLite vor,
aber in keinem Format, das eine Routing-Engine lesen kann. Damit war keine einzige
Reisezeitaussage der Studie unabhängig prüfbar.
[`backtest/export_gtfs.py`](../backtest/export_gtfs.py) schließt das; der Export ist gegen
die Datenbank verifiziert (Hannover–Frankfurt: 158 Minuten in beiden).

**Der Frankfurter Sonderfrage fehlt eine Variante.** [`05-sonderfragen.md`](05-sonderfragen.md)
prüft Hauptbahnhof gegen Flughafen-Fernbahnhof. Der Gutachterentwurf führt eine dritte
Betriebsstelle, „Frankfurt (Main) Hbf Fernbahn", die zwei Drittel seiner Frankfurter
Fernverkehrshalte trägt.

---

## Grenzen dieses Vergleichs

* **Nur 16 Kanten sind direkt vergleichbar.** Verlangt wurde ein Abschnitt ohne
  Zwischenhalt zwischen zwei unserer 20 Knoten in beiden Fahrplänen. Die aufsummierten
  107 Minuten sind deshalb eine Untergrenze der unterstellten Beschleunigung.
* **Der Gutachterentwurf fährt mehr.** 2.532 Züge auf 188 Linien gegen unsere 1.700 auf
  84. Ein Teil des Reisezeitvorsprungs stammt aus dem dichteren und direkteren
  Liniennetz, nicht aus der Infrastruktur. Die Zahlen oben nennen deshalb die Fahrzeit
  ohne anfängliche Wartezeit; über die Türzeit gerechnet wäre der Abstand mit 57 Minuten
  noch größer, aber zugunsten des dichteren Angebots verzerrt.
* **197 der 433 Bahnhöfe im GTFS des Gutachterentwurfs haben keine gesicherte Koordinate.**
  Sie bekommen weit auseinanderliegende Platzhalter. Da MOTIS hier ohne Straßenrouting
  läuft, geht die Lage nicht in die Reisezeit ein — wohl aber entfallen an diesen
  Bahnhöfen Fußwegumstiege, was den Gutachterentwurf leicht benachteiligt.
* **Der Gutachterentwurf ist von 2020** und bildet einen Zielzustand ab, unsere Studie
  wertet den Fahrplan von August 2026 aus. Die „heutigen Bestzeiten" sind daher jünger als
  der Zielfahrplan; für Kanten, die seit 2020 ausgebaut wurden, unterschätzt der Vergleich
  die unterstellte Beschleunigung.
* **Kein Nahverkehr in unserem Fahrplan.** Die Routing-Ergebnisse beider Seiten sind auf
  Fernverkehr beschränkt, damit der Vergleich fair bleibt. Ein echter Reisender hätte im
  Gutachterentwurf zusätzlich den Nahverkehr.
