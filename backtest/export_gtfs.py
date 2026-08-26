#!/usr/bin/env python3
"""Schreibt beide Fahrpläne als GTFS, damit dieselbe Routing-Engine sie bewerten kann.

Der Aufbau folgt schaerfo/dtakt-fahrplan (gtfs_views.sql, export_gtfs.py, MIT,
Copyright 2025 Christian Schärf): SQL-Sichten je GTFS-Datei, dann jede Sicht als CSV
in ein ZIP. Geändert ist die Quelle — hier kommt zusätzlich unser eigener gerechneter
Fahrplan hinzu, den es bislang nur als PDF, Excel und SQLite gab.

Koordinaten für die Bahnhöfe des Gutachterentwurfs stammen aus unserer eigenen
Datenbank, soweit die Zuordnung greift. Für die übrigen wird ein Platzhalter gesetzt:
MOTIS läuft hier mit abgeschaltetem Straßenrouting, die Lage geht deshalb nicht in die
Reisezeit ein — nur in die Ortssuche, die wir nicht benutzen.

Aufruf:  export_gtfs.py unser  <bahn.db>  <backtest.db> <ziel.zip>
         export_gtfs.py dtakt  <dtakt.db> <backtest.db> <ziel.zip>
"""
import csv
import io
import sqlite3
import sys
from zipfile import ZIP_DEFLATED, ZipFile

FV = ("A", "B", "C", "D", "F", "H")
# Bahnhöfe ohne gesicherte Koordinate bekommen weit auseinanderliegende Platzhalter.
# Alle auf denselben Punkt zu legen wäre ein Fehler: MOTIS bildet zwischen nahe
# beieinander liegenden Haltestellen Fußwege, und 197 Bahnhöfe auf einem Punkt ergäben
# lauter Umstiege zwischen Orten, die nichts miteinander zu tun haben. Das Raster liegt
# im Atlantik, damit die Platzhalter auch von echten Bahnhöfen weit entfernt sind.
PLATZHALTER_LAT0, PLATZHALTER_LON0, PLATZHALTER_SCHRITT = 40.0, -30.0, 0.5

# GTFS route_type je Kategorie des Gutachterentwurfs, nach schaerfo/dtakt-fahrplan
ROUTE_TYPE = {"X": 2, "F": 102, "A": 101, "N": 106, "S": 109, "C": 101,
              "D": 101, "H": 102, "RRX": 2, "RbZ": 106, "B": 101, "AS": 104}


def hhmmss(minuten):
    return f"{minuten // 60:02d}:{minuten % 60:02d}:00"


def schreibe(zip_pfad, tabellen):
    with ZipFile(zip_pfad, "w", compression=ZIP_DEFLATED) as z:
        for name, (kopf, zeilen) in tabellen.items():
            puffer = io.StringIO()
            schreiber = csv.writer(puffer, lineterminator="\n")
            schreiber.writerow(kopf)
            schreiber.writerows(zeilen)
            z.writestr(name, puffer.getvalue())
    return {name: len(z[1]) for name, z in tabellen.items()}


def unser(bahn_db, _backtest_db):
    con = sqlite3.connect(bahn_db)

    stops = [(name, name, lat, lon) for name, lat, lon in con.execute(
        "SELECT name, lat, lon FROM bahnhof_bedienung WHERE lat IS NOT NULL")]
    bekannt = {s[0] for s in stops}

    routen, trips = {}, []
    for zug_id, linie, kategorie, von, nach in con.execute(
            "SELECT zug_id, linie, kategorie, von, nach FROM fahrplan_zug"):
        routen[linie] = (linie, kategorie)
        trips.append((linie, "1", str(zug_id), f"{von} – {nach}"))

    zeiten = []
    for zug_id, folge, station, an, ab in con.execute(
            "SELECT zug_id, folge, station, an, ab FROM fahrplan_halt ORDER BY zug_id, folge"):
        if station not in bekannt:
            continue
        an = an if an is not None else ab
        ab = ab if ab is not None else an
        if an is None:
            continue
        zeiten.append((str(zug_id), station, hhmmss(an), hhmmss(ab), folge))

    return {
        "agency.txt": (["agency_id", "agency_name", "agency_url", "agency_timezone"],
                       [("1", "Systemtakt Fernverkehr", "https://github.com/uselessbusinessclown/systemtakt", "Europe/Berlin")]),
        "calendar.txt": (["service_id", "monday", "tuesday", "wednesday", "thursday",
                          "friday", "saturday", "sunday", "start_date", "end_date"],
                         [("1", 1, 1, 1, 1, 1, 1, 1, "20260101", "20261231")]),
        "stops.txt": (["stop_id", "stop_name", "stop_lat", "stop_lon"], stops),
        "routes.txt": (["route_id", "agency_id", "route_short_name", "route_type"],
                       [(linie, "1", kategorie, 101) for linie, kategorie in routen.values()]),
        "trips.txt": (["route_id", "service_id", "trip_id", "trip_headsign"], trips),
        "stop_times.txt": (["trip_id", "stop_id", "arrival_time", "departure_time", "stop_sequence"],
                           zeiten),
    }


