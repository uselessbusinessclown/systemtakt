#!/usr/bin/env python3
"""Stellt die Routing-Ergebnisse beider Fahrpläne gegenüber.

Für jede Anfrage wird aus der Pareto-Menge, die MOTIS zurückgibt, die Reisekette mit
der frühesten Ankunft gewählt. Ausgewiesen werden zwei Maße:

  Türzeit    Ankunft minus Anfragezeitpunkt. Enthält die Wartezeit auf den ersten Zug
             und misst damit, was ein Reisender tatsächlich erlebt, der zu einer
             beliebigen Zeit am Bahnhof steht. Ein dichteres Angebot verkürzt sie,
             unabhängig von der Taktqualität.
  Fahrzeit   Reine Dauer der Reisekette ohne die anfängliche Wartezeit. Vergleicht die
             Fahrplanqualität bei gegebenem Zug und ist gegen Angebotsdichte robust.

Beide werden gebraucht: Der Gutachterentwurf fährt rund die Hälfte mehr Züge als unser
Plan, deshalb wäre ein Vergleich allein über die Türzeit zu seinen Gunsten verzerrt.

Aufruf:  vergleich.py <relationen.csv> <antworten-unser> <antworten-dtakt> <ziel.db>
"""
import csv
import json
import sqlite3
import statistics
import sys
from datetime import datetime


def zeitpunkt(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def beste(zeile, anfrage_zeit):
    """(Türzeit, Fahrzeit, Umstiege) der Kette mit der frühesten Ankunft, in Minuten."""
    antwort = json.loads(zeile)
    ketten = antwort.get("itineraries") or []
    brauchbar = []
    for k in ketten:
        start, ende = zeitpunkt(k["startTime"]), zeitpunkt(k["endTime"])
        if start < anfrage_zeit:
            continue                      # Zug ist vor der Anfrage abgefahren
        brauchbar.append((ende, start, k))
    if not brauchbar:
        return None
    ende, start, k = min(brauchbar, key=lambda x: x[0])
    tuerzeit = (ende - anfrage_zeit).total_seconds() / 60
    fahrzeit = k["duration"] / 60
    return tuerzeit, fahrzeit, k.get("transfers", 0)


def main():
    rel_pfad, unser_pfad, dtakt_pfad, ziel_db = sys.argv[1:5]

    with open(rel_pfad, encoding="utf-8") as f:
        relationen = list(csv.DictReader(f, delimiter=";"))
    unsere_zeilen = open(unser_pfad, encoding="utf-8").read().splitlines()
    dtakt_zeilen = open(dtakt_pfad, encoding="utf-8").read().splitlines()
    assert len(relationen) == len(unsere_zeilen) == len(dtakt_zeilen), "Zeilen passen nicht"

    zeilen = []
    for rel, u_zeile, d_zeile in zip(relationen, unsere_zeilen, dtakt_zeilen):
        t = zeitpunkt(f"{rel['zeit'][:0]}2026-09-02T{rel['zeit']}")
        u, d = beste(u_zeile, t), beste(d_zeile, t)
        zeilen.append((
            rel["von"], rel["nach"], rel["zeit"],
            u[0] if u else None, u[1] if u else None, u[2] if u else None,
            d[0] if d else None, d[1] if d else None, d[2] if d else None))

    con = sqlite3.connect(ziel_db)
    con.executescript("""
        DROP TABLE IF EXISTS reisezeiten;
        CREATE TABLE reisezeiten(
          von TEXT, nach TEXT, zeit TEXT,
          unser_tuer REAL, unser_fahrt REAL, unser_umstiege INT,
          dtakt_tuer REAL, dtakt_fahrt REAL, dtakt_umstiege INT);
    """)
    con.executemany("INSERT INTO reisezeiten VALUES(?,?,?,?,?,?,?,?,?)", zeilen)
    con.commit()

    beide = [z for z in zeilen if z[3] is not None and z[6] is not None]
    nur_u = sum(1 for z in zeilen if z[3] is not None and z[6] is None)
    nur_d = sum(1 for z in zeilen if z[3] is None and z[6] is not None)
    keins = sum(1 for z in zeilen if z[3] is None and z[6] is None)

    print(f"Anfragen                       {len(zeilen):>6}")
    print(f"  in beiden Fahrplänen lösbar  {len(beide):>6}")
    print(f"  nur bei uns lösbar           {nur_u:>6}")
    print(f"  nur im Gutachterentwurf      {nur_d:>6}")
    print(f"  in keinem                    {keins:>6}\n")
    if not beide:
        return

    def statistik(werte):
        return statistics.mean(werte), statistics.median(werte)

    u_tuer = [z[3] for z in beide]
    d_tuer = [z[6] for z in beide]
    u_fahrt = [z[4] for z in beide]
    d_fahrt = [z[7] for z in beide]
    u_um = [z[5] for z in beide]
    d_um = [z[8] for z in beide]

    print(f"{'Maß':<26}{'unser Plan':>13}{'Gutachter':>12}{'Differenz':>12}")
    print("─" * 63)
    for name, u, d, einheit in (
            ("Türzeit, Mittel", *statistik(u_tuer)[:1] + statistik(d_tuer)[:1], "min"),
            ("Türzeit, Median", statistics.median(u_tuer), statistics.median(d_tuer), "min"),
            ("Fahrzeit, Mittel", statistics.mean(u_fahrt), statistics.mean(d_fahrt), "min"),
            ("Fahrzeit, Median", statistics.median(u_fahrt), statistics.median(d_fahrt), "min"),
            ("Umstiege, Mittel", statistics.mean(u_um), statistics.mean(d_um), ""),
    ):
        print(f"{name:<26}{u:>10.1f} {einheit:<2}{d:>9.1f} {einheit:<2}{d - u:>+9.1f} {einheit}")

    schneller_u = sum(1 for z in beide if z[4] < z[7])
    schneller_d = sum(1 for z in beide if z[7] < z[4])
    gleich = len(beide) - schneller_u - schneller_d
    print(f"\nFahrzeit je Relation: unser Plan schneller in {schneller_u} Fällen, "
          f"Gutachterentwurf in {schneller_d}, gleichauf {gleich}")

    umst_u = sum(1 for z in beide if z[5] < z[8])
    umst_d = sum(1 for z in beide if z[8] < z[5])
    print(f"Weniger Umstiege:     unser Plan in {umst_u} Fällen, "
          f"Gutachterentwurf in {umst_d}")

    print("\nGrößte Fahrzeitvorteile des Gutachterentwurfs:")
    for z in sorted(beide, key=lambda z: z[4] - z[7], reverse=True)[:8]:
        print(f"  {z[0]:<22}→ {z[1]:<22}{z[4]:>6.0f} → {z[7]:>4.0f} min "
              f"({z[7] - z[4]:>+5.0f})  Umst. {z[5]}→{z[8]}")
    print("\nGrößte Fahrzeitvorteile unseres Plans:")
    for z in sorted(beide, key=lambda z: z[7] - z[4], reverse=True)[:8]:
        print(f"  {z[0]:<22}→ {z[1]:<22}{z[4]:>6.0f} → {z[7]:>4.0f} min "
              f"({z[7] - z[4]:>+5.0f})  Umst. {z[5]}→{z[8]}")


if __name__ == "__main__":
    main()
