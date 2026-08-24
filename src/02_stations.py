
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lib'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src', 'lib'))
from paths import ROOT, DATA, OUT, DB, GTFS  # noqa: E402
import sqlite3, json, math, os
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
from shapely.prepared import prep

con = sqlite3.connect(DB); cur = con.cursor()

# --- country lookup
cg = json.load(open('/tmp/countries.geojson'))
polys=[]; names=[]
for f in cg['features']:
    p = f['properties']
    iso = p.get('ISO3166-1-Alpha-2') or ''
    nm  = p.get('name') or ''
    try: g = shape(f['geometry'])
    except Exception: continue
    polys.append(g); names.append((iso, nm))
tree = STRtree(polys)

bl = json.load(open('/tmp/bl.geojson'))
blp = [(shape(f['geometry']), f['properties']['name'], f['properties']['id']) for f in bl['features']]

def country(lat, lon):
    pt = Point(lon, lat)
    for i in tree.query(pt):
        if polys[i].contains(pt): return names[i]
    # nearest fallback
    i = min(range(len(polys)), key=lambda j: polys[j].distance(pt))
    return names[i]

def bundesland(lat, lon):
    pt = Point(lon, lat)
    for g,nm,iso in blp:
        if g.contains(pt): return nm, iso
    return None, None

cur.executescript("""
DROP TABLE IF EXISTS station;
CREATE TABLE station(
  station_id TEXT PRIMARY KEY,   -- parent_station id
  name TEXT, lat REAL, lon REAL,
  land_iso TEXT, land TEXT, bundesland TEXT, bundesland_iso TEXT
);
DROP TABLE IF EXISTS stop_station;
CREATE TABLE stop_station(stop_id TEXT PRIMARY KEY, station_id TEXT);
""")

rows = list(cur.execute("""
 SELECT s.parent, MIN(s.name), AVG(s.lat), AVG(s.lon)
 FROM stop s WHERE s.parent IS NOT NULL GROUP BY s.parent"""))
out=[]
for sid, name, lat, lon in rows:
    iso, cn = country(lat, lon)
    bln, bli = bundesland(lat, lon) if iso=='DE' else (None,None)
    out.append((sid, name, lat, lon, iso, cn, bln, bli))
cur.executemany("INSERT INTO station VALUES(?,?,?,?,?,?,?,?)", out)
cur.execute("INSERT INTO stop_station SELECT stop_id, parent FROM stop WHERE parent IS NOT NULL")
con.commit()
print('stations', len(out))
for r in cur.execute("SELECT land_iso, land, COUNT(*) FROM station GROUP BY 1 ORDER BY 3 DESC"): print(' ', r)
con.close()
