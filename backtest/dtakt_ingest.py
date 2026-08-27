#!/usr/bin/env python3
"""Liest den 3. Gutachterentwurf Zielfahrplan Deutschlandtakt (railML 2.2) nach SQLite.

Schema und die Behandlung negativer Tagesversätze sind übernommen aus
schaerfo/dtakt-fahrplan (db_ingest.py, MIT, Copyright 2025 Christian Schärf).
Geändert: streamender Parser (iterparse) statt vollständigem DOM — die Datei ist
698 MB groß, das Original braucht dafür rund 10 GB Arbeitsspeicher.

Aufruf:  dtakt_ingest.py <dtakt-lf.railml> <ziel.db>
"""
import re
import sqlite3
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://www.railml.org/schemas/2013}"
NS_VIR = "{http://www.sma-partner.ch/schemas/2013/Viriato/Base}"

SCHEMA = """
PRAGMA journal_mode = OFF;
PRAGMA synchronous  = OFF;

CREATE TABLE station(
  station_id TEXT PRIMARY KEY, name TEXT, code TEXT, operational_type TEXT);

CREATE TABLE category(
  category_id TEXT PRIMARY KEY, code TEXT, description TEXT);

CREATE TABLE train_part(
  train_part_id TEXT PRIMARY KEY, category_id TEXT);

CREATE TABLE stop(
  stop_id INTEGER PRIMARY KEY, train_part_id TEXT, station_id TEXT,
  arrival TEXT, departure TEXT, sequence INT);

CREATE TABLE train(
  train_id TEXT PRIMARY KEY, description TEXT, train_number TEXT,
  line_name TEXT, train_part_id TEXT, group_id TEXT, sequence INT);

CREATE TABLE train_group(
  train_group_id TEXT PRIMARY KEY, code TEXT, train_number INT);
"""

INDIZES = """
CREATE INDEX ix_stop_part    ON stop(train_part_id);
CREATE INDEX ix_stop_station ON stop(station_id);
CREATE INDEX ix_train_part   ON train(train_part_id);
"""

ZEIT = re.compile(r"^((\d{2}):\d{2}:\d{2})(?:\.\d+)?$")


class Zeit:
    """Rechnet Ankunfts- und Abfahrtszeiten in GTFS-taugliche Zeiten um.

    Der Datensatz enthält vereinzelt negative arrivalDay/departureDay. GTFS kennt
    keine negativen Zeiten, deshalb wird der gesamte Zuglauf um den nötigen Betrag
    nach vorn geschoben. Logik aus schaerfo/dtakt-fahrplan.
    """

    def __init__(self):
        self._versatz = 0

    def lies(self, times_el, schluessel):
        wert = times_el.attrib.get(schluessel)
        if not wert:
            return None
        treffer = ZEIT.search(wert)
        if not treffer:
            return None
        wert = treffer[1]
        tag = times_el.attrib.get(schluessel + "Day")
        if tag:
            tag = int(tag)
            if tag < 0:
                self._versatz = -tag
            tag += self._versatz
        else:
            tag = self._versatz
        if tag > 0:
            stunden = treffer[2]
            wert = str(int(stunden) + 24 * tag) + wert[len(stunden):]
        return wert


def main():
    quelle, ziel = sys.argv[1], sys.argv[2]
    Path(ziel).unlink(missing_ok=True)
    con = sqlite3.connect(ziel)
    con.executescript(SCHEMA)

    stationen, kategorien, zugteile, halte = [], [], [], []
    zuege, gruppen = [], []
    halt_id = 0
    # Zugteil -> Gruppe wird erst über train aufgelöst; train kennt die Gruppe nicht
    # direkt, deshalb merken wir uns die Zuordnung aus trainGroup/trainRef.
    zug_zu_gruppe = {}

    def leeren():
        nonlocal stationen, kategorien, zugteile, halte, zuege, gruppen
        if stationen:
            con.executemany("INSERT OR REPLACE INTO station VALUES(?,?,?,?)", stationen)
            stationen = []
        if kategorien:
            con.executemany("INSERT OR REPLACE INTO category VALUES(?,?,?)", kategorien)
            kategorien = []
        if zugteile:
            con.executemany("INSERT OR REPLACE INTO train_part VALUES(?,?)", zugteile)
            zugteile = []
        if halte:
            con.executemany("INSERT INTO stop VALUES(?,?,?,?,?,?)", halte)
            halte = []
        if zuege:
            con.executemany("INSERT OR REPLACE INTO train VALUES(?,?,?,?,?,?,?)", zuege)
            zuege = []
        if gruppen:
            con.executemany("INSERT OR REPLACE INTO train_group VALUES(?,?,?)", gruppen)
            gruppen = []

    kontext = ET.iterparse(quelle, events=("end",))
    for _, el in kontext:
        tag = el.tag

        if tag == NS + "ocp":
            prop = el.find(NS + "propOperational")
            stationen.append((
                el.attrib["id"],
                el.attrib.get("name"),
                el.attrib.get("code"),
                prop.attrib.get("operationalType") if prop is not None else None,
            ))
            el.clear()

        elif tag == NS + "category":
            kategorien.append((el.attrib["id"], el.attrib.get("code"), el.attrib.get("description")))
            el.clear()

        elif tag == NS + "trainPart":
            teil_id = el.attrib["id"]
            zugteile.append((teil_id, el.attrib.get("categoryRef")))
            uhr = Zeit()
            folge = 1
            ocps = el.find(NS + "ocpsTT")
            if ocps is not None:
                for ocp in ocps:
                    art = ocp.attrib.get("ocpType")
                    if art != "stop":
                        continue
                    an = ab = None
                    for times in ocp.iterfind(NS + "times"):
                        if times.attrib.get("scope") == "published":
                            an = uhr.lies(times, "arrival")
                            ab = uhr.lies(times, "departure")
                    halt_id += 1
                    halte.append((halt_id, teil_id, ocp.attrib.get("ocpRef"), an, ab, folge))
                    folge += 1
            el.clear()
            if len(halte) > 200_000:
                leeren()

        elif tag == NS + "train":
            teil = el.find(NS + "trainPartSequence")
            ref = None
            if teil is not None:
                tpr = teil.find(NS + "trainPartRef")
                if tpr is not None:
                    ref = tpr.attrib.get("ref")
            name_el = el.find(NS_VIR + "trainName")
            zuege.append((
                el.attrib["id"],
                el.attrib.get("description"),
                el.attrib.get("trainNumber"),
                name_el.text if name_el is not None else None,
                ref,
                None,
                None,
            ))
            el.clear()

        elif tag == NS + "trainGroup":
            gid = el.attrib["id"]
            nummer = el.attrib.get("trainNumber")
            gruppen.append((gid, el.attrib.get("code"), int(nummer) if nummer else None))
            for kind in el:
                if kind.tag == NS + "trainRef":
                    zug_zu_gruppe[kind.attrib["ref"]] = (gid, kind.attrib.get("sequence"))
            el.clear()

    leeren()
    con.executemany(
        "UPDATE train SET group_id=?, sequence=? WHERE train_id=?",
        [(g, s, t) for t, (g, s) in zug_zu_gruppe.items()],
    )
    con.executescript(INDIZES)
    con.commit()

    for tabelle in ("station", "category", "train_part", "stop", "train", "train_group"):
        anzahl = con.execute(f"SELECT count(*) FROM {tabelle}").fetchone()[0]
        print(f"  {tabelle:<12} {anzahl:>9,}".replace(",", "."))
    con.close()


if __name__ == "__main__":
    main()
