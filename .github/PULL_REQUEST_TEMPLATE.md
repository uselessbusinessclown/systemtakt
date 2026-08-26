## Worum es geht

<!-- Ein bis drei Sätze. Bei einer Ergebniskorrektur: welche Aussage sich ändert. -->

## Art der Änderung

- [ ] Korrektur eines Ergebnisses (Zahl oder Aussage ändert sich)
- [ ] Datenfehler (Bahnhof, Linie, Sprinter, Fahrzeit)
- [ ] Reproduzierbarkeit (Pipeline läuft wieder oder läuft weiter)
- [ ] Dokumentation
- [ ] Aufräumen ohne inhaltliche Wirkung

## Prüfungen

```bash
python -m compileall -q src && python tools/check_bootstrap.py && python tools/check_links.py
```

- [ ] durchgelaufen
- [ ] `ruff check src` durchgelaufen (falls installiert)

## Wenn sich ein Ergebnis ändert

- [ ] `docs/CHANGELOG.md` ergänzt — mit der Angabe, was vorher falsch war
- [ ] Betroffene Zahlen in `README.md` und unter `docs/` nachgezogen
- [ ] Die verworfene Fassung liegt unter `src/legacy/`, nicht im Papierkorb

## Wenn ein Skript hinzukommt

- [ ] Nächste freie Nummer in `src/`
- [ ] Eintrag im `Makefile`
- [ ] Zeile in der Tabelle in `src/README.md`
- [ ] Pfade ausschließlich über `src/lib/paths.py`
