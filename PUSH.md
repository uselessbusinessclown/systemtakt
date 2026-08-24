# Dieses Repository auf GitHub veröffentlichen

Das Repository ist vollständig vorbereitet und committet (zwei Commits, Branch `main`).
Es fehlt nur noch der Push.

## Weg 1 — selbst pushen (funktioniert immer)

```bash
unzip systemtakt-fernverkehr-repo.zip
cd systemtakt-fernverkehr
git remote add origin https://github.com/uselessbusinessclown/systemtakt.git
git push -u origin main
```

Falls das Zielrepository bereits eine README oder Lizenz enthält, vorher einmal
`git pull --rebase origin main` — oder das Repository leer anlegen.

## Weg 2 — Claude pushen lassen

Dafür muss das Repository der Sitzung als Quelle hinzugefügt werden. Der Git-Proxy dieser
Umgebung reicht Zugangsdaten nur für Repositories durch, die in der Sitzungskonfiguration
stehen; ein eigenes Token hilft nicht, GitHub lehnt es für Git-Operationen ab.

In der Claude-Desktop-App: die GitHub-Quelle der Sitzung um
`uselessbusinessclown/systemtakt` erweitern. Danach genügt ein Hinweis, und der Push läuft.

## Was gepusht wird

| | |
|---|---|
| Dateien | 115 |
| Größe | rund 18 MB |
| Commits | 2 |
| Branch | `main` |

Enthalten sind Quellcode (Pipeline, Optimierer, Fahrplan-Engine, PDF-Erzeugung),
Dokumentation, die SQLite-Datenbank, der CSV-Export aller 36 Tabellen und die fertigen
Ausgaben (zwei Kursbuch-PDFs, Studie als PDF und Word, Excel-Arbeitsmappe).
