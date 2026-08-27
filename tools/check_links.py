#!/usr/bin/env python3
"""Prüft, dass alle relativen Verweise in den Markdown-Dateien auf vorhandene Dateien zeigen.

Externe Verweise (http, https, mailto) und reine Ankerziele werden übersprungen —
sie zu prüfen hieße, im CI das Netz zu befragen.
"""
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)")
EXTERN = ("http://", "https://", "mailto:", "#")

fehler = []
geprueft = 0

for markdown in sorted(ROOT.glob("**/*.md")):
    if ".git" in markdown.parts or "node_modules" in markdown.parts:
        continue
    for treffer in LINK.finditer(markdown.read_text(encoding="utf-8")):
        ziel = treffer.group(1)
        if ziel.startswith(EXTERN):
            continue
        geprueft += 1
        datei = urllib.parse.unquote(ziel.split("#")[0])
        if not datei:
            continue
        if not (markdown.parent / datei).resolve().exists():
            fehler.append(f"{markdown.relative_to(ROOT)} → {ziel}")

for eintrag in fehler:
    print(f"TOTER VERWEIS  {eintrag}")

print(f"{geprueft} relative Verweise geprüft, {len(fehler)} tot")
sys.exit(1 if fehler else 0)
