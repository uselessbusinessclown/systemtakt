#!/usr/bin/env python3
"""Leitet Knotenminuten aus einem Fahrplan ab — für beide Fahrpläne mit demselben Verfahren.

Einen Vollknoten erkennt man daran, dass die Züge kurz vor einer bestimmten Minute
ankommen und kurz danach abfahren. Gesucht ist die Minute, die zu den meisten Halten
passt; weil bei einem sauber gebauten Knoten alle Minuten zwischen der letzten Ankunft
und der ersten Abfahrt gleich gut passen, wird die Mitte dieses Plateaus genommen.

Das Verfahren wird unverändert auf unseren gerechneten Fahrplan und auf den
Gutachterentwurf angewandt — nur so ist der Vergleich belastbar. Die Eichprobe prüft,
ob es unsere eigenen, veröffentlichten Knotenminuten wiederfindet; sie muss 20/20
treffen, sonst misst der anschließende Vergleich den eigenen Schätzfehler mit.

Aufruf:  knotenanalyse.py <unser.db> <dtakt.db> <ziel.db> [takt]
"""
import sqlite3
import sys

FENSTER = 8     # halbe Knotenfensterbreite in Minuten
FV = ("A", "B", "C", "D", "F", "H")

# Über RL100 verifizierte Zuordnung unserer 20 Vollknoten. Frankfurt und Berlin
# führt der Gutachterentwurf getrennt nach Bahnsteigebene — beide werden ausgewiesen.
KNOTEN_ZUORDNUNG = {
    "Hannover Hbf":        ["HH"],
    "Frankfurt(Main)Hbf":  ["YFFF", "FF"],
    "Nürnberg Hbf":        ["NN"],
    "Mannheim Hbf":        ["RM"],
    "Erfurt Hbf":          ["UE  P"],
    "Berlin Hbf":          ["BL", "BLS"],
    "Köln Hbf":            ["KK"],
    "München Hbf":         ["MH"],
    "Kassel-Wilhelmshöhe": ["FKW"],
    "Fulda":               ["FFU"],
    "Dortmund Hbf":        ["EDO"],
    "Würzburg Hbf":        ["NWH"],
    "Duisburg Hbf":        ["EDG"],
    "Hamburg Hbf":         ["AH"],
    "Stuttgart Hbf":       ["TS F"],
    "Leipzig Hbf":         ["LL"],
    "Bremen Hbf":          ["HB"],
    "Münster(Westf)Hbf":   ["EMSTP"],
    "Karlsruhe Hbf":       ["RK"],
    "Dresden Hbf":         ["DH"],
}


