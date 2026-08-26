#!/usr/bin/env python3
"""Erzeugt zwei deckungsgleiche Anfragedateien für `motis batch`.

Gefragt wird nach allen geordneten Paaren der 20 Vollknoten zu drei Tageszeiten.
Beide Dateien enthalten dieselben Relationen in derselben Reihenfolge — nur unter
den Haltestellenkennungen des jeweiligen Fahrplans. Nur so lassen sich die Antworten
zeilenweise gegenüberstellen.

Die Zuordnung stammt aus knotenanalyse.KNOTEN_ZUORDNUNG und ist über RL100-Codes
geprüft; auf die maschinelle Namenszuordnung wird hier bewusst verzichtet, weil der
Gutachterentwurf DB-interne Kurznamen führt („Hmb-Harburg", „Mü-Pasing").

Aufruf:  baue_anfragen.py <ausgabeverzeichnis>
"""
import sys
import urllib.parse
from pathlib import Path

from knotenanalyse import KNOTEN_ZUORDNUNG

DATUM = "2026-09-02"                      # ein Mittwoch im Geltungszeitraum beider Feeds
ZEITEN = ["06:00:00Z", "10:00:00Z", "15:00:00Z"]   # 08, 12 und 17 Uhr Ortszeit


def anfrage(von, nach, zeit):
    return (f"/api/v6/plan?fromPlace={urllib.parse.quote_plus('plan_' + von)}"
            f"&toPlace={urllib.parse.quote_plus('plan_' + nach)}"
            f"&time={DATUM}T{zeit}")


def main():
    ziel = Path(sys.argv[1])
    ziel.mkdir(parents=True, exist_ok=True)

    knoten = [(unser, codes[0]) for unser, codes in KNOTEN_ZUORDNUNG.items()]

    unsere, dtakt, relationen = [], [], []
    for i, (u_von, d_von) in enumerate(knoten):
        for j, (u_nach, d_nach) in enumerate(knoten):
            if i == j:
                continue
            for zeit in ZEITEN:
                unsere.append(anfrage(u_von, u_nach, zeit))
                dtakt.append(anfrage(d_von, d_nach, zeit))
                relationen.append((u_von, u_nach, zeit))

    (ziel / "queries-systemtakt.txt").write_text("\n".join(unsere) + "\n", encoding="utf-8")
    (ziel / "queries-dtakt.txt").write_text("\n".join(dtakt) + "\n", encoding="utf-8")
    with open(ziel / "relationen.csv", "w", encoding="utf-8") as f:
        f.write("nr;von;nach;zeit\n")
        for nr, (v, n, z) in enumerate(relationen):
            f.write(f"{nr};{v};{n};{z}\n")

    print(f"{len(knoten)} Knoten → {len(relationen)} Anfragen je Fahrplan "
          f"({len(knoten) * (len(knoten) - 1)} Relationen × {len(ZEITEN)} Zeiten)")


if __name__ == "__main__":
    main()
