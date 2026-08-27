#!/usr/bin/env python3
"""Zerlegt den Reisezeitvorsprung des Gutachterentwurfs in seine zwei Ursachen.

Der Gutachterentwurf ist im Routing rund 44 Minuten schneller. Das kann zwei Gründe
haben, die sich fachlich vollkommen unterschiedlich lesen:

  (a) Infrastruktur — er lässt die Züge zwischen zwei Knoten schneller fahren, als es
      heute möglich ist. Unsere Studie verbietet das per Nebenbedingung („neubaufrei").
      Dann ist die Differenz kein Mangel unseres Modells, sondern der Preis der
      Nebenbedingung, und der Vergleich beziffert ihn.

  (b) Taktdisziplin — er fährt dieselben Kanten in derselben Zeit, verliert aber weniger
      Zeit an den Knoten, weil er die Züge nicht in enge gemeinsame Zeitfenster zwingt.
      Dann misst die Differenz, was unser strenger integraler Takt tatsächlich kostet.

Gemessen wird deshalb je Netzkante die reine Fahrzeit zwischen zwei benachbarten
Knoten — im Gutachterentwurf als Minimum über alle Züge, die beide Bahnhöfe ohne
Zwischenhalt verbinden, bei uns als heutige Bestzeit aus `kante`.

Aufruf:  zerlegung.py <bahn.db> <dtakt.db> <ziel.db>
"""
import sqlite3
import sys
import statistics

from knotenanalyse import KNOTEN_ZUORDNUNG

FV = ("A", "B", "C", "D", "F", "H")


def dtakt_kantenzeiten(con, codes):
    """Kürzeste Fahrzeit je Bahnhofspaar über einen direkten Abschnitt ohne Zwischenhalt."""
    platzhalter = ",".join("?" * len(FV))
    frage = f"""
      SELECT tp.train_part_id, trim(s.code), st.arrival, st.departure, st.sequence
      FROM stop st
      JOIN station s USING(station_id)
      JOIN train_part tp USING(train_part_id)
      JOIN category c USING(category_id)
      WHERE c.code IN ({platzhalter})
      ORDER BY tp.train_part_id, st.sequence
    """

    def minuten(t):
        if not t:
            return None
        hh, mm, _ = t.split(":")
        return int(hh) * 60 + int(mm)

    zeiten = {}
    laufweg, letzter = [], None
    for teil, code, an, ab, folge in con.execute(frage, FV):
        if teil != letzter:
            laufweg, letzter = [], teil
        laufweg.append((code, minuten(an), minuten(ab)))
        if len(laufweg) >= 2:
            (a_code, _, a_ab), (b_code, b_an, _) = laufweg[-2], laufweg[-1]
            if a_code in codes and b_code in codes and a_ab is not None and b_an is not None:
                dauer = b_an - a_ab
                if 0 < dauer < 600:
                    paar = (a_code, b_code)
                    if paar not in zeiten or dauer < zeiten[paar]:
                        zeiten[paar] = dauer
    return zeiten


def main():
    bahn_db, dtakt_db, ziel_db = sys.argv[1:4]
    code_von_name = {n: c[0] for n, c in KNOTEN_ZUORDNUNG.items()}
    name_von_code = {c: n for n, c in code_von_name.items()}

    dtakt = dtakt_kantenzeiten(sqlite3.connect(dtakt_db), set(name_von_code))

    bahn = sqlite3.connect(bahn_db)
    # unsere Kantenbasis: heutige Bestzeit und Median über alle beobachteten Fahrten
    unsere = {}
    for a, b, t_min, t_median in bahn.execute(
            "SELECT a, b, t_min, t_median FROM kante"):
        if a in code_von_name and b in code_von_name:
            unsere[(code_von_name[a], code_von_name[b])] = (t_min, t_median)

    zeilen = []
    for paar, d_zeit in sorted(dtakt.items()):
        u = unsere.get(paar)
        if not u:
            continue
        zeilen.append((name_von_code[paar[0]], name_von_code[paar[1]],
                       u[0], u[1], d_zeit, d_zeit - u[0], d_zeit - u[1]))

    con = sqlite3.connect(ziel_db)
    con.executescript("""
        DROP TABLE IF EXISTS kantenvergleich;
        CREATE TABLE kantenvergleich(
          von TEXT, nach TEXT, unser_bestzeit INT, unser_median INT,
          dtakt_zeit INT, diff_zur_bestzeit INT, diff_zum_median INT);
    """)
    con.executemany("INSERT INTO kantenvergleich VALUES(?,?,?,?,?,?,?)", zeilen)
    con.commit()

    if not zeilen:
        print("Keine gemeinsamen Kanten gefunden.")
        return

    d_best = [z[5] for z in zeilen]
    schneller = sum(1 for x in d_best if x < 0)
    langsamer = sum(1 for x in d_best if x > 0)

    print(f"Direkt vergleichbare Netzkanten zwischen unseren 20 Knoten: {len(zeilen)}\n")
    print(f"{'Vergleich gegen die heutige Bestzeit':<44}")
    print("─" * 63)
    print(f"  Gutachterentwurf schneller als heute möglich   {schneller:>4} Kanten")
    print(f"  Gutachterentwurf langsamer                     {langsamer:>4} Kanten")
    print(f"  gleich                                         {len(zeilen) - schneller - langsamer:>4} Kanten")
    print(f"\n  mittlere Abweichung  {statistics.mean(d_best):>+6.1f} min je Kante")
    print(f"  Median               {statistics.median(d_best):>+6.1f} min je Kante")
    summe_schneller = -sum(x for x in d_best if x < 0)
    print(f"  aufsummierte Beschleunigung über alle Kanten  {summe_schneller:>5} min")

    print("\nKanten, die der Gutachterentwurf schneller befährt als heute je gefahren wurde")
    print("(das ist genau der Neubau, den unsere Studie per Nebenbedingung ausschließt):")
    print(f"\n{'Kante':<48}{'heute':>7}{'D-Takt':>8}{'Diff':>7}")
    print("─" * 70)
    for z in sorted(zeilen, key=lambda z: z[5])[:20]:
        if z[5] >= 0:
            break
        print(f"{z[0] + ' → ' + z[1]:<48}{z[2]:>6}'{z[4]:>7}'{z[5]:>+6}")

    print("\nKanten, die der Gutachterentwurf langsamer befährt (Taktzuschlag oder Umweg):")
    print(f"\n{'Kante':<48}{'heute':>7}{'D-Takt':>8}{'Diff':>7}")
    print("─" * 70)
    for z in sorted(zeilen, key=lambda z: -z[5])[:10]:
        if z[5] <= 0:
            break
        print(f"{z[0] + ' → ' + z[1]:<48}{z[2]:>6}'{z[4]:>7}'{z[5]:>+6}")


if __name__ == "__main__":
    main()
