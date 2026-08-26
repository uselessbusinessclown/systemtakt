#!/usr/bin/env python3
"""Ordnet die Bahnhöfe unserer Studie denen des Gutachterentwurfs zu.

Die Namen stammen aus verschiedenen Quellen — GTFS/DELFI bei uns, Viriato-Export
beim Deutschlandtakt — und schreiben sich unterschiedlich:
  „Frankfurt(Main)Hbf"   ↔  „Frankfurt (Main) Hbf Fernbahn"
  „Münster(Westf)Hbf"    ↔  „Münster Hbf"
Zugeordnet wird über einen normalisierten Namen, danach über Koordinaten, soweit
vorhanden. Ausgabe ist eine Tabelle `zuordnung` in der Backtest-Datenbank.
"""
import re
import sqlite3
import sys
import unicodedata

FV = ("A", "B", "C", "D", "F", "H")

# Zusätze, die nur eine Betriebsstelle näher bezeichnen, nicht den Ort
ZUSATZ = re.compile(
    r"\b(hbf|hauptbahnhof|fernbahn|regionalbahn|pbf|personenbahnhof|bf|bahnhof|"
    r"fernbf|tief|hoch|oben|unten|nord|sued|ost|west)\b"
)
KLAMMER = re.compile(r"\([^)]*\)")


def normalisiere(name: str) -> str:
    if not name:
        return ""
    s = name.lower()
    s = s.replace("ß", "ss")
    s = KLAMMER.sub(" ", s)
    s = ZUSATZ.sub(" ", s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s


def main():
    unser_db, dtakt_db, ziel_db = sys.argv[1], sys.argv[2], sys.argv[3]

    unser = sqlite3.connect(unser_db)
    unsere = {}
    for sid, name, lat, lon in unser.execute(
        "SELECT station_id, name, lat, lon FROM bahnhof_bedienung"
    ):
        unsere[name] = (sid, lat, lon, normalisiere(name))
    # nur Bahnhöfe, die im gerechneten Fahrplan wirklich vorkommen
    im_fahrplan = {r[0] for r in unser.execute("SELECT DISTINCT station FROM fahrplan_halt")}
    knoten = {r[0]: r[1] for r in unser.execute("SELECT name, knotenminute FROM itf_knotenzeit")}

    dt = sqlite3.connect(dtakt_db)
    dtakt = {}
    frage = f"""
      SELECT DISTINCT s.name, s.code
      FROM stop st
      JOIN station s USING(station_id)
      JOIN train_part tp USING(train_part_id)
      JOIN category c USING(category_id)
      WHERE c.code IN ({','.join('?' * len(FV))})
    """
    for name, code in dt.execute(frage, FV):
        schluessel = normalisiere(name)
        # Bei mehreren Kandidaten gewinnt der kürzere Name (die Hauptbetriebsstelle)
        if schluessel not in dtakt or len(name) < len(dtakt[schluessel][0]):
            dtakt[schluessel] = (name, code)

    ziel = sqlite3.connect(ziel_db)
    ziel.executescript("""
        DROP TABLE IF EXISTS zuordnung;
        CREATE TABLE zuordnung(
          unser_name TEXT PRIMARY KEY, unser_id TEXT, lat REAL, lon REAL,
          dtakt_name TEXT, dtakt_code TEXT, schluessel TEXT,
          im_fahrplan INT, knotenminute INT);
    """)
    zeilen, treffer = [], 0
    for name, (sid, lat, lon, schluessel) in unsere.items():
        d = dtakt.get(schluessel)
        if d:
            treffer += 1
        zeilen.append((name, sid, lat, lon, d[0] if d else None, d[1] if d else None,
                       schluessel, 1 if name in im_fahrplan else 0, knoten.get(name)))
    ziel.executemany("INSERT INTO zuordnung VALUES(?,?,?,?,?,?,?,?,?)", zeilen)
    ziel.commit()

    gesamt_fp = sum(1 for z in zeilen if z[7])
    treffer_fp = sum(1 for z in zeilen if z[7] and z[4])
    treffer_kn = sum(1 for z in zeilen if z[8] is not None and z[4])
    print(f"Bahnhöfe unserer Datenbank      {len(zeilen):>4}   zugeordnet {treffer:>4}")
    print(f"davon im gerechneten Fahrplan   {gesamt_fp:>4}   zugeordnet {treffer_fp:>4}")
    print(f"davon Vollknoten                {len(knoten):>4}   zugeordnet {treffer_kn:>4}")
    print()
    fehlend = [z[0] for z in zeilen if z[8] is not None and not z[4]]
    if fehlend:
        print("Vollknoten ohne Gegenstück im Gutachterentwurf:", ", ".join(fehlend))
    fehlend_fp = [z[0] for z in zeilen if z[7] and not z[4]]
    if fehlend_fp:
        print(f"\n{len(fehlend_fp)} Fahrplanbahnhöfe ohne Gegenstück (erste 25):")
        print("  " + ", ".join(fehlend_fp[:25]))


if __name__ == "__main__":
    main()
