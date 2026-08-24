"""Pfade des Projekts, unabhängig vom Arbeitsverzeichnis."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, 'data')
OUT  = os.path.join(ROOT, 'output')
DB   = os.path.join(DATA, 'bahn.db')
GTFS = os.path.join(DATA, 'gtfs_fv')
for p in (DATA, OUT): os.makedirs(p, exist_ok=True)
# damit `import lib.xyz` und `import xyz` aus src/lib funktionieren
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'src', 'lib'))
