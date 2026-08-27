# Bekannte Lücken der Reproduktion

[`06-grenzen.md`](06-grenzen.md) benennt die **fachlichen** Grenzen: was die Untersuchung
inhaltlich nicht leistet. Dieses Blatt hält die **handwerklichen** Lücken fest — die
Stellen, an denen `make all` heute nicht durchläuft oder nur deshalb durchläuft, weil ein
Zwischenergebnis eingecheckt ist.

Die Ergebnisse selbst sind davon nicht berührt: `data/bahn.db`, die CSV-Ausleitung und
alle Dokumente unter `output/` stammen aus vollständigen Läufen. Wer sie nachrechnen will,
stößt aber auf das Folgende.

---

## Die Pipeline kann `itf_ergebnis` nicht neu aufbauen

Die Tabelle `itf_ergebnis` hält die optimierten Soll-Fahrzeiten je Netzkante. In der
mitgelieferten Datenbank hat sie das Schema der Fassung 4 — richtungsgetrennt, mit
`t_soll_r1` und `t_soll_r2`.

**Kein Skript der aktiven Pipeline erzeugt diese Tabelle.** Angelegt wird sie nur in
`src/legacy/optimize.py`, `src/legacy/rebuild.py` und `src/legacy/apply_n1.py` — und dort
im alten Schema der Fassung 3 mit einer einzigen Spalte `t_soll`. Das Skript, das die
Fassung-4-Fassung geschrieben hat, ist nicht im Repository.

Solange das so ist, ist `data/bahn.db` für diese Tabelle die einzige Quelle.

## Erledigt: die beiden Analyseschritte an der Spaltenumbenennung

`src/19_ist_takt.py` und `src/21_sprinter_ueberholung.py` fragten die Spalte `t_soll` ab,
die es seit Fassung 4 nicht mehr gibt, und brachen mit
`sqlite3.OperationalError: no such column: t_soll` ab.

Beide laufen wieder. Die offene fachliche Frage — welche der beiden Richtungszeiten gilt —
ist so entschieden: `t_soll_r1` gilt in der gespeicherten Orientierung a→b, `t_soll_r2` in
der Gegenrichtung, und der Laufweg wird richtungsrein aufsummiert. Das ist keine
Formalie: Bei 37 der 68 Kanten unterscheiden sich beide Zeiten, im Mittel um 3,6 und im
Höchstfall um 23 Minuten (Fulda–Karlsruhe: 153 gegen 130).

Dabei kam ein zweiter, schwerwiegenderer Fehler zutage. `19_ist_takt.py` dreht den
Knotenplan so, dass Berlin auf :00 liegt, und schrieb dabei die Ankunfts- und
Abfahrtsfenster pauschal mit ±3 Minuten neu. Das ist die Symmetrie der Fassung 3. Jeder
Lauf des Skripts hätte die richtungsgetrennte Knotenbindung der Fassung 4 — den
eigentlichen Fortschritt dieser Fassung — aus der Datenbank gelöscht. Die Fenster werden
jetzt aus `off_a1`/`off_d1`/`off_a2`/`off_d2` neu gebildet.

## Drei Zwischenergebnisse haben keinen Erzeuger im Repository

| Datei | wird gelesen von | erzeugt von |
|---|---|---|
| `data/zentralitaet.json` | `18_zentrierung.py` | — |
| `data/varianten.json` | `17_frankfurt_varianten.py` | — |
| `data/pesp_final.json` | — | — |

Die beiden erstgenannten sind eingecheckt, deshalb laufen 17 und 18 durch. Ein Lauf von
Grund auf könnte sie nicht herstellen. `pesp_final.json` wird von nichts mehr gebraucht.

## Zwei weitere Zwischenergebnisse kommen aus `legacy/`

`data/knotenwahl2.json` (gelesen von `12_optimize_final.py`) stammt aus
`src/legacy/run_kw2.py`, `data/zentrierung_exakt.json` (gelesen von `18_zentrierung.py`)
aus `src/legacy/run_exakt2.py`. Beide Erzeuger stehen nicht im Makefile. Die aktive
Pipeline hängt damit an Skripten, die als verworfen dokumentiert sind.

## Der Dokumentgenerator hat keine Eingabedatei