def knotenminute(ankuenfte, abfahrten, takt, fenster=FENSTER):
    """(Minute, Güte, Anzahl Halte) für eine Menge von Halten.

    Bewertet wird je Kandidatenminute m, wie viele Halte in das Knotenmuster passen:
    Ankunft in (m - fenster, m], Abfahrt in [m, m + fenster). Bei einem sauber
    gebauten Taktknoten erreichen mehrere aufeinanderfolgende Minuten denselben
    Höchstwert — nämlich alle Minuten zwischen der letzten Ankunft und der ersten
    Abfahrt. Genommen wird die Mitte dieses Plateaus.

    Das ist genau die Definition, der auch unsere veröffentlichte `knotenminute`
    folgt: Hannover hat Ankünfte :26/:27 und Abfahrten :31/:34, ausgewiesen ist :29.
    Wer statt der Mitte den Rand nimmt, verschiebt jeden Knoten systematisch — und
    vergleicht am Ende zwei Fahrpläne über einen Fehler des eigenen Schätzers.
    """
    gesamt = len(ankuenfte) + len(abfahrten)
    if gesamt == 0:
        return None, 0.0, 0

    punkte = []
    for m in range(takt):
        treffer = 0
        for a in ankuenfte:
            if (m - a) % takt < fenster:      # Ankunft liegt vor der Knotenminute
                treffer += 1
        for d in abfahrten:
            if (d - m) % takt < fenster:      # Abfahrt liegt nach der Knotenminute
                treffer += 1
        punkte.append(treffer)

    hoechst = max(punkte)
    kandidaten = [m for m in range(takt) if punkte[m] == hoechst]

    # Längsten zusammenhängenden Bogen der Gewinnerminuten suchen (zyklisch)
    bester_bogen = []
    for start in kandidaten:
        if (start - 1) % takt in kandidaten:
            continue                          # nicht der Beginn eines Bogens
        bogen, m = [], start
        while m in kandidaten and len(bogen) < takt:
            bogen.append(m)
            m = (m + 1) % takt
        if len(bogen) > len(bester_bogen):
            bester_bogen = bogen
    if not bester_bogen:                      # alle Minuten gleichauf
        bester_bogen = kandidaten

    mitte = bester_bogen[(len(bester_bogen) - 1) // 2]
    return mitte, hoechst / gesamt, gesamt


def unsere_halte(db, takt):
    con = sqlite3.connect(db)
    daten = {}
    for station, an, ab in con.execute("SELECT station, an, ab FROM fahrplan_halt"):
        a, d = daten.setdefault(station, ([], []))
        if an is not None:
            a.append(an % takt)
        if ab is not None:
            d.append(ab % takt)
    return daten


def dtakt_halte(db, takt):
    con = sqlite3.connect(db)
    frage = f"""
      SELECT trim(s.code), st.arrival, st.departure
      FROM stop st
      JOIN station s USING(station_id)
      JOIN train_part tp USING(train_part_id)
      JOIN category c USING(category_id)
      WHERE c.code IN ({','.join('?' * len(FV))})
    """
    daten = {}
    for code, an, ab in con.execute(frage, FV):
        a, d = daten.setdefault(code, ([], []))
        if an:
            hh, mm, _ = an.split(":")
            a.append((int(hh) * 60 + int(mm)) % takt)
        if ab:
            hh, mm, _ = ab.split(":")
            d.append((int(hh) * 60 + int(mm)) % takt)
    return daten


def abweichung(a, b, takt):
    d = (a - b) % takt
    return min(d, takt - d)


def main():
    unser_db, dtakt_db, ziel_db = sys.argv[1], sys.argv[2], sys.argv[3]
    takt = int(sys.argv[4]) if len(sys.argv) > 4 else 30

    unsere = unsere_halte(unser_db, takt)
    dtakt = dtakt_halte(dtakt_db, takt)
    veroeffentlicht = dict(
        sqlite3.connect(unser_db).execute("SELECT name, knotenminute FROM itf_knotenzeit"))

    zeilen = []
    for name, codes in KNOTEN_ZUORDNUNG.items():
        u_an, u_ab = unsere.get(name, ([], []))
        u_m, u_g, u_n = knotenminute(u_an, u_ab, takt)
        for code in codes:
            d_an, d_ab = dtakt.get(code, ([], []))
            d_m, d_g, d_n = knotenminute(d_an, d_ab, takt)
            zeilen.append(dict(
                takt=takt, name=name, code=code, haupt=1 if code == codes[0] else 0,
                unser_m=u_m, unser_guete=u_g, unser_n=u_n,
                veroeffentlicht=veroeffentlicht.get(name),
                dtakt_m=d_m, dtakt_guete=d_g, dtakt_n=d_n))

    ziel = sqlite3.connect(ziel_db)
    ziel.executescript("""
        CREATE TABLE IF NOT EXISTS knotenvergleich(
          takt INT, name TEXT, code TEXT, haupt INT,
          unser_m INT, unser_guete REAL, unser_n INT,
          veroeffentlicht INT,
          dtakt_m INT, dtakt_guete REAL, dtakt_n INT,
          PRIMARY KEY(takt, name, code));
    """)
    ziel.executemany(
        "INSERT OR REPLACE INTO knotenvergleich VALUES(:takt,:name,:code,:haupt,"
        ":unser_m,:unser_guete,:unser_n,:veroeffentlicht,"
        ":dtakt_m,:dtakt_guete,:dtakt_n)", zeilen)
    ziel.commit()

    haupt = [z for z in zeilen if z["haupt"]]

    print(f"═══ Grundtakt {takt} Minuten, Knotenfenster ±{FENSTER} min ═══\n")

    # --- Eichprobe ---
    genau = sum(1 for z in haupt if abweichung(z["unser_m"], z["veroeffentlicht"], takt) == 0)
    bis1 = sum(1 for z in haupt if abweichung(z["unser_m"], z["veroeffentlicht"], takt) <= 1)
    print(f"Eichprobe am eigenen Fahrplan: {genau}/{len(haupt)} Knotenminuten exakt, "
          f"{bis1}/{len(haupt)} auf ±1 min genau wiedergefunden")
    u_guete = sum(z["unser_guete"] for z in haupt) / len(haupt)
    d_guete = sum(z["dtakt_guete"] for z in haupt) / len(haupt)
    print(f"Mittlere Knotengüte: unser Fahrplan {u_guete:.0%}, Gutachterentwurf {d_guete:.0%}\n")

    print(f"{'Knoten':<22}{'unser':>7}{'Güte':>6}  {'D-Takt':>7}{'Güte':>6}{'Halte':>8}   Code")
    print("─" * 72)
    for z in haupt:
        print(f"{z['name']:<22}{z['unser_m']:>6}'{z['unser_guete']:>5.0%}  "
              f"{z['dtakt_m']:>6}'{z['dtakt_guete']:>5.0%}{z['dtakt_n']:>8}   {z['code']}")

    # --- gemeinsame Verschiebung ---
    bester_v, beste_summe = 0, None
    for v in range(takt):
        summe = sum(abweichung(z["dtakt_m"] - v, z["unser_m"], takt) for z in haupt)
        if beste_summe is None or summe < beste_summe:
            bester_v, beste_summe = v, summe
    mittel = beste_summe / len(haupt)
    zufall = takt / 4
    print(f"\nBeste gemeinsame Verschiebung: {bester_v:+d} min")
    print(f"  mittlere Abweichung danach   {mittel:.1f} min je Knoten")
    print(f"  bei zufälliger Lage erwartet {zufall:.1f} min")
    print(f"  → {'deutlich besser als Zufall' if mittel < zufall * 0.6 else 'nicht besser als Zufall'}")

    innerhalb3 = sum(1 for z in haupt if abweichung(z["dtakt_m"] - bester_v, z["unser_m"], takt) <= 3)
    print(f"  {innerhalb3}/{len(haupt)} Knoten liegen nach der Verschiebung innerhalb von 3 Minuten")

    print(f"\n{'Knoten':<22}{'unser':>7}{'D-Takt':>8}{'Abw.':>8}")
    print("─" * 46)
    for z in sorted(haupt, key=lambda z: abweichung(z["dtakt_m"] - bester_v, z["unser_m"], takt)):
        abw = abweichung(z["dtakt_m"] - bester_v, z["unser_m"], takt)
        print(f"{z['name']:<22}{z['unser_m']:>6}'{z['dtakt_m']:>7}'{abw:>5} min")

    # --- Zweitebenen (Frankfurt, Berlin) ---
    neben = [z for z in zeilen if not z["haupt"]]
    if neben:
        print("\nZweite Bahnsteigebene im Gutachterentwurf:")
        for z in neben:
            print(f"  {z['name']:<22}{z['code']:<7}{z['dtakt_m']:>4}'  Güte {z['dtakt_guete']:>4.0%}"
                  f"  {z['dtakt_n']:>5} Halte")


if __name__ == "__main__":
    main()
