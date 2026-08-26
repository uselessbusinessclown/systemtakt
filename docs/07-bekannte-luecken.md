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

## Zwei Analyseschritte brechen an derselben Umbenennung ab

`src/19_ist_takt.py` und `src/21_sprinter_ueberholung.py` fragen weiterhin die Spalte
`t_soll` ab, die es seit Fassung 4 nicht mehr gibt:

```
sqlite3.OperationalError: no such column: t_soll
```

Beide stehen im Makefile (`make analyse` beziehungsweise `make fahrplan`). Die Reparatur
ist keine reine Umbenennung: Es muss entschieden werden, ob die Auswertung gegen `t_soll_r1`,
gegen `t_soll_r2` oder gegen beide Richtungen laufen soll. Das ist eine fachliche
Entscheidung und steht deshalb hier statt in einem stillen Fix.

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