`src/web/makedoc.js` liest in der ersten Zeile `doc_data.json` aus dem Arbeitsverzeichnis.
Diese Datei liegt nicht im Repository, und kein Skript erzeugt sie. Der letzte Schritt von
`make ausgaben` scheitert deshalb:

```
Error: ENOENT: no such file or directory, open 'doc_data.json'
```

`output/Systemtakt_Fernverkehr_Deutschland.docx` ist trotzdem gültig — es stammt aus einem
Lauf, bei dem die Datei vorhanden war.

Die Node-Abhängigkeit ist inzwischen in [`src/web/package.json`](../src/web/package.json)
deklariert (`npm install` vor `node makedoc.js`); geprüft ist sie gegen `docx` 8.5 und 9.7.

## Das Dashboard wird nirgends zusammengesetzt

`src/web/dashboard.html` (133 KB) ist eingecheckt. Die Bausteine `head.part`,
`style.part`, `body.part` und `script.part` ergeben aneinandergehängt nur 58 KB — der
Zusammenbau ist also mehr als eine Verkettung, und der Schritt, der ihn leistet, fehlt.
Bis er nachgereicht ist, ist `dashboard.html` von Hand zu pflegen und die `.part`-Dateien
sind Referenz, nicht Quelle.

## Erledigt: drei Tabellen stammten aus Fassung 3

`ist_takt`, `soll_skelett` und `knoten_kapazitaet` waren seit Fassung 3 nicht neu erzeugt
worden und beschrieben einen Fahrplan mit **64** Vollknoten. Von den 20 Knotenzeiten in
`knoten_kapazitaet` stimmten genau zwei mit dem aktuellen Plan überein, und die beiden
zufällig — Berlin als Anker und Würzburg. `ist_takt` bewertete 875 Taktlagen an 63
Bahnhöfen, von denen 43 längst keine Vollknoten mehr sind.

Nach dem Neulauf: 472 Taktlagen an genau den 20 Vollknoten, 188 Zeilen Soll-Skelett, 20
Zeilen Kapazität. Der ausgewiesene Gleisbedarf ändert sich dabei nicht — er wird allein
aus den Halten je Tag abgeleitet und hängt nicht am Knotenplan.

Ebenfalls behoben: Die Taktbewertung stand in `20_kapazitaet.py` und las die Anteile aus
der gerundeten Anzeigespalte `minuten` zurück. Dadurch kamen 75 der 472 Lagen auf Anteile
über 100 %, und sechs wurden falsch eingestuft. Die Bewertung steht jetzt in
`19_ist_takt.py`, wo die Rohwerte vorliegen.

## Vorsicht: `01_build_db.py` löscht die Datenbank ohne Rückfrage

Die erste Anweisung des Skripts lautet sinngemäß „falls `data/bahn.db` existiert, lösche
sie". Wer die Skripte der Reihe nach aufruft, um zu prüfen, ob sie anlaufen, verliert
dabei den gesamten mitgelieferten Datenbestand — die Rohdaten unter `data/gtfs_fv/` liegen
nicht im Repository, ein Wiederaufbau ist ohne `make daten` also nicht möglich.

Wiederherstellen lässt sich der Stand mit `git checkout -- data/bahn.db`.

## Kleinigkeiten

* **`/tmp` fest verdrahtet.** `src/02_stations.py` liest die Staats- und
  Bundeslandgrenzen aus `/tmp/countries.geojson` und `/tmp/bl.geojson` — genau dorthin lädt
  das Makefile sie. Unter Windows läuft das nicht.
* **`make clean` räumt nicht auf.** Entfernt werden nur `data/gtfs_fv` und die
  `__pycache__`-Verzeichnisse, nicht die heruntergeladenen GeoJSON-Dateien.
* **Die Lizenz nennt keinen Rechteinhaber.** In [`LICENSE`](../LICENSE) steht
  „Copyright (c) 2026" ohne Namen.
* **Keine Tests.** Geprüft wird im CI nur, dass alles übersetzt, keine Namen undefiniert
  sind, der Pfad-Bootstrap trägt und kein Verweis in der Dokumentation tot ist. Ob die
  Optimierung das Richtige rechnet, prüft niemand automatisch — dafür steht der
  Optimalitätsnachweis von HiGHS in [`02-methodik.md`](02-methodik.md).
