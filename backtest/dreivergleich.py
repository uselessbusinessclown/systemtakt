#!/usr/bin/env python3
"""Knotengüte an den 20 Vollknoten in drei Fahrplänen — heute, unser Plan, Gutachterentwurf.

Bislang standen zwei Werte nebeneinander: unser gerechneter Plan mit 100 % (trivial, er
ist aus den Knotenminuten konstruiert) und der Gutachterentwurf mit 53 %. Der fehlende
dritte Wert ist der wichtigste: Was leistet der **heutige** Fahrplan?

Ohne ihn ist der Vergleich nicht einzuordnen. Liegt heute schon bei 50 %, dann kauft der
Gutachterentwurf mit erheblichem Ausbau keine bessere Taktbindung. Liegt heute deutlich
darunter, ist auch sein loser Takt ein Fortschritt.

Angewandt wird derselbe Schätzer wie in knotenanalyse.py, auf dieselben 20 Bahnhöfe, mit
demselben Fenster. Der heutige Fahrplan kommt aus stop_time/stop_station der eigenen
Datenbank, also aus dem GTFS-Fernverkehrsfeed.

Aufruf:  dreivergleich.py <bahn.db> <dtakt.db>
"""
import collections
import sqlite3
import sys

from knotenanalyse import KNOTEN_ZUORDNUNG, dtakt_halte, knotenminute, unsere_halte

TAKT = 30


def heutige_halte(db, takt):
    """Ankunfts- und Abfahrtsminuten des heutigen Fernverkehrs je Bahnhof.

    Züge, die an weniger als der Hälfte der 31 ausgewerteten Tage fahren, bleiben außen
    vor. Sonst bewerten Entlastungs- und Wochenendleistungen den Knoten mit, die mit dem
    Grundtakt nichts zu tun haben und ihn systematisch schlechter aussehen lassen.
    """
    con = sqlite3.connect(db)
    s2st = dict(con.execute("SELECT stop_id, station_id FROM stop_station"))
    name = dict(con.execute("SELECT station_id, name FROM station"))
    vt = dict(con.execute("SELECT trip_id, verkehrstage FROM trip_summary"))

    daten = collections.defaultdict(lambda: ([], []))
    for tid, sid, arr, dep in con.execute("SELECT trip_id, stop_id, arr, dep FROM stop_time"):
        st = name.get(s2st.get(sid))
        if st is None:
            continue
        # Züge mit weniger als der Hälfte der Verkehrstage bleiben außen vor
        if (vt.get(tid) or 0) < 15:
            continue
        an, ab = daten[st]
        if arr is not None:
            an.append((arr // 60) % takt)
        if dep is not None:
            ab.append((dep // 60) % takt)
    return daten


def main():
    bahn_db, dtakt_db = sys.argv[1], sys.argv[2]

    heute = heutige_halte(bahn_db, TAKT)
    unser = unsere_halte(bahn_db, TAKT)
    dtakt = dtakt_halte(dtakt_db, TAKT)

    print(f"Knotengüte im 30-Minuten-Raster, Fenster ±8 min, an den 20 Vollknoten\n")
    print(f"{'Knoten':<22}{'heute':>16}{'unser Plan':>14}{'Gutachter':>13}")
    print("─" * 65)

    summen = {"heute": [], "unser": [], "dtakt": []}
    for name, codes in KNOTEN_ZUORDNUNG.items():
        h_an, h_ab = heute.get(name, ([], []))
        u_an, u_ab = unser.get(name, ([], []))
        d_an, d_ab = dtakt.get(codes[0], ([], []))

        h_m, h_g, h_n = knotenminute(h_an, h_ab, TAKT)
        u_m, u_g, _ = knotenminute(u_an, u_ab, TAKT)
        d_m, d_g, _ = knotenminute(d_an, d_ab, TAKT)
        for schluessel, wert in (("heute", h_g), ("unser", u_g), ("dtakt", d_g)):
            summen[schluessel].append(wert)

        print(f"{name:<22}{h_m:>7}' {h_g:>6.0%}{u_m:>7}' {u_g:>4.0%}{d_m:>7}' {d_g:>4.0%}")

    print("─" * 65)
    m = {k: sum(v) / len(v) for k, v in summen.items()}
    print(f"{'Mittel':<22}{m['heute']:>15.0%}{m['unser']:>13.0%}{m['dtakt']:>12.0%}")
    print(f"\nDie 100 % unseres Plans sind kein Qualitätsnachweis — er ist aus den")
    print(f"Knotenminuten konstruiert. Aussagekräftig ist der Abstand zwischen den")
    print(f"beiden anderen Spalten: {m['dtakt'] - m['heute']:+.0%} Punkte.")


if __name__ == "__main__":
    main()
