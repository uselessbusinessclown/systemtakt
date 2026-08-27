# Systemtakt Fernverkehr — Reproduktionspfad
# Alle Skripte schreiben in data/bahn.db und lesen von dort.

PY := python3
SRC := src

.DEFAULT_GOAL := help
.PHONY: help all daten analyse optimierung fahrplan ausgaben pruefen clean

## 0 — Übersicht der Ziele
help:
	@echo "Ziele:"
	@echo "  daten        Rohdaten laden und data/bahn.db aufbauen"
	@echo "  analyse      Netz- und Angebotsanalyse"
	@echo "  optimierung  Knotenwahl und exakte Optimierung (~1 h)"
	@echo "  fahrplan     Minutenplan zum Tagesfahrplan ausrollen"
	@echo "  ausgaben     PDFs, Word-Studie und Excel-Arbeitsmappe erzeugen"
	@echo "  all          alles der Reihe nach"
	@echo "  pruefen      dieselben Prüfungen wie im CI"
	@echo "  clean        Rohdaten und Zwischenstände entfernen"
	@echo
	@echo "Bekannte Lücken der Reproduktion: docs/07-bekannte-luecken.md"

all: daten analyse optimierung fahrplan ausgaben

## 1 — Rohdaten laden und Datenbank aufbauen
daten:
	curl -sSL -o /tmp/fv.zip https://download.gtfs.de/germany/fv_free/latest.zip
	mkdir -p data/gtfs_fv && unzip -o /tmp/fv.zip -d data/gtfs_fv
	curl -sSL -o /tmp/countries.geojson https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson
	curl -sSL -o /tmp/bl.geojson https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_bundeslaender/1_sehr_hoch.geo.json
	$(PY) $(SRC)/01_build_db.py
	$(PY) $(SRC)/02_stations.py
	$(PY) $(SRC)/03_fix_names.py
	$(PY) $(SRC)/04_cities.py
	$(PY) $(SRC)/05_trip_summary.py
	$(PY) $(SRC)/06_classify_sprinter.py

## 2 — Netz- und Angebotsanalyse
analyse:
	$(PY) $(SRC)/07_analysis.py
	$(PY) $(SRC)/08_ziel_liniennetz.py
	$(PY) $(SRC)/09_itf_edges.py
	$(PY) $(SRC)/10_systemfahrzeiten.py
	$(PY) $(SRC)/19_ist_takt.py
	$(PY) $(SRC)/20_kapazitaet.py

## 3 — Knotenwahl und exakte Optimierung (dauert ~1 h)
optimierung:
	$(PY) $(SRC)/11_knotenwahl.py
	$(PY) $(SRC)/12_optimize_final.py

## 4 — Fahrplan ausrollen
fahrplan:
	$(PY) $(SRC)/13_build_fahrplan.py
	$(PY) $(SRC)/21_sprinter_ueberholung.py

## 5 — Ausgaben
ausgaben:
	$(PY) $(SRC)/17_frankfurt_varianten.py
	$(PY) $(SRC)/18_zentrierung.py
	$(PY) $(SRC)/14_pdf_kursbuch.py
	$(PY) $(SRC)/15_pdf_bahnhoefe.py
	$(PY) $(SRC)/16_build_xlsx.py
	cd $(SRC)/web && npm install --silent && node makedoc.js

## 6 — Dieselben Prüfungen, die der CI fährt
pruefen:
	$(PY) -m compileall -q $(SRC)
	$(PY) tools/check_bootstrap.py
	$(PY) tools/check_links.py
	@command -v ruff >/dev/null && ruff check $(SRC) || echo "ruff nicht installiert — übersprungen"

clean:
	rm -rf data/gtfs_fv
	rm -f /tmp/fv.zip /tmp/countries.geojson /tmp/bl.geojson
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
