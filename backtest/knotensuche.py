#!/usr/bin/env python3
"""Sucht Taktknoten im Gutachterentwurf, ohne unsere Knotenwahl vorauszusetzen.

Die Frage ist nicht nur, ob der Deutschlandtakt unsere 20 Knotenminuten trifft,
sondern zuerst: Hat er überhaupt Vollknoten — und wo? Dafür wird für jeden Bahnhof
mit genügend Halten die Knotengüte bestimmt, in vier Varianten:

    Verkehr:  nur Fernverkehr  /  Fern- und Nahverkehr zusammen
    Raster:   30 Minuten       /  60 Minuten

Der Vergleich beider Verkehrsarten prüft die naheliegendste Gegenerklärung für einen
schwachen Befund im Fernverkehr: Ein integraler Taktfahrplan bindet vor allem FV an NV.
Wer nur den Fernverkehr betrachtet, sieht den Knoten dann womöglich gar nicht.

Aufruf:  knotensuche.py <dtakt.db> <ziel.db>
"""
import sqlite3
import sys

from knotenanalyse import KNOTEN_ZUORDNUNG, knotenminute

FV = ("A", "B", "C", "D", "F", "H")
NV = ("X", "N", "S", "RRX", "RbZ", "AS")
MINDEST_HALTE = 120


def halte(con, kategorien, takt):
    frage = f"""
      SELECT trim(s.code), s.name, st.arrival, st.departure
      FROM stop st
      JOIN station s USING(station_id)
      JOIN train_part tp USING(train_part_id)
      JOIN category c USING(category_id)
      WHERE c.code IN ({','.join('?' * len(kategorien))})
    """
    daten = {}
    for code, name, an, ab in con.execute(frage, kategorien):
        eintrag = daten.setdefault(code, ([], [], name))
        if an:
            hh, mm, _ = an.split(":")
            eintrag[0].append((int(hh) * 60 + int(mm)) % takt)
        if ab:
            hh, mm, _ = ab.split(":")
            eintrag[1].append((int(hh) * 60 + int(mm)) % takt)
    return daten


def main():
    dtakt_db, ziel_db = sys.argv[1], sys.argv[2]
    con = sqlite3.connect(dtakt_db)
    unsere_codes = {c[0] for c in KNOTEN_ZUORDNUNG.values()}

    ziel = sqlite3.connect(ziel_db)
    ziel.executescript("""
        DROP TABLE IF EXISTS knotensuche;
        CREATE TABLE knotensuche(
          verkehr TEXT, takt INT, code TEXT, name TEXT,
          minute INT, guete REAL, halte INT, unser_knoten INT,
          PRIMARY KEY(verkehr, takt, code));
    """)

    ergebnis = {}
    for bezeichnung, kategorien in (("FV", FV), ("FV+NV", FV + NV)):
        for takt in (30, 60):
            daten = halte(con, kategorien, takt)
            zeilen = []
            for code, (an, ab, name) in daten.items():
                if len(an) + len(ab) < MINDEST_HALTE:
                    continue
                m, guete, n = knotenminute(an, ab, takt)
                zeilen.append((bezeichnung, takt, code, name, m, guete, n,
                               1 if code in unsere_codes else 0))
            ziel.executemany("INSERT INTO knotensuche VALUES(?,?,?,?,?,?,?,?)", zeilen)
            ergebnis[(bezeichnung, takt)] = zeilen
    ziel.commit()

    print(f"Bahnhöfe mit mindestens {MINDEST_HALTE} Halten\n")
    print(f"{'Variante':<12}{'Bahnhöfe':>9}{'mittl. Güte':>13}{'Güte an unseren 20':>21}")
    print("─" * 56)
    for (bez, takt), zeilen in ergebnis.items():
        alle = sum(z[5] for z in zeilen) / len(zeilen)
        unsere = [z[5] for z in zeilen if z[7]]
        m_unsere = sum(unsere) / len(unsere) if unsere else 0
        print(f"{bez + ' / ' + str(takt) + ' min':<12}{len(zeilen):>9}{alle:>12.0%}{m_unsere:>20.0%}")

    for (bez, takt), zeilen in ergebnis.items():
        print(f"\n═══ {bez}, {takt}-Minuten-Raster — die 15 schärfsten Knoten ═══")
        print(f"{'Bahnhof':<26}{'Minute':>8}{'Güte':>7}{'Halte':>8}   unser?")
        for z in sorted(zeilen, key=lambda z: -z[5])[:15]:
            marke = "  ✓" if z[7] else ""
            print(f"{z[3]:<26}{z[4]:>7}'{z[5]:>6.0%}{z[6]:>8}{marke}")


if __name__ == "__main__":
    main()
