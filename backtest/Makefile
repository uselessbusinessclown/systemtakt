# Backtest gegen den offiziellen Deutschlandtakt
#
# Der 3. Gutachterentwurf des Zielfahrplans ist nach dem Informationsfreiheitsgesetz
# maschinenlesbar veröffentlicht. Er ist die einzige unabhängige Gegenprobe zu unserem
# gerechneten Knotenplan, die es gibt — erstellt von Gutachtern mit Betriebssimulation
# und Infrastrukturplanung, für dasselbe Netz.
#
# Der Weg von der Rohdatei zum Vergleich folgt schaerfo/dtakt-fahrplan (MIT):
# railML einlesen, nach GTFS wandeln, mit MOTIS routen.
#
# Voraussetzungen: curl, unzip, patch, Python 3.11+, rund 3 GB freier Plattenplatz.
# Für den Routing-Vergleich zusätzlich MOTIS (siehe Ziel `motis`).

PY      := python3
ROOT    := ..
EIN     := input
ZWISCHEN:= intermediate
AUS     := out
BAHN    := $(ROOT)/data/bahn.db

# Zielfahrplan Deutschlandtakt, 3. Gutachterentwurf, über fragdenstaat.de (27 MB)
QUELLE_ZIP   := https://fragdenstaat.de/files/foi/519018/3.%20Gutachterentwurf%20Zielfahrplan%20Dtakt%20-%20maschienenlesbar.zip?download
# Gemeinschaftspatch, behebt rund 360 doppelte trainPart-Kennungen im Original
QUELLE_PATCH := https://gist.github.com/TheMinefighter/1ed90508f3fff466c43869c1b394b243/raw/7e4cb4983c3bf6e5e2b03564cd72a07a9f9c16cc/Export_fixed.railml.diff

MOTIS ?= motis

.DEFAULT_GOAL := help
.PHONY: help alle daten knoten routing motis aufraeumen

help:
	@echo "Ziele:"
	@echo "  daten     Gutachterentwurf laden und nach SQLite einlesen (~750 MB Download+Entpacken)"
	@echo "  knoten    Knotenminuten ableiten und vergleichen (heute, unser Plan, Gutachterentwurf)"
	@echo "  routing   beide Fahrpläne als GTFS exportieren und Anfragen bauen"
	@echo "  motis     Anfragen durch MOTIS fahren und auswerten (MOTIS=<pfad> nötig)"
	@echo "  alle      daten, knoten, routing"
	@echo
	@echo "Ergebnis liegt in $(AUS)/backtest.db; die Auswertung steht in"
	@echo "$(ROOT)/docs/08-backtest-deutschlandtakt.md"

alle: daten knoten routing

# ---------------------------------------------------------------- Rohdaten
$(EIN)/dtakt-schedule.zip:
	mkdir -p $(EIN)
	curl -sSL -o $@ "$(QUELLE_ZIP)"

$(EIN)/Export_fixed.railml.diff:
	mkdir -p $(EIN)
	curl -sSL -o $@ "$(QUELLE_PATCH)"

$(ZWISCHEN)/dtakt.railml: $(EIN)/dtakt-schedule.zip
	mkdir -p $(ZWISCHEN)
	unzip -o -q $< -d $(ZWISCHEN)
	mv "$(ZWISCHEN)/200713_3GE_FV,NV,SGV_Export.railml" $@

# Zeilenenden normalisieren, damit der Patch greift (ersetzt dos2unix)
$(ZWISCHEN)/dtakt-lf.railml: $(ZWISCHEN)/dtakt.railml $(EIN)/Export_fixed.railml.diff
	LC_ALL=C tr -d '\r' < $< > $@
	patch --quiet $@ < $(EIN)/Export_fixed.railml.diff

$(ZWISCHEN)/dtakt.db: $(ZWISCHEN)/dtakt-lf.railml dtakt_ingest.py
	$(PY) dtakt_ingest.py $< $@

daten: $(ZWISCHEN)/dtakt.db

# ---------------------------------------------------------------- Auswertung
$(AUS)/backtest.db: $(ZWISCHEN)/dtakt.db match_stations.py
	mkdir -p $(AUS)
	$(PY) match_stations.py $(BAHN) $< $@

knoten: $(AUS)/backtest.db knotenanalyse.py knotensuche.py
	$(PY) knotenanalyse.py $(BAHN) $(ZWISCHEN)/dtakt.db $(AUS)/backtest.db 30
	$(PY) knotensuche.py $(ZWISCHEN)/dtakt.db $(AUS)/backtest.db
	$(PY) zerlegung.py $(BAHN) $(ZWISCHEN)/dtakt.db $(AUS)/backtest.db
	$(PY) dreivergleich.py $(BAHN) $(ZWISCHEN)/dtakt.db

routing: $(AUS)/backtest.db export_gtfs.py baue_anfragen.py
	$(PY) export_gtfs.py unser $(BAHN) $(AUS)/backtest.db $(AUS)/systemtakt-gtfs.zip
	$(PY) export_gtfs.py dtakt $(ZWISCHEN)/dtakt.db $(AUS)/backtest.db $(AUS)/dtakt-gtfs.zip
	$(PY) baue_anfragen.py $(AUS)

# MOTIS gibt es als fertiges Programm unter github.com/motis-project/motis/releases.
# Pfad über MOTIS=... setzen, falls es nicht im Suchpfad liegt.
motis: routing
	for plan in systemtakt dtakt; do \
	  rm -rf $(AUS)/motis-$$plan; mkdir -p $(AUS)/motis-$$plan; \
	  cp $(AUS)/$$plan-gtfs.zip $(AUS)/motis-$$plan/feed.zip; \
	  printf 'timetable:\n  datasets:\n    plan:\n      path: feed.zip\nstreet_routing: false\ngeocoding: true\nosr_footpath: false\n' \
	    > $(AUS)/motis-$$plan/config.yml; \
	  ( cd $(AUS)/motis-$$plan && $(MOTIS) import -c config.yml >/dev/null ); \
	  cp $(AUS)/queries-$$plan.txt $(AUS)/motis-$$plan/queries.txt; \
	  ( cd $(AUS)/motis-$$plan && $(MOTIS) batch -d data -q queries.txt -r responses.txt >/dev/null ); \
	done
	$(PY) vergleich.py $(AUS)/relationen.csv \
	  $(AUS)/motis-systemtakt/responses.txt $(AUS)/motis-dtakt/responses.txt $(AUS)/backtest.db

aufraeumen:
	rm -rf $(ZWISCHEN) $(AUS)
	rm -f $(EIN)/dtakt-schedule.zip