def dtakt(dtakt_db, backtest_db):
    con = sqlite3.connect(dtakt_db)
    con.execute("ATTACH DATABASE ? AS bt", (backtest_db,))

    # Koordinaten über die geprüfte Namenszuordnung, sonst Platzhalter
    koordinaten = {}
    for code, lat, lon in con.execute("""
            SELECT trim(s.code), z.lat, z.lon
            FROM bt.zuordnung z JOIN station s ON s.name = z.dtakt_name
            WHERE z.dtakt_name IS NOT NULL AND z.lat IS NOT NULL"""):
        koordinaten[code] = (lat, lon)

    platzhalter = ",".join("?" * len(FV))
    stops = []
    ohne_koordinate = 0
    for code, name in con.execute(f"""
            SELECT DISTINCT trim(s.code), s.name
            FROM stop st JOIN station s USING(station_id)
            JOIN train_part tp USING(train_part_id) JOIN category c USING(category_id)
            WHERE c.code IN ({platzhalter})
            ORDER BY trim(s.code)""", FV):
        if code in koordinaten:
            lat, lon = koordinaten[code]
        else:
            lat = PLATZHALTER_LAT0 + (ohne_koordinate // 20) * PLATZHALTER_SCHRITT
            lon = PLATZHALTER_LON0 + (ohne_koordinate % 20) * PLATZHALTER_SCHRITT
            ohne_koordinate += 1
        stops.append((code, name, lat, lon))
    print(f"  (davon {ohne_koordinate} ohne gesicherte Koordinate)")

    routen, trips = {}, []
    for train_id, gruppe, beschreibung, kat in con.execute(f"""
            SELECT t.train_id, coalesce(t.group_id, t.train_id), t.description, c.code
            FROM train t JOIN train_part tp USING(train_part_id)
            JOIN category c USING(category_id)
            WHERE c.code IN ({platzhalter})""", FV):
        routen[gruppe] = (gruppe, kat)
        trips.append((gruppe, "1", train_id, (beschreibung or "")[:120]))

    zeiten = []
    for train_id, code, an, ab, folge in con.execute(f"""
            SELECT t.train_id, trim(s.code), st.arrival, st.departure, st.sequence
            FROM stop st
            JOIN station s USING(station_id)
            JOIN train_part tp USING(train_part_id)
            JOIN category c USING(category_id)
            JOIN train t USING(train_part_id)
            WHERE c.code IN ({platzhalter})
            ORDER BY t.train_id, st.sequence""", FV):
        an = an or ab
        ab = ab or an
        if not an:
            continue
        zeiten.append((train_id, code, an, ab, folge))

    return {
        "agency.txt": (["agency_id", "agency_name", "agency_url", "agency_timezone"],
                       [("1", "Deutschlandtakt (3. Gutachterentwurf)", "https://www.deutschlandtakt.de", "Europe/Berlin")]),
        "calendar.txt": (["service_id", "monday", "tuesday", "wednesday", "thursday",
                          "friday", "saturday", "sunday", "start_date", "end_date"],
                         [("1", 1, 1, 1, 1, 1, 1, 1, "20260101", "20261231")]),
        "stops.txt": (["stop_id", "stop_name", "stop_lat", "stop_lon"], stops),
        "routes.txt": (["route_id", "agency_id", "route_short_name", "route_type"],
                       [(g, "1", k, ROUTE_TYPE.get(k, 101)) for g, k in routen.values()]),
        "trips.txt": (["route_id", "service_id", "trip_id", "trip_headsign"], trips),
        "stop_times.txt": (["trip_id", "stop_id", "arrival_time", "departure_time", "stop_sequence"],
                           zeiten),
    }


def main():
    welcher, quelle, backtest, ziel = sys.argv[1:5]
    tabellen = {"unser": unser, "dtakt": dtakt}[welcher](quelle, backtest)
    for name, anzahl in schreibe(ziel, tabellen).items():
        print(f"  {name:<16}{anzahl:>8,}".replace(",", "."))


if __name__ == "__main__":
    main()
